"""
중앙 설정 파일 (config.py)

- LLM 제공자(OpenAI / Anthropic)와 모델, 임베딩, ChromaDB 컬렉션, 데이터 경로를
  한곳에서 관리합니다.
- LLM_PROVIDER 값만 바꾸면 GPT <-> Claude 전환이 됩니다.
- 실제 키는 코드에 적지 말고 .env 파일(.env.example 참고)에 넣으세요.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- 경로 ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = str(BASE_DIR / "chroma_db")

# --- LLM 설정 ------------------------------------------------------------
# "openai" 또는 "anthropic" 중 선택 (.env의 LLM_PROVIDER로도 제어 가능)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

_LLM_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}
LLM_MODEL = os.getenv("LLM_MODEL", _LLM_MODELS[LLM_PROVIDER])

# 법률 도메인이라 환각을 줄이기 위해 낮게 설정
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# --- 임베딩 설정 ---------------------------------------------------------
# 기본: OpenAI text-embedding-3-small (가장 간단)
# 한국어 로컬 모델로 교체하려면 .env에:
#   EMBEDDING_PROVIDER=huggingface
#   EMBEDDING_MODEL=jhgan/ko-sroberta-multitask
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")

_EMBEDDING_MODELS = {
    "openai": "text-embedding-3-small",
    "huggingface": "jhgan/ko-sroberta-multitask",
}
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", _EMBEDDING_MODELS[EMBEDDING_PROVIDER])

# --- ChromaDB 컬렉션 -----------------------------------------------------
# 라우팅 정확도를 위해 지식베이스를 4개 컬렉션으로 분리
COLLECTIONS = {
    "laws": "auction_laws",            # 법령 조문
    "procedures": "auction_procedures",  # 절차 해설
    "glossary": "auction_glossary",    # 용어집
    "cases": "auction_cases",          # 가상 사례
}

# --- 청킹 파라미터 (clause-aware) ----------------------------------------
# 법령은 "## 제○○조" 단위로 끊고, 너무 긴 조문만 아래 크기로 추가 분할
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# --- 검색 파라미터 -------------------------------------------------------
TOP_K = int(os.getenv("TOP_K", "4"))  # 검색 시 가져올 청크 수
