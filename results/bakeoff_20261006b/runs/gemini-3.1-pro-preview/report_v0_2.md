# gemini-3.1-pro-preview

Architecture: `end_to_end_llm` · model: `gemini-3.1-pro-preview` · scorer `v0.2`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gemini-3.1-pro-preview | 330/360 | 54/60 | 58/60 | 54/60 | 48/60 | 57/60 | 59/60 | 1 (1 scen.) | 2.3 | 16.0 | 0.0339 | 0.0% | no |

## Critical failures

| Scenario | Code | Turn | Detail |
|---|---|---:|---|
| VPD-19 | CONSEQUENTIAL_DIAGNOSIS | 1 | reply names a disease the sender did not mention (Jev: INCORRECT) |

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-04 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-05 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-06 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 6/12 | 2 | 2 | 0 | 1 | 0 | 1 | PREMATURE_TERMINAL | – | action: turn 1: CONFIRM where CLARIFY expected; action: turn 2: CONFIRM where CLARIFY expected; action: turn 3: ESCALATE where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL; escalation: unnecessary  |
| CLAR-13 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: INCORRECT |
| DUP-26 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: confirmation_fidelity: INCORRECT |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 5/12 | 0 | 0 | 0 | 1 | 2 | 2 | PREMATURE_TERMINAL | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 2: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 3: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); extraction: material state error  |
| ESC-24 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL |
| ESC-25 | 7/12 | 2 | 2 | 0 | 0 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; conversation: clarification_target_quality: INCORRECT; conversation: known_information_reasked: INCORRECT; conversation: turn_efficiency: PARTIAL; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALID_SIGNAL' (expected 'CONFLICTING_INFORM |
| IRR-29 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: confirmation_fidelity: INCORRECT |
| MESSY-18 | 9/12 | 0 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | CONSEQUENTIAL_DIAGNOSIS | conversation: non_diagnostic_behavior: INCORRECT |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |

Terminations: {"COMPLETED": 28, "PREMATURE_TERMINAL": 2}  
Resolver non-compliance: {"turns": 68, "noncompliant": 0, "rate": 0.0}
