"""
Run the full job-search agent pipeline.

Usage:
    python main.py --resume data/resume.pdf --jobs data/sample_jobs.json --top 3

By default this drops you into an interactive approval prompt for each
tailored application (y/n/skip). Nothing is ever sent automatically --
"approved" just marks it ready in the tracker; actually emailing/applying
is a separate, deliberate step (see README).
"""
import argparse
from job_sources.manual import load_jobs
from pipeline import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", required=True, help="Path to resume PDF or .txt")
    parser.add_argument("--jobs", required=True, help="Path to a JSON file of job postings")
    parser.add_argument("--top", type=int, default=5, help="How many top-matched jobs to tailor")
    parser.add_argument("--min-score", type=float, default=0.0, help="Minimum fit score (0-1) to consider")
    args = parser.parse_args()

    jobs = load_jobs(args.jobs)
    graph = build_graph()

    result = graph.invoke({
        "resume_path": args.resume,
        "jobs": jobs,
        "top_n": args.top,
        "min_score": args.min_score,
        "non_interactive_decisions": None,   # real interactive review
        "profile": None, "scored": None, "tailored": None, "prep_sheets": None,
    })

    print("\n\n===== SUMMARY =====")
    for app in result["tailored"]:
        print(f"[{app.status:>10}] {app.job.title} @ {app.job.company}  (fit {app.fit_score:.2f})")

    approved = [a for a in result["tailored"] if a.status == "approved"]
    if approved:
        print(f"\n{len(approved)} application(s) approved and logged to data/applications.db")
        print("Interview prep sheets generated for each -- see result['prep_sheets'] or query interview_prep.py directly.")
    else:
        print("\nNo applications approved this run.")


if __name__ == "__main__":
    main()
