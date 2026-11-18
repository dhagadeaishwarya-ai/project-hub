import pytest
from jose import JWTError
from app.security import hash_password, verify_password, create_access_token, decode_token


def test_hash_differs_from_plain_text_and_verifies():
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_wrong_password_fails():
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    assert verify_password("WrongPassword123!", hashed) is False


def test_expired_token_is_rejected():
    token = create_access_token(
        subject="test@example.com",
        role="student",
        expires_minutes=-5  # expired 5 minutes ago
    )

    with pytest.raises(JWTError):
        decode_token(token)
