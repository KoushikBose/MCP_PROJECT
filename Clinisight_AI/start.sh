#!/usr/bin/env bash
# Default container entrypoint: runs the FastAPI backend internally and the
# Streamlit UI as the public-facing process on Render's $PORT (Render exposes
# only one port per web service, so the UI has to be what's reachable).
set -euo pipefail

uvicorn app:app --host 0.0.0.0 --port 8081 --workers 2 &
API_PID=$!

streamlit run ui/streamlit_app.py \
    --server.port="${PORT:-8501}" \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false &
UI_PID=$!

wait -n "$API_PID" "$UI_PID"
