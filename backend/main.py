import os
import io
import json
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import google.generativeai as genai
from datetime import datetime

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MonumentLog(Base):
    __tablename__ = "monument_logs"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    identification_result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Gemini AI Setup
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "DUMMY_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/identify")
async def identify_monument(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        
        # Analyze with Gemini 1.5 Flash Vision
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "You are a heritage expert. Identify this monument or architecture. "
            "Respond ONLY in raw JSON matching this structure: "
            '{"name": "...", "location": "...", "style": "...", "history": "..."}'
        )
        
        response = model.generate_content([
            prompt,
            {"mime_type": file.content_type, "data": contents}
        ])
        
        # Parse JSON output from AI
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        
        # Save identification log to PostgreSQL database
        log = MonumentLog(filename=file.filename, identification_result=clean_text)
        db.add(log)
        db.commit()

        # Trigger background processing worker (EXIF extraction & optimization)
        try:
            from backend.worker import process_image_background
            process_image_background.delay(file.filename)
        except Exception:
            pass # Non-blocking if worker/redis is offline
            
        return data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))