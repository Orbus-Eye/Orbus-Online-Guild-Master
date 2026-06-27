# Orbus Online — Build Rules (binding policy)

> This file is the project's permanent policy ledger. Rules listed here are
> binding on every fork/iteration. Adding/removing a rule requires explicit
> user approval and a dated entry under "Change log" below.

---

## R1 — Guide-sync rule (introduced Phase 19.3, 2026-06-27)

Every task that **changes mechanics visible to the player** MUST update the
in-app Player Guide (`/app/frontend/src/pages/Guide.jsx`) in the same bundle.

Examples of "player-visible mechanics":
- New endpoint that adds a button / page / flow in the UI.
- Change to economy (gold cost, reward formulas, drop rates).
- New collection/feature visible from the dashboard or nav.
- Cooldowns, rate limits, lifetime caps (e.g. rename count).
- Privacy-relevant defaults (chat visibility, leaderboard inclusion).

In every final report, include the section:
```
Guida aggiornata: sì / no
Sezioni modificate: [list]
Motivazione (se no): [string]
```

If the change is purely backend-internal (no player-visible behavior), state
"no — backend only" with a one-line justification.

---

## R2 — Privacy & PII (binding)

The following data is **never** allowed in API responses, audit logs visible
to non-admin users, or chat payloads:
- Email addresses
- Internal `user_id` / `_id` (ObjectId) values
- `sender_guild_id` (raw — only `sender_public_name` is allowed)
- JWT tokens, refresh tokens, password hashes
- Any `is_test_user` boolean (internal only)

Chat-specific (Phase 19.3): messages from `users.is_test_user=True` MUST be
filtered out of the **global** chat read responses. Exception: a test user
always sees their **own** messages (so QA flows work in dev). Consortium
chat is implicitly safe (membership gates it).

---

## R3 — No regressions on prior rounds

Every fork MUST keep these test suites green:
- ROUND 4 Forge / Equipment / Bound-on-Equip
- ROUND 5 Raids / Dungeons / Power bump
- Phase 19 Raid Leaderboard / Weekly Raid hooks
- Phase 19.1 Review hotfix
- Phase 19.2 UX (rename, modal, markers, guide)
- Market / Crafting / Streak / Weekly / Chronicle / Consortium / Leaderboard privacy

A full `pytest tests/` run must finish with the previous baseline of
**passed** counts unchanged or higher (498+ as of Phase 19.2). New tests
introduced by the fork are additive.

---

## R4 — No production cleanup, no hard deletes

Forks may NOT:
- Hard-delete users from production (`db.users.delete_one/_many` on prod data).
- Cleanup leaderboard rows or guild rows owned by allowlisted players.
- Modify `/app/memory/ALLOWLIST.md` unless a real player joins (then add,
  never remove — and log under "Change log" in `ALLOWLIST.md`).

Test pollution sweeps in `backend/tests/conftest.py` are exempt provided they
honour the allowlist filter (already enforced).

---

## R5 — No pay-to-win / no premium boost

Until explicit product authorization, the codebase MUST NOT introduce:
- Premium subscriptions tied to gameplay power.
- Paid power gear, paid stat re-rolls beyond the existing hard cap.
- Reputation purchases.
- Cosmetic items are allowed (validate via `validate_item_monetization`).

---

## R6 — Test account hygiene

Any account created for QA purposes must:
- Use an `@orbus.test` email (clearly synthetic).
- Be flagged `is_test_user=True` in the database before sign-off.
- Be tracked in the fork's final report under "Account test creati + cleanup".

---

## R7 — Stop-before-deploy

Forks must STOP before any production deployment unless the user has given
explicit deploy authorization in the prompt. The user owns the deploy gate.

---

## Change log

| Date | Phase | Change | Author |
|---|---|---|---|
| 2026-06-27 | 19.3 | Initial policy ledger created. R1-R7 codified. | e1 |
