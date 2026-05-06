# import whisper

# model = whisper.load_model("tiny")

# def transcribe_audio(file_path):
#     result = model.transcribe(file_path)
#     return result["text"]


import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_audio(file_path: str) -> str:
    with open(file_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=f
        )
    return transcript.text