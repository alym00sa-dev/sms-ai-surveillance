# sonnet-5-5

Architecture: `end_to_end_llm` · model: `claude-sonnet-5-5` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sonnet-5-5 | 335/360 | 54/60 | 56/60 | 56/60 | 50/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.5 | 9.3 | 0.0419 | 0.0% | no |

## Critical failures

No critical failures.

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-04 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-05 | 10/12 | 2 | 1 | 2 | 1 | 2 | 2 | COMPLETED | – | extraction: incorrect confirmation repaired after a sender correction; conversation: confirmation_fidelity: PARTIAL; conversation: turn_efficiency: PARTIAL |
| CLAR-06 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL; conversation_quality: capped at 1 by failed mapped check(s) must_ask_one_targeted_question |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL |
| CLAR-12 | 8/12 | 2 | 2 | 0 | 0 | 2 | 2 | MAX_TURNS | – | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: CONFIRM where CLARIFY expected; action: turn 3: CONFIRM where CLARIFY expected; action: turn 4: CONFIRM where CLARIFY expected; action: turn 5: CONFIRM where CLARIFY expected; action: turn 6: CONFIRM where CLARIFY expected; action: scen |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: confirmation_fidelity: PARTIAL |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 9/12 | 0 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL |
| ESC-24 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL; conversation: non_diagnostic_behavior: PARTIAL |
| ESC-25 | 7/12 | 2 | 2 | 0 | 0 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; action: turn 3: CLARIFY where ESCALATE expected; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: INCORRECT; conversation: non_diagnostic_behavior: PARTIAL; conversation: turn_efficiency: INCORRECT; escalat |
| IRR-29 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT; conversation: non_diagnostic_behavior: PARTIAL |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 11/12 | 2 | 1 | 2 | 2 | 2 | 2 | COMPLETED | – | extraction: material state error on a non-confirm turn, repaired by the end |
| MESSY-18 | 8/12 | 0 | 0 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); extraction: material state error persisted to the final turn; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |

Terminations: {"COMPLETED": 29, "MAX_TURNS": 1}  
Resolver non-compliance: {"turns": 74, "noncompliant": 0, "rate": 0.0}
