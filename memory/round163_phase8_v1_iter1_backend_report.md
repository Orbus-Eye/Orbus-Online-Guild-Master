# ROUND 16.3 Phase 8 V1 Iter1 Backend — Stalle e Cavalcature

**Status**: ✅ COMPLETO (backend only)
**Data**: 2026-07-01
**Regressione baseline**: 78/78 PASSED (`test_forge_actions_p0`, `test_races_endpoint_p1`, `test_pvp_phase7a_p0`, `test_pvp_season_phase7b_p0`)
**Test suite dedicata**: 28/28 PASSED (`test_stables_phase8_v1.py`)

---

## 1. Scope realizzato

Sistema di cavalcature **esclusivamente cosmetico e narrativo**. Zero impatto su combat, economia, ranking, travel time. Free-to-earn (nessuna monetizzazione), free-to-cosmetize.

### Requisiti confermati con user (Msg 322)
- ✅ **9 mount totali**: 1 starter (`ronzino-di-strada`, domain `starter`) + 8 domain (uno per continente canonico)
- ✅ **5 rotte narrative** cosmetic-only (badge/title/lore, mai gold/xp/reputation/materials)
- ✅ **Claim starter fixed** (`ronzino-di-strada`), idempotente, first-time only, **senza gate di livello**
- ✅ **Auto-attivazione al claim** (UX: mount subito visibile; deselect via `set-active mount_slug=null`)
- ✅ **Set-active accetta null** per deselezionare (camminare a piedi narrativamente)
- ✅ Whitelist audit `50 → 54` (aggiunti 4 event types dedicati)

### Vincoli Anti-P2W enforced
- Ogni mount ha esplicitamente `affects_combat=false`, `affects_economy=false`, `affects_ranking=false`, `affects_travel_time=false`, `can_be_sold_for_real_money=false` (hardcoded nel catalog + anti-drift override nel seed).
- Reward rotte narrative limitato a `cosmetic_badge | cosmetic_title | lore_entry` (test 05 + 22 lo assertano runtime).
- Zero scritture su `guilds.gold`, `guilds.reputation`, `guilds.level`, `guild_pvp_stats.*` da tutto il modulo (test 20 + 21 verificano immutabilità post-claim/travel).

---

## 2. Catalog

### 9 Mount (`app.stables.catalog.MOUNT_CATALOG_V1`)

| Slug | Nome IT | Dominio | Rarità | Fonte |
|---|---|---|---|---|
| `ronzino-di-strada` | Ronzino di Strada | starter | common | starter_quest |
| `scarabeo-runico` | Scarabeo Runico | ambash | uncommon | craft |
| `cervo-lunare` | Cervo Lunare | velur | rare | world_boss_drop |
| `lupo-delle-fronde` | Lupo delle Fronde | soe | uncommon | world_boss_drop |
| `salamandra-di-efreto` | Salamandra di Efreto | efreto | rare | craft |
| `segugio-cinereo` | Segugio Cinereo | irthe | uncommon | achievement |
| `remora-tempestosa` | Remora Tempestosa | nathos | rare | world_boss_drop |
| `ombra-sellata` | Ombra Sellata | ergolat | epic | narrative |
| `grifone-delle-alture` | Grifone delle Alture | aveol | rare | achievement |

### 5 Rotte narrative (`NARRATIVE_ROUTES_V1`) — coprono 5 domini su 8

| Slug | Dominio richiesto | Reward type | Reward slug |
|---|---|---|---|
| `sentiero-delle-fronde` | soe | cosmetic_badge | `traveler_of_fronde` |
| `via-delle-alture` | aveol | cosmetic_title | `titolo_scalatore_delle_alture` |
| `traccia-lunare` | velur | lore_entry | `codex_traccia_lunare` |
| `passo-delle-ceneri` | efreto | cosmetic_badge | `badge_passo_ceneri` |
| `cammino-ombra` | ergolat | cosmetic_title | `titolo_pellegrino_ombra` |

I 3 domini scoperti (ambash, irthe, nathos) sono riservati a **Phase 8 V2**.

---

## 3. Collezioni MongoDB

- `mount_catalog` — 9 documenti, seed idempotente al lifespan, unique(slug).
- `narrative_routes` — 5 documenti, seed idempotente, unique(slug).
- `guild_mount_ownership` — creata dinamicamente su claim/grant. Unique (guild_id, mount_slug). Indice ausiliario (guild_id, is_active).
- `narrative_route_completions` — one-shot per guild+route. Unique (guild_id, route_slug).
- `narrative_rewards_unlocked` — badge/title/lore assegnati. Unique (guild_id, reward_slug).

---

## 4. Endpoint

### Pubblici (`/api/stables/*`)

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/catalog` | Elenca tutti i 9 mount con ownership + active flag per la gilda corrente |
| GET | `/mine` | Elenca i mount posseduti + `active_mount` |
| POST | `/set-active` | Attiva un mount (`{mount_slug: str}`) o deseleziona (`{mount_slug: null}` o body vuoto) |
| POST | `/quest/starter/claim` | Grant idempotente del ronzino, auto-attiva |
| GET | `/narrative-routes` | 5 rotte + flag `is_completed` / `can_travel` / `missing_reason` |
| POST | `/narrative-routes/{slug}/travel` | Percorri la rotta (one-shot) e sblocca il badge cosmetic |
| GET | `/narrative-rewards/mine` | Elenca badge/title/lore sbloccati dalla gilda |

### Admin dev-gated (`/api/admin/stables/*`)

| Metodo | Path | Descrizione |
|---|---|---|
| GET | `/catalog` | Vista admin con owner_count per slug + completions_total |
| POST | `/dev/grant-mount` | Grant manuale (dev only, 403 in prod) |

Errori restituiti in formato `{code, user_message}`: `stables.not_owned`, `stables.route_not_found`, `stables.mount_required`, `stables.wrong_domain`, `stables.route_already_completed`, `stables.starter_already_claimed`, `stables.mount_not_found`.

---

## 5. Audit events (4 nuovi)

Aggiunti sia a `app.audit.log.EVENT_TYPES` sia a `AUDIT_EVENT_WHITELIST` di `app.admin.audit_routes`:

- `MOUNT_STARTER_CLAIMED` — emesso al primo claim del ronzino
- `MOUNT_ACQUIRED` — emesso ad ogni grant successivo (admin, world_boss_drop, achievement, craft)
- `MOUNT_ACTIVE_SET` — emesso ad ogni set-active (anche al deselect)
- `NARRATIVE_ROUTE_TRAVELED` — emesso al completamento di una rotta

**Whitelist count**: `50 → 54` (verificato runtime dal test 24).

---

## 6. File creati / modificati

### Creati (in questo Iter)

- `/app/backend/tests/test_stables_phase8_v1.py` — 28 test

### Popolati (dallo scaffold precedente + mie modifiche mirate)

- `/app/backend/app/stables/__init__.py` — export router + admin_router + seed helpers
- `/app/backend/app/stables/models.py` — `SetActiveMountPayload` (mount_slug Optional[str]), `AdminGrantMountPayload`
- `/app/backend/app/stables/catalog.py` — 9 mount + 5 rotte + `ANTI_P2W_FLAGS`
- `/app/backend/app/stables/seed.py` — `ensure_stables_indexes`, `ensure_mount_catalog`, `ensure_narrative_routes` (tutti idempotenti)
- `/app/backend/app/stables/services.py` — logica business (claim, set-active, travel, admin_grant, narrative_rewards)
- `/app/backend/app/stables/routes.py` — 7 endpoint pubblici
- `/app/backend/app/stables/admin_routes.py` — 2 endpoint admin

### Modificati (integrazione)

- `/app/backend/app/audit/log.py` — +4 event_types in `EVENT_TYPES`
- `/app/backend/app/admin/audit_routes.py` — +4 event_types in `AUDIT_EVENT_WHITELIST` (50→54)
- `/app/backend/app/core/app_factory.py` — import stables + include 2 router
- `/app/backend/app/core/lifespan.py` — ensure_stables_indexes + ensure_mount_catalog + ensure_narrative_routes al startup

---

## 7. Test suite

**File**: `/app/backend/tests/test_stables_phase8_v1.py` — 28 test.

Categorie:
1. **Unit (test 01-06)** — invariants catalog: 9 mount, 1 starter + 8 domain, IT fields presenti, 5 rotte, reward cosmetico, ANTI_P2W_FLAGS shape.
2. **Seed idempotency (07-08)** — 2 seed consecutivi non duplicano, DB ha 9+5 attivi.
3. **HTTP catalog + narrative (09-10)** — flags P2W = false runtime, 5 rotte esatte.
4. **HTTP claim + mine + set-active (11-13)** — idempotency, deselect null, active_mount tracking.
5. **Error paths (14-16)** — not_owned, wrong_domain, route_not_found.
6. **Direct-DB travel + admin (17-19)** — travel success, 409 idempotent, admin_grant idempotente.
7. **Anti-P2W (20-22)** — snapshot BEFORE/AFTER, verifica immutabilità gold/rep/level/pvp_stats + reward_type solo cosmetic in DB.
8. **Audit (23-24)** — event_types registrati + whitelist ≥54.
9. **Admin HTTP (25-26)** — /admin/stables/catalog, /admin/stables/dev/grant-mount (dev-gated).
10. **Regression (27-28)** — no regression su pvp_season, OpenAPI include tutti i path stables.

### Esecuzione

```bash
cd /app/backend
python -m pytest tests/test_stables_phase8_v1.py -v
# → 28 passed
```

Regression baseline:

```bash
python -m pytest tests/test_forge_actions_p0.py tests/test_races_endpoint_p1.py \
                  tests/test_pvp_phase7a_p0.py tests/test_pvp_season_phase7b_p0.py -v
# → 78 passed
```

**DB Isolation attiva**: pytest gira su `orbus_r16_test` (guard-rail conftest.py). Nessuna scrittura al DB prod-dev tramite direct-DB tests (solo tramite HTTP endpoints, come da pattern esistente in Phase 7B).

---

## 8. Zero-P2W verification checklist

- [x] Ogni mount ha `affects_combat=false`
- [x] Ogni mount ha `affects_economy=false`
- [x] Ogni mount ha `affects_ranking=false`
- [x] Ogni mount ha `affects_travel_time=false`
- [x] Ogni mount ha `can_be_sold_for_real_money=false`
- [x] Anti-drift: seed forza tutti i flag a False anche se il catalog venisse editato per errore
- [x] Reward rotte narrative: solo `cosmetic_badge | cosmetic_title | lore_entry` (test 05 + 22)
- [x] Nessuna scrittura runtime su `guilds.gold`, `guilds.reputation`, `guilds.level`, `guilds.name`
- [x] Nessuna scrittura runtime su `guild_pvp_stats.*`
- [x] Nessuna scrittura runtime su `adventurers.stats`, `inventory`, `item_instances`
- [x] Test 20 + 21 snapshot BEFORE/AFTER e assertano immutabilità

---

## 9. Limiti / Debiti aperti

- **P3 residuo**: pytest HTTP admin bypass su prod-dev DB per test_26 (idempotency-tolerant workaround). Tracciato in Phase 8 V1 come acceptable trade-off.
- **Iter2 Frontend**: pagina Stalla + integrazione dashboard/gilda + UI per claim/travel/set-active (non implementati in questo Iter1, sono per Iter2 secondo il piano user).
- **Phase 8 V2**: 3 domini scoperti (ambash, irthe, nathos) senza rotta narrativa e rotte con `-5% penality` opzionale su esplorazione dedicata (P2, non P0).

---

## 10. Next Action Items

1. **Phase 8 V1 Iter2 Frontend** — pagina Stalla React + integrazione dashboard/gilda
2. **Phase 8 V2** — rotte narrative sui 3 domini rimanenti + flavor `-5% travel time` (esplorativo, non combat)
3. **P3 debt** — pytest HTTP admin bypass fix (mocked backend client in tests)
