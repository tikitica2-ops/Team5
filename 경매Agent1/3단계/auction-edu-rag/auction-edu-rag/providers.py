"""
providers.py

config 설정에 따라 LLM / 임베딩 객체를 생성해 돌려주는 팩토리.
ingest.py 와 이후 agents/ 가 공통으로 사용한다.
provider 전환은 config(.env)에서만 하면 되도록 분리.
"""

import config


def get_embeddings():
    """임베딩 객체 반환 (기본: OpenAI text-embedding-3-small)."""
    if config.EMBEDDING_PROVIDER == "openai":
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(model=config.EMBEDDING_MODEL)
    if config.EMBEDDING_PROVIDER == "huggingface":
        # 한국어 로컬 임베딩 옵션 (sentence-transformers 필요)
        from langchain_community.embeddings import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
    raise ValueError(f"지원하지 않는 EMBEDDING_PROVIDER: {config.EMBEDDING_PROVIDER}")


def get_llm():
    """채팅 LLM 객체 반환 (openai=gpt-4o-mini / anthropic=claude)."""
    if config.LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)
    if config.LLM_PROVIDER == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=config.LLM_MODEL, temperature=config.LLM_TEMPERATURE)
    raise ValueError(f"지원하지 않는 LLM_PROVIDER: {config.LLM_PROVIDER}")
