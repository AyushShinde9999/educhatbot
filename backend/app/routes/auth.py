from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserResponse, LoginRequest, UserRegister
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    is_account_locked,
    record_failed_login,
    reset_failed_logins
)
from app.utils.rate_limiter import auth_rate_limiter
from app.services.audit_service import audit_service
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(reg_data: UserRegister, request: Request, db: Session = Depends(get_db)):
    """
    Register a new Admin user account. Requires valid admin_secret key.
    """
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check_rate_limit(request, identifier=f"reg:{client_ip}")

    # Verify registration secret
    if reg_data.admin_secret.strip() != settings.ADMIN_REGISTRATION_SECRET:
        audit_service.log_action(
            db=db,
            actor=reg_data.username,
            action="REGISTER_FAILED_BAD_SECRET",
            ip_address=client_ip,
            details="Registration attempted with invalid admin secret key."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin Registration Secret Key."
        )

    username = reg_data.username.strip()
    email = reg_data.email.strip().lower()

    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is already registered."
        )

    # Hash password & create user
    new_user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash(reg_data.password),
        role="admin",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit_service.log_action(
        db=db,
        actor=username,
        action="USER_REGISTERED",
        ip_address=client_ip,
        details=f"New admin account registered: {username} ({email})"
    )

    access_token = create_access_token(data={"sub": new_user.username, "role": new_user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=new_user.username,
        role=new_user.role
    )

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate admin user and return JWT access token.
    Applies rate limiting and account lockout protection (5 failed attempts = 15 min lock).
    """
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check_rate_limit(request, identifier=f"auth:{client_ip}")

    username = login_data.username.strip()

    # Check if account is locked out
    is_locked, rem_mins = is_account_locked(username)
    if is_locked:
        audit_service.log_action(
            db=db,
            actor=username,
            action="LOGIN_BLOCKED_LOCKED",
            ip_address=client_ip,
            details=f"Login attempt blocked. Account locked for {rem_mins} more minutes."
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is temporarily locked out due to multiple failed login attempts. Please try again in {rem_mins} minutes."
        )

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        attempts = record_failed_login(username)
        audit_service.log_action(
            db=db,
            actor=username,
            action="LOGIN_FAILED",
            ip_address=client_ip,
            details=f"Failed attempt {attempts}."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Reset failed login count on clean login
    reset_failed_logins(username)
    
    audit_service.log_action(
        db=db,
        actor=username,
        action="LOGIN_SUCCESS",
        ip_address=client_ip,
        details="Successfully logged in to Admin Dashboard."
    )

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return Token(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns current authenticated admin profile.
    """
    return current_user
