"""Pruebas de las primitivas criptográficas (bcrypt, JWT, tokens)."""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    PasswordPolicyError,
    assert_password_policy,
    create_access_token,
    decode_access_token,
    generate_reset_token,
    hash_password,
    password_policy_violations,
    verify_password,
)


# ----------------------------------------------------------------------
# Contraseñas
# ----------------------------------------------------------------------
def test_hash_password_produces_bcrypt_hash() -> None:
    hashed = hash_password("Banned2024Admin", rounds=4)
    assert hashed.startswith("$2b$")
    assert "Banned2024Admin" not in hashed
    assert verify_password("Banned2024Admin", hashed) is True
    assert verify_password("otra-clave", hashed) is False


def test_hash_is_salted() -> None:
    primero = hash_password("Banned2024Admin", rounds=4)
    segundo = hash_password("Banned2024Admin", rounds=4)
    assert primero != segundo  # sal aleatoria distinta en cada hash


def test_verify_password_with_none_or_corrupted_hash_returns_false() -> None:
    assert verify_password("cualquiera", None) is False
    assert verify_password("cualquiera", "no-es-un-hash") is False
    assert verify_password("cualquiera", "") is False


def test_hash_password_rejects_more_than_72_bytes() -> None:
    with pytest.raises(PasswordPolicyError):
        hash_password("a" * 73, rounds=4)


@pytest.mark.parametrize(
    "contrasena",
    [
        "corta1A",  # menor a 12 caracteres
        "todoenminusculas1",  # sin mayúscula
        "SINNUMEROS123",  # sin minúscula
        "SolamenteLetras",  # sin número
    ],
)
def test_password_policy_rejects_weak_passwords(contrasena: str) -> None:
    assert password_policy_violations(contrasena) != []


def test_password_policy_violations_are_descriptive() -> None:
    sin_mayusculas = password_policy_violations("1234567890")
    assert any("mayúscula" in violation for violation in sin_mayusculas)
    assert any("minúscula" in violation for violation in sin_mayusculas)

    # "corta" tiene minúscula pero ni mayúscula, ni número, ni largo suficiente.
    cortas = password_policy_violations("corta")
    assert any("12 caracteres" in violation for violation in cortas)
    assert any("mayúscula" in violation for violation in cortas)
    assert any("número" in violation for violation in cortas)

    larga = password_policy_violations("A1" + "a" * 72)
    assert any("72 bytes" in violation for violation in larga)

    assert any(
        "común" in violation
        for violation in password_policy_violations("Administrador1")
    )


def test_assert_password_policy_raises_with_all_violations() -> None:
    with pytest.raises(PasswordPolicyError) as excinfo:
        assert_password_policy("123")
    assert len(excinfo.value.violations) >= 3


def test_strong_password_passes_policy() -> None:
    assert assert_password_policy("Banned2024Admin") is None
    assert password_policy_violations("Banned2024Admin") == []


# ----------------------------------------------------------------------
# Tokens de recuperación
# ----------------------------------------------------------------------
def test_generate_reset_token_is_url_safe_and_unique() -> None:
    primero = generate_reset_token()
    segundo = generate_reset_token()
    assert primero != segundo
    assert len(primero) >= 43  # 256 bits en base64url
    assert all(char.isalnum() or char in "-_" for char in primero)


# ----------------------------------------------------------------------
# JWT
# ----------------------------------------------------------------------
def test_access_token_round_trip() -> None:
    token, expires_in = create_access_token(
        subject="admin-uuid", session_version=3, role="admin", expires_minutes=15
    )
    payload = decode_access_token(token)
    assert payload.subject == "admin-uuid"
    assert payload.session_version == 3
    assert payload.role == "admin"
    assert expires_in == 900
    assert payload.expires_at > datetime.now(timezone.utc)


def test_access_token_contains_required_claims() -> None:
    token, _ = create_access_token(subject="admin-uuid", session_version=1, role="admin")
    claims = jwt.decode(token, options={"verify_signature": False})
    for claim in ("sub", "iss", "aud", "jti", "iat", "nbf", "exp", "ver", "role"):
        assert claim in claims


def test_expired_token_raises_expired_error() -> None:
    token, _ = create_access_token(
        subject="admin-uuid", session_version=1, role="admin", expires_minutes=-1
    )
    with pytest.raises(ExpiredTokenError):
        decode_access_token(token)


def test_token_signed_with_another_secret_is_rejected() -> None:
    otro_secreto = jwt.encode(
        {
            "sub": "admin-uuid",
            "iss": "bannedbyabrejeet:service1",
            "aud": "bannedbyabrejeet:admin-console",
            "ver": 1,
            "jti": "x",
            "iat": int(time.time()),
            "nbf": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        "otro-secreto-que-no-es-el-del-servicio-32b",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(otro_secreto)


def test_token_without_expiration_is_rejected() -> None:
    # Un token sin "exp" debe rechazarse (política "require").
    token = jwt.encode({"sub": "x"}, "secreto", algorithm="HS256")
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_with_wrong_audience_is_rejected() -> None:
    otro = jwt.encode(
        {
            "sub": "admin-uuid",
            "iss": "bannedbyabrejeet:service1",
            "aud": "otro-consola",
            "ver": 1,
            "jti": "x",
            "iat": int(time.time()),
            "nbf": int(time.time()),
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        },
        "secreto-de-pruebas-bannedbyabrejeet-32bytes-minimo",
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(otro)
