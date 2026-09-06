"""
Parses a resume (PDF or plain text) into a structured Profile.

Heuristic section-header parser tuned for the common
SUMMARY / SKILLS / PROJECTS / EDUCATION layout. For messier resumes,
swap `parse_sections()` for an LLM call (see README) -- the rest of the
pipeline only depends on the Profile dataclass, not on how it was built.
"""
import re
from pypdf import PdfReader
from models import Profile

SECTION_HEADERS = ["SUMMARY", "SKILLS", "PROJECTS", "EDUCATION", "CERTIFICATIONS", "CERTIFICATIONS & LANGUAGES"]


def extract_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        reader = PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_links(path: str) -> dict:
    """
    PDF text extraction only sees hyperlink *anchor text* (e.g. "GitHub"),
    not the actual URL -- that lives in the page's annotation objects.
    This reads the real URLs from /Annots so links come out correct.
    """
    links = {}
    if not path.lower().endswith(".pdf"):
        return links

    reader = PdfReader(path)
    for page in reader.pages:
        for annot in page.get("/Annots", []) or []:
            obj = annot.get_object()
            uri = obj.get("/A", {}).get("/URI")
            if not uri:
                continue
            uri_lower = uri.lower()
            if "github" in uri_lower:
                links["github"] = uri
            elif "linkedin" in uri_lower:
                links["linkedin"] = uri
            elif "netlify" in uri_lower or "portfolio" in uri_lower:
                links["portfolio"] = uri
    return links


def _split_sections(text: str) -> dict:
    pattern = r"(?m)^(" + "|".join(SECTION_HEADERS) + r")\s*$"
    parts = re.split(pattern, text)
    sections = {}
    # parts alternates: [preamble, header, body, header, body, ...]
    for i in range(1, len(parts) - 1, 2):
        header = parts[i].strip().upper()
        body = parts[i + 1].strip()
        sections[header] = body
    return sections, parts[0] if parts else ""


def parse_resume(path: str) -> Profile:
    text = extract_text(path)
    sections, preamble = _split_sections(text)

    # --- contact block: first few lines usually hold name/email/links ---
    lines = [l.strip() for l in preamble.splitlines() if l.strip()]
    name = lines[0] if lines else "Candidate"
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", preamble)
    email = email_match.group(0) if email_match else ""
    location_match = re.search(r"([A-Za-z ]+,\s*[A-Za-z ]+,\s*India)", preamble)
    location = location_match.group(0) if location_match else ""

    links = extract_links(path)

    summary = sections.get("SUMMARY", "").replace("\n", " ").strip()

    skills = []
    for line in sections.get("SKILLS", "").splitlines():
        if ":" in line:
            skills.append(line.split(":", 1)[1].strip())
    skills_flat = [s.strip() for group in skills for s in group.split(",")]

    projects = []
    proj_text = sections.get("PROJECTS", "")
    # split on lines that look like a project title (contain an em-dash and end without trailing period)
    blocks = re.split(r"\n(?=[A-Z][^\n]{0,120}—)", proj_text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        title_line, *rest = block.splitlines()
        bullets = [re.sub(r"^[•\-\*]\s*", "", r).strip() for r in rest if r.strip()]
        projects.append({"title": title_line.strip(), "bullets": bullets})

    education = [l.strip() for l in sections.get("EDUCATION", "").splitlines() if l.strip()]

    return Profile(
        name=name, email=email, location=location, summary=summary,
        skills=skills_flat, projects=projects, education=education, links=links
    )
