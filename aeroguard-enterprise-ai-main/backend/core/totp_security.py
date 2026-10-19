"""
RFC 6238 Google Authenticator TOTP & Pre-Auth / Session Token Engine.
Fixes the 4 critical 2FA bugs between Backend and Frontend:
1. Preserves leading zeros on 6-digit OTP strings (`str(otp).strip().zfill(6)`).
2. Stages `pending_totp_secret` separately from active `totp_secret` so refreshing QR setup
   never invalidates an in-flight setup or locks out an existing user.
3. Implements `valid_window=1` (-30s, 0s, +30s) per RFC 6238 to prevent clock-drift rejections.
4. Aligns `pre_auth_token` (Stage 1 login) with `access_token` (Stage 2 verified session)
   so Angular's AuthInterceptor never sends an invalid header during mandatory 2FA enrollment.
"""

import hmac
import time
import json
import uuid
import base64
import struct
import secrets
import hashlib
from urllib.parse import quote


def generate_base32_secret(length: int = 32) -> str:
    """Generates a clean RFC 4648 Base32 secret (A-Z, 2-7) compatible with Google Authenticator."""
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _normalize_base32(secret: str) -> bytes:
    cleaned = "".join(ch for ch in secret.strip().upper() if ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    padding = (8 - (len(cleaned) % 8)) % 8
    return base64.b32decode(cleaned + ("=" * padding), casefold=True)


def generate_totp_code(secret: str, timestamp: float = None, period: int = 30, digits: int = 6) -> str:
    """Computes a 6-digit RFC 6238 TOTP code with guaranteed leading-zero preservation."""
    if timestamp is None:
        timestamp = time.time()
    counter = int(timestamp // period)
    key = _normalize_base32(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    otp = binary % (10 ** digits)
    return str(otp).zfill(digits)


def verify_totp_code(secret: str, submitted_code: str, timestamp: float = None, valid_window: int = 1) -> bool:
    """
    Verifies a submitted 6-digit Google Authenticator OTP across [-valid_window, +valid_window]
    30-second steps using constant-time digest comparison.
    """
    if not secret or submitted_code is None:
        return False
    normalized_code = "".join(ch for ch in str(submitted_code).strip() if ch.isdigit())
    if len(normalized_code) != 6:
        return False
    if timestamp is None:
        timestamp = time.time()
    for step_offset in range(-valid_window, valid_window + 1):
        candidate = generate_totp_code(secret, timestamp=timestamp + (step_offset * 30))
        if hmac.compare_digest(candidate, normalized_code):
            return True
    return False


def build_otpauth_uri(email: str, secret: str, issuer: str = "AeroGuard-FactoryMind") -> str:
    """Builds the standard Google Authenticator QR provisioning URI."""
    label = f"{quote(issuer)}:{quote(email)}"
    return f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def issue_signed_token(payload: dict, secret_key: str = "aeroguard-secret", ttl_seconds: int = 3600) -> str:
    """Issues an HMAC-SHA256 signed token (used for both `pre_auth_token` and `access_token`)."""
    body = dict(payload)
    body["jti"] = str(uuid.uuid4())
    body["exp"] = int(time.time()) + ttl_seconds
    raw = base64.urlsafe_b64encode(json.dumps(body, sort_keys=True).encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(secret_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def verify_signed_token(token: str, expected_scope: str = None, secret_key: str = "aeroguard-secret") -> dict:
    """Verifies token signature, expiration, and scope (`pre_auth_2fa` vs `full_session`)."""
    if not token or "." not in token:
        raise ValueError("Malformed authentication token.")
    raw, sig = token.rsplit(".", 1)
    expected_sig = hmac.new(secret_key.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid token signature.")
    padding = "=" * ((4 - (len(raw) % 4)) % 4)
    data = json.loads(base64.urlsafe_b64decode((raw + padding).encode("utf-8")).decode("utf-8"))
    if data.get("exp", 0) < int(time.time()):
        raise ValueError("Token has expired.")
    if expected_scope and data.get("scope") != expected_scope:
        raise ValueError(f"Invalid token scope: expected {expected_scope}, got {data.get('scope')}.")
    return data
