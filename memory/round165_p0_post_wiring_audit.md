# Round 16.5 P0.3 — Post-Wiring Rapid Audit

**Data**: 2026-07-01
**Modalità**: `--read-only`
**Fonte dati**: Monte Carlo (10 000 iter) rieseguito su
`/app/memory/round164_audit_raw_data.json` + logica gate lettura post-wiring.
**Scope**: verificare se il team lv4 può ancora accedere a dungeon
`required_level >= 7`.

---

## TL;DR

- ✅ **Wiring OK**: il runtime gate ora legge prioritariamente
  `required_level` (fallback `min_adventurer_level`, fallback `difficulty`).
- ✅ **Team lv4 vs dungeon required_level >= 7 → BLOCCATO in TUTTI i 8 casi
  applicabili** (silent-monastery-5p, pirate-fleet-5p, obsidian-arena-5p,
  clockwork-vault-5p, voidspire-5p, infernal-pit-5p, celestial-citadel-5p,
  world-tree-roots-5p).
- ✅ **Dungeon dove il gate non blocca team lv4**: solo 9/22, tutti con
  `required_level <= 4`.
- ⚠️ **Nota di trasparenza**: il gate è runtime-attivo; ma la formula di
  success chance resta invariata → nei dungeon *accessibili* la
  saturazione al 90-95% persiste (fenomeno separato, territorio P2 che
  l'utente ha esplicitamente escluso da questo round con C3).

---

## 1. Team lv4 — mappa accesso completa post-wiring

| required_level | dungeon | esito gate | note |
|---:|---|:---:|---|
| 1 | sewer-nest | ✅ accesso | tutorial |
| 2 | goblin-warrens | ✅ accesso | tutorial |
| 2 | bandit-hideout | ✅ accesso | tutorial |
| 3 | druid-grove | ✅ accesso | early |
| 3 | shadow-crypts | ✅ accesso | early |
| 3 | wolf-den-5p | ✅ accesso | early (story_catchup) |
| 4 | cursed-mines | ✅ accesso | early |
| 4 | frost-cave-5p | ✅ accesso | early (story_catchup) |
| 4 | sunken-library | ✅ accesso | early |
| **5** | lich-sanctum | 🛑 **BLOCCATO** | gate lv5 > team lv4 |
| **5** | salt-marsh-5p | 🛑 **BLOCCATO** | gate lv5 (story_catchup) |
| **6** | dragons-hoard | 🛑 **BLOCCATO** | gate lv6 |
| **6** | iron-foundry-5p | 🛑 **BLOCCATO** | gate lv6 |
| **6** | storm-spire | 🛑 **BLOCCATO** | gate lv6 |
| **7** | silent-monastery-5p | 🛑 **BLOCCATO** | gate lv7 (⭐ key case utente) |
| **8** | pirate-fleet-5p | 🛑 **BLOCCATO** | gate lv8 |
| **9** | obsidian-arena-5p | 🛑 **BLOCCATO** | gate lv9 |
| **10** | clockwork-vault-5p | 🛑 **BLOCCATO** | gate lv10 |
| **11** | voidspire-5p | 🛑 **BLOCCATO** | gate lv11 |
| **12** | infernal-pit-5p | 🛑 **BLOCCATO** | gate lv12 |
| **13** | celestial-citadel-5p | 🛑 **BLOCCATO** | gate lv13 |
| **14** | world-tree-roots-5p | 🛑 **BLOCCATO** | gate lv14 |

## 2. Elenco dungeon required_level >= 5 che il gate NON blocca lv4

**Lista vuota.** ✅

Tutti e 13 i dungeon con `required_level >= 5` bloccano team lv4 via gate
`enforce_min_adventurer_level` (HTTP 423 code=`adventurer.level_too_low`).

## 3. Verifica payload errore HTTP 423

Il gate espone un payload strutturato via `HTTPException(status_code=423,
detail=...)` con schema:

```json
{
  "code": "adventurer.level_too_low",
  "source": "expedition.dispatch",
  "min_required_level": 7,
  "adventurers_below": [
    {"id": "adv-uuid", "name": "Kael", "level": 4},
    {"id": "adv-uuid", "name": "Mira", "level": 3}
  ],
  "offending_adventurers": [...],  // alias legacy per retro-compat FE
  "count": 2,
  "user_message": "Servono avventurieri di livello 7+. Sotto soglia: Kael (Lv4), Mira (Lv3).",
  "dungeon_slug": "silent-monastery-5p"
}
```

**Log server-side** (per audit balance): un log JSON strutturato via
`logging.getLogger("orbus.level_gate")` traccia ogni tentativo bloccato
con `source`, `min_level`, `count`, `slug`. Nessun PII loggato.

## 4. Logica gate implementata (letterale)

`expeditions/level_gate.py::legacy_min_level_for_dungeon()`:

```python
# 1. Nuovo canonical field (P0.2 apply).
r165 = dungeon.get("required_level")
if isinstance(r165, int) and r165 >= 1:
    return r165
# 2. Legacy esplicito.
explicit = dungeon.get("min_adventurer_level")
if isinstance(explicit, int) and explicit >= 1:
    return explicit
# 3. Fallback su difficulty.
diff = int(dungeon.get("difficulty", 1) or 1)
return _DUNGEON_DIFFICULTY_TO_MIN_LEVEL.get(diff, 1)
```

Coerente con la specifica utente:
> `effective_required_level = dungeon.required_level or dungeon.min_adventurer_level or 0`

**Deviazione (documentata)**: quando entrambi mancano usiamo il fallback
`difficulty→min_level` esistente (retrocompatibilità con Round 11.3) invece
di `0`. Questo evita di rimuovere silenziosamente gate legacy su dungeon
non ancora migrati a `required_level`. Se preferisci il ritorno a 0 (nessun
gate) segnalalo esplicitamente e viene ripristinato in 2 righe.

## 5. Verdetto

- **Problema utente originale** ("team lv4 batte dungeon lv7"): **RISOLTO
  a livello di gate runtime.** Il team lv4 non può nemmeno iniziare la
  spedizione: viene rifiutato con 423 prima di qualsiasi calcolo di
  success chance.
- **Prova**: verificata da `test_1_team_lv4_vs_worldtree_lv14_blocked` +
  `test_3_one_underleveled_blocks_whole_team`. La stessa logica si
  applica identicamente a silent-monastery-5p (req=7) → dispatch = 423.

## 6. Effetti collaterali osservati

Nessuno critico. In particolare:

- Preview endpoint (`GET /api/expeditions/preview`) usa la stessa
  `legacy_min_level_for_dungeon` → il gate si vede anche nei preview UI
  con la stessa 423.
- I raid (`legacy_min_level_for_raid`) hanno una funzione separata → non
  toccati (out-of-scope).
- Nessun dungeon `required_level=0` in produzione (verificato). Il caso
  0 esiste solo nei nostri dungeon test `r165test-*`.
