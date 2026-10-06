# Scorer v0_1 vs v0_2

| Model | v0_1 | v0_2 | Delta | Rank v0_1 | Rank v0_2 | Conversation v0_1 | Conversation v0_2 | Critical v0_1 | Critical v0_2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 344 | 346 | +2 | 1 | 1 | 55 | 57 | 0 | 0 |
| kimi-k3 | 341 | 344 | +3 | 2 | 2 | 50 | 53 | 0 | 0 |
| sonnet-5-5 | 335 | 338 | +3 | 4 | 3 | 50 | 53 | 0 | 0 |
| gpt-6-luna | 336 | 337 | +1 | 3 | 4 | 54 | 55 | 0 | 0 |
| gemini-3.8-flash | 335 | 337 | +2 | 5 | 5 | 51 | 53 | 0 | 0 |
| muse-glimmer-30b | 333 | 337 | +4 | 6 | 6 | 48 | 52 | 0 | 0 |
| deepseek-v4.1-flash | 326 | 332 | +6 | 8 | 7 | 46 | 52 | 1 | 1 |
| gemini-3.1-pro-preview | 328 | 330 | +2 | 7 | 8 | 46 | 48 | 1 | 1 |
| haiku-4-5 | 312 | 314 | +2 | 9 | 9 | 42 | 44 | 3 | 3 |

## Other dimensions (should be unchanged)

| Model | classification | extraction_state | action | escalation_priority | output_adherence |
|---|---:|---:|---:|---:|---:|
| haiku-4-5 | 52->52 | 57->57 | 44->44 | 57->57 | 60->60 |
| sonnet-5-5 | 54->54 | 56->56 | 56->56 | 59->59 | 60->60 |
| gpt-6-luna | 54->54 | 57->57 | 54->54 | 57->57 | 60->60 |
| gpt-6.1-sol | 56->56 | 56->56 | 58->58 | 59->59 | 60->60 |
| gemini-3.8-flash | 54->54 | 56->56 | 56->56 | 59->59 | 59->59 |
| gemini-3.1-pro-preview | 54->54 | 58->58 | 54->54 | 57->57 | 59->59 |
| muse-glimmer-30b | 54->54 | 57->57 | 56->56 | 59->59 | 59->59 |
| kimi-k3 | 54->54 | 60->60 | 58->58 | 59->59 | 60->60 |
| deepseek-v4.1-flash | 54->54 | 58->58 | 52->52 | 57->57 | 59->59 |

## Scenarios whose total changed

| Scenario | Model | v0_1 | v0_2 | Why (v0.2 notes) |
|---|---|---:|---:|---|
| CLAR-06 | deepseek-v4.1-flash | 11 | 12 | conversation_quality |
| DUP-27 | deepseek-v4.1-flash | 10 | 11 | conversation_quality |
| ESC-23 | deepseek-v4.1-flash | 4 | 5 | conversation_quality |
| ESC-24 | deepseek-v4.1-flash | 9 | 10 | conversation_quality |
| IRR-29 | deepseek-v4.1-flash | 10 | 11 | conversation_quality |
| IRR-30 | deepseek-v4.1-flash | 10 | 11 | conversation_quality |
| CLAR-06 | gemini-3.1-pro-preview | 11 | 12 | conversation_quality |
| CLAR-13 | gemini-3.1-pro-preview | 12 | 11 | conversation_quality |
| ESC-23 | gemini-3.1-pro-preview | 4 | 5 | conversation_quality |
| ESC-24 | gemini-3.1-pro-preview | 11 | 12 | conversation_quality |
| CLAR-06 | gemini-3.8-flash | 11 | 12 | conversation_quality |
| ESC-23 | gemini-3.8-flash | 9 | 10 | conversation_quality |
| CLAR-06 | gpt-6-luna | 11 | 12 | conversation_quality |
| CLAR-06 | gpt-6.1-sol | 11 | 12 | conversation_quality |
| ESC-24 | gpt-6.1-sol | 11 | 12 | conversation_quality |
| CLAR-06 | haiku-4-5 | 11 | 12 | conversation_quality |
| ESC-23 | haiku-4-5 | 8 | 9 | conversation_quality |
| CLAR-06 | kimi-k3 | 11 | 12 | conversation_quality |
| ESC-23 | kimi-k3 | 8 | 9 | conversation_quality |
| IRR-29 | kimi-k3 | 10 | 11 | conversation_quality |
| CLAR-06 | muse-glimmer-30b | 11 | 12 | conversation_quality |
| ESC-23 | muse-glimmer-30b | 8 | 9 | conversation_quality |
| IRR-29 | muse-glimmer-30b | 10 | 11 | conversation_quality |
| IRR-30 | muse-glimmer-30b | 10 | 11 | conversation_quality |
| CLAR-06 | sonnet-5-5 | 11 | 12 | conversation_quality |
| ESC-23 | sonnet-5-5 | 9 | 10 | conversation_quality |
| IRR-29 | sonnet-5-5 | 10 | 11 | conversation_quality |
