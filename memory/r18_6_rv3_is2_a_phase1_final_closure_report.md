# R18.6.RV3-IS2-A Phase 1 · Item Identity, Naming & Lore Contract · Final Closure Report

**Gate**: `R18.6.RV3-IS2-A · Item Identity, Naming & Lore Contract · Phase 1`
**PM final verdict**: `R18.6.RV3-IS2-A Phase 1 · APPROVED WITH PATCH + FORMAL CLOSURE`
**Status**: `CLOSED / PM-LOCKED`
**Regime**: `DOCUMENTAL_ONLY` · zero code · zero DB · zero nuovi sigilli
**Class slug**: `cacciatore_del_vuoto`

---

## §1 · PM verdict verbatim

`R18.6.RV3-IS2-A Phase 1 · APPROVED WITH PATCH + FORMAL CLOSURE`

Il PM ha ratificato Phase 1 e adjudicato tutte le 10 open questions (5 blocking risolte). `blocking_pm_questions = 0`. Phase 2 rimane `HOLD · NOT_AUTHORIZED`.

## §2 · Phase 1 CLOSED

- `gate_status` = `CLOSED / PM-LOCKED`
- `pm_locked` = `True`
- `closure_type` = `governance_semantic_lock`
- `patch_verdicts_integrated` = Q1..Q10 (10/10 ratified · 0 blocking)

## §3 · 80/80 sections

Struttura §1..§80 preservata post-patch. Semantic parity MD↔JSON confermata.

## §4 · Identity matrix 120/120

- `identity_matrix_rows` = `120`
- `unique_blueprint_codes` = `120`
- Tutti `name_candidate` = `null` · `lore_text` = `null` · `display_name_*` = `null` · `description_*` = `null` · `localization_key` = `null`

## §5 · 9 preserved source identities

- 6 REUSE_VALID (Q4): `warlock_patron_seal`, `warlock_imp_collar`, `warlock_hex_sigil`, `warlock_black_ring`, `warlock_cursed_pendant`, `warlock_fetish_charm`
- 3 REUSE_CONDITIONAL (pending validation): `apprentice-robe`, `initiate_robe`, `apprentice-handbook`

## §6 · 111 active new identities required

`NEW_CANONICAL_IDENTITY_REQUIRED · PLAYER_NAME_REQUIRED · LORE_DIRECTION_REQUIRED` · Phase 2 draft generation.

## §7 · 3 dormant contingency identities

`DECLARED · DORMANT · OUTSIDE_ACTIVE_ROSTER` · trigger = `worst_case_all_3_reuse_conditional_fail`.

## §8 · Capacity 114

Maximum possible new identities = 111 active + 3 contingency = **114**.

## §9 · No final names generated

Phase 1 constraint: `zero name_candidate concrete values` · tutte null.

## §10 · No final lore generated

Phase 1 constraint: `lore_status ∈ {PRESERVE_EXISTING, DIRECTION_ONLY}` · nessun lore_text finale.

## §11 · Italian primary language

Player-facing language: **italiano** · leggibile · pronunciabile · coerente Orbus fantasy · distinguibile in inventario.

## §12 · Localization schema

Schema-only in Phase 1 · valori null: `display_name_it`, `display_name_en_future`, `description_it`, `description_en_future`, `localization_key`.

## §13 · Tier tone contract (T1-T5 sintesi)

- T1: chiaro · funzionale · leggibile · bassa densità lore
- T2: tecnica · rito iniziale · Marchio · primi Frammenti
- T3: identità di classe piena · Onirade · dissipazione · anti-incorporeo
- T4: ritualità avanzata · riflesso · canalizzazione · assenza · Faro Rovesciato
- T5: endgame · firma della classe · vocabolario canonico forte

## §14 · Rarity tone contract (Common-Legendary sintesi)

- Common: semplice · funzionale · nessun nome proprio
- Uncommon: tecnica riconoscibile · prima caratterizzazione
- Rare: identità evocativa · funzione meccanica percepibile
- Epic: nome memorabile · forte identità Vuoto
- Legendary: nome univoco · firma narrativa · 3 T5-only · NO NAMES generated Phase 1

## §15 · Slot semantics (14 canonical)

`head · neck · shoulders · chest · back · hands · wrist · waist · legs · feet · main_hand · off_hand · ring · accessory`

**Authority hierarchy** (Q10): IS1 blueprint slot > armor_tags/weapon_tags (hint only). Conflict: IS1 wins.

## §16 · Class identity pillars

**Cacciatore del Vuoto**: `Vuoto · Onirade · Marchio · Frammenti · Drenaggio · Dissipazione · Riflesso · Assenza · Rituale · Canalizzazione · Faro Rovesciato`

**Anti-overlap**: Mago · Paladino · Cacciatore di Mostri · Negromante · Alchimista · Ladro/Assassino.

## §17 · Vocabulary taxonomy (6-status Q7 · PM RATIFIED)

- `CANONICAL_UNRESTRICTED`: Vuoto · Marchio · Frammento · Drenaggio · Dissipazione · Riflesso · Assenza · Rituale · Canalizzazione
- `CANONICAL_RESTRICTED`: Onirade · Faro Rovesciato
- `CHARACTER_NAME_RESTRICTED`: Nael
- `INTERNAL_ONLY`: Payoff
- `LEGACY_PRESERVED_ONLY`: Warlock · Patrono · Patto · Coven · Hex
- `NEW_ITEM_FORBIDDEN`: Sacro · Luce · Ossa · Bestia · Alchimia · Bacchetta · Tomo · Grimorio · Ladro · Assassino

## §18 · Repetition thresholds (Q1 hard caps ratificati)

Scope: 111 active NEW_FUTURE. Caps (Phase 2 draft):
`Vuoto ≤ 10 · Onirade ≤ 4 · Marchio ≤ 8 · Frammento_family ≤ 8 · Faro Rovesciato ≤ 2 · Drenaggio ≤ 6 · Dissipazione ≤ 6 · Riflesso ≤ 8 · Assenza ≤ 8 · Rituale_family ≤ 10 · Canalizzazione ≤ 6`

## §19 · Nael policy

`display_name_status = FORBIDDEN` (tutte le rarità/slot) · `lore_status = RESTRICTED_PM_REVIEW`

## §20 · Onirade policy

Display: `CLASS_SPECIFIC · Epic/Legendary · PM_REVIEW · cap ≤4`. Forbidden in SHARED_FAMILY, UNIVERSAL_NEUTRAL.

## §21 · Faro Rovesciato policy

Display: `CLASS_SPECIFIC · Epic/Legendary · PM_REVIEW · cap ≤2`. Forbidden in Common, Uncommon, SHARED_FAMILY, UNIVERSAL_NEUTRAL.

## §22 · Payoff internal-only policy

`INTERNAL_ONLY_PLAYER_FACING_FORBIDDEN` · reserved AFX1/IS2-B technical language · italian alternative TBD Phase 2.

## §23 · Legacy Warlock preservation

6 REUSE_VALID (Warlock legacy) preserved · **NO rename · NO translation · NO retro-branding · NO new display_name_it** · localizzazione futura = gate separato.

## §24 · Existing-item no-rename policy

`localization_action = DEFERRED_TO_SEPARATE_LEGACY_LOCALIZATION_GATE` per tutti REUSE_VALID + REUSE_CONDITIONAL.

## §25 · Cohesive-family policy (Q5)

Cohesive naming families ammesse · **2-4 items per family** · zero set mechanics · zero set bonus · zero 2-4-6 piece bonus.

## §26 · Legendary candidate structure (Q6)

Strutture ammesse: `PROPER_NOUN`, `RITUAL_TITLE`, `HYBRID_FORM`. Phase 2 può proporre 1 candidato per struttura per ciascuna delle 3 Legendary T5. `LORE_PROPOSAL_PENDING_PM` obbligatorio · auto-canonical NOT authorized.

## §27 · arcane_adept_orb final treatment (Q9)

`NOT_COMPATIBLE · FINAL` · existing mutation NO · class_tags mutation NO · rename NO · retro-branding NO · void-native successor `REQUIRED_FUTURE_COVERAGE` · Phase 1 name NOT generated · identity NOT canonized · item row NOT created · EV-F2 unaffected.

## §28 · voidpiercer-bow final treatment

`NOT_COMPATIBLE · FINAL · no successor requirement · name NOT reusable for new void items`.

## §29 · Tag hint-only policy (Q10)

`armor_tags = semantic_family_hint` · `weapon_tags = weapon_identity_hint`. Non authoritative per: slot · tier · rarity · identity class · source verdict. **Conflict resolution: IS1 canonical specification WINS · log conflict · no silent reinterpretation.**

## §30 · Collision taxonomy

6 categories: `EXACT_DUPLICATE · NORMALIZED_DUPLICATE · NEAR_DUPLICATE · LORE_COLLISION · CLASS_IDENTITY_COLLISION · SAFE`.

## §31 · Phase 2 remains HOLD

Phase 2 authorization required · PM explicit verdict pending · prerequisites all met (blocking=0).

## §32 · Governance evidence

- `pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → `6 passed · 36/36 byte-identical`
- `lore_meta.py` hash = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` · INVARIATO
- Backend / Frontend / OpenAPI: 0 modifiche
- DB writes = 0 · Item generation = 0 · Name generation = 0 · Final lore generation = 0 · Registry generation = 0 · Registry apply = 0
- IS1 source MD/JSON/closure/manifest: INVARIATI
- Sealed set 36 artifacts: byte-identical · nessun nuovo sigillo aggiunto

## §33 · Explicit STOP

```
IS2-A Phase 1        = CLOSED / PM-LOCKED
IS2-A Phase 2        = HOLD (NOT AUTHORIZED)
IS2-B                = HOLD
AFX2                 = RESERVED FUTURE
NC1                  = HOLD
Registry v3 gen/app  = NOT AUTHORIZED
Gate 11              = HOLD
Monaco               = HOLD
ATTENDO VERDICT PM.
```
