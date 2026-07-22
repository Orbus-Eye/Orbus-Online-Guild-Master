# R18.6.RV3-IS2-B Phase 1 · Final Closure Report

**Gate**: `R18.6.RV3-IS2-B Phase 1 · Stat Budget & Mechanical Effect Contract`
**Regime**: DOCUMENTAL ONLY · READ-ONLY · NO APPLY
**Stato**: **CLOSED / PM-LOCKED**
**Baseline consumata**: R18.5 · CdV G1-G5 · AFX1 · IC1 · IS1 · IS2-A Phase 1 · IS2-A Phase 2 Rev-4 · IS2-A-L1
**Timestamp closure**: 2026-07-22T08:21:48Z
**Lingua**: Italiano
**Continuità**: IS2-A ramo LOCKED/IMMUTABLE · IS2-B Phase 1 chiuso in same-dispatch post PM verdict Q01-Q08

---

## 1. PM verdict

Il PM ha adjudicato in modo autoritativo le 10 sub-domande Q01-Q08 in un unico dispatch. Nessuna open question residua (`blocking = 0`). L'artefatto Phase 1 è stato patchato deterministicamente per integrare i verdetti, e questo report chiude formalmente Phase 1.

## 2. Phase 1 CLOSED

- Gate `R18.6.RV3-IS2-B Phase 1` → **CLOSED / PM-LOCKED**.
- Nessuna riapertura ammessa senza Gate correttivo esplicito.
- Phase 2 **NON avviata**.

## 3. Section count

57/57 sezioni preservate nel draft Phase 1 patchato (`grep -c "^## [0-9]"` sull'MD = 57; `len(sections)` sul JSON = 57). Nessuna sezione persa nella patch.

## 4. Main-stat contract

- Main stat CdV: **Intelligenza**
- Priority: Intelligenza → Costituzione → Destrezza
- Soft cap Intelligenza: **100**
- Tier bands: T1 10-25 · T2 25-45 · T3 45-70 · T4 70-90 · T5 90-115
- Item-level main_stat_value: `null` in Phase 1

## 5. Secondary-stat priority

- Costituzione = secondary defensive
- Destrezza = tertiary utility/opportunistic
- Vietato: Dex main stat CdV · dual-primary Int/Dex · conversione retroattiva Dex→Int

## 6. Tier stat bands

Bande di Intelligenza per tier: **T1 10-25 · T2 25-45 · T3 45-70 · T4 70-90 · T5 90-115**.

## 7. Slot budget bands (Q03 DESIGN_LOCKED)

| Banda | Weight | Slots |
|---|---:|---|
| **S** Primary | **1.00** | main_hand · chest · legs |
| **A** Major | **0.85** | head · shoulders · hands · feet |
| **B** Standard | **0.70** | neck · back · waist · off_hand |
| **C** Utility | **0.55** | wrist · ring · accessory |

Relative base-budget weights, NON statistiche/multiplier separati.

## 8. Rarity multipliers

`Common 1.00 · Uncommon 1.15 · Rare 1.35 · Epic 1.60 · Legendary 1.85`. TOTAL BUDGET MULTIPLIER incluse utility uniche. Anti-double-counting §15.

## 9. Focus coefficient = 1.00

`DESIGN_LOCKED` · baseline immutabile per la classe pilota.

## 10. Balestra coefficient = 0.88 (Q01)

`DESIGN_LOCKED` · banda ratificata 0.85-0.90. Razionale PM: identità a distanza · sicurezza posizionale · precisione/dissipazione mirata · minore potenza vs focus · nessuna deriva Dex-primary.

## 11. Pugnale coefficient = 0.78 (Q02)

`DESIGN_LOCKED` · banda ratificata 0.70-0.80. Razionale PM: rischio da prossimità · identità rituale/opportunistica · minore potenza strutturale vs focus · compensazione parziale · no conversione Dex-primary. Ritual close bonus ≤ 1 per Mark application, refresh non resetta.

## 12. Rounding policy (Q04)

- Metodo: **`ROUND_HALF_UP`** final-only (non banker's rounding)
- Internal precision: **4 decimal places**
- No intermediate rounding
- Ordine: `base budget → slot multiplier → weapon coefficient → rarity multiplier → budget split → final rounding`
- Output futuro: flat stats int · percentages 1 decimal · durations 1 decimal sec · coefficients 2 decimal · internal budget 4 decimal
- Residui → main stat prima, secondary defensive poi. Mai creare budget extra.

## 13. Stacking policy (Q05)

- Passive flat stats → **ADDITIVE** (entro budget/soft cap/system cap)
- Stesso unique effect nominale → **NON_STACKING** · `HIGHEST_EFFECTIVE_VALUE_WINS`
- Same family default → **NON_STACKING**, additivo solo con `ADD_WITHIN_CAP` esplicito
- Durate → **REFRESH**, no auto-extension, `EXTEND_WITHIN_HARD_CAP` opt-in
- Proc chance → **`ADDITIVE_BEFORE_CAP`**, cap 45%
- Legendary same identity → **NON_STACKING**, highest valid wins, no automatic multiplicative synergy

## 14. Utility/effect budget ceilings (Q07)

Combined effect+utility ceiling per rarity (**MAXIMUM CAPS, not target**):

| Rarity | Combined ceiling | Statistical minimum |
|---|:---:|:---:|
| Common | ≤ 10% | ≥ 90% |
| Uncommon | ≤ 20% | ≥ 80% |
| Rare | ≤ 30% | ≥ 70% |
| Epic | ≤ 40% | ≥ 60% |
| Legendary | ≤ 50% | ≥ 50% |

Utility share interna: non-Legendary ≤ 40% del combined; Legendary ≤ 50% del combined. Budget non speso NON diventa potenza extra esterna.

## 15. Anti-double-counting rule

**TOTAL ITEM BUDGET** = unica sorgente di potenza (base stats + effects + utility + affix + unique Legendary). Rarity multiplier applicato **una sola volta** al totale. Ogni componente consuma il medesimo totale. Vietato: `rarity multiplier + full-stat + full-effect + full-affix + free unique utility`.

## 16. Affix eligibility boundary

T1=1 · T2=2 · T3=3 · T4=4 · T5=5 slot. Overlay 140 family occurrences su 120 blueprint units = **eligibility**, non assegnazione.

## 17. Effect taxonomy (13 categorie)

`PASSIVE_STAT · CONDITIONAL_STAT · MARK_INTERACTION · DRAIN_INTERACTION · FRAGMENT_INTERACTION · PAYOFF_UTILITY (tecnico interno, non player-facing "Payoff") · DISPEL_UTILITY · ANTI_INCORPOREAL · ANTI_SUMMON · CHANNEL_MOBILITY · RITUAL_PROTECTION · WEAPON_IDENTITY_EFFECT · LEGENDARY_UNIQUE_EFFECT`

## 18. Mechanic hard caps (immutabili)

- Frammenti cap = **5**
- Marchio duration = **10**
- Active marks = **5**
- Combined proc cap = **45%**
- Focus bonus per resource segment = **≤ 2**
- Pugnale ritual-close bonus per Mark application = **≤ 1** (refresh non resetta)

Nessun item, affix, Legendary unique può violarli.

## 19. Boss safeguards

Vietato: direct boss nullification · boss immunity bypass · unconditional summon deletion · ignore boss safeguard. Direzioni future ammesse **solo** su valid boss-summoned add con safeguard/condition/budget. Schema flag `boss_safeguard_required=true` su ANTI_SUMMON, DISPEL_UTILITY, ANTI_INCORPOREAL.

## 20. Forbidden mechanics (incluso Q08)

resource cap increase · active marks > 5 · Mark duration > 10 · unmarked resource generation · direct boss nullification · boss safeguard bypass · P2W · dual Int/Dex primary · cross-class optimal item · focus bonus > 2 per segment · ritual-close bonus > 1 per Mark · untested PvP effects · cross-phase persistence · random full-resource waste · **mechanical set bonuses** (Q08 · DESIGN_LOCKED).

## 21. Anti-P2W

`can_be_sold_for_real_money = false` per combat item · progression item · ranking item · economy-impacting item. Potenza NON da acquisto real-money. Conflict → gameplay integrity wins.

## 22. Veste direction (Q06a)

- **Mechanical identity pillar**: `RITUAL_CHANNEL_PROTECTION`
- **Budget class**: `LEGENDARY_DEFENSIVE_RITUAL`
- Direzione autorizzata: protezione durante canalizzazione · stabilità rituale · resilienza tramite Costituzione · riduzione rischio durante Drain
- Vietato: invulnerabilità · immunità completa · assorbimento illimitato · annullamento totale interruzioni · persistenza cross-phase · superamento cap
- Effetto consumerà budget Legendary totale, NON aggiuntivo sopra 1.85
- Status: `DIRECTION_ONLY` · effect_final=null · effect_value=null · proc_chance=null · duration=null · cooldown=null

## 23. Occhio direction (Q06b)

- **Mechanical identity pillar**: `IDENTIFY_MARK_ORCHESTRATION`
- **Budget class**: `LEGENDARY_PRIMARY_CONTROL`
- Direzione autorizzata: migliore orchestrazione Identify→Mark · efficienza Drain · interazione condizionale Frammenti · leggibilità bersaglio prioritario
- Vietato: cap Frammenti > 5 · generazione Frammenti senza Marchio · focus bonus > 2 · Marchi attivi > 5 · durata > 10 · proc > 45% · boss safeguard bypass
- Focus resta arma primaria; la Legendary non deve rendere le altre famiglie inutilizzabili
- Status: `DIRECTION_ONLY` · effect_final=null · effect_value=null · proc_chance=null · duration=null · cooldown=null

## 24. Balestra direction (Q06c)

- **Mechanical identity pillar**: `RANGED_PRECISION_DISPEL`
- **Budget class**: `LEGENDARY_RANGED_UTILITY`
- Direzione autorizzata: precisione rituale a distanza · Marchio mirato · dissipazione selettiva · interazione anti-summon su bersagli validi
- Vietato: colpo garantito · precisione assoluta · eliminazione automatica evocazioni · nullificazione diretta boss · bypass immunità boss · trasformazione Dex-primary
- Anti-summon futuro solo su valid boss-summoned add con safeguard + condizione + budget
- Status: `DIRECTION_ONLY` · effect_final=null · effect_value=null · proc_chance=null · duration=null · cooldown=null

## 25. Set-bonus prohibition (Q08)

Mechanical set bonuses = **FORBIDDEN · DESIGN_LOCKED**. Non autorizzati: bonus 2/4/6 pezzi · effetto per equipaggiamento multiplo · set progression · set-exclusive proc. **Consentite** cohesive naming families senza collegamento meccanico / bonus cumulativo / requisito equipaggiamento congiunto.

## 26. Item-level numeric values still null

Tutti i campi numerici item-level restano `null`: `main_stat_value` · `weapon_coefficient_value` item-level · `base_budget` · `utility_budget` · `effect_budget` · `effect_value`. La chiusura Phase 1 non introduce alcun valore numerico item-by-item.

## 27. Item-level effects still null

Effetti finali di tutti gli item (inclusi i 3 Legendary): `effect_final = null`, `proc_chance = null`, `duration = null`, `cooldown = null`. Solo direzioni contract-level sono locked (Q06a-c).

## 28. Phase 2 remains HOLD

`R18.6.RV3-IS2-B Phase 2` = **HOLD / NOT AUTHORIZED**. La chiusura Phase 1 non autorizza automaticamente Phase 2. Phase 2 richiede autorizzazione PM esplicita successiva.

## 29. Registry generation disabled

`Registry_status` corpus 111 = `NOT_GENERATED`. Registry v3 Item Generation & Apply = `NOT_AUTHORIZED`. Zero Registry entry, zero apply, zero runtime item.

## 30. Governance evidence

| Voce | Valore |
|---|:---:|
| Sealed scripts | **36/36 byte-identical** |
| `lore_meta.py` SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` **INVARIATO** |
| Backend Python mods | **0** |
| Frontend mods | **0** |
| OpenAPI schema mods | **0** |
| DB writes / migrations | **0** |
| Registry v3 apply / item generation | **0** |
| Test suite additions/modifications | **0** |
| Nuovi sigilli | **0** |
| `.env` mods | **0** |
| Rev-4 MD/JSON modificati | **0** |
| Closure Phase 2 files modificati | **0** |
| Closure L1 files modificati | **0** |
| IS1 chain modificato | **0** |
| §31 self-hash embedded | **0 file** |

## 31. Explicit STOP

```
R18.6.RV3-IS2-B Phase 1                          = CLOSED / PM-LOCKED
R18.6.RV3-IS2-B Phase 2                          = HOLD / NOT AUTHORIZED
R18.6.RV3-NC1                                    = HOLD / NOT AUTHORIZED
R18.6 Gate 11                                    = HOLD / NOT AUTHORIZED
Registry v3 Item Generation & Apply              = NOT AUTHORIZED
Monaco                                           = HOLD / NOT AUTHORIZED
AFX2                                             = RESERVED FUTURE / NOT AUTHORIZED

IS2-A ramo (Phase 1, Phase 2 Rev-4, L1)          = LOCKED / IMMUTABLE
IS2-B Phase 1                                    = CLOSED / PM-LOCKED
Cacciatore del Vuoto                             = ACTIVE-DESIGN-READY (design layer only)

ATTENDO VERDICT PM.
```
