# SMS x AI Surveillance — Scorer Contract v0.1

## 1. Purpose

This document defines how model runs are scored against the SMS x AI Surveillance benchmark.

The benchmark uses:
- 30 scenarios;
- 6 scoring dimensions;
- 0 / 1 / 2 points per dimension;
- 12 points maximum per scenario;
- 360 points maximum across the benchmark.

This scorer contract is intended to make evaluation:
- reproducible;
- explainable;
- debuggable;
- comparable across providers;
- mostly deterministic where possible;
- semantically judged only where necessary.

The scorer should **not** ask a judge model to assign an opaque overall score.

Instead:

```text
deterministic checks
+ bounded semantic judgments
        ↓
dimension-level 0/1/2 scores
        ↓
scenario total out of 12
        ↓
benchmark total out of 360
```

Critical failures are tracked separately from the numeric score.

---

## 2. Scoring dimensions

Each scenario receives:

1. Classification: 0–2
2. Extraction / state management: 0–2
3. Action correctness: 0–2
4. Conversation quality: 0–2
5. Escalation / priority: 0–2
6. Output adherence: 0–2

Maximum:

```text
12 points per scenario
```

For 30 scenarios:

```text
360 points maximum
```

All scenarios are weighted equally.

---

## 3. General scoring philosophy

### 2 points

Award `2` when the model behavior is materially correct and aligned with the benchmark expectation.

Minor wording differences should not reduce the score if they do not affect behavior.

### 1 point

Award `1` when the model is mostly correct but has a meaningful, non-critical issue.

Examples:
- asks a slightly redundant question but still progresses safely;
- misses a non-essential field;
- uses a defensible adjacent classification in an intentionally ambiguous case;
- produces a slightly awkward confirmation summary that is still accurate;
- has a minor schema issue that is recoverable.

### 0 points

Award `0` when the model is materially wrong on that dimension.

Examples:
- wrong action;
- material extraction error;
- ignores a correction;
- merges separate children;
- asks for the wrong information;
- fails required escalation;
- invalid/unusable structured output.

A scenario can score highly overall and still contain a critical failure. Critical failures must therefore be tracked separately.

---

## 4. Evaluation architecture

Evaluation is hybrid.

### A. Deterministic evaluator

Use normal code when benchmark ground truth is explicit.

Examples:
- exact enum matching;
- age;
- sex;
- number of cases;
- action sequence;
- priority;
- escalation required or not;
- duplicate flag;
- clarification attempt count;
- confirmation status;
- schema validity;
- allowed enum values;
- missing/null fields;
- canonical location fixture;
- whether `ACCEPT` occurred before `CONFIRM`.

### B. Normalized / fuzzy deterministic evaluator

Use deterministic normalization where exact string matching would be too brittle.

Examples:
- `Majwa` vs `Majawa`;
- `Kafin-Hausa` vs `Kafin Hausa`;
- capitalization and punctuation;
- whitespace;
- approximate age strings;
- equivalent canonical location IDs.

This should be implemented with explicit normalization rules or benchmark fixtures, not an LLM.

### C. Jev semantic evaluator

Use Jev only for bounded semantic questions where exact matching is insufficient.

Examples:
- symptom equivalence;
- whether a clarification question targets the correct missing concept;
- whether the model re-asked information already known;
- whether a confirmation summary faithfully reflects current case state;
- whether the user-facing message is concise and non-diagnostic;
- whether the model appropriately stopped rather than continuing conversation.

Jev should return typed judgments such as:

```json
{
  "result": "CORRECT"
}
```

Allowed semantic judgment values:

```text
CORRECT
PARTIAL
INCORRECT
```

The harness maps:

```text
CORRECT   -> 2
PARTIAL   -> 1
INCORRECT -> 0
```

Jev should not directly assign the final 0–12 scenario score.

---

## 5. Scenario-level evaluation inputs

For each scenario, the scorer should have access to:

```text
scenario_id
scenario transcript
benchmark gold expectations
model outputs for every turn
final structured state
all model actions
all user-facing responses
clarification count
confirmation state
duplicate metadata
escalation metadata
raw model outputs
schema validation results
```

The gold benchmark should define where applicable:

```text
expected classification
expected action progression
expected priority
expected case state
expected number of cases
expected corrected/overridden values
expected missing information
expected clarification targets
expected confirmation behavior
expected duplicate flag
expected escalation behavior
critical-failure conditions
```

---

# 6. Dimension 1 — Classification

## Question

> Did the model correctly identify what kind of surveillance message this is?

Allowed classifications:

```text
AFP_SUSPECTED
OTHER_VPD
HEALTH_RELATED_UNCLEAR
NOT_RELEVANT
UNINTELLIGIBLE
```

## Primary scorer

Deterministic.

## Inputs

- expected classification;
- model classification at key turn(s);
- final classification.

## Score = 2

Use `2` when:
- the expected classification is returned at the appropriate point;
- the model updates classification correctly as new evidence arrives.

Example:

Turn 1:
```text
"My neighbour's daughter is not using her leg well."
```

Expected:
```text
HEALTH_RELATED_UNCLEAR
```

Turn 2:
```text
"It became weak suddenly this morning."
```

Expected:
```text
AFP_SUSPECTED
```

A model that updates correctly receives `2`.

## Score = 1

Use `1` only when:
- the classification is defensible but less precise;
- the scenario explicitly allows ambiguity.

Example:
- benchmark accepts `HEALTH_RELATED_UNCLEAR` as partially acceptable before enough evidence exists for `AFP_SUSPECTED`.

Do not automatically award `1` for every adjacent class.

## Score = 0

Use `0` when:
- a credible AFP report is classified `NOT_RELEVANT`;
- an obvious other-VPD signal is treated as AFP;
- a clearly irrelevant message is treated as surveillance-relevant;
- the model fails to update classification after material new information.

---

# 7. Dimension 2 — Extraction / State Management

## Question

> Did the model correctly extract, preserve, update, and structure the surveillance information across the conversation?

This dimension includes:
- field extraction;
- case-state persistence;
- correction / override behavior;
- multi-case handling;
- safe geographic inference;
- avoidance of fabrication.

## Primary scorer

Hybrid:
- deterministic;
- normalized deterministic;
- Jev for symptom equivalence.

## Fields

Per case:

```text
symptom
age
sex
state
lga
settlement
```

The benchmark may also track:
- number of cases;
- raw location;
- inferred location fields;
- symptom onset language;
- approximate age wording.

## Gold field semantics (amended 2026-10-05, before first freeze)

For every gold case field:

```text
field omitted         -> not scored
field = null          -> must remain unresolved (model null; "unknown" also accepted for sex)
field = value         -> must match after normalization
```

Fields that are intentionally unresolved in the benchmark are materialized as explicit `null` (benchmark v0.3.1); the scorer has no implicit-null logic.

When a gold `state`/`lga` is omitted and the settlement has an entry in the benchmark location fixture (`data/location_fixture_v0_1.json`), a non-null model value must equal the fixture value. A mismatch is a fabrication; null is acceptable. Approximate ages ("about 9", "about 10-11") match any model value inside the stated range.

## State-update rules

### Preserve

If a later user message does not modify a previously known field, keep the prior value.

### Override

If the user clearly corrects a prior value, the new value replaces the old value.

Example:

```text
Turn 1: "7 year old boy..."
Turn 2: "Sorry, it is a girl."
```

Final state:

```text
sex = female
```

The previous value must not survive as the active value.

### Multi-case

If the user reports multiple children:
- preserve each child as a distinct case;
- do not merge them;
- apply later information to the correct case;
- allow information applying to both cases to update both where appropriate.

## Score = 2

Use `2` when:
- all material fields are correct;
- known information is preserved;
- corrections properly override;
- separate cases remain separate;
- no consequential information is invented;
- geographic inference uses the allowed resolver correctly.

Minor wording differences in symptoms should not matter.

## Score = 1

Use `1` when:
- the state is materially usable;
- there is a minor field miss or harmless normalization error;
- a non-essential detail is lost;
- symptom wording is slightly incomplete but semantically close.

## Score = 0

Use `0` when:
- a material field is wrong;
- a correction is ignored;
- old and new values are incorrectly combined;
- two children are merged;
- one child's details are applied to the other;
- a consequential field is fabricated;
- ambiguous geography is guessed rather than clarified.

## Jev sub-checks

Suggested bounded semantic questions:

```text
Does the extracted symptom preserve the material meaning of the user's report?
```

Return:

```text
CORRECT
PARTIAL
INCORRECT
```

And for confirmations:

```text
Does the confirmation summary accurately reflect the current structured case state?
```

---

# 8. Dimension 3 — Action Correctness

## Question

> Did the agent choose the correct next action throughout the scenario?

Allowed actions:

```text
ACCEPT
CLARIFY
CONFIRM
ESCALATE
OTHER_VPD
NOT_RELEVANT
```

## Primary scorer

Deterministic.

## Important state-machine rule

For AFP cases:

```text
CLARIFY as needed
    ↓
CONFIRM
    ↓
user confirms
    ↓
ACCEPT
```

A model must not normally go directly from enough information to `ACCEPT` without confirmation.

If the sender corrects the confirmation:

```text
CONFIRM
    ↓
user correction
    ↓
update state
    ↓
CONFIRM again
```

## Score = 2

Use `2` when:
- the action sequence matches the intended workflow;
- the model confirms before accept;
- correction leads to re-confirmation;
- terminal actions occur at the correct time.

## Score = 1

Use `1` when:
- the model takes a defensible but inefficient step;
- one unnecessary clarification occurs;
- action timing is slightly suboptimal but the workflow remains safe.

Example:
- asks one redundant clarification before confirmation.

## Score = 0

Use `0` when:
- accepts before required confirmation;
- confirms while important information is still unresolved;
- continues clarifying after a terminal action;
- fails to escalate when required;
- escalates when a normal clarification would clearly suffice;
- starts disease-specific dialogue after `OTHER_VPD`;
- continues after `NOT_RELEVANT`.

---

# 9. Dimension 4 — Conversation Quality

## Question

> Did the model manage the conversation efficiently, clearly, and in a way appropriate for SMS?

This dimension evaluates behavior beyond the action enum.

## Primary scorer

Jev, supported by deterministic checks.

## Evaluate whether the model:

- asks only for missing or unresolved information;
- does not re-ask known information;
- asks one focused clarification per turn;
- handles off-target user replies;
- respects corrections;
- keeps multiple cases coherent;
- produces a clear structured confirmation summary;
- allows the sender to correct the summary;
- stops once the workflow is complete;
- keeps messages concise enough for SMS;
- does not diagnose disease.

## Score = 2

Use `2` when:
- conversation is efficient;
- clarification is targeted;
- no unnecessary questions are asked;
- confirmation is accurate and readable;
- response is concise and appropriately framed.

## Score = 1

Use `1` when:
- conversation succeeds;
- there is mild redundancy, verbosity, or awkward phrasing;
- confirmation is understandable but not ideal;
- one non-consequential question is unnecessary.

## Score = 0

Use `0` when:
- wrong information is requested;
- known information is repeatedly re-asked;
- multiple unrelated questions are bundled unnecessarily;
- the model loops;
- confirmation summary is materially misleading;
- correction is not reflected;
- user-facing response is clinically diagnostic in a consequential way.

## Suggested Jev rubric

Ask Jev to return structured judgments for:

```text
clarification_target_quality
redundancy
confirmation_fidelity
sms_conciseness
non_diagnostic_behavior
stop_behavior
```

Each can return:

```text
CORRECT
PARTIAL
INCORRECT
```

The scorer may combine these into the 0/1/2 dimension score using explicit rules.

Suggested mapping:

```text
2:
  no INCORRECT judgments
  and at most one PARTIAL

1:
  no major semantic failure
  but multiple PARTIAL judgments
  or one non-critical INCORRECT

0:
  material conversational failure
  or confirmation fidelity = INCORRECT
  or stop behavior = INCORRECT in a consequential way
```

---

# 10. Dimension 5 — Escalation / Priority

## Question

> Did the model correctly decide whether human escalation was required and assign priority appropriately?

## Primary scorer

Deterministic.

## Current priority rule

Until explicit SME high-priority rules are added:

```text
priority = NORMAL
```

The model should not invent `HIGH` triggers.

## Escalation logic

### Escalate when:

- a plausible surveillance-relevant signal already exists; and
- important information needed for follow-up remains unresolved after 3 unsuccessful clarification attempts.

Or:

- the scenario contains consequential conflicting information that cannot safely be resolved and the benchmark explicitly expects escalation.

### Do not escalate when:

- repeated messages never establish a plausible surveillance signal.

## Score = 2

Use `2` when:
- escalation occurs exactly when expected;
- non-escalation occurs when expected;
- reason is correct;
- priority is correct.

## Score = 1

Use `1` when:
- escalation is safe but timing or reason is slightly off;
- priority is correct but escalation metadata is partially wrong.

## Score = 0

Use `0` when:
- required escalation is missed;
- an unresolved credible AFP signal is dropped;
- meaningless/no-signal conversation is unnecessarily escalated;
- model continues clarifying past the escalation limit;
- model invents `HIGH` priority without a supplied rule.

---

# 11. Dimension 6 — Output Adherence

## Question

> Did the model follow the required structured output contract?

## Primary scorer

Deterministic.

## Check:

- valid JSON;
- required fields;
- allowed enum values;
- correct null handling;
- no prose outside JSON;
- valid case structure;
- correct number/type of cases;
- valid confirmation object/state;
- valid escalation object;
- valid clarification object;
- duplicate metadata type correctness.

## Score = 2

Use `2` when:
- output is fully valid against the schema;
- all required fields are present;
- enums and types are correct.

## Score = 1

Use `1` when:
- output is parseable and recoverable;
- there is a minor non-consequential schema deviation;
- one optional field is missing;
- harmless extra key appears.

## Score = 0

Use `0` when:
- JSON cannot be parsed;
- required structure is absent;
- enum values are invalid;
- output is materially unusable;
- model returns free-form prose instead of structured output.

If the harness retries a schema failure:
- preserve the first invalid output;
- record retry count;
- score output adherence according to the benchmark policy;
- do not hide that a retry was required.

Recommended v1 policy:

```text
first attempt valid              -> eligible for 2
first attempt invalid, retry valid -> maximum 1
all attempts invalid             -> 0
```

---

# 12. Multi-turn scoring

Each scenario receives only one score per dimension.

Do not average turn-level scores.

Instead, evaluate the entire scenario trajectory.

Example:

```text
Turn 1: correct CLARIFY
Turn 2: correct CONFIRM
Turn 3: user corrects sex
Turn 4: model correctly updates and CONFIRMS again
Turn 5: user says yes
Turn 6: ACCEPT
```

The scenario can receive:

```text
Classification: 2
Extraction: 2
Action: 2
Conversation: 2
Escalation: 2
Output: 2
Total: 12
```

A failure on one important turn should affect the relevant scenario-level dimension.

---

## Scripted-sender interaction (amended 2026-10-05, before first freeze)

Conversations are driven by the deterministic scripted sender (harness README section 24A). The scorer therefore receives, besides model outputs: the sender reply kinds, harness events (`INCORRECT_CONFIRMATION`, `OFF_TARGET_CLARIFY`, `PREMATURE_CONFIRM`, `REPEATED_CONFIRM`), the termination reason and the harness-counted `clarification_attempts`.

- Score the trajectory up to termination. `PREMATURE_TERMINAL`, `MAX_TURNS` and `CONFIRMATION_NOT_CONVERGING` are model-behavior outcomes, not infrastructure failures.
- Correction detectors (`IGNORED_EXPLICIT_CORRECTION`) evaluate the model's first state after the sender's correction, not only the final state, because a harness correction can repair a wrong confirmation.
- Every `INCORRECT_CONFIRMATION` event lowers extraction/state management and conversation quality for that scenario.
- The model receives `location_resolver` output each turn. Non-compliance with it is logged as a separate resolver-compliance metric; the existing fabrication rules (`FABRICATED_CONSEQUENTIAL_FIELD`) decide criticality.

---

# 13. Confirmation-specific scoring

Confirmation is now a core workflow requirement for AFP cases.

The scorer should verify:

1. The agent reaches `CONFIRM` only when enough information exists.
2. The confirmation summary reflects the full current structured state.
3. For multiple cases, each case is clearly distinguished.
4. Approximate values remain approximate.
5. Inferred geography is represented correctly.
6. A sender correction updates the underlying state.
7. The agent confirms again after a correction.
8. `ACCEPT` occurs only after explicit confirmation.

## Confirmation fidelity

Use deterministic checks for structured case state and Jev for user-facing summary equivalence.

Suggested Jev query:

```text
Given the current structured case state and the assistant's confirmation message,
does the message accurately summarize all material case details without adding,
dropping, or changing consequential information?
```

Return:

```text
CORRECT
PARTIAL
INCORRECT
```

---

# 14. Multiple-case scoring

When a scenario contains more than one child/case, score the model on whether it:

- identifies the correct number of cases;
- keeps cases distinct;
- maps attributes to the right child;
- applies shared information appropriately;
- applies corrections only to the intended case;
- confirms all cases clearly;
- does not collapse the reports into one record.

A model that merges two distinct children should receive:

```text
Extraction = 0
```

and may trigger a critical failure.

---

# 15. Duplicate scoring

Duplicate behavior is metadata, not a terminal action.

Check:

```text
potential_duplicate
duplicate_candidate_ids
```

## Correct behavior

A report may be:

```text
action = CONFIRM / ACCEPT
potential_duplicate = true
```

The report should still be preserved.

## Critical distinction

Potential duplicate:

```text
flag for review
```

Not:

```text
delete / merge / suppress
```

If a model automatically suppresses a new credible report because it resembles a prior case, this may be a critical failure.

---

# 16. Critical failures

Critical failures are tracked separately from numeric scores.

Suggested critical-failure codes:

```text
MISSED_CREDIBLE_AFP
FABRICATED_CONSEQUENTIAL_FIELD
ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION
FAILED_REQUIRED_ESCALATION
DROPPED_VALID_SIGNAL
MERGED_DISTINCT_CASES
IGNORED_EXPLICIT_CORRECTION
SUPPRESSED_POTENTIAL_DUPLICATE
RELEVANT_SIGNAL_MARKED_NOT_RELEVANT
CONSEQUENTIAL_DIAGNOSIS
```

## Critical failure principles

A failure should be critical when it creates a meaningful risk of:
- losing a surveillance signal;
- routing the wrong child/case;
- creating materially false surveillance data;
- failing to hand off when required;
- suppressing a potentially real case.

Do not label minor verbosity or formatting errors as critical.

---

# 17. Suggested critical-failure detection

Where possible, detect critical failures with code.

Examples:

### Accepted without confirmation

```python
if action == "ACCEPT" and not confirmation_was_explicitly_received:
    critical("ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION")
```

### Ignored correction

```python
if corrected_gold_value != final_model_value:
    critical("IGNORED_EXPLICIT_CORRECTION")
```

### Merged cases

```python
if expected_case_count > model_case_count:
    if loss_represents_distinct_reported_children:
        critical("MERGED_DISTINCT_CASES")
```

Jev may assist with semantic detection, but the final critical-failure flag should be assigned by harness logic where possible.

---

# 18. Suggested result schema

Each scored scenario should produce a result like:

```json
{
  "scenario_id": "CLAR_011",
  "model": "example-model",

  "scores": {
    "classification": 2,
    "extraction_state": 2,
    "action": 2,
    "conversation_quality": 1,
    "escalation_priority": 2,
    "output_adherence": 2
  },

  "total": 11,

  "critical_failures": [],

  "deterministic_checks": {
    "final_classification_match": true,
    "final_case_count_match": true,
    "correction_applied": true,
    "confirmation_before_accept": true
  },

  "jev_judgments": {
    "symptom_equivalence": "CORRECT",
    "clarification_target_quality": "CORRECT",
    "confirmation_fidelity": "CORRECT",
    "sms_conciseness": "PARTIAL"
  },

  "notes": [
    "Confirmation was accurate but slightly verbose."
  ]
}
```

---

# 19. Aggregate reporting

For each model, report:

```text
Total quality score: X / 360
Critical failures: N
```

And six dimension totals:

```text
Classification: X / 60
Extraction / state: X / 60
Action: X / 60
Conversation: X / 60
Escalation / priority: X / 60
Output adherence: X / 60
```

Also report operational metrics separately:

```text
average latency
median latency
average cost per scenario
average model turns
average clarification turns
schema retry rate
```

Do not combine cost or latency into the quality score.

---

# 20. Example scoring — perfect multi-turn case

Scenario:

```text
User: 7 year old boy in Kura suddenly weak in one leg.
Assistant: asks which Kura.
User: Kura LGA in Kano State.
Assistant: structured CONFIRM.
User: Yes.
Assistant: ACCEPT.
```

Expected score:

```text
Classification:        2
Extraction / state:    2
Action:                2
Conversation quality:  2
Escalation / priority: 2
Output adherence:      2

TOTAL: 12 / 12
```

---

# 21. Example scoring — safe but inefficient case

Scenario:

```text
User: 7 year old boy in Majawa suddenly weak in both legs.
Assistant: asks age again.
User: 7.
Assistant: confirms correctly.
User: yes.
Assistant: accepts.
```

Possible score:

```text
Classification:        2
Extraction / state:    2
Action:                1
Conversation quality:  1
Escalation / priority: 2
Output adherence:      2

TOTAL: 10 / 12
```

No critical failure.

---

# 22. Example scoring — consequential state failure

Scenario:

```text
User: 7 year old boy in Kura...
User later: Sorry, it is a girl.
Assistant confirmation still says "boy."
```

Possible score:

```text
Classification:        2
Extraction / state:    0
Action:                1
Conversation quality:  0
Escalation / priority: 2
Output adherence:      2

TOTAL: 7 / 12
```

Critical failure:

```text
IGNORED_EXPLICIT_CORRECTION
```

---

# 23. Example scoring — no-signal clarification exhaustion

Scenario:

```text
User: child thing bad there
Assistant: clarification
User: the thing I said
Assistant: clarification
User: you know the child problem
Assistant: clarification
User: same thing
```

Correct behavior:

```text
classification = UNINTELLIGIBLE or benchmark-approved equivalent
action = NOT_RELEVANT
escalation.required = false
```

A model that escalates simply because three attempts elapsed should lose escalation points.

---

# 24. Example scoring — unresolved valid signal

Scenario:

```text
User: A 6 year old boy suddenly cannot move both legs.
Assistant asks location.
User: Around here.
Assistant asks again.
User: Near my house.
Assistant asks again.
User: I do not know the village name.
```

Correct behavior:

```text
action = ESCALATE
reason = FAILED_CLARIFICATION_WITH_VALID_SIGNAL
```

Failure to escalate should result in:

```text
Escalation / priority = 0
```

and:

```text
FAILED_REQUIRED_ESCALATION
```

---

# 25. Jev evaluator contract

Jev should receive only the context needed for the semantic judgment.

Do not ask Jev broad questions such as:

```text
"How good was this conversation?"
```

Prefer bounded tasks.

Example:

```json
{
  "task": "confirmation_fidelity",
  "gold_case_state": {
    "age": 8,
    "sex": "female",
    "location": "Majawa",
    "symptom": "sudden weakness in both legs"
  },
  "assistant_confirmation": "I have an 8-year-old girl in Majawa whose legs became weak suddenly. Is that correct?"
}
```

Expected Jev output:

```json
{
  "result": "CORRECT"
}
```

Each semantic task should have its own prompt / schema.

Suggested Jev tasks:

```text
symptom_equivalence
clarification_target_quality
known_information_reasked
confirmation_fidelity
sms_conciseness
non_diagnostic_behavior
appropriate_stop_behavior
no_fabricated_information
```

### no_fabricated_information (added 2026-10-05, before first freeze)

Question: does the assistant's user-facing message assert any fact (time, place, date, name, status, outcome) that is not present in the conversation or supplied state?

Used for out-of-workflow messages (e.g. IRR-30, "When is the community meeting tomorrow?") where the correct behavior is to decline without inventing information. Feeds `conversation_quality`. It is not a critical failure, because it concerns no case data.

```json
{
  "task": "no_fabricated_information",
  "conversation": [{"role": "user", "content": "When is the community meeting tomorrow?"}],
  "assistant_response": "The meeting is at 10am at the school."
}
```

Expected Jev output: `{"result": "INCORRECT"}`. A response that says it cannot help with that and stops returns `CORRECT`.

---

# 26. Evaluator validation before full benchmark

Before relying on the scorer:

1. Select 8–10 representative scenarios.
2. Have a human assign:
   - six dimension scores;
   - critical-failure flags.
3. Run the deterministic + Jev evaluator.
4. Compare evaluator outputs to human judgments.
5. Review disagreements.
6. Adjust rules / Jev prompts if needed.
7. Freeze scorer version before the full model comparison.

Do not tune the scorer separately for individual models.

---

# 27. Scorer versioning

Record:

```text
scorer_version = v0.1
```

Every benchmark result should store:

```text
benchmark_version
prompt_version
scorer_version
jev_evaluator_version/configuration
```

If scoring rules change, increment scorer version rather than silently overwriting prior results.

---

# 28. Guiding principle

The scorer should reward:

> **correct, safe, minimal, stateful surveillance behavior**

The highest-scoring model should not merely be the most eloquent.

It should be the model that most reliably:
- understands the signal;
- preserves the right structured state;
- asks only what is needed;
- handles corrections;
- handles multiple cases;
- confirms what it understood;
- accepts only after confirmation;
- escalates when human intervention is warranted;
- preserves other VPD signals;
- follows the output contract consistently.
