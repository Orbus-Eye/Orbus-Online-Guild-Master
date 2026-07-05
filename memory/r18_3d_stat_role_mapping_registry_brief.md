# R18.3d — Stat/Role Mapping Registry (BRIEF, non implementato)

**Stato**: 📋 **BRIEF PRONTO** — in attesa di GO PM esplicito per implementazione
**Data brief**: 2026-07-05T16:30:00Z UTC
**Autore**: e1_dev (su direttiva PM Messaggio 220)
**Origine**: Backlog HOLD storico + necessità di consolidare mapping stat↔role emersa durante R18.Reset.1b.hotfix.v1_3 e R18.Reset.2

---

## 1. Scope

Round dedicato per consolidare e sigillare un **Stat/Role Mapping Registry** ufficiale — la source-of-truth per la relazione fra classi avventuriero, ruoli operativi, e statistiche primarie/secondarie usate nei flussi runtime (recruitment, expedition scoring, combat resolution, forge bonuses, PvP matchmaking).

**Deliverable**:
- 1 registry JSON firmato in `/app/memory/r18_3d_stat_role_mapping_registry.json`
- 1 modulo Python read-only `/app/backend/app/core/stat_role_registry.py` che carica ed espone il registry
- 1 endpoint di introspezione `GET /api/system/stat-role-registry` (auth admin) per consumo tooling
- 1 test suite dedicata (contract + coverage 11/11 classi safe)
- 1 report closure dedicato

**Non-scope (esplicito)**:
- ❌ NON modificare i base_stats esistenti degli avventurieri (dominio catalog, gestito altrove)
- ❌ NON introdurre nuove classi né rinominare ruoli esistenti
- ❌ NON modificare la logica di combat/expedition/PvP (registry è read-only reference)
- ❌ NON toccare adventurers storici o `adventurer_classes` catalog
- ❌ NON hard delete di alcun documento
- ❌ NON risolvere in questo round `R18.1 drift`, `Traits`, `Fatigue/Cucina`, `SMTP R17` (rimangono in HOLD)

## 2. Contesto e razionale

Durante `R18.Reset.1b.hotfix.v1_3` è emerso che le 11 safe-classes (`alchemist`, `bard`, `druid`, `mage`, `monk`, `paladin`, `priest`, `ranger`, `rogue`, `warlock`, `warrior`) hanno un mapping stat/role implicito che è **replicato in almeno 4 punti del codice**:
- `adventurer_classes` catalog collection (source-of-truth attuale)
- script di reset `round18_reset1b_apply_v1_3.py` (per rigenerazione roster)
- logica di scoring expedition (backend service)
- filtri UI su recruitment/roster (frontend components)

**Rischio corrente**: schema drift silenzioso in caso di modifica non-coordinata a uno solo dei punti.

**Obiettivo**: consolidare **un solo file registry** letto ovunque, con validazione runtime a startup e test contract-locked.

## 3. Struttura del registry

**File**: `/app/memory/r18_3d_stat_role_mapping_registry.json`
**Formato**: JSON immutabile, sigillato via SHA256 nel registry di controllo.

**Schema draft**:
```json
{
  "registry_version": "R18.3d.v1",
  "generated_at": "<ISO UTC>",
  "seal_authority": "PM Orchestrator",
  "primary_stats": ["strength", "agility", "intellect", "endurance", "faith"],
  "roles": ["tank", "damage_melee", "damage_ranged", "damage_magic", "support_healer", "support_utility"],
  "classes": {
    "warrior": {
      "role": "tank",
      "primary_stat": "strength",
      "secondary_stats": ["endurance"],
      "base_stats_ref": "adventurer_classes.slug=warrior",
      "usable_in_expedition": true,
      "usable_in_pvp": true
    },
    "monk":     {"role": "damage_melee",   "primary_stat": "agility",   "secondary_stats": ["endurance"], "...": "..."},
    "rogue":    {"role": "damage_melee",   "primary_stat": "agility",   "secondary_stats": ["intellect"], "...": "..."},
    "ranger":   {"role": "damage_ranged",  "primary_stat": "agility",   "secondary_stats": ["intellect"], "...": "..."},
    "mage":     {"role": "damage_magic",   "primary_stat": "intellect", "secondary_stats": ["faith"],     "...": "..."},
    "warlock":  {"role": "damage_magic",   "primary_stat": "intellect", "secondary_stats": ["faith"],     "...": "..."},
    "priest":   {"role": "support_healer", "primary_stat": "faith",     "secondary_stats": ["intellect"], "...": "..."},
    "druid":    {"role": "support_healer", "primary_stat": "faith",     "secondary_stats": ["intellect"], "...": "..."},
    "paladin":  {"role": "tank",           "primary_stat": "strength",  "secondary_stats": ["faith"],     "...": "..."},
    "bard":     {"role": "support_utility","primary_stat": "intellect", "secondary_stats": ["agility"],   "...": "..."},
    "alchemist":{"role": "support_utility","primary_stat": "intellect", "secondary_stats": ["endurance"], "...": "..."}
  },
  "sha256_of_data": "<computed>"
}
```

**Nota**: i valori esatti `primary_stat` / `secondary_stats` andranno confermati **byte-exact** contro il catalog `adventurer_classes` live via task preliminare di allineamento (Fase A del round).

## 4. Fasi del round

**Fase A — Discovery & Alignment (read-only)**
- Estrazione dei mapping attuali dai 4 punti (catalog, script reset, expedition service, frontend)
- Diff matrix per identificare drift esistenti
- Compilazione del registry draft
- Peer review PM su mapping proposto

**Fase B — Consolidation (write, single point of change)**
- Salvataggio del registry JSON in `/app/memory/`
- Creazione modulo Python read-only `stat_role_registry.py` con loader + validator (lancia error a startup se JSON malformed o mismatch con catalog)
- Endpoint admin `GET /api/system/stat-role-registry`
- Refactor **conservativo** dei 4 consumer per leggere dal modulo unificato (una PR per consumer, no big-bang)
- Test suite dedicata

**Fase C — SEAL**
- SHA256 del registry JSON registrato
- Header "CLOSED & SEALED" nel test file
- Update PRD.md + closure report

## 5. Test attesi (elenco preliminare, PM rifinirà al GO)

1. Registry JSON schema-valid contro Pydantic model
2. Coverage 11/11 safe classes presenti nel registry
3. Nessuna classe extra (whitelist strict)
4. `primary_stat` di ogni classe presente in `primary_stats` list
5. `role` di ogni classe presente in `roles` list
6. `secondary_stats` è subset di `primary_stats` (no drift)
7. Consistency check runtime: `adventurer_classes` catalog live corrisponde al registry (id, name, base_stats primary)
8. Modulo Python `stat_role_registry` è read-only (no mutator method)
9. Endpoint `GET /api/system/stat-role-registry` richiede auth admin
10. Endpoint response byte-exact contro il file JSON
11. Startup del backend fallisce (fail-fast) se registry file missing o corrupt
12. Nessun consumer del registry può bypassare il loader (grep-based test)
13. Compatibilità retro: expedition scoring output identico pre/post-refactor per 100 casi campione
14. Compatibilità retro: recruitment filter output identico pre/post-refactor per 100 casi campione
15. SHA256 del registry file matches il valore nel registry di controllo (contract lock)

## 6. Rischi e mitigazione

- **Rischio**: drift esistente fra i 4 consumer → refactor rompe casi edge non documentati.
  - Mitigazione: Fase A discovery esaustiva + snapshot test pre-refactor.
- **Rischio**: PM può decidere modifica ai mapping durante peer review → churn implementativo.
  - Mitigazione: brief include placeholder mappings; **mapping finale confermato byte-exact prima di Fase B**.
- **Rischio**: fail-fast a startup su registry corrupt → blocco produzione se JSON viene malformato accidentalmente.
  - Mitigazione: validazione + backup su path alternativo, CI-check al deploy.
- **Rischio**: endpoint admin espone dati sensibili di balance → leak di formula PvP.
  - Mitigazione: auth admin obbligatoria, mai esposto a client non-admin.

## 7. Backup / Rollback

- Backup del catalog `adventurer_classes` **pre-refactor** (jsonl export) in `/app/backend/backups/r18_3d_pre_apply_<timestamp>/`.
- Rollback path: ripristino via `restore_from_jsonl_manifest` (script già sealed).
- Il registry file è puramente additivo → rimozione del modulo `stat_role_registry.py` + revert dei 4 consumer restaura lo stato pre-round.

## 8. Endpoint schema OpenAPI (draft)

```yaml
GET /api/system/stat-role-registry:
  summary: Read-only introspection of the Stat/Role Mapping Registry
  security:
    - bearerAuth: []
  responses:
    "200":
      description: OK — registry content byte-exact
      content:
        application/json:
          schema:
            type: object
            properties:
              registry_version: {type: string}
              generated_at: {type: string, format: date-time}
              primary_stats: {type: array, items: {type: string}}
              roles: {type: array, items: {type: string}}
              classes: {type: object, additionalProperties: {type: object}}
              sha256_of_data: {type: string}
    "401":
      description: Unauthorized (no JWT)
    "403":
      description: Forbidden (not admin)
```

## 9. GO checklist per PM (prima di autorizzare implementazione)

- [ ] Confermare mapping byte-exact delle 11 safe classes (primary_stat, secondary_stats, role) — SUB-TASK DEDICATO
- [ ] Confermare naming endpoint `GET /api/system/stat-role-registry` (o alternativa)
- [ ] Confermare nome file registry `/app/memory/r18_3d_stat_role_mapping_registry.json` (o alternativa)
- [ ] Confermare che Fase B refactor dei 4 consumer non tocca la logica business (solo cambio source-of-truth)
- [ ] Confermare priorità e sprint di inclusione
- [ ] Confermare che nessun altro round in HOLD (Traits, Fatigue/Cucina, SMTP R17) sarà toccato in questo round
- [ ] Confermare policy su `fail-fast at startup` in caso di registry corrupt (vs soft-fallback loggato)

---

**BRIEF PRONTO. Nessuna implementazione fino a GO PM esplicito.**

**Prossimo GO atteso**: autorizzazione PM Fase A (Discovery & Alignment) del round R18.3d.
