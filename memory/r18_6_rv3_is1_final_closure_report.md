# R18.6.RV3-IS1 · Item Specification & Roster Contract · Final Closure Report

**Gate**: `R18.6.RV3-IS1 · Item Specification & Roster Contract`
**Fase governance**: `R18.6 Pilot ACTIVE-DESIGN-READY` · `Cacciatore del Vuoto`
**Regime**: `DOCUMENTAL ONLY / READ-ONLY per il codice · PM-LOCKED per la governance`
**Data closure**: `2026-07-12` (UTC)
**Verdetto PM**: `R18.6.RV3-IS1 · PM APPROVED · GO FORMAL CLOSURE`

---

## §1 · PM final verdict

Verbatim: **"R18.6.RV3-IS1 · PM APPROVED · GO FORMAL CLOSURE"**.

Il Project Manager ha ratificato integralmente la patch sincronizzata MD+JSON (turno precedente) che ha:
- ripristinato il source-slot di `warlock_patron_seal` via swap 1:1 con NEW_FUTURE (micro-fix ratificato);
- adjudicato i 12 record REUSE_VALID con vocabolario strict (3 EXACT_MATCH · 6 COARSE_SOURCE_ONLY · 3 MISMATCH);
- applicato MIT-D SOURCE-BINDING FALLBACK ai 6 record armor;
- eseguito 3 accessory swap 1:1 per i record MISMATCH (`black_ring`, `cursed_pendant`, `fetish_charm`);
- preservato tutti i lock aggregati IC1 senza riaprire il gate IC1.

## §2 · IS1 CLOSED

- `gate_status` = `CLOSED / PM-LOCKED`
- `pm_locked` = `True`
- `closure_type` = `governance_semantic_lock` (non sealed technical lock)
- `closure_authority` = `PM_VERDICT_R18_6_RV3_IS1_APPROVED_GO_FORMAL_CLOSURE`

## §3 · Roster 120/120

- `roster_total_units` = `120`
- Verifica algoritmica su `roster_120_units` array del JSON IS1 source.

## §4 · 122-section final source

- IS1 source MD: `memory/r18_6_rv3_is1_item_specification_roster_contract.md`
- Line count: `1111` righe
- Sections: `122` (`§1..§122`)
- SHA256: `cdfc2303c74a0fc94a03861b5ae377f7e1da65800c974fde887ff962ed97c485` · **INVARIATO in questo turno**

## §5 · MD/JSON semantic parity

- IS1 source MD e IS1 source JSON contengono la **stessa baseline semantica** post-patch sincronizzata.
- Verdict: **PASS**.
- 9 sezioni PM richieste presenti in entrambi i file con naming allineato (`source_slot_authority_policy`, `reuse_valid_strict_audit`, `six_coarse_armor_binding_fallbacks`, `three_accessory_slot_reallocations`, `reuse_valid_unbound_standby_ledger`, `patron_seal_swap_ledger`, `source_realization_accounting`, `ic1_accounting_reconciliation`, `blueprint_code_semantic_audit`).

## §6 · Blueprint-code contract

- `unique_blueprint_codes` = `120/120`
- `tier_token_match` = `120/120`
- `slot_token_match` = `120/120`
- `family_token_match` = `120/120`
- `outliers` = `0`
- `collisions` = `0`
- `stale_semantic_codes` = `0`
- `audit_result` = `120/120 CLEAN`

## §7 · Source-slot authority policy

- `slot_type` = **AUTHORITATIVE GRANULAR** quando ∈ 14 canonici: `{head, neck, shoulders, chest, back, hands, wrist, waist, legs, feet, main_hand, off_hand, ring, accessory}`.
- **9 alias PM approvati** (unici validi):
  - `amulet → neck`, `belt → waist`, `cloak → back`, `cape → back`, `trinket → accessory`
  - `weapon_main → main_hand`, `weapon_off → off_hand`, `main-hand → main_hand`, `off-hand → off_hand`

## §8 · `armor_tags` authority boundary

- **AUTHORITATIVE FOR ARMOR FAMILY**: `stoffa`, `cuoio`.
- **NOT AUTHORITATIVE FOR SLOT**: `armor_tags` **non** determina lo slot canonico.

## §9 · `weapon_tags` authority boundary

- **AUTHORITATIVE FOR WEAPON FAMILY**: `focus`, `balestra`, `pugnale`.
- **NOT SLOT SUBSTITUTE**: `weapon_tags` non sostituisce il contratto di equipaggiamento per la determinazione dello slot.

## §10 · Alias policy preserved

- Alias autorizzati: 9 (elencati in §7).
- **Vietati** e **rifiutati** definitivamente in IS1:
  - `armor → chest / legs / hands / feet / shoulders / wrist / waist`  (categoria macro · non alias)
  - `accessory → ring / neck / back`  (categoria macro · non alias)
  - `focus → pugnale`  (weapon_tag non è slot substitute)

## §11 · EV-F2 REUSE_VALID universe = 12 (IMMUTABLE)

- `ev_f2_reuse_valid_universe_size` = `12`
- `mutation_permitted` = `False`
- Il verdetto EV-F2 primary è **immutabile**. La declassation IS1 opera esclusivamente sul binding source-slot ai fini dell'active roster.

## §12 · IS1 active REUSE_VALID = 6 (exact-bound)

Slugs attivi con `binding_status = ACTIVE_REUSE_VALID_EXACT_BOUND`:
1. `warlock_patron_seal` — T2 accessory Epic class_specific
2. `warlock_imp_collar` — T1 accessory Rare universal_neutral
3. `warlock_hex_sigil` — T1 accessory Epic universal_neutral
4. `warlock_black_ring` — T2 accessory Rare universal_neutral  (via swap)
5. `warlock_cursed_pendant` — T2 accessory Rare class_specific  (via swap)
6. `warlock_fetish_charm` — T3 accessory Epic class_specific  (via swap)

## §13 · Unbound REUSE_VALID standby = 6

Slugs in `reuse_valid_unbound_standby_ledger`:
1. `warlock_covenant_robe`
2. `warlock_coven_mantle`
3. `warlock_novice_robe`
4. `warlock_hex_focus_robe`
5. `warlock_shadow_mail`
6. `warlock_shadowweave_robe`

Motivo standby: `no_authoritative_granular_slot`.

## §14 · Active REUSE_CONDITIONAL = 3

Slugs attivi con `source_type = REUSE_CONDITIONAL` (PM_RATIFIED IS1-A):
1. `apprentice-robe` — T1 chest stoffa Common shared_family
2. `initiate_robe` — T1 legs stoffa Common shared_family
3. `apprentice-handbook` — T1 accessory universal_position Epic class_specific

## §15 · Conditional standby = 29

Ledger IS1-A `conditional_standby_pool = 29` · invariato · PM_LOCKED.

## §16 · NEW_FUTURE = 111

- `new_future_baseline_original` = 105
- `new_future_armor_fallback_absorbed` = 6 (via MIT-D)
- `new_future_total` = 111

## §17 · Worst-case NEW_FUTURE = 114 (documentato)

Se falliscono tutti i 3 REUSE_CONDITIONAL: `active_exact_reuse=6 · NEW_FUTURE=114 · total=120`. Scenario documentato ma **NON applicato**.

## §18 · Six coarse armor fallback decisions

**Policy applicata**: `MIT-D SOURCE-BINDING FALLBACK` (`MIT-A / MIT-B / MIT-C = REJECTED`).

| slug declassed | source_item_id | blueprint_code_absorbed | tier | slot | armor_type | rarity | identity |
|---|---|---|---|---|---|---|---|
| `warlock_covenant_robe` | `2618698e-9f73-40a0-8286-085c922b3179` | `cdv_t1_head_stoffa_001` | T1 | head | stoffa | Common | shared_family |
| `warlock_coven_mantle` | `dca4edbd-616d-4ce3-9c2a-29c7b78784ac` | `cdv_t1_shoulders_stoffa_001` | T1 | shoulders | stoffa | Common | shared_family |
| `warlock_novice_robe` | `3a6cc600-8316-46f1-8431-fd4281840623` | `cdv_t1_chest_stoffa_001` | T1 | chest | stoffa | Common | shared_family |
| `warlock_hex_focus_robe` | `5417640b-3030-4be1-a68d-e3cf87e0444c` | `cdv_t1_chest_stoffa_002` | T1 | chest | stoffa | Common | shared_family |
| `warlock_shadow_mail` | `3ac9f59f-430e-4638-bee5-62ca225648ec` | `cdv_t1_legs_stoffa_001` | T1 | legs | stoffa | Uncommon | class_specific |
| `warlock_shadowweave_robe` | `c8d5f2e3-b4ca-4b2a-a90e-2cb69a81c3c9` | `cdv_t1_legs_stoffa_002` | T1 | legs | stoffa | Uncommon | class_specific |

Lineage impostato: `replaces_unbound_reuse_valid_source_item_id`, `replaces_unbound_reuse_valid_slug`, `source_binding_fallback=true`, `source_binding_fallback_reason=coarse_armor_slot_without_granular_authority`, `source_binding_fallback_gate=IS1`. Zero item creati.

## §19 · Three accessory swaps

| slug | previous_blueprint_code | new_blueprint_code | swap_partner_previous_bp | swap_reason |
|---|---|---|---|---|
| `warlock_black_ring` | `cdv_t1_ring_universal_position_001` | `cdv_t2_accessory_universal_position_001` | `cdv_t2_accessory_universal_position_001` (NEW_FUTURE) | `accessory_source_slot_realignment_IS1` |
| `warlock_cursed_pendant` | `cdv_t1_neck_universal_position_001` | `cdv_t2_accessory_universal_position_002` | `cdv_t2_accessory_universal_position_002` (NEW_FUTURE) | `accessory_source_slot_realignment_IS1` |
| `warlock_fetish_charm` | `cdv_t1_back_universal_position_001` | `cdv_t3_accessory_universal_position_001` | `cdv_t3_accessory_universal_position_001` (NEW_FUTURE) | `accessory_source_slot_realignment_IS1` |

- `cascading_used` = `False`
- `new_alias_policy_invented` = `False`
- `charm_to_back_rule_introduced` = `False`
- `impossible_swaps` = `0`
- `swaps_executed` = `3/3`

## §20 · `warlock_patron_seal` correction

Final mapping (PM RATIFIED micro-fix pregresso):
- `slot` = `accessory` ✅
- `equipment_category` = `UNIVERSAL` ✅
- `armor_type` = `null` ✅
- `weapon_family` = `null` ✅
- `blueprint_code` = `cdv_t2_accessory_universal_position_003`
- `strict_verdict` = `EXACT_MATCH`
- `source_item_id` = `4b728fcb-129a-44b5-b446-5c3647a214f6`

**Stale mapping attivi `patron_seal → hands_stoffa`**: `0` ✅ (le occorrenze residue di `hands_stoffa` nel documento sono legittime · riferite al partner NEW_FUTURE che ha ereditato quel blueprint_code, mai a `patron_seal`).

## §21 · Zero active source-slot mismatch

- `ACTIVE_MISMATCH` = `0`
- `CONFLICTING_SOURCE_METADATA` = `0`
- `ACTIVE_EXACT_MATCH` = `6`
- `ACTIVE_CANONICAL_ALIAS_MATCH` = `0`
- `UNBOUND_COARSE_SOURCE` = `6`

Formulazione finale: **"12/12 adjudicated · 6 exact-bound active · 6 eligibility-valid but granular-slot unbound"**.

## §22 · 120/120 blueprint-code semantic audit

- `verdict` = `120/120 CLEAN`
- Zero outliers, zero collisioni, zero stale semantic codes.
- Parser di validazione: family come suffisso, slot come token/i prima della family (multi-word aware `main_hand`/`off_hand`), tier prefisso.
- Swap lineage tracciato per micro-fix `patron_seal` e per i 3 accessory realignment.

## §23 · IC1 aggregate locks preserved

**Delta IC1 per ogni dimensione = 0** (dimostrazione post-patch):

| dimensione | delta |
|---|---|
| blueprint_total | 0 |
| tier (T1..T5) | 0/0/0/0/0 |
| slot (14 canonical) | 0 su tutti |
| rarity (Common..Legendary) | 0/0/0/0/0 |
| identity | 0/0/0 |
| armor_family | 0/0 |
| weapon_family | 0/0/0 |
| affix_overlay | 0 |
| Legendary allocation | 0 |

**IC1 status**: `CLOSED_LOCKED · NO REOPEN`. La modifica è **IS1 SOURCE-BINDING REALIZATION**, non blueprint coverage change.

## §24 · Legendary 3 T5-only

- `legendary_total` = `3`
- Distribuzione: tutti in T5 (`Counter({'T5': 3})`)
- Zero Legendary in T1-T4.

## §25 · Affix overlay 140

- `sum(len(eligible_affix_families))` = `140`
- Invariato · lock IC1 preservato.

## §26 · Anti-P2W intent

- **Nessun runtime item creato** in questa fase.
- **Nessuna alterazione** dell'economia, dei drop rate, dell'RNG, dei prezzi shop, dei parametri competitivi.
- La governance IS1 opera esclusivamente sul **contratto documentale** delle unità blueprint. Nessun impatto in-game.

## §27 · Item naming deferred

- Naming/rinominazione item = **DEFERRED to IS2-A** (Identity/Naming/Lore gate).
- IS2-A stato: `HOLD` (non autorizzato in questa chiusura).

## §28 · Final lore deferred

- Finalizzazione lore, descrizioni, storytelling, hooks narrativi = **DEFERRED to IS2-A / lore finalization gate**.

## §29 · Stat numbers deferred

- Definizione numerica finale statistiche, effetti meccanici, budget aritmetici = **DEFERRED to IS2-B** (Stat Budget & Mechanical Effect gate).
- IS2-B stato: `PLANNED / HOLD`.

## §30 · Registry generation deferred

- `Registry v3 generation` = **NOT AUTHORIZED**.
- Nessun runtime item ID è stato generato. Nessuna entry Registry v3 esiste.

## §31 · Implementation/apply disabled

- `runtime_item_creation` = `0`
- `runtime_item_id` = `null` per tutte le 120 unità del roster IS1
- `Registry apply` = `False` per tutte le unità
- `apply_authorized` = `False` sui 6 armor MIT-D fallback

## §32 · Governance evidence

- **`pytest backend/tests/backend_r18_4_sealed_integrity_test.py`** → `6 passed · 36/36 byte-identical`
- **`lore_meta.py` hash osservato** = `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` = atteso PM → **INVARIATO**
- **Backend applicativo**: 0 modifiche
- **Frontend**: 0 modifiche
- **OpenAPI**: 0 modifiche
- **DB writes** = 0
- **Migration** = 0
- **Item generation** = 0
- **Registry module** = 0
- **Registry apply** = 0
- **Sealed set 36 artifacts**: byte-identical · nessun nuovo sigillo aggiunto
- **File modificati/creati in questo turno di closure**: `M memory/PRD.md`, `?? memory/r18_6_rv3_is1_final_closure_report.md`, `?? memory/r18_6_rv3_is1_final_closure_report.json`, `?? memory/r18_6_rv3_is1_closure_manifest.json` (più untracked pre-esistenti invariati)

## §33 · Final STOP

```
IS1               = CLOSED / PM-LOCKED
IS1 patch         = FROZEN
IS1 closure       = APPROVED · ARTIFACT WRITTEN
PRD append        = APPLIED
IS2-A             = HOLD
IS2-B             = PLANNED / HOLD
AFX2              = RESERVED FUTURE
NC1               = HOLD
Registry v3 gen   = NOT AUTHORIZED
Registry v3 app   = NOT AUTHORIZED
Gate 11           = HOLD
Monaco            = HOLD
Wave 1            = HOLD
ATTENDO VERDICT PM.
```
