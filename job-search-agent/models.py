"""Core data structures used across the pipeline."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Profile:
    """Structured version of the candidate's resume."""
    name: str
    email: str
    location: str
    summary: str
    skills: List[str]
    projects: List[dict]  # [{"title": str, "bullets": [str, ...]}]
    education: List[str]
    links: dict  # {"github": str, "linkedin": str, "portfolio": str}


@dataclass
class JobPosting:
    job_id: str
    title: str
    company: str
    location: str
    source: str          # "indeed" | "dice" | "zip_recruiter" | "manual"
    description: str
    url: str
    posted_on: Optional[str] = None
    job_type: Optional[str] = None


@dataclass
class ScoredJob:
    job: JobPosting
    fit_score: float           # 0-1
    matched_skills: List[str]
    rationale: str


@dataclass
class TailoredApplication:
    job: JobPosting
    fit_score: float
    resume_summary: str
    project_order: List[str]   # project titles, ordered by relevance
    email_subject: str
    email_body: str
    status: str = "pending_review"   # pending_review | approved | rejected | sent


@dataclass
class ApplicationRecord:
    job_id: str
    company: str
    title: str
    status: str
    resume_version: str
    date_applied: Optional[str] = None
    notes: str = ""
