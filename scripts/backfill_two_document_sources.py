#!/usr/bin/env python3
"""Attach verified official source PDFs to two older admin uploads.

Matches the exact PDF fingerprint so a later replacement with the same filename
cannot accidentally inherit an unrelated source link. Safe to run repeatedly.
"""

import os

from pymongo import MongoClient


SOURCES = (
    (
        "Central_Goods_and_Services_Tax_Amendment_Act_2018.pdf",
        "7372bf7a26a0049698c6f2dc29d0b4ead2140ebdb03524f4efd8d8663402e11b",
        "https://www.gstcouncil.gov.in/sites/default/files/2024-03/annexure-3_cgst-amendment-act_2018.pdf",
    ),
    (
        "Income_Tax_Department_ITR_Definition_Searchable_Excerpt.pdf",
        "0a2b7a7a101efa4dfff3fa7a9a7de12a5473afe9059c42e9844375504097bc32",
        "https://www.incometax.gov.in/iec/foportal/sites/default/files/2022-07/ABC%20of%20Tax.pdf",
    ),
)


def main():
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017"))
    documents = client[os.getenv("MONGODB_DB", "india_law_ai_rag_local")].admin_documents
    for filename, sha256, source_url in SOURCES:
        identity = {"filename": filename, "sha256": sha256, "status": "indexed"}
        document = documents.find_one(identity, {"source_url": 1})
        if document is None:
            raise SystemExit(f"Indexed PDF not found: {filename}")
        existing_url = document.get("source_url")
        if existing_url and existing_url != source_url:
            raise SystemExit(f"Different source link already set: {filename}")
        documents.update_one(identity, {"$set": {"source_url": source_url}})
        print(f"Linked: {filename}")
    client.close()


if __name__ == "__main__":
    main()
