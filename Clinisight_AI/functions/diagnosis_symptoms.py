from functions.portkey_gateway import chat_completion


def get_diagnosis(description: str, symptoms: list[str] | None = None) -> str:
    """
    Get diagnosis based on the patient's description via the Portkey gateway,
    which routes across a fallback chain of hosted models so no local
    model download/install is required.
    """
    symptoms = symptoms or []
    keyword_hint = (
        f"\nRecognized symptom keywords: {', '.join(symptoms)}." if symptoms else ""
    )
    prompt = (
        f"Patient description: {description}{keyword_hint}\n"
        "Suggest possible medical diagnoses and a possible cure for the same."
    )
    return chat_completion(
        [
            {"role": "system", "content": "You are a helpful medical assistant."},
            {"role": "user", "content": prompt},
        ]
    )

if __name__=="__main__":
    output=get_diagnosis("I have a throbbing headache and a fever.", ["headache", "fever"])
    print(output)
