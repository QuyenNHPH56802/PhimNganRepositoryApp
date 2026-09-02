"""Security & auth package."""

from __future__ import annotations

from translator_api.security.session import (
    SessionError,
    issue_session_jwt,
    verify_session_jwt,
)
from translator_api.security.rbac import Role, require_project_role
from translator_api.security.csrf import CsrfTokenError, issue_csrf_token, verify_csrf_token
from translator_api.security.consent import (
    ConsentActionError,
    grant_consent,
    revoke_consent,
    request_consent,
)
from translator_api.security.identity import UserIdentity

__all__ = [
    "ConsentActionError",
    "CsrfTokenError",
    "Role",
    "SessionError",
    "UserIdentity",
    "grant_consent",
    "issue_csrf_token",
    "issue_session_jwt",
    "request_consent",
    "require_project_role",
    "revoke_consent",
    "verify_csrf_token",
    "verify_session_jwt",
]