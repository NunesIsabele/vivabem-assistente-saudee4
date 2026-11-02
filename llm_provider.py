"""Conexão com a API Gemini, sem busca automática na web."""

import os
from pathlib import Path

from google import genai
from google.genai import types

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"


def _load_local_env():
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        os.environ.setdefault(name.strip(), value.strip().strip("\"'"))


def _get_api_key():
    _load_local_env()
    key = os.getenv("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def generate_response(question: str, instructions: str) -> str:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", DEFAULT_MODEL),
        contents=question,
        config=types.GenerateContentConfig(system_instruction=instructions),
    )
    return response.text or "Não consegui gerar uma resposta agora. Tente novamente."
