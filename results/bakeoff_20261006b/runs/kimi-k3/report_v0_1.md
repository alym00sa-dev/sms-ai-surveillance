# kimi-k3

Architecture: `end_to_end_llm` · model: `moonshotai/Kimi-K3` · scorer `v0.1`

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| kimi-k3 | 341/360 | 54/60 | 60/60 | 58/60 | 50/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.3 | 16.5 | 0.0476 | 0.0% | no |

## Critical failures

No critical failures.

## Scenarios

| Scenario | Total | Classification | Extraction/state | Action | Conversation | Escalation | Output | Ended | Critical | Notes |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| AFP-01 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-02 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-03 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| AFP-04 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| AFP-05 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-06 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: clarification_target_quality: PARTIAL; conversation_quality: capped at 1 by failed mapped check(s) must_ask_one_targeted_question |
| CLAR-07 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-08 | 10/12 | 0 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | classification: turn 1: classification AFP_SUSPECTED (expected HEALTH_RELATED_UNCLEAR) |
| CLAR-09 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-10 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-11 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-12 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| CLAR-13 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-26 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-27 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| DUP-28 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| ESC-23 | 8/12 | 0 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | classification: turn 1: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 2: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 3: classification HEALTH_RELATED_UNCLEAR (expected UNINTELLIGIBLE); classification: turn 4: classific |
| ESC-24 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: PARTIAL; conversation: non_diagnostic_behavior: PARTIAL |
| ESC-25 | 8/12 | 2 | 2 | 0 | 1 | 1 | 2 | COMPLETED | – | action: turn 2: CLARIFY where ESCALATE expected; conversation: appropriate_stop_behavior: PARTIAL; conversation: clarification_target_quality: INCORRECT; conversation: turn_efficiency: PARTIAL; escalation: escalated with reason 'FAILED_CLARIFICATION_WITH_VALID_SIGNAL' (expected 'CONFLICTING_INFORMAT |
| IRR-29 | 10/12 | 2 | 2 | 2 | 0 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: INCORRECT |
| IRR-30 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: appropriate_stop_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| MESSY-14 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| MESSY-15 | 11/12 | 2 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| MESSY-16 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-17 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| MESSY-18 | 9/12 | 0 | 2 | 2 | 1 | 2 | 2 | COMPLETED | – | classification: turn 1: classification NOT_RELEVANT (expected HEALTH_RELATED_UNCLEAR); conversation: non_diagnostic_behavior: PARTIAL; conversation: sms_conciseness: PARTIAL |
| VPD-19 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-20 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |
| VPD-21 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – | conversation: sms_conciseness: PARTIAL |
| VPD-22 | 12/12 | 2 | 2 | 2 | 2 | 2 | 2 | COMPLETED | – |  |

Terminations: {"COMPLETED": 30}  
Resolver non-compliance: {"turns": 69, "noncompliant": 0, "rate": 0.0}
