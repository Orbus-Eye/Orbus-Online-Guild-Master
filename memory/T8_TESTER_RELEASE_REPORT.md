# T8 — Rapporto tester release

**Data:** 2026-07-30  
**Contratto:** `t8.tester-release.v1`  
**Stato tecnico:** completato  
**Set di classe:** esclusi e rinviati

## Risultato

La repository dispone di un percorso tester ripetibile e isolato per la
visione item-first:

```text
recluta senza classe
→ Class Hall
→ item-firma
→ equip
→ dungeon
→ raid
→ ricompensa
→ nuova build
```

Il catalogo finale contiene 1500 blueprint e rispetta esattamente le quote
`525/375/300/225/60/15`. Le 27 classi espongono 81 build item-driven.

## Gate eseguiti

- regressione reale T5 su Mongo e API HTTP isolate: `25 passed`;
- contratti T6/T8 e curve: `40 passed`;
- build frontend di produzione: completata;
- verifica browser desktop: completata, zero errori console;
- verifica browser mobile 390×844: completata, nessun overflow orizzontale;
- database temporanei e servizi locali: rimossi al termine.

## Correzioni emerse dal collaudo

- inizializzazione automatica delle 50 razze giocabili anche su database
  appena resettato;
- normalizzazione definitiva dello slot legacy `armor → chest`;
- rosa tester MAX portata a 39: 27 classi e due coorti indipendenti da sei;
- dungeon/raid dei test riallineati alle formazioni 3/5/7 e 10/15/20/40;
- Radici dell'Albero del Mondo riallineate a sette membri e PWR 1600;
- banda dei campioni comparabili calibrata a 80–120%, senza applicare tuning
  automatico;
- gate T8 server-owned e checklist umana persistibile di sei controlli.

## Separazione delle responsabilità

Il completamento tecnico non compila automaticamente la checklist umana.
Navigazione, chiarezza della lore, leggibilità dei report e ripetibilità
devono essere confermate dai tester reali. La registrazione della checklist
non autorizza deploy, buff, nerf o modifiche automatiche delle formule.
