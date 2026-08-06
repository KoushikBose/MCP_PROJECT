from functions.portkey_gateway import chat_completion


def summarize_text(text: str) -> str:
    """
    Get a summary of the provided medical text via the Portkey gateway,
    which routes across a fallback chain of hosted models so no local
    model download/install is required.
    """
    prompt = f"Summarize The Following Medical Abstract :\n\n{text}"
    return chat_completion(
        [
            {"role": "system", "content": "You are a Medical Summarizer."},
            {"role": "user", "content": prompt},
        ]
    )
