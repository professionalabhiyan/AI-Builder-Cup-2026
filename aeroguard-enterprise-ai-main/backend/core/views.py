import hmac
import html
try:
    from django.http import HttpResponse, JsonResponse
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from rest_framework import status
except ImportError:
    HttpResponse = JsonResponse = Response = object
    class APIView:
        pass
    class status:
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403

try:
    from .portal_template import PORTAL_HTML
    from .totp_security import (
        generate_base32_secret,
        generate_totp_code,
        verify_totp_code,
        build_otpauth_uri,
        issue_signed_token,
        verify_signed_token,
    )
    from .ml_engine import (
        VALIDATED_INDUSTRIAL_DATASETS,
        detect_machine_anomaly,
        run_gemini_incident_investigation,
        train_hybrid_ml_xai_pipeline,
    )
except ImportError:
    from portal_template import PORTAL_HTML
    from totp_security import (
        generate_base32_secret,
        generate_totp_code,
        verify_totp_code,
        build_otpauth_uri,
        issue_signed_token,
        verify_signed_token,
    )
    from ml_engine import (
        VALIDATED_INDUSTRIAL_DATASETS,
        detect_machine_anomaly,
        run_gemini_incident_investigation,
        train_hybrid_ml_xai_pipeline,
    )

# MFA is kept in the system but held inactive by default per team configuration
SYSTEM_SECURITY_POLICY = {
    "mfa_enforced": False,
}

USERS_STORE = {
    "professionalabhiyan@gmail.com": {
        "id": "a1111111-2222-4333-8444-555555555501",
        "email": "professionalabhiyan@gmail.com",
        "password_secret": "AeroGuard@2026!",
        "full_name": "Abhiyan",
        "role": "SUPER_ADMIN",
        "department": "Operations & AI Lead",
        "is_active": True,
        "is_immutable_super_admin": True,
        "is_2fa_enabled": False,
        "is_2fa_setup_complete": True,
        "totp_secret": "JBSWY3DPEHPK3PXPJBSWY3DPEHPK3PXP",
        "pending_totp_secret": "",
    },
    "sangamshrestha104@gmail.com": {
        "id": "a1111111-2222-4333-8444-555555555502",
        "email": "sangamshrestha104@gmail.com",
        "password_secret": "AeroGuard@2026!",
        "full_name": "Sangam Shrestha",
        "role": "SUPER_ADMIN",
        "department": "ML & Security Architecture",
        "is_active": True,
        "is_immutable_super_admin": True,
        "is_2fa_enabled": False,
        "is_2fa_setup_complete": True,
        "totp_secret": "KRSXG5CTMVRXEZLUKRSXG5CTMVRXEZLU",
        "pending_totp_secret": "",
    },
    "sysadmin@aeroguard.ai": {
        "id": "a1111111-2222-4333-8444-555555555503",
        "email": "sysadmin@aeroguard.ai",
        "password_secret": "AeroGuard@2026!",
        "full_name": "Plant Floor System Admin",
        "role": "SYSTEM_ADMIN",
        "department": "Bay A Production",
        "is_active": True,
        "is_immutable_super_admin": False,
        "is_2fa_enabled": False,
        "is_2fa_setup_complete": False,
        "totp_secret": "MFRGGZDFMZTWQ2LKN5XWC3DPEHPK3PXP",
        "pending_totp_secret": "",
    }
}


def sanitize_user_dict(user):
    """Strip sensitive secrets before returning user profile to clients."""
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "department": user["department"],
        "is_active": user["is_active"],
        "is_immutable_super_admin": user.get("is_immutable_super_admin", user["role"] == "SUPER_ADMIN"),
        "is_2fa_setup_complete": user["is_2fa_setup_complete"],
    }


def can_delete_or_demote_user(actor_email: str, target_email: str):
    """
    Enforces Peer Super Admin Immutability:
    1. A Super Admin CANNOT delete, deactivate, or demote another Super Admin (or themselves).
    2. Only SYSTEM_ADMIN accounts can be removed by a SUPER_ADMIN.
    """
    actor = USERS_STORE.get(str(actor_email).strip().lower())
    target = USERS_STORE.get(str(target_email).strip().lower())
    if not actor or actor.get("role") != "SUPER_ADMIN":
        return False, "Only a Super Admin can manage user accounts."
    if not target:
        return False, "Target user account not found."
    if target.get("role") == "SUPER_ADMIN" or target.get("is_immutable_super_admin"):
        return False, "Security Policy Violation: Peer Super Admin accounts are immutable and cannot be removed or demoted."
    if actor["email"] == target["email"]:
        return False, "Security Policy Violation: You cannot delete your own account."
    return True, "Allowed"


def portal_home_view(request):
    """Serves the clean FactoryMind Industrial Dashboard on GET /"""
    return HttpResponse(PORTAL_HTML, content_type="text/html; charset=utf-8")


def health_check_view(request):
    """Serves 200 OK live system status on GET /health/ and GET /api/v1/health/"""
    return JsonResponse({
        "status": "HEALTHY",
        "service": "FactoryMind-Industrial-Operations-API",
        "version": "2.5.0",
        "ml_accuracy_pct": 97.78,
        "mfa_status": "ENFORCED" if SYSTEM_SECURITY_POLICY["mfa_enforced"] else "ON_HOLD_INACTIVE",
        "peer_super_admin_protection": "ACTIVE_IMMUTABLE",
        "super_admins": ["professionalabhiyan@gmail.com", "sangamshrestha104@gmail.com"],
    })


def favicon_view(request):
    return HttpResponse(status=204)


class AuthLoginAPIView(APIView):
    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        password = str(request.data.get("password", ""))
        user = USERS_STORE.get(email)

        if not user or not user.get("is_active", True):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # Constant-time password comparison to prevent timing side-channel attacks
        expected_pw = user.get("password_secret", "AeroGuard@2026!")
        if not hmac.compare_digest(password.encode("utf-8"), expected_pw.encode("utf-8")):
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # When MFA is on hold (default), issue full session token immediately after password check
        if not SYSTEM_SECURITY_POLICY.get("mfa_enforced", False):
            access_token = issue_signed_token(
                {"email": user["email"], "user_id": user["id"], "role": user["role"], "scope": "full_session"},
                ttl_seconds=28800
            )
            return Response({
                "status": "AUTHENTICATED",
                "mfa_status": "ON_HOLD",
                "access_token": access_token,
                "user": sanitize_user_dict(user),
            })

        # If MFA is enabled in settings, proceed to 2FA verification stage
        pre_auth_token = issue_signed_token(
            {"email": email, "user_id": user["id"], "scope": "pre_auth_2fa"},
            ttl_seconds=600
        )
        next_step = "VERIFY_2FA" if user["is_2fa_setup_complete"] else "SETUP_2FA_REQUIRED"
        return Response({
            "status": next_step,
            "pre_auth_token": pre_auth_token,
            "user_uuid": user["id"],
            "email": user["email"],
            "role": user["role"],
            "is_2fa_setup_complete": user["is_2fa_setup_complete"],
        })


class TwoFASetupAPIView(APIView):
    def post(self, request):
        token = request.data.get("pre_auth_token") or request.headers.get("X-Pre-Auth-Token", "")
        try:
            claims = verify_signed_token(token, expected_scope="pre_auth_2fa")
        except ValueError as err:
            return Response({"error": str(err)}, status=status.HTTP_401_UNAUTHORIZED)

        user = USERS_STORE.get(claims["email"])
        if not user["pending_totp_secret"]:
            user["pending_totp_secret"] = user["totp_secret"] or generate_base32_secret(32)

        secret = user["pending_totp_secret"]
        otpauth_uri = build_otpauth_uri(user["email"], secret)
        return Response({
            "user_uuid": user["id"],
            "email": user["email"],
            "secret": secret,
            "otpauth_uri": otpauth_uri,
            "issuer": "AeroGuard-FactoryMind",
            "current_demo_otp": generate_totp_code(secret),
        })


class TwoFAVerifyAPIView(APIView):
    def post(self, request):
        token = request.data.get("pre_auth_token") or request.headers.get("X-Pre-Auth-Token", "")
        otp_code = str(request.data.get("otp_code", "")).strip()
        try:
            claims = verify_signed_token(token, expected_scope="pre_auth_2fa")
        except ValueError as err:
            return Response({"error": str(err)}, status=status.HTTP_401_UNAUTHORIZED)

        user = USERS_STORE.get(claims["email"])
        active_secret = user["pending_totp_secret"] or user["totp_secret"]
        if not verify_totp_code(active_secret, otp_code, valid_window=1):
            return Response(
                {"error": "Invalid 6-digit Google Authenticator OTP code."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user["pending_totp_secret"]:
            user["totp_secret"] = user["pending_totp_secret"]
            user["pending_totp_secret"] = ""
        user["is_2fa_setup_complete"] = True

        access_token = issue_signed_token(
            {"email": user["email"], "user_id": user["id"], "role": user["role"], "scope": "full_session"},
            ttl_seconds=28800
        )
        return Response({
            "status": "AUTHENTICATED",
            "access_token": access_token,
            "user": sanitize_user_dict(user),
        })


class UserManagementAPIView(APIView):
    def get(self, request):
        return Response({
            "users": [sanitize_user_dict(u) for u in USERS_STORE.values()],
            "mfa_enforced": SYSTEM_SECURITY_POLICY["mfa_enforced"],
        })

    def post(self, request):
        actor_email = str(request.data.get("actor_email", "professionalabhiyan@gmail.com")).strip().lower()
        actor = USERS_STORE.get(actor_email)
        if not actor or actor.get("role") != "SUPER_ADMIN":
            return Response({"error": "Only a Super Admin can create accounts."}, status=status.HTTP_403_FORBIDDEN)

        email = html.escape(str(request.data.get("email", "")).strip().lower())
        full_name = html.escape(str(request.data.get("full_name", "System Admin")).strip())
        department = html.escape(str(request.data.get("department", "Operations")).strip())
        if not email or "@" not in email:
            return Response({"error": "Valid email address is required."}, status=status.HTTP_400_BAD_REQUEST)
        if email in USERS_STORE:
            return Response({"error": "Account already exists."}, status=status.HTTP_400_BAD_REQUEST)

        USERS_STORE[email] = {
            "id": f"a1111111-2222-4333-8444-{len(USERS_STORE) + 555555555501}",
            "email": email,
            "password_secret": "AeroGuard@2026!",
            "full_name": full_name,
            "role": "SYSTEM_ADMIN",
            "department": department,
            "is_active": True,
            "is_immutable_super_admin": False,
            "is_2fa_enabled": False,
            "is_2fa_setup_complete": False,
            "totp_secret": generate_base32_secret(32),
            "pending_totp_secret": "",
        }
        return Response({"status": "CREATED", "user": sanitize_user_dict(USERS_STORE[email])}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        actor_email = str(request.data.get("actor_email", "professionalabhiyan@gmail.com")).strip().lower()
        target_email = str(request.data.get("target_email", "")).strip().lower()
        allowed, reason = can_delete_or_demote_user(actor_email, target_email)
        if not allowed:
            return Response({"error": reason}, status=status.HTTP_403_FORBIDDEN)

        del USERS_STORE[target_email]
        return Response({"status": "DELETED", "deleted_email": target_email})
