# FASE 8A — Rebalance difficoltà dungeon (audit, simulazioni, nuova curva)
Data: 2026-08-08 · Branch: Lavoro-partito-08/08/2026 · Baseline: f1d5996

## 1. Diagnosi: perché una squadra Lv15 farmava dungeon Lv40

Misure dal codice reale (non stime):
- Stat iniziali: somma base di classe ≈32 + jitter medio → **~34**.
- Level-up: **+1 stat**/livello (`_resolve_levelup`) → potere base
  membro = somma_stat + livello×2 ≈ **33 + 3·L** (Lv15: 78, Lv40: 153).
- Item (catalogo T6): power_score = rarità + L//20; bonus primario =
  rarità + min(4, L//20); secondario da Rare in su. **10 slot fisici.**
- Bonus ruoli squadra: fino a +25.

Il potere reale cresce quindi soprattutto con l'**equipaggiamento**
(10 slot × item), non col livello. La vecchia curva `recommended_power`
(es. Lv15→333, Lv40→560) cresceva molto più piano del potere reale:
una squadra Lv15 "media" (~535 di team power col vecchio equip medio)
aveva rating 96% sul dungeon Lv40 (560) → ~43-84% di chance a seconda
dell'equip, e il gate al 60% (336) non la fermava mai. Con la vecchia
k=4.4 la zona utile della logistica era anche troppo morbida.

## 2. Il modello formale (`app/shared/power_model.py`)

4 fasce simulate (slot riempiti × rarità prevalente, funzione del Lv):
sottopotenziata / **media** / ben_equipaggiata / molto_forte.

**Nuova curva** = parità con la squadra MEDIA di pari livello:
`recommended_power(L, size) = size × member_power(L, media) + 25`.

### Potere squadra (5 membri) per livello × fascia
| Lv | sottopotenziata | media | ben equip. | molto forte |
|---|---|---|---|---|
| 10 | 370 | 390 | 540 | 790 |
| 15 | 455 | **535** | 615 | 865 |
| 20 | 570 | 670 | 1040 | 1040 |
| 30 | 740 | 850 | 1190 | 1540 |
| 40 | 940 | **1350** | 1490 | 1840 |
| 50 | 1120 | 1570 | 1990 | 1990 |
| 60 | 1370 | 2240 | 2240 | 2240 |
| 70 | 1520 | 2390 | 2390 | 2840 |
| 80 | 1790 | 2640 | 2640 | 3140 |

(Nota: ad alcuni livelli le fasce convergono — la rarità prevalente
coincide quando l'epic diventa il tetto pratico sotto il legendary.
Artefatto del modello, ininfluente sull'accettazione.)

## 3. Nuove costanti

| Parametro | Prima | Dopo |
|---|---|---|
| `POWER_GATE_RATIO` | 0.60 | **0.70** |
| `SUCCESS_CURVE_K` | 4.4 | **5.5** |
| Punti curva | R75→25 · R125→75 · R150→90 | **R75→20 · R125→80 · R150→94** |
| `GUARANTEED_SUCCESS_RATING` | 200 | 200 (invariato) |
| Overpower | ×1.5/×2/×2.5/×3 a R125/150/175/200 | invariato |

## 4. Curva recommended_power: prima → dopo (gate = 70% del nuovo)

| Dungeon | Lv | Size | Rec prima | Rec dopo | × | Gate prima | Gate dopo |
|---|---|---|---|---|---|---|---|
| training-yard* | 1 | 3 | 15 | 90 | 6.00 | 9 | 63 |
| sewer-nest* | 1 | 3 | 35 | 110 | 3.14 | 21 | 77 |
| goblin-warrens | 5 | 5 | 117 | 315 | 2.69 | 70 | 221 |
| bandit-hideout | 5 | 3 | 75 | 200 | 2.67 | 45 | 140 |
| druid-grove** | 10 | 5 | 267 | 400 | 1.50 | 160 | 280 |
| shadow-crypts** | 10 | 5 | 283 | 425 | 1.50 | 169 | 298 |
| wolf-den-5p | 10 | 5 | 260 | 390 | 1.50 | 156 | 273 |
| cursed-mines | 15 | 5 | 333 | 535 | 1.61 | 199 | 375 |
| sunken-library | 15 | 3 | 215 | 330 | 1.53 | 129 | 231 |
| frost-cave-5p | 15 | 5 | 310 | 535 | 1.73 | 186 | 375 |
| lich-sanctum | 20 | 5 | 408 | 670 | 1.64 | 244 | 469 |
| salt-marsh-5p | 20 | 5 | 360 | 670 | 1.86 | 216 | 469 |
| dragons-hoard | 25 | 7 | 642 | 1075 | 1.67 | 385 | 753 |
| storm-spire | 25 | 5 | 483 | 775 | 1.60 | 289 | 543 |
| iron-foundry-5p | 25 | 5 | 410 | 775 | 1.89 | 246 | 543 |
| silent-monastery-5p | 30 | 5 | 460 | 850 | 1.85 | 276 | 595 |
| pirate-fleet-5p | 35 | 5 | 510 | 1100 | 2.16 | 306 | 770 |
| obsidian-arena-5p | 40 | 5 | 560 | 1350 | 2.41 | 336 | 945 |
| clockwork-vault-5p | 45 | 5 | 610 | 1425 | 2.34 | 366 | 998 |
| voidspire-5p | 50 | 5 | 660 | 1570 | 2.38 | 396 | 1099 |
| infernal-pit-5p | 60 | 5 | 760 | 2240 | 2.95 | 456 | 1568 |
| celestial-citadel-5p | 65 | 5 | 810 | 2315 | 2.86 | 486 | 1621 |
| world-tree-roots-5p | 70 | 7 | 1600 | 3335 | 2.08 | 960 | 2335 |

\* Tutorial: valori AUTORATI sotto il modello (il modello assume slot
equip che una gilda day-1 non ha; una squadra fresca ~120 di potere ha
87% su training-yard e ~62% su sewer-nest: tutorial giocabile).
\*\* Alzati al vincolo minimo ×1.5 (il modello puro dava ×1.4).

**Vincolo +50% (verificato da test)**: il gate d'ingresso cresce
≥×1.5 per OGNI dungeon (min ×1.62); il rec cresce ×1.5–×3.0; la chance
di una stessa squadra crolla (es. Lv15 media su cursed-mines: 96%→50%;
su obsidian-arena Lv40: da farmabile a BLOCCATA).

## 5. Raid (per la FASE 8B — gate PWR)

| Raid | Lv | Roster | Rec prima | Rec dopo | × |
|---|---|---|---|---|---|
| moonfall-vigil | 40 | 10 | 1500 | 3100 | 2.07 |
| broken-bastion-siege | 60 | 15 | 2400 | 7700 | 3.21 |
| necropolis-bells | 70 | 20 | 3500 | 10925 | 3.12 |
| dragon-vault | 80 | 40 | 8000 | 24100 | 3.01 |

Formula: roster × membro_medio(L) × **1.15** (severità raid) + 50.

## 6. Matrice squadra × dungeon (fascia MEDIA, curva e gate nuovi)

`rating% → chance` · BLOCK = sotto il PWR gate (70%)

| SqLv \ DgLv | 10 | 15 | 20 | 30 | 40 | 50 | 60 | 70 | 80 |
|---|---|---|---|---|---|---|---|---|---|
| 10 | **50%** | 18% | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| 15 | 88% | **50%** | 25% | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| 20 | 98% | 80% | **50%** | 24% | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| 30 | 100% | 96% | 82% | **50%** | BLOCK | BLOCK | BLOCK | BLOCK | BLOCK |
| 40 | 100% | 100% | 100% | 96% | **50%** | 32% | BLOCK | BLOCK | BLOCK |
| 50 | 100% | 100% | 100% | 99% | 71% | **50%** | 16% | BLOCK | BLOCK |
| 60 | 100% | 100% | 100% | 100% | 97% | 91% | **50%** | 42% | 30% |
| 70 | 100% | 100% | 100% | 100% | 99% | 95% | 60% | **50%** | 38% |
| 80 | 100% | 100% | 100% | 100% | 99% | 98% | 73% | 63% | **50%** |

(Le matrici complete per le 4 fasce sono generate da
`python -m app.scripts.fase8_dungeon_difficulty_audit`.)

## 7. PROVA DI ACCETTAZIONE — squadra Lv15 vs dungeon Lv40

| Fascia Lv15 | Team | Gate Lv40 (945) | Esito |
|---|---|---|---|
| sottopotenziata | 455 | 945 | **BLOCK** |
| media | 535 | 945 | **BLOCK** |
| ben equipaggiata | 615 | 945 | **BLOCK** |
| molto forte (10× Rare) | 865 | 945 | **BLOCK** |

Una squadra Lv15 supera il gate del Lv40 solo con equip da endgame
(es. pezzi Legendary Lv80: membro ~430 → team ~2100 → rating 158% →
farmabile). È il caso "veramente eccezionale" richiesto: PWR-driven,
nessun hard level-gate.

Progressione Lv15 media: Lv10-15 → 88%/50% · Lv20 → 25% · Lv25-30 →
BLOCK · Lv40 → BLOCK. Combacia col mandato.

## 8. Effetti sull'Overpower

Moltiplicatori invariati. Con la nuova curva il rating scala più
lentamente in progressione (parità a pari livello), ma sui CONTENUTI
VECCHI l'endgame resta a rating 200-700% → ×3.0 immediato: la farm dei
reagenti bassi è preservata (verificato da test dedicato).

## 9. Rollout

`python -m app.scripts.fase8_apply_rebalance` (dry-run; `--apply` per
scrivere): aggiorna `dungeons.recommended_power` e
`raid_dungeons.recommended_power_combined`. Idempotente e auditabile.
Da eseguire DOPO `fase2_redistribuzione_team_size --apply` (le team
size restano di competenza di quello script; è compatibile: i poteri
che imposta vengono sovrascritti da questo).

Test: `backend_fase8_rebalance_test.py` (7 casi, incluso il test di
regressione principale Lv15-vs-Lv40 e il vincolo gate ≥×1.5 per slug).
