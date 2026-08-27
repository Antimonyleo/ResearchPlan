# Contributing

Keep one canonical `rescamp/SKILL.md`. Do not add host-specific instruction forks. Put detailed guidance in focused one-level references and deterministic behavior in dependency-free scripts when possible.

Before a pull request:

```bash
pip install jsonschema   # development and release checks only; the skill runtime is stdlib-only
python3 scripts/validate_release.py --root .
```

Behavior changes require tests and at least one scenario showing the intended gain without excessive interview burden. Public scenarios are calibration cases; do not use them alone for performance claims. Never commit credentials, private benchmark keys, restricted data, or human-subject information.
