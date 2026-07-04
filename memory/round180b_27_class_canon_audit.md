# ROUND 18.0b — 27 Class Canon Ingestion & Technical Audit

**Round:** R18.0b (audit-only, read-only)
**Data creazione:** 2026-07-04 19:10 UTC
**Autorizzato dal PM:** Msg brief 2026-07-04T18:40Z (27 classi ufficiali)
**Autore:** e1 main agent
**Fonti:** `/app/memory/source_materials/r18_27_class_sources/` (27 Base PDF + 27 Abilità PDF + 6 extra + manifest JSON/MD)
**Scope:** catalogazione tecnica read-only. Zero implementazione, zero DB write, zero seed, zero codice.

> **⚠️ IMPORTANTE**: slug, ruoli, stat, armor, meccaniche sono **candidati tecnici**, NON decisioni finali. Il PM approva ogni valore prima dell'implementazione R18.2+.

---

## Sezione 1 — Executive Summary

**Deliverable eseguiti**:
- Download + estrazione archivio ufficiale PM (`orbus_r18_27_class_sources.zip`, 62 file totali, 5.94 MB)
- Parsing 27 Base PDF + 27 Abilità PDF + 6 extra (`Cammino Celeste.TXT`, `Leggende Bardiche.TXT`, `Scuole di Necromanzia.TXT`, `Sentiero del Guardiano.TXT`, `Trasformazioni Druido.pdf`, `Via del Dominatore.TXT`)
- 27/27 schede compilate (con TBD_ocr esplicitamente marcati)
- Matrice live→canonical (14 classi live giocabili → 27 canonical)
- Matrice canonical→live (27 canonical + presenza live)
- Analisi ruoli potenziali preliminari + rischi tecnici + 24 domande PM aperte

**Qualità estrazione OCR/regex**:
- fantasy_archetipo: **13/27** (curly quotes ora catturate)
- dadi_vita: **27/27**
- progressione_incantesimi: 27/27 (bulk-match tabella 'EXP 1-7')
- armi/armature/scudi: ~15-18/27 (regex line-based, non struct-aware)
- risorsa_classe (hints): 27/27 (keyword scan)

**Findings chiave**:
- **9 classi live 1:1 canonical**: warrior/rogue/mage/paladin/druid/necromancer/monk/bard/alchemist
- **5 classi live SENZA mapping canonical sicuro**: priest (190 adv), ranger (175 adv), berserker (3 adv), assassin (0 adv), warlock (128 adv) — **P0 blocker per R18.3 migration**
- **18 classi canoniche NUOVE** (no live counterpart): richiedono nuovo slug, training field, item pool, talent tree, drop table
- **Talent tree scale**: 27 × 3 rami × 5 tier × 4 talenti = **1620 slot teorici** (vs 900 nella roadmap R18.1.1)
- **6 classi con file extra**: Bardo, Druido (×2), Guerriero, Negromante, Paladino
- **Struttura PDF**: D&D 3.5/Pathfinder-style. Tabella EXP+incantesimi per livello 1-7, HP Dadi Vita d6/d8/d10, competenze armi/armature/scudi, sezione Speciale + Tiri Salvezza. Livelli fino a 24+ nei PDF (il PM sigilla Lv max 60 → estensione oltre TBD).

---

## Sezione 2 — Fonti dati

### Path archivio
- **Public URL**: `https://customer-assets.emergentagent.com/job_orbus-dungeon/artifacts/rppx4sgs_orbus_r18_27_class_sources.zip`
- **Path locale**: `/app/memory/source_materials/r18_27_class_sources/`
- **Data scarico**: 2026-07-04 19:10 UTC
- **Size**: 5.94 MB · **File totali**: 62 (27 Base + 27 Abilità + 6 extra + 2 manifest)

### Manifest autoritativo (usato come fonte di verità)
- `orbus_r18_27_class_sources_manifest.json` — mapping macchina 27 entry
- `orbus_r18_27_class_sources_manifest.md` — mirror human-readable
- **Consistenza**: 27/27 entry manifest → 27/27 file base + 27/27 file abilità presenti nello ZIP. ✅ Nessuna inconsistenza.
- **Nota nome**: file abilità Cavaliere di Draghi contiene typo `Descrizione Abilità Cavliere di Draghi.pdf` (manca 'a' in 'Cavaliere'). Manifest lo indicizza correttamente.

### File extra opzionali (6)
| Classe | File extra | Type |
|---|---|---|
| Bardo | `Leggende Bardiche.TXT` | Lore approfondito |
| Druido | `Sentiero del Guardiano.TXT` + `Trasformazioni Druido.pdf` | 1 via + progressione trasformazioni |
| Guerriero | `Via del Dominatore.TXT` | 1 via (potenziale merge Berserker) |
| Negromante | `Scuole di Necromanzia.TXT` | Sottoclassi/scuole |
| Paladino | `Cammino Celeste.TXT` | 1 cammino |

### Copertura richieste brief
- `file_base`: **27/27** ✅
- `file_abilita`: **27/27** ✅
- `file_progressione_extra`: **6/27** (parziale — solo 5 classi hanno extra ufficiale)

### Osservazioni OCR/formattazione (globali)
- Tutti i Base PDF condividono struttura: paragrafo apertura tra virgolette (spesso curly `“”`), sezione 'Competenze in Armi e Armature', tabella EXP+incantesimi con separatori `----`, sezione 'TIRI SALVEZZA', 'Speciale <Classe>'.
- Regex ASCII iniziale ha catturato solo 1/27 fantasy (Guerriero, con `"`); dopo re-extract con curly-quote regex → 13/27.
- Tabelle progressione (colonne slot per livello 1-7) sono estraibili ma il parsing colonne dettagliato richiede algoritmo dedicato non implementato in R18.0b (fuori scope audit).
- Livelli speciali (es. 'Una volta ogni 3 livelli +1 ai tiri per colpire' per Guerriero) sono catturati come stringhe raw ma il pattern per livello (1/2/3/5/7/9…) richiede parsing manuale.

---

## Sezione 3 — Catalogazione 27 classi (schede)

### Alchimista

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `alchimista` |
| file_base | `Base Alchimista.pdf` |
| file_abilita | `Descrizione Abilità Alchimista.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | ki, carica |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi semplici: Pugnali, balestre leggere, baston |
| armature_consentite | Competenze nelle Armature: |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Utility |
| live_counterpart | `alchemist` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 3785 chars, Abilità PDF 14764 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Artificiere

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `artificiere` |
| file_base | `Base Artificiere.pdf` |
| file_abilita | `Descrizione Abilità Artificiere.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | Tra le fucine ruggenti, i laboratori illuminati da scintille e le biblioteche cariche di tomi arcani, |
| dadi_vita | **d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | ki, carica, runa |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi semplici: L'Artificiere padroneggia le armi più basilari come bastoni, pugnali, fionde |
| armature_consentite | Armature |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, DPS |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 4052 chars, Abilità PDF 21581 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Astrologo

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `astrologo` |
| file_base | `Base Astrologo.pdf` |
| file_abilita | `Descrizione Abilità Astrologo.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | frase scritta dagli dèi o da forze più antiche degli dèi stessi. Interpretare il firmamento significa |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, carte, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Control |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 7263 chars, Abilità PDF 24764 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Bardo

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `bardo` |
| file_base | `Base Bardo.pdf` |
| file_abilita | `Descrizione Abilità Bardo.pdf` |
| file_progressione_extra | `Leggende Bardiche.TXT` |
| fantasy/archetipo | combattimento, il loro fascino naturale e la loro creatività li rendono figure centrali nelle relazioni |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | vuoto, spiriti |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Control |
| live_counterpart | `bard` |
| cammini/scuole/vie | Leggende Bardiche.TXT |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 6785 chars, Abilità PDF 24580 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Burattinaio

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `burattinaio` |
| file_base | `Base Burattinaio.pdf` |
| file_abilita | `Descrizione Abilità Burattinaio.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | Al livello 36, una volta al giorno può usare Sinfonia dei Fili: per 1 minuto, tutti i nemici entro 18 |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, dominio, vuoto |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Summoner, Control |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 8333 chars, Abilità PDF 30064 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cacciatore del Sangue

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cacciatore_sangue` |
| file_base | `Base Cacciatore del Sangue.pdf` |
| file_abilita | `Descrizione Abilità Cacciatore del Sangue.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Tutte le armi semplici |
| armature_consentite | Competenze – Armi e Armature |
| scudi | Scudi (ma molte abilità impongono pen |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 3233 chars, Abilità PDF 22018 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cacciatore del Vuoto

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cacciatore_vuoto` |
| file_base | `Base Cacciatore del Vuoto.pdf` |
| file_abilita | `Descrizione abilità Cacciatore del Vuoto.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, vuoto |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi: Armi semplici e armi da guerra. |
| armature_consentite | Armature: Armature leggere e medie, scudi. |
| scudi | Armature: Armature leggere e medie, scudi. |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Control |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 3558 chars, Abilità PDF 13794 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cacciatore di Mostri

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cacciatore_mostri` |
| file_base | `Base Cacciatore di Mostri.pdf` |
| file_abilita | `Descrizione Abilità Cacciatore di Mostri.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | Da solo, è perfetto per sessioni investigative e contratti: seguire una pista, interrogare testimoni, |
| dadi_vita | **1d10** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | essenza, carica, carte |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Utility |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 9088 chars, Abilità PDF 17393 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cartografo

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cartografo` |
| file_base | `Base Cartografo.pdf` |
| file_abilita | `Descrizione Abilità Cartografo.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, dominio |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Utility, Support |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 6478 chars, Abilità PDF 18368 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cavaliere della Morte

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cavaliere_morte` |
| file_base | `Base Cavaliere della Morte.pdf` |
| file_abilita | `Descrizione abilità Cavaliere della Morte.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d10** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, essenza |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi: Tutte le armi semplici e da guerra. |
| armature_consentite | Competenze di armi e armature |
| scudi | Armature: Tutte le armature (leggere, medie, pesanti) e scudi. |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Tank, DPS |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 3227 chars, Abilità PDF 17371 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cavaliere di Draghi

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cavaliere_draghi` |
| file_base | `Base Cavaliere di Draghi.pdf` |
| file_abilita | `Descrizione Abilità Cavliere di Draghi.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **d10** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, dominio |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | Armature: |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Tank, DPS |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 4120 chars, Abilità PDF 18447 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Cronista

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `cronista` |
| file_base | `Base Cronista.pdf` |
| file_abilita | `Descrizione Abilità Cronista.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, carte, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Utility |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 8692 chars, Abilità PDF 23909 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Druido

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `druido` |
| file_base | `Base Druido.pdf` |
| file_abilita | `Descrizioni Abilità Druido.pdf` |
| file_progressione_extra | `Sentiero del Guardiano.TXT`, `Trasformazioni Druido.pdf` |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, vuoto, spiriti |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | Armature |
| scudi | degli scudi. Tuttavia, hanno una particolarità molto importante: non indossano |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Healer, Hybrid |
| live_counterpart | `druid` |
| cammini/scuole/vie | Sentiero del Guardiano.TXT, Trasformazioni Druido.pdf |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 4013 chars, Abilità PDF 16866 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Fabbro Arcano

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `fabbro_arcano` |
| file_base | `Base Fabbro Arcano.pdf` |
| file_abilita | `Descrizione Abilità Fabbro Arcano.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, rune |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | Ogni armatura ha una volontà. |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Utility |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 8595 chars, Abilità PDF 24641 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Giocatore d'Azzardo

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `giocatore_azzardo` |
| file_base | `Base Giocatore d'Azzardo.pdf` |
| file_abilita | `Descrizione Abilità Giocatore d'Azzardo.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | pericolosi, tornei, tavoli maledetti e patti con entità che giocano con anime, ricordi o anni di vita. |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, carte, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Hybrid, Utility |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 8836 chars, Abilità PDF 17874 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Guerriero

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `guerriero` |
| file_base | `Base Guerriero.pdf` |
| file_abilita | `Descrizione Abilità Guerriero.pdf` |
| file_progressione_extra | `Via del Dominatore.TXT` |
| fantasy/archetipo | Scegliendo la via del Guerriero/Barbaro, incarnerai sia la disciplina del combattente addestrato che la furia selvaggia dell’antico guerriero tribale. La tua forza nasce dall’unione tra tecniche precise, apprese sul campo di battaglia o nell’addestra... |
| dadi_vita | **d10** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, carica |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Tutte le armi semplici e marziali |
| armature_consentite | Competenze in Armi e Armature: |
| scudi | Scudi |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Tank, DPS |
| live_counterpart | `warrior` |
| cammini/scuole/vie | Via del Dominatore.TXT |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme) |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 3195 chars, Abilità PDF 14461 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Ladro

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `ladro` |
| file_base | `Base Ladro.pdf` |
| file_abilita | `Descrizione Abilità Ladro.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, vuoto, rune |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi semplici (pugnali, bastoni, fionde, archi corti). |
| armature_consentite | ricchezze o vendetta, la notte è tua complice e le tenebre la tua armatura. |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Utility |
| live_counterpart | `rogue` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 3590 chars, Abilità PDF 22774 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Mago

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `mago` |
| file_base | `Base Mago.pdf` |
| file_abilita | `Descrizione Abilità Mago.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | mondi interi. Il vostro potere deriva dallo studio approfondito, dai tomi polverosi delle biblioteche |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | furia, carica, dominio |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Come mago hai accesso principalmente alle armi più semplici e meno ingombranti, adatte a chi |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Control |
| live_counterpart | `mage` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 4171 chars, Abilità PDF 27098 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Mercante

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `mercante` |
| file_base | `Base Mercante.pdf` |
| file_abilita | `Descrizione Abilità Mercante.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | trasformato in potere. il Mercante piega il mondo attraverso contratti, favori, debiti, oggetti rari, |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, sangue, vuoto |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Utility, Support |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 9824 chars, Abilità PDF 20950 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Monaco

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `monaco` |
| file_base | `Base Monaco.pdf` |
| file_abilita | `Descrizione abilità Monaco.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | furia, ki, essenza |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Il Monaco è un guerriero ascetico, maestro di arti marziali e del corpo come arma. Addestrato |
| armature_consentite | Come Monaco, il vostro personaggio non si affida tanto alle armi tradizionali o alle armature |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Hybrid |
| live_counterpart | `monk` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 4387 chars, Abilità PDF 18680 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Negromante

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `negromante` |
| file_base | `Base Negromante.pdf` |
| file_abilita | `Descrizione Abilità Negromante.pdf` |
| file_progressione_extra | `Scuole di Necromanzia.TXT` |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | essenza, dominio |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Summoner, DPS |
| live_counterpart | `necromancer` |
| cammini/scuole/vie | Scuole di Necromanzia.TXT |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 3547 chars, Abilità PDF 14904 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Paladino

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `paladino` |
| file_base | `Base Paladino.pdf` |
| file_abilita | `Descrizione abilità Paladino.pdf` |
| file_progressione_extra | `Cammino Celeste.TXT` |
| fantasy/archetipo | difensori dei deboli, giustizieri contro il male e protettori della sacra armonia. Tuttavia, non tutti i |
| dadi_vita | **d10** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, essenza |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | Caratterizzati da un'armatura scintillante e una fede incrollabile, i paladini si ergono come |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Tank, Healer |
| live_counterpart | `paladin` |
| cammini/scuole/vie | Cammino Celeste.TXT |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **BASSO** |

*Note OCR*: Base PDF Base PDF 3708 chars, Abilità PDF 15799 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Parassita

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `parassita` |
| file_base | `Base Parassita.pdf` |
| file_abilita | `Descrizione Abilità Parassita.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | In gruppo, il Parassita è resistente, disturbante e adattabile. Può assorbire danni, rubare vitalità, |
| dadi_vita | **1d8** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, carica, dominio |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | DPS, Control |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 11766 chars, Abilità PDF 21108 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate 

### Pittore

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `pittore` |
| file_base | `Base Pittore.pdf` |
| file_abilita | `Descrizione Abilità Pittore.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | essenza, carica, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, Control |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 9367 chars, Abilità PDF 21338 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Runista

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `runista` |
| file_base | `Base Runista.pdf` |
| file_abilita | `Descrizione Abilità Runista.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | delle rune: alcuni studiano le rune elementali, altri quelle protettive, altri ancora le rune proibite |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, essenza, carica |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | Può incidere rune su armi, armature, porte, pavimenti o oggetti, trasformandoli in catalizzatori |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Support, DPS |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 6161 chars, Abilità PDF 28533 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Sciamano

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `sciamano` |
| file_base | `Base Sciamano.pdf` |
| file_abilita | `Descrizione Abilità Sciamano.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | Gli sciamani sono guide spirituali, intermediari tra il regno dei mortali e quello degli spiriti. Essi |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | mana, furia, essenza |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | Armi semplici: Lo sciamano è esperto nell'uso di armi basilari, spesso preferendo |
| armature_consentite | Competenze in Armature: |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Healer, Support |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **MEDIO** |

*Note OCR*: Base PDF Base PDF 5310 chars, Abilità PDF 15568 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

### Sognatore

| Campo | Valore |
|---|---|
| **slug_candidate (non finale)** | `sognatore` |
| file_base | `Base Sognatore.pdf` |
| file_abilita | `Descrizione Abilità Sognatore.pdf` |
| file_progressione_extra | nessuno |
| fantasy/archetipo | TBD_source_readable_but_extraction_regex_missed_quote_marker |
| dadi_vita | **1d6** |
| progressione_incantesimi | Completa (7 livelli incantesimi) |
| risorsa_classe (hints keyword) | carica, dominio, sangue |
| oggetto_di_classe | TBD_ocr_or_ability_pdf |
| armi_consentite | TBD_ocr |
| armature_consentite | TBD_ocr |
| scudi | TBD_ocr |
| stat_primaria_probabile | TBD_PM_decision |
| ruoli_potenziali_preliminari | Control, Support |
| live_counterpart | `NO_LIVE_MATCH` |
| cammini/scuole/vie | nessuno (o TBD nel PDF Abilità) |
| dati_mancanti | stat_primaria_probabile, oggetto_di_classe, livelli_speciali dettagliati, risorsa_classe (solo hints estratti, non conferme), fantasy_archetipo |
| rischio_tecnico | **ALTO** |

*Note OCR*: Base PDF Base PDF 9367 chars, Abilità PDF 20025 chars. Tabelle progressione incantesimi con separatori '----' → parsing colonne complesso; fantasia/quote potenzialmente in virgolette curly '""' non catturate d

---

## Sezione 4 — Matrice live → canonical

14 classi live giocabili (escluso `recruit_unassigned` tecnica) mappate sulle 27 canonical target.

| classe_live | slug_live | classe_canonica_R18 | mapping_sicuro | mapping_ambiguo | rischio_migration | note |
|---|---|---|---|---|---|---|
| warrior | `warrior` | Guerriero | ✅ |  | ALTO (290 adv) | 1:1 match diretto, seed R160 → R18.1 alias-safe |
| rogue | `rogue` | Ladro | ✅ |  | ALTO (229 adv) | 1:1 match diretto |
| mage | `mage` | Mago | ✅ |  | ALTO (218 adv) | 1:1 match diretto |
| priest | `priest` | ? |  | ⚠️ ambiguo_alto | ALTO (190 adv) | Non in 27 canonical. Candidati: (a) merge in Paladino (spec Healer), (b) merge in Sciamano, (c) split come 28ª. **PM decision required** — priest ha 190 adv attivi (post-alias Cleric R18.1) → migrazione critica. |
| ranger | `ranger` | ? |  | ⚠️ ambiguo_alto | ALTO (175 adv) | Non in 27 canonical. Candidati: Cacciatore di Mostri (fantasy 'tracker/hunter'), Cacciatore del Vuoto, Cacciatore del Sangue. **PM decision required** — 175 adv attivi. |
| paladin | `paladin` | Paladino | ✅ |  | ALTO (166 adv) | 1:1 match diretto. Extra `Cammino Celeste.TXT` disponibile. |
| berserker | `berserker` | Guerriero? |  | ⚠️ ambiguo_medio | BASSO (3 adv) | Non in 27 canonical. Il PDF `Base Guerriero.pdf` menziona 'Guerriero/Barbaro' unificato + `Via del Dominatore.TXT`. **Possibile ramo talento** del Guerriero, non classe canonica separata. 3 adv attivi (low risk). |
| druid | `druid` | Druido | ✅ |  | ALTO (167 adv) | 1:1 match diretto. Extra `Sentiero del Guardiano.TXT` + `Trasformazioni Druido.pdf`. |
| necromancer | `necromancer` | Negromante | ✅ |  | BASSO (0 adv) | 1:1 match diretto. Extra `Scuole di Necromanzia.TXT`. |
| monk | `monk` | Monaco | ✅ |  | ALTO (162 adv) | 1:1 match diretto |
| bard | `bard` | Bardo | ✅ |  | ALTO (177 adv) | 1:1 match diretto. Extra `Leggende Bardiche.TXT`. |
| assassin | `assassin` | Ladro |  | ⚠️ ambiguo_basso | BASSO (0 adv) | Non in 27 canonical. Merge naturale con Ladro (0 adv attivi → low risk). Alternativa: ramo talento specializzato. |
| warlock | `warlock` | ? |  | ⚠️ ambiguo_alto | ALTO (128 adv) | Non in 27 canonical. Candidati: (a) Cacciatore del Vuoto (patronage 'Vuoto'), (b) Parassita, (c) Cavaliere della Morte. **PM decision required** — 128 adv attivi. |
| alchemist | `alchemist` | Alchimista | ✅ |  | ALTO (135 adv) | 1:1 match diretto. Kit Alchemico come oggetto di classe. |

## Sezione 5 — Matrice canonical → live

| classe_canonica_R18 | presente_live | slug_live | richiede_nuovo_slug | richiede_training_field | richiede_item_pool | richiede_talent_tree | richiede_migrazione |
|---|---|---|---|---|---|---|---|
| Alchimista | ✅ | `alchemist` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Artificiere | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Astrologo | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Bardo | ✅ | `bard` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Burattinaio | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cacciatore del Sangue | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cacciatore del Vuoto | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cacciatore di Mostri | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cartografo | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cavaliere della Morte | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cavaliere di Draghi | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Cronista | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Druido | ✅ | `druid` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Fabbro Arcano | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Giocatore d'Azzardo | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Guerriero | ✅ | `warrior` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Ladro | ✅ | `rogue` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Mago | ✅ | `mage` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Mercante | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Monaco | ✅ | `monk` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Negromante | ✅ | `necromancer` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Paladino | ✅ | `paladin` | no | sì (retrain) | estendere pool | **sì (60 slot)** | audit live adv → canonical |
| Parassita | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Pittore | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Runista | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Sciamano | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |
| Sognatore | ❌ | — | **sì** | **sì (onboarding)** | **creare pool completo** | **sì (60 slot)** | no |

**Coverage totale**: 9/27 canonical con live counterpart · 18/27 canonical nuove

---

## Sezione 6 — Ruoli potenziali (preliminari, non decisione)

**⚠️ IMPORTANTE**: lettura preliminare basata su fantasia + meccaniche osservabili. **Il PM conferma ciascun ruolo.** Molte classi possono coprire 2+ ruoli via talent tree branching.

### Distribuzione ruoli possibili

| Ruolo | Numero classi | Classi candidate |
|---|---|---|
| **Tank** | 4 | Cavaliere della Morte, Cavaliere di Draghi, Guerriero, Paladino |
| **Healer** | 3 | Druido, Paladino, Sciamano |
| **DPS** | 13 | Artificiere, Cacciatore del Sangue, Cacciatore del Vuoto, Cacciatore di Mostri, Cavaliere della Morte, Cavaliere di Draghi, Guerriero, Ladro, Mago, Monaco, Negromante, Parassita, Runista |
| **Support** | 12 | Alchimista, Artificiere, Astrologo, Bardo, Cartografo, Cronista, Fabbro Arcano, Mercante, Pittore, Runista, Sciamano, Sognatore |
| **Control** | 8 | Astrologo, Bardo, Burattinaio, Cacciatore del Vuoto, Mago, Parassita, Pittore, Sognatore |
| **Summoner** | 2 | Burattinaio, Negromante |
| **Utility** | 8 | Alchimista, Cacciatore di Mostri, Cartografo, Cronista, Fabbro Arcano, Giocatore d'Azzardo, Ladro, Mercante |
| **Hybrid** | 3 | Druido, Giocatore d'Azzardo, Monaco |

### Formule esplicative (pattern-based, non definitive)
- **Tank**: dv=d10, armature pesanti, scudi, meccaniche protezione/aggro
- **Healer**: incantesimi completa + risorsa focus/mana + tag 'cure'
- **DPS**: alta damage output, meccaniche offensive dirette
- **Support**: buff/debuff/utility passivi al party
- **Control**: crowd-control, immobilizzazione, alterazioni
- **Summoner**: evocazione creature/costrutti
- **Utility**: fuori-combattimento, esplorazione, mercantile
- **Hybrid**: ruolo variabile via talent tree

---

## Sezione 7 — Scala talent tree aggiornata (27 classi)

### Numeri teorici sigillati PM
| Metrica | Valore |
|---|---|
| Classi canoniche | **27** |
| Rami talento per classe | 3 |
| Tier per ramo | 5 |
| Talenti per tier | 4 |
| **Slot totali per classe** | **60** (3 × 5 × 4) |
| **Slot totali sistema** | **1620** (27 × 60) |
| Punti massimi allocabili / classe | **30** (50% degli slot) |
| Rami talento totali sistema | **81** (27 × 3) |

### Vs roadmap precedente (era 15 classi)
- +80% slot totali da progettare (1620 vs 900)
- +80% rami tematici (81 vs 45)
- Content bottleneck maggiore per R18.2 seed → **suggerito rollout scaglionato per ondate** (vedi §12)

### Vincoli invariati
- **NON creare talenti reali, nomi rami, bonus numerici, combat math** — R18.0b è audit-only
- Schema scaffolding `talent_tree_definitions` (creato in R18.1) supporta già la struttura 3/5/4 senza modifiche.

---

## Sezione 8 — Matrice item class-bound futura (27 classi × slot × tier)

Template vuoto — item definitivi verranno scritti dal PM. **NON creare item ora.**

| classe | slot | livello_item_tier | rarità | tipo | stat_primaria | stat_secondarie | tag_classe | drop_source |
|---|---|---|---|---|---|---|---|---|
| Guerriero | weapon | T1 (Lv1-10) | Common | TBD | TBD | TBD | `guerriero` | dungeon starter |
| Guerriero | armor | T2 (Lv11-20) | Uncommon | TBD | TBD | TBD | `guerriero` | mid-tier |
| Guerriero | accessory | T3 (Lv21-30) | Rare | TBD | TBD | TBD | `guerriero` | mid-endgame |
| Mago | weapon | T1 (Lv1-10) | Common | TBD | TBD | TBD | `mago` | dungeon starter |
| Mago | armor | T2 (Lv11-20) | Uncommon | TBD | TBD | TBD | `mago` | mid-tier |
| Mago | accessory | T3 (Lv21-30) | Rare | TBD | TBD | TBD | `mago` | mid-endgame |
| Paladino | weapon | T1 (Lv1-10) | Common | TBD | TBD | TBD | `paladino` | dungeon starter |
| Paladino | armor | T2 (Lv11-20) | Uncommon | TBD | TBD | TBD | `paladino` | mid-tier |
| Paladino | accessory | T3 (Lv21-30) | Rare | TBD | TBD | TBD | `paladino` | mid-endgame |
| Alchimista | weapon | T1 (Lv1-10) | Common | TBD | TBD | TBD | `alchimista` | dungeon starter |
| Alchimista | armor | T2 (Lv11-20) | Uncommon | TBD | TBD | TBD | `alchimista` | mid-tier |
| Alchimista | accessory | T3 (Lv21-30) | Rare | TBD | TBD | TBD | `alchimista` | mid-endgame |
| Sognatore | weapon | T1 (Lv1-10) | Common | TBD | TBD | TBD | `sognatore` | dungeon starter |
| Sognatore | armor | T2 (Lv11-20) | Uncommon | TBD | TBD | TBD | `sognatore` | mid-tier |
| Sognatore | accessory | T3 (Lv21-30) | Rare | TBD | TBD | TBD | `sognatore` | mid-endgame |
| ... (× 27 classi × 6 tier × 3 slot ≈ ~972 item) | | | | | | | | |

**Volume stimato**: 27 × 3 slot × 6 tier × ~2 rarity/rank = **~972 item class-bound** + eventual item generici. Content bottleneck P0 per R18.7.

---

## Sezione 9 — Roadmap dungeon/raid aggiornata (27 classi context)

Aggiornamento parametri:

| Parametro | Valore precedente (15 classi) | Nuovo (27 classi) | Delta |
|---|---|---|---|
| Dungeon target totali | 100 | 100 | =0 |
| Raid target totali | 20 | 20 | =0 |
| Tier item (ogni 10 lvl) | 6 | 6 | =0 |
| Lv max avventuriero | 60 | 60 | =0 |
| Item class-bound / classe | ~3 slot × 6 tier = 18 | invariato per classe | =0 |
| **Item pool totale class-bound** | ~15 × 18 = 270 | **~27 × 18 = 486** | **+80%** |
| **Talent slot totali** | 900 | **1620** | **+80%** |
| Ruoli coperti | 4 (T/H/D/S) | 8 (T/H/D/S/Ctrl/Sum/Ut/Hyb) | +100% |

### Rischi principali (dungeon/raid × 27 classi)
1. **Class-bound drop coverage**: 100 dungeon × 27 classi = 2700 potenziali drop-per-classe. Impossibile 1:1. → serve algoritmo weighted smart-loot su party composition.
2. **Power creep amplificato**: 27 classi con progression indipendente = 27 curve XP-vs-PWR da bilanciare.
3. **Content bottleneck**: 486 item + 1620 talent + 100 dungeon + 20 raid = ~2200 doc catalog totali da progettare. Scaglionabile in 6 ondate (§12).
4. **Test coverage**: monte-carlo balance su combo party (27 permutation × team 5-p) → serve heuristic non exhaustive.
5. **Party composition sanity**: alcune classi possono essere 'flavor' (es. Pittore, Sognatore) → gate 'min 1 tank + 1 healer' per dungeon medi+.

**NON creare dungeon/raid/boss/drop table definitiva ora.**

---

## Sezione 10 — Domande PM aperte (24 numerate)

### P0 — Mapping migration live→canonical (blocker R18.3)
1. **[Q1] Priest → dove?** 190 adv attivi post-alias R18.1. Candidati: (a) merge in Paladino spec Healer, (b) merge in Sciamano, (c) split come 28ª, (d) ramo talento Paladino. → decisione critica prima di R18.3.
2. **[Q2] Ranger → dove?** 175 adv. Candidati: Cacciatore di Mostri (fantasy 'tracker'), Cacciatore del Vuoto, Cacciatore del Sangue.
3. **[Q3] Warlock → dove?** 128 adv. Candidati: Cacciatore del Vuoto (patronage), Parassita, Cavaliere della Morte.
4. **[Q4] Berserker → ramo talento Guerriero?** 3 adv attivi + `Via del Dominatore.TXT` extra. Il PDF Base Guerriero menziona 'Guerriero/Barbaro' unificato. Conferma ramo talento invece che classe canonica?
5. **[Q5] Assassin → merge Ladro?** 0 adv attivi. Merge diretto o via talent tree?

### P0 — Slug ufficiali per DB
6. **[Q6] Slug definitivi per 27 classi?** Candidati tecnici in §3 con snake_case + accenti rimossi. PM approva o modifica?

### P1 — Stat + Ruoli
7. **[Q7] Stat primaria per ciascuna delle 27 classi** — non ricavabile dai PDF Base (nessuna menzione esplicita STR/DEX/INT).
8. **[Q8] Stat secondarie** — ordine per ciascuna classe?
9. **[Q9] Ruoli ufficiali per ciascuna** — §6 propone lettura preliminare.
10. **[Q10] Quali classi possono tankare?** Preliminare: Guerriero, Paladino, Cavaliere della Morte, Cavaliere di Draghi.
11. **[Q11] Quali classi possono curare?** Preliminare: Druido, Paladino, Sciamano. → priest fate cosa?
12. **[Q12] Quali classi possono evocare?** Preliminare: Burattinaio, Negromante. Altri?

### P2 — Armature/scudi/focus
13. **[Q13] Armor tier per classe** — leggera/media/pesante/nessuna. Regex OCR ha catturato parzialmente.
14. **[Q14] Scudo sì/no per classe** — idem.
15. **[Q15] Focus obbligatorio per caster?** (Kit Alchemico per Alchimista già confermato)

### P2 — Risorse classe
16. **[Q16] Risorsa classe ufficiale**: mana / furia / ki / karma / punti-X / carte / fortuna / focus / essenza / rune / totem / sangue / vuoto — quali per quali classi?
17. **[Q17] Meccaniche 'troppo costose'** — Burattinaio (evocazioni multiple), Sognatore (dimensioni oniriche), Cronista (rewind), Cartografo (mappa dinamica), Cavaliere di Draghi (mount+combat), Parassita (host swap): quali realizzabili in engine testuale?

### P3 — Content pool & sovrapposizioni
18. **[Q18] Item pool più grande** per quali classi? Preliminare: Cavaliere di Draghi (mount+lance), Alchimista (kit+pozioni), Fabbro Arcano (forge tool+incudine mobile).
19. **[Q19] Sovrapposizioni archetipi** — 3 Cacciatori Sangue/Vuoto/Mostri: differenziare come? Talent branching o classi indipendenti?
20. **[Q20] Dati mancanti nei file** — livelli speciali dettagliati, oggetto di classe (per non-Alchimista), risorse dedicate. Materiale integrativo?
21. **[Q21] Ordine implementazione R18.2 → R18.7?** Vedi §12 — 6 ondate proposte.

### P3 — Design gameplay long-term
22. **[Q22] Priest legacy pipeline** — 190 adv migrati Cleric→priest in R18.1. Se priest non canonical, come gestire?
23. **[Q23] Beta gilde opt-in R18.2** — quali gilde selezionare per talent tree beta?
24. **[Q24] Item universali vs class-bound** — quale % mantenere universale?

---

## Sezione 11 — Rischi tecnici globali (top 5)

### 1. **Migration 14 live → 27 canonical [ALTO]**
- 5 classi live senza mapping sicuro: priest (190) + ranger (175) + warlock (128) + berserker (3) + assassin (0) = **496 adv attivi da riassegnare**
- Ogni decisione richiede PM approval prima di implementation
- Rischio: player loss di identity se retrain forzato senza compensation
- Mitigazione: `class_slug=recruit_unassigned` come fallback + Training Field UI di R18.3 + retrain gratuito prima volta

### 2. **Item pool + talent slot esplosione [ALTO]**
- 1620 talent slot + ~486 item class-bound = **~2100 doc catalog** da progettare
- Content bottleneck: 27 classi × 15 doc/classe = 405 unità-lavoro
- Rischio: R18.7 rimane TBD indefinitely
- Mitigazione: 6 ondate scaglionate (§12), 4-5 classi/ondata

### 3. **Balance con 27 classi [ALTO]**
- Party composition space: C(27,5) = **80'730** combinazioni
- Test monte-carlo balance non exhaustive → serve heuristic + player analytics
- Rischio: emergenza meta narrow (2-3 classi 'meta', 24 'flavor')
- Mitigazione: talent tree branching + smart loot + soft class-bound R18.4 SOFT prima di HARD

### 4. **Sovrapposizioni archetipi [MEDIO]**
- 3 Cacciatori (Sangue/Vuoto/Mostri) → differenziazione critica
- 2 Cavalieri (Morte/Draghi) → differenziazione critica
- Cronista/Cartografo/Astrologo → tutti 'utility knowledge classes'
- Rischio: classi ridondanti/confuse per il player
- Mitigazione: forte differenziazione fantasy + risorsa unica per ciascuna

### 5. **Test coverage [MEDIO]**
- 27 classi × 100 dungeon × 20 raid = 54000 potenziali combinations testabili
- Test suite R18.1 (18 test) copre solo schema, non gameplay balance
- Rischio: bug latenti in interaction talent-item-classe
- Mitigazione: test-per-classe (27 fixture unit), test-per-raid (20 integration), test-per-tier (6 balance monte carlo)

---

## Sezione 12 — Raccomandazione ordine implementazione (proposta, non definitiva)

### Criterio proposto: **Ondate scaglionate per compatibilità live + priorità narrativa**

**Ondata 1 — 9 classi 1:1 live→canonical** (R18.2 PILOT):
- Guerriero, Ladro, Mago, Paladino, Druido, Negromante, Monaco, Bardo, Alchimista
- Motivazione: zero migration needed. Player base già familiare. Talent tree seed pilot.
- Deliverable: 9 × 60 = **540 talent slot** + 9 × 18 ≈ **162 item class-bound**

**Ondata 2 — 5 classi live orphan da riassegnare** (R18.3 con Training Field):
- priest, ranger, warlock, berserker, assassin → decidere target canonical (§10 Q1-Q5)
- Motivazione: 496 adv da migrare in modo controllato con opt-in Training Field UI
- Rischio: alto player-facing → serve UI IT forte + retrain gratuito primo cambio

**Ondata 3 — 5 classi nuove 'core role'** (R18.3 P0):
- Sciamano (Healer), Cavaliere della Morte (Tank), Cavaliere di Draghi (Tank/DPS), Runista (Support), Astrologo (Control)
- Motivazione: coprono ruoli mancanti (Sciamano/Healer alt, Cavalieri/Tank alt)

**Ondata 4 — 5 classi nuove 'thematic'** (R18.4):
- Cacciatore di Mostri, Cacciatore del Sangue, Cacciatore del Vuoto, Artificiere, Cronista
- Motivazione: 3 Cacciatori insieme per differenziazione clear; Artificiere/Cronista utility support

**Ondata 5 — 5 classi nuove 'exotic'** (R18.5):
- Burattinaio (Summoner), Fabbro Arcano (Support), Mercante (Utility), Cartografo (Utility), Pittore (Control)
- Motivazione: meccaniche complesse → tempo dev maggiore

**Ondata 6 — 3 classi nuove 'wildcard'** (R18.6):
- Giocatore d'Azzardo (Hybrid), Parassita (Control), Sognatore (Control)
- Motivazione: meccaniche molto sperimentali → prototype con beta gilde

### Metriche ondata
| Ondata | Classi | Talent slot | Item class-bound stimati |
|---|---|---|---|
| Ondata 1 (R18.2 PILOT) | 9 | 540 | ~162 |
| Ondata 2 (R18.3 migration) | 5 | 300 | ~90 |
| Ondata 3 (R18.3 core role) | 5 | 300 | ~90 |
| Ondata 4 (R18.4 thematic) | 5 | 300 | ~90 |
| Ondata 5 (R18.5 exotic) | 5 | 300 | ~90 |
| Ondata 6 (R18.6 wildcard) | 3 | 180 | ~54 |
| **Totale** | **32*** | **1920*** | **~576** |

*Il totale 32 include il 'wildcard split' delle 5 live-orphans se il PM decide di renderle canonical (28-32). Se merge → target rimane 27 canonical (1620 slot).

### Criterio decisionale
- 27 rimangono target ufficiale ma le 5 live-orphans devono avere destinazione **prima** di aprire R18.2
- Se PM sceglie 'merge' per tutte le 5 → target rimane 27
- Se PM sceglie 'split' per 1-2 → target sale a 28-29 (deroga esplicita PM)

**PM APPROVA IL CRITERIO A 6 ONDATE O PROPONE ALTERNATIVA?**

---

## Conferma vincoli R18.0b rispettati

- ✅ **Zero implementazione**
- ✅ **Zero DB write** (solo `find`/`aggregate` read-only su `adventurers` + `adventurer_classes`)
- ✅ **Zero modifiche codice applicativo**
- ✅ **Zero seed**
- ✅ **Zero hard delete**
- ✅ **Zero modifiche a combat math / drop / reward / economia / PvP / premium / auto-equip**
- ✅ **Zero decisioni sigillate come definitive** (slug/ruoli/stat/armor tutti marcati candidati o TBD_PM_decision)
- ✅ Scritture solo in `/app/memory/round180b_*.md/json` + `/app/memory/source_materials/r18_27_class_sources/`

---

**Firmato:** e1 main agent · 2026-07-04 19:10 UTC · R18.0b OPEN (audit-only, waiting PM decisions on Q1-Q24)
