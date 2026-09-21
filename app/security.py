import base64, hashlib, hmac, json, os, time
from app.config import SECRET


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return base64.urlsafe_b64encode(salt + digest).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.urlsafe_b64decode(stored.encode())
        salt, expected = raw[:16], raw[16:]
        actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_token(student_id: int) -> str:
    payload = {'sub': str(student_id), 'exp': int(time.time()) + 60 * 60 * 8}
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':')).encode()).decode().rstrip('=')
    sig = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + '.' + sig


def decode_token(token: str):
    try:
        body, sig = token.split('.', 1)
        good = hmac.compare_digest(sig, hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).hexdigest())
        if not good:
            return None
        payload = json.loads(base64.urlsafe_b64decode(body + '=' * ((4 - len(body) % 4) % 4)))
        if payload.get('exp', 0) < time.time():
            return None
        return payload
    except Exception:
        return None
