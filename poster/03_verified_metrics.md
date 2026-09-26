# Verified Metrics — Poster 10

MIT • Python 3.12 • HEAD 89a038a • verified 2026-09-26. Verified for this poster on Windows / CPython 3.12.10.

## Headline cards
- 8 — REPOS AGGREGATED
- 27 — TEST FUNCTIONS
Notes: 8 active ML security repos' evidence aggregated. 27 test_ functions (HEAD 89a038a).

## Verified surface
| Item | Value |
|---|---|
| Dashboard framework | FastAPI |
| Auth on API | token |
| Design system | shared |

## Chart values
| Series | Value |
|---|---|
| Grouped F1 (redteam) | 97 |
| OOD F1 (redteam) | 72 |
| Weak ROC-AUC (poison) | 54 |
Note: Dashboards display weak results (OOD 0.72, ROC-AUC 0.54) next to strong ones — by design.

## Historical / provenance
Every displayed number is read from a committed evidence/*.json in a sibling repo — not hand-entered. Weak results are shown, not hidden.

## Not established by this repository
Live SOC monitoring. Real-time telemetry or alerting. That static snapshots equal current CI state.
