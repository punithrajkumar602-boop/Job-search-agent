"""
The full pipeline, as a LangGraph state machine:

  parse_resume -> load_jobs -> score_jobs -> tailor_top_jobs
       -> human_review -> track_results -> generate_interview_prep -> END

Every node reads/writes a shared `PipelineState` dict. The human_review
node is a real breakpoint: it will call input() per application unless
you pass non_interactive_decisions (only meant for demos/tests).
"""
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END

from resume_parser import parse_resume
from matching_agent import score_jobs
from tailoring_agent import tailor_application
from approval_gate import review
from interview_prep import generate_prep_sheet
import tracker


class PipelineState(TypedDict):
    resume_path: str
    jobs: List[dict]                 # raw job dicts, see job_sources/manual.py
    profile: Optional[object]
    scored: Optional[list]
    tailored: Optional[list]
    top_n: int
    min_score: float
    non_interactive_decisions: Optional[dict]
    prep_sheets: Optional[dict]


def node_parse_resume(state: PipelineState) -> PipelineState:
    state["profile"] = parse_resume(state["resume_path"])
    return state


def node_score_jobs(state: PipelineState) -> PipelineState:
    from models import JobPosting
    job_objs = [JobPosting(**j) for j in state["jobs"]]
    state["scored"] = score_jobs(state["profile"], job_objs, min_score=state.get("min_score", 0.0))
    return state


def node_tailor(state: PipelineState) -> PipelineState:
    top = state["scored"][: state.get("top_n", 5)]
    state["tailored"] = [tailor_application(state["profile"], sj) for sj in top]
    return state


def node_human_review(state: PipelineState) -> PipelineState:
    for app in state["tailored"]:
        review(app, non_interactive_decisions=state.get("non_interactive_decisions"))
    return state


def node_track(state: PipelineState) -> PipelineState:
    tracker.init_db()
    for app in state["tailored"]:
        tracker.upsert_application({
            "job_id": app.job.job_id,
            "company": app.job.company,
            "title": app.job.title,
            "status": app.status,
            "resume_version": app.job.job_id,
            "fit_score": app.fit_score,
            "notes": "" if app.status != "approved" else "ready to send",
        })
    return state


def node_interview_prep(state: PipelineState) -> PipelineState:
    state["prep_sheets"] = {
        app.job.job_id: generate_prep_sheet(app)
        for app in state["tailored"] if app.status == "approved"
    }
    return state


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("parse_resume", node_parse_resume)
    graph.add_node("score_jobs", node_score_jobs)
    graph.add_node("tailor", node_tailor)
    graph.add_node("human_review", node_human_review)
    graph.add_node("track", node_track)
    graph.add_node("interview_prep", node_interview_prep)

    graph.set_entry_point("parse_resume")
    graph.add_edge("parse_resume", "score_jobs")
    graph.add_edge("score_jobs", "tailor")
    graph.add_edge("tailor", "human_review")
    graph.add_edge("human_review", "track")
    graph.add_edge("track", "interview_prep")
    graph.add_edge("interview_prep", END)

    return graph.compile()
