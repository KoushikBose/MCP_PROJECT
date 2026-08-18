from functions.guardrails import guarded_chat_completion


def summarize_text(text: str) -> str:
    """
    Get a summary of the provided medical text via the Portkey gateway,
    which routes across a fallback chain of hosted models so no local
    model download/install is required. `text` originates from third-party
    PubMed/web content, so the NeMo Guardrails input rail (see
    functions/guardrails.py) screens it for prompt-injection payloads
    before it's sent to the model, and the output rail screens the summary
    before it's returned.
    """
    prompt = f"Summarize The Following Medical Abstract :\n\n{text}"
    return guarded_chat_completion(
        [
            {"role": "system", "content": "You are a Medical Summarizer."},
            {"role": "user", "content": prompt},
        ]
    )
