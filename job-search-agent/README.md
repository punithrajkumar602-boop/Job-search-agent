# AI Job Search Agent Pipeline

A LangGraph pipeline that parses your resume, scores real job postings
against it, tailors a resume summary + application email per job, and
tracks everything — with a **human approval gate** before anything is
marked ready to send. Nothing is auto-submitted; that's intentional
(see "Why there's an approval gate" below).

Tested end-to-end on the included sample resume and 4 real fresher
AI/ML job postings — see `data/resume.pdf` and `data/sample_jobs.json`.

## Architecture

```
parse_resume -> score_jobs -> tailor -> human_review -> track -> interview_prep
```

| Stage | File | What it does |
|---|---|---|
| Resume parsing | `resume_parser.py` | Extracts a structured `Profile` from a PDF/text resume |
| Job scoring | `matching_agent.py` | TF-IDF similarity + matched-keyword rationale (offline, no API key) |
| Tailoring | `tailoring_agent.py` | Per-job resume summary + email; template-based, or Claude if `ANTHROPIC_API_KEY` is set |
| Human review | `approval_gate.py` | CLI prompt — approve / reject / skip each application |
| Tracking | `tracker.py` | SQLite log of every application and its status |
| Interview prep | `interview_prep.py` | Generates a topical + generalist question sheet for approved jobs |

## Setup

```bash
pip install -r requirements.txt
```

Optional — for LLM-written summaries/emails instead of templates:
```bash
export ANTHROPIC_API_KEY=sk-...
```

## Run it — Web UI (Streamlit)

```bash
streamlit run streamlit_app.py
```
This opens a browser tab automatically (usually http://localhost:8501).
Upload your resume, optionally upload a jobs JSON (or leave blank to
use the sample jobs), set how many top jobs to tailor, and click
"Run pipeline". Switch to the **Review** tab to see each tailored
application with an editable email preview, Approve/Reject/Skip
buttons, a "Download tailored resume (.docx)" button, and an
"Open job / Apply" button that goes straight to the real listing.
The **Tracker** tab shows everything you've approved or rejected.

## Run it — Command line

```bash
python main.py --resume data/resume.pdf --jobs data/sample_jobs.json --top 4
```

You'll be prompted per job: `Approve this application? [y/n/skip]`.
Approved ones get logged to `data/applications.db` and get an interview
prep sheet generated.

## Feeding in real, live jobs

`job_sources/manual.py` reads jobs from a JSON file (see
`data/sample_jobs.json` for the exact shape). To connect to a live job
source:

- **If you have Indeed/Dice/ZipRecruiter connectors in Claude** (as used
  to build this): have Claude call those tools directly, save results in
  the same JSON shape, and point `--jobs` at that file.
- **If you have direct API access** to a job board: fill in
  `job_sources/indeed.py`'s `fetch_jobs()` and call it in `main.py`
  instead of `load_jobs()`.

## Why there's an approval gate

Auto-apply tools that submit without showing you the application first
have a documented failure mode: bad matches, and in some cases,
applications submitted to fraudulent listings. This pipeline tailors
and drafts everything for you, but a person decides what actually goes
out. If you want it faster, make `approval_gate.py`'s CLI output
terser — don't remove the `input()` call.

## Extending this

- **Better scoring**: swap `matching_agent.py`'s TF-IDF for an
  LLM-as-judge call (same pattern as a RAG evaluator — score + written
  rationale, not just cosine similarity).
- **Adaptive interview prep**: replace `interview_prep.py`'s static
  template with a LangGraph state machine that adjusts question
  difficulty based on answers (i.e. an actual mock-interview loop).
- **Auto-send on approval**: once `status == "approved"`, wire in an
  email API (e.g. SMTP or Gmail API) to actually send — kept out of
  this repo on purpose so the send step stays a deliberate, separate
  action you add yourself.
- **More job sources**: add a new file under `job_sources/` per source,
  each returning the same list-of-dicts shape.
