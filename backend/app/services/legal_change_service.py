"""Source-reviewed, date-scoped legal changes used for deterministic comparisons."""

from datetime import date, datetime, timedelta
import re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from langchain_core.documents import Document

from app.db.mongodb import get_db


CURRENT_OR_COMPARISON = re.compile(
    r"\b(?:current|currently|latest|today|now|pehla|pehle|hun|ajj|"
    r"changed?|amend(?:ed|ment)?|before|after|earlier|effective|in force|"
    r"lagu|badleya|farak)\b", re.IGNORECASE,
)


def india_today() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def official_url(value: str) -> bool:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and (
        host.endswith(".gov.in") or host.endswith(".nic.in")
        or host in {"gov.in", "nic.in"}
    ) and not parsed.username and not parsed.password


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


def change_key(law_keyword: str, provision: str) -> str:
    return _normalize(law_keyword) + "::" + _normalize(provision)


def matches_question(record: dict, question: str) -> bool:
    """Require both an exact law keyword and provision; never guess from a year."""
    q = _normalize(question)
    law = _normalize(record["law_keyword"])
    provision = _normalize(record["provision"])
    return bool(
        law and provision
        and re.search(rf"(?<!\w){re.escape(law)}(?!\w)", q)
        and re.search(rf"(?<!\w){re.escape(provision)}(?!\w)", q)
    )


def public_change(record: dict) -> dict:
    return {
        "id": str(record["_id"]),
        **{key: record[key] for key in (
            "law_keyword", "provision", "before_text", "after_text",
            "before_from", "effective_from", "verified_through",
            "before_source_url", "after_source_url", "commencement_source_url",
        )},
        "verified_by": record.get("verified_by", ""),
        "created_at": record["created_at"].isoformat(),
    }


async def list_changes() -> list[dict]:
    cursor = get_db().legal_changes.find({}).sort("created_at", -1)
    return [public_change(record) async for record in cursor]


async def find_change(question: str) -> dict | None:
    # This collection is deliberately small and curated, unlike the document index.
    async for record in get_db().legal_changes.find({}):
        if matches_question(record, question):
            return record
    return None


def comparison_answer(record: dict, question: str, today: date | None = None) -> dict:
    today = today or india_today()
    before_end = (date.fromisoformat(record["effective_from"]) - timedelta(days=1)).isoformat()
    verified = date.fromisoformat(record["verified_through"])
    current = verified >= today
    later_label = "Current verified position" if current else "Later verified position"
    status = (
        f"Verified as of {verified.isoformat()}."
        if current else
        f"Verified only through {verified.isoformat()}; changes after that date have not been checked."
    )
    answer = (
        f"**Direct answer — {record['law_keyword']} {record['provision']}**\n"
        f"The reviewed record shows an earlier and a later position. "
        f"The later position took effect on {record['effective_from']} [3].\n\n"
        f"**Earlier position ({record['before_from']} to {before_end})**\n"
        f"{record['before_text']} [1]\n\n"
        f"**{later_label} (effective {record['effective_from']})**\n"
        f"{record['after_text']} [2]\n\n"
        f"**How the dates apply**\n"
        f"The earlier position is recorded for {record['before_from']} through {before_end} [1]. "
        f"The later position is recorded from {record['effective_from']} through "
        f"{verified.isoformat()} [2, 3].\n\n"
        f"**Verification limit**\n{status} This comparison uses the admin-reviewed record "
        f"and its linked official sources."
    )
    source_specs = (
        ("Before version", record["before_source_url"], record["before_text"]),
        ("Later version", record["after_source_url"], record["after_text"]),
        ("Commencement evidence", record["commencement_source_url"],
         f"Effective from {record['effective_from']}."),
    )
    sources = [Document(page_content=summary, metadata={
        "citation_id": str(number), "title": f"{record['law_keyword']} {record['provision']} — {label}",
        "filename": urlparse(url).path.rsplit("/", 1)[-1] or "Official source",
        "source_url": url, "source_type": "reviewed legal change",
    }) for number, (label, url, summary) in enumerate(source_specs, 1)]
    return {"question": question, "answer": answer, "source_documents": sources}


def unverified_answer(question: str) -> dict:
    return {
        "question": question,
        "answer": "I could not verify the earlier and current legal position from a reviewed amendment record. Please check the relevant Act, amendment and commencement notification in the official sources.",
        "source_documents": [],
    }
