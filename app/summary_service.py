import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

def generate_summary(transcript: str):
    if not transcript:
        return ["No transcript available"]

    prompt = f"""
Summarize the following transcript into concise bullet points.
Return only bullet points, one per line.

Transcript:
{transcript}
"""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=500,
        temperature=0.2,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    text = response.content[0].text

    lines = [
        line.replace("-", "").replace("•", "").strip()
        for line in text.split("\n")
        if line.strip()
    ]

    return lines