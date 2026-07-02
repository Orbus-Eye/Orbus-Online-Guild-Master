import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "../components/ui/alert-dialog";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";

/** ROUND 16.5.1 B.2 — Admin Tester Tools UI.
 * SOLO account @orbus.test o is_test_user=True.
 * Ambiente APP_ENV=dev/preview OR ENABLE_TESTER_TOOLS=true.
 *
 * ROUND 16.5.1 E2 fix — Refactor a `api` wrapper condiviso (lib/api.js).
 * Motivazione: la vecchia versione usava `axios` raw + `Authorization:
 * Bearer` letto da localStorage. Post ROUND 11.4a l'auth è cookie-only
 * (httpOnly) e le richieste mutating richiedono il double-submit CSRF.
 * Su same-origin il browser inviava il cookie automaticamente ma il
 * client raw NON echeggiava mai l'header `X-CSRF-Token`, producendo
 * 403 `auth.csrf.invalid` su Set MAX / Set MIN / Grant.
 *
 * Il wrapper `api`:
 *   - `withCredentials: true` (cookie httpOnly access_token viaggia)
 *   - inietta `X-CSRF-Token` su POST/PATCH/PUT/DELETE se già cacheato
 *   - retry singolo su 403 `auth.csrf.invalid` dopo `_refreshCsrf()`
 *   - normalizza `detail` in `err.normalizedMessage` per il toast
 *
 * `formatApiError` (import condiviso) gestisce tutti i casi:
 * string / array Pydantic / object {code, user_message, message}.
 * Sostituisce la funzione locale che duplicava la logica pre-fix BUG#2.
 */
export default function AdminTesterTools() {
  // ROUND 16.5.1 BUG#2 fix — default target = admin corrente (che ha
  // is_test_user=True). Ne evita 403 all'apertura del pannello.
  const [email, setEmail] = useState("admin@orbus.test");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pendingTool, setPendingTool] = useState(null);
  const [needConfirm, setNeedConfirm] = useState(false);

  const loadStatus = async () => {
    if (!email) return;
    setLoading(true);
    try {
      const r = await api.get(`/admin/tester-tools/status`, {
        params: { target_email: email },
      });
      setStatus(r.data);
      toast.success("Status caricato");
    } catch (e) {
      toast.error(`Errore: ${formatApiError(e)}`);
      setStatus(null);
    } finally { setLoading(false); }
  };

  const invoke = async (tool, confirm = false) => {
    try {
      const r = await api.post(
        `/admin/tester-tools/${tool}`,
        { target_email: email, confirm },
      );
      toast.success(`${tool} eseguito: ${JSON.stringify(r.data).slice(0, 100)}`);
      loadStatus();
      setNeedConfirm(false);
      setPendingTool(null);
    } catch (e) {
      const parsed = formatApiError(e);
      if (parsed.includes("require_confirm")) {
        toast.warning("Chiamata recente rilevata — richiede conferma esplicita");
        setPendingTool(tool);
        setNeedConfirm(true);
      } else {
        toast.error(`Errore: ${parsed}`);
      }
    }
  };

  return (
    <div className="p-6 space-y-6 min-h-screen bg-slate-900 text-slate-100"
         data-testid="admin-tester-tools-page">
      <h1 className="text-3xl font-bold">Admin — Tester Tools</h1>
      <p className="text-sm text-slate-400">
        Round 16.5.1 B.2 — Bottoni SOLO per account test (`@orbus.test`
        o `is_test_user=True`). Ogni operazione registra audit
        + snapshot pre-modifica. Idempotente. Nessun hard delete.
      </p>

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle>Target account</CardTitle></CardHeader>
        <CardContent className="flex gap-3 flex-wrap">
          <Input value={email} onChange={(e) => setEmail(e.target.value)}
                 placeholder="target@orbus.test" className="max-w-md bg-slate-900"
                 data-testid="target-email" />
          <Button onClick={loadStatus} disabled={loading}
                  data-testid="load-status-btn">
            {loading ? "…" : "Carica status"}
          </Button>
        </CardContent>
      </Card>

      {status && (
        <Card className="bg-slate-800 border-slate-700" data-testid="status-card">
          <CardHeader>
            <CardTitle>Status: {status.target_user.email}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <StatBox label="is_test_user" value={String(status.target_user.is_test_user)} />
              <StatBox label="tools_enabled" value={String(status.tools_enabled)} />
              <StatBox label="env" value={status.env} />
              <StatBox label="guild_id"
                       value={status.guild?.id?.slice(0, 8) || "—"} />
              <StatBox label="guild.level" value={status.guild?.level ?? "—"} />
              <StatBox label="guild.gold" value={status.guild?.gold ?? "—"} />
              <StatBox label="max_team_power_ever"
                       value={status.guild?.max_team_power_ever ?? "—"} />
              <StatBox label="roster active"
                       value={status.roster?.active_count ?? "—"} />
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle>Azioni</CardTitle></CardHeader>
        <CardContent className="flex flex-col md:flex-row gap-3">
          <ConfirmButton label="Dai avventurieri al tester"
                         confirmText="Crea avv fino a 20 attivi (idempotente)."
                         onConfirm={() => invoke("grant-adventurers")}
                         testId="grant-btn" />
          <ConfirmButton label="Set tester MAX"
                         confirmText="Guild lv 15, oro 100k, roster lv 10. NON hard-delete."
                         onConfirm={() => invoke("set-max", needConfirm && pendingTool === "set-max")}
                         testId="set-max-btn" />
          <ConfirmButton label="Set tester MIN"
                         confirmText="Guild lv 1, oro 100, roster 3 lv 1. Archivio soft il resto."
                         onConfirm={() => invoke("set-min", needConfirm && pendingTool === "set-min")}
                         testId="set-min-btn" />
        </CardContent>
      </Card>
    </div>
  );
}

function StatBox({ label, value }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded p-2">
      <div className="text-xs text-slate-500 uppercase">{label}</div>
      <div className="font-mono text-sm">{value}</div>
    </div>
  );
}

function ConfirmButton({ label, confirmText, onConfirm, testId }) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button data-testid={testId}>{label}</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Confermi &laquo;{label}&raquo;?</AlertDialogTitle>
          <AlertDialogDescription>{confirmText}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Annulla</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}
                             data-testid={`${testId}-confirm`}>
            Sì, procedi
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
