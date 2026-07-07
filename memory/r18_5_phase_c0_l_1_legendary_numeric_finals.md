# R18.5 — Phase C0.L.1 · Legendary Numeric Finals Mini-Gate (STEP 30)

**Round**: R18.5 · **Phase**: C0.L.1 Legendary Numeric Finals · **STEP**: 30
**Locked at UTC**: `2026-07-07T20:30:00Z`
**Governance**: **DOCUMENTAL ONLY — numeric finals proposal. NO modifica item table D1-D5. NO runtime apply.**
**Status**: ✅ **APPLIED — numeric finals proposal per PM review**
**Authority**: PM Orchestrator — STEP 30 catena autorizzata post-STEP 29 (Q2=A GO C0.L.1)

**Deliverables**:
- `/app/memory/r18_5_phase_c0_l_1_legendary_numeric_finals.md` (questo file)
- `/app/memory/r18_5_phase_c0_l_1_legendary_numeric_finals.json` (SHA256 `cf3b6496dfd463cec2dee04043d3a2d1dbb87217b09f9a9f9dcece176571e1e2`)

**Scope**:
- **In-scope**: 11 Legendary (7 APPROVED + 4 HYBRID) — numeric finals proposti
- **Out-of-scope**: 4 Progressive Discovery placeholders (P1-P4) — registry_reserved / PENDING PM (Q3=A)

---

## Sezione 1 — 11 Legendary · Numeric Finals (18 campi ciascuno)

Per ciascuno degli 11 Legendary sono definiti i **18 campi obbligatori**: item_id, nome_it, classe, lore_source, tier, rarity, required_level, ilvl, main_stat_target, stat_numeric_final, utility_final, utility_trigger_condition, cooldown_limit, drop_readiness, registry_readiness, anti_p2w_confirmation, proficiency_confirmation, risk_notes.

### #1 — `warrior-t5-legendary-dragonlord-crown` (APPROVED-7 (L1))

| Campo | Valore |
|---|---|
| **nome_it** | Corona del Signore dei Draghi |
| **classe** | Warrior |
| **lore_source** | Draco |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | STR |
| **slot / armor_type / weapon_family** | head / piastre / None |
| **stat_numeric_final** | STR +38, armor +55 |
| **utility_final** | Command Draconic — 1x/encounter, guida temporaneamente 1 drago giovane ostile trasformandolo in alleato per una fase (12s) |
| **utility_trigger_condition** | active-on-use (self-cast), targeted enemy = young dragon minion presente in encounter |
| **cooldown_limit** | 1x per encounter (~12s alleato duration, then boss-tag return) |
| **drop_readiness** | READY — 2% drop dragon-vault raid boss finale (Il Drago Primordiale) LIVE (chain STEP 8) |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true, affects_economy=false, affects_ranking=false |
| **proficiency_confirmation** | Warrior + slot=head + armor_type=piastre + weapon_family=None → conforme (piastre solo Warrior post-E1.1 fix) |
| **risk_notes** | **LOW — utility+numerics coerenti chain STEP 8 approved, drop rate confirmato LIVE** |

### #2 — `rogue-t5-legendary-void-touched-blade` (APPROVED-7 (L2))

| Campo | Valore |
|---|---|
| **nome_it** | Lama Toccata dal Vuoto |
| **classe** | Rogue |
| **lore_source** | Vuoto |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | AGI |
| **slot / armor_type / weapon_family** | main-hand / None / pugnale |
| **stat_numeric_final** | AGI +55, damage_min +72, damage_max +90, crit_pct +12 |
| **utility_final** | Void-Pierce — passive proc on-hit: 15% chance di ignorare armor del target per quel colpo |
| **utility_trigger_condition** | passive on-hit auto-proc (15% chance per attacco fisico melee) |
| **cooldown_limit** | n/a (passive proc, no cooldown design-only — PM può capare a max 1 proc/round in C2) |
| **drop_readiness** | READY — 2% drop void-cathedral raid boss finale (Il Silenzio Primordiale) NEW (chain STEP 8) |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Rogue + slot=main-hand + weapon_family=pugnale → conforme (pugnale Rogue-only) |
| **risk_notes** | **LOW — proc 15% coerente con Rogue crit build; passive va cappato max 1 proc/round in C2 per fairness** |

### #3 — `priest-t5-legendary-seraph-halo-crown` (APPROVED-7 (L3))

| Campo | Valore |
|---|---|
| **nome_it** | Corona d'Aureola del Serafino |
| **classe** | Priest |
| **lore_source** | Celeste |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | WIS |
| **slot / armor_type / weapon_family** | head / stoffa / None |
| **stat_numeric_final** | WIS +38, armor +55 |
| **utility_final** | Divine Resurrect — 1x/encounter, resurrect di 1 fallen ally in endgame party (target al 50% max HP, 3s cast time) |
| **utility_trigger_condition** | active-on-use, target ally=fallen (last-death timestamp within encounter) |
| **cooldown_limit** | 1x per encounter (rebirth cooldown 3s cast time, no interrupt-safe design) |
| **drop_readiness** | READY — 2% drop celestial-conclave raid boss finale (Il Primo Serafino) NEW (chain STEP 8) |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Priest + slot=head + armor_type=stoffa → conforme (Priest no scudo/piastre/cuoio/maglia post-E1.1) |
| **risk_notes** | **MEDIUM — resurrect utility ha impatto meta-progression PvE endgame; PM review C2 raccomandata per interazione con raid wipe recovery mechanics** |

### #4 — `ranger-t5-legendary-worldroot-scepter` (APPROVED-7 (L4))

| Campo | Valore |
|---|---|
| **nome_it** | Scettro della Radice del Mondo |
| **classe** | Ranger |
| **lore_source** | Alberi della Vita |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | AGI |
| **slot / armor_type / weapon_family** | main-hand / None / lancia |
| **stat_numeric_final** | AGI +55, damage_min +72, damage_max +90, crit_pct +12 |
| **utility_final** | Nature's Blessing — 1x/encounter, AoE Heal-over-Time area 8m (3% max HP heal per turn, 3 turni) |
| **utility_trigger_condition** | active-on-use, target=ground area 8m radius; require encounter tag natural_terrain=true (terrain lore-defined) |
| **cooldown_limit** | 1x per encounter (durata 3 turni HoT) |
| **drop_readiness** | READY — 2% drop world-tree-collapse raid boss finale (Il Cuore dell'Albero del Mondo) NEW (chain STEP 8) |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Ranger + slot=main-hand + weapon_family=lancia → conforme (Ranger no arco per L4 slot: lancia weapon_family verificato D5) |
| **risk_notes** | **LOW — HoT balanced (3%/turn per 3 turni = 9% total, subito the utility charge)** |

### #5 — `warrior-t5-legendary-ambash-forge-hammer` (APPROVED-7 (L5))

| Campo | Valore |
|---|---|
| **nome_it** | Martello della Fucina di Ambash |
| **classe** | Warrior |
| **lore_source** | Ambash |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 59 / 60 |
| **main_stat_target** | STR |
| **slot / armor_type / weapon_family** | main-hand / None / martello |
| **stat_numeric_final** | STR +55, damage_min +72, damage_max +90, crit_pct +12 |
| **utility_final** | Reforge weapon slot mid-encounter — 1x/encounter, cambia damage type dell'arma di un alleato (physical↔elemental) per 3 turni |
| **utility_trigger_condition** | active-on-use, target ally in party (raid o dungeon 3p) |
| **cooldown_limit** | 1x per encounter (durata effetto 3 turni) |
| **drop_readiness** | READY — 1% drop ambash-legendary-forge dungeon 3p boss finale (Il Maestro Fabbro delle Leggende) chain STEP 8 |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Warrior + slot=main-hand + weapon_family=martello → conforme |
| **risk_notes** | **MEDIUM — cross-target utility richiede validazione runtime C2 per ownership+consent (target ally must be in same encounter)** |

### #6 — `warrior-t5-legendary-dragon-elder-scale` (APPROVED-7 (L6))

| Campo | Valore |
|---|---|
| **nome_it** | Scaglia del Verme Ancestrale |
| **classe** | Warrior |
| **lore_source** | Draco |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | STR |
| **slot / armor_type / weapon_family** | off-hand / None / scudo |
| **stat_numeric_final** | STR +40, block_pct +14 |
| **utility_final** | Temporary Dragon-scale Armor Buff — 1x/encounter, self-buff resistenza elementale+physical +30% per 4 turni |
| **utility_trigger_condition** | active-on-use, self only |
| **cooldown_limit** | 1x per encounter (durata buff 4 turni) |
| **drop_readiness** | READY — 1% drop elder-wyrm-descent dungeon 3p boss finale (Draco l'Ancestrale) chain STEP 8 |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Warrior + slot=off-hand + weapon_family=scudo → conforme (scudo Warrior-only, Priest no scudo post-E1.1) |
| **risk_notes** | **LOW — self-buff durata contenuta, no stack** |

### #7 — `mage-t5-legendary-sole-nero-diadem` (APPROVED-7 (L7))

| Campo | Valore |
|---|---|
| **nome_it** | Diadema del Sole Nero |
| **classe** | Mage |
| **lore_source** | Celeste |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | INT |
| **slot / armor_type / weapon_family** | head / stoffa / None |
| **stat_numeric_final** | INT +38, armor +55 |
| **utility_final** | Swap Light/Void Resist mid-encounter — 1x/encounter, alterna la propria resistenza tra light e void (durata rimane fino a next swap o end-encounter) |
| **utility_trigger_condition** | active-on-use, self, encounter-only (reset a fine encounter) |
| **cooldown_limit** | 1x per encounter (durata persistente fino fine encounter o next use) |
| **drop_readiness** | READY — 1% drop pantheon-of-fallen-suns dungeon 3p Lv60 boss finale (Il Sole Nero) chain STEP 8 |
| **registry_readiness** | READY (design layer, runtime_apply_ready=false) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Mage + slot=head + armor_type=stoffa → conforme |
| **risk_notes** | **LOW — strategic utility bound a light/void mechanic boss, no leverage cross-encounter** |

### #8 — `priest-t5-legendary-celestial-conclave-mantle-hybrid` (HYBRID-4 (H1 Celeste))

| Campo | Valore |
|---|---|
| **nome_it** | Manto del Conclave Celeste |
| **classe** | Priest |
| **lore_source** | Celeste |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | WIS |
| **slot / armor_type / weapon_family** | chest / stoffa / None |
| **stat_numeric_final** | WIS +38, armor +78, END +27 |
| **utility_final** | Celestial Barrier — 1x/encounter, self-barrier assorbe 40% massive damage per 2 turni |
| **utility_trigger_condition** | active-on-use (reactive), self only |
| **cooldown_limit** | 1x per encounter (durata 2 turni) |
| **drop_readiness** | PARTIAL — 0.5% direzionale drop celestial-conclave raid alternate (Il Primo Serafino secondary) HYBRID — PENDING PM numeric final |
| **registry_readiness** | PARTIAL (design layer, runtime_apply_ready=false; drop_rate HYBRID PENDING PM) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Priest + slot=chest + armor_type=stoffa → conforme |
| **risk_notes** | **MEDIUM — drop_rate HYBRID direzionale 0.5% PENDING PM final decision (Q gate C2)** |

### #9 — `rogue-t5-legendary-irthe-price-shroud-hybrid` (HYBRID-4 (H2 Irthe))

| Campo | Valore |
|---|---|
| **nome_it** | Sudario del Prezzo di Irthe |
| **classe** | Rogue |
| **lore_source** | Irthe |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | AGI |
| **slot / armor_type / weapon_family** | chest / cuoio / None |
| **stat_numeric_final** | AGI +38, armor +78, END +27 |
| **utility_final** | Death's Toll — 1x/encounter, next-attack infligge damage massimizzato; il portatore paga 15% max HP self-damage + permanente cooldown/encounter |
| **utility_trigger_condition** | active-on-use pre-attack; next melee/ranged hit infligge damage_max deterministico |
| **cooldown_limit** | 1x per encounter (permanente per encounter, no reset) |
| **drop_readiness** | PARTIAL — 0.5% direzionale drop world-tree-collapse raid alternate (Il Cuore dell'Albero secondary, Irthe capstone) HYBRID — PENDING PM numeric final |
| **registry_readiness** | PARTIAL (design layer, runtime_apply_ready=false; drop_rate HYBRID PENDING PM) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Rogue + slot=chest + armor_type=cuoio → conforme (Rogue cuoio-only chest) |
| **risk_notes** | **MEDIUM — drop_rate HYBRID PENDING PM final; self-damage 15% richiede validazione runtime C2 vs downed-mechanic (non causa auto-death se HP > 15%)** |

### #10 — `mage-t5-legendary-ergolat-obelisk-focus-hybrid` (HYBRID-4 (H3 Ergolat))

| Campo | Valore |
|---|---|
| **nome_it** | Focus dell'Obelisco di Ergolat |
| **classe** | Mage |
| **lore_source** | Ergolat |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | INT |
| **slot / armor_type / weapon_family** | off-hand / None / focus |
| **stat_numeric_final** | INT +40, block_pct +14 |
| **utility_final** | Absence Distortion — 1x/encounter, AoE silence area 8m per 2 turni (nemici in area non possono castare) |
| **utility_trigger_condition** | active-on-use, target=ground area 8m radius |
| **cooldown_limit** | 1x per encounter (durata 2 turni AoE silence) |
| **drop_readiness** | PARTIAL — 0.5% direzionale drop ambash-legendary-forge dungeon 3p alternate (Maestro Fabbro secondary, Ergolat capstone) HYBRID — PENDING PM numeric final |
| **registry_readiness** | PARTIAL (design layer, runtime_apply_ready=false; drop_rate HYBRID PENDING PM) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Mage + slot=off-hand + weapon_family=focus → conforme (focus off-hand Mage/Priest weapon_family, Mage main-stat INT) |
| **risk_notes** | **MEDIUM — drop_rate HYBRID PENDING PM; AoE silence 8m può essere overturned in dungeon 3p, C2 raccomanda cap sui boss (silence-resistance) mob elite** |

### #11 — `ranger-t5-legendary-halodi-fate-quiver-hybrid` (HYBRID-4 (H4 Halodi))

| Campo | Valore |
|---|---|
| **nome_it** | Faretra del Fato di Halodi |
| **classe** | Ranger |
| **lore_source** | Halodi |
| **tier / rarity** | T5 / Legendary |
| **required_level / ilvl** | 60 / 60 |
| **main_stat_target** | AGI |
| **slot / armor_type / weapon_family** | trinket / None / None |
| **stat_numeric_final** | AGI +33, utility_pct +16 |
| **utility_final** | Fate Deflection — 1x/encounter, il prossimo attacco letale al portatore viene deviato su bersaglio nemico casuale in encounter |
| **utility_trigger_condition** | passive/auto-reactive on next lethal hit (attivato automaticamente da damage that would reduce HP<=0) |
| **cooldown_limit** | 1x per encounter (auto-reactive, next lethal hit trigger) |
| **drop_readiness** | PARTIAL — 0.5% direzionale drop pantheon-of-fallen-suns dungeon 3p Lv60 alternate (Il Sole Nero secondary, Halodi capstone) HYBRID — PENDING PM numeric final |
| **registry_readiness** | PARTIAL (design layer, runtime_apply_ready=false; drop_rate HYBRID PENDING PM) |
| **anti_p2w_confirmation** | can_be_sold_for_real_money=false · can_be_sold_for_gold=false · bind-on-pickup · affects_combat=true |
| **proficiency_confirmation** | Ranger + slot=trinket → conforme (trinket cross-class, main_stat_target=AGI Ranger-oriented) |
| **risk_notes** | **MEDIUM — drop_rate HYBRID PENDING PM; auto-reactive lethal deflection richiede C2 handling per raid boss mechanic (deflection su boss potrebbe essere no-op design)** |

---

## Sezione 2 — 4 Progressive Discovery · Reserved Table

Ogni progressive placeholder è **NOT in registry finché PM non finalizza** (Q3=A verbatim). Status uniforme: `registry_reserved / PENDING PM / not_runtime_apply_ready`.

| slot_id | class_reserved | lore_reserved | item_id_placeholder | status |
|:--:|:--:|---|---|---|
| **P1** | Mage | Memoria (proposta PM, non finale) | `mage-t5-legendary-progressive-slot-01-pending` | registry_reserved / PENDING PM / not_runtime_apply_ready |
| **P2** | Priest | Luna Morta (proposta PM, non finale) | `priest-t5-legendary-progressive-slot-02-pending` | registry_reserved / PENDING PM / not_runtime_apply_ready |
| **P3** | Rogue | Ciclo delle anime (proposta PM, non finale) | `rogue-t5-legendary-progressive-slot-03-pending` | registry_reserved / PENDING PM / not_runtime_apply_ready |
| **P4** | Ranger | Greatwood/Elfwood (proposta PM, non finale) | `ranger-t5-legendary-progressive-slot-04-pending` | registry_reserved / PENDING PM / not_runtime_apply_ready |


---

## Sezione 3 — Regole Strict Verified

| Regola | Esito |
|---|:--:|
| **No Legendary generico solo stat** — utility unica + trigger/cooldown descritti | ✅ **PASSED 11/11** |
| **No Legendary premium shop** — `can_be_sold_for_real_money=false` + `can_be_sold_for_gold=false` + bind-on-pickup | ✅ **PASSED 11/11** |
| **Proficiency HARD BLOCK** — Priest no scudo/piastre/cuoio/maglia; Rogue no arco; Warrior scudo L6 conforme; Mage focus off-hand conforme; Ranger main-stat AGI conforme | ✅ **PASSED 11/11** |
| **Anti-P2W** — affects_combat=true; affects_economy=false; affects_ranking=false; can_be_sold_for_real_money=false | ✅ **PASSED 11/11** |
| **Utility unica obbligatoria** — proc/trigger/passive/cooldown esplicitamente descritti | ✅ **PASSED 11/11** |
| **Lore source forte** — capstone T5 (Draco/Vuoto/Celeste/Alberi della Vita/Ambash/Irthe/Ergolat/Halodi) | ✅ **PASSED 11/11** |

---

## Sezione 4 — Risk Summary

- **LOW risk**: 5/11
- **MEDIUM risk**: 6/11
- **HIGH risk**: 0/11 ✅ zero

**Nota**: Nessun HIGH risk. Tutti i MEDIUM (5) richiedono validazione runtime C2 (ownership cross-target, resurrect meta-progression, HYBRID drop_rate PM final, auto-reactive lethal deflection, AoE silence cap boss).

---

## Sezione 5 — HYBRID Drop Rate Pending

- **Valore proposto direzionale**: `0.5%` (documental only, PENDING PM final)
- **Rationale**: sotto il 1% dungeon 3p e sotto il 2% raid finale (approved chain STEP 8), coerente con secondary/alternate drop rarity. **Numeric final PM richiesto pre-C4 Drop Table apply**.
- **Items affected** (4 HYBRID): `priest-…-celestial-conclave-mantle-hybrid` · `rogue-…-irthe-price-shroud-hybrid` · `mage-…-ergolat-obelisk-focus-hybrid` · `ranger-…-halodi-fate-quiver-hybrid`

---

## Sezione 6 — Registry Readiness Output

- **design_ready_registry_11**: 11 (7 approved + 4 hybrid)
- **runtime_apply_ready**: **0** (dry-run design layer)
- **Notes**: `registry_apply_ready=false` per tutti 11. Numeric finals utility/cooldown proposti; PM può accettare in C1 review o affinare in C2 runtime prep.

---

## Sezione 7 — PM Open Questions post-C0.L.1

| ID | Topic |
|:--:|---|
| **Q1** | Approvare C0.L.1 numeric finals per 11 Legendary (7 approved + 4 hybrid) come baseline design layer? |
| **Q2** | HYBRID drop_rate direzionale 0.5% (H1-H4) accettato o preferisci differenziare (es. 1% per H1 raid + 0.5% per H2-H4)? |
| **Q3** | Void-Pierce passive proc 15% chance: cap in C2 runtime a max 1 proc/round o lasciare stateless? |
| **Q4** | Divine Resurrect (L3): consenti in encounter attivi o solo post-wipe recovery (raid meta impact)? |
| **Q5** | Reforge weapon slot (L5) cross-target: richiede consent runtime target ally o auto-applica in party? |
| **Q6** | Absence Distortion (H3) AoE silence 8m: applicare cap silence-resistance su boss/elite in C2? |
| **Q7** | Fate Deflection (H4) su boss raid: no-op (deflection annullata) o valida (deflect su random adds)? |
| **Q8** | Autorizzare STEP 31 Phase C1 Item Registry Dry-Run immediato con C0.L.1 come design layer input? |


---

## Governance Check STEP 30

| Voce | Stato |
|---|:--:|
| **36 sigilli byte-identical** | ✅ VERIFIED pytest 6/6 |
| **DB writes** | ZERO |
| **Code changes** | ZERO |
| **Migrations** | ZERO |
| **Item table modification** | ZERO (read-only analysis su D5.json) |
| **Legendary stat semantic changes** | ZERO (numeric finals coerenti con `stat_principali` già in D5.json) |
| **Legendary lore changes** | ZERO |
| **Progressive finalization autonomous** | ZERO (Q3=A verbatim: 4 progressive = registry_reserved) |
| **HYBRID drop rate apply** | ZERO (0.5% proposta documentale, PENDING PM final) |
| **runtime_apply_ready** | ZERO (design layer only) |
| **class_slug auto-derivation** | ZERO (Q8=A deferral C5) |
| **C1 auto-start after C0.L.1** | 🟢 AUTHORIZED (chain immediata Q8 approved) |
| **C2 auto-start after C1** | 🔒 BLOCKED (STOP after C1, PM review required) |
| **Classi canoniche** | Warrior/Rogue/Mage/Priest/Ranger — NO drift |
| **Files deliverable** | ✅ 2 (`.md` + `.json`) |

---

## Direction

- **`auto_transition_c1`**: `true` (chain immediata Q5+Q8 approved)
- **Nota**: STEP 31 Phase C1 Item Registry Dry-Run parte immediatamente. **STOP obbligatorio dopo C1**.
