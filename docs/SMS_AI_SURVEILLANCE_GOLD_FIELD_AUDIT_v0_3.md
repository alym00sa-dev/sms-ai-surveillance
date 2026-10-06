# Gold Field Audit — Benchmark v0.3

## Rule adopted

- Field omitted from a gold case: **not scored**.
- Field explicitly `null`: **must remain unresolved**.
- Field with a value: **must match** (after normalization).

`sex = "unknown"` and `null` are both treated as unresolved.

## What the audit found

Across all gold cases, 119 field omissions occur in 24 of 30 scenarios:

| Cause | Count | Handling |
|---|---:|---|
| Field named in `missing_important_fields` (age, location) | 30 | Clear intent: unresolved. See flag 1. |
| Non-AFP or terminal turn (OTHER_VPD, NOT_RELEVANT) | 16 | Not scored; nothing to extract. |
| `state`/`lga` omitted while `settlement` is known | 69 | Not scored. See flag 2. |
| Other | 4 | See flags 3 and below. |

The benchmark file was not modified.

## Flags (genuinely ambiguous)

1. **Unresolved-by-intent fields would let a guess pass.** In CLAR-06, CLAR-07, CLAR-08, CLAR-09, CLAR-10, CLAR-11, CLAR-13, ESC-24, ESC-25 and MESSY-17, the omitted field is one the model must not guess, yet "not scored" would ignore a guess. *Proposed:* treat any field covered by `missing_important_fields` as an implicit `null` (age→age; location→settlement, lga, state; unambiguous_location→state, lga; specific_location→settlement; case_identity→settlement, lga, state). Needs your approval because it extends your rule.
2. **Wrong inference would go unchecked.** For the 69 omitted `state`/`lga` cases, a model that infers a wrong LGA/state is never penalized. *Proposed:* when the fixture resolves the settlement, a non-null model value must equal the fixture value; a mismatch is a fabrication. The fixture must therefore be complete (Majawa, Dange, Bodinga, Tureta, Wamakko, Wurno, Sokoto town, Gwadabawa, Tambuwal, Gidan Waya, Kafur, Kura). I will not fill it in from memory; the values need your confirmation.
3. **"Near X" is treated inconsistently.** CLAR-13 gives `lga = Kafin Hausa` for "a village near Kafin Hausa", but ESC-25 leaves `lga`/`state` unscored for "somewhere near Majawa" while listing `specific_location` as missing. *Question:* may the model infer Kafin Hausa/Jigawa from "near Majawa" in ESC-25, or must it stay unresolved? *Proposed:* explicit `null` for lga/state in ESC-25 turns 1 and 2.
4. **Kura is both ambiguous and unique.** CLAR-09 and CLAR-11 require Kura to be ambiguous until the sender gives Kano/Kura LGA, but the CLAR-08 note says Kura should be uniquely resolvable. The fixture needs a scenario-scoped setting (CLAR-08: unique; CLAR-09, CLAR-11: ambiguous).

## Minor, not flagged

- CLAR-11 turn 1 omits `settlement` while CLAR-09 turn 1 lists `settlement = Kura` for the same input; harmless under "not scored".
- VPD-21 and VPD-22 omit `sex` although the message says "a man" / "a woman"; not scored under the rule.
- Approximate ages appear as strings ("about 9", "about 10-11", "about 14"). The scorer needs an explicit normalizer (a number inside the stated range matches).

---

## Resolution in benchmark v0.3.1 (2026-10-05)

New file `data/sms_ai_benchmark_v0_3_1.jsonl`; the original v0.3 file is unchanged. Each row carries `benchmark_version`.

1. **Implicit nulls materialized.** 32 gold fields are now explicit `null` (CLAR-06 3, CLAR-07 1, CLAR-08 1, CLAR-09 2, CLAR-10 2, CLAR-11 2, CLAR-13 2, MESSY-17 1, ESC-24 12, ESC-25 6). The scorer has no implicit-null logic.
2. **Fixture check.** `data/location_fixture_v0_1.json` covers every settlement named in the gold. The 69 omitted `state`/`lga` fields stay unscored but a non-null model value must equal the fixture value (see scorer contract, "Gold field semantics").
3. **ESC-25.** `state`, `lga` and `settlement` are explicit `null` on both turns.
4. **Kura.** CLAR-08 now uses Majawa (user text, gold settlement, notes). Kura is ambiguous in every scenario that uses it (CLAR-09, CLAR-11).
5. **CLAR-11.** `must_apply_user_correction` and `must_not_retain_superseded_value` moved from turn 2 to turn 3, where the sex correction arrives. Turn 2 now checks `must_resolve_location_from_followup`.

### Re-audit

| Cause | Count | Status |
|---|---:|---|
| Non-AFP or terminal turn | 16 | Not scored. |
| `state`/`lga` omitted, settlement in fixture | 69 | Fixture-checked. |
| Other omissions | 2 | CLAR-13 turn 1 `state` (resolved by the fixture's `lga_level` entry for Kafin Hausa); CLAR-11 turn 1 `settlement` (not scored). |
| Intended-unresolved fields still omitted | 0 | |

### Open items

- The fixture is `DRAFT_PENDING_SME_SIGNOFF`. Sokoto LGA names were checked against a public LGA list; the settlement-to-LGA mappings are benchmark-defined. Majawa, Gidan Waya and Kura come from the spec and gold annotations.
- Kura's other candidate places are not named. The fixture declares the ambiguity and requires both state and LGA.
