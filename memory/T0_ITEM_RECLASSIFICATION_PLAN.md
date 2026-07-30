# T0 — Piano di riclassificazione item

**Stato:** dry-run offline, zero scritture database  
**Data:** 2026-07-29

## Contratto

Il catalogo finale contiene 1500 blueprint:

- Comune: 525;
- Non-Comune: 375;
- Raro: 300;
- Epico: 225;
- Leggendario: 60;
- Unico: 15.

La quota descrive la presenza nel catalogo e non il drop rate.

## Evidenza locale disponibile

La snapshot storica
`memory/backups/round183c_prestart/orbus_r16/items.bson.gz` contiene 178 item
attivi non-test:

| Rarità | Correnti snapshot | Target finale | Mancanti teorici |
|---|---:|---:|---:|
| Comune | 52 | 525 | 473 |
| Non-Comune | 37 | 375 | 338 |
| Raro | 39 | 300 | 261 |
| Epico | 39 | 225 | 186 |
| Leggendario | 11 | 60 | 49 |
| Unico | 0 | 15 | 15 |

Risultati:

- slug duplicati: 0;
- nomi italiani duplicati case-insensitive: 0;
- item senza fonte: 0;
- Leggendari dichiarati sotto livello 15: 11;
- drop ordinari endgame dichiarati: 0;
- mutazioni eseguite: 0.

Questa non è la snapshot corrente da 261 item. I numeri mancanti sono quindi
soltanto un controllo dello strumento, non la quantità da produrre.

## Regole di riclassificazione

1. Non cambiare rarità soltanto per riempire una percentuale.
2. Preservare ID e slug degli item validi.
3. Canonicalizzare le rarità in
   `Common/Uncommon/Rare/Epic/Legendary/Unique`.
4. Forzare ogni Leggendario e Unico al livello massimo 15.
5. Rimuovere Leggendari e Unici dalle tabelle casuali ordinarie.
6. Riservare `ultra_rare_random_drop` al solo
   `l_unico_anello_della_compagnia`.
7. Richiedere nome singolare, fonte, lore, flavor, slot, compatibilità,
   binding e metodo di acquisizione prima dell'attivazione.
8. Conteggiare soltanto item attivi e non-test nelle quote finali.
9. Non classificare automaticamente come universale un item privo di classe:
   deve essere una decisione esplicita.
10. Bloccare import e attivazioni che superano una quota.

## Procedura sulla futura snapshot esatta

1. Esportazione read-only dei 261 item in JSONL o BSON.
2. Esecuzione di `python -m app.scripts.t0_item_catalog_audit <snapshot>`.
3. Revisione manuale di duplicati, binding non classificati e rarità.
4. Produzione di un manifest `before → after`, senza applicazione.
5. Approvazione del manifest.
6. Snapshot di rollback.
7. Migrazione idempotente su database locale isolato.
8. Nuovo audit e verifica che gli ID siano invariati.
9. Soltanto dopo: valutazione di qualsiasi ambiente condiviso.

## Gate per iniziare T1

T1 può iniziare usando il catalogo esistente e placeholder. La produzione dei
1239 item teoricamente mancanti resta vietata fino a T6. Il completamento
dell'audit esatto è necessario prima dell'import finale, non blocca la
progettazione delle meccaniche delle 27 classi.
