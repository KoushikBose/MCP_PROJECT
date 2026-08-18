from mcp.server.fastmcp import FastMCP
from functions.symptom_extractor import extract_symptoms
from functions.diagnosis_symptoms import get_diagnosis
from functions.summarizer_pubmed import summarize_text
from functions.pubmed_articles import fetch_pubmed_articles_with_metadata
from functions.web_search import fetch_web_results
from functions.cache_store import get_cached, set_cached
from functions.guardrails import GuardrailBlocked


mcp=FastMCP("Clinisight Ai")


@mcp.tool("diagnosis")
async def clinisight_ai(symptom_text: str):
    """
    Extracts symptoms from patient text, gets a possible diagnosis,
    and summarizes relevant PubMed research.
    Results are cached on disk (shared with the FastAPI backend) so
    repeat symptom sets skip the Ollama calls entirely.
    """
    symptom=extract_symptoms(symptom_text)
    symptom_key = sorted(symptom)

    diagnosis_result = get_cached("diagnosis", symptom_key, symptom_text)
    if diagnosis_result is None:
        try:
            diagnosis_result = get_diagnosis(symptom_text, symptom)
        except GuardrailBlocked as exc:
            return {"error": str(exc)}
        set_cached("diagnosis", symptom_key, symptom_text, value=diagnosis_result)

    pubmed_query = " ".join(symptom)
    pubmed_article = get_cached("pubmed_sources", pubmed_query)
    if pubmed_article is None:
        pubmed_article = fetch_pubmed_articles_with_metadata(pubmed_query)
        set_cached("pubmed_sources", pubmed_query, value=pubmed_article)

    abstracts_text = "\n\n".join(article["abstract"] for article in pubmed_article)[:4000]
    summary = get_cached("pubmed_summary", abstracts_text)
    if summary is None:
        try:
            summary = summarize_text(abstracts_text)
        except GuardrailBlocked as exc:
            return {"error": str(exc)}
        set_cached("pubmed_summary", abstracts_text, value=summary)

    web_results = get_cached("web_sources", symptom_text)
    if web_results is None:
        web_results = fetch_web_results(symptom_text)
        set_cached("web_sources", symptom_text, value=web_results)

    return{
        "symptom":symptom,
        "diagnosis":diagnosis_result,
        "pubmed_summary":summary,
        "web_sources":web_results
    }

if __name__=="__main__":
    mcp.run(transport='stdio')

