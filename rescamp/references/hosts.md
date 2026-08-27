# Hosts and installation

One canonical `rescamp/` tree serves Claude Code and Codex. Install it with the standard
Skills CLI:

```bash
npx skills add Antimonyleo/ResearchPlan --skill rescamp -g \
  -a claude-code -a codex -y
```

Omit `-g` for project scope. Add `--copy` when symlinks are undesirable. The installer
requires Node.js 18+; the installed skill requires only Python 3.9+.

| Host | User scope | Project scope | Invoke | Explicit-only policy |
|---|---|---|---|---|
| Claude Code | `~/.claude/skills/rescamp` | `.claude/skills/rescamp` | `/rescamp <Mode>` | `disable-model-invocation: true` in `SKILL.md` |
| Codex | `~/.agents/skills/rescamp` | `.agents/skills/rescamp` | `/rescamp <Mode>` | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |

The canonical, portable user mode tokens are `Camp-auto`, `Camp-brief`, and `Camp-full`.
Use the same spelling and capitalization on both hosts. Other harnesses may expose a different
explicit wrapper, but must pass the same mode token and preserve the same state transitions.

Claude Code's frontmatter field is host-specific. This bundle targets Claude Code and Codex;
it is not packaged for claude.ai skill uploads, whose frontmatter rules are narrower.

## Live acceptance

The repository's `scripts/host_acceptance.py` can render any canonical mode without launching
the selected host:

```bash
python3 scripts/host_acceptance.py --host codex --project /path/to/project \
  --mode Camp-auto --goal "Does intervention X change outcome Y?" --dry-run
python3 scripts/host_acceptance.py --host codex --project /path/to/project \
  --mode Camp-brief --goal "Does intervention X change outcome Y?" --dry-run
python3 scripts/host_acceptance.py --host codex --project /path/to/project \
  --mode Camp-full --goal "Does intervention X change outcome Y?" --dry-run
```

Use `--host claude-code` to check Claude Code syntax. For a live run, remove `--dry-run` and
add one or more `--expect <project-relative-path>` arguments. Every non-help live run requires
at least one expected artifact, and each expected artifact must be created or changed. When
the host chooses the campaign slug, use `--expect-glob
'research-campaigns/*/state/campaign.json'` instead of guessing that identifier.

The receipt records the host version, the installed skill-tree digest and its comparison with
the repository's canonical `rescamp/` bytes, response hashes, elapsed time, and before/after
fingerprints for expected artifacts. A pre-existing unchanged file cannot pass.
The completeness check accepts the installer's whole-tree symlink as well as a copied tree,
but rejects missing or unexpected files and symlinks nested inside the canonical tree.
This proves only that invocation completed and created or changed the named files; it does not
judge the research plan or prove reviewer independence.

`rescamp/scripts/validate_skill.py` is intentionally local: it validates the tree supplied to
it and has no external canonical source. Repository host acceptance is the check that compares
an installed tree with this repository's `rescamp/` bytes.

Run live acceptance only in a trusted project: the selected coding host can execute project
instructions with the permissions granted to that host.

## Degrade honestly

If the host cannot create a separate reviewer context, produce the review packet and report
that the independence requirement is unmet. If it cannot persist files or run Python, explain
that deterministic state, validation, and audit are unavailable rather than pretending they ran.
