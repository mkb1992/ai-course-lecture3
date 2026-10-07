from __future__ import annotations

from collections.abc import Iterator

from openai import OpenAI

from services.keys import huggingface_api_key
from services.prompts import llm_messages

HF_ROUTER = "https://router.huggingface.co/v1"
LLAMA_BASE_MODEL = "meta-llama/Llama-3.1-8B:featherless-ai"
LLAMA_INSTRUCT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
MAX_NEW_TOKENS = 512

MISSING_KEY = (
    "Hugging Face token was not found. For offline use, put it in HF_Key.txt. "
    "On Streamlit Cloud, add HF_TOKEN in Secrets."
)


def _client() -> OpenAI | None:
    key = huggingface_api_key()
    if not key:
        return None
    return OpenAI(base_url=HF_ROUTER, api_key=key)


def _served_model(event: object, fallback: str) -> str:
    return getattr(event, "model", None) or fallback


def stream_tokens(
    model_id: str,
    messages: list[dict[str, str]],
    *,
    document: str = "",
    kind: str = "instruct",
    topic: str = "",
    controls: dict[str, object] | None = None,
) -> Iterator[str]:
    client = _client()
    if client is None:
        yield MISSING_KEY
        return
    extras = dict(controls or {})
    max_tokens = int(extras.pop("max_tokens", MAX_NEW_TOKENS))
    prompt_kind = "llama_base" if kind == "base" else "llama_instruct"
    print(
        "[LLAMA REQUEST]",
        "topic=",
        topic or kind,
        "model=",
        model_id,
        "controls=",
        {"max_tokens": max_tokens, **extras},
    )
    served_logged = False
    yielded = False
    try:
        stream = client.chat.completions.create(
            model=model_id,
            messages=llm_messages(messages, document, kind=prompt_kind),
            max_tokens=max_tokens,
            stream=True,
            **extras,
        )
        for event in stream:
            if not served_logged:
                print("[LLAMA RESPONSE]", "served=", _served_model(event, model_id))
                served_logged = True
            if not event.choices:
                continue
            piece = event.choices[0].delta.content
            if piece:
                yielded = True
                yield piece
    except Exception as exc:
        yield f"Hugging Face could not answer with {model_id}: {exc}"
        return
    if not yielded:
        yield f"{model_id} returned an empty reply."


def chat(
    model_id: str,
    messages: list[dict[str, str]],
    *,
    document: str = "",
    kind: str = "instruct",
    topic: str = "",
    controls: dict[str, object] | None = None,
) -> str:
    return "".join(
        stream_tokens(
            model_id,
            messages,
            document=document,
            kind=kind,
            topic=topic,
            controls=controls,
        )
    )
