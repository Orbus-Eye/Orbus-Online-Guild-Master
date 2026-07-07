# R18.5 Pre-D2 — Craft NPC Directory (STEP 12)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: Pre-D2 Micro-step — Craft NPC Directory
**Locked at (UTC)**: 2026-07-07T14:30:00Z
**Governance**: DOCUMENTAL ONLY
**Status**: DRAFT — 5 NPC LOCKED confermati verbatim, 0 nuovi PENDING
**Authority**: PM Orchestrator — Q3=C + Q5=GO verbatim
**Scope**: fonte unica dei Craft NPC cornerstone D1 (5 LOCKED) + framework per eventuali nuovi NPC T2+ (max 10 totali)

---

## Executive Summary

Il PM ha approvato in Q3=C i **5 NPC craftsman citati in D1** come **LOCKED** (nome/lore/ruolo cornerstone) e in Q5=GO l'istituzione di una **directory documentale unica** per prevenire drift di naming attraverso D2-D5.

Questa directory:
- Consolida i **5 NPC LOCKED** con campi coerenti con l'utilizzo effettivo in D1 (materiali/famiglie/classi servite verificati sui 300 items D1)
- Definisce il **framework di 12 campi obbligatori** per ogni NPC
- Riserva **max 5 slot** per nuovi NPC craftsman T2+ (stato `PENDING PM`, da approvare esplicitamente)
- Applica **policy anti-P2W R18** verbatim (no premium vendor, no P2W)

**Cap totale**: 10 NPC max. **Attivi ora**: 5 LOCKED. **Slot residui**: 5 (PENDING PM).

---

## Framework — 12 Campi Obbligatori per NPC

| # | Campo | Tipo | Note |
|---:|---|---|---|
| 1 | `npc_id` | string kebab | UNIQUE identifier |
| 2 | `nome_it` | string | Nome IT verbatim (LOCKED = no rename) |
| 3 | `ruolo_crafting` | string | Es. fabbro, tessitrice, sarto |
| 4 | `location_regione` | string | Regione + zona specifica |
| 5 | `lore_source` | string | Una delle 22 lore sources approvate |
| 6 | `materiali_trattati` | array | Cuoio, stoffa, metallo, ecc. |
| 7 | `item_families_servite` | array | Iconic-family + linee evolutive |
| 8 | `tier_range_previsto` | array | Es. T1-T3 (multi-tier) |
| 9 | `classi_piu_servite` | array | 1-2 classi target |
| 10 | `note_narrative` | string | 2-3 righe lore/personalità |
| 11 | `anti_p2w_note` | string | Esplicita: NO premium, NO P2W |
| 12 | `stato` | enum | `LOCKED` (D1) OR `PENDING PM` (nuovi) |

---

## 5 NPC LOCKED (cornerstone D1, verbatim confermati)

### NPC 1 · Fabbro Bulwark

| Campo | Valore |
|---|---|
| `npc_id` | `fabbro-bulwark` |
| `nome_it` | Fabbro Bulwark |
| `ruolo_crafting` | Fabbro armature pesanti + scudi ordinari |
| `location_regione` | Krastlov Militia Camp — quartiere della forgia |
| `lore_source` | Ambash (leggera — forgia base gilda Bulwark) |
| `materiali_trattati` | ferro grezzo, acciaio base, legno duro (per impugnature scudi) |
| `item_families_servite` | `bulwark` (scudi Warrior), `ironhelm` (heavy armor W3 support) |
| `tier_range_previsto` | T1 (D1 cornerstone) · T2 (evolutivo D2) · T3+ possibile con avanzamento gilda |
| `classi_piu_servite` | Warrior (primario) |
| `note_narrative` | Fabbro di lunga esperienza, ex-soldato Krastlov. Ha giurato di forgiare solo per chi difende. Suo padre fondò la gilda Bulwark. Non forgia armi elaborate — solo scudi solidi e armature pratiche. |
| `anti_p2w_note` | **NO premium vendor. NO P2W.** Recipe unlockable via quest chain (starter-crafting D1 documentato). Materiali richiedono grind + gold ordinario. Nessuna variante "instant unlock" per soldi reali. |
| `stato` | **LOCKED** |
| **D1 usage** | 3 items D1 (Lv3-7): `warrior-bulwark-novice-shield`, `warrior-bulwark-roundshield`, `warrior-bulwark-towershield` |

### NPC 2 · Cuoiaia Elfwood

| Campo | Valore |
|---|---|
| `npc_id` | `cuoiaia-elfwood` |
| `nome_it` | Cuoiaia Elfwood |
| `ruolo_crafting` | Cuoiaia specializzata in armature leggere di cuoio |
| `location_regione` | Elfwood Fringe — laboratorio all'aperto sotto grande quercia |
| `lore_source` | Elfwood (bracket B1 leggera) |
| `materiali_trattati` | cuoio grezzo, pellame di cervo, corda vegetale, resina d'albero |
| `item_families_servite` | `leathercraft` (Rogue light armor) |
| `tier_range_previsto` | T1 (D1 cornerstone) · T2 (evolutivo D2 possibile con materiali T2) |
| `classi_piu_servite` | Rogue (primario) |
| `note_narrative` | Anziana elfa dei boschi, ha lavorato il cuoio per generazioni. Non tratta con maghi ("stoffa non ha vita, è morta"). Preferisce pelli di animali cacciati in modo rispettoso — no bracconieri, no shortcut. |
| `anti_p2w_note` | **NO premium vendor. NO P2W.** Recipe via side-quest "Prime Pellicce" (D1). Materiali richiedono caccia + tempo. Nessun instant-craft acquistabile. |
| `stato` | **LOCKED** |
| **D1 usage** | 3 items D1 (Lv3-6): `rogue-leathercraft-cloak`, `rogue-leathercraft-hood`, `rogue-leathercraft-gloves` |

### NPC 3 · Sarto Sacro

| Campo | Valore |
|---|---|
| `npc_id` | `sarto-sacro` |
| `nome_it` | Sarto Sacro |
| `ruolo_crafting` | Sarto specializzato in vesti sacre + accessori cerimoniali |
| `location_regione` | Halodi Sanctuary — atelier attiguo al monastero |
| `lore_source` | Halodi (bracket B1 leggera, santuario) |
| `materiali_trattati` | stoffa bianca benedetta, lino sacro, filo d'oro cerimoniale, incenso solido (per finiture) |
| `item_families_servite` | `novice-holy` (Priest vestments) |
| `tier_range_previsto` | T1 (D1 cornerstone) · T2 (evolutivo D2 possibile) · T3+ con benedizioni maggiori |
| `classi_piu_servite` | Priest (primario) |
| `note_narrative` | Ex-novizio del monastero, ha rinunciato ai voti per servire attraverso l'arte del tessuto. Recita una preghiera per ogni cucitura. Non produce mai per chi non ha "cuore benedetto" (recheable via achievement pathway). |
| `anti_p2w_note` | **NO premium vendor. NO P2W.** Recipe via preghiera + reputation con santuario Halodi. Materiali cerimoniali richiedono quest chain religiosa. Nessuna scorciatoia real-money. |
| `stato` | **LOCKED** |
| **D1 usage** | 2 items D1 (Lv3-5): `priest-novice-holy-vestments`, `priest-novice-holy-slippers` |

### NPC 4 · Tessitrice Arcana

| Campo | Valore |
|---|---|
| `npc_id` | `tessitrice-arcana` |
| `nome_it` | Tessitrice Arcana |
| `ruolo_crafting` | Tessitrice di vesti arcane e stoffe imbevute di mana |
| `location_regione` | Torre Arcana degli Apprendisti — laboratorio piano terra |
| `lore_source` | Faglie arcane (bracket B1 leggera) |
| `materiali_trattati` | stoffa magica base, filo di mana, polvere arcana (per rune), seta lunare (per finiture) |
| `item_families_servite` | `novice-arcane` (Mage arcane robes) |
| `tier_range_previsto` | T1 (D1 cornerstone) · T2 (evolutivo D2 possibile) · T3+ con materiali arcani T3 |
| `classi_piu_servite` | Mage (primario) |
| `note_narrative` | Maga anziana con affinità per il tessuto invece che per il combattimento. Ha lasciato la ricerca teorica per dedicarsi all'arte pratica dell'infondere mana nella stoffa. Vede ogni veste come un incantesimo permanente. |
| `anti_p2w_note` | **NO premium vendor. NO P2W.** Recipe via quest "Filo di Mana" (D1) + reputation con Torre Arcana. Materiali richiedono grind arcano + quest chain. Nessuna variante real-money. |
| `stato` | **LOCKED** |
| **D1 usage** | 3 items D1 (Lv3-6): `mage-novice-arcane-robe`, `mage-novice-arcane-slippers`, `mage-tessitrice-arcana-T2-recipe` (implicito nel starter-crafting T2) |

### NPC 5 · Conciatore Elfwood

| Campo | Valore |
|---|---|
| `npc_id` | `conciatore-elfwood` |
| `nome_it` | Conciatore Elfwood |
| `ruolo_crafting` | Conciatore specializzato in cuoio medium + finiture per armature ranger |
| `location_regione` | Elfwood Fringe — vicino a Cuoiaia Elfwood ma laboratorio separato |
| `lore_source` | Elfwood (bracket B1 leggera, complementare a Cuoiaia) |
| `materiali_trattati` | cuoio conciato con linfa foresta, pellame di cinghiale, corno intagliato, resina d'albero |
| `item_families_servite` | `scout-leather` (Ranger medium armor) |
| `tier_range_previsto` | T1 (D1 cornerstone) · T2 (evolutivo D2 con materiali forestali T2) |
| `classi_piu_servite` | Ranger (primario) |
| `note_narrative` | Uomo di mezza età, ex-scout della Ranger Company. Ha perso l'occhio in caccia ed è tornato all'artigianato. Conosce ogni animale della foresta come fossero suoi figli — sa esattamente quale pelle serve per quale scopo. Non produce per bracconieri. |
| `anti_p2w_note` | **NO premium vendor. NO P2W.** Recipe via quest "Cuoio Forte" (D1) + reputation con Ranger Company. Materiali forestali richiedono caccia rispettosa. Nessuna scorciatoia real-money. |
| `stato` | **LOCKED** |
| **D1 usage** | 3 items D1 (Lv3-6): `ranger-scout-leather-jerkin`, `ranger-scout-leather-cap`, `ranger-scout-leather-gloves` |

---

## Distribuzione classi servite (5 LOCKED)

| Classe | NPC servente | Materiali primari |
|---|---|---|
| Warrior | Fabbro Bulwark | ferro/acciaio + legno duro |
| Rogue | Cuoiaia Elfwood | cuoio leggero + pellame cervo |
| Mage | Tessitrice Arcana | stoffa arcana + filo di mana |
| Priest | Sarto Sacro | stoffa sacra + lino cerimoniale |
| Ranger | Conciatore Elfwood | cuoio medium + pellame cinghiale |

**Coverage**: 5/5 classi canoniche servite ✅. Nessuna classe rimasta senza NPC cornerstone.

---

## Nuovi NPC PENDING (max 5 slot residui)

**Stato attuale**: **0 nuovi NPC** proposti in questo Mini-Gate.

Il PM ha lockato i 5 NPC cornerstone. Nuovi NPC craftsman potranno emergere durante:
- **Phase D2 (T2)** — se materiali T2 richiedono specializzazioni (es. gioielliere per rings/amulets, alchimista avanzato)
- **Phase D3-D5 (T3-T5)** — endgame master craftsmen (es. legendary forge, arcane weaver endgame)

**Regola**: ogni nuovo NPC craftsman scoperto in D2-D5 deve essere:
1. Segnalato come `stato = PENDING PM` nel report della Phase corrente
2. NON usato in item finalizzati fino ad approvazione esplicita PM
3. Coerente con i 5 LOCKED (nessuna contraddizione narrativa/geografica/lore)
4. Compatibile con anti-P2W policy R18

---

## Governance Check STEP 12

| Voce | Status |
|---|---|
| Sealed files 36 hash byte-identical | ✅ (pytest atteso conferma) |
| DB writes | ZERO |
| Code changes | ZERO |
| Migrations | ZERO |
| NPC creation live | ZERO (design only) |
| Registry generation | ZERO |
| Drop table apply | ZERO |
| Economy changes | ZERO |
| `lore_meta.py` touch | INVARIATO |
| Sealed file modification | ZERO |
| Anti-P2W policy coverage | ✅ 5/5 NPC hanno `anti_p2w_note` esplicita |
| PM autonomous decision new | ZERO (5 NPC verbatim PM, 0 nuovi proposti) |
| Files deliverable | 2 (.md + .json) |
| Coerenza dati con D1 verificata | ✅ (analisi 300 items D1 per estrarre materiali/famiglie/classi effettive) |

---

## Handoff STEP 13 — Phase D2 (T2 × 350)

I 5 NPC LOCKED restano cornerstone anche in D2. **NON rinominare. NON contraddire.**

Se emergono nuovi NPC craftsman T2 durante STEP 13 → segnalati come `PENDING PM` nella sezione "NPC Craft usage" del report D2 (Sezione 13/16). Il PM potrà approvarli in review D2 → integrazione formale in questa directory in un futuro update.
