import os
import logging
from typing import Optional
import jwt

SECRET = os.getenv("NEXTAUTH_SECRET", "")

def verify_token(token: str) -> Optional[dict]:
    if not SECRET:
        logging.warning("NEXTAUTH_SECRET is not set")
        return None
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        print(f"Decoded payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        logging.info("JWT expired")
    except jwt.InvalidTokenError as e:
        print(f"Token error: {e}")
    return None