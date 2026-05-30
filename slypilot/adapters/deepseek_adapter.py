"""Single-provider DeepSeek adapter for SlyPilot V1."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib import error, request

from slypilot.task_packet_builder import BuiltPacket
from slypilot.utils.token_estimator import estimate_tokens


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    status: str
    response_text: str
    response_tokens: int
    model: str
    raw_payload: dict[str, object]


class DeepSeekAdapterError(RuntimeError):
    pass


def run_deepseek_live(packet: BuiltPacket) -> ProviderResponse:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekAdapterError("DEEPSEEK_API_KEY is required for live runs")

    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": packet.content,
            }
        ],
        "temperature": 0,
    }

    req = request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            raw_text = response.read().decode("utf-8")
    except error.URLError as exc:  # pragma: no cover - exercised through mock in tests
        raise DeepSeekAdapterError(f"DeepSeek live run failed: {exc}") from exc

    payload_data = json.loads(raw_text)
    response_text = _extract_response_text(payload_data)
    response_tokens = estimate_tokens(response_text)

    return ProviderResponse(
        provider="deepseek",
        status="completed",
        response_text=response_text,
        response_tokens=response_tokens,
        model=model,
        raw_payload=payload_data,
    )


def _extract_response_text(payload: dict[str, object]) -> str:
    choices = payload.get("choices", [])
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message", {})
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content
    return json.dumps(payload, ensure_ascii=False)
