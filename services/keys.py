from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OPENAI_KEY_FILE = ROOT / "openAI API.txt"
HF_KEY_FILE = ROOT / "HF_Key.txt"
_FILE_KEY_NAMES = {
    "OPENAI_API_KEY",
    "HF_TOKEN",
    "HUGGINGFACE_API_KEY",
    "API_KEY",
}
SECRETS_FILES = (
    ROOT / ".streamlit" / "secrets.toml",
    Path.home() / ".streamlit" / "secrets.toml",
)


def _from_secrets(name: str) -> str:
    if not any(path.is_file() for path in SECRETS_FILES):
        return ""
    try:
        import streamlit as st

        value = st.secrets.get(name)
    except Exception:
        return ""
    if value is None:
        return ""
    return str(value).strip()


def _from_env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def _from_file(path: Path) -> str:
    if not path.is_file():
        return ""
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""
    for line in text.splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        if "=" in raw:
            left, right = raw.split("=", 1)
            name = left.strip().replace("-", "_").upper()
            if name in _FILE_KEY_NAMES or name.endswith("API_KEY"):
                raw = right.strip()
        return raw.strip().strip('"').strip("'")
    return text.strip().strip('"').strip("'")


def openai_api_key() -> str:
    return (
        _from_secrets("OPENAI_API_KEY")
        or _from_env("OPENAI_API_KEY")
        or _from_file(OPENAI_KEY_FILE)
    )


def anthropic_api_key() -> str:
    return _from_secrets("ANTHROPIC_API_KEY") or _from_env("ANTHROPIC_API_KEY")


def huggingface_api_key() -> str:
    return (
        _from_secrets("HF_TOKEN")
        or _from_secrets("HUGGINGFACE_API_KEY")
        or _from_env("HF_TOKEN")
        or _from_env("HUGGINGFACE_API_KEY")
        or _from_file(HF_KEY_FILE)
    )
