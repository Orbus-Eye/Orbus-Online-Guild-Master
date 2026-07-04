# Orbus Online — World Roadmap

**Status**: living document. Solo Phase 1 in esecuzione (R16.3). Le fasi 2→8 sono in scope FUTURO e NON vanno implementate prima dell'approvazione esplicita per ogni round.


---

## R18 — Progression Rework (nuova sequenza — aggiornata 2026-07-04 in R18.1.1)

Il PM ha espanso lo scope R18 con nuova visione: Lv 60, 100 dungeon, 20 raid, 15 classi canoniche, class-bound, Tomi/Maestria, Grade Common→Legendary. Vedi documento dedicato **`/app/memory/round18_progression_rework_roadmap.md`** per le 12 sezioni di material decisionale.

| Fase | Status | Scope sintetico |
|---|---|---|
| **R18.0** | ✅ CLOSED | Audit adventurer/classes/items/schema |
| **R18.0b** | 🔜 PENDING (audit-only) | Class Canon & Archetype Audit — identificare le 15 classi canoniche vs sottoclassi/rami talento |
| **R18.1** | ✅ CLOSED | Schema Foundation & Backfill (91 orfani, aliasing 6, grade backfill 2131, roster cap, talent scaffolding) |
| **R18.1.1** | ✅ IN PROGRESS | Safety Hotfix (canonical roster cap `max(level, guild_level, 1)`) + guard `recruit_unassigned` su expedition dispatch + roadmap expansion |
| **R18.2** | ⏸ WAITING R18.0b | Talent Tree Engine Schema + Beta UI (no talenti reali, solo engine) |
| **R18.3** | ⏸ WAITING R18.2 | Training Fields + Class Choice + Class Mastery + Tomes drop |
| **R18.4** | ⏸ WAITING R18.3 | Grade System (Common→Legendary) + Class-Bound Item Soft/Hard Migration (5 fasi) |
| **R18.5** | ⏸ WAITING R18.4 | PWR Solo-Equip + XP Curve Lv60 (3 varianti) + Item Tier Rework (2 modelli) |
| **R18.6** | ⏸ AUDIT-ONLY | Dungeon/Raid Content Rebalance Plan (23 dungeon + 3 raid attuali) |
| **R18.7** | ⏸ HEAVY LIFT | Large Content Expansion: 77 nuovi dungeon + 17 nuovi raid |

**Prossimo brief richiesto:** R18.0b — Class Canon & Archetype Audit (audit-only, 1-2 giorni). Motivazione: R18.2 talent tree design dipende dal N esatto di classi canoniche. Vedi `round18_progression_rework_roadmap.md` §2 e "Raccomandazione prossimo step".

---

## Phase 1 — World Boss V1 Alveora *(R16.3, CLOSED ✅ 2026-07-01)*

**Goal**: introdurre il primo evento cooperativo globale a tempo — un mega-boss ("Alveora, la Burattinaia della Luna") condiviso da tutte le gilde. Le gilde inviano squadre per contribuire a ridurre l'HP totale entro il timer.

**Componenti chiave**:
- Catalog boss riutilizzabile (`world_boss_catalog`).
- Eventi istanziati (`world_boss_events`) con `status: scheduled|active|resolving|completed|failed|expired`.
- Contributi per squadra (`world_boss_contributions`) + partecipanti gilda (`world_boss_participants`).
- Reward pool con tier top-10 / partecipazione / fallimento (`world_boss_rewards`).
- Resolution idempotente CAS-protected + on-visit fallback + script CLI recovery.
- 3 fasi narrative con threats crescenti (I Fili si Tendono → La Sinfonia dei Fili → Il Sorriso della Luna Morta).
- UI mobile-first: `/world-boss`, `/world-boss/:id`, `/world-boss/:id/report`.
- Admin controls create/start/resolve/recover.

**Prerequisiti**: sistema counter/threat esistente (R16.0 P4), audit log (R16.A P2), on-visit fallback pattern (R16.1.1).

**Rischi P2W**: nessuno. Reward = event currency non-monetizzabile + oro pool. Nessun item leggendario diretto.

**Note**: threats nuovi `mind_control`, `puppet_minions`, `moon_phase` — mappati a counter esistenti tramite `THREAT_COUNTER_MAP` locale nel modulo (no modifica seed R16.0). Aggiunto counter `counter_mind_control` come nuovo tag (append-only).

---

## Phase 2 — Mondo & 8 mastocontinenti *(R16.3, CLOSED ✅ 2026-07-01)*

**Stato**: sigillato post-verifica `e1_tester` 4/4 PASS. WARN filtro `is_active` sui continenti pubblici confermato come design.

**Goal**: mappare il mondo su 8 continenti tematici. Ogni gilda sceglie il proprio continente d'ancoraggio DOPO aver completato il primo raid.

**Componenti chiave**:
- Catalog continenti con lore + tag tematici.
- `guilds.continent_slug` + `guilds.continent_chosen_at`.
- Storico trasferimenti (cooldown + costo).
- UI Mondo (mappa testuale + card per continente).

**Continenti (reference)**:
| Slug | Nome IT | Tema | Divinità |
|---|---|---|---|
| `ambash` | Ambash | Magia | (TBD) |
| `velur` | Velur | Reincarnazione | (TBD) |
| `soe` | Soe | Natura | (TBD) |
| `efreto` | Efreto | Elementi | (TBD) |
| `irthe` | Irthe | Morte | (TBD) |
| `nathos` | Nathos | Vita | (TBD) |
| `ergolat` | Ergolat | Vuoto | (TBD, Alveora-connected) |
| `aveol` | Aveol | Ordine | (TBD) |

**Prerequisiti**: Phase 1 completato + almeno un World Boss risolto (per unlock).

**Rischi P2W**: nessuno se la scelta è puramente narrativa/estetica. Attenzione a benefit statistici futuri.

---

## Phase 3 — Eventi continentali & Incarichi di Sede *(R16.3, CLOSED ✅ 2026-07-01)*

**Stato**: sigillato post-verifica `e1_tester` 4/4 PASS. 2 WARN chiariti (level_bonus=15 corretto via `guild_level=4`; presence null risolto rieseguendo reset script post-pytest).

**Componenti**: gilde vicine (proximity map dentro continente), eventi continentali admin-triggered, Incarichi di Sede (entrate passive scalate su lvl gilda + territorio).

**Rischi P2W**: entrate passive devono essere CAP-ped, no premium boost.

---

## Phase 4 — Risorse continentali + classifiche continentali *(R16.3, READY-TO-VERIFY 🟡 2026-07-01)*

**Stato**: Backend + frontend + 30/30 pytest PASS. In attesa E2E `e1_tester` manuale.

**Goal**: introdurre 8 risorse continentali (5 epic + 3 rare) con missioni di gathering usando avventurieri idle, e classifiche continentali V0 read-only.

**Componenti**:
- Catalog 8 risorse (una per continente) con `item_type="material_continental"`, drop rate CONSERVATIVE (3% epic / 5% rare + max +10% event bonus).
- Missioni 30 min / 20 oro cost / team 3 avv idle. CAS resolve + on-visit fallback + CLI recovery.
- Classifiche V0: `resource_gathering_count` + `site_income_total` (7gg rolling, freschezza 24h, top 20).
- Modificatori event `site_income_pct > 0` → +2% drop bonus (cap +10%).
- 11 endpoint (7 public + 4 admin), 5 nuovi audit event UPPERCASE.
- Frontend mobile-first 4 pagine + 2 nav voci.

**Rischi P2W**: zero (costo oro/missione, no accelerazione premium, leaderboard read-only).

**Rischi bilanciamento**: bassi (drop conservativi, market_cap_daily=3 persistito per Phase 6).

---

## Phase 4 — sealing pending E2E *(future once verified)*

---

## Phase 5 — Forgia Leggendaria & Forgia di Arfus *(future)*

**Componenti**: nuove Forge tier avanzate con receipts unlockable via achievement/reputation. Legendary items sbloccabili solo tramite crafting endgame (mai drop diretto). Arfus = Forgia mistica associata a Alveora/Ergolat.

**Rischi P2W**: legendary devono essere `is_tradeable=false` una volta craftati (BOP) per non creare RMT.

---

## Phase 6 — Patti commerciali gilda + specializzazioni gilda *(future)*

**Componenti**: gilda può stipulare patti con altre gilde vicine (bonus scambio market), specializzazione unica per gilda (Mercantile, Militare, Arcanista, Esploratore) con perk asimmetrici.

---

## Phase 7 — PvP continentale *(R16.3, CLOSED ✅ 2026-07-01)*

**Stato**: sigillato dopo doppio ciclo Iter1 Backend + Iter2 Frontend per entrambe le sub-fasi 7A e 7B.

### Phase 7A — PvP 1v1 Continentale
- **Backend**: 33/33 pytest PASS
- Elo K=32 clamp `[800, 2400]`, gate `guild.level ≥ 8`, max 3 sfide attive, cooldown 12h coppia, bracket ±200 Elo, team snapshot 5v5, resolution deterministica `random.Random(battle_id+role)`, on-visit fallback, recovery CLI, Arfus applier filtrato PvP (6 categorie combat_*, cap 50%)
- 6 audit events UPPERCASE + admin whitelist 41 → 47
- **Frontend**: 4 pagine + `PvpMiniCard` + `PvpGuildLevelGate` + battle log narrativo italiano

### Phase 7B — Leaderboard settimanale + Cosmetici
- **Backend**: 31/31 pytest PASS (+ guard-rail leaderboard endpoint parity)
- Snapshot settimanale + rollover on-visit, CAS lock idempotente, 24 cosmetici (8 continenti × 3 tipi: `title` rank1, `badge` rank≤3, `frame` rank≤10)
- Recovery CLI, 3 audit events UPPERCASE + admin whitelist 47 → **50**
- **Frontend**: 3 pagine + `PvpSeasonMiniCard` + nav voce "Stagione PvP" badge NEW + disclaimer anti-P2W ×3

**Rischi P2W**: neutralizzati. Reward = titoli + cosmetici puramente decorativi (test regression `test_26_no_p2w_stat_impact_after_award` asserta immutabilità di `guild.gold/reputation/level/name` e `guild_pvp_stats.elo/wins/losses/draws` dopo award). Nessun buff acquistabile pre-match. Whitelist Arfus PvP taglia effetti non-combat.

---

## Phase 8 V1 — Stalla & Cavalcature (cosmetic-only) *(R16.3, CLOSED ✅ 2026-07-01)*

**Stato**: sigillato dopo doppio ciclo Iter1 Backend + Iter2 Frontend, con 28/28 pytest PASS su `test_stables_phase8_v1.py`.

**Goal**: introdurre un sistema di cavalcature **puramente cosmetico e narrativo** — nessun impatto su combat/economia/ranking/travel time. Cataloghi statici, seed idempotente, feature free-to-earn.

**Componenti chiave**:
- **9 mount**: 1 starter (`ronzino-di-strada`) + 8 domain (uno per continente): scarabeo-runico (ambash), cervo-lunare (velur), lupo-delle-fronde (soe), salamandra-di-efreto (efreto), segugio-cinereo (irthe), remora-tempestosa (nathos), ombra-sellata (ergolat), grifone-delle-alture (aveol)
- **5 rotte narrative** cosmetic-only: sentiero-delle-fronde (soe), via-delle-alture (aveol), traccia-lunare (velur), passo-delle-ceneri (efreto), cammino-ombra (ergolat)
- 4 collezioni Mongo con seed idempotenti al lifespan
- **9 endpoint**: 7 pubblici + 2 admin (dev-gated)
- **4 audit events** UPPERCASE: `MOUNT_STARTER_CLAIMED`, `MOUNT_ACQUIRED`, `MOUNT_ACTIVE_SET`, `NARRATIVE_ROUTE_TRAVELED` → admin whitelist 50 → **54**
- **Frontend**: pagina `Stables.jsx` con 3 tab (Le Mie / Catalogo / Rotte Narrative), CTA "Rivendica il Ronzino" (auto-attiva), set-active con deselect (`mount_slug: null`), toast italiani, mini-card Dashboard, nav voce "Stalla" (badge NEW) in sezione Gilda
- **Anti-P2W disclaimer ×2**: box emerald full su Stables page + micro-disclaimer su mini-card

**Rischi P2W**: NEUTRALIZZATI runtime.
- Catalog hardcoded `affects_combat=false`, `affects_economy=false`, `affects_ranking=false`, `affects_travel_time=false`, `can_be_sold_for_real_money=false`
- Anti-drift override nel seed (anche se catalog venisse editato, seed force-sets flags a False)
- Reward rotte limitato a `cosmetic_badge | cosmetic_title | lore_entry` (test 05 + 22)
- Test regression `test_20_no_p2w_stat_impact_after_claim` + `test_21_no_p2w_stat_impact_after_narrative_travel` snapshot BEFORE/AFTER assertano immutabilità di `guild.gold/reputation/level/name` e `guild_pvp_stats.*`
- Zero scritture runtime a `adventurers.stats`, `inventory`, `item_instances`

---

## Phase 8 V2 — Rotte narrative estese + esplorazione dedicata *(FUTURE / DESIGN REVIEW REQUIRED 🔴)*

**Componenti proposti**:
- 3 rotte narrative sui domini non ancora coperti (ambash, irthe, nathos)
- Variante esplorativa opzionale con `-5% travel time` **applicabile SOLO a rotte narrative dedicate**, mai a farm loop di gathering/expedition/mission
- Ricompense sempre cosmetiche

**Rischi P2W**: **richiede design review conservativo** prima dell'implementazione.
- Il `-5% travel time` non deve mai applicarsi a operazioni economiche (gathering, expedition, missione) — altrimenti impatta indirettamente il balance economico
- Nessun sovrapposizione con `world_events.travel_time_bonus`
- Nessuna monetizzazione premium
- Free-to-earn come V1

---

## Note trasversali

- **Idempotenza**: ogni evento con timer DEVE avere CAS lock + on-visit fallback + script CLI recovery, per non ripetere il bug raid stuck (R16.1.1).
- **Localizzazione**: tutti i modelli seedati devono avere sia `name_it`/`description_it` che `name_en`/`description_en`.
- **No hard delete**: soft-delete con `deleted_at` o `is_active=false`. Mai `delete_many` in production.
- **Audit-first**: ogni mutazione critica emette `audit_log` event best-effort.
- **Backward compatibility**: append-only sui seed R16.0 (dungeons, threats, counters, classes).

---

*Ultimo aggiornamento: 1 luglio 2026 — R16.3 Phase 1..6 CLOSED ✅ · **Phase 7A CLOSED ✅** (Backend 33/33 + Frontend + gate lvl8 + Arfus PvP whitelist) · **Phase 7B CLOSED ✅** (Backend 31/31 + Frontend + 24 cosmetici + disclaimer anti-P2W ×3) · **Phase 8 V1 CLOSED ✅** (Backend 28/28 + Frontend + 9 mount + 5 rotte narrative + anti-P2W ×2). **Round 16.3 OFFICIALLY CLOSED ✅**. Phase 8 V2 (`-5% travel time` esplorativo) parked in attesa design review conservativo anti-P2W. Vedi `/app/memory/round163_final_report.md` per il consolidamento finale.*

---

## Round 16.5 P0 — CLOSED (2026-07-01)

- Fasi: P0.1 (dry-run) + P0.2 (apply DB) + P0.3 (wiring runtime) + P0.3-D2 (rimozione fallback difficulty)
- Test: 23/23 passed su `orbus_r16_test`
- Problema utente originale (team lv4 → dungeon lv7) risolto e verificato
- Report finale: `/app/memory/round165_p0_final_report.md`
- Snapshot rollback: `/app/memory/round165_p0_prechange_snapshot.json` (sha256 `a028743e…`)

## Round 16.5.1 — CLOSED ✅ (2026-07-02)

Sigillo definitivo dopo doppio pass `e1_tester` + fix E2 (CSRF Tester
Tools UI) + fix F2 (i18n bottoni Tester Tools).

- **FASE A** (fallback D2): rimosso fallback difficulty, 3 test aggiunti, Round 16.5 P0 CLOSED
- **FASE B.1**: world_events extension — GET/PATCH/deactivate/duplicate endpoints (estensione, no nuova collection)
- **FASE B.2**: Tester Tools — status/grant/set-max/set-min con guardrail rinforzati + audit + snapshot
- **FASE B.3**: raids/last + raids/replay-preview (backend pronto, UI dashboard integration deferita a R16.5.2)
- **FASE B.4**: raid countdown remaining_seconds server-side (osservato live decrement 16m 45s → 16m 33s)
- **FASE E2** (2026-07-02): `AdminTesterTools.jsx` refactored a wrapper condiviso `lib/api.js` — cookie auth + double-submit CSRF header auto-injection. 2 nuovi test backend (`test_E2_csrf_reject_when_cookie_auth_and_no_header`, `test_E2_csrf_accept_when_header_matches_cookie`). Difesa CSRF backend NON abbassata.
- **FASE F2** (2026-07-02): i18n bottoni Tester Tools — 3 label italianizzate (`Dai avventurieri al tester`, `Set tester MAX`, `Set tester MIN`). Stringhe minori residue → backlog R16.5.2 item 5.
- **Test**: 20/20 backend passed su `orbus_r16_test` (isolated port 8002)
- **Frontend**: lint OK, webpack compile OK
- **Report finale**: `/app/memory/round1651_final_report.md` (sezione "Sigillo finale")
- **Deferred esplicito** (non blockers, tracked in `/app/memory/backlog.md` R16.5.2):
  - Admin F5 blank-screen (item 1)
  - Client-side guard `/admin/tester-tools` (item 2)
  - `AdminWorldEvents.jsx` allineamento wrapper (item 3)
  - Hook `useAdminGuard()` condiviso (item 4)
  - Stringhe residue admin (item 5)
- **Guardrail rispettati**: no balance change, no P2W, no hard delete, no toccati modifiers/reward/economia, no rimozione difese CSRF backend.

## Round 16.5.3 — CLOSED & SEALED ✅ (2026-07-02)

Core loop fixes: P0.1 raid gate + P0.2 activity sweep + P1 Guild XP V1 + I2 label micro-fix.

- **P0.1** Raid gate visibility & enforcement — audit ha rivelato che il fix era già al 90% presente. Micro-fix: aggiunto `dungeon_slug` al payload d'errore `underleveled_squad` in raid.preview + raid.start. Mapping confermato: tier1→8, tier2→12.
- **P0.2** Sweep unificato `sweep_activities_for_guild` nuovo helper in `app/core/activity_sweep.py`. Chiama best-effort expedition + raid recovery + resource mission resolver. Agganciato a `GET /api/adventurers`, `GET /api/roster/health`, `GET /api/guilds/me`. Latency <30ms (0 attività) / ~80ms worst-case.
- **P1** Guild XP "Prestigio di Gilda" V1 bare-minimum — nuovo modulo `app/achievements/xp_hooks.py`. 3 drip hooks: expedition (+15/+5, cap 8/day), raid (+80/+40/+15, cap 1/day), resource mission (+10, cap 6/day). Nuova collection `guild_xp_daily_cap_tracker` con unique index. Idempotenza via activity_id + `db.audit_log`. Nessun backfill retroattivo. Frontend: card "PRESTIGIO DI GILDA" (label italiana) con sezione "COSA FARE PER SALIRE" statica V1.
- **I2** Label micro-fix (chiusura, 2026-07-02): risolto ambiguità `guild.level` legacy vs `prestige_level`. `GuildProgressCard.jsx`: `LIVELLO` → `LV PRESTIGIO`, `XP` → `XP Prestigio`. Nessun cambio logica. Le ~10 occorrenze "Livello Gilda" in Forge/Spec/PvP/Arfus restano invariate (riferite al guild.level legacy, semanticamente corrette).
- **Test**: 12/12 backend passed su `orbus_r16_test` (isolated port 8002)
- **Frontend**: lint OK, webpack compile OK
- **Deferred a R16.5.4** (Guild XP V2 Extended): 7 hook rimanenti (continental event, daily/weekly contract, structure upgrade, guild spec, trade pact, PvP battle) — vedi `/app/memory/backlog.md`.
- **Report finale**: `/app/memory/round1653_final_report.md` (con sezione "Label micro-fix" + firma SEALED)
- **Guardrail rispettati**: no balance change, no P2W, no hard delete, no toccati XP avventurieri/reward/drop/PvP/Stalla/economia, no rimozione difese CSRF/gate, no unificazione livelli.

### Backlog aperto (ordine suggerito per prossimi round)

1. **R16.5.4** — Guild XP V2 Extended Hooks (P2) — 7 hook rimanenti al sistema Prestigio.
2. **R16.5.2** — Admin Polish (P3) — 5 item tracciati (F5 blank, guard client-side, AdminWorldEvents axios raw, useAdminGuard, stringhe residue).
3. **Territory `KeyError: 'library'`** — audit indipendente (P2) — visibile nei log su `GET /api/territory/me`.
4. **R16.5.5+ (opzionale)** — Unificazione terminologia `guild.level` vs `prestige_level` — pianificare con cautela (impatti gate Forge/Spec/PvP/Arfus/TradePact).

Scope: unificazione UX/tecnica delle pagine admin. Vedi
`/app/memory/backlog.md` sezione "Round 16.5.2 — Admin Polish"
per l'elenco dettagliato dei 5 items. Nessun cambio funzionale.
Vincoli: no modifiche a balance/reward/drop/XP/PvP/economia.
Attesa decisione utente per apertura.


## Round 16.5.4a — Password UX Fix CLOSED ✅ (2026-07-02)

Micro-fix registrazione con policy password strutturata + checklist dinamica FE.

- **Policy Q1-C**: 8 char + 1 maiuscola + 1 numero + 1 speciale (era 8+letter+digit).
- **Backend**: `app/core/security.py` — nuovo `validate_password_strength()` con payload strutturato `{code:"password.requirements_not_met", user_message: "…"}` (400). Applicato a `/api/auth/register` + `/api/auth/password-reset/confirm`. Login invariato (retro-compat utenti esistenti).
- **Frontend**: nuovo helper `lib/passwordPolicy.js` (mirror validator BE) + nuovo componente `PasswordChecklist.jsx` (4 righe live, ✓/✗). Integrato in `Register.jsx` + `PasswordResetConfirm.jsx` con submit disabled finché policy KO.
- **Test**: 8/8 PASS (5 password matrix + missing_special + change-password + login retro-compat) su `orbus_r16_test`.
- **Report**: `/app/memory/round1654a_password_ux_report.md`
- **NESSUNA modifica**: login, sessioni, cookie, CSRF, JWT, DB, endpoint.

---

## Round 16.5.4b — Auto-Equip Class-Aware CLOSED & SEALED ✅ (definitivo, 2026-07-02T20:11Z)

> **Status**: Sigillo definitivo dopo REOPEN #2 chiuso via `e1_tester` browser (M1). 23/23 test PASS + 3/3 test browser PASS (UI refresh Warrior Lv10, Warning-only skip Mage, Warrior regression).

BLOCCO A (auto-equip class-aware fix) + BLOCCO B (ADJ-2 seed integrity Legendary required_level) + REOPEN #1 (verifica live end-to-end + fix 2× `NameError` + HTTP E2E test) + REOPEN #2 (UI stale onChanged + warning-only skip Q2-b(iii)).

- **Root cause originale**: formula fitness leggeva `item['stats']` (dict inesistente) → ranking degenerato a solo `power_score`; level gate leggeva campi legacy inesistenti; `item_equip_power` locale ignorava i `*_bonus`.
- **Fix formula**: `PRIMARY_WEIGHT=3.0 · SECONDARY_WEIGHT=1.5 · POWER_WEIGHT=1.0 · STAT_TAG_BONUS=2.0 · WARNING_PENALTY=0.5`. Sort tie-break totalmente deterministico.
- **ADJ-2 backfill**: 6 Legendary con `required_adventurer_level` a valore corretto (sword/staff=9, altri=8). Script `round1654b_seed_integrity.py` dry-run+apply idempotente con snapshot rollback.
- **REOPEN fix 2× `NameError`** (`grammar_it`, `class_it_short`) — 2 righe in `auto_equip.py`.
- **Test**: 23/23 PASS (11 unit auto-equip + 5 unit backfill + 3 HTTP E2E + 4 REOPEN #2 warning-skip) su `orbus_r16_test`.
- **e1_tester browser**: REOPEN #1 6/6 PASS. REOPEN #2 in attesa di verifica browser dopo Q2-b(iii).
- **REOPEN #2 fix chiave**:
  - FE: `Adventurers.jsx` — nuovo `reloadAndRefreshSelected` + `onChanged` prop → modale rinfrescata senza reload.
  - BE: `auto_equip.py` — Auto-Equip **SCARTA** severity=warning (regola PM Q2-b(iii)); empty state IT differenziato con `off_class_seen` counter.
- **Report**: `/app/memory/round1654b_final_report.md` (con sez. 18 REOPEN + Sigillo CLOSED & SEALED)
- **Audit**: `/app/memory/round1654b_audit_report.md`
- **Snapshot ADJ-2**: `/app/memory/round1654b_adj2_snapshot.json`
- **Bug adiacenti tracciati per R16.5.4c**: ADJ-9 [P1] class_slug backfill (94% avventurieri), ADJ-3 [P1] warlock/alchemist zero item, ADJ-1 [P2] rarity case mismatch, ADJ-6 [P3] audit entity_id, ADJ-7 [P3] except generico che mangia 423.
- **NESSUNA modifica** a drop/reward/PvP/economia/premium/stat item; zero hard delete; solo `required_adventurer_level` toccato sui 6 Legendary target.

---

## Round 16.5.4d — Mobile Expedition Rewards & Guild Prestige — CLOSED & SEALED ✅ (2026-07-03)

> **Status**: sigillato 2026-07-03T12:45:00Z (opzione A PM). 4/4 TC accepted (mobile 390/375 padding, dashboard Prestigio-first, desktop). 3 fix consegnati: mobile `pb-24 sm:pb-8` su ExpeditionReport, 10+ stringhe IT hardcoded, Dashboard con `LIVELLO` legacy nascosto + copy Prestigio dinamico. Screenshot in `/app/memory/round1654d_viewports/`. Follow-up: R16.5.4e (Territory KeyError) e R16.5.4f (Localization Sweep) tracciati in backlog.

## Round 17.0 — Game Systems Refoundation Audit — COMPLETED ✅ (2026-07-03)

> **Deliverable consegnati**: `/app/memory/round17_refoundation_audit.md` + `round17_appendix_queries.md`. Roadmap R17.1 → R17.2 → R17.3 approvata dal PM.

## Round 16.5.4e — Territory KeyError Hotfix — CLOSED & SEALED ✅ (2026-07-04)

> **Status**: sigillato 2026-07-04T08:00:00Z. Fix difensivo `get_structure_max_level`. 6/6 pytest verde. WARN log live confermato.

## Round 17.1 — Onboarding & First Player Success — CLOSED & SEALED ✅ (2026-07-04T10:45Z)

> **Status**: sigillato definitivo 2026-07-04T10:45Z (validazione Playwright TC2 accettata dal PM). Mini-fix pre-sealing completato (audit whitelist + UI fallback reward + browser check Playwright). Deliverable: `/app/memory/round171_final_report.md` (16-point PM sealing checklist).
>
> **P0 delivered**:
> - `training-yard` starter dungeon seedato (idempotent boot hook).
> - `FirstObjectiveCard` in Dashboard + `?starter=training-yard` handler in `/dungeons`.
> - 10 FIRST_* audit events emessi da `emit_first_event` con idempotency guard per gilda.
> - Fallback reward primo fallimento starter: +5 gold + +5 XP Prestigio + audit `STARTER_FALLBACK_REWARD_GRANTED`.
> - **Mini-fix (2026-07-04)**:
>   - `AUDIT_EVENT_WHITELIST` include i 10 R17.1 event types → admin filter enabled.
>   - `GET /api/expeditions/{id}` espone `fallback_reward` (read-only derivation).
>   - Frontend banner IT `:: LEZIONE APPRESA` con testo esatto + `+5 oro` + `+5 Prestigio di Gilda`.
>   - Playwright browser check PASS (screenshot `/app/memory/round171_fallback_banner.jpeg` + `_mobile.jpeg`).
>
> **Test**: 13/13 pytest R17.1 PASS (4 whitelist + 9 fallback logic+UI). Regression `tester@orbus.test` invariata.
>
> **Warning tracciato non-blocker**:
> - `FIRST_PRESTIGE_GAINED` 0 record (whitelist ok, event non ancora triggerato da player reali) — monitorare in R17.1b/R17.2.
>
> **Bug residui non bloccanti**:
> - SMTP `@orbus.test` refused (P2, tracciato `R17.infra.smtp`).
> - `result_log` post-fail in inglese sotto il banner IT (deferrato a R17.1b P0).
>
> **Deferred to R17.1b (aperto in backlog, non ancora iniziato)**: localizzazione IT result_log/summary/equipment_delta, prominenza label Prestigio, milestone toasts, polish primo report, mobile readability check, CTA "Riprova con team più forte".

---

## Round 17.1b — Onboarding Polish & Report Localization — CLOSED & SEALED ✅ (2026-07-04T12:35Z)

> **Status**: sigillato definitivo 2026-07-04T12:35Z (2/2 E2E PASS post-fix TDZ accettati dal PM). Include mini-fix BLOCKER TDZ e fix root-cause `FIRST_PRESTIGE_GAINED`. Deliverable: `/app/memory/round171b_final_report.md`.
>
> **Test**: 13/13 pytest R17.1 PASS · milestone toasts audit-verified (FIRST_EXPEDITION_STARTED/COMPLETED/PRESTIGE_GAINED 1/1/1 per fresh guild) · Playwright desktop+mobile PASS · fix TDZ verified con 0 console errors.
>
> **Follow-up non-blocker**: CTA class-fit balancing (P2, tracciato R17.1c/R17.2 P2) · FIRST_PRESTIGE_GAINED legacy non retroattivo (accettato).

---

## Round 17.2 — World Content Activation (Path A) — CLOSED & SEALED ✅ (2026-07-04T14:20Z)

> **Status**: sigillato definitivamente 2026-07-04T14:20Z (PM approva A+i post-hotfix Auto-Equip UI parity + `e1_tester` accepted). Deliverable: `/app/memory/round172_final_report.md` (14-point checklist + hotfix regressione UI + sezione CLOSED & SEALED).
>
> **Scope Path A** (post-audit pivot approvato PM Msg 280):
> - **P0.1** Achievements audit — `/achievements` render OK (110 catalog in DB verificati). No re-seed necessario.
> - **P0.3** Resource Missions Path A — durata 780s (13m), cap 6/gilda/giorno, cooldown 1/continente/giorno, gate Prestigio Lv2, reward +8 rare / +10 epic XP Prestigio idempotent.
> - **P1** Prestige next-unlock tooltip — mapping dinamico Lv5 Forgia Leggendaria / Lv6 Forgia di Arfus / Lv8 Specializzazione della Gilda (import runtime da `MIN_GUILD_LEVEL`).
> - **Hotfix Auto-Equip UI parity** — bottone "Auto-Equipaggia" ora presente sia nel modale (`AdventurerDetailModal.jsx`) sia nella pagina dedicata (`AdventurerEquipment.jsx`). Regressione UX preesistente pre-R17.1, non causata da R17.2.
>
> **Test**: 13/13 pytest R17.1 PASS (regression). Playwright screenshot: `round172_{achievements_audit, prestige_tooltip, resources_stats, hotfix_autoequip_btn, hotfix_autoequip_click}.jpeg`.
>
> **Guardrail rispettati**: NO hard delete, NO migration DB, NO modifiche a drop/reward/PvP/premium/economia, NO refactor.

---

## R17.3 — Endgame & Class Depth — Step 2 CLOSED & SEALED ✅ (2026-07-04T16:00Z)

**Status**: Step 2 sigillato definitivamente. Deliverable: `/app/memory/round173_step2_report.md` (14-point checklist + hotfix + CLOSED & SEALED).

**Consegne sigillate**:
- ✅ D Tooltip Prestigio Lv 2/5/6/8 — sorgente unica `MIN_GUILD_LEVEL`
- ✅ C1P1 Class coverage 20 item bucket-safe · idempotenza confermata · Auto-Equip E2E PASS
- ✅ E CTA class-fit `?auto=classfit` con role mapping 14 classi
- ✅ T-A CTA testo "squadra bilanciata"

**R17.3 Step 3**: DEFERRED indefinitely — PM apre R18.0 rework macro prima.

---

## R18.0 — Adventurer Identity, Class Mastery & Progression Rework — OPEN (audit-only) 🔍 (2026-07-04T16:10Z)

**Status**: aperto audit READ-ONLY. NO implementazione. NO modifica codice/DB/seed. Solo dati + feasibility + rischi.

**Deliverable**:
- `/app/memory/round180_adventurer_rework_audit.md` — 17 sezioni
- `/app/memory/round180_adventurer_rework_raw_data.json` — dati raw

**Scope visione**: adventurer Common/Recluta → training field → 15 classi canoniche + talent tree + mastery + tomi + PWR solo equip + item class-bound + grado Common→Legendary + roster 50 + rework dungeon/raid.

**Vincoli tassativi**: NO implementazione · NO modifica codice/DB/seed · NO hard delete · NO balance/drop/reward/PvP/economia/premium · SOLO audit.

**Prossimo step**: PM legge → prende decisioni design → apre R18.1/R18.2/R18.3/R18.4 (roadmap 4 round tematici).

---

## R17.3 — Step 2 pre-sealing archived (superato)

**Step 1 (audit-only)**: `/app/memory/round173_step1_audit.md` ✅ CLOSED

**Step 2 (D + C1P1 + E)**: `/app/memory/round173_step2_report.md` ⏳ **CLOSED pre-sealing** — awaiting `e1_tester` E2E validation prima del sealing formale.

**Consegne Step 2**:
- ✅ **D** Tooltip Lv2 → mapping esteso Lv 2/5/6/8 (Missioni Risorse + Forgia Leg + Arfus + Spec). Sorgente unica `MIN_GUILD_LEVEL` da 4 moduli.
- ✅ **C1P1** Class coverage patch (20 item, bucket 1/3/5/8, P-A approvato): monk accessory 1→5, warlock 4/3/3→6/6/6, alchemist 4/3/3→6/6/6. Snapshot `round173step2_c1p1_snapshot.json` sha256=`ee3e5d47…`. Idempotenza confermata.
- ✅ **E** CTA class-fit balancing → `?auto=classfit` in `ExpeditionNew.jsx` con role mapping 14 classi (Tank/Healer/Support/DPS) + fallback graceful. CTA testo IT "Riprova con squadra bilanciata" in `ExpeditionReport.jsx`.
- ✅ **T-A** upgrade testo CTA da "team più forte" → "squadra bilanciata" (grep verify: 0 residui).

**Test**: pytest R17.1 13/13 PASS · Auto-Equip live E2E su 3 classi (monk +11, warlock +6, alchemist +6) · dry-run+apply pattern R16.5.4c rispettato.

**Guardrail**: NO Legendary · NO power creep (verifica programmatica) · NO hard delete · NO modifiche drop/economia/PvP/premium · Solo `db.items.insert_one × 20`.

**Deferred Step 3+**:
- **A** Bridge Raids Lv12-17 (5 raid: sunken-vault, whispering-arboretum, shattered-mint, hollow-choir, starfall-reliquary)
- **B** Endgame Lv15-20 (3 dungeon: void-cradle, moonshadow-crypt, astral-lens) + 10-15 achievement endgame + B1 material sink
- **D** estensioni certezza MEDIA/BASSA (PvP continentale, site contracts, territory) — richiedono audit code path dedicato

---

## Round 17.3 — Endgame & Class Depth — OPEN (Step 1 audit-only) 🔍 (2026-07-04)

> **Status**: aperto Step 1 audit-only 2026-07-04. PM approva "A+i": procedere con audit design PRIMA di qualsiasi apply. Nessun seed, nessuna modifica reward/drop/economia in Step 1.
>
> **Deliverable Step 1**: `/app/memory/round173_step1_audit.md` — 5 audit A→E.
>
> **Scope Step 1** (5 audit da consegnare, no apply):
> - **A. Raid mid-tier Lv5-14** — proposta 5 raid (tabella slug/nome/level/power/durata/reward/materiali/ruoli/note). Progressione Lv5→7→9→11→13. NO power creep vs endgame esistente (broken-bastion-siege pw800, necropolis-bells pw900, dragon-vault pw1400).
> - **B. Endgame Lv15-20** — analisi lacune (dungeon Lv15+? raid endgame da rifinire? reward endgame? Legendary Forge gate?). Elenco lacune + rischi + priorità. NO implement.
> - **C. Class depth / item coverage residua** — tabella coverage per 14 classi (monk accessory=1, warlock=3/3/4, alchemist=4/3/3 sotto soglia). 6 orfani Guardian/Cleric. Proposta item patch se necessaria.
> - **D. Tooltip Prestigio mapping completo** — audit gate reali: territory, raid endgame, forge (già mapped), world, class hall, specializations (mapped), resource missions (Lv2), PvP. Tabella livello/feature/fonte codice/endpoint UI/certezza (alta/media/bassa). Implementa solo certezza ALTA in Step 2.
> - **E. CTA retry class-fit balancing** — algoritmo proposto (pseudocodice): disponibilità + livello + class-fit primary/secondary + ruoli Tank/Healer/DPS + power + requisito dungeon. NO party invalide. Solo suggerimento, NO avvio auto.
>
> **Vincoli tassativi Step 1**:
> - ❌ NO apply seed massivo
> - ❌ NO modifica reward/drop/economia
> - ❌ NO hard delete
> - ❌ NO premium/PvP/Stalla/World Boss touch
> - ❌ NO refactor tecnico generico
> - ✅ SOLO audit / design / proposta / tabelle
>
> **Note**: R16.5.4f Localization Sweep [P3] NON aperto come mini-round separato, tracciato parallelo. PM approverà ogni sub-item (A/B/C/D/E) singolarmente prima del passaggio a Step 2 (apply).
>
> **Prossimo step**: PM review audit → approvazione sub-item singoli → Step 2 (apply mirato, uno per uno).

---

## Round 17.1b — Onboarding Polish — PLANNED 🔜 (superato)

---

## Round 17.1 Step 0 — First Funnel Stabilization — CLOSED & SEALED ✅ (2026-07-04)

> **Status**: sigillato 2026-07-04T08:00:00Z. Preflight R17.1 completo. `FirstObjectiveCard` mounted in Dashboard. Funnel event mapping.

**Interventi chiave**:
- **ADJ-9**: backfill `class_slug` su 1909 avventurieri (94.01%→99.71%), fix `common._generate_candidate` per popolare `class_slug` in write path, 6 orfani Guardian/Cleric documentati.
- **ADJ-3 opzione A approvata dal PM**: 22 nuovi item (Warlock 10 + Alchemist 10 + Druid 2 armor gap), Epic Lv8, no Legendary, no power creep verificato programmatico via `POWER_MAX_BY_BUCKET`. Coverage Warlock/Alchemist: 0/0/0 → 4/3/3.
- **ADJ-1**: 17 item con rarity lowercase normalizzati a Capitalized; nuovo helper `app.shared.rarity.canonicalize_rarity` (27 test unit PASS).
- **P2 (ADJ-3.c)**: fix `auto_equip.py` — no più leak "HTTPException" nei warning player-facing; `_extract_it_message` estrae `user_message` italiano; logger dedicato per errori tecnici server-side.
- **ADJ-6**: verificato già presente in `auto_equip.py`, `equip_item_service`, `unequip_item_service` (fix R16.5.4b).
- **ADJ-7**: 423 `level_gate` ora bubble-up come user_message pulito nel warning (non più mangiato da `except Exception`).

**Test**: 54/54 PASS (27 R16.5.4b/c auto-equip + 27 canonicalizer). Regression curl live Warrior invariata.

**Snapshot**: `round1654c_adj9_snapshot.json` + `round1654c_adj3_snapshot.json` + `round1654c_adj1_snapshot.json`. Audit events emessi.

**File nuovi**: `app/scripts/round1654c_seed_integrity.py`, `round1654c_class_coverage_seed.py`, `round1654c_rarity_normalize.py`, `app/shared/rarity.py`, `tests/backend_round1654c_rarity_test.py`. **Modified**: `adventurers/common.py`, `equipment/auto_equip.py`. Frontend: nessun file toccato.

**Bug residui / tracking per fasi successive**:
- 6 avventurieri orfani Guardian/Cleric (classe non nel catalog) — decisione design pendente.
- Testing E2E browser Warlock/Alchemist non eseguito (tester@orbus.test non ha adv di queste classi).

**Report**: `/app/memory/round1654c_final_report.md`.

---

## Round 16.5.4c — Seed Integrity & Auto-Equip Cleanup PLANNED 🔜

Chiude i buchi di data-integrity + coverage di classi + cleanup Auto-Equip rilevati durante audit e REOPEN #1/#2 di R16.5.4b.

**Lista aggiornata dopo Sigillo definitivo R16.5.4b (2026-07-02):**

### P1 items
1. **ADJ-9** ⭐ Backfill `class_slug` per 94% avventurieri legacy + fix `POST /api/adventurers/recruit`.
2. **ADJ-3** Item pool coverage per Warlock/Alchemist/Druid — seed patch dedicata con `recommended_classes` popolato (weapon+armor+accessory a 5 livelli target).

### P2 items
3. **ADJ-3.c** NEW: "accessory: equip fallito (HTTPException)" nel payload Mage
   - Root cause probabile: except generico che cattura `HTTPException` senza logging pulito.
   - Fix: gestire il caso "nessun accessorio adatto" con reason italiana pulita, no eccezione nel warning.
   - Test dedicato: mage senza accessory class-fit → reason IT pulita, no "HTTPException" stringato.

### P3 items
4. **ADJ-1** Rarity case-mismatch normalization (Legendary vs legendary, 11+ docs).
5. **ADJ-6** Estensione `related_entity_id=adv.id` a `equip_item_service` + `unequip_item_service`.
6. **ADJ-7** Bubble-up 423 level_gate come warning strutturato in `auto_equip`.
7. **NEW** Verifica visiva UI empty state per Druido (branch `off_class_seen=0`).

Vincoli: dry-run+apply obbligatorio per ogni seed patch, snapshot rollback, zero drop/balance/P2W shift, zero hard delete.

