# from fastapi import FastAPI, UploadFile, File
# import os
# import shutil
# import tempfile

# from app.whisper_service import transcribe_audio
# from app.summary_service import generate_summary  
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def home():
#     return {"message": "Backend Running"}

# @app.get("/health")
# def health():
#     return {"status": "ok"}

# @app.post("/upload-audio")
# def upload_audio(file: UploadFile = File(...)):
#     # ✅ Cross-platform temp directory (Windows + Linux + Vercel)
#     temp_dir = tempfile.gettempdir()
#     file_path = os.path.join(temp_dir, file.filename)

#     # Save file safely
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     # Process audio
#     text = transcribe_audio(file_path)
#     summary = generate_summary(text)

#     # Optional cleanup (good practice)
#     try:
#         os.remove(file_path)
#     except:
#         pass

#     return {
#         "message": "File uploaded successfully",
#         "filename": file.filename,
#         "transcript": text,
#         "summary": summary
#     }

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os, shutil, tempfile
from typing import Optional

from app.whisper_service import transcribe_audio
from app.summary_service import generate_summary
from app.auth import verify_token          # JWT verification helper
from app.database import db                # MongoDB connection

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── helpers ────────────────────────────────────────────────────────────────

def get_optional_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Return userId if a valid Bearer token is present, else None (guest)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    return payload.get("sub") if payload else None

def get_required_user(authorization: Optional[str] = Header(None)) -> str:
    """Like get_optional_user but raises 401 for guests."""
    user_id = get_optional_user(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

# ─── existing routes (updated) ───────────────────────────────────────────────

@app.get("/")
def home():
    return {"message": "Backend Running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload-audio")
async def upload_audio(
    file: UploadFile = File(...),
    user_id: Optional[str] = Depends(get_optional_user),
):
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    text = transcribe_audio(file_path)
    summary = generate_summary(text)

    try:
        os.remove(file_path)
    except Exception:
        pass

    # Persist to MongoDB only for authenticated users
    session_id = None
    if user_id:
        result = db.sessions.insert_one({
            "userId":     user_id,
            "filename":   file.filename,
            "transcript": text,
            "summary":    summary,
            "createdAt":  __import__("datetime").datetime.utcnow(),
        })
        session_id = str(result.inserted_id)

    return {
        "message":    "File uploaded successfully",
        "filename":   file.filename,
        "transcript": text,
        "summary":    summary,
        "sessionId":  session_id,   # None for guests
    }

# ─── history routes (auth required) ─────────────────────────────────────────

@app.get("/history")
async def get_history(user_id: str = Depends(get_required_user)):
    """Return all past sessions for the logged-in user (newest first)."""
    cursor = (
        db.sessions
        .find({"userId": user_id}, {"_id": 1, "filename": 1, "summary": 1, "createdAt": 1})
        .sort("createdAt", -1)
        .limit(50)
    )
    sessions = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        doc["createdAt"] = doc["createdAt"].isoformat()
        sessions.append(doc)
    return {"sessions": sessions}

@app.get("/history/{session_id}")
async def get_session(session_id: str, user_id: str = Depends(get_required_user)):
    """Return a single session's full transcript + summary."""
    from bson import ObjectId
    doc = db.sessions.find_one({"_id": ObjectId(session_id), "userId": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Session not found")
    doc["id"] = str(doc.pop("_id"))
    doc["createdAt"] = doc["createdAt"].isoformat()
    return doc

@app.delete("/history/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_required_user)):
    from bson import ObjectId
    result = db.sessions.delete_one({"_id": ObjectId(session_id), "userId": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": session_id}