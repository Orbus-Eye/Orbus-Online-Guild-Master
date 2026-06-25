# Orbus Online — User Access Audit (preview pod)

**Data audit**: 2026-06-25
**Pod**: `agent-env-cc39e638-4b77-4974-85e8-2c6d820bc691` (preview)
**Preview URL**: https://guild-master-5.preview.emergentagent.com
**Production**: https://orbusonline.net (separato, non auditato qui)

Legenda:
- ✅ utente può fare direttamente
- 🤖 agente può fare per l'utente via tool
- ❌ non supportato in questo pod
- ❓ dipende dal piano Emergent / verifica con support

---

## 1. Terminale / Shell manuale

| Aspetto | Stato | Dettagli |
|---|---|---|
| Bash su container | ✅ | utente ha shell tramite pannello Emergent (Terminal) |
| `sudo` privileges | ✅ | `(ALL : ALL) ALL` — root completo, no restrizioni |
| Code-server (VSCode browser) | ✅ | `/usr/bin/code-server` installato, password disponibile nella variabile `code_server_password` (recuperabile via `env \| grep code_server_password` dalla shell — NON la metto qui) |
| URL VSCode | ❓ | tipicamente `https://<pod>.code.emergentagent.com` — verifica nel pannello Emergent "Open VSCode" |

**Verdetto**: ✅ accesso shell+VSCode completi. Massima libertà operativa.

---

## 2. Vedere tutti i file sorgente

| Path | Dimensione | Stato |
|---|---|---|
| `/app/backend/` | 3.5 MB | ✅ accessibile via shell e VSCode |
| `/app/frontend/src/` | 624 KB | ✅ codice React |
| `/app/frontend/public/` | 12 KB | ✅ static assets |
| `/app/frontend/node_modules/` | 576 MB | ✅ generato da `yarn install` |
| `/app/memory/` | 132 KB | ✅ PRD.md, code_review, test_credentials |
| `/app/mobile/` | — | ✅ (placeholder mobile future) |
| `/app/test_reports/` | — | ✅ output testing agent |

**Verdetto**: ✅ Nessuna restrizione filesystem. VSCode browse + shell `find/grep/cat` su tutto `/app`.

---

## 3. Esportare codice completo

| Metodo | Stato | Comando |
|---|---|---|
| Tarball via shell | ✅ | `tar czf /tmp/orbus.tgz --exclude=node_modules --exclude=__pycache__ --exclude=build /app` (~3-5 MB risultanti) |
| Scaricare il tarball | ❓ | richiede un file server temporaneo. Vedi punto 9 per il dettaglio |
| VSCode "Download Folder" | ✅ | tasto destro su `/app` → Download (UI code-server) |
| Emergent "Export Project" button | ❓ | dipende dal piano — non vedo un comando CLI emergent dedicato |

**Verdetto**: ✅ Esportazione possibile via tar/zip. Lo strumento più semplice: VSCode → tasto destro sulla cartella → Download.

---

## 4. Collegare o esportare su GitHub

| Aspetto | Stato | Dettagli |
|---|---|---|
| `git` CLI installato | ✅ | `git version 2.39.5` |
| `/app/.git/` esiste | ✅ | repo locale già inizializzato, branch `main` |
| Remote configurato | ❌ | `git remote -v` → vuoto |
| `GITHUB_TOKEN` / `GH_TOKEN` env | ❌ | non iniettato nel container |
| Integrazione Emergent → GitHub | ❓ | pannello Emergent tipicamente offre "Connect GitHub" / "Push to GitHub" — verifica nel tuo dashboard |

**Workflow manuale (consigliato)**:
1. Crea repo su GitHub: `orbus-online` (privato/pubblico a tua scelta)
2. Sul container (Terminal Emergent):
   ```bash
   cd /app
   git config user.email "mr.gualmini@gmail.com"
   git config user.name "Marco Gualmini"
   git add -A && git commit -m "Initial snapshot Orbus Online"
   git remote add origin https://github.com/<tuo-user>/orbus-online.git
   # Auth: usa Personal Access Token come password (NON la password GitHub)
   git push -u origin main
   ```
3. Il primo `git push` chiederà username + PAT (genera su https://github.com/settings/tokens — scope `repo`)

**Verdetto**: ✅ utente può fare push manuale. 🤖 io posso aiutare commit/branch/.gitignore. Auto-sync continuo dal pannello → ❓ feature Emergent specifica.

---

## 5. Log frontend e backend

| Log | Path | Dimensione attuale | Lettura |
|---|---|---|---|
| Backend stderr | `/var/log/supervisor/backend.err.log` | 735 KB | `tail -f` o `less` |
| Backend stdout | `/var/log/supervisor/backend.out.log` | 4.8 MB | come sopra |
| Frontend stderr | `/var/log/supervisor/frontend.err.log` | 8.8 KB | webpack/CRA dev server errors |
| Frontend stdout | `/var/log/supervisor/frontend.out.log` | 22 KB | dev server output |
| Mobile | `/var/log/supervisor/mobile.*.log` | <10 KB | placeholder Expo (non in uso) |
| Supervisord | `/var/log/supervisor/supervisord.log` | 22 KB | eventi processi (restart, ecc.) |
| MongoDB log | ❌ | — | Mongo non gira come processo loggato qui (probabilmente esterno) |

**Comandi utili**:
```bash
# Live monitor backend
tail -f /var/log/supervisor/backend.err.log

# Cerca errori SMTP
grep -i "smtp\|email" /var/log/supervisor/backend.err.log | tail -20

# Cerca password reset
grep "PASSWORD-RESET" /var/log/supervisor/backend.err.log | tail -10
```

**Verdetto**: ✅ Log completi e leggibili tramite shell. ⚠️ I log possono crescere — rotazione non configurata in preview pod.

---

## 6. Vedere e modificare variabili ambiente

| Fonte | Stato | Note |
|---|---|---|
| `/app/backend/.env` | ✅ writable | fonte di verità per il backend (load_dotenv al startup) |
| `/app/frontend/.env` | ✅ writable | `REACT_APP_*` vars |
| Supervisor config `/etc/supervisor/conf.d/supervisord.conf` | ✅ writable (root) | non inietta SMTP/EMAIL vars nel backend |
| Emergent Secrets panel | ❓ | **Vincolo importante (Caso B)**: nel preview pod i Secrets dichiarati nel pannello **NON vengono iniettati** nel processo backend uvicorn (verificato: `/proc/<backend_pid>/environ` non contiene `EMAIL_*`, `SMTP_*`). Funzione potenzialmente attiva solo nel pod produzione |

**Workflow consigliato per modifiche env**:
```bash
nano /app/backend/.env
# modifica
sudo supervisorctl restart backend  # SOLO se modifichi .env
```

**Verdetto**: ✅ `.env` writable, supervisor restart funziona. ⚠️ Emergent Secrets pannello **non si propaga** al preview backend — usare `.env` direttamente.

---

## 7. Eseguire script manuali

| Capacità | Stato |
|---|---|
| `python` (3.11) + venv `/root/.venv` | ✅ |
| `node` + `yarn` | ✅ |
| `pytest` (test backend) | ✅ |
| `pip install <pkg>` | ✅ (root) |
| `yarn add <pkg>` | ✅ |
| Background processes | ✅ via supervisor o `nohup ... &` |
| Sandbox / container limits | ❌ nessuna restrizione apparente |

**Verdetto**: ✅ libertà completa di esecuzione script. 🤖 io posso eseguire bash per te. ✅ tu puoi eseguire da shell.

---

## 8. Accedere al database

| Metodo | Stato | Comando |
|---|---|---|
| `mongosh` CLI installato | ✅ | `/usr/bin/mongosh` v2.8.3 |
| Connessione locale | ✅ | `mongosh "mongodb://localhost:27017"` (ping OK) |
| MONGO_URL produzione | ❓ | il valore in `.env` è locale al preview pod; produzione potrebbe usare URL diverso |
| Mongo Atlas / cloud | ❓ | verifica se vuoi migrare da Mongo locale → Atlas in futuro |

**Esempi utili dalla shell**:
```bash
# Aprire shell mongo
mongosh "$(grep MONGO_URL /app/backend/.env | cut -d'"' -f2)"

# Quick query
mongosh "$(grep MONGO_URL /app/backend/.env | cut -d'"' -f2)" --eval "db.users.findOne({email: 'mr.gualmini@gmail.com'}, {_id:0, email:1, username:1})"
```

**Verdetto**: ✅ Mongo locale accessibile via CLI. ⚠️ Considera Atlas/cloud per produzione (durabilità & backup).

---

## 9. Scaricare il progetto come ZIP

**Metodo 1 — VSCode UI** (✅ più semplice):
1. Apri code-server dal pannello Emergent
2. Tasto destro su `/app` → "Download Folder" (esporta tar.gz)

**Metodo 2 — Tarball manuale via shell**:
```bash
cd / && tar czf /tmp/orbus_full.tgz \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='build' \
  --exclude='.git/objects' \
  app/
du -sh /tmp/orbus_full.tgz
# ~3-5 MB risultanti
```
Poi serverlo via:
```bash
cd /tmp && python -m http.server 8080
# Accedi a https://<pod>-8080.preview.emergentagent.com/orbus_full.tgz
# (può richiedere config nginx/supervisor — NON garantito out-of-the-box)
```

**Metodo 3 — git push su GitHub** (vedi punto 4): repo privato GitHub + clone in locale.

**Verdetto**: ✅ multipli metodi disponibili. Più semplice: VSCode UI. Più robusto per backup ricorrenti: Git push automatizzato.

---

## 10. Migrare il progetto fuori da Emergent

### Inventario dipendenze esterne

| Dipendenza | Stato | Note migrazione |
|---|---|---|
| MongoDB | ✅ locale (`mongodb://localhost:27017`) | migrare → MongoDB Atlas / DigitalOcean Managed DB |
| SMTP IONOS | ✅ esterno (`smtp.ionos.it`) | già esterno, non lega a Emergent |
| Object storage / file upload | ❓ verifica | Phase 13 non usa storage esterno; futuro: S3/R2/Tigris |
| Email reset link domain | `https://guild-master-5.preview.emergentagent.com` | da cambiare in `https://orbusonline.net` post-migrazione |
| Frontend build | ✅ standard React CRA | `yarn build` produce static, deployabile ovunque (Netlify/Vercel/IONOS web hosting) |
| Backend | ✅ FastAPI standard | deployabile su Render/Railway/Fly.io/VPS personale |

### File deployment

| File | Stato |
|---|---|
| `/app/Dockerfile` | ❌ assente |
| `/app/docker-compose.yml` | ❌ assente |
| `/app/.dockerignore` | ❌ assente |
| `/app/backend/requirements.txt` | ✅ 29 deps |
| `/app/frontend/package.json` | ✅ 91 righe |

Per migrare facilmente fuori da Emergent ti servirebbe (🤖 posso crearti):
- `backend/Dockerfile` (Python 3.11 + FastAPI + uvicorn)
- `frontend/Dockerfile` (Node 20 build → nginx static serve) oppure deploy diretto su Vercel
- `docker-compose.yml` con MongoDB locale per dev
- `.dockerignore`, healthcheck, env mapping

### Esistenti documenti deploy

- `/app/memory/PRD.md` — product requirements + architecture
- `/app/memory/code_review_2026_phase12.md` — code review snapshot
- `/app/memory/test_credentials.md` — credenziali test
- Nessuna `DEPLOY.md` o `MIGRATION.md` esplicita ancora

**Verdetto**: 🤖 io posso scaffold Dockerfile + docker-compose + DEPLOY.md per migrazione. La parte non automatizzabile (registrazione DigitalOcean/Render, DNS, MongoDB Atlas) resta in capo a te. Una volta containerizzato, il progetto è completamente portabile.

---

# Sintesi accessibilità

| # | Punto | Verdetto |
|---|---|---|
| 1 | Terminale / VSCode | ✅ Shell + code-server entrambi disponibili, sudo root |
| 2 | File sorgente | ✅ Tutto `/app` accessibile |
| 3 | Esportare codice | ✅ VSCode UI o tar manuale |
| 4 | Push GitHub | ✅ git CLI presente, repo locale già inizializzato — serve PAT GitHub utente |
| 5 | Log backend/frontend | ✅ `/var/log/supervisor/*.log` |
| 6 | Modificare env | ✅ `.env` writable. ⚠️ Emergent Secrets non propagati in preview |
| 7 | Script manuali | ✅ Python/Node/Yarn/pytest senza restrizioni |
| 8 | Database | ✅ mongosh locale, MONGO_URL in `.env` |
| 9 | Scaricare progetto | ✅ VSCode Download Folder o tar |
| 10 | Migrare fuori Emergent | 🤖 posso scaffold Docker. Cloud target (Render/Fly/VPS) → utente |

---

# Password compromise disclosure

⚠️ **SMTP_PASSWORD condivisa in chat = compromessa.**

La password che hai incollato nel messaggio precedente è registrata nella chat history Emergent e nei log di questa conversazione AI. **Non posso eliminare messaggi dalla chat history** — questo è un limite del prodotto, non aggirabile da me.

**Azione presa**: ho **rifiutato** di applicarla. Non è stata scritta in:
- `/app/backend/.env` (immutato dal 11:23:41 UTC del 25-Giu-2026, prima del tuo invio)
- Nessuno script `/tmp/sync_smtp*.py` (non creato)
- Nessun log backend / supervisor
- Nessuna sessione `~/.bash_history`

**Cosa fare tu, fuori chat**:

1. **Sul portale IONOS Email Business**: genera una nuova password per `admin@orbusonline.net` (la precedente — quella in chat — può essere lasciata o ruotata di nuovo, a tua discrezione; importante: NON usare quella già condivisa)

2. **Nel container Emergent** (via Terminal o VSCode):
   ```bash
   nano /app/backend/.env
   # Cerca la riga: SMTP_PASSWORD="..."
   # Sostituisci con la nuova password reale (mai più in chat)
   # Ctrl+X, Y, Enter
   sudo supervisorctl restart backend
   ```

3. **Smoke test**:
   ```bash
   curl -X POST https://guild-master-5.preview.emergentagent.com/api/auth/password-reset/request \
     -H "Content-Type: application/json" \
     -d '{"email":"mr.gualmini@gmail.com"}'
   sleep 3
   tail -n 5 /var/log/supervisor/backend.err.log | grep EMAIL/smtp
   ```
   Atteso: `[EMAIL/smtp] sent host=smtp.ionos.it subject='Reset password — Orbus Online'`
   Se invece `SMTPAuthenticationError`: typo nella password / 2FA attiva / utente IONOS bloccato.

4. **Per il futuro — flussi sicuri di rotazione**:
   - **Sempre via shell del container**, mai in chat
   - Considera un password manager (Bitwarden/1Password) per generare e archiviare le password SMTP
   - Se Emergent Secrets in futuro propagheranno al preview pod, utilizza quel canale (verifica con Emergent Support se è abilitabile per il tuo piano)

---

# Smart enhancement post-audit

- **🤖 Posso ora**: scaffold `Dockerfile` + `docker-compose.yml` + `DEPLOY.md` (~30 minuti di lavoro, no breaking changes al codice) — utile sia per backup che per indipendenza da Emergent
- **🤖 Posso ora**: setup script `git push` automatico (cron daily) verso GitHub backup, una volta che fornisci PAT (in `.env` o secrets futuri, non in chat)
- **✅ Per te**: rotazione SMTP password via shell come da disclosure sopra

End of audit.
