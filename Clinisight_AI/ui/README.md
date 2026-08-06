# ClinInsight AI — dashboard

A Streamlit front end for the ClinInsight AI FastAPI backend (`../app.py`). It is a
standalone client: it talks to the backend over HTTP and can be run, deployed, or
iterated on independently of the API.

## Features

- **Symptom intake form** — free-text description plus quick-add pills for the
  symptom keywords the backend's extractor recognizes, and a severity selector.
- **Live backend status** in the sidebar, with the API base URL configurable at
  runtime (defaults to `http://localhost:8081`, overridable via the
  `CLINISIGHT_API_BASE` environment variable).
- **Staged analysis status** while the request runs (extraction → diagnosis →
  literature search → summarization).
- **Tabbed results** — AI diagnosis overview with detected-symptom badges,
  a literature review tab with per-article cards (title, authors, date, abstract,
  PubMed link), a plain-language summary, and a downloadable Markdown report.
- **Session history** in the sidebar — revisit any past analysis from this
  session, plus a symptom-frequency chart across your queries.
- Cached API calls (`st.cache_data`) so re-submitting the same description
  doesn't re-run the LLM/PubMed pipeline unnecessarily.

## Running it

From the project root (the shared `.venv` already has `streamlit` installed):

```bash
uv run streamlit run ui/streamlit_app.py
```

Or with the venv directly:

```bash
.venv/Scripts/streamlit run ui/streamlit_app.py
```

Make sure the backend is running first:

```bash
uv run uvicorn app:app --host 0.0.0.0 --port 8081
```

The dashboard opens at `http://localhost:8501`.

## Notes

- The backend's symptom extractor is regex-based and only recognizes a fixed
  vocabulary (headache, fever, nausea, fatigue, pain, dizziness, vomiting,
  shortness of breath) — the quick-add pills mirror that list so results stay
  predictable.
- This is an informational tool, not a diagnostic device; the disclaimer in
  the app and in generated reports should stay intact.
