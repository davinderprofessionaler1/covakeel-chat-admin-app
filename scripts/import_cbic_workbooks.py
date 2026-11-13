#!/usr/bin/env python3
"""Import the CBIC links in the supplied notification/circular XLSX files locally.

The import is resumable: already indexed source URLs are skipped. Each result is
appended to a JSONL report so failures can be inspected without losing progress.
"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("HF_HOME", str(ROOT / ".local" / "huggingface"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from app.db.mongodb import get_db, mongodb  # noqa: E402
from app.services import admin_service, pdf_url_import  # noqa: E402


MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
SHEET_PATTERN = re.compile(r"xl/worksheets/sheet\d+\.xml$")
CELL_ROW = re.compile(r"^[A-Z]+(\d+)$")


def read_workbook(path: Path):
    """Extract label, date, and linked CBIC URL without changing the workbook."""
    with ZipFile(path) as book:
        strings = []
        if "xl/sharedStrings.xml" in book.namelist():
            root = ET.fromstring(book.read("xl/sharedStrings.xml"))
            strings = ["".join(t.text or "" for t in item.iter(MAIN + "t"))
                       for item in root.iter(MAIN + "si")]
        for sheet_file in sorted(name for name in book.namelist() if SHEET_PATTERN.fullmatch(name)):
            rel_file = sheet_file.replace("worksheets/", "worksheets/_rels/") + ".rels"
            relationships = {}
            if rel_file in book.namelist():
                relationships = {item.attrib["Id"]: item.attrib.get("Target", "")
                                 for item in ET.fromstring(book.read(rel_file))}
            root = ET.fromstring(book.read(sheet_file))
            values = {}
            for cell in root.iter(MAIN + "c"):
                value = cell.find(MAIN + "v")
                inline = cell.find(MAIN + "is")
                if value is not None:
                    raw = value.text or ""
                    values[cell.attrib["r"]] = strings[int(raw)] if cell.attrib.get("t") == "s" else raw
                elif inline is not None:
                    values[cell.attrib["r"]] = "".join(t.text or "" for t in inline.iter(MAIN + "t"))
            heading = values.get("A1", "")
            if "Circular" in heading:
                prefix = "CGST Circular"
            elif "(Rate)" in heading:
                prefix = "CGST Rate Notification"
            elif "Notification" in heading:
                prefix = "CGST Notification"
            else:
                raise ValueError(f"Unrecognized sheet heading in {path.name}: {heading}")
            for link in root.iter(MAIN + "hyperlink"):
                coordinate = link.attrib.get("ref", "")
                match = CELL_ROW.fullmatch(coordinate)
                if not match or not coordinate.startswith("C"):
                    continue
                row = match.group(1)
                url = relationships.get(link.attrib.get(REL + "id", ""), "").strip()
                number = values.get("A" + row, "").strip()
                if not url or not number:
                    continue
                raw_date = values.get("B" + row, "")
                try:
                    date = (datetime(1899, 12, 30) + timedelta(days=float(raw_date))).strftime("%d %b %Y")
                except (TypeError, ValueError, OverflowError):
                    date = ""
                title = f"{prefix} {number}" + (f" — {date}" if date else "")
                yield {"url": url, "title": title, "workbook": path.name,
                       "sheet": heading, "row": int(row)}


async def import_entries(entries, report_path: Path, limit: int | None, retry_failed: bool):
    db = get_db()
    await db.command("ping")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    totals = {"indexed": 0, "already_indexed": 0, "duplicate_pdf": 0, "failed": 0}
    consecutive_download_errors = 0
    latest = {}
    if report_path.exists():
        for line in report_path.read_text(encoding="utf-8").splitlines():
            try:
                previous = json.loads(line)
            except json.JSONDecodeError:
                continue
            if previous.get("url"):
                latest[previous["url"]] = previous.get("status")
    handled = {url for url, status in latest.items()
               if status in {"indexed", "indexed_alternative", "indexed_ocr",
                             "already_indexed", "duplicate_pdf"}
               or (status == "failed" and not retry_failed)}
    pending = [entry for entry in entries if entry["url"] not in handled]
    if limit:
        pending = pending[:limit]
    print(f"Already checked {len(handled)} links; {len(pending)} left for this run", flush=True)
    with report_path.open("a", encoding="utf-8") as report:
        for position, entry in enumerate(pending, 1):
            result = {**entry, "checked_at": datetime.now(timezone.utc).isoformat()}
            try:
                url, filename = pdf_url_import.parse_pdf_url(entry["url"])
                existing = await db.admin_documents.find_one({"source_url": url, "status": "indexed"})
                if existing:
                    result.update(status="already_indexed", filename=existing["filename"],
                                  pages=existing.get("pages", 0), chunks=existing.get("chunks", 0))
                else:
                    filename, data = await pdf_url_import.download_pdf(url)
                    consecutive_download_errors = 0
                    try:
                        queued = await admin_service.queue_upload(filename, data, entry["title"], url)
                    except ValueError as exc:
                        if "already in the knowledge base" not in str(exc):
                            raise
                        result.update(status="duplicate_pdf", filename=filename, error=str(exc))
                    else:
                        await admin_service.process_upload(queued["id"])
                        document = await db.admin_documents.find_one({"_id": queued["id"]})
                        if document["status"] == "indexed":
                            result.update(status="indexed", filename=filename,
                                          pages=document["pages"], chunks=document["chunks"])
                            await db.admin_documents.update_many(
                                {"filename": filename, "status": "failed", "_id": {"$ne": queued["id"]}},
                                {"$set": {"status": "replaced", "updatedAt": datetime.utcnow()}},
                            )
                        else:
                            result.update(status="failed", filename=filename,
                                          error=document.get("error", "Indexing failed"))
            except Exception as exc:
                result.update(status="failed", error=str(exc)[:300])
                if isinstance(exc, ValueError) and ("download" in str(exc).lower() or "timed out" in str(exc).lower()):
                    consecutive_download_errors += 1
                else:
                    consecutive_download_errors = 0
            totals[result["status"]] += 1
            report.write(json.dumps(result, ensure_ascii=False) + "\n")
            report.flush()
            if position % 10 == 0 or result["status"] == "failed":
                print(f"{position}/{len(pending)}: {result['status']} "
                      f"{entry['title']}" + (f" ({result['error']})" if result.get("error") else ""), flush=True)
            if consecutive_download_errors >= 10:
                print("Stopping after 10 consecutive download errors; rerun to resume.", flush=True)
                break
    print("RESULT", json.dumps(totals), "REPORT", report_path, flush=True)
    if mongodb.client is not None:
        mongodb.client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbooks", nargs="+", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--report", type=Path, default=ROOT / ".local" / "imports" / "cbic-workbooks.jsonl")
    args = parser.parse_args()
    entries = list(dict((item["url"], item) for path in args.workbooks for item in read_workbook(path)).values())
    print(f"Found {len(entries)} unique linked documents in {len(args.workbooks)} workbooks", flush=True)
    if args.dry_run:
        for item in entries[:5]:
            print(json.dumps(item, ensure_ascii=False), flush=True)
        return
    asyncio.run(import_entries(entries, args.report, args.limit, args.retry_failed))


if __name__ == "__main__":
    main()
