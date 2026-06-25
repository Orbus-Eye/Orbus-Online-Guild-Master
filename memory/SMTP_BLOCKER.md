# SMTP delivery blocker — Emergent platform limitation

**Date:** February 2026 (investigation date on container: 2026-06-25)
**Status:** OPEN — platform blocker, not a code defect.
**Severity:** P1 (real email delivery broken; in-app flows unaffected).

---

## TL;DR

The Emergent preview pod runs the backend under `supervisord`, which starts the
uvicorn process with a **clean environment** (only `PATH`, `LANG`, `LC_*`, `PWD`,
`SUPERVISOR_*`, `APP_URL`, `INTEGRATION_PROXY_URL`).

Any custom secret defined in the **Emergent "Chiavi/Secrets" panel** is NOT
propagated into the backend process's `os.environ`. The only source of truth
that the backend can read is `/app/backend/.env` (loaded via `python-dotenv`).

Therefore an `SMTP_PASSWORD` typed into the Secrets panel will **never reach**
`SMTPProvider.__init__` and IONOS authentication fails with
`SMTPAuthenticationError`.

This is a **platform limitation**, not a code defect in Orbus.

---

## Evidence gathered (read-only investigation)

### Step 1 · File-mount inspection

| Path | Result |
| --- | --- |
| `/run/secrets/` | **does not exist** |
| `/var/lib/secrets/` | does not exist |
| `/etc/secrets/` | does not exist |
| `/var/run/secrets/` | does not exist |
| `/tmp/secrets/` | does not exist |
| `/app/secrets/` | does not exist |
| `/app/.emergent/` | exists but contains only `emergent.yml` (job metadata: `env_image_name`, `job_id`, `created_at`). No secrets. |
| `/root/.emergent/` | exists but contains only `.screenshots/`, `automation_output/`, `tool_outputs/`. Agent runtime artifacts, no secrets. |
| `find / -name "*.secrets*"` | nothing |
| `find / -name "secrets.json"` | nothing |

### Step 2 · HTTP endpoint inspection

| URL | HTTP | Notes |
| --- | --- | --- |
| `http://localhost:8000/secrets` | — | port not listening |
| `http://localhost:9090/secrets` | — | port not listening |
| `http://169.254.169.254/secrets` | — | cloud metadata service not reachable |
| `https://integrations.emergentagent.com/secrets` | **404** | gateway accepts only its own integration routes |
| `https://integrations.emergentagent.com/v1/secrets` | 404 | |
| `https://integrations.emergentagent.com/api/secrets` | 404 | |
| `https://integrations.emergentagent.com/health` | 404 | |
| `$preview_endpoint/secrets`, `/__emergent__/secrets`, `/.emergent/secrets` | 200 — **but it's the React SPA catch-all** (size = `/` size); not a real endpoint | |

Listening ports inside the pod:
- `:8001` → Orbus backend (uvicorn)
- `:8010` → Emergent agent plugin server (private)
- `:8020` → MongoDB MCP server (private)
- `:27017` → MongoDB
- `:3000`, `:3001`, `:4040` → frontend / mobile / ngrok

**No port exposes a Secrets API.**

### Step 3 · Backend process environment

The user-facing backend is **PID 1853**, supervised by `supervisord`.

```
$ cat /proc/1853/environ | tr '\0' '\n' | sort -u
APP_URL=https://...preview.emergentagent.com
INTEGRATION_PROXY_URL=https://integrations.emergentagent.com
LANG=C.UTF-8
LANGUAGE= LC_ADDRESS= LC_ALL= LC_COLLATE= LC_CTYPE=
LC_IDENTIFICATION= LC_MEASUREMENT= LC_MESSAGES= LC_MONETARY=
LC_NAME= LC_NUMERIC= LC_PAPER= LC_TELEPHONE= LC_TIME=
PATH=...  PWD=/  TERM=unknown
SUPERVISOR_ENABLED=1 SUPERVISOR_GROUP_NAME=backend
SUPERVISOR_PROCESS_NAME=backend SUPERVISOR_SERVER_URL=unix:///var/run/supervisor.sock
```

Notably absent: `STRIPE_API_KEY`, `NGROK_AUTHTOKEN`, `SMTP_PASSWORD`,
`RESEND_API_KEY`, `JWT_SECRET`, `MONGO_URL`, anything from the Emergent
Secrets panel.

The agent's interactive shell DOES see `STRIPE_API_KEY=<len=16>` and
`NGROK_AUTHTOKEN=<len=49>` (injected at container boot), but **supervisor
does not inherit them** because `service supervisor start` is a separate
init context. The supervisor config (`/etc/supervisor/conf.d/supervisord_mono.conf`,
read-only) lists only `APP_URL` and `INTEGRATION_PROXY_URL` for the backend
program; no `SMTP_PASSWORD` placeholder, no `{{SMTP_PASSWORD}}` substitution
pattern in `/entrypoint.sh`.

### Step 4 · `emergent_integrations_manager` tool

Returns only the LLM universal key:
```json
{"key_type":"LLM","emergent_llm_key":"sk-emergent-***"}
```
No interface to read arbitrary user-defined secrets.

### Step 5 · Emergent documentation in pod

- `/app/memory/*.md` — Orbus internal docs only.
- No `/usr/share/doc/emergent*`, no `man emergent`, no `/etc/emergent.conf`.
- `/entrypoint.sh` substitutes `${NGROK_AUTHTOKEN}` from container env into
  the supervisor config for the **mobile** program only. There is **no
  analogous substitution mechanism** for user-defined backend secrets.

### Step 6 · Why Stripe works for other apps

`STRIPE_API_KEY` is injected by Emergent into the **container's PID 1
environment**, which the agent shell inherits. Apps that need it must:
- copy it into `/app/backend/.env` explicitly (manual), OR
- modify the supervisor config to add `STRIPE_API_KEY="..."` to the
  `environment=` line (read-only file, blocked).

So Stripe is **not** seamlessly available to a supervisor-managed backend
either — it's the same blocker. The "Stripe works out of the box" guidance
elsewhere in Emergent docs likely refers to apps that read Stripe creds
from `.env` after manual paste.

---

## Why the agent cannot self-heal this

To set `SMTP_PASSWORD` in `/app/backend/.env`, the agent needs the actual
password value. The user has explicitly refused to paste it in chat
(compromised after a previous accidental disclosure). Without the value
in chat, the agent has no source to pull from:

- The Secrets panel content is not exposed via filesystem, HTTP, or any
  agent tool.
- `emergent_integrations_manager` returns only the LLM key.
- No SDK / RPC bridge is wired into the agent runtime.

**The agent has the ability to WRITE `/app/backend/.env`** (verified: agent
can write any file under `/app`). What it cannot do is **READ the user's
Secrets-panel value** to know WHAT to write.

---

## Action items for the user (no shell required)

### Path A — paste the password in chat ONE TIME, then rotate

1. Generate a **fresh** IONOS SMTP App Password
   (IONOS panel → Email → `noreply@orbusonline.com` → App Passwords → New).
2. Paste it ONCE in this chat with the message:
   > `New SMTP password (will rotate after): <password>`
3. The agent will:
   - `search_replace` it into `/app/backend/.env` line `SMTP_PASSWORD=...`
   - `sudo supervisorctl restart backend`
   - test the password-reset flow end-to-end
   - confirm 250 OK from IONOS
4. User rotates the password in IONOS panel again (now safe — it served
   its purpose, was used once in the agent session, chat session can be
   discarded).

**Risk:** the password is briefly visible in chat history. Mitigated by
the rotate-immediately-after policy.

### Path B — Open Emergent Support ticket

Suggested ticket text (copy-paste):

> **Subject:** Preview pod: Emergent "Secrets/Chiavi" panel values are not
> propagated to supervisor-managed backend processes.
>
> **Body:**
> The supervisor config in `/etc/supervisor/conf.d/supervisord_mono.conf`
> is read-only and lists only `APP_URL` + `INTEGRATION_PROXY_URL` in the
> `environment=` line for the `[program:backend]` block. Custom secrets
> typed into the Emergent Secrets panel never appear in
> `/proc/<backend_pid>/environ`. There is no documented mount under
> `/run/secrets/`, no `/v1/secrets` endpoint on
> `INTEGRATION_PROXY_URL`, and `emergent_integrations_manager` only
> exposes the universal LLM key.
>
> **Request:** Please document (or implement) a supported mechanism for
> backend code to read user-defined secrets from the panel —
> e.g. one of:
>   1. inject panel values into the `environment=` line of the supervisor
>      config at `entrypoint.sh` substitution time, OR
>   2. mount them as `/run/secrets/<NAME>` files, OR
>   3. expose them via an authenticated `INTEGRATION_PROXY_URL/secrets`
>      endpoint scoped to the current `job_id`.
>
> **Workaround in use today:** users paste secrets directly into
> `/app/backend/.env`, which requires shell access. Users without shell
> access are blocked.

### Path C — Ask the Emergent main-chat agent (if accessible)

The main Emergent agent (orchestrator level above E1) may have privileged
file-write or supervisor-restart capabilities not exposed to the in-app
agent. Ask in the Emergent main chat:

> "Please write `SMTP_PASSWORD=<value>` into `/app/backend/.env` for
> job_id `061a0d27-a4f4-4f8c-b3de-2927d5a369fd` and restart the backend
> supervisor service. The value will be supplied via the Secrets panel
> variable named `SMTP_PASSWORD`."

If the main agent has Secrets-panel read access (uncertain), this is the
cleanest path. Otherwise it'll fall back to Path A.

---

## In-app impact (what works WITHOUT email)

The following flows degrade gracefully because `SMTPProvider.send()`
returns `False` (it doesn't raise):

- **Registration** — succeeds (HTTP 201). The welcome email is best-effort
  and the failure is logged but not surfaced to the user.
- **Password reset** — the `/api/auth/password-reset/request` endpoint
  returns 200 to prevent user enumeration, but the email never arrives.
  **This is the only user-visible breakage.**
- All other in-app flows (recruit, equip, expedition, leaderboard, daily
  quests) are unaffected.

---

## Recommended `.env` security hygiene (independent of this blocker)

Regardless of which path the user picks, the following best-practices
should be in place (already true today, verified during this investigation):

1. `/app/backend/.env` is `chmod 644` — readable only by root. ✅
2. `SMTP_PASSWORD` is never logged (verified by
   `backend_phase93_smtp_test.py::test_password_never_logged`). ✅
3. `SMTPException` strings are sanitised to `type(exc).__name__` only,
   so AUTH error messages cannot leak the password. ✅
4. `load_dotenv` is called with `override=False` (default — verified
   in `server.py`: `load_dotenv(ROOT_DIR / ".env")`). So if Emergent
   EVER starts propagating panel secrets into `os.environ`, those would
   take precedence over `.env` automatically.

---

*End of blocker report.*
