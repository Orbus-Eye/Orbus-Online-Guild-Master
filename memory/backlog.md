# Orbus Backlog

Formato: `[STATE] <round_ref> — <titolo breve>`
Origine di verità dei backlog aperti dei round R18.*.

---

## Backlog aperti

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

## HOLD (in attesa di GO PM)

- `R18.1 drift`
- `R18.3d Stat/Role Mapping Registry`
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`
- `orbus.seed_round5.base_strength` warning (P3, HOLD by PM directive)
