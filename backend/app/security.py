import hashlib, hmac, json, time
from urllib.parse import parse_qsl
from datetime import datetime, timedelta
from jose import jwt, JWTError
from .config import settings
import os, base64
ALGO="HS256"
def hash_pw(p):
    salt=os.urandom(16)
    dk=hashlib.pbkdf2_hmac("sha256", p.encode(), salt, 120000)
    return "pbkdf2$"+base64.b64encode(salt).decode()+"$"+base64.b64encode(dk).decode()
def verify_pw(p,h):
    try:
        _,s,d=h.split("$"); salt=base64.b64decode(s); expected=base64.b64decode(d)
        dk=hashlib.pbkdf2_hmac("sha256", p.encode(), salt, 120000)
        return hmac.compare_digest(dk, expected)
    except Exception: return False
def create_token(sub, role="user", extra=None):
    exp=datetime.utcnow()+timedelta(days=7)
    data={"sub":str(sub),"role":role,"exp":exp}
    if extra: data.update(extra)
    return jwt.encode(data, settings.JWT_SECRET, algorithm=ALGO)
def decode_token(t):
    try: return jwt.decode(t, settings.JWT_SECRET, algorithms=[ALGO])
    except JWTError: return None
def verify_init_data(init_data: str, bot_token: str):
    """Verify Telegram initData per docs. Returns user dict or None."""
    if not init_data or not bot_token: return None
    try:
        parsed=dict(parse_qsl(init_data, keep_blank_values=True))
        hash_val=parsed.pop("hash", None)
        if not hash_val: return None
        data_check="\n".join(f"{k}={v}" for k,v in sorted(parsed.items()))
        secret=hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calc=hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, hash_val): return None
        auth_date=int(parsed.get("auth_date",0))
        if auth_date and time.time()-auth_date>86400: return None
        user=json.loads(parsed.get("user","{}"))
        return user
    except Exception:
        return None
def make_init_data(user: dict, bot_token: str):
    """Helper for tests: create valid initData."""
    import urllib.parse
    params={"auth_date":str(int(time.time())),"query_id":"AAtest","user":json.dumps(user,separators=(",",":"))}
    data_check="\n".join(f"{k}={v}" for k,v in sorted(params.items()))
    secret=hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    h=hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    params["hash"]=h
    return urllib.parse.urlencode(params)
