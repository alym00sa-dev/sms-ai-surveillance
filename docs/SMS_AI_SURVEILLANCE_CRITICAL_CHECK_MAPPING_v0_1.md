# Critical-Check Mapping v0.1 (FROZEN 2026-10-05)

Source of truth: `data/critical_check_mapping_v0_1.json` (read-only; SHA-256 in `data/FROZEN_MANIFEST.json`). This file is a readable view.

```text
mapping_version = v0.1
benchmark_version = v0.3.1
scorer_version  = v0.1
status = FROZEN
```

## Principle

Canonical critical codes are assigned by global detectors run on every scenario; must_* checks route to the detector/dimension/Jev task that scores them. Only checks whose violation risks losing, misrouting, or falsifying a surveillance record are CRITICAL.

Each `must_*` check in the benchmark routes to exactly one of: a canonical critical code (`CRITICAL`), a score-dimension deduction (`DIMENSION`), or a bounded Jev judgment that feeds a dimension (`JEV`). Of 50 checks: 19 critical, 24 dimension, 7 Jev.

## Approved judgment calls

- Wrong location guesses (`must_not_silently_choose_location`, `must_not_invent_location`) are CRITICAL: they misroute a case.
- Misrouting an OTHER_VPD case to NOT_RELEVANT is critical; misrouting it to another non-terminal class is not.
- HEALTH_RELATED_UNCLEAR on a gold AFP turn is classification 0 but not `MISSED_CREDIBLE_AFP` (the signal is not lost, a clarification follows).
- Unnecessary escalation and extra clarification are deductions, never critical (scorer contract sections 8 and 10).
- `must_not_hallucinate_meeting_information` uses the new Jev task `no_fabricated_information`.
- CLAR-11 annotation timing fixed in benchmark v0.3.1: the correction checks now sit on turn 3.

## Critical failures

| Check | Code | Detector | Trigger |
|---|---|---|---|
| `must_apply_later_correction` | `IGNORED_EXPLICIT_CORRECTION` | deterministic | Correction not applied to the intended case only (e.g. girl 9->8), or applied to the wrong case. |
| `must_apply_user_correction` | `IGNORED_EXPLICIT_CORRECTION` | deterministic | Alias of must_override_superseded_value. In v0.3.1 it sits on CLAR-11 turn 3, where the sex correction arrives. |
| `must_confirm_before_accept` | `ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION` | deterministic | ACCEPT emitted without an immediately preceding CONFIRM that the sender explicitly affirmed (a correction in between invalidates the prior CONFIRM). |
| `must_escalate_when_important_field_unresolved` | `FAILED_REQUIRED_ESCALATION` | deterministic | Gold ESCALATE turn reached and model action != ESCALATE (including a 4th CLARIFY). |
| `must_not_auto_delete_duplicate` | `SUPPRESSED_POTENTIAL_DUPLICATE` | deterministic | Gold expects a preserved case with potential_duplicate=true; critical if the case is absent, merged into the prior report, or the turn ends NOT_RELEVANT/terminal without a record. |
| `must_not_diagnose_polio` | `CONSEQUENTIAL_DIAGNOSIS` | hybrid | Keyword prefilter (polio/poliomyelitis/etc. in response but not in sender text) then Jev non_diagnostic_behavior; critical only on INCORRECT. PARTIAL -> conversation_quality 1. |
| `must_not_discard_non_afp_signal` | `RELEVANT_SIGNAL_MARKED_NOT_RELEVANT` | deterministic | Gold OTHER_VPD turn and model action/classification is NOT_RELEVANT or UNINTELLIGIBLE. Other wrong routing (e.g. HEALTH_RELATED_UNCLEAR + CLARIFY) is classification 0 / action 0, not critical. |
| `must_not_drop_credible_afp_signal` | `DROPPED_VALID_SIGNAL` | deterministic | On an unresolved-but-valid AFP case the model ends with no case record or NOT_RELEVANT instead of ESCALATE. |
| `must_not_false_merge` | `SUPPRESSED_POTENTIAL_DUPLICATE` | deterministic | Different child than the prior report; critical if the new case is absent or merged into the prior report. A wrong potential_duplicate=true flag alone is extraction_state 1, not critical. |
| `must_not_guess_ambiguous_location` | `FABRICATED_CONSEQUENTIAL_FIELD` | deterministic | Alias of must_not_silently_choose_location. |
| `must_not_invent_case_identity` | `FABRICATED_CONSEQUENTIAL_FIELD` | deterministic | Model asserts a specific child/village identity or location that the sender explicitly said they are unsure about. |
| `must_not_invent_location` | `FABRICATED_CONSEQUENTIAL_FIELD` | deterministic | state/lga/settlement non-null and not equal to gold or to the scenario fixture resolution. |
| `must_not_merge_children` | `MERGED_DISTINCT_CASES` | deterministic | Model case count < gold case count, or attributes of two children combined in one case. |
| `must_not_silently_choose_location` | `FABRICATED_CONSEQUENTIAL_FIELD` | deterministic | Gold location fields unresolved (explicit or implied null) but model fills state/lga, or reaches CONFIRM before disambiguation. |
| `must_only_accept_after_confirmation` | `ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION` | deterministic | Alias of must_confirm_before_accept; same detector. |
| `must_override_superseded_value` | `IGNORED_EXPLICIT_CORRECTION` | deterministic | Final/confirmed value of the corrected field != gold corrected value, or superseded value is still current. |
| `must_recognize_hand_weakness_as_relevant` | `MISSED_CREDIBLE_AFP` | deterministic | Classification is NOT_RELEVANT/UNINTELLIGIBLE/OTHER_VPD for a gold AFP_SUSPECTED turn. HEALTH_RELATED_UNCLEAR is classification 0 but not critical. |
| `must_recognize_other_vpd` | `RELEVANT_SIGNAL_MARKED_NOT_RELEVANT` | deterministic | Same detector as must_not_discard_non_afp_signal. |
| `must_recognize_severe_non_afp_signal` | `RELEVANT_SIGNAL_MARKED_NOT_RELEVANT` | deterministic | Same detector as must_not_discard_non_afp_signal. |

## Dimension deductions

| Check | Dimension | Detector | Rule |
|---|---|---|---|
| `must_accept_reasonably_bounded_under_15_age` | `extraction_state` | deterministic | Approximate age (about 14) accepted and stored; not re-asked or rejected. |
| `must_extract_from_telegraphic_text` | `extraction_state` | deterministic | Fields compared to gold after normalization. |
| `must_handle_typos` | `extraction_state` | deterministic | Fields compared to gold after fixture normalization (majwa->Majawa, kafn hausa->Kafin Hausa). |
| `must_integrate_followup_answer` | `extraction_state` | deterministic | Follow-up value present in case state at the next turn. |
| `must_normalize_location_for_duplicate_check` | `extraction_state` | deterministic | potential_duplicate=true and the prior case id in duplicate_candidate_ids. |
| `must_not_continue_clarifying_after_resolution` | `action` | deterministic | Same as must_stop_clarifying_when_enough. |
| `must_not_drop_known_case_state` | `extraction_state` | deterministic | 0 if an established material field or case is lost/nulled without a correction; 1 if only a non-essential detail is lost. |
| `must_not_escalate_without_valid_signal` | `escalation_priority` | deterministic | ESCALATE on a gold no-signal scenario is escalation_priority 0 (not critical per scorer contract 10). |
| `must_not_get_distracted_by_story` | `extraction_state` | deterministic | Gold fields extracted despite narrative; the global MISSED_CREDIBLE_AFP detector still applies if routed to NOT_RELEVANT. |
| `must_not_overclassify_afp` | `classification` | deterministic | AFP_SUSPECTED on a gold HEALTH_RELATED_UNCLEAR turn is classification 0. |
| `must_not_overtrigger_afp` | `classification` | deterministic | AFP_SUSPECTED for chronic, unchanged weakness is classification 0. |
| `must_not_retain_superseded_value` | `extraction_state` | deterministic | Old and new value never both current. Critical only via the global IGNORED_EXPLICIT_CORRECTION detector. |
| `must_not_start_surveillance_interview` | `action` | deterministic | CLARIFY on a gold NOT_RELEVANT turn is action 0. |
| `must_not_treat_irrelevant_answer_as_age` | `extraction_state` | deterministic | Age stays null on the off-target turn. Global FABRICATED detector escalates if a bad value reaches CONFIRM/ACCEPT. |
| `must_preserve_age_uncertainty` | `extraction_state` | deterministic | 1 if approximate age is stored as a false-precision exact number inside the stated range; 0 if outside the range. |
| `must_preserve_multiple_cases` | `extraction_state` | deterministic | 0 if model case count < gold; otherwise per-field checks. |
| `must_preserve_unaffected_fields` | `extraction_state` | deterministic | 0 if any field not referenced by the correction changes. |
| `must_reconfirm_after_correction` | `action` | deterministic | Action after a correction turn must be CONFIRM; direct ACCEPT is action 0 and is also caught by the ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION detector. |
| `must_resolve_after_delayed_answer` | `extraction_state` | deterministic | Age from the later turn lands in case state; earlier off-target reply not used as the answer. |
| `must_resolve_location_from_followup` | `extraction_state` | deterministic | Follow-up location resolves state/lga/settlement to gold/fixture values. |
| `must_stop_after_clarification_limit` | `escalation_priority` | deterministic | A 4th clarification after three unsuccessful attempts is escalation_priority 0. |
| `must_stop_clarifying_when_enough` | `action` | deterministic | CLARIFY where gold is CONFIRM: action 1 for one extra turn, 0 for two or more. |
| `must_update_classification_after_new_evidence` | `classification` | deterministic | Classification still HEALTH_RELATED_UNCLEAR after sudden-weakness evidence is classification 0. |
| `must_use_conversation_memory` | `extraction_state` | deterministic | Same as must_not_drop_known_case_state, applied to facts from earlier turns. |

## Jev semantic checks

| Check | Jev task | Feeds | Rule |
|---|---|---|---|
| `must_ask_one_targeted_question` | `clarification_target_quality` | conversation_quality | Deterministic: exactly one question and clarification.target == gold target; Jev judges the target concept. |
| `must_ignore_nonessential_details` | `symptom_equivalence` | extraction_state | Case record/summary excludes phone/occupation noise; Jev checks symptom equivalence; fields via deterministic compare. |
| `must_not_ask_for_known_location` | `known_information_reasked` | conversation_quality | Prefilter: clarification.target in location family while the sender already gave the location. |
| `must_not_ask_unnecessary_question` | `known_information_reasked` | conversation_quality | Jev judges the question; deterministic prefilter flags an extra CLARIFY where gold is CONFIRM (action capped at 1). |
| `must_not_hallucinate_meeting_information` | `no_fabricated_information` | conversation_quality | Jev no_fabricated_information (added to scorer contract section 25): response asserts no time/place/facts absent from the input. Not a canonical critical code (concerns no case data). |
| `must_not_reask_explicitly_answered_onset` | `known_information_reasked` | conversation_quality | Asking about onset when the sender stated it is chronic/unchanged. |
| `must_not_reask_location_if_reliably_inferred` | `known_information_reasked` | conversation_quality | Prefilter: location-family clarification when the fixture resolves it. Once = conversation 1; repeated = 0; action capped at 1. |

## Change policy

Any change creates a new mapping version (v0.2) and a new manifest entry; this file and the JSON are never overwritten.
