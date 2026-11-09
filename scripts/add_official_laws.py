#!/usr/bin/env python3
"""Add the four verified official law PDFs without rebuilding the existing index.

PDFs must already be downloaded into .local/official_law/ using the URLs below.
This script is idempotent and updates the local manifest after each document.
"""

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("HF_HOME", str(ROOT / ".local" / "huggingface"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import fitz
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import CHROMA_DB_PATH

SOURCES = {
    "Bharatiya_Nyaya_Sanhita_2023.pdf": (
        "The Bharatiya Nyaya Sanhita, 2023",
        "https://www.mha.gov.in/files/documents/250883_english01042024.pdf",
    ),
    "Bharatiya_Nagarik_Suraksha_Sanhita_2023.pdf": (
        "The Bharatiya Nagarik Suraksha Sanhita, 2023",
        "https://www.mha.gov.in/files/documents/250884_2english_01042024.pdf",
    ),
    "Indian_Contract_Act_1872.pdf": (
        "The Indian Contract Act, 1872",
        "https://www.cag.gov.in/uploads/media/Indian-Contract-Act-1872-20200816140128.pdf",
    ),
    "Companies_Act_2013.pdf": (
        "The Companies Act, 2013",
        "https://www.nclt.gov.in/sites/default/files/Act%26rules/the_companies_act_2013_0.pdf",
    ),
}


def main():
    pdf_dir = ROOT / ".local" / "official_law"
    missing = [name for name in SOURCES if not (pdf_dir / name).is_file()]
    if missing:
        raise SystemExit(f"Missing PDFs: {', '.join(missing)}")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    store = Chroma(
        collection_name="indian_law_acts",
        persist_directory=str(CHROMA_DB_PATH),
        embedding_function=embeddings,
    )
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    manifest_path = CHROMA_DB_PATH / "local_manifest.json"
    manifest = json.loads(manifest_path.read_text())

    for filename, (title, url) in SOURCES.items():
        path = pdf_dir / filename
        data = path.read_bytes()
        if len(data) > 20_000_000 or not data.startswith(b"%PDF"):
            raise SystemExit(f"Invalid PDF or over 20 MB: {filename}")
        fingerprint = hashlib.sha256(data).hexdigest()
        if store._collection.get(where={"sha256": fingerprint}, include=[])["ids"]:
            print(f"Already indexed: {filename}", flush=True)
            continue

        pages = []
        with fitz.open(path) as pdf:
            for page_number, page in enumerate(pdf, 1):
                content = page.get_text().strip()
                if content:
                    pages.append(Document(page_content=content, metadata={
                        "filename": filename,
                        "title": title,
                        "source": url,
                        "source_url": url,
                        "page": page_number,
                        "language": "EN",
                        "sha256": fingerprint,
                    }))
        if not pages:
            raise SystemExit(f"No selectable text in {filename}")
        chunks = splitter.split_documents(pages)
        print(f"Indexing {filename}: {len(chunks)} chunks", flush=True)
        for start in range(0, len(chunks), 100):
            batch = chunks[start:start + 100]
            store.add_documents(
                batch,
                ids=[f"official:{fingerprint}:{i}" for i in range(start, start + len(batch))],
            )

        manifest["sources"] = [
            source for source in manifest["sources"] if source.get("filename") != filename
        ]
        manifest["sources"].append({
            "filename": filename,
            "title": title,
            "source": url,
            "sha256": fingerprint,
            "pages": len(pages),
            "chunks": len(chunks),
        })
        manifest["indexed_chunks"] = store._collection.count()
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(f"Indexed {filename}; total chunks: {manifest['indexed_chunks']}", flush=True)


if __name__ == "__main__":
    main()
