# R18.Reset.2 — Fresh Start Banner UI/API (BRIEF, non implementato)

**Stato**: 📋 **BRIEF PRONTO** — in attesa di GO PM esplicito per implementazione
**Data brief**: 2026-07-05T15:04:00Z UTC
**Autore**: e1_dev (su direttiva PM)
**Origine**: Known Deferred Scope da `R18.Reset.1b.hotfix.v1_3`

---

## 1. Scope

Round dedicato per implementare in modo isolato il banner "Fresh Start"
del reset R18.Reset.1b + relativo endpoint di dismiss persistente.

**Deliverable**:
- 1 endpoint API dedicato
- 1 componente UI banner nella dashboard
- 1 persistenza dismiss (per-guild)
- 1 test suite dedicata (backend + frontend automation con testing_agent)

**Non-scope (esplicito)**:
- ❌ NON toccare `migration-banner` esistente
- ❌ NON estendere endpoint `migration-banner/dismiss` (evitare accoppiamento)
- ❌ NON modificare roster / adventurers
- ❌ NON modificare gold / risorse
- ❌ NON modificare reset state / audit
- ❌ NON hard delete di alcun documento
- ❌ NON dedupe audit event (backlog separato `R18.Tooling.AuditEventIdempotencyKey`)

## 2. Endpoint

### `POST /api/guilds/me/r18-reset-banner/dismiss`

**Auth**: Bearer JWT (obbligatorio)

**Request body**: nessuno o `{}` (idempotente su chiamate ripetute)

**Response 200**:
```json
{
  "guild_id": "<uuid>",
  "r18_reset1b_banner_dismissed": true,
  "dismissed_at": "<iso utc>"
}
```

**Response 401**: senza token
**Response 403**: se un utente prova a dismissare banner di un'altra guild (nel POC dell'endpoint non è possibile, ma la semantica è "solo la propria guild")

**Comportamento**:
- Recupera `current_user` dal JWT
- Recupera la guild dell'utente via `guilds.find_one({owner_user_id: current_user.id})` (o schema equivalente esistente)
- Se già `r18_reset1b_banner_dismissed=true` → ritorna 200 idempotente senza toccare `dismissed_at`
- Se `false` o missing → `update_one({...}, {$set: {r18_reset1b_banner_dismissed: True, r18_reset1b_banner_dismissed_at: ISO_UTC}})`
- Nessun altro side-effect (no audit event, no roster touch, no gold touch)

## 3. UI Banner

**Trigger di visibilità**:
- Mostrato in dashboard solo se `guild.r18_reset1b_banner_dismissed !== true` E `guild.r18_reset1b_hotfix_v1_3 === true` (o equivalente marker che indica gilda post-reset)

**Testo banner (byte-exact, IT-locale, LOCKED)**:
```
Le gilde sono state riallineate per il nuovo inizio di Orbus. Il nome della tua gilda è stato preservato; progressi, roster e risorse sono ripartiti da zero.
```

**Interazione**:
- Pulsante "Ho capito" (o equivalente CTA) chiama `POST /api/guilds/me/r18-reset-banner/dismiss`
- On success: banner sparisce con animazione discreta
- Su errore rete: banner resta, mostra toast "Riprova più tardi"

**Design constraints** (coerenti con la palette scura Orbus, sobrio):
- Non usare emoji nei testi (in linea con guidelines UI)
- Non usare gradient viola/violet (guidelines)
- Layout minimale, testo leggibile, pulsante secondario coerente con shadcn/ui

## 4. DB Schema

**Nessun nuovo campo strutturale**: il field `r18_reset1b_banner_dismissed`
esiste già sul doc `guilds` (impostato a `false` dal reset v1.2).

Nuovo campo aggiuntivo introdotto da R18.Reset.2:
- `guilds.r18_reset1b_banner_dismissed_at` (ISO UTC string, opzionale, `None` di default) — timestamp del dismiss

## 5. Test attesi (elenco preliminare, PM rifinirà al GO)

Backend:
1. `POST` senza token → **401**
2. `POST` con token valido, guild presente → **200** + `r18_reset1b_banner_dismissed=true`
3. `POST` idempotente: seconda call → 200 senza aggiornare `dismissed_at`
4. `POST` con user senza guild → 404 con messaggio chiaro
5. Nessun altro doc `guilds` modificato oltre a quella dell'utente
6. Nessun audit event emesso da questo endpoint (silente)
7. Nessun tocco a `migration_banner_*` fields
8. Nessun tocco a `adventurers`, `inventory_items`, `expeditions`
9. Response schema Pydantic con `guild_id`, `r18_reset1b_banner_dismissed`, `dismissed_at`
10. Field `r18_reset1b_banner_dismissed_at` persistito con formato ISO UTC

Frontend/E2E:
11. Banner appare in dashboard con testo byte-exact per gilda con `dismissed=false`
12. Click su "Ho capito" scatena POST + banner sparisce
13. Refresh pagina dopo dismiss: banner NON riappare (persistenza OK)
14. Banner NON appare per gilde che non hanno il marker post-reset
15. Migration-banner esistente NON viene toccato / rimosso

## 6. Rischi mitigazione

- **Rischio**: sovrapposizione visuale con migration-banner esistente.
  - Mitigazione: analisi UI pre-implementazione, banner in slot dedicato.
- **Rischio**: race condition doppio-click su dismiss.
  - Mitigazione: idempotency lato server + debounce lato frontend.
- **Rischio**: guild senza il marker post-reset che vede il banner.
  - Mitigazione: guard lato frontend + fallback lato backend (nessun panic).

## 7. Endpoint schema OpenAPI (draft)

```yaml
POST /api/guilds/me/r18-reset-banner/dismiss:
  summary: Dismiss the R18.Reset.1b fresh-start banner for the current user's guild
  security:
    - bearerAuth: []
  responses:
    "200":
      description: OK — banner dismissed (idempotent)
      content:
        application/json:
          schema:
            type: object
            properties:
              guild_id: {type: string, format: uuid}
              r18_reset1b_banner_dismissed: {type: boolean}
              dismissed_at: {type: string, format: date-time, nullable: true}
    "401":
      description: Unauthorized
    "404":
      description: User has no guild
```

## 8. Backup / Rollback

Il reset banner non tocca alcun stato critico. In caso di bug:
- il dismiss può essere rigenerato mediante `db.guilds.update_many({}, {$set: {r18_reset1b_banner_dismissed: False}})` (script sibling, mai su sealed).
- Nessun backup dedicato necessario per l'endpoint stesso (readonly su tutto tranne un field per-guild).

## 9. GO checklist per PM (prima di autorizzare implementazione)

- [ ] Confermare byte-exact del testo del banner in italiano
- [ ] Confermare naming endpoint `POST /api/guilds/me/r18-reset-banner/dismiss` (o alternativa)
- [ ] Confermare naming field `r18_reset1b_banner_dismissed_at` (o alternativa)
- [ ] Confermare priorità e sprint di inclusione
- [ ] Confermare che nessun altra funzionalità (recruitment, expedition, ecc.) sarà toccata in questo round

---

**BRIEF PRONTO. Nessuna implementazione fino a GO PM esplicito.**
