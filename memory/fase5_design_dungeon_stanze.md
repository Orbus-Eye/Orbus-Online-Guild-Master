# FASE 5 — Design: dungeon a stanze
Data: 2026-08-08 · Branch: Lavoro-partito-08/08/2026 · Stato: implementato (pilota)

## 0. Principi

- **Rollout a pilota, dietro flag.** Il refactor NON tocca il flusso legacy:
  i dungeon in `ROOMS_PILOT_SLUGS` partono "a stanze", tutti gli altri
  restano single-block. Flag globale `ROOMS_MODE_ENABLED` per spegnere
  tutto all'istante. Piloti iniziali: `sewer-nest` (3p tutorial) e
  `goblin-warrens` (5p base).
- **Un solo timer.** Il sistema riusa il campo `completes_at` e la lazy
  sweep esistente (`complete_due_expeditions`): in modalità stanze il
  timer rappresenta la stanza corrente (o la scadenza della decisione).
  Niente scheduler nuovi, niente stati orfani.
- **Riuso dei mattoni di completamento.** XP per membro (trait/Arfus/
  debuff/catch-up/consumabile), accredito loot/materiali e gli hook
  post-completamento sono estratti in helper condivisi usati sia dal
  legacy sia dal finalize a stanze: una sola verità per l'economia.

## 1. Data model

`dungeons` non cambia. Le stanze sono AUTORATE in codice
(`app/dungeons/rooms.py`), come già DUNGEON_LORE: niente migrazioni.

Blueprint stanza: `{idx, slug, name_it, kind, duration_share, gold_share,
xp_share, chance_modifier, has_loot, narrative_it}`
- `kind ∈ {guard, ambient, treasure, boss}` — il boss è sempre l'ultima.
- Le share di oro/XP sommano a 1.0 (economia ≈ legacy).
- Dungeon facili 3 stanze, medi 4, difficili 5 (dal blueprint autorato;
  generatore di fallback deterministico per slug non autorati).

Sull'expedition doc (solo modalità stanze, campi additivi):
```
mode: "rooms"
rooms_snapshot: [ {…blueprint, chance, duration_seconds, gold, xp} ]   # congelato al dispatch
current_room_idx: int
room_state: "in_room" | "awaiting_choice"
rest_bonus_next: int            # +8 se il gruppo ha riposato
carried_gold / carried_xp: int  # maturati, EROGATI solo alla fine
carried_loot_ids: [item_id]     # bottino "in spalla"
room_results: [ {idx, name_it, success, roll, chance, gold, xp, loot_count, resolved_at} ]
decision_deadline: iso          # = completes_at durante awaiting_choice
```

## 2. Macchina a stati

```
dispatch ──► in_room (timer stanza)
   sweep due ─► risolvi stanza:
        successo & non ultima ─► awaiting_choice (completes_at = now+24h)
        successo & ultima     ─► FINALIZE completed
        fallimento            ─► FINALIZE failed (ritirata forzata)
awaiting_choice:
   POST /advance {action}:
        continue          ─► in_room (stanza successiva)
        rest_and_continue ─► in_room (timer stanza +25%, chance +8)
        escape            ─► FINALIZE escaped
   sweep oltre deadline   ─► auto-continue (mai run bloccate)
```
`status` resta `"in_progress"` fino al finalize → il lock del gruppo,
le liste e il cap attività funzionano invariati (vincolo J.20 gratis).

## 3. Probabilità per stanza

`chance_stanza = clamp(5, 100, chance_base ± modificatore)` dove
`chance_base` è la curva logistica di Fase 2 (threat inclusi) e i
modificatori sono: guard 0, ambient +5, treasure +5, boss −10.
Il riposo aggiunge +8 alla stanza successiva (una volta).

## 4. Economia (vincoli J.21)

Per stanza superata maturano: `gold = base_gold × gold_share`,
`xp = base_xp × xp_share`, e SOLO nelle stanze `has_loot`
(treasure/boss) un roll della loot table del dungeon. Tutto resta
"in spalla" (carried_*) fino al finalize:

| Esito | Oro | Item (selezione casuale) | XP | Reagente/Pietra/Overpower |
|---|---|---|---|---|
| **Completato** | 100% | 100% + extra Overpower | 100% **+25% bonus finale** | sì |
| **Fuga** | 50% | ogni item tenuto al 50% | 50% del maturato | no |
| **Sconfitta in stanza** | 25% | ogni item tenuto al 25% | 40% del maturato | no |

- L'XP si eroga SOLO al finalize (per-membro, con tutti i moltiplicatori
  esistenti). Il +25% finale premia il completamento vs farm di fuga.
- L'Overpower (moltiplicatore congelato al dispatch) si applica solo al
  bottino del completamento; reagente del dungeon e Pietra della
  Conoscenza solo a completamento: finire i dungeon conta.

## 5. API

- Dispatch: invariato (`POST /api/expeditions`) — se il dungeon è
  pilota, il doc nasce in modalità stanze.
- `POST /api/expeditions/{id}/advance` `{action: continue|rest_and_continue|escape}`
  → 409 se non in `awaiting_choice`; escape non chiede conferma lato
  API (la conferma è UX del FE).
- `GET /api/expeditions/{id}`: `expedition_public` espone i campi stanze;
  le stanze future mostrano solo il nome ("???" oltre la successiva —
  anti-spoiler coerente con la visibilità progressiva).

## 6. Frontend

- `ExpeditionReport.jsx` diventa la vista "run": timeline delle stanze
  (fatte ✓ / corrente con countdown / prossima / future oscurate),
  bottino in spalla, e il pannello scelta con i tre bottoni
  (Prosegui / Riposa e prosegui (+8%) / Fuggi con conferma a doppio
  click). Polling ogni 10s finché la run è viva.
- `Dungeons.jsx`: badge "⚑ A STANZE" sui dungeon pilota
  (`rooms_mode: true` in `dungeon_public`).

## 7. Rischi e mitigazioni

- **Run bloccate in attesa di scelta** → deadline 24h con auto-continue.
- **Doppio reward su retry della sweep** → il finalize passa dallo stesso
  claim CAS `in_progress → completing` del legacy (idempotente).
- **Drift economico** → share che sommano a 1.0 + test puri sui
  blueprint; l'unico delta voluto è il +25% XP al completamento.
- **Regressioni sul legacy** → estrazione helper condivisi coperta dal
  fatto che il legacy li chiama con gli stessi valori di prima; i
  dungeon non-pilota non cambiano percorso.

## 8. Fuori scope (prossime iterazioni)

Percorsi ramificati (scelta fra 2 stanze), eventi ambientali con skill
check per classe, ferite/morale per stanza, stanze per i raid. Il data
model li supporta (basta estendere blueprint e azioni).
