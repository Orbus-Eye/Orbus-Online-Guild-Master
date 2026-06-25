# Production Deploy Checklist — `orbusonline.net`

**Pod di produzione**: NON accessibile dall'agente di sviluppo. La preview
è un container separato da quello di produzione. Le modifiche fatte in
`/app/backend/.env` del preview pod **non** propagano automaticamente in
produzione.

**Goal**: configurare il pod produzione per inviare email (welcome +
password reset) usando la mailbox IONOS `support@orbusonline.net` e per
generare link che puntino a `https://orbusonline.net`.

---

## Stato a oggi (verificato dal preview pod)

| Componente | Preview | Produzione |
| --- | --- | --- |
| Frontend `/` | ✅ 200 | ✅ 200 (Cloudflare → pod prod) |
| API `/api/health` | ✅ `{"status":"ok"}` | ✅ `{"status":"ok","env":"development"}` |
| OpenAPI 42 paths | ✅ | ✅ |
| TLS valido | ✅ | ✅ (Google Trust Services, scad. sett 2026) |
| DNS | preview.emergentagent.com | orbusonline.net → 162.159.142.117 (Cloudflare anycast) |
| `APP_BASE_URL` | `https://orbusonline.net` ✅ | **da settare** |
| `SMTP_USERNAME` | `support@orbusonline.net` ✅ | **da settare** |
| `SMTP_PASSWORD` | length=20, sha256[:12]=68945b379b54 (valida — AUTH OK) | **da settare con stessa password** |
| `EMAIL_FROM` | `Orbus Online <support@orbusonline.net>` ✅ | **da settare** |
| `EMAIL_REPLY_TO` | `support@orbusonline.net` ✅ | **da settare** |
| Welcome email reale | ✅ inviata 17:30:37 UTC | da testare post-config |
| Reset email reale | ✅ inviata 17:30:07 UTC | da testare post-config |

---

## Codice: niente da modificare

Audit completato. Tutto il codice legge la config dall'ambiente:

- `app/core/email.py:230` — `EMAIL_FROM` da `os.environ`
- `app/core/email.py:52` — `EMAIL_REPLY_TO` da `os.environ`
- `app/auth/services.py:218` — `APP_BASE_URL` per il link reset
- `app/auth/services.py:252` — `APP_BASE_URL` per il link welcome

Nessun valore hardcoded. Il pod prod, una volta riavviato con le env vars
corrette, userà automaticamente `https://orbusonline.net/...` nei link.

**OpenAPI invariato** — nessuna nuova route, nessuna nuova schema.

---

## Variabili `.env` da settare in produzione

Copia/incolla esatto del blocco da applicare al `.env` del pod prod (i
valori sensibili sono indicati in `<…>` — vanno presi dal pannello IONOS
o dal `.env` del preview).

```env
# ── App identity ────────────────────────────────────────────────
APP_BASE_URL="https://orbusonline.net"
APP_ENV="production"               # opzionale ma raccomandato (al
                                   # momento risulta "development")

# ── Email pipeline ──────────────────────────────────────────────
EMAIL_PROVIDER="smtp"
SMTP_HOST="smtp.ionos.it"
SMTP_PORT="587"
SMTP_USE_TLS="true"
SMTP_USERNAME="support@orbusonline.net"
SMTP_PASSWORD="<COPIA dalla mailbox IONOS support@orbusonline.net>"
EMAIL_FROM="Orbus Online <support@orbusonline.net>"
EMAIL_REPLY_TO="support@orbusonline.net"
SEND_WELCOME_EMAIL="true"
```

Le variabili **non** da modificare (devono restare quelle di prod):

- `MONGO_URL`, `DB_NAME` (database produzione, NON il database preview)
- `JWT_SECRET` (la rotazione del secret invaliderebbe tutti i token attivi)
- `CORS_ORIGINS` (dipende dalle origin che servono prod)
- `TIGRIS_*` (object storage, se configurato in prod)

---

## Come applicare il cambio in produzione

Hai **due strade**, in ordine di preferibilità:

### Strada 1 — Via Emergent Deploy/Secrets panel (raccomandata)

1. Apri la dashboard Emergent del progetto Orbus
2. Vai a **Deploy** → **orbusonline.net** → **Environment Variables**
   (o sezione "Secrets" del pod prod)
3. Aggiungi / aggiorna le 10 variabili elencate sopra
4. Salva e **redeploy** il pod produzione (oppure restart se l'UI lo
   permette senza rebuild)
5. Aspetta che il pod sia "healthy"

### Strada 2 — Apri ticket a Emergent Support

Se la dashboard non espone le Environment Variables del pod prod, copia
questo testo nel ticket:

> **Subject:** orbusonline.net — request env var update on production pod
>
> **Body:**
> Please update the production pod environment of project Orbus
> (`orbusonline.net`) with the following variables, then restart the
> backend service:
>
> ```
> APP_BASE_URL=https://orbusonline.net
> APP_ENV=production
> EMAIL_PROVIDER=smtp
> SMTP_HOST=smtp.ionos.it
> SMTP_PORT=587
> SMTP_USE_TLS=true
> SMTP_USERNAME=support@orbusonline.net
> SMTP_PASSWORD=<provided separately via secure channel>
> EMAIL_FROM=Orbus Online <support@orbusonline.net>
> EMAIL_REPLY_TO=support@orbusonline.net
> SEND_WELCOME_EMAIL=true
> ```
>
> The SMTP password will be provided to you via the Emergent secure
> secrets channel — please do not request it via this ticket.
>
> Current production pod is missing SMTP credentials; preview pod has
> them correctly and the email pipeline works end-to-end (verified
> 2026-06-25 17:30 UTC).

---

## Smoke test post-deploy produzione

Dopo che il pod prod è stato riavviato con la nuova config:

```bash
# 1. Password reset reale verso una tua inbox
curl -s -X POST https://orbusonline.net/api/auth/password-reset/request \
  -H "Content-Type: application/json" \
  -H "Accept-Language: it-IT" \
  -d '{"email":"mr.gualmini@gmail.com"}' \
  -w "\nHTTP=%{http_code}\n"
# atteso: HTTP=200 {"status":"ok"}

# 2. Verifica nei log del pod prod (via Emergent dashboard / supporto)
#    deve apparire una linea tipo:
#    [EMAIL/smtp] sent host=smtp.ionos.it to=mr.gualmini@gmail.com
#                 subject='Reset password — Orbus Online'

# 3. Controlla Gmail: inbox + spam + promozioni.
#    Il link nel corpo DEVE essere:
#    https://orbusonline.net/password-reset/confirm?token=...
#    NON https://guild-master-5.preview.emergentagent.com/...

# 4. Click sul link → la UI prod (orbusonline.net) deve gestire il token
#    e accettare una nuova password.
```

---

## Deliverability Gmail (problema noto separato)

Anche con SMTP correttamente configurato, **Gmail potrebbe filtrare** le
email in spam o droppare silenziosamente se il dominio `orbusonline.net`
**non ha record DNS SPF / DKIM / DMARC** che autorizzino IONOS a inviare
per quel dominio.

Controllo veloce dal terminale (eseguibile dall'utente):

```bash
# SPF — deve includere IONOS
dig +short TXT orbusonline.net | grep "v=spf1"
# atteso esempio: "v=spf1 include:_spf.perfora.net include:_spf.kundenserver.de ~all"

# DKIM — IONOS fornisce un selector come default._domainkey
dig +short TXT default._domainkey.orbusonline.net
# atteso: chiave pubblica RSA lunga; se vuoto → DKIM non firmato

# DMARC — opzionale ma raccomandato
dig +short TXT _dmarc.orbusonline.net
# atteso: "v=DMARC1; p=none; rua=mailto:..."
```

Se uno qualsiasi dei tre è vuoto:

1. IONOS pannello → Domini & SSL → `orbusonline.net` → **DNS**
2. Sezione "Mail server records" → abilita SPF + DKIM automatici
   (IONOS li configura con un click su mailboxes ospitate da loro)
3. Aspetta propagazione DNS (10–30 min)
4. Verifica con i comandi `dig` sopra
5. Mandati una mail di test e controlla l'header in Gmail → deve mostrare
   `spf=pass` e `dkim=pass`

**Importante**: SPF/DKIM/DMARC sono **lato DNS del dominio**, NON nel
codice dell'app e NON in `.env`. Vanno configurati una sola volta nel
pannello IONOS DNS.

---

## Verifica finale checklist (da spuntare manualmente dopo deploy)

- [ ] Pod prod riavviato con le 10 env vars
- [ ] `curl https://orbusonline.net/api/health` → `{"status":"ok","env":"production"}`
- [ ] `curl POST /api/auth/password-reset/request` → 200 + email arriva su Gmail
- [ ] Link nel body email punta a `https://orbusonline.net/...`
- [ ] Welcome email arriva sul prossimo register
- [ ] Subject in italiano se `Accept-Language: it-IT`
- [ ] Mittente: `Orbus Online <support@orbusonline.net>`
- [ ] Reply-To: `support@orbusonline.net`
- [ ] Nessun raw token nei log prod (solo `token_hash=<12hex>`)
- [ ] SPF + DKIM verificati con `dig` (deliverability Gmail)

---

*Documento generato 2026-06-25. Aggiornare dopo il primo smoke prod
positivo o dopo modifiche al provider email.*
