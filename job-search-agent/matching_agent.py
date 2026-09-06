"""
Scores each job against the candidate profile.

Default: TF-IDF cosine similarity -- works offline, no API key needed.
Upgrade path: swap `score_jobs()` to call an LLM-as-judge (like the
evaluator in the RAG-Eval-Guardrails project) for reasoning-based scoring
instead of pure keyword overlap. See README "Upgrading to LLM scoring".
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from models import ScoredJob


def _profile_text(profile) -> str:
    project_text = " ".join(
        p["title"] + " " + " ".join(p["bullets"]) for p in profile.projects
    )
    return f"{profile.summary} {' '.join(profile.skills)} {project_text}"


def score_jobs(profile, jobs, min_score: float = 0.0):
    profile_doc = _profile_text(profile)
    job_docs = [j.description for j in jobs]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000)
    matrix = vectorizer.fit_transform([profile_doc] + job_docs)
    sims = cosine_similarity(matrix[0:1], matrix[1:]).flatten()

    vocab = vectorizer.get_feature_names_out()
    profile_terms = set(vectorizer.transform([profile_doc]).indices)

    results = []
    for job, sim in zip(jobs, sims):
        if sim < min_score:
            continue
        job_vec = vectorizer.transform([job.description])
        job_terms = set(job_vec.indices)
        overlap = [vocab[i] for i in (profile_terms & job_terms)][:8]
        rationale = (
            f"TF-IDF similarity {sim:.2f}. Overlapping terms: {', '.join(overlap)}"
            if overlap else f"TF-IDF similarity {sim:.2f}. Low keyword overlap."
        )
        results.append(ScoredJob(job=job, fit_score=round(float(sim), 3),
                                  matched_skills=overlap, rationale=rationale))

    return sorted(results, key=lambda r: r.fit_score, reverse=True)
