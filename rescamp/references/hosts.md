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
| Claude Code | `~/.claude/skills/rescamp` | `.claude/skills/rescamp` | `/rescamp <goal>` | `disable-model-invocation: true` in `SKILL.md` |
| Codex | `~/.agents/skills/rescamp` | `.agents/skills/rescamp` | `$rescamp <goal>` | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |

Claude Code's frontmatter field is host-specific. This bundle targets Claude Code and Codex;
it is not packaged for claude.ai skill uploads, whose frontmatter rules are narrower.

## Live acceptance

The repository's `scripts/host_acceptance.py` can exercise an explicit mode through either
installed CLI. Non-help modes require at least one expected artifact:

```bash
python3 scripts/host_acceptance.py --host codex --project /path/to/project \
  --mode start --goal "Does intervention X change outcome Y?" \
  --expect research-campaigns/example/state/campaign.json
```

The receipt records the host version, skill-tree digest, response hashes, elapsed time, and
before/after fingerprints for expected artifacts. A pre-existing unchanged file cannot pass.
This proves only that invocation completed and created or changed the named files; it does not
judge the research plan or prove reviewer independence.

## Degrade honestly

If the host cannot create a separate reviewer context, produce the review packet and report
that the independence requirement is unmet. If it cannot persist files or run Python, explain
that deterministic state, validation, and audit are unavailable rather than pretending they ran.
