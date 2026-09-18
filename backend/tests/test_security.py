import pytest
from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    record_failed_login,
    is_account_locked,
    reset_failed_logins
)

def test_password_hashing():
    raw_pass = "Admin@KKWagh2026"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation():
    data = {"sub": "admin", "role": "admin"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 20

def test_account_lockout_mechanism():
    user = "test_user_lockout"
    reset_failed_logins(user)

    # 4 failed attempts should not lock account
    for _ in range(4):
        record_failed_login(user)
    
    is_locked, _ = is_account_locked(user)
    assert is_locked is False

    # 5th failed attempt should trigger lockout
    record_failed_login(user)
    is_locked, remaining_mins = is_account_locked(user)
    assert is_locked is True
    assert remaining_mins > 0

    # Reset cleans lockout
    reset_failed_logins(user)
    is_locked_reset, _ = is_account_locked(user)
    assert is_locked_reset is False
