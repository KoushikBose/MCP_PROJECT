from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from functions.symptom_extractor import extract_symptoms
from functions.diagnosis_symptoms import get_diagnosis
from functions.pubmed_articles import fetch_pubmed_articles_with_metadata
from functions.summarizer_pubmed import summarize_text
from functions.web_search import fetch_web_results
from functions.cache_store import cache_stats, clear_cache, get_cached, set_cached
from functions.guardrails import GuardrailBlocked

app=FastAPI()


class SymtomInput(BaseModel):
    description :str
    force_refresh: bool = False

@app.get("/")
def root():
    return {"status": "ok", "message": "ClinInsight AI is running. See /docs for the API."}

@app.post("/diagnosis")
def diagnosis(data:SymtomInput):
    symptom = extract_symptoms(data.description)
    symptom_key = sorted(symptom)
    cache_hits = {
        "diagnosis": False,
        "pubmed_sources": False,
        "pubmed_summary": False,
        "web_sources": False,
    }

    diagnosis_result = None if data.force_refresh else get_cached("diagnosis", symptom_key, data.description)
    if diagnosis_result is not None:
        cache_hits["diagnosis"] = True
    else:
        try:
            diagnosis_result = get_diagnosis(data.description, symptom)
        except GuardrailBlocked as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_cached("diagnosis", symptom_key, data.description, value=diagnosis_result)

    pubmed_query = " ".join(symptom)
    pubmed_article = None if data.force_refresh else get_cached("pubmed_sources", pubmed_query)
    if pubmed_article is not None:
        cache_hits["pubmed_sources"] = True
    else:
        pubmed_article = fetch_pubmed_articles_with_metadata(pubmed_query)
        set_cached("pubmed_sources", pubmed_query, value=pubmed_article)

    abstracts_text = "\n\n".join(article["abstract"] for article in pubmed_article)[:3000]
    summary = None if data.force_refresh else get_cached("pubmed_summary", abstracts_text)
    if summary is not None:
        cache_hits["pubmed_summary"] = True
    else:
        try:
            summary = summarize_text(abstracts_text)
        except GuardrailBlocked as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        set_cached("pubmed_summary", abstracts_text, value=summary)

    web_query = data.description
    web_results = None if data.force_refresh else get_cached("web_sources", web_query)
    if web_results is not None:
        cache_hits["web_sources"] = True
    else:
        web_results = fetch_web_results(web_query)
        set_cached("web_sources", web_query, value=web_results)

    return {
        "symptom":symptom,
        "diagnosis":diagnosis_result,
        "pubmed_summary" :summary,
        "sources": pubmed_article,
        "web_sources": web_results,
        "cache": cache_hits,
    }


@app.post("/cache/clear")
def cache_clear():
    removed = clear_cache()
    return {"status": "ok", "removed": removed}


@app.get("/cache/stats")
def cache_stat_endpoint():
    return cache_stats()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host = "0.0.0.0", port=8081, reload = True)

