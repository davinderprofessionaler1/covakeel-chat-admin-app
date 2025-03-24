import os
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import threading
from langchain.schema import Document
import pytesseract
from pdf2image import convert_from_path, pdfinfo_from_path
import re
import unicodedata
import fitz
from lingua import Language, LanguageDetectorBuilder
from typing import Tuple

FOLDER = "./acts"
OCR_LANGS = "hin+eng"
OUTPUT_JSON = "processed_documents_acts.json"
PROGRESS_JSON = "processing_progress_acts.json"
MAX_WORKERS = 5
available_languages = [Language.HINDI, Language.ENGLISH]

# Thread-safe lock for JSON writing
json_lock = threading.Lock()


def detect_pdf_language(path):
    """Detect language of a PDF file using middle 3 pages."""

    text = ""

    try:
        # Get total number of pages first
        print(os.path.exists(path))
        info = pdfinfo_from_path(path)
        total_pages = int(info["Pages"])

        page_images = []

        if total_pages <= 3:
            # Convert all pages if total <= 3
            page_images = convert_from_path(path, dpi=300, thread_count=8)
        else:
            # Calculate middle 3 pages
            mid = total_pages // 2
            half_span = 1  # pages before and after mid, total = 3

            start_page = max(1, mid - half_span)
            end_page = min(total_pages, mid + half_span)

            # Adjust if at start or end (for PDFs with <3 pages near ends)
            if end_page - start_page + 1 < 3:
                if start_page == 1:
                    end_page = min(total_pages, start_page + 2)
                elif end_page == total_pages:
                    start_page = max(1, end_page - 2)

            page_images = convert_from_path(
                path, first_page=start_page, last_page=end_page, dpi=300, thread_count=8
            )

    except Exception as e:
        print(f"Failed to convert PDF {path}: {e}")
        return ""

    for page_image in page_images:
        text += pytesseract.image_to_string(page_image, lang=OCR_LANGS) + "\n"

    detector = LanguageDetectorBuilder.from_languages(*available_languages).build()
    languages = detector.detect_multiple_languages_of(text)
    isHindi = sum([True for lang in languages if lang.language == Language.HINDI]) > 0
    return "EN" if not isHindi else "HI"


def clean_text(text: str) -> str:
    """
    Cleans OCR‑extracted legal text by:
      1. Unicode normalizing
      2. Removing (cid:NN) artifacts
      3. Standardizing punctuation & quotes
      4. Fixing hyphen‑broken line‑breaks
      5. Rejoining mid‑sentence line‑breaks
      6. Removing Roman‑script gibberish tokens (no vowels, punctuation‑heavy)
      7. Collapsing very long repeated phrases
      8. Injecting section markers for top‑level clause numbers
      9. Stripping isolated‑script artifacts (Latin in Devanagari runs)
     10. Final gibberish‑by‑ratio filter
     11. Normalizing whitespace
    """
    # 1. Unicode normalize
    text = unicodedata.normalize("NFC", text)

    # 2. Remove (cid:NN) artifacts
    text = re.sub(r"\(cid:\d+\)", "", text)

    # 3. Normalize punctuation & quotes
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace(""", '"').replace(""", '"')
    text = text.replace("'", "'").replace("'", "'")

    # 4. Fix hyphenated line‑breaks
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # 5. Join broken lines mid‑sentence
    text = re.sub(r"(?<=[^\.\?!])\n+(?=[^\n])", " ", text)

    # 6. Remove Roman‑script "gibberish" tokens (no vowels)
    text = re.sub(
        r"\b(?!.*[aeiouAEIOU])[A-Za-z/.\'`\-]{2,}\b",
        "",
        text,
    )

    # 7. Collapse repeated phrases
    text = re.sub(r"(\b[A-Za-z ]{3,}\b)(?:\s+\1){2,}", r"\1", text)

    # 8. Inject section markers
    text = re.sub(r"^(\d+)\.\s+", r"[SEC_\1] ", text, flags=re.MULTILINE)

    # 9. Strip isolated Latin in Devanagari runs
    text = re.sub(r"(?<=[\u0900-\u097F])\s*[A-Za-z]+\s*(?=[\u0900-\u097F])", "", text)

    # 10. Final gibberish‑by‑ratio filter
    def keep_token(tok: str) -> bool:
        # must have at least half its chars alphanumeric
        alnum = sum(c.isalnum() for c in tok)
        return (alnum / len(tok)) >= 0.5

    tokens = text.split()
    text = " ".join(tok for tok in tokens if keep_token(tok))

    # 11. Normalize whitespace
    text = re.sub(r"\s{2,}", " ", text).strip()

    text = text.replace("jftLVªh laö Mhö ,yö&33004@99", "")
    return text


def ocr_pdf(path: str) -> str:
    """Convert scanned PDF pages to text using pytesseract."""
    text = ""
    try:
        page_images = convert_from_path(path, dpi=300, thread_count=8)
    except Exception as e:
        print(f"Failed to convert PDF {path}: {e}")
        return ""

    for page_image in page_images[:100]:  # Limit to first 100 pages
        text += pytesseract.image_to_string(page_image, lang=OCR_LANGS, nice=-18) + "\n"
    return text


def get_direct_text(pdf_path: str) -> str:
    text = ""
    try:
        # Method 1: PyMuPDF (fastest, good for most PDFs)
        print("Trying PyMuPDF extraction...")
        doc = fitz.open(pdf_path)
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text += page_text
            if page_num % 10 == 0:  # Log every 10 pages
                print(f"Processed {page_num + 1} pages...")
        doc.close()
        if len(text.strip()) > 100:  # If we got substantial text
            print(f"Successfully extracted {len(text)} characters using PyMuPDF")
            return text
        else:
            return ""
    except Exception as e:
        print(f"PyMuPDF failed for {pdf_path}: {e}")
        return ""


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, str]:
    """Extract text using multiple methods for better accuracy"""
    text_language = detect_pdf_language(pdf_path)
    if text_language == "EN":
        print(f"Detected English text in: {os.path.basename(pdf_path)}")
        text = get_direct_text(pdf_path)
        if text:
            return (text, "EN")
        print(f"PyMuPDF extraction failed for {pdf_path}, falling back to OCR")
        # Fallback to OCR if PyMuPDF extraction fails or gives insufficient text
        print("Using OCR for English text extraction...")
        text = ocr_pdf(pdf_path)
        if text:
            return (text, "EN")
    else:
        text = ocr_pdf(pdf_path)
        return (text, "HI")


def load_and_detect_language(pdf_path: str) -> list[Document]:
    text, language = extract_text_from_pdf(pdf_path)  # Unpack the tuple
    docs = [
        Document(
            page_content=clean_text(text),  # Pass only the text string
            metadata={
                "source": os.path.basename(pdf_path),
                "language": language,
            },
        )
    ]
    return docs


def document_to_dict(doc: Document) -> Dict[str, Any]:
    """Convert a Document object to a dictionary for JSON serialization."""
    return {"page_content": doc.page_content, "metadata": doc.metadata}


def load_existing_data() -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load existing processed documents and progress from JSON files."""
    documents = []
    progress = {
        "processed_files": set(),
        "failed_files": set(),
        "total_files": 0,
        "total_documents": 0,
        "start_time": None,
        "last_update": None,
    }

    # Load existing documents
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
                documents = json.load(f)
            print(f"Loaded {len(documents)} existing documents from {OUTPUT_JSON}")
        except Exception as e:
            print(f"Error loading existing documents: {e}")

    # Load progress
    if os.path.exists(PROGRESS_JSON):
        try:
            with open(PROGRESS_JSON, "r", encoding="utf-8") as f:
                saved_progress = json.load(f)
                progress["processed_files"] = set(
                    saved_progress.get("processed_files", [])
                )
                progress["failed_files"] = set(saved_progress.get("failed_files", []))
                progress["total_files"] = saved_progress.get("total_files", 0)
                progress["total_documents"] = saved_progress.get("total_documents", 0)
                progress["start_time"] = saved_progress.get("start_time")
                progress["last_update"] = saved_progress.get("last_update")
            print(
                f"Loaded progress: {len(progress['processed_files'])} processed files, {len(progress['failed_files'])} failed files"
            )
        except Exception as e:
            print(f"Error loading progress: {e}")

    return documents, progress


def save_progress(progress: Dict[str, Any]) -> None:
    """Save progress to JSON file."""
    progress_to_save = {
        "processed_files": list(progress["processed_files"]),
        "failed_files": list(progress["failed_files"]),
        "total_files": progress["total_files"],
        "total_documents": progress["total_documents"],
        "start_time": progress["start_time"],
        "last_update": progress["last_update"],
    }

    with json_lock:
        try:
            with open(PROGRESS_JSON, "w", encoding="utf-8") as f:
                json.dump(progress_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving progress: {e}")


def save_documents(documents: List[Dict[str, Any]]) -> None:
    """Save all documents to JSON file."""
    with json_lock:
        try:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving documents: {e}")


def process_single_file(
    args: tuple,
) -> tuple[str, Optional[List[Document]], Optional[str]]:
    """Process a single PDF file. Returns (filename, documents, error_message)."""
    filename, pdf_path = args

    try:
        print(f"Processing: {filename}")
        start_time = time.time()

        docs = load_and_detect_language(pdf_path)

        processing_time = time.time() - start_time
        print(
            f"✓ Completed {filename} in {processing_time:.2f}s - {len(docs)} documents"
        )

        return filename, docs, None

    except Exception as e:
        error_msg = f"Error processing {filename}: {str(e)}"
        print(f"✗ {error_msg}")
        return filename, None, error_msg


def get_pending_files(
    folder: str, processed_files: set, failed_files: set
) -> List[tuple]:
    """Get list of PDF files that haven't been processed yet."""
    all_files = []

    if not os.path.exists(folder):
        print(f"Folder {folder} does not exist!")
        return all_files

    for filename in os.listdir(folder):
        if not filename.lower().endswith(".pdf"):
            continue

        if filename in processed_files:
            continue

        # Optionally skip failed files (comment out if you want to retry them)
        # if filename in failed_files:
        #     continue

        pdf_path = os.path.join(folder, filename)
        all_files.append((filename, pdf_path))

    return all_files


def print_statistics(progress: Dict[str, Any]) -> None:
    """Print current processing statistics."""
    print("\n" + "=" * 60)
    print("PROCESSING STATISTICS")
    print("=" * 60)
    print(f"Total files found: {progress['total_files']}")
    print(f"Successfully processed: {len(progress['processed_files'])}")
    print(f"Failed: {len(progress['failed_files'])}")
    print(f"Total documents extracted: {progress['total_documents']}")

    if progress["start_time"]:
        elapsed = time.time() - progress["start_time"]
        print(f"Total elapsed time: {elapsed:.2f} seconds")

        if progress["total_documents"] > 0:
            rate = progress["total_documents"] / elapsed
            print(f"Processing rate: {rate:.2f} documents/second")

    print("=" * 60)


def main():
    """Main processing function with parallel execution and persistence."""
    print("Starting PDF processing with parallel execution...")

    # Load existing data and progress
    all_documents, progress = load_existing_data()

    # Get pending files
    pending_files = get_pending_files(
        FOLDER, progress["processed_files"], progress["failed_files"]
    )

    if not pending_files:
        print("No pending files to process!")
        print_statistics(progress)
        return

    print(f"Found {len(pending_files)} files to process")

    # Update progress
    progress["total_files"] = len(pending_files) + len(progress["processed_files"])
    if not progress["start_time"]:
        progress["start_time"] = time.time()

    # Process files in parallel
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_filename = {
            executor.submit(process_single_file, file_info): file_info[0]
            for file_info in pending_files
        }

        # Process completed tasks
        for future in as_completed(future_to_filename):
            filename, docs, error_msg = future.result()

            # Update progress
            progress["last_update"] = datetime.now().isoformat()

            if error_msg:
                progress["failed_files"].add(filename)
                print(f"Failed to process {filename}: {error_msg}")
            else:
                progress["processed_files"].add(filename)

                # Convert documents to dictionaries and add to collection
                if docs:
                    doc_dicts = [document_to_dict(doc) for doc in docs]
                    all_documents.extend(doc_dicts)
                    progress["total_documents"] += len(doc_dicts)

                print(
                    f"✓ Successfully processed {filename} - Total documents: {progress['total_documents']}"
                )

            # Save progress after each file
            save_progress(progress)

            # Save documents periodically (every 10 files) to avoid memory issues
            if len(progress["processed_files"]) % 10 == 0:
                save_documents(all_documents)
                print(f"Saved {len(all_documents)} documents to {OUTPUT_JSON}")

    # Final save
    save_documents(all_documents)
    save_progress(progress)

    print(f"\n🎉 Processing complete!")
    print(f"📄 Final output saved to: {OUTPUT_JSON}")
    print(f"📊 Progress saved to: {PROGRESS_JSON}")

    print_statistics(progress)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        print("Progress has been saved. You can resume by running the script again.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Progress has been saved. You can resume by running the script again.")
