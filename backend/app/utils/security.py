import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Account lockout tracking store: username -> {"attempts": int, "locked_until": datetime}
_login_attempts: Dict[str, dict] = {}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def is_account_locked(username: str) -> Tuple[bool, Optional[int]]:
    """
    Checks if an account is currently locked out due to excessive failed attempts.
    Returns (is_locked, remaining_minutes).
    """
    record = _login_attempts.get(username)
    if not record:
        return False, None

    locked_until = record.get("locked_until")
    if locked_until:
        now = datetime.utcnow()
        if now < locked_until:
            remaining_secs = int((locked_until - now).total_seconds())
            remaining_mins = max(1, (remaining_secs + 59) // 60)
            return True, remaining_mins
        else:
            # Lockout expired
            _login_attempts.pop(username, None)
            return False, None
    return False, None

def record_failed_login(username: str) -> int:
    """
    Records a failed login attempt. If max attempts reached, sets lockout timer.
    Returns current attempt count.
    """
    now = datetime.utcnow()
    record = _login_attempts.get(username, {"attempts": 0, "locked_until": None})
    
    # If previous lockout expired, reset attempts
    if record.get("locked_until") and now >= record["locked_until"]:
        record = {"attempts": 0, "locked_until": None}

    record["attempts"] += 1

    if record["attempts"] >= settings.MAX_LOGIN_ATTEMPTS:
        record["locked_until"] = now + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)

    _login_attempts[username] = record
    return record["attempts"]

def reset_failed_logins(username: str):
    """
    Resets failed login attempts for a username upon successful login.
    """
    _login_attempts.pop(username, None)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
