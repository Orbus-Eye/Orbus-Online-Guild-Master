# RT2-C-P1 — Generic Effect Engine Pure Foundation

**Status:** `IMPLEMENTED · PURE-VERIFIED · READY FOR RT2-C-P2`  
**Timestamp UTC:** `2026-07-28T12:45:24Z`  
**Branch:** `main-260728`  
**Anchor HEAD:** `780c05894f60c99745e0a94a3a7c337895a86c4a`  
**Closure ancestor:** `c0d8150cf4aaab259ad0c7aefa5b0a86522ed340` — PASS

## Outcome

RT2-C-P1 adds a generic, immutable and deterministic effect foundation without
touching an existing production file. The module resolves stat, state-tag,
resource and feedback-only primitives into mutation intents. It does not mutate
game state, read a clock, use RNG, write a database, call a network service,
emit logs or expose a route.

The foundation is ready for the separate RT2-C-P2 integration gate. P1 itself
does not persist effects and does not activate any feature flag.

## Production perimeter

New files only:

```text
backend/app/stats/runtime/effects/__init__.py
backend/app/stats/runtime/effects/models.py
backend/app/stats/runtime/effects/registry.py
backend/app/stats/runtime/effects/resolver.py
backend/app/stats/runtime/effects/serialization.py
```

Existing production files modified: `0`.

## Implemented contract

- frozen dataclasses for definitions, requests, instances and resolutions;
- separate `EffectResultCode` enum with exactly 10 canonical codes;
- static tuple-backed registry with fail-closed definition validation;
- no gameplay definition in the default registry;
- all six authorized primitives:
  - `STAT_FLAT_TEMPORARY`;
  - `STATE_TAG_APPLY`;
  - `STATE_TAG_REMOVE`;
  - `RESOURCE_GENERATE`;
  - `RESOURCE_CONSUME`;
  - `FEEDBACK_ONLY`;
- canonical runtime-stat whitelist:
  `strength`, `agility`, `intellect`, `endurance`, `faith`;
- statically registered state tags and resources; arbitrary paths rejected;
- all four duration models, including bounded `USE_COUNT 1..10`;
- all four stacking policies, including additive cap `<=5`;
- deterministic effect instance IDs derived from bounded authoritative inputs;
- canonical ordering:
  `definition priority ASC → root event sequence ASC → instance ID lexical`;
- trigger-depth cap `1`;
- active-instance cap `16`;
- effects-per-root-event cap `8`;
- feedback-per-resolution cap `8`;
- distinct receipt, audit and player-feedback descriptors;
- event-driven phase, expedition and use-count lifecycle resolution;
- deterministic replay as a zero-mutation no-op;
- three compact BSON projections A/B/C.

`Void Echo` exists only as a test fixture. The production registry remains empty.

## BSON feasibility

Baseline full-cap state: `230593` bytes.  
Active-effect budget: `6144` bytes.  
Projected state target: `245760` bytes.  
Hard limit: `262144` bytes.

Worst-case fixture:

```text
16 active instances
64-byte effect IDs
64-byte source IDs
64-byte target IDs
32-byte application IDs
USE_COUNT=10
stack_count=5
magnitude=10000
priority=10000
```

| Scenario | Layout | Active bytes | Projected full-cap | Verdict |
|---|---:|---:|---:|---|
| same max-bound target | A | 5642 | 236235 | PASS |
| same max-bound target | B | 4585 | 235178 | PASS |
| same max-bound target | C | 4506 | 235099 | PASS |
| 16 unique max-bound targets | A | 5642 | 236235 | PASS |
| 16 unique max-bound targets | B | 6004 | 236597 | PASS |
| 16 unique max-bound targets | C | 4506 | 235099 | PASS |

Layout B remains the recommended P2 integration candidate because it is
target-keyed and Mongo-safe while passing the explicit worst-case budget with
`140` bytes of margin. Its target keys use reversible base64url encoding, so
raw `$`, `.`, Unicode or other target characters never become Mongo field
syntax.

## Verification

```text
P1 pure tests, serial
= 57 passed

P1 pure tests, repository-configured xdist
= 57 passed

Black
= PASS · 11 files unchanged

Flake8
= PASS

purity AST contract
= PASS · no database/network/clock/RNG/logging imports

git diff --check
= PASS

sealed integrity, Windows LF-normalized
= 6 logical checks equivalent
= 36/36 artifacts byte-identical

RT2-B closure manifest, Windows LF-normalized
= 24/24 manifest entries byte-identical
```

OpenAPI was not re-imported in P1 because the isolated runtime intentionally
contains only the dependencies needed by this pure gate. No route, application
bootstrap file or existing production file changed.

## Files and LF-normalized SHA256

| File | SHA256 |
|---|---|
| `effects/__init__.py` | `44a7a9fd569b6fad961137ce8ea14939912ea62f1d6fa9065651a43826c842a6` |
| `effects/models.py` | `a833d042a1f45a686ffdd91d513fc007e4b26233f0632ce1e742b5faf9b594cb` |
| `effects/registry.py` | `055e5639f5bb0ccb676c1991bc6f867a67e3f2c891f8995660796f7a5448b538` |
| `effects/resolver.py` | `31c82b012cdd2b1987bfa8c2782359eccd8580a2849cb5b211e1c1a610b4aacc` |
| `effects/serialization.py` | `d1ba5ca980b0249d50aee70888d58769438c697ca69ca1976731cdd6ff6d6b48` |
| `effects tests/__init__.py` | `a06055629a20b1f3c73c95f9580c68efd073ba175132ce99099cc116f932e673` |
| `effects tests/conftest.py` | `ba2433054e56f238396389c6f51175c186a5291dde2d8a3f516447498e56304c` |
| `test_models_registry.py` | `9e407c27c40fe605dcaa55fe1637a35c6eed5b33b02b3ed38dbce88e94449869` |
| `test_resolver.py` | `1be21a28166c61fde7c45dd1086ed0b496f1600a8cdb8802c4786141f467fdae` |
| `test_lifecycle_serialization.py` | `45a3c158d596ddfe19f9af01f40f1c905ca151751fbfa83e58961baaaa35ee0c` |
| `test_purity_contract.py` | `f806a84df91f60cc44e8f45ad45026860c5618698c627003d10a569d7c872871` |

## Fail-stops

```text
CONTEXT_ANCHOR_FAIL = NOT TRIGGERED
SEALED_INTEGRITY_VIOLATION = NOT TRIGGERED
BSON_BUDGET_EXCEEDED = NOT TRIGGERED
TRIGGER_DEPTH_CONTRACT_VIOLATION = NOT TRIGGERED
EXISTING_PRODUCTION_FILE_MODIFIED = NOT TRIGGERED
DATABASE_WRITE = 0
NETWORK_CALL = 0
FEATURE_FLAG_ACTIVATION = 0
PUBLIC_ROUTE_CHANGE = 0
```

## Next gate

`RT2-C-P2` may now integrate the P1 contracts into the top-level expedition
runtime state, FakeStore/Mongo rehydration and guarded dispatcher. Integration
must preserve:

- receipt capacity `512`;
- state target `<=245760` bytes;
- default-OFF runtime activation;
- zero change to `TransitionResultCode` and `CasResultCode`;
- response invariance when the effect gate is disabled.
