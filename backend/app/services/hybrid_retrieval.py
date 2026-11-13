"""Combine exact document terms with semantic search for the local law library."""

from collections import Counter
import math
import re

from langchain_core.documents import Document


WORDS = re.compile(r"[a-z0-9]+", re.IGNORECASE)
STOP_WORDS = {
    "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "does",
    "explain", "for", "from", "how", "in", "is", "it", "its", "mean", "means",
    "of", "on", "or", "the", "to", "under", "what", "when", "where", "which",
    "who", "why", "with", "you",
}
SEARCH_ALIASES = {
    "gst": ("goods", "services", "tax"),
    "filing": ("filed", "furnish", "furnished", "return", "returns"),
    "penalties": ("penalty", "fee", "fees"),
    "late": ("fee", "fees", "delay", "delayed"),
}
DEFINITION_QUESTION = re.compile(
    r"^\s*(?:what\s+(?:is|are|does)\s+|define\s+|meaning\s+of\s+)(.+?)\s*\??\s*$",
    re.IGNORECASE,
)
DOCUMENT_NUMBER = re.compile(r"\b\d{1,3}(?:/\d{1,3})?/\d{4}\b")
GST_SCOPE_QUESTION = re.compile(
    r"\bgst\b.*\b(?:outside|excluded|not covered|out of scope|outside purview)\b|"
    r"\b(?:outside|excluded|not covered|out of scope|outside purview)\b.*\bgst\b",
    re.IGNORECASE,
)


def _gst_scope_sources(records, limit):
    """Use the actual scope provisions for broad 'outside GST' questions."""
    matches = []
    for content, metadata, _, _ in records:
        title = (metadata.get("title") or metadata.get("filename") or "").lower()
        if "central goods and services tax act" in title:
            section = re.search(r"(?m)^\s*(?:7|9)\.\s*\(", content)
            schedule = re.search(r"SCHEDULE\s+III\s*\[See section 7\]", content, re.IGNORECASE)
            if section and re.search(r"alcoholic liquor for human consumption|petroleum crude|activities or transactions specified in Schedule III", content, re.IGNORECASE):
                matches.append((0, Document(page_content=content, metadata=metadata)))
            elif schedule:
                matches.append((2, Document(page_content=content, metadata=metadata)))
        elif "constitution of india" in title and re.search(r"\(12A\)\s*[“\"']?goods and services tax", content, re.IGNORECASE):
            matches.append((1, Document(page_content=content, metadata=metadata)))
        elif "central goods and services tax (amendment) act, 2018" in title and re.search(
            r"32\.\s+In Schedule III", content, re.IGNORECASE
        ):
            matches.append((3, Document(page_content=content, metadata=metadata)))
        elif "central goods and services tax (amendment) act, 2023" in title and re.search(
            r"4\.\s+In the principal Act,\s+in Schedule III", content, re.IGNORECASE
        ):
            matches.append((4, Document(page_content=content, metadata=metadata)))
        elif "notification 48/2023-central tax" in title and re.search(
            r"1st day\s+of\s+October,?\s+2023", content, re.IGNORECASE
        ):
            matches.append((5, Document(page_content=content, metadata=metadata)))
        elif "one hundred and first amendment" in title and re.search(r"\(12A\)\s*[“\"']?goods and services tax", content, re.IGNORECASE):
            matches.append((6, Document(page_content=content, metadata=metadata)))
    matches.sort(key=lambda item: item[0])
    return [document for _, document in matches[:limit]]


def _canonical_number(value):
    parts = value.split("/")
    return "/".join(str(int(part)) for part in parts[:-1]) + "/" + parts[-1]


def _terms(text):
    return [word.lower() for word in WORDS.findall(text) if len(word) > 1 and word.lower() not in STOP_WORDS]


def _target(question):
    match = DEFINITION_QUESTION.match(question)
    if not match:
        return ""
    target = re.sub(r"\s+(?:mean|stand\s+for)$", "", match.group(1), flags=re.IGNORECASE)
    target = re.split(r"\s+under\s+", target, maxsplit=1, flags=re.IGNORECASE)[0]
    target = re.sub(r"^(?:a|an|the)\s+", "", target, flags=re.IGNORECASE)
    return " ".join(_terms(target))


def _key(document):
    return (document.metadata.get("filename"), document.metadata.get("page"), document.page_content)


def _title_initialism(metadata):
    title = metadata.get("title") or metadata.get("filename", "").removesuffix(".pdf")
    words = [word.lower() for word in WORDS.findall(title) if word.lower() not in {"and", "the"}]
    return "".join(word[0] for word in words)


def retrieve_documents(vector_store, question, limit=10):
    """Prefer exact legal terms while retaining semantic results for broader questions.

    The collection is read on each query so newly indexed and removed documents are
    reflected immediately, including replacements that do not change the count.
    """
    terms = list(dict.fromkeys(_terms(question)))
    finance_act = re.search(r"\bfinance\s+act(?:\s+of)?\s*,?\s*(20\d{2})\b", question, re.IGNORECASE)
    named_section = re.search(r"\bsection\s+(\d{1,3}[a-z]?)\b", question, re.IGNORECASE)
    finance_section = (finance_act.group(1), named_section.group(1)) if finance_act and named_section else None
    cited_document = re.search(
        r"\b(notification|circular)(?:\s+no\.?)?\s+(\d{1,3}(?:/\d{1,3})?/\d{4})\b",
        question, re.IGNORECASE,
    )
    cited_number = _canonical_number(cited_document.group(2)) if cited_document else None
    cited_rate = bool(re.search(r"\brate\s+notification\b", question, re.IGNORECASE)
                      or re.search(r"\bcentral\s+tax\s*\(rate\)", question, re.IGNORECASE))
    cited_corrigendum = bool(re.search(r"\bcorrigendum\b", question, re.IGNORECASE))
    act_acronyms = set(terms) & {"bns", "bnss"}
    source_clause = re.search(r"\bunder\s+(?:the\s+)?(.+?)\s*\??$", question, re.IGNORECASE)
    source_terms = set(_terms(source_clause.group(1))) if source_clause else set()
    search_terms = list(dict.fromkeys(terms + [alias for term in terms for alias in SEARCH_ALIASES.get(term, ())]))
    semantic = vector_store.similarity_search_with_relevance_scores(
        question, k=20, score_threshold=0.35
    )
    if not terms:
        return [document for document, _ in semantic[:limit]]

    collection = vector_store._collection.get(include=["documents", "metadatas"])
    records = []
    frequencies = Counter()
    for content, metadata in zip(collection["documents"], collection["metadatas"]):
        text_terms = Counter(_terms(content))
        title_terms = set(_terms(metadata.get("title") or metadata.get("filename", "")))
        present = set(text_terms) | title_terms
        frequencies.update(present & set(search_terms))
        records.append((content, metadata, text_terms, title_terms))

    if GST_SCOPE_QUESTION.search(question) and not cited_document and not named_section:
        scope_sources = _gst_scope_sources(records, limit)
        if scope_sources:
            return scope_sources

    target = _target(question)
    exact_target = re.compile(r"\b" + r"\s+".join(map(re.escape, target.split())) + r"\b", re.IGNORECASE) if target else None
    lexical = []
    for content, metadata, text_terms, title_terms in records:
        score = 0.0
        for term in search_terms:
            if term not in text_terms and term not in title_terms:
                continue
            idf = math.log(1 + (len(records) + 1) / (frequencies[term] + 1))
            weight = 1 if term in terms else 0.6
            score += weight * idf * (min(text_terms[term], 3) + (2 if term in title_terms else 0))
        if finance_section:
            year, section = finance_section
            source_name = metadata.get("title") or metadata.get("filename", "")
            if ("finance" in _terms(source_name) and year in _terms(source_name)
                    and re.search(rf"(?m)^\s*{re.escape(section)}\.\s+", content, re.IGNORECASE)):
                score += 300
        if cited_document:
            source_name = metadata.get("title") or metadata.get("filename", "")
            source_lower = source_name.lower()
            source_numbers = {_canonical_number(value) for value in DOCUMENT_NUMBER.findall(source_name)}
            same_kind = cited_document.group(1).lower() in source_lower
            same_rate = cited_rate == ("rate notification" in source_lower or "(rate)" in source_lower)
            same_corrigendum = cited_corrigendum == ("corrigendum" in source_lower)
            if cited_number in source_numbers and same_kind and same_rate and same_corrigendum:
                score += 300
        if metadata.get("page") == 1 and any(
            _title_initialism(metadata).startswith(acronym) for acronym in act_acronyms
        ):
            score += 100
        if "late" in terms and ("filing" in terms or "penalties" in terms):
            if re.search(r"\blate\s+fees?\b", content, re.IGNORECASE) and re.search(
                r"\b(?:returns?|furnish(?:ed)?)\b", content, re.IGNORECASE
            ):
                score += 20
        has_target = bool(exact_target and exact_target.search(content))
        if target and len(target.split()) == 1 and 2 <= len(target) <= 6:
            if metadata.get("page") == 1 and target in _title_initialism(metadata):
                has_target = True
                score += 30
                title_words = set(_terms(metadata.get("title") or metadata.get("filename", "")))
                if "act" in title_words and "amendment" not in title_words:
                    score += 15
        if score <= 0:
            continue
        if has_target:
            score += 10
            # Prefer the Act's primary definition over incidental uses such as
            # "contingent contract is a contract" or "One Person Company means".
            if len(target.split()) == 1 and (not source_terms or source_terms <= title_terms) and (
                re.search(rf"[\"“]{re.escape(target)}[\"”]\s+means\b", content, re.IGNORECASE)
                or (target == "contract" and re.search(
                    r"\ban\s+agreement\s+enforceable\s+by\s+law\s+is\s+a\s+contract\b",
                    content, re.IGNORECASE,
                ))
            ):
                score += 200
            if len(target.split()) == 1 and re.search(
                rf"(?:\b{re.escape(target)}\b[\"'”’]?\s+(?:means|is|refers\s+to|stands\s+for)\b|"
                rf"\bis\s+(?:an?\s+)?{re.escape(target)}\b)",
                content,
                re.IGNORECASE,
            ):
                score += 60
            if re.search(
                exact_target.pattern + r"\s*(?:[-—–:]|stands\s+for\b|means\b|is\b)",
                content,
                re.IGNORECASE,
            ):
                score += 20
        lexical.append((score, has_target, Document(page_content=content, metadata=metadata)))
    lexical.sort(key=lambda item: item[0], reverse=True)

    # A definition question with a literal match must not be drowned out by
    # unrelated semantically similar tax or law passages.
    if target and any(item[1] for item in lexical):
        return [document for _, matched, document in lexical if matched][:limit]
    if target and len(target.split()) == 1 and target not in frequencies:
        return []

    ranked = {}
    best_lexical_score = lexical[0][0] if lexical else 1
    for position, (score, _, document) in enumerate(lexical[:20], 1):
        key = _key(document)
        ranked[key] = [1.5 / (60 + position) + 0.03 * score / best_lexical_score, document]
    for position, (document, _) in enumerate(semantic, 1):
        key = _key(document)
        if key in ranked:
            ranked[key][0] += 1 / (60 + position)
        else:
            ranked[key] = [1 / (60 + position), document]
    return [document for _, document in sorted(ranked.values(), key=lambda item: item[0], reverse=True)[:limit]]
