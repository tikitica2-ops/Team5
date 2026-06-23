import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Fix for Python 3.14 compatibility with protobuf
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
sys.modules['google._upb._message'] = None

# Load environment variables from .env file
load_dotenv()

PUBLIC_DATA_PORTAL_KEY = os.getenv("PUBLIC_DATA_PORTAL_KEY")

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Data file paths
LAWS_DIR = DATA_DIR / "laws"
PROCEDURES_DIR = DATA_DIR / "procedures"
GLOSSARY_FILE = DATA_DIR / "glossary" / "glossary.json"
CASES_FILE = DATA_DIR / "cases" / "sample_cases.json"

# ChromaDB Collection names
COLLECTION_LAWS = "auction_laws"
COLLECTION_PROCEDURES = "auction_procedures"
COLLECTION_GLOSSARY = "auction_glossary"
COLLECTION_CASES = "auction_cases"

# LLM & Embedding provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()

# Model Names
OPENAI_LLM_MODEL = "gpt-4o-mini"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

ANTHROPIC_LLM_MODEL = "claude-3-5-sonnet-20240620"
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-1.5-flash")

HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "jhgan/ko-sroberta-multitask")

# Ensure necessary folders exist
DATA_DIR.mkdir(exist_ok=True)
LAWS_DIR.mkdir(parents=True, exist_ok=True)
PROCEDURES_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "glossary").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "cases").mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)
