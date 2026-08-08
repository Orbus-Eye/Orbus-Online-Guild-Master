# FASE 3 — Design: reagenti per dungeon, Cucina, Alchimia, consumabili, Pietra della Conoscenza
Data: 2026-08-08 · Branch: Lavoro-partito-08/08/2026 · Stato: implementato in questa fase

## 1. Un reagente principale per dungeon/raid

Prima: i materiali cadevano per **tier** (tabella T1–T4 condivisa), quindi
nessun dungeon aveva un'identità di farm — "dove trovo X?" non aveva risposta.

Ora: **ogni dungeon/raid ha UN reagente principale**, coerente con la lore.
Regola d'oro: la mappa contenuto→reagente è univoca per contenuto (un solo
tipo per dungeon); un reagente può appartenere a più dungeon dello stesso
tema (i comuni), i rari vivono nei contenuti alti e i più rari SOLO nei raid.

### Tabella dungeon → reagente principale

| Dungeon | Reagente | Rarità | Drop | Qty |
|---|---|---|---|---|
| training-yard, goblin-warrens, iron-foundry-5p | Scheggia di Ferro (iron_shard) | common | 60% | 1–3 |
| sewer-nest, bandit-hideout, wolf-den-5p | Cuoio Grezzo (raw_leather) | common | 60% | 1–3 |
| druid-grove, silent-monastery-5p | Erba Curativa (healing_herb) | common | 60% | 1–3 |
| shadow-crypts, sunken-library | Polvere Arcana (arcane_dust) | uncommon | 50% | 1–2 |
| cursed-mines, pirate-fleet-5p | Gemma Opaca (dull_gem) | uncommon | 50% | 1–2 |
| lich-sanctum | **Ossa Antiche** (ossa_antiche) ★ | uncommon | 50% | 1–2 |
| frost-cave-5p | **Ghiaccio Eterno** (ghiaccio_eterno) ★ | uncommon | 50% | 1–2 |
| salt-marsh-5p | **Spezia Palustre** (spezia_palustre) ★ | uncommon | 50% | 1–2 |
| dragons-hoard | **Scaglia di Drago** (scaglia_di_drago) ★ | rare | 35% | 1–2 |
| storm-spire | **Essenza di Tempesta** (essenza_di_tempesta) ★ | rare | 35% | 1–2 |
| obsidian-arena-5p | **Ossidiana** (ossidiana) ★ | rare | 35% | 1–2 |
| clockwork-vault-5p | **Ingranaggio Arcano** (ingranaggio_arcano) ★ | rare | 35% | 1–2 |
| voidspire-5p | **Frammento del Vuoto** (frammento_del_vuoto) ★ | rare | 35% | 1–2 |
| infernal-pit-5p | **Cenere Infernale** (cenere_infernale) ★ | epic | 22% | 1 |
| celestial-citadel-5p | **Lacrima Celeste** (lacrima_celeste) ★ | epic | 22% | 1 |
| world-tree-roots-5p | **Linfa del Mondo** (linfa_del_mondo) ★ | epic | 22% | 1 |

### Raid → reagente (GARANTITO a vittoria, 50% qty dimezzata su parziale)

| Raid | Reagente | Rarità | Qty vittoria |
|---|---|---|---|
| moonfall-vigil | **Polvere di Luna** (polvere_di_luna) ★ | epic | 2–3 |
| broken-bastion-siege | **Nucleo d'Assedio** (nucleo_d_assedio) ★ | epic | 2–3 |
| necropolis-bells | **Rintocco Spettrale** (rintocco_spettrale) ★ | legendary | 1–2 |
| dragon-vault | Essenza di Drago (dragon_essence) | legendary | 1–2 |

★ = 12 nuovi materiali (item_type=material, nomi italiani). `dragon_essence`
viene promossa a reagente esclusivo di dragon-vault (prima cadeva anche nei
dungeon T3/T4).

- I dungeon fanno rollare SOLO il loro reagente principale (più chiarezza,
  più identità); fallback legacy sulla tabella tier per slug non mappati.
- Fallimento dungeon = 50% del rate. L'**Overpower** (Fase 2) moltiplica le
  quantità → i dungeon vecchi sono la farm efficiente dei reagenti bassi.
- Ai raid il reagente è garantito a vittoria: sono la SOLA fonte dei 4
  reagenti da raid (richiesta "i più rari nei raid").

## 2. Professioni di crafting: Fucina, Cucina, Alchimia

Le ricette guadagnano `profession ∈ {forge, cooking, alchemy}` (legacy →
forge). Stessa collection `recipes`, stesso endpoint: il FE le mostra in tre
tab tematiche. Nuove ricette (tutte con output consumabile tranne Fucina):

**Cucina** (cibo → potere per N spedizioni):
- Stufato del Viandante: 2×Erba Curativa + 1×Spezia Palustre + 10g →
  consumabile +5 potere, 3 spedizioni.
- Banchetto dell'Eroe: 2×Spezia Palustre + 1×Scaglia di Drago + 40g →
  +12 potere, 3 spedizioni.

**Alchimia** (pozioni → XP o potere):
- Elisir di Vigore: 2×Erba Curativa + 1×Polvere Arcana + 20g →
  +8 potere, 5 spedizioni.
- Tonico del Sapiente: 1×Polvere di Luna + 2×Polvere Arcana + 60g →
  +25% XP, 3 spedizioni (usa un reagente da raid: i raid contano).

## 3. Scomparto "Consumabile" degli avventurieri

Modello minimo estendibile. Sull'item (`items`):

```json
"consumable_effect": {
  "type": "xp_boost" | "power_boost",
  "magnitude": 0.5,          // xp_boost: frazione (+50%) · power_boost: potere flat
  "charges": 5               // numero di spedizioni
}
```

Sull'avventuriero: `active_consumable = {item_id, slug, name_it, type,
magnitude, charges_left, activated_at}` — **uno per avventuriero**.

- Attivazione: `POST /api/adventurers/{id}/consumable {item_id}` — consuma
  1 copia dall'inventario (conditional $inc, mai negativo), 409 se c'è già
  un buff attivo (prima lo si annulla). `DELETE` = annulla senza rimborso.
- `power_boost`: applicato al potere del membro al **dispatch** (entra nel
  team_power e quindi in rating/chance/gate) + snapshot sul membro.
- `xp_boost`: applicato all'XP del membro al **completamento** (moltiplicativo
  con trait/debuff/catch-up).
- Le cariche scendono di 1 a ogni spedizione COMPLETATA (successo o
  fallimento); a 0 il buff sparisce.
- Report squadra: riga buff ("Pietra della Conoscenza: +50% XP · 3 rimaste").
- FE: assegnazione dall'inventario ("Usa su…" per i consumabili con
  effetto), stato visibile nella scheda avventuriero (con annulla).

## 4. Pietra della Conoscenza

- Item consumabile `pietra_della_conoscenza`, rarità Rare:
  `consumable_effect = {type: xp_boost, magnitude: 0.5, charges: 5}`.
- **Drop 20%** dai dungeon a successo (roll indipendente, NON moltiplicato
  dall'Overpower: è già generosa — decisione economica esplicita).
- Interazione XP (ordine ininfluente, moltiplicativo):
  `XP = base × trait × Arfus × debuff_stat × catch-up × consumabile`.

## 5. Traduzioni (dal censimento Fase 1.10)

Messaggi d'errore player-facing tradotti in italiano nei domini toccati da
questa fase (crafting) + i 404/availability più comuni (adventurers,
equipment). Il resto del censimento resta tracciato per la rifinitura.

## 6. Rollout

- `seeds/seed_reagenti_fase3.py`: 12 nuovi materiali + 5 consumabili +
  campo profession/consumable_effect + ricette Cucina/Alchimia (idempotente,
  eseguire sull'ambiente col DB come gli altri seed).
- Zero migrazioni distruttive: i materiali esistenti restano validi; le
  ricette legacy diventano `profession=forge` via default a lettura.
- Compatibilità: inventari con vecchi materiali invariati; la tabella tier
  legacy resta come fallback per contenuti non mappati.
