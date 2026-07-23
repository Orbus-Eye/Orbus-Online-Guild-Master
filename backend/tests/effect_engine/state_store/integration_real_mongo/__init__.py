"""RT2-B-1B-1 · Integration test package (REAL Mongo · LOCAL ISOLATED ONLY).

All tests in this package write to localhost Mongo on databases matching
`orbus_r16_rt2b_test` or `orbus_r16_rt2b_it_<unique_run_id>` ONLY.

Every test is protected by:
- guardrail assertions (host + db name)
- fixture-level cleanup (drop_database in teardown)
- suite-level residue verification (`test_cleanup.py`)

Regime: `RT2-B-1B-1 · LOCAL ISOLATED · NO RUNTIME WIRING · NO SHARED ENV`.
"""
