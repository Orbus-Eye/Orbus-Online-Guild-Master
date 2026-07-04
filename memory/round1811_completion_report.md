# ROUND 18.1.1 — Safety Hotfix + Roadmap Expansion · Completion Report — CLOSED & SEALED ✅

**Round:** R18.1.1 (Adventurer Identity — Safety Hotfix)
**Data completamento:** 2026-07-04
**Data SEAL:** 2026-07-04T18:33:00Z
**Autorizzato dal PM:** opzione D (mini-round bridge tra R18.1 e R18.2)
**Sigillato dal PM:** post-brief 2026-07-04T18:40Z (R18.0b 27-class ingestion)
**Autore agent:** e1 main agent
**DB target:** `orbus_r16` (dev/preview live)
**Scope:** 2 hotfix tecnici additivi + roadmap expansion documentation. Feature flag `R18_REWORK_ENABLED=false` OFF. Zero player-facing impact.

> **⚠️ NON RIAPRIRE senza nuovo brief PM esplicito.**

---

## Sommario esecutivo

R18.1.1 chiude i 2 residui tecnici di R18.1:
1. **Canonical roster level formula** — `la lanterna di ferro` cap 22 → 40 (unica guild reale impattata)
2. **Guard `recruit_unassigned` su expedition dispatch** — HTTP 400 con messaggio IT

E apre la roadmap R18 espansa (12 sezioni, 24 domande PM P0-P3, 9 fasi da R18.0b a R18.7). Nota: la roadmap è basata su target **15 classi** (versione ante-brief 2026-07-04T18:35Z). Il PM ha successivamente sigillato **27 classi canoniche** — le sezioni §2 (Class Canon) e §3 (Talent Tree scale) del documento sono superate. L'audit R18.0b ripartirà da 27 classi.

---

## Hotfix 1 — Canonical Roster Level Formula

### Decisione PM sigillata
```
effective_level = max(guild.level or 0, guild.guild_level or 0, 1)
max_roster_cap  = min(50, 10 + effective_level * 2)
```

### Diff atteso vs applicato
- **Drift totale** `level != guild_level` (entrambi settati): **207/303** guilds
- **Cap effettivamente cambiato con nuova formula:** **1 sola guild reale** (`la lanterna di ferro`)
- Motivo: le altre 206 guilds con drift avevano `guild_level ≥ level` → formula precedente (`guild_level or level`) restituiva già il valore massimo

### La Lanterna di Ferro — before/after
| Field | Before | After |
|---|---|---|
| `level` | 15 | 15 |
| `guild_level` | 6 | 6 |
| `r18_effective_level` | (assente) | **15** |
| `max_roster_cap` | 22 | **40** |
| `current_roster_size` | 23 | 23 |
| `is_grandfathered` | true | **false** |

### Script `round1811_roster_cap_hotfix.py`
Path: `/app/backend/app/scripts/round1811_roster_cap_hotfix.py` (210 righe)
Contract:
- `--dry-run` (default): scan diff + report top changes, zero write
- `--apply`: aggiorna solo doc con `cap_changed OR gf_changed`
- Feature-flag guard: aborta se `R18_REWORK_ENABLED != false`
- Marker: `r18_roster_cap_recomputed_at` (iso timestamp) + `r18_effective_level` (int)
- Audit event: `R18_ROSTER_CAP_RECOMPUTED` emesso in `audit_log` con top-20 diff (solo se `updated > 0`)

### Idempotenza verificata
| Run | Guilds scanned | Cap/GF changed | Guilds updated | Audit event |
|---|---|---|---|---|
| Dry-run | 303 | 1 | 0 (preview) | 0 |
| Apply #1 | 303 | 1 | 1 | 1 emesso |
| Apply #2 | 303 | 0 | 0/0 | 0 (no-op guard) |

### Whitelist admin audit
File modificato: `/app/backend/app/admin/audit_routes.py`  
Aggiunto `R18_ROSTER_CAP_RECOMPUTED` a `AUDIT_EVENT_WHITELIST` frozenset. Verificato via API admin: `GET /api/admin/audit/events?event_type=R18_ROSTER_CAP_RECOMPUTED&limit=50` → **200 OK**.

---

## Hotfix 2 — Guard `recruit_unassigned` su Expedition Dispatch

### Regola
Nel service `_validate_and_persist_expedition` (path unico `POST /api/expeditions` + `/api/expeditions/preview`):
```python
_playable_slugs = set slug WHERE is_playable != false FROM adventurer_classes
for adv in members_live:
    if adv.class_slug == "recruit_unassigned"
       OR not adv.class_slug
       OR adv.class_slug not in _playable_slugs:
        raise HTTPException(400, detail={
            "code": "adventurers.recruit_unassigned_in_set",
            "source": "expedition.dispatch",
            "unassigned_adventurers": [...],
            "count": N,
            "user_message": "Questo avventuriero non ha ancora una classe assegnata. Riassegnalo prima di mandarlo in missione."
        })
```

### File modificato
`/app/backend/app/expeditions/services.py` (+38 righe in `_validate_and_persist_expedition`)

### E2E HTTP verified
1. Login `tester@orbus.test` + CSRF token acquired
2. Inject temporaneo: `adventurer aac9f4dd (name=Test-Mage-R1654c)` DB update `class_slug` mage → recruit_unassigned
3. `POST /api/expeditions` con 3-adv team incluso l'orfano
4. Response: **HTTP 400** con body identico allo schema atteso, user_message IT esatto
5. Rollback: `class_slug` → mage (verified)

Backend log:
```
INFO: POST /api/expeditions HTTP/1.1 400 Bad Request
INFO: POST /api/expeditions HTTP/1.1 201 Created (baseline normal dispatch)
```

### Perché NON esteso a raid/resource
- **Raid start**: flow diverso, non selezione `adventurer_ids` diretta (usa party dinamica)
- **Resource missions**: endpoint non accetta `adventurer_ids` come parametro (auto-selection interno)
- Deferred a **R18.4** con brief dedicato quando class-bound HARD arriverà

---

## Test suite R18.1 aggiornata

**Comando:** `cd /app/backend && PYTHONPATH=/app/backend python -m pytest tests/backend_round181_migration_test.py -c /dev/null -p no:cacheprovider --confcutdir=/tmp -v`

**Risultato:** **18/18 PASSED in 0.08s** ✅

| # | Test | Result |
|---|---|---|
| 01-10 | (preserved from R18.1) | ✅ |
| 11 | `soft_no_hard_block` — **RISCRITTO** per canonical formula (verifica `la lanterna di ferro` cap=40 + `r18_effective_level=15` + `is_grandfathered=False`) | ✅ |
| 12-17 | (preserved from R18.1) | ✅ |
| 18 | `expedition_guardrail_recruit_unassigned_active` — **RISCRITTO** per guard attivo (verifica marker `recruit_unassigned_in_set` + `Riassegnalo prima di mandarlo in missione` + `is_playable` in codice service) | ✅ |

---

## Roadmap R18 espansa

**File creato:** `/app/memory/round18_progression_rework_roadmap.md` (**644 righe**)

**Contenuto (12 sezioni)**:
1. Onboarding avventurieri (recruit + training field, prima classe gratuita, D11 REOPENED)
2. **15 classi canoniche + Class Canon Audit R18.0b** — ⚠️ SUPERATO da nuovo sigillo PM 27 classi
3. Talent tree 3×5×4 = 60 slot/classe, 30 punti — scala superata (era 15×60=900, ora 27×60=1620)
4. PWR solo da oggetti (R18.5)
5. Livello max 60 + 3 varianti curva XP (Casual/Standard/Hardcore)
6. Item power tier ogni 10 lvl (Modello A bracket vs Modello B breakpoint)
7. Item class-bound roadmap 5 fasi (SOFT → Audit → HARD → Smart loot → Auto-equip)
8. 100 dungeon + 20 raid distribuzione proposta
9. Grade Common→Legendary + 3 criteri anti-farm
10. Tomi & Maestria di Classe
11. Roster max 50 (chiuso in R18.1.1)
12. Dungeon/raid rework obbligatorio (R18.6+R18.7)

**24 domande PM aperte** numerate P0 (5) / P1 (7) / P2 (7) / P3 (5).

**Raccomandazione**: R18.0b (Class Canon Audit) prima di R18.2.

**Nota importante post-brief 2026-07-04T18:40Z**: PM ha sigillato target **27 classi canoniche**. Sezioni §2 e §3 del documento sono superate. Il nuovo audit R18.0b lavorerà su 27 classi (Alchimista, Artificiere, Astrologo, Bardo, Burattinaio, Cacciatore del Sangue, Cacciatore del Vuoto, Cacciatore di Mostri, Cartografo, Cavaliere della Morte, Cavaliere di Draghi, Cronista, Druido, Fabbro Arcano, Giocatore d'Azzardo, Guerriero, Ladro, Mago, Mercante, Monaco, Negromante, Paladino, Parassita, Pittore, Runista, Sciamano, Sognatore). Scala talent tree teorica ricalcolata: 27 × 60 = **1620 slot**.

---

## File toccati (finali)

| File | Type | Note |
|---|---|---|
| `backend/app/scripts/round1811_roster_cap_hotfix.py` | NEW (210 righe) | Hotfix 1 script |
| `backend/app/expeditions/services.py` | MODIFIED (+38 righe) | Hotfix 2 guard |
| `backend/app/admin/audit_routes.py` | MODIFIED (+1 event whitelist) | R18_ROSTER_CAP_RECOMPUTED |
| `backend/tests/backend_round181_migration_test.py` | MODIFIED (test_11 + test_18 riscritti) | Riflette nuova realtà |
| `memory/round18_progression_rework_roadmap.md` | NEW (644 righe) | Roadmap working doc |
| `memory/orbus_world_roadmap.md` | UPDATED (+22 righe) | Nuova sequenza R18 in cima |
| `memory/round1811_completion_report.md` | NEW (this file) | Completion + SEAL |

---

## Guardrail rispettati

- ✅ **Zero hard delete** (solo `$set` update in DB, insert audit event)
- ✅ **Zero frontend touched** (`/app/frontend/**` invariato)
- ✅ **Zero modifiche a economia/PvP/premium/drop/reward/auto-equip/combat math**
- ✅ **Feature flag `R18_REWORK_ENABLED=false` OFF preservato** (verificato via script guard)
- ✅ **Idempotenza confermata** (dry-run + apply + 2nd apply = 0 modifiche)
- ✅ **Raid/Resource extension NOT applied** (deferred a R18.4 con brief dedicato)

---

## Comandi riproducibili

```bash
# Hotfix 1 apply
cd /app/backend && PYTHONPATH=/app/backend python -m app.scripts.round1811_roster_cap_hotfix --dry-run
cd /app/backend && PYTHONPATH=/app/backend python -m app.scripts.round1811_roster_cap_hotfix --apply

# Test suite
cd /app/backend && PYTHONPATH=/app/backend python -m pytest \
  tests/backend_round181_migration_test.py -c /dev/null \
  -p no:cacheprovider --confcutdir=/tmp -v

# Verify Hotfix 2 (guard) via HTTP
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
TOKEN=$(curl -s -X POST "$API_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@orbus.test","password":"password123"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
CSRF=$(curl -s "$API_URL/api/auth/csrf" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['csrf_token'])")
# (poi inject class_slug=recruit_unassigned via DB update + POST /api/expeditions)

# Verify audit event whitelist
curl -s "$API_URL/api/admin/audit/events?event_type=R18_ROSTER_CAP_RECOMPUTED&limit=5" \
  -H "Authorization: Bearer $TOKEN" -H "X-CSRF-Token: $CSRF" \
  | python3 -m json.tool
```

---

**Firmato:** e1 main agent · 2026-07-04T18:33Z · R18.1.1 CLOSED & SEALED ✅
