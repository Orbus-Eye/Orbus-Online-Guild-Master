# R18.6 — Classless, 27 Class Hall e baseline item-first

**Aggiornato:** 2026-07-29  
**Stato:** baseline tester locale raggiunto; profondità gameplay in corso

## Risultato

Il percorso autorevole parte da un avventuriero senza classe. Il tester può
confrontare 27 Hall, completare una prova safe-mode, confermare il sentiero,
ricevere ed equipaggiare un item identitario e progredire fino a ottenere
cinque item della classe.

Il catalogo Hall contiene 135 item singolari e lore-reviewed. Il catalogo
Mongo locale isolato contiene 261 item attivi non-test, tutti con identità
univoca, fonte lore e flavor text.

La Collection Book rende visibili stato, Hall, wave, slot, lore, fonte,
provenienza ed effetto. Gli strumenti tester permettono reset e smoke matrix.
Le 27 signature modificano ora il potere della spedizione e il report mostra
item, avventuriero, statistica, magnitudo, delta e fonte lore.

## Evidenze

```text
16 unit classless/Class Hall
21 unit proiezione/report effetti item
2 unit copertura narrativa Common
39 regressione mirata finale
116 real-Mongo effect engine
6 real-Mongo Class Hall
2 HTTP black-box
27/27 assignment
27/27 signature equip
9 spedizioni × 3 membri
27 Hall / 135 item in Collection Book
frontend build e browser QA verdi
FastAPI/OpenAPI: 306 route / 284 path
```

Nessun database condiviso o di produzione è stato modificato. Nessun commit,
push o deploy è stato eseguito.

## Limiti aperti

- le classi richiedono kit, encounter e tuning distintivi;
- 268 conflitti null legacy richiedono migrazione dedicata;
- il registry da 1500 è legacy a cinque archetipi e richiede remap;
- la suite storica monolitica non è portabile e va bonificata.

Il prossimo incremento è la vertical slice di profondità Wave A, sempre
costruita attorno a scelte item leggibili e verificabili.
