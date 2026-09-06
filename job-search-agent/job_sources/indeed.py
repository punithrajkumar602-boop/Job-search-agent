"""
Placeholder for a live job source. Fill in `fetch_jobs()` with a real
call to whichever job-search API/connector you have access to (Indeed,
Dice, ZipRecruiter, LinkedIn, etc.) and return a list of dicts matching
the JobPosting fields: job_id, title, company, location, source,
description, url, posted_on, job_type.

If you're running this from inside Claude (e.g. via Claude Code with the
Indeed/Dice/ZipRecruiter connectors already available), you don't need
this file at all -- just have Claude call those tools directly and pass
the results straight into job_sources/manual.py's load_jobs() shape, or
save them to sample_jobs.json.
"""


def fetch_jobs(query: str, location: str) -> list[dict]:
    raise NotImplementedError(
        "Wire this up to a real job API/connector. "
        "Until then, use job_sources/manual.py with a JSON file of jobs."
    )
