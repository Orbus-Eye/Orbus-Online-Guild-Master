# R18.6.RV3-IS2-A Phase 2 · Rev-3 · Minimal PM Content Patch

**Gate**: `R18.6.RV3-IS2-A Phase 2 · Rev-3` · **Status**: `REV3_TARGET_FINAL_DRAFT · AWAITING_PM_FINAL_CONTENT_SIGNOFF`  
**Regime**: `DOCUMENTAL_ONLY · ITALIAN_ONLY · NO_RUNTIME · NO_APPLY` · **UTC**: `2026-07-12T23:29:25.443326+00:00`  
**Supersedes**: `REV2_PM_CONTENT_PATCH` · **Rev-2 status**: `AUTOMATED_ZERO-BLOCKING_PASS · PM_CONTENT_PATCH_REQUIRED` · **Rev-1 status**: `STRUCTURAL_COMPLIANCE_PASS · CONTENT_REVIEW_SUPERSEDED` · **R0 status**: `REJECTED_FOR_COMPLIANCE · AUDIT_REFERENCE_ONLY`  
**Rev-2 MD sha256**: `4466a674471bc980527246bdb5d85c1ac6a58f39971c55de79a3ff8872122e0f` · **Rev-2 JSON sha256**: `cd0be793b79f40d7c3b52f1de34efd9a96d4039025b682715e5d650136e0ca12`  
**Rev-1 MD sha256**: `302c67d75d7979ef1247bdc8819eb92359359e10f2750c038f86bdf5c1bf6cd8` · **Rev-1 JSON sha256**: `32add8cec5f2a3155a91227d8e870c45055437375cb9d32aae483e33c90c1ce3`  
**R0 MD sha256**: `ef487f1cfffdf7b7d27d7457591047be253840548b4584cf23342d544e4a7d6d` · **R0 JSON sha256**: `4a0e04a46be1381261848bbdf7d427ec54ab482d94ed57fb4b9db3c333fd54c1`  
**Phase 2 closure**: `HOLD`

---

## §1 · Executive Summary

```json
{
  "title": "R18.6.RV3-IS2-A Phase 2 · Rev-3 · Minimal PM Content Patch",
  "gate": "R18.6.RV3-IS2-A Phase 2",
  "revision": "R3",
  "supersedes": "REV2_PM_CONTENT_PATCH",
  "rev2_status": "AUTOMATED_ZERO-BLOCKING_PASS · PM_CONTENT_PATCH_REQUIRED",
  "rev1_status": "STRUCTURAL_COMPLIANCE_PASS · CONTENT_REVIEW_SUPERSEDED",
  "r0_status": "REJECTED_FOR_COMPLIANCE · AUDIT_REFERENCE_ONLY",
  "rev2_md_sha256": "4466a674471bc980527246bdb5d85c1ac6a58f39971c55de79a3ff8872122e0f",
  "rev2_json_sha256": "cd0be793b79f40d7c3b52f1de34efd9a96d4039025b682715e5d650136e0ca12",
  "rev1_md_sha256": "302c67d75d7979ef1247bdc8819eb92359359e10f2750c038f86bdf5c1bf6cd8",
  "rev1_json_sha256": "32add8cec5f2a3155a91227d8e870c45055437375cb9d32aae483e33c90c1ce3",
  "r0_md_sha256": "ef487f1cfffdf7b7d27d7457591047be253840548b4584cf23342d544e4a7d6d",
  "r0_json_sha256": "4a0e04a46be1381261848bbdf7d427ec54ab482d94ed57fb4b9db3c333fd54c1",
  "content": "Rev-3 minimal PM content patch · 4 candidati modificati (2 PM-directed + 2 third_changes deterministici documentati) · 113 preservati bit-identical da Rev-2 · zero blocking language errors · nuovo validator §E prior_pm_semantic_blacklist attivo."
}
```

## §2 · Scope

```json
{
  "in_scope": [
    "PM-directed replacements §C.1 (Scatto dei Frammenti) + §C.2 (Sigillo della Soglia Vigile)",
    "Third_change §D COLLISION_PROVOKED_BY_PM_PATCH: cdv_t3_off_hand_focus_001",
    "Third_change §E BLACKLIST_VIOLATION: cdv_t1_main_hand_balestra_001",
    "New validator §E · prior_pm_semantic_blacklist_audit (117 candidati)",
    "Full re-audit legacy + 8-category blocking + 10-status taxonomy"
  ],
  "out_of_scope": [
    "global regeneration",
    "PM_APPROVED naming",
    "stat/effect",
    "Registry",
    "closure Phase 2",
    "IS2-B/NC1/Gate 11"
  ]
}
```

## §3 · Governance

```json
{
  "regime": "DOCUMENTAL_ONLY · ITALIAN_ONLY",
  "pm_verdict_ref": "R18.6.RV3-IS2-A Phase 2 Rev-3 · MINIMAL PM CONTENT PATCH GO",
  "phase_1_lock": "IMMUTABLE",
  "phase_2_closure": "HOLD",
  "rev2_preserved": true,
  "rev1_preserved": true,
  "r0_preserved": true,
  "sealed_integrity": "6 passed · 36/36 byte-identical",
  "anchor_lore_meta": "a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f"
}
```

## §4 · Source Of Truth

```json
{
  "consumed": [
    "Rev-2 (base)",
    "Rev-1 (audit reference)",
    "R0 (audit reference)",
    "IS1 source",
    "Phase 1 source"
  ],
  "live_catalog_items": 178
}
```

## §5 · Phase 1 Dependency

```json
{
  "phase_1_source_md": "a70199c4932fffff24920740e31119a31c3bdcc28cc55d7be56ffdc39f8a2bd3",
  "phase_1_source_json": "2e5f115726799d3465de6458a3a6779d6f573f00fa61c115a9ddd48666755e52",
  "status": "CLOSED_PM_LOCKED_IMMUTABLE"
}
```

## §6 · Phase 1 Contract Locks

```json
{
  "vocabulary_taxonomy": "LOCKED",
  "repetition_caps": "LOCKED",
  "restricted_policies": "LOCKED",
  "legacy_preservation": "LOCKED",
  "p2q_adjudication_r1": "P2Q1..P2Q5 all PM_ADJUDICATED"
}
```

## §7 · Active Roster Accounting

```json
{
  "roster_total": 120,
  "preserved_existing": 9,
  "new_future": 111,
  "non_legendary": 108,
  "legendary": 3,
  "contingency_dormant": 3
}
```

## §8 · Preserved Identity Accounting

```json
{
  "reuse_valid": 6,
  "reuse_conditional": 3,
  "reuse_valid_slugs": [
    "warlock_patron_seal",
    "warlock_imp_collar",
    "warlock_hex_sigil",
    "warlock_black_ring",
    "warlock_cursed_pendant",
    "warlock_fetish_charm"
  ],
  "reuse_conditional_slugs": [
    "apprentice-robe",
    "initiate_robe",
    "apprentice-handbook"
  ],
  "draft_generated": 0
}
```

## §9 · New Future Accounting

```json
{
  "count": 111,
  "non_legendary_primary_drafts": 108,
  "legendary_units": 3,
  "legendary_candidates_total": 9,
  "total_candidate_name_strings": 117,
  "identity_packages": 111
}
```

## §10 · Contingency Exclusion

```json
{
  "count": 3,
  "draft_generated": 0,
  "content_status": "DORMANT_NOT_GENERATED"
}
```

## §11 · Naming Methodology

```json
{
  "revision": "R3",
  "policy": "MINIMAL PATCH · targeted PM-directed + deterministic third_changes only",
  "total_changes": 5,
  "pm_directed": 2,
  "third_changes": 3
}
```

## §12 · Lore Methodology

```json
{
  "format": "1-2 frasi <=45 parole",
  "lore_preserved_count": 117,
  "lore_changed_due_to_Rev3_count": 0,
  "rationale": "Lore Rev-2 template-based per identity_class×family×tier · non cita nomi specifici · nessun cambio nome Rev-3 invalida lore correlato"
}
```

## §13 · Vocabulary Compliance

```json
{
  "canonical_usage": {
    "Canalizzazione": 5,
    "Riflesso": 4,
    "Rituale": 6,
    "Vuoto": 5,
    "Frammento": 4,
    "Marchio": 7,
    "Assenza": 5,
    "Dissipazione": 4,
    "Drenaggio": 2,
    "Faro Rovesciato": 2,
    "Onirade": 2
  },
  "caps": {
    "Vuoto": 10,
    "Onirade": 4,
    "Marchio": 8,
    "Frammento": 8,
    "Faro Rovesciato": 2,
    "Drenaggio": 6,
    "Dissipazione": 6,
    "Riflesso": 8,
    "Assenza": 8,
    "Rituale": 10,
    "Canalizzazione": 6
  },
  "all_within_caps": true
}
```

## §14 · Repetition Cap Compliance

```json
{
  "caps": {
    "Vuoto": 10,
    "Onirade": 4,
    "Marchio": 8,
    "Frammento": 8,
    "Faro Rovesciato": 2,
    "Drenaggio": 6,
    "Dissipazione": 6,
    "Riflesso": 8,
    "Assenza": 8,
    "Rituale": 10,
    "Canalizzazione": 6
  },
  "observed": {
    "Canalizzazione": 5,
    "Riflesso": 4,
    "Rituale": 6,
    "Vuoto": 5,
    "Frammento": 4,
    "Marchio": 7,
    "Assenza": 5,
    "Dissipazione": 4,
    "Drenaggio": 2,
    "Faro Rovesciato": 2,
    "Onirade": 2
  },
  "phrase_over_limit": 0,
  "bigram_over_limit_count": 0,
  "trigram_over_limit_count": 0,
  "bigram_max": 2,
  "trigram_max": 2,
  "pattern_max": 4,
  "pattern_usage_all_within_12": true
}
```

## §15 · Tier Tone Compliance

```json
{
  "tier_distribution": {
    "T3": 25,
    "T4": 26,
    "T5": 28,
    "T1": 13,
    "T2": 19
  }
}
```

## §16 · Rarity Tone Compliance

```json
{
  "rarity_distribution": {
    "Epic": 11,
    "Rare": 24,
    "Uncommon": 32,
    "Common": 41,
    "Legendary": 3
  }
}
```

## §17 · Slot Semantic Compliance

```json
{
  "slot_distribution": {
    "accessory": 8,
    "ring": 12,
    "main_hand": 15,
    "off_hand": 6,
    "feet": 7,
    "legs": 9,
    "waist": 6,
    "wrist": 5,
    "hands": 7,
    "back": 6,
    "chest": 9,
    "head": 8,
    "neck": 6,
    "shoulders": 7
  },
  "slot_semantic_violation": 0,
  "validation_status": "CLEAN_ALL"
}
```

## §18 · Identity Class Compliance

```json
{
  "identity_distribution": {
    "class_specific": 63,
    "universal_neutral": 19,
    "shared_family": 29
  }
}
```

## §19 · Cohesive Family Usage

```json
{
  "families_used": 0,
  "policy": "optional · P2Q2 adjudicated"
}
```

## §20 · Collision Methodology

```json
{
  "sources": [
    "live 178",
    "117 Rev-3 candidates",
    "Rev-2 candidate universe",
    "Rev-1 candidate universe",
    "R0 candidate universe",
    "Class Hall canonical"
  ],
  "categories": [
    "EXACT",
    "NORMALIZED",
    "NEAR",
    "LIVE_COLLISION",
    "LORE_COLLISION",
    "CLASS_IDENTITY",
    "SAFE"
  ]
}
```

## §21 · Roster 111 Units

```json
{
  "records_count": 111,
  "non_legendary_count": 108,
  "legendary_count": 3
}
```

## §22 · T1 Names

```json
{
  "count": 13,
  "names": [
    "Draco del Marchio",
    "Cerchietto della via",
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Torcia nel Marchio",
    "Sigillo di Fiamma calma",
    "Manto di archivio",
    "Veste di Metodo",
    "Sopravveste di Metodo",
    "Fasce in Dissipazione",
    "Cappuccio di Studio",
    "Medaglione della bottega",
    "Palandrana di Cammino"
  ]
}
```

## §23 · T2 Names

```json
{
  "count": 19,
  "names": [
    "Punteruolo di Incisione",
    "Anello del novizio semplice",
    "Ferramento di scuola dell'usanza",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Lanterna dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Fascia dell'iniziato della Dissipazione",
    "Cinghia tecnico di Sentiero",
    "Polsino di Vuoto",
    "Velo di usanza",
    "Farsetto di Percorso",
    "Livrea in Disciplina",
    "Manopole in Assenza",
    "Velo in Percorso",
    "Aureola di Insegnamento",
    "Medaglione del quotidiano",
    "Sopravveste di Apprendimento"
  ]
}
```

## §24 · T3 Names

```json
{
  "count": 25,
  "names": [
    "Feticcio del cercatore di Canalizzazione",
    "Fibula del cercatore di Riflesso",
    "Balestra della soglia della Proiezione",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo della Soglia Vigile",
    "Reliquiario del Segno",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Calzari conciati del Sentiero",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato della Marcia",
    "Cinta dell'iniziato del Rito",
    "Nastro dell'iniziato rituale",
    "Fasce da polso dell'iniziato dei Frammenti",
    "Sciarpa della cronaca",
    "Blusa di Studio",
    "Mitene della Disciplina",
    "Guanti di Cammino",
    "Berretto della Veglia",
    "Velo della Via",
    "Ciondolo semplice",
    "Rinforzo di Disciplina",
    "Bandoliera del Cammino"
  ]
}
```

## §25 · T4 Names

```json
{
  "count": 26,
  "names": [
    "Cifra dell'esperto del Rituale",
    "Emblema del custode della Canalizzazione",
    "Sigillo dell'esperto in Rituale",
    "Balestra del custode di Colpo controllato",
    "Lama del maestro incisore",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'artigiano",
    "Vera dell'adepto del Vuoto",
    "Stivali dell'esperto di Battuta",
    "Ghette dell'adepto di Drenaggio",
    "Cosciali dell'adepto del Cammino",
    "Gonna dell'esperto nel Riflesso",
    "Sigillo del veggente di Segno",
    "Fascia del veggente di Drenaggio",
    "Vinca dell'esperto in Silenzio",
    "Drappo di quotidiano",
    "Farsetto di Bilico",
    "Casacca di Disciplina",
    "Palme di Dissipazione",
    "Cuffia di Sentiero",
    "Copricapo dell'Insegnamento",
    "Girocollo dell'usanza",
    "Rinforzo di Scuola",
    "Sopravveste dell'Insegnamento"
  ]
}
```

## §26 · T5 Names

```json
{
  "count": 25,
  "names": [
    "Cifra dell'apice nel Vuoto",
    "Suggello del pinnacolo del Rituale",
    "Fibula della firma del Frammento",
    "Vera dell'apogeo nel Vuoto",
    "Anello del pinnacolo di Marchio",
    "Ferramento della firma nel Marchio",
    "Sandali dell'apice marchiato",
    "Balestra dell'apogeo della Proiezione",
    "Cifra del canone della Traiettoria",
    "Suggello dell'apogeo di Passo taciturno",
    "Amuleto del canone di Punto vicino",
    "Cerchio dell'apice di Assenza",
    "Mitene dell'apogeo della Veglia",
    "Cosciali dell'apice in Marcia",
    "Pantaloni dell'apice marchiato",
    "Cinturone dell'apogeo in Marcia",
    "Legaccio dell'apice dello Studio",
    "Drappo di mestiere",
    "Drappo in scambio",
    "Corazza di Percorso",
    "Manopole del Sentiero",
    "Diadema dello Studio",
    "Amuleto di artigiano",
    "Ciondolo dello scriba",
    "Bandoliera di Veglia"
  ]
}
```

## §27 · Common Names

```json
{
  "count": 41,
  "names": [
    "Manto di archivio",
    "Veste di Metodo",
    "Sopravveste di Metodo",
    "Fasce in Dissipazione",
    "Cappuccio di Studio",
    "Medaglione della bottega",
    "Palandrana di Cammino",
    "Velo di usanza",
    "Farsetto di Percorso",
    "Livrea in Disciplina",
    "Manopole in Assenza",
    "Velo in Percorso",
    "Aureola di Insegnamento",
    "Medaglione del quotidiano",
    "Sopravveste di Apprendimento",
    "Sciarpa della cronaca",
    "Blusa di Studio",
    "Mitene della Disciplina",
    "Guanti di Cammino",
    "Berretto della Veglia",
    "Velo della Via",
    "Ciondolo semplice",
    "Rinforzo di Disciplina",
    "Bandoliera del Cammino",
    "Drappo di quotidiano",
    "Farsetto di Bilico",
    "Casacca di Disciplina",
    "Palme di Dissipazione",
    "Cuffia di Sentiero",
    "Copricapo dell'Insegnamento",
    "Girocollo dell'usanza",
    "Rinforzo di Scuola",
    "Sopravveste dell'Insegnamento",
    "Drappo di mestiere",
    "Drappo in scambio",
    "Corazza di Percorso",
    "Manopole del Sentiero",
    "Diadema dello Studio",
    "Amuleto di artigiano",
    "Ciondolo dello scriba",
    "Bandoliera di Veglia"
  ]
}
```

## §28 · Uncommon Names

```json
{
  "count": 32,
  "names": [
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Torcia nel Marchio",
    "Sigillo di Fiamma calma",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Lanterna dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Fascia dell'iniziato della Dissipazione",
    "Cinghia tecnico di Sentiero",
    "Polsino di Vuoto",
    "Calzari conciati del Sentiero",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato della Marcia",
    "Cinta dell'iniziato del Rito",
    "Nastro dell'iniziato rituale",
    "Fasce da polso dell'iniziato dei Frammenti",
    "Stivali dell'esperto di Battuta",
    "Ghette dell'adepto di Drenaggio",
    "Cosciali dell'adepto del Cammino",
    "Gonna dell'esperto nel Riflesso",
    "Sigillo del veggente di Segno",
    "Fascia del veggente di Drenaggio",
    "Vinca dell'esperto in Silenzio",
    "Mitene dell'apogeo della Veglia",
    "Cosciali dell'apice in Marcia",
    "Pantaloni dell'apice marchiato",
    "Cinturone dell'apogeo in Marcia",
    "Legaccio dell'apice dello Studio"
  ]
}
```

## §29 · Rare Names

```json
{
  "count": 24,
  "names": [
    "Draco del Marchio",
    "Cerchietto della via",
    "Punteruolo di Incisione",
    "Anello del novizio semplice",
    "Ferramento di scuola dell'usanza",
    "Balestra della soglia della Proiezione",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo della Soglia Vigile",
    "Reliquiario del Segno",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Balestra del custode di Colpo controllato",
    "Lama del maestro incisore",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'artigiano",
    "Vera dell'adepto del Vuoto",
    "Sandali dell'apice marchiato",
    "Balestra dell'apogeo della Proiezione",
    "Cifra del canone della Traiettoria",
    "Suggello dell'apogeo di Passo taciturno",
    "Amuleto del canone di Punto vicino",
    "Cerchio dell'apice di Assenza"
  ]
}
```

## §30 · Epic Names

```json
{
  "count": 11,
  "names": [
    "Feticcio del cercatore di Canalizzazione",
    "Fibula del cercatore di Riflesso",
    "Cifra dell'esperto del Rituale",
    "Emblema del custode della Canalizzazione",
    "Sigillo dell'esperto in Rituale",
    "Cifra dell'apice nel Vuoto",
    "Suggello del pinnacolo del Rituale",
    "Fibula della firma del Frammento",
    "Vera dell'apogeo nel Vuoto",
    "Anello del pinnacolo di Marchio",
    "Ferramento della firma nel Marchio"
  ]
}
```

## §31 · Legendary Candidate Roster

```json
{
  "count": 3,
  "records": [
    {
      "blueprint_code": "cdv_t5_chest_stoffa_001",
      "tier": "T5",
      "slot": "chest",
      "family": "stoffa",
      "identity_class": "shared_family",
      "rarity_intent": "Legendary",
      "narrative_role": "apogee_of_ritual_channeling",
      "candidates": [
        {
          "structure": "proper_noun",
          "candidate_name": "Sudario del Faro Rovesciato",
          "canonical_terms": {
            "Faro Rovesciato": 1
          },
          "restricted_terms": {
            "Faro Rovesciato": 1
          },
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Manto della Grande Canalizzazione",
          "canonical_terms": {
            "Canalizzazione": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Veste di Onirade",
          "canonical_terms": {
            "Onirade": 1
          },
          "restricted_terms": {
            "Onirade": 1
          },
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Manto della Grande Canalizzazione",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_chest_stoffa",
      "lore_text_it_draft": "Draft Legendary breve: identità di firma, pending PM adjudication.",
      "PM_review_required": true
    },
    {
      "blueprint_code": "cdv_t5_main_hand_focus_001",
      "tier": "T5",
      "slot": "main_hand",
      "family": "focus",
      "identity_class": "class_specific",
      "rarity_intent": "Legendary",
      "narrative_role": "signature_weapon",
      "candidates": [
        {
          "structure": "proper_noun",
          "candidate_name": "Occhio del Faro Rovesciato",
          "canonical_terms": {
            "Faro Rovesciato": 1
          },
          "restricted_terms": {
            "Faro Rovesciato": 1
          },
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Focus dell'Assenza profonda",
          "canonical_terms": {
            "Assenza": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Voce di Onirade",
          "canonical_terms": {
            "Onirade": 1
          },
          "restricted_terms": {
            "Onirade": 1
          },
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Focus dell'Assenza profonda",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_main_hand_focus",
      "lore_text_it_draft": "Draft Legendary breve: identità di firma, pending PM adjudication.",
      "PM_review_required": true
    },
    {
      "blueprint_code": "cdv_t5_main_hand_balestra_001",
      "tier": "T5",
      "slot": "main_hand",
      "family": "balestra",
      "identity_class": "class_specific",
      "rarity_intent": "Legendary",
      "narrative_role": "ranged_ritual_signature",
      "candidates": [
        {
          "structure": "proper_noun",
          "candidate_name": "Scatto dei Frammenti",
          "canonical_terms": {
            "Frammento": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV3_PATCH",
          "prior_pm_semantic_blacklist_hit": null
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Balestra della Traiettoria certa",
          "canonical_terms": {},
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Voce dei Bersagli assenti",
          "canonical_terms": {
            "Assenza": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM",
          "linguistic_quality_status": {
            "grammar_status": "PASS",
            "agreement_status": "PASS",
            "naturalness_status": "PASS",
            "lexical_fit_status": "PASS",
            "fantasy_register_status": "PASS",
            "slot_readability_status": "PASS",
            "weapon_family_readability_status": "PASS",
            "class_identity_drift_status": "PASS",
            "prior_pm_verdict_status": "PASS",
            "prior_pm_semantic_blacklist_status": "PASS"
          },
          "revision_source": "REV2_PRESERVED"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Balestra della Traiettoria certa",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_main_hand_balestra",
      "lore_text_it_draft": "Draft Legendary breve: identità di firma, pending PM adjudication.",
      "PM_review_required": true
    }
  ],
  "preferred_candidate_policy": "AGENT_RECOMMENDATION_ONLY · PM_SELECTED = 0 · PM adjudication required"
}
```

## §32 · Focus Naming

```json
{
  "count": 9,
  "names": [
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo della Soglia Vigile",
    "Reliquiario del Segno",
    "Emblema del maestro della Risonanza",
    "Torcia nel Marchio",
    "Sigillo di Fiamma calma",
    "Lanterna dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Sigillo del veggente di Segno"
  ]
}
```

## §33 · Balestra Naming

```json
{
  "count": 6,
  "names": [
    "Draco del Marchio",
    "Balestra della soglia della Proiezione",
    "Balestra del custode di Colpo controllato",
    "Reliquiario dell'esperto di Verso arcuato",
    "Balestra dell'apogeo della Proiezione",
    "Cifra del canone della Traiettoria"
  ]
}
```

## §34 · Pugnale Naming

```json
{
  "count": 4,
  "names": [
    "Punteruolo di Incisione",
    "Lama del maestro incisore",
    "Suggello dell'apogeo di Passo taciturno",
    "Amuleto del canone di Punto vicino"
  ]
}
```

## §35 · Stoffa Naming

```json
{
  "count": 39,
  "names": [
    "Sandali dell'apice marchiato",
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Sopracalze dell'iniziato di Assenza",
    "Coscialette tecnico del Riflesso",
    "Fascia dell'iniziato della Dissipazione",
    "Polsino di Vuoto",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinta dell'iniziato del Rito",
    "Nastro dell'iniziato rituale",
    "Fasce da polso dell'iniziato dei Frammenti",
    "Ghette dell'adepto di Drenaggio",
    "Gonna dell'esperto nel Riflesso",
    "Fascia del veggente di Drenaggio",
    "Pantaloni dell'apice marchiato",
    "Legaccio dell'apice dello Studio",
    "Veste di Metodo",
    "Sopravveste di Metodo",
    "Fasce in Dissipazione",
    "Cappuccio di Studio",
    "Palandrana di Cammino",
    "Livrea in Disciplina",
    "Manopole in Assenza",
    "Velo in Percorso",
    "Aureola di Insegnamento",
    "Sopravveste di Apprendimento",
    "Blusa di Studio",
    "Guanti di Cammino",
    "Velo della Via",
    "Bandoliera del Cammino",
    "Casacca di Disciplina",
    "Palme di Dissipazione",
    "Copricapo dell'Insegnamento",
    "Sopravveste dell'Insegnamento",
    "Manopole del Sentiero",
    "Diadema dello Studio",
    "Bandoliera di Veglia"
  ]
}
```

## §36 · Cuoio Naming

```json
{
  "count": 18,
  "names": [
    "Gambali di cuoio tecnico della Marcia",
    "Cinghia tecnico di Sentiero",
    "Calzari conciati del Sentiero",
    "Cinturone dell'iniziato della Marcia",
    "Stivali dell'esperto di Battuta",
    "Cosciali dell'adepto del Cammino",
    "Vinca dell'esperto in Silenzio",
    "Mitene dell'apogeo della Veglia",
    "Cosciali dell'apice in Marcia",
    "Cinturone dell'apogeo in Marcia",
    "Farsetto di Percorso",
    "Mitene della Disciplina",
    "Berretto della Veglia",
    "Rinforzo di Disciplina",
    "Farsetto di Bilico",
    "Cuffia di Sentiero",
    "Rinforzo di Scuola",
    "Corazza di Percorso"
  ]
}
```

## §37 · Universal Naming

```json
{
  "count": 32,
  "names": [
    "Feticcio del cercatore di Canalizzazione",
    "Fibula del cercatore di Riflesso",
    "Cifra dell'esperto del Rituale",
    "Emblema del custode della Canalizzazione",
    "Sigillo dell'esperto in Rituale",
    "Cifra dell'apice nel Vuoto",
    "Suggello del pinnacolo del Rituale",
    "Fibula della firma del Frammento",
    "Vera dell'apogeo nel Vuoto",
    "Anello del pinnacolo di Marchio",
    "Ferramento della firma nel Marchio",
    "Cerchietto della via",
    "Anello del novizio semplice",
    "Ferramento di scuola dell'usanza",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'artigiano",
    "Vera dell'adepto del Vuoto",
    "Cerchio dell'apice di Assenza",
    "Manto di archivio",
    "Medaglione della bottega",
    "Velo di usanza",
    "Medaglione del quotidiano",
    "Sciarpa della cronaca",
    "Ciondolo semplice",
    "Drappo di quotidiano",
    "Girocollo dell'usanza",
    "Drappo di mestiere",
    "Drappo in scambio",
    "Amuleto di artigiano",
    "Ciondolo dello scriba"
  ]
}
```

## §38 · Class Specific Naming

```json
{
  "count": 61,
  "names": [
    "Feticcio del cercatore di Canalizzazione",
    "Fibula del cercatore di Riflesso",
    "Cifra dell'esperto del Rituale",
    "Emblema del custode della Canalizzazione",
    "Sigillo dell'esperto in Rituale",
    "Cifra dell'apice nel Vuoto",
    "Suggello del pinnacolo del Rituale",
    "Fibula della firma del Frammento",
    "Vera dell'apogeo nel Vuoto",
    "Anello del pinnacolo di Marchio",
    "Ferramento della firma nel Marchio",
    "Draco del Marchio",
    "Punteruolo di Incisione",
    "Balestra della soglia della Proiezione",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo della Soglia Vigile",
    "Reliquiario del Segno",
    "Balestra del custode di Colpo controllato",
    "Lama del maestro incisore",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Vera dell'adepto del Vuoto",
    "Sandali dell'apice marchiato",
    "Balestra dell'apogeo della Proiezione",
    "Cifra del canone della Traiettoria",
    "Suggello dell'apogeo di Passo taciturno",
    "Amuleto del canone di Punto vicino",
    "Cerchio dell'apice di Assenza",
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Torcia nel Marchio",
    "Sigillo di Fiamma calma",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Lanterna dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Fascia dell'iniziato della Dissipazione",
    "Cinghia tecnico di Sentiero",
    "Polsino di Vuoto",
    "Calzari conciati del Sentiero",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato della Marcia",
    "Cinta dell'iniziato del Rito",
    "Nastro dell'iniziato rituale",
    "Fasce da polso dell'iniziato dei Frammenti",
    "Stivali dell'esperto di Battuta",
    "Ghette dell'adepto di Drenaggio",
    "Cosciali dell'adepto del Cammino",
    "Gonna dell'esperto nel Riflesso",
    "Sigillo del veggente di Segno",
    "Fascia del veggente di Drenaggio",
    "Vinca dell'esperto in Silenzio",
    "Cosciali dell'apice in Marcia",
    "Pantaloni dell'apice marchiato",
    "Cinturone dell'apogeo in Marcia",
    "Fasce in Dissipazione",
    "Manopole in Assenza",
    "Palme di Dissipazione"
  ]
}
```

## §39 · Shared Family Naming

```json
{
  "count": 28,
  "names": [
    "Mitene dell'apogeo della Veglia",
    "Legaccio dell'apice dello Studio",
    "Veste di Metodo",
    "Sopravveste di Metodo",
    "Cappuccio di Studio",
    "Palandrana di Cammino",
    "Farsetto di Percorso",
    "Livrea in Disciplina",
    "Velo in Percorso",
    "Aureola di Insegnamento",
    "Sopravveste di Apprendimento",
    "Blusa di Studio",
    "Mitene della Disciplina",
    "Guanti di Cammino",
    "Berretto della Veglia",
    "Velo della Via",
    "Rinforzo di Disciplina",
    "Bandoliera del Cammino",
    "Farsetto di Bilico",
    "Casacca di Disciplina",
    "Cuffia di Sentiero",
    "Copricapo dell'Insegnamento",
    "Rinforzo di Scuola",
    "Sopravveste dell'Insegnamento",
    "Corazza di Percorso",
    "Manopole del Sentiero",
    "Diadema dello Studio",
    "Bandoliera di Veglia"
  ]
}
```

## §40 · Universal Neutral Naming

```json
{
  "count": 19,
  "names": [
    "Cerchietto della via",
    "Anello del novizio semplice",
    "Ferramento di scuola dell'usanza",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'artigiano",
    "Manto di archivio",
    "Medaglione della bottega",
    "Velo di usanza",
    "Medaglione del quotidiano",
    "Sciarpa della cronaca",
    "Ciondolo semplice",
    "Drappo di quotidiano",
    "Girocollo dell'usanza",
    "Drappo di mestiere",
    "Drappo in scambio",
    "Amuleto di artigiano",
    "Ciondolo dello scriba"
  ]
}
```

## §41 · Lore Draft Roster

```json
{
  "total_lore_drafts": 111,
  "format": "1-2 frasi <=45 parole",
  "status": "DRAFT_PENDING_PM",
  "lore_preserved_count": 117,
  "lore_changed_due_to_Rev3_count": 0
}
```

## §42 · Localization Key Proposals

```json
{
  "format": "item.cacciatore_del_vuoto.<blueprint_code>.name/description",
  "status": "PROPOSAL_ONLY · NOT_IMPLEMENTED",
  "count": 108
}
```

## §43 · Canonical Term Usage Ledger

```json
{
  "Canalizzazione": 5,
  "Riflesso": 4,
  "Rituale": 6,
  "Vuoto": 5,
  "Frammento": 4,
  "Marchio": 7,
  "Assenza": 5,
  "Dissipazione": 4,
  "Drenaggio": 2,
  "Faro Rovesciato": 2,
  "Onirade": 2
}
```

## §44 · Restricted Term Usage Ledger

```json
{
  "Onirade": 2,
  "Onirade_cap": 4,
  "Faro Rovesciato": 2,
  "Faro_Rovesciato_cap": 2,
  "legendary_only": true
}
```

## §45 · Forbidden Term Validation

```json
{
  "violations_count": 0,
  "forbidden_list": [
    "Sacro",
    "Sacri",
    "Sacra",
    "Sacre",
    "Luce",
    "Luci",
    "Ossa",
    "Bestia",
    "Bestie",
    "Alchimia",
    "Bacchetta",
    "Tomo",
    "Grimorio",
    "Ladro",
    "Assassino",
    "Nael",
    "Payoff",
    "Warlock",
    "Patrono",
    "Patto",
    "Coven",
    "Hex"
  ]
}
```

## §46 · Head Noun Repetition Ledger

```json
{
  "global_counts": {
    "Feticcio": 1,
    "Fibula": 2,
    "Cifra": 3,
    "Emblema": 2,
    "Sigillo": 4,
    "Suggello": 2,
    "Vera": 3,
    "Anello": 2,
    "Ferramento": 2,
    "Draco": 1,
    "Cerchietto": 3,
    "Punteruolo": 1,
    "Balestra": 3,
    "Lanterna": 3,
    "Reliquiario": 2,
    "Lama": 1,
    "Anelletto": 1,
    "Sandali": 1,
    "Amuleto": 2,
    "Cerchio": 1,
    "Gambali": 3,
    "Gonna": 2,
    "Torcia": 1,
    "Sopracalze": 1,
    "Coscialette": 1,
    "Fascia": 2,
    "Cinghia": 1,
    "Polsino": 1,
    "Calzari": 1,
    "Ghette": 2,
    "Suole": 1,
    "Cinturone": 2,
    "Cinta": 1,
    "Nastro": 1,
    "Fasce": 2,
    "Stivali": 1,
    "Cosciali": 2,
    "Vinca": 1,
    "Mitene": 2,
    "Pantaloni": 1,
    "Legaccio": 1,
    "Manto": 1,
    "Veste": 1,
    "Sopravveste": 3,
    "Cappuccio": 1,
    "Medaglione": 2,
    "Palandrana": 1,
    "Velo": 3,
    "Farsetto": 2,
    "Livrea": 1,
    "Manopole": 2,
    "Aureola": 1,
    "Sciarpa": 1,
    "Blusa": 1,
    "Guanti": 1,
    "Berretto": 1,
    "Ciondolo": 2,
    "Rinforzo": 2,
    "Bandoliera": 2,
    "Drappo": 3,
    "Casacca": 1,
    "Palme": 1,
    "Cuffia": 1,
    "Copricapo": 1,
    "Girocollo": 1,
    "Corazza": 1,
    "Diadema": 1
  },
  "max_global": 4,
  "cap_global": 8,
  "all_within_cap": true,
  "per_slot_max": 3,
  "per_slot_cap": 3,
  "all_per_slot_within_cap": true
}
```

## §47 · Phrase Repetition Ledger

```json
{
  "bigram_over_limit": {},
  "trigram_over_limit": {},
  "threshold": "<=2 occurrences",
  "bigram_total_distinct": 250,
  "trigram_total_distinct": 193
}
```

## §48 · Naming Pattern Usage Ledger

```json
{
  "counts": {
    "NP_T3_accessory_universal_position": 2,
    "NP_T4_accessory_universal_position": 3,
    "NP_T5_accessory_universal_position": 3,
    "NP_T5_ring_universal_position": 4,
    "NP_T1_main_hand_balestra": 1,
    "NP_T1_ring_universal_position": 1,
    "NP_T2_main_hand_pugnale": 1,
    "NP_T2_ring_universal_position": 2,
    "NP_T3_main_hand_balestra": 1,
    "NP_T3_main_hand_focus": 2,
    "NP_T3_off_hand_focus": 1,
    "NP_T3_ring_universal_position": 2,
    "NP_T4_main_hand_balestra": 1,
    "NP_T4_main_hand_pugnale": 1,
    "NP_T4_off_hand_balestra": 1,
    "NP_T4_off_hand_focus": 1,
    "NP_T4_ring_universal_position": 3,
    "NP_T5_feet_stoffa": 1,
    "NP_T5_main_hand_balestra": 1,
    "NP_T5_off_hand_balestra": 1,
    "NP_T5_off_hand_pugnale": 2,
    "NP_T1_legs_stoffa": 2,
    "NP_T1_main_hand_focus": 2,
    "NP_T2_feet_stoffa": 1,
    "NP_T2_legs_cuoio": 1,
    "NP_T2_legs_stoffa": 1,
    "NP_T2_main_hand_focus": 2,
    "NP_T2_waist_stoffa": 1,
    "NP_T2_wrist_cuoio": 1,
    "NP_T2_wrist_stoffa": 1,
    "NP_T3_feet_cuoio": 1,
    "NP_T3_feet_stoffa": 2,
    "NP_T3_legs_stoffa": 1,
    "NP_T3_waist_cuoio": 1,
    "NP_T3_waist_stoffa": 2,
    "NP_T3_wrist_stoffa": 1,
    "NP_T4_feet_cuoio": 1,
    "NP_T4_feet_stoffa": 1,
    "NP_T4_legs_cuoio": 1,
    "NP_T4_legs_stoffa": 1,
    "NP_T4_main_hand_focus": 1,
    "NP_T4_waist_stoffa": 1,
    "NP_T4_wrist_cuoio": 1,
    "NP_T5_hands_cuoio": 1,
    "NP_T5_legs_cuoio": 1,
    "NP_T5_legs_stoffa": 1,
    "NP_T5_waist_cuoio": 1,
    "NP_T5_wrist_stoffa": 1,
    "NP_T1_back_universal_position": 1,
    "NP_T1_chest_stoffa": 2,
    "NP_T1_hands_stoffa": 1,
    "NP_T1_head_stoffa": 1,
    "NP_T1_neck_universal_position": 1,
    "NP_T1_shoulders_stoffa": 1,
    "NP_T2_back_universal_position": 1,
    "NP_T2_chest_cuoio": 1,
    "NP_T2_chest_stoffa": 1,
    "NP_T2_hands_stoffa": 1,
    "NP_T2_head_stoffa": 2,
    "NP_T2_neck_universal_position": 1,
    "NP_T2_shoulders_stoffa": 1,
    "NP_T3_back_universal_position": 1,
    "NP_T3_chest_stoffa": 1,
    "NP_T3_hands_cuoio": 1,
    "NP_T3_hands_stoffa": 1,
    "NP_T3_head_cuoio": 1,
    "NP_T3_head_stoffa": 1,
    "NP_T3_neck_universal_position": 1,
    "NP_T3_shoulders_cuoio": 1,
    "NP_T3_shoulders_stoffa": 1,
    "NP_T4_back_universal_position": 1,
    "NP_T4_chest_cuoio": 1,
    "NP_T4_chest_stoffa": 1,
    "NP_T4_hands_stoffa": 1,
    "NP_T4_head_cuoio": 1,
    "NP_T4_head_stoffa": 1,
    "NP_T4_neck_universal_position": 1,
    "NP_T4_shoulders_cuoio": 1,
    "NP_T4_shoulders_stoffa": 1,
    "NP_T5_back_universal_position": 2,
    "NP_T5_chest_cuoio": 1,
    "NP_T5_hands_stoffa": 1,
    "NP_T5_head_stoffa": 1,
    "NP_T5_neck_universal_position": 2,
    "NP_T5_shoulders_stoffa": 1
  },
  "max_pattern": 4,
  "cap": 12,
  "all_within_cap": true
}
```

## §49 · Exact Collision Audit

```json
{
  "exact_duplicate": 0
}
```

## §50 · Normalized Collision Audit

```json
{
  "normalized_duplicate": 0,
  "live_catalog_collision": 0,
  "live_collision_list": []
}
```

## §51 · Near Collision Audit

```json
{
  "near_duplicates": []
}
```

## §52 · Lore Collision Audit

```json
{
  "canonical_places_referenced": [
    "Faro Rovesciato di Onirade (Legendary only)"
  ],
  "no_new_proper_names_non_legendary": true
}
```

## §53 · Class Identity Collision Audit

```json
{
  "cross_class_signature_conflicts": 0,
  "class_identity_drift_FAIL": 0
}
```

## §54 · Legacy Item Preservation

```json
{
  "count": 6,
  "draft_generated": 0,
  "policy": "PRESERVE_EXISTING",
  "slugs": [
    "warlock_patron_seal",
    "warlock_imp_collar",
    "warlock_hex_sigil",
    "warlock_black_ring",
    "warlock_cursed_pendant",
    "warlock_fetish_charm"
  ]
}
```

## §55 · Conditional Item Preservation

```json
{
  "count": 3,
  "draft_generated": 0,
  "policy": "PRESERVE_EXISTING_PENDING_VALIDATION",
  "slugs": [
    "apprentice-robe",
    "initiate_robe",
    "apprentice-handbook"
  ]
}
```

## §56 · Arcane Adept Orb Successor Identity

```json
{
  "status": "NOT_COMPATIBLE FINAL",
  "successor": "REQUIRED_FUTURE_COVERAGE",
  "phase_2_draft_created": false
}
```

## §57 · Voidpiercer Bow Exclusion

```json
{
  "status": "NOT_COMPATIBLE FINAL",
  "successor": "None",
  "name_reusable": false
}
```

## §58 · Mechanic Promise Validation

```json
{
  "violations": 0
}
```

## §59 · Stat Promise Validation

```json
{
  "violations": 0
}
```

## §60 · Proper Name Proposal Ledger

```json
{
  "count": 3,
  "non_legendary_proper_names": 0,
  "all_status": "LORE_PROPOSAL_PENDING_PM (Legendary only)"
}
```

## §61 · Legendary Alternative Comparison

```json
{
  "records": [
    {
      "blueprint_code": "cdv_t5_chest_stoffa_001",
      "candidates": [
        "Sudario del Faro Rovesciato",
        "Manto della Grande Canalizzazione",
        "Veste di Onirade"
      ],
      "agent_recommendation": "Manto della Grande Canalizzazione",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_focus_001",
      "candidates": [
        "Occhio del Faro Rovesciato",
        "Focus dell'Assenza profonda",
        "Voce di Onirade"
      ],
      "agent_recommendation": "Focus dell'Assenza profonda",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_balestra_001",
      "candidates": [
        "Scatto dei Frammenti",
        "Balestra della Traiettoria certa",
        "Voce dei Bersagli assenti"
      ],
      "agent_recommendation": "Balestra della Traiettoria certa",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    }
  ]
}
```

## §62 · Validation Summary

```json
{
  "identity_packages": 111,
  "non_legendary_primary_names": 108,
  "Legendary_packages": 3,
  "Legendary_candidate_strings": 9,
  "total_candidate_strings": 117,
  "candidate_strings": 117,
  "changed_candidate_count": 5,
  "unchanged_candidate_count": 112,
  "preserved_source_identities": 9,
  "dormant_contingency_names": 0,
  "exact_duplicate": 0,
  "normalized_duplicate": 0,
  "phrase_over_limit": 0,
  "head_noun_global_over_limit": 0,
  "head_noun_slot_over_limit": 0,
  "slot_semantic_violation": 0,
  "weapon_family_head_noun_mismatch": 0,
  "armor_family_head_noun_mismatch": 0,
  "forbidden_vocabulary_violation": 0,
  "restricted_vocabulary_violation": 0,
  "mechanic_promise_violation": 0,
  "stat_promise_violation": 0,
  "absolute_tone_violation": 0,
  "readability_flag": 0,
  "grammar_FAIL": 0,
  "agreement_FAIL": 0,
  "naturalness_FAIL": 0,
  "lexical_fit_FAIL": 0,
  "class_identity_drift_FAIL": 0,
  "prior_pm_semantic_regression": 0,
  "prior_pm_semantic_blacklist_violation": 0,
  "all_caps_respected": true,
  "all_head_noun_within_8": true,
  "all_patterns_within_12": true
}
```

## §63 · Risk Register

```json
{
  "risks": [
    {
      "id": "R1",
      "name": "Draft names non definitivi",
      "severity": "LOW",
      "mitigation": "all DRAFT_PENDING_PM"
    },
    {
      "id": "R2",
      "name": "Legendary preferred non selezionato",
      "severity": "LOW",
      "mitigation": "PM_SELECTED=0 · PM adjudica"
    },
    {
      "id": "R3",
      "name": "PM_REVIEW cases in taxonomy",
      "severity": "LOW",
      "mitigation": "elencati in §64 · non blocking"
    }
  ]
}
```

## §64 · Pm Open Questions

```json
{
  "questions": [
    {
      "question_id": "P2Q1",
      "status": "PM_ADJUDICATED_R1"
    },
    {
      "question_id": "P2Q2",
      "status": "PM_ADJUDICATED_R1"
    },
    {
      "question_id": "P2Q3",
      "status": "PM_ADJUDICATED_R1"
    },
    {
      "question_id": "P2Q4",
      "status": "PM_ADJUDICATED_R1"
    },
    {
      "question_id": "P2Q5",
      "status": "PM_ADJUDICATED_R1"
    }
  ],
  "new_questions": [],
  "pm_review_ledger": []
}
```

## §65 · Go Hold Recommendation

```json
{
  "phase_2_rev_3_recommendation": "HOLD (attendo PM FINAL CONTENT SIGN-OFF)",
  "phase_2_closure": "HOLD",
  "next_action": "await_PM_final_content_signoff"
}
```

## Change Ledger Rev-2 → Rev-3 · Legendary

| blueprint_code | structure | rev2_name | rev3_name | category |
|---|---|---|---|---|
| `cdv_t5_main_hand_balestra_001` | proper_noun | Arco dei Frammenti | **Scatto dei Frammenti** | PM_DIRECTED |

## Change Ledger Rev-2 → Rev-3 · Non-Legendary

| blueprint_code | rev2_name | rev3_name | category | change_reason |
|---|---|---|---|---|
| `cdv_t1_main_hand_balestra_001` | Arco rituale del Marchio | **Draco del Marchio** | THIRD_CHANGE_BLACKLIST_AND_HEAD_CAP | THIRD_CHANGE §E · deterministic reason=BLACKLIST_VIOLATION + HEAD_NOUN_SLOT_CAP:… |
| `cdv_t3_main_hand_focus_002` | Sigillo del cacciatore del Segno | **Sigillo della Soglia Vigile** | PM_DIRECTED | PM_DIRECTED §C.2: 'Sigillo del cacciatore del Segno' UNNATURAL_GENITIVE_CHAIN + … |
| `cdv_t3_off_hand_focus_001` | Reliquiario della soglia del Segno | **Reliquiario del Segno** | THIRD_CHANGE_COLLISION | THIRD_CHANGE §D · deterministic reason=COLLISION_PROVOKED_BY_PM_PATCH: PM patch … |
| `cdv_t1_main_hand_focus_001` | Lanterna nel Marchio | **Torcia nel Marchio** | THIRD_CHANGE_REV2_LEGACY_HEAD_CAP | THIRD_CHANGE deterministic reason=REV2_LEGACY_UNAUDITED_HEAD_CAP: Rev-2 aveva he… |

## Roster Draft · 108 Non-Legendary

| # | blueprint_code | tier | slot | rarity | ic | family | display_name_it_draft | source |
|---|---|---|---|---|---|---|---|---|
| 1 | `cdv_t3_accessory_universal_position_002` | T3 | accessory | Epic | class_specific | universal_position | **Feticcio del cercatore di Canalizzazione** | REV2 |
| 2 | `cdv_t3_accessory_universal_position_003` | T3 | accessory | Epic | class_specific | universal_position | **Fibula del cercatore di Riflesso** | REV2 |
| 3 | `cdv_t4_accessory_universal_position_001` | T4 | accessory | Epic | class_specific | universal_position | **Cifra dell'esperto del Rituale** | REV2 |
| 4 | `cdv_t4_accessory_universal_position_002` | T4 | accessory | Epic | class_specific | universal_position | **Emblema del custode della Canalizzazione** | REV2 |
| 5 | `cdv_t4_accessory_universal_position_003` | T4 | accessory | Epic | class_specific | universal_position | **Sigillo dell'esperto in Rituale** | REV2 |
| 6 | `cdv_t5_accessory_universal_position_001` | T5 | accessory | Epic | class_specific | universal_position | **Cifra dell'apice nel Vuoto** | REV2 |
| 7 | `cdv_t5_accessory_universal_position_002` | T5 | accessory | Epic | class_specific | universal_position | **Suggello del pinnacolo del Rituale** | REV2 |
| 8 | `cdv_t5_accessory_universal_position_003` | T5 | accessory | Epic | class_specific | universal_position | **Fibula della firma del Frammento** | REV2 |
| 9 | `cdv_t5_ring_universal_position_002` | T5 | ring | Epic | class_specific | universal_position | **Vera dell'apogeo nel Vuoto** | REV2 |
| 10 | `cdv_t5_ring_universal_position_003` | T5 | ring | Epic | class_specific | universal_position | **Anello del pinnacolo di Marchio** | REV2 |
| 11 | `cdv_t5_ring_universal_position_004` | T5 | ring | Epic | class_specific | universal_position | **Ferramento della firma nel Marchio** | REV2 |
| 12 | `cdv_t1_main_hand_balestra_001` | T1 | main_hand | Rare | class_specific | balestra | **Draco del Marchio** | REV3 |
| 13 | `cdv_t1_ring_universal_position_001` | T1 | ring | Rare | universal_neutral | universal_position | **Cerchietto della via** | REV2 |
| 14 | `cdv_t2_main_hand_pugnale_001` | T2 | main_hand | Rare | class_specific | pugnale | **Punteruolo di Incisione** | REV2 |
| 15 | `cdv_t2_ring_universal_position_001` | T2 | ring | Rare | universal_neutral | universal_position | **Anello del novizio semplice** | REV2 |
| 16 | `cdv_t2_ring_universal_position_002` | T2 | ring | Rare | universal_neutral | universal_position | **Ferramento di scuola dell'usanza** | REV2 |
| 17 | `cdv_t3_main_hand_balestra_001` | T3 | main_hand | Rare | class_specific | balestra | **Balestra della soglia della Proiezione** | REV2 |
| 18 | `cdv_t3_main_hand_focus_001` | T3 | main_hand | Rare | class_specific | focus | **Lanterna dell'iniziato in Canalizzazione** | REV2 |
| 19 | `cdv_t3_main_hand_focus_002` | T3 | main_hand | Rare | class_specific | focus | **Sigillo della Soglia Vigile** | REV3 |
| 20 | `cdv_t3_off_hand_focus_001` | T3 | off_hand | Rare | class_specific | focus | **Reliquiario del Segno** | REV3 |
| 21 | `cdv_t3_ring_universal_position_001` | T3 | ring | Rare | universal_neutral | universal_position | **Vera del silenzio del pellegrino** | REV2 |
| 22 | `cdv_t3_ring_universal_position_002` | T3 | ring | Rare | universal_neutral | universal_position | **Cerchietto del silenzio dell'usanza** | REV2 |
| 23 | `cdv_t4_main_hand_balestra_001` | T4 | main_hand | Rare | class_specific | balestra | **Balestra del custode di Colpo controllato** | REV2 |
| 24 | `cdv_t4_main_hand_pugnale_001` | T4 | main_hand | Rare | class_specific | pugnale | **Lama del maestro incisore** | REV2 |
| 25 | `cdv_t4_off_hand_balestra_001` | T4 | off_hand | Rare | class_specific | balestra | **Reliquiario dell'esperto di Verso arcuato** | REV2 |
| 26 | `cdv_t4_off_hand_focus_001` | T4 | off_hand | Rare | class_specific | focus | **Emblema del maestro della Risonanza** | REV2 |
| 27 | `cdv_t4_ring_universal_position_001` | T4 | ring | Rare | universal_neutral | universal_position | **Cerchietto dell'esperto del pellegrino** | REV2 |
| 28 | `cdv_t4_ring_universal_position_002` | T4 | ring | Rare | universal_neutral | universal_position | **Anelletto dell'artigiano** | REV2 |
| 29 | `cdv_t4_ring_universal_position_003` | T4 | ring | Rare | class_specific | universal_position | **Vera dell'adepto del Vuoto** | REV2 |
| 30 | `cdv_t5_feet_stoffa_001` | T5 | feet | Rare | class_specific | stoffa | **Sandali dell'apice marchiato** | REV2 |
| 31 | `cdv_t5_main_hand_balestra_002` | T5 | main_hand | Rare | class_specific | balestra | **Balestra dell'apogeo della Proiezione** | REV2 |
| 32 | `cdv_t5_off_hand_balestra_001` | T5 | off_hand | Rare | class_specific | balestra | **Cifra del canone della Traiettoria** | REV2 |
| 33 | `cdv_t5_off_hand_pugnale_001` | T5 | off_hand | Rare | class_specific | pugnale | **Suggello dell'apogeo di Passo taciturno** | REV2 |
| 34 | `cdv_t5_off_hand_pugnale_002` | T5 | off_hand | Rare | class_specific | pugnale | **Amuleto del canone di Punto vicino** | REV2 |
| 35 | `cdv_t5_ring_universal_position_001` | T5 | ring | Rare | class_specific | universal_position | **Cerchio dell'apice di Assenza** | REV2 |
| 36 | `cdv_t1_legs_stoffa_001` | T1 | legs | Uncommon | class_specific | stoffa | **Gambali del Vuoto** | REV2 |
| 37 | `cdv_t1_legs_stoffa_002` | T1 | legs | Uncommon | class_specific | stoffa | **Gonna del Frammento** | REV2 |
| 38 | `cdv_t1_main_hand_focus_001` | T1 | main_hand | Uncommon | class_specific | focus | **Torcia nel Marchio** | REV3 |
| 39 | `cdv_t1_main_hand_focus_002` | T1 | main_hand | Uncommon | class_specific | focus | **Sigillo di Fiamma calma** | REV2 |
| 40 | `cdv_t2_feet_stoffa_001` | T2 | feet | Uncommon | class_specific | stoffa | **Sopracalze dell'iniziato di Assenza** | REV2 |
| 41 | `cdv_t2_legs_cuoio_001` | T2 | legs | Uncommon | class_specific | cuoio | **Gambali di cuoio tecnico della Marcia** | REV2 |
| 42 | `cdv_t2_legs_stoffa_001` | T2 | legs | Uncommon | class_specific | stoffa | **Coscialette tecnico del Riflesso** | REV2 |
| 43 | `cdv_t2_main_hand_focus_001` | T2 | main_hand | Uncommon | class_specific | focus | **Lanterna dell'iniziato del Riflesso** | REV2 |
| 44 | `cdv_t2_main_hand_focus_002` | T2 | main_hand | Uncommon | class_specific | focus | **Lanterna tecnico di Marchio** | REV2 |
| 45 | `cdv_t2_waist_stoffa_001` | T2 | waist | Uncommon | class_specific | stoffa | **Fascia dell'iniziato della Dissipazione** | REV2 |
| 46 | `cdv_t2_wrist_cuoio_001` | T2 | wrist | Uncommon | class_specific | cuoio | **Cinghia tecnico di Sentiero** | REV2 |
| 47 | `cdv_t2_wrist_stoffa_001` | T2 | wrist | Uncommon | class_specific | stoffa | **Polsino di Vuoto** | REV2 |
| 48 | `cdv_t3_feet_cuoio_001` | T3 | feet | Uncommon | class_specific | cuoio | **Calzari conciati del Sentiero** | REV2 |
| 49 | `cdv_t3_feet_stoffa_001` | T3 | feet | Uncommon | class_specific | stoffa | **Ghette del discepolo in Dissipazione** | REV2 |
| 50 | `cdv_t3_feet_stoffa_002` | T3 | feet | Uncommon | class_specific | stoffa | **Suole dell'iniziato nel Rito** | REV2 |
| 51 | `cdv_t3_legs_stoffa_001` | T3 | legs | Uncommon | class_specific | stoffa | **Gambali del discepolo in Canalizzazione** | REV2 |
| 52 | `cdv_t3_waist_cuoio_001` | T3 | waist | Uncommon | class_specific | cuoio | **Cinturone dell'iniziato della Marcia** | REV2 |
| 53 | `cdv_t3_waist_stoffa_001` | T3 | waist | Uncommon | class_specific | stoffa | **Cinta dell'iniziato del Rito** | REV2 |
| 54 | `cdv_t3_waist_stoffa_002` | T3 | waist | Uncommon | class_specific | stoffa | **Nastro dell'iniziato rituale** | REV2 |
| 55 | `cdv_t3_wrist_stoffa_001` | T3 | wrist | Uncommon | class_specific | stoffa | **Fasce da polso dell'iniziato dei Frammenti** | REV2 |
| 56 | `cdv_t4_feet_cuoio_001` | T4 | feet | Uncommon | class_specific | cuoio | **Stivali dell'esperto di Battuta** | REV2 |
| 57 | `cdv_t4_feet_stoffa_001` | T4 | feet | Uncommon | class_specific | stoffa | **Ghette dell'adepto di Drenaggio** | REV2 |
| 58 | `cdv_t4_legs_cuoio_001` | T4 | legs | Uncommon | class_specific | cuoio | **Cosciali dell'adepto del Cammino** | REV2 |
| 59 | `cdv_t4_legs_stoffa_001` | T4 | legs | Uncommon | class_specific | stoffa | **Gonna dell'esperto nel Riflesso** | REV2 |
| 60 | `cdv_t4_main_hand_focus_001` | T4 | main_hand | Uncommon | class_specific | focus | **Sigillo del veggente di Segno** | REV2 |
| 61 | `cdv_t4_waist_stoffa_001` | T4 | waist | Uncommon | class_specific | stoffa | **Fascia del veggente di Drenaggio** | REV2 |
| 62 | `cdv_t4_wrist_cuoio_001` | T4 | wrist | Uncommon | class_specific | cuoio | **Vinca dell'esperto in Silenzio** | REV2 |
| 63 | `cdv_t5_hands_cuoio_001` | T5 | hands | Uncommon | shared_family | cuoio | **Mitene dell'apogeo della Veglia** | REV2 |
| 64 | `cdv_t5_legs_cuoio_001` | T5 | legs | Uncommon | class_specific | cuoio | **Cosciali dell'apice in Marcia** | REV2 |
| 65 | `cdv_t5_legs_stoffa_001` | T5 | legs | Uncommon | class_specific | stoffa | **Pantaloni dell'apice marchiato** | REV2 |
| 66 | `cdv_t5_waist_cuoio_001` | T5 | waist | Uncommon | class_specific | cuoio | **Cinturone dell'apogeo in Marcia** | REV2 |
| 67 | `cdv_t5_wrist_stoffa_001` | T5 | wrist | Uncommon | shared_family | stoffa | **Legaccio dell'apice dello Studio** | REV2 |
| 68 | `cdv_t1_back_universal_position_001` | T1 | back | Common | universal_neutral | universal_position | **Manto di archivio** | REV2 |
| 69 | `cdv_t1_chest_stoffa_001` | T1 | chest | Common | shared_family | stoffa | **Veste di Metodo** | REV2 |
| 70 | `cdv_t1_chest_stoffa_002` | T1 | chest | Common | shared_family | stoffa | **Sopravveste di Metodo** | REV2 |
| 71 | `cdv_t1_hands_stoffa_001` | T1 | hands | Common | class_specific | stoffa | **Fasce in Dissipazione** | REV2 |
| 72 | `cdv_t1_head_stoffa_001` | T1 | head | Common | shared_family | stoffa | **Cappuccio di Studio** | REV2 |
| 73 | `cdv_t1_neck_universal_position_001` | T1 | neck | Common | universal_neutral | universal_position | **Medaglione della bottega** | REV2 |
| 74 | `cdv_t1_shoulders_stoffa_001` | T1 | shoulders | Common | shared_family | stoffa | **Palandrana di Cammino** | REV2 |
| 75 | `cdv_t2_back_universal_position_001` | T2 | back | Common | universal_neutral | universal_position | **Velo di usanza** | REV2 |
| 76 | `cdv_t2_chest_cuoio_001` | T2 | chest | Common | shared_family | cuoio | **Farsetto di Percorso** | REV2 |
| 77 | `cdv_t2_chest_stoffa_001` | T2 | chest | Common | shared_family | stoffa | **Livrea in Disciplina** | REV2 |
| 78 | `cdv_t2_hands_stoffa_001` | T2 | hands | Common | class_specific | stoffa | **Manopole in Assenza** | REV2 |
| 79 | `cdv_t2_head_stoffa_001` | T2 | head | Common | shared_family | stoffa | **Velo in Percorso** | REV2 |
| 80 | `cdv_t2_head_stoffa_002` | T2 | head | Common | shared_family | stoffa | **Aureola di Insegnamento** | REV2 |
| 81 | `cdv_t2_neck_universal_position_001` | T2 | neck | Common | universal_neutral | universal_position | **Medaglione del quotidiano** | REV2 |
| 82 | `cdv_t2_shoulders_stoffa_001` | T2 | shoulders | Common | shared_family | stoffa | **Sopravveste di Apprendimento** | REV2 |
| 83 | `cdv_t3_back_universal_position_001` | T3 | back | Common | universal_neutral | universal_position | **Sciarpa della cronaca** | REV2 |
| 84 | `cdv_t3_chest_stoffa_001` | T3 | chest | Common | shared_family | stoffa | **Blusa di Studio** | REV2 |
| 85 | `cdv_t3_hands_cuoio_001` | T3 | hands | Common | shared_family | cuoio | **Mitene della Disciplina** | REV2 |
| 86 | `cdv_t3_hands_stoffa_001` | T3 | hands | Common | shared_family | stoffa | **Guanti di Cammino** | REV2 |
| 87 | `cdv_t3_head_cuoio_001` | T3 | head | Common | shared_family | cuoio | **Berretto della Veglia** | REV2 |
| 88 | `cdv_t3_head_stoffa_001` | T3 | head | Common | shared_family | stoffa | **Velo della Via** | REV2 |
| 89 | `cdv_t3_neck_universal_position_001` | T3 | neck | Common | universal_neutral | universal_position | **Ciondolo semplice** | REV2 |
| 90 | `cdv_t3_shoulders_cuoio_001` | T3 | shoulders | Common | shared_family | cuoio | **Rinforzo di Disciplina** | REV2 |
| 91 | `cdv_t3_shoulders_stoffa_001` | T3 | shoulders | Common | shared_family | stoffa | **Bandoliera del Cammino** | REV2 |
| 92 | `cdv_t4_back_universal_position_001` | T4 | back | Common | universal_neutral | universal_position | **Drappo di quotidiano** | REV2 |
| 93 | `cdv_t4_chest_cuoio_001` | T4 | chest | Common | shared_family | cuoio | **Farsetto di Bilico** | REV2 |
| 94 | `cdv_t4_chest_stoffa_001` | T4 | chest | Common | shared_family | stoffa | **Casacca di Disciplina** | REV2 |
| 95 | `cdv_t4_hands_stoffa_001` | T4 | hands | Common | class_specific | stoffa | **Palme di Dissipazione** | REV2 |
| 96 | `cdv_t4_head_cuoio_001` | T4 | head | Common | shared_family | cuoio | **Cuffia di Sentiero** | REV2 |
| 97 | `cdv_t4_head_stoffa_001` | T4 | head | Common | shared_family | stoffa | **Copricapo dell'Insegnamento** | REV2 |
| 98 | `cdv_t4_neck_universal_position_001` | T4 | neck | Common | universal_neutral | universal_position | **Girocollo dell'usanza** | REV2 |
| 99 | `cdv_t4_shoulders_cuoio_001` | T4 | shoulders | Common | shared_family | cuoio | **Rinforzo di Scuola** | REV2 |
| 100 | `cdv_t4_shoulders_stoffa_001` | T4 | shoulders | Common | shared_family | stoffa | **Sopravveste dell'Insegnamento** | REV2 |
| 101 | `cdv_t5_back_universal_position_001` | T5 | back | Common | universal_neutral | universal_position | **Drappo di mestiere** | REV2 |
| 102 | `cdv_t5_back_universal_position_002` | T5 | back | Common | universal_neutral | universal_position | **Drappo in scambio** | REV2 |
| 103 | `cdv_t5_chest_cuoio_001` | T5 | chest | Common | shared_family | cuoio | **Corazza di Percorso** | REV2 |
| 104 | `cdv_t5_hands_stoffa_001` | T5 | hands | Common | shared_family | stoffa | **Manopole del Sentiero** | REV2 |
| 105 | `cdv_t5_head_stoffa_001` | T5 | head | Common | shared_family | stoffa | **Diadema dello Studio** | REV2 |
| 106 | `cdv_t5_neck_universal_position_001` | T5 | neck | Common | universal_neutral | universal_position | **Amuleto di artigiano** | REV2 |
| 107 | `cdv_t5_neck_universal_position_002` | T5 | neck | Common | universal_neutral | universal_position | **Ciondolo dello scriba** | REV2 |
| 108 | `cdv_t5_shoulders_stoffa_001` | T5 | shoulders | Common | shared_family | stoffa | **Bandoliera di Veglia** | REV2 |

## Legendary Candidate Roster (Rev-3)

### cdv_t5_chest_stoffa_001 · T5 chest stoffa
- narrative_role: `apogee_of_ritual_channeling` · agent_recommendation: **Manto della Grande Canalizzazione** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun** (REV2): `Sudario del Faro Rovesciato`
  - **ritual_title** (REV2): `Manto della Grande Canalizzazione`
  - **hybrid** (REV2): `Veste di Onirade`

### cdv_t5_main_hand_focus_001 · T5 main_hand focus
- narrative_role: `signature_weapon` · agent_recommendation: **Focus dell'Assenza profonda** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun** (REV2): `Occhio del Faro Rovesciato`
  - **ritual_title** (REV2): `Focus dell'Assenza profonda`
  - **hybrid** (REV2): `Voce di Onirade`

### cdv_t5_main_hand_balestra_001 · T5 main_hand balestra
- narrative_role: `ranged_ritual_signature` · agent_recommendation: **Balestra della Traiettoria certa** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun** (REV3): `Scatto dei Frammenti`
  - **ritual_title** (REV2): `Balestra della Traiettoria certa`
  - **hybrid** (REV2): `Voce dei Bersagli assenti`

## Explicit STOP

```
IS2_A_Phase_1            = CLOSED / PM-LOCKED
IS2_A_Phase_2_R0         = REJECTED_FOR_COMPLIANCE (AUDIT_REFERENCE_ONLY)
IS2_A_Phase_2_Rev_1      = STRUCTURAL_COMPLIANCE_PASS · CONTENT_REVIEW_SUPERSEDED
IS2_A_Phase_2_Rev_2      = AUTOMATED_ZERO-BLOCKING_PASS · PM_CONTENT_PATCH_REQUIRED
IS2_A_Phase_2_Rev_3      = TARGET FINAL DRAFT (attendo PM FINAL CONTENT SIGN-OFF)
Phase_2_closure          = HOLD
IS2_B                    = HOLD
NC1                      = HOLD
Registry_v3_gen          = NOT_AUTHORIZED
Registry_v3_app          = NOT_AUTHORIZED
Gate_11                  = HOLD
Monaco                   = HOLD
next_action              = ATTENDO PM FINAL CONTENT SIGN-OFF
```