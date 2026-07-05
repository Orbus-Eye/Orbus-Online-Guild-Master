# R18.3d — Phase B · PM Decision Lock

**Round**: `R18.3d` (Stat/Role Mapping Registry)
**Fase**: **B — Design-First Staged Apply (B0 Decision Lock)**
**Data**: 2026-07-05T17:15:00Z UTC
**Author**: e1_dev (verbatim da response PM su Open Questions Phase A)
**Status**: 🔒 **LOCKED — every deviation requires new PM gate**

---

## Decisioni PM (verbatim)

### Q1 — Metadata SAFE append-only
**PM decision**: **SÌ** — aggiunta 5 field SAFE su `adventurer_classes` autorizzata.

**Fields ammessi**: `role_display_it`, `class_role_tags`, `design_primary_stat_it`, `design_secondary_stats_it`, `stat_role_registry_source_round`.

**Vincoli**: append-only, `$unset`-reversibili, zero runtime, zero player-facing.

### Q2 — `role_display_it` visibility
**PM decision**: **(b) admin-only / API introspection**. `role_display_it` NON player-facing in questo round. UI slitta a `R18.3d.v2`.

### Q3 — Relazione `class_role_tags` ↔ `role_tags` R15
**PM decision**: **(b) field separati**. `role_tags` R15 invariato. `class_role_tags` = metadata design/admin. Nessuna unificazione runtime, nessuna sostituzione automatica.

### Q4 — Registry source-of-truth
**PM decision**: **(b) `adventurer_classes` resta SoT live, registry = solo doc + audit**. NON collegare registry a `auto-equip` / `xp_modifier` / `combat` / `sorting` / `recruitment` / `matchmaking`.

### Q5 — Mapping 6→5 confermato
**PM decision**: mapping LOCKED per R18.3d:

| Design IT | Live 5-stat |
|:---|:---|
| Forza | strength |
| Destrezza | agility |
| Costituzione | endurance |
| Intelligenza | intellect |
| Saggezza | intellect (collisione accettata) |
| Carisma | faith |

**Nota classi spirituali future** (Druido/Sciamano): NO override per-classe, NO sesta stat. Usa `design_primary_stat_it`, `role_display_it`, `class_role_tags`, focus, descrizione per differenziare.

### Q6 — Hidden classes
**PM decision**: **(a) tenerle hidden**. `cacciatore_di_mostri` e `cacciatore_del_vuoto` restano `is_playable=false`, `migration_target_only=true`, hidden. Riapertura in round futuro dedicato (`R18.3e` / `R18.ClassRecruitment.Unlock`).

### Q7 — R18.4 dependency
**PM decision**: **SÌ** — R18.4 può partire senza `role_display_it` player-facing. Registry / admin metadata basta per R18.4.

### Q8 — Bard drift
**PM decision**: **(c) lascia drift e documenta in Phase B**. NO fix su `bard.role` ora. Nel registry:
- `role_atomic_candidate` (proposta, probabilmente "Healer" o "DPS") ma NON applicato
- `role_display_it = "Support"` (se coerente)
- `class_role_tags = ["Support", ...]`
- Backlog entry obbligatoria: **`R18.3d.followup — Bard Role Drift Resolution`** (Status BACKLOG)

### Q9 — Paladin faith
**PM decision**: **(a) accetta live `faith` come definitivo + (c) `class_role_tags`**. Paladin resta `primary_stat=faith` (catalog live). NON toccare R15 seed. Nel registry:

```
design_primary_stat_it = "Carisma"
mapped_primary_stat_live = "faith"
role_display_it = "Healer/Tank"
class_role_tags = ["Healer", "Tank", "Support", "Holy"]
```

### Q10 — 27 canonical vs 18 live
**PM decision**: 27 canoniche = target design. Phase B gestisce:
- 18 classi live DB → registry con catalog metadata candidate
- 9 classi mancanti → registry memory-only con `design_only=true`
- NO seed nuove classi, NO nuove classi in DB, NO recruitment change

**Nota agente (per PM refinement)**: il conteggio "27 canonical - 18 live = 9 design-only" assume che tutte le 18 live siano canonical-covered. L'analisi Phase A ha invece rilevato che dei 18 doc live, solo 11 hanno counterpart nel canonical set 27 (`alchemist, bard, cacciatore_del_vuoto, cacciatore_di_mostri, druid, mage, monk, necromancer, paladin, rogue, warrior`). I restanti 7 sono orphan live (`priest, ranger, warlock, assassin, berserker, recruit_unassigned, test-class-5e0064`) e le canonical mancanti da DB sono effettivamente **16** (non 9). Registry Phase B documenta entrambe le viste con trasparenza; se il PM conferma l'interpretazione "27 − 18 = 9" verrà applicata pragmaticamente sulla struttura registry, altrimenti la vista `canonical-missing-16` sarà quella autoritativa.

---

## Vincoli assoluti LOCKED (Phase B)

- ❌ NO modifiche a: `primary_stat`, `role`, `base_*`, `VALID_ROLES`, `is_playable`, `is_active`, `is_canonical`
- ❌ NO combat math change, auto-equip change, XP modifier change
- ❌ NO recruitment visibility change, hidden class unlock
- ❌ NO player-facing UI change
- ❌ NO schema migration, NO class seed, NO hard delete
- ❌ NO touch agli 8 sigilli R18.Reset.1b + al SEALED test file R18.Reset.2

---

**Decision Lock chiuso — utilizzato come contract per B1→B5.**
