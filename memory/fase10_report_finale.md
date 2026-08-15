# FASE 10 — Report finale
## Tester fixes + Beni di Gilda + Dungeon automatici

- **Data**: 2026-08-15
- **Branch**: `main` (source of truth della tranche, come da mandato)
- **HEAD iniziale**: `c4488e50492147d8d07a33ce759423097fa546c5` (merge PR #8)
- **HEAD finale**: vedi ultimo commit `FASE 10U` su `main` (push verificato con `git ls-remote`)
- **Commit della tranche**: 10A → 10B → 10C-F → 10G-N → 10U (uno per macro-fase)

---

## 10A — P0 · Scelta classe nuovo avventuriero — **PASS**

| Voce | Esito |
|---|---|
| Root cause | **RIPRODOTTA CON TEST** (non ipotizzata): dalla FASE 9 il backend serve `class_mechanic` **senza** `builds` (`class_mechanic_public`), ma la griglia delle 27 Sale in `ClassHallAssignmentJourney.jsx` faceva `hall.class_mechanic.builds.map(...)` → `TypeError` in render → l'intera pagina Sale di Classe finiva in ErrorBoundary **appena esisteva una recluta senza classe** (cioè subito dopo la creazione di un nuovo avventuriero). Senza reclute classless la griglia non montava: per questo il bug appariva solo dopo la creazione. Riproduzione: test Jest eseguito sul codice pre-fix → crash esattamente su `builds.map` (riga 439). |
| Fix | Chip `builds` → chip `resonance_tags` canonici (con guardia null); `ExpeditionExplainer` allineato al formato post-FASE 9 (`resonance_active`/`matched_tags` top-level, fallback lettura vecchi snapshot `active_build`). |
| Flow completo | creazione → classless (`recruit_unassigned`) → apertura Sale ✔ → prova sicura → conferma → classe + **ruolo fisso canonico** scritti insieme → ritorno senza errori. |
| Classi testate | Guerriero (DPS), Paladino (TANK), Alchimista (HEALER), Astrologo (HEALER), Cavaliere di Draghi (TANK) — conferma end-to-end (mock CAS) con verifica del `class_role` scritto. |
| Regressione permanente | FE `class_hall_assignment_journey.test.jsx` (3 test, payload reale senza builds); BE `test_fase10_class_assignment.py` (6 test: contratto payload 27/27 senza `builds` + `resonance_tags` presenti + campi card + conferma parametrizzata sulle 5 classi). Registry 27 classi intatto (13 DPS / 6 TANK / 8 HEALER — suite FASE 9 verde). |

## 10B — Italianizzazione Dungeon/Raid — **PASS**

| Voce | Prima | Dopo |
|---|---|---|
| Nomi dungeon nelle notifiche/report | `dungeon_name` EN persistito; mappa FE copriva **10/32** dungeon; toast `Replay started: Goblin Warrens` | Backend fonte autoritativa: `dungeon_name_it` esposto **sempre** (anche doc legacy, via reverse-map EN→slug→IT); dispatch persiste `dungeon_slug` + `dungeon_name_it`; toast «Spedizione ripetuta: Tane dei Goblin» |
| Nomi raid | `raid_public` non esponeva **alcun** nome; `raids.catalog` IT copriva **3/9** raid; toast `Raid completed` | `raid_name`/`raid_name_it` snapshot al via + fallback per slug sui doc legacy; i18n completata 9/9 (IT+EN); toast «Raid completato» |
| Narrativa report | `narrative_summary`/result_log IT con nome EN dentro | nome ITALIANO in narrativa IT, log stanze e log legacy; `narrative_en` resta EN |
| Email benvenuto IT | «Invia il tuo team a Goblin Warrens» | «Invia il tuo team alle Tane dei Goblin» |
| Slug/enum/campi API | — | **INVARIATI** (cambia solo la rappresentazione player-facing) |
| Censimento automatico | — | BE `test_fase10_italianizzazione.py` (7 test: ogni dungeon/raid seedato risolve nome IT ≠ EN; serializer legacy; narrativa; email) + FE `dungeon_raid_it_census.test.js` (scan statico sorgenti contro toast EN vietati; copertura `raids.catalog` 9/9; helper IT-first) |

Acceptance del mandato verificata in test: doc legacy `"Goblin Warrens"` → `dungeon_name_it == "Tane dei Goblin"`.

## 10C-F — Beni di Gilda — **PASS**

| Requisito | Esito |
|---|---|
| Cap 120 (`GUILD_SUPPLIES_CAP`) | **PASS** — nessun accredito può superarlo (CAS-loop `min(cap, cur+n)`; 118+5 → 120, testato) |
| Refill giornaliero 00:00 → 120 (non +120) | **PASS** — refill = «qualsiasi saldo → 120», lazy + idempotente via CAS su `guild_supplies_last_refill` (giorno UTC, stessa convenzione del reset giornaliero quest/streak: **nessun secondo scheduler**). Doppio trigger stesso giorno = zero effetti (testato). |
| Mercato 100 Beni / 2000 MO | **PASS** — endpoint dedicato, atomico su oro+cap; **bloccato** se anche un solo Bene andrebbe perso, con 409 che riporta saldo/cap/pacchetto/persi (es. 85/120 → «perderesti 65») → la UI comunica tutto, nessun comportamento nascosto; conferma esplicita in 2 click nel Mercato; 409 dedicato per oro insufficiente. |
| Dungeon manuale +5 | **PASS** — solo completamento **manuale riuscito**, dentro il motore condiviso (idempotente per claim CAS); **negato all'AUTO**. |
| Raid +50 | **PASS** — su raid **vinto** (victory), nel finalize claimato CAS (una volta sola). |
| Missione +10 | **PASS** — audit sistemi «missione»: il completion event canonico è quello delle **missioni risorse** (`resource_gathering_missions`, evento `on_resource_mission_completed`); reward su successo con marker CAS per `mission_id` (mai doppio). |
| Visualizzazione | **PASS** — Dashboard (hero stat «Beni di Gilda X / 120»), pagina Dungeon (badge), punto di scelta modalità (ExpeditionNew: «Beni disponibili: X / 120»), Mercato (card pacchetto). Tooltip del mandato ovunque. |
| Fallback gilde esistenti | **PASS** — campo assente → 120 (`effective_supplies`), schema backward-compatible: **nessuna migration necessaria** (backfill lazy al primo tocco del giorno). |

## 10G-L — Dungeon automatici — riepilogo scorecard

| Requisito | Esito |
|---|---|
| Gate first-clear manuale | **PASS** — AUTO solo per dungeon a stanze con `manual_dungeon_clears.<slug>` sul doc gilda (scritto SOLO dal finalize manuale riuscito); 409 `auto.manual_first_clear_required` altrimenti (testato). |
| AUTO non sblocca / non è first clear | **PASS** — le run auto NON aggiornano mai `manual_dungeon_clears` e il gate `min_total_expeditions_completed` ora esclude `auto_mode` (testato). |
| Costo 15 al dispatch | **PASS** — `spend_supplies` atomico ($gte, mai saldo negativo, retry non addebita due volte), pagato dopo TUTTE le validazioni; messaggio «Beni di Gilda insufficienti. Servono 15 Beni di Gilda.» (testato). |
| Durata ×1.20 | **PASS** — durata per stanza ×1.20 sul percorso; esempio esatto del mandato in test: 5m+8m+7m = 20m → **24m**. Totale esposto (`auto_total_duration_seconds`) e mostrato («durata 24m»). |
| Route replay | **PASS** — il clear manuale salva lo snapshot FINALE (lineare, bivi risolti) + `base_chance`; l'AUTO lo rimaterializza: stessa sequenza, chance ricalcolate per la squadra attuale preservando i modificatori congelati, **mai branch nuovi/segreti** (i fork non risolti vengono scartati — testato). Default = ultimo completamento manuale valido (un clear successivo su altro ramo lo sostituisce). |
| Nessun click | **PASS** — in AUTO `_resolve_current_room` passa direttamente alla stanza successiva (CAS `in_room idx → in_room idx+1`): niente `awaiting_choice`, azioni manuali rifiutate (409 `rooms.auto_mode`); sweep con recupero in cascata delle stanze scadute. |
| Squadra occupata | **PASS** — lock invariato per tutta la durata (release solo al finalize). |
| Loot/XP canonici | **PASS** — stesso motore del manuale (PWR, chance, loot, reagenti, Pietra della Conoscenza, XP, Overpower, equip, consumabili): **nessuna seconda loot table**. Differenze dell'AUTO: −15 Beni, +20% tempo, zero click. |
| AUTO senza +5 Beni | **PASS** — guardia esplicita nel motore di completamento. |
| RAID AUTO | **DISABLED** — nessun pulsante in UI, nessun campo/endpoint backend; registrato come futura possibilità in `memory/backlog.md` (FASE10.backlog). |

## 10M-N — Riposo — **PASS**

- `rest_used = false` alla partenza di ogni spedizione a stanze; primo «RIPOSA E PROCEDI» → bonus canonico (+8% chance, +25% durata stanza successiva) e `rest_used = true`; secondo tentativo → 409 `rooms.rest_already_used` (**max 1 per intero dungeon**, non per stanza) con backstop CAS `rest_used ≠ true` contro race/double-click (testato).
- UI: pulsante sostituito da «⛺ Riposo già utilizzato» (pannello scelte E pannello bivi); PROCEDI **sempre disponibile** (testato).
- AUTO: nessun riposo, nessun rest bonus (avanzamento sempre `rest=False`) (testato).

## 10O-P — UI modalità + notifiche — **PASS**

- ExpeditionNew: sezione **MODALITÀ** con card `MANUALE` («Gioca stanza per stanza. Puoi usare Riposa e Procedi una volta.») e `AUTOMATICA` («15 Beni di Gilda · +20% durata · Nessuna scelta durante la spedizione», durata stimata), saldo «Beni disponibili: X / 120», stati bloccati «Prima completa il dungeon manualmente» / «Beni insufficienti».
- Notifiche AUTO in italiano con nome IT: toast «Spedizione automatica iniziata — Tane dei Goblin — durata 24m»; card dashboard «Spedizione automatica completata: <nome IT>» per le run concluse non lette; banner nel report della run auto.

## 10Q — Audit — **PASS**

Registrati (e usati) in `audit/log.py`: `guild_supplies_market_purchase`, `guild_supplies_daily_refill`, `guild_supplies_dungeon_reward`, `guild_supplies_raid_reward`, `guild_supplies_mission_reward`, `auto_dungeon_dispatched`, `auto_dungeon_completed`, `dungeon_rest_used`. Tutti i reward sono idempotenti (claim CAS di spedizioni/raid; marker CAS per missioni; filtro-giorno per il refill).

## 10S — Migration / DB — **PASS (nessuno script necessario)**

- Nuovi campi tutti backward-compatible con fallback: `guild_supplies` (assente → 120), `guild_supplies_last_refill` (assente → refill al primo tocco), `manual_dungeon_clears` (assente → AUTO bloccato, corretto by design), `rest_used` (assente → false), `auto_mode` (assente → false), `dungeon_name_it`/`raid_name_it` (assenti → risolti dal serializer via slug/nome EN).
- **Nessuna scrittura production autonoma**: zero script `--apply` in questa tranche; il backfill è lazy e idempotente dentro i normali flussi server.

## 10R — Verifiche

| Verifica | Esito |
|---|---|
| Backend puri (`pytest --noconftest`, senza Mongo) | **172 passed, 0 failed** (106 skipped: dipendenze opzionali/httpx). Nuovi: class_assignment 6 · italianizzazione 7 · guild_supplies 8 · auto_dungeon 10. |
| Test stantii sanati | `test_t3_raid_contract` (poteri raid pre-FASE 8 → canonici 3100/7700/10925/24100), `test_career_revamp_contract` (5 fondatori gratuiti → 6, FASE 9A). |
| Esclusi (limite ambiente, NON regressioni FASE 10) | `test_save_as_squad.py` (TestClient+DB reale), `test_db_isolation_selftest.py` (subprocess sul Python globale privo di pytest). Invariati da prima della tranche. |
| Frontend Jest | **35/35** (6 suite; nuovi: journey 3 + censimento IT 3). |
| `yarn lint` | **0 errori / 0 warning**. |
| `yarn build` | **Compiled successfully**. |
| OpenAPI / boot | `create_app()` monta **319 route** (317 + `GET/POST /api/guild-supplies*`); import smoke pulito. |
| Sealed integrity | **PASS** — nessuno script/report sealed R18.* toccato. |
| Suite integrazione Mongo (`backend_phase*/round*`, requests/BASE_URL) | **NON eseguibile in locale** (nessun MongoDB/Docker su questa macchina): da eseguire sull'ambiente con DB, come per le fasi precedenti. |
| Working tree | pulito al momento del push. |
| Push | eseguito su `origin/main` e verificato con `git ls-remote`. |

## Criteri non negoziabili — verifica finale

- ✔ Un nuovo avventuriero **può** scegliere la classe (root cause riprodotta, fixata, regressione permanente).
- ✔ Nessuna notifica Dungeon/Raid player-facing con nomi inglesi (server-authoritative + censimento automatico anti-regressione).
- ✔ AUTO **impossibile** prima del primo completamento manuale (gate 409 + test).
- ✔ AUTO **non può** esplorare branch mai completati (route replay lineare, fork scartati + test).
- ✔ RIPOSA E PROCEDI **max 1 volta** per dungeon (pre-check + CAS + UI + test).

## Filosofia implementata

```
MANUALE    = più interattivo e leggermente più efficiente
             (riposo 1×, +5 Beni, conta per sblocchi e first clear)
AUTOMATICO = comodità: 15 Beni di Gilda + 20% tempo, zero click,
             stessi loot/XP canonici, nessun riposo, nessuno sblocco
RAID       = sempre manuale, per ora (backlog FASE10)
```

## Passi successivi (richiedono ambiente DB / decisione owner — NON eseguiti)

1. Deploy del branch → i seed di boot restano invariati (nessun nuovo seed in FASE 10).
2. Suite integrazione completa con Mongo (`pytest backend/tests` + `backend_phase*/round*`).
3. Collaudo manuale: nuova recluta → scelta classe (5 classi campione); notifiche IT; refill 00:00; mercato 100/2000 col cap; +5/+50/+10; primo clear manuale → sblocco AUTO → run auto (costo 15, durata +20%, nessun click, niente +5); riposo 1×.
4. Go-live su orbusonline.net: esclusivamente decisione dell'owner.
