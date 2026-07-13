# R18.6.RV3-IS2-A-L1 · Legendary Candidate Selection · Closure Report

**Gate**: `R18.6.RV3-IS2-A-L1 · Legendary Candidate Selection`
**Regime**: DOCUMENTAL ONLY · READ-ONLY (backend/frontend/OpenAPI/DB/Registry INVARIATI)
**Stato**: **CLOSED / PM-LOCKED**
**Baseline di riferimento**: `r18_6_rv3_is2_a_phase2_full_identity_naming_lore_roster_rev4.md/.json` (PM_LOCKED)
**Timestamp closure L1**: 2026-07-13T10:10:35Z
**Lingua**: Italiano
**Continuità**: IS1 CLOSED · IS2-A Phase 1 CLOSED · IS2-A Phase 2 CLOSED/PM-LOCKED · IS2-A-L1 CLEAN RESUME

---

## 1. PM recovery verdict

Il PM ha ratificato il diagnostic post Bad-Gateway con verdetto **CLEAN RESUME AUTORIZZATO**. Il filesystem risultava byte-identical alla baseline post-Phase-2 (nessun artefatto parziale, nessun PRD append parziale, nessun commit orfano, sigilli 36/36 byte-identical, `lore_meta.py` INVARIANT). Rollback NOT REQUIRED · Targeted repair NOT REQUIRED · Clean restart SAFE. Il precedente errore di trasporto è classificato come `execution interruption with filesystem impact = none` e non genera lineage nel presente report.

## 2. Clean-resume classification

L'esecuzione IS2-A-L1 è ripartita **ex-novo** dalla baseline post-Phase-2. Nessun tentativo di recupero di file inesistenti. Nessun lineage fittizio. Contenuti deterministici e riproducibili. §31 rispettato (no self-hash embedded). Nessuna modifica a backend/frontend/OpenAPI/DB/Registry/test/env/sigilli. Cacciatore del Vuoto = ACTIVE-DESIGN-READY (design layer only).

## 3. IS2-A-L1 CLOSED

- Gate status: **CLOSED / PM-LOCKED**.
- Autorizzazione all'apertura successiva di altri Gate: **NO**.
- L'esito L1 **non abilita** IS2-B, NC1, Gate 11, Registry v3, Monaco, AFX2.
- Legendary selection su tier diversi da T5 pilot: **NOT AUTHORIZED** (fuori scope L1 attuale).

## 4. Three Legendary packages

Sono coinvolti esattamente 3 pacchetti Legendary tier-5 per la classe Cacciatore del Vuoto, uno per ciascuno dei 3 slot Legendary previsti dal roster Rev-4:

1. `cdv_t5_chest_stoffa_002` — slot `chest`, subtype `stoffa`
2. `cdv_t5_main_hand_focus_001` — slot `main_hand`, subtype `focus`
3. `cdv_t5_main_hand_balestra_001` — slot `main_hand`, subtype `balestra`

Totale Legendary packages = **3**.

## 5. Nine candidates reviewed (elenco esplicito ABC per blueprint)

Il roster Rev-4 offre 3 candidate strings (A/B/C) per ciascuno dei 3 pacchetti, per un totale di **9 candidate strings reviewed**. I 6 candidati NOT_SELECTED restano preservati come `AUDIT_REFERENCE_ONLY` — non eliminati, non rinominati, non promossi.

### 5.a · `cdv_t5_chest_stoffa_002`
- **A** — «Sudario del Faro Rovesciato»
- **B** — «Manto della Grande Canalizzazione»
- **C** — «Veste di Onirade»

### 5.b · `cdv_t5_main_hand_focus_001`
- **A** — «Occhio del Faro Rovesciato»
- **B** — «Focus dell'Assenza profonda»
- **C** — «Voce di Onirade»

### 5.c · `cdv_t5_main_hand_balestra_001`
- **A** — «Scatto dei Frammenti»
- **B** — «Balestra della Traiettoria certa»
- **C** — «Voce dei Bersagli assenti»

## 6. Three PM selections

Le 3 stringhe ratificate dal PM (design_status = `DESIGN_LOCKED`, selection_status = `PM_SELECTED`):

| Blueprint | PM_SELECTED | display_name_it |
|---|:---:|---|
| `cdv_t5_chest_stoffa_002` | **C** | «Veste di Onirade» |
| `cdv_t5_main_hand_focus_001` | **A** | «Occhio del Faro Rovesciato» |
| `cdv_t5_main_hand_balestra_001` | **B** | «Balestra della Traiettoria certa» |

## 7. Six non-selected alternatives (motivi PM verbatim)

### 7.a · Chest `cdv_t5_chest_stoffa_002`
- **A NOT_SELECTED — «Sudario del Faro Rovesciato»**: «sfumatura funebre non necessaria / possibile deriva Negromante / leggibilità chest inferiore».
- **B NOT_SELECTED — «Manto della Grande Canalizzazione»**: «interpretabile come slot back / identità meno distintiva / costruzione descrittiva».

### 7.b · Focus `cdv_t5_main_hand_focus_001`
- **B NOT_SELECTED — «Focus dell'Assenza profonda»**: «head noun tecnico e generico / minore Legendary signature weapon».
- **C NOT_SELECTED — «Voce di Onirade»**: «troppo astratto per arma primaria / minore leggibilità come focus».

### 7.c · Balestra `cdv_t5_main_hand_balestra_001`
- **A NOT_SELECTED — «Scatto dei Frammenti»**: «più leggibile come azione che oggetto / identità balestra meno immediata».
- **C NOT_SELECTED — «Voce dei Bersagli assenti»**: «troppo astratto / leggibilità arma inferiore».

Totale non-selected alternatives = **6** (tutti in stato `AUDIT_REFERENCE_ONLY`).

## 8. Rationale chest — «Veste di Onirade»

Razionale PM verbatim: **slot readability forte · stoffa identity forte · Legendary identity forte · canonical lore connection chiara · linguistic naturalness alta**.

## 9. Rationale focus — «Occhio del Faro Rovesciato»

Razionale PM verbatim: **focus identity forte · class signature forte · Faro identity coerente · memorizzabilità alta · weapon-family conflict assente · coerente con loop Identify→Mark→Drain→Payoff senza promettere meccanica**.

## 10. Rationale balestra — «Balestra della Traiettoria certa»

Razionale PM verbatim: **weapon readability massima · balestra identity esplicita · ranged ritual identity coerente · precision theme forte · class overlap assente · «certa» = tono narrativo, non garanzia meccanica**.

## 11. Slot-semantic validation

Verifica read-only che i 3 nomi PM_SELECTED siano semanticamente coerenti con il loro slot:

- «Veste di Onirade» · head-noun `Veste` · slot `chest` → coerente (armor identity, no back/head/hand overlap).
- «Occhio del Faro Rovesciato» · head-noun `Occhio` · slot `main_hand` subtype `focus` → coerente (focus identity metaforico, no bare-weapon-name conflict).
- «Balestra della Traiettoria certa» · head-noun `Balestra` · slot `main_hand` subtype `balestra` → coerente (weapon-family esplicito).

**Slot-semantic violations = 0**.

## 12. Weapon-family validation

Verifica read-only che il naming non introduca conflict tra weapon-family:

- `Balestra` compare 1 volta come head-noun, esclusivamente nel blueprint balestra dedicato. Nessun altro nome del corpus attivo (108 non-Leg + 3 PM-selected Leg) usa `Balestra` come head-noun al di fuori di questo blueprint.
- `Occhio` come head-noun di un focus → nessun overlap con weapon-family concreta (arco, spada, ecc.).
- `Veste` come head-noun di un chest → nessun overlap con weapon-family.

**Weapon-family violations = 0**.

## 13. Vocabulary validation

Verifica dei vocabolari:

- Forbidden vocabulary: nessun token vietato tra i 3 nomi PM_SELECTED (verificato contro la forbidden vocabulary list Phase 1 ereditata da IS1-SEALED).
- Restricted vocabulary uso post-L1:
  - «Onirade» → 1 occorrenza attiva nel corpus 111 (in «Veste di Onirade»). Conforme al cap CLASS_SPECIFIC 1x.
  - «Faro Rovesciato» → 1 occorrenza attiva nel corpus 111 (in «Occhio del Faro Rovesciato»). Conforme al cap CLASS_SPECIFIC 1x.

**Forbidden vocabulary violations = 0**.
**Restricted vocabulary violations = 0**.

## 14. Restricted-term validation

Uso dei termini restricted dopo la selezione:

| Termine | Occorrenze corpus attivo post-L1 | Identity | Rarity | PM Review | Conforme |
|---|:---:|---|---|:---:|:---:|
| «Onirade» | **1** (in «Veste di Onirade») | CLASS_SPECIFIC | Legendary | ✅ Completed | ✅ |
| «Faro Rovesciato» | **1** (in «Occhio del Faro Rovesciato») | CLASS_SPECIFIC | Legendary | ✅ Completed | ✅ |

**Nota audit metodologica**: le occorrenze grezze di grep su Rev-4 MD (`Onirade` = 18 · `Faro Rovesciato` = 17) includono tabelle di conteggio vocabolario, alternative NOT_SELECTED (`Voce di Onirade`, `Sudario del Faro Rovesciato`, ecc.), agent_recommendation ed entry di roster metadata — **fuori dal corpus attivo 111 post-selezione**. Il corpus attivo comprende esclusivamente i 108 nomi non-Legendary selected + i 3 nomi Legendary PM-selected. In quel corpus, ciascun termine restricted appare esattamente 1 volta.

## 15. Lexical-cap validation

- Cap per-slot head-noun: rispettato in ogni slot Rev-4 post-selezione (la selezione L1 non introduce nuove clusterizzazioni head-noun ≥3 in singolo slot).
- Cap globale head-noun: invariato rispetto a Rev-4 PM_LOCKED — la selezione ha ridotto lo spazio candidati (117 → 111) ma non ha alterato distribuzione head-noun tra slot.
- exact duplicate = **0** · normalized duplicate = **0** sui 111 nomi attivi.

**Lexical-cap violations = 0**.

## 16. Mechanic-promise validation

Verifica che nessuno dei 3 nomi PM_SELECTED prometta meccanica specifica al giocatore:

- «Veste di Onirade»: puramente identity/lore, nessuna meccanica implicata.
- «Occhio del Faro Rovesciato»: identity Legendary, «Occhio» = evocativo (percezione/marchio), non promessa di meccanica quantificabile. Coerente con loop Identify→Mark→Drain→Payoff **senza esplicitare parametri**.
- «Balestra della Traiettoria certa»: «certa» = tono narrativo/aspirazionale, non garanzia di hit-guarantee, crit deterministico o accuracy quantificata.

**Mechanic-promise violations = 0**.

## 17. Stat-promise validation

Nessuno dei 3 nomi PM_SELECTED contiene numeri, valori percentuali, riferimenti a caratteristiche numeriche o buff quantificati.

**Stat-promise violations = 0**.

## 18. Selected-name accounting

Post-L1, il corpus dei nomi attivi selezionati è così composto:

| Categoria | Conteggio |
|---|---:|
| Non-Legendary selected draft names (invariato da Rev-4) | **108** |
| Legendary PM-selected names (nuovo post-L1) | **3** |
| **Total active new design names** | **111** |

Confronto con il pre-L1 candidate corpus:
- Pre-L1: 108 non-Leg + 9 Legendary candidate = **117 candidate strings**
- Post-L1: 108 non-Leg + 3 PM-selected Leg = **111 active selected new-name strings**
- Delta: 6 alternative Legendary passano a `NOT_SELECTED` (archiviate come `AUDIT_REFERENCE_ONLY`, non attive).

## 19. Preserved identity accounting

Le 9 identità Preserved da IS1 restano byte-identical rispetto a IS1-SEALED. L'evento L1 **non modifica** in alcun modo le identità preservate.

- Preserved identity rows: **9**
- IS1 chain identity locks: `IS1-SEALED` invariato.

## 20. Contingency exclusion

I 3 slot contingency dormant restano dormienti anche post-L1. La selezione Legendary L1 riguarda esclusivamente i 3 pacchetti Legendary attivi, **non** i contingency dormant.

- Dormant contingency packages: **3**
- Generated names from dormant contingency: **0**

## 21. Runtime disabled

**Nessun item generato in runtime.** La selezione L1 è puramente di identity/naming design:

- runtime_status per i 3 nomi PM_SELECTED: `NOT_IMPLEMENTED`
- localization_status per i 3 nomi PM_SELECTED: `NOT_IMPLEMENTED`
- Nessuna scrittura DB, nessuna migration.
- Vietato scrivere: "item live" · "record DB" · "Registry entry" · "runtime localization".

## 22. Registry disabled

- Registry_status per i 3 nomi PM_SELECTED: `NOT_GENERATED`.
- apply_status: `false`.
- Registry v3 Item Generation & Apply: `NOT_AUTHORIZED` (rimane fuori scope).

## 23. Governance evidence

| Voce | Valore |
|---|:---:|
| Sealed scripts | **36/36 byte-identical** (`pytest backend/tests/backend_r18_4_sealed_integrity_test.py` → 6 passed) |
| `lore_meta.py` SHA | `a18f708b043e1dccf4910a3ab61b7520b16dba5db742c48b1f7ea67f60965b8f` **INVARIATO** |
| Backend Python mods | **0** |
| Frontend mods | **0** |
| OpenAPI schema mods | **0** |
| DB writes / migrations | **0** |
| Registry v3 apply / item generation | **0** |
| Test suite additions/modifications | **0** |
| Nuovi sigilli | **0** |
| `.env` mods | **0** |
| Modifiche a Rev-4 MD/JSON | **0** (baseline PM_LOCKED invariata) |
| Modifiche a closure Phase 2 files | **0** (PM_LOCKED invariati) |
| Modifiche a IS1 chain | **0** |
| Modifiche a IS2-A Phase 1 files | **0** |
| §31 self-hash embedded | **0 file** (chat-only disclosure per manifest L1 + PRD) |

## 24. Explicit STOP

```
R18.6.RV3-IS2-A-L1 Legendary Candidate Selection = CLOSED / PM-LOCKED
R18.6.RV3-IS2-B (Stat Budget & Mechanical Effect) = HOLD / NOT AUTHORIZED
R18.6.RV3-NC1 (Null Conflict Remediation Planning) = HOLD / NOT AUTHORIZED
R18.6 Gate 11                                     = HOLD / NOT AUTHORIZED
Registry v3 Item Generation & Apply               = NOT AUTHORIZED
Monaco                                            = HOLD / NOT AUTHORIZED
AFX2                                              = RESERVED FUTURE / NOT AUTHORIZED

Cacciatore del Vuoto = ACTIVE-DESIGN-READY (design layer only).

ATTENDO VERDICT PM.
```
