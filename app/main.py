from fastapi import FastAPI, UploadFile, File
import os
import shutil
import tempfile

from app.whisper_service import transcribe_audio
from app.summary_service import generate_summary  
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload-audio")
def upload_audio(file: UploadFile = File(...)):
    # ✅ Cross-platform temp directory (Windows + Linux + Vercel)
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)

    # Save file safely
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process audio
    text = transcribe_audio(file_path)
    summary = generate_summary(text)

    # Optional cleanup (good practice)
    try:
        os.remove(file_path)
    except:
        pass

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "transcript": text,
        "summary": summary
    }