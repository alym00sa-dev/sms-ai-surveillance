# gpt-6.1-sol

Architecture: `end_to_end_llm` · model: `gpt-6.1-sol` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-6.1-sol | 344/360 | 56/60 | 56/60 | 58/60 | 55/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.3 | 15.0 | 0.0229 | 0.0% | no |

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
| CLAR-08 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL; conversation: sms_conciseness: PARTIAL |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 11/12 | 2 | 1 | 2 | 2 | 2 | 2 | COMPLETED | – | extraction: Jev: recorded symptom loses or adds a detail; conversation: symptom_equivalence: PARTIAL |
| CLAR-13 | 11/12 | 2 | 1 | 2 | 2 | 2 | 2 | COMPLETED | – | extraction: Jev: recorded symptom loses or adds a detail; conversation: symptom_equivalence: PARTIAL |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 8/12 | 0 | 0 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 3: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 4: classification NOT_RELEVANT (expected UNINTELLIGIBLE); extraction: material state error persisted to the final turn |
| ESC-24 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL |
| ESC-25 | 7/12 | 2 | 2 | 0 | 0 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; action: turn 3: CLARIFY where ESCALATE expected; conversation: clarification_target_quality: INCORRECT; conversation: sms_conciseness: PARTIAL; conversation: turn_efficiency: INCORRECT; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALI |
| IRR-29 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR) |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |

Terminations: {"COMPLETED": 30}  
Resolver non-compliance: {"turns": 70, "noncompliant": 0, "rate": 0.0}
