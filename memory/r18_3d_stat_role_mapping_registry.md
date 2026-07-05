# R18.3d — Stat/Role Mapping Registry (MD Companion)

```
═══════════════════════════════════════════════════════════════════════
🔒 CLOSED & SEALED — R18.3d Phase B (documental-only) — 2026-07-05T18:05:00Z UTC
🔒 SEAL AUTHORITY: PM Orchestrator
🔒 SEAL NOTE: Closed as documental-only registry. No DB metadata apply executed.
🔒 Do NOT modify this file without explicit new PM gate.
═══════════════════════════════════════════════════════════════════════
```

**Round**: `R18.3d` (Stat/Role Mapping Registry)
**Fase**: B — Design-First Staged Apply (Q10.b Correction)
**Registry JSON companion**: `/app/memory/r18_3d_stat_role_mapping_registry.json`
**Decision Lock**: `/app/memory/r18_3d_phase_b_pm_decisions.md`
**Status**: **CLOSED & SEALED — documental-only** (nessun apply DB eseguito)

---

## 1 · Sintesi (Executive)

Il registry R18.3d è la fonte **documentale** ufficiale della corrispondenza tra:

- il **set canonico di 27 classi** italiane (target design PM, LOCKED Q10.b)
- i **18 documenti live** presenti nel catalog `adventurer_classes` (source-of-truth runtime)
- le **mapping IT ↔ 5-stat live** (LOCKED Q5)
- il **role system atomico** `Tank / DPS / Healer` (LOCKED Q3)

**Governance chiave**: il catalog live `adventurer_classes` **rimane la source-of-truth runtime**. Il registry è **documentale + admin introspection only**. Non viene collegato ad `auto-equip`, `xp_modifier`, `combat resolvers`, `recruitment`, `sorting`, `matchmaking` (Q4).

**Delta principale rispetto al catalog live**: solo **2 slug canonici italiani** hanno counterpart identico nel DB (`cacciatore_di_mostri`, `cacciatore_del_vuoto`). Gli altri 16 documenti live sono legacy inglesi/placeholder e sono documentati separatamente come `legacy_live_classes` con `canonical_target=false`.

**Nessun apply DB eseguito**: il registry viene sigillato allo stato documentale. Il sibling script `round18_3d_apply_metadata.py` resta come artefatto storico + guard hard-stop reference.

---

## 2 · Mapping 6 → 5 (LOCKED Q5)

| Design IT | Design EN | Live runtime | Collision |
|:---|:---|:---|:---:|
| Forza | strength | `strength` | — |
| Destrezza | dexterity | `agility` | — |
| Costituzione | constitution | `endurance` | — |
| Intelligenza | intelligence | `intellect` | — |
| Saggezza | wisdom | `intellect` | ⚠ con Intelligenza (accettata da PM) |
| Carisma | charisma | `faith` | — |

Nessun override per-classe. Classi spirituali future (Druido/Sciamano/Astrologo) usano `design_primary_stat_it` + `role_display_it` + `class_role_tags` per differenziazione.

---

## 3 · Role System (LOCKED Q3)

**Runtime atomico**: `Tank`, `DPS`, `Healer`
**Admin-only labels IT** (Q2, non player-facing in questo round): Tank→"Difensore", DPS→"Danneggiante", Healer→"Curatore"
**Class role tags taxonomy** (metadata, non runtime, Q3 separato da `role_tags` R15): `Tank, Frontline, Off-Healer, Off-Tank, DPS, DPS Melee, DPS Ranged, DPS Burst, DPS Caster, Healer, Healer Dedicated, Healer AoE, Support, Buffer, Debuffer, Utility, Stealth, Scout, Summoner, Control, Self-Sustain, Holy, Arcane, Divine, Nature, Elemental, Hybrid`

---

## 4 · Le 27 classi canoniche (slug italiani LOCKED)

Legenda: `⭐ = priority critical` · `✓ = exists_in_live_db (canonical ∩ live)` · `α = has_live_alias` (legacy live counterpart)

| # | slug (IT) | Nome IT | primary IT | primary live | role | class_role_tags principali | Live |
|:---:|:---|:---|:---|:---|:---:|:---|:---:|
| 1 | alchimista | Alchimista | Intelligenza | intellect | DPS | DPS/Support/Utility | α |
| 2 | artificiere | Artificiere | Intelligenza | intellect | DPS | DPS/Utility/Arcane | — |
| 3 | astrologo | Astrologo | Saggezza | intellect | Support | Support/Buffer/Arcane | — |
| 4 | bardo | Bardo | Intelligenza | intellect | Healer_or_DPS ⚠ | Support/Buffer/Debuffer | α *(drift Q8)* |
| 5 | burattinaio | Burattinaio | Intelligenza | intellect | DPS | DPS/Summoner/Control | — |
| 6 | cacciatore_del_sangue | Cacciatore del Sangue | Destrezza | agility | DPS | DPS Melee/Scout/Hybrid | — |
| 7 | cacciatore_del_vuoto ⭐ | Cacciatore del Vuoto | (TBD) | — | TBD | (hidden, Q6) | ✓ |
| 8 | cacciatore_di_mostri ⭐ | Cacciatore di Mostri | (TBD) | — | TBD | (hidden, Q6) | ✓ |
| 9 | cartografo | Cartografo | Intelligenza | intellect | Support | Support/Utility/Scout | — |
| 10 | cavaliere_della_morte | Cavaliere della Morte | Forza | strength | Tank | Tank/Frontline/Arcane | — |
| 11 | cavaliere_di_draghi | Cavaliere di Draghi | Forza | strength | Tank | Tank/Frontline/Elemental | — |
| 12 | cronista | Cronista | Intelligenza | intellect | Support | Support/Utility/Buffer | — |
| 13 | druido | Druido | Carisma | faith | Healer | Healer AoE/Nature | α |
| 14 | fabbro_arcano | Fabbro Arcano | Costituzione | endurance | DPS | DPS Melee/Utility/Arcane | — |
| 15 | giocatore_d_azzardo | Giocatore d'Azzardo | Destrezza | agility | DPS | DPS/Support/Utility | — |
| 16 | guerriero ⭐ | Guerriero | Forza | strength | Tank | Tank/Frontline | α |
| 17 | ladro ⭐ | Ladro | Destrezza | agility | DPS | DPS Melee/Stealth | α |
| 18 | mago | Mago | Intelligenza | intellect | DPS | DPS Caster/Arcane/Control | α |
| 19 | mercante | Mercante | Carisma | faith | Support | Support/Utility | — |
| 20 | monaco | Monaco | Destrezza | agility | DPS | DPS Melee/Self-Sustain/Divine | α |
| 21 | negromante | Negromante | Intelligenza | intellect | DPS | DPS Caster/Summoner/Arcane | α |
| 22 | paladino ⭐ | Paladino | **Carisma** | **faith** *(Q9)* | Tank | **Healer/Tank/Support/Holy** | α |
| 23 | parassita | Parassita | Costituzione | endurance | DPS | DPS/Debuffer/Self-Sustain | — |
| 24 | pittore | Pittore | Carisma | faith | Support | Support/Buffer/Debuffer | — |
| 25 | runista | Runista | Intelligenza | intellect | DPS | DPS Caster/Support/Arcane | — |
| 26 | sciamano | Sciamano | Saggezza | intellect | Healer | Healer/Support/Nature/Elemental | — |
| 27 | sognatore | Sognatore | Intelligenza | intellect | DPS | DPS Caster/Support/Arcane | — |

**Alias evidenti (α)**: 9 slug canonici hanno counterpart legacy con corrispondenza inglese→italiano diretta (`alchemist→alchimista, bard→bardo, druid→druido, mage→mago, monk→monaco, necromancer→negromante, paladin→paladino, warrior→guerriero, rogue→ladro`).

---

## 5 · Canonical ∩ Live (2 documenti)

Solo 2 classi canonical esistono nel DB live con slug **identico**:

| slug | live status | note |
|:---|:---|:---|
| `cacciatore_di_mostri` | `is_playable=false, migration_target_only=true` | HIDDEN (Q6 LOCKED). Design pending R18.3e / R18.ClassRecruitment.Unlock. Nessun `primary_stat`, nessun `base_*`. |
| `cacciatore_del_vuoto` | `is_playable=false, migration_target_only=true` | HIDDEN (Q6 LOCKED). Come sopra. |

**Nota**: erano gli **unici 2 candidati per un ipotetico B3 apply**. Il PM ha scelto **B5 documental-only** ⇒ nessun apply DB eseguito.

---

## 6 · Canonical Design-Only (25 memory-only, non in DB)

Le 25 classi canoniche che **non hanno counterpart nel DB live** (né come slug canonico né come alias effettivo del catalog):

`alchimista, artificiere, astrologo, bardo, burattinaio, cacciatore_del_sangue, cartografo, cavaliere_della_morte, cavaliere_di_draghi, cronista, druido, fabbro_arcano, giocatore_d_azzardo, guerriero, ladro, mago, mercante, monaco, negromante, paladino, parassita, pittore, runista, sciamano, sognatore`

**Nota importante**: alcune di queste hanno un alias evidente con un doc legacy live inglese (es. `guerriero` ↔ `warrior`), ma la migrazione effettiva del catalog live è **fuori scope R18.3d**. Sarà valutata in `R18.3e — Canonical IT ↔ Legacy EN Class Bridge` (backlog aperto).

---

## 7 · Legacy Live Classes (16, documentale, `canonical_target=false`)

Documenti live NON canonici, mantenuti nel DB senza modifiche runtime. Nessuno di questi è nella lista canonica LOCKED PM.

| # | live_slug | alias_target | needs_PM_review | note |
|:---:|:---|:---:|:---:|:---|
| 1 | warrior | guerriero | N | alias evidente |
| 2 | rogue | ladro | N | alias evidente |
| 3 | mage | mago | N | alias evidente |
| 4 | monk | monaco | N | alias evidente |
| 5 | paladin | paladino | N | alias evidente; `primary_stat=faith` LIVE accettato (Q9) |
| 6 | druid | druido | N | alias evidente |
| 7 | necromancer | negromante | N | alias evidente (`is_active=false`) |
| 8 | **bard** | **bardo** | **Y** | ⚠ `role=Support` NON in `VALID_ROLES` — **drift Q8**, backlog aperto |
| 9 | alchemist | alchimista | N | alias evidente |
| 10 | priest | *null* | Y | no canonical counterpart; ~190 adv live |
| 11 | ranger | *null* | Y | ambiguous target; ~175 adv live |
| 12 | warlock | *null* | Y | ambiguous target; ~128 adv live |
| 13 | assassin | *null* | Y | ambiguous; `is_active=false`, 0 adv live |
| 14 | berserker | *null* | Y | ambiguous; `is_active=false`, 3 adv live |
| 15 | recruit_unassigned | *null* | N | placeholder interno |
| 16 | test-class-5e0064 | *null* | N | doc di test |

**Nessun runtime touch** su questi documenti. Tutti conservano `primary_stat`, `role`, `base_*`, `is_playable`, `is_active` originali.

---

## 8 · Paladino — `primary_stat=faith` accettato (Q9 LOCKED)

Il PM ha accettato come **definitivo** il valore live `paladin.primary_stat=faith` (fonte: seed R15 SEALED `round15_seed_class_identity.py:71`). Il registry documenta:

```
slug:                       paladino
class_name_it:              Paladino
design_primary_stat_it:     Carisma
design_secondary_stats_it:  [Forza, Costituzione]
mapped_primary_stat_live:   faith           ← LOCKED da catalog live SoT
mapped_secondary_stats_live: [strength, endurance]
role_atomic_candidate:      Tank
role_display_it:            Healer/Tank
class_role_tags:            [Healer, Tank, Support, Holy]
priority:                   critical
alias_from_live_slug:       paladin
notes:                      PM Q9 LOCKED — do NOT touch R15 seed;
                            hybrid Tank/Support/Holy via class_role_tags
```

Il seed R15 non è stato modificato. Nessun impatto runtime.

---

## 9 · Bardo — drift documentato (Q8)

Il documento live `bard` ha `role="Support"`, valore **non incluso** in `VALID_ROLES=(Tank, DPS, Healer)`. Il PM ha scelto l'opzione **(c) lascia drift e documenta**.

**Registry canonical entry `bardo`**:
- `role_atomic_candidate = "Healer_or_DPS"` (hint pending, non applicato)
- `role_display_it = "Support"`
- `class_role_tags = ["Support", "Buffer", "Debuffer", "Utility"]`
- `drift_flag = "bard_alias_role_support_not_in_valid_roles"`
- `needs_PM_review = true`

**Registry legacy_live entry `bard`**: contiene stesso `drift_flag` + `alias_target_canonical_slug=bardo`.

**Backlog**: entry `R18.3d.followup — Bard Role Drift Resolution` (P3) aperta in `/app/memory/backlog.md`.

---

## 10 · Nessun apply DB eseguito (dichiarazione esplicita)

Il registry JSON è la **fonte documentale** ufficiale. Non è la source-of-truth runtime.

- **Zero DB write** eseguiti in Phase B.
- Nessun documento `adventurer_classes` è stato modificato.
- Nessun evento `R18_3D_METADATA_APPLIED` è presente in `audit_log`.
- `audit_log` count invariato (baseline 11896 = post-seal 11896, verificato).
- I 5 field metadata SAFE (`role_display_it, class_role_tags, design_primary_stat_it, design_secondary_stats_it, stat_role_registry_source_round`) **non esistono** in alcun documento live.
- Il modulo Python `stat_role_registry.py` è **UNWIRED** — nessun runtime consumer lo importa.
- Il sibling script `round18_3d_apply_metadata.py` è conservato come **artefatto documentale** + reference per il guard hard-stop; non è mai stato eseguito con `--apply`.

---

## 11 · Audit trail & Riferimenti

| Elemento | Path |
|:---|:---|
| Decision lock PM (MD) | `/app/memory/r18_3d_phase_b_pm_decisions.md` |
| Decision lock PM (JSON) | `/app/memory/r18_3d_phase_b_pm_decisions.json` |
| Registry JSON companion | `/app/memory/r18_3d_stat_role_mapping_registry.json` |
| MD companion (this file) | `/app/memory/r18_3d_stat_role_mapping_registry.md` |
| Loader Python UNWIRED | `/app/backend/app/core/stat_role_registry.py` |
| Sibling script (never applied) | `/app/backend/app/scripts/round18_3d_apply_metadata.py` |
| Test suite | `/app/backend/tests/backend_r18_3d_stat_role_registry_test.py` |
| Seal registry (SHA256) | `/app/memory/r18_3d_seal_registry.json` |
| Backlog `R18.3d.followup Bard` | `/app/memory/backlog.md` |
| Backlog `R18.3e Bridge` | `/app/memory/backlog.md` |
| Closure report | `/app/memory/r18_3d_phase_b_final_closure_report.md` |

**SHA256** dei 5 file sigillati registrati in `/app/memory/r18_3d_seal_registry.json`.

---

**R18.3d Phase B = CLOSED & SEALED (documental-only) — 2026-07-05T18:05:00Z UTC**
