from __future__ import annotations

from dataclasses import dataclass

OUTPUT_LENGTHS: dict[str, int | None] = {
    "Auto": None,
    "10": 10,
    "100": 100,
    "0.5K": 500,
    "1K": 1000,
    "4K": 4000,
    "8K": 8000,
    "16K": 16000,
}
OUTPUT_LENGTH_HINTS = {
    "Auto": "Model decides",
    "10": "~10",
    "100": "~100",
    "0.5K": "~500",
    "1K": "~1K",
    "4K": "~4K",
    "8K": "~8K",
    "16K": "~16K",
}
DEFAULT_OUTPUT_LENGTH = "Auto"
DEFAULT_REASONING = "Auto"
DEFAULT_VERBOSITY = "Auto"

VERBOSITY_OPTIONS = ["Auto", "Low", "Medium", "High"]
TEMPERATURE_STEPS = [round(i / 10, 1) for i in range(0, 21)]

REASONING_GPT52 = ["Auto", "None", "Low", "Medium", "High", "XHigh"]
REASONING_GPT56 = ["Auto", "None", "Low", "Medium", "High", "XHigh", "Max"]


@dataclass(frozen=True)
class ModelControls:
    max_tokens: bool = True
    reasoning: tuple[str, ...] | None = None
    verbosity: bool = False
    temperature: str | None = None
    disabled: bool = False


_RANGE = "range"
_WHEN_NONE = "reasoning_none"

_CHAT = ModelControls(temperature=_RANGE)
_GPT52 = ModelControls(
    reasoning=tuple(REASONING_GPT52),
    verbosity=True,
    temperature=_WHEN_NONE,
)
_GPT56 = ModelControls(reasoning=tuple(REASONING_GPT56), verbosity=True)

REGISTRY: dict[str, ModelControls] = {
    "GPT-4o Mini": _CHAT,
    "GPT-4.1": _CHAT,
    "GPT-5.2": _GPT52,
    "GPT-5.6 Sol": _GPT56,
}


def spec_for(model: str | None) -> ModelControls:
    if not model:
        return ModelControls(max_tokens=False, disabled=True)
    return REGISTRY.get(
        model,
        ModelControls(max_tokens=False, disabled=True),
    )


def temperature_key(value: float) -> str:
    return str(int(round(value * 10)))


def parse_temperature(label: str) -> float | None:
    if label == "Auto":
        return None
    try:
        return min(2.0, max(0.0, float(label)))
    except ValueError:
        return None


def temperature_allowed(spec: ModelControls, reasoning: str | None) -> bool:
    if spec.disabled or spec.temperature is None:
        return False
    if spec.temperature == _RANGE:
        return True
    return spec.temperature == _WHEN_NONE and reasoning == "None"


def request_params(
    model: str | None,
    *,
    output_length: str | None = None,
    reasoning: str | None = None,
    verbosity: str | None = None,
    temperature: float | None = None,
) -> dict[str, object]:
    spec = spec_for(model)
    extras: dict[str, object] = {}
    if spec.disabled:
        return extras
    if spec.max_tokens:
        label = str(output_length) if output_length is not None else ""
        limit = OUTPUT_LENGTHS.get(label, None)
        if limit is not None:
            extras["max_completion_tokens"] = limit
    if spec.reasoning and reasoning and reasoning != "Auto" and reasoning in spec.reasoning:
        extras["reasoning_effort"] = reasoning.lower()
    if spec.verbosity and verbosity and verbosity != "Auto" and verbosity in VERBOSITY_OPTIONS:
        extras["verbosity"] = verbosity.lower()
    if temperature_allowed(spec, reasoning) and temperature is not None:
        extras["temperature"] = float(temperature)
    return extras
