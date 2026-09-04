"""
Minimal JWT auth with two roles: viewer, admin.

This is intentionally simple — an in-memory user table, not a full
identity system. Swap USERS_DB for a Postgres table + hashed lookups
if you take this further.
"""

import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt

SECRET_KEY = os.environ.get("JWT_SECRET", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


# username -> (hashed_password, role)
USERS_DB = {
    "viewer": (hash_password("viewer123"), "viewer"),
    "admin":  (hash_password("admin123"), "admin"),
}


def authenticate_user(username: str, password: str, db=None) -> str | None:
    if db is not None:
        try:
            from db.models import User
            user_rec = db.query(User).filter(User.username == username).first()
            if user_rec:
                if verify_password(password, user_rec.hashed_password):
                    return user_rec.role
                return None
        except Exception:
            pass

    record = USERS_DB.get(username)
    if not record:
        return None
    hashed, role = record
    if not verify_password(password, hashed):
        return None
    return role


def create_access_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
