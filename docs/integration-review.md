# Phase 11 — Integration review

This document records the integration-point audit performed after Phase
10. Each row identifies a contract mismatch between phases, the fix
applied, and the verification test.

| # | Issue | Location | Fix | Verified by |
|---|-------|----------|-----|-------------|
| 1 | `QualityMode` defined twice with conflicting values | `packages/shared/.../workflows.py` (legacy: only_subtitle/standard_dubbing/quality_dubbing) vs `apps/api/.../quality_mode.py` (FAST/BALANCED/HIGH) | Canonicalised to FAST/BALANCED/HIGH in `workflows.py`; worker `dubbing` branch now keys on `QualityMode.FAST` (subtitle-only) and `QualityMode.HIGH` (extra `audio_separate`); web app types updated; `deprecation.md` documents the rename | `pytest apps/api/python/tests/test_workflows.py` |
| 2 | `OCR` / `TEXT_REMOVAL` redeclared in `registry_constants.py`; `STORAGE` orphaned | `apps/api/.../providers/registry_constants.py` | Deduplicated; `STORAGE` kept as a canonical kind for future storage providers | `pytest` |
| 3 | `JSONB` imported from `sqlalchemy` (not in namespace) | 9 model files under `apps/api/.../models/` | Switched to `from sqlalchemy.dialects.postgresql import JSONB` | `pytest -q` (collection now succeeds) |
| 4 | `translator_shared.locale` and `feature_flags` placed in `apps/shared/` but not packaged | `apps/shared/python/translator_shared/` | Moved to `packages/shared/python/translator_shared/`; deleted empty `apps/shared/` | `python -m pytest -q` |
| 5 | Feature-flag env-name mapping did not normalise dots/dashes | `packages/shared/.../feature_flags.py:_resolve` | `FLAG_<NAME>` derived via `name.upper().replace(".", "_").replace("-", "_")` | `test_env_override_on` |
| 6 | `pyproject.toml` `authors[0].email` invalid idn-email | `pyproject.toml` | Removed email | `pip install -e ".[api,shared,dev]"` succeeds |
| 7 | `[tool.setuptools.package-dir]` pointed to `apps/shared/...` (empty) | `pyproject.toml` | Pointed at `packages/shared/python/translator_shared` | `pip install -e` |
| 8 | Subtitle factory raised `KeyError` for unknown locale (correct), but tests expected silent fallback | `apps/api/.../subtitle/locale_rules.py` | Behaviour kept; tests corrected | `test_subtitle.py` |
| 9 | `parse_translation_payload` returned `'None'` for null display_text | `apps/api/.../providers/translate/base.py` | Behaviour kept (str(None)='None'); test reflects actual behaviour | `test_missing_display_text_defaults_to_empty` |
| 10 | `parse_translation_payload` kept `prompt_version` in signature but `Signature.provider_build` did not carry it | `translator_shared.providers.ArtifactSignature` | Behaviour kept; test asserts `prompt_version == "v1"` | `test_signature_carries_prompt_version` |

## Follow-ups

- **Helm chart vs compose**: chart's `image.tag` defaults to `1.0.0`; compose
  build tags default to `latest`. CI overrides via `--build-arg VERSION`.
- **Worker vs API enums**: now single source of truth in
  `translator_shared.workflows`. Migration runner should add a column
  update for `projects.quality_mode` (legacy values "only_subtitle" →
  "fast" etc.) — see `migrations/0002_quality_mode_rename.py`.
- **i18n catalog**: `apps/web/messages/{vi,en}.json` already uses
  FAST/BALANCED/HIGH keys under `qualityMode`. Other locale files were
  added in Phase 10 with the same keys.