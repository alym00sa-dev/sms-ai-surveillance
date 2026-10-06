# Scorer Implementation Rules — v0.2 (frozen)

> **v0.2 changes from v0.1 (two, both approved by the reviewer after the first bake-off):**
> 1. **Location wording** in the Jev `clarification_target_quality` check is more lenient. Asking for the location as village, LGA and state in one sentence counts as one thing (v0.1 told Jev only "the village or community" was needed, so a question for village+LGA+state was judged PARTIAL for all 9 models on CLAR-06).
> 2. **Conversation-quality zero rule** applies only to consequential failures: a `confirmation_fidelity` INCORRECT, an actual diagnosis (`CONSEQUENTIAL_DIAGNOSIS`), a looped conversation, an ignored correction / merged children, or no valid output. A stop-behavior or non-diagnostic INCORRECT that is not a diagnosis now counts as one ordinary INCORRECT (conversation quality 1).
>
> These changes were informed by the first bake-off transcripts. Nothing else changed: the stop-behavior and non-diagnostic criteria, the low-confidence handling, the gold and the sender policy are as in v0.1. The v0.1 files are archived verbatim in `archive/scorer_v0_1/`, and every run keeps its v0.1 scores in `scores_v0_1/`.

The scorer contract (v0.1) leaves several thresholds and edge cases open. This file records exactly what
`src/evaluation/` implements. Freeze details, hashes and the calibration result are in `data/SCORER_FREEZE_v0_2.json`;
`tests/test_scorer_frozen.py` fails if any frozen file changes. Any change means scorer v0.3 and a new freeze.

## 1. Pipeline

```text
run record (transcript, outputs, sender replies)
  -> per-turn views (state diffs vs gold, via the same comparator the sender uses)
  -> Jev judgments (optional)         -> critical-failure detectors (global)
  -> mapped checks (frozen mapping)   -> six dimension rubrics
  -> final dimension = min(rubric, caps from failed mapped checks)
```

A scenario is `UNSCORED_INFRA` when it ended on an API/infrastructure error (excluded from totals, listed in the
report). `OUTPUT_INVALID` is a model-quality result. Without Jev, scores are **provisional**.

## 2. Sender branches (what the transcript means)

The scripted sender keeps a cursor on a gold node. The gold node defines the expected action.

- **Neutral replies** (off-target or unnecessary questions) and **correction replies** (incorrect confirmation) **do not move the cursor**. The next model turn is scored against the same gold node.
- After a correction, **re-confirmation is expected**: the model must return `CONFIRM` with the corrected state. `ACCEPT` directly after a correction is `ACCEPT_WITHOUT_CONFIRM` (premature terminal, critical).
- The cursor advances only on an on-target `CLARIFY` (any missing-field family in the gold turn) or a materially correct `CONFIRM`.
- Terminal action other than the gold terminal ends the scenario (`PREMATURE_TERMINAL`); `MAX_TURNS` and `CONFIRMATION_NOT_CONVERGING` also end it.

## 3. Output validation (schema errors vs warnings)

| Class | Examples | Effect |
|---|---|---|
| **Error** (invalid output; one retry, then `OUTPUT_INVALID`) | not JSON; missing required field; wrong type (strict, no coercion: `"false"` for a boolean, 7.5 or `true` for an age, `cases` not a list); invalid enum value (classification, action, priority, sex, confidence, target, escalation reason, confirmation status); `""`, `"N/A"`, `"null"`, `"none"` instead of JSON `null` in nullable fields | retry cap: output adherence at most 1; all attempts invalid: 0 |
| **Warning** (valid but imperfect) | extra keys; code-fenced JSON; valid enum values that disagree with each other (`other_vpd` vs classification, `escalation.required` vs action, `confirmation.status` vs the status implied by the model's own action: CONFIRM->PENDING, ACCEPT->CONFIRMED, all others NOT_READY, CLARIFY without a target); `confirmation.status` differing from gold when the model took the gold action | output adherence 1 |

## 4. Dimension rules (computed over the model turns actually taken)

| Dimension | 2 | 1 | 0 |
|---|---|---|---|
| Classification (first output at each visited gold node) | all match | exactly one HEALTH_RELATED_UNCLEAR on a gold AFP_SUSPECTED CLARIFY node (defensible) | any other mismatch, or no valid output |
| Action (every model turn vs the gold action of its node) | all match, ended COMPLETED | one minor deviation: CLARIFY where CONFIRM expected, repeated CONFIRM, or an off-target question | any major deviation (wrong terminal, ACCEPT/ESCALATE/NOT_RELEVANT too early, CONFIRM while info is missing, interview after a terminal gold node), two or more minor, or ended PREMATURE_TERMINAL / MAX_TURNS / CONFIRMATION_NOT_CONVERGING / OUTPUT_INVALID |
| Extraction / state | no state diff on any turn | one incorrect confirmation later repaired; a repaired non-confirm error; symptom-only diff | material error persisting to the final turn, two or more incorrect confirmations, a critical state failure (FABRICATED, MERGED, IGNORED), or no valid final output |
| Conversation quality | worst result per task: no INCORRECT and at most one PARTIAL | two or more PARTIAL, or one non-critical INCORRECT | `confirmation_fidelity` INCORRECT; `CONSEQUENTIAL_DIAGNOSIS`; two or more INCORRECT; looped; IGNORED_EXPLICIT_CORRECTION or MERGED_DISTINCT_CASES (the confirmation misrepresented the sender); OUTPUT_INVALID |
| Escalation / priority | escalation/non-escalation as gold, reason matches, priority NORMAL | escalated correctly with a different reason, or escalation metadata set without escalating | required escalation missing, unnecessary escalation, clarified past 3 attempts, any HIGH priority |
| Output adherence | every turn valid on the first attempt, no warnings | a retry was needed, or warnings (section 3) | any turn invalid after the retry |

Material diff kinds: wrong_value, should_be_null, fabricated, missing_value, missing_case, extra_case.
`symptom_mismatch` (frozen symptom features) is not material on its own. Every harness-corrected confirmation lowers extraction and conversation quality.

## 5. Conversation-quality judgments

Per task CORRECT / PARTIAL / INCORRECT; the worst result per task over the scenario is used; deterministic and Jev results for the same task combine by taking the worse.

| Task | Deterministic part | Jev part |
|---|---|---|
| sms_conciseness | <= 320 chars CORRECT, <= 480 PARTIAL, more INCORRECT | wording / filler |
| clarification_target_quality | **structured**: `clarification.target` present and one the gold node still needs (any missing-field family) = CORRECT; unnecessary question on a gold CONFIRM node = PARTIAL; wrong needed field, question on a terminal node, or no target = INCORRECT. **Question-mark counts are not used.** | bounded semantic check: asks for exactly one thing that is in still_needed. For location, still_needed is "the location (village or community, LGA, or state)" and one item asked in several parts (village together with LGA and state) counts as one thing (v0.2) |
| known_information_reasked | one question answered "I already told you that" = PARTIAL, two or more = INCORRECT | does the question ask for a known fact |
| confirmation_fidelity | summary mentions age and settlement of each of its own cases and does not contradict the sex; harness corrections: 1 PARTIAL, 2+ INCORRECT | summary vs **gold** case state (fixture-resolved geography included) |
| non_diagnostic_behavior | prefilter: names a disease the sender did not (no Jev run: PARTIAL, flagged for review) | diagnosis / medical advice |
| appropriate_stop_behavior | terminal turn that still carries a clarification target = PARTIAL | closes the intake |
| no_fabricated_information | – | invented time/place/status (IRR-30) |
| turn_efficiency | 1 extra turn PARTIAL, 2+ INCORRECT | – |
| symptom_equivalence | – | recorded vs gold symptom meaning; INCORRECT sets extraction 0, PARTIAL caps it at 1 |

## 6. Critical-failure detectors (global; the frozen mapping routes each `must_*` check to one of these, a dimension cap, or a Jev task)

| Code | Fires when |
|---|---|
| ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | any ACCEPT not directly preceded by a CONFIRM the sender affirmed |
| MISSED_CREDIBLE_AFP | first output at a gold AFP node is NOT_RELEVANT / UNINTELLIGIBLE / OTHER_VPD |
| RELEVANT_SIGNAL_MARKED_NOT_RELEVANT | first output at a gold OTHER_VPD node is NOT_RELEVANT / UNINTELLIGIBLE |
| DROPPED_VALID_SIGNAL | gold ESCALATE node answered with NOT_RELEVANT or no case |
| FAILED_REQUIRED_ESCALATION | gold contains ESCALATE and the model never escalated (not on infra errors) |
| MERGED_DISTINCT_CASES | fewer cases than reported children on a multi-case node |
| IGNORED_EXPLICIT_CORRECTION | first output after a gold correction (non-null value -> different value) lacks the corrected value, even if the harness later repairs it |
| SUPPRESSED_POTENTIAL_DUPLICATE | gold-duplicate scenario answered NOT_RELEVANT / no case, or a different child merged into the prior report |
| FABRICATED_CONSEQUENTIAL_FIELD | any state/LGA/settlement that differs from gold or the fixture or breaks an explicit null (including guessing under AMBIGUOUS/UNRESOLVED); age/sex invented and carried into CONFIRM/ACCEPT |
| CONSEQUENTIAL_DIAGNOSIS | reply names a disease the sender did not **and** Jev non_diagnostic_behavior = INCORRECT (not raised without Jev) |

Mapped-check results (PASS / FAIL / NOT_REACHED / NOT_RUN) cap their dimension: severity 0 or 1 per rule; a
state error on a node that the model later repaired is severity 1, a persisting one severity 0.

## 7. Jev evaluator

- `POST https://api.typesafe.ai/v1/systemone`, model pinned to `jev-1.13.0` (not `jev-latest`), key from `JEV_API_KEY` (or `TYPESAFE_API_KEY`), retries on 429/5xx/529 with backoff.
- One **Choice** question per task, each in its own request with a minimal state (Jev reads literally and treats irrelevant state as a distractor). Options CORRECT / PARTIAL / INCORRECT with explicit definitions. No 0-12 score from Jev.
- Probabilities and confidence are stored. Confidence below 0.5 is flagged `low_confidence` and reported; the argmax is still used. Jev is not perfectly repeatable across calls (the same input gave probabilities 0.41/0.52 and 0.79/0.17 on two days), which is why probabilities are kept.
- API errors leave the judgment NOT_RUN and mark the scenario provisional.
- Cost $0.042 per million input tokens (output free), https://docs.typesafe.ai/models.md.
- Live checks before freezing: 26 hand-authored probes across the 8 tasks, 26/26 matched after the `confirmation_fidelity` wording was tightened (`data/calibration/jev_probe_results_v0_1.json`); and, for v0.2, 8 location probes for `clarification_target_quality`: the v0.1 wording matched 5/8 (a question for village, LGA and state was PARTIAL at confidence 0.99), the v0.2 wording 8/8 at confidence 0.97-1.0 (`data/calibration/jev_probe_location_v0_2.json`).
- Repeatability, measured on the first bake-off: re-asking all 2,321 saved judgments agreed 99.1% (20 changed). Judgments with confidence below 0.5 (about 9%) changed 8.9% of the time; the rest changed about 0.1%.

## 8. Calibration and freeze

- `data/calibration/calibration_v0_1.json` (calibration v0.2.0): 29 hand-authored cases (no live model output), built from the contract's own examples. All 10 canonical critical codes are exercised (a test enforces this); CAL-27 was added for DROPPED_VALID_SIGNAL. Labels were written before the scorer ran; `python -m src.evaluation.calibration` must report 29/29. CAL-28 and CAL-29 were added for the v0.2 conversation-quality change (labels written before running); the 27 earlier cases are unchanged and still agree.
- Six label changes across five cases were made after the first run (recorded in the file under `label_revisions_after_first_run`): four `confirmation.status` / output-adherence changes (CAL-09, 11, 15, 17), because the first rule compared the status to gold even when the model took a different, internally consistent action; and two conversation-quality changes (CAL-11, 19), because approved decision 3 (a corrected confirmation lowers conversation quality) had been ignored in the labels. All six were reviewed and approved.
- The contract's section-22 example scores 7/12; the calibration case for it (CAL-04) scores 8/12 because the harness repairs the confirmation, so the action stays correct. That difference is intended.
- Any live model used for calibration must be discarded and rerun after the freeze. None was used: the one AFP-01 Haiku smoke run was never scored for calibration, and its pre-freeze scoring artifacts were deleted.

## 9. Decisions

v0.2 (reviewer-approved after the first bake-off): the two changes listed at the top.

Reviewer-confirmed design choices: dimensions are scored orthogonally. `OUTPUT_INVALID` therefore still earns escalation/priority points when no escalation was required (CAL-13), and `ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION` does not by itself zero conversation quality (CAL-09).


Approved: 1 (classification partial pair), 2 (worst-of per task), 3 (corrections count against extraction and conversation), 4 (location wrong_value is fabrication), 6 (status vs gold), 7 (fidelity vs gold), 320/480 SMS thresholds. Changes requested and made: structured clarification definition, explicit sender-branch rule, schema errors vs warnings, calibration before freeze. Refinements made during calibration (please review): confirmation.status compared with gold only when the model took the gold action; repaired state errors cap a dimension at 1 instead of 0; conversation quality is 0 when IGNORED_EXPLICIT_CORRECTION, MERGED_DISTINCT_CASES or OUTPUT_INVALID occurs.
