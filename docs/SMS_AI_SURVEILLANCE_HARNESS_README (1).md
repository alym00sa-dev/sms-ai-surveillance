# SMS x AI Surveillance Prototype Harness

## 1. Purpose

This repository evaluates AI-assisted SMS disease-surveillance intake for Nigeria.

The immediate goal is **not** to build a production SMS system. The goal is to compare AI systems on whether they can reliably turn messy, natural-language community reports into safe, structured surveillance signals.

The first prototype is English-only. Hausa and other languages can be added later.

The primary surveillance use case is **Acute Flaccid Paralysis (AFP)**. The system should also recognize a plausible non-AFP vaccine-preventable / priority-disease signal, preserve it, and stop rather than opening a second disease-specific workflow.

The harness should support:
- multi-turn conversations;
- multiple children/cases in one conversation;
- structured case state and later corrections/overrides;
- mandatory sender confirmation before AFP acceptance;
- model-to-model comparison;
- deterministic scoring where possible;
- bounded semantic scoring with Jev where needed;
- latency and cost tracking;
- a separate Jev-assisted decisioning experiment.

---

## 2. Core research question

> Can an AI layer reliably turn messy, natural-language community SMS reports into usable surveillance signals, ask only the minimum necessary follow-up questions, maintain and correct case state across turns, confirm its final interpretation with the sender, and escalate appropriately when it cannot safely complete intake?

The benchmark should help answer:
- Which models classify AFP / other relevant signals most reliably?
- Which models extract and maintain case information best?
- Which models handle corrections and multiple cases correctly?
- Which models manage clarification most efficiently?
- Which models produce faithful confirmation summaries?
- Which models escalate correctly?
- Which models are best on latency, turns, and cost?
- Does a Jev-assisted decisioning architecture improve reliability or efficiency?

---

## 3. Prototype scope

### In scope

The AI should:
- identify likely AFP-related messages;
- extract structured surveillance information;
- support multiple case records in one conversation;
- infer geographic hierarchy when safe;
- ask one focused clarification question when needed;
- preserve case state across turns;
- apply later explicit corrections as overrides;
- preserve unaffected information;
- present a structured confirmation before AFP acceptance;
- accept only after sender confirmation;
- recognize and preserve other VPD signals;
- flag possible duplicates;
- escalate after repeated failed clarification only when a plausible surveillance signal already exists;
- generate concise SMS-appropriate responses;
- return machine-readable structured output every turn.

### Out of scope for v1

The prototype should not:
- diagnose disease;
- provide clinical advice;
- build full disease-specific flows for non-AFP conditions;
- automatically merge or delete duplicate cases;
- invent geographic mappings;
- invent high-priority rules;
- connect to production SMS/VAS infrastructure;
- optimize separate prompts per provider during the baseline comparison.

---

## 4. Surveillance fields

For each AFP-related case, attempt to establish:

1. `symptom`
2. `age`
3. `sex`
4. `state`
5. `lga`
6. `settlement`

Geographic hierarchy may be inferred from sufficiently specific location information when the benchmark resolver says the mapping is reliable.

Do not ask a sender to repeat geography that can be safely inferred.

The operational completeness rule is:

> Enough information exists when surveillance staff can reasonably identify and follow up the reported case(s).

Once that threshold is reached, the agent moves to `CONFIRM`, not directly to `ACCEPT`.

---

## 5. Behavioral principles

1. Detect; do not diagnose.
2. Extract before asking.
3. Ask only for information still needed.
4. Ask at most one focused clarification question per turn.
5. Maintain structured state across turns.
6. Later explicit corrections override earlier values.
7. Preserve unaffected state.
8. Support multiple cases in one conversation without merging people.
9. Never invent missing information.
10. Infer geography only when reliable.
11. Preserve uncertainty, including approximate age.
12. Recognize and preserve other VPD signals, then stop.
13. Escalate only when human follow-up is genuinely warranted.
14. Flag potential duplicates; do not auto-merge or delete them.
15. Keep responses short and SMS-appropriate.
16. Confirm the complete interpreted AFP state before acceptance.
17. Reconfirm after any correction made during confirmation.
18. Make decisions auditable through structured output.

---

## 6. Classification, action, priority, confirmation

### Classification

```text
AFP_SUSPECTED
OTHER_VPD
HEALTH_RELATED_UNCLEAR
NOT_RELEVANT
UNINTELLIGIBLE
```

Classification answers: **What does this message appear to be?**

### Action

```text
ACCEPT
CLARIFY
CONFIRM
ESCALATE
OTHER_VPD
NOT_RELEVANT
```

Action answers: **What should the agent do next?**

- `CLARIFY`: ask one focused question for information still needed.
- `CONFIRM`: enough information exists; present the complete structured interpretation and ask sender to confirm/correct.
- `ACCEPT`: sender explicitly confirmed the latest structured interpretation.
- `ESCALATE`: stop AI intake and hand off to a human.
- `OTHER_VPD`: preserve a relevant non-AFP signal and stop.
- `NOT_RELEVANT`: stop because the message is outside the surveillance workflow or never establishes a meaningful surveillance signal.

### Priority

```text
NORMAL
HIGH
```

Priority is independent from action.

For v1, default to `NORMAL`. Do not invent `HIGH` rules; use `HIGH` only if explicit SME-defined rules are added later.

### Confirmation status

```text
NOT_READY
PENDING
CONFIRMED
```

- `NOT_READY`: case is incomplete or the workflow terminates another way.
- `PENDING`: agent has generated the structured summary and is awaiting sender confirmation/correction.
- `CONFIRMED`: sender explicitly confirmed the latest summary.

---

## 7. Confirmation and state-update flow

For AFP-suspected cases:

```text
extract/update state
      ↓
clarify if needed
      ↓
CONFIRM complete structured interpretation
      ↓
     user
   /      \
 yes     correction
  |          |
ACCEPT   update state
             ↓
          CONFIRM again
```

Rules:
- Never jump directly from a complete AFP message to `ACCEPT`.
- Explicit later corrections override earlier values.
- Do not retain superseded values as current truth.
- Preserve all unrelated fields.
- In a multi-case conversation, update only the case(s) referred to by the sender.
- Confirmation turns do not count toward the three failed clarification attempts.

---

## 8. Multiple-case behavior

A sender may report more than one child in the same conversation.

The agent should:
- create separate case records;
- preserve shared location/context when appropriate;
- ask a question that can apply to multiple cases when useful;
- apply later information to the correct case(s);
- never force one child per conversation;
- clearly enumerate each case in the final confirmation summary.

Example:

```text
User: Two children in Gwadabawa have weak legs. A boy 5 and a girl maybe 9.
Agent: Did the weakness start suddenly for both children?
User: Yes, both started today, but the girl is actually 8.
Agent: I have: 1) boy, age 5 ... 2) girl, age 8 ... Is this correct?
User: Yes.
Agent: ACCEPT
```

---

## 9. Clarification and escalation policy

A clarification attempt is unsuccessful when the sender's reply does not resolve the requested information.

The agent may make up to **3 unsuccessful clarification attempts**.

After the third unsuccessful attempt:
- `ESCALATE` if a plausible surveillance signal already exists but important follow-up information remains unresolved;
- do not escalate if no meaningful surveillance signal was ever established; terminate instead.

Consequential contradictions may also justify escalation before the three-attempt limit when the case cannot safely be resolved.

---

## 10. Other VPD behavior

For v1:

```json
{
  "classification": "OTHER_VPD",
  "other_vpd": true,
  "action": "OTHER_VPD",
  "priority": "NORMAL"
}
```

The agent should:
- preserve the signal and whatever information was provided;
- stop;
- not start a disease-specific follow-up conversation;
- not require AFP-style confirmation.

The benchmark does not require naming the specific other disease.

---

## 11. Duplicate behavior

Duplicate detection is a flag, not a disposition.

A valid report may simultaneously be:

```text
action = CONFIRM or ACCEPT
potential_duplicate = true
```

The system may identify candidate prior reports, but it must never automatically delete, suppress, or merge the new report.

Potential-duplicate status is internal metadata and need not be mentioned in the sender-facing SMS.

---

## 12. Required model output

Use a `cases` array for case state.

```json
{
  "classification": "AFP_SUSPECTED",
  "other_vpd": false,
  "action": "CONFIRM",
  "priority": "NORMAL",
  "cases": [
    {
      "case_id": "case_1",
      "symptom": "sudden weakness in both legs",
      "age": 7,
      "sex": "male",
      "state": "Jigawa",
      "lga": "Kafin Hausa",
      "settlement": "Majawa"
    }
  ],
  "location_resolution": [
    {
      "case_id": "case_1",
      "raw_location": "Majawa",
      "inferred_fields": ["lga", "state"],
      "confidence": "high"
    }
  ],
  "missing_information": [],
  "potential_duplicate": false,
  "duplicate_candidate_ids": [],
  "escalation": {
    "required": false,
    "reason": null
  },
  "clarification": {
    "target": null,
    "attempt_number": 0
  },
  "confirmation": {
    "status": "PENDING"
  },
  "response": "I have: a 7-year-old boy in Majawa, Kafin Hausa, Jigawa, with sudden weakness in both legs. Is this correct?"
}
```

For complete schema/enums, use `SMS_AI_SURVEILLANCE_PROMPT_README.md` as the prompt contract.

---

## 13. Multi-turn input

Provide both:
- full conversation transcript;
- structured current state.

Suggested envelope:

```json
{
  "conversation": [],
  "current_case_state": {
    "cases": []
  },
  "clarification_attempts": 0,
  "candidate_prior_reports": [],
  "location_resolver": {
    "resolver_version": "v0.1",
    "status": "UNRESOLVED",
    "candidates": [],
    "mentions": []
  }
}
```

The harness owns and persists state between turns, including `clarification_attempts` (counted by the scripted sender, see section 24A). `location_resolver` is recomputed every turn from the sender's messages (section 14).

---

## 14. Lightweight location resolver

Use a small benchmark-only resolver fixture rather than a production geocoder.

The resolver is deterministic, reads only sender messages, and its output is **provided to every candidate model as structured input** (`location_resolver` in the envelope, section 13). It is also the scoring reference. Models are not expected to memorize geography.

Status per turn:

```text
RESOLVED    exactly one candidate place (hierarchy filled from the fixture)
AMBIGUOUS   several candidates; `requires` names the fields that would disambiguate
UNRESOLVED  no usable location (none given, only a nearby reference, or a conflict)
```

Fixture behavior covers:
- unambiguous Majawa mapping;
- `Majwa` -> `Majawa` normalization;
- intentionally ambiguous `Kura` until both state and LGA are supplied;
- "near X" settlement references stay UNRESOLVED, while a "near" LGA still resolves at LGA level;
- state-only resolution for "Sokoto town" (LGA ambiguous).

Implementation: `src/benchmark/location_fixture.py`. Data: `data/location_fixture_v0_1.json` (status: pending SME sign-off). Kura is declared ambiguous with no listed candidates: nothing is invented and the answer is not hinted. It resolves only after the sender states both state and LGA. The SME may add concrete candidate places at sign-off.

Because the model receives the resolver output, geography is not a memory test. Scoring compares model fields against gold and the fixture; non-compliance with the resolver (guessing under AMBIGUOUS/UNRESOLVED, or contradicting RESOLVED) is detected by the existing fabrication rules and is also logged as a separate resolver-compliance metric.

---

## 15. Benchmark

Use:

```text
sms_ai_benchmark_v0_3.jsonl
sms_ai_benchmark_README_v0_3.md
```

The benchmark contains 30 scenarios and is weighted toward relevant, multi-turn surveillance interactions.

Important v0.3 benchmark behaviors:
- complete AFP reports go to `CONFIRM`, then `ACCEPT` after sender confirmation;
- explicit corrections override prior state and trigger reconfirmation;
- multiple cases can coexist in one conversation;
- other VPD cases preserve + stop;
- duplicate cases remain preserved;
- escalation requires a meaningful underlying signal unless a different consequential conflict demands handoff.

---

## 16. Model slate

### Anthropic

```text
claude-sonnet-5-5
claude-haiku-4-5-20251001
```

### OpenAI

```text
gpt-6-luna
gpt-6.1-sol
```

### Google

```text
gemini-3.8-flash
gemini-3.1-pro-preview
```

### Together.ai / open models

```text
google/gemma-4-31B-it
Qwen/Qwen3.8-Flash
meta-models/Muse-Glimmer-30B
moonshotai/Kimi-K3
deepseek-ai/DeepSeek-V4.1-Flash
```

### Jev

Use Jev in two roles:
1. bounded semantic evaluator;
2. separate decisioning architecture experiment.

Keep model/provider identifiers configurable.

---

## 17. Baseline comparison rules

Use the same:
- system prompt;
- output contract;
- benchmark;
- state fixture;
- scoring rubric.

Do not initially:
- tune prompts separately per provider;
- add model-specific few-shot examples;
- optimize based on benchmark failures.

Provider-native JSON/structured-output features may be used and should be logged.

Use consistent/default reasoning settings where practical and record all configuration.

---

## 18. Scoring

Each scenario receives six scores, each `0 / 1 / 2`:

1. **Classification**
2. **Extraction / state management**
3. **Action**
4. **Conversation quality**
5. **Escalation / priority**
6. **Output adherence**

Maximum per scenario: **12**.

Maximum across 30 scenarios: **360**.

### Extraction / state management includes
- correct field extraction;
- safe location inference;
- uncertainty preservation;
- multiple-case separation;
- correction / override semantics;
- preservation of unaffected fields;
- no consequential fabrication.

### Action includes
- correct `CLARIFY` / `CONFIRM` / `ACCEPT` / terminal behavior;
- no direct AFP `ACCEPT` before explicit confirmation.

### Conversation quality includes
- asking only needed questions;
- one focused clarification per turn;
- not re-asking known facts;
- faithful structured confirmation;
- reconfirmation after corrections;
- efficient turns.

### Output adherence includes
- valid JSON/schema;
- valid enums/nulls;
- `cases` array;
- confirmation status;
- no commentary outside JSON.

Do not give longer conversations extra weight: each scenario still has a maximum of 12.

---

## 19. Critical failures

Track separately from the numeric score.

Examples:
- misses credible AFP signal;
- invents consequential information;
- merges distinct children;
- fails to apply explicit correction;
- accepts AFP without confirmation;
- fails required escalation;
- suppresses distinct case as duplicate;
- routes a clearly relevant health signal to `NOT_RELEVANT`;
- gives consequential diagnosis rather than surveillance-intake behavior.

---

## 20. Evaluator architecture

Use a hybrid evaluator.

### Deterministic code

Use for:
- enum/action/priority matches;
- schema validity;
- explicit age/sex;
- benchmark location fixture;
- case count and case identity where explicit;
- duplicate flags;
- clarification count;
- escalation requirement/reason;
- confirmation status;
- whether `ACCEPT` followed explicit confirmation.

### Jev semantic evaluation

Use for bounded semantic checks such as:
- symptom equivalence;
- appropriate clarification target;
- whether confirmation accurately summarizes current state;
- whether a correction was properly applied while preserving unaffected facts;
- response concision and non-diagnostic wording.

Jev should return typed sub-judgments, not a direct opaque 0–12 score.

The harness converts deterministic + Jev sub-judgments into the six dimension scores.

---

## 21. Jev decisioning experiment

Compare:

### Baseline

```text
conversation/state -> LLM -> classification + cases + action + priority + response
```

### Jev-assisted

```text
conversation/state
      ↓
LLM extraction / language understanding
      ↓
Jev bounded decisioning
      ├─ classification
      ├─ action
      └─ priority
      ↓
LLM response generation
```

Treat this as a required second experiment in the harness, not an optional extension and not a replacement for the baseline model bake-off. The implementation should support running both architectures against the same benchmark and scoring contract.

### Required Jev experiment run

After the baseline model bake-off is working end to end, run a Jev-assisted configuration across the same 30 benchmark scenarios. The Jev-assisted run should:
- use the same benchmark scenarios and gold expectations;
- use the same prompt and structured state inputs wherever applicable, including the same `location_resolver` output;
- preserve the same confirmation-before-accept, override, multi-case, duplicate, and escalation rules;
- use the same 0/1/2 scorer contract and critical-failure definitions;
- log latency, cost, turns, and schema failures separately;
- be reported side-by-side with the corresponding end-to-end LLM baseline.

At minimum, the Jev architecture should be implemented as:

```text
LLM -> extraction / case-state update
Jev -> classification + action + priority
LLM -> user-facing response / confirmation text
```

The harness should make this architecture configurable so the exact division of responsibility can be iterated later without changing the benchmark format.

---

## 22. Operational metrics

Log separately from quality score:
- per-turn latency;
- end-to-end scenario latency;
- input/output tokens;
- provider usage;
- estimated cost per turn;
- estimated cost per scenario;
- turns to resolution;
- clarification count;
- confirmation count;
- structured-output retry count.

Do not mix latency or cost into the quality score.

---

## 23. Suggested repository structure

```text
src/
  adapters/
    anthropic.py
    openai.py
    google.py
    together.py
    jev.py

  benchmark/
    loader.py
    runner.py
    state.py
    location_fixture.py
    envelope.py
    compare.py
    scripted_user.py

  prompts/
    system_prompt.txt

  schemas/
    model_output.py
    benchmark_case.py
    score.py

  evaluation/
    deterministic.py
    semantic_jev.py
    aggregate.py
    critical_failures.py

  reporting/
    results.py
    tables.py

data/
  sms_ai_benchmark_v0_3_1.jsonl
  location_fixture_v0_1.json
  critical_check_mapping_v0_1.json
  FROZEN_MANIFEST.json
results/
tests/
```

---

## 24. Recommended run flow

For each model and scenario:

```text
1. Load benchmark scenario and fixtures.
2. Initialize conversation + structured case state.
3. Send prompt and envelope (conversation, state, attempts, prior reports,
   location_resolver computed from the sender messages so far).
4. Parse and validate JSON output.
5. Update structured state according to model output.
6. Ask the scripted sender (section 24A) for the next message, or terminate.
7. Save raw transcript and every structured output.
8. Run deterministic checks.
9. Run Jev semantic checks where needed.
10. Produce six 0/1/2 dimension scores.
11. Log critical failures.
12. Record cost/latency/turn metrics.
13. Save scenario result.
```

After the baseline provider/model runs are complete, execute the required Jev-assisted decisioning experiment over the full benchmark using the same evaluation pipeline. Save it as a distinct system configuration so results can be compared directly against end-to-end LLM runs.

Terminal actions are:

```text
ACCEPT
ESCALATE
OTHER_VPD
NOT_RELEVANT
```

`CONFIRM` is not terminal.

---

## 24A. Scripted sender policy (no LLM user simulator in v1)

The sender is a deterministic, state-aware script (`src/benchmark/scripted_user.py`). The benchmark's scripted user turns are used only when the model's behavior earns them. The scenario keeps a cursor into the gold turns; the gold turn at the cursor defines what the model should do now.

| Model action | Condition | Sender reply | Cursor |
|---|---|---|---|
| `CLARIFY` | gold is `CLARIFY` and the target is in the same family as any gold `missing_important_fields` (age / location / symptom) | next scripted turn | advances |
| `CLARIFY` | off-target, or gold expects `CONFIRM`/terminal | neutral, no new information: "I already told you that." if gold state already holds that field, else "I don't know." | stays |
| `CONFIRM` | interpreted state materially correct vs gold and gold is `CONFIRM` | next scripted turn; the scripted "Yes, that is correct." is sent only here | advances |
| `CONFIRM` | state materially incorrect | deterministic correction built from the gold diff ("No, that is not correct. ...") | stays |
| `CONFIRM` | state correct but gold expects `CLARIFY` | "I don't know." | stays |
| `CONFIRM` | repeated after the sender already affirmed | affirmation resent | stays |
| terminal | equals the gold terminal on the last gold turn | scenario ends `COMPLETED` | |
| terminal | anything else (e.g. `ACCEPT` without `CONFIRM`, early `ESCALATE`, `NOT_RELEVANT` on a relevant signal) | scenario ends `PREMATURE_TERMINAL` | |

Bounds and counters:
- `max_model_turns = gold turns + 3` (ends as `MAX_TURNS`).
- At most 2 corrections per scenario, then `CONFIRMATION_NOT_CONVERGING`.
- `clarification_attempts` is counted by the harness: a `CLARIFY` is unsuccessful when the reply does not resolve the requested information (gold annotation of the next turn still lists the field, the next gold action is `ESCALATE`/`NOT_RELEVANT`, or the reply was neutral). The model's own `attempt_number` is not authoritative.

"Materially correct" is a deterministic comparison, with no Jev call in the loop: omitted gold fields are ignored, explicit nulls must stay unresolved, valued fields and case count must match (fixture-checked), and symptom meaning must carry the frozen normalized features of the gold symptom. Those features (`data/symptom_features_v0_1.json`, keyed by gold symptom string) are intentionally small: `body_region` (leg/arm), `laterality` (both/one/left/right) and `onset` (sudden). The model's symptom text is reduced to the same features by a small keyword extractor (`src/benchmark/symptoms.py`); every non-null gold feature must be satisfied, and the derived model features are logged with each CONFIRM turn. Finer wording fidelity is judged by Jev after the run.

Logged per scenario: termination reason, every sender reply kind, and events (`INCORRECT_CONFIRMATION`, `OFF_TARGET_CLARIFY`, `PREMATURE_CONFIRM`, `REPEATED_CONFIRM`). Scoring detectors must evaluate the model's first state after a sender correction, not only the final state, because a harness correction can repair a wrong confirmation.

Terminations other than `COMPLETED` are scored on what happened up to that point; they are not infrastructure failures.

---

## 25. Reporting

Produce both aggregate and scenario-level outputs.

Example aggregate table:

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency | Avg cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Model A | 341/360 | 58/60 | 57/60 | 59/60 | 53/60 | 56/60 | 58/60 | 0 | 2.8 | ... | ... |

Retain scenario-level notes explaining lost points and critical failures.

Also produce a dedicated architecture comparison for the Jev decisioning experiment. At minimum, compare the Jev-assisted system against the relevant end-to-end LLM baseline on:
- total quality score;
- six dimension scores;
- critical failures;
- average turns to resolution;
- latency;
- cost per scenario;
- schema/retry rate.

Label Jev-assisted results clearly as an architecture configuration rather than as another standalone generative model.

---

## 26. Reproducibility

Record:
- location fixture version and SHA-256, resolver version;
- scripted-sender policy version and turn cap;
- critical-check mapping version and SHA-256 (`data/FROZEN_MANIFEST.json`);
- model/provider ID;
- run timestamp;
- system prompt version;
- benchmark version;
- temperature;
- reasoning/effort setting;
- max tokens;
- structured-output mode;
- provider parameters;
- Jev evaluator configuration/version;
- architecture mode (`end_to_end_llm` or `jev_assisted_decisioning`);
- Jev decisioning configuration/version for Jev-assisted runs;
- git commit if available.

---

## 27. Error handling

Distinguish:
- model-quality failures;
- API/infrastructure failures;
- structured-output failures.

Do not silently count provider outages as model-quality failures.

For invalid structured output, preserve raw output, validation errors, and any retry behavior.

---

## 28. Credentials

Never hard-code keys.

Example environment variables:

```text
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
TOGETHER_API_KEY=
JEV_API_KEY=
```

---

## 29. First implementation milestone

Start small:

1. load benchmark v0.3;
2. implement the location fixture;
3. run one model across all scenarios;
4. maintain `cases` state across turns;
5. support `CONFIRM` -> correction/reconfirm -> `ACCEPT`;
6. validate JSON;
7. save transcripts/results;
8. implement deterministic scoring;
9. produce a basic summary table.

Then add:
- Jev semantic scoring;
- remaining model adapters;
- cost normalization;
- Jev decisioning architecture.

---

## 30. Source artifacts

Use these files together:

```text
SMS_AI_SURVEILLANCE_HARNESS_README.md
SMS_AI_SURVEILLANCE_PROMPT_README.md
sms_ai_benchmark_README_v0_3.md
sms_ai_benchmark_v0_3.jsonl
```

---

## 31. Guiding principle

Optimize for:

> **reliable surveillance behavior with the minimum necessary conversational burden, while preserving sender control over the final interpreted record.**

A strong system should recognize the signal, maintain structured state, ask only what it needs, apply corrections correctly, confirm what it understood, accept only after confirmation, and escalate only when human follow-up is genuinely warranted.
