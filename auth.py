import jwt
from datetime import datetime, timedelta
from typing import Optional
import os

SECRET_KEY = os.getenv('SECRET_KEY', 'litto-watch-secret-key-2026')
ALGORITHM = 'HS256'
DUREE_TOKEN = timedelta(hours=24)

def creer_token(utilisateur_id: int, email: str) -> str:
    """Crée un token JWT"""
    payload = {
        'sub': utilisateur_id,
        'email': email,
        'exp': datetime.utcnow() + DUREE_TOKEN,
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decoder_token(token: str) -> Optional[dict]:
    """Décode et vérifie un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
