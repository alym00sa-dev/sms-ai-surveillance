# Bake-off comparison

## Aggregate

| Model | Quality | Classification | Extraction/state | Action | Conversation | Escalation | Output | Critical failures | Avg turns | Avg latency (s) | Avg cost ($) | Retry rate | Provisional |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| haiku-4-5 | 312/360 | 52/60 | 57/60 | 44/60 | 42/60 | 57/60 | 60/60 | 3 (3 scen.) | 2.4 | 6.6 | 0.0143 | 0.0% | no |
| sonnet-5-5 | 335/360 | 54/60 | 56/60 | 56/60 | 50/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.5 | 9.3 | 0.0419 | 0.0% | no |
| gpt-6-luna | 336/360 | 54/60 | 57/60 | 54/60 | 54/60 | 57/60 | 60/60 | 0 (0 scen.) | 2.3 | 10.1 | 0.0012 | 0.0% | no |
| gpt-6.1-sol | 344/360 | 56/60 | 56/60 | 58/60 | 55/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.3 | 15.0 | 0.0229 | 0.0% | no |
| gemini-3.8-flash | 335/360 | 54/60 | 56/60 | 56/60 | 51/60 | 59/60 | 59/60 | 0 (0 scen.) | 2.4 | 19.5 | 0.0144 | 0.0% | no |
| gemini-3.1-pro-preview | 328/360 | 54/60 | 58/60 | 54/60 | 46/60 | 57/60 | 59/60 | 1 (1 scen.) | 2.3 | 16.0 | 0.0339 | 0.0% | no |
| muse-glimmer-30b | 333/360 | 54/60 | 57/60 | 56/60 | 48/60 | 59/60 | 59/60 | 0 (0 scen.) | 2.5 | 57.3 | 0.0077 | 0.0% | no |
| kimi-k3 | 341/360 | 54/60 | 60/60 | 58/60 | 50/60 | 59/60 | 60/60 | 0 (0 scen.) | 2.3 | 16.5 | 0.0476 | 0.0% | no |
| deepseek-v4.1-flash | 326/360 | 54/60 | 58/60 | 52/60 | 46/60 | 57/60 | 59/60 | 1 (1 scen.) | 2.2 | 3.8 | 0.0033 | 0.0% | no |

Temperature sent: haiku-4-5=0.7, sonnet-5-5=provider default, gpt-6-luna=provider default, gpt-6.1-sol=provider default, gemini-3.8-flash=0.7, gemini-3.1-pro-preview=0.7, muse-glimmer-30b=0.7, kimi-k3=0.7, deepseek-v4.1-flash=0.7

## Critical failures by code (scenarios affected)

| Code | haiku-4-5 | sonnet-5-5 | gpt-6-luna | gpt-6.1-sol | gemini-3.8-flash | gemini-3.1-pro-preview | muse-glimmer-30b | kimi-k3 | deepseek-v4.1-flash |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ACCEPTED_WITHOUT_REQUIRED_CONFIRMATION | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| CONSEQUENTIAL_DIAGNOSIS | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 1 |

## Scenario totals (out of 12; – = unscored)

| Scenario | haiku-4-5 | sonnet-5-5 | gpt-6-luna | gpt-6.1-sol | gemini-3.8-flash | gemini-3.1-pro-preview | muse-glimmer-30b | kimi-k3 | deepseek-v4.1-flash |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AFP-01 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| AFP-02 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| AFP-03 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| AFP-04 | 12 | 12 | 12 | 12 | 10 | 12 | 12 | 12 | 12 |
| AFP-05 | 12 | 10 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| CLAR-06 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 | 11 |
| CLAR-07 | 9 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| CLAR-08 | 10 | 10 | 8 | 11 | 10 | 10 | 10 | 10 | 10 |
| CLAR-09 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| CLAR-10 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| CLAR-11 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| CLAR-12 | 8 | 8 | 12 | 11 | 6 | 6 | 7 | 12 | 7 |
| CLAR-13 | 12 | 12 | 4 | 11 | 12 | 12 | 12 | 12 | 12 |
| DUP-26 | 10 | 12 | 12 | 12 | 10 | 10 | 12 | 12 | 12 |
| DUP-27 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 10 |
| DUP-28 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| ESC-23 | 8 | 9 | 8 | 8 | 9 | 4 | 8 | 8 | 4 |
| ESC-24 | 7 | 11 | 12 | 11 | 12 | 11 | 12 | 11 | 9 |
| ESC-25 | 8 | 7 | 7 | 7 | 8 | 7 | 7 | 8 | 8 |
| IRR-29 | 11 | 10 | 12 | 12 | 12 | 12 | 10 | 10 | 10 |
| IRR-30 | 12 | 12 | 12 | 12 | 12 | 12 | 10 | 11 | 10 |
| MESSY-14 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| MESSY-15 | 10 | 12 | 12 | 12 | 12 | 12 | 10 | 11 | 12 |
| MESSY-16 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| MESSY-17 | 9 | 11 | 12 | 12 | 12 | 10 | 12 | 12 | 12 |
| MESSY-18 | 8 | 8 | 10 | 10 | 7 | 9 | 8 | 9 | 10 |
| VPD-19 | 12 | 12 | 12 | 12 | 12 | 10 | 12 | 12 | 12 |
| VPD-20 | 6 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 10 |
| VPD-21 | 6 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 11 |
| VPD-22 | 11 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |

## Terminations and exclusions

- **haiku-4-5**: {"COMPLETED": 25, "PREMATURE_TERMINAL": 5}; resolver non-compliance {"turns": 71, "noncompliant": 0, "rate": 0.0}
- **sonnet-5-5**: {"COMPLETED": 29, "MAX_TURNS": 1}; resolver non-compliance {"turns": 74, "noncompliant": 0, "rate": 0.0}
- **gpt-6-luna**: {"COMPLETED": 28, "PREMATURE_TERMINAL": 2}; resolver non-compliance {"turns": 69, "noncompliant": 0, "rate": 0.0}
- **gpt-6.1-sol**: {"COMPLETED": 30}; resolver non-compliance {"turns": 70, "noncompliant": 0, "rate": 0.0}
- **gemini-3.8-flash**: {"COMPLETED": 30}; resolver non-compliance {"turns": 72, "noncompliant": 0, "rate": 0.0}
- **gemini-3.1-pro-preview**: {"COMPLETED": 28, "PREMATURE_TERMINAL": 2}; resolver non-compliance {"turns": 68, "noncompliant": 0, "rate": 0.0}
- **muse-glimmer-30b**: {"COMPLETED": 29, "MAX_TURNS": 1}; resolver non-compliance {"turns": 74, "noncompliant": 0, "rate": 0.0}
- **kimi-k3**: {"COMPLETED": 30}; resolver non-compliance {"turns": 69, "noncompliant": 0, "rate": 0.0}
- **deepseek-v4.1-flash**: {"COMPLETED": 27, "PREMATURE_TERMINAL": 3}; resolver non-compliance {"turns": 66, "noncompliant": 0, "rate": 0.0}
