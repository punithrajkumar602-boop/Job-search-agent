"""
Streamlit UI for the job search agent pipeline.

Run:
    streamlit run streamlit_app.py

Everything runs on your own machine. Nothing is sent anywhere except
when you click a job's real "Open job" link.
"""
import os
import json
from io import BytesIO

import streamlit as st

from resume_parser import parse_resume
from matching_agent import score_jobs
from tailoring_agent import tailor_application
from resume_export import build_resume_docx
from models import JobPosting
import tracker

st.set_page_config(page_title="Job Search Agent", layout="wide", page_icon="\U0001F3AF")
tracker.init_db()

if "profile" not in st.session_state:
    st.session_state.profile = None
if "applications" not in st.session_state:
    st.session_state.applications = {}  # job_id -> TailoredApplication

os.makedirs("uploads", exist_ok=True)

# ---------------------------------------------------------------- Styling
# Design tokens: a deep "control room" ink background -- you're the
# operator, the pipeline does the legwork -- with one warm coral->amber
# gradient standing in for momentum/progress, used only on primary
# actions and the one animated moment (the launch bar below). Space
# Grotesk for headings (geometric, a little mechanical -- fits
# "agent/pipeline"), Inter for body.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

:root {
  --bg-deep: #0b0f1a;
  --bg-mid: #121a2b;
  --panel: #141d33;
  --panel-border: #223052;
  --text: #e7ecf5;
  --muted: #8695b3;
  --accent-1: #ff6b4a;
  --accent-2: #ffc24a;
}

html, body, [class*="css"], .stMarkdown, p, span, label {
  font-family: 'Inter', -apple-system, sans-serif;
}
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }

.stApp {
  background:
    radial-gradient(1200px 600px at 15% -10%, rgba(255,107,74,0.10), transparent 60%),
    radial-gradient(1000px 500px at 100% 0%, rgba(255,194,74,0.06), transparent 55%),
    var(--bg-deep);
  color: var(--text);
}

[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 28px; border-bottom: 1px solid var(--panel-border); }
[data-testid="stTabs"] button { color: var(--muted); font-weight: 600; font-family: 'Space Grotesk', sans-serif; }
[data-testid="stTabs"] button[aria-selected="true"] { color: var(--text); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
  background: linear-gradient(90deg, var(--accent-1), var(--accent-2));
  height: 3px;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--panel);
  border: 1px solid var(--panel-border) !important;
  border-radius: 14px;
}

[data-testid="stButton"] button {
  border-radius: 8px;
  font-weight: 600;
  transition: transform 0.12s ease, box-shadow 0.12s ease, border-color 0.12s ease;
}
[data-testid="stButton"] button[kind="primary"] {
  background: linear-gradient(120deg, var(--accent-1), var(--accent-2));
  border: none;
  color: #0b0f1a;
}
[data-testid="stButton"] button[kind="primary"]:hover { transform: translateY(-1px); box-shadow: 0 8px 22px rgba(255,107,74,0.30); }
[data-testid="stButton"] button[kind="secondary"] {
  background: transparent;
  border: 1px solid var(--panel-border);
  color: var(--text);
}
[data-testid="stButton"] button[kind="secondary"]:hover { border-color: var(--accent-1); }

[data-testid="stDownloadButton"] button {
  background: var(--bg-mid);
  border: 1px solid var(--panel-border);
  color: var(--text);
  border-radius: 8px;
}
[data-testid="stLinkButton"] a { border-radius: 8px; }

[data-testid="stFileUploaderDropzone"], [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input {
  background: var(--bg-mid) !important;
  border: 1px solid var(--panel-border) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}

[data-testid="stDataFrame"] { border: 1px solid var(--panel-border); border-radius: 10px; overflow: hidden; }

/* One orchestrated motion moment: the launch sequence while the
   pipeline actually runs. Everything else on the page stays still. */
@keyframes scan {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.launch-bar {
  height: 6px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--panel-border) 0%, var(--accent-1) 45%, var(--accent-2) 55%, var(--panel-border) 100%);
  background-size: 300% 100%;
  animation: scan 1.1s linear infinite;
  margin: 10px 0 8px 0;
}
.launch-label { color: var(--muted); font-size: 13px; font-family: 'Space Grotesk', sans-serif; }

.hero-wrap { display: flex; align-items: center; gap: 14px; margin-bottom: 4px; }
.hero-badge {
  width: 40px; height: 40px; border-radius: 10px;
  background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; flex-shrink: 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="hero-wrap"><div class="hero-badge">\U0001F3AF</div>'
    '<h1 style="margin:0;">Job Search Agent</h1></div>',
    unsafe_allow_html=True,
)
st.caption("Score, tailor, and track applications — you approve every send.")

tab_run, tab_review, tab_tracker = st.tabs(["Run", "Review", "Tracker"])

# ---------------------------------------------------------------- Run tab
with tab_run:
    st.subheader("1. Upload your resume and job list")
    st.caption("Nothing is submitted automatically — you approve or reject each application on the Review tab.")

    resume_file = st.file_uploader("Resume (PDF)", type=["pdf"])
    jobs_file = st.file_uploader("Jobs file (JSON) — optional, uses the built-in sample jobs if left blank", type=["json"])
    top_n = st.number_input("How many top-matched jobs to tailor", min_value=1, max_value=20, value=5)

    run_clicked = st.button("Run pipeline", type="primary", disabled=resume_file is None)
    launch_slot = st.empty()

    if run_clicked:
        launch_slot.markdown(
            '<div class="launch-bar"></div><div class="launch-label">Parsing resume and scoring jobs…</div>',
            unsafe_allow_html=True,
        )

        resume_path = os.path.join("uploads", "resume.pdf")
        with open(resume_path, "wb") as f:
            f.write(resume_file.getbuffer())

        if jobs_file:
            jobs_data = json.load(jobs_file)
        else:
            with open("data/sample_jobs.json") as f:
                jobs_data = json.load(f)

        profile = parse_resume(resume_path)
        st.session_state.profile = profile

        job_objs = [JobPosting(**j) for j in jobs_data]
        scored = score_jobs(profile, job_objs)[:top_n]

        apps = {}
        for sj in scored:
            apps[sj.job.job_id] = tailor_application(profile, sj)
        st.session_state.applications = apps

        launch_slot.empty()
        st.success(f"Tailored {len(apps)} application(s) — check the Review tab.")

    if st.session_state.profile:
        with st.expander("Parsed profile (for sanity-checking)"):
            p = st.session_state.profile
            st.write(f"**Name:** {p.name}  |  **Email:** {p.email}")
            st.write(f"**Skills:** {', '.join(p.skills)}")
            st.write(f"**Links:** {p.links}")

# ------------------------------------------------------------- Review tab
with tab_review:
    st.subheader("2. Review each tailored application")

    apps = sorted(st.session_state.applications.values(), key=lambda a: a.fit_score, reverse=True)

    if not apps:
        st.info("No applications yet — run the pipeline in the **Run** tab first.")

    for app_obj in apps:
        job_id = app_obj.job.job_id
        with st.container(border=True):
            top_col1, top_col2 = st.columns([5, 1])
            with top_col1:
                st.subheader(f"{app_obj.job.title} — {app_obj.job.company}")
                st.caption(
                    f"{app_obj.job.location} · fit score {app_obj.fit_score:.2f} · "
                    f"status: **{app_obj.status.replace('_', ' ')}**"
                )
            with top_col2:
                st.link_button("Open job / Apply", app_obj.job.url, use_container_width=True)

            st.markdown(f"**Tailored summary:** {app_obj.resume_summary}")
            st.text_area(
                "Application email",
                f"Subject: {app_obj.email_subject}\n\n{app_obj.email_body}",
                height=220,
                key=f"email_{job_id}",
            )

            c1, c2, c3, c4 = st.columns(4)

            def _set_status(status, app_obj=app_obj):
                app_obj.status = status
                tracker.upsert_application({
                    "job_id": app_obj.job.job_id,
                    "company": app_obj.job.company,
                    "title": app_obj.job.title,
                    "status": app_obj.status,
                    "resume_version": app_obj.job.job_id,
                    "fit_score": app_obj.fit_score,
                    "notes": "ready to send" if status == "approved" else "",
                })

            if c1.button("Approve", key=f"approve_{job_id}", type="primary"):
                _set_status("approved")
                st.rerun()
            if c2.button("Reject", key=f"reject_{job_id}"):
                _set_status("rejected")
                st.rerun()
            if c3.button("Skip", key=f"skip_{job_id}"):
                _set_status("skipped")
                st.rerun()

            buf = BytesIO()
            build_resume_docx(st.session_state.profile, app_obj, buf)
            c4.download_button(
                "Download tailored resume (.docx)",
                data=buf.getvalue(),
                file_name=f"Resume_{app_obj.job.company}_{app_obj.job.title}.docx".replace(" ", "_"),
                key=f"dl_{job_id}",
            )

# ------------------------------------------------------------ Tracker tab
with tab_tracker:
    st.subheader("3. Application tracker")
    rows = tracker.all_applications()
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Nothing logged yet — approve or reject an application in the Review tab first.")
