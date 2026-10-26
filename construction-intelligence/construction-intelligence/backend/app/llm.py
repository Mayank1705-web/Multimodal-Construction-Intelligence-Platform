"""Multimodal LLM gateway: provider adapters plus strict JSON validation with one repair retry."""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from . import mock
from .config import get_settings
from .errors import AppError
from .images import PreparedImage
from .prompts import build_system

T = TypeVar("T", bound=BaseModel)


def extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start:end + 1])


# ------------------------------------------------------------ providers
def _anthropic_call(system: str, user_text: str, images: list[PreparedImage]) -> str:
    import anthropic

    s = get_settings()
    if not s.anthropic_api_key:
        raise AppError("llm_not_configured", "ANTHROPIC_API_KEY is not set.", 503)
    client = anthropic.Anthropic(api_key=s.anthropic_api_key, timeout=s.llm_timeout_seconds)
    content: list[dict[str, Any]] = [
        {"type": "image", "source": {"type": "base64", "media_type": im.media_type, "data": im.b64}} for im in images
    ]
    content.append({"type": "text", "text": user_text})
    resp = client.messages.create(model=s.anthropic_model, max_tokens=4096, system=system,
                                  messages=[{"role": "user", "content": content}])
    return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


def _bedrock_call(system: str, user_text: str, images: list[PreparedImage]) -> str:
    import boto3
    from botocore.config import Config

    s = get_settings()
    if not s.bedrock_model_id:
        raise AppError("llm_not_configured", "BEDROCK_MODEL_ID is not set.", 503)
    client = boto3.client("bedrock-runtime", region_name=s.aws_region,
                          config=Config(read_timeout=s.llm_timeout_seconds, retries={"max_attempts": 2}))
    content: list[dict[str, Any]] = [{"image": {"format": "jpeg", "source": {"bytes": im.data}}} for im in images]
    content.append({"text": user_text})
    resp = client.converse(modelId=s.bedrock_model_id, system=[{"text": system}],
                           messages=[{"role": "user", "content": content}],
                           inferenceConfig={"maxTokens": 4096, "temperature": 0.2})
    return "".join(p.get("text", "") for p in resp["output"]["message"]["content"])


async def _call_provider(system: str, user_text: str, images: list[PreparedImage]) -> str:
    provider = get_settings().llm_provider
    fn = {"anthropic": _anthropic_call, "bedrock": _bedrock_call}.get(provider)
    if fn is None:
        raise AppError("llm_not_configured", f"Unknown LLM_PROVIDER '{provider}'.", 503)
    try:
        return await asyncio.to_thread(fn, system, user_text, images)
    except AppError:
        raise
    except Exception as exc:  # network, auth, rate limit
        raise AppError("llm_unavailable", f"The AI service could not complete the request: {type(exc).__name__}.", 502) from exc


# ------------------------------------------------------------ public API
async def run_task(task: str, model: Type[T], user_text: str, images: list[PreparedImage],
                   mock_ctx: dict[str, Any]) -> tuple[T, str, int]:
    """Return (validated result, provider name, latency ms)."""
    settings = get_settings()
    provider = settings.llm_provider
    started = time.perf_counter()

    if provider == "mock":
        try:
            result = model.model_validate(mock.generate(task, mock_ctx))
        except ValidationError as exc:  # a bug in the mock, not user error
            raise AppError("internal_contract_error", f"Mock output failed validation: {exc.errors()[:1]}", 500) from exc
        return result, "mock", int((time.perf_counter() - started) * 1000)

    system = build_system(task, model)
    raw = await _call_provider(system, user_text, images)
    try:
        result = model.model_validate(extract_json(raw))
    except (ValueError, ValidationError) as first_error:
        repair = (f"{user_text}\n\nYour previous reply was rejected: {str(first_error)[:600]}\n"
                  "Return ONLY a corrected JSON object that follows the schema exactly.")
        raw = await _call_provider(system, repair, images)
        try:
            result = model.model_validate(extract_json(raw))
        except (ValueError, ValidationError) as exc:
            raise AppError("invalid_ai_response", "The AI returned a response that did not match the required format. Please try again.", 502) from exc
    return result, provider, int((time.perf_counter() - started) * 1000)
