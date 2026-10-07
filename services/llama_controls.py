from __future__ import annotations

from services.openai_controls import OUTPUT_LENGTHS

DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.6
DEFAULT_TOP_P = 0.9
DEFAULT_FREQUENCY_PENALTY = 0.0


def clamp_temperature(value: float) -> float:
    return min(2.0, max(0.0, float(value)))


def clamp_top_p(value: float) -> float:
    return min(1.0, max(0.0, float(value)))


def clamp_frequency_penalty(value: float) -> float:
    return min(2.0, max(-2.0, float(value)))


def request_params(
    *,
    control_mode: str | None = None,
    output_length: str | None = None,
    temperature: float | None = None,
    top_p: float | None = None,
    frequency_penalty: float | None = None,
) -> dict[str, object]:
    extras: dict[str, object] = {}
    if (control_mode or "Auto") != "Manual":
        extras["max_tokens"] = DEFAULT_MAX_TOKENS
        return extras
    limit = OUTPUT_LENGTHS.get(str(output_length or ""), None)
    extras["max_tokens"] = DEFAULT_MAX_TOKENS if limit is None else limit
    if temperature is not None:
        extras["temperature"] = clamp_temperature(temperature)
    if top_p is not None:
        extras["top_p"] = clamp_top_p(top_p)
    if frequency_penalty is not None:
        extras["frequency_penalty"] = clamp_frequency_penalty(frequency_penalty)
    return extras
