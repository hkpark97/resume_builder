import json
import re

from fastapi import HTTPException
from openai import OpenAI

from app.config import settings

COMMON_SKILLS = [
    "python",
    "fastapi",
    "react",
    "javascript",
    "typescript",
    "sql",
    "postgresql",
    "aws",
    "docker",
    "kubernetes",
    "linux",
    "git",
    "rest api",
    "api",
    "machine learning",
    "openai",
    "jwt",
    "sqlalchemy",
]


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


def extract_terms(text: str) -> list[str]:
    text_lower = text.lower()

    return [skill for skill in COMMON_SKILLS if skill in text_lower]


def overlap_score(resume_terms: list[str], job_terms: list[str]) -> float:
    if not job_terms:
        return 0.0

    resume_set = set(resume_terms)
    job_set = set(job_terms)
    matched = resume_set & job_set

    return round(len(matched) / len(job_set) * 100, 1)


def _mock_analysis() -> dict:
    return {
        "final_score": 78.0,
        "summary": (
            "This is a mock analysis. The resume appears to be a moderately strong "
            "match for the job posting, with some missing keywords and room for stronger bullet points."
        ),
        "breakdown": {
            "skills": 82,
            "experience": 76,
            "tools": 70,
            "seniority": 80,
            "domain": 72,
        },
        "missing_keywords": [
            "ATS optimization",
            "stakeholder management",
            "Python",
            "cloud deployment",
            "metrics-driven impact",
        ],
        "improvements": [
            "Add more job-specific keywords from the posting into the skills and experience sections.",
            "Rewrite bullets to show measurable impact using numbers, scale, or business outcomes.",
            "Move the most relevant experience closer to the top of the resume.",
        ],
        "rewritten_bullets": [
            "Improved backend workflow efficiency by automating manual resume analysis steps and reducing review time.",
            "Built and maintained API-driven features that supported user authentication, file uploads, and structured analysis results.",
            "Collaborated across product and technical requirements to deliver a cleaner user flow from resume upload to job-fit scoring.",
        ],
        "recommendation": "tailor first",
        "report_markdown": """
## Mock Resume Match Report

### Match Summary
This is a mock result for frontend/backend testing. The candidate looks like a **moderately strong match** for this role.

### Score Breakdown
- Skills match: 82%
- Experience match: 76%
- Tools match: 70%
- Seniority match: 80%
- Domain match: 72%

### Missing Keywords
- ATS optimization
- Stakeholder management
- Python
- Cloud deployment
- Metrics-driven impact

### Top Improvements
1. Add more job-specific keywords from the posting.
2. Rewrite bullets with measurable outcomes.
3. Highlight the most relevant projects near the top.

### Suggested Bullet Rewrites
- Improved backend workflow efficiency by automating manual resume analysis steps and reducing review time.
- Built and maintained API-driven features that supported user authentication, file uploads, and structured analysis results.
- Collaborated across product and technical requirements to deliver a cleaner user flow from resume upload to job-fit scoring.

### Recommendation
Tailor the resume before applying.
""",
    }


def analyze_resume_job(
    resume_text: str,
    job_description: str,
    job_title: str = "",
    company: str = "",
) -> dict:
    if settings.use_mock_ai:
        return _mock_analysis()

    resume_terms = extract_terms(resume_text)
    job_terms = extract_terms(job_description)
    skills_overlap = overlap_score(resume_terms, job_terms)

    prompt = f"""
You are an expert resume consultant. Analyze the resume against the job posting.

Rules:
- Do not invent fake experience.
- Be practical.
- Output valid JSON only.
- Be conservative. Do not give a high score just because the resume sounds generally strong.
- Apply the same scoring rubric consistently every time.
- Use the deterministic scoring signal as an important input, but still consider experience, tools, seniority, and domain relevance.
- If the skills overlap score is low, the final_score should usually be lower unless there is strong evidence from experience.

Scoring rubric:
- 90-100: Excellent match. Resume strongly matches required skills, experience, tools, and domain.
- 75-89: Strong match. Most key requirements are present, minor tailoring needed.
- 60-74: Moderate match. Some relevant experience, several missing requirements.
- 40-59: Weak match. Limited overlap with job requirements.
- 0-39: Poor match. Resume does not align with the role.

Deterministic scoring signal:
- Resume matched terms: {resume_terms}
- Job required terms detected: {job_terms}
- Skills overlap score: {skills_overlap}

Job title: {job_title}
Company: {company}

Resume:
{resume_text[:14000]}

Job posting:
{job_description[:14000]}

Return JSON exactly:
{{
  "final_score": 0,
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
                    "Use the same scoring rubric consistently."
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
    data["final_score"] = float(data.get("final_score") or 0)

    if "breakdown" not in data or not isinstance(data["breakdown"], dict):
        data["breakdown"] = {}

    data["breakdown"]["skills_overlap_signal"] = skills_overlap
    data["matched_terms"] = resume_terms
    data["job_terms_detected"] = job_terms

    return data
