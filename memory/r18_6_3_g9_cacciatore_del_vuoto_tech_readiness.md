# R18.6.3-G9 TECH_READINESS · Cacciatore del Vuoto · Specifica Tecnica Documentale

> ⚠️ **SPECIFICA TECNICA DOCUMENTALE — NON IMPLEMENTAZIONE**
> Questo documento contiene **proposal-only** per l'implementazione futura runtime della Sala, della Prova safe-mode, della conferma esplicita e dell'assegnazione classe. Ogni endpoint proposto è marcato `PROPOSAL ONLY · NOT IMPLEMENTED · NOT ROUTED · NOT IN OPENAPI`. Ogni field DB proposto è marcato `PROPOSAL ONLY · NO DB WRITE · NO MIGRATION`.
>
> Nessuna modifica a backend/frontend/OpenAPI/DB/test in questa fase. Discovery read-only autorizzata.

**Sala**: Faro Rovesciato di Onirade · **Hall Master**: Nael di Onirade · **Classe**: Cacciatore del Vuoto
**Stato Sala runtime**: **inactive** (planned) · **Stato Prova runtime**: **not implemented** · **Feature flag**: **disabled** · **Class assignment runtime**: **prohibited**

## 1 · Executive summary

Gate 9 definisce, in modalità **documentale e read-only**, la specifica tecnica per rendere IMPLEMENTABILI in futuro (Gate 10+):

1. la **Sala Faro Rovesciato di Onirade** in stato *ACTIVE*
2. la **Prova del Riflesso Vuoto** come sessione safe-mode
3. il flow di **conferma esplicita post-Prova**
4. l'**assegnazione classe iniziale** con `class_slug apply` sicuro, idempotente, auditabile
5. l'integrazione con proficiency · equip eligibility · XP/main-stat pipeline

Gate 9 **non applica nulla**: nessun endpoint reale · nessun record DB · nessun feature flag abilitato · nessun test scritto.

## 2 · Current runtime inventory

Componenti runtime **già esistenti** nel sistema (discovery read-only 2026-07-11):

- **Backend modulo `class_halls/`** (`/app/backend/app/class_halls/`):
  - `routes.py`: prefix `/api/class-halls` · 3 endpoint (`GET /`, `GET /{class_slug}`, `POST /{class_slug}/unlock-specialization`)
  - `services.py`: `seed_class_halls_for_guild`, `list_class_halls`, `enrich_halls_for_ui`, `get_class_hall`, `unlock_specialization`, `BASE_CLASS_SLUGS`
  - Collection MongoDB: `class_halls` · PK `{guild_id}::{class_slug}`
- **Backend modulo `onboarding/`**: `services.py` (funzioni onboarding esistenti)
- **Backend modulo `auth/`**: `routes.py` + `services.py` + `schemas.py`
- **Frontend page**: `/app/frontend/src/pages/ClassHalls.jsx`
- **Feature flags** (env-based esistenti): `R18_REWORK_ENABLED`, `R18_TALENT_ENGINE_ENABLED`
- **Sealed integrity test**: `backend/tests/backend_r18_4_sealed_integrity_test.py` (36 file byte-identical, read-only)

Componenti runtime **INESISTENTI** oggi:

- Endpoint `POST /class-halls/{hall_id}/visit` — NON esiste
- Endpoint `POST /class-halls/{hall_id}/trial/*` — NON esiste
- Endpoint `POST /class-halls/{hall_id}/class/confirm` — NON esiste
- Concetto DB `trial_status`, `trial_attempt_count`, `explicit_confirmation_at`, `class_assignment_status`, `class_assignment_source`, `class_assignment_history`, `class_readiness_version` — NON presenti nello schema attuale
- Concetto runtime "Trial safe-mode session" — NON implementato
- Concetto runtime "explicit_confirmation" — NON implementato

## 3 · Existing backend components

- `app/class_halls/routes.py` — 3 endpoint list/get/unlock-specialization
- `app/class_halls/services.py` — 7 funzioni servizio (seed, list, enrich, get, unlock, ecc.)
- `app/onboarding/services.py` — pipeline onboarding esistente
- `app/auth/*` — auth stack completo (JWT + user schema)
- `app/adventurers/*` — routes/services/generator per adventurers
- `app/core/database.py` — MongoDB async connection (`db`)
- `app/core/security.py` — `get_current_user` dependency
- `app/guilds/services.py` — `user_guild_or_404`
- `app/audit/log.py` — audit logging pipeline

Gate 9 **NON deve modificare** nessuno di questi file. Le proposal API sono orientate a **estendere** in futuro `class_halls/` con nuovi router sotto lo stesso prefix.

## 4 · Existing frontend components

- `frontend/src/pages/ClassHalls.jsx` — page esistente (rendering hall list)
- `frontend/src/components/navMenu.js` — nav esistente
- `frontend/src/App.js` — routing esistente

Nessun componente frontend per Trial safe-mode / explicit confirmation / class assignment iniziale è oggi presente. **Nessuna modifica frontend in Gate 9**.

## 5 · Existing DB fields

Discovery read-only sulle collection principali (senza query live · basata su modelli sorgente):

- Collection **`class_halls`**: PK `{guild_id}::{class_slug}` · campi principali (esistenti): identificativo hall, guild ref, class_slug ref, specialization unlock state, seed timestamp
- Collection **`users`** (o equivalente auth): identificativo utente, credenziali, ruoli
- Collection **`guilds`**: identificativo gilda, membri
- Collection **`adventurers`**: identificativo adventurer, class_slug (se applicabile per adventurer generation), stats

I campi runtime **richiesti dalla feature Sala+Prova+Confirmation** (`trial_status`, `explicit_confirmation_at`, `class_assignment_status`, `class_assignment_source`, `class_assignment_history`, `class_readiness_version`, `hall_discovery_state`, `hall_onboarding_state`, `trial_attempt_count`, `trial_completed_at`, `trial_version`) **NON sono presenti** nelle collection attuali.

## 6 · Gap analysis

| Area | Stato attuale | Gap | Priorità futura |
|---|---|---|---|
| Hall discovery/visit endpoint | assente | endpoint proposal `POST /class-halls/{hall_id}/visit` | ALTA |
| Trial safe-mode session model | assente | schema DB `trial_status` + endpoint `/trial/start` | ALTA |
| Trial checkpoint model | assente | endpoint `/trial/checkpoint` + campo `trial_checkpoint_state` | MEDIA |
| Trial completion tracking | assente | endpoint `/trial/complete` + campo `trial_completed_at` | ALTA |
| Explicit confirmation flow | assente | endpoint `/class/confirm` + campo `explicit_confirmation_at` | CRITICA |
| Class assignment initial | assente (esiste solo `unlock-specialization` per spec) | endpoint `/class/apply` gated · campo `class_assignment_status` | CRITICA |
| Idempotency guard | assente | request_id + retry-safe pattern | ALTA |
| Anti-farming safeguards | N/A (runtime assente) | policy safeguards in servizio | MEDIA |
| Rite of Rebirth compat | N/A | verifica compat modello storico class change | MEDIA |
| Feature flag runtime | esistono `R18_REWORK_ENABLED`, `R18_TALENT_ENGINE_ENABLED` (env) | nuovo flag proposal `CLASS_HALL_ASSIGNMENT_ENABLED` | ALTA |

## 7 · Target state machine

State machine baseline concettuale della Recluta rispetto a Sala + Prova + Conferma:

```
RECRUIT_UNASSIGNED
    │  (visita Sala)
    ▼
HALL_DISCOVERED
    │  (interazione Atrio + selezione classe)
    ▼
HALL_ONBOARDING_STARTED
    │  (dialoghi Nael G7 completati)
    ▼
TRIAL_AVAILABLE
    │  (ingresso nel cerchio · G8 sez 4)
    ▼
TRIAL_IN_PROGRESS
    │  (FASE 0 → FASE 7 · retry illimitato)
    ▼
TRIAL_COMPLETED
    │  (FASE 7 riepilogo Nael consegnato)
    ▼
AWAITING_EXPLICIT_CONFIRMATION
    │  (Recluta sceglie: CONFERMA IL CAMMINO / NON SONO PRONTO)
    ▼
CLASS_ASSIGNMENT_PENDING
    │  (regola critica AND-10 verificata · flag globale on · per-Hall enabled · Hall ACTIVE · readiness approved · target canonico)
    ▼
CLASS_ASSIGNED
```

**Stati tecnici di recovery aggiunti (FIX 9 G10)** — NON stati di gameplay · NON mostrati con codici tecnici al giocatore · NON autorizzano assegnazioni manuali:

- `CLASS_ASSIGNMENT_FAILED_RETRYABLE` — errore **pre-commit** recuperabile (validation fail, timeout DB pre-write, race condition risolvibile). Il giocatore vede messaggio UI IT futuro: *"Impossibile completare la conferma. La tua scelta non è andata persa. Riprova."* Retry idempotente autorizzato.
- `CLASS_ASSIGNMENT_RECONCILIATION_REQUIRED` — commit di `class_slug` è **valido** ma side-effect/audit/history secondari sono incompleti. Il giocatore vede messaggio UI IT futuro: *"La classe è stata assegnata. Alcuni dati sono in aggiornamento."* Reconcile-forward > rollback distruttivo (FIX 8 G10).

**Totale stati state machine documentati: 11** (9 happy-path + 2 recovery tecnici).

Gate 9 deve **verificare** che questi stati siano: **sufficienti · idempotenti · auditabili · recuperabili dopo errore**. Non li implementa.

## 8 · Recruit state (RECRUIT_UNASSIGNED)

- La Recluta è utente autenticato con account attivo · nessuna classe assegnata
- Nel DB attuale: nessun `class_slug` sul profilo Recluta (l'attuale flow adventurers genera adventurers con class_slug ma quello è un modello diverso · qui la Recluta è l'utente umano)
- Transizione uscita: **verso `HALL_DISCOVERED`** dopo visita esplicita a una Sala
- Nessuna assegnazione automatica di classe possibile a partire da questo stato

## 9 · Hall visit state (HALL_DISCOVERED)

- La Recluta ha visitato l'Atrio delle Vocazioni e ha selezionato una Sala
- Proposal DB: `hall_discovery_state = { hall_id, discovered_at, class_slug_target }`
- Proposal endpoint: `POST /api/class-halls/{hall_id}/visit` (PROPOSAL ONLY · NOT IMPLEMENTED)
- La visita **NON è vincolante** · la Recluta può cambiare Sala successivamente
- Il campo `class_slug_target` NON è un `class_slug` applicato (solo intent)

## 10 · Trial state (TRIAL_AVAILABLE → TRIAL_IN_PROGRESS)

- Trigger: la Recluta ha completato l'onboarding G7 e vuole entrare nel cerchio
- Proposal DB: `trial_status ∈ { available, in_progress, completed, abandoned }` · `trial_attempt_count` incremental · `trial_started_at` timestamp
- Proposal endpoint: `POST /api/class-halls/{hall_id}/trial/start` (PROPOSAL ONLY)
- **Vincoli safe-mode dal G8 (LOCK)**: `retry_limit=unlimited` · `cooldown=0` · `no_death_penalty` · `no_resource_loss`
- Ogni retry incrementa `trial_attempt_count` MA **non sblocca contenuto** (anti-farming G8 sez 32)

## 11 · Trial completion state (TRIAL_COMPLETED)

- Trigger: la Recluta completa la FASE 7 (Riepilogo Nael)
- Proposal DB: `trial_status = completed` · `trial_completed_at` timestamp · `trial_version` (design version della Prova · per invalidare completamenti su Prova rinnovata)
- Proposal endpoint: `POST /api/class-halls/{hall_id}/trial/complete` (PROPOSAL ONLY)
- **Zero reward**: no XP · no gold · no item · no material · no drop · no achievement farmabile
- Completion **NON assegna la classe** — precondizione ma non sufficiente

## 12 · Explicit confirmation state (AWAITING_EXPLICIT_CONFIRMATION)

- Trigger: TRIAL_COMPLETED verified
- La Recluta è **davanti a Nael** in FASE 8 · 2 sole opzioni: `CONFERMA IL CAMMINO` / `NON SONO PRONTO`
- Proposal DB: `explicit_confirmation_at` (timestamp opt) · `confirmation_choice ∈ { confirm_path, not_ready }`
- Proposal endpoint: `POST /api/class-halls/{hall_id}/class/confirm` (PROPOSAL ONLY)
- **HC-Q5 G7 LOCK CRITICAL**: nessuna conferma automatica · nessun countdown · nessuna scelta implicita
- Ogni conferma deve essere azione utente **esplicita** e **volontaria**

## 13 · Class assignment state (CLASS_ASSIGNMENT_PENDING → CLASS_ASSIGNED)

- Trigger: `confirmation_choice = confirm_path` **AND** regola critica AND-10 (sez 14 · esteso FIX 3+8+G10)
- Proposal DB: `class_assignment_status ∈ { pending, applied, rolled_back, failed, reconciliation_required }` · `class_slug` (set solo se applied · scritto sul **documento canonico avventuriero**, FIX 2 G10) · `class_assignment_at` · `class_assignment_source = "trial_confirmation_flow"` · `class_assignment_id` (univoco per domain-level idempotency, FIX 4 G10)
- **Internal service operation** (FIX 6 G10): `apply_class_assignment()` — **NOT PUBLIC ROUTE**. Invocata solo dal servizio dopo `class/confirm` valida i prerequisiti.
- **Stato attuale runtime**: feature flag `CLASS_HALL_ASSIGNMENT_ENABLED` = **disabled** AND `hall_cacciatore_del_vuoto.assignment_enabled` = **disabled** → nessuna transazione avviabile in fase attuale
- L'operazione interna respinge la richiesta se anche una sola delle 10 condizioni AND è false (comportamento tecnico documentale)

## 14 · class_slug write requirements (regola critica AND-10 · esteso G10)

La classe può essere assegnata (write di `class_slug` sul **documento canonico avventuriero** · FIX 2 G10) **SOLO se tutte le 10 condizioni sono `true` contemporaneamente**:

1. `status corrente = recruit_unassigned`
2. `Hall = ACTIVE e selezionabile`
3. `Trial = completed`
4. `explicit_confirmation = true`
5. `target class_slug canonico` (validato server-side contro `r18_6_1_canonical_27_class_halls_expansion.json` · es. `cacciatore_del_vuoto`) — **FIX 8 G10**
6. `class readiness = approved`
7. `feature flag CLASS_HALL_ASSIGNMENT_ENABLED = enabled` (kill switch globale · FIX 3 G10)
8. `hall.assignment_enabled = true` (per-Hall allowlist · FIX 3 G10)
9. `class_slug` corrente sul documento avventuriero = `null` (atomic compare-and-set · FIX 8 G10)
10. tutte le altre validazioni pre-write = PASS (auth valid · adventurer ownership · no duplicate assignment · no concurrent write)

**Nessun singolo flag bypassa le altre condizioni.** Verifica AND completa in server-side operation `apply_class_assignment()`.

**Stato attuale del sistema** (2026-07-11):

- Hall ACTIVE = **false**
- class readiness final = **false**
- feature flag `CLASS_HALL_ASSIGNMENT_ENABLED` = **disabled** (non ancora esistente in env)
- `hall_cacciatore_del_vuoto.assignment_enabled` = **disabled**
- runtime apply = **prohibited**
- → **nessuna assegnazione possibile ORA**

## 15 · Idempotency requirements

- Ogni endpoint di scrittura proposal deve accettare header `Idempotency-Key` (UUID client-generated)
- Backend memorizza `(user_id, endpoint, idempotency_key)` per ~24h → duplicati restituiscono la response originale
- **Trial start** con stessa key entro finestra → restituisce la stessa `trial_session_id`
- **Class confirm** con stessa key entro finestra → restituisce la stessa decisione
- **Class apply** con stessa key entro finestra → NO doppia assegnazione (idempotente per costruzione)
- Proposal DB: collection `idempotency_keys { user_id, endpoint, key, response_hash, created_at (TTL 24h) }`

## 16 · API contract proposal (PROPOSAL ONLY · NOT IMPLEMENTED · NOT ROUTED · NOT IN OPENAPI)

| Metodo | Path | Descrizione | Marcatura |
|---|---|---|---|
| `GET` | `/api/class-halls` | list Sale (esiste già runtime) | EXISTS · OUT OF G9 SCOPE |
| `GET` | `/api/class-halls/{hall_id}` | dettaglio Sala (esiste già runtime) | EXISTS · OUT OF G9 SCOPE |
| `POST` | `/api/class-halls/{hall_id}/visit` | segna visita Recluta | PROPOSAL ONLY |
| `POST` | `/api/class-halls/{hall_id}/trial/start` | avvia sessione Prova safe-mode | PROPOSAL ONLY |
| `POST` | `/api/class-halls/{hall_id}/trial/checkpoint` | registra checkpoint di fase | PROPOSAL ONLY |
| `POST` | `/api/class-halls/{hall_id}/trial/complete` | segna Prova completata | PROPOSAL ONLY |
| `POST` | `/api/class-halls/{hall_id}/trial/abandon` | segna Prova abbandonata | PROPOSAL ONLY |
| `POST` | `/api/class-halls/{hall_id}/class/confirm` | registra scelta esplicita CONFERMA/NON SONO PRONTO · **termina il flusso pubblico** · avvia internamente la transazione di assegnazione (FIX 6 G10) | PROPOSAL ONLY |
| ~~`POST`~~ | ~~`/api/class-halls/{hall_id}/class/apply`~~ | ~~applica `class_slug` (gated feature flag)~~ **RIMOSSO** dalle proposte pubbliche (FIX 6 G10) | **INTERNAL SERVICE OPERATION · NOT PUBLIC ROUTE · NOT CLIENT-CALLABLE** |
| `GET` | `/api/class-halls/{hall_id}/trial/state` | stato corrente Prova per la Recluta | PROPOSAL ONLY |

**TUTTE le proposal pubbliche** (visit, trial/start, trial/checkpoint, trial/complete, trial/abandon, class/confirm, trial/state): `PROPOSAL ONLY · NOT IMPLEMENTED · NOT ROUTED · NOT IN OPENAPI`. **Nessuna modifica a OpenAPI in Gate 9.**

**`class/apply` è internal service operation** (nome tecnico non runtime-lockato es. `apply_class_assignment()`), invocata **solo dal servizio** dopo `class/confirm` valida tutti i prerequisiti. Non è client-callable. Non compare in OpenAPI pubblico. Il flusso pubblico termina con `class/confirm`.

## 17 · Request schemas (proposal only)

- `POST /trial/start` request body: `{ hall_id, class_slug_target, idempotency_key }`
- `POST /trial/checkpoint` request body: `{ trial_session_id, phase_id ∈ { FASE_0..FASE_7 }, phase_state_snapshot, idempotency_key }`
- `POST /trial/complete` request body: `{ trial_session_id, idempotency_key }`
- `POST /trial/abandon` request body: `{ trial_session_id, reason (opt), idempotency_key }`
- `POST /class/confirm` request body: `{ trial_session_id, choice ∈ { confirm_path, not_ready }, idempotency_key }`
- `POST /class/apply` request body: `{ trial_session_id, confirmed_at, idempotency_key }` — auth JWT required

**Nessun schema è definito in Pydantic model reale.** Solo descrizione documentale.

## 18 · Response schemas (proposal only)

- `POST /trial/start` response: `{ trial_session_id, hall_id, class_slug_target, status: "in_progress", started_at }`
- `POST /trial/checkpoint` response: `{ trial_session_id, phase_id, accepted: true }`
- `POST /trial/complete` response: `{ trial_session_id, status: "completed", completed_at, trial_version }`
- `POST /class/confirm` response: `{ trial_session_id, choice, confirmed_at }`
- `POST /class/apply` response (feature flag on): `{ user_id, class_slug, applied_at, source: "trial_confirmation_flow" }`
- `POST /class/apply` response (feature flag off · stato attuale): `403 Forbidden` + `{ error_code: "HALL_CLASS_ASSIGN_DISABLED", message: "Runtime apply prohibited in current phase." }`

## 19 · Validation errors

- `400` — payload invalido, `idempotency_key` malformato, `class_slug_target` non canonico
- `401` — JWT assente o invalido
- `403` — feature flag disabled · Hall inactive · class readiness not approved
- `404` — `hall_id` inesistente · `trial_session_id` inesistente
- `409` — conflitto stato: es. `class/apply` chiamato con `explicit_confirmation` mancante o `trial_status != completed`
- `422` — validation Pydantic (quando implementato)
- `429` — rate limit anti-farming (soglie safe-mode-friendly · non punitive)

## 20 · Authorization requirements

- Tutti gli endpoint proposal richiedono JWT auth (`get_current_user` dependency esistente)
- `class/apply` richiede in aggiunta: `user_guild_or_404` (dep esistente) + feature flag `CLASS_HALL_ASSIGNMENT_ENABLED = enabled` + admin approval opzionale per prima Wave
- Nessun endpoint proposal deve essere accessibile senza auth
- Nessuna elevazione di privilegio implicita

## 21 · DB schema proposal (PROPOSAL ONLY · NO DB WRITE · NO MIGRATION)

Campi proposal (da aggiungere in futuro alla collection appropriata · **verificare prima se equivalente già esiste**):

| Field | Tipo | Location proposta | Marcatura |
|---|---|---|---|
| `class_slug` | string | `users` o `characters` | PROPOSAL ONLY · verificare se esiste |
| `class_assignment_status` | enum `pending/applied/rolled_back/failed` | `users` | PROPOSAL ONLY |
| `class_assignment_source` | string | `users` | PROPOSAL ONLY |
| `class_assignment_at` | ISODate | `users` | PROPOSAL ONLY |
| `class_assignment_history` | array of objects | `users` | PROPOSAL ONLY |
| `hall_discovery_state` | object | `users` | PROPOSAL ONLY |
| `hall_onboarding_state` | object | `users` | PROPOSAL ONLY |
| `trial_status` | enum | nuova collection `trial_sessions` | PROPOSAL ONLY |
| `trial_attempt_count` | int | `trial_sessions` | PROPOSAL ONLY |
| `trial_completed_at` | ISODate | `trial_sessions` | PROPOSAL ONLY |
| `trial_version` | string | `trial_sessions` | PROPOSAL ONLY |
| `explicit_confirmation_at` | ISODate | `users` | PROPOSAL ONLY |
| `class_readiness_version` | string | metadata globale (config) | PROPOSAL ONLY |
| `idempotency_keys` (collection) | `{user_id, endpoint, key, response_hash, created_at TTL}` | nuova collection | PROPOSAL ONLY |

**Nessun campo scritto · nessuna migrazione applicata · nessun index creato in Gate 9.**

## 22 · Audit fields

Ogni transizione di stato Recluta rispetto a class_slug deve produrre audit log:

- `audit_event_type ∈ { hall_visited, trial_started, trial_checkpoint, trial_completed, trial_abandoned, class_confirmed, class_applied, class_apply_denied }`
- `audit_event_payload`: `{ user_id, hall_id, class_slug, trial_session_id, timestamp, feature_flag_state, ... }`
- Storage: modulo esistente `app/audit/log.py` (`audit_log` collection) — riuso pipeline esistente in futuro · **nessuna modifica ora**
- Retention: da definire in Gate 10+

## 23 · Historical class tracking

- La Recluta può, in futuro, cambiare classe tramite **Rite of Rebirth** (feature esistente in design R18.3f · non applicata)
- Proposal campo `class_assignment_history`: array di oggetti `{ class_slug, applied_at, source, terminated_at (opt), termination_reason (opt) }`
- Ogni Rebirth append un nuovo oggetto · classe corrente = ultimo elemento con `terminated_at = null`
- **Gate 9 NON implementa nulla**: documenta compatibilità di schema

## 24 · Rite of Rebirth compatibility

- R18.3f **Class Slug Migration Readiness** è in HOLD (dipendenza formale)
- Il modello `class_assignment_history` deve essere compatibile con Rite of Rebirth
- Ogni class change (initial assignment o Rebirth) deve passare attraverso lo stesso `class_assignment_transaction` (sez 37) — no path alternativi
- **Nessuna esecuzione** di R18.3f in Gate 9

## 25 · Proficiency integration

- La weapon family reserved `Lanterna` (G7 semantic guard sez 44) resta `reserved_future_review` · **non integrata** nella proficiency del Cacciatore del Vuoto
- Proficiency attiva Cacciatore del Vuoto (da G5 EQUIP): `focus`, `balestra`, `pugnale` + `stoffa`, `cuoio`
- Gate 9 NON riapre proficiency · documenta solo il vincolo di integrità futura
- Registry v3 pilot esclude Lanterna dal set attivo (RV3 approved · apply NOT authorized)

## 26 · Equip eligibility integration

- Assegnata la classe (in futuro), il sistema equip eligibility deve leggere `class_slug` per determinare cosa la Recluta può indossare
- Modulo esistente: `app/equipment/*` (esiste già, ma NON gestisce class_slug della Recluta oggi · gestisce equip degli adventurers)
- Proposal: futura integrazione read-side `class_slug → allowed_armor + allowed_weapon_family`
- **Gate 9 NON modifica** il modulo `equipment/`

## 27 · XP-main-stat future integration

- Cacciatore del Vuoto: main stat **Intelligenza** (G3 · G6 LOCK)
- XP pipeline futura deve applicare bonus `+X% XP se main_stat = INT` (design_only · NO valori numerici in Gate 9)
- Proposal: nuovo campo `xp_multiplier_source = "class_main_stat_alignment"` in audit event
- **Gate 9 NON modifica** XP pipeline

## 28 · Hall availability flags

- Ogni Sala ha uno stato: `PLANNED` (design_only) · `ACTIVE` (runtime disponibile) · `DEPRECATED`
- Attualmente **tutte le Sale Wave 1** (Cacciatore del Vuoto incluso) sono in stato `PLANNED`
- Proposal campo DB: `class_halls.availability_state ∈ { planned, active, deprecated }`
- Trigger di attivazione futura: PM approval Wave 1 + feature flag `CLASS_HALL_ASSIGNMENT_ENABLED = enabled`
- Gate 9 NON attiva alcuna Sala

## 29 · PLANNED vs ACTIVE state

- **PLANNED**: Sala visibile in UI con marker *"SALA DI DESIGN — NON ANCORA ISTANZIATA IN GIOCO"* (G7 HC-Q8 LOCK) · nessun onboarding · nessuna Prova avviabile · nessun class_slug apply
- **ACTIVE**: Sala pienamente istanziata · onboarding disponibile · Prova avviabile · class_slug apply gated dietro feature flag
- Transizione `PLANNED → ACTIVE`: richiede PM approval + Gate 10 readiness completa
- La transizione **NON è automatica** basata su feature flag: è approvazione umana esplicita

## 30 · Trial availability flags

- Proposal campo DB: `trial_sessions.trial_available_flag` (derivato da `hall.availability_state = active` + `feature_flag = enabled`)
- Se `trial_available_flag = false` · endpoint `/trial/start` restituisce 403 con messaggio *"PROVA DI DESIGN — NON ANCORA DISPONIBILE IN GIOCO"* (G8 TR-Q8 LOCK)
- Stato attuale runtime: `trial_available_flag = false` per Cacciatore del Vuoto

## 31 · Safe-mode session model

- Ogni sessione Prova è un documento nella collection proposal `trial_sessions`:
  - `_id`, `user_id`, `hall_id`, `class_slug_target`
  - `status ∈ { in_progress, completed, abandoned }`
  - `attempt_count`, `started_at`, `completed_at (opt)`, `abandoned_at (opt)`
  - `phase_state_snapshots`: array di checkpoint per fase (FASE_0..FASE_7)
  - `trial_version`: design version della Prova
  - `no_reward_flag = true` (invariante · non è settabile a false)
  - `no_persistence_side_effects = true` (invariante)

## 32 · Checkpoint model

- Ogni checkpoint fase è un elemento in `phase_state_snapshots`: `{ phase_id, snapshot_at, phase_completed: bool, retry_count_in_phase, hint_level_shown ∈ { 0, 1, 2 } }`
- Checkpoint **non persiste risorse di gioco** (Frammenti sono interni al singolo scontro · G8 sez 11)
- Ripresa dopo abbandono: futuro Gate può decidere se `resume_from_last_checkpoint` o `restart_from_fase_0` (**TR-Q6 policy checkpoint precisa = spec futura Gate 9/10**)

## 33 · Retry model

- `retry_limit = unlimited` (G8 sez 29 LOCK)
- `cooldown = 0` (G8 sez 30 LOCK)
- `attempt_count` incrementale · **nessuno sblocco basato su count**
- Ogni retry crea un nuovo `trial_session_id` (per audit) o riusa lo stesso (per idempotency) · **decisione tecnica in Gate 10**
- Anti-farming: `attempt_count` NON entra in leaderboard/ranking/achievement

## 34 · Abandon model

- La Recluta può abbandonare la Prova in qualsiasi momento (G8 sez 43 · 45)
- Proposal endpoint: `POST /trial/abandon` (PROPOSAL ONLY)
- Registra `trial_sessions.status = abandoned` + `abandoned_at` + `abandon_reason (opt)`
- Nessuna penalità · nessun consumo · nessun blocco futuro
- Ritorno UX: Sala o Atrio (decisione UI · non backend)

## 35 · Anti-farming safeguards

- Trial produce **zero reward** (G8 sez 31): no XP · no gold · no item · no material · no drop · no achievement farmabile
- Nessuna metrica ripetibile è ottimizzabile (G8 sez 32)
- Retry non concede vantaggi accumulabili
- Rate limit soft (429) solo per protezione infrastruttura · **non è penalità di gioco**
- Se un utente accumula > N tentativi (soglia da definire in Gate 10) · un audit event `trial_high_retry` viene emesso · **nessuna azione automatica** verso l'utente

## 36 · No-reward enforcement

- Backend deve validare (in futuro): endpoint `/trial/complete` **NON** emette event XP · **NON** modifica `gold` · **NON** aggiunge item all'inventory · **NON** modifica achievement counter
- Test futuro obbligatorio: `test_trial_complete_zero_reward_enforcement` (Gate 10+)
- Enforcement architetturale: nessun hook post-trial è collegato a XP/gold/item pipeline

## 37 · Class assignment transaction

- La scrittura di `class_slug` sul profilo Recluta è una **transazione atomica** composta da:
  1. Verifica AND-8 (sez 14) · fail-fast se qualsiasi condizione è false
  2. Idempotency check (sez 15) · return cached response se duplicato
  3. Write `class_slug = target_class_slug` + `class_assignment_status = applied` + `class_assignment_at = now()` + append `class_assignment_history`
  4. Emit audit event `class_applied`
  5. Response 200 con payload response schema
- Se step 3 fallisce: `class_assignment_status = failed` · rollback secondo strategia sez 38

## 38 · Rollback strategy

- Se `class/apply` fallisce a metà transazione:
  - Riporta `class_slug` allo stato precedente (di solito `null`)
  - Set `class_assignment_status = rolled_back`
  - Append audit event `class_apply_rolled_back` con motivazione
  - Response 500 con `error_code: ROLLBACK_APPLIED`
- MongoDB non ha transazioni multi-document nativo · usa **replica set transactions** o **compensating actions** (decisione tecnica Gate 10)

## 39 · Failure recovery

- Se `/class/apply` fallisce per timeout / connessione / errore MongoDB: la Recluta può riprovare con stesso `idempotency_key`
- Se stato DB è inconsistente (raro): admin path documentale `POST /api/admin/class-assignment/reconcile` (**PROPOSAL ONLY**, non in Gate 9)
- Ogni failure emette audit event con root cause

## 40 · Concurrency safeguards

- Un utente può avere **al massimo 1 sessione Prova attiva** contemporaneamente (query filter `status=in_progress AND user_id=X`)
- Un utente può avere **al massimo 1 richiesta `/class/apply` in-flight** (idempotency + optimistic locking su `class_assignment_status`)
- Se doppio submit: seconda chiamata ritorna 409 `CONCURRENT_APPLY_IN_PROGRESS`
- Nessuna elezione di doppie classi per user

## 41 · Duplicate confirmation safeguards

- Se `/class/confirm` è chiamato più volte con stessa scelta e stesso `idempotency_key`: response cached identica (idempotenza)
- Se `/class/confirm` è chiamato più volte con **scelte diverse** (senza stessa key): return 409 `CONFIRMATION_ALREADY_MADE` · la scelta iniziale è quella valida
- La scelta `not_ready` NON blocca visite future · può essere ri-espressa come `confirm_path` in una sessione successiva

## 42 · Migration dependency

- **R18.3f Class Slug Migration Readiness**: HOLD · nessun class_slug può essere applicato/migrato in produzione senza R18.3f approvato
- La Recluta oggi NON ha campo `class_slug` sul profilo utente (dipendenza per creare il campo)
- Migration path: R18.3f fornirà **script di migrazione dry-run** + **feature flag** + **schema check**
- Gate 9 documenta la dipendenza · **non applica** R18.3f

## 43 · R18.3f dependency

Ogni scrittura di `class_slug` sul profilo Recluta:

- Deve essere abilitata da R18.3f Class Slug Migration
- Deve rispettare lo schema definito da R18.3f
- Deve emettere gli audit event definiti da R18.3f
- Deve rispettare le drift-guards di R18.3f (assenza di reintroduzione classi non-canonical come `warlock` legacy)
- **Bridge legacy `warlock → cacciatore_del_vuoto`**: `mapped_design_only = true` · applicabile in migrazione **solo dopo R18.3f apply approved** · Gate 9 può referenziarlo ma NON attivarlo

## 44 · Registry v3 dependency

- **R18.6.RV3 Registry v3 Additive Planning**: architecture approved · apply NOT authorized
- Il pilot Cacciatore del Vuoto usa il registry v3 (`focus`, `balestra`, `pugnale` + `stoffa`, `cuoio`) come design reference
- Gate 9 documenta il vincolo · **non applica** Registry v3
- L'eventuale futura activation Sala richiede Registry v3 already applied per garantire consistency proficiency ↔ equip eligibility

## 45 · Eligibility Validation dependency

- **R18.6.RV3-EV Eligibility Validation Gate**: HOLD (gate futuro obbligatorio pre-Item Creation)
- Nessun item può essere creato/droppato per Cacciatore del Vuoto senza EV approved
- Gate 9 documenta il vincolo · **non applica** EV
- L'attivazione Sala PRECEDE la creazione item (safe-mode trial è pre-item)

## 46 · Observability requirements

- Ogni transizione stato Recluta emette event tracciabile (audit + metrics)
- Metrics proposal:
  - `hall_visits_total{hall_id,class_slug}` counter
  - `trial_sessions_started_total{hall_id,class_slug}` counter
  - `trial_sessions_completed_total{hall_id,class_slug}` counter
  - `trial_sessions_abandoned_total{hall_id,class_slug}` counter
  - `class_assignments_applied_total{class_slug}` counter (0 in fase attuale)
  - `class_apply_denied_total{reason}` counter
- Storage: sistema metrics esistente · **nessuna nuova infrastruttura in Gate 9**

## 47 · Logging requirements

- Livello INFO per transizioni di stato
- Livello WARN per fallimenti recoverable (idempotency conflict, retry limits soft)
- Livello ERROR per fallimenti non-recoverable (DB error, rollback triggered)
- Log strutturato JSON con campi standard: `user_id`, `hall_id`, `class_slug`, `event`, `outcome`, `duration_ms`, `feature_flag_state`
- **Vietato** loggare dati sensibili (password, JWT full token) — solo `user_id`

## 48 · Privacy requirements

- `user_id` è ID interno · mai `email` in audit/logs
- Log Prova (checkpoint, riepilogo) non contengono dati identificativi personali oltre `user_id`
- Retention audit event: da definire (proposal: 90 giorni) · Gate 10+
- GDPR compliance: implementata via export/delete API esistente auth (non modificata in Gate 9)

## 49 · Security requirements

- Tutti gli endpoint proposal richiedono JWT valido (dep `get_current_user`)
- `/class/apply` in aggiunta: rate limit per user (max N/day, N da definire · anti-abuse)
- Nessun endpoint proposal deve accettare `class_slug` da payload che salta la regola AND-8 (server-side enforcement)
- Nessun cross-user access: un utente può solo modificare il proprio state
- `hall_id` è pubblico · `trial_session_id` è per-user segreto (server-side lookup con user_id filter)

## 50 · Test strategy

Gate 9 **non scrive test** (dispatch PM: NO test file creation). Documenta solo il piano:

- **Unit test** (Gate 10+): logica AND-8, idempotency, rollback, concurrency guard, feature flag gating
- **Integration test** (Gate 10+): flow end-to-end visita→trial→confirm→apply con mock DB
- **E2E test** (Gate 10+): browser flow Sala UI → Prova UI → confirmation dialog → dashboard mostra class_slug
- **Sealed integrity test**: NON modificato (36 sigilli protetti da Gate 9 e successivi)

## 51 · Unit test plan (documental)

- `test_and8_all_conditions_true_allows_apply` (Gate 10+)
- `test_and8_any_condition_false_denies_apply_403` (parametrizzato 8 casi)
- `test_idempotency_duplicate_returns_cached` (Gate 10+)
- `test_concurrency_double_submit_returns_409` (Gate 10+)
- `test_rollback_on_partial_failure_restores_state` (Gate 10+)
- `test_feature_flag_disabled_denies_apply_403` (Gate 10+)
- `test_hall_planned_denies_apply_403` (Gate 10+)
- `test_class_slug_not_canonical_denies_400` (Gate 10+)

## 52 · Integration test plan (documental)

- `test_visit_creates_hall_discovery_state` (Gate 10+)
- `test_trial_start_creates_trial_session` (Gate 10+)
- `test_trial_checkpoint_appends_snapshot` (Gate 10+)
- `test_trial_complete_transitions_status` (Gate 10+)
- `test_trial_complete_emits_zero_reward` (Gate 10+ · CRITICO)
- `test_class_confirm_records_choice` (Gate 10+)
- `test_class_apply_gated_feature_flag_off` (Gate 10+ · CRITICO)
- `test_class_apply_full_flow_end_to_end_with_flag_on_and_hall_active` (Gate 10+)

## 53 · End-to-end test plan (documental)

- **E2E-1**: Visitatore → Sala UI PLANNED → marker visibile → nessuna Prova avviabile (STATE ATTUALE atteso)
- **E2E-2**: Visitatore → Sala UI ACTIVE (feature flag on · gate futuro) → dialoghi Nael → cerchio → Prova avvia → FASE 0..7 → riepilogo → conferma → classe applicata sul profilo (Gate 10+)
- **E2E-3**: Visitatore rinuncia in FASE 8 → ritorno all'Atrio · nessuna assegnazione (Gate 10+)
- **E2E-4**: Retry Prova senza limite (Gate 10+)
- **E2E-5**: Doppio submit `/class/apply` con stessa idempotency-key → una sola assegnazione (Gate 10+)

## 54 · Sealed integrity impact

- I 36 file sigillati (`backend/tests/backend_r18_4_sealed_integrity_test.py`) **NON possono essere modificati** senza PM approval esplicita
- Se l'implementazione futura richiedesse modifiche a uno dei 36 file: **prima** PM approval + **poi** aggiornamento hash nel test (con verifica bilaterale)
- Gate 9 documenta il vincolo: **nessuna implementazione futura può bypassare i 36 sigilli**
- L'anchor `backend/app/content/lore_meta.py` = `a18f708b...65b8f` è invariante · qualsiasi modifica richiede re-approval PM

## 55 · Deployment prerequisites

Per attivare (in futuro Gate 10+) la Sala Cacciatore del Vuoto in ambiente prod:

1. R18.3f applied (class_slug schema migration)
2. Registry v3 applied
3. Sala availability_state = `active` (approvata PM)
4. Feature flag `CLASS_HALL_ASSIGNMENT_ENABLED` = enabled (env var)
5. class readiness final = approved
6. Test suite Gate 10 = 100% pass
7. Sealed integrity 36/36 = byte-identical
8. Backup DB pre-migration disponibile
9. Rollback playbook approvato
10. Monitoring dashboards configurati

**Gate 9 NON avvia** nessuno di questi step.

## 56 · Feature flag strategy

- Nuovo flag proposto: `CLASS_HALL_ASSIGNMENT_ENABLED` (env-based · default `false`)
- Attivazione: solo dopo Gate 10 readiness + PM approval
- Rollout: gradual (canary) · monitorato via metrics sez 46
- Kill switch: setting `CLASS_HALL_ASSIGNMENT_ENABLED = false` disabilita instant · idempotency keys restano validi
- Coexistence: `CLASS_HALL_ASSIGNMENT_ENABLED` è **ortogonale** a `R18_REWORK_ENABLED` e `R18_TALENT_ENGINE_ENABLED` esistenti · nessun conflitto

## 57 · Rollback criteria

Se dopo activation Wave 1 (futuro) si rilevano:

- Assegnazioni classe errate (bug transaction)
- Feedback utenti negativi > soglia PM
- Sealed integrity failure
- Data corruption
- Perdite anomale di risorse Recluta

→ **Kill switch feature flag** immediato (`CLASS_HALL_ASSIGNMENT_ENABLED = false`)
→ Playbook rollback: restore DB pre-activation · disable endpoint routes · audit event `rollback_triggered` · comunicazione utenti

**Gate 9 NON esegue** alcun rollback (nulla da rollbackare · nessuna attivazione).

## 58 · Readiness checklist

Checklist da valutare in Gate 10 PM_REVIEW (**Gate 9 NON tick nulla**):

- [ ] R18.3f applied
- [ ] Registry v3 applied
- [ ] R18.6.RV3-EV applied
- [ ] Sala availability_state = active
- [ ] `CLASS_HALL_ASSIGNMENT_ENABLED` env var configurata (default off)
- [ ] Unit test Gate 10 = 100% pass
- [ ] Integration test Gate 10 = 100% pass
- [ ] E2E test Gate 10 = 100% pass
- [ ] Sealed integrity 36/36 = byte-identical
- [ ] Rollback playbook approvato
- [ ] Monitoring dashboards attivi
- [ ] PM final approval

## 59 · Risk register (15 rischi tracciati)

| ID | Rischio | Severity | Status |
|---|---|---|---|
| TR9-R1 | Ambiguità schema `class_slug` vs `class_slug` adventurers legacy | MEDIUM | DESIGNED (namespace separati · Recluta ≠ adventurer) |
| TR9-R2 | Race condition doppio submit `/class/apply` | HIGH | DESIGNED (idempotency + optimistic locking) |
| TR9-R3 | Rollback parziale lascia DB inconsistente | HIGH | DESIGNED (compensating actions + audit) |
| TR9-R4 | Feature flag enable accidentale | HIGH | DESIGNED (default false · env var esplicita) |
| TR9-R5 | Hall availability_state modificato senza PM approval | HIGH | DESIGNED (workflow approval documentato) |
| TR9-R6 | Trial checkpoint spam anti-farming saturazione DB | MEDIUM | DESIGNED (rate limit soft + TTL su snapshots) |
| TR9-R7 | Class assignment applied a class_slug non canonico | HIGH | DESIGNED (server-side canonical validation) |
| TR9-R8 | Bridge legacy `warlock → cacciatore_del_vuoto` attivato per errore | MEDIUM | DESIGNED (dipende da R18.3f · `mapped_design_only = true`) |
| TR9-R9 | Sealed integrity breach in future implementation | HIGH | DESIGNED (36 sigilli · PM approval required) |
| TR9-R10 | XP/gold accidentalmente emessi da trial complete | HIGH | DESIGNED (enforcement architetturale sez 36) |
| TR9-R11 | Rite of Rebirth path bypass class_assignment_transaction | MEDIUM | DESIGNED (unified transaction sez 37) |
| TR9-R12 | Concurrency guard non copre replica set failover | MEDIUM | DESIGNED (transactions Mongo replica-aware) |
| TR9-R13 | UI polling `/trial/state` genera carico eccessivo | LOW | DESIGNED (cache lato server + polling rate limit) |
| TR9-R14 | Discovery leaks internal state a utente | MEDIUM | DESIGNED (server-side filtering `no_persistence_side_effects`) |
| TR9-R15 | Dipendenza Gate 9 cross-team (frontend UX design) non allineata | MEDIUM | TRACKED (Gate 10 dovrà sincronizzare UX design team) |

## 60 · PM Open Questions (TR9-Q1..TR9-Q8)

- **TR9-Q1** · *Nuova collection `trial_sessions` separata o embed in `users`?* → **a) LOCK collection separata** · b) embed in users · c) altra proposta PM
- **TR9-Q2** · *`class_slug` field location: `users` o nuova collection `characters`?* → **a) LOCK `users.class_slug`** · b) nuova collection `characters` · c) altra proposta PM
- **TR9-Q3** · *Naming feature flag: `CLASS_HALL_ASSIGNMENT_ENABLED` conferma?* → **a) LOCK naming** · b) rinomina proposta PM
- **TR9-Q4** · *Idempotency window 24h conferma?* → **a) LOCK 24h** · b) 1h · c) 7 giorni · d) configurabile
- **TR9-Q5** · *Retry Prova: nuovo `trial_session_id` per ogni retry o riuso stesso?* → **a) LOCK nuovo id per audit** · b) riuso stesso · c) configurabile
- **TR9-Q6** · *Rate limit anti-abuse su `/class/apply` (max N/day)?* → **a) LOCK 5/day** · b) 10/day · c) 1/day · d) unlimited
- **TR9-Q7** · *Rollback strategy: replica set transactions o compensating actions?* → **a) LOCK replica set transactions** · b) compensating · c) hybrid
- **TR9-Q8** · *Admin path `/api/admin/class-assignment/reconcile` incluso in Gate 10 o deferred?* → **a) LOCK deferred (Gate 11+)** · b) incluso Gate 10 · c) mai

## 61 · GO/HOLD Recommendation Gate 10 PM_REVIEW

- **Gate 9 status**: DRAFT · pending PM review + risposte TR9-Q1..TR9-Q8
- **Gate 10 PM_REVIEW status**: 🔒 **HOLD** · attende PM ACK Gate 9 + GO esplicito
- **Gate 10 scope preview**: PM_REVIEW è **NON** implementazione. È il gate di **review finale** della specifica G9 · risposta alle TR9-Q · approvazione go/no-go per Gate 11 (che a sua volta sarà il primo gate implementativo, se autorizzato).
- **NO Gate 10 auto-start** · **NO Wave 1 auto-start** · **NO class unlock auto-start** · **NO Hall activation auto-start**
- **NO implementation** ha luogo in Gate 10 · Gate 10 è review
- **Recommended next step**: PM review G9 TECH_READINESS + risposte TR9-Q1..TR9-Q8 → G9 CLOSED verdict → GO Gate 10 PM_REVIEW

## 62 · Nota consolidata Micro-fix G10 (10 chiarimenti PM)

Applicati come chiarimenti documentali post PM-review Gate 9:

- **FIX 1 · Storage ibrido**: identità permanente Recluta → **documento canonico avventuriero** (campi `class_slug`, `class_assignment_status`, `class_assignment_source`, `class_assignment_at`, `class_assignment_id`, `class_assignment_history`, `class_readiness_version`). Sessioni Trial temporanee → collection separata proposta `class_hall_trial_sessions` (nome non runtime-lockato) · `PROPOSAL ONLY · NO CREATION · NO MIGRATION · NO DB WRITE`. Nessun checkpoint nel documento avventuriero. Nessun `class_slug` nella sessione come source of truth. Riutilizzare campi equivalenti esistenti se presenti (verifica read-only pre-implementation).
- **FIX 2 · class_slug location**: `class_slug` su **root del documento canonico dell'avventuriero** (source of truth). NON su root account/user · NON su Trial session · NON su Hall document · NON su collection tecnica separata. Utente/account può avere più avventurieri → nessuna classe globale su account. Pre-implementation: verificare schema live per riutilizzare campo canonico già presente (nessun duplicato).
- **FIX 3 · Feature flag a due livelli**: `CLASS_HALL_ASSIGNMENT_ENABLED` (kill switch globale · default `false`) **AND** `hall.assignment_enabled` (per-Hall allowlist · default `false`). Regola AND: entrambi `true` + `hall.status=ACTIVE` + `class_readiness=approved`. Nessun singolo flag bypassa altre condizioni. Stato attuale: entrambi disabled.
- **FIX 4 · Idempotency a due livelli**: **L1 Request replay** (`Idempotency-Key` UUID · chiave concettuale `authenticated_user_id + adventurer_id + hall_id + trial_version + idempotency_key` · finestra **24h**). **L2 Idempotenza di dominio** (`class_assignment_id` univoco + atomic conditional update + `class_slug=null` + `status=recruit_unassigned`). Dopo assegnazione valida: duplicati restituiscono stato già assegnato · NO seconda write. Scadenza cache L1 NON deve permettere seconda write (L2 permanente).
- **FIX 5 · Checkpoint server-authoritative**: client-driven request · server-authoritative state. Il client può richiedere transizione, inviare input, mostrare checkpoint, richiedere ripresa. Il client NON può dichiarare autonomamente fase completata, Trial completata, Payoff superato, classe eleggibile. Server valida sessione attiva, fase corrente, transizione consentita, stato precedente, versione Prova, completion evidence prevista. Checkpoint idempotenti, ordinati, recuperabili, NON saltabili tramite payload client.
- **FIX 6 · `/class/apply` rimosso da API pubbliche**: `POST /api/class-halls/{hall_id}/class/apply` **rimosso** dalle proposal pubbliche. Documentato come `internal operation: apply_class_assignment()` (nome non runtime-lockato) · marker `INTERNAL SERVICE OPERATION · NOT PUBLIC ROUTE · NOT CLIENT-CALLABLE`. Flusso pubblico termina con `POST /api/class-halls/{hall_id}/class/confirm` che valida prerequisiti, registra intento esplicito, avvia internamente la transazione.
- **FIX 7 · Rate limit `/class/confirm`**: baseline **3 req/min per adventurer_id · 10 req/min per account autenticato**. Replay identiche con stessa `Idempotency-Key` → NO nuove write. Limite superato → HTTP 429 futuro · NO mutazione · NO perdita Trial · NO reset · NO consumo. Rate limit NON sostituisce idempotenza né controllo atomico.
- **FIX 8 · Atomic compare-and-set + reconcile-forward**: pre-write validation AND-10 (sez 14). Write futura: singola mutazione atomica sul documento canonico avventuriero con condizione `class_slug ancora null`. **Failure pre-commit**: nessuna mutazione permanente · stato recuperabile · retry idempotente. **Post-commit valido**: NO rollback automatico distruttivo verso `recruit_unassigned`. Se falliscono log/audit/operazioni secondarie: classe assegnata resta source of truth · sistema entra in riconciliazione · si riparano effetti secondari. **Principio: reconcile-forward > rollback distruttivo.**
- **FIX 9 · Due failure states tecnici**: `CLASS_ASSIGNMENT_FAILED_RETRYABLE` (pre-commit) + `CLASS_ASSIGNMENT_RECONCILIATION_REQUIRED` (post-commit reconcile). NON stati gameplay · NON mostrati con codici tecnici · NON autorizzano assegnazioni manuali. Messaggi UI futuri in italiano definiti in sez 7. Totale stati state machine: **11** (9 happy + 2 recovery).
- **FIX 10 · Admin reconcile INTERNAL-ONLY**: necessario ma `INTERNAL ONLY · ADMIN ONLY · NOT PLAYER API · NOT PUBLIC OPENAPI`. Preferire comando amministrativo interno o endpoint amministrativo isolato. NON aggiunto ora. Caratteristiche future obbligatorie: `dry_run=true` default, role-based authorization, audit completo, reason obbligatoria, correlation_id, prima/dopo, no hard delete. **Azioni consentite**: ispezionare assegnazioni bloccate, ripristinare side-effect mancanti, ricostruire audit, riconciliare stato pending, chiudere transazione già validamente committata. **Azioni vietate**: scegliere classe arbitraria, bypassare Prova, bypassare conferma esplicita, bypassare feature flag, bypassare readiness, forzare `class_slug` senza evidenza valida. Reconcile ripara coerenza tecnica · NON è scorciatoia di assegnazione.

### Class assignment transaction — 13 step obbligatori (esteso G10)

1. autenticazione (JWT valido)
2. autorizzazione su avventuriero (ownership)
3. verifica `status = recruit_unassigned`
4. verifica `hall.status = ACTIVE`
5. verifica `trial_status = completed`
6. verifica `explicit_confirmation = true`
7. verifica `class_readiness = approved`
8. verifica feature flag globale `CLASS_HALL_ASSIGNMENT_ENABLED = true`
9. verifica per-Hall enable `hall.assignment_enabled = true`
10. verifica `target_slug` canonico (registry check)
11. **atomic compare-and-set** su `class_slug` (condition `class_slug IS NULL`)
12. scrittura `class_assignment_history` + audit event `class_applied`
13. risposta idempotente (usa `class_assignment_id` per response cache)

Failure step 1-10 → `CLASS_ASSIGNMENT_FAILED_RETRYABLE` · idempotent retry autorizzato.
Failure step 11 (race condition CAS lost) → `CLASS_ASSIGNMENT_FAILED_RETRYABLE` · nessuna mutazione persistita.
Failure step 12-13 con step 11 committato → `CLASS_ASSIGNMENT_RECONCILIATION_REQUIRED` · reconcile-forward.

### Dipendenze ancora aperte (Gate 10 NON può dichiarare implicite)

- R18.3f Class Slug Migration Readiness
- R18.6.RV3-EV Eligibility Validation
- Registry v3 (architecture approved, apply not authorized)
- Feature flag implementation (`CLASS_HALL_ASSIGNMENT_ENABLED` + `hall.assignment_enabled`)
- Hall activation approval (per-Hall)
- Runtime implementation gate futuro
- Deployment approval

---

## 🛑 STOP obbligatorio a fine G9 · Non procedere a Gate 10 senza nuovo GO PM

> ⚠️ **SPECIFICA TECNICA DOCUMENTALE — NON IMPLEMENTAZIONE**
> Questo documento descrive **PROPOSAL ONLY** per implementazione futura. Nessun endpoint reale · nessuna modifica OpenAPI · nessuna migrazione DB · nessun class_slug applicato · nessuna Hall attivata · nessuna Prova avviabile · nessun feature flag abilitato · nessun test scritto.

Attendo PM review Gate 9 TECH_READINESS + risposte a **TR9-Q1..TR9-Q8**. Nessun auto-start Gate 10 · Nessun auto-start Wave 1 successors · Nessuna modifica R18.5/R18.6/R18.6.1/R18.6.2/G1/G2/G3/G4/G5/RV3/G6/G7/G8 (tutti LOCKED).
