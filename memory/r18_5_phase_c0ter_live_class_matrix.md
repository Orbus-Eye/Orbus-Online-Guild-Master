# R18.5 Phase C0-ter — Live Class Matrix Integration (DOCUMENTAL ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Fase**: **C0-ter** — Integrazione matrice classi live (5 classi) con main stat + armor/weapon proficiency + identità narrativa PM
- **Locked at UTC**: `2026-07-06T20:00:00Z`
- **Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Predecessori autoritativi**:
  - `r18_5_gate2_pm_decisions.md/.json` (Gate 2 — resolve delle 3 decisioni bloccanti)
  - `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json` (C0-bis — scale-up + matrici proficiency proposte)
  - `r18_5_phase_b_gate1_pm_decisions.md/.json` (Gate 1 — SQ11-SQ18)
- **Successore**: NON autorizzato — Phase C tech dry-run resta BLOCCATO fino a nuovo gate PM.

## 0. Scope C0-ter

Registrare integralmente le **5 classi live** con:
- Main stat (Gate 2 sez. 7 policy)
- Armor proficiency (Gate 2 sez. 5 hard-block)
- Weapon proficiency (Gate 2 sez. 6 hard-block)
- Identità narrativa PM verbatim
- Vietati espliciti PM

**Nessuna decisione nuova**. Ogni valore è **PM verbatim** dal messaggio Gate 2 corrente.

## 1. Warrior (Guerriero)

- **Main stat**: **Forza**
- **Armor proficiency**: **maglia**, **piastre**
- **Weapon proficiency**: **spada**, **ascia**, **martello**, **scudo**, **lancia**, **arma_in_asta**
- **Identità (PM verbatim)**: *frontliner, uso naturale di piastre e scudi*
- **Vietato**: stoffa/cuoio come equip principale, focus/tomi/bastoni magici

## 2. Rogue (Ladro)

- **Main stat**: **Destrezza**
- **Armor proficiency**: **cuoio**
- **Weapon proficiency**: **pugnale**, **spada**, **balestra**
- **Identità (PM verbatim)**: *danno agile, equip leggero*
- **Vietato**: maglia/piastre, scudo, bastoni/tomi/focus

## 3. Mage (Mago)

- **Main stat**: **Intelligenza**
- **Armor proficiency**: **stoffa**
- **Weapon proficiency**: **bastone**, **tomo**, **focus**, **pugnale**
- **Identità (PM verbatim)**: *caster arcano, fragile ma potente*
- **Vietato**: cuoio/maglia/piastre, scudo, armi pesanti

## 4. Priest

- **Main stat**: **Saggezza**
- **Armor proficiency**: **stoffa**
- **Weapon proficiency**: **bastone**, **martello**, **focus**, **reliquia**
- **Identità (PM verbatim)**: *caster sacro/support, NON Cleric drift, NON Warrior con cure*
- **Vietato**: piastre (in questa fase), spade/asce/pugnali come identità primaria

## 5. Ranger

- **Main stat**: **Destrezza**
- **Armor proficiency**: **cuoio**, **maglia**
- **Weapon proficiency**: **arco**, **balestra**, **spada**, **pugnale**, **lancia**
- **Identità (PM verbatim)**: *combattente mobile a distanza*
- **Vietato**: piastre, focus/tomi/bastoni da caster

---

## 6. Cross-tabella — Class × Armor proficiency (5 classi × 4 armor types)

Regola Gate 2 sez. 5: ✅ = classe **può** equipaggiare, ❌ = **hard block** runtime.

|            | stoffa | cuoio | maglia | piastre |
|:---|:---:|:---:|:---:|:---:|
| **Warrior** | ❌ | ❌ | ✅ | ✅ |
| **Rogue**   | ❌ | ✅ | ❌ | ❌ |
| **Mage**    | ✅ | ❌ | ❌ | ❌ |
| **Priest**  | ✅ | ❌ | ❌ | ❌ |
| **Ranger**  | ❌ | ✅ | ✅ | ❌ |

### Osservazioni di coerenza
- **stoffa** → solo Mage e Priest (caster).
- **cuoio** → solo Rogue e Ranger (agili).
- **maglia** → solo Warrior e Ranger (ibrido difesa-mobilità).
- **piastre** → solo Warrior (frontliner).
- Priest esclude piastre "in questa fase" (verbatim PM) — riservato per possibile futura variante.

## 7. Cross-tabella — Class × Weapon proficiency (5 classi × 16 weapon families)

Regola Gate 2 sez. 6: ✅ = weapon proficiency, ❌ = hard block runtime.

| Weapon family | Warrior | Rogue | Mage | Priest | Ranger |
|:---|:---:|:---:|:---:|:---:|:---:|
| **spada**         | ✅ | ✅ | ❌ | ❌ | ✅ |
| **ascia**         | ✅ | ❌ | ❌ | ❌ | ❌ |
| **martello**      | ✅ | ❌ | ❌ | ✅ | ❌ |
| **pugnale**       | ❌ | ✅ | ✅ | ❌ | ✅ |
| **arco**          | ❌ | ❌ | ❌ | ❌ | ✅ |
| **balestra**      | ❌ | ✅ | ❌ | ❌ | ✅ |
| **bastone**       | ❌ | ❌ | ✅ | ✅ | ❌ |
| **tomo**          | ❌ | ❌ | ✅ | ❌ | ❌ |
| **focus**         | ❌ | ❌ | ✅ | ✅ | ❌ |
| **strumento**     | ❌ | ❌ | ❌ | ❌ | ❌ |
| **falce**         | ❌ | ❌ | ❌ | ❌ | ❌ |
| **lancia**        | ✅ | ❌ | ❌ | ❌ | ✅ |
| **arma_in_asta**  | ✅ | ❌ | ❌ | ❌ | ❌ |
| **scudo**         | ✅ | ❌ | ❌ | ❌ | ❌ |
| **reliquia**      | ❌ | ❌ | ❌ | ✅ | ❌ |
| **trinket**       | ❌ | ❌ | ❌ | ❌ | ❌ |

### Verifica coerenza (weapon per classe)

| Classe | Count weapon | Weapon list |
|---|:---:|---|
| Warrior | 6 | spada, ascia, martello, scudo, lancia, arma_in_asta |
| Rogue | 3 | pugnale, spada, balestra |
| Mage | 4 | bastone, tomo, focus, pugnale |
| Priest | 4 | bastone, martello, focus, reliquia |
| Ranger | 5 | arco, balestra, spada, pugnale, lancia |

- **scudo** → esclusivo Warrior (coerente con "frontliner + uso naturale di scudi").
- **reliquia** → esclusiva Priest (coerente con "caster sacro/support").
- **arma_in_asta** → esclusiva Warrior.
- **ascia** → esclusiva Warrior.
- **tomo** → esclusivo Mage (coerente con caster arcano).
- **arco** → esclusivo Ranger (coerente con "combattente mobile a distanza").

## 8. Weapon families non assegnate a classi live (`PENDING PM approval`)

3 famiglie su 16 **non sono coperte** da nessuna delle 5 classi live PM:

| Weapon family | Stato | Nota |
|---|---|---|
| **strumento** | non assegnato | Candidato per **Bard drift** (in backlog) o classe futura (musicista/bardo/scaldo). `PENDING PM approval` |
| **falce** | non assegnato | Candidato per classe futura (reaper/necromante/druido?). `PENDING PM approval` |
| **trinket** | non assegnato | Categoria "accessorio generico" — possibile **universal** (utilizzabile da tutte le classi) o riservato a classi future. `PENDING PM approval` |

**Nota governance**: Emergent NON assegna autonomamente queste 3 famiglie. Verranno lockate dal PM in future gate.

## 9. Impact analysis futuro (documentale, non implementato in C0-ter)

Il futuro **Phase C tech dry-run** (BLOCCATO fino a nuovo gate PM) dovrà gestire i seguenti impatti runtime.

### 9.1 Endpoint `/api/adventurers/{id}/eligible-items` (R18.4.followup Phase B/C, SEALED)

Attualmente espone `compatibility_state` 4-state (universal / recommended / not_recommended / blocked). Dovrà estendere:

- Nuovo controllo pre-4-state: **proficiency hard block**.
- Nuovi `reason_code` in payload:
  - `proficiency_missing_armor`
  - `proficiency_missing_weapon`
- Se hard block → `compatibility_state = "blocked"` con reason_code proficiency.

**Attenzione**: `derive_ui_4state` è **SEALED** (R18.4.followup Phase C). L'estensione richiederà:
- Nuovo gate PM per aprire il sigillo (o nuovo file non-sealed di wrapping)
- Preservare 36 SHA256 esistenti se possibile con approccio wrapping

### 9.2 UI `ItemCompatibilityBadge` (SEALED R18.4.followup C)

Attualmente 4-state (Universale / Consigliato / Non consigliato / Bloccato). Opzioni:

- **Opzione A**: 5° stato "Non equipaggiabile per proficiency" (nuovo badge dedicato).
- **Opzione B**: Integrare in "Bloccato" con tooltip che espone `reason_code` (proficiency_missing_armor/weapon).

**Preferenza PM `PENDING` — da decidere in prossimo gate**.

### 9.3 Auto-equip logic (`app/equipment/auto_equip.py`, non-sealed)

Attualmente: skip con warning su compatibility mismatch.

Cambio richiesto: **hard block** su proficiency mismatch (armor o weapon). L'auto-equip non deve tentare di equipaggiare item bloccati da proficiency.

### 9.4 Serializer `item_public()` (non-sealed)

Attualmente NON espone `armor_type` né `weapon_family` come fields dedicati. Dovranno essere aggiunti per abilitare il proficiency check runtime:

```json
{
  "id": "...",
  "slot_type": "weapon",
  "weapon_family": "spada",   // nuovo
  "armor_type": null,          // nuovo (null per weapon)
  ...
}
```

E per armor:
```json
{
  "id": "...",
  "slot_type": "chest",
  "weapon_family": null,       // null per armor
  "armor_type": "piastre",     // nuovo
  ...
}
```

**Attenzione**: `item_public()` potrebbe essere SEALED — verifica in Phase C tech dry-run, gate PM richiesto se sigillo da rompere.

### 9.5 DB backfill richiesto

Nuovo dry-run script Phase C tech:
- `round18_5_backfill_weapon_family_dryrun.py` — mappa item.slot_type=weapon → weapon_family da parsing metadata/name/subtype esistente. Output: report divergenze + proposta.
- `round18_5_backfill_armor_type_dryrun.py` — analogo per armor.
- Idempotency: `no_change_skip` counter.

## 10. Self-check Phase C0-ter

- [x] 5 classi live PM verbatim registrate (Warrior, Rogue, Mage, Priest, Ranger)
- [x] Main stat per classe (Forza, Destrezza, Intelligenza, Saggezza, Destrezza)
- [x] Armor proficiency per classe (2, 1, 1, 1, 2 armor types)
- [x] Weapon proficiency per classe (6, 3, 4, 4, 5 weapon families)
- [x] Identità narrativa PM verbatim per ogni classe
- [x] Vietati espliciti PM per ogni classe
- [x] Cross-tabella armor 5×4 completa
- [x] Cross-tabella weapon 5×16 completa
- [x] Coerenza cross-tabelle vs identità PM verificata
- [x] Weapon families non assegnate (strumento, falce, trinket) → `PENDING PM approval` esplicito
- [x] Impact analysis Phase C tech futuro documentato (endpoint, UI, auto-equip, serializer, DB backfill)
- [x] Naming canonical Mage/Priest usato ovunque (no Wizard/Cleric drift)
- [x] Nessuna decisione nuova introdotta — solo integrazione di PM verbatim
- [x] Zero DB writes, zero code changes, sigilli 36/36 intatti

**Phase C0-ter CLOSED**. Le 5 classi live sono ora **matrice pronta** per il futuro Phase C tech dry-run (BLOCCATO fino a nuovo gate PM esplicito).

## 11. Note per il PM

- Le tre weapon families non coperte (**strumento**, **falce**, **trinket**) restano **congelate**. Se il PM le vuole associare a Bard drift, classe futura, o universal (per trinket), serve un nuovo gate.
- La rottura del sigillo `derive_ui_4state` o `item_public()` per aggiungere proficiency check richiede **gate PM dedicato** con motivazione esplicita e preservation plan dei 36 sigilli byte-identical (o accettazione della loro modifica con nuovo hash registry).
- I 6 remaining non-blocking items (Gate 2 sez. 9) restano audit-only.
