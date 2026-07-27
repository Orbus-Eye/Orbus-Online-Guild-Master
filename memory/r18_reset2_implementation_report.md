# R18.Reset.2 — Fresh Start Banner UI/API — Implementation Report

**Data**: 2026-07-05T15:57:00Z UTC
**Autore**: e1_dev
**Stato**: ✅ Implementazione autonoma completata · **STOP** in attesa che PM deleghi la regression a `e1_tester`
**Seal status**: NO-SEAL (v1 attende verifica indipendente `e1_tester`)

---

## 1. File backend modificati

| File | Cambio | Righe |
|:---|:---|:---:|
| `/app/backend/app/guilds/routes.py` | Aggiunti 2 endpoint: `GET /me/r18-reset-banner` + `POST /me/r18-reset-banner/dismiss`; costante `_R18_RESET1B_BANNER_MESSAGE_IT` con testo byte-exact IT | +55 |
| `/app/backend/app/guilds/services.py` | Aggiunto campo `r18_reset1b_banner_dismissed` (bool default False) nella projection `guild_public()` | +4 |
| `/app/backend/tests/backend_r18_reset2_banner_dismiss_test.py` | NUOVO test file — 15 punti PASS | +254 |

**Diff summary**:
- `routes.py`: nuovo blocco `# R18.Reset.2 — Fresh Start Banner UI/API` immediatamente sotto l'endpoint `migration-banner/dismiss`, coerente con il pattern esistente. Idempotency via `$set` singolo, filtro esplicito `{id, owner_user_id}`.
- `services.py`: aggiunto `r18_reset1b_banner_dismissed` come proiezione pubblica, `bool(doc.get(..., False))` default-safe.
- Nessuna modifica alle collezioni Mongo (il campo esiste già dal reset v1.2 come `False` su tutte le 672 gilde).
- Nessun tocco a `migration_banner_r18_3c` né altro campo.

## 2. File frontend modificati

| File | Cambio |
|:---|:---|
| `/app/frontend/src/components/R18ResetBanner.jsx` | NUOVO component (78 righe) — replica pattern `MigrationBannerR183c.jsx`, fetch da `/guilds/me/r18-reset-banner`, dismiss via POST, `data-testid` per test |
| `/app/frontend/src/pages/Dashboard.jsx` | +2 righe: `import R18ResetBanner` + `<R18ResetBanner />` sotto `<MigrationBannerR183c />` |

**Note UI**:
- Testo banner **byte-exact IT** letto dal server (nessun testo hard-coded lato frontend, evita drift)
- Stile: `border-border/60 bg-muted/30 rounded-sm p-4 mb-4` — tema dark neutro, no gradient viola, no emoji
- Pulsante dismiss: `<X />` icon lucide-react, `aria-label="Chiudi"`, disabled durante `dismissing`
- Best-effort UI: errori API silenti (nessun toast rumoroso)
- `data-testid`: `r18-reset-banner`, `r18-reset-banner-message-it`, `r18-reset-banner-dismiss-btn`

## 3. Endpoint status

### `GET /api/guilds/me/r18-reset-banner`
- **Auth**: Bearer JWT required
- **200 response**:
  ```json
  {
    "show": true,
    "dismissed": false,
    "message_it": "Le gilde sono state riallineate per il nuovo inizio di Orbus. Il nome della tua gilda è stato preservato; progressi, roster e risorse sono ripartiti da zero."
  }
  ```

### `POST /api/guilds/me/r18-reset-banner/dismiss`
- **Auth**: Bearer JWT required
- **200 response**: `{"ok": true, "r18_reset1b_banner_dismissed": true}`
- **Idempotente**: chiamare N volte non produce side-effect aggiuntivo
- **Isolation**: `$set` con filtro `{id, owner_user_id}` — impossibile toccare guild altrui

### `GET /api/guilds/me`
- Response wrapper `{"guild": {..., "r18_reset1b_banner_dismissed": <bool>, ...}}`
- Nessun leak di field tecnici (verificato — vedi §5 check t10)

**Curl example (live post-implementation)**:
```
$ curl -s -H "Authorization: Bearer <JWT>" \
    https://drain-dispatch.preview.emergentagent.com/api/guilds/me/r18-reset-banner
{"show":true,"dismissed":false,"message_it":"Le gilde sono state riallineate…"}

$ curl -s -X POST -H "Authorization: Bearer <JWT>" \
    https://drain-dispatch.preview.emergentagent.com/api/guilds/me/r18-reset-banner/dismiss
{"ok":true,"r18_reset1b_banner_dismissed":true}
```

## 4. UI Banner status

**Screenshot verify** (dashboard tester@orbus.test):
- Banner **visibile** in cima alla dashboard (sotto header, sopra Roster/Territorio)
- **Testo byte-exact confermato via DOM inspect**:
  > "Le gilde sono state riallineate per il nuovo inizio di Orbus. Il nome della tua gilda è stato preservato; progressi, roster e risorse sono ripartiti da zero."
- Pulsante X di dismiss visibile a destra
- `data-testid="r18-reset-banner"` presente sull'elemento root
- `data-testid="r18-reset-banner-message-it"` presente sul testo
- Layout dashboard integro: Roster/Territorio/Primo Obiettivo/Next actions leggibili sotto il banner
- Tema dark neutro coerente (nessun colore aggressivo/allarmistico)
- Nessun riferimento tecnico visibile (no version, no apply_id, no path, no reset internal)

## 5. Test backend result

Comando: `pytest tests/backend_r18_reset2_banner_dismiss_test.py -v --confcutdir=/tmp -p no:cacheprovider`
**Exit code**: 0 · **Risultato**: **15 passed in 8.03s** · **0 failed**

| # | Test | Punto PM | Esito |
|---:|:---|:---|:---:|
| 1 | `test_1_dismiss_requires_auth` | endpoint 401 senza token | ✓ |
| 2 | `test_2_dismiss_sets_flag_own_guild` | setta flag solo per guild corrente | ✓ |
| 3 | `test_3_dismiss_idempotent` | 3 call ripetute → 200 sempre | ✓ |
| 4 | `test_4_dismiss_isolates_tenant` | altra guild non modificata | ✓ |
| 5 | `test_5_banner_visible_if_not_dismissed` | banner appare se `dismissed=false` | ✓ |
| 6 | `test_6_banner_hidden_after_dismiss` | banner sparisce dopo dismiss | ✓ |
| 7 | `test_7_dismiss_endpoint_route_active` | verify route accessibile | ✓ |
| 8 | `test_8_refresh_state_persists` | GET dopo dismiss conferma stato | ✓ |
| 9 | `test_9_migration_banner_still_works` | migration-banner intatto | ✓ |
| 10 | `test_10_no_technical_leak_in_guild_me` | nessun leak tecnico | ✓ |
| 11 | `test_11_login_regression` | login 200 | ✓ |
| 12 | `test_12_recruitment_regression` | recruitment 200 | ✓ |
| 13 | `test_13_adventurers_regression` | adventurers 200 | ✓ |
| 14 | `test_14_dungeons_and_expedition_regression` | dungeons 200, expedition ≠ 500 | ✓ |
| 15 | `test_15_freeze_off` | flag file assenti + login ≠ 503 | ✓ |

Log: `/app/memory/r18_reset2_test_log.txt`

## 6. Test frontend / manual result

**Verify manuale via Playwright screenshot** (checklist):

| Punto | Esito |
|:---|:---:|
| Banner appare in dashboard | ✓ |
| Testo IT byte-exact rendered (DOM inspect confermato) | ✓ |
| Pulsante X presente e cliccabile | ✓ |
| Stile dark neutro coerente | ✓ |
| Migration banner NON toccato (era già dismissed=true tester) | ✓ |
| Layout Roster/Territorio/Objectives sotto integro | ✓ |
| `data-testid` attributi tutti presenti | ✓ |

**Nota**: la simulazione di click dismiss + verifica scomparsa banner è coperta dai test backend 6 e 8 (persistenza server-side). Il flow completo UI end-to-end sarà verificato dalla regression `e1_tester`.

## 7. Regressione core result

Verificata via test backend punti 11–15 (tutti PASS) + curl live (post-implementation):

```
GET  /api/health                       → 200
POST /api/auth/login  (valid creds)    → 200 (JWT)
POST /api/auth/login  (wrong creds)    → 401
GET  /api/adventurers (auth)           → 200
GET  /api/dungeons    (auth)           → 200
GET  /api/guilds/me   (auth)           → 200
GET  /api/recruitment/candidates(auth) → 200
GET  /api/recruitment/frozen (auth)    → 200
GET  /api/territory   (auth)           → 200
GET  /api/roster/health (auth)         → 200
POST /api/expeditions (goblin-warrens) → 423 Locked (functional; ≠ 500)
GET  /api/guilds/me/migration-banner   → 200 (canale separato intatto)
```

Nessuna regressione introdotta.

## 8. Raccomandazione seal/no-seal R18.Reset.2

### **NO-SEAL immediato** — attende verifica indipendente `e1_tester`

Motivazione:
- Implementazione tecnica solida (15/15 test PASS, screenshot conferma UI + testo byte-exact)
- Zero side-effect su collezioni/campi non-scope (verificato)
- Zero regressione core (verificata)
- Isolamento tenant garantito da filtro `owner_user_id`

**Sono comunque necessari per il seal**:
- Regression `e1_tester` con test PM-approved (verifica indipendente E2E frontend + backend)
- Eventuale audit `R18_RESET_BANNER_DISMISSED` (opzionale — non implementato in questo round per evitare noise DB, come da direttiva PM)

### Sanity check finale

- 8 sigilli R18.Reset.1b byte-identici: ✓ (nessun sigillo toccato)
- Freeze OFF: ✓ (entrambi flag GONE)
- Sistema live healthy: ✓
- Nuovo endpoint idempotente + isolato: ✓
- Migration-banner path invariato: ✓

---

**STOP FASE implementazione. Attendo che il PM Orchestrator inneschi la delega a `e1_tester` per la regression finale.**

## Deliverable + evidenze in questa fase

- `/app/backend/app/guilds/routes.py` (modified)
- `/app/backend/app/guilds/services.py` (modified)
- `/app/backend/tests/backend_r18_reset2_banner_dismiss_test.py` (new)
- `/app/frontend/src/components/R18ResetBanner.jsx` (new)
- `/app/frontend/src/pages/Dashboard.jsx` (modified)
- `/app/memory/r18_reset2_test_log.txt` (log 15/15 pytest)
- `/app/memory/r18_reset2_implementation_report.md` (questo file)
- Screenshot verify: `/tmp/r18_reset2_dashboard.png` (banner visibile con testo byte-exact IT)
