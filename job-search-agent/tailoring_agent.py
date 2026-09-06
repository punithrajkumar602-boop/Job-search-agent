"""
Generates a tailored resume summary, project ordering, and application
email for one scored job.

Default: template-based (no API key needed, works offline).
If ANTHROPIC_API_KEY is set in the environment, uses Claude to write a
sharper, job-specific summary and email instead of the template.
"""
import os
from models import TailoredApplication

USE_LLM = bool(os.environ.get("ANTHROPIC_API_KEY"))

if USE_LLM:
    import anthropic
    _client = anthropic.Anthropic()


def _llm_tailor(profile, scored_job) -> tuple[str, str, str]:
    """Returns (summary, email_subject, email_body) written by Claude."""
    prompt = f"""You are helping a job seeker tailor their application.

CANDIDATE PROFILE:
Name: {profile.name}
Summary: {profile.summary}
Skills: {', '.join(profile.skills)}
Projects: {[(p['title']) for p in profile.projects]}
Links: {profile.links}

JOB:
Title: {scored_job.job.title}
Company: {scored_job.job.company}
Description: {scored_job.job.description[:2000]}

Write, in this exact format with these exact headers:
SUMMARY: <2-3 sentence resume summary tailored to this job>
SUBJECT: <email subject line>
BODY: <application email body, professional, under 200 words, mentions 2-3 relevant projects, includes candidate's links>
"""
    resp = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    summary = text.split("SUMMARY:")[1].split("SUBJECT:")[0].strip()
    subject = text.split("SUBJECT:")[1].split("BODY:")[0].strip()
    body = text.split("BODY:")[1].strip()
    return summary, subject, body


def _template_tailor(profile, scored_job) -> tuple[str, str, str]:
    """Offline fallback: keyword-driven summary + a generic but personalized email."""
    top_terms = ", ".join(scored_job.matched_skills[:5]) or "your core requirements"
    summary = (
        f"{profile.summary} Directly relevant to this {scored_job.job.title} role: "
        f"hands-on experience with {top_terms}."
    )
    subject = f"Application for {scored_job.job.title} – {profile.name}"

    project_lines = "\n".join(
        f"- {p['title']}" for p in profile.projects[:3]
    )
    body = (
        f"Hi {scored_job.job.company} Team,\n\n"
        f"I'm applying for the {scored_job.job.title} role. {profile.summary}\n\n"
        f"Relevant project experience:\n{project_lines}\n\n"
        f"You can find full project code and live demos here:\n"
        f"GitHub: {profile.links.get('github', '')}\n"
        f"Portfolio: {profile.links.get('portfolio', '')}\n\n"
        f"Thank you for your consideration,\n{profile.name}\n{profile.email}"
    )
    return summary, subject, body


def tailor_application(profile, scored_job) -> TailoredApplication:
    if USE_LLM:
        summary, subject, body = _llm_tailor(profile, scored_job)
    else:
        summary, subject, body = _template_tailor(profile, scored_job)

    project_order = [p["title"] for p in profile.projects]

    return TailoredApplication(
        job=scored_job.job,
        fit_score=scored_job.fit_score,
        resume_summary=summary,
        project_order=project_order,
        email_subject=subject,
        email_body=body,
    )
