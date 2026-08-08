user_problem_statement: >
  Gate R18.6.RV3-IS2-B-P2B-RT2-B-2B-2-1 (DRAIN TRANSITION & COMPLETION-TO-FRAGMENT
  FOUNDATION) + correzione PM B2B2Q07 (payload 15-campi nella processed-event receipt)
  + V1 real-Mongo + V1S full-cap BSON hardening. Libreria runtime interna
  (app/stats/runtime), nessuna API pubblica nuova. Verifica via pytest.

testing_agent_instructions: >
  BACKEND VERIFICATION VIA PYTEST ONLY (nessun endpoint HTTP nuovo da testare;
  verificare solo che il backend sia healthy e OpenAPI abbia 275 paths).
  Eseguire da /app/backend:
  1) python -m pytest tests/effect_engine --ignore=tests/effect_engine/state_store/integration_real_mongo --ignore=tests/effect_engine/transitions/integration_real_mongo -q
     ATTESO: 365 passed.
  2) python -m pytest tests/effect_engine/transitions/integration_real_mongo tests/effect_engine/state_store/integration_real_mongo -q -n 0
     ATTESO: 104 passed, 1 xfailed (test_v06_bson_size_at_full_cap_512 xfail e' DOCUMENTATO/ATTESO).
     NOTA: test_perf_mongo_p95 e' load-sensitive; se fallisce, rieseguirlo isolato: deve passare.
  3) python -m pytest tests/backend_r18_4_sealed_integrity_test.py -q  -> ATTESO: 6 passed.
  4) curl http://localhost:8001/api/openapi.json | contare paths -> ATTESO: 275.
  NON modificare codice. NON testare frontend. Riportare i conteggi esatti.

backend:
  - task: "Drain transitions + B2B2Q07 receipt payload + V1S compaction"
    implemented: true
    working: true
    file: "backend/app/stats/runtime/"
    stuck_count: 0
    priority: "high"
    needs_retesting: false
    status_history:
      - working: true
        agent: "main"
        comment: "365/365 non-mongo, 104/104+1 xfail real-mongo serial, sealed 6/6, OpenAPI 275 (verifica main agent, da confermare con testing agent)"
      - working: true
        agent: "testing"
        comment: "VERIFIED ✓ All pytest gates passed: (1) 365/365 passed effect_engine non-mongo tests in 2.56s; (2) 104/104 passed + 1 xfailed (test_v06_bson_size_at_full_cap_512 - documented BSON fail-stop for PM review) real-mongo integration tests in 3.57s; (3) 6/6 passed sealed integrity tests in 0.63s; (4) OpenAPI confirmed 275 paths. Bug fix B2B2Q07 VERIFIED: drain tests (test_p13_completion_payload_embedded_15_fields, test_v01_payload_persisted_in_receipt_real_mongo) confirm 15-field completion payload properly persisted in EventReceipt.result_payload with zero TrustedDrainReceipt dependency. All 72 drain-specific tests passed (test_drain_dispatcher.py, test_drain_mocked_mongo.py, test_drain_pure.py, test_drain_real_mongo.py). Gate RT2-B-2B-2-1 COMPLETE."

metadata:
  created_by: "main_agent"
  version: "1.0"
  test_sequence: 2

test_plan:
  current_focus:
    - "Drain transitions + B2B2Q07 receipt payload + V1S compaction"
  stuck_tasks: []
  test_all: false

agent_communication:
  - agent: "main"
    message: "Verificare esclusivamente via pytest come da testing_agent_instructions. xfail v06 e' atteso (fail-stop BSON documentato per PM review)."
  - agent: "testing"
    message: "Gate RT2-B-2B-2-1 verification COMPLETE. All 4 pytest gates passed with exact expected counts. Bug fix B2B2Q07 confirmed working: 15-field completion payload correctly persisted in EventReceipt.result_payload across all drain test suites (pure, dispatcher, mocked mongo, real mongo). Zero TrustedDrainReceipt dependency verified. OpenAPI stable at 275 paths. No code modifications made. Ready for main agent to summarize and finish."
