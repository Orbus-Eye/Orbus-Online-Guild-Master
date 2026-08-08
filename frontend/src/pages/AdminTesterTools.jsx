import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "../components/ui/alert-dialog";
import { toast } from "sonner";
import { api, formatApiError } from "../lib/api";

const CONTROLLED_REASON_LABELS = {
  controlled_total_power_spread: "divario di potenza totale",
  controlled_equipment_spread: "divario nelle statistiche degli item",
  controlled_item_effect_spread: "divario dell'effetto item",
  controlled_class_resonance_spread: "divario della risonanza di classe",
  controlled_dungeon_outcome_spread: "divario negli esiti del dungeon",
};

const SEVERITY_LABELS = {
  low: "bassa",
  medium: "media",
  high: "alta",
  critical: "critica",
};

const REVIEW_SCOPE_LABELS = {
  item: "item",
  class_resonance: "risonanza di classe",
  encounter: "incontro",
  mixed: "analisi mista",
};

const T8_CHECKLIST_LABELS = {
  desktop_navigation: "Navigazione desktop verificata",
  mobile_navigation: "Navigazione mobile verificata",
  classless_hall_journey: "Percorso senza classe → Class Hall completato",
  item_lore_and_sources: "Lore e fonti degli item comprensibili",
  dungeon_and_raid_reports: "Report dungeon e raid verificati",
  reset_repeatability: "Reset e ripetizione del viaggio verificati",
};

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
  const [email, setEmail] = useState("tester@orbus.test");
  const [status, setStatus] = useState(null);
  const [smoke, setSmoke] = useState(null);
  const [vertical, setVertical] = useState(null);
  const [release, setRelease] = useState(null);
  const [releaseChecks, setReleaseChecks] = useState(
    Object.fromEntries(Object.keys(T8_CHECKLIST_LABELS).map((key) => [key, false])),
  );
  const [releaseNotes, setReleaseNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingTool, setPendingTool] = useState(null);
  const [needConfirm, setNeedConfirm] = useState(false);

  const loadStatus = async () => {
    if (!email) return;
    setLoading(true);
    try {
      const [statusResponse, smokeResponse, verticalResponse, releaseResponse] = await Promise.all([
        api.get(`/admin/tester-tools/status`, {
          params: { target_email: email },
        }),
        api.get(`/admin/tester-tools/smoke-matrix`, {
          params: { target_email: email },
        }),
        api.get(`/admin/tester-tools/vertical-slice`, {
          params: { target_email: email },
        }),
        api.get(`/admin/tester-tools/release-readiness`, {
          params: { target_email: email },
        }),
      ]);
      setStatus(statusResponse.data);
      setSmoke(smokeResponse.data);
      setVertical(verticalResponse.data);
      setRelease(releaseResponse.data);
      setReleaseChecks(releaseResponse.data?.human_checklist?.checks || releaseChecks);
      setReleaseNotes(releaseResponse.data?.human_checklist?.notes || "");
      toast.success("Stato e percorso tester aggiornati");
    } catch (e) {
      toast.error(`Errore: ${formatApiError(e)}`);
      setStatus(null);
      setSmoke(null);
      setVertical(null);
      setRelease(null);
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

  const saveReleaseChecklist = async () => {
    setLoading(true);
    try {
      await api.post(`/admin/tester-tools/release-checklist`, {
        target_email: email,
        confirm: true,
        ...releaseChecks,
        notes: releaseNotes,
      });
      toast.success("Checklist T8 registrata senza autorizzare il deploy");
      await loadStatus();
    } catch (e) {
      toast.error(`Errore checklist: ${formatApiError(e)}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadTuningExport = () => {
    const bundle = vertical?.balance?.controlled?.export_bundle;
    if (!bundle?.payload || !bundle?.sha256 || !bundle?.canonical_json) {
      toast.error("Export tuning non ancora disponibile");
      return;
    }
    const blob = new Blob(
      [bundle.canonical_json],
      { type: "application/json;charset=utf-8" },
    );
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `orbus-t5-tuning-${bundle.sha256.slice(0, 12)}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    toast.success("Export tuning preparato");
  };

  return (
    <div className="p-6 space-y-6 min-h-screen bg-slate-900 text-slate-100"
         data-testid="admin-tester-tools-page">
      <h1 className="text-3xl font-bold">Admin — Tester Tools</h1>
      <p className="text-sm text-slate-400">
        Strumenti riservati agli account test. Il nuovo viaggio conserva
        account, gilda e storico, ma riparte da cinque reclute senza classe:
        ciascuna dovrà scegliere una Class Hall.
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
              <StatBox label="senza classe"
                       value={status.roster?.classless_count ?? "—"} />
              <StatBox label="classe scelta"
                       value={status.roster?.assigned_count ?? "—"} />
              <StatBox label="stati invalidi"
                       value={status.roster?.invalid_class_state_count ?? "—"} />
            </div>
          </CardContent>
        </Card>
      )}

      {release && (
        <Card className="bg-slate-800 border-slate-700"
              data-testid="tester-release-readiness">
          <CardHeader>
            <CardTitle className="flex flex-wrap items-center gap-3">
              Gate T8 — Tester release
              <span className={`text-xs rounded-full px-3 py-1 ${
                release.t8_release_ready
                  ? "bg-emerald-950 text-emerald-300"
                  : release.automated_ready
                    ? "bg-cyan-950 text-cyan-300"
                    : "bg-amber-950 text-amber-300"
              }`}>
                {release.t8_release_ready
                  ? "PRONTA PER I TESTER"
                  : release.automated_ready
                    ? "AUTOMAZIONE VERDE · MANCA CHECKLIST"
                    : "GATE TECNICI INCOMPLETI"}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="T5 verticale"
                       value={release.automated_gate?.t5_vertical_slice ? "OK" : "NO"} />
              <StatBox label="Catalogo T6"
                       value={`${release.catalog?.total ?? 0}/1500`} />
              <StatBox label="Quote / economia"
                       value={release.catalog?.ready ? "OK" : "NO"} />
              <StatBox label="Checklist umana"
                       value={`${release.human_checklist?.completed_count ?? 0}/${release.human_checklist?.required_count ?? 6}`} />
            </div>
            <div className="rounded border border-slate-700 bg-slate-900 p-3">
              <div className="mb-3 text-sm font-semibold">
                Verifiche manuali del tester
              </div>
              <div className="grid gap-2 md:grid-cols-2">
                {Object.entries(T8_CHECKLIST_LABELS).map(([key, label]) => (
                  <label key={key}
                         className="flex min-w-0 items-start gap-3 rounded border border-slate-700 p-3 text-sm">
                    <input
                      type="checkbox"
                      className="mt-0.5 h-4 w-4 shrink-0"
                      checked={Boolean(releaseChecks[key])}
                      onChange={(event) => setReleaseChecks((current) => ({
                        ...current,
                        [key]: event.target.checked,
                      }))}
                      data-testid={`t8-check-${key}`}
                    />
                    <span>{label}</span>
                  </label>
                ))}
              </div>
              <textarea
                value={releaseNotes}
                onChange={(event) => setReleaseNotes(event.target.value)}
                maxLength={2000}
                placeholder="Note del tester, problemi osservati o dispositivo usato"
                className="mt-3 min-h-24 w-full rounded border border-slate-700 bg-slate-950 p-3 text-sm"
                data-testid="t8-checklist-notes"
              />
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <Button onClick={saveReleaseChecklist}
                        disabled={loading}
                        data-testid="save-t8-checklist">
                  Registra checklist T8
                </Button>
                <span className="text-xs text-slate-500">
                  La registrazione non autorizza commit, deploy o tuning automatico.
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {smoke && (
        <Card className="bg-slate-800 border-slate-700"
              data-testid="tester-smoke-matrix">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              Matrice giocabilità
              <span className={`text-xs rounded-full px-3 py-1 ${
                smoke.ready_for_tester_slice
                  ? "bg-emerald-950 text-emerald-300"
                  : "bg-rose-950 text-rose-300"
              }`}>
                {smoke.ready_for_tester_slice
                  ? "SLICE TESTER PRONTA"
                  : "CONTROLLI BLOCCANTI"}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {smoke.checks?.map((check) => (
              <div key={check.key}
                   className="grid grid-cols-[auto_1fr_auto] gap-3 items-center rounded border border-slate-700 bg-slate-900 p-3">
                <span aria-hidden="true"
                      className={check.ok ? "text-emerald-400" : (check.blocking ? "text-rose-400" : "text-amber-400")}>
                  {check.ok ? "✓" : (check.blocking ? "✕" : "○")}
                </span>
                <div>
                  <div className="text-sm font-medium">{check.label_it}</div>
                  {check.detail_it && (
                    <div className="text-xs text-slate-500">{check.detail_it}</div>
                  )}
                </div>
                <div className="text-right text-xs font-mono text-slate-300">
                  <div>{String(check.current)}</div>
                  <div className="text-slate-600">obiettivo {String(check.target)}</div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {vertical && (
        <Card className="bg-slate-800 border-slate-700"
              data-testid="tester-vertical-slice">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              Percorso giocabile item-first
              <span className={`text-xs rounded-full px-3 py-1 ${
                vertical.t5_completion_ready
                  ? "bg-emerald-950 text-emerald-300"
                  : "bg-amber-950 text-amber-300"
              }`}>
                {vertical.t5_completion_ready
                  ? "T5 COMPLETA"
                  : vertical.ready_for_playtest
                    ? "SLICE MINIMA PRONTA"
                    : "IN COLLAUDO"}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <StatBox label="Hall scelte"
                       value={vertical.telemetry?.class_hall_chosen ?? 0} />
              <StatBox label="Dungeon risonanti"
                       value={vertical.telemetry?.resonant_dungeon_completed ?? 0} />
              <StatBox label="Raid completati"
                       value={vertical.telemetry?.completed_raids ?? 0} />
              <StatBox label="Build osservate"
                       value={`${vertical.coverage?.observed_build_count ?? 0}/${vertical.coverage?.expected_build_count ?? 81}`} />
            </div>
            {vertical.coverage && (
              <div className="space-y-3">
                <div className="grid gap-3 md:grid-cols-5">
                  {vertical.coverage.waves.map((wave) => (
                    <div key={wave.wave}
                         className={`rounded border p-3 ${
                           wave.minimum_slice_ready
                             ? "border-emerald-800 bg-emerald-950/30"
                             : "border-slate-700 bg-slate-900"
                         }`}>
                      <div className="font-semibold">Wave {wave.wave}</div>
                      <div className="mt-1 text-xs text-slate-400">
                        Percorsi {wave.journey_class_count}/{wave.class_count}
                      </div>
                      <div className="text-xs text-slate-400">
                        Build {wave.observed_build_count}/{wave.expected_build_count}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  <span className={`rounded-full px-3 py-1 ${
                    vertical.coverage.minimum_wave_slice_ready
                      ? "bg-emerald-950 text-emerald-300"
                      : "bg-slate-900 text-slate-400"
                  }`}>
                    Percorso completo in ogni Wave
                  </span>
                  <span className={`rounded-full px-3 py-1 ${
                    vertical.coverage.full_class_build_coverage_ready
                      ? "bg-emerald-950 text-emerald-300"
                      : "bg-slate-900 text-slate-400"
                  }`}>
                    27 classi / 81 build pronte al tuning
                  </span>
                </div>
                {vertical.coverage.priority_queue?.length > 0 && (
                  <div>
                    <div className="mb-2 text-xs uppercase text-slate-500">
                      Prossime classi da collaudare
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      {vertical.coverage.priority_queue.slice(0, 8).map((entry) => (
                        <div key={entry.class_slug}
                             className="rounded border border-slate-700 bg-slate-900 px-3 py-2 text-sm">
                          <span className="font-medium">{entry.class_name_it}</span>
                          <span className="ml-2 text-xs text-slate-500">
                            Wave {entry.wave} · build {entry.observed_build_count}/{entry.expected_build_count}
                          </span>
                          {entry.missing_build_ids.length > 0 && (
                            <div className="mt-1 text-xs text-slate-500">
                              Mancano: {entry.missing_build_ids.join(", ")}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {vertical.balance && (
              <div className="space-y-3 rounded border border-slate-700 bg-slate-950/40 p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold">Campioni per il bilanciamento</div>
                    <div className="text-xs text-slate-500">
                      Obiettivo minimo {vertical.balance.minimum_samples_per_build} attività comparabili per build
                    </div>
                  </div>
                  <div className="flex gap-2 text-xs">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-slate-300">
                      Pronte {vertical.balance.sample_ready_build_count}/{vertical.balance.expected_build_count}
                    </span>
                    <span className={`rounded-full px-3 py-1 ${
                      vertical.balance.review_signal_count
                        ? "bg-amber-950 text-amber-300"
                        : "bg-slate-900 text-slate-400"
                    }`}>
                      Segnali {vertical.balance.review_signal_count}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-slate-500">
                  {vertical.balance.methodology_it}
                </p>
                {vertical.balance.controlled && (
                  <div className="rounded border border-cyan-900 bg-cyan-950/20 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <div className="text-sm font-semibold text-cyan-200">
                          Confronto controllato delle tre build
                        </div>
                        <div className="text-xs text-cyan-300/70">
                          Stesso incontro e stessa squadra
                        </div>
                      </div>
                      <div className="flex gap-2 text-xs">
                        <span className="rounded-full bg-slate-900 px-3 py-1 text-cyan-200">
                          Classi {vertical.balance.controlled.ready_class_count}/{vertical.balance.controlled.expected_class_count}
                        </span>
                        <span className="rounded-full bg-slate-900 px-3 py-1 text-cyan-200">
                          Build {vertical.balance.controlled.ready_build_count}/{vertical.balance.controlled.expected_build_count}
                        </span>
                        <span className={`rounded-full px-3 py-1 ${
                          vertical.balance.controlled.replication_ready
                            ? "bg-emerald-950 text-emerald-300"
                            : "bg-slate-900 text-slate-400"
                        }`}>
                          Replica {vertical.balance.controlled.replicated_ready_build_count}/{vertical.balance.controlled.expected_build_count}
                        </span>
                      </div>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">
                      {vertical.balance.controlled.methodology_it}
                    </p>
                    <div className="mt-3 flex flex-wrap items-center gap-3">
                      <Button
                        type="button"
                        onClick={downloadTuningExport}
                        disabled={!vertical.balance.controlled.export_bundle}
                        data-testid="download-tuning-export"
                      >
                        Scarica export tuning
                      </Button>
                      {vertical.balance.controlled.export_bundle?.sha256 && (
                        <span className="font-mono text-[11px] text-slate-500">
                          SHA-256 {vertical.balance.controlled.export_bundle.sha256.slice(0, 16)}…
                        </span>
                      )}
                    </div>
                    {vertical.balance.controlled.review_queue?.length > 0 ? (
                      <div className="mt-3 space-y-2">
                        {vertical.balance.controlled.review_queue.slice(0, 8).map((entry) => (
                          <div key={entry.class_slug}
                               className="rounded border border-amber-900 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="font-medium">{entry.class_name_it}</span>
                              <span className="rounded-full bg-amber-900/60 px-2 py-0.5 uppercase">
                                {SEVERITY_LABELS[entry.severity] || entry.severity} · {entry.severity_score}
                              </span>
                              <span className="text-amber-300/80">
                                Ambito: {REVIEW_SCOPE_LABELS[entry.recommended_scope] || entry.recommended_scope}
                              </span>
                            </div>
                            <div className="mt-1 text-amber-300/80">
                              {entry.review_reasons
                                .map((reason) => CONTROLLED_REASON_LABELS[reason] || reason)
                                .join(" · ")}
                            </div>
                            <div className="mt-2 text-slate-300">
                              {entry.manual_action_it}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : vertical.balance.controlled.preliminary_review_queue?.length > 0 ? (
                      <div className="mt-3 text-xs text-amber-300">
                        Sono emersi segnali preliminari, ma servono almeno due
                        squadre indipendenti prima di trasformarli in proposte
                        di revisione.
                      </div>
                    ) : vertical.balance.controlled.replication_ready ? (
                      <div className="mt-3 text-xs text-emerald-300">
                        Due squadre indipendenti non mostrano divari che
                        richiedano modifiche immediate.
                      </div>
                    ) : (
                      <div className="mt-3 text-xs text-slate-500">
                        Servono ancora confronti condivisi con almeno due
                        squadre indipendenti per tutte le build.
                      </div>
                    )}
                  </div>
                )}
                {vertical.balance.sample_priority_queue?.length > 0 && (
                  <div>
                    <div className="mb-2 text-xs uppercase text-slate-500">
                      Prossimi campioni da raccogliere
                    </div>
                    <div className="grid gap-2 md:grid-cols-2">
                      {vertical.balance.sample_priority_queue.slice(0, 8).map((entry) => (
                        <div key={`${entry.class_slug}:${entry.build_id}`}
                             className="rounded bg-slate-900 px-3 py-2 text-sm">
                          <span className="font-medium">{entry.class_name_it}</span>
                          <span className="ml-2 text-slate-400">{entry.build_name_it}</span>
                          <div className="text-xs text-slate-500">
                            Wave {entry.wave} · {entry.comparable_samples}/{entry.samples} comparabili · ne mancano {entry.samples_needed}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {vertical.balance.review_queue?.length > 0 && (
                  <div>
                    <div className="mb-2 text-xs uppercase text-amber-400">
                      Segnali da esaminare
                    </div>
                    <div className="space-y-2">
                      {vertical.balance.review_queue.slice(0, 8).map((entry) => (
                        <div key={`${entry.class_slug}:${entry.build_id}`}
                             className="rounded border border-amber-900 bg-amber-950/30 px-3 py-2 text-xs text-amber-200">
                          {entry.class_name_it} · {entry.build_name_it}: {entry.review_signals.join(", ")}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
            {vertical.bottleneck && (
              <div className="rounded border border-amber-800 bg-amber-950/40 p-3 text-sm text-amber-200">
                Prossima prova richiesta: {vertical.bottleneck.label_it}
              </div>
            )}
            {vertical.t5_bottleneck && (
              <div className="rounded border border-cyan-900 bg-cyan-950/30 p-3 text-sm text-cyan-200">
                Gate T5 successivo: {vertical.t5_bottleneck.label_it}
              </div>
            )}
            <div className="space-y-3">
              {vertical.adventurers?.slice(0, 10).map((adventurer) => (
                <div key={adventurer.adventurer_id}
                     className="rounded border border-slate-700 bg-slate-900 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <span className="font-medium">{adventurer.name}</span>
                      <span className="ml-2 text-xs text-slate-500">
                        {adventurer.class_slug || "senza classe"} · livello {adventurer.level}
                      </span>
                    </div>
                    <span className="font-mono text-xs text-slate-300">
                      {adventurer.completed_steps}/{adventurer.total_steps}
                    </span>
                  </div>
                  <div className="mt-3 grid gap-2 md:grid-cols-3">
                    {adventurer.steps.map((step) => (
                      <div key={step.key}
                           className={`rounded px-2 py-1 text-xs ${
                             step.completed
                               ? "bg-emerald-950 text-emerald-300"
                               : "bg-slate-800 text-slate-500"
                           }`}>
                        {step.completed ? "✓" : "○"} {step.label_it}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle>Azioni</CardTitle></CardHeader>
        <CardContent className="flex flex-col md:flex-row gap-3">
          <ConfirmButton label="Aggiungi reclute senza classe"
                         confirmText="Porta il roster a 20. Ogni nuova recluta dovrà scegliere la propria Class Hall."
                         onConfirm={() => invoke("grant-adventurers")}
                         testId="grant-btn" />
          <ConfirmButton label="Nuovo viaggio Class Hall"
                         confirmText="Archivia il roster attivo, libera l'equipaggiamento e crea cinque reclute senza classe. Account, gilda e storico restano intatti."
                         onConfirm={() => invoke("reset-class-hall-journey", true)}
                         testId="reset-class-hall-journey-btn" />
          <ConfirmButton label="Set tester MAX"
                         confirmText="Gilda lv 15, strutture sbloccate, oro 100k e rosa completa di 39 avventurieri al livello 80: 27 classi più due squadre indipendenti da sei supporti per i dungeon da 7. Le nuove reclute restano senza classe."
                         onConfirm={() => invoke("set-max", needConfirm && pendingTool === "set-max")}
                         testId="set-max-btn" />
          <ConfirmButton label="Set tester MIN"
                         confirmText="Gilda e strutture tornano allo stato iniziale, oro 100 e tre avventurieri attivi. Gli item degli avventurieri archiviati vengono liberati; le Class Hall dei tre mantenuti non vengono azzerate."
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
