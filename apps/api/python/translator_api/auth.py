"""Backward-compatibility shim.

Legacy code imports `translator_api.auth.UserIdentity`; the real class
lives in `translator_api.security.identity`. Re-export here so callers
keep working without a refactor.
"""

from translator_api.security.identity import UserIdentity

__all__ = ["UserIdentity"]
