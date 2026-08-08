import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../components/ui/select";
import { toast } from "sonner";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL;

/** ROUND 16.5.1 B.1 — Admin CRUD eventi continentali.
 * Estensione del sistema world_events (nessuna nuova collection).
 * Solo istanze dal catalog fisso di 12 eventi.
 */
export default function AdminWorldEvents() {
  const [events, setEvents] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [filterContinent, setFilterContinent] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [loading, setLoading] = useState(false);
  // Create form
  const [newContinent, setNewContinent] = useState("");
  const [newSlug, setNewSlug] = useState("");
  const [newStart, setNewStart] = useState("");
  const [newEnd, setNewEnd] = useState("");

  const authHeader = () => {
    const t = localStorage.getItem("token");
    return t ? { Authorization: `Bearer ${t}` } : {};
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filterContinent) params.continent_slug = filterContinent;
      if (filterStatus) params.status = filterStatus;
      const r = await axios.get(`${API}/api/admin/world-events/all`, {
        headers: authHeader(), params,
      });
      setEvents(r.data.instances || []);
      const c = await axios.get(`${API}/api/admin/world-events/catalog`, {
        headers: authHeader(),
      });
      setCatalog(c.data.catalog || []);
    } catch (e) {
      toast.error(`Errore caricamento: ${e.response?.data?.detail || e.message}`);
    } finally {
      setLoading(false);
    }
  }, [filterContinent, filterStatus]);

  useEffect(() => { load(); }, [load]);

  const createEvent = async () => {
    if (!newContinent || !newSlug || !newStart || !newEnd) {
      toast.error("Compila tutti i campi");
      return;
    }
    try {
      await axios.post(`${API}/api/admin/world-events`, {
        continent_slug: newContinent, event_slug: newSlug,
        starts_at: newStart, ends_at: newEnd,
      }, { headers: authHeader() });
      toast.success("Evento creato");
      setNewContinent(""); setNewSlug(""); setNewStart(""); setNewEnd("");
      load();
    } catch (e) {
      toast.error(`Errore: ${e.response?.data?.detail || e.message}`);
    }
  };

  const action = async (eid, verb) => {
    try {
      await axios.post(`${API}/api/admin/world-events/${eid}/${verb}`, {},
        { headers: authHeader() });
      toast.success(`Azione '${verb}' completata`);
      load();
    } catch (e) {
      toast.error(`Errore: ${e.response?.data?.detail || e.message}`);
    }
  };

  return (
    <div className="p-6 space-y-6 min-h-screen bg-slate-900 text-slate-100"
         data-testid="admin-world-events-page">
      <h1 className="text-3xl font-bold">Admin — Eventi Continentali</h1>
      <p className="text-sm text-slate-400">
        Round 16.5.1 B.1 — CRUD istanze dal catalog fisso (12 eventi).
        Modifiers non modificabili qui.
      </p>

      {/* Filtri */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle>Filtri</CardTitle></CardHeader>
        <CardContent className="flex gap-4 flex-wrap">
          <Input placeholder="continente slug" value={filterContinent}
                 data-testid="filter-continent"
                 onChange={(e) => setFilterContinent(e.target.value)}
                 className="max-w-xs bg-slate-900" />
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="max-w-xs bg-slate-900" data-testid="filter-status">
              <SelectValue placeholder="tutti gli stati" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">tutti</SelectItem>
              <SelectItem value="scheduled">scheduled</SelectItem>
              <SelectItem value="active">active</SelectItem>
              <SelectItem value="expired">expired</SelectItem>
            </SelectContent>
          </Select>
          <Button onClick={load} data-testid="reload-btn">Aggiorna</Button>
        </CardContent>
      </Card>

      {/* Create form */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader><CardTitle>Crea nuova istanza</CardTitle></CardHeader>
        <CardContent className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Input placeholder="continent_slug" value={newContinent}
                 data-testid="new-continent"
                 onChange={(e) => setNewContinent(e.target.value)}
                 className="bg-slate-900" />
          <Select value={newSlug} onValueChange={setNewSlug}>
            <SelectTrigger className="bg-slate-900" data-testid="new-event-slug">
              <SelectValue placeholder="event_slug (dal catalog)" />
            </SelectTrigger>
            <SelectContent>
              {catalog.map((c) => (
                <SelectItem key={c.slug} value={c.slug}>
                  {c.name_it || c.slug}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input type="datetime-local" value={newStart}
                 data-testid="new-start"
                 onChange={(e) => setNewStart(e.target.value)}
                 className="bg-slate-900" />
          <Input type="datetime-local" value={newEnd}
                 data-testid="new-end"
                 onChange={(e) => setNewEnd(e.target.value)}
                 className="bg-slate-900" />
          <Button onClick={createEvent} className="md:col-span-4"
                  data-testid="create-event-btn">Crea evento</Button>
        </CardContent>
      </Card>

      {/* Lista */}
      <Card className="bg-slate-800 border-slate-700">
        <CardHeader>
          <CardTitle>Istanze ({events.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading && <p className="text-slate-400">Caricamento…</p>}
          <div className="space-y-2">
            {events.map((e) => (
              <div key={e.id}
                   data-testid={`event-row-${e.id}`}
                   className="border border-slate-700 rounded p-3 flex flex-wrap gap-2 items-center">
                <span className="font-mono text-xs text-slate-500">
                  {e.id.slice(0, 8)}
                </span>
                <span className="font-semibold">{e.continent_slug}</span>
                <span className="text-slate-400">/</span>
                <span>{e.event_slug}</span>
                <span className={`px-2 py-1 rounded text-xs font-mono ${
                  e.status === "active" ? "bg-green-900 text-green-200" :
                  e.status === "scheduled" ? "bg-yellow-900 text-yellow-200" :
                  "bg-slate-700 text-slate-400"}`}>
                  {e.status}
                </span>
                <div className="ml-auto flex gap-2">
                  {e.status === "scheduled" && (
                    <Button size="sm" onClick={() => action(e.id, "activate")}
                            data-testid={`activate-${e.id}`}>Attiva</Button>
                  )}
                  {e.status === "active" && (
                    <Button size="sm" variant="destructive"
                            onClick={() => action(e.id, "deactivate")}
                            data-testid={`deactivate-${e.id}`}>Disattiva</Button>
                  )}
                  {e.status === "expired" && (
                    <Button size="sm" variant="outline"
                            onClick={() => action(e.id, "duplicate")}
                            data-testid={`duplicate-${e.id}`}>Duplica</Button>
                  )}
                </div>
              </div>
            ))}
            {!loading && events.length === 0 && (
              <p className="text-slate-400" data-testid="no-events-msg">
                Nessuna istanza trovata.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
