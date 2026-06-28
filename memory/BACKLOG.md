
## ADDENDUM TASK 6 — Guida Traits & Statistiche (esecuzione dopo FASE C, prima di TASK 7)

### Scope
G1 — Sezione "Traits degli Avventurieri" nella Guida (positivi/negativi/misti, esclude is_test+is_active=false, valori reali, NO slug raw).
G2 — Sezione "Statistiche degli Avventurieri" nella Guida (tutte le stats reali del modello, descrizione+effetto+UI+PWR; NO false spiegazioni).
G3 — Data-driven: NO hardcode JSX. Endpoint backend (`GET /api/traits/catalog`, `GET /api/stats/catalog`) o catalog Python (`app/traits/public_catalog.py`, `app/stats/public_catalog.py`). I18n IT/EN aggiornato. Nota in REFACTOR_LOG.md per la procedura di aggiornamento.
G4 — Test: 5 backend (test/inactive nascosti, polarità corretta, stats documentate, no leak slug raw) + 7 FE (sezioni visibili, leggibili, mobile responsive 375px, i18n IT/EN, no console errors).

### Vincoli
Solo traits realmente implementati nel codice (Brave, Quick Learner, Frail, Sharp Eye, Devout + eventuali). Traits ambigui → "Misto/Neutro" + nota report. Tutto in preview.

### Output a chiusura TASK 6
N. traits + N. stats documentate, conferma esclusioni test/inactive, conferma no slug raw, screenshot Guida (Traits + Stats), lista endpoint nuovi + OpenAPI count.
