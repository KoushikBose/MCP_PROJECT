import re

SYMPTOMS = [
    # general / constitutional
    "fever", "chills", "night sweats", "sweating", "fatigue", "malaise",
    "weakness", "dehydration", "weight loss", "weight gain", "loss of appetite",

    # neurological
    "headache", "migraine", "dizziness", "lightheadedness", "fainting",
    "confusion", "memory loss", "numbness", "tingling", "seizures", "tremors",
    "blurred vision", "double vision", "loss of taste", "loss of smell",
    "sensitivity to light", "sensitivity to sound", "slurred speech",
    "difficulty speaking",

    # pain
    "chest pain", "chest tightness", "abdominal pain", "stomach pain",
    "stomach ache", "abdominal cramps", "back pain", "neck pain",
    "joint pain", "muscle pain", "muscle aches", "muscle weakness",
    "body aches", "body ache", "ear pain", "eye pain", "throat pain",
    "pelvic pain", "cramps", "stiffness", "pain",

    # respiratory
    "shortness of breath", "difficulty breathing", "wheezing", "dry cough",
    "cough", "sore throat", "runny nose", "stuffy nose", "nasal congestion",
    "sneezing", "congestion",

    # cardiovascular
    "palpitations", "irregular heartbeat", "high blood pressure",
    "low blood pressure",

    # gastrointestinal
    "nausea", "vomiting", "diarrhea", "constipation", "bloating",
    "indigestion", "heartburn", "blood in stool",

    # musculoskeletal / skin
    "swelling", "rash", "itching", "hives", "dry skin", "bruising", "redness",

    # mental health
    "anxiety", "depression", "insomnia", "irritability", "mood swings",
]

# Longer/multi-word phrases must be tried before their shorter substrings
# (e.g. "chest pain" before "pain") so regex alternation matches the more
# specific phrase first instead of stopping at the shorter one.
_SORTED_SYMPTOMS = sorted(SYMPTOMS, key=len, reverse=True)
_SYMPTOM_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in _SORTED_SYMPTOMS) + r")\b"
)


def extract_symptoms(text:str):
    """
    Extracts symptoms from the given text using regular expressions.
    """
    symptoms=_SYMPTOM_PATTERN.findall(text.lower())
    return list(set(symptoms))

if __name__=="__main__":
    text="I Am Having Back Pain and Having Fever Too"
    symptoms=extract_symptoms(text)
    print(symptoms)