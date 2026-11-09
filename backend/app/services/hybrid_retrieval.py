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
