# Piano di lavoro — Evoluzione Orbus Online: Guild Master
Data: 2026-08-08 · Autore: Claude (lead engineering pass) · Stato: PROPOSTA — in attesa di via libera per Fase 1

## 1. Audit iniziale

### 1.1 Stato del repository
- **La cartella locale NON è un repository git** (nessuna `.git`): è un export scompattato (`-main`). Non è possibile verificare branch o differenze col repo GitHub `Orbus-Eye/Orbus-Online-Guild-Master` da qui.
- Raccomandazione: prima di toccare codice, `git init` locale + commit baseline (solo locale, nessun push), così ogni fase è diffabile e reversibile. In alternativa: clonare il repo vero e riallineare.
- Cartelle di backup nel workspace da NON toccare: `_fresh_accidental_build_backup`, `_fresh_parcheggio_backend`, `_fresh_parcheggio_frontend`, `_legacy_backup_before_restore`, `_mongo_dumps`.
- La cartella `memory/` del progetto contiene i report storici dei round precedenti (R14–R18): il progetto ha una forte cultura di documentazione per round; questo piano la continua.

### 1.2 Stack e struttura
- **Backend**: FastAPI, ~60 domini modulari sotto `backend/app/` (routes/services/schemas per dominio), MongoDB standalone (niente transazioni multi-documento → pattern conditional `$inc` con revert). Test pytest in `backend/tests/`.
- **Frontend**: React 19 + CRA/craco, Tailwind + shadcn/Radix, ~90 pagine in `frontend/src/pages/`, i18n custom (`i18n/lang/it.json` 48KB + `en.json`).
- **Due monoliti a rischio**: `backend/app/expeditions/services.py` (67KB) e `backend/app/raids/__init__.py` (44KB). Ogni modifica lì va fatta chirurgicamente.

### 1.3 Mappa feature richieste → moduli

| Feature | Dove vive |
|---|---|
| Probabilità successo / cap 95% | `shared/constants.py` (`SUCCESS_CHANCE_MAX=95`), `expeditions/formulas.py` (`compute_success_chance`), consumata da preview/services/report |
| Gating dungeon per livello | `expeditions/level_gate.py` (canonico `required_level` + curve in `shared/content_curve.py`), `dungeons/gates.py` (gate per potere-picco gilda) |
| Dungeon 3/5/7 | Già nel modello: `required_team_size` ∈ {3,5,7}, filtro API in `dungeons/routes.py`. Da rivedere solo la distribuzione del catalogo |
| Report spedizioni | BE `expeditions/report_builder.py`; FE `ExpeditionReport.jsx` (41KB), `RaidReport.jsx`. **Nessun endpoint DELETE esiste** → PULISCI da creare |
| Inventario/Deposito | BE `inventory/`; FE `pages/Inventory.jsx` su route `/inventory` (voce menu "Deposito") |
| Auto-equip | BE `equipment/auto_equip.py` (25KB, class-aware/stat-aware); FE `AdventurerEquipment.jsx`, `InventoryEquipModal.jsx` |
| Crafting/reagenti | BE `crafting/` (Fucina, ricette), `materials/catalog.py` (8 materiali hardcoded), `expeditions/material_drop_tables.py`, `forge/`, `legendary_forge/`; FE `Crafting.jsx`, `Forge.jsx` |
| Streak | FE `StreakBadge.jsx`, montato a metà `Dashboard.jsx` (riga ~251) |
| Homepage | FE `Dashboard.jsx` (28KB, ~15 mini-card in ordine storico, non di importanza) |
| Avatar/ritratti | **NON ESISTE nulla** (né BE né FE; `ui/avatar.jsx` è solo primitiva shadcn). Razze/genere già nei dati (`round160_backfill_race_gender.py`) |
| Progressione gilda | `guilds/services.py`, `achievements/levels.py`; XP hooks in `achievements/xp_hooks.py`, `expeditions/xp_modifier.py` |
| Immagini/static | **ZERO asset**: `frontend/public/` contiene solo favicon. Nessun mount statico immagini nel backend |
| Traduzioni | i18n it/en; molte stringhe IT hardcoded nei componenti; rarità/nomi interni in inglese con mapping display (`displayLabels.js`, `rarityLabel`) |

### 1.4 Incongruenze e bug rilevati (statico)
1. **Deposito nero**: `Inventory.jsx` gestisce errori API (catch → rows=[]), quindi la causa probabile è un'eccezione runtime in render. Indiziati: `buildEquippedByMap` legge solo 3 slot legacy (`weapon/armor/accessory`) mentre il sistema ora ha 10 slot (`ring_1`, `trinket_2`…) → shape mismatch con `/api/adventurers`; possibile crash in `InventoryEquipModal`/`ItemCompatibilityBadge` su item null. **Non c'è ErrorBoundary globale** (solo `ReportErrorBoundary` sui report): qualunque throw = pagina nera. Serve repro runtime, poi fix + ErrorBoundary globale.
2. **Auto-equip vs "Bloccato"**: `auto_equip.py` esclude già item `is_bound` ad altri avventurieri; il bug segnalato ("equipaggia oggetti Bloccato") indica una semantica diversa di "Bloccato" (level-gate? 4-state UI? `ui_4state.py`) o un buco nel filtro. Da riprodurre e chiudere; UX "già equipaggiato da X" da anticipare (oggi derivata client-side, in ritardo).
3. **Terminologia "Prestigio"**: presente in `ExpeditionReport.jsx` ("+X XP Prestigio"), `GuildProgressCard`, `Dashboard`, `FirstObjectiveCard`, `it.json` e vari BE (`guild_prestige_delta`). Rinomina display → "Livello di gilda" (chiavi i18n + label; i field API restano per compatibilità).
4. **Visibilità contenuti**: `list_dungeons_for_guild` ritorna TUTTO il catalogo con flag `unlocked` → il FE mostra contenuti futuri. Manca visibilità progressiva.
5. **Consumabili**: `item_type: "consumable"` esiste (filtri inventario) ma non c'è slot consumabile sugli avventurieri né logica d'uso.
6. **Pietra della Conoscenza**: non esiste. `xp_modifier.py` è il punto d'aggancio naturale per buff XP.
7. **Bonus XP top-5 gilda**: non esiste.
8. **Barra XP nei report squadra**: il report mostra XP di prestigio gilda ma non barre XP per avventuriero.
9. **Dungeon a stanze**: `encounters.py` ha già `encounter_phases` (fasi narrative/metadata) ma la spedizione è un blocco unico con un solo timer → il refactor a stanze è reale e profondo (stato, timer per stanza, loot per stanza, riposo, fuga).

## 2. Piano per fasi

### Fase 1 — Bugfix e quick wins (rischio basso-medio)
Obiettivi: Deposito, auto-equip+UX, rinomina Prestigio, PULISCI report, barra XP report, streak in alto, visibilità progressiva, censimento testi EN.
File probabili: `Inventory.jsx`, `App.js` (ErrorBoundary), `equipment/auto_equip.py`, `equipment/ui_4state.py`, `InventoryEquipModal.jsx`, `expeditions/routes.py`+`services.py` (DELETE reports), `raids/__init__.py` (DELETE), `ExpeditionReport.jsx`, `RaidReport.jsx`, `Expeditions.jsx` (lista+PULISCI), `Dashboard.jsx` (ordine card), `dungeons/services.py` (visibilità), i18n `it.json`, `displayLabels.js`.
Rischi: DELETE report → decidere soft-delete (flag `dismissed`) vs hard-delete; visibilità progressiva non deve nascondere contenuti già sbloccati/attivi. Dipendenze: repro runtime con app avviata (mongo locale + seed).
Ordine: 1) setup runtime+git baseline 2) Deposito+ErrorBoundary 3) auto-equip 4) PULISCI 5) barra XP 6) prestigio→livello 7) dashboard/streak 8) visibilità 9) censimento EN.

### Fase 2 — Probabilità >100%, gating a potere, distribuzione 3/5/7, bonus XP top-5
Obiettivi:
- Nuova curva successo: rimozione clamp 95; oltre 100% la % di successo resta 100 ma l'eccedenza diventa **Overpower bonus** sui drop. Formula proposta (da validare con te prima dell'implementazione): `chance_raw = 50 + delta_scalato(team_power, recommended_power)` con curvatura logistica dolce; `overpower = max(0, chance_raw - 100)`; bonus drop = `+50% quantità per ogni 25 punti overpower` (lineare a gradini, documentata nel report giocatore).
- Gating: sostituire il level-gate con richiesta di **potere totale del gruppo** ≥ soglia del dungeon (con messaggio chiaro); mantenere `required_level` solo come fallback dati.
- Catalogo: base = dungeon da 5; 3 e 7 come varianti periodiche; nessun buco di progressione ai poteri bassi.
- Bonus catch-up: se i top-5 avventurieri della gilda sono ≥ Lv10 → +25% XP a tutti quelli sotto Lv10 (implementato come modificatore in `xp_modifier.py`, estendibile a soglie future).
File: `shared/constants.py`, `expeditions/formulas.py`, `expeditions/services.py`, `expeditions/preview.py`, `loot_tables.py`, `report_builder.py`, `expeditions/level_gate.py`, `dungeons/gates.py`, `shared/content_curve.py`, seeds dungeon, `xp_modifier.py`; FE: `ExpeditionNew.jsx`, `DungeonPreviewModal.jsx`, `ExpeditionReport.jsx`, `Dungeons.jsx`.
Rischi: alto impatto bilanciamento; i test esistenti asseriscono il clamp 95 → aggiornare test; monolite services.py.
Dipendenze: Fase 1 (report UI). Documento formula prima del codice.

### Fase 3 — Reagenti, crafting, Cucina, Alchimia, consumabili, Pietra della Conoscenza
Obiettivi: 1 reagente principale per dungeon/raid (rari nei raid), tabella reagenti ridisegnata, sezioni Cucina+Alchimia con ricette e consumabili, slot "Consumabile" per avventuriero, Pietra della Conoscenza (drop 20%, +50% XP per 5 dungeon), italianizzazione nomi.
File: `materials/catalog.py`, `material_drop_tables.py`, `loot_tables.py`, `crafting/`, seeds (`seed_items_it.py`, `seed_recipes_it.py`), `items/final_catalog.py`, nuovo dominio `consumables` o estensione `equipment` (slot), `xp_modifier.py` (buff con contatore dungeon residui); FE: `Crafting.jsx` (tab Fucina/Cucina/Alchimia), `Inventory.jsx`, `AdventurerDetailModal.jsx` (slot consumabile + buff visibile).
Rischi: migrazione dati inventari esistenti; coerenza economia (dungeon vecchi devono restare farmabili). Dipendenze: Fase 2 (drop bonus overpower interagisce con drop reagenti).

### Fase 4 — Restyling fantasy + immagini + avatar default
Obiettivi: sistema asset (`frontend/public/assets/...` con manifest), placeholder fantasy generati/SVG per: sezioni, dungeon/raid, banner dashboard, classi/razze, reagenti/consumabili; card decorative (bordi, texture, gradienti tematici); dashboard riorganizzata "da gioco"; avatar default per razza×genere (fallback garantito).
File: `frontend/public/assets/**` (nuovo), `tailwind.config.js`, `index.css`, `AppHeader.jsx`, `Dashboard.jsx`, `Dungeons.jsx`, `Raids.jsx`, `Crafting.jsx`, card components; nuovo `components/GameImage.jsx` (fallback-safe); mapping slug→asset.
Rischi: bassi (solo estetica), attenzione a bundle size e mobile. Dipendenze: nessuna dura; meglio dopo Fase 3 per conoscere le sezioni definitive.

### Fase 5 — Refactor dungeon a stanze
Obiettivi: dungeon composti da stanze (2–4 low level, più per gli alti), ogni stanza con tempo/loot/tema; dopo ogni stanza: riposo o prosecuzione con scelta percorso; gruppo lockato nel dungeon; fuga = 50% oro + 50% item scelti random, XP finale solo a completamento.
Design da produrre PRIMA del codice: data model (`dungeon_rooms` nel doc dungeon + `expedition.room_state`), macchina a stati (in_room → room_complete → resting → choosing → …, escaped/completed), reward per stanza vs finale, compatibilità col vecchio flusso (feature flag + dungeon legacy single-block), recovery per spedizioni interrotte.
File: `dungeons/encounters.py` (evolve `encounter_phases` → stanze reali), `expeditions/services.py` (split consigliato in `room_engine.py`), `report_builder.py`, seeds lore stanze; FE: `ExpeditionNew.jsx`, nuova `ExpeditionRun.jsx` (vista stanza/riposo/scelta), `ExpeditionReport.jsx`.
Rischi: i più alti del piano (stato persistente, timer multipli, fuga, recovery); mitigazione: feature flag, rollout su 1 dungeon pilota. Dipendenze: Fasi 1-2 (formule e report nuovi).

### Fase 6 — Upload avatar custom + rifinitura
Obiettivi: upload immagine da PC (validazione tipo/dimensione, resize server-side, storage su disco o GridFS, serving statico), fallback a avatar razza/genere; polish UX; traduzioni finali.
File: nuovo `backend/app/avatars/` (routes/services/storage), `app_factory.py` (StaticFiles mount), FE `AdventurerDetailModal.jsx`, `Adventurers.jsx`, `GameImage.jsx`.
Rischi: sicurezza upload (MIME sniffing, size cap, niente SVG utente), path traversal. Dipendenze: Fase 4 (sistema asset/fallback).

### Fase 7 — Testing e rifinitura finale
Obiettivi: suite pytest aggiornata sulle nuove formule/flussi, smoke test FE (build + lint + pagine chiave), pass di bilanciamento con simulazioni (`round14_loot_sim.py` come base), report finale e checklist pre-live (il go-live lo decidi tu).

## 3. Quick wins (rischio basso, subito)
ErrorBoundary globale · fix Deposito · PULISCI report (soft-delete) · barra XP nei report · streak in alto in Dashboard · rinomina Prestigio→Livello di gilda · "già equipaggiato da X" anticipato nella UI equip · nascondere dungeon non ancora raggiungibili · censimento automatico stringhe EN (script) · bonus XP top-5 (piccolo e isolato in xp_modifier).

## 4. Major refactor
1. Dungeon a stanze (Fase 5) — il più grande; richiede design doc approvato prima del codice.
2. Curva successo/overpower + gating a potere (Fase 2) — tocca il cuore del bilanciamento.
3. Economia reagenti + Cucina/Alchimia (Fase 3) — ridisegno dati + migrazione.
4. Sistema immagini/asset + avatar (Fasi 4/6) — nuovo sottosistema, ma additivo.

## 5. Raccomandazione
Partire dalla **Fase 1**, iniziando con: (a) git init + commit baseline locale, (b) avvio runtime locale (mongo + backend + frontend) per riprodurre il bug Deposito, (c) fix in ordine quick-win. Ogni fase si chiude con: riepilogo modifiche, cosa testare, commit locale dedicato.
