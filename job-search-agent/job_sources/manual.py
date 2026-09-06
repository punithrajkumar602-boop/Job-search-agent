"""Loads jobs from a local JSON file. Simplest possible job source --
useful for testing, or for pasting in jobs you found manually."""
import json


def load_jobs(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
