from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, public, saved
app = FastAPI(title="Resumagic Service v4", version="0.4.0")
app.add_middleware(
    CORSMiddleware, 
    allow_origins=[
        "http://127.0.0.1:5173", 
        "http://localhost:5173",
        "https://resume-builder-ten-kappa-52.vercel.app"
        ], 
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"])
app.include_router(public.router)
app.include_router(auth.router)
app.include_router(saved.router)
@app.get("/health")
def health(): return {"status": "ok"}
