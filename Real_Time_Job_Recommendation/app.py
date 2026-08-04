import os
from datetime import datetime

import pandas as pd
import streamlit as st

from src.helper import extract_text_from_pdf, ask_openai
from src.job_api import fetch_linkedin_jobs, fetch_naukri_jobs, fetch_indeed_jobs

st.set_page_config(
    page_title="AI Job Recommender",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# Cached wrappers — avoid re-calling OpenAI / Apify on every Streamlit rerun
# --------------------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def cached_ask_openai(prompt: str, max_tokens: int = 500) -> str:
    return ask_openai(prompt, max_tokens=max_tokens)


@st.cache_data(show_spinner=False, ttl=1800)
def cached_fetch_jobs(platform: str, keywords: str, location: str, rows: int):
    if platform == "LinkedIn":
        jobs = fetch_linkedin_jobs(keywords, location=location, rows=rows) or []
    elif platform == "Indeed":
        jobs = fetch_indeed_jobs(keywords, location=location, rows=rows) or []
    else:
        jobs = fetch_naukri_jobs(keywords, location=location, rows=rows) or []
    return jobs


# Different scraper actors use different field names for a company's logo, so
# try the common variants in order and take the first usable URL.
_LOGO_KEYS = (
    "companyLogo",
    "companyLogoUrl",
    "logoUrl",
    "logo",
    "company_logo",
    "companyImage",
    "employerLogo",
    "orgLogo",
    "logoPathV3",
    "logoPath",
)


def extract_logo_url(job: dict) -> str | None:
    for key in _LOGO_KEYS:
        value = job.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    return None


_PLATFORM_BADGE_COLORS = {
    "LinkedIn": "blue",
    "Naukri": "orange",
    "Indeed": "violet",
}


# --------------------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------------------

_DEFAULTS = {
    "file_id": None,
    "resume_text": None,
    "summary": None,
    "gaps": None,
    "roadmap": None,
    "keywords": None,
    "analyzed": False,
    "jobs": [],
    "jobs_fetched": False,
    "analyzed_at": None,
}
for key, value in _DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset_analysis():
    for key, value in _DEFAULTS.items():
        st.session_state[key] = value


# --------------------------------------------------------------------------------------
# Sidebar — inputs & search preferences
# --------------------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Setup")

    missing_keys = []
    if not os.getenv("OPENAI_API_KEY"):
        missing_keys.append("OPENAI_API_KEY")
    if not os.getenv("APIFY_API_TOKEN"):
        missing_keys.append("APIFY_API_TOKEN")
    if missing_keys:
        st.error(f"Missing environment variable(s): {', '.join(missing_keys)}. Add them to your .env file.")

    uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

    st.divider()
    with st.expander("🔍 Job search preferences", expanded=True):
        location = st.selectbox(
            "Preferred location",
            ["India", "Remote", "United States", "United Kingdom", "Global"],
            index=0,
        )
        rows = st.slider("Jobs to fetch per platform", min_value=10, max_value=100, value=30, step=10)
        platforms = st.multiselect(
            "Platforms",
            ["LinkedIn", "Naukri", "Indeed"],
            default=["LinkedIn", "Naukri", "Indeed"],
        )
        custom_keywords = st.text_input(
            "Override search keywords (optional)",
            placeholder="e.g. Senior Data Scientist, NLP",
        )

    st.divider()
    analyze_clicked = st.button(
        "🚀 Analyze Resume",
        type="primary",
        width="stretch",
        disabled=uploaded_file is None or bool(missing_keys),
    )

    if st.session_state.analyzed:
        if st.button("🔄 Start Over", width="stretch"):
            reset_analysis()
            st.rerun()

# --------------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------------

st.title("🧭 AI Job Recommender")
st.caption(
    "Upload your resume to get an AI-generated summary, a skill-gap analysis, a career roadmap, "
    "and live job matches from LinkedIn and Naukri."
)

if uploaded_file is None and not st.session_state.analyzed:
    st.info("👈 Upload a PDF resume in the sidebar, set your job search preferences, and click **Analyze Resume** to get started.")
    st.stop()

# Detect a newly uploaded file that differs from the last analyzed one
if uploaded_file is not None:
    current_id = f"{uploaded_file.name}-{uploaded_file.size}"
    if st.session_state.analyzed and current_id != st.session_state.file_id:
        st.warning("A different resume was uploaded. Click **Analyze Resume** in the sidebar to refresh your results.")

# --------------------------------------------------------------------------------------
# Run the analysis pipeline
# --------------------------------------------------------------------------------------

if analyze_clicked and uploaded_file is not None:
    try:
        with st.status("Analyzing your resume...", expanded=True) as status:
            st.write("📖 Extracting text from PDF...")
            resume_text = extract_text_from_pdf(uploaded_file)
            if not resume_text.strip():
                status.update(label="Could not read any text from this PDF.", state="error")
                st.error("The uploaded PDF appears to be empty or scanned as an image. Try a text-based PDF.")
                st.stop()

            st.write("📑 Summarizing skills, education, and experience...")
            summary = cached_ask_openai(
                f"Summarize this resume highlighting the skills, education, and experience:\n\n{resume_text}",
                max_tokens=500,
            )

            st.write("🛠️ Identifying skill gaps...")
            gaps = cached_ask_openai(
                f"Analyze this resume and highlight missing skills, certifications, and experiences "
                f"needed for better job opportunities:\n\n{resume_text}",
                max_tokens=400,
            )

            st.write("🚀 Building a career roadmap...")
            roadmap = cached_ask_openai(
                f"Based on this resume, suggest a future roadmap to improve this person's career prospects "
                f"(skills to learn, certifications needed, industry exposure):\n\n{resume_text}",
                max_tokens=400,
            )

            st.write("🔑 Extracting job search keywords...")
            keywords = cached_ask_openai(
                f"Based on this resume summary, suggest the best job titles and keywords for searching jobs. "
                f"Give a comma-separated list only, no explanation.\n\nSummary: {summary}",
                max_tokens=100,
            )

            status.update(label="Analysis complete!", state="complete")

        st.session_state.file_id = f"{uploaded_file.name}-{uploaded_file.size}"
        st.session_state.resume_text = resume_text
        st.session_state.summary = summary
        st.session_state.gaps = gaps
        st.session_state.roadmap = roadmap
        st.session_state.keywords = (keywords or "").replace("\n", "").strip()
        st.session_state.analyzed = True
        st.session_state.analyzed_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.session_state.jobs = []
        st.session_state.jobs_fetched = False
        st.toast("Resume analyzed successfully!", icon="✅")
    except Exception as exc:
        st.error(f"Something went wrong during analysis: {exc}")
        st.stop()

if not st.session_state.analyzed:
    st.stop()

# --------------------------------------------------------------------------------------
# Results
# --------------------------------------------------------------------------------------

resume_text = st.session_state.resume_text
word_count = len(resume_text.split())
reading_time = max(1, round(word_count / 200))

summary_tab, gaps_tab, roadmap_tab, jobs_tab = st.tabs(
    ["📑 Summary", "🛠️ Skill Gaps", "🚀 Roadmap", "💼 Job Matches"]
)

with summary_tab:
    c1, c2, c3 = st.columns(3)
    c1.metric("Resume word count", word_count)
    c2.metric("Est. reading time", f"{reading_time} min")
    c3.metric("Analyzed at", st.session_state.analyzed_at)

    with st.container(border=True):
        st.markdown(st.session_state.summary)

    with st.expander("View extracted resume text"):
        st.text(resume_text)

with gaps_tab:
    with st.container(border=True):
        st.markdown(st.session_state.gaps)

with roadmap_tab:
    with st.container(border=True):
        st.markdown(st.session_state.roadmap)

    report = (
        f"# Resume Analysis Report\n\n"
        f"Generated: {st.session_state.analyzed_at}\n\n"
        f"## Summary\n{st.session_state.summary}\n\n"
        f"## Skill Gaps\n{st.session_state.gaps}\n\n"
        f"## Roadmap\n{st.session_state.roadmap}\n"
    )
    st.download_button(
        "⬇️ Download Full Report (Markdown)",
        data=report,
        file_name="resume_analysis_report.md",
        mime="text/markdown",
        width="stretch",
    )

with jobs_tab:
    st.write("**Suggested search keywords:**")
    kw_list = [k.strip() for k in (st.session_state.keywords or "").split(",") if k.strip()]
    if kw_list:
        badge_row = "  ".join(f":blue-badge[{kw}]" for kw in kw_list)
        st.markdown(badge_row)
    else:
        st.caption("No keywords extracted.")

    search_keywords = custom_keywords.strip() or st.session_state.keywords

    fetch_clicked = st.button("🔎 Find Matching Jobs", type="primary", disabled=not platforms)
    if not platforms:
        st.caption("Select at least one platform in the sidebar to search for jobs.")

    if fetch_clicked:
        try:
            all_jobs = []
            total_platforms = len(platforms)
            progress_bar = st.progress(0.0, text="Warming up the job search...")
            with st.status("🔎 Fetching live job listings...", expanded=True) as status:
                for i, platform in enumerate(platforms):
                    st.write(f"🔄 Searching **{platform}** for **{search_keywords}**...")
                    with st.spinner(f"Talking to {platform}..."):
                        raw_jobs = cached_fetch_jobs(platform, search_keywords, location, rows)
                    for job in raw_jobs:
                        apply_url = job.get("applyUrl") if platform == "Indeed" else None
                        all_jobs.append(
                            {
                                "platform": platform,
                                "title": job.get("title", "Untitled role"),
                                "company": job.get("companyName", "Unknown company"),
                                "location": job.get("location", "Not specified"),
                                "url": job.get("jobUrl") or job.get("link") or job.get("jdURL") or job.get("url"),
                                "apply_url": apply_url,
                                "logo": extract_logo_url(job),
                            }
                        )
                    st.write(f"✅ {platform}: found {len(raw_jobs)} jobs.")
                    progress_bar.progress(
                        (i + 1) / total_platforms,
                        text=f"Searched {i + 1}/{total_platforms} platforms...",
                    )
                status.update(label=f"Found {len(all_jobs)} jobs.", state="complete")
            progress_bar.empty()

            st.session_state.jobs = all_jobs
            st.session_state.jobs_fetched = True
            st.toast(f"Found {len(all_jobs)} job listings!", icon="💼")
        except Exception as exc:
            st.error(f"Something went wrong while fetching jobs: {exc}")

    if st.session_state.jobs_fetched:
        jobs = st.session_state.jobs

        if not jobs:
            st.warning("No jobs found for these keywords. Try adjusting your search preferences.")
        else:
            filter_col, platform_col = st.columns([3, 2])
            with filter_col:
                search_filter = st.text_input(
                    "Live search",
                    key="job_filter",
                    icon=":material/search:",
                    placeholder="Search by title, company, or location...",
                )
            with platform_col:
                platform_filter = st.segmented_control(
                    "Platform",
                    options=["All"] + sorted({j["platform"] for j in jobs}),
                    default="All",
                    key="platform_filter",
                )

            filtered = jobs
            if platform_filter and platform_filter != "All":
                filtered = [j for j in filtered if j["platform"] == platform_filter]
            if search_filter:
                needle = search_filter.lower()
                filtered = [
                    j
                    for j in filtered
                    if needle in j["title"].lower()
                    or needle in j["company"].lower()
                    or needle in j["location"].lower()
                ]

            st.caption(f"Showing {len(filtered)} of {len(jobs)} jobs")

            if filtered:
                df = pd.DataFrame(filtered)
                st.download_button(
                    "⬇️ Export visible jobs (CSV)",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="job_matches.csv",
                    mime="text/csv",
                )

            cols = st.columns(2)
            for i, job in enumerate(filtered):
                with cols[i % 2].container(border=True):
                    logo_col, info_col = st.columns([1, 5], vertical_alignment="center")
                    with logo_col:
                        if job.get("logo"):
                            st.image(job["logo"], width=48)
                        else:
                            st.markdown(":material/apartment:")
                    with info_col:
                        st.markdown(f"**{job['title']}**")
                        st.caption(f"{job['company']} · :material/location_on: {job['location']}")
                    st.badge(job["platform"], color=_PLATFORM_BADGE_COLORS.get(job["platform"], "gray"))
                    if job.get("apply_url"):
                        btn_col1, btn_col2 = st.columns(2)
                        if job["url"]:
                            btn_col1.link_button("View job", job["url"], width="stretch")
                        btn_col2.link_button("⚡ Apply now", job["apply_url"], width="stretch", type="primary")
                    elif job["url"]:
                        st.link_button("View job", job["url"], width="stretch")
