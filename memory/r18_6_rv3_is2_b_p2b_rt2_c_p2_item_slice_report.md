# RT2-C-P2 + RT2-E-A — Effect Persistence and Lore-Linked Item Slice

**Status:** `IMPLEMENTED · LOCAL-VERIFIED · REAL-MONGO V1 PENDING`  
**Timestamp UTC:** `2026-07-28T13:29:33Z`  
**Branch:** `main-260728`  
**Anchor HEAD:** `780c05894f60c99745e0a94a3a7c337895a86c4a`  
**Closure ancestor:** `c0d8150cf4aaab259ad0c7aefa5b0a86522ed340` — PASS

## Outcome

The generic effect engine is no longer pure-only. It now has guarded
top-level runtime-state persistence, FakeStore and mocked-Mongo coverage,
versioned rehydration, deterministic dispatch, receipt deduplication,
lease/fencing/CAS integration and lifecycle removal.

The first item-first consumer is also present. Five live seed items now have:

- a singular Italian and English identity;
- an explicit Orbus lore source, lore tags and reviewed flavor text;
- soft class affinity covering both legacy and canonical class slugs;
- a readable player-facing effect summary;
- one immutable static server-side effect definition;
- deterministic compilation into `EffectRequest`;
- end-to-end FakeStore dispatch.

Database item metadata can reference an effect but cannot define primitive,
magnitude, duration, target, stacking or executable behaviour.

## RT2-C-P2 perimeter

Production integration:

```text
backend/app/stats/runtime/effects/dispatcher.py
backend/app/stats/runtime/effects/resolver.py
backend/app/stats/runtime/effects/serialization.py
backend/app/stats/runtime/state_store/models.py
backend/app/stats/runtime/state_store/fake_store.py
backend/app/stats/runtime/state_store/mongo_adapter.py
backend/app/stats/runtime/feature_flags.py
backend/app/stats/runtime/wiring/feature_flags.py
```

Implemented guarantees:

- `active_effect_instances` is a canonical top-level tuple;
- legacy documents missing the field rehydrate to an empty tuple;
- layout-B rehydration requires an exact injected versioned registry;
- definition-owned primitive, key and priority are restored from code;
- malformed, duplicate, over-cap or unknown-version payloads fail closed;
- dispatcher gate is evaluated before the first store call;
- gate requires transient state, item engine, trusted test user, isolated
  localhost and allowlisted Mongo target;
- server state assigns event sequence and expected state version;
- receipt capacity remains `512`;
- full-cap `512 receipts + 16 effects` BSON measurement is `235622` bytes,
  below the `245760` target and `262144` hard ceiling;
- no public route or application bootstrap wiring was added.

## RT2-E-A item slice

Static definitions:

| Live slug | Player-facing identity | Canonical affinity | Lore | Effect |
|---|---|---|---|---|
| `iron_sword` | Lama del Primo Giuramento di Krastlov | Guerriero | Krastlov | +2 Tempra until phase end |
| `balanced_dagger` | Pugnale dell'Ultimo Passo di Irthe | Ladro | Irthe | +2 Agilità until phase end |
| `apprentice_staff` | Bastone della Prima Faglia di Ergolat | Mago | Ergolat | +2 Intelletto until phase end |
| `initiate_robe` | Veste del Voto Infranto di Halodi | Paladino | Halodi | +2 Fede until phase end |
| `path_bow` | Arco del Sentiero Muto di Elfwood | Cacciatore di Mostri | Elfwood | +2 Agilità until phase end |

The item-hook compiler enforces:

- stable identity preference `blueprint_id → slug → legacy UUID`;
- no duplicate blueprint or duplicate player-facing name in one loadout;
- exactly one reference object per effect-bearing item;
- reviewed lore and matching `lore_key`;
- classless adventurers cannot activate item effects;
- hard mismatch fails closed;
- soft off-class gear remains equippable but its effect is inactive;
- static registry definition and lore tags must agree;
- deterministic event/application IDs;
- maximum `8` item effects per root event;
- legacy items without metadata remain valid.

## Catalog audit used for roadmap

The locked R18.5 design tables contain `1500` blueprint rows:

```text
item_id uniqueness = 1500/1500
nome_it uniqueness = 1500/1500
lore_source populated = 1500/1500
classes represented = 5 legacy archetypes
effect_metadata populated = 0/1500
PENDING/placeholder records = 7
```

They remain design/reference material, not a live-catalog claim. They must be
mapped to the 27 canonical classes, lore-reviewed at player-copy level and
applied through a reversible migration before being presented as implemented.

## Verification

```text
P1 + P2 effects tests
= 97 passed

feature-flag and state-store targeted regression
= 119 passed

item hook + loadout snapshot targeted
= 27 passed

complete local effect-engine suite, real-Mongo directories excluded
= 543 passed in 2.60s

git diff --check
= PASS

critical flake8 undefined-name/syntax perimeter
= PASS
```

One pre-existing Windows microbenchmark compared two independent ~2 ms p95
samples with zero tolerance and failed intermittently under both parallel and
serial full-suite load while passing alone. Its method now preserves the
existing `5 ms` hard cap and adds a bounded `25%` relative scheduler-noise
allowance. The complete serial suite passes.

## Real-Mongo V1 status

`RT2-C-V1` is not closed:

```text
MongoDB Windows service = not found
localhost:27017 = closed
Docker = not found
Podman = not found
```

No shared, production or non-allowlisted database was used as a substitute.
The next real-Mongo run must use the repository's unique allowlisted
`orbus_r16_rt2b_it_<run_id>` database and cleanup fixtures.

## Historical closure note

The RT2-B closure manifest is a historical snapshot. P2 intentionally extends
three files that were part of that snapshot (`feature_flags.py`,
`state_store/models.py`, `state_store/mongo_adapter.py`). This is an authorized
successor delta, not a claim that the old manifest remains byte-identical.
The current successor hashes are recorded below.

## LF-normalized SHA256

| File | SHA256 |
|---|---|
| `effects/item_catalog.py` | `90d32234f6e102b05da80678a4700bddf20a2a0b961c6a0e2f4646f16aaf9e64` |
| `effects/item_hooks.py` | `bbfdcc3107d327fc2eb5cf38811e4cfd57e508266beacba9c2329150026b7542` |
| `effects/dispatcher.py` | `f084366a738f9f5ce863bb5c12782cf5cb4931fed35e6372f7ffd534b3adf8df` |
| `effects/serialization.py` | `de5b09e10aef77a2f3f77a5a99e1c9b0fa3bb3c001b9113ea8b77c3cd8f185ea` |
| `state_store/models.py` | `824e185eccd3f5250ea40727fdf32682aa4ead1b6e5062d039d2f9fb747425c0` |
| `state_store/mongo_adapter.py` | `82983bf6fbe212f5ceaa65842931c9638d648bc2c2eaed12abc71e8e7f011815` |
| `seeds/seed_items_it.py` | `fedba6d35476e191edcae6b83a11034494e3ea3861e656d0156b9725551c2b45` |
| `items/services.py` | `9e6f1813492720aeaafd69741abd09b0c1720180bd1a2d475c4452e32ee23e94` |
| `runtime/loadout_snapshot.py` | `83205eb49d84eb3f6116e3233498932c60bdc781c66eb3150cbe6255e98f51bc` |
| `test_item_hooks.py` | `cb3b751f3f8fa4df4f6a326d4084b81d60a08114eadf4352050080b3f8403257` |

## Next delivery gate

Proceed on two tracks without claiming either closed prematurely:

1. add reproducible real-Mongo item-effect integration tests and run them when
   an isolated local Mongo becomes available;
2. implement the classless recruitment and Class Hall assignment vertical
   slice for the five readiness-approved classes, using the five starter items
   as the first post-choice reward/equip path.

