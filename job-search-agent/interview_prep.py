"""
Generates a short interview-prep sheet for a job right after its
application is approved. Mirrors the adaptive-questioning idea from the
AI-Interview-Assistant project -- this is the template-based version;
swap in that project's LangGraph state machine for adaptive difficulty.
"""

GENERIC_QUESTIONS = [
    "Walk me through a project where you had to debug a model or pipeline that wasn't working as expected.",
    "How do you evaluate whether an AI system's output is good enough to ship?",
    "Describe a time you had to learn a new library or framework quickly for a project.",
]

TOPIC_QUESTIONS = {
    "rag": "How would you reduce hallucination in a RAG pipeline, and how would you measure whether it worked?",
    "agent": "How do you handle a multi-agent system where two agents disagree?",
    "llm": "How do you decide when a prompt-engineering fix is enough vs. when you need fine-tuning?",
    "computer vision": "Walk me through your approach to debugging a computer vision model with poor accuracy on edge cases.",
    "nlp": "How would you approach building an NLP feature for a language with limited labeled data?",
}


def generate_prep_sheet(tailored_app) -> str:
    desc = tailored_app.job.description.lower()
    topical = [q for key, q in TOPIC_QUESTIONS.items() if key in desc]

    lines = [
        f"Interview Prep — {tailored_app.job.title} at {tailored_app.job.company}",
        "=" * 60,
        "\nLikely topical questions based on the job description:",
    ]
    for q in (topical or ["No strong topic match found — expect generalist ML/AI questions."]):
        lines.append(f"  • {q}")

    lines.append("\nGeneral fresher-round questions to prepare:")
    for q in GENERIC_QUESTIONS:
        lines.append(f"  • {q}")

    lines.append("\nProjects to have ready to walk through on screen-share:")
    for title in tailored_app.project_order[:2]:
        lines.append(f"  • {title}")

    return "\n".join(lines)
