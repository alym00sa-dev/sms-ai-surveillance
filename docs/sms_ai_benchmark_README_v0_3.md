# SMS x AI Surveillance Benchmark v0.3

## Purpose

This benchmark evaluates AI systems for an English-language prototype of community SMS disease-surveillance intake in Nigeria.

The benchmark is intentionally small: **30 scenarios**. It emphasizes realistic, multi-turn, surveillance-relevant interactions rather than broad chatbot capability.

The primary use case is AFP surveillance. Other VPD / priority-disease signals are recognized, preserved, and stopped without disease-specific follow-up.

---

## What changed in v0.3

v0.3 incorporates the final scenario review and introduces three important behaviors:

1. **Mandatory structured confirmation before AFP acceptance**
   - Once enough information is available, the agent uses `CONFIRM`, not `ACCEPT`.
   - The agent presents the complete interpreted case state and asks the sender to confirm or correct it.
   - `ACCEPT` occurs only after explicit sender confirmation.

2. **State override semantics**
   - Later sender corrections override earlier values.
   - Unaffected fields persist.
   - If a correction occurs during confirmation, the agent confirms the updated record again before acceptance.

3. **Multiple cases in one conversation**
   - The agent may maintain multiple children/cases simultaneously.
   - It must not merge separate people.
   - Follow-up information may update one, several, or all cases.
   - The final confirmation must clearly enumerate each case.

---

## Benchmark file

```text
sms_ai_benchmark_v0_3.jsonl
```

Each line is one scenario.

---

## Scenario mix

The 30 cases cover:

- straightforward AFP reports;
- missing information and clarification;
- ambiguous or messy natural-language input;
- state correction / override;
- multiple children in one conversation;
- other VPD signals;
- escalation with and without a valid underlying signal;
- duplicate and near-duplicate reports;
- irrelevant / administrative messages.

The set intentionally indexes toward surveillance-relevant interactions.

---

## Benchmark expected-state schema

The benchmark stores compact expected behavior per user turn.

Example:

```json
{
  "classification": "AFP_SUSPECTED",
  "action": "CONFIRM",
  "priority": "NORMAL",
  "cases": [
    {
      "age": 7,
      "sex": "male",
      "state": "Jigawa",
      "lga": "Kafin Hausa",
      "settlement": "Majawa",
      "symptom": "sudden weakness in both legs"
    }
  ],
  "missing_important_fields": [],
  "clarification_target": null,
  "potential_duplicate": false,
  "escalation_reason": null,
  "confirmation_status": "PENDING",
  "other_vpd": false
}
```

The benchmark annotation is intentionally more compact than the full model output schema. The harness should map:

- benchmark `cases` -> model `cases`
- benchmark `clarification_target` -> model `clarification.target`
- benchmark `escalation_reason` -> model `escalation.reason`
- benchmark `confirmation_status` -> model `confirmation.status`

---

## Action semantics

Allowed actions:

```text
ACCEPT
CLARIFY
CONFIRM
ESCALATE
OTHER_VPD
NOT_RELEVANT
```

### CONFIRM

`CONFIRM` means the agent believes the AFP intake is complete enough for submission but requires sender verification first.

The user-facing message should:
- summarize all interpreted cases;
- be concise enough for an SMS-like interaction;
- clearly separate multiple cases;
- preserve uncertainty;
- invite confirmation or correction.

### ACCEPT

`ACCEPT` is valid only after explicit confirmation of the latest structured summary.

A model that jumps directly from a complete AFP report to `ACCEPT` should lose action/conversation points and may trigger `must_confirm_before_accept`.

---

## Multi-case and override evaluation

The benchmark includes cases where:

- two children are reported in one conversation;
- one later message applies to both children;
- a later message corrects an earlier age/sex value;
- correction happens after the agent has already generated a confirmation summary.

Expected behavior:

- retain each child as a distinct case;
- apply the correction to the appropriate case only;
- replace superseded values rather than accumulating contradictions;
- preserve unaffected state;
- confirm the updated state again before `ACCEPT`.

---

## Location resolver fixture

The harness should use a **small benchmark-only location resolver**, not a full geocoder.

It exists only to make benchmark expectations deterministic.

Examples of fixture behavior:
- `Majawa` can map unambiguously to the configured LGA/state for relevant scenarios;
- `Majwa` can normalize to `Majawa`;
- some `Kura` scenarios are configured as ambiguous until LGA/state is supplied.

The purpose is to test agent behavior, not model memorization of Nigerian geography.

---

## Other VPD behavior

For v1:

- `classification = OTHER_VPD`
- `other_vpd = true`
- `action = OTHER_VPD`
- preserve the signal;
- stop;
- no disease-specific follow-up;
- no AFP confirmation step.

Priority defaults to `NORMAL` until explicit SME-defined `HIGH` rules exist.

---

## Clarification / escalation policy

A clarification attempt is unsuccessful when the sender's reply does not resolve the requested information.

After three unsuccessful clarification attempts:

- escalate only when a plausible surveillance signal already exists and important follow-up information remains unresolved;
- do not escalate if no meaningful surveillance signal was ever established.

Confirmation turns do not count as clarification attempts.

---

## Scoring

Each scenario receives six dimension scores:

```text
0 = materially wrong
1 = partially correct / defensible but suboptimal
2 = correct
```

Maximum per scenario: **12**.

With 30 scenarios, maximum quality score: **360**.

### 1. Classification — 0/1/2

Did the model correctly understand the message type?

### 2. Extraction / state management — 0/1/2

Did it correctly extract and maintain case state across the full scenario?

This includes:
- field extraction;
- geographic inference;
- preserving approximate values;
- multiple-case separation;
- later corrections overriding earlier values;
- preserving unaffected state;
- avoiding fabricated values.

### 3. Action — 0/1/2

Did it choose the correct next action at the correct point?

This includes correct use of `CONFIRM` before `ACCEPT`.

### 4. Conversation quality — 0/1/2

Did it:
- ask only needed questions;
- ask one focused clarification at a time;
- avoid re-asking known information;
- efficiently maintain a multi-turn conversation;
- provide a complete, concise confirmation summary;
- reconfirm after corrections;
- stop when appropriate?

### 5. Escalation / priority — 0/1/2

Did it:
- escalate when required;
- avoid unnecessary escalation;
- apply the three-attempt rule correctly;
- keep v1 priority at NORMAL absent explicit HIGH rules?

### 6. Output adherence — 0/1/2

Did it:
- return valid structured output;
- use the correct schema/enums;
- represent multiple cases correctly;
- use confirmation status correctly;
- avoid extra non-JSON content?

---

## Multi-turn scoring

A scenario receives one 0–12 score regardless of the number of turns.

Do not average per-turn scores in a way that gives long conversations more weight.

Evaluate the six dimensions across the full interaction.

---

## Critical failures

Track critical failures separately from the numeric score.

Examples:
- missing a credible AFP signal;
- inventing consequential case information;
- merging distinct children into one case;
- failing to apply an explicit correction;
- accepting an AFP case without required confirmation;
- failing required escalation for a valid signal;
- suppressing a distinct case as a duplicate;
- routing a clearly relevant surveillance signal to `NOT_RELEVANT`;
- consequential diagnosis rather than surveillance intake behavior.

---

## Evaluator architecture

Use a hybrid evaluator.

### Deterministic checks

Use code for:
- classification;
- action;
- priority;
- `other_vpd`;
- schema validity;
- explicit age/sex fields;
- fixture-normalized locations;
- case count / case separation;
- duplicate flags;
- escalation state/reason;
- confirmation status;
- clarification-attempt count;
- whether `ACCEPT` followed explicit confirmation.

### Jev semantic checks

Use Jev for bounded semantic judgments such as:
- symptom equivalence;
- whether a clarification targets the right concept;
- whether the confirmation summary faithfully represents all current case state;
- whether an update correctly overrides a prior value while preserving other facts;
- whether the response is concise and non-diagnostic;
- whether two differently worded outputs are functionally equivalent.

Jev should not directly assign an opaque overall `9/12` score. It should produce typed sub-judgments that the harness maps to the six 0/1/2 dimensions.

---

## Version

```text
benchmark_version = v0.3
```
