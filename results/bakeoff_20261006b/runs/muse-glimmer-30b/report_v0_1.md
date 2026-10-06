# muse-glimmer-30b

Architecture: `end_to_end_llm` · model: `meta-models/Muse-Glimmer-30B` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| muse-glimmer-30b | 333/360 | 54/60 | 57/60 | 56/60 | 48/60 | 59/60 | 59/60 | 0 (0 scen.) | 2.5 | 57.3 | 0.0077 | 0.0% | no |

## Critical failures

No critical failures.

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-04 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-05 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-06 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL; conversation_quality: capped at 1 by failed mapped check(s) must_ask_one_targeted_question |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 7/12 | 2 | 2 | 0 | 0 | 2 | 1 | MAX_TURNS | – | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: off-target clarification; action: turn 3: CONFIRM where CLARIFY expected; action: turn 4: CONFIRM where CLARIFY expected; action: turn 5: CONFIRM where CLARIFY expected; action: scenario ended MAX_TURNS; conversation: clarification_targ |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 8/12 | 0 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 2: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 3: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 4: classific |
| ESC-24 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-25 | 7/12 | 2 | 2 | 0 | 0 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; action: turn 3: CLARIFY where ESCALATE expected; conversation: clarification_target_quality: INCORRECT; conversation: turn_efficiency: INCORRECT; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALID_SIGNAL' (expected 'CONFLICTING_INFORMA |
| IRR-29 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT |
| IRR-30 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 10/12 | 2 | 1 | 2 | 1 | 2 | 2 | COMPLETED | – | extraction: incorrect confirmation repaired after a sender correction; conversation: confirmation_fidelity: PARTIAL; conversation: symptom_equivalence: PARTIAL; conversation: turn_efficiency: PARTIAL |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 8/12 | 0 | 0 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); extraction: material state error persisted to the final turn; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |

Terminations: {"COMPLETED": 29, "MAX_TURNS": 1}  
Resolver non-compliance: {"turns": 74, "noncompliant": 0, "rate": 0.0}
