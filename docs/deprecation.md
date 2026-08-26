# Deprecation Policy

## Goals

- Public APIs are deprecated for at least one minor release before removal.
- Removal dates are explicit (`Removal: YYYY-MM-DD` next to `@deprecated`).
- `scripts/check_deprecations.py` fails CI when any removal date is past.

## Workflow

1. Mark a function as deprecated:
   ```python
   @deprecated("Use new_func instead")
   def old_func(...): ...

   def old_func(...):
       """..."""
       # Removal: 2026-12-31
       ...
   ```

2. Add a `DeprecationWarning` at the start of the body:
   ```python
   warnings.warn("old_func is deprecated; use new_func", DeprecationWarning, stacklevel=2)
   ```

3. Update the timeline below with a short rationale.

4. CI `python scripts/check_deprecations.py` enforces removal dates.

## Timeline

| Symbol | Introduced | Deprecated | Removal | Replacement |
|--------|-----------|-----------|---------|-------------|
| `QualityMode.FAST` | 0.9.0 | 1.0.0 | 2027-01-01 | `QualityMode.BALANCED` |
| `quality_mode` query param | 0.9.0 | 1.0.0 | 2027-01-01 | request body |
| `wav2vec2_legacy_provider` | 0.5.0 | 0.9.0 | 2026-12-31 | `whisperx_provider` |

## Removing a symbol

1. Run `git grep` for the symbol.
2. Update callers.
3. Remove the `@deprecated` block.
4. Drop the row from the timeline above.
5. Re-run `python scripts/check_deprecations.py`.

## Communication

Deprecations appear in `releases/vX.Y.Z.md`. Critical deprecations are
also announced on Slack `#ops-translator` with 30-day notice.