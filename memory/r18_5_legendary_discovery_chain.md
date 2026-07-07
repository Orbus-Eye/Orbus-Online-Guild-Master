# R18.5 Mini-Gate — Legendary Discovery Chain (STEP 8)

**Round**: R18.5 — Itemization, ILVL & Gear Progression Rework
**Phase**: Mini-Gate post-Batch 5 — Legendary Discovery Chain
**Locked at (UTC)**: 2026-07-07T11:15:00Z
**Governance**: DOCUMENTAL ONLY
**Status**: DRAFT (design layer only, no runtime effects)
**Authority**: PM Orchestrator — Q13=A verbatim + Q21 D→B verbatim
**Scope**: 7 Legendary candidate approvati Batch 5 — narrative discovery hook + design rationale (utility numeriche finali PENDING Phase D)

---

## Executive Summary

Il PM ha approvato **Q13=A** su 7 Legendary candidate (4 primari raid @ drop 2% + 3 secondari dungeon @ drop 1%). Questo Mini-Gate produce il **layer narrativo di scoperta** per ciascun Legendary — hook + reveal + giustificazione narrativa della rarità e delle policy anti-shop / anti-craft-normale. Le **utility numeriche finali** restano **PENDING PM** in Phase D. Nessuna item creation live, nessun DB write, nessun drop table apply.

**Regole PM strict verbatim rispettate**:
- ✅ solo T5
- ✅ max 15 in catalog (7 attivi, margine 8/15)
- ✅ utility unica + lore source forte
- ✅ NO Legendary generico +stat
- ✅ NO Legendary shop
- ✅ NO Legendary craft normale
- ✅ drop RARISSIMO 1-2% direzionale (2% primari raid boss finale · 1% secondari dungeon endgame)

---

## Discovery Chain — 4 Legendary Primari (drop 2% raid boss finale)

### L1 · `dragonlord-crown` (Draco · R1 `dragon-vault` LIVE)

- **Narrative hook**: Nelle vecchie cronache dei Krastlov si parla di una corona forgiata dall'ultimo re draconico caduto nell'Era della Fiamma, custodita nel cuore del Dragon Vault. Chi la porta non comanda i draghi con la forza, ma con la voce del sangue reale draconico.
- **Prima quest/reveal**: Un frammento della corona (item descrittivo, non funzionale) appare come reward guaranteed alla prima clear di `dragon-vault` — il frammento sblocca lore text che rivela l'esistenza dell'artefatto completo, ottenibile solo con drop rate 2% dal boss finale del raid.
- **Fonte**: R1 `dragon-vault` (LIVE, boss finale del raid)
- **Lore source**: **Draco** (macro-lore endgame R18.5, 6× cumulative approved Q9)
- **Utility fantasy proposta**: **Command Draconic** — attivazione limitata (1× per encounter) che permette di guidare temporaneamente un drago giovane ostile in un encounter draconico, trasformandolo in alleato per una fase.
- **Perché è raro (2%)**: L'artefatto è UNICO nella narrazione del mondo — la corona esiste in una sola forma. Il 2% drop rate rappresenta la difficoltà mitologica di "meritare" la corona, non un artificio matematico. Ogni giocatore che la ottiene ha una storia personale con Dragon Vault.
- **Perché non è craftabile normalmente**: Il forging della corona richiedeva sangue draconico reale, tecniche perdute e la benedizione di un drago-re. Nessun forgiatore vivente ha accesso a queste condizioni — di conseguenza è narrativamente impossibile ricrearla via crafting standard.
- **Perché non è shop / non P2W**: La corona è simbolo di legittimità draconica, non merce. Vendere la Command Draconic significherebbe rompere la coerenza narrativa del mondo (i draghi non obbedirebbero a chi la ha "comprata"). Anti-P2W policy R18: `can_be_sold_for_real_money = false` obbligatorio.
- **Drop source design-only**: 2% boss finale `dragon-vault` — NON runtime, NON applicato, NON DB entry. Design layer solo.

---

### L2 · `void-touched-blade` (Vuoto · R2 `void-cathedral` NEW DRAFT)

- **Narrative hook**: Nel Vuoto (la 17ª lore source approvata Q17) i confini della realtà si assottigliano. La Void-Touched Blade non è forgiata — è emersa. Alcuni sostengono sia la manifestazione fisica della Void Cathedral stessa, un frammento di realtà che ha assunto forma di lama.
- **Prima quest/reveal**: Il primo hint appare come "eco spettrale" durante l'exploration di `void-touched-outpost` (dungeon Lv56-57 B5) — un frammento di lama semi-materiale che scompare al tocco. La quest chain porta al Void Cathedral raid, dove la lama piena può manifestarsi con probabilità 2% al defeat del boss finale.
- **Fonte**: R2 `void-cathedral` (NEW DRAFT, boss finale del raid endgame)
- **Lore source**: **Vuoto** (17ª fonte approved Q17 Batch 5)
- **Utility fantasy proposta**: **Void-Pierce** — con probabilità % gli attacchi ignorano l'armor del target, come se la lama passasse "tra le realtà" invece che attraverso la difesa fisica.
- **Perché è raro (2%)**: Il Vuoto non "dona" — cede solo quando le condizioni cosmiche sono allineate. Il 2% rappresenta la sincronia rara tra il defeat del boss e la manifestazione del Vuoto stesso. Non è un premio, è un evento.
- **Perché non è craftabile normalmente**: Il Vuoto non è materia. Nessun forgiatore può "craftare" ciò che esiste per assenza. Ogni tentativo standard di forgiatura fallirebbe per definizione narrativa.
- **Perché non è shop / non P2W**: Vendere un frammento di Vuoto è concettualmente impossibile — non ha "valore in oro" perché non appartiene alla materia commerciabile. Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 2% boss finale `void-cathedral` — NON runtime.

---

### L3 · `seraph-halo-crown` (Celeste · R3 `celestial-conclave` NEW DRAFT)

- **Narrative hook**: Nel Celestial Conclave, i Serafini decaduti hanno lasciato le loro aureole prima di cadere. La Seraph Halo Crown non è indossata — è concessa quando il portatore mostra una forma di misericordia narrativamente riconosciuta durante l'encounter finale del raid.
- **Prima quest/reveal**: Durante `starforged-approach` (dungeon Lv57-58 B5) i giocatori incontrano un Serafino morente che offre una benedizione. La benedizione (item narrativo) diventa "chiave di reveal" per il Celestial Conclave — dove la corona può manifestarsi al 2% con condizione narrativa attiva.
- **Fonte**: R3 `celestial-conclave` (NEW DRAFT, boss finale)
- **Lore source**: **Celeste** (5× cumulative post-B5, bridge con `celestial-citadel-5p` Elite LIVE)
- **Utility fantasy proposta**: **Divine Resurrect** — 1× per encounter, resurrect di un fallen ally in un party endgame. Simbolizza la compassione dei Serafini caduti.
- **Perché è raro (2%)**: La corona richiede sia la vittoria SIA una condizione narrativa (misericordia dimostrata). Il 2% incorpora entrambi i requisiti, non è pura RNG.
- **Perché non è craftabile normalmente**: Le aureole seraphiche esistono solo in numero fisso (i Serafini caduti sono contati nella lore). Nessun forgiatore mortale può crearne di nuove — sarebbero false, non funzionanti narrativamente.
- **Perché non è shop / non P2W**: La misericordia non si compra. Vendere Divine Resurrect romperebbe la coerenza morale della lore Celeste (l'attivazione stessa richiede intenzione narrativa autentica). Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 2% boss finale `celestial-conclave` — NON runtime.

---

### L4 · `worldroot-scepter` (Alberi della Vita · R4 `world-tree-collapse` NEW DRAFT)

- **Narrative hook**: L'Albero della Vita centrale sta collassando (evento endgame R18.5). Prima del suo crollo definitivo, una singola radice si è cristallizzata in scettro — l'ultimo dono vivente della foresta prima della sua fine. Chi lo porta ha voce nella rigenerazione.
- **Prima quest/reveal**: Il primo hint arriva da un druido morente in un dungeon Lv58-59 (candidate B5) che parla della "voce delle radici che tacerà per sempre". La quest chain conduce al World Tree Collapse raid dove lo scettro può manifestarsi al 2%.
- **Fonte**: R4 `world-tree-collapse` (NEW DRAFT, boss finale del raid capstone)
- **Lore source**: **Alberi della Vita** (2× cumulative R18.5 — B2 raid + B5 raid capstone)
- **Utility fantasy proposta**: **Nature's Blessing** — AoE Heal-over-Time in aree naturali (definite narrativamente dal terrain lore). L'utility riflette la natura simbiotica del Legendary con l'ambiente.
- **Perché è raro (2%)**: Lo scettro è UNICO nella narrazione — deriva dall'ultima radice viva dell'Albero centrale. La rarità 2% rappresenta la difficoltà di essere presenti al momento esatto della cristallizzazione, non un puro drop.
- **Perché non è craftabile normalmente**: L'Albero della Vita centrale sta collassando — dopo il raid, non ci sarà più fonte per craftare uno scettro simile. Il forging è narrativamente impossibile perché la materia prima è finita.
- **Perché non è shop / non P2W**: Lo scettro è parte del ciclo naturale — non è merce. Vendere Nature's Blessing significherebbe commercializzare il residuo di una vita cosmica, contraria alla lore Alberi della Vita. Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 2% boss finale `world-tree-collapse` — NON runtime.

---

## Discovery Chain — 3 Legendary Secondari (drop 1% dungeon endgame)

### L5 · `ambash-forge-hammer` (Ambash · #6 `ambash-legendary-forge` Normal 3p B5)

- **Narrative hook**: La Ambash Forge è la fucina mitologica dove sono stati forgiati alcuni degli artefatti perduti dell'Era Ambash. Il Forge Hammer è lo strumento personale del Maestro Forgiatore caduto — non forgia, ma RE-forgia, permettendo di rimodellare l'arma di un compagno in mezzo alla battaglia.
- **Prima quest/reveal**: Il primo hint appare come "eco del martello" nei dungeon Lv54-55 (candidate B4 endgame preview). La quest chain porta al dungeon `ambash-legendary-forge` (B5) dove il martello può manifestarsi con drop 1% dal boss del dungeon.
- **Fonte**: #6 `ambash-legendary-forge` (Normal 3p B5, boss del dungeon)
- **Lore source**: **Ambash** (3× cumulative post-B5)
- **Utility fantasy proposta**: **Reforge weapon slot mid-encounter** — attivazione singola per encounter che permette al portatore di rimodellare temporaneamente la propria arma o quella di un alleato (es. cambio damage type / property).
- **Perché è raro (1%)**: Il martello è un artefatto personale — solo il legittimo erede spirituale del Maestro può farlo apparire. Il 1% riflette la rarità dell'allineamento narrativo, non pura RNG.
- **Perché non è craftabile normalmente**: Il forging del martello richiede la Ambash Forge originale, e usare la forgia per craftare il proprio "martello superiore" è un paradosso narrativo (serve il martello per aprire la forgia).
- **Perché non è shop / non P2W**: La reforge è arte, non commercio. Vendere Reforge weapon significherebbe svalutare l'unicità del Maestro. Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 1% boss finale `ambash-legendary-forge` — NON runtime.

---

### L6 · `dragon-elder-scale` (Draco · #8 `elder-wyrm-descent` Normal 3p B5)

- **Narrative hook**: Gli Elder Wyrm dell'Era Draconica portano cicatrici di battaglie millenarie sulla loro pelle. Una singola scala può, se strappata durante il defeat dell'Elder, mantenere l'essenza protettiva del drago originale.
- **Prima quest/reveal**: La conoscenza di questa scala arriva da un vecchio cacciatore di draghi (NPC narrativo) in un dungeon Lv57-58 (candidate B5). La quest chain conduce al `elder-wyrm-descent` dove la scala può essere ottenuta al defeat con drop 1%.
- **Fonte**: #8 `elder-wyrm-descent` (Normal 3p B5, boss finale del dungeon)
- **Lore source**: **Draco** (6× cumulative post-B5 — record, accepted Q9)
- **Utility fantasy proposta**: **Temporary Dragon-scale Armor Buff** — attivazione limitata che conferisce temporaneamente un armor buff con natura draconica (resistenza elementale + physical), durata definita in D-phase.
- **Perché è raro (1%)**: La scala mantiene l'essenza SOLO se strappata nell'istante esatto del defeat — momento narrativo raro e non replicabile ordinariamente. Il 1% riflette questa finestra temporale narrativa.
- **Perché non è craftabile normalmente**: Le scale draconiche standard vendute nel mercato sono "morte" — non hanno essenza. Solo quelle strappate al momento del defeat mantengono la potenza. Impossibile craftare una scala "viva" per definizione narrativa.
- **Perché non è shop / non P2W**: Vendere una scala viva richiederebbe farm continuo di Elder Wyrm, e ogni Elder Wyrm ha una sola scala viva. Il market crolla narrativamente. Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 1% boss finale `elder-wyrm-descent` — NON runtime.

---

### L7 · `sole-nero-diadem` (Celeste · #9 `pantheon-of-fallen-suns` Normal 3p B5 vetta Lv60)

- **Narrative hook**: Nel Pantheon of Fallen Suns riposano i "soli caduti" — le divinità solari-celesti che hanno perso la loro forma di luce diventando ombra. Il Sole Nero Diadem è la corona di uno di questi soli, cristallizzata nel momento della sua caduta: metà luce, metà void.
- **Prima quest/reveal**: Durante il tragitto Lv58-59 (candidate B5) i giocatori scoprono frammenti di "diadem cracks" (item narrativo) che accennano al Pantheon. La quest chain conduce al `pantheon-of-fallen-suns` (dungeon vetta Lv60) dove il diadem completo può manifestarsi al drop 1%.
- **Fonte**: #9 `pantheon-of-fallen-suns` (Normal 3p B5, dungeon vetta Lv60, boss finale)
- **Lore source**: **Celeste** (5× cumulative post-B5, capstone endgame narrativo)
- **Utility fantasy proposta**: **Swap light/void resist mid-encounter** — attivazione che permette di cambiare la propria resistenza tra light e void durante un encounter (utility strategica per boss con damage type mutevole).
- **Perché è raro (1%)**: Il diadem esiste solo nell'ultimo Sole Caduto — un singolo esemplare per boss narrativo. Il 1% rappresenta la difficoltà di ottenerlo integro (spesso si frantuma nel defeat).
- **Perché non è craftabile normalmente**: Nessun forgiatore mortale può bilanciare light e void nello stesso oggetto — richiede la natura duale intrinseca di un Sole Caduto. Craft standard = fallimento narrativo.
- **Perché non è shop / non P2W**: La dualità light/void è una qualità metafisica, non commerciabile. Vendere Swap light/void resist romperebbe il bilanciamento cosmico della lore Celeste. Anti-P2W: `can_be_sold_for_real_money = false`.
- **Drop source design-only**: 1% boss finale `pantheon-of-fallen-suns` — NON runtime.

---

## Riepilogo Design — Anti-P2W Policy R18 (coerenza cross-Legendary)

Per tutti i 7 Legendary candidate:

| Policy | Valore |
|---|---|
| `is_cosmetic` | false (hanno utility funzionale) |
| `affects_combat` | true (utility active narrativa) |
| `affects_economy` | false (non commerciabili) |
| `affects_ranking` | true (indirettamente, via encounter performance) |
| `is_tradeable` | false (bind-on-pickup) |
| `can_be_sold_for_gold` | false |
| `can_be_sold_for_real_money` | **false** (obbligatorio R18 anti-P2W) |
| `item_binding_policy` | Bind-on-Pickup |
| `drop_source_type` | design-only (non runtime, non applicato) |

**Nota Anti-P2W R18**: la policy `can_be_sold_for_real_money = false` è **obbligatoria** per tutti gli item che soddisfano `affects_combat = true OR affects_economy = true OR affects_ranking = true`. Tutti i 7 Legendary candidate ricadono in questa categoria e sono pertanto **non monetizzabili real-money by design**.

---

## Utility Numeriche Finali — PENDING PM (Phase D)

Le utility descritte in questo Mini-Gate sono **fantasy proposals**, non numeric finals. Le seguenti decisioni restano **PENDING PM** in Phase D:

- Valori numerici esatti di ogni utility (es. % armor ignore, HoT tick rate, ecc.)
- Cooldown effettivi (1× per encounter vs 1× per boss vs 1× per day)
- Interazioni con altri gear pieces
- Scaling con ILVL del portatore
- Sinergie di party con altri Legendary

**Governance**: nessuna utility numerica finale è stata decisa autonomamente in questo Mini-Gate. Tutto è narrative + design intent.

---

## Governance Check Mini-Gate Legendary Discovery Chain

| Voce | Status |
|---|---|
| Sealed files 36 hash byte-identical | ✅ (pytest verificato) |
| DB writes | ZERO |
| Code changes (`.py`/`.js`/`.jsx`/`.tsx`/`.ts`) | ZERO |
| Migrations | ZERO |
| Item creation live | ZERO |
| Drop table apply | ZERO |
| Economy changes | ZERO |
| `lore_meta.py` touch | INVARIATO |
| Sealed file modification | ZERO |
| Legendary runtime effects | ZERO |
| Legendary numeric utility finals | PENDING PM (Phase D) |
| Anti-P2W policy coherence | ✅ (7/7 items covered) |
| PM autonomous decision new | ZERO (tutti hook derivati da lore sources approvate) |
| Files deliverable | 2 (.md + .json) |

---

## Handoff STEP 9 — Phase D0 Item Table Blueprint

Post-Mini-Gate STEP 8, la sequenza autorizzata continua con **STEP 9 — R18.5 Phase D0 Item Table Schema + 1500 Distribution Blueprint**:

- Deliverable: `/app/memory/r18_5_phase_d0_item_table_blueprint.md/.json`
- Scope: 15 sezioni schema + blueprint distributivo 1500 item (NON catalogo completo)
- 7 Legendary Discovery Chain di questo file → integrati in D0 Sezione 11 (Legendary 7/15 candidate mapping)

**R18.5 status flow (aggiornato post STEP 8)**:
`... → C0-octies B5 CLOSED → Mini-Gate Legendary Discovery Chain (STEP 8) ✅ DRAFT → Phase D0 Item Table Blueprint (STEP 9) 🟡 AUTHORIZED chain → Phase D1-D5 item table drafting 🔒 pending D0`
