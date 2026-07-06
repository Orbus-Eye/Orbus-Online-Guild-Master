# Orbus Backlog

Formato: `[STATE] <round_ref> — <titolo breve>`
Origine di verità dei backlog aperti dei round R18.*.

---

## Backlog aperti

### [BACKLOG] R18.4.backlog — Backfill Apply Idempotency Counter Pattern
- **Aperto**: 2026-07-06
- **Origine**: risk note #1 report B3 real apply
- **Descrizione**: `backfill_slot_type_apply` usa early guard fail-fast (exit 1) in idempotency invece di `already_correct` counter. Zero DB write in rerun, comportamento safe intenzionale. Alignment desiderabile con pattern `class_bound_apply` (che ritorna `modified_count=0` + `already_correct=178` esplicito).
- **Priorità**: P3
- **Blocker**: none
- **Non fare**: modificare i 2 sibling script real apply senza GO PM esplicito (sono sealed post-B4).
- **Status**: BACKLOG

---

### [BACKLOG] R18.4.backlog — Class-Bound Apply Zero-Write Audit Noise
- **Aperto**: 2026-07-06
- **Origine**: risk note #2 report B3 real apply
- **Descrizione**: `class_bound_apply` rerun emette 2° audit event `R18_4_ITEM_BINDING_POLICY_APPLIED` con `modified_count=0`. Audit noise minimo, distinguibile via `apply_id` UUID. Considerare filtro audit event se `count==0` per compressione telemetria.
- **Priorità**: P3
- **Blocker**: none
- **Non fare**: modificare i sibling script apply senza GO PM (sealed post-B4).
- **Status**: BACKLOG

---

### [BACKLOG] R18.4.followup — Public API serializer exposure of slot_type + item_binding_policy for UI activation
- **Aperto**: 2026-07-06
- **Origine**: nota tester POST-APPLY smoke E2E + PM directive B4
- **Descrizione**: I public API serializers (`/api/items`, `/api/admin/items`, inventory item embed) NON espongono `slot_type` e `item_binding_policy`. Coerente con "metadata only, no runtime enforcement" attuale R18.4. Sblocco necessario per future UI features (binding badges 4-state su catalog cards, SQ7 UI activation, `recommended_for_class` + `is_universal` derived signals).
- **Priorità**: P3
- **Blocker**: none — sblocca SQ7 UI activation futura.
- **Non fare**: modificare serializer runtime senza GO PM esplicito.
- **Status**: BACKLOG

---

### [BACKLOG] R18.4.followup — Shield slot mapping decision
- **Aperto**: 2026-07-06
- **Origine**: R18.4 Phase B2 PM Decision Lock — SQ1 opzione (a) confermata
- **Obiettivo**: rivalutare mapping shield → armor in caso di introduzione futura di un 4° slot equipaggiabile dedicato (`shield`) o di modifica delle regole di equipaggio a 4 slot.
- **Motivazione**: SQ1(a) è SAFE non-breaking ma è una scelta di semplicità (2 items impattati: `spec_signature_aegis_of_the_defender`, `spec_signature_thornwood_shield`). Se il gameplay futuro richiede shield stackabile con armor o slot dedicato, questo mapping va rivisto.
- **Priorità**: P3
- **Scope**: rivisitazione del design equipment slots + eventuale extend EQUIPMENT_SLOTS.
- **Non fare**: cambiare il mapping in autonomia senza GO PM esplicito.
- **Status**: BACKLOG

---

### [BACKLOG] R18.4.backlog — specialization_unlocks dead branch cleanup
- **Aperto**: 2026-07-06
- **Origine**: R18.4 Phase B1 Deep-Dive Audit + Phase B2 SQ2 lock
- **Obiettivo**: decidere se rimuovere, deprecare formalmente, o riattivare il branch `specialization_unlocks` in `backend/app/equipment/compatibility.py:130-165` (3 rule-step attualmente non usati da nessun item runtime).
- **Motivazione**: feature R16.0 introdotta ma mai popolata su items. Il branch è dead code runtime; da SQ2 PM lock è mantenuto e documentato come "reserved for future specialization system".
- **Priorità**: P3
- **Scope**: audit di eventuali round futuri che potrebbero riattivare la feature; documentazione formale della semantica in `equipment/README` (se creato).
- **Non fare**: rimuovere il codice senza GO PM esplicito; usarlo come SoT R18.4 (esplicitamente escluso da SQ2).
- **Status**: BACKLOG

---

### [BACKLOG] R18.4.backlog — berserker/assassin dormant signature items
- **Aperto**: 2026-07-06
- **Origine**: R18.4 Phase B1 Deep-Dive Audit + Phase B2 SQ4 lock
- **Obiettivo**: rivalutare lo status dei 2 items signature `spec_signature_bloodied_greataxe` (req=berserker) e `spec_signature_silent_kris` (req=assassin), attualmente de-facto unusable (0 adventurer live per berserker/assassin post-reset R18.Reset.1b).
- **Motivazione**: mantenere metadata dormant (SQ4 opzione a) evita perdite di dati storici del catalog; rivisitazione richiesta quando/se berserker/assassin verranno unlockati in round dedicati.
- **Priorità**: P3
- **Scope**: audit periodico (ogni ~3 round) dello status delle classi dormant + policy per gli items associati (mantenere / disattivare / riassegnare classe).
- **Non fare**: rimuovere gli items dal catalog, disattivarli (`is_active=false`), cambiare `required_class_optional`, o unlockare le classi target senza GO PM esplicito.
- **Status**: BACKLOG

---

### [BACKLOG] R18.Backlog — Seed Idempotent Timestamp Churn Noise
Origine: R18.3e Phase B W1 investigation (delta items +5 post-B2)
Obiettivo: evitare o ridurre churn non necessario su collezioni seedate quando un hot-reload backend riesegue seed idempotenti.
Priorità: P3
Status: BACKLOG

---

### [BACKLOG] R18.Backlog — Dungeon Label i18n Consistency Review
Origine: R18.3e Phase B WARN 3 (tester browser rilevò dungeon label IT nonostante scelta i18n EN)
Obiettivo: allineare comportamento i18n frontend sui dungeon label (rispettare la lingua selezionata dall'utente).
Priorità: P3
Status: BACKLOG

---

### [BACKLOG] R18.Tooling — DryRun/Apply Path Readiness Gate
Origine: R18.3e Phase B W3 (apply_real() stub scoperto in fase apply reale)
Obiettivo: policy che i sibling script dry-run debbano dichiarare esplicitamente nel gate pre-apply se il write path è implementato o stubbed, evitando scope drift durante l'apply reale.
Priorità: P3
Status: BACKLOG

---

### [BACKLOG] R18.3e — Canonical IT ↔ Legacy EN Class Bridge
Origine: R18.3d Phase B Q10.b + verifica e1_tester (canonical 27 IT vs live 16 EN legacy quasi disgiunti)
Obiettivo: mappare legacy live EN verso canonical IT; decidere se usare `alias_target`, `canonical_slug`, o migration vera.
Vincoli: NO recruitment change senza approvazione PM. NO runtime fields change senza PM.

Esempi da valutare in quel round (draft, NON applicati):
  warrior     → guerriero
  rogue       → ladro
  mage        → mago
  priest      → paladino OPPURE classe legacy da dismettere (decisione PM)
  ranger      → cacciatore_di_mostri
  warlock     → cacciatore_del_vuoto
  monk        → monaco
  druid       → druido
  bard        → bardo
  alchemist   → alchimista
  necromancer → negromante

Priorità: P2 (blocker prerequisito per R18.4 se R18.4 tocca item class-bound player-facing)
Status: BACKLOG

---

### [BACKLOG] R18.Tooling.AuditEventIdempotencyKey
- **Aperto**: 2026-07-05
- **Origine**: WARN M3 regression `R18.Reset.1b.hotfix.v1_3` — l'audit event `R18_FULL_GUILD_FRESH_START_APPLIED` risulta emesso 2 volte (una da REAL APPLY v1.1 subsequently rolled-back, una da v1.2 apply).
- **Obiettivo**: evitare eventi base duplicati nei round massivi tramite idempotency key esplicita per singolo apply logico.
- **Motivazione**: cosmetico, non-blocking (audit è append-only, i due record hanno metadata.apply_id diversi, ma il singolo `event_type` cumulativo può confondere consumer downstream).
- **Priorità**: P3 (cosmetico)
- **Scope**:
  - definire schema `idempotency_key` sui doc audit_log (es. `event_type + metadata.apply_id`)
  - unique compound index opzionale + guardia applicativa nei writer
  - migration script per popolare la chiave sui doc storici
- **Non fare**: dedupe distruttivo sui record storici senza esplicito GO PM.
- **Round dedicato**: da schedulare come `R18.Tooling.AuditEventIdempotencyKey` (round tooling separato).

---

### [BACKLOG] R18.Backlog — Migration Banner State Schema Review
- **Aperto**: 2026-07-05
- **Origine**: WARN 1 emerso durante il **REAL APPLY v1.2** e confermato durante il testing R18.Reset.2. Il flag di stato del migration banner (`r18_reset1b_banner_dismissed`) è correttamente persistito e restituito da `GET /api/guilds/me/r18-reset-banner`, ma **non è esplicitamente esposto nella response di `GET /api/guilds/me`** in modo strutturato all'interno di uno schema Pydantic tipizzato (arriva come chiave "flat" nella response dict).
- **Obiettivo**: consolidare uno schema Pydantic dedicato per lo stato dei banner (migration + fresh-start reset) esposto da `GET /api/guilds/me`, così che il frontend possa consumarlo senza ricorrere a lookup su chiavi dinamiche.
- **Motivazione**: coerenza contract API, riduzione rischio drift schema tra frontend e backend, base per futuri banner (multi-banner state).
- **Priorità**: P3 (cosmetico / documentale, non-blocking)
- **Scope**:
  - definire modello `GuildBannerState` con campi `r18_reset1b_banner_dismissed: bool`, `r18_reset1b_banner_dismissed_at: str | None`, futuri banner nested
  - integrare come sub-object opzionale nel response schema di `GET /api/guilds/me`
  - test di contract: response schema validato con Pydantic + snapshot test frontend
- **Non fare**: rimuovere il field "flat" `r18_reset1b_banner_dismissed` dalla root del doc guild (breaking change per client esistenti).
- **Round dedicato**: da schedulare come `R18.Backlog.MigrationBannerStateSchemaReview` quando prioritizzato.

---

### [BACKLOG] R18.3d.followup — Bard Role Drift Resolution
- **Aperto**: 2026-07-05
- **Origine**: R18.3d Phase B — decisione PM Q8 ("lascia drift e documenta"). Il documento live `adventurer_classes` per la classe `bard` ha `role="Support"`, valore che **non è incluso** nel set canonico `VALID_ROLES=(Tank, DPS, Healer)` definito in `backend/app/admin/services.py:19`.
- **Obiettivo**: convergere il valore `bard.role` sul set canonico o espandere formalmente `VALID_ROLES` includendo "Support", risolvendo il drift storico.
- **Motivazione**: coerenza contract admin (validation `POST /api/admin/classes` blocca upsert con role fuori VALID_ROLES ma il doc esistente vive in drift), leggibilità API pubblica (frontend `RoleMarker.jsx` gestisce già "Support" come marker ma senza garanzia backend).
- **Priorità**: P3 (documentato, non-blocking; il drift è preesistente a R18.Reset.1b e non impatta 3360 adventurers starter post-reset).
- **Scope opzioni**:
  - (a) `db.adventurer_classes.update_one({"slug":"bard"}, {"$set":{"role":"Healer" o "DPS"}})` — richiede regenerazione snapshot `class_role` sugli adventurers Bard esistenti (~0 live, bard non è nelle 11 safe).
  - (b) Espansione `VALID_ROLES` includendo "Support" — impatto trasversale admin/formulas/pvp; richiede audit dedicato.
  - (c) Introduzione secondary field `role_display_it` (già in R18.3d Phase B) come workaround player-facing senza cambiare `role` runtime.
- **Non fare**: modificare `role` in autonomia senza GO PM esplicito; il registry R18.3d documenta il drift con `role_atomic_candidate` hint + `drift_flag`.
- **Round dedicato**: da schedulare come `R18.3d.followup.BardRoleDriftResolution`.

---

### [BACKLOG] R18.Backlog — Dungeon Locked Status Code Consistency Review
- **Aperto**: 2026-07-05
- **Origine**: WARN 2 emerso durante regression check R18.Reset.1b.hotfix.v1_3. Il flusso `POST /api/expeditions` con dungeon locked per gate di livello restituisce **HTTP 403 Forbidden** in alcuni percorsi vs **HTTP 423 Locked** in altri, senza uno standard consolidato lato server.
- **Obiettivo**: allineare tutti i percorsi runtime al codice REST semanticamente corretto (**423 Locked** per gate funzionali su risorsa non pronta, **403 Forbidden** solo per accessi vietati da policy/permission).
- **Motivazione**: chiarezza contract REST, robustezza retry-strategy lato frontend (423 → il client sa che è una condizione temporanea, non un permesso mancante).
- **Priorità**: P3 (cosmetico contract, non-blocking; le response text sono già informative).
- **Scope**:
  - audit di tutti i handler expedition/dungeon per identificare i punti di ritorno 403 vs 423
  - convergenza sul codice `423 Locked` con message body `code=DUNGEON_LOCKED` e context (`min_level`, `owner_level`, ecc.)
  - regression suite: test dedicati per verificare 423 su locked flow, 403 preservato solo per ownership violation
- **Non fare**: cambiare il codice in flussi non-expedition prima di analisi impatto (potenziale rottura client mobile).
- **Round dedicato**: da schedulare come `R18.Backlog.DungeonLockedStatusCodeConsistency` quando prioritizzato.

---

## Backlog risolti (mantenuti per tracciabilità)

Vuoto.

---

## Nuovi backlog P3 aperti in R18.4.followup Phase C (2026-07-06)

### [BACKLOG] R18.backlog — phase14_* legacy regression debt cleanup
- **Aperto**: 2026-07-06 (durante R18.4.followup Phase C, chiude Nota 2 del PM)
- **Origine**: durante regression Phase B+C sono stati rilevati **10 test PRE-ESISTENTI failing** nella suite `phase14_*` (`backend_phase14_4_round15_test.py`, `backend_phase14_6_round3ab_test.py`).
- **Cause identificate**:
  - **Password policy stale**: alcuni test usano password `12345678` che non passa più la validation aggiornata (`_make_user_with_guild` builder legacy).
  - **Path count congelato**: `test_path_count_now_45` si aspetta 86 paths ma il codebase attuale ne ha 275 (crescita normale post round 14–18).
- **Non correlati a R18.4/followup**: verificato che il fail esiste anche pre-Phase B/C (git blame + timestamp). Nessuna modifica in Phase B o Phase C ha aggravato o causato questi drift.
- **Priorità**: **P3** (test stale, non impatta runtime; regression coverage attivo garantito da suite più recenti).
- **Scope**:
  - refactor helper `_make_user_with_guild` in `backend_phase14_4_round15_test.py` per usare password conforme alla policy corrente
  - refresh dello snapshot `path_count` in `backend_phase14_6_round3ab_test.py` al valore attuale del codebase
  - opzionale: convertire il path count check in soft-assert (soglia minima) per evitare stale drift a ogni nuovo endpoint
- **Non fare**: modificare la logica applicativa; è solo debito di test stale.
- **Round dedicato**: da schedulare come `R18.backlog.phase14_legacy_test_cleanup` quando prioritizzato.

---

## HOLD (in attesa di GO PM)

- `R18.1 drift`
- ~~`R18.3d Stat/Role Mapping Registry`~~ → **CLOSED & SEALED 2026-07-05 (documental-only, no DB apply)**
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`
- `orbus.seed_round5.base_strength` warning (P3, HOLD by PM directive)
