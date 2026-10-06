# gemini-3.8-flash

Architecture: `end_to_end_llm` · model: `gemini-3.8-flash` · scorer `v0.2`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gemini-3.8-flash | 337/360 | 54/60 | 56/60 | 56/60 | 53/60 | 59/60 | 59/60 | 0 (0 scen.) | 2.4 | 19.5 | 0.0144 | 0.0% | no |

## Critical failures

No critical failures.

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-04 | 10/12 | 2 | 1 | 2 | 1 | 2 | 2 | COMPLETED | – | extraction: symptom wording differs from gold features; conversation: confirmation_fidelity: PARTIAL; conversation: symptom_equivalence: PARTIAL; conversation: turn_efficiency: PARTIAL |
| AFP-05 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-06 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 6/12 | 2 | 1 | 0 | 0 | 2 | 1 | COMPLETED | – | extraction: Jev: recorded symptom loses or adds a detail; action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: off-target clarification; conversation: clarification_target_quality: INCORRECT; conversation: known_information_reasked: PARTIAL; conversation: symptom_equivalence: PARTIAL; con |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-26 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: confirmation_fidelity: INCORRECT |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 2: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 3: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 4: classific |
| ESC-24 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-25 | 8/12 | 2 | 2 | 0 | 1 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: INCORRECT; conversation: turn_efficiency: PARTIAL; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALID_SIGNAL' (expected 'CONFLICTING_INFORMAT |
| IRR-29 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 7/12 | 0 | 0 | 2 | 1 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); extraction: material state error persisted to the final turn; conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |

Terminations: {"COMPLETED": 30}  
Resolver non-compliance: {"turns": 72, "noncompliant": 0, "rate": 0.0}
