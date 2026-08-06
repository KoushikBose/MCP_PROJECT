import os

from dotenv import load_dotenv
from portkey_ai import Portkey

load_dotenv()

# Fallback chain: Portkey tries each target in order and moves to the next
# one only if the current model errors out or times out.
FALLBACK_CONFIG = {
    "strategy": {"mode": "fallback"},
    "targets": [
        {
            "provider": "ollama",
            "api_key": os.getenv("OLAMA_TOKEN", ""),
            "custom_host": "https://ollama.com",
            "override_params": {"model": "gpt-oss:20b-cloud"},
        },
        {
            "provider": "groq",
            "api_key": os.getenv("GROQ_API_KEY", ""),
            "override_params": {"model": "llama-3.3-70b-versatile"},
        },
        {
            "provider": "google",
            "api_key": os.getenv("GOOGLE_API_KEY", ""),
            "override_params": {"model": "gemini-2.0-flash"},
        },
        {
            "provider": "openai",
            "api_key": os.getenv("OPENAI_API_KEY", ""),
            "override_params": {"model": "gpt-4o-mini"},
        },
        {
            "provider": "anthropic",
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "override_params": {"model": "claude-haiku-4-5"},
        },
    ],
}

_client: Portkey | None = None


def _get_client() -> Portkey:
    global _client
    if _client is None:
        # A Portkey dashboard Config (PORTKEY_CONFIG_ID, e.g. "pc-...") takes
        # precedence over the in-code fallback chain when both are set, since
        # it's managed centrally in Portkey rather than redeployed with the app.
        config = os.getenv("PORTKEY_CONFIG_ID") or FALLBACK_CONFIG
        _client = Portkey(
            api_key=os.getenv("PORTKEY_API_KEY", ""),
            config=config,
        )
    return _client


def chat_completion(messages: list[dict], **kwargs) -> str:
    """
    Runs a chat completion through the Portkey gateway.

    Portkey walks the fallback chain in FALLBACK_CONFIG (Ollama Cloud ->
    Groq -> Gemini -> GPT-4o-mini -> Claude Haiku) and returns the first
    model's response that succeeds, so a single provider outage or rate
    limit doesn't take the whole app down.
    """
    response = _get_client().chat.completions.create(messages=messages, **kwargs)
    content = response.choices[0].message.content
    return content.strip() if content else ""
