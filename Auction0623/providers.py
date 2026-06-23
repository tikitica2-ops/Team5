import os
import streamlit as st
import config

def get_llm(temperature=0.0):
    """
    Returns an LLM instance based on configuration.
    """
    # Try to load keys from streamlit secrets first (useful for deployment)
    openai_key = None
    anthropic_key = None
    google_key = None
    try:
        if hasattr(st, "secrets"):
            openai_key = st.secrets.get("OPENAI_API_KEY")
            anthropic_key = st.secrets.get("ANTHROPIC_API_KEY")
            google_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not openai_key:
        openai_key = os.getenv("OPENAI_API_KEY")
    if not anthropic_key:
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not google_key:
        google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if config.LLM_PROVIDER == "openai":
        if not openai_key:
            raise ValueError("OpenAI API Key is missing. Please set OPENAI_API_KEY in .env file or Streamlit Secrets.")
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            openai_api_key=openai_key,
            model=config.OPENAI_LLM_MODEL,
            temperature=temperature
        )
    elif config.LLM_PROVIDER == "anthropic":
        if not anthropic_key:
            raise ValueError("Anthropic API Key is missing. Please set ANTHROPIC_API_KEY in .env file or Streamlit Secrets.")
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            anthropic_api_key=anthropic_key,
            model=config.ANTHROPIC_LLM_MODEL,
            temperature=temperature
        )
    elif config.LLM_PROVIDER in ["gemini", "google"]:
        if not google_key:
            raise ValueError("Google Gemini API Key is missing. Please set GOOGLE_API_KEY or GEMINI_API_KEY in .env file or Streamlit Secrets.")
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=google_key,
            model=config.GEMINI_LLM_MODEL,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")

def get_embedding_model():
    """
    Returns an Embedding model instance based on configuration.
    """
    # Try to load keys from streamlit secrets first (useful for deployment)
    openai_key = None
    try:
        if hasattr(st, "secrets"):
            openai_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    if not openai_key:
        openai_key = os.getenv("OPENAI_API_KEY")

    if config.EMBEDDING_PROVIDER == "openai":
        if not openai_key:
            raise ValueError("OpenAI API Key is missing. Please set OPENAI_API_KEY in .env file or Streamlit Secrets to use OpenAI Embeddings.")
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            openai_api_key=openai_key,
            model=config.OPENAI_EMBEDDING_MODEL
        )
    elif config.EMBEDDING_PROVIDER == "huggingface":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        # Load local HuggingFace embedding model
        return HuggingFaceEmbeddings(
            model_name=config.HF_EMBEDDING_MODEL
        )
    else:
        raise ValueError(f"Unknown Embedding provider: {config.EMBEDDING_PROVIDER}")

def get_gemini_llm(temperature=0.2):
    """
    Returns a Gemini LLM instance specifically for the Auction Diary feature.
    If the key is missing, falls back to the default LLM provider.
    """
    google_key = None
    try:
        if hasattr(st, "secrets"):
            google_key = st.secrets.get("GOOGLE_API_KEY") or st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not google_key:
        google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")

    if not google_key:
        # Fallback to default LLM to prevent error if key is missing during demo
        return get_llm(temperature=temperature)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            google_api_key=google_key,
            model=config.GEMINI_LLM_MODEL,
            temperature=temperature
        )
    except Exception:
        # Fallback in case of import or initialization error
        return get_llm(temperature=temperature)
