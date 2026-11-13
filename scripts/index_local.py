#!/usr/bin/env python3
"""Build/rebuild a local Chroma corpus from PDFs, without Claude calls.

Usage: backend/.venv/bin/python scripts/index_local.py [--pdf-dir PATH]
Without --pdf-dir, downloads the official RTI and CGST Act PDFs for a starter corpus.
The starter corpus is not a complete or verified-current Indian law collection.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("HF_HOME", str(ROOT / ".local" / "huggingface"))
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from app.core.config import CHROMA_DB_PATH
import fitz
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

OFFICIAL_SOURCES = {
    "Right_to_Information_Act_2005.pdf": "https://cic.gov.in/sites/default/files/RTI_English.pdf",
    "Central_Goods_and_Services_Tax_Act_2017.pdf": "https://www.gstcouncil.gov.in/sites/default/files/2024-04/annexure-3_cgst-act_2017.pdf",
    "CGST_Extension_to_Jammu_and_Kashmir_Act_2017.pdf": "https://www.gstcouncil.gov.in/sites/default/files/2024-03/annexure-3_cgst-extension-to-jammu-and-kashmir-act_2017.pdf",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf-dir", type=Path, help="Index all text-based PDFs in this directory")
    args = parser.parse_args()
    pdf_dir = args.pdf_dir or ROOT / ".local" / "corpus"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    sample = args.pdf_dir is None
    if sample:
        for filename, url in OFFICIAL_SOURCES.items():
            path = pdf_dir / filename
            if not path.exists():
                print(f"Downloading {filename}...", flush=True)
                req = urllib.request.Request(url, headers={"User-Agent": "IndiaLawAI-local-setup/1.0"})
                with urllib.request.urlopen(req, timeout=90) as response:
                    data = response.read(20_000_001)
                if len(data) > 20_000_000 or not data.startswith(b"%PDF"):
                    raise SystemExit(f"{filename} was not a valid PDF under 20 MB.")
                path.write_bytes(data)
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=500)
    documents, ids, sources = [], [], []
    for path in sorted(pdf_dir.glob("*.pdf")):
        fingerprint = hashlib.sha256(path.read_bytes()).hexdigest()
        pages = []
        with fitz.open(path) as pdf:
            for page_num, page in enumerate(pdf, 1):
                text = page.get_text().strip()
                if text:
                    pages.append(Document(page_content=text, metadata={
                        "filename": path.name,
                        "source": OFFICIAL_SOURCES.get(path.name, path.name) if sample else path.name,
                        "page": page_num, "language": "EN", "sha256": fingerprint,
                    }))
        chunks = splitter.split_documents(pages)
        if not chunks:
            raise SystemExit(f"{path.name} has no extractable text; use the OCR pipeline first.")
        documents.extend(chunks)
        ids.extend(f"{fingerprint}:{i}" for i in range(len(chunks)))
        sources.append({"filename": path.name, "source": OFFICIAL_SOURCES.get(path.name, path.name) if sample else path.name,
                        "sha256": fingerprint, "pages": len(pages), "chunks": len(chunks)})
    if not documents:
        raise SystemExit(f"No PDFs found in {pdf_dir}")
    print(f"Embedding {len(documents)} chunks from {len(sources)} PDF(s)...", flush=True)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"}, encode_kwargs={"normalize_embeddings": True},
    )
    store = Chroma(collection_name="indian_law_acts", persist_directory=str(CHROMA_DB_PATH),
                   embedding_function=embeddings, collection_metadata={"hnsw:space": "cosine"})
    for start in range(0, len(documents), 100):
        store.add_documents(documents[start:start + 100], ids=ids[start:start + 100])
    results = store.similarity_search("right to information request", k=3)
    manifest = {"starter_corpus": sample, "sources": sources,
                "indexed_chunks": store._collection.count(), "retrieval_results": len(results)}
    (CHROMA_DB_PATH / "local_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
