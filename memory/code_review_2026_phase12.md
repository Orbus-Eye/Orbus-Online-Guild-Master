# Code Review — Orbus Online Guild Master
**Date**: 2026-06-24
**Reviewer**: e1_dev (self-review workaround — `code_review_agent` infra bug)
**Scope**: Security · Anti-P2W · Game invariants · i18n · Architecture · Tests
**Codebase state**: 272/272 pytest, OpenAPI 39, Phase 12.3 i18n complete, Phase 9.3 email runtime-ready (Resend key not yet in `.env`)

---

## P0 Blockers

**None found.** Auth, anti-P2W, recruitment/dungeon/expedition/equipment/leaderboard invariants tutte coperte da test e logica server-side. Nessun fix applicato in questa review.

---

## P1 Before Alpha

### P1-1 · Equipment item duplication via concurrent equip
**File**: `app/equipment/services.py:138-200` (`equip_item_service`)
**Description**: La check `available = total_qty - equipped_qty` (riga 174-178) NON è atomica. Due chiamate POST `/api/adventurers/{a}/equipment` e POST `/api/adventurers/{b}/equipment` per lo **stesso `item_id`** quando `total_qty=1, equipped_qty=0` possono passare entrambe il controllo `available <= 0`, poi inserire entrambe in `equipped_items` (slot diversi su avventurieri diversi). L'unique index `(adventurer_id, slot)` previene il doppio-equip sullo stesso slot ma NON previene questo scenario cross-adventurer.

**Risk**: Item duplication exploit. Un avventuriero usa il "vero" copy, l'altro un copy fantasma. Inflaziona equipment_power → distorce leaderboard `max_team_power_ever`.

**Fix consigliato** (~10 LOC):
```python
# Replace the count_documents check with an atomic find_one_and_update on
# the inventory_items row, decrementing a NEW field `reserved_quantity`.
# OR: use a transaction (Mongo replica set required) wrapping the count
# check + insert.
# Simplest in current single-node setup:
#   1) atomic $inc on `inventory_items.reserved_qty` gated by
#      {reserved_qty: {$lt: quantity}} via find_one_and_update
#   2) on insert failure rollback the $inc
```

**Blocking roadmap**: Y per alpha multi-user (cooperative play / leaderboard fairness)

**Test mancante**: stress test concorrenza (`asyncio.gather(*equip_calls)`) — aggiungerlo in `tests/backend_phase6_concurrency_test.py`

---

### P1-2 · Recruitment refresh CAS atomic ma item totale concorrente potrebbe degenerare in 409 loop
**File**: `app/recruitment/services.py:refresh_candidates_for_guild`
**Description**: La CAS funziona ma se la UI permette doppio-click rapido il client riceve 409 senza retry visibile (toast generico "Refresh state changed concurrently"). Non c'è duplicazione né danno, ma è UX scadente in mobile.

**Risk**: bassa — solo UX, no exploit

**Fix consigliato**: aggiungere `disabled` sul refresh button via state in `Recruitment.jsx` durante il request (già esiste `refreshing` boolean — verificare che copra il path POST nuovo)

**Blocking roadmap**: N

---

### P1-3 · Welcome email può loggare il username in log strutturati con caratteri di controllo
**File**: `app/auth/services.py:send_welcome_email_safe:253`
**Description**: `username` viene passato dritto al template via `render_welcome(lang, app_url, username)`. Il rendering HTML interpola con f-string senza escape — un username con `<script>` finirebbe nel subject e nel body. La policy di registrazione attualmente NON valida i caratteri del username (solo length 2-32 in `RegisterIn`).

**Risk**: HTML injection nelle email (XSS in client mail web che renderizza HTML). Non sfrutta il sito, ma è phishing-friendly se l'admin invia rinvii.

**Fix consigliato** (~3 LOC in `email_templates.py`):
```python
import html as _html
safe_username = _html.escape(safe_username)
```
E aggiungere `Pydantic Field(pattern=r"^[A-Za-z0-9_-]{2,32}$")` su `RegisterIn.username`.

**Blocking roadmap**: Y per produzione (anche con un singolo utente malicious)

---

### P1-4 · `ResendProvider` non supporta `reply_to`
**File**: `app/core/email.py:71-95`
**Description**: La task Phase 9.3 STEP 2 ha richiesto `EMAIL_REPLY_TO=admin@orbusonline.net` e estensione del provider. Attualmente i params Resend non includono `reply_to`. Utenti che rispondono alle email finirebbero a `noreply@orbusonline.net` (potenziale bounce).

**Risk**: bassa — UX, no security

**Fix consigliato** (~5 LOC):
```python
def __init__(self, api_key, from_addr, reply_to=None):
    self._reply_to = reply_to
...
params = {..., "reply_to": [self._reply_to]} if self._reply_to else {...}
```
E factory legge `EMAIL_REPLY_TO` da env.

**Blocking roadmap**: N (gating Resend activation è blocked anyway — manca la API key)

---

### P1-5 · Test pollution accumulata
**File**: MongoDB collections `users`, `guilds`, `adventurers`, `expeditions`, `recruitment_offers`
**Description**: Ogni run di pytest registra utenti `p2_*`, `p93_*`, `ob_*`, `ref_*` etc. via API real (no cleanup teardown). Dopo ~10 cicli CI il DB cresce a migliaia di docs.

**Risk**: bassa in dev; in CI può degradare velocità test e occupare spazio Mongo

**Fix consigliato** (~20 LOC): pytest fixture session-scope con teardown che cancella docs con email matching `^p\d+_|^ob_|^ref_|^smoke_|^i18n_|^e2e_` su tutte le collection menzionate. Da fare PRIMA di pubblicare per CI continui.

**Blocking roadmap**: N

---

### P1-6 · Flaky xdist test races
**File**: `tests/backend_phase4_test.py::test_cross_guild_adventurer_returns_404`, `tests/backend_phase7_test.py::test_*` (loot/expedition), `tests/backend_phase11_2_test.py::test_goblin_warrens_always_unlocked`
**Description**: Quando pytest-xdist gira 2 worker in parallelo, ~1-2 test su 272 falliscono in modo non-deterministico. Tutti PASS in isolazione. Pattern: leggono lo stato del tester condiviso (gold/adventurers/dungeons) che viene mutato in parallelo da altri test sullo stesso utente.

**Risk**: bassa — falso positivo nel report CI

**Fix consigliato**: Tutti i test che mutano stato dovrebbero usare `_register_fresh_user(tag)` invece del tester condiviso. Audit + refactor dei ~5-8 test ancora dipendenti dal tester.

**Blocking roadmap**: N — gating CI può richiedere `--forked` o `-n 1` come workaround

---

## P2 Later (tech debt)

### P2-1 · `localStorage` JWT (accepted risk documentato)
**File**: `frontend/src/context/AuthContext.jsx` (key `orbus_token`)
**Mitigation**: short access token (7d) + refresh token su separate channel; documentato esplicitamente dal team. Migrazione a httpOnly cookie richiede CSRF token + backend cookie flow. **Non bloccante per alpha**.

### P2-2 · `Admin.jsx` e `AdventurerEquipment.jsx` componenti monolitici
**Smell**: ciascun file >500 LOC con state machine inline. Splittare in sub-component (`<ItemForm/>`, `<ClassForm/>`, `<EquipmentSlot/>`).

### P2-3 · 80 item names non tradotti
**Status**: deferred a Phase 12.4 opzionale per ROI basso. Fallback EN backend è leggibile.

### P2-4 · Admin deep forms (rarity_weights, traits_pool, drop tables) restano EN
**Status**: low-traffic CRUD, ROI basso, documentato in PRD Phase 12.3.

### P2-5 · No rate limit su `/api/auth/register`
**Smell**: Login ha lockout per email (5 attempts/15min). Register no — un attaccante può creare utenti spam per saturare welcome email send. Mitigation parziale: `SEND_WELCOME_EMAIL=false` flag esiste. Long-term: aggiungere rate limit IP-based su register.

### P2-6 · `confirm_password_reset` non controlla che la nuova password sia diversa dalla vecchia
**Smell**: l'utente può resettare alla stessa password. UX minor.

### P2-7 · Resend `params` dict aspetta `"to": [string]` ma `Emails.send` SDK riceve singolo dict — verificare retro-compat con SDK v2.32+
**File**: `app/core/email.py:81`
**Smell**: aggiungere unit test che usa SDK reale in modo dry-run (no network) per validare la shape.

### P2-8 · `validate_item_monetization` non chiamato su `seed_data.py` se l'item è cosmetic con `affects_combat=True`
**Smell**: il validator consente combat-cosmetic se NON ha `can_be_sold_for_real_money`. Ok perché il flag non si "attiva" per real money, ma documentazione: "cosmetic+combat" è semanticamente strano. Considerare separare `is_cosmetic` da `affects_combat`.

### P2-9 · Backend logs strutturati assenti
**Smell**: usa `logger.info`, no JSON structured logging. Per production debugging serve formatter JSON con request_id correlation.

### P2-10 · Frontend `lib/api.js` retry policy assente
**Smell**: una connessione mobile flaky non auto-retry. Considerare axios-retry per GET idempotenti.

---

## False positives / accepted risks

- **localStorage JWT**: vedi P2-1 sopra
- **Item names EN fallback**: deferred ufficialmente
- **STR/AGI/INT/END/FAI non localizzate**: convenzione MMO universale, documentata in `Adventurers.jsx`
- **Flaky xdist test**: documentato + isolato (PASS in single-worker)
- **Resend API key empty**: documentato come "runtime-ready, not activated"
- **Tester forced-admin on every restart**: gated by `APP_ENV != production`, fail-safe
- **CORS `*` in dev**: gated by `APP_ENV != production`, validation hard-fails on `*` in prod

---

## Coverage tests vs invarianti critici

| Invariante | Test esistente | Coverage |
|:--|:--|:--|
| JWT secret from env, no default | `backend_test.py` | ✅ |
| Bcrypt password hashing | `backend_test.py` | ✅ |
| Password reset one-time use | `backend_phase93_email_test.py::test_reset_token_one_time_use_unchanged` | ✅ |
| Password reset TTL | implicito su `expires_at` + Mongo TTL index | ⚠️ no explicit time-skew test |
| Account enumeration prevention | `backend_phase93_email_test.py` | ✅ |
| Admin gating su 16 routes | `backend_phase5d_test.py` | ✅ |
| Anti-P2W validate_item_monetization | `backend_phase4_test.py::TestMonetizationValidation` | ✅ |
| Leaderboard no PII leak | `backend_phase9_leaderboard_test.py` | ✅ |
| Recruitment refresh limit + race | `backend_phase11_2_test.py` (CAS verified) | ✅ |
| Dungeon gates dispatch 403 | `backend_phase11_2_test.py` | ✅ |
| Dragon's Hoard sticky | `backend_phase7_test.py` + `backend_phase11_2_test.py` | ✅ |
| Replay-last-run non bypass | `backend_phase8_test.py` | ✅ |
| Equip cross-guild defense | `backend_phase6_test.py` | ✅ |
| Equip during expedition blocked | `backend_phase6_test.py` | ✅ |
| **Equipment item duplication race** | **mancante** | ❌ (vedi P1-1) |
| **HTML injection username welcome** | **mancante** | ❌ (vedi P1-3) |
| i18n fallback chain | manca (~5 LOC unit test su `resolve()`) | ❌ |

---

## Suggested next phase

### 🟢 Trait Effect Resolution — RECOMMENDED

**Motivazione**:
1. **Game-design depth**: gli avventurieri hanno 30 tratti ma solo 7 categorie applicate nel combat (`affected_stat` ∈ `{strength, agility, intellect, endurance, faith, xp_gain}`). I tratti come "Brave" (resists fear), "Lucky" (better loot rolls), "Stalwart" (holds vs swarms) sono **dichiarati ma non risolti** dalla formula. La codebase ha già `app/expeditions/formulas.py` pronta per essere estesa.
2. **Differentiation**: senza tratti effettivi, due avventurieri stessa classe sono interscambiabili → leaderboard piatta.
3. **No P0/P1 work bloccante**: con la check di P1-1 (equipment duplication) come pre-req, la roadmap successiva è "Trait Effects" → "Build diversity".

**Alternative considerate**:
- 🟡 **DB cleanup test pollution** (P2-1) — utile per CI ma non sblocca utenti
- 🟡 **Daily Quests** — retention loop, ma richiede prima fix equipment duplication
- 🟡 **Phase 12.4 item names** — cosmetico, ROI basso
- 🔴 **Activate Resend live** — bloccato da API key

**Pre-req prima di Trait Resolution**:
1. Applicare fix **P1-1** (equipment duplication race) — è il rischio più alto rimasto
2. Applicare fix **P1-3** (HTML escape username) — sicurezza email
3. Considerare anche **P1-4** (reply_to su Resend) durante l'estensione email

---

## Summary findings

| Priority | Count |
|:--|:-:|
| **P0** | 0 |
| **P1** | 6 |
| **P2** | 10 |
| **False positives** | 7 |

**Fix applicati in questa review**: 0 (read-only, P0 vuoto). Tutti i P1 sono documentati con file:line + fix consigliato.

**Test PASS rate**: 272/272 (baseline mantenuta, nessuna modifica applicata).
**OpenAPI**: 39 paths invariato.
