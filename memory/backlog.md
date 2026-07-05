# Orbus Backlog

Formato: `[STATE] <round_ref> — <titolo breve>`
Origine di verità dei backlog aperti dei round R18.*.

---

## Backlog aperti

### [BACKLOG] R18.Tooling.AuditEventIdempotencyKey
- **Aperto**: 2026-07-05
- **Origine**: WARN M3 regression `R18.Reset.1b.hotfix.v1_3` — l'audit event `R18_FULL_GUILD_FRESH_START_APPLIED` risulta emesso 2 volte (una da REAL APPLY v1.1 subsequently rolled-back, una da v1.2 apply).
- **Obiettivo**: evitare eventi base duplicati nei round massivi tramite idempotency key esplicita per singolo apply logico.
- **Motivazione**: cosmetico, non-blocking (audit è append-only, i due record hanno metadata.apply_id diversi, ma il singolo `event_type` cumulativo può confondere consumer downstream).
- **Priorità**: P3 (cosmetico)
- **Scope**:
  - definire schema `idempotency_key` sui doc audit_log (es. `event_type + metadata.apply_id`)
  - unique compound index opzionale + guardia applicativa nei writer
  - migration script per popolare la chiave sui doc storici
- **Non fare**: dedupe distruttivo sui record storici senza esplicito GO PM.
- **Round dedicato**: da schedulare come `R18.Tooling.AuditEventIdempotencyKey` (round tooling separato).

---

## Backlog risolti (mantenuti per tracciabilità)

Vuoto.

---

## HOLD (in attesa di GO PM)

- `R18.1 drift`
- `R18.3d Stat/Role Mapping Registry`
- `Traits`
- `Fatigue/Cucina`
- `SMTP R17`
- `orbus.seed_round5.base_strength` warning (P3, HOLD by PM directive)
