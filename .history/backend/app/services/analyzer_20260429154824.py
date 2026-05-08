import json, re
from fastapi import HTTPException
from openai import OpenAI
from app.config import settings
def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OPENAI_API_KEY is missing. Add it to backend/.env before analysis.")
    return OpenAI(api_key=settings.openai_api_key)
def _extract_json(text: str) -> dict:
    text = text.strip()
    try: return json.loads(text)
    except Exception: pass
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        try: return json.loads(m.group(0))
        except Exception: pass
    return {"final_score": 0, "summary": "Non-JSON result", "report_markdown": text}

def analyze_resume_job(resume_text: str, job_description: str, job_title: str = "", company: str = "") -> dict:
    if settings.use_mock_ai:
        return {
            "final_score": 78.0,
            "summary": "This is a mock analysis. The resume appears to be a moderately strong match for the job posting, with some missing keywords and room for stronger bullet points.",
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

    # existing OpenAI code continues below
    
# def analyze_resume_job(resume_text: str, job_description: str, job_title: str = "", company: str = "") -> dict:
#     prompt = f'''
# You are an expert resume consultant. Analyze the resume against the job posting.
# Rules: Do not invent fake experience. Be practical. Output valid JSON only.

# Job title: {job_title}
# Company: {company}
# Resume: {resume_text[:14000]}
# Job posting: {job_description[:14000]}

# Return JSON exactly:
# {{
#   "final_score": 0,
#   "summary": "1-2 sentence summary",
#   "breakdown": {{"skills": 0, "experience": 0, "tools": 0, "seniority": 0, "domain": 0}},
#   "missing_keywords": ["keyword1"],
#   "improvements": ["improvement1"],
#   "rewritten_bullets": ["bullet1"],
#   "recommendation": "apply / tailor first / skip",
#   "report_markdown": "markdown report"
# }}
# '''
#     res = _client().chat.completions.create(
#         model=settings.openai_chat_model,
#         messages=[
#             {
#                 "role": "user",
#                 "content": prompt,
#             }
#         ],
#     )

    data = _extract_json(res.choices[0].message.content)
    data["final_score"] = float(data.get("final_score") or 0)

    return data
