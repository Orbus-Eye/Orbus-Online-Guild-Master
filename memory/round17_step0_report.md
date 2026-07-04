# Round 17 Step 0 — First Funnel Stabilization Report

**Data**: 2026-07-04T07:40Z (UTC).
**Tipo**: preflight R17.1 (max 1 giornata). Include micro-hotfix R16.5.4e.
**Vincoli**: no wizard onboarding pesante · no seed raid/achievements · no balance/reward · no hard delete · no premium/PvP.

---

## 1. Fix KeyError library (root cause + diff + test)

**Root cause**: `get_structure_max_level(slug)` in `app/territory/structures.py:174` faceva `STRUCTURE_CATALOG[slug]` senza guard. Doc `guild_structures` legacy referenziavano slug rimossi dal catalog (`library`, e ora anche `market` — scoperto post-fix nei WARN log live) → `KeyError` in `_public_doc`.

**Diff sintetico**:
```diff
-    meta = STRUCTURE_CATALOG[slug]
+    meta = STRUCTURE_CATALOG.get(slug)
+    if meta is None:
+        logging.getLogger("orbus.territory").warning(
+            "get_structure_max_level: unknown structure slug %r ...", slug)
+        return 0  # sentinel: no upgrade path
```

**Test**: `backend/tests/backend_round1654e_territory_hotfix_test.py` — **6/6 PASS**.

**Verifica live in produzione**: dopo il deploy, WARN emessi in log per `library` E `market` (nuovo slug orfano scoperto). Nessun crash, endpoint `/api/territory/my` risponde 200 su tutte le gilde.

Report dedicato: `/app/memory/round1654e_hotfix_report.md`. Sealed ✅.

---

## 2. Eventi funnel — mapping (9 righe)

| Event canonico | Status | File / endpoint attuale | Gap da coprire in R17.1 |
| --- | --- | --- | --- |
| `REGISTERED` | ❌ da aggiungere | `POST /api/auth/register` (`app/auth/routes.py`) | emit `write_audit(event_type="user_registered", ...)` post-`insert_one(user)`. Metadata: `{user_id, email_masked}`. Idempotente per natura (register è già unico). |
| `GUILD_CREATED` | ❌ da aggiungere | `POST /api/guilds` (`app/guilds/routes.py`) | emit `write_audit(event_type="guild_created", actor_user_id, actor_guild_id, ...)`. Idempotente (owner_user_id UNIQUE su guilds). |
| `FIRST_ADVENTURER_VIEWED` | ❌ da aggiungere | primo `GET /api/adventurers` con roster ≥ 1 | emit una-tantum in `app/adventurers/routes.py`, guardare `db.audit_log.find_one({actor_guild_id, event_type})` prima. |
| `FIRST_DUNGEON_VIEWED` | ❌ da aggiungere | primo `GET /api/dungeons` o `/api/expeditions/browse` | emit una-tantum in `app/expeditions/routes.py`. |
| `FIRST_EXPEDITION_PREVIEWED` | ❌ da aggiungere | primo `POST /api/expeditions/preview` (o simile) | emit sul preview endpoint prima del "launch". |
| `FIRST_EXPEDITION_STARTED` | ✅ derivabile da `expeditions.status="in_progress"` | `app/expeditions/services.py:launch_expedition` (già emette `gold_credited` a completion) | derivabile: primo doc `expeditions` con `guild_id` = "started". Aggiungere `write_audit` esplicito per audit funnel. |
| `FIRST_EXPEDITION_COMPLETED` | ✅ derivabile da `guild.total_expeditions_completed >= 1` | `app/expeditions/services.py:419-434` (già emette `gold_credited`, `loot_awarded`) | aggiungere `write_audit(event_type="first_expedition_completed", ...)` guardando cardinality. |
| `FIRST_REPORT_OPENED` | ❌ da aggiungere | primo `GET /api/expeditions/{id}` con `status="completed"` | emit una-tantum in `app/expeditions/routes.py`. |
| `FIRST_PRESTIGE_GAINED` | ✅ derivabile da audit `guild_xp_gained` | `app/achievements/engine.py:add_guild_xp` (già emette `guild_xp_gained`) | il primo `guild_xp_gained` per una gilda È di fatto FIRST_PRESTIGE_GAINED. Filtro query = telemetria. Nessun nuovo emit richiesto se preferiamo aggregazione ex-post. |

**Riepilogo**:
- **3/9 eventi già derivabili** senza modifica codice (`FIRST_EXPEDITION_STARTED/COMPLETED`, `FIRST_PRESTIGE_GAINED`) via query sul dato esistente.
- **6/9 eventi da aggiungere** con emit mirato in R17.1 (register/guild_created/adventurer_viewed/dungeon_viewed/expedition_previewed/report_opened).
- Nessun emit generico in tutta la codebase. Solo 6 punti mirati.

Regole idempotenza: ogni emit `FIRST_*` deve fare un `find_one({actor_guild_id, event_type})` prima dell'insert. Metadata leggero: `{guild_id, user_id_masked, timestamp}`. Nessun PII.

---

## 3. Stato gilde Lv0

Query live (2026-07-04T07:40Z):
```
guilds con guild_level ∈ {None, 0, missing}:  96 su 289 (33%)
guilds a Prestigio Lv3 (plateau achievement iniziali): 192 (66%)
guilds a Prestigio Lv6 (tester):                        1 (0.3%)
```

Le 96 gilde a Lv0 sono i target primari del nudge Step 0.

---

## 4. CTA Dashboard per gilde Lv0

**File nuovo**: `frontend/src/components/FirstObjectiveCard.jsx`

**File modificato**: `frontend/src/pages/Dashboard.jsx` — import + mount tra `TerritoryWidget` e `NextActionsCard`.

**Logica**:
- Card visibile SOLO se `guild.total_expeditions_completed === 0`.
- Branch CTA:
  - `advCount < 3` → CTA `[Recluta il primo team →]` → `/recruitment`
  - `advCount >= 3` → CTA `[Prepara la prima spedizione →]` → `/expeditions?starter=sewer-nest`
- Testo IT, badge amber "📍 PRIMO OBIETTIVO", descrizione branch-aware, reward hint.

**Mockup renderizzato** (viewport 390×844, tester fresh `r17step0-fresh-*@orbus.test`, advCount=5 → branch expedition):

```
┌────────────────────────────────────────┐
│ 📍 PRIMO OBIETTIVO                     │
│ Inizia la tua prima spedizione         │
│                                        │
│ Scegli 3 avventurieri e completa il    │
│ primo dungeon per ottenere Prestigio   │
│ e i primi equipaggiamenti.             │
│                                        │
│ Ricompensa: Prestigio di Gilda + oro   │
│ + equip iniziale.                      │
│                                        │
│ [Prepara la prima spedizione →]        │
└────────────────────────────────────────┘
```

**Verifica DOM** (`page.evaluate` su tester fresh):
```json
{
  "cardVisible": true,
  "cta_expedition_present": true,
  "ctaHref": "/expeditions?starter=sewer-nest",
  "ctaLabel": "Prepara la prima spedizione →",
  "title": "Inizia la tua prima spedizione",
  "desc": "Scegli 3 avventurieri e completa il primo dungeon...",
  "horizontalOverflow": false
}
```

**Verifica hide behavior** (viewport 390×844, `tester@orbus.test`, total_expeditions_completed=1):
```json
{ "cardVisible": false, "note": "card MUST be null" }
```

Confermato PASS su ENTRAMBE le branch (visible su gilda Lv0 fresh, nascosto su gilda con ≥1 spedizione completata).

---

## 5. Verifica starter dungeon

**Query live** (dungeons con `required_level ≤ 1` OR `recommended_power ≤ 25`):

```
slug=sewer-nest  lv=1  pwr=35  team=3  dur=45s  gold=25  xp=18  5p=False
```

**Esito**: **1 solo candidato disponibile**, ma **power 35 è troppo alto** per un team rookie Lv1 base (~20-25 team power). Il player si scontra con il primo failure loop identificato in R17.0 audit P0-5.

**Gap**: manca uno **starter dungeon "guarantee-win"** a power ≤ 20, durata ≤ 60s, party_size=3. La CTA della Dashboard punta comunque a `sewer-nest` (best available), ma la vera fix è in R17.1.

**Proposta** (da creare in R17.1, non in Step 0):

```
slug: "training-yard"
name: "Cortile di Addestramento" (IT) / "Training Yard" (EN)
required_level: 1
recommended_power: 15
required_team_size: 3
is_5p: false
base_duration_seconds: 60
base_gold_reward: 20
base_xp_reward: 15
narrative_hook: "Un percorso di allenamento nel cortile della gilda. Rischio minimo, ricompensa modesta, ma è il primo passo."
enemy_families: ["training_dummies", "wooden_targets"]
loot_table: [{slug: "cracked_wooden_sword", drop_chance: 0.5}, {slug: "basic_leather_wrap", drop_chance: 0.5}]
difficulty: "starter"
gate: null
bucket: "starter"
```

Il CTA `?starter=sewer-nest` andrà refactorizzato per puntare a `?starter=training-yard` in R17.1.

---

## 6. Primo percorso player attuale (step-by-step, dove si blocca)

Player fresh test creato via `POST /api/auth/register` con `password="Password123!"` (validazione password richiede maiuscola + numero + speciale + ≥8 char).

| Step | Azione | UI/UX osservata | Blocco potenziale |
| --- | --- | --- | --- |
| 1 | Register email/password | Form OK, redirect a create-guild | Password requirement non spiegato bene lato client |
| 2 | Create guild (nome + descrizione) | Form OK, redirect a Dashboard | Nessuno |
| 3 | Vede Dashboard | ✅ **Card "PRIMO OBIETTIVO" visibile** (Step 0 fix). Sotto: NextActionsCard, Daily Loop, ecc. | Nessuno |
| 4 | Click "Prepara la prima spedizione →" | Va a `/expeditions?starter=sewer-nest` | Query param `starter` ignorato dalla pagina attuale (`Expeditions.jsx`). Il player deve scegliere manualmente il dungeon dalla lista. |
| 5 | Sceglie sewer-nest | Team select richiede 3 adv | ⚠️ Team power calcolato ~20-25 vs required 35 → warning "sotto power consigliato". |
| 6 | Lancia spedizione | Timer 45s | ⚠️ Alta probabilità di fail per team rookie |
| 7 | Report | Report IT chiaro (fix R16.5.4d) | Se fail: narrative EN residua (R16.5.4f) |

**Punto di blocco principale (post Step 0)**:
- Step 4-5-6: Il CTA porta correttamente all'elenco spedizioni ma il starter dungeon esistente (`sewer-nest`) è troppo difficile. **Serve fix in R17.1** (starter dedicato + query param `starter` gestito).

**Punto di blocco secondario**:
- Step 4: `?starter=sewer-nest` non è processato da `Expeditions.jsx` (attualmente ignorato). In R17.1 aggiungere logica: se query param presente, auto-selezionare il dungeon e mostrare "Lancia" pre-configurato.

---

## 7. Blocchi rimasti (da affrontare in R17.1)

1. **Starter dungeon dedicato** (power ≤ 20) — proposta in §5.
2. **Query param `?starter=<slug>` handling** in `Expeditions.jsx` — auto-select + prompt "Lancia".
3. **Emit dei 6/9 eventi funnel** mancanti (register, guild_created, adventurer_viewed, dungeon_viewed, expedition_previewed, report_opened).
4. **Password requirements client-side hint** durante registrazione (già ok server-side, gap solo UX).
5. **Fallback rewards on fail** ("20% team XP anche se fallisci" — pattern anti-churn).
6. **Toast celebrazione** ai milestone funnel.
7. **Onboarding wizard** interattivo (feature completa, non nudge card).

---

## 8. Cosa entra in R17.1 (scope proposto, confermato/aggiornato dal Step 0)

Scope R17.1 confermato dall'audit R17.0 + Step 0:

- **P0** Seed idempotente starter dungeon "training-yard" (Lv1, pwr 15, party 3, dur 60s).
- **P0** Handling `?starter=<slug>` query param in `Expeditions.jsx` + prompt Launch UI.
- **P0** 6 emit `FIRST_*` audit events (register, guild_created, adventurer_viewed, dungeon_viewed, expedition_previewed, report_opened).
- **P0** Emit `FIRST_EXPEDITION_COMPLETED` esplicito (aggiungere `write_audit` in `services.py:419`).
- **P1** Fallback rewards on expedition fail (min +5g +10 team XP anche se `status="failed"`).
- **P1** Password hint client-side.
- **P1** Toast celebrazione milestone funnel.
- **P2** Wizard onboarding step-by-step (in seconda fase R17.1, dopo che P0 sono verified).

**Non entra in R17.1** (rimane a R17.2/R17.3):
- Raid catalog seed
- Achievements catalog seed
- Resource missions generator
- Endgame dungeon Lv15-20
- Item seed pass per classi carenti

---

## 9. Test eseguiti (Step 0)

| Test | Come | Esito |
| --- | --- | --- |
| R16.5.4e Territory hotfix — unit + integration | `pytest tests/backend_round1654e_territory_hotfix_test.py` | ✅ 6/6 PASS |
| R16.5.4e hotfix — live verification | WARN log live in produzione (`library` + `market`) | ✅ PASS |
| Step 0 audit funnel events | grep code + query MongoDB | ✅ Table produced (§2) |
| Step 0 starter dungeon audit | Mongo query dungeons `required_level ≤ 1` | ✅ 1 candidato (sewer-nest, gap identificato) |
| Step 0 Dashboard nudge — fresh guild (advCount=5, exp=0) | Playwright 390×844, DOM assertion | ✅ PASS (card visible, CTA expedition, no horizontal overflow) |
| Step 0 Dashboard nudge — tester (exp=1) | Playwright 390×844, DOM assertion | ✅ PASS (card null) |

---

## 10. Conferma: nessuna modifica reward/drop/economia/PvP/premium

- ✅ Zero modifiche a `expeditions/services.py` (reward calc).
- ✅ Zero modifiche a `achievements/xp_hooks.py` (pesi XP).
- ✅ Zero modifiche a `achievements/levels.py` (curva Prestigio).
- ✅ Zero modifiche a `raids/*`, `pvp*`, `premium*`, `stables/*`, `world_boss/*`.
- ✅ Zero modifiche a drop table dungeon.

## 11. Conferma: nessun hard delete

- ✅ Zero `delete_one` / `delete_many` in questo Step 0.
- ✅ Fix R16.5.4e è additivo (aggiunge fallback), non rimuove nulla.
- ✅ Card Dashboard nuova (`FirstObjectiveCard.jsx`), non rimpiazza nulla.

---

## Deliverable Step 0

- `/app/memory/round1654e_hotfix_report.md` — R16.5.4e sealed.
- `/app/memory/round17_step0_report.md` — questo report.
- `/app/backend/app/territory/structures.py` — fix difensivo `get_structure_max_level`.
- `/app/backend/tests/backend_round1654e_territory_hotfix_test.py` — 6 test.
- `/app/frontend/src/components/FirstObjectiveCard.jsx` — nuovo componente.
- `/app/frontend/src/pages/Dashboard.jsx` — import + mount card.
- Backlog + roadmap aggiornati.

**Sigillo**: Step 0 chiuso. Pronto per apertura R17.1 quando il PM decide.
