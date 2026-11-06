"""Export/import the local app's MongoDB records without changing their IDs.

Run from backend/: python tools/migrate_mongodb.py export|import FILE
The export contains private account and chat data; transfer it over SSH only.
"""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bson import json_util
from pymongo import MongoClient

from app.core.config import MONGODB_DB, MONGODB_URI

COLLECTIONS = ("users", "conversations", "messages", "sources")


def export_records(path: Path):
    with MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000) as client:
        db = client[MONGODB_DB]
        records = {name: list(db[name].find({})) for name in COLLECTIONS}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_util.dumps({"format": "covakeel-mongodb-v1", "collections": records}))
    path.chmod(0o600)
    print("Exported:", {name: len(docs) for name, docs in records.items()})


def import_records(path: Path):
    payload = json_util.loads(path.read_text())
    if payload.get("format") != "covakeel-mongodb-v1" or set(payload.get("collections", {})) != set(COLLECTIONS):
        raise SystemExit("Unsupported or incomplete MongoDB export")
    with MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000) as client:
        db = client[MONGODB_DB]
        if any(db[name].estimated_document_count() for name in COLLECTIONS):
            raise SystemExit("Destination collections must be empty before import")
        for name in COLLECTIONS:
            docs = payload["collections"][name]
            if docs:
                db[name].insert_many(docs, ordered=True)
        print("Imported:", {name: db[name].count_documents({}) for name in COLLECTIONS})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("export", "import"))
    parser.add_argument("file", type=Path)
    args = parser.parse_args()
    if args.operation == "export":
        export_records(args.file)
    else:
        import_records(args.file)


if __name__ == "__main__":
    main()
