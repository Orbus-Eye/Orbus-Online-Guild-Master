# T6 — Rapporto catalogo finale item

Data gate tecnico locale: 2026-07-30

## Esito

Il catalogo deterministico `t6.final.v1` supera i gate tecnici T6.

| Contratto | Esito |
|---|---:|
| Blueprint totali | 1500 |
| Comune | 525 |
| Non-Comune | 375 |
| Raro | 300 |
| Epico | 225 |
| Leggendario | 60 |
| Unico | 15 |
| Item di classe | 1350, 50 per 27 classi |
| Item universali | 150 |
| Dungeon con pool completo | 23/23 |
| Raid con pool completo | 4/4 |
| Blueprint senza fonte | 0 |
| Blueprint senza lore/flavor/effetto | 0 |
| Blueprint senza slot/livello/binding | 0 |

Hash SHA-256:
`b609d2697a55543841a0a6ee1b1722fd1d7489a04c9ecb97208be3e8add68840`

## Politica endgame

- Leggendari e Unici richiedono il livello avventuriero 80.
- I dungeon ordinari rilasciano soltanto Comune, Non-Comune, Raro ed Epico.
- I raid non rilasciano oggetti Unici.
- Quattordici Unici sono consegne garantite di traguardi endgame irripetibili.
- L'unico Unico casuale è `L'Unico Anello della "Compagnia"`.
- L'Anello proviene soltanto dal boss mondiale Alveora, con un tiro per gilda
  contribuente per evento, probabilità privata `0,000001` e unicità globale.

## Attivazione e compatibilità

Il seed T6 usa batch da 250 e non riscrive gli ID di item già presenti.
Il catalogo T6 convive temporaneamente con le righe legacy: i pool runtime
preferiscono `catalog_version=t6.final.v1`, mentre gli inventari storici
rimangono risolvibili. La disattivazione dei legacy richiede il successivo
audit dell'ambiente tester e non viene eseguita automaticamente.

Prova su Mongo locale isolato:

- prima esecuzione: 1500 inserimenti;
- seconda esecuzione: 0 inserimenti, 0 modifiche;
- nessun duplicato.

## Pool runtime

- Ogni combinazione dungeon/rarità dichiarata possiede almeno un blueprint.
- Ogni combinazione raid/rarità dichiarata possiede almeno un blueprint.
- Le ricompense raid usano un seed legato all'istanza del raid.
- Un ledger dedicato e `source_grant_id` impediscono duplicazioni durante
  retry, crash recovery o doppio completamento.

## Simulazione

Sono state eseguite 100.000 iterazioni per ciascuno dei 46 rami dungeon e
degli 8 rami raid:

- tutte le frequenze osservate sono entro la tolleranza del gate;
- nessun Leggendario o Unico è apparso nei dungeon;
- nessun Unico è apparso nei raid;
- la policy dell'Anello equivale a 1 ottenimento atteso per un milione di tiri
  eleggibili, senza inserirlo nei pool dungeon/raid.

Test automatici mirati: 27 superati. Le sessioni con tester umani e il tuning
basato su telemetria appartengono alla T8.
