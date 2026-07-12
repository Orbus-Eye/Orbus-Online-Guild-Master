# R18.6.RV3-IS2-A · Item Identity, Naming & Lore Contract · Phase 1

**Gate**: `R18.6.RV3-IS2-A`  
**Phase**: `Phase 1 · Identity/Naming/Lore Contract only`  
**Status**: `CONTRACT_DRAFTED · AWAITING_PM_VERDICT`  
**Regime**: `DOCUMENTAL_ONLY · READ_ONLY_DISCOVERY`  
**Created UTC**: `2026-07-12T13:20:24.152224+00:00`  
**Class slug**: `cacciatore_del_vuoto`  
**Fixed anchors**: Hall = `Faro Rovesciato di Onirade` · Master = `Nael di Onirade` · Loop = `Identify → Mark → Drain → Payoff`  
**Phase 2 status**: `HOLD · NOT_AUTHORIZED`  

---

## §1 · Executive Summary

- **title**: `Executive Summary`
- **content**: `R18.6.RV3-IS2-A Phase 1 · Item Identity, Naming & Lore Contract per la classe cacciatore_del_vuoto · governance-only · zero nomi finali · 120-unit identity matrix in cui 9 preservano identità sorgente (6 REUSE_VALID + 3 REUSE_CONDITIONAL provisional) e 111 NEW_FUTURE richiedono nuova identità canonica in Phase 2. Discovery read-only sul live catalog (178 item) fornisce baseline collision-audit. Nessun name_candidate né lore_text generato in questa fase.`
- **phase**: `Phase 1 · Contract only`
- **phase_2_status**: `HOLD · NOT AUTHORIZED`

## §2 · Scope

- **title**: `Scope`
- **in_scope**:
  - `identity architecture · naming architecture · lore architecture`
  - `language policy · internal name policy · localization contract`
  - `status taxonomies (naming/lore)`
  - `tier tone T1..T5`
  - `rarity tone Common..Legendary`
  - `class identity pillars`
  - `anti-overlap policy (Mago/Paladino/Cacciatore di Mostri/Negromante/Alchimista)`
  - `legacy warlock policy`
  - `existing_reuse preservation`
  - `conditional_identity policy`
  - `new_future_identity policy`
  - `contingency_identity policy`
  - `Legendary identity contract (3 unit T5)`
  - `canonical/restricted/forbidden vocabulary proposals`
  - `collision audit methodology + taxonomy`
  - `duplicate/near-duplicate prevention`
  - `set name policy`
  - `affix language relationship`
  - `mechanic/stat/boss-safeguard prohibition`
  - `identity matrix 120 units`
  - `risk register`
  - `PM open questions`
  - `Phase 2 readiness recommendation`
- **out_of_scope**:
  - `name generation (final names)`
  - `lore text generation`
  - `stat/effect/proc/affix assignment`
  - `item generation / runtime item_id / Registry generation / Registry apply`
  - `DB writes / migration`
  - `backend/frontend/OpenAPI modifications`
  - `NC1 / IS2-B / Gate 11 / Registry v3 / Monaco kickoff`

## §3 · Governance

- **title**: `Governance`
- **regime**: `DOCUMENTAL_ONLY · READ_ONLY_DISCOVERY`
- **pm_verdict_ref**: `IS2-A Phase 1 · GO CONTRACT ONLY`
- **dependencies_closed**:
  - `RV3-EV`
  - `AFX1`
  - `IC1`
  - `IS1`
- **artifacts_created_this_gate**:
  - `memory/r18_6_rv3_is2_a_phase1_identity_naming_lore_contract.md`
  - `memory/r18_6_rv3_is2_a_phase1_identity_naming_lore_contract.json`
- **artifacts_untouched**:
  - `IS1 source MD/JSON`
  - `IS1 closure MD/JSON`
  - `IS1 closure manifest`
  - `PRD.md`
  - `lore_meta.py`
  - `36 sealed artifacts`
- **phase_2_gate**: `PM_AUTHORIZATION_REQUIRED_BEFORE_ANY_NAME_GENERATION`

## §4 · Source Of Truth

- **consumed_read_only**:
  - `Orbus Lore Book (memory/Orbus_Lore_Book_Worldbuilding.pdf)`
  - `R18.5 Itemization artifacts (r18_5_*)`
  - `Cacciatore del Vuoto G1..G8 (r18_6_3_g1..g8_*)`
  - `R18.6.3 G6 Player Guide, G7 Class Hall Completion, G8 Safe-Mode Trial`
  - `RV3-EV (r18_6_rv3_ev_*)`
  - `AFX1 (r18_6_rv3_afx1_*)`
  - `IC1 (r18_6_rv3_ic1_*)`
  - `IS1 (r18_6_rv3_is1_*)`
- **fixed_anchors**:
  - **class_slug**: `cacciatore_del_vuoto`
  - **class_hall**: `Faro Rovesciato di Onirade`
  - **class_master**: `Nael di Onirade`
  - **gameplay_loop**: `Identify → Mark → Drain → Payoff`

## §5 · Is1 Closure Dependency

- **is1_gate_status**: `CLOSED / PM-LOCKED`
- **is1_source_md_sha256**: `cdfc2303c74a0fc94a03861b5ae377f7e1da65800c974fde887ff962ed97c485`
- **is1_source_json_sha256**: `1b0d3ea057b36362fd779ee2d1f5f0e6af1f0b64abdc4a00b7aefd745a616f6b`
- **dependency_type**: `hard_gate_immutable_upstream`

## §6 · Active Roster Baseline

- **roster_total_units**: `120`
- **active_reuse_valid**: `6`
- **active_reuse_conditional**: `3`
- **new_future**: `111`
- **tier_totals**:
  - **T1**: `18`
  - **T2**: `22`
  - **T3**: `26`
  - **T4**: `26`
  - **T5**: `28`
- **slot_totals_14_canonical**:
  - **head**: `8`
  - **neck**: `6`
  - **shoulders**: `7`
  - **chest**: `10`
  - **back**: `6`
  - **hands**: `7`
  - **wrist**: `5`
  - **waist**: `6`
  - **legs**: `10`
  - **feet**: `7`
  - **main_hand**: `15`
  - **off_hand**: `6`
  - **ring**: `12`
  - **accessory**: `15`
- **category_totals**:
  - **ARMOR**: `60`
  - **WEAPON**: `21`
  - **UNIVERSAL**: `39`
- **rarity_totals**:
  - **Common**: `42`
  - **Uncommon**: `33`
  - **Rare**: `27`
  - **Epic**: `15`
  - **Legendary**: `3`
- **identity_totals**:
  - **class_specific**: `68`
  - **shared_family**: `30`
  - **universal_neutral**: `22`

## §7 · Source Realization

- **ev_f2_reuse_valid_universe_immutable**: `12`
- **is1_active_exact_bound_reuse_valid**: `6`
- **is1_unbound_standby_reuse_valid**: `6`
- **active_reuse_conditional**: `3`
- **conditional_standby_pool**: `29`
- **conditional_fallback_reserve**: `3`
- **new_future_active**: `111`
- **worst_case_new_future**: `114`

## §8 · Identity Architecture

- **pillars_cacciatore_del_vuoto**:
  - `Vuoto`
  - `Onirade`
  - `riflesso`
  - `assenza`
  - `Marchio`
  - `Drenaggio`
  - `Frammenti`
  - `dissipazione`
  - `evocazioni`
  - `incorporei`
  - `canalizzazione`
  - `rituale`
- **anti_saturation_rule**: `no_single_pillar_should_dominate_full_roster_naming`

## §9 · Naming Architecture

- **schema_keys**:
  - `blueprint_code`
  - `identity_status`
  - `identity_theme_primary`
  - `identity_theme_secondary`
  - `naming_pattern`
  - `name_candidate`
  - `name_status`
  - `localization_key`
  - `lore_direction`
  - `lore_text`
  - `lore_status`
  - `rarity_tone`
  - `tier_tone`
  - `slot_semantics`
  - `class_identity_strength`
  - `collision_status`
  - `PM_status`
- **player_facing_language**: `italiano`
- **internal_language**: `snake_case_english_technical_namespace`

## §10 · Lore Architecture

- **lore_direction_only_in_phase_1**: `True`
- **no_final_lore_text_written**: `True`
- **boundary**: `any_new_proper_name_marked_LORE_PROPOSAL_PENDING_PM`

## §11 · Language Policy

- **player_facing_name**: `italiano · leggibile · pronunciabile · coerente Orbus fantasy · distinguibile in inventario`
- **internal_name**: `snake_case_english_technical`
- **no_mixing**: `separate identity_key · player_name · localization_key · description_key`

## §12 · Internal Name Policy

- **format**: `snake_case_lowercase_english`
- **reserved_prefixes**:
  - `cdv_`
- **no_conflict_with_live_slugs**: `True`

## §13 · Localization Contract

- **phase_1_state**: `contract_only_values_null`
- **keys_defined**:
  - `display_name_it`
  - `display_name_en_future`
  - `description_it`
  - `description_en_future`
  - `localization_key`

## §14 · Identity Schema

- **see**: `§9 naming_architecture · schema keys`

## §15 · Naming Schema

- **see**: `§9 naming_architecture · schema keys`

## §16 · Lore Schema

- **keys**:
  - `lore_direction`
  - `lore_text`
  - `lore_status`
  - `lore_authority_boundary`

## §17 · Status Taxonomy

- **naming_status**:
  - `PRESERVE_EXISTING`
  - `DRAFT_REQUIRED`
  - `CONTINGENCY_DRAFT_REQUIRED`
  - `PM_REVIEW`
  - `PM_APPROVED`
  - `CANONICAL_LOCKED`
- **lore_status**:
  - `PRESERVE_EXISTING`
  - `DIRECTION_ONLY`
  - `DRAFT_REQUIRED`
  - `LORE_PROPOSAL_PENDING_PM`
  - `PM_APPROVED`
  - `CANONICAL_LOCKED`
- **phase_1_constraint**: `no_name_can_be_PM_APPROVED_or_CANONICAL_LOCKED`

## §18 · T1 Tone

- **tone**: `chiaro · funzionale · leggibile · poco solenne · bassa densità lore`
- **communicates**: `inizio del percorso · strumento · disciplina · apprendimento`
- **avoid**: `titoli epici`

## §19 · T2 Tone

- **tone**: `tecnica · rito iniziale · Marchio · primi Frammenti · controllo del Vuoto`
- **language**: `specialistico`

## §20 · T3 Tone

- **tone**: `identità di classe pienamente leggibile · Onirade · dissipazione · anti-incorporeo · anti-evocazione`
- **note**: `non ogni nome è nome proprio`

## §21 · T4 Tone

- **tone**: `ritualità avanzata · riflesso · canalizzazione · assenza · Faro Rovesciato`
- **register**: `raro · autorevole · non ancora Legendary`

## §22 · T5 Tone

- **tone**: `endgame · firma della classe · alto valore identitario · vocabolario canonico forte`
- **distinction**: `chiaramente distinto dai tier precedenti`

## §23 · Common Tone

- **tone**: `semplice · funzionale · nessun nome proprio · nessun titolo assoluto`

## §24 · Uncommon Tone

- **tone**: `tecnica riconoscibile · prima caratterizzazione · lessico di scuola/rito`

## §25 · Rare Tone

- **tone**: `identità evocativa · funzione meccanica percepibile · lessico canonico più forte`

## §26 · Epic Tone

- **tone**: `nome memorabile · forte identità Vuoto · nessuna inflazione da Legendary`

## §27 · Legendary Tone

- **tone**: `nome univoco · firma narrativa · potenziale nome proprio · forte riconoscibilità`
- **count**: `3 T5-only`
- **phase_1_generation**: `NOT_AUTHORIZED`

## §28 · Armor Identity

- **principle**: `armor identity distinta per family (stoffa vs cuoio)`
- **see**:
  - `§29 stoffa`
  - `§30 cuoio`

## §29 · Stoffa Identity

- **themes**:
  - `rituale`
  - `canalizzazione`
  - `Marchio`
  - `riflesso`
  - `dissipazione`
  - `Onirade`

## §30 · Cuoio Identity

- **themes**:
  - `mobilità`
  - `caccia rituale`
  - `approccio opportunistico`
  - `protezione rituale`
  - `controllo distanza`
- **forbidden**: `identità Cacciatore di Mostri`

## §31 · Focus Identity

- **role**: `primary class weapon`
- **themes**:
  - `riflesso`
  - `faro`
  - `frammento`
  - `Marchio`
  - `risonanza`
  - `assenza controllata`
- **forbidden_substitutes**:
  - `bacchetta`
  - `tomo`
  - `bastone`
  - `grimorio`

## §32 · Balestra Identity

- **role**: `ranged arcane signature`
- **themes**:
  - `precisione rituale`
  - `Marchio a distanza`
  - `dissipazione mirata`
  - `proiezione del Vuoto`
- **forbidden**:
  - `Cacciatore di Mostri Dex`
  - `arma militare generica`
  - `arco rinominato`

## §33 · Pugnale Identity

- **role**: `ritual opportunistic`
- **themes**:
  - `rito ravvicinato`
  - `incisione del Marchio`
  - `protezione rituale`
  - `momento opportunistico`
- **forbidden**:
  - `Ladro`
  - `Assassino`
  - `build Dex primaria`

## §34 · Universal Identity

- **scope**: `back/neck/ring/accessory`
- **rule**: `niente identità esclusiva CdV · niente Nael/Onirade/Hall come identità esclusiva · niente riferimenti a classi/meccaniche esclusive`

## §35 · Class Specific Identity

- **allowed**: `Marchio · Onirade · Frammenti · Faro Rovesciato · incorporei · evocazioni · rituali del Vuoto`
- **rule**: `senza saturazione lessicale`

## §36 · Shared Family Identity

- **compatible_with**: `caster Int · armor leggera · focus neutro · accessori intelligenti`
- **forbidden**: `lore esclusiva Vuoto · riferimenti esclusivi ad altra classe`

## §37 · Universal Neutral Identity

- **rule**: `identità neutra · nessun tag classe · nessun tag CdV esclusivo`

## §38 · Class Identity Pillars

- **see**: `§8 identity_architecture`

## §39 · Anti Mago Overlap

- **forbidden_tropes**:
  - `Arcano generico`
  - `tomo`
  - `incantesimo`
  - `runa arcana generica`
  - `apprendista mago`

## §40 · Anti Paladino Overlap

- **forbidden_tropes**:
  - `Sacro`
  - `Luce`
  - `Giuramento cavalleresco`
  - `fede della Luce`
  - `stendardo sacro`

## §41 · Anti Cacciatore Di Mostri Overlap

- **forbidden_tropes**:
  - `Bestia`
  - `preda`
  - `trofeo`
  - `balestra da caccia militare`
  - `muta di segugi`

## §42 · Anti Negromante Overlap

- **forbidden_tropes**:
  - `Non-morti`
  - `ossa`
  - `sepolcro`
  - `risveglio dei morti`
  - `carne putrida`
  - `corruzione della carne`

## §43 · Anti Alchimista Overlap

- **forbidden_tropes**:
  - `Alchimia`
  - `boccetta`
  - `reagente`
  - `distillazione`
  - `laboratorio`
  - `transmutazione chimica`

## §44 · Legacy Warlock Policy

- **status**: `SOURCE_HISTORY · NON nuova identità canonica`
- **forbidden_reuse_for_new_items**:
  - `Warlock`
  - `Patrono`
  - `Patto demoniaco`
  - `Coven`
  - `Hex`
- **exception**: `un termine può essere riesaminato solo se possiede significato canonico indipendente (soggetto a PM verdict)`

## §45 · Existing Reuse Preservation

- **count**: `6`
- **slugs**:
  - `warlock_patron_seal`
  - `warlock_imp_collar`
  - `warlock_hex_sigil`
  - `warlock_black_ring`
  - `warlock_cursed_pendant`
  - `warlock_fetish_charm`
- **rules**:
  - `existing source identity PRESERVED`
  - `base item rename = NO`
  - `retro-branding Vuoto = NO`
  - `new lore replacement = NO`
  - `no new names generated in Phase 1`

## §46 · Conditional Identity Policy

- **count**: `3`
- **slugs**:
  - `apprentice-robe`
  - `initiate_robe`
  - `apprentice-handbook`
- **identity_status**: `IDENTITY_SOURCE_PRESERVED_PENDING_VALIDATION`
- **fallback_rule**: `if conditional fails → 1:1 NEW_FUTURE fallback → new identity/name required (not generated now)`

## §47 · New Future Identity Policy

- **count**: `111`
- **identity_status**: `NEW_CANONICAL_IDENTITY_REQUIRED · PLAYER_NAME_REQUIRED · LORE_DIRECTION_REQUIRED`
- **phase_1_action**: `no_final_names_no_final_lore`

## §48 · Contingency Identity Policy

- **count**: `3`
- **scope**: `outside active roster of 120`
- **trigger**: `worst_case_all_3_reuse_conditional_fail`
- **phase_1_action**: `no_final_names_no_final_lore`
- **naming_capacity_total_supported_by_contract**: `114`

## §49 · Legendary Identity Contract

- **count**: `3`
- **tier**: `T5-only`
- **units**:
  -
    - **role**: `T5 main_hand focus`
    - **narrative_role**: `signature_weapon_of_the_Cacciatore`
    - **identity_pillar**: `faro_riflesso_marchio_canalizzazione`
    - **forbidden_overlap**:
      - `bacchetta arcana generica`
      - `tomo epico`
      - `staff Mago`
    - **name_structure**: `proper_noun_or_titolo_ritualee_singolare`
    - **lore_density**: `HIGH_but_no_final_lore_phase1`
    - **future_utility_theme_boundary**: `Payoff_climax_Vuoto`
  -
    - **role**: `T5 main_hand balestra`
    - **narrative_role**: `ranged_ritual_signature`
    - **identity_pillar**: `proiezione_Vuoto_precisione_ritualea_distanza`
    - **forbidden_overlap**:
      - `arco Cacciatore di Mostri`
      - `arma militare generica`
    - **name_structure**: `proper_noun_or_designazione_rituale`
    - **lore_density**: `HIGH_but_no_final_lore_phase1`
    - **future_utility_theme_boundary**: `Marchio_a_distanza_dissipazione_mirata`
  -
    - **role**: `T5 chest stoffa`
    - **narrative_role**: `apogee_of_ritual_channeling`
    - **identity_pillar**: `canalizzazione_totale_Onirade_Faro_Rovesciato`
    - **forbidden_overlap**:
      - `mantello Mago generico`
      - `robe Negromante`
    - **name_structure**: `nome_proprio_o_titolo_rituale_apice`
    - **lore_density**: `HIGH_but_no_final_lore_phase1`
    - **future_utility_theme_boundary**: `assenza_dissipazione_endgame`
- **phase_1_state**: `NO_NAMES_GENERATED · NO_STATS · NO_EFFECTS · NO_LORE_FINAL`

## §50 · Canonical Vocabulary

- **core**:
  - `Vuoto`
  - `Onirade`
  - `Marchio`
  - `Frammento`
  - `Faro Rovesciato`
  - `Drenaggio`
  - `Dissipazione`
  - `Riflesso`
  - `Assenza`
  - `Rituale`
  - `Canalizzazione`
- **usage_note**: `non tutti gli item devono contenere il vocabolario canonico · anti-saturazione obbligatoria`

## §51 · Restricted Vocabulary

- **requires_pm_review**:
  - `Nael`
  - `Onirade come luogo proprio nei nomi`
  - `Faro Rovesciato in nome item vs solo lore`
  - `Payoff (dominio meccanico riservato AFX1/IS2-B)`
- **note**: `restricted != forbidden · caso per caso PM adjudication`

## §52 · Forbidden Vocabulary

- **class_overlap_forbidden**:
  - `Sacro`
  - `Luce`
  - `Giuramento`
  - `Non-morto`
  - `Ossa`
  - `Bestia`
  - `Trofeo`
  - `Alchimia`
  - `Bacchetta`
  - `Tomo`
  - `Grimorio`
  - `Ladro`
  - `Assassino`
- **legacy_warlock_forbidden_for_new_items**:
  - `Warlock`
  - `Patrono`
  - `Patto demoniaco`
  - `Coven`
  - `Hex`
- **promise_forbidden**:
  - `+Intelligenza N`
  - `proc`
  - `% chance`
  - `immunità totale`
  - `ignora boss`
  - `annulla ogni evocazione`

## §53 · Repetition Control Proposal

- **principle**: `no more than X% of items can contain the same canonical token`
- **proposed_soft_thresholds_pending_pm**:
  - **Vuoto_in_name**: `≤ 25% del roster`
  - **Onirade_in_name**: `≤ 10% del roster`
  - **Marchio_in_name**: `≤ 20% del roster`
  - **Frammento_in_name**: `≤ 15% del roster`
  - **Faro_Rovesciato_in_name**: `≤ 5% del roster (preferibile solo Legendary/T5)`
- **status**: `PM_REVIEW · NO_AUTO_LOCK`

## §54 · Naming Pattern Catalog

- **patterns**:
  -
    - **id**: `NP_STOFFA_T1`
    - **template**: `[funzionale-descrittore] di [scuola/rito iniziale]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_STOFFA_T2_T3`
    - **template**: `[titolo tecnico] del [Vuoto/Marchio/Onirade]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_STOFFA_T4_T5`
    - **template**: `[titolo rituale] di [nome canonico/riferimento faro]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_CUOIO`
    - **template**: `[abito/protezione] del [rito/caccia rituale]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_FOCUS`
    - **template**: `[oggetto strumentale] del [riflesso/faro/frammento]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_BALESTRA`
    - **template**: `[strumento a distanza] del [Marchio/dissipazione]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_PUGNALE`
    - **template**: `[lama rituale] del [rito ravvicinato]`
    - **example_placeholder**: `None`
  -
    - **id**: `NP_UNIVERSAL`
    - **template**: `[oggetto neutro] [descrittore magico non-classe-specifico]`
    - **example_placeholder**: `None`
- **phase_1_note**: `template only · zero example instantiation · zero final names`

## §55 · Slot Semantics

- **14_canonical_slots**:
  - `head`
  - `neck`
  - `shoulders`
  - `chest`
  - `back`
  - `hands`
  - `wrist`
  - `waist`
  - `legs`
  - `feet`
  - `main_hand`
  - `off_hand`
  - `ring`
  - `accessory`
- **rules**:
  - `ogni futuro nome coerente semanticamente con lo slot`
  - `vietato: nome di anello su chest`
  - `vietato: nome di mantello su accessorio`
  - `vietato: nome di lama su focus`

## §56 · Name Slot Validation

- **validator_hint**: `future validator must check semantic coherence name<->slot before PM_APPROVED`

## §57 · Lore Authority Boundary

- **requires_pm_verdict**:
  - `continenti`
  - `regni`
  - `divinità`
  - `fazioni`
  - `personaggi canonici`
  - `Class Master`
  - `luoghi maggiori`
  - `eventi storici`
- **rule**: `qualunque nuovo nome proprio → LORE_PROPOSAL_PENDING_PM · mai CANONICAL in draft automatico`

## §58 · New Proper Name Governance

- **policy**: `proposed new proper names MUST be flagged LORE_PROPOSAL_PENDING_PM · no auto-canonical in Phase 1`

## §59 · Collision Audit Methodology

- **read_only_sources**:
  - `items collection (178 live)`
  - `IS1 roster (120 blueprint)`
  - `Orbus Lore Book canonical docs`
  - `Class Hall names`
  - `Class Master names`
- **audit_type**: `read_only_discovery · zero mutation`
- **phase**: `baseline_only_no_names_in_phase_1_but_taxonomy_locked`

## §60 · Collision Taxonomy

- **categories**:
  - `EXACT_DUPLICATE`
  - `NORMALIZED_DUPLICATE`
  - `NEAR_DUPLICATE`
  - `LORE_COLLISION`
  - `CLASS_IDENTITY_COLLISION`
  - `SAFE`

## §61 · Live Catalog Collision Audit

- **warlock_legacy_items_count**: `18`
- **voidpiercer_bow_present**: `True`
- **arcane_adept_orb_present**: `True`
- **cacciatore_del_vuoto_items_pre_existing**: `0`
- **total_live_items**: `178`
- **unique_live_names_lowercased**: `178`
- **unique_live_slugs_lowercased**: `178`

## §62 · Lore Collision Audit

- **canonical_places_locked**:
  - `Faro Rovesciato di Onirade`
  - `Onirade`
- **canonical_npc_locked**:
  - `Nael di Onirade`
- **collision_scope_phase_1**: `baseline_only`
- **warning_forbidden_reuse_for_new_items**: `18`

## §63 · Class Collision Audit

- **forbidden_reuse_of_class_signature_terms_from**:
  - `Mago`
  - `Paladino`
  - `Cacciatore di Mostri`
  - `Negromante`
  - `Alchimista`
  - `Assassino/Ladro`

## §64 · Duplicate Prevention

- **forbidden**:
  - `stesso nome su slot diversi`
  - `nome differenziato solo da numero`
  - `nome differenziato solo da rarità`
  - `5 copie stesso nome per T1..T5`
  - `sostituzione meccanica di una parola senza identità distinta`

## §65 · Near Duplicate Prevention

- **rules**:
  - `normalized name distance ≥ threshold PM_DEFINE`
  - `semantic distinct pillar per item`

## §66 · Set Name Policy

- **set_mechanics_authorized**: `False`
- **set_bonuses_authorized**: `False`
- **set_completion_2_4_6_pieces**: `NOT_AUTHORIZED`
- **cohesive_naming_family_without_gameplay_set_mechanics**: `ALLOWED_ONLY_AS_NARRATIVE_COHESION`

## §67 · Affix Language Relationship

- **may_suggest**:
  - `Marchio`
  - `Drenaggio`
  - `Dissipazione`
  - `Frammenti`
  - `Payoff`
  - `anti-incorporeo`
  - `anti-evocazione`
  - `canalizzazione`
  - `rituale`
- **constraint**: `name implication must not exceed future mechanical specification (consumes AFX1 vocabulary)`

## §68 · Mechanic Promise Prohibition

- **forbidden_language**:
  - `annulla ogni evocazione`
  - `dissipa qualsiasi effetto`
  - `uccide tutti gli incorporei`
  - `rende invulnerabili`
  - `ignora i boss`
- **principle**: `lore cannot contradict boss safeguard / hard cap / AFX1`

## §69 · Stat Promise Prohibition

- **forbidden**:
  - `+N Intelligenza`
  - `+% X`
  - `proc rate esplicito`
  - `durate esplicite`
  - `cap numerici`
  - `danno numerico`
  - `immunità assoluta`
- **reason**: `stat values appartengono a IS2-B (HOLD)`

## §70 · Boss Safeguard Language

- **principle**: `boss safeguard must not be contradicted by item names or lore descriptions`

## §71 · Anti P2W Narrative Neutrality

- **principle**: `nessun nome/lore che suggerisca vantaggio pay-to-win o exclusive advantage attraverso rarity/tier`

## §72 · Identity Matrix 120 Units

- **note**: `see array 'identity_matrix' at document root · 120 rows · all name_candidate=null lore_text=null in Phase 1`

## §73 · Active Reuse Accounting

- **active_reuse_valid_count**: `6`
- **active_reuse_valid_slugs**:
  - `warlock_patron_seal`
  - `warlock_imp_collar`
  - `warlock_hex_sigil`
  - `warlock_black_ring`
  - `warlock_cursed_pendant`
  - `warlock_fetish_charm`
- **active_reuse_conditional_count**: `3`
- **active_reuse_conditional_slugs**:
  - `apprentice-robe`
  - `initiate_robe`
  - `apprentice-handbook`
- **existing_identity_preserve_count_total**: `9`

## §74 · New Future Accounting

- **count**: `111`
- **identity_required**: `True`
- **phase_1_names_generated**: `0`

## §75 · Contingency Accounting

- **count**: `3`
- **outside_active_roster**: `True`
- **trigger**: `worst_case_all_3_conditional_fail`
- **phase_1_names_generated**: `0`

## §76 · Validation Rules

- **sections_required**: `80`
- **identity_matrix_rows_required**: `120`
- **unique_blueprint_codes_required**: `120`
- **all_name_candidates_must_be_null_phase_1**: `True`
- **all_lore_text_must_be_null_phase_1**: `True`
- **json_parse_must_pass**: `True`
- **md_json_semantic_parity_required**: `True`

## §77 · Risk Register

- **risks**:
  -
    - **id**: `R1`
    - **name**: `Semantic saturation of Void vocabulary`
    - **severity**: `HIGH`
    - **mitigation**: `§53 repetition control thresholds`
  -
    - **id**: `R2`
    - **name**: `Class identity collision with Mago/Negromante/Alchimista`
    - **severity**: `HIGH`
    - **mitigation**: `§39-§43 anti-overlap policy`
  -
    - **id**: `R3`
    - **name**: `Legacy Warlock terminology drift`
    - **severity**: `MEDIUM`
    - **mitigation**: `§44 legacy_warlock_policy`
  -
    - **id**: `R4`
    - **name**: `Name-slot semantic mismatch`
    - **severity**: `MEDIUM`
    - **mitigation**: `§55-§56 slot_semantics + name_slot_validation`
  -
    - **id**: `R5`
    - **name**: `Mechanic/stat promises in item names`
    - **severity**: `HIGH`
    - **mitigation**: `§67-§70 affix relationship + prohibitions`
  -
    - **id**: `R6`
    - **name**: `Live catalog collision (178 items)`
    - **severity**: `MEDIUM`
    - **mitigation**: `§59-§64 collision audit methodology`
  -
    - **id**: `R7`
    - **name**: `Legendary inflation across non-T5 tiers`
    - **severity**: `MEDIUM`
    - **mitigation**: `§27 legendary_tone + §49 legendary_identity_contract`
  -
    - **id**: `R8`
    - **name**: `Retro-branding of REUSE_VALID/CONDITIONAL sources`
    - **severity**: `HIGH`
    - **mitigation**: `§45-§46 preservation policies`
  -
    - **id**: `R9`
    - **name**: `Fetish_charm/cursed_pendant/black_ring narrative dissonance with new accessory blueprint`
    - **severity**: `LOW`
    - **mitigation**: `§45 base item rename NO`
  -
    - **id**: `R10`
    - **name**: `Contingency 3 units drifting into Phase 2 without gate`
    - **severity**: `LOW`
    - **mitigation**: `§48 contingency_identity_policy + Phase 2 HOLD`

## §78 · Pm Open Questions

- **questions**:
  -
    - **question_id**: `Q1`
    - **verbatim_question**: `Confermare le soglie di ripetizione lessicale proposte in §53 o richiedere revisione?`
    - **agent_recommendation**: `Adottare le soglie proposte come baseline PM_REVIEW e affinare in Phase 2 con dati reali.`
    - **impact**: `HIGH`
    - **default_proposal**: `soglie §53 as-is`
    - **blocking**: `False`
  -
    - **question_id**: `Q2`
    - **verbatim_question**: `L'uso del termine 'Nael' o 'Onirade' è ammesso solo in lore o anche in item name (non-Legendary)?`
    - **agent_recommendation**: `Restringere l'uso in nomi item ai soli Legendary T5 · in tier inferiori solo in lore text.`
    - **impact**: `HIGH`
    - **default_proposal**: `restrizione Legendary-only`
    - **blocking**: `True`
  -
    - **question_id**: `Q3`
    - **verbatim_question**: `Il termine 'Payoff' (meccanica AFX1) può apparire in nomi player-facing?`
    - **agent_recommendation**: `NO · riservare 'Payoff' al dominio meccanico interno (AFX1/IS2-B).`
    - **impact**: `MEDIUM`
    - **default_proposal**: `forbid_in_names`
    - **blocking**: `True`
  -
    - **question_id**: `Q4`
    - **verbatim_question**: `I 6 REUSE_VALID warlock preservano il nome legacy in localizzazione italiana futura o richiedono display_name_it distinto?`
    - **agent_recommendation**: `Preservare il nome legacy come display_name_en_future · richiedere display_name_it distinto in IS2-A Phase 2 (PM verdict per ciascuno).`
    - **impact**: `HIGH`
    - **default_proposal**: `defer_to_phase_2_per_item_PM`
    - **blocking**: `True`
  -
    - **question_id**: `Q5`
    - **verbatim_question**: `È autorizzato definire 'cohesive naming family' narrativi anche senza set-mechanic in Phase 1?`
    - **agent_recommendation**: `Autorizzare la struttura del contratto (§66) ma NO nomi concreti in Phase 1.`
    - **impact**: `LOW`
    - **default_proposal**: `contract_only_no_names`
    - **blocking**: `False`
  -
    - **question_id**: `Q6`
    - **verbatim_question**: `Le 3 unità Legendary T5 richiedono narrative_role di tipo 'nome proprio' oppure 'titolo rituale' o entrambi?`
    - **agent_recommendation**: `Ammettere entrambe le strutture per Phase 2 · PM verdict caso per caso in Phase 2 dopo draft.`
    - **impact**: `MEDIUM`
    - **default_proposal**: `both_structures_allowed`
    - **blocking**: `False`
  -
    - **question_id**: `Q7`
    - **verbatim_question**: `Il verdict PM su §51 restricted_vocabulary (Faro Rovesciato, Payoff) è richiesto prima di Phase 2 kickoff?`
    - **agent_recommendation**: `SÌ · adjudication esplicita prima di autorizzare Phase 2.`
    - **impact**: `HIGH`
    - **default_proposal**: `PM_adjudicate_before_phase_2`
    - **blocking**: `True`
  -
    - **question_id**: `Q8`
    - **verbatim_question**: `La contingency di 3 unità entra nel naming contract con capacity 114 o resta fuori fino al trigger?`
    - **agent_recommendation**: `Restare fuori del roster attivo · contract dichiara capacity 114 max ma solo 111 attivi in Phase 2 iniziale.`
    - **impact**: `LOW`
    - **default_proposal**: `capacity_declared_but_dormant`
    - **blocking**: `False`
  -
    - **question_id**: `Q9`
    - **verbatim_question**: `L'esistente `arcane_adept_orb` (Legendary amulet) può essere considerato pre-existing successor blueprint o resta NOT_COMPATIBLE definitivamente?`
    - **agent_recommendation**: `NOT_COMPATIBLE final · futuro item Vuoto-native con nome distinto · zero retro-branding.`
    - **impact**: `MEDIUM`
    - **default_proposal**: `NOT_COMPATIBLE_final`
    - **blocking**: `True`
  -
    - **question_id**: `Q10`
    - **verbatim_question**: `Autorizzare l'inclusione di `armor_tags`/`weapon_tags` come semantic hint in naming_pattern_catalog Phase 2?`
    - **agent_recommendation**: `SÌ come hint solo · non authoritative per slot (§8 IS1 policy).`
    - **impact**: `LOW`
    - **default_proposal**: `allow_as_hint_only`
    - **blocking**: `False`

## §79 · Phase 2 Readiness

- **prerequisites_before_phase_2_kickoff**:
  - `PM adjudication of §78 blocking questions (Q2,Q3,Q4,Q7,Q9)`
  - `PM ratification of §53 repetition thresholds (Q1)`
  - `PM verdict on §51 restricted vocabulary (Q7)`
  - `PM verdict on legacy warlock names localization strategy (Q4)`
- **phase_2_scope_hint**: `full naming/lore roster generation for 111 NEW_FUTURE + 3 Legendary T5 contract fulfillment · localization pass · PM review cycles · collision audit vs live 178 + Phase-2-generated names`

## §80 · Go Hold Recommendation

- **phase_2_recommendation**: `HOLD`
- **phase_2_authorization_required**: `True`
- **current_state**: `IS2-A Phase 1 CONTRACT WRITTEN · awaiting PM verdict on §78 blocking questions and on §51 restricted vocabulary`
- **next_action**: `await_PM_verdict`

## Identity Matrix · 120 Units (Phase 1 · all name_candidate=null · lore_text=null)

Rows: **120** · Unique blueprint_code: **120** · Existing identity preserve: **9** · New identity required: **111** · Contingency: **3** · Naming capacity supported: **114**

| # | blueprint_code | src | tier | slot | rarity | identity | family | identity_status | naming_status | lore_status | primary_theme |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `cdv_t1_head_stoffa_001` | NF | T1 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 2 | `cdv_t2_head_stoffa_001` | NF | T2 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 3 | `cdv_t2_head_stoffa_002` | NF | T2 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 4 | `cdv_t3_head_stoffa_001` | NF | T3 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 5 | `cdv_t3_head_cuoio_001` | NF | T3 | head | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 6 | `cdv_t4_head_stoffa_001` | NF | T4 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 7 | `cdv_t4_head_cuoio_001` | NF | T4 | head | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 8 | `cdv_t5_head_stoffa_001` | NF | T5 | head | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 9 | `cdv_t2_accessory_universal_position_002` | RV | T2 | accessory | Rare | class_specific | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `Vuoto_Marchio_Onirade` |
| 10 | `cdv_t2_neck_universal_position_001` | NF | T2 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 11 | `cdv_t3_neck_universal_position_001` | NF | T3 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 12 | `cdv_t4_neck_universal_position_001` | NF | T4 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 13 | `cdv_t5_neck_universal_position_001` | NF | T5 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 14 | `cdv_t5_neck_universal_position_002` | NF | T5 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 15 | `cdv_t1_shoulders_stoffa_001` | NF | T1 | shoulders | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 16 | `cdv_t2_shoulders_stoffa_001` | NF | T2 | shoulders | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 17 | `cdv_t3_shoulders_stoffa_001` | NF | T3 | shoulders | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 18 | `cdv_t3_shoulders_cuoio_001` | NF | T3 | shoulders | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 19 | `cdv_t4_shoulders_stoffa_001` | NF | T4 | shoulders | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 20 | `cdv_t4_shoulders_cuoio_001` | NF | T4 | shoulders | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 21 | `cdv_t5_shoulders_stoffa_001` | NF | T5 | shoulders | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 22 | `cdv_t1_chest_stoffa_001` | NF | T1 | chest | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 23 | `cdv_t1_chest_stoffa_002` | NF | T1 | chest | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 24 | `cdv_t1_chest_stoffa_003` | RC | T1 | chest | Common | shared_family | stoffa | `IDENTITY_SOURCE_PRESERVED_PENDING_VALIDATION` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `caster_int_rituale_generico` |
| 25 | `cdv_t2_chest_stoffa_001` | NF | T2 | chest | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 26 | `cdv_t2_chest_cuoio_001` | NF | T2 | chest | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 27 | `cdv_t3_chest_stoffa_001` | NF | T3 | chest | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 28 | `cdv_t4_chest_stoffa_001` | NF | T4 | chest | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 29 | `cdv_t4_chest_cuoio_001` | NF | T4 | chest | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 30 | `cdv_t5_chest_stoffa_001` | NF | T5 | chest | Legendary | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 31 | `cdv_t5_chest_cuoio_001` | NF | T5 | chest | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 32 | `cdv_t3_accessory_universal_position_001` | RV | T3 | accessory | Epic | class_specific | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `Vuoto_Marchio_Onirade` |
| 33 | `cdv_t2_back_universal_position_001` | NF | T2 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 34 | `cdv_t3_back_universal_position_001` | NF | T3 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 35 | `cdv_t4_back_universal_position_001` | NF | T4 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 36 | `cdv_t5_back_universal_position_001` | NF | T5 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 37 | `cdv_t5_back_universal_position_002` | NF | T5 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 38 | `cdv_t2_accessory_universal_position_003` | RV | T2 | accessory | Epic | class_specific | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `Vuoto_Marchio_Onirade` |
| 39 | `cdv_t2_hands_stoffa_001` | NF | T2 | hands | Common | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 40 | `cdv_t3_hands_stoffa_001` | NF | T3 | hands | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 41 | `cdv_t3_hands_cuoio_001` | NF | T3 | hands | Common | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 42 | `cdv_t4_hands_stoffa_001` | NF | T4 | hands | Common | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 43 | `cdv_t5_hands_stoffa_001` | NF | T5 | hands | Common | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 44 | `cdv_t5_hands_cuoio_001` | NF | T5 | hands | Uncommon | shared_family | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 45 | `cdv_t2_wrist_stoffa_001` | NF | T2 | wrist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 46 | `cdv_t2_wrist_cuoio_001` | NF | T2 | wrist | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 47 | `cdv_t3_wrist_stoffa_001` | NF | T3 | wrist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 48 | `cdv_t4_wrist_cuoio_001` | NF | T4 | wrist | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 49 | `cdv_t5_wrist_stoffa_001` | NF | T5 | wrist | Uncommon | shared_family | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `caster_int_rituale_generico` |
| 50 | `cdv_t2_waist_stoffa_001` | NF | T2 | waist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 51 | `cdv_t3_waist_stoffa_001` | NF | T3 | waist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 52 | `cdv_t3_waist_stoffa_002` | NF | T3 | waist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 53 | `cdv_t3_waist_cuoio_001` | NF | T3 | waist | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 54 | `cdv_t4_waist_stoffa_001` | NF | T4 | waist | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 55 | `cdv_t5_waist_cuoio_001` | NF | T5 | waist | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 56 | `cdv_t1_legs_stoffa_001` | NF | T1 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 57 | `cdv_t1_legs_stoffa_002` | NF | T1 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 58 | `cdv_t1_legs_stoffa_003` | RC | T1 | legs | Uncommon | class_specific | stoffa | `IDENTITY_SOURCE_PRESERVED_PENDING_VALIDATION` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `Vuoto_Marchio_Onirade` |
| 59 | `cdv_t2_legs_stoffa_001` | NF | T2 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 60 | `cdv_t2_legs_cuoio_001` | NF | T2 | legs | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 61 | `cdv_t3_legs_stoffa_001` | NF | T3 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 62 | `cdv_t4_legs_stoffa_001` | NF | T4 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 63 | `cdv_t4_legs_cuoio_001` | NF | T4 | legs | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 64 | `cdv_t5_legs_stoffa_001` | NF | T5 | legs | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 65 | `cdv_t5_legs_cuoio_001` | NF | T5 | legs | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 66 | `cdv_t2_feet_stoffa_001` | NF | T2 | feet | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 67 | `cdv_t3_feet_stoffa_001` | NF | T3 | feet | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 68 | `cdv_t3_feet_stoffa_002` | NF | T3 | feet | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 69 | `cdv_t3_feet_cuoio_001` | NF | T3 | feet | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 70 | `cdv_t4_feet_stoffa_001` | NF | T4 | feet | Uncommon | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 71 | `cdv_t4_feet_cuoio_001` | NF | T4 | feet | Uncommon | class_specific | cuoio | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 72 | `cdv_t5_feet_stoffa_001` | NF | T5 | feet | Rare | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 73 | `cdv_t1_main_hand_focus_001` | NF | T1 | main_hand | Uncommon | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 74 | `cdv_t1_main_hand_focus_002` | NF | T1 | main_hand | Uncommon | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 75 | `cdv_t1_main_hand_balestra_001` | NF | T1 | main_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 76 | `cdv_t2_main_hand_focus_001` | NF | T2 | main_hand | Uncommon | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 77 | `cdv_t2_main_hand_focus_002` | NF | T2 | main_hand | Uncommon | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 78 | `cdv_t2_main_hand_pugnale_001` | NF | T2 | main_hand | Rare | class_specific | pugnale | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 79 | `cdv_t3_main_hand_focus_001` | NF | T3 | main_hand | Rare | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 80 | `cdv_t3_main_hand_focus_002` | NF | T3 | main_hand | Rare | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 81 | `cdv_t3_main_hand_balestra_001` | NF | T3 | main_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 82 | `cdv_t4_main_hand_focus_001` | NF | T4 | main_hand | Uncommon | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 83 | `cdv_t4_main_hand_balestra_001` | NF | T4 | main_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 84 | `cdv_t4_main_hand_pugnale_001` | NF | T4 | main_hand | Rare | class_specific | pugnale | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 85 | `cdv_t5_main_hand_focus_001` | NF | T5 | main_hand | Legendary | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 86 | `cdv_t5_main_hand_balestra_001` | NF | T5 | main_hand | Legendary | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 87 | `cdv_t5_main_hand_balestra_002` | NF | T5 | main_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 88 | `cdv_t3_off_hand_focus_001` | NF | T3 | off_hand | Rare | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 89 | `cdv_t4_off_hand_focus_001` | NF | T4 | off_hand | Rare | class_specific | focus | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 90 | `cdv_t4_off_hand_balestra_001` | NF | T4 | off_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 91 | `cdv_t5_off_hand_balestra_001` | NF | T5 | off_hand | Rare | class_specific | balestra | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 92 | `cdv_t5_off_hand_pugnale_001` | NF | T5 | off_hand | Rare | class_specific | pugnale | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 93 | `cdv_t5_off_hand_pugnale_002` | NF | T5 | off_hand | Rare | class_specific | pugnale | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Rituale_Frammento` |
| 94 | `cdv_t2_accessory_universal_position_001` | RV | T2 | accessory | Rare | universal_neutral | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `neutro_universale` |
| 95 | `cdv_t2_ring_universal_position_001` | NF | T2 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 96 | `cdv_t2_ring_universal_position_002` | NF | T2 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 97 | `cdv_t3_ring_universal_position_001` | NF | T3 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 98 | `cdv_t3_ring_universal_position_002` | NF | T3 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 99 | `cdv_t4_ring_universal_position_001` | NF | T4 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 100 | `cdv_t4_ring_universal_position_002` | NF | T4 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 101 | `cdv_t4_ring_universal_position_003` | NF | T4 | ring | Rare | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 102 | `cdv_t5_ring_universal_position_001` | NF | T5 | ring | Rare | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 103 | `cdv_t5_ring_universal_position_002` | NF | T5 | ring | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 104 | `cdv_t5_ring_universal_position_003` | NF | T5 | ring | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 105 | `cdv_t5_ring_universal_position_004` | NF | T5 | ring | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 106 | `cdv_t1_accessory_universal_position_001` | RV | T1 | accessory | Rare | universal_neutral | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `neutro_universale` |
| 107 | `cdv_t1_accessory_universal_position_002` | RV | T1 | accessory | Epic | universal_neutral | universal_position | `IDENTITY_PRESERVED_EXISTING` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `neutro_universale` |
| 108 | `cdv_t1_accessory_universal_position_003` | RC | T1 | accessory | Epic | class_specific | universal_position | `IDENTITY_SOURCE_PRESERVED_PENDING_VALIDATION` | `PRESERVE_EXISTING` | `PRESERVE_EXISTING` | `Vuoto_Marchio_Onirade` |
| 109 | `cdv_t1_ring_universal_position_001` | NF | T1 | ring | Rare | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 110 | `cdv_t1_neck_universal_position_001` | NF | T1 | neck | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 111 | `cdv_t1_hands_stoffa_001` | NF | T1 | hands | Common | class_specific | stoffa | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 112 | `cdv_t1_back_universal_position_001` | NF | T1 | back | Common | universal_neutral | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `neutro_universale` |
| 113 | `cdv_t3_accessory_universal_position_002` | NF | T3 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 114 | `cdv_t3_accessory_universal_position_003` | NF | T3 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 115 | `cdv_t4_accessory_universal_position_001` | NF | T4 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 116 | `cdv_t4_accessory_universal_position_002` | NF | T4 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 117 | `cdv_t4_accessory_universal_position_003` | NF | T4 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 118 | `cdv_t5_accessory_universal_position_001` | NF | T5 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 119 | `cdv_t5_accessory_universal_position_002` | NF | T5 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |
| 120 | `cdv_t5_accessory_universal_position_003` | NF | T5 | accessory | Epic | class_specific | universal_position | `NEW_CANONICAL_IDENTITY_REQUIRED` | `DRAFT_REQUIRED` | `DIRECTION_ONLY` | `Vuoto_Marchio_Onirade` |

**Nota Phase 1**: tutti i campi `name_candidate`, `lore_text`, `display_name_it`, `display_name_en_future`, `description_it`, `description_en_future`, `localization_key` sono impostati a `null`/None. Fare riferimento al JSON per la matrice completa.

## Accounting Summary

- **identity_matrix_rows**: `120`
- **unique_blueprint_codes**: `120`
- **existing_identity_preserve_count**: `9`
- **new_identity_required_count**: `111`
- **contingency_new_identity_possible**: `3`
- **naming_capacity_total_supported**: `114`
- **source_type_totals**: `{'NEW_FUTURE': 111, 'REUSE_VALID': 6, 'REUSE_CONDITIONAL': 3}`

## Explicit STOP

```
IS2_A_Phase_1          = ARTIFACT WRITTEN
IS2_A_Phase_2          = HOLD (NOT AUTHORIZED)
IS2_B                  = HOLD
AFX2                   = RESERVED FUTURE
NC1                    = HOLD
Registry_v3_gen        = NOT_AUTHORIZED
Registry_v3_app        = NOT_AUTHORIZED
Gate_11                = HOLD
Monaco                 = HOLD
next_action            = ATTENDO VERDICT PM
```
