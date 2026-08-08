# FASE 7 — Report finale della tranche "Lavoro-partito-08/08/2026"
Data: 2026-08-08 · Branch: Lavoro-partito-08/08/2026

## 1. Cosa contiene questa tranche (Fasi 1–6)

| Fase | Commit | Contenuto |
|---|---|---|
| 1 | 9dd262d…d7327ba | Fix Deposito nero (ReferenceError `slot`), ErrorBoundary globale, auto-equip rispetta "Bloccato" + rollback swap, "già equipaggiato da X" preventivo, PULISCI report (soft-delete), barra XP nei report, Prestigio→Livello di Gilda, streak in alto, visibilità progressiva, censimento EN |
| 2 | 93cf3a7 | Curva successo logistica senza cap 95 (100% reale), Overpower (drop ×1.5→×3.0), gate a potere del gruppo (60% del consigliato), distribuzione 3/5/7 (script `fase2_redistribuzione_team_size`), catch-up XP top-5 |
| 3 | 3cbecd6 | Un reagente principale per dungeon/raid (12 materiali nuovi, rari raid-only), Cucina+Alchimia (tab + 4 ricette), scomparto Consumabile, Pietra della Conoscenza (20%, +50% XP ×5), traduzioni errori |
| 4 | 062c4e2 | Sistema immagini (132 SVG placeholder + GameImage fallback), hero banner, card fantasy, avatar razziali 50×2, manifest asset |
| 5 | 4a8be4c | Dungeon a stanze (pilota: sewer-nest, goblin-warrens): stanze con lore, riposo/scelta/fuga 50%, XP solo a fine run +25%, motore CAS idempotente, timeline FE |
| 6 | (questo) | Upload avatar personalizzato (PNG/JPEG/WEBP ≤2MB, magic bytes, no SVG), serving statico, UI cambia/rimuovi ritratto |

Design docs nel repo: `fase2_design_bilanciamento.md`,
`fase3_design_reagenti_crafting.md`, `fase4_asset_manifest.md`,
`fase5_design_dungeon_stanze.md`, `piano_lavoro_evoluzione_2026-08-08.md`.

## 2. Stato dei test

- **Backend (puri, senza Mongo)**: 56/56 verdi — auto-equip gate (6),
  visibilità progressiva (5), bilanciamento F2 (16), reagenti/consumabili
  F3 (13), stanze F5 (10), upload avatar F6 (6).
- **Frontend (Jest)**: 13/13 — regressione Deposito (4), GameImage (4),
  territorio pre-esistente (5). Build di produzione pulita.
- **Smoke**: `create_app()` monta 314 route senza errori.
- **NON eseguibili in locale** (niente MongoDB su questa macchina): la
  suite d'integrazione `backend/tests/backend_round*` e il collaudo
  end-to-end. Da eseguire sull'ambiente col DB prima del go-live.
- Pre-esistenti noti: test "sealed" R18.4 richiede i path `/app/...` del
  container emergent; `yarn lint` rotto (ESLint 9 senza flat config).

## 3. Passi di rollout sull'ambiente col DB (in ordine)

1. `python -m app.seeds.seed_fase3_reagenti_consumabili` — materiali,
   consumabili, ricette, backfill profession.
2. `python -m app.scripts.fase2_redistribuzione_team_size` (dry-run),
   poi `--apply` — distribuzione 3/5/7.
3. Verificare `AVATAR_UPLOAD_DIR` (o default `backend/uploads/avatars`)
   scrivibile e persistente (volume).
4. Suite d'integrazione: `pytest backend/tests` con DB di test.
5. Collaudo manuale: checklist §4.

## 4. Checklist di collaudo manuale (per i tester)

- [ ] Deposito con oggetti → nessuna schermata nera; badge equip su anelli/monili.
- [ ] Auto-Equip: mai item "Bloccato"; swap falliti ripristinano il pezzo.
- [ ] PULISCI su spedizioni e raid (con "Ripeti ultima" ancora vivo).
- [ ] Squadra forte su dungeon T1 → 100% + banner Overpower + item extra.
- [ ] Squadra sotto il 60% del potere → blocco con messaggio chiaro.
- [ ] Top-5 ≥ Lv10 → novellino con "+25% recupero" nel report.
- [ ] Dungeon mappato → SOLO il suo reagente; raid vinto → reagente garantito.
- [ ] Cucina/Alchimia: craft di Stufato/Elisir e assegnazione ("Usa su…").
- [ ] Pietra della Conoscenza: drop ~20%, buff visibile, cariche a scalare.
- [ ] Tane dei Goblin (pilota stanze): timeline, riposo (+8%), fuga (50%),
      completamento (+25% XP); dungeon non-pilota invariati.
- [ ] Upload ritratto (PNG ok, SVG rifiutato, >2MB rifiutato) e rimozione.
- [ ] Estetica: hero banner, card dungeon con immagini, avatar razziali.

## 5. Lavoro residuo consigliato (prossima tranche)

- 38 messaggi backend ancora in EN (censimento aggiornato in
  `fase1_censimento_testi_inglesi.md`) + pagine Admin/Guida.
- Art definitiva al posto dei placeholder (manifest F4, con specifiche).
- Estensione stanze: più dungeon nel pilota, percorsi ramificati, stanze
  nei raid (il data model è pronto).
- Raid: valutare rimozione level-gate a favore del potere (oggi solo dungeon).
- Sanare la collisione case-insensitive `memory/BACKLOG.md` vs
  `memory/backlog.md` (blocca i checkout puliti su Windows).
- `yarn lint` da migrare a flat config ESLint 9.

**Il go-live su orbusonline.net resta una decisione dell'owner.**
