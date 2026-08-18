"""
Security guardrails around every LLM call, powered by NVIDIA NeMo
Guardrails (see guardrails/config.yml and guardrails/prompts.yml), checked
with an NVIDIA-hosted model (NVIDIA_API_KEY, see .env.example).

The "self check input" rail screens free-text going INTO the diagnosis/
summarizer model (patient descriptions, PubMed/web content being
summarized) for jailbreak and prompt-injection attempts. The "self check
output" rail screens completions coming OUT of that model before they reach
a caller. Both functions.diagnosis_symptoms and functions.summarizer_pubmed
call into this module, so the same policy applies consistently across the
FastAPI backend (app.py) and the MCP tool (mcp_tool.py).

If the guardrails check itself fails unexpectedly (e.g. the NVIDIA endpoint
is unreachable), we fail OPEN and let the request through rather than
taking the whole app down over a moderation-service outage -- see the
try/except in _run_rail below.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from nemoguardrails import LLMRails, RailsConfig

from functions.portkey_gateway import chat_completion

load_dotenv()

log = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "guardrails"

# Exact refusal text emitted by the "self check input"/"self check output"
# flows (bundled with nemoguardrails) when a rail blocks.
_REFUSAL_MESSAGE = "I'm sorry, I can't respond to that."


class GuardrailBlocked(Exception):
    """Raised when a NeMo Guardrails input/output rail refuses a request."""


_rails: Optional[LLMRails] = None


def _get_rails() -> LLMRails:
    global _rails
    if _rails is None:
        config = RailsConfig.from_path(str(_CONFIG_DIR))
        _rails = LLMRails(config)
    return _rails


def _extract_content(response: Any) -> str:
    """
    rails.generate(..., options=...) returns a GenerationResponse object
    whose `.response` is a list of message dicts (rather than a plain
    message dict, which is what's returned when no options are passed).
    """
    if hasattr(response, "response"):
        response = response.response
    if isinstance(response, list) and response:
        response = response[-1]
    if isinstance(response, dict):
        return str(response.get("content", ""))
    return str(response)


def _rail_blocked(messages: list[dict], rails_options: dict) -> bool:
    """
    Runs the given messages through NeMo Guardrails with only the specified
    rail enabled and reports whether that rail refused the content.

    Fails OPEN (returns False / "not blocked") if the check itself errors
    out, e.g. the NVIDIA endpoint is unreachable -- a guardrails outage
    should degrade the safety check, not take down diagnosis/summarization.
    """
    try:
        rails = _get_rails()
        response = rails.generate(messages=messages, options={"rails": rails_options})
        return _extract_content(response).strip() == _REFUSAL_MESSAGE
    except Exception:
        log.exception("NeMo Guardrails check failed; allowing request through (fail-open).")
        return False


def check_input(user_text: str, *, block_message: str | None = None) -> None:
    """
    Runs the 'self check input' rail against free text about to be sent to
    an LLM (a patient description, or third-party PubMed/web content about
    to be summarized). Raises GuardrailBlocked if the rail judges it to be a
    jailbreak/prompt-injection attempt or a request for unsafe content.
    """
    if not user_text or not user_text.strip():
        return

    blocked = _rail_blocked(
        [{"role": "user", "content": user_text}],
        {"input": True, "output": False, "dialog": False},
    )
    if blocked:
        raise GuardrailBlocked(
            block_message
            or "Your request was blocked by the safety guardrails. Please "
            "rephrase without instructions directed at the assistant "
            "itself."
        )


def check_output(user_text: str, bot_text: str) -> str:
    """
    Runs the 'self check output' rail against a generated response before
    it is returned to a caller. Raises GuardrailBlocked if the rail judges
    the response unsafe to show. Returns bot_text unchanged when it passes.
    """
    if not bot_text or not bot_text.strip():
        return bot_text

    blocked = _rail_blocked(
        [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": bot_text},
        ],
        {"input": False, "output": True, "dialog": False},
    )
    if blocked:
        raise GuardrailBlocked(
            "The generated response was blocked by the safety guardrails."
        )
    return bot_text


def guarded_chat_completion(messages: list[dict], **kwargs) -> str:
    """
    Drop-in, rails-wrapped replacement for
    functions.portkey_gateway.chat_completion: runs the input rail on the
    latest user message, performs the real completion, then runs the
    output rail on the result.
    """
    user_text = next(
        (m["content"] for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    check_input(user_text)
    bot_text = chat_completion(messages, **kwargs)
    return check_output(user_text, bot_text)
