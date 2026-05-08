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
    prompt = f'''
You are an expert resume consultant. Analyze the resume against the job posting.
Rules: Do not invent fake experience. Be practical. Output valid JSON only.

Job title: {job_title}
Company: {company}
Resume: {resume_text[:14000]}
Job posting: {job_description[:14000]}

Return JSON exactly:
{{
  "final_score": 0,
  "summary": "1-2 sentence summary",
  "breakdown": {{"skills": 0, "experience": 0, "tools": 0, "seniority": 0, "domain": 0}},
  "missing_keywords": ["keyword1"],
  "improvements": ["improvement1"],
  "rewritten_bullets": ["bullet1"],
  "recommendation": "apply / tailor first / skip",
  "report_markdown": "markdown report"
}}
'''
    res = _client().responses.create(model=settings.openai_chat_model, input=prompt)
    data = _extract_json(res.output_text)
    data["final_score"] = float(data.get("final_score") or 0)
    return data
