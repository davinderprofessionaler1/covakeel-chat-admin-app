"""Load local configuration before database and authentication modules import it."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BACKEND_DIR / ".env")
os.environ.setdefault("HF_HOME", str(BACKEND_DIR.parent / ".local" / "huggingface"))
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "india_law_ai_rag_local")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("Set JWT_SECRET_KEY to a random value of at least 32 characters in backend/.env")

_chroma_path = Path(os.getenv("CHROMA_DB_PATH", "chroma_db"))
CHROMA_DB_PATH = _chroma_path if _chroma_path.is_absolute() else BACKEND_DIR / _chroma_path
ADMIN_UPLOAD_DIR = Path(os.getenv("ADMIN_UPLOAD_DIR", str(BACKEND_DIR.parent / ".local" / "admin-uploads")))
CORS_ORIGINS = [origin.strip() for origin in os.getenv(
    "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081"
).split(",") if origin.strip()]
