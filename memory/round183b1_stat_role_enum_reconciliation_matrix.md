# ROUND 18.3b.1 — Stat/Role Enum Reconciliation Matrix (Audit-only)

**Round**: R18.3b.1 · **Data**: 2026-07-04T21:02Z · **Status**: OPEN — Decision Support · **Autorità**: PM-facing

⚠️ **ZERO implementazione. ZERO DB write. ZERO code change. ZERO decisione sigillata.** Solo materiale per far decidere il PM.

---

## §1 · Executive summary

### Il conflitto in sintesi
- **PM design model** (R18.3b P0 answers, design intent): **6 stat** (Forza, Destrezza, Costituzione, Intelligenza, Saggezza, Carisma) + **ruoli compositi** (Healer/Tank hybrid, DPS/Utility, DPS Caster, Martial DPS/Tank, ...).
- **Live backend model**: **5 stat** (`strength`, `agility`, `intellect`, `endurance`, `faith`) + **role enum atomico** (`Tank`, `DPS`, `Healer`) + anomalia `Support` (bard).

### Perché serve decisione ORA
Blocca **R18.4** (item class-bound: item stat bonus mapping deve conoscere `primary_stat` finale), **R18.5** (PWR solo-equip + XP curve: `xp_modifier.py::expected_primary_stat` dipende da `primary_stat`), **R18.6** (dungeon/raid rebalance: primary stat threshold per party role).

### Impact su universo live
- **27 classi canoniche PM** design intent (11 con `primary_stat_intent` definito da R18.3b)
- **17 classi catalog live** (13 playable legacy + 2 R18.3a hidden + `recruit_unassigned` + `alchemist`)
- **2125 adventurers live** (post-R18.3c migration, 496 con `migration_round=R18.3c`)
- **~176 code references** a stat keys legacy nel backend
- **53 references** a `base_strength/agility/intellect/endurance/faith`
- **59 references** a `role`/`VALID_ROLES`/`class_role` in services+routes

### Preview 4 opzioni

| Opzione | Cambio schema | Cambio combat math | Round richiesti | Rischio regressione |
|---|---|---|---|---|
| **A · Full 6-stat migration** | SÌ (grosso) | **SÌ** (proibito PM) | ≥ 3 | **ALTO** |
| **B · Mantieni 5-stat legacy** | No | No | 0 | Nessuno |
| **C · Mapping esplicito 6→5** | No (aliasing catalog) | No | 1 | Basso |
| **D · 5-stat + design_tags append** | Append-only | No | 1 | Basso |

### Raccomandazione preliminare e1_dev (non vincolante)
**Opzione D** ha il miglior rapporto rischio/beneficio tecnico, preserva il fantasy PM al 100% via `design_primary_stat_it` + `role_display_it`, non tocca combat math, non richiede backfill di 2125 adv. Opzione C è la fallback più snella se PM preferisce zero schema change. Opzione A è **segnale rosso** (tocca combat math → proibito).

### Conflitto secondario rilevato (§ Bonus)
**Buona notizia**: `PRIMARY_STAT_IT` in `expeditions/xp_modifier.py:35-41` **già mappa** `agility→"Destrezza"` e `endurance→"Costituzione"`. Il display IT è già 4/5 6-stat-compatible. Solo `faith` è ambiguo (Fede legacy vs Carisma/Fede PM). Questo mitiga il gap semantico e favorisce l'Opzione D.

### Preview P0 counting
- 6 domande PM finali (§10) da rispondere prima di procedere con qualsiasi implementazione.

---

## §2 · Conflitto tecnico rilevato

### Enum live (con file:riga sorgente)

| Enum | Valori | File:riga |
|---|---|---|
| `VALID_ROLES` | `("Tank", "DPS", "Healer")` | `/app/backend/app/admin/services.py:19` |
| `primary_stat` values (live docs) | `strength`, `agility`, `intellect`, `endurance`, `faith` | schema catalog, 13 doc live |
| `base_*` fields | `base_strength`, `base_agility`, `base_intellect`, `base_endurance`, `base_faith` | `/app/backend/app/onboarding/services.py:56-60`, `common.py:115-119`, `services.py:148-152` |
| `PRIMARY_STAT_IT` | `strength→Forza, agility→Destrezza, intellect→Intelletto, endurance→Costituzione, faith→Fede` | `/app/backend/app/expeditions/xp_modifier.py:35-41` |

### PM design intent (R18.3b — 11 classi mappate con stat_intent)

| Classe | role_intent | primary_stat_intent | secondary_stats_intent |
|---|---|---|---|
| Paladino | `Healer/Tank hybrid` | `charisma` | `[strength, constitution]` |
| Guerriero | `Martial DPS/Tank` | `strength` | `[constitution, dexterity]` |
| Ladro | `DPS/Utility` | `dexterity` | `[intelligence, charisma]` |
| Cacciatore di Mostri | `DPS/Utility` | `dexterity` | `[wisdom, constitution]` |
| Cacciatore del Vuoto | `DPS Caster` | `intelligence` | `[constitution, dexterity]` |
| Druido | `Healer/Hybrid` (P0-* deferred) | `wisdom` | `[constitution, strength]` |
| Sciamano | `Healer/Support` | `wisdom` | `[charisma, constitution]` |
| Astrologo | `Support/Control` | `wisdom` | `[intelligence, charisma]` |
| Sognatore | `Control/Support` | `wisdom` | `[charisma, intelligence]` |
| Mercante | `Utility/Support` | `charisma` | `[intelligence, wisdom]` |
| Giocatore d'Azzardo | `Hybrid/Utility` | `charisma` | `[dexterity, intelligence]` |

### 11 Conflitti mappati

**Role compositi non atomic** (5):
1. `Healer/Tank hybrid` (Paladino) — non in `VALID_ROLES`
2. `Martial DPS/Tank` (Guerriero) — non atomic
3. `DPS/Utility` (Ladro, CdM) — `Utility` non in enum
4. `DPS Caster` (CdV) — qualifica extra su atomic
5. `Support/Control`, `Control/Support`, `Utility/Support`, `Hybrid/Utility` — 4 valori non atomic

**Stat 6-stat mancanti in live** (6):
6. `charisma` — not in `("strength", "agility", "intellect", "endurance", "faith")`
7. `dexterity` — not in enum (existe `agility`, semantica sovrapponibile)
8. `constitution` — not in enum (existe `endurance`, semantica sovrapponibile)
9. `intelligence` — not in enum (existe `intellect`, semantica identica)
10. `wisdom` — not in enum (nessun proxy diretto; `faith` è candidato PM per divine channeling, `intellect` per lore)
11. `base_*` schema: nessun `base_dexterity/constitution/wisdom/charisma` field su catalog docs

---

## §3 · Opzioni A/B/C/D — Deep-dive

### Opzione A — Full 6-stat migration

**Cambio**: adottare enum `(strength, dexterity, constitution, intelligence, wisdom, charisma)` come nuovo schema catalog + adventurer.

**Impatti**:

| Area | Impatto | Righe stimate |
|---|---|---|
| Catalog `adventurer_classes` | Backfill **13 doc live** (rename `agility→dexterity`, `endurance→constitution`, `intellect→intelligence`, `faith→wisdom or charisma`) | 13 update_many |
| `adventurers` 2125 doc | Rename stat keys (`stats.agility → stats.dexterity`, ecc.) via update pipeline | 2125 doc |
| `common.py::_roll_starting_stats` | Riscrivere 5 lines (line 115-119) | 5 |
| `onboarding/services.py::_roll_starting_stats` (duplicate) | Riscrivere 5 lines (line 56-60) | 5 |
| `adventurers/services.py::adventurer_public` | Aggiornare 5 `base_*` keys | 5 |
| `equipment/auto_equip.py` | Riscrivere `primary_stat` fallback (line 151, 246, 538, 577) — **combat/equip logic** | 15 |
| `expeditions/xp_modifier.py::expected_primary_stat` | Line 59 `class_doc.get("primary_stat")` + PRIMARY_STAT_IT — **XP curve logic** | 10 |
| `adventurers/routes.py::_primary_stat_value` line 138-142 — **combat sort** | 5 |
| `PRIMARY_STAT_IT` | Sostituire enum key | 6 righe |
| Frontend `ClassesAndStatsSection.jsx` mirror | Sync 5 righe | 5 |
| Test suite regression | Almeno 40+ test toccati (test_R18.1.*, test_R14.*, ecc.) | ~1500 righe di test |

**Combat math impact**: **SÌ**. `_primary_stat_value(a)` è usato per sorting in `/api/adventurers?sort=primary_desc|primary_asc`. `expected_primary_stat(class_doc, level)` è usato per XP curve in `expeditions/services.py:413-414`. `auto_equip.py::compute_recommended_loadout` legge `primary_stat` per equip scoring.

**Rollback complessità**: enorme. Rollback richiede reverse update_many su 2125 adv + rollback code (git revert 60+ file). Backup mongodump necessario.

**Rischio player-facing**:
- Se la UI mostra "Forza / Destrezza / ..." (già mappato da `PRIMARY_STAT_IT`), il player vede solo la sostituzione `Fede → Saggezza` o `Fede → Carisma`. Confusione media.
- Se cambiano i valori numerici (es. `faith=6 → charisma=6` per Paladino), impatto zero.
- Se PM decide di rimappare i valori con nuova calibrazione (es. `wisdom` primary per Druido con nuovo scaling), i player vedono rebalance visibile.

**Tempi stimati**: **≥ 3 round dedicati** (R18.3d schema + R18.3e backfill + R18.3f code+test), 2000+ righe modificate, 15 test suite regression.

**Segnale rosso**: **TOCCA combat math**. PM ha proibito esplicitamente ("Zero modifiche combat math"). Opzione A non è compatibile con il vincolo attuale.

---

### Opzione B — Mantieni 5-stat legacy

**Cambio**: nessuno. Backend live `(strength, agility, intellect, endurance, faith)` resta autoritativo.

**Impatti**:

| Area | Impatto |
|---|---|
| Backfill catalog | 0 |
| Backfill adventurers | 0 |
| Combat math | Non tocca |
| Auto-equip | Non tocca |
| Frontend | Nessun cambio |
| Test regression | 0 |
| Tempi | 0 round (già ok) |

**Vantaggi tecnici**:
- Zero code delta
- Zero regression risk
- Zero backfill 2125 adv
- Zero schema migration
- Combat math preservato as-is
- Playable classes 13 live restano intatte

**Tradeoff design PM**:
- Le 27 classi PM sono progettate su 6-stat (Carisma per Mercante/GdA/Bardo/Paladino, Saggezza per Druido/Sciamano/Astrologo/Sognatore/CdM secondary)
- **Perdita semantica**:
  - Carisma → mappato a `faith` (fantasy: fede/aura persuasiva plausible, ma perde nuance social)
  - Saggezza → mappato a `faith` (per Druido/Sciamano) o `intellect` (per Astrologo/Sognatore) — ambiguità intrinseca
  - Costituzione → mappato a `endurance` (fantasy stat name legacy, ok)
  - Destrezza → mappato a `agility` (fantasy stat name legacy, ok)
  - Intelligenza → mappato a `intellect` (identico)
- PM design è "frustrato" dallo schema legacy: le sue distinzioni Carisma/Saggezza vengono perse in un unico `faith` polimorfico.
- Ma la `PRIMARY_STAT_IT` già mostra "Destrezza"/"Costituzione" via alias → player non vedono `agility`/`endurance` grezzi.

**Player-facing coerenza**: massima (nessun cambio, tooltip identici).

**Note**: opzione più safe ma design PM frustrato. Compatibile con Opzione D come "combo" (5-stat + design tags).

---

### Opzione C — Mapping esplicito 6→5

**Cambio**: nessuno nel codice combat. Solo **catalog** riceve alias field opzionali per rappresentare intent PM (via aliasing declarative), ma la logica live legge solo il campo autoritativo 5-stat.

**Mapping proposto**:

| PM 6-stat | Live 5-stat | Confidence |
|---|---|---|
| **Forza** | `strength` | ✅ 100% |
| **Destrezza** | `agility` | ✅ 100% (già mappato in `PRIMARY_STAT_IT`) |
| **Costituzione** | `endurance` | ✅ 100% (già mappato in `PRIMARY_STAT_IT`) |
| **Intelligenza** | `intellect` | ✅ 100% |
| **Carisma** | `faith` | ⚠️ 70% — fantasy-plausible (fede/aura/persuasione) ma perde social nuance |
| **Saggezza** | **CRITICO — 3 alternative** | ⚠️ ambigua |

**Alternative Saggezza**:

**Alt 1 · Saggezza → `faith`** (spiritual attunement)

Fantasy tag: "connessione spirituale, empatia divina, natural insight, canalizzazione"

| Classe | Semantica alt 1 | Fit |
|---|---|---|
| Druido (wisdom P0-*) | Faith = attunement natura | ✅ Ottimo (nature-spirit fit) |
| Sciamano (wisdom) | Faith = spiriti/totem | ✅ Ottimo (spirit-bond fit) |
| Astrologo (wisdom P0-*) | Faith = cosmica insight | ⚠️ Ok (astrology = destiny/faith) |
| Sognatore (wisdom) | Faith = dream-fabric attunement | ⚠️ Ok (oneiric = mystical) |
| CdM (wisdom secondary) | Faith = hunt instinct | ❌ Debole (hunter secular) |

**Pro**: coerente con Paladino/priest lineage. **Contro**: sovraccarica `faith` con troppa semantica (divine + spiritual + insight + hunt instinct). Se player vede `Fede: 8` in una scheda Cacciatore di Mostri, si chiede "perché fede sul cacciatore?".

**Alt 2 · Saggezza → `intellect`** (knowledge + perception)

Fantasy tag: "conoscenza applicata, percezione affilata, deduzione"

| Classe | Semantica alt 2 | Fit |
|---|---|---|
| Druido (wisdom) | Intellect = conoscenza fauna/flora | ⚠️ Ok (nature scholar) |
| Sciamano (wisdom) | Intellect = conoscenza spiriti | ⚠️ Debole (perde spiritual) |
| Astrologo (wisdom) | Intellect = astro-lore | ✅ Ottimo (scholarly) |
| Sognatore (wisdom) | Intellect = simbolismo sogni | ⚠️ Debole (dream ≠ logic) |
| CdM (wisdom) | Intellect = tracking/percezione | ✅ Ottimo (hunter perception) |

**Pro**: coerente con Astrologo/CdM (scholarly). **Contro**: perde nuance spiritual per Druido/Sciamano/Sognatore.

**Alt 3 · Saggezza come `design_tag` non-numerico**

Nessuna stat DB dedicata. `wisdom` è solo un tag descrittivo in `class.primary_stat_display_it` o `class.role_tags`.

| Classe | Semantica alt 3 | Fit |
|---|---|---|
| Druido | primary_stat_live=`faith`, display_it="Saggezza" | ✅ Ottimo (compatibile Opz D) |
| Sciamano | primary_stat_live=`faith`, display_it="Saggezza" | ✅ Ottimo |
| Astrologo | primary_stat_live=`intellect`, display_it="Saggezza" | ✅ Ottimo |
| Sognatore | primary_stat_live=`intellect`, display_it="Saggezza" | ✅ Ottimo |
| CdM | secondary_stat_live=`intellect`, secondary_display_it=["Saggezza"] | ✅ Ottimo |

**Pro**: preserva design PM, evita mapping forzato. **Contro**: richiede introduzione campo `display_it` (converge verso Opzione D).

**Impatti Opzione C**:
- Catalog: 15 doc live ricevono `primary_stat_alias_pm_it` (nuovo field, append-only) e `secondary_stats_alias_pm_it` — MA questa è già Opzione D. C = D senza il role_display.
- Combat math: non tocca.
- Auto-equip: non tocca.
- Frontend: se vuole mostrare "Carisma"/"Saggezza", legge `primary_stat_alias_pm_it` con fallback su `PRIMARY_STAT_IT`.

**Tempi stimati**: **1 round** (R18.3d) di backfill catalog append-only + frontend read alias.

**Rischio player-facing**: basso. Confusione se player vede in UI "Carisma: 6 (faith)" — dipende da come si presenta l'aliasing.

---

### Opzione D — 5-stat live + design_tags estesi

**Cambio**: nessuno nel combat. Catalog e adventurer ricevono campi `design_*` append-only:
- `class.primary_stat_display_it` (es. "Carisma") — usato solo da UI
- `class.secondary_stats_display_it` (es. `["Forza", "Costituzione"]`)
- `class.role_tags` (array esteso: `["Healer", "Tank"]`)
- `class.role_display_it` (es. `"Healer/Tank"`)

Backend logic autoritativo continua a usare `primary_stat` (5-stat legacy). UI/tooltip legge `*_display_it` con fallback.

**Esempio Paladino**:

```json
{
  "slug": "paladin",
  "role": "Healer",                      // matchmaking / VALID_ROLES compat
  "role_tags": ["Healer", "Tank"],       // party composition extended (opzionale)
  "role_display_it": "Healer/Tank",      // UI tooltip
  "primary_stat": "faith",               // combat math legge questo
  "primary_stat_display_it": "Carisma",  // UI legge questo
  "secondary_stats": ["strength", "endurance"],       // combat
  "secondary_stats_display_it": ["Forza", "Costituzione"]  // UI
}
```

**Impatti**:

| Area | Impatto | Righe |
|---|---|---|
| Catalog backfill | 13 doc live + 2 R18.3a hidden = 15 update_many `$set` append-only | 15 |
| Adventurer collection | 0 (adventurers non toccati) | 0 |
| Combat math | Non tocca | 0 |
| Auto-equip | Non tocca | 0 |
| `adventurer_public()` serializer | Espone `role_tags`, `role_display_it`, `primary_stat_display_it` (già append-only R18.3a.1) | 5 righe (già in place per is_playable/migration_target_only) |
| Frontend `ClassesAndStatsSection` | Legge nuovi field con fallback | 20 righe |
| Test regression | Nessuno rotto | 0 |
| Tempi | **1 round** (R18.3d) | — |

**Vantaggi**:
- Preserva design PM al 100% (`Carisma`, `Saggezza`, ruoli compositi tutti rappresentabili come display_tag)
- Zero touch combat math (compliant con vincolo PM)
- Zero backfill 2125 adv
- Rollback trivial (`$unset` sui 15 doc)
- `role` atomic resta canonico per matchmaking
- Compatibile con Opzione C (D = C + role_display_it + role_tags array)

**Rischio confusione display vs calcolo**:
- Player vede "Carisma" in tooltip Paladino, ma se ispeziona debug/dev tools vede `primary_stat: faith`.
- Mitigation: banner UI IT chiarificatore "Le stat visualizzate sono localizzate. Il calcolo tecnico usa nomi legacy."
- Nel gameplay normale, il player non ha mai accesso al raw `primary_stat` slug — solo al display IT.

**Compatibilità item/auto-equip**: piena. `auto_equip.py` legge `primary_stat` autoritativo (live 5-stat), ignora `*_display_it`.

**Necessità traduttori backend**: minima. `adventurer_public()` già espone display fields optional; basta aggiungere 2 righe per `primary_stat_display_it`, `secondary_stats_display_it`, `role_display_it`.

---

## §4 · Tabella impatto tecnico

| Opzione | Backfill catalog | Backfill adventurers | Schema change | Combat math tocca? | Auto-equip tocca? | Round stimati | Reg risk |
|---|---|---|---|---|---|---|---|
| **A · 6-stat migration** | 13 doc rename | **2125 doc** rename | **Sì (grosso)** | 🔴 **SÌ (PROIBITO)** | Sì | ≥ 3 | ALTO |
| **B · 5-stat legacy** | 0 | 0 | 0 | No | No | 0 (già ok) | Nessuno |
| **C · Mapping 6→5** | 15 doc alias `$set` | 0 (solo derived) | 0 (append-only) | No | No | 1 | Basso |
| **D · 5-stat + tags** | 15 doc append-only | 0 | Sì (append-only) | No | No | 1 | Basso |

**Minor round count**: B (0) > C ≈ D (1) > A (≥3).
**Segnale rosso combat math**: **Opzione A** (vincolo PM proibito).

---

## §5 · Tabella impatto gameplay/design

| Opzione | Fantasy accuracy | Player-facing coerenza | Item design | Talent tree design | Dungeon/raid balance | Party composition |
|---|---|---|---|---|---|---|
| A | ✅ Massima (native 6-stat) | ⚠️ Rebalance visibile (stat rename) | 🔴 Riscrivere stat_bonus mapping | ✅ Native | 🔴 Ricalibrare threshold | ✅ Native |
| B | ❌ Frustrato (perde Carisma/Saggezza) | ✅ Massima (nessun cambio) | ✅ Immutato | ⚠️ Compresso a 5-stat | ✅ Immutato | ⚠️ Compresso |
| C | ⚠️ Buona con alt Saggezza chiarita | ✅ Ok (display già IT via PRIMARY_STAT_IT) | ✅ Immutato | ⚠️ Alias-driven | ✅ Immutato | ⚠️ Alias |
| D | ✅ Massima (design_tags cover full 6-stat + composite role) | ✅ Ok (display esplicito) | ✅ Immutato | ✅ Full via role_tags | ✅ Immutato | ✅ Full |

**Miglior preservazione fantasy PM**: **D > A > C > B**.

---

## §6 · Tabella rischio regressione

| Opzione | Auto-equip | Combat sort | Recruitment UI | Dungeon success chance | Expedition dispatch | Onboarding | Global reg risk |
|---|---|---|---|---|---|---|---|
| A | 🔴 ALTO | 🔴 ALTO | 🔴 ALTO | 🔴 ALTO | 🟡 MEDIO | 🔴 ALTO | **ALTO** |
| B | 🟢 nullo | 🟢 nullo | 🟢 nullo | 🟢 nullo | 🟢 nullo | 🟢 nullo | **NESSUNO** |
| C | 🟢 nullo | 🟢 nullo | 🟡 MEDIO (alias display) | 🟢 nullo | 🟢 nullo | 🟢 nullo | **BASSO** |
| D | 🟢 nullo | 🟢 nullo | 🟡 MEDIO (display estesi) | 🟢 nullo | 🟢 nullo | 🟢 nullo | **BASSO** |

**Distribuzione**: A=ALTO · B=nessuno · C=basso · D=basso.

---

## §7 · Casi studio classi (11 classi × 4 opzioni)

### 1. Paladino

**PM design intent**: role=`Healer/Tank hybrid`, primary=`charisma`, secondary=`[strength, constitution]`

- **A (6-stat)**: role=`Healer/Tank hybrid`, primary=`charisma`, secondary=`[strength, constitution]` — native compatible. Rebalance combat sort visibile.
- **B (5-stat)**: role=`Tank` (atomic), primary=`faith`, secondary=`[strength, endurance]` — legacy live. **Perdita**: role composite → single, `charisma` → `faith`, `constitution` → `endurance`.
- **C (mapping 6→5)**: role=`Tank` atomic, primary=`faith` (aliased "Carisma"), secondary=`[strength, endurance]` (aliased "Costituzione") + `role_display_it`. Saggezza n/a per Paladino. 
- **D (5-stat + tags)**: role=`Tank` (matchmaking), role_tags=`[Healer, Tank]`, role_display_it=`Healer/Tank`, primary_stat=`faith`, primary_stat_display_it=`Carisma`, secondary_stats_display_it=`[Forza, Costituzione]`.

### 2. Guerriero

**PM design intent**: role=`Martial DPS/Tank`, primary=`strength`, secondary=`[constitution, dexterity]`

- **A**: role=`Martial DPS/Tank`, primary=`strength`, secondary=`[constitution, dexterity]` — native.
- **B**: role=`Tank`, primary=`strength`, secondary=`[endurance]` — legacy. Perde `dexterity` secondary.
- **C**: role=`Tank`, primary=`strength`, secondary=`[endurance, agility]` (aliased "Costituzione, Destrezza").
- **D**: role=`Tank`, role_tags=`[DPS, Tank]`, role_display_it=`Martial DPS/Tank`, primary=`strength`, secondary=`[endurance, agility]`, secondary_display_it=`[Costituzione, Destrezza]`.

### 3. Ladro

**PM design intent**: role=`DPS/Utility`, primary=`dexterity`, secondary=`[intelligence, charisma]`

- **A**: native `DPS/Utility` + `dexterity` + `[intelligence, charisma]`.
- **B**: role=`DPS`, primary=`agility`, secondary=`[strength]` — perde `intelligence`, `charisma`.
- **C**: role=`DPS`, primary=`agility` (aliased "Destrezza"), secondary=`[intellect, faith]` (aliased "Intelligenza, Carisma").
- **D**: role=`DPS`, role_tags=`[DPS, Utility]`, role_display_it=`DPS/Utility`, primary=`agility`, secondary_display_it=`[Intelligenza, Carisma]`.

### 4. Cacciatore di Mostri

**PM design intent**: role=`DPS/Utility`, primary=`dexterity`, secondary=`[wisdom, constitution]`

- **A**: native `DPS/Utility` + `dexterity` + `[wisdom, constitution]`.
- **B**: role=`TBD`→`DPS` post-decision, primary=`agility`, secondary=`[endurance]` — perde `wisdom`.
- **C**: role=`DPS`, primary=`agility` (aliased "Destrezza"), secondary=`[intellect, endurance]` (aliased "Saggezza [alt 2], Costituzione") con alt Saggezza=Intellect.
- **D**: role=`DPS`, role_tags=`[DPS, Utility]`, role_display_it=`DPS/Utility`, primary=`agility`, secondary=`[intellect, endurance]`, secondary_display_it=`[Saggezza, Costituzione]`.

### 5. Cacciatore del Vuoto

**PM design intent**: role=`DPS Caster`, primary=`intelligence`, secondary=`[constitution, dexterity]`

- **A**: native `DPS Caster` + `intelligence` + `[constitution, dexterity]`.
- **B**: role=`TBD`→`DPS`, primary=`intellect`, secondary=`[endurance]` — perde `dexterity`.
- **C**: role=`DPS`, primary=`intellect` (aliased "Intelligenza"), secondary=`[endurance, agility]` (aliased "Costituzione, Destrezza").
- **D**: role=`DPS`, role_display_it=`DPS Caster`, primary=`intellect`, secondary=`[endurance, agility]`, secondary_display_it=`[Costituzione, Destrezza]`.

### 6. Druido

**PM design intent**: role=`Healer/Hybrid` (deferred), primary=`wisdom`, secondary=`[constitution, strength]`

- **A**: native.
- **B**: role=`Healer` (live: druid role=Healer), primary=`faith`, secondary=`[endurance]` — Saggezza→faith legacy compresso.
- **C alt 1 (Saggezza→faith)**: role=`Healer`, primary=`faith` (aliased "Saggezza"), secondary=`[endurance, strength]` (aliased "Costituzione, Forza"). ✅ **Fit ottimo**.
- **C alt 2 (Saggezza→intellect)**: role=`Healer`, primary=`intellect` (aliased "Saggezza"). ⚠️ Rebalance: primary_stat cambia da faith→intellect per druid live (167 adv, RISCHIO).
- **D**: role=`Healer`, role_tags=`[Healer, Hybrid]`, primary=`faith` (live invariato), primary_stat_display_it=`Saggezza`. ✅ Zero-touch adventurer, tag semantico.

### 7. Sciamano

**PM design intent**: role=`Healer/Support`, primary=`wisdom`, secondary=`[charisma, constitution]`

- **A**: native.
- **B**: **classe non seedata**. Se decision B, resta unseeded o seedata con `wisdom`→`faith` legacy.
- **C alt 1 (Saggezza→faith)**: primary=`faith` (aliased "Saggezza"), secondary=`[faith, endurance]` (Carisma→faith conflict — collisione stat aliases). **Problema Alt 1 + Carisma→faith**: entrambi mappano a faith, ambiguità.
- **D**: primary=`faith`, primary_stat_display_it=`Saggezza`, secondary=`[faith, endurance]`, secondary_display_it=`[Carisma, Costituzione]`. **Ma stessa collisione**: 2 slot mostrano "Fede" via alias display se non separati.

⚠️ **Nota critica**: se Carisma e Saggezza collidono entrambi su `faith`, l'aliasing display può diventare confuso. Opzione D può aggiungere `stat_source_kind` per distinguere (es. `charisma_via_faith` vs `wisdom_via_faith`), oppure PM decide alt Saggezza→intellect per evitare double-mapping.

### 8. Astrologo

**PM design intent**: role=`Support/Control`, primary=`wisdom`, secondary=`[intelligence, charisma]`

- **A**: native.
- **B**: role=`Support` (non in VALID_ROLES legacy → richiede espansione), primary=`faith`, secondary=`[intellect]`.
- **C alt 2 (Saggezza→intellect)**: primary=`intellect` (aliased "Saggezza"), secondary=`[intellect, faith]` (aliased "Intelligenza, Carisma"). **Problema**: primary e secondary entrambi `intellect` — aliasing OK ma stat doubled?
- **D**: primary=`intellect`, primary_stat_display_it=`Saggezza`, secondary=`[intellect, faith]`, secondary_display_it=`[Intelligenza, Carisma]`. Live legge secondary=`intellect` una volta (nessuna doppia stat), display mostra 2 nomi diversi mappati sulla stessa stat live. **Rischio**: player confusion.

### 9. Sognatore

**PM design intent**: role=`Control/Support`, primary=`wisdom`, secondary=`[charisma, intelligence]`

- **A**: native.
- **B**: unseeded classe.
- **C alt 1/2**: primary alt 1 `faith` o alt 2 `intellect` (aliased "Saggezza"). Alt 1 fit debole (dream ≠ divine), alt 2 fit debole (dream ≠ logic pura). Best PM-per-class decision.
- **D**: primary=`faith` (o `intellect`, PM decide), primary_stat_display_it=`Saggezza`.

### 10. Mercante

**PM design intent**: role=`Utility/Support`, primary=`charisma`, secondary=`[intelligence, wisdom]`

- **A**: native.
- **B**: role=`Support` (non in enum), primary=`faith`, secondary=`[intellect]` — perde `wisdom`.
- **C**: primary=`faith` (aliased "Carisma"), secondary=`[intellect, faith]` (aliased "Intelligenza, Saggezza"). **Collisione**: primary=faith + secondary contiene faith aliased come Saggezza — doppia rappresentazione.
- **D**: primary=`faith`, primary_stat_display_it=`Carisma`, secondary=`[intellect, faith]`, secondary_display_it=`[Intelligenza, Saggezza]`. Stessa collisione display.

### 11. Giocatore d'Azzardo

**PM design intent**: role=`Hybrid/Utility`, primary=`charisma`, secondary=`[dexterity, intelligence]`

- **A**: native.
- **B**: unseeded classe.
- **C**: primary=`faith` (aliased "Carisma"), secondary=`[agility, intellect]` (aliased "Destrezza, Intelligenza"). Nessuna collisione.
- **D**: primary=`faith`, primary_stat_display_it=`Carisma`, secondary=`[agility, intellect]`, secondary_display_it=`[Destrezza, Intelligenza]`.

---

## §8 · Role enum reconciliation — analisi separata

**Live**: `("Tank", "DPS", "Healer")` — 3 valori atomic, hardcoded in `admin/services.py:19`.
**PM design**: `("Tank", "Healer", "DPS", "Support", "Control", "Summoner", "Utility", "Hybrid")` + composite (`Healer/Tank hybrid`, `DPS/Utility`, `DPS Caster`, `Martial DPS/Tank`, ...).

### Sotto-opzione 1 — Role atomic live + `role_tags` array futuro

**Compat**: D
- Impatto tecnico: append field `role_tags: list[str]` su catalog (15 doc `$set`). Zero validation change su `VALID_ROLES`.
- Impatto UI: tooltip legge `role_tags` con fallback `role`.
- Impatto matchmaking/party: usa `role` autoritativo (compat legacy).
- Impatto auto-equip: nessuno (auto-equip legge `primary_stat`).
- Impatto talent tree: `role_tags` fornisce contesto extra per branch selection.
- Rischio reg: basso.

### Sotto-opzione 2 — Espandere VALID_ROLES

**Compat**: A o D
- Impatto tecnico: aggiungere `Support`, `Control`, `Utility`, `Summoner`, `Hybrid` a `VALID_ROLES` (2 righe). Composite roles (`Healer/Tank hybrid`) NON aggiunti (resta atomic).
- Impatto validation: `POST /api/admin/classes` accetta nuovi valori.
- Impatto matchmaking: nessuno se logica party non filtra su enum.
- Impatto UI: bard esistente (`role=Support`) diventa canonico non anomalia.
- Rischio reg: basso.

### Sotto-opzione 3 — `role` per matchmaking + `role_display` per UI

**Compat**: D
- Impatto tecnico: append `role_display_it: str` su catalog (es. `"Healer/Tank"`). Zero cambi validation.
- Impatto UI: tooltip legge `role_display_it` con fallback `role`.
- Impatto matchmaking: usa `role` atomic (immutato).
- Rischio reg: nullo.

### Sotto-opzione 4 — `primary_role` + `secondary_roles`

**Compat**: A o D
- Impatto tecnico: catalog `primary_role: str` (atomic) + `secondary_roles: list[str]` (extended, opzionale). Backfill 15 doc.
- Impatto validation: `primary_role ∈ VALID_ROLES`, `secondary_roles ⊆ EXTENDED_ROLES`.
- Impatto UI: legge entrambi, mostra formato "Primary / Secondary".
- Impatto talent tree: `secondary_roles` per multi-branch selection.
- Rischio reg: medio (nuova validation).

**Best fit per Opzione D**: **Sotto-opz 1 + 3 combinati** (`role_tags` + `role_display_it`), zero validation change, massima flessibilità UI, zero regression.

---

## §9 · Raccomandazione tecnica e1_dev (non vincolante)

### Preferenza: **Opzione D + Role sub-option 1 (+3)**

**Motivazione con dati**:

1. **Combat math intoccato**: `_primary_stat_value` (routes.py:138) legge `a.get("primary_stat")` — resta autoritativo live (5-stat). Zero regression su sort, XP curve, auto-equip.
2. **Backfill minimo**: 15 catalog docs con `$set` append-only (`role_tags`, `role_display_it`, `primary_stat_display_it`, `secondary_stats_display_it`). Zero touch a 2125 adventurers.
3. **Fantasy PM preservato**: 100% delle 27 design intent rappresentabili via display fields. `Healer/Tank hybrid`, `DPS Caster`, `Martial DPS/Tank` tutti esprimibili.
4. **Rischio regressione basso**: cambi solo in `adventurer_public()` serializer (già estende R18.3a.1 con `is_playable`/`migration_target_only`) + frontend `ClassesAndStatsSection.jsx` (~20 righe di UI display fallback).
5. **Rollback trivial**: `$unset` sui 15 doc + git revert 2-3 file.
6. **Compatibilità con R18.4/R18.5**: item class-bound può usare `primary_stat` autoritativo (5-stat). XP curve invariata. Party composition può opzionalmente leggere `role_tags` per matching più ricco.
7. **Opzione A esclusa**: **segnale rosso combat math** (violazione vincolo PM esplicito).

### Fallback tecnico se PM preferisce zero append-only

**Opzione B pure** (5-stat legacy senza design tags) — accettabile ma frustra fantasy design. Compatibile con R18.4/R18.5 senza cambi.

### Opzione C intermedia

Se PM vuole zero campo nuovo su catalog: possiamo affidarsi a `PRIMARY_STAT_IT` (già esiste!) per display display. Nessun catalog change. Ma:
- Non permette `role_display_it` (role composite non rappresentabile).
- Saggezza resta ambigua (alt 1 vs alt 2 deve essere decisa).

### Segnale rosso ripetuto

**Opzione A tocca combat math** (auto-equip, XP curve, primary stat sort). PM ha proibito. Include come opzione teorica ma **non raccomandata**.

---

## §10 · Domande PM finali

1. **Adotto A / B / C / D come modello ufficiale?**
   - Risposta attesa: `A` / `B` / `C` / `D` / `custom` / `deferred`

2. **Se C, quale alternativa Saggezza?**
   - Alt 1 (Saggezza → faith, spiritual attunement)
   - Alt 2 (Saggezza → intellect, knowledge/perception)
   - Alt 3 (Saggezza come display-only tag, converge verso D)
   - Risposta attesa: `1` / `2` / `3` / `mixed per-classe` / `deferred`

3. **Se D, role_tags come array o `role_display_it` come stringa singola?**
   - Opz 1 (`role_tags` array) — extensible party comp
   - Opz 3 (`role_display_it` string) — semplice UI-only
   - Opz 1+3 (entrambi) — massima flessibilità
   - Risposta attesa: `array` / `string` / `both` / `deferred`

4. **In quale round applico la decisione?**
   - R18.3d dedicato (schema + backfill separato)
   - Parallelo a R18.4 (item class-bound)
   - Parallelo a R18.5 (PWR solo-equip)
   - Risposta attesa: `R18.3d` / `parallel-R18.4` / `parallel-R18.5` / `deferred`

5. **Grandfathering per adventurer live esistenti se cambia il nome stat visibile?**
   - Sì, banner UI IT chiarificatore ("Le stat sono state rinominate secondo il canon 6-stat")
   - No, transizione silenziosa (PRIMARY_STAT_IT già mappa 4/5 nomi al 6-stat display)
   - Risposta attesa: `sì banner` / `no silenzioso` / `partial per stat` / `deferred`

6. **UI banner IT necessario se la scelta impatta stat display?**
   - Sì, banner one-shot (dismissible come R18.3c)
   - No, tooltip inline sufficiente
   - Solo hover tooltip su stat name
   - Risposta attesa: `banner` / `tooltip` / `hover` / `nessuno` / `deferred`

**Totale**: **6 domande PM finali** numerate.

---

## §Bonus · Conflitti secondari rilevati

Durante l'analisi ho trovato conflitti nascosti non-ovvi che influenzano la scelta:

### B1 · `PRIMARY_STAT_IT` già usa alias 6-stat-compatibile

**File**: `/app/backend/app/expeditions/xp_modifier.py:35-41`

```python
PRIMARY_STAT_IT = {
    "strength": "Forza",
    "agility": "Destrezza",      # ← già usa nome 6-stat!
    "intellect": "Intelletto",   # (Intelligenza in italiano puro)
    "endurance": "Costituzione", # ← già usa nome 6-stat!
    "faith": "Fede",             # ← unico non-6-stat (PM vuole Carisma o Saggezza)
}
```

**Impact**: 4/5 stat legacy hanno GIÀ display name compatibile con 6-stat PM. Solo `faith` resta ambiguo. Se scelgo Opzione D, il display di 4/5 stat non cambia — solo `faith` diventa aliasable (`Carisma` o `Saggezza` a seconda della classe).

**Proposta**: Opzione D può riutilizzare `PRIMARY_STAT_IT` come fallback e sovrascriverlo per-classe con `primary_stat_display_it` solo dove necessario (classi con Carisma/Saggezza design intent).

### B2 · `class_role` frozen sull'adventurer

**File**: `/app/backend/app/onboarding/services.py:52`, `common.py:133`, `recruitment/services.py:114`

`class_role` viene copiato dal catalog `role` al momento del recruit. Storicamente 2125 adv esistenti hanno `class_role` frozen (o null per alcuni). Post-R18.3c, un adv `priest→paladin` conserva `class_role="Healer"` (frozen da priest recruit), non "Tank" del nuovo catalog paladin.

**Impact**: se PM adotta ruoli compositi (Opzione A o D), la propagazione ai `class_role` esistenti richiede backfill 2125 adv. Se Opzione D con `role_tags` sul catalog, gli adv già migrati NON ricevono automaticamente il tag composite — servirebbe backfill separato di `class_role_tags` sull'adv.

**Proposta**: Opzione D può includere `class_role_tags` sull'adv (append-only, defaulta a `[class_role]` in serializer) per zero-write coverage. Ma richiede test regression per assicurare recruitment/UI non degradi.

### B3 · `admin/services.py::VALID_ROLES` hardcoded

Enum atomic hardcoded senza export configurabile. Per Opzione D sub-opz 2 (espansione enum), è banale (aggiungere 5 valori). Ma se PM vuole role composite come valori atomici (`"Healer/Tank"` singolo string), serve considerare edge cases (matchmaking filter, admin UI dropdown).

### B4 · Frontend mirror di `PRIMARY_STAT_IT`

**File**: `/app/frontend/src/components/ClassesAndStatsSection.jsx` (commento nel backend indica mirror manuale).

Se cambio `PRIMARY_STAT_IT` (backend), devo sincronizzare mirror frontend. Attuale: ~5 righe. Opzione D approach: fallback su `PRIMARY_STAT_IT` + override da `class.primary_stat_display_it` — frontend riceve tutto via API senza hardcoded map.

### B5 · Talent tree pilot R18.2 non usa `role`/`stat`

Pilot R18.2 seedato 540 placeholder senza dipendenza da `role`/`primary_stat`. Buona notizia: R18.5 (talenti reali) potrà usare qualsiasi enum decision Opzione B/C/D senza refactor pilot.

### Cosa fare in R18.3b.1 vs cosa rimandare

**In R18.3b.1 (questo round)**: solo documentazione. Nessuna implementazione.

**Rimandare a R18.3d** (post PM decision):
- Backfill catalog `role_tags`, `role_display_it`, `primary_stat_display_it`, `secondary_stats_display_it` (Opzione D)
- Update frontend `ClassesAndStatsSection.jsx` con fallback logic
- Update `adventurer_public()` serializer per esporre nuovi field
- Update test regression per coprire display path

**Rimandare a R18.4+**: item class-bound può leggere `primary_stat` autoritativo indipendentemente da decisione. Talent tree può leggere `role_tags` se PM sceglie Opzione D.

---

## Conferma vincoli R18.3b.1

- ✅ Zero implementazione
- ✅ Zero DB write (nemmeno index)
- ✅ Zero schema migration
- ✅ Zero codice modificato
- ✅ Zero seed
- ✅ Zero update catalog
- ✅ Zero update adventurers
- ✅ Zero combat math change
- ✅ Zero auto-equip change
- ✅ Zero item change
- ✅ Zero UI change
- ✅ Zero hard delete
- ✅ Zero decisioni sigillate (tutto candidato)
- ✅ Solo lettura del codice esistente + scritture su `/app/memory/round183b1_*.md/json`
- ✅ Regression cross-round 94/94 PASS (invariato)
- ✅ Feature flag `R18_REWORK_ENABLED=false` invariato

---

## Firma

**R18.3b.1 OPEN — Decision Support READY.**

*Firma: e1 main agent · 2026-07-04T21:02Z*

Attendo risposta PM alle 6 domande §10 per procedere. In assenza di decisione, il sistema resta stable in modalità Opzione B implicit (5-stat legacy immutato).

---

## §11 · PM Decision Sealed

**Sealed at**: 2026-07-04T21:35Z
**Sealed by**: PM (via briefing to e1 main agent)
**Round status transition**: OPEN → **CLOSED & SEALED**

### Scelta PM

| Dimensione | Opzione | Valore |
|---|---|---|
| **Stat system** | **C.2** | Mapping esplicito 6→5 con **Saggezza → intellect** (non faith) |
| **Role enum** | **R3** | Role atomico backend (`VALID_ROLES` immutato) + `role_display_it` composito + `class_role_tags[]` UI-only |

### Mapping ufficiale sigillato

| design_stat_it | design_stat_en | live_stat | note |
|---|---|---|---|
| Forza | strength | strength | 1:1 diretto |
| Destrezza | dexterity | agility | 1:1 canonico |
| Costituzione | constitution | endurance | 1:1 canonico |
| Intelligenza | intelligence | intellect | 1:1 diretto |
| **Saggezza** | **wisdom** | **intellect** | ⚠️ **collisione by-design PM** con Intelligenza |
| Carisma | charisma | faith | 1:1 fantasy-plausible |

### Motivazione PM (dal briefing)

1. **Saggezza → intellect** (non faith): evita sovraccarico semantico su `faith` (già mappato a Carisma). Mantiene coerenza per classi caster/scholar (Astrologo, Sognatore, Cacciatore di Mostri) che usano wisdom come "acume mentale/percezione", coerente con `intellect` legacy.
2. **Druido/Sciamano**: la doppia natura (wisdom + nature magic) è gestibile via `role_tags` (`Healer` + `Nature`/`Elemental`) senza dover collassare wisdom su faith.
3. **Collisione Saggezza/Intelligenza**: **accettata by-design** PM. Entrambe le stat "mentali" convergono su `intellect` legacy — le classi che le distinguono nel design intent (es. Cacciatore di Mostri con secondary `Saggezza` + primary `Destrezza`) usano `role_tags` per differenziare il flavor.
4. **Role atomico immutato**: `VALID_ROLES=("Tank","DPS","Healer")` resta canonico backend. Compositi (`Healer/Tank`, `DPS/Utility`) sono display-only via `role_display_it`; enrichment tag via `class_role_tags[]`.

### Applicabilità

- **Immediata (R18.3d)**: registry mapping ufficiale + catalog metadata append-only per 13 classi live (design_primary_stat_it, mapped_primary_stat_live, role_display_it, class_role_tags, ecc.) — solo non-combat, solo append-only.
- **Differita (R18.4+)**: item stat bonus resta legacy 5-stat (`{strength|agility|intellect|endurance|faith}_bonus`). Item class-bound può leggere `mapped_primary_stat_live` (che punta al live legacy) senza refactor combat.
- **Differita (R18.5)**: talenti reali possono leggere `design_primary_stat_it` per UI flavor, `mapped_primary_stat_live` per math.

### Vincoli invariati post-sealing

- ❌ Zero schema migration stat live
- ❌ Zero cambio `VALID_ROLES` enum
- ❌ Zero cambio combat math / auto-equip formula
- ❌ Zero cambio `base_strength/base_agility/base_intellect/base_endurance/base_faith`
- ✅ Registry mapping + catalog metadata append-only autorizzati in R18.3d

### Round successivo

**R18.3d — Stat/Role Mapping Registry Apply** (apply controllato non-combat) apre subito dopo il sealing.

---

**R18.3b.1 CLOSED & SEALED · 2026-07-04T21:35Z**

*Firma sealing: e1 main agent (relay PM decision)*
