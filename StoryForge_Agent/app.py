import re

import streamlit as st

from core import (
    HF_TOKEN,
    MODEL_INFO,
    MODEL_SCRIPT,
    STYLES,
    TAVILY_API_KEY,
    build_source_text,
    fetch_search_results,
    generate_script,
    summarize,
)

TOPICS = ["General", "News", "Finance"]
TIME_RANGES = ["Any time", "Day", "Week", "Month", "Year"]
EXAMPLE_TOPICS = ["AI trends 2026", "Climate policy", "Space exploration", "Stock market today"]

st.set_page_config(
    page_title="StoryForge Agent",
    page_icon=":material/travel_explore:",
    layout="centered",
)


if not HF_TOKEN or not TAVILY_API_KEY:
    st.title(":material/travel_explore: StoryForge Agent", text_alignment="center")
    st.error(
        "Missing API credentials. Set `HF_TOKEN` and `TAVILY_API_KEY` in your `.env` file before running the app.",
        icon=":material/error:",
    )
    st.stop()

st.session_state.setdefault("query", "")
st.session_state.setdefault("history", [])
st.session_state.setdefault("results", {})
st.session_state.setdefault("scripts", {})
st.session_state.setdefault("current_query", None)
st.session_state.setdefault("trigger_search", False)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_") or "topic"


def use_example(topic: str) -> None:
    st.session_state.query = topic
    st.session_state.trigger_search = True


def load_history_query(query: str) -> None:
    st.session_state.current_query = query


def clear_history() -> None:
    st.session_state.history = []
    st.session_state.results = {}
    st.session_state.scripts = {}
    st.session_state.current_query = None


with st.sidebar:
    st.markdown("#### :material/tune: Search settings")
    topic = st.segmented_control("Focus", TOPICS, default="General", required=True, key="topic")
    max_results = st.slider("Sources to fetch", 3, 10, 5, key="max_results")
    time_range = st.selectbox("Time range", TIME_RANGES, key="time_range")
    style = st.segmented_control("Summary style", list(STYLES), default="Balanced", required=True, key="style")

    st.markdown("#### :material/history: Recent searches")
    if not st.session_state.history:
        st.caption("Your recent searches will appear here.")
    else:
        for past_query in st.session_state.history[:8]:
            st.button(
                past_query,
                key=f"hist_{past_query}",
                on_click=load_history_query,
                args=(past_query,),
                width="stretch",
            )
        st.button("Clear history", icon=":material/delete:", on_click=clear_history, width="stretch")

    st.caption(f"Summaries by {MODEL_INFO.split('/')[-1]} · Scripts by {MODEL_SCRIPT.split('/')[-1]}")

st.title(":material/travel_explore: StoryForge Agent", text_alignment="center")
st.caption(
    "Search any topic and get an AI-powered summary, source links, and a ready-to-post video script.",
    text_alignment="center",
)

st.text_input(
    "Search topic",
    key="query",
    placeholder="e.g. AI trends 2026, climate policy, space exploration",
    icon=":material/search:",
    label_visibility="collapsed",
)

with st.container(horizontal=True):
    for example in EXAMPLE_TOPICS:
        st.button(example, key=f"ex_{example}", on_click=use_example, args=(example,))

search_clicked = st.button("Search", type="primary", icon=":material/search:", width="stretch")
run_search = search_clicked or st.session_state.pop("trigger_search", False)
query = st.session_state.query.strip()

if run_search and not query:
    st.warning("Enter a topic to search.", icon=":material/warning:")
elif run_search and query:
    summary = None
    with st.status(f"Researching '{query}'...", expanded=True) as status:
        st.write("Searching the web...")
        results = fetch_search_results(query, topic, max_results, time_range)
        source_text = build_source_text(results, query)

        st.write("Writing summary...")
        try:
            summary = summarize(query, source_text, style)
        except Exception as e:
            summary = None
            st.error(f"Error generating summary: {e}", icon=":material/error:")

        status.update(
            label="Research ready" if summary else "Something went wrong",
            state="complete" if summary else "error",
        )

    if summary:
        st.session_state.results[query] = {"results": results, "summary": summary}
        if query in st.session_state.history:
            st.session_state.history.remove(query)
        st.session_state.history.insert(0, query)
        st.session_state.current_query = query
        st.toast("Research ready", icon=":material/check_circle:")

current = st.session_state.current_query
if current and current in st.session_state.results:
    data = st.session_state.results[current]
    summary = data["summary"]
    results = data["results"]
    word_count = len(summary.split())
    read_time = max(1, round(word_count / 200))

    st.subheader(current)
    st.caption(f"{word_count} words · ~{read_time} min read · {len(results)} sources")

    tab_summary, tab_sources, tab_script = st.tabs(
        [
            ":material/description: Summary",
            f":material/link: Sources ({len(results)})",
            ":material/movie: Video script",
        ],
        key="result_tabs",
    )

    with tab_summary:
        st.write(summary)
        st.download_button(
            "Download summary",
            data=summary,
            file_name=f"{slugify(current)}_summary.txt",
            icon=":material/download:",
        )

    with tab_sources:
        if results:
            for r in results:
                with st.container(border=True):
                    st.markdown(f"**[{r.get('title') or 'Untitled'}]({r.get('url') or ''})**")
                    st.caption(r.get("content") or "")
        else:
            st.caption("No sources were returned for this search.")

    with tab_script:
        script = st.session_state.scripts.get(current)
        button_label = "Regenerate script" if script else "Generate script"
        if st.button(button_label, icon=":material/movie:"):
            with st.spinner("Crafting your video script..."):
                try:
                    new_script = generate_script(summary)
                except Exception as e:
                    new_script = None
                    st.error(f"Error generating video script: {e}", icon=":material/error:")
            if new_script:
                st.session_state.scripts[current] = new_script

        script = st.session_state.scripts.get(current)
        if script:
            st.write(script)
            st.download_button(
                "Download script",
                data=script,
                file_name=f"{slugify(current)}_script.txt",
                icon=":material/download:",
            )
        else:
            st.caption("Generate a short-form video script from this summary.")
else:
    st.caption("Try a topic above to get started.")

st.caption("Made with :material/favorite:", text_alignment="center")
