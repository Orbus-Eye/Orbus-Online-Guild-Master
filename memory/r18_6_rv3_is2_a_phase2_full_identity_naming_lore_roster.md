# R18.6.RV3-IS2-A Phase 2 · Full Identity/Naming/Lore Roster · DRAFT

**Gate**: `R18.6.RV3-IS2-A Phase 2` · **Status**: `DRAFT_GENERATED · AWAITING_PM_REVIEW`  
**Regime**: `DOCUMENTAL_ONLY · ITALIAN_ONLY · NO_RUNTIME · NO_APPLY` · **UTC**: `2026-07-12T14:05:38.332929+00:00`  
**Phase 2 closure**: `HOLD`

---

## §1 · Executive Summary

```json
{
  "title": "Executive Summary",
  "gate": "R18.6.RV3-IS2-A Phase 2",
  "content": "Full draft roster · 108 non-Legendary + 9 Legendary candidates (3 units × 3 structures) + 111 lore drafts · all DRAFT_PENDING_PM · zero canonical · Phase 2 closure HOLD."
}
```

## §2 · Scope

```json
{
  "in_scope": [
    "108 non-Legendary primary drafts",
    "9 Legendary candidates (3 per unit)",
    "111 lore drafts",
    "collision audit vs live 178",
    "cap/repetition/forbidden validation"
  ],
  "out_of_scope": [
    "names PM_APPROVED/CANONICAL",
    "stat/effect assignment",
    "item generation",
    "Registry",
    "DB writes",
    "IS2-B/NC1/Gate11 kickoff",
    "Phase 2 closure"
  ]
}
```

## §3 · Governance

```json
{
  "regime": "DOCUMENTAL_ONLY",
  "pm_verdict_ref": "R18.6.RV3-IS2-A Phase 2 · GO FULL DRAFT ROSTER",
  "phase_1_lock": "IMMUTABLE",
  "phase_2_closure": "HOLD"
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
    "G1-G8"
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
  "vocabulary_taxonomy": "LOCKED (6-status)",
  "repetition_caps": "LOCKED",
  "restricted_policies": "LOCKED (Nael/Onirade/Faro Rovesciato/Payoff)",
  "legacy_preservation": "LOCKED",
  "tag_hint_only": "LOCKED"
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
  "content_status": "DORMANT_NOT_GENERATED"
}
```

## §11 · Naming Methodology

```json
{
  "pattern": "[head_noun_slot] + [tier_mod] + [family_qualifier]",
  "rules": [
    "universal_neutral: neutral qualifiers only · no CdV terms",
    "shared_family: no Onirade/Faro Rovesciato",
    "class_specific: canonical/restricted within caps"
  ],
  "escalation_offset": "seed_offset 0..19 to satisfy caps and uniqueness"
}
```

## §12 · Lore Methodology

```json
{
  "format": "1-2 frasi ≤45 parole",
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
    "Vuoto": 3,
    "Onirade": 0,
    "Marchio": 8,
    "Frammento": 5,
    "Faro Rovesciato": 0,
    "Drenaggio": 1,
    "Dissipazione": 6,
    "Riflesso": 8,
    "Assenza": 8,
    "Rituale": 10,
    "Canalizzazione": 6
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
  "restricted_Onirade_count": 0,
  "restricted_Faro_Rovesciato_count": 0
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
    "Vuoto": 3,
    "Onirade": 0,
    "Marchio": 8,
    "Frammento": 5,
    "Faro Rovesciato": 0,
    "Drenaggio": 1,
    "Dissipazione": 6,
    "Riflesso": 8,
    "Assenza": 8,
    "Rituale": 10,
    "Canalizzazione": 6
  },
  "phrase_violations": {
    "del rito": 16,
    "del marchio": 8,
    "della proiezione": 3,
    "del riflesso": 8,
    "del faro": 4,
    "della caccia": 8,
    "della caccia rituale": 8,
    "caccia rituale": 8,
    "della canalizzazione": 7,
    "tecnico del": 5,
    "tecnico del rito": 4,
    "del discepolo": 4,
    "del discepolo del": 3,
    "del discepolo del marchio": 3,
    "discepolo del": 3,
    "discepolo del marchio": 3,
    "monile del": 3,
    "del cercatore": 4,
    "del frammento": 5,
    "della soglia": 7,
    "della soglia del": 4,
    "della soglia del rito": 3,
    "soglia del": 4,
    "soglia del rito": 3,
    "lanterna del": 3,
    "della dissipazione": 7,
    "della dissipazione mirata": 3,
    "dissipazione mirata": 3,
    "del maestro": 4,
    "del maestro del": 3,
    "maestro del": 3,
    "del vuoto": 3,
    "del custode": 5,
    "del veggente": 4,
    "della marcia": 8,
    "dell'adepto della": 3,
    "dell'adepto della marcia": 3,
    "della firma": 6,
    "del canone": 6,
    "del canone del": 4,
    "canone del": 4,
    "dell'apice della": 3
  },
  "pattern_max": 4,
  "pattern_usage_all_within_12": true
}
```

## §15 · Tier Tone Compliance

```json
{
  "tier_distribution": {
    "T1": 13,
    "T2": 19,
    "T3": 25,
    "T4": 26,
    "T5": 28
  }
}
```

## §16 · Rarity Tone Compliance

```json
{
  "rarity_distribution": {
    "Common": 41,
    "Uncommon": 32,
    "Rare": 24,
    "Epic": 11,
    "Legendary": 3
  }
}
```

## §17 · Slot Semantic Compliance

```json
{
  "slot_distribution": {
    "back": 6,
    "chest": 9,
    "hands": 7,
    "head": 8,
    "legs": 9,
    "main_hand": 15,
    "neck": 6,
    "ring": 12,
    "shoulders": 7,
    "feet": 7,
    "waist": 6,
    "wrist": 5,
    "accessory": 8,
    "off_hand": 6
  },
  "validation_status": "CLEAN_ALL"
}
```

## §18 · Identity Class Compliance

```json
{
  "identity_distribution": {
    "universal_neutral": 19,
    "shared_family": 29,
    "class_specific": 63
  }
}
```

## §19 · Cohesive Family Usage

```json
{
  "families_used": 0,
  "policy": "2-4 items · no set mechanics · optional in Phase 2 draft"
}
```

## §20 · Collision Methodology

```json
{
  "sources": [
    "live 178",
    "117 candidates"
  ],
  "categories": [
    "EXACT_DUPLICATE",
    "NORMALIZED_DUPLICATE",
    "NEAR_DUPLICATE",
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
  "see": "array 'roster_draft' root of document"
}
```

## §22 · T1 Names

```json
{
  "count": 13,
  "names": [
    "Cappa neutro",
    "Veste del Rito",
    "Tunica del Marchio",
    "Guanti del Rito",
    "Cappuccio del Rito",
    "Gambali del Rito",
    "Pantaloni del Marchio",
    "Sigillo della Proiezione",
    "Sigillo del Riflesso",
    "Focus del Faro",
    "Amuleto neutro",
    "Anello neutro",
    "Mantellina del Rito"
  ]
}
```

## §23 · T2 Names

```json
{
  "count": 19,
  "names": [
    "Mantello semplice",
    "Veste della Caccia rituale",
    "Cotta della Canalizzazione",
    "Stivali tecnico del Rito",
    "Manopole del Marchio",
    "Corona del Marchio",
    "Copricapo della Canalizzazione",
    "Gambali tecnico della Caccia rituale",
    "Gambali tecnico del Rito",
    "Sigillo tecnico del Riflesso",
    "Focus rituale del Faro",
    "Focus rituale dell'Incisione",
    "Collare semplice",
    "Anello tecnico neutro",
    "Vera di scuola comune",
    "Spalliera del Marchio",
    "Cintura tecnico del Rito",
    "Braccialetto tecnico della Caccia rituale",
    "Braccialetto tecnico del Rito"
  ]
}
```

## §24 · T3 Names

```json
{
  "count": 25,
  "names": [
    "Reliquia del discepolo del Marchio",
    "Monile del cercatore del Frammento",
    "Sciarpa comune",
    "Casacca dell'Assenza",
    "Stivali della soglia della Caccia rituale",
    "Stivali della soglia del Rito",
    "Scarpe del discepolo del Marchio",
    "Guanti della Caccia rituale",
    "Bracciali della Canalizzazione",
    "Cappuccio della Caccia rituale",
    "Cerchietto dell'Assenza",
    "Pantaloni del discepolo del Marchio",
    "Lanterna del cercatore della Dissipazione mirata",
    "Lanterna del cercatore del Frammento",
    "Prisma del cacciatore della Risonanza",
    "Ciondolo comune",
    "Reliquiario della soglia del Riflesso",
    "Anello della soglia neutro",
    "Cerchio del discepolo semplice",
    "Mantellina della Caccia rituale",
    "Pauldrones della Canalizzazione",
    "Cintura della soglia della Caccia rituale",
    "Cintura della soglia del Rito",
    "Cintola del cercatore della Canalizzazione",
    "Braccialetto della soglia del Rito"
  ]
}
```

## §25 · T4 Names

```json
{
  "count": 26,
  "names": [
    "Talismano del maestro del Vuoto",
    "Monile del custode del Frammento",
    "Feticcio del veggente della Dissipazione",
    "Sudario del viaggiatore",
    "Tunica della Marcia",
    "Mantello del Riflesso",
    "Scarpe dell'adepto della Marcia",
    "Sandali del custode della Canalizzazione",
    "Bende dell'Assenza",
    "Corona della Marcia",
    "Diadema del Riflesso",
    "Pantaloni dell'adepto della Marcia",
    "Braghe del veggente dell'Assenza",
    "Lanterna del custode della Dissipazione mirata",
    "Prisma del veggente della Risonanza",
    "Balestra del maestro del Rito ravvicinato",
    "Pendaglio del viaggiatore",
    "Reliquiario del maestro della Proiezione",
    "Reliquiario del maestro del Riflesso",
    "Cerchio dell'adepto semplice",
    "Vera del custode comune",
    "Vera del custode del Frammento",
    "Spalliera della Marcia",
    "Sopravveste dell'Assenza",
    "Nastro del veggente dell'Assenza",
    "Bracciale dell'adepto della Marcia"
  ]
}
```

## §26 · T5 Names

```json
{
  "count": 25,
  "names": [
    "Talismano della firma del Vuoto",
    "Monile del canone del Frammento",
    "Feticcio della firma della Dissipazione",
    "Velo della via",
    "Drappo del mercato",
    "Cotta del Cammino",
    "Ghette della firma dell'Assenza",
    "Manopole dell'apice della Marcia",
    "Palme del Riflesso",
    "Aureola del Rito",
    "Cosciali del canone del Cammino",
    "Braghe della firma dell'Assenza",
    "Balestra dell'apice della Proiezione",
    "Medaglione della via",
    "Reliquia del mercato",
    "Cripta del canone della Dissipazione mirata",
    "Icona dell'apice dell'Incisione",
    "Cripta del canone dell'Attimo",
    "Cerchietto della firma della Dissipazione",
    "Sigillo dell'apice del Riflesso",
    "Cerchietto del canone del Drenaggio",
    "Sigillo della firma del Vuoto",
    "Manto del Rito",
    "Fascia dell'apice della Marcia",
    "Vinca del canone del Rito"
  ]
}
```

## §27 · Common Names

```json
{
  "count": 41,
  "names": [
    "Cappa neutro",
    "Veste del Rito",
    "Tunica del Marchio",
    "Guanti del Rito",
    "Cappuccio del Rito",
    "Amuleto neutro",
    "Mantellina del Rito",
    "Mantello semplice",
    "Veste della Caccia rituale",
    "Cotta della Canalizzazione",
    "Manopole del Marchio",
    "Corona del Marchio",
    "Copricapo della Canalizzazione",
    "Collare semplice",
    "Spalliera del Marchio",
    "Sciarpa comune",
    "Casacca dell'Assenza",
    "Guanti della Caccia rituale",
    "Bracciali della Canalizzazione",
    "Cappuccio della Caccia rituale",
    "Cerchietto dell'Assenza",
    "Ciondolo comune",
    "Mantellina della Caccia rituale",
    "Pauldrones della Canalizzazione",
    "Sudario del viaggiatore",
    "Tunica della Marcia",
    "Mantello del Riflesso",
    "Bende dell'Assenza",
    "Corona della Marcia",
    "Diadema del Riflesso",
    "Pendaglio del viaggiatore",
    "Spalliera della Marcia",
    "Sopravveste dell'Assenza",
    "Velo della via",
    "Drappo del mercato",
    "Cotta del Cammino",
    "Palme del Riflesso",
    "Aureola del Rito",
    "Medaglione della via",
    "Reliquia del mercato",
    "Manto del Rito"
  ]
}
```

## §28 · Uncommon Names

```json
{
  "count": 32,
  "names": [
    "Gambali del Rito",
    "Pantaloni del Marchio",
    "Sigillo del Riflesso",
    "Focus del Faro",
    "Stivali tecnico del Rito",
    "Gambali tecnico della Caccia rituale",
    "Gambali tecnico del Rito",
    "Sigillo tecnico del Riflesso",
    "Focus rituale del Faro",
    "Cintura tecnico del Rito",
    "Braccialetto tecnico della Caccia rituale",
    "Braccialetto tecnico del Rito",
    "Stivali della soglia della Caccia rituale",
    "Stivali della soglia del Rito",
    "Scarpe del discepolo del Marchio",
    "Pantaloni del discepolo del Marchio",
    "Cintura della soglia della Caccia rituale",
    "Cintura della soglia del Rito",
    "Cintola del cercatore della Canalizzazione",
    "Braccialetto della soglia del Rito",
    "Scarpe dell'adepto della Marcia",
    "Sandali del custode della Canalizzazione",
    "Pantaloni dell'adepto della Marcia",
    "Braghe del veggente dell'Assenza",
    "Prisma del veggente della Risonanza",
    "Nastro del veggente dell'Assenza",
    "Bracciale dell'adepto della Marcia",
    "Manopole dell'apice della Marcia",
    "Cosciali del canone del Cammino",
    "Braghe della firma dell'Assenza",
    "Fascia dell'apice della Marcia",
    "Vinca del canone del Rito"
  ]
}
```

## §29 · Rare Names

```json
{
  "count": 24,
  "names": [
    "Sigillo della Proiezione",
    "Anello neutro",
    "Focus rituale dell'Incisione",
    "Anello tecnico neutro",
    "Vera di scuola comune",
    "Lanterna del cercatore della Dissipazione mirata",
    "Lanterna del cercatore del Frammento",
    "Prisma del cacciatore della Risonanza",
    "Reliquiario della soglia del Riflesso",
    "Anello della soglia neutro",
    "Cerchio del discepolo semplice",
    "Lanterna del custode della Dissipazione mirata",
    "Balestra del maestro del Rito ravvicinato",
    "Reliquiario del maestro della Proiezione",
    "Reliquiario del maestro del Riflesso",
    "Cerchio dell'adepto semplice",
    "Vera del custode comune",
    "Vera del custode del Frammento",
    "Ghette della firma dell'Assenza",
    "Balestra dell'apice della Proiezione",
    "Cripta del canone della Dissipazione mirata",
    "Icona dell'apice dell'Incisione",
    "Cripta del canone dell'Attimo",
    "Cerchietto della firma della Dissipazione"
  ]
}
```

## §30 · Epic Names

```json
{
  "count": 11,
  "names": [
    "Reliquia del discepolo del Marchio",
    "Monile del cercatore del Frammento",
    "Talismano del maestro del Vuoto",
    "Monile del custode del Frammento",
    "Feticcio del veggente della Dissipazione",
    "Talismano della firma del Vuoto",
    "Monile del canone del Frammento",
    "Feticcio della firma della Dissipazione",
    "Sigillo dell'apice del Riflesso",
    "Cerchietto del canone del Drenaggio",
    "Sigillo della firma del Vuoto"
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
          "candidate_name": "Veste del Faro Rovesciato",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 1,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Manto della Canalizzazione totale",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 1
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Sudario di Onirade",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 1,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Manto della Canalizzazione totale",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_chest",
      "lore_text_it_draft": "Riservato al draft Phase 2 · testo Legendary breve pending PM adjudication.",
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
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 1,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Focus dell'Assenza Consumata",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 1,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Voce di Onirade",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 1,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Focus dell'Assenza Consumata",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_focus",
      "lore_text_it_draft": "Riservato al draft Phase 2 · testo Legendary breve pending PM adjudication.",
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
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 1,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "ritual_title",
          "candidate_name": "Balestra della Dissipazione ultima",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 1,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        },
        {
          "structure": "hybrid",
          "candidate_name": "Voce dei Bersagli assenti",
          "canonical_terms": {
            "Vuoto": 0,
            "Onirade": 0,
            "Marchio": 0,
            "Frammento": 0,
            "Faro Rovesciato": 0,
            "Drenaggio": 0,
            "Dissipazione": 0,
            "Riflesso": 0,
            "Assenza": 0,
            "Rituale": 0,
            "Canalizzazione": 0
          },
          "forbidden_terms_detected": [],
          "proper_noun_status": "LORE_PROPOSAL_PENDING_PM",
          "display_name_status": "DRAFT_PENDING_PM"
        }
      ],
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY",
      "agent_recommendation": "Balestra della Dissipazione ultima",
      "display_name_status": "DRAFT_PENDING_PM",
      "lore_status": "DRAFT_PENDING_PM",
      "lore_direction_it": "pillar_endgame_balestra",
      "lore_text_it_draft": "Riservato al draft Phase 2 · testo Legendary breve pending PM adjudication.",
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
    "Sigillo del Riflesso",
    "Focus del Faro",
    "Sigillo tecnico del Riflesso",
    "Focus rituale del Faro",
    "Lanterna del cercatore del Frammento",
    "Prisma del cacciatore della Risonanza",
    "Reliquiario della soglia del Riflesso",
    "Prisma del veggente della Risonanza",
    "Reliquiario del maestro del Riflesso"
  ]
}
```

## §33 · Balestra Naming

```json
{
  "count": 6,
  "names": [
    "Sigillo della Proiezione",
    "Lanterna del cercatore della Dissipazione mirata",
    "Lanterna del custode della Dissipazione mirata",
    "Reliquiario del maestro della Proiezione",
    "Balestra dell'apice della Proiezione",
    "Cripta del canone della Dissipazione mirata"
  ]
}
```

## §34 · Pugnale Naming

```json
{
  "count": 4,
  "names": [
    "Focus rituale dell'Incisione",
    "Balestra del maestro del Rito ravvicinato",
    "Icona dell'apice dell'Incisione",
    "Cripta del canone dell'Attimo"
  ]
}
```

## §35 · Stoffa Naming

```json
{
  "count": 39,
  "names": [
    "Veste del Rito",
    "Tunica del Marchio",
    "Guanti del Rito",
    "Cappuccio del Rito",
    "Gambali del Rito",
    "Pantaloni del Marchio",
    "Mantellina del Rito",
    "Cotta della Canalizzazione",
    "Stivali tecnico del Rito",
    "Manopole del Marchio",
    "Corona del Marchio",
    "Copricapo della Canalizzazione",
    "Gambali tecnico del Rito",
    "Spalliera del Marchio",
    "Cintura tecnico del Rito",
    "Braccialetto tecnico del Rito",
    "Casacca dell'Assenza",
    "Stivali della soglia del Rito",
    "Scarpe del discepolo del Marchio",
    "Bracciali della Canalizzazione",
    "Cerchietto dell'Assenza",
    "Pantaloni del discepolo del Marchio",
    "Pauldrones della Canalizzazione",
    "Cintura della soglia del Rito",
    "Cintola del cercatore della Canalizzazione",
    "Braccialetto della soglia del Rito",
    "Mantello del Riflesso",
    "Sandali del custode della Canalizzazione",
    "Bende dell'Assenza",
    "Diadema del Riflesso",
    "Braghe del veggente dell'Assenza",
    "Sopravveste dell'Assenza",
    "Nastro del veggente dell'Assenza",
    "Ghette della firma dell'Assenza",
    "Palme del Riflesso",
    "Aureola del Rito",
    "Braghe della firma dell'Assenza",
    "Manto del Rito",
    "Vinca del canone del Rito"
  ]
}
```

## §36 · Cuoio Naming

```json
{
  "count": 18,
  "names": [
    "Veste della Caccia rituale",
    "Gambali tecnico della Caccia rituale",
    "Braccialetto tecnico della Caccia rituale",
    "Stivali della soglia della Caccia rituale",
    "Guanti della Caccia rituale",
    "Cappuccio della Caccia rituale",
    "Mantellina della Caccia rituale",
    "Cintura della soglia della Caccia rituale",
    "Tunica della Marcia",
    "Scarpe dell'adepto della Marcia",
    "Corona della Marcia",
    "Pantaloni dell'adepto della Marcia",
    "Spalliera della Marcia",
    "Bracciale dell'adepto della Marcia",
    "Cotta del Cammino",
    "Manopole dell'apice della Marcia",
    "Cosciali del canone del Cammino",
    "Fascia dell'apice della Marcia"
  ]
}
```

## §37 · Universal Naming

```json
{
  "count": 32,
  "names": [
    "Cappa neutro",
    "Amuleto neutro",
    "Anello neutro",
    "Mantello semplice",
    "Collare semplice",
    "Anello tecnico neutro",
    "Vera di scuola comune",
    "Reliquia del discepolo del Marchio",
    "Monile del cercatore del Frammento",
    "Sciarpa comune",
    "Ciondolo comune",
    "Anello della soglia neutro",
    "Cerchio del discepolo semplice",
    "Talismano del maestro del Vuoto",
    "Monile del custode del Frammento",
    "Feticcio del veggente della Dissipazione",
    "Sudario del viaggiatore",
    "Pendaglio del viaggiatore",
    "Cerchio dell'adepto semplice",
    "Vera del custode comune",
    "Vera del custode del Frammento",
    "Talismano della firma del Vuoto",
    "Monile del canone del Frammento",
    "Feticcio della firma della Dissipazione",
    "Velo della via",
    "Drappo del mercato",
    "Medaglione della via",
    "Reliquia del mercato",
    "Cerchietto della firma della Dissipazione",
    "Sigillo dell'apice del Riflesso",
    "Cerchietto del canone del Drenaggio",
    "Sigillo della firma del Vuoto"
  ]
}
```

## §38 · Class Specific Naming

```json
{
  "count": 61,
  "names": [
    "Guanti del Rito",
    "Gambali del Rito",
    "Pantaloni del Marchio",
    "Sigillo della Proiezione",
    "Sigillo del Riflesso",
    "Focus del Faro",
    "Stivali tecnico del Rito",
    "Manopole del Marchio",
    "Gambali tecnico della Caccia rituale",
    "Gambali tecnico del Rito",
    "Sigillo tecnico del Riflesso",
    "Focus rituale del Faro",
    "Focus rituale dell'Incisione",
    "Cintura tecnico del Rito",
    "Braccialetto tecnico della Caccia rituale",
    "Braccialetto tecnico del Rito",
    "Reliquia del discepolo del Marchio",
    "Monile del cercatore del Frammento",
    "Stivali della soglia della Caccia rituale",
    "Stivali della soglia del Rito",
    "Scarpe del discepolo del Marchio",
    "Pantaloni del discepolo del Marchio",
    "Lanterna del cercatore della Dissipazione mirata",
    "Lanterna del cercatore del Frammento",
    "Prisma del cacciatore della Risonanza",
    "Reliquiario della soglia del Riflesso",
    "Cintura della soglia della Caccia rituale",
    "Cintura della soglia del Rito",
    "Cintola del cercatore della Canalizzazione",
    "Braccialetto della soglia del Rito",
    "Talismano del maestro del Vuoto",
    "Monile del custode del Frammento",
    "Feticcio del veggente della Dissipazione",
    "Scarpe dell'adepto della Marcia",
    "Sandali del custode della Canalizzazione",
    "Bende dell'Assenza",
    "Pantaloni dell'adepto della Marcia",
    "Braghe del veggente dell'Assenza",
    "Lanterna del custode della Dissipazione mirata",
    "Prisma del veggente della Risonanza",
    "Balestra del maestro del Rito ravvicinato",
    "Reliquiario del maestro della Proiezione",
    "Reliquiario del maestro del Riflesso",
    "Vera del custode del Frammento",
    "Nastro del veggente dell'Assenza",
    "Bracciale dell'adepto della Marcia",
    "Talismano della firma del Vuoto",
    "Monile del canone del Frammento",
    "Feticcio della firma della Dissipazione",
    "Ghette della firma dell'Assenza",
    "Cosciali del canone del Cammino",
    "Braghe della firma dell'Assenza",
    "Balestra dell'apice della Proiezione",
    "Cripta del canone della Dissipazione mirata",
    "Icona dell'apice dell'Incisione",
    "Cripta del canone dell'Attimo",
    "Cerchietto della firma della Dissipazione",
    "Sigillo dell'apice del Riflesso",
    "Cerchietto del canone del Drenaggio",
    "Sigillo della firma del Vuoto",
    "Fascia dell'apice della Marcia"
  ]
}
```

## §39 · Shared Family Naming

```json
{
  "count": 28,
  "names": [
    "Veste del Rito",
    "Tunica del Marchio",
    "Cappuccio del Rito",
    "Mantellina del Rito",
    "Veste della Caccia rituale",
    "Cotta della Canalizzazione",
    "Corona del Marchio",
    "Copricapo della Canalizzazione",
    "Spalliera del Marchio",
    "Casacca dell'Assenza",
    "Guanti della Caccia rituale",
    "Bracciali della Canalizzazione",
    "Cappuccio della Caccia rituale",
    "Cerchietto dell'Assenza",
    "Mantellina della Caccia rituale",
    "Pauldrones della Canalizzazione",
    "Tunica della Marcia",
    "Mantello del Riflesso",
    "Corona della Marcia",
    "Diadema del Riflesso",
    "Spalliera della Marcia",
    "Sopravveste dell'Assenza",
    "Cotta del Cammino",
    "Manopole dell'apice della Marcia",
    "Palme del Riflesso",
    "Aureola del Rito",
    "Manto del Rito",
    "Vinca del canone del Rito"
  ]
}
```

## §40 · Universal Neutral Naming

```json
{
  "count": 19,
  "names": [
    "Cappa neutro",
    "Amuleto neutro",
    "Anello neutro",
    "Mantello semplice",
    "Collare semplice",
    "Anello tecnico neutro",
    "Vera di scuola comune",
    "Sciarpa comune",
    "Ciondolo comune",
    "Anello della soglia neutro",
    "Cerchio del discepolo semplice",
    "Sudario del viaggiatore",
    "Pendaglio del viaggiatore",
    "Cerchio dell'adepto semplice",
    "Vera del custode comune",
    "Velo della via",
    "Drappo del mercato",
    "Medaglione della via",
    "Reliquia del mercato"
  ]
}
```

## §41 · Lore Draft Roster

```json
{
  "total_lore_drafts": 111,
  "format": "1-2 frasi ≤45 parole",
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
  "Vuoto": 3,
  "Onirade": 0,
  "Marchio": 8,
  "Frammento": 5,
  "Faro Rovesciato": 0,
  "Drenaggio": 1,
  "Dissipazione": 6,
  "Riflesso": 8,
  "Assenza": 8,
  "Rituale": 10,
  "Canalizzazione": 6
}
```

## §44 · Restricted Term Usage Ledger

```json
{
  "Onirade": 0,
  "Onirade_cap": 4,
  "Faro Rovesciato": 0,
  "Faro_Rovesciato_cap": 2,
  "class_specific_only": true,
  "PM_review": true
}
```

## §45 · Forbidden Term Validation

```json
{
  "violations_count": 0,
  "forbidden_list": [
    "Sacro",
    "Luce",
    "Ossa",
    "Bestia",
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
    "Cappa": 1,
    "Veste": 2,
    "Tunica": 2,
    "Guanti": 2,
    "Cappuccio": 2,
    "Gambali": 3,
    "Pantaloni": 3,
    "Sigillo": 5,
    "Focus": 3,
    "Amuleto": 1,
    "Anello": 3,
    "Mantellina": 2,
    "Mantello": 2,
    "Cotta": 2,
    "Stivali": 3,
    "Manopole": 2,
    "Corona": 2,
    "Copricapo": 1,
    "Collare": 1,
    "Vera": 3,
    "Spalliera": 2,
    "Cintura": 3,
    "Braccialetto": 3,
    "Reliquia": 2,
    "Monile": 3,
    "Sciarpa": 1,
    "Casacca": 1,
    "Scarpe": 2,
    "Bracciali": 1,
    "Cerchietto": 3,
    "Lanterna": 3,
    "Prisma": 2,
    "Ciondolo": 1,
    "Reliquiario": 3,
    "Cerchio": 2,
    "Pauldrones": 1,
    "Cintola": 1,
    "Talismano": 2,
    "Feticcio": 2,
    "Sudario": 1,
    "Sandali": 1,
    "Bende": 1,
    "Diadema": 1,
    "Braghe": 2,
    "Balestra": 2,
    "Pendaglio": 1,
    "Sopravveste": 1,
    "Nastro": 1,
    "Bracciale": 1,
    "Velo": 1,
    "Drappo": 1,
    "Ghette": 1,
    "Palme": 1,
    "Aureola": 1,
    "Cosciali": 1,
    "Medaglione": 1,
    "Cripta": 2,
    "Icona": 1,
    "Manto": 1,
    "Fascia": 1,
    "Vinca": 1
  },
  "max_global": 5,
  "cap_global": 8,
  "all_within_cap": true
}
```

## §47 · Phrase Repetition Ledger

```json
{
  "phrase_violations": {
    "del rito": 16,
    "del marchio": 8,
    "della proiezione": 3,
    "del riflesso": 8,
    "del faro": 4,
    "della caccia": 8,
    "della caccia rituale": 8,
    "caccia rituale": 8,
    "della canalizzazione": 7,
    "tecnico del": 5,
    "tecnico del rito": 4,
    "del discepolo": 4,
    "del discepolo del": 3,
    "del discepolo del marchio": 3,
    "discepolo del": 3,
    "discepolo del marchio": 3,
    "monile del": 3,
    "del cercatore": 4,
    "del frammento": 5,
    "della soglia": 7,
    "della soglia del": 4,
    "della soglia del rito": 3,
    "soglia del": 4,
    "soglia del rito": 3,
    "lanterna del": 3,
    "della dissipazione": 7,
    "della dissipazione mirata": 3,
    "dissipazione mirata": 3,
    "del maestro": 4,
    "del maestro del": 3,
    "maestro del": 3,
    "del vuoto": 3,
    "del custode": 5,
    "del veggente": 4,
    "della marcia": 8,
    "dell'adepto della": 3,
    "dell'adepto della marcia": 3,
    "della firma": 6,
    "del canone": 6,
    "del canone del": 4,
    "canone del": 4,
    "dell'apice della": 3
  },
  "threshold": "≤2 occurrences for ≥2-word normalized phrases"
}
```

## §48 · Naming Pattern Usage Ledger

```json
{
  "counts": {
    "NP_T1_back_universal_position": 1,
    "NP_T1_chest_stoffa": 2,
    "NP_T1_hands_stoffa": 1,
    "NP_T1_head_stoffa": 1,
    "NP_T1_legs_stoffa": 2,
    "NP_T1_main_hand_balestra": 1,
    "NP_T1_main_hand_focus": 2,
    "NP_T1_neck_universal_position": 1,
    "NP_T1_ring_universal_position": 1,
    "NP_T1_shoulders_stoffa": 1,
    "NP_T2_back_universal_position": 1,
    "NP_T2_chest_cuoio": 1,
    "NP_T2_chest_stoffa": 1,
    "NP_T2_feet_stoffa": 1,
    "NP_T2_hands_stoffa": 1,
    "NP_T2_head_stoffa": 2,
    "NP_T2_legs_cuoio": 1,
    "NP_T2_legs_stoffa": 1,
    "NP_T2_main_hand_focus": 2,
    "NP_T2_main_hand_pugnale": 1,
    "NP_T2_neck_universal_position": 1,
    "NP_T2_ring_universal_position": 2,
    "NP_T2_shoulders_stoffa": 1,
    "NP_T2_waist_stoffa": 1,
    "NP_T2_wrist_cuoio": 1,
    "NP_T2_wrist_stoffa": 1,
    "NP_T3_accessory_universal_position": 2,
    "NP_T3_back_universal_position": 1,
    "NP_T3_chest_stoffa": 1,
    "NP_T3_feet_cuoio": 1,
    "NP_T3_feet_stoffa": 2,
    "NP_T3_hands_cuoio": 1,
    "NP_T3_hands_stoffa": 1,
    "NP_T3_head_cuoio": 1,
    "NP_T3_head_stoffa": 1,
    "NP_T3_legs_stoffa": 1,
    "NP_T3_main_hand_balestra": 1,
    "NP_T3_main_hand_focus": 2,
    "NP_T3_neck_universal_position": 1,
    "NP_T3_off_hand_focus": 1,
    "NP_T3_ring_universal_position": 2,
    "NP_T3_shoulders_cuoio": 1,
    "NP_T3_shoulders_stoffa": 1,
    "NP_T3_waist_cuoio": 1,
    "NP_T3_waist_stoffa": 2,
    "NP_T3_wrist_stoffa": 1,
    "NP_T4_accessory_universal_position": 3,
    "NP_T4_back_universal_position": 1,
    "NP_T4_chest_cuoio": 1,
    "NP_T4_chest_stoffa": 1,
    "NP_T4_feet_cuoio": 1,
    "NP_T4_feet_stoffa": 1,
    "NP_T4_hands_stoffa": 1,
    "NP_T4_head_cuoio": 1,
    "NP_T4_head_stoffa": 1,
    "NP_T4_legs_cuoio": 1,
    "NP_T4_legs_stoffa": 1,
    "NP_T4_main_hand_balestra": 1,
    "NP_T4_main_hand_focus": 1,
    "NP_T4_main_hand_pugnale": 1,
    "NP_T4_neck_universal_position": 1,
    "NP_T4_off_hand_balestra": 1,
    "NP_T4_off_hand_focus": 1,
    "NP_T4_ring_universal_position": 3,
    "NP_T4_shoulders_cuoio": 1,
    "NP_T4_shoulders_stoffa": 1,
    "NP_T4_waist_stoffa": 1,
    "NP_T4_wrist_cuoio": 1,
    "NP_T5_accessory_universal_position": 3,
    "NP_T5_back_universal_position": 2,
    "NP_T5_chest_cuoio": 1,
    "NP_T5_feet_stoffa": 1,
    "NP_T5_hands_cuoio": 1,
    "NP_T5_hands_stoffa": 1,
    "NP_T5_head_stoffa": 1,
    "NP_T5_legs_cuoio": 1,
    "NP_T5_legs_stoffa": 1,
    "NP_T5_main_hand_balestra": 1,
    "NP_T5_neck_universal_position": 2,
    "NP_T5_off_hand_balestra": 1,
    "NP_T5_off_hand_pugnale": 2,
    "NP_T5_ring_universal_position": 4,
    "NP_T5_shoulders_stoffa": 1,
    "NP_T5_waist_cuoio": 1,
    "NP_T5_wrist_stoffa": 1
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
  "near_duplicates": [],
  "note": "none automatically flagged in this deterministic draft"
}
```

## §52 · Lore Collision Audit

```json
{
  "canonical_places_referenced": [
    "Faro Rovesciato di Onirade (lore/name restricted)"
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
        "Veste del Faro Rovesciato",
        "Manto della Canalizzazione totale",
        "Sudario di Onirade"
      ],
      "agent_recommendation": "Manto della Canalizzazione totale",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_focus_001",
      "candidates": [
        "Occhio del Faro Rovesciato",
        "Focus dell'Assenza Consumata",
        "Voce di Onirade"
      ],
      "agent_recommendation": "Focus dell'Assenza Consumata",
      "preferred_candidate": "AGENT_RECOMMENDATION_ONLY"
    },
    {
      "blueprint_code": "cdv_t5_main_hand_balestra_001",
      "candidates": [
        "Lancia dei Frammenti",
        "Balestra della Dissipazione ultima",
        "Voce dei Bersagli assenti"
      ],
      "agent_recommendation": "Balestra della Dissipazione ultima",
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
  "forbidden_vocabulary_violation": 0,
  "mechanic_promise_violation": 0,
  "stat_promise_violation": 0,
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
      "mitigation": "policy defined · optional in Phase 2"
    },
    {
      "id": "R3",
      "name": "Legendary preferred non selezionato",
      "severity": "LOW",
      "mitigation": "AGENT_RECOMMENDATION_ONLY · PM adjudica"
    },
    {
      "id": "R4",
      "name": "Head noun ripetuti per volume alto NF (111 unit)",
      "severity": "MEDIUM",
      "mitigation": "head_noun cap 8 global/3 slot"
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
      "verbatim": "Confermare l'algoritmo deterministico [head_noun + tier_mod + family_qualifier] o richiedere pool più ampio in Phase 2 Rev-1?",
      "agent_recommendation": "Espandere pool head_noun/qualifier in Rev-1 per maggiore varietà",
      "impact": "MEDIUM",
      "default_proposal": "expand_in_rev_1",
      "blocking": false
    },
    {
      "question_id": "P2Q2",
      "verbatim": "Le famiglie coese (cohesive_naming_families) devono essere generate in Phase 2 Rev-1 o restare in draft solo tramite naming_family_id?",
      "agent_recommendation": "Introdurre in Rev-1 con esempio narrativo",
      "impact": "LOW",
      "default_proposal": "introduce_rev_1",
      "blocking": false
    },
    {
      "question_id": "P2Q3",
      "verbatim": "Per Legendary preferred_candidate = AGENT_RECOMMENDATION_ONLY(ritual_title) accettabile o PM richiede short-list separata?",
      "agent_recommendation": "Accettare come default · PM sceglierà",
      "impact": "MEDIUM",
      "default_proposal": "accept_as_default",
      "blocking": true
    },
    {
      "question_id": "P2Q4",
      "verbatim": "Il lore draft di 1-2 frasi ≤45 parole è sufficiente o serve expansion per Rare/Epic in Rev-1?",
      "agent_recommendation": "Espandere Rare/Epic in Rev-1 · Common/Uncommon restano brevi",
      "impact": "MEDIUM",
      "default_proposal": "expand_rare_epic_rev_1",
      "blocking": false
    },
    {
      "question_id": "P2Q5",
      "verbatim": "Vietare occorrenze di 'Frammenti' in nomi non-Legendary per riservarli come climax narrativo?",
      "agent_recommendation": "NON vietare · resta entro cap 8 · monitor Phase 3",
      "impact": "LOW",
      "default_proposal": "keep_within_cap",
      "blocking": false
    }
  ]
}
```

## §65 · Go Hold Recommendation

```json
{
  "phase_2_recommendation": "HOLD (attendo PM review su draft roster)",
  "phase_2_closure": "HOLD",
  "next_action": "await_PM_review_of_draft"
}
```

## Roster Draft · 108 Non-Legendary

| # | blueprint_code | tier | slot | rarity | ic | family | display_name_it_draft | head_noun |
|---|---|---|---|---|---|---|---|---|
| 1 | `cdv_t1_back_universal_position_001` | T1 | back | Common | universal_neutral | universal_position | **Cappa neutro** | Cappa |
| 2 | `cdv_t1_chest_stoffa_001` | T1 | chest | Common | shared_family | stoffa | **Veste del Rito** | Veste |
| 3 | `cdv_t1_chest_stoffa_002` | T1 | chest | Common | shared_family | stoffa | **Tunica del Marchio** | Tunica |
| 4 | `cdv_t1_hands_stoffa_001` | T1 | hands | Common | class_specific | stoffa | **Guanti del Rito** | Guanti |
| 5 | `cdv_t1_head_stoffa_001` | T1 | head | Common | shared_family | stoffa | **Cappuccio del Rito** | Cappuccio |
| 6 | `cdv_t1_legs_stoffa_001` | T1 | legs | Uncommon | class_specific | stoffa | **Gambali del Rito** | Gambali |
| 7 | `cdv_t1_legs_stoffa_002` | T1 | legs | Uncommon | class_specific | stoffa | **Pantaloni del Marchio** | Pantaloni |
| 8 | `cdv_t1_main_hand_balestra_001` | T1 | main_hand | Rare | class_specific | balestra | **Sigillo della Proiezione** | Sigillo |
| 9 | `cdv_t1_main_hand_focus_001` | T1 | main_hand | Uncommon | class_specific | focus | **Sigillo del Riflesso** | Sigillo |
| 10 | `cdv_t1_main_hand_focus_002` | T1 | main_hand | Uncommon | class_specific | focus | **Focus del Faro** | Focus |
| 11 | `cdv_t1_neck_universal_position_001` | T1 | neck | Common | universal_neutral | universal_position | **Amuleto neutro** | Amuleto |
| 12 | `cdv_t1_ring_universal_position_001` | T1 | ring | Rare | universal_neutral | universal_position | **Anello neutro** | Anello |
| 13 | `cdv_t1_shoulders_stoffa_001` | T1 | shoulders | Common | shared_family | stoffa | **Mantellina del Rito** | Mantellina |
| 14 | `cdv_t2_back_universal_position_001` | T2 | back | Common | universal_neutral | universal_position | **Mantello semplice** | Mantello |
| 15 | `cdv_t2_chest_cuoio_001` | T2 | chest | Common | shared_family | cuoio | **Veste della Caccia rituale** | Veste |
| 16 | `cdv_t2_chest_stoffa_001` | T2 | chest | Common | shared_family | stoffa | **Cotta della Canalizzazione** | Cotta |
| 17 | `cdv_t2_feet_stoffa_001` | T2 | feet | Uncommon | class_specific | stoffa | **Stivali tecnico del Rito** | Stivali |
| 18 | `cdv_t2_hands_stoffa_001` | T2 | hands | Common | class_specific | stoffa | **Manopole del Marchio** | Manopole |
| 19 | `cdv_t2_head_stoffa_001` | T2 | head | Common | shared_family | stoffa | **Corona del Marchio** | Corona |
| 20 | `cdv_t2_head_stoffa_002` | T2 | head | Common | shared_family | stoffa | **Copricapo della Canalizzazione** | Copricapo |
| 21 | `cdv_t2_legs_cuoio_001` | T2 | legs | Uncommon | class_specific | cuoio | **Gambali tecnico della Caccia rituale** | Gambali |
| 22 | `cdv_t2_legs_stoffa_001` | T2 | legs | Uncommon | class_specific | stoffa | **Gambali tecnico del Rito** | Gambali |
| 23 | `cdv_t2_main_hand_focus_001` | T2 | main_hand | Uncommon | class_specific | focus | **Sigillo tecnico del Riflesso** | Sigillo |
| 24 | `cdv_t2_main_hand_focus_002` | T2 | main_hand | Uncommon | class_specific | focus | **Focus rituale del Faro** | Focus |
| 25 | `cdv_t2_main_hand_pugnale_001` | T2 | main_hand | Rare | class_specific | pugnale | **Focus rituale dell'Incisione** | Focus |
| 26 | `cdv_t2_neck_universal_position_001` | T2 | neck | Common | universal_neutral | universal_position | **Collare semplice** | Collare |
| 27 | `cdv_t2_ring_universal_position_001` | T2 | ring | Rare | universal_neutral | universal_position | **Anello tecnico neutro** | Anello |
| 28 | `cdv_t2_ring_universal_position_002` | T2 | ring | Rare | universal_neutral | universal_position | **Vera di scuola comune** | Vera |
| 29 | `cdv_t2_shoulders_stoffa_001` | T2 | shoulders | Common | shared_family | stoffa | **Spalliera del Marchio** | Spalliera |
| 30 | `cdv_t2_waist_stoffa_001` | T2 | waist | Uncommon | class_specific | stoffa | **Cintura tecnico del Rito** | Cintura |
| 31 | `cdv_t2_wrist_cuoio_001` | T2 | wrist | Uncommon | class_specific | cuoio | **Braccialetto tecnico della Caccia rituale** | Braccialetto |
| 32 | `cdv_t2_wrist_stoffa_001` | T2 | wrist | Uncommon | class_specific | stoffa | **Braccialetto tecnico del Rito** | Braccialetto |
| 33 | `cdv_t3_accessory_universal_position_002` | T3 | accessory | Epic | class_specific | universal_position | **Reliquia del discepolo del Marchio** | Reliquia |
| 34 | `cdv_t3_accessory_universal_position_003` | T3 | accessory | Epic | class_specific | universal_position | **Monile del cercatore del Frammento** | Monile |
| 35 | `cdv_t3_back_universal_position_001` | T3 | back | Common | universal_neutral | universal_position | **Sciarpa comune** | Sciarpa |
| 36 | `cdv_t3_chest_stoffa_001` | T3 | chest | Common | shared_family | stoffa | **Casacca dell'Assenza** | Casacca |
| 37 | `cdv_t3_feet_cuoio_001` | T3 | feet | Uncommon | class_specific | cuoio | **Stivali della soglia della Caccia rituale** | Stivali |
| 38 | `cdv_t3_feet_stoffa_001` | T3 | feet | Uncommon | class_specific | stoffa | **Stivali della soglia del Rito** | Stivali |
| 39 | `cdv_t3_feet_stoffa_002` | T3 | feet | Uncommon | class_specific | stoffa | **Scarpe del discepolo del Marchio** | Scarpe |
| 40 | `cdv_t3_hands_cuoio_001` | T3 | hands | Common | shared_family | cuoio | **Guanti della Caccia rituale** | Guanti |
| 41 | `cdv_t3_hands_stoffa_001` | T3 | hands | Common | shared_family | stoffa | **Bracciali della Canalizzazione** | Bracciali |
| 42 | `cdv_t3_head_cuoio_001` | T3 | head | Common | shared_family | cuoio | **Cappuccio della Caccia rituale** | Cappuccio |
| 43 | `cdv_t3_head_stoffa_001` | T3 | head | Common | shared_family | stoffa | **Cerchietto dell'Assenza** | Cerchietto |
| 44 | `cdv_t3_legs_stoffa_001` | T3 | legs | Uncommon | class_specific | stoffa | **Pantaloni del discepolo del Marchio** | Pantaloni |
| 45 | `cdv_t3_main_hand_balestra_001` | T3 | main_hand | Rare | class_specific | balestra | **Lanterna del cercatore della Dissipazione mirata** | Lanterna |
| 46 | `cdv_t3_main_hand_focus_001` | T3 | main_hand | Rare | class_specific | focus | **Lanterna del cercatore del Frammento** | Lanterna |
| 47 | `cdv_t3_main_hand_focus_002` | T3 | main_hand | Rare | class_specific | focus | **Prisma del cacciatore della Risonanza** | Prisma |
| 48 | `cdv_t3_neck_universal_position_001` | T3 | neck | Common | universal_neutral | universal_position | **Ciondolo comune** | Ciondolo |
| 49 | `cdv_t3_off_hand_focus_001` | T3 | off_hand | Rare | class_specific | focus | **Reliquiario della soglia del Riflesso** | Reliquiario |
| 50 | `cdv_t3_ring_universal_position_001` | T3 | ring | Rare | universal_neutral | universal_position | **Anello della soglia neutro** | Anello |
| 51 | `cdv_t3_ring_universal_position_002` | T3 | ring | Rare | universal_neutral | universal_position | **Cerchio del discepolo semplice** | Cerchio |
| 52 | `cdv_t3_shoulders_cuoio_001` | T3 | shoulders | Common | shared_family | cuoio | **Mantellina della Caccia rituale** | Mantellina |
| 53 | `cdv_t3_shoulders_stoffa_001` | T3 | shoulders | Common | shared_family | stoffa | **Pauldrones della Canalizzazione** | Pauldrones |
| 54 | `cdv_t3_waist_cuoio_001` | T3 | waist | Uncommon | class_specific | cuoio | **Cintura della soglia della Caccia rituale** | Cintura |
| 55 | `cdv_t3_waist_stoffa_001` | T3 | waist | Uncommon | class_specific | stoffa | **Cintura della soglia del Rito** | Cintura |
| 56 | `cdv_t3_waist_stoffa_002` | T3 | waist | Uncommon | class_specific | stoffa | **Cintola del cercatore della Canalizzazione** | Cintola |
| 57 | `cdv_t3_wrist_stoffa_001` | T3 | wrist | Uncommon | class_specific | stoffa | **Braccialetto della soglia del Rito** | Braccialetto |
| 58 | `cdv_t4_accessory_universal_position_001` | T4 | accessory | Epic | class_specific | universal_position | **Talismano del maestro del Vuoto** | Talismano |
| 59 | `cdv_t4_accessory_universal_position_002` | T4 | accessory | Epic | class_specific | universal_position | **Monile del custode del Frammento** | Monile |
| 60 | `cdv_t4_accessory_universal_position_003` | T4 | accessory | Epic | class_specific | universal_position | **Feticcio del veggente della Dissipazione** | Feticcio |
| 61 | `cdv_t4_back_universal_position_001` | T4 | back | Common | universal_neutral | universal_position | **Sudario del viaggiatore** | Sudario |
| 62 | `cdv_t4_chest_cuoio_001` | T4 | chest | Common | shared_family | cuoio | **Tunica della Marcia** | Tunica |
| 63 | `cdv_t4_chest_stoffa_001` | T4 | chest | Common | shared_family | stoffa | **Mantello del Riflesso** | Mantello |
| 64 | `cdv_t4_feet_cuoio_001` | T4 | feet | Uncommon | class_specific | cuoio | **Scarpe dell'adepto della Marcia** | Scarpe |
| 65 | `cdv_t4_feet_stoffa_001` | T4 | feet | Uncommon | class_specific | stoffa | **Sandali del custode della Canalizzazione** | Sandali |
| 66 | `cdv_t4_hands_stoffa_001` | T4 | hands | Common | class_specific | stoffa | **Bende dell'Assenza** | Bende |
| 67 | `cdv_t4_head_cuoio_001` | T4 | head | Common | shared_family | cuoio | **Corona della Marcia** | Corona |
| 68 | `cdv_t4_head_stoffa_001` | T4 | head | Common | shared_family | stoffa | **Diadema del Riflesso** | Diadema |
| 69 | `cdv_t4_legs_cuoio_001` | T4 | legs | Uncommon | class_specific | cuoio | **Pantaloni dell'adepto della Marcia** | Pantaloni |
| 70 | `cdv_t4_legs_stoffa_001` | T4 | legs | Uncommon | class_specific | stoffa | **Braghe del veggente dell'Assenza** | Braghe |
| 71 | `cdv_t4_main_hand_balestra_001` | T4 | main_hand | Rare | class_specific | balestra | **Lanterna del custode della Dissipazione mirata** | Lanterna |
| 72 | `cdv_t4_main_hand_focus_001` | T4 | main_hand | Uncommon | class_specific | focus | **Prisma del veggente della Risonanza** | Prisma |
| 73 | `cdv_t4_main_hand_pugnale_001` | T4 | main_hand | Rare | class_specific | pugnale | **Balestra del maestro del Rito ravvicinato** | Balestra |
| 74 | `cdv_t4_neck_universal_position_001` | T4 | neck | Common | universal_neutral | universal_position | **Pendaglio del viaggiatore** | Pendaglio |
| 75 | `cdv_t4_off_hand_balestra_001` | T4 | off_hand | Rare | class_specific | balestra | **Reliquiario del maestro della Proiezione** | Reliquiario |
| 76 | `cdv_t4_off_hand_focus_001` | T4 | off_hand | Rare | class_specific | focus | **Reliquiario del maestro del Riflesso** | Reliquiario |
| 77 | `cdv_t4_ring_universal_position_001` | T4 | ring | Rare | universal_neutral | universal_position | **Cerchio dell'adepto semplice** | Cerchio |
| 78 | `cdv_t4_ring_universal_position_002` | T4 | ring | Rare | universal_neutral | universal_position | **Vera del custode comune** | Vera |
| 79 | `cdv_t4_ring_universal_position_003` | T4 | ring | Rare | class_specific | universal_position | **Vera del custode del Frammento** | Vera |
| 80 | `cdv_t4_shoulders_cuoio_001` | T4 | shoulders | Common | shared_family | cuoio | **Spalliera della Marcia** | Spalliera |
| 81 | `cdv_t4_shoulders_stoffa_001` | T4 | shoulders | Common | shared_family | stoffa | **Sopravveste dell'Assenza** | Sopravveste |
| 82 | `cdv_t4_waist_stoffa_001` | T4 | waist | Uncommon | class_specific | stoffa | **Nastro del veggente dell'Assenza** | Nastro |
| 83 | `cdv_t4_wrist_cuoio_001` | T4 | wrist | Uncommon | class_specific | cuoio | **Bracciale dell'adepto della Marcia** | Bracciale |
| 84 | `cdv_t5_accessory_universal_position_001` | T5 | accessory | Epic | class_specific | universal_position | **Talismano della firma del Vuoto** | Talismano |
| 85 | `cdv_t5_accessory_universal_position_002` | T5 | accessory | Epic | class_specific | universal_position | **Monile del canone del Frammento** | Monile |
| 86 | `cdv_t5_accessory_universal_position_003` | T5 | accessory | Epic | class_specific | universal_position | **Feticcio della firma della Dissipazione** | Feticcio |
| 87 | `cdv_t5_back_universal_position_001` | T5 | back | Common | universal_neutral | universal_position | **Velo della via** | Velo |
| 88 | `cdv_t5_back_universal_position_002` | T5 | back | Common | universal_neutral | universal_position | **Drappo del mercato** | Drappo |
| 89 | `cdv_t5_chest_cuoio_001` | T5 | chest | Common | shared_family | cuoio | **Cotta del Cammino** | Cotta |
| 90 | `cdv_t5_feet_stoffa_001` | T5 | feet | Rare | class_specific | stoffa | **Ghette della firma dell'Assenza** | Ghette |
| 91 | `cdv_t5_hands_cuoio_001` | T5 | hands | Uncommon | shared_family | cuoio | **Manopole dell'apice della Marcia** | Manopole |
| 92 | `cdv_t5_hands_stoffa_001` | T5 | hands | Common | shared_family | stoffa | **Palme del Riflesso** | Palme |
| 93 | `cdv_t5_head_stoffa_001` | T5 | head | Common | shared_family | stoffa | **Aureola del Rito** | Aureola |
| 94 | `cdv_t5_legs_cuoio_001` | T5 | legs | Uncommon | class_specific | cuoio | **Cosciali del canone del Cammino** | Cosciali |
| 95 | `cdv_t5_legs_stoffa_001` | T5 | legs | Uncommon | class_specific | stoffa | **Braghe della firma dell'Assenza** | Braghe |
| 96 | `cdv_t5_main_hand_balestra_002` | T5 | main_hand | Rare | class_specific | balestra | **Balestra dell'apice della Proiezione** | Balestra |
| 97 | `cdv_t5_neck_universal_position_001` | T5 | neck | Common | universal_neutral | universal_position | **Medaglione della via** | Medaglione |
| 98 | `cdv_t5_neck_universal_position_002` | T5 | neck | Common | universal_neutral | universal_position | **Reliquia del mercato** | Reliquia |
| 99 | `cdv_t5_off_hand_balestra_001` | T5 | off_hand | Rare | class_specific | balestra | **Cripta del canone della Dissipazione mirata** | Cripta |
| 100 | `cdv_t5_off_hand_pugnale_001` | T5 | off_hand | Rare | class_specific | pugnale | **Icona dell'apice dell'Incisione** | Icona |
| 101 | `cdv_t5_off_hand_pugnale_002` | T5 | off_hand | Rare | class_specific | pugnale | **Cripta del canone dell'Attimo** | Cripta |
| 102 | `cdv_t5_ring_universal_position_001` | T5 | ring | Rare | class_specific | universal_position | **Cerchietto della firma della Dissipazione** | Cerchietto |
| 103 | `cdv_t5_ring_universal_position_002` | T5 | ring | Epic | class_specific | universal_position | **Sigillo dell'apice del Riflesso** | Sigillo |
| 104 | `cdv_t5_ring_universal_position_003` | T5 | ring | Epic | class_specific | universal_position | **Cerchietto del canone del Drenaggio** | Cerchietto |
| 105 | `cdv_t5_ring_universal_position_004` | T5 | ring | Epic | class_specific | universal_position | **Sigillo della firma del Vuoto** | Sigillo |
| 106 | `cdv_t5_shoulders_stoffa_001` | T5 | shoulders | Common | shared_family | stoffa | **Manto del Rito** | Manto |
| 107 | `cdv_t5_waist_cuoio_001` | T5 | waist | Uncommon | class_specific | cuoio | **Fascia dell'apice della Marcia** | Fascia |
| 108 | `cdv_t5_wrist_stoffa_001` | T5 | wrist | Uncommon | shared_family | stoffa | **Vinca del canone del Rito** | Vinca |

## Legendary Candidate Roster (3 unit × 3 candidati = 9)

### cdv_t5_chest_stoffa_001 · T5 chest stoffa
- narrative_role: `apogee_of_ritual_channeling` · agent_recommendation: **Manto della Canalizzazione totale** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Veste del Faro Rovesciato` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Manto della Canalizzazione totale` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Sudario di Onirade` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

### cdv_t5_main_hand_focus_001 · T5 main_hand focus
- narrative_role: `signature_weapon` · agent_recommendation: **Focus dell'Assenza Consumata** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Occhio del Faro Rovesciato` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Focus dell'Assenza Consumata` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Voce di Onirade` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

### cdv_t5_main_hand_balestra_001 · T5 main_hand balestra
- narrative_role: `ranged_ritual_signature` · agent_recommendation: **Balestra della Dissipazione ultima** · preferred: `AGENT_RECOMMENDATION_ONLY`
  - **proper_noun**: `Lancia dei Frammenti` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **ritual_title**: `Balestra della Dissipazione ultima` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`
  - **hybrid**: `Voce dei Bersagli assenti` · status: `DRAFT_PENDING_PM` · proper_noun: `LORE_PROPOSAL_PENDING_PM`

## Lore Draft Roster (108 non-Legendary · brief)

| blueprint_code | draft_name | lore_text_it_draft |
|---|---|---|
| `cdv_t1_back_universal_position_001` | Cappa neutro | Un cappa neutro d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t1_chest_stoffa_001` | Veste del Rito | Veste del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t1_chest_stoffa_002` | Tunica del Marchio | Tunica del Marchio: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t1_hands_stoffa_001` | Guanti del Rito | Guanti del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t1_head_stoffa_001` | Cappuccio del Rito | Cappuccio del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t1_legs_stoffa_001` | Gambali del Rito | Gambali del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t1_legs_stoffa_002` | Pantaloni del Marchio | Pantaloni del Marchio: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t1_main_hand_balestra_001` | Sigillo della Proiezione | Sigillo della Proiezione: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t1_main_hand_focus_001` | Sigillo del Riflesso | Sigillo del Riflesso: focus del riflesso, custodisce un Frammento in stato calmo. |
| `cdv_t1_main_hand_focus_002` | Focus del Faro | Focus del Faro: focus del riflesso, custodisce un Frammento in stato calmo. |
| `cdv_t1_neck_universal_position_001` | Amuleto neutro | Un amuleto neutro d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t1_ring_universal_position_001` | Anello neutro | Un anello neutro d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t1_shoulders_stoffa_001` | Mantellina del Rito | Mantellina del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_back_universal_position_001` | Mantello semplice | Un mantello semplice d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t2_chest_cuoio_001` | Veste della Caccia rituale | Veste della Caccia rituale: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_chest_stoffa_001` | Cotta della Canalizzazione | Cotta della Canalizzazione: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_feet_stoffa_001` | Stivali tecnico del Rito | Stivali tecnico del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t2_hands_stoffa_001` | Manopole del Marchio | Manopole del Marchio: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t2_head_stoffa_001` | Corona del Marchio | Corona del Marchio: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_head_stoffa_002` | Copricapo della Canalizzazione | Copricapo della Canalizzazione: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_legs_cuoio_001` | Gambali tecnico della Caccia rituale | Gambali tecnico della Caccia rituale: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t2_legs_stoffa_001` | Gambali tecnico del Rito | Gambali tecnico del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t2_main_hand_focus_001` | Sigillo tecnico del Riflesso | Sigillo tecnico del Riflesso: focus del riflesso, custodisce un Frammento in stato calmo. |
| `cdv_t2_main_hand_focus_002` | Focus rituale del Faro | Focus rituale del Faro: focus del riflesso, custodisce un Frammento in stato calmo. |
| `cdv_t2_main_hand_pugnale_001` | Focus rituale dell'Incisione | Focus rituale dell'Incisione: lama per l'incisione del Marchio nell'attimo ravvicinato. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t2_neck_universal_position_001` | Collare semplice | Un collare semplice d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t2_ring_universal_position_001` | Anello tecnico neutro | Un anello tecnico neutro d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t2_ring_universal_position_002` | Vera di scuola comune | Un vera di scuola comune d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t2_shoulders_stoffa_001` | Spalliera del Marchio | Spalliera del Marchio: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t2_waist_stoffa_001` | Cintura tecnico del Rito | Cintura tecnico del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t2_wrist_cuoio_001` | Braccialetto tecnico della Caccia rituale | Braccialetto tecnico della Caccia rituale: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t2_wrist_stoffa_001` | Braccialetto tecnico del Rito | Braccialetto tecnico del Rito: tessuto per contenere il Marchio nelle sue fasi iniziali. |
| `cdv_t3_accessory_universal_position_002` | Reliquia del discepolo del Marchio | Reliquia del discepolo del Marchio: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_accessory_universal_position_003` | Monile del cercatore del Frammento | Monile del cercatore del Frammento: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_back_universal_position_001` | Sciarpa comune | Un sciarpa comune d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t3_chest_stoffa_001` | Casacca dell'Assenza | Casacca dell'Assenza: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_feet_cuoio_001` | Stivali della soglia della Caccia rituale | Stivali della soglia della Caccia rituale: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t3_feet_stoffa_001` | Stivali della soglia del Rito | Stivali della soglia del Rito: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t3_feet_stoffa_002` | Scarpe del discepolo del Marchio | Scarpe del discepolo del Marchio: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t3_hands_cuoio_001` | Guanti della Caccia rituale | Guanti della Caccia rituale: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_hands_stoffa_001` | Bracciali della Canalizzazione | Bracciali della Canalizzazione: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_head_cuoio_001` | Cappuccio della Caccia rituale | Cappuccio della Caccia rituale: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_head_stoffa_001` | Cerchietto dell'Assenza | Cerchietto dell'Assenza: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_legs_stoffa_001` | Pantaloni del discepolo del Marchio | Pantaloni del discepolo del Marchio: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t3_main_hand_balestra_001` | Lanterna del cercatore della Dissipazione mirata | Lanterna del cercatore della Dissipazione mirata: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_main_hand_focus_001` | Lanterna del cercatore del Frammento | Lanterna del cercatore del Frammento: focus del riflesso, custodisce un Frammento in stato calmo. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_main_hand_focus_002` | Prisma del cacciatore della Risonanza | Prisma del cacciatore della Risonanza: focus del riflesso, custodisce un Frammento in stato calmo. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_neck_universal_position_001` | Ciondolo comune | Un ciondolo comune d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t3_off_hand_focus_001` | Reliquiario della soglia del Riflesso | Reliquiario della soglia del Riflesso: focus del riflesso, custodisce un Frammento in stato calmo. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t3_ring_universal_position_001` | Anello della soglia neutro | Un anello della soglia neutro d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t3_ring_universal_position_002` | Cerchio del discepolo semplice | Un cerchio del discepolo semplice d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t3_shoulders_cuoio_001` | Mantellina della Caccia rituale | Mantellina della Caccia rituale: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_shoulders_stoffa_001` | Pauldrones della Canalizzazione | Pauldrones della Canalizzazione: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t3_waist_cuoio_001` | Cintura della soglia della Caccia rituale | Cintura della soglia della Caccia rituale: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t3_waist_stoffa_001` | Cintura della soglia del Rito | Cintura della soglia del Rito: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t3_waist_stoffa_002` | Cintola del cercatore della Canalizzazione | Cintola del cercatore della Canalizzazione: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t3_wrist_stoffa_001` | Braccialetto della soglia del Rito | Braccialetto della soglia del Rito: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t4_accessory_universal_position_001` | Talismano del maestro del Vuoto | Talismano del maestro del Vuoto: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_accessory_universal_position_002` | Monile del custode del Frammento | Monile del custode del Frammento: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_accessory_universal_position_003` | Feticcio del veggente della Dissipazione | Feticcio del veggente della Dissipazione: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_back_universal_position_001` | Sudario del viaggiatore | Un sudario del viaggiatore d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t4_chest_cuoio_001` | Tunica della Marcia | Tunica della Marcia: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_chest_stoffa_001` | Mantello del Riflesso | Mantello del Riflesso: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_feet_cuoio_001` | Scarpe dell'adepto della Marcia | Scarpe dell'adepto della Marcia: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t4_feet_stoffa_001` | Sandali del custode della Canalizzazione | Sandali del custode della Canalizzazione: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t4_hands_stoffa_001` | Bende dell'Assenza | Bende dell'Assenza: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t4_head_cuoio_001` | Corona della Marcia | Corona della Marcia: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_head_stoffa_001` | Diadema del Riflesso | Diadema del Riflesso: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_legs_cuoio_001` | Pantaloni dell'adepto della Marcia | Pantaloni dell'adepto della Marcia: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t4_legs_stoffa_001` | Braghe del veggente dell'Assenza | Braghe del veggente dell'Assenza: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t4_main_hand_balestra_001` | Lanterna del custode della Dissipazione mirata | Lanterna del custode della Dissipazione mirata: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_main_hand_focus_001` | Prisma del veggente della Risonanza | Prisma del veggente della Risonanza: focus del riflesso, custodisce un Frammento in stato calmo. |
| `cdv_t4_main_hand_pugnale_001` | Balestra del maestro del Rito ravvicinato | Balestra del maestro del Rito ravvicinato: lama per l'incisione del Marchio nell'attimo ravvicinato. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_neck_universal_position_001` | Pendaglio del viaggiatore | Un pendaglio del viaggiatore d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t4_off_hand_balestra_001` | Reliquiario del maestro della Proiezione | Reliquiario del maestro della Proiezione: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_off_hand_focus_001` | Reliquiario del maestro del Riflesso | Reliquiario del maestro del Riflesso: focus del riflesso, custodisce un Frammento in stato calmo. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_ring_universal_position_001` | Cerchio dell'adepto semplice | Un cerchio dell'adepto semplice d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t4_ring_universal_position_002` | Vera del custode comune | Un vera del custode comune d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t4_ring_universal_position_003` | Vera del custode del Frammento | Vera del custode del Frammento: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t4_shoulders_cuoio_001` | Spalliera della Marcia | Spalliera della Marcia: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_shoulders_stoffa_001` | Sopravveste dell'Assenza | Sopravveste dell'Assenza: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t4_waist_stoffa_001` | Nastro del veggente dell'Assenza | Nastro del veggente dell'Assenza: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t4_wrist_cuoio_001` | Bracciale dell'adepto della Marcia | Bracciale dell'adepto della Marcia: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_accessory_universal_position_001` | Talismano della firma del Vuoto | Talismano della firma del Vuoto: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_accessory_universal_position_002` | Monile del canone del Frammento | Monile del canone del Frammento: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_accessory_universal_position_003` | Feticcio della firma della Dissipazione | Feticcio della firma della Dissipazione: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_back_universal_position_001` | Velo della via | Un velo della via d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t5_back_universal_position_002` | Drappo del mercato | Un drappo del mercato d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t5_chest_cuoio_001` | Cotta del Cammino | Cotta del Cammino: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t5_feet_stoffa_001` | Ghette della firma dell'Assenza | Ghette della firma dell'Assenza: veste calibrata sul Riflesso, adatta a rituali di soglia. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_hands_cuoio_001` | Manopole dell'apice della Marcia | Manopole dell'apice della Marcia: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t5_hands_stoffa_001` | Palme del Riflesso | Palme del Riflesso: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t5_head_stoffa_001` | Aureola del Rito | Aureola del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t5_legs_cuoio_001` | Cosciali del canone del Cammino | Cosciali del canone del Cammino: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_legs_stoffa_001` | Braghe della firma dell'Assenza | Braghe della firma dell'Assenza: veste calibrata sul Riflesso, adatta a rituali di soglia. |
| `cdv_t5_main_hand_balestra_002` | Balestra dell'apice della Proiezione | Balestra dell'apice della Proiezione: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_neck_universal_position_001` | Medaglione della via | Un medaglione della via d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t5_neck_universal_position_002` | Reliquia del mercato | Un reliquia del mercato d'uso comune, forgiato senza segno di scuola né appartenenza. |
| `cdv_t5_off_hand_balestra_001` | Cripta del canone della Dissipazione mirata | Cripta del canone della Dissipazione mirata: balestra per proiezione rituale, cadenza lenta ma precisa. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_off_hand_pugnale_001` | Icona dell'apice dell'Incisione | Icona dell'apice dell'Incisione: lama per l'incisione del Marchio nell'attimo ravvicinato. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_off_hand_pugnale_002` | Cripta del canone dell'Attimo | Cripta del canone dell'Attimo: lama per l'incisione del Marchio nell'attimo ravvicinato. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_ring_universal_position_001` | Cerchietto della firma della Dissipazione | Cerchietto della firma della Dissipazione: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_ring_universal_position_002` | Sigillo dell'apice del Riflesso | Sigillo dell'apice del Riflesso: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_ring_universal_position_003` | Cerchietto del canone del Drenaggio | Cerchietto del canone del Drenaggio: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_ring_universal_position_004` | Sigillo della firma del Vuoto | Sigillo della firma del Vuoto: oggetto della disciplina, calibrato sulla dissipazione controllata. Segnato dall'Assenza, si rivela nei momenti di canalizzazione. |
| `cdv_t5_shoulders_stoffa_001` | Manto del Rito | Manto del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |
| `cdv_t5_waist_cuoio_001` | Fascia dell'apice della Marcia | Fascia dell'apice della Marcia: cuoio conciato per la caccia rituale, resistente ai passi silenziosi. |
| `cdv_t5_wrist_stoffa_001` | Vinca del canone del Rito | Vinca del canone del Rito: strumento adatto a chi cammina la via delle discipline arcane, senza vincolo di sigillo. |

## Explicit STOP

```
IS2_A_Phase_1          = CLOSED / RATIFIED
IS2_A_Phase_2          = DRAFT GENERATED
Phase_2_closure        = HOLD (attendo PM review)
IS2_B                  = HOLD
NC1                    = HOLD
Registry_v3_gen        = NOT_AUTHORIZED
Registry_v3_app        = NOT_AUTHORIZED
Gate_11                = HOLD
Monaco                 = HOLD
next_action            = ATTENDO VERDICT PM
```