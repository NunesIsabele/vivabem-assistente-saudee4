"""Carrega a chave local e envia perguntas à API Gemini."""

import os
from pathlib import Path

from google import genai
from google.genai import types


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.5-flash-lite"


def _load_local_env() -> None:
    """Lê variáveis simples de um .env sem substituir as já definidas no sistema."""
    env_file = PROJECT_DIR / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip()
        value = value.strip().strip("\"'")
        if name:
            os.environ.setdefault(name, value)


def _get_api_key() -> str | None:
    """Lê a chave localmente ou dos segredos do Streamlit Cloud."""
    _load_local_env()
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key

    try:
        import streamlit as st

        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _generate(question: str, instructions: str, use_search: bool):
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError(
            "não encontrei GEMINI_API_KEY. No uso local, confira o arquivo .env; "
            "no Streamlit Community Cloud, configure a chave em Secrets."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    client = genai.Client(api_key=api_key)
    config_options = {"system_instruction": instructions}
    if use_search:
        config_options["tools"] = [
            types.Tool(google_search=types.GoogleSearch())
        ]

    response = client.models.generate_content(
        model=model,
        contents=question,
        config=types.GenerateContentConfig(**config_options),
    )
    if not response.text:
        return "Não consegui gerar uma resposta agora. Tente novamente.", []

    sources = []
    if use_search and response.candidates:
        metadata = getattr(response.candidates[0], "grounding_metadata", None)
        for chunk in getattr(metadata, "grounding_chunks", None) or []:
            web_source = getattr(chunk, "web", None)
            uri = getattr(web_source, "uri", None)
            title = getattr(web_source, "title", None)
            if uri and not any(source["url"] == uri for source in sources):
                sources.append({"title": title or "Fonte consultada", "url": uri})

    return response.text, sources


def generate_response(question: str, instructions: str) -> str:
    """Envia a pergunta ao Gemini sem busca na web."""
    answer, _ = _generate(question, instructions, use_search=False)
    return answer


def generate_response_with_sources(question: str, instructions: str):
    """Envia a pergunta com busca opcional e retorna referências da API."""
    return _generate(question, instructions, use_search=True)
