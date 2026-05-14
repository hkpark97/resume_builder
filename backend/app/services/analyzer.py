import json
import re
from typing import Any

from fastapi import HTTPException
from openai import OpenAI

from app.config import settings


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=400,
            detail="OPENAI_API_KEY is missing. Add it to backend/.env before analysis.",
        )

    return OpenAI(api_key=settings.openai_api_key)


def _extract_json(text: str) -> dict:
    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return {
        "final_score": 0,
        "summary": "Non-JSON result",
        "breakdown": {},
        "missing_keywords": [],
        "improvements": [],
        "rewritten_bullets": [],
        "recommendation": "tailor first",
        "report_markdown": text,
    }


def clean_job_posting_text(text: str) -> str:
    remove_patterns = [
        "apply now",
        "save job",
        "share",
        "similar jobs",
        "recommended jobs",
        "cookie",
        "privacy policy",
        "terms of use",
        "equal opportunity",
        "about us",
        "follow us",
        "sign in",
        "create alert",
        "job alert",
        "back to jobs",
    ]

    lines = text.splitlines()
    cleaned_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        line_lower = line.lower()

        if not line:
            continue

        if len(line) < 3:
            continue

        if any(pattern in line_lower for pattern in remove_patterns):
            continue

        if line_lower in seen:
            continue

        seen.add(line_lower)
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)

    return cleaned[:14000]


def normalize_terms(items: list[Any]) -> list[str]:
    normalized = []

    for item in items or []:
        if not isinstance(item, str):
            continue

        value = item.strip().lower()

        if not value:
            continue

        normalized.append(value)

    return sorted(set(normalized))


def overlap_score(candidate_terms: list[str], required_terms: list[str]) -> float:
    candidate_set = set(candidate_terms)
    required_set = set(required_terms)

    if not required_set:
        return 0.0

    matched = candidate_set & required_set

    return round(len(matched) / len(required_set) * 100, 1)


def weighted_score(scores: dict[str, float]) -> float:
    final_score = (
        scores.get("required_skills", 0) * 0.4
        + scores.get("tools", 0) * 0.2
        + scores.get("frameworks", 0) * 0.15
        + scores.get("databases_cloud", 0) * 0.15
        + scores.get("domain", 0) * 0.1
    )

    return round(max(0, min(final_score, 100)), 1)


def extract_match_entities_with_ai(resume_text: str, job_text: str) -> dict:
    prompt = f"""
Extract structured matching entities from the resume and job posting.

Rules:
- Do not use any predefined skill list.
- Extract only entities actually present in the text.
- Normalize similar terms when obvious.
  Example: "PostgreSQL" and "Postgres" -> "postgresql".
- Keep terms concise.
- Return valid JSON only.

Resume:
{resume_text[:12000]}

Job posting:
{job_text[:12000]}

Return JSON exactly:
{{
  "resume": {{
    "skills": [],
    "tools": [],
    "frameworks": [],
    "databases": [],
    "cloud": [],
    "domains": [],
    "seniority": ""
  }},
  "job": {{
    "required_skills": [],
    "preferred_skills": [],
    "tools": [],
    "frameworks": [],
    "databases": [],
    "cloud": [],
    "domains": [],
    "seniority": ""
  }}
}}
"""

    res = _client().chat.completions.create(
        model=settings.openai_chat_model,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract resume and job posting matching entities. "
                    "Return valid JSON only. Do not invent skills."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    data = _extract_json(res.choices[0].message.content)

    resume = data.get("resume", {}) or {}
    job = data.get("job", {}) or {}

    return {
        "resume": {
            "skills": normalize_terms(resume.get("skills", [])),
            "tools": normalize_terms(resume.get("tools", [])),
            "frameworks": normalize_terms(resume.get("frameworks", [])),
            "databases": normalize_terms(resume.get("databases", [])),
            "cloud": normalize_terms(resume.get("cloud", [])),
            "domains": normalize_terms(resume.get("domains", [])),
            "seniority": str(resume.get("seniority", "") or "").strip().lower(),
        },
        "job": {
            "required_skills": normalize_terms(job.get("required_skills", [])),
            "preferred_skills": normalize_terms(job.get("preferred_skills", [])),
            "tools": normalize_terms(job.get("tools", [])),
            "frameworks": normalize_terms(job.get("frameworks", [])),
            "databases": normalize_terms(job.get("databases", [])),
            "cloud": normalize_terms(job.get("cloud", [])),
            "domains": normalize_terms(job.get("domains", [])),
            "seniority": str(job.get("seniority", "") or "").strip().lower(),
        },
    }


def calculate_hybrid_score(entities: dict) -> dict:
    resume = entities["resume"]
    job = entities["job"]

    resume_databases_cloud = resume["databases"] + resume["cloud"]
    job_databases_cloud = job["databases"] + job["cloud"]

    scores = {
        "required_skills": overlap_score(
            resume["skills"],
            job["required_skills"],
        ),
        "tools": overlap_score(
            resume["tools"],
            job["tools"],
        ),
        "frameworks": overlap_score(
            resume["frameworks"],
            job["frameworks"],
        ),
        "databases_cloud": overlap_score(
            resume_databases_cloud,
            job_databases_cloud,
        ),
        "domain": overlap_score(
            resume["domains"],
            job["domains"],
        ),
    }

    final_score = weighted_score(scores)

    matched_required_skills = sorted(
        set(resume["skills"]) & set(job["required_skills"])
    )

    missing_required_skills = sorted(
        set(job["required_skills"]) - set(resume["skills"])
    )

    return {
        "final_score": final_score,
        "breakdown": scores,
        "matched_required_skills": matched_required_skills,
        "missing_required_skills": missing_required_skills,
    }


def analyze_resume_job(
    resume_text: str,
    job_description: str,
    job_title: str = "",
    company: str = "",
) -> dict:
    cleaned_job_description = clean_job_posting_text(job_description)

    entities = extract_match_entities_with_ai(
        resume_text=resume_text,
        job_text=cleaned_job_description,
    )

    hybrid = calculate_hybrid_score(entities)
    calculated_score = hybrid["final_score"]

    prompt = f"""
You are an expert resume consultant. Analyze the resume against the job posting.

Rules:
- Do not invent fake experience.
- Be practical.
- Output valid JSON only.
- The final_score has already been calculated by the backend hybrid scoring engine.
- You must use this exact final_score: {calculated_score}
- Do not change the final_score.
- Use the extracted entities and scoring breakdown to explain the result.
- Focus on practical resume improvements.

Job title: {job_title}
Company: {company}

Backend calculated score:
{calculated_score}

Backend scoring breakdown:
{json.dumps(hybrid["breakdown"], indent=2)}

Extracted resume entities:
{json.dumps(entities["resume"], indent=2)}

Extracted job entities:
{json.dumps(entities["job"], indent=2)}

Matched required skills:
{hybrid["matched_required_skills"]}

Missing required skills:
{hybrid["missing_required_skills"]}

Resume:
{resume_text[:12000]}

Cleaned job posting:
{cleaned_job_description[:12000]}

Return JSON exactly:
{{
  "final_score": {calculated_score},
  "summary": "1-2 sentence summary",
  "breakdown": {{
    "skills": 0,
    "experience": 0,
    "tools": 0,
    "seniority": 0,
    "domain": 0
  }},
  "missing_keywords": ["keyword1"],
  "improvements": ["improvement1"],
  "rewritten_bullets": ["bullet1"],
  "recommendation": "apply / tailor first / skip",
  "report_markdown": "markdown report"
}}
"""

    res = _client().chat.completions.create(
        model=settings.openai_chat_model,
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict resume-job matching evaluator. "
                    "Return valid JSON only. Do not use markdown outside JSON. "
                    "Do not change the backend-calculated final_score."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    data = _extract_json(res.choices[0].message.content)

    data["final_score"] = calculated_score
    data["hybrid_score"] = calculated_score
    data["hybrid_breakdown"] = hybrid["breakdown"]
    data["matched_required_skills"] = hybrid["matched_required_skills"]
    data["missing_required_skills"] = hybrid["missing_required_skills"]
    data["extracted_entities"] = entities

    if "breakdown" not in data or not isinstance(data["breakdown"], dict):
        data["breakdown"] = {}

    return data
