# gpt-6-luna

Architecture: `end_to_end_llm` · model: `gpt-6-luna` · scorer `v0.2`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| gpt-6-luna | 337/360 | 54/60 | 57/60 | 54/60 | 55/60 | 57/60 | 60/60 | 0 (0 scen.) | 2.3 | 10.1 | 0.0012 | 0.0% | no |

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
| CLAR-06 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 8/12 | 0 | 1 | 2 | 1 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR); extraction: Jev: recorded symptom loses or adds a detail; conversation: clarification_target_quality: INCORRECT; conversation: symptom_equivalence: PARTIAL |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-13 | 4/12 | 2 | 0 | 0 | 0 | 0 | 2 | PREMATURE_TERMINAL | – | extraction: material state error persisted to the final turn; action: turn 1: off-target clarification; action: turn 2: off-target clarification; action: turn 3: ESCALATE where CLARIFY expected; action: scenario ended PREMATURE_TERMINAL; conversation: appropriate_stop_behavior: PARTIAL; conversation |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 8/12 | 0 | 2 | 0 | 2 | 2 | 2 | PREMATURE_TERMINAL | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 2: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 3: classification NOT_RELEVANT (expected UNINTELLIGIBLE); action: turn 3: NOT_RELEVANT where CLARIFY  |
| ESC-24 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-25 | 7/12 | 2 | 2 | 0 | 0 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; action: turn 3: CLARIFY where ESCALATE expected; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: INCORRECT; conversation: turn_efficiency: INCORRECT; escalation: escalated with reason 'FAILED_CLARIFICATION |
| IRR-29 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| IRR-30 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-15 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR) |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |

Terminations: {"COMPLETED": 28, "PREMATURE_TERMINAL": 2}  
Resolver non-compliance: {"turns": 69, "noncompliant": 0, "rate": 0.0}
