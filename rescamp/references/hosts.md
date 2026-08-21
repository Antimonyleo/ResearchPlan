# Host registry and capability contract

One canonical `rescamp/` directory and one `SKILL.md` serve every host. `SKILL.md` names no
host. Everything host-specific lives here and in per-host metadata files inside the same
bundle. **Adding a host means adding a row and a metadata file — never a line in `SKILL.md`.**

This works because each host ignores the others' metadata: Claude Code ignores
`agents/openai.yaml`, Codex ignores `skillOverrides`. Shipping the union is why the installed
trees can stay byte-identical.

## Registry

| Host | User scope | Project scope | Explicit invocation | Explicit-only mechanism |
|---|---|---|---|---|
| `claude-code` | `~/.claude/skills/rescamp` | `.claude/skills/rescamp` | `/rescamp <goal>` | `skillOverrides.rescamp: user-invocable-only` in `settings.json` (user) or `settings.local.json` (project) |
| `codex` | `~/.agents/skills/rescamp` | `.agents/skills/rescamp` | `$rescamp <goal>` | `policy.allow_implicit_invocation: false` in `agents/openai.yaml` |

Codex also reads an organization scope at `/etc/codex/skills/`; the installer does not write there.

To add a host, append a row, ship its metadata file in the bundle if it needs one, and add an
entry to the `HOSTS` registry in the repository's `scripts/install.py` (that installer lives in
the source repository, not inside this installed skill directory). If a new host requires an
instruction change in `SKILL.md`, that is a signal the instruction is host-coupled and belongs
here instead.

## Capability declarations

Capabilities are **declared, not guessed**:

```bash
scripts/rescamp.py host-probe --host-id codex --campaign <campaign> \
  --declare subagent=false --declare network=true
```

This probes what is directly testable and records the rest as you declare it, storing the result
in campaign state as `host_profile`. Anything you do not declare stays `unknown` and is treated
as absent. Gating currently consults one field: if `host_profile.subagent` is `false`, a review
record claiming `independent-subagent` is rejected. The other declarations are recorded for
audit and for your own honesty; they are not yet enforced.

| Capability | How it is established | Absent → |
|---|---|---|
| `filesystem`, `python`, `skill_dir`, `progressive_references` | probed directly by `host-probe` | no durable state: the model must improvise, and the campaign records that it did |
| `subagent` | **declared** — the host adapter or the operator asserts it | independence rungs 2–3 unavailable; high-assurance is blocked |
| `structured_question_control` | declared | prose question format (`SKILL.md`) |
| `background_execution` | declared | `runtime.enabled` stays false; produce a runbook, never claim continuous execution |
| `network` | declared | ask the user instead of researching, and say so rather than inflating the budget silently |

A capability left `unknown` is treated as absent. Never upgrade a declaration to make a gate pass.

## Independence is self-attested

`mode` on a review record is a claim by whoever wrote the record. The engine checks that the
value is legal, that reviewer identities are distinct, and that `execution_evidence` is present
for any mode claiming independence — but nothing inside this skill can observe another process
and prove a separate reviewer really ran. Treat the recorded rung as an attestation with an
audit trail, not as proof, and say so when reporting. `references/architecture.md` section 15
defines the ladder.

Where a host has a shell, the strongest portable mechanism is a **reviewer adapter**: a command
that reads a review packet on stdin and returns a `review.schema.json` object on stdout, run as
a genuinely separate process. That gives a real rung-2 reviewer on any host and makes
`execution_evidence` corroborated rather than merely asserted. The same stdin/stdout contract
the benchmark uses (`benchmark/adapters/external_command_protocol.md`) applies.

## Degrade honestly

When a capability is absent, say so in the rendered bundle. Produce review packets instead of
claiming reviews happened; produce a runbook instead of claiming a scheduler; record an unmet
condition instead of quietly lowering the bar.
