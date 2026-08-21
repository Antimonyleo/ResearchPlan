# Campaign object field vocabulary

`add` rejects fields outside this vocabulary, so use these exact names. Print any
entry at runtime with `scripts/rescamp.py schema <path>`, or list the paths with
`scripts/rescamp.py schema list`. **Required** fields are the ones deterministic
validation blocks on; the rest are optional but are rendered when present.

Every field of these objects is rendered into `CAMPAIGN_PROMPT.md`, including keys outside
the spec, so record only what changes the research decision.

Two caveats. `add` enforces this vocabulary; `set` with a whole subtree does **not**. A
misspelled field loaded via `set` is stored, never validated, and then rendered into
`CAMPAIGN_PROMPT.md` as authoritative content, sitting beside the real field it was meant
to be. That is the hazard: not that the typo disappears, but that it does not.

And `sketch`, top-level `assumptions`, and `contradictions` are campaign state that the
prompt does not render — they inform the interview and the review, not the execution brief.

The dict-valued sections (`campaign.mission`, `constitution`, `evaluation`,
`resources_dispatch`, `runtime`, `ethics_rights_safety`, `reporting`, `kickoff`) are written
with `set`, not `add`, and have no table here; their required fields are reported by
`validate` and listed in `references/architecture.md`.

## `campaign.dossier.objects`

One object. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `description` | no | Description. |
| `current_state` | no | Current state. |
| `boundary` | no | Boundary. |
| `name` | no | Name. |

## `campaign.dossier.source_hierarchy`

One source. Heading is `id` plus `source`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `tier` | no | Tier. |
| `admissibility` | no | Admissibility. |
| `limitations` | no | Known limitations. |
| `source` | no | Source. |

## `campaign.dossier.context`

One context item. Heading is `id` plus `summary`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `relevance` | no | Why it changes the design. |
| `summary` | no | Summary. |

## `campaign.dossier.access_rights`

One access record. Heading is `id` plus `resource`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `rights` | no | Rights. |
| `approval` | no | Approval. |
| `expiry` | no | Expiry. |
| `resource` | no | Resource. |

## `campaign.dossier.alternatives`

One alternative. Heading is `id` plus `account`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `evidence` | no | Existing evidence. |
| `status` | no | Status. |
| `account` | no | Account. |

## `campaign.inquiries`

One inquiry. Heading is `id` plus `question_or_claim`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `importance` | **yes** | Why it matters. |
| `admissible_support` | **yes** | Admissible support. |
| `counterevidence_or_rival` | **yes** | Counterevidence, rival explanation, reading, or objection. |
| `discriminating_implication` | no | Discriminating prediction or interpretive implication. |
| `verification_or_adjudication` | **yes** | Verification or adjudication. |
| `uncertainty_boundary` | no | Uncertainty and external-validity boundary. |
| `reporting_rule` | **yes** | Reporting rule. |
| `question_or_claim` | **yes** | Question or claim. |

## `campaign.methods`

One method. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `purpose` | **yes** | Purpose. |
| `inquiry_ids` | no | Answers inquiries. |
| `inputs` | no | Inputs. |
| `outputs` | **yes** | Outputs. |
| `assumptions` | no | Assumptions. |
| `limitations` | **yes** | Limitations. |
| `cost` | no | Cost. |
| `dependencies` | no | Dependencies. |
| `can_change_decision` | no | Decision it can change. |
| `name` | no | Name. |

## `campaign.tools`

One tool. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `identity_version` | no | Identity and version. |
| `production` | no | Production use. |
| `purpose` | no | Purpose. |
| `access` | no | Access. |
| `access_license` | no | Access and licence. |
| `license` | no | License or rights. |
| `documentation` | no | Authoritative documentation. |
| `name` | no | Name. |

## `campaign.canaries`

One canary. Heading is `id` plus `production_like_test`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `tool_id` | **yes** | Tool. |
| `expected_artifacts` | **yes** | Expected artifacts and schema. |
| `sanity_checks` | **yes** | Positive, negative, and sanity cases. |
| `downstream_acceptance` | **yes** | Downstream acceptance. |
| `quarantine_rules` | no | Quarantine triggers. |
| `production_like_test` | **yes** | Production like test. |

## `campaign.stages`

One stage. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `purpose` | **yes** | Purpose. |
| `prerequisite_stage_ids` | no | Prerequisites. |
| `inputs` | no | Inputs. |
| `activities` | **yes** | Activities. |
| `outputs` | **yes** | Outputs. |
| `owner` | no | Owner. |
| `budget` | no | Budget. |
| `pace` | no | Expected pace. |
| `gate_id` | **yes** | Promotion gate. |
| `name` | no | Name. |

## `campaign.gates`

One gate. Heading is `id` plus `criteria`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `stage_id` | **yes** | Stage. |
| `required_evidence` | **yes** | Required evidence. |
| `owner` | **yes** | Owner. |
| `on_fail` | **yes** | On failure. |
| `criteria` | **yes** | Criteria. |

## `campaign.roles`

One role. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `description` | no | Description. |
| `responsibility` | no | Responsibility. |
| `authority` | no | Authority. |
| `limits` | no | Limits. |
| `name` | no | Name. |

## `campaign.work_units`

One work unit. Heading is `id` plus `objective`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `authoritative_inputs` | **yes** | Authoritative inputs and hashes. |
| `permitted_actions` | **yes** | Permitted actions. |
| `prohibited_actions` | **yes** | Prohibited actions. |
| `method_constraints` | no | Method and tool constraints. |
| `outputs` | **yes** | Exact outputs. |
| `acceptance_test` | **yes** | Verification and acceptance. |
| `resource_ceiling` | **yes** | Resource ceiling. |
| `retry_policy` | **yes** | Retry and failure classes. |
| `escalation` | **yes** | Escalation and handoff. |
| `dependency_ids` | no | Depends on work units (queue). |
| `approval_ids` | no | Required approvals before dispatch (queue). |
| `retry_limit` | no | Maximum retry attempts (queue). |
| `objective` | **yes** | Objective. |

## `campaign.claims`

One claim. Heading is `id` plus `statement`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `inquiry_id` | **yes** | Inquiry. |
| `support` | **yes** | Support. |
| `counterevidence_or_objections` | **yes** | Counterevidence and objections. |
| `verification` | **yes** | Verification. |
| `status` | **yes** | Status. |
| `uncertainty` | no | Uncertainty. |
| `reporting_rule` | **yes** | Reporting rule. |
| `statement` | **yes** | Statement. |

## `campaign.deliverables`

One deliverable. Heading is `id` plus `name`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `path` | **yes** | Path. |
| `schema` | no | Schema. |
| `acceptance_test` | **yes** | Acceptance test. |
| `owner` | **yes** | Owner. |
| `immutable_after_freeze` | no | Immutable after freeze. |
| `name` | **yes** | Name. |

## `blockers`

One blocker. Heading is `id` plus `description`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `severity` | no | Severity. |
| `status` | no | Status. |
| `owner` | no | Owner. |
| `unblocks` | no | Unblocked by. |
| `description` | no | Description. |

## `contradictions`

One contradiction. Heading is `id` plus `description`.

| Field | Required | Meaning |
|---|---|---|
| `id` | recommended | Stable identifier used by cross-references. |
| `importance` | no | Importance. |
| `status` | no | Status. |
| `statements` | no | Conflicting statements. |
| `description` | no | Description. |
