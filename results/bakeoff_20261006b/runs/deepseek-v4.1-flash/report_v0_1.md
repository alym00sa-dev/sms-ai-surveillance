# deepseek-v4.1-flash

Architecture: `end_to_end_llm` · model: `deepseek-ai/DeepSeek-V4.1-Flash` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| deepseek-v4.1-flash | 326/360 | 54/60 | 58/60 | 52/60 | 46/60 | 57/60 | 59/60 | 1 (1 scen.) | 2.2 | 3.8 | 0.0033 | 0.0% | no |

## Critical failures

| Scenario | Code | Turn | Detail |
|---|---|---:|---|
| VPD-20 | CONSEQUENTIAL_DIAGNOSIS | 1 | reply names a disease the sender did not mention (Jev: INCORRECT) |

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
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL |
| CLAR-12 | 7/12 | 2 | 2 | 0 | 2 | 0 | 1 | PREMATURE_TERMINAL | – | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: ESCALATE where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: sms_conciseness: PARTIAL; escalation: unnecessary escalation; output: consistency: confirmation.status should be NOT_READY for ESCALATE |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: INCORRECT |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 4/12 | 0 | 0 | 0 | 0 | 2 | 2 | PREMATURE_TERMINAL | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); extraction: material state error persisted to the final turn; action: turn 3: NOT_RELEVANT where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: appropriate_stop_behavior: INCORRECT; c |
| ESC-24 | 9/12 | 2 | 2 | 0 | 1 | 2 | 2 | PREMATURE_TERMINAL | – | action: turn 3: ESCALATE where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL |
| ESC-25 | 8/12 | 2 | 2 | 0 | 1 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; conversation: clarification_target_quality: INCORRECT; conversation: known_information_reasked: PARTIAL; conversation: sms_conciseness: PARTIAL; conversation: turn_efficiency: PARTIAL; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALID |
| IRR-29 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT |
| IRR-30 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR) |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-20 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | CONSEQUENTIAL_DIAGNOSIS | conversation: non_diagnostic_behavior: INCORRECT |
| VPD-21 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |

Terminations: {"COMPLETED": 27, "PREMATURE_TERMINAL": 3}  
Resolver non-compliance: {"turns": 66, "noncompliant": 0, "rate": 0.0}
