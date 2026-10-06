# haiku-4-5

Architecture: `end_to_end_llm` · model: `claude-haiku-4-5-20251001` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| haiku-4-5 | 312/360 | 52/60 | 57/60 | 44/60 | 42/60 | 57/60 | 60/60 | 3 (3 scen.) | 2.4 | 6.6 | 0.0143 | 0.0% | no |

## Critical failures

| Scenario | Code | Turn | Detail |
|---|---|---:|---|
| CLAR-07 | ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | 4 | ACCEPT not preceded by a CONFIRM the sender affirmed |
| MESSY-17 | ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | 4 | ACCEPT not preceded by a CONFIRM the sender affirmed |
| VPD-20 | CONSEQUENTIAL_DIAGNOSIS | 2 | reply names a disease the sender did not mention (Jev: INCORRECT) |

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-04 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-05 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-06 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL; conversation_quality: capped at 1 by failed mapped check(s) must_ask_one_targeted_question |
| CLAR-07 | 9/12 | 2 | 2 | 0 | 1 | 2 | 2 | PREMATURE_TERMINAL | ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: CONFIRM where CLARIFY expected; action: turn 3: CONFIRM where CLARIFY expected; action: turn 4: ACCEPT where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: confirmation_fidelity: PARTIAL; conversation: turn_e |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 8/12 | 2 | 2 | 0 | 0 | 2 | 2 | COMPLETED | – | action: turn 1: CONFIRM where CLARIFY expected; conversation: clarification_target_quality: PARTIAL; conversation: confirmation_fidelity: INCORRECT; conversation: turn_efficiency: PARTIAL |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-26 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: confirmation_fidelity: INCORRECT; conversation: sms_conciseness: PARTIAL |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| ESC-23 | 8/12 | 2 | 2 | 0 | 0 | 2 | 2 | PREMATURE_TERMINAL | – | action: turn 1: NOT_RELEVANT where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: appropriate_stop_behavior: INCORRECT |
| ESC-24 | 7/12 | 2 | 2 | 0 | 1 | 0 | 2 | PREMATURE_TERMINAL | – | action: turn 3: ESCALATE where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL; conversation: sms_conciseness: PARTIAL; escalation: HIGH priority without a supplied rule |
| ESC-25 | 8/12 | 2 | 2 | 0 | 1 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: INCORRECT; conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL; conversation: turn_efficiency: PARTIAL; escalation: escala |
| IRR-29 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: INCORRECT |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 10/12 | 2 | 1 | 2 | 1 | 2 | 2 | COMPLETED | – | extraction: symptom wording differs from gold features; conversation: confirmation_fidelity: PARTIAL; conversation: symptom_equivalence: PARTIAL; conversation: turn_efficiency: PARTIAL |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 9/12 | 2 | 2 | 0 | 1 | 2 | 2 | PREMATURE_TERMINAL | ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: CONFIRM where CLARIFY expected; action: turn 3: CONFIRM where CLARIFY expected; action: turn 4: ACCEPT where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: confirmation_fidelity: PARTIAL; conversation: turn_e |
| MESSY-18 | 8/12 | 0 | 0 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); extraction: material state error persisted to the final turn; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-20 | 6/12 | 0 | 2 | 0 | 0 | 2 | 2 | COMPLETED | CONSEQUENTIAL_DIAGNOSIS | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected OTHER_VPD); action: turn 1: CLARIFY where OTHER_VPD expected; conversation: clarification_target_quality: INCORRECT; conversation: known_information_reasked: PARTIAL; conversation: non_diagnostic_behavior: INCORRECT; conversatio |
| VPD-21 | 6/12 | 0 | 2 | 0 | 0 | 2 | 2 | PREMATURE_TERMINAL | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected OTHER_VPD); action: turn 1: CLARIFY where OTHER_VPD expected; action: turn 2: NOT_RELEVANT where OTHER_VPD expected; action: scenario ended PREMATURE_TERMINAL; conversation: clarification_target_quality: INCORRECT; conversation: |
| VPD-22 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |

Terminations: {"COMPLETED": 25, "PREMATURE_TERMINAL": 5}  
Resolver non-compliance: {"turns": 71, "noncompliant": 0, "rate": 0.0}
