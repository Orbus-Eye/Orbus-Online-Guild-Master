# R18.6.RV3-IS2-A Phase 2 · Rev-1 · Full Identity/Naming/Lore Roster · DRAFT

**Gate**: `R18.6.RV3-IS2-A Phase 2 · Rev-1` · **Status**: `REV1_DRAFT_GENERATED · AWAITING_PM_REVIEW`  
**Regime**: `DOCUMENTAL_ONLY · ITALIAN_ONLY · NO_RUNTIME · NO_APPLY` · **UTC**: `2026-07-12T20:38:16.743804+00:00`  
**Supersedes**: `DRAFT_R0` · **R0 status**: `REJECTED_FOR_COMPLIANCE · AUDIT_REFERENCE_ONLY`  
**R0 MD sha256**: `ef487f1cfffdf7b7d27d7457591047be253840548b4584cf23342d544e4a7d6d`  
**R0 JSON sha256**: `4a0e04a46be1381261848bbdf7d427ec54ab482d94ed57fb4b9db3c333fd54c1`  
**Phase 2 closure**: `HOLD`

---

## §1 · Executive Summary

```json
{
  "title": "R18.6.RV3-IS2-A Phase 2 · Rev-1 · Full Identity/Naming/Lore Draft Roster",
  "gate": "R18.6.RV3-IS2-A Phase 2",
  "revision": "R1",
  "supersedes": "DRAFT_R0",
  "r0_status": "REJECTED_FOR_COMPLIANCE · AUDIT_REFERENCE_ONLY",
  "r0_md_sha256": "ef487f1cfffdf7b7d27d7457591047be253840548b4584cf23342d544e4a7d6d",
  "r0_json_sha256": "4a0e04a46be1381261848bbdf7d427ec54ab482d94ed57fb4b9db3c333fd54c1",
  "content": "117 candidate strings zero-violation · 108 non-Legendary primary drafts + 9 Legendary A/B/C · 111 lore drafts · closure HOLD."
}
```

## §2 · Scope

```json
{
  "in_scope": [
    "108 non-Legendary primary drafts (Rev-1)",
    "9 Legendary candidates (3 unità · A/B/C forms)",
    "111 lore drafts (italiano · 1-2 frasi · <=45 parole)",
    "global n-gram audit (bigram/trigram cap<=2)",
    "slot/weapon-family/armor-family semantic strict",
    "absolute-tone + readability audits",
    "collision audit vs live 178 + R0 candidates (tracking)"
  ],
  "out_of_scope": [
    "PM_APPROVED / CANONICAL / LOCKED naming",
    "stat/effect assignment (IS2-B)",
    "Registry v3 generation/apply",
    "DB writes / migrations",
    "IS2-B / NC1 / Gate 11 kickoff",
    "Phase 2 formal closure"
  ]
}
```

## §3 · Governance

```json
{
  "regime": "DOCUMENTAL_ONLY · ITALIAN_ONLY",
  "pm_verdict_ref": "R18.6.RV3-IS2-A Phase 2 Rev-1 · GO (post R0 rejected)",
  "phase_1_lock": "IMMUTABLE",
  "phase_2_closure": "HOLD",
  "r0_preserved": true,
  "sealed_integrity": "6 passed · 36/36 byte-identical",
  "anchor_lore_meta": "a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f"
}
```

## §4 · Source Of Truth

```json
{
  "consumed": [
    "IS1 source",
    "IS2-A Phase 1 (post-patch)",
    "Orbus Lore Book",
    "AFX1",
    "IC1",
    "G1-G8",
    "R0 draft (audit reference)"
  ],
  "live_catalog_items": 178,
  "r0_candidate_universe_size": 117
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
  "vocabulary_taxonomy": "LOCKED (6-status)",
  "repetition_caps": "LOCKED",
  "restricted_policies": "LOCKED (Nael/Onirade/Faro Rovesciato/Payoff)",
  "legacy_preservation": "LOCKED",
  "tag_hint_only": "LOCKED",
  "p2q_adjudication_r1": {
    "P2Q1": "FAM_Q_EXPANSION_APPLIED",
    "P2Q2": "cohesive_families_allowed_not_required",
    "P2Q3": "AGENT_RECOMMENDATION_ONLY_accepted",
    "P2Q4": "no_global_lore_expansion_required",
    "P2Q5": "Frammento_not_Legendary_only"
  }
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
  "contingency_dormant": 3,
  "maximum_capacity": 114
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
  "total_candidate_name_strings": 117
}
```

## §10 · Contingency Exclusion

```json
{
  "count": 3,
  "draft_generated": 0,
  "content_status": "DORMANT_NOT_GENERATED",
  "name_candidate": null,
  "lore_text": null
}
```

## §11 · Naming Methodology

```json
{
  "pattern": "[head_noun_slot_family] + [tier_mod] + [family_qualifier]",
  "rules_v1": "HN_SLOT_BY_FAMILY strict",
  "rules_v2": "FAM_Q expanded 12-15/family with preposition variations",
  "legendary_rule": "hardcoded 3 A/B/C, ritual_title default recommendation"
}
```

## §12 · Lore Methodology

```json
{
  "format": "1-2 frasi <=45 parole",
  "new_proper_names": "ONLY_Legendary · LORE_PROPOSAL_PENDING_PM",
  "forbidden": [
    "nuovi regni",
    "continenti",
    "divinità",
    "fazioni",
    "Class Master",
    "personaggi storici",
    "guerre",
    "eventi fondativi",
    "luoghi maggiori"
  ]
}
```

## §13 · Vocabulary Compliance

```json
{
  "canonical_usage": {
    "Faro Rovesciato": 2,
    "Canalizzazione": 5,
    "Onirade": 2,
    "Assenza": 5,
    "Frammento": 4,
    "Dissipazione": 5,
    "Riflesso": 4,
    "Rituale": 10,
    "Vuoto": 5,
    "Marchio": 8,
    "Drenaggio": 2
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
  "all_within_caps": true,
  "restricted_Onirade_count": 2,
  "restricted_Faro_Rovesciato_count": 2,
  "restricted_context": "Onirade/Faro Rovesciato appear ONLY in Legendary class_specific Epic/Legendary candidates (allowed)"
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
    "Faro Rovesciato": 2,
    "Canalizzazione": 5,
    "Onirade": 2,
    "Assenza": 5,
    "Frammento": 4,
    "Dissipazione": 5,
    "Riflesso": 4,
    "Rituale": 10,
    "Vuoto": 5,
    "Marchio": 8,
    "Drenaggio": 2
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
  "policy": "2-4 items · no set mechanics · optional (P2Q2 adjudicated: allowed not required)"
}
```

## §20 · Collision Methodology

```json
{
  "sources": [
    "live 178",
    "117 Rev-1 candidates",
    "R0 candidate universe (tracking)",
    "Class Hall/Master canonical lore"
  ],
  "categories": [
    "EXACT_DUPLICATE",
    "NORMALIZED_DUPLICATE",
    "NEAR_DUPLICATE",
    "LIVE_CATALOG_COLLISION",
    "LORE_COLLISION",
    "CLASS_IDENTITY_COLLISION",
    "SAFE"
  ]
}
```

## §21 · Roster 111 Units

```json
{
  "records_count": 111,
  "non_legendary_count": 108,
  "legendary_count": 3,
  "see": "array 'roster_draft' + 'legendary_roster' at root"
}
```

## §22 · T1 Names

```json
{
  "count": 13,
  "names": [
    "Bocca del rito del Marchio a distanza",
    "Cerchietto della via",
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Lanterna nel Marchio",
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
    "Anello del novizio semplici",
    "Ferramento di scuola dell'usanza",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Verniera dell'iniziato del Riflesso",
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
    "Arco rituale della soglia del Marchio a distanza",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo del cacciatore del Segno",
    "Reliquiario della soglia del Segno",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Calzari di cuoio del cacciatore della Marcia",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato di Caccia rituale",
    "Cinta dell'iniziato del Rito",
    "Nastro dell'iniziato rituale",
    "Fasce da polso dell'iniziato dei Frammenti",
    "Sciarpa della cronaca",
    "Blusa di Studio",
    "Mitene della Disciplina",
    "Guanti di Cammino",
    "Berretto della Veglia",
    "Velo della Via",
    "Ciondolo semplici",
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
    "Punta del maestro di Ombra rituale",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'esperto semplici",
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
    "Verniera lunga dell'apogeo di Verso arcuato",
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
    "Ciondolo semplici",
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
    "Lanterna nel Marchio",
    "Sigillo di Fiamma calma",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Verniera dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Fascia dell'iniziato della Dissipazione",
    "Cinghia tecnico di Sentiero",
    "Polsino di Vuoto",
    "Calzari di cuoio del cacciatore della Marcia",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato di Caccia rituale",
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
    "Bocca del rito del Marchio a distanza",
    "Cerchietto della via",
    "Punteruolo di Incisione",
    "Anello del novizio semplici",
    "Ferramento di scuola dell'usanza",
    "Arco rituale della soglia del Marchio a distanza",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo del cacciatore del Segno",
    "Reliquiario della soglia del Segno",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Balestra del custode di Colpo controllato",
    "Punta del maestro di Ombra rituale",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'esperto semplici",
    "Vera dell'adepto del Vuoto",
    "Sandali dell'apice marchiato",
    "Verniera lunga dell'apogeo di Verso arcuato",
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
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Manto della Canalizzazione consumata",
          "canonical_terms": {
            "Canalizzazione": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
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
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Manto della Canalizzazione consumata",
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
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Focus dell'Assenza consumata",
          "canonical_terms": {
            "Assenza": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
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
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Focus dell'Assenza consumata",
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
          "candidate_name": "Lancia dei Frammenti",
          "canonical_terms": {
            "Frammento": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Balestra della Dissipazione consumata",
          "canonical_terms": {
            "Dissipazione": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Verniera dei Bersagli assenti",
          "canonical_terms": {
            "Assenza": 1
          },
          "restricted_terms": {},
          "forbidden_terms_detected": [],
          "absolute_tone_detected": [],
          "readability_flag": null,
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Balestra della Dissipazione consumata",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_main_hand_balestra",
      "lore_text_it_draft": "Draft Legendary breve: identità di firma, pending PM adjudication.",
      "PM_review_required": true
    }
  ],
  "preferred_candidate_policy": "AGENT_RECOMMENDATION_ONLY (ritual_title default) · PM adjudication required"
}
```

## §32 · Focus Naming

```json
{
  "count": 9,
  "names": [
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo del cacciatore del Segno",
    "Reliquiario della soglia del Segno",
    "Emblema del maestro della Risonanza",
    "Lanterna nel Marchio",
    "Sigillo di Fiamma calma",
    "Verniera dell'iniziato del Riflesso",
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
    "Bocca del rito del Marchio a distanza",
    "Arco rituale della soglia del Marchio a distanza",
    "Balestra del custode di Colpo controllato",
    "Reliquiario dell'esperto di Verso arcuato",
    "Verniera lunga dell'apogeo di Verso arcuato",
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
    "Punta del maestro di Ombra rituale",
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
    "Calzari di cuoio del cacciatore della Marcia",
    "Cinturone dell'iniziato di Caccia rituale",
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
    "Anello del novizio semplici",
    "Ferramento di scuola dell'usanza",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'esperto semplici",
    "Vera dell'adepto del Vuoto",
    "Cerchio dell'apice di Assenza",
    "Manto di archivio",
    "Medaglione della bottega",
    "Velo di usanza",
    "Medaglione del quotidiano",
    "Sciarpa della cronaca",
    "Ciondolo semplici",
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
    "Bocca del rito del Marchio a distanza",
    "Punteruolo di Incisione",
    "Arco rituale della soglia del Marchio a distanza",
    "Lanterna dell'iniziato in Canalizzazione",
    "Sigillo del cacciatore del Segno",
    "Reliquiario della soglia del Segno",
    "Balestra del custode di Colpo controllato",
    "Punta del maestro di Ombra rituale",
    "Reliquiario dell'esperto di Verso arcuato",
    "Emblema del maestro della Risonanza",
    "Vera dell'adepto del Vuoto",
    "Sandali dell'apice marchiato",
    "Verniera lunga dell'apogeo di Verso arcuato",
    "Cifra del canone della Traiettoria",
    "Suggello dell'apogeo di Passo taciturno",
    "Amuleto del canone di Punto vicino",
    "Cerchio dell'apice di Assenza",
    "Gambali del Vuoto",
    "Gonna del Frammento",
    "Lanterna nel Marchio",
    "Sigillo di Fiamma calma",
    "Sopracalze dell'iniziato di Assenza",
    "Gambali di cuoio tecnico della Marcia",
    "Coscialette tecnico del Riflesso",
    "Verniera dell'iniziato del Riflesso",
    "Lanterna tecnico di Marchio",
    "Fascia dell'iniziato della Dissipazione",
    "Cinghia tecnico di Sentiero",
    "Polsino di Vuoto",
    "Calzari di cuoio del cacciatore della Marcia",
    "Ghette del discepolo in Dissipazione",
    "Suole dell'iniziato nel Rito",
    "Gambali del discepolo in Canalizzazione",
    "Cinturone dell'iniziato di Caccia rituale",
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
    "Anello del novizio semplici",
    "Ferramento di scuola dell'usanza",
    "Vera del silenzio del pellegrino",
    "Cerchietto del silenzio dell'usanza",
    "Cerchietto dell'esperto del pellegrino",
    "Anelletto dell'esperto semplici",
    "Manto di archivio",
    "Medaglione della bottega",
    "Velo di usanza",
    "Medaglione del quotidiano",
    "Sciarpa della cronaca",
    "Ciondolo semplici",
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
  "status": "DRAFT_PENDING_PM"
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
  "Faro Rovesciato": 2,
  "Canalizzazione": 5,
  "Onirade": 2,
  "Assenza": 5,
  "Frammento": 4,
  "Dissipazione": 5,
  "Riflesso": 4,
  "Rituale": 10,
  "Vuoto": 5,
  "Marchio": 8,
  "Drenaggio": 2
}
```

## §44 · Restricted Term Usage Ledger

```json
{
  "Onirade": 2,
  "Onirade_cap": 4,
  "Faro Rovesciato": 2,
  "Faro_Rovesciato_cap": 2,
  "class_specific_only": true,
  "legendary_epic_only": true,
  "PM_review": true
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
    "Bocca del rito": 1,
    "Cerchietto": 3,
    "Punteruolo": 1,
    "Arco rituale": 1,
    "Lanterna": 3,
    "Reliquiario": 2,
    "Balestra": 1,
    "Punta": 1,
    "Anelletto": 1,
    "Sandali": 1,
    "Verniera lunga": 1,
    "Amuleto": 2,
    "Cerchio": 1,
    "Gambali": 2,
    "Gonna": 2,
    "Sopracalze": 1,
    "Gambali di cuoio": 1,
    "Coscialette": 1,
    "Verniera": 1,
    "Fascia": 2,
    "Cinghia": 1,
    "Polsino": 1,
    "Calzari di cuoio": 1,
    "Ghette": 2,
    "Suole": 1,
    "Cinturone": 2,
    "Cinta": 1,
    "Nastro": 1,
    "Fasce da polso": 1,
    "Stivali": 1,
    "Cosciali": 2,
    "Vinca": 1,
    "Mitene": 2,
    "Pantaloni": 1,
    "Legaccio": 1,
    "Manto": 1,
    "Veste": 1,
    "Sopravveste": 3,
    "Fasce": 1,
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
  "threshold": "<=2 occurrences for any normalized n-gram >=2 words",
  "bigram_total_distinct": 261,
  "trigram_total_distinct": 208
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
  "live_collision_list": [],
  "r0_candidate_overlap_count": 5,
  "r0_candidate_overlap_note": "OVERLAP IS TRACKING ONLY · not a violation · R0 audit-reference retained"
}
```

## §51 · Near Collision Audit

```json
{
  "near_duplicates": [],
  "note": "no automatic near-flagging in Rev-1 draft"
}
```

## §52 · Lore Collision Audit

```json
{
  "canonical_places_referenced": [
    "Faro Rovesciato di Onirade (lore/name restricted, Legendary only)"
  ],
  "no_new_proper_names_non_legendary": true
}
```

## §53 · Class Identity Collision Audit

```json
{
  "cross_class_signature_conflicts": 0
}
```

## §54 · Legacy Item Preservation

```json
{
  "count": 6,
  "draft_generated": 0,
  "policy": "PRESERVE_EXISTING · no rename · no translation · no retro-branding",
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
  "violations": 0,
  "forbidden_patterns": [
    "annulla ogni evocazione",
    "dissipa qualsiasi effetto",
    "uccide gli incorporei",
    "ignora il boss",
    "rende invulnerabili",
    "garantisce un Frammento"
  ]
}
```

## §59 · Stat Promise Validation

```json
{
  "violations": 0,
  "forbidden_patterns": [
    "+N Intelligenza",
    "%",
    "proc",
    "durata numerica",
    "cap",
    "danno",
    "ILVL"
  ]
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
        "Manto della Canalizzazione consumata",
        "Veste di Onirade"
      ],
      "agent_recommendation": "Manto della Canalizzazione consumata",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_focus_001",
      "candidates": [
        "Occhio del Faro Rovesciato",
        "Focus dell'Assenza consumata",
        "Voce di Onirade"
      ],
      "agent_recommendation": "Focus dell'Assenza consumata",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_balestra_001",
      "candidates": [
        "Lancia dei Frammenti",
        "Balestra della Dissipazione consumata",
        "Verniera dei Bersagli assenti"
      ],
      "agent_recommendation": "Balestra della Dissipazione consumata",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    }
  ]
}
```

## §62 · Validation Summary

```json
{
  "active_roster_rows": 120,
  "preserved_existing": 9,
  "new_future_identity_packages": 111,
  "new_future_draft_identity_rows": 111,
  "non_legendary_primary_draft_names": 108,
  "legendary_identity_packages": 3,
  "legendary_candidate_names": 9,
  "total_candidate_name_strings": 117,
  "dormant_contingency_names": 0,
  "exact_duplicate": 0,
  "normalized_duplicate": 0,
  "phrase_over_limit": 0,
  "slot_semantic_violation": 0,
  "weapon_family_head_noun_mismatch": 0,
  "armor_family_head_noun_mismatch": 0,
  "forbidden_vocabulary_violation": 0,
  "restricted_vocabulary_violation": 0,
  "mechanic_promise_violation": 0,
  "stat_promise_violation": 0,
  "absolute_tone_violation": 0,
  "readability_flag": 0,
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
      "name": "Cohesive families non implementate",
      "severity": "LOW",
      "mitigation": "P2Q2 adjudicated as optional"
    },
    {
      "id": "R3",
      "name": "Legendary preferred non selezionato",
      "severity": "LOW",
      "mitigation": "AGENT_RECOMMENDATION_ONLY · PM adjudica"
    },
    {
      "id": "R4",
      "name": "Pattern universal_position densi (32 items)",
      "severity": "LOW",
      "mitigation": "HN pool distinto per slot · cap 12 rispettato"
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
      "status": "PM_ADJUDICATED_R1",
      "resolution": "FAM_Q_EXPANSION_APPLIED"
    },
    {
      "question_id": "P2Q2",
      "status": "PM_ADJUDICATED_R1",
      "resolution": "cohesive_families_allowed_not_required"
    },
    {
      "question_id": "P2Q3",
      "status": "PM_ADJUDICATED_R1",
      "resolution": "AGENT_RECOMMENDATION_ONLY_accepted"
    },
    {
      "question_id": "P2Q4",
      "status": "PM_ADJUDICATED_R1",
      "resolution": "no_global_lore_expansion_required"
    },
    {
      "question_id": "P2Q5",
      "status": "PM_ADJUDICATED_R1",
      "resolution": "Frammento_not_Legendary_only"
    }
  ],
  "new_questions": []
}
```

## §65 · Go Hold Recommendation

```json
{
  "phase_2_rev_1_recommendation": "HOLD (attendo PM review Rev-1)",
  "phase_2_closure": "HOLD",
  "next_action": "await_PM_review_of_rev1_draft"
}
```

## Roster Draft · 108 Non-Legendary

| # | blueprint_code | tier | slot | rarity | ic | family | display_name_it_draft | head_noun |
|---|---|---|---|---|---|---|---|---|
| 1 | `cdv_t3_accessory_universal_position_002` | T3 | accessory | Epic | class_specific | universal_position | **Feticcio del cercatore di Canalizzazione** | Feticcio |
| 2 | `cdv_t3_accessory_universal_position_003` | T3 | accessory | Epic | class_specific | universal_position | **Fibula del cercatore di Riflesso** | Fibula |
| 3 | `cdv_t4_accessory_universal_position_001` | T4 | accessory | Epic | class_specific | universal_position | **Cifra dell'esperto del Rituale** | Cifra |
| 4 | `cdv_t4_accessory_universal_position_002` | T4 | accessory | Epic | class_specific | universal_position | **Emblema del custode della Canalizzazione** | Emblema |
| 5 | `cdv_t4_accessory_universal_position_003` | T4 | accessory | Epic | class_specific | universal_position | **Sigillo dell'esperto in Rituale** | Sigillo |
| 6 | `cdv_t5_accessory_universal_position_001` | T5 | accessory | Epic | class_specific | universal_position | **Cifra dell'apice nel Vuoto** | Cifra |
| 7 | `cdv_t5_accessory_universal_position_002` | T5 | accessory | Epic | class_specific | universal_position | **Suggello del pinnacolo del Rituale** | Suggello |
| 8 | `cdv_t5_accessory_universal_position_003` | T5 | accessory | Epic | class_specific | universal_position | **Fibula della firma del Frammento** | Fibula |
| 9 | `cdv_t5_ring_universal_position_002` | T5 | ring | Epic | class_specific | universal_position | **Vera dell'apogeo nel Vuoto** | Vera |
| 10 | `cdv_t5_ring_universal_position_003` | T5 | ring | Epic | class_specific | universal_position | **Anello del pinnacolo di Marchio** | Anello |
| 11 | `cdv_t5_ring_universal_position_004` | T5 | ring | Epic | class_specific | universal_position | **Ferramento della firma nel Marchio** | Ferramento |
| 12 | `cdv_t1_main_hand_balestra_001` | T1 | main_hand | Rare | class_specific | balestra | **Bocca del rito del Marchio a distanza** | Bocca del rito |
| 13 | `cdv_t1_ring_universal_position_001` | T1 | ring | Rare | universal_neutral | universal_position | **Cerchietto della via** | Cerchietto |
| 14 | `cdv_t2_main_hand_pugnale_001` | T2 | main_hand | Rare | class_specific | pugnale | **Punteruolo di Incisione** | Punteruolo |
| 15 | `cdv_t2_ring_universal_position_001` | T2 | ring | Rare | universal_neutral | universal_position | **Anello del novizio semplici** | Anello |
| 16 | `cdv_t2_ring_universal_position_002` | T2 | ring | Rare | universal_neutral | universal_position | **Ferramento di scuola dell'usanza** | Ferramento |
| 17 | `cdv_t3_main_hand_balestra_001` | T3 | main_hand | Rare | class_specific | balestra | **Arco rituale della soglia del Marchio a distanza** | Arco rituale |
| 18 | `cdv_t3_main_hand_focus_001` | T3 | main_hand | Rare | class_specific | focus | **Lanterna dell'iniziato in Canalizzazione** | Lanterna |
| 19 | `cdv_t3_main_hand_focus_002` | T3 | main_hand | Rare | class_specific | focus | **Sigillo del cacciatore del Segno** | Sigillo |
| 20 | `cdv_t3_off_hand_focus_001` | T3 | off_hand | Rare | class_specific | focus | **Reliquiario della soglia del Segno** | Reliquiario |
| 21 | `cdv_t3_ring_universal_position_001` | T3 | ring | Rare | universal_neutral | universal_position | **Vera del silenzio del pellegrino** | Vera |
| 22 | `cdv_t3_ring_universal_position_002` | T3 | ring | Rare | universal_neutral | universal_position | **Cerchietto del silenzio dell'usanza** | Cerchietto |
| 23 | `cdv_t4_main_hand_balestra_001` | T4 | main_hand | Rare | class_specific | balestra | **Balestra del custode di Colpo controllato** | Balestra |
| 24 | `cdv_t4_main_hand_pugnale_001` | T4 | main_hand | Rare | class_specific | pugnale | **Punta del maestro di Ombra rituale** | Punta |
| 25 | `cdv_t4_off_hand_balestra_001` | T4 | off_hand | Rare | class_specific | balestra | **Reliquiario dell'esperto di Verso arcuato** | Reliquiario |
| 26 | `cdv_t4_off_hand_focus_001` | T4 | off_hand | Rare | class_specific | focus | **Emblema del maestro della Risonanza** | Emblema |
| 27 | `cdv_t4_ring_universal_position_001` | T4 | ring | Rare | universal_neutral | universal_position | **Cerchietto dell'esperto del pellegrino** | Cerchietto |
| 28 | `cdv_t4_ring_universal_position_002` | T4 | ring | Rare | universal_neutral | universal_position | **Anelletto dell'esperto semplici** | Anelletto |
| 29 | `cdv_t4_ring_universal_position_003` | T4 | ring | Rare | class_specific | universal_position | **Vera dell'adepto del Vuoto** | Vera |
| 30 | `cdv_t5_feet_stoffa_001` | T5 | feet | Rare | class_specific | stoffa | **Sandali dell'apice marchiato** | Sandali |
| 31 | `cdv_t5_main_hand_balestra_002` | T5 | main_hand | Rare | class_specific | balestra | **Verniera lunga dell'apogeo di Verso arcuato** | Verniera lunga |
| 32 | `cdv_t5_off_hand_balestra_001` | T5 | off_hand | Rare | class_specific | balestra | **Cifra del canone della Traiettoria** | Cifra |
| 33 | `cdv_t5_off_hand_pugnale_001` | T5 | off_hand | Rare | class_specific | pugnale | **Suggello dell'apogeo di Passo taciturno** | Suggello |
| 34 | `cdv_t5_off_hand_pugnale_002` | T5 | off_hand | Rare | class_specific | pugnale | **Amuleto del canone di Punto vicino** | Amuleto |
| 35 | `cdv_t5_ring_universal_position_001` | T5 | ring | Rare | class_specific | universal_position | **Cerchio dell'apice di Assenza** | Cerchio |
| 36 | `cdv_t1_legs_stoffa_001` | T1 | legs | Uncommon | class_specific | stoffa | **Gambali del Vuoto** | Gambali |
| 37 | `cdv_t1_legs_stoffa_002` | T1 | legs | Uncommon | class_specific | stoffa | **Gonna del Frammento** | Gonna |
| 38 | `cdv_t1_main_hand_focus_001` | T1 | main_hand | Uncommon | class_specific | focus | **Lanterna nel Marchio** | Lanterna |
| 39 | `cdv_t1_main_hand_focus_002` | T1 | main_hand | Uncommon | class_specific | focus | **Sigillo di Fiamma calma** | Sigillo |
| 40 | `cdv_t2_feet_stoffa_001` | T2 | feet | Uncommon | class_specific | stoffa | **Sopracalze dell'iniziato di Assenza** | Sopracalze |
| 41 | `cdv_t2_legs_cuoio_001` | T2 | legs | Uncommon | class_specific | cuoio | **Gambali di cuoio tecnico della Marcia** | Gambali di cuoio |
| 42 | `cdv_t2_legs_stoffa_001` | T2 | legs | Uncommon | class_specific | stoffa | **Coscialette tecnico del Riflesso** | Coscialette |
| 43 | `cdv_t2_main_hand_focus_001` | T2 | main_hand | Uncommon | class_specific | focus | **Verniera dell'iniziato del Riflesso** | Verniera |
| 44 | `cdv_t2_main_hand_focus_002` | T2 | main_hand | Uncommon | class_specific | focus | **Lanterna tecnico di Marchio** | Lanterna |
| 45 | `cdv_t2_waist_stoffa_001` | T2 | waist | Uncommon | class_specific | stoffa | **Fascia dell'iniziato della Dissipazione** | Fascia |
| 46 | `cdv_t2_wrist_cuoio_001` | T2 | wrist | Uncommon | class_specific | cuoio | **Cinghia tecnico di Sentiero** | Cinghia |
| 47 | `cdv_t2_wrist_stoffa_001` | T2 | wrist | Uncommon | class_specific | stoffa | **Polsino di Vuoto** | Polsino |
| 48 | `cdv_t3_feet_cuoio_001` | T3 | feet | Uncommon | class_specific | cuoio | **Calzari di cuoio del cacciatore della Marcia** | Calzari di cuoio |
| 49 | `cdv_t3_feet_stoffa_001` | T3 | feet | Uncommon | class_specific | stoffa | **Ghette del discepolo in Dissipazione** | Ghette |
| 50 | `cdv_t3_feet_stoffa_002` | T3 | feet | Uncommon | class_specific | stoffa | **Suole dell'iniziato nel Rito** | Suole |
| 51 | `cdv_t3_legs_stoffa_001` | T3 | legs | Uncommon | class_specific | stoffa | **Gambali del discepolo in Canalizzazione** | Gambali |
| 52 | `cdv_t3_waist_cuoio_001` | T3 | waist | Uncommon | class_specific | cuoio | **Cinturone dell'iniziato di Caccia rituale** | Cinturone |
| 53 | `cdv_t3_waist_stoffa_001` | T3 | waist | Uncommon | class_specific | stoffa | **Cinta dell'iniziato del Rito** | Cinta |
| 54 | `cdv_t3_waist_stoffa_002` | T3 | waist | Uncommon | class_specific | stoffa | **Nastro dell'iniziato rituale** | Nastro |
| 55 | `cdv_t3_wrist_stoffa_001` | T3 | wrist | Uncommon | class_specific | stoffa | **Fasce da polso dell'iniziato dei Frammenti** | Fasce da polso |
| 56 | `cdv_t4_feet_cuoio_001` | T4 | feet | Uncommon | class_specific | cuoio | **Stivali dell'esperto di Battuta** | Stivali |
| 57 | `cdv_t4_feet_stoffa_001` | T4 | feet | Uncommon | class_specific | stoffa | **Ghette dell'adepto di Drenaggio** | Ghette |
| 58 | `cdv_t4_legs_cuoio_001` | T4 | legs | Uncommon | class_specific | cuoio | **Cosciali dell'adepto del Cammino** | Cosciali |
| 59 | `cdv_t4_legs_stoffa_001` | T4 | legs | Uncommon | class_specific | stoffa | **Gonna dell'esperto nel Riflesso** | Gonna |
| 60 | `cdv_t4_main_hand_focus_001` | T4 | main_hand | Uncommon | class_specific | focus | **Sigillo del veggente di Segno** | Sigillo |
| 61 | `cdv_t4_waist_stoffa_001` | T4 | waist | Uncommon | class_specific | stoffa | **Fascia del veggente di Drenaggio** | Fascia |
| 62 | `cdv_t4_wrist_cuoio_001` | T4 | wrist | Uncommon | class_specific | cuoio | **Vinca dell'esperto in Silenzio** | Vinca |
| 63 | `cdv_t5_hands_cuoio_001` | T5 | hands | Uncommon | shared_family | cuoio | **Mitene dell'apogeo della Veglia** | Mitene |
| 64 | `cdv_t5_legs_cuoio_001` | T5 | legs | Uncommon | class_specific | cuoio | **Cosciali dell'apice in Marcia** | Cosciali |
| 65 | `cdv_t5_legs_stoffa_001` | T5 | legs | Uncommon | class_specific | stoffa | **Pantaloni dell'apice marchiato** | Pantaloni |
| 66 | `cdv_t5_waist_cuoio_001` | T5 | waist | Uncommon | class_specific | cuoio | **Cinturone dell'apogeo in Marcia** | Cinturone |
| 67 | `cdv_t5_wrist_stoffa_001` | T5 | wrist | Uncommon | shared_family | stoffa | **Legaccio dell'apice dello Studio** | Legaccio |
| 68 | `cdv_t1_back_universal_position_001` | T1 | back | Common | universal_neutral | universal_position | **Manto di archivio** | Manto |
| 69 | `cdv_t1_chest_stoffa_001` | T1 | chest | Common | shared_family | stoffa | **Veste di Metodo** | Veste |
| 70 | `cdv_t1_chest_stoffa_002` | T1 | chest | Common | shared_family | stoffa | **Sopravveste di Metodo** | Sopravveste |
| 71 | `cdv_t1_hands_stoffa_001` | T1 | hands | Common | class_specific | stoffa | **Fasce in Dissipazione** | Fasce |
| 72 | `cdv_t1_head_stoffa_001` | T1 | head | Common | shared_family | stoffa | **Cappuccio di Studio** | Cappuccio |
| 73 | `cdv_t1_neck_universal_position_001` | T1 | neck | Common | universal_neutral | universal_position | **Medaglione della bottega** | Medaglione |
| 74 | `cdv_t1_shoulders_stoffa_001` | T1 | shoulders | Common | shared_family | stoffa | **Palandrana di Cammino** | Palandrana |
| 75 | `cdv_t2_back_universal_position_001` | T2 | back | Common | universal_neutral | universal_position | **Velo di usanza** | Velo |
| 76 | `cdv_t2_chest_cuoio_001` | T2 | chest | Common | shared_family | cuoio | **Farsetto di Percorso** | Farsetto |
| 77 | `cdv_t2_chest_stoffa_001` | T2 | chest | Common | shared_family | stoffa | **Livrea in Disciplina** | Livrea |
| 78 | `cdv_t2_hands_stoffa_001` | T2 | hands | Common | class_specific | stoffa | **Manopole in Assenza** | Manopole |
| 79 | `cdv_t2_head_stoffa_001` | T2 | head | Common | shared_family | stoffa | **Velo in Percorso** | Velo |
| 80 | `cdv_t2_head_stoffa_002` | T2 | head | Common | shared_family | stoffa | **Aureola di Insegnamento** | Aureola |
| 81 | `cdv_t2_neck_universal_position_001` | T2 | neck | Common | universal_neutral | universal_position | **Medaglione del quotidiano** | Medaglione |
| 82 | `cdv_t2_shoulders_stoffa_001` | T2 | shoulders | Common | shared_family | stoffa | **Sopravveste di Apprendimento** | Sopravveste |
| 83 | `cdv_t3_back_universal_position_001` | T3 | back | Common | universal_neutral | universal_position | **Sciarpa della cronaca** | Sciarpa |
| 84 | `cdv_t3_chest_stoffa_001` | T3 | chest | Common | shared_family | stoffa | **Blusa di Studio** | Blusa |
| 85 | `cdv_t3_hands_cuoio_001` | T3 | hands | Common | shared_family | cuoio | **Mitene della Disciplina** | Mitene |
| 86 | `cdv_t3_hands_stoffa_001` | T3 | hands | Common | shared_family | stoffa | **Guanti di Cammino** | Guanti |
| 87 | `cdv_t3_head_cuoio_001` | T3 | head | Common | shared_family | cuoio | **Berretto della Veglia** | Berretto |
| 88 | `cdv_t3_head_stoffa_001` | T3 | head | Common | shared_family | stoffa | **Velo della Via** | Velo |
| 89 | `cdv_t3_neck_universal_position_001` | T3 | neck | Common | universal_neutral | universal_position | **Ciondolo semplici** | Ciondolo |
| 90 | `cdv_t3_shoulders_cuoio_001` | T3 | shoulders | Common | shared_family | cuoio | **Rinforzo di Disciplina** | Rinforzo |
| 91 | `cdv_t3_shoulders_stoffa_001` | T3 | shoulders | Common | shared_family | stoffa | **Bandoliera del Cammino** | Bandoliera |
| 92 | `cdv_t4_back_universal_position_001` | T4 | back | Common | universal_neutral | universal_position | **Drappo di quotidiano** | Drappo |
| 93 | `cdv_t4_chest_cuoio_001` | T4 | chest | Common | shared_family | cuoio | **Farsetto di Bilico** | Farsetto |
| 94 | `cdv_t4_chest_stoffa_001` | T4 | chest | Common | shared_family | stoffa | **Casacca di Disciplina** | Casacca |
| 95 | `cdv_t4_hands_stoffa_001` | T4 | hands | Common | class_specific | stoffa | **Palme di Dissipazione** | Palme |
| 96 | `cdv_t4_head_cuoio_001` | T4 | head | Common | shared_family | cuoio | **Cuffia di Sentiero** | Cuffia |
| 97 | `cdv_t4_head_stoffa_001` | T4 | head | Common | shared_family | stoffa | **Copricapo dell'Insegnamento** | Copricapo |
| 98 | `cdv_t4_neck_universal_position_001` | T4 | neck | Common | universal_neutral | universal_position | **Girocollo dell'usanza** | Girocollo |
| 99 | `cdv_t4_shoulders_cuoio_001` | T4 | shoulders | Common | shared_family | cuoio | **Rinforzo di Scuola** | Rinforzo |
| 100 | `cdv_t4_shoulders_stoffa_001` | T4 | shoulders | Common | shared_family | stoffa | **Sopravveste dell'Insegnamento** | Sopravveste |
| 101 | `cdv_t5_back_universal_position_001` | T5 | back | Common | universal_neutral | universal_position | **Drappo di mestiere** | Drappo |
| 102 | `cdv_t5_back_universal_position_002` | T5 | back | Common | universal_neutral | universal_position | **Drappo in scambio** | Drappo |
| 103 | `cdv_t5_chest_cuoio_001` | T5 | chest | Common | shared_family | cuoio | **Corazza di Percorso** | Corazza |
| 104 | `cdv_t5_hands_stoffa_001` | T5 | hands | Common | shared_family | stoffa | **Manopole del Sentiero** | Manopole |
| 105 | `cdv_t5_head_stoffa_001` | T5 | head | Common | shared_family | stoffa | **Diadema dello Studio** | Diadema |
| 106 | `cdv_t5_neck_universal_position_001` | T5 | neck | Common | universal_neutral | universal_position | **Amuleto di artigiano** | Amuleto |
| 107 | `cdv_t5_neck_universal_position_002` | T5 | neck | Common | universal_neutral | universal_position | **Ciondolo dello scriba** | Ciondolo |
| 108 | `cdv_t5_shoulders_stoffa_001` | T5 | shoulders | Common | shared_family | stoffa | **Bandoliera di Veglia** | Bandoliera |

## Legendary Candidate Roster (3 unità × 3 forme A/B/C = 9)

### cdv_t5_chest_stoffa_001 · T5 chest stoffa
- narrative_role: `apogee_of_ritual_channeling` · agent_recommendation: **Manto della Canalizzazione consumata** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Sudario del Faro Rovesciato` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Manto della Canalizzazione consumata` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Veste di Onirade` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

### cdv_t5_main_hand_focus_001 · T5 main_hand focus
- narrative_role: `signature_weapon` · agent_recommendation: **Focus dell'Assenza consumata** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Occhio del Faro Rovesciato` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Focus dell'Assenza consumata` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Voce di Onirade` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

### cdv_t5_main_hand_balestra_001 · T5 main_hand balestra
- narrative_role: `ranged_ritual_signature` · agent_recommendation: **Balestra della Dissipazione consumata** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Lancia dei Frammenti` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Balestra della Dissipazione consumata` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Verniera dei Bersagli assenti` · display_status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

## Lore Draft Roster (108 non-Legendary · brief)

| blueprint_code | draft_name | lore_text_it_draft |
|---|---|---|
| `cdv_t3_accessory_universal_position_002` | Feticcio del cercatore di Canalizzazione | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t3_accessory_universal_position_003` | Fibula del cercatore di Riflesso | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_accessory_universal_position_001` | Cifra dell'esperto del Rituale | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_accessory_universal_position_002` | Emblema del custode della Canalizzazione | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_accessory_universal_position_003` | Sigillo dell'esperto in Rituale | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_accessory_universal_position_001` | Cifra dell'apice nel Vuoto | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_accessory_universal_position_002` | Suggello del pinnacolo del Rituale | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_accessory_universal_position_003` | Fibula della firma del Frammento | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_ring_universal_position_002` | Vera dell'apogeo nel Vuoto | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_ring_universal_position_003` | Anello del pinnacolo di Marchio | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_ring_universal_position_004` | Ferramento della firma nel Marchio | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t1_main_hand_balestra_001` | Bocca del rito del Marchio a distanza | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t1_ring_universal_position_001` | Cerchietto della via | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t2_main_hand_pugnale_001` | Punteruolo di Incisione | Lama per l'incisione precisa nel gesto ravvicinato. Si rivela nei momenti di veglia rituale. |
| `cdv_t2_ring_universal_position_001` | Anello del novizio semplici | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t2_ring_universal_position_002` | Ferramento di scuola dell'usanza | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t3_main_hand_balestra_001` | Arco rituale della soglia del Marchio a distanza | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t3_main_hand_focus_001` | Lanterna dell'iniziato in Canalizzazione | Focus di sostegno alla canalizzazione controllata, in stato calmo. Si rivela nei momenti di veglia rituale. |
| `cdv_t3_main_hand_focus_002` | Sigillo del cacciatore del Segno | Focus di sostegno alla canalizzazione controllata, in stato calmo. Si rivela nei momenti di veglia rituale. |
| `cdv_t3_off_hand_focus_001` | Reliquiario della soglia del Segno | Focus di sostegno alla canalizzazione controllata, in stato calmo. Si rivela nei momenti di veglia rituale. |
| `cdv_t3_ring_universal_position_001` | Vera del silenzio del pellegrino | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t3_ring_universal_position_002` | Cerchietto del silenzio dell'usanza | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t4_main_hand_balestra_001` | Balestra del custode di Colpo controllato | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_main_hand_pugnale_001` | Punta del maestro di Ombra rituale | Lama per l'incisione precisa nel gesto ravvicinato. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_off_hand_balestra_001` | Reliquiario dell'esperto di Verso arcuato | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_off_hand_focus_001` | Emblema del maestro della Risonanza | Focus di sostegno alla canalizzazione controllata, in stato calmo. Si rivela nei momenti di veglia rituale. |
| `cdv_t4_ring_universal_position_001` | Cerchietto dell'esperto del pellegrino | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t4_ring_universal_position_002` | Anelletto dell'esperto semplici | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t4_ring_universal_position_003` | Vera dell'adepto del Vuoto | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_feet_stoffa_001` | Sandali dell'apice marchiato | Veste calibrata sulle discipline arcane della soglia. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_main_hand_balestra_002` | Verniera lunga dell'apogeo di Verso arcuato | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_off_hand_balestra_001` | Cifra del canone della Traiettoria | Balestra per proiezione rituale, cadenza lenta ma precisa nel bersaglio. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_off_hand_pugnale_001` | Suggello dell'apogeo di Passo taciturno | Lama per l'incisione precisa nel gesto ravvicinato. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_off_hand_pugnale_002` | Amuleto del canone di Punto vicino | Lama per l'incisione precisa nel gesto ravvicinato. Si rivela nei momenti di veglia rituale. |
| `cdv_t5_ring_universal_position_001` | Cerchio dell'apice di Assenza | Oggetto della disciplina, calibrato sulla dissipazione controllata. Si rivela nei momenti di veglia rituale. |
| `cdv_t1_legs_stoffa_001` | Gambali del Vuoto | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t1_legs_stoffa_002` | Gonna del Frammento | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t1_main_hand_focus_001` | Lanterna nel Marchio | Focus di sostegno alla canalizzazione controllata, in stato calmo. |
| `cdv_t1_main_hand_focus_002` | Sigillo di Fiamma calma | Focus di sostegno alla canalizzazione controllata, in stato calmo. |
| `cdv_t2_feet_stoffa_001` | Sopracalze dell'iniziato di Assenza | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t2_legs_cuoio_001` | Gambali di cuoio tecnico della Marcia | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t2_legs_stoffa_001` | Coscialette tecnico del Riflesso | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t2_main_hand_focus_001` | Verniera dell'iniziato del Riflesso | Focus di sostegno alla canalizzazione controllata, in stato calmo. |
| `cdv_t2_main_hand_focus_002` | Lanterna tecnico di Marchio | Focus di sostegno alla canalizzazione controllata, in stato calmo. |
| `cdv_t2_waist_stoffa_001` | Fascia dell'iniziato della Dissipazione | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t2_wrist_cuoio_001` | Cinghia tecnico di Sentiero | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t2_wrist_stoffa_001` | Polsino di Vuoto | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t3_feet_cuoio_001` | Calzari di cuoio del cacciatore della Marcia | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t3_feet_stoffa_001` | Ghette del discepolo in Dissipazione | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t3_feet_stoffa_002` | Suole dell'iniziato nel Rito | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t3_legs_stoffa_001` | Gambali del discepolo in Canalizzazione | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t3_waist_cuoio_001` | Cinturone dell'iniziato di Caccia rituale | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t3_waist_stoffa_001` | Cinta dell'iniziato del Rito | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t3_waist_stoffa_002` | Nastro dell'iniziato rituale | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t3_wrist_stoffa_001` | Fasce da polso dell'iniziato dei Frammenti | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t4_feet_cuoio_001` | Stivali dell'esperto di Battuta | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t4_feet_stoffa_001` | Ghette dell'adepto di Drenaggio | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t4_legs_cuoio_001` | Cosciali dell'adepto del Cammino | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t4_legs_stoffa_001` | Gonna dell'esperto nel Riflesso | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t4_main_hand_focus_001` | Sigillo del veggente di Segno | Focus di sostegno alla canalizzazione controllata, in stato calmo. |
| `cdv_t4_waist_stoffa_001` | Fascia del veggente di Drenaggio | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t4_wrist_cuoio_001` | Vinca dell'esperto in Silenzio | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_hands_cuoio_001` | Mitene dell'apogeo della Veglia | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t5_legs_cuoio_001` | Cosciali dell'apice in Marcia | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_legs_stoffa_001` | Pantaloni dell'apice marchiato | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t5_waist_cuoio_001` | Cinturone dell'apogeo in Marcia | Cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_wrist_stoffa_001` | Legaccio dell'apice dello Studio | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t1_back_universal_position_001` | Manto di archivio | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t1_chest_stoffa_001` | Veste di Metodo | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t1_chest_stoffa_002` | Sopravveste di Metodo | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t1_hands_stoffa_001` | Fasce in Dissipazione | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t1_head_stoffa_001` | Cappuccio di Studio | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t1_neck_universal_position_001` | Medaglione della bottega | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t1_shoulders_stoffa_001` | Palandrana di Cammino | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t2_back_universal_position_001` | Velo di usanza | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t2_chest_cuoio_001` | Farsetto di Percorso | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t2_chest_stoffa_001` | Livrea in Disciplina | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t2_hands_stoffa_001` | Manopole in Assenza | Tessuto per contenere il segno nelle sue fasi iniziali. |
| `cdv_t2_head_stoffa_001` | Velo in Percorso | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t2_head_stoffa_002` | Aureola di Insegnamento | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t2_neck_universal_position_001` | Medaglione del quotidiano | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t2_shoulders_stoffa_001` | Sopravveste di Apprendimento | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_back_universal_position_001` | Sciarpa della cronaca | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t3_chest_stoffa_001` | Blusa di Studio | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_hands_cuoio_001` | Mitene della Disciplina | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_hands_stoffa_001` | Guanti di Cammino | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_head_cuoio_001` | Berretto della Veglia | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_head_stoffa_001` | Velo della Via | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_neck_universal_position_001` | Ciondolo semplici | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t3_shoulders_cuoio_001` | Rinforzo di Disciplina | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t3_shoulders_stoffa_001` | Bandoliera del Cammino | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_back_universal_position_001` | Drappo di quotidiano | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t4_chest_cuoio_001` | Farsetto di Bilico | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_chest_stoffa_001` | Casacca di Disciplina | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_hands_stoffa_001` | Palme di Dissipazione | Veste calibrata sulle discipline arcane della soglia. |
| `cdv_t4_head_cuoio_001` | Cuffia di Sentiero | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_head_stoffa_001` | Copricapo dell'Insegnamento | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_neck_universal_position_001` | Girocollo dell'usanza | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t4_shoulders_cuoio_001` | Rinforzo di Scuola | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t4_shoulders_stoffa_001` | Sopravveste dell'Insegnamento | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t5_back_universal_position_001` | Drappo di mestiere | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t5_back_universal_position_002` | Drappo in scambio | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t5_chest_cuoio_001` | Corazza di Percorso | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t5_hands_stoffa_001` | Manopole del Sentiero | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t5_head_stoffa_001` | Diadema dello Studio | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |
| `cdv_t5_neck_universal_position_001` | Amuleto di artigiano | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t5_neck_universal_position_002` | Ciondolo dello scriba | Oggetto d'uso comune, forgiato senza segno di scuola né appartenenza distintiva. |
| `cdv_t5_shoulders_stoffa_001` | Bandoliera di Veglia | Strumento adatto a chi cammina la via delle discipline, senza vincolo di sigillo di classe. |

## Explicit STOP

```
IS2_A_Phase_1            = CLOSED / RATIFIED
IS2_A_Phase_2_R0         = REJECTED_FOR_COMPLIANCE (AUDIT_REFERENCE_ONLY)
IS2_A_Phase_2_Rev_1      = DRAFT GENERATED
Phase_2_closure          = HOLD (attendo PM review Rev-1)
IS2_B                    = HOLD
NC1                      = HOLD
Registry_v3_gen          = NOT_AUTHORIZED
Registry_v3_app          = NOT_AUTHORIZED
Gate_11                  = HOLD
Monaco                   = HOLD
next_action              = ATTENDO VERDICT PM
```