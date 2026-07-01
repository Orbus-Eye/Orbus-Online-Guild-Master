# Orbus Online — World Roadmap

**Status**: living document. Solo Phase 1 in esecuzione (R16.3). Le fasi 2→8 sono in scope FUTURO e NON vanno implementate prima dell'approvazione esplicita per ogni round.

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
