# FASE 2 — Design bilanciamento: successo >100%, Overpower, gate a potere, 3/5/7, catch-up XP
Data: 2026-08-08 · Branch: Lavoro-partito-08/08/2026 · Stato: implementato in questa fase

## 1. Perché il 95% era "sempre 95%"

La vecchia formula era `chance = 50 + (PT − PC)` con clamp [10, 95]: lineare in
**punti assoluti** di potere. Bastava superare il potere consigliato di 45 punti
assoluti per saturare — a metà gioco qualunque squadra decente stava al cap, e
il cap nascondeva quanto la squadra fosse davvero più forte del contenuto.

## 2. Rating di Potenza (la nuova grandezza centrale)

```
R = round(100 × PT / PC)
```
- `PT` = potere squadra effettivo (stat + livelli + equip + effetti + bonus ruoli)
- `PC` = potere consigliato del dungeon
- R è una **percentuale**: 100 = parità, 150 = squadra al 150% del contenuto.
  Può superare 100 senza limiti: è il numero che il giocatore vede crescere.

## 3. Probabilità di successo — curva logistica

```
chance(R) = round( 100 / (1 + e^(−k·(R−100)/100)) )   con k = 4.4
clamp [5, 100];  R ≥ 200 → 100 garantito
```

| R (rating) | 50 | 75 | 100 | 125 | 150 | 175 | ≥200 |
|---|---|---|---|---|---|---|---|
| Probabilità | 10% | 25% | 50% | 75% | 90% | 96% | 100% |

Proprietà volute:
- **relativa**, non assoluta: scala uguale dal tutorial all'endgame;
- **parità = 50%** (retro-compatibile con l'intenzione della vecchia formula);
- crescita **morbida** (curvatura funzionale, niente gradini);
- il **100% esiste davvero**: a potenza doppia la vittoria è garantita —
  da lì in poi il giocatore gioca per l'Overpower, non per la chance.

## 4. Overpower — l'eccedenza diventa drop

```
OP = max(0, R − 100)
molt_drop = min(3.0, 1 + 0.5 × ⌊OP / 25⌋)
```

| R | 100–124 | 125–149 | 150–174 | 175–199 | ≥200 |
|---|---|---|---|---|---|
| Moltiplicatore drop | ×1.0 | ×1.5 | ×2.0 | ×2.5 | ×3.0 (cap) |

- Si applica a: **numero di item** lootati e **quantità di materiali**.
- NON si applica a oro e XP (hanno già i loro moltiplicatori; evitiamo doppia
  inflazione — l'oro resta la valvola economica, l'XP la valvola progressione).
- Item extra: campionati tra gli item già usciti dal roll normale (stessa
  loot table, stessa distribuzione rarità).
- Il moltiplicatore è **congelato al dispatch** (campo `overpower_loot_multiplier`
  sull'expedition) e mostrato nel report ("bottino da Overpower").
- Farmabilità dei dungeon vecchi (richiesta D.7): una squadra endgame su un
  dungeon T1 va dritta a ×3.0 → rigiocare contenuti vecchi per i reagenti
  diventa efficiente per design.

## 5. Gate d'ingresso a potere (sostituisce il level-gate dei dungeon)

```
PT_min = ⌈0.60 × PC⌉      (equivale a chance ≈ 14%)
```
- Sotto PT_min: HTTP 423 `team.power_too_low` con messaggio chiaro
  ("Potere squadra X, servono almeno Y — il dungeon consiglia Z").
- Il rischio resta possibile (60–100% = run azzardata), l'assurdo no.
- Il level-gate (`adventurer.level_too_low`) è **rimosso solo per i dungeon**
  (dispatch + preview). I raid mantengono i loro gate attuali (già basati su
  potere-picco gilda + livello): eventuale revisione in una fase dedicata.
- `min_adventurer_level` resta esposto nell'API come dato informativo
  (fascia consigliata), non più bloccante.

## 6. Distribuzione dungeon 3/5/7 (base = 5)

Linea principale (prima tutta da 3): ora **base 5**, con i 3 come "incursioni
rapide" e i 7 come "grandi imprese". Tutorial resta a 3 per non chiedere 5
avventurieri al giorno uno (il reclutamento iniziale ne dà 3).

| Slug | Size prima | Size dopo | PC prima | PC dopo |
|---|---|---|---|---|
| training-yard | 3 | 3 | 15 | 15 |
| sewer-nest | 3 | 3 | 35 | 35 |
| goblin-warrens | 3 | **5** | 70 | 117 |
| bandit-hideout | 3 | 3 | 75 | 75 |
| druid-grove | 3 | **5** | 160 | 267 |
| shadow-crypts | 3 | **5** | 170 | 283 |
| cursed-mines | 3 | **5** | 200 | 333 |
| sunken-library | 3 | 3 | 215 | 215 |
| lich-sanctum | 3 | **5** | 245 | 408 |
| dragons-hoard | 3 | **7** | 275 | 642 |
| storm-spire | 3 | **5** | 290 | 483 |
| linea `-5p` | 5 | 5 | — | invariati |
| world-tree-roots-5p | 7 | 7 | 1600 | invariato |

- Scaling PC = round(PC_vecchio × size_nuova / size_vecchia): la difficoltà
  **per membro** resta identica → la progressione iniziale non si indurisce.
- XP (`base_xp_reward`) è per-membro: invariato.
- Oro invariato (economia di gilda, non per-testa).
- Risultato: 4×3 / 16×5 / 2×7 sul catalogo attivo → base 5, varianti periodiche.
- Applicazione: `DUNGEON_CURVE` aggiornata + script idempotente
  `backend/app/scripts/fase2_redistribuzione_team_size.py` (dry-run di default,
  `--apply` per scrivere su DB; aggiorna `required_team_size` e
  `recommended_power` solo per gli slug in tabella).

## 7. Catch-up XP di gilda (top-5)

```
se i 5 avventurieri di livello più alto della gilda hanno TUTTI level ≥ 10:
    ogni avventuriero con level < 10 guadagna XP ×1.25
```
- Implementato come tabella estendibile `CATCHUP_TIERS = ((10, 0.25),)` in
  `expeditions/catchup.py` (pure) — domani si può aggiungere (30, 0.25) ecc.
- Si applica all'XP di fine spedizione, DOPO trait/Arfus/debuff stat primaria
  (moltiplicatori indipendenti, ordine ininfluente perché moltiplicativi).
- Mostrato nel report squadra: "⬆ Recupero gilda +25%".
- "Più forti" = per livello (il criterio della soglia è il livello stesso).

## 8. Compatibilità e rischi

- `compute_success_chance(team_power, recommended_power)` mantiene la firma:
  tutti i consumer (preview, dispatch, equipment delta, script di audit)
  prendono la curva nuova automaticamente. I raid usano un proprio calcolo e
  NON cambiano in questa fase.
- Costanti: `SUCCESS_CHANCE_MIN 10→5`, `SUCCESS_CHANCE_MAX 95→100`,
  nuove `OVERPOWER_*`, `GUARANTEED_SUCCESS_RATING`, `POWER_GATE_RATIO`.
- Il bonus threat/counter (R16.0) ora satura a 100 invece di 95.
- Test esistenti che asserivano il clamp 95 aggiornati.
- Le spedizioni già in corso conservano la loro `success_chance` congelata:
  nessuna migrazione necessaria. I doc senza `overpower_loot_multiplier`
  (legacy) completano con moltiplicatore 1.0.
- Rollout DB (3/5/7): richiede l'esecuzione dello script con `--apply`
  sull'ambiente col DB (decisione dell'owner, come per il deploy).
