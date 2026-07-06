# R18.5 Phase C0 — PM Item Table Drafting Support (DOCUMENTAL ONLY)

> **⚠️ SUPERSEDED (scope catalogo reale)** — 2026-07-06T19:00:00Z
> Questo file resta valido come **micro-sample / skeleton** (80 item, max 4 Legendary), ma **NON è più il cap del catalogo reale**. Il catalogo reale R18.5 è definito in `r18_5_phase_c0bis_progression_dungeon_raid_matrix.md/.json`: **1500 equip minimo, max 15 Legendary, 60 dungeon, 12 raid, proficiency system obbligatorio**. I 13 draft di questo file restano come esempi non autoritativi.

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Fase**: **C0** (pre-C tech) — supporto documentale al drafting PM della tabella item batch primo lotto
- **Locked at UTC**: `2026-07-06T18:00:00Z`
- **Governance**: DOCUMENTAL ONLY — zero DB writes, zero code changes, zero migration, zero registry definitivo. 36 sigilli byte-identical.
- **Predecessori**: `r18_5_phase_b1_design_lock.md/.json` (patched), `r18_5_phase_b2_implementation_plan.md/.json` (patched), `r18_5_phase_b_gate1_pm_decisions.md/.json` (authoritative)
- **Successore**: Phase C tech dry-run — **BLOCCATO** finché PM non compila/approva la tabella item qui sotto.

## 0. Scope Phase C0

Preparare una **tabella item leggibile, compilabile in-place dal PM**, che diventerà la fonte unica per il futuro dry-run tecnico e successivo seed. Emergent qui **NON finalizza**: fornisce **schema + skeleton vuoto + max 15 esempi propositivi come stimolo** (tutti flaggati `PENDING PM approval / DRAFT ONLY / NOT FINAL`).

### Cosa Emergent PUÒ fare in C0
- Definire lo schema tabella (i 14 campi PM-defined).
- Fornire skeleton vuoto di 80 righe distribuite T1=24 / T2=20 / T3=20 / T4=12 / T5=4 (allineato a SQ14).
- Proporre 10-15 draft esempi come stimolo creativo per il PM (**flag PENDING PM approval su ognuno**).
- Elencare campi PENDING PM per ogni draft (tutto ciò che non è deterministico dalle regole PM SQ).

### Cosa Emergent NON PUÒ fare in C0
- Finalizzare nomi player-facing.
- Finalizzare stat numerici.
- Finalizzare utility narrative.
- Finalizzare drop source / drop rate.
- Finalizzare classi consigliate.
- Finalizzare signature / legendary.
- Auto-approvare bilanciamento.
- Superare **15 draft esempi** (deve essere stimolo, non tabella finale).
- Superare **4 Legendary** nel draft (Gate 1 SQ14 lock).

## 1. Schema tabella item — 14 campi PM-defined

| # | Campo | Tipo | Descrizione | Vincoli / esempio |
|---|---|---|---|---|
| 1 | **ID** | slug tecnico | id univoco backend | `lama_faglia_quieta` — solo `[a-z0-9_]`, lowercase |
| 2 | **Nome IT** | stringa | nome player-facing | `Lama della Faglia Quieta` — italiano lore-consistent |
| 3 | **Lore source** | enum \| null | fonte narrativa | `Ambash` per T3+, `null` per T1/T2 generic |
| 4 | **Rarity** | enum | rarità player-facing | Common / Uncommon / Rare / Epic / Legendary |
| 5 | **Tier** | enum | tier tecnico | T1 / T2 / T3 / T4 / T5 (mapping Gate 1 SQ12) |
| 6 | **Required level** | int 1-60 | livello min. per equip | Gate 1 correction: max 60 |
| 7 | **ILVL** | int 1-60 | item level | Range vincolato tier (SQ18): T1=1-15, T2=16-30, T3=31-45, T4=46-55, T5=56-60 |
| 8 | **Slot** | enum | slot equip | weapon / helm / chest / legs / accessory / shield |
| 9 | **Tipo** | enum | tipo entità | spada / bastone / ascia / elmo / anello / amuleto / ecc. |
| 10 | **Stat** | dict | stat numerici | `{str: 5, agi: 3, int: 0, end: 2, faith: 0}` |
| 11 | **Utility** | stringa \| null | effetto narrativo lore-linked | Obbligatoria T3+, `null` per T1/T2 |
| 12 | **Classi consigliate** | list | class_slug compatibili | `[warrior, paladin]` (lowercase, canonical class_slug attuale) |
| 13 | **Binding** | enum | policy binding | universal / soft / hard / signature |
| 14 | **Fonte** | enum | acquisition | drop / craft / dungeon / boss / achievement |

### Esempio VALIDO (Rare, T3, lore-linked)
```
ID              lama_faglia_quieta
Nome IT         Lama della Faglia Quieta
Lore source     Ambash
Rarity          Rare
Tier            T3
Required level  35
ILVL            38
Slot            weapon
Tipo            spada
Stat            {str: 8, agi: 4, int: 0, end: 2, faith: 0}
Utility         Riduce del 10% il rischio di evento arcano instabile nei dungeon magici
Classi consigl. [warrior, paladin, cacciatore_di_mostri]
Binding         soft
Fonte           dungeon (Cripta delle Faglie di Ambash — early tier)
```

### Esempio INVALIDO (rifiutato — solo +stat, no lore, no utility)
```
ID              spada_epica_forza
Nome IT         Spada Epica di Forza
Lore source     null
Rarity          Epic
Tier            T4
Required level  48
ILVL            50
Slot            weapon
Tipo            spada
Stat            {str: 15}
Utility         null   ← ❌ T4 senza utility narrativa lore-linked
Classi consigl. [warrior]
Binding         soft
Fonte           drop
```
Motivo rifiuto: item T3+ senza `lore_source` + senza `utility` → viola Gate 1 lore-driven rule.

## 2. Skeleton tabella vuota compilabile in-place dal PM (80 righe)

### Legenda status
- 🟢 = draft Emergent (10-15 max, tutti `PENDING PM approval / DRAFT ONLY`)
- ⬜ = riga vuota, **da compilare dal PM**

### T1 — Common (24 righe, ILVL 1-15, Required lvl 1-10)

| # | ID | Nome IT | Slot | Tipo | ILVL | Req.lv | Stat | Bind | Status |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `spada_arrugginita` | Spada Arrugginita | weapon | spada | 3 | 1 | `{str:2}` | universal | 🟢 DRAFT PENDING PM |
| 2 | `armatura_cuoio_grezzo` | Armatura di Cuoio Grezzo | armor | armor_light | 5 | 2 | `{end:2, agi:1}` | universal | 🟢 DRAFT PENDING PM |
| 3 | `anello_rame` | Anello di Rame | accessory | ring | 4 | 1 | `{end:1}` | universal | 🟢 DRAFT PENDING PM |
| 4 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| 5 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ⬜ PM |
| 24 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |

*(righe 4-24: da compilare dal PM. Emergent ha lasciato solo 3 draft come stimolo per T1 — no lore source richiesta a T1)*

### T2 — Uncommon (20 righe, ILVL 16-30, Required lvl 10-20)

| # | ID | Nome IT | Slot | Tipo | ILVL | Req.lv | Stat | Bind | Status |
|---|---|---|---|---|---|---|---|---|---|
| 25 | `arco_cacciatore` | Arco del Cacciatore | weapon | bow | 20 | 12 | `{agi:5, str:2}` | soft | 🟢 DRAFT PENDING PM |
| 26 | `mantello_boscaiolo` | Mantello del Boscaiolo | armor | armor_medium | 22 | 14 | `{end:3, agi:3}` | universal | 🟢 DRAFT PENDING PM |
| 27 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| 28 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ⬜ PM |
| 44 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |

*(righe 27-44: da compilare dal PM. Emergent ha lasciato solo 2 draft T2 come stimolo — lore source opzionale a T2)*

### T3 — Rare (20 righe, ILVL 31-45, Required lvl 20-35) — **LORE SOURCE + UTILITY OBBLIGATORI**

| # | ID | Nome IT | Slot | Tipo | ILVL | Req.lv | Stat | Lore | Utility | Bind | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 45 | `lama_faglia_quieta` | Lama della Faglia Quieta | weapon | spada | 38 | 30 | `{str:8, agi:4}` | Ambash | Riduce del 10% il rischio di evento arcano instabile nei dungeon magici | soft | 🟢 DRAFT PENDING PM |
| 46 | `mantello_alba_silente` | Mantello dell'Alba Silente | armor | robe | 40 | 32 | `{int:6, faith:4}` | Alevora | Cura 5 HP all'inizio di ogni scontro nei dungeon della Luna Morta | soft | 🟢 DRAFT PENDING PM |
| 47 | `talismano_ergolat` | Talismano di Ergolat | accessory | amulet | 35 | 25 | `{end:5, int:3}` | Ergolat | Aumenta del 5% la resistenza contro creature della Faglia | universal | 🟢 DRAFT PENDING PM |
| 48 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ⬜ PM |
| 64 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |

*(righe 48-64: da compilare dal PM. Emergent ha lasciato 3 draft T3 come stimolo — tutti con lore source Gate 1 approved)*

### T4 — Epic (12 righe, ILVL 46-55, Required lvl 35-50) — **LORE + UTILITY OBBLIGATORI**

| # | ID | Nome IT | Slot | Tipo | ILVL | Req.lv | Stat | Lore | Utility | Bind | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 65 | `elmo_krastlov` | Elmo di Krastlov | helm | armor_heavy | 50 | 42 | `{end:12, str:6}` | Krastlov | Ignora la prima ferita critica di ogni scontro (1x/dungeon) | soft | 🟢 DRAFT PENDING PM |
| 66 | `arco_vento_halodi` | Arco del Vento di Halodi | weapon | bow | 52 | 45 | `{agi:14, str:5}` | Halodi | +15% probabilità di colpo critico in dungeon aperti | soft | 🟢 DRAFT PENDING PM |
| 67 | `stivali_soe` | Stivali di Soe | legs | armor_medium | 48 | 38 | `{agi:10, end:6}` | Soe | Riduce la fatica accumulata dopo il combattimento del 20% | universal | 🟢 DRAFT PENDING PM |
| 68 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ⬜ PM |
| 76 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |

*(righe 68-76: da compilare dal PM. Emergent ha lasciato 3 draft T4 come stimolo)*

### T5 — Legendary (4 righe, ILVL 56-60, Required lvl 50-60) — **LORE + UTILITY OBBLIGATORI, HARD CAP 4**

| # | ID | Nome IT | Slot | Tipo | ILVL | Req.lv | Stat | Lore | Utility | Bind | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 77 | `lama_vuoto_ambash` | Lama del Vuoto di Ambash | weapon | spada | 60 | 55 | `{str:20, agi:8, int:6}` | Ambash | Una volta a dungeon: dissolve l'affisso più pericoloso del boss finale | signature | 🟢 DRAFT PENDING PM |
| 78 | `corona_luna_morta` | Corona della Luna Morta | helm | armor_heavy | 58 | 52 | `{int:15, faith:12, end:8}` | Luna Morta | Immunità agli effetti di "silenzio arcano". Vede sempre il boss in eventi con nebbia | signature | 🟢 DRAFT PENDING PM |
| 79 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |
| 80 | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ PM |

**⚠️ HARD CAP Legendary = 4** (Gate 1 SQ14). Emergent ha lasciato **2 draft T5** come stimolo, restano **2 slot Legendary** da compilare dal PM.

## 3. Draft count summary

| Tier | Draft Emergent | Skeleton empty per PM | Total righe |
|---|---:|---:|---:|
| T1 | 3 | 21 | 24 |
| T2 | 2 | 18 | 20 |
| T3 | 3 | 17 | 20 |
| T4 | 3 | 9 | 12 |
| T5 | 2 | 2 | 4 |
| **Total** | **13** ✅ | **67** | **80** |

- Draft Emergent totali: **13** ≤ **15** (rispetta cap C0 rule).
- Legendary draft: **2** ≤ **4** (rispetta Gate 1 SQ14).
- Ogni item T3+ nei draft ha `lore_source` + `utility` (rispetta lore-driven rule).
- **Ogni draft flaggato `🟢 DRAFT PENDING PM`**.

## 4. Campi PENDING PM per ogni draft (checklist)

Per ognuno dei 13 draft, il PM deve rivedere e approvare/modificare:

| Campo | Deterministico dalle regole | PENDING PM |
|---|---|---|
| ID (slug) | Sì (pattern lowercase snake_case) | opzionale rename |
| Nome IT | **NO** | ✅ PENDING |
| Lore source | Range da list Gate 1 | ✅ scelta specifica PENDING |
| Rarity | Sì (accoppiata a tier) | — |
| Tier | Sì (accoppiata a rarity) | — |
| Required level | Range da tier | ✅ valore esatto PENDING |
| ILVL | Range da tier (SQ18) | ✅ valore esatto PENDING |
| Slot | Enum | ✅ scelta PENDING |
| Tipo | Enum (subset family taxonomy B.1) | ✅ scelta PENDING |
| Stat | Range da tier budget (SQ18-related) | ✅ numeri esatti PENDING |
| Utility | **NO** | ✅ full text PENDING |
| Classi consigliate | Compatibili con family | ✅ lista finale PENDING |
| Binding | Enum universal/soft/hard/signature | ✅ scelta PENDING |
| Fonte | Enum drop/craft/dungeon/boss | ✅ scelta PENDING |

## 5. Regole tassative Phase C0 (non delegabili al builder)

- ❌ Emergent NON finalizza nomi player-facing.
- ❌ Emergent NON finalizza stat numeriche.
- ❌ Emergent NON finalizza utility narrative.
- ❌ Emergent NON finalizza drop source / drop rate.
- ❌ Emergent NON finalizza classi consigliate.
- ❌ Emergent NON finalizza signature.
- ❌ Emergent NON finalizza legendary.
- ❌ Emergent NON forza "GO auto-approve" su nulla.
- ✅ Ogni item nel draft è flaggato `PENDING PM approval / DRAFT ONLY / NOT FINAL`.
- ✅ Legendary count ≤ 4.
- ✅ Ogni item T3+ ha `lore_source` da lista Gate 1 approvata.
- ✅ Ogni item T3+ ha `utility` narrativa lore-linked.
- ✅ Draft count totale ≤ 15.

## 6. Cosa succede dopo Phase C0

Il PM può:
1. **Approvare i 13 draft** as-is (raro, di solito verranno modificati).
2. **Modificare i draft** (rename, ritoccare stat, riscrivere utility, cambiare classi).
3. **Compilare le 67 righe vuote** con nuovi item.
4. **Rifiutare draft** e sostituirli.
5. **Ridurre / espandere** il batch (con giustificazione, ma cap hard 80 senza nuovo gate).

Una volta la tabella C0 è **compilata e approvata dal PM**, si potrà aprire **Phase C tech** (dry-run scripts backfill + validation). Non prima.

## 7. Self-check Phase C0

- [x] Schema 14 campi PM-defined completo
- [x] Esempio VALIDO fornito (`lama_faglia_quieta`)
- [x] Esempio INVALIDO fornito con motivazione rifiuto
- [x] Skeleton 80 righe distribuite T1=24 / T2=20 / T3=20 / T4=12 / T5=4 (SQ14)
- [x] Draft Emergent totali: 13 ≤ 15 (cap C0)
- [x] Legendary draft: 2 ≤ 4 (Gate 1 SQ14 hard cap)
- [x] Ogni item T3+ nei draft ha `lore_source` da lista Gate 1
- [x] Ogni item T3+ nei draft ha `utility` narrativa
- [x] Ogni draft flaggato `PENDING PM approval / DRAFT ONLY`
- [x] Checklist campi PENDING PM per draft
- [x] Regole tassative Emergent esplicitate
- [x] Zero DB writes / Zero code changes / Zero migration

**Phase C0 CLOSED (deliverable pronto)**. Attesa **compilazione + approvazione PM tabella item**.

## 8. Note per il PM

- Puoi editare **direttamente in questo file** o esportare la tabella in un tool esterno e reimportarla.
- Se cambi la distribuzione T1/T2/T3/T4/T5, apri un nuovo gate (il cap 80/24/20/20/12/4 è Gate 1 lock).
- Se aggiungi Legendary oltre 4, apri un nuovo gate (hard cap SQ14).
- Se aggiungi item T3+ senza lore source o senza utility, verranno automaticamente flaggati come non conformi da Phase C tech.
- Le classi consigliate usano `class_slug` attuale (canonical dopo R18.3f quando sbloccato — R18.5 seed migrable).
