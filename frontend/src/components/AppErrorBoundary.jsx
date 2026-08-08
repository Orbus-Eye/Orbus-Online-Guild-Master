import React from "react";

/**
 * FASE 1 (2026-08-08) — Error boundary GLOBALE.
 *
 * Prima di questo componente un qualunque errore di render in una pagina
 * smontava l'intero albero React e il giocatore vedeva solo una schermata
 * nera (è successo col Deposito, vedi inventory_deposito.test.jsx).
 * Ora l'errore viene contenuto e il giocatore riceve un fallback leggibile
 * in tema di gioco con due vie d'uscita a pieno reload (che resettano
 * anche lo stato del boundary).
 *
 * `ReportErrorBoundary` resta come boundary locale più specifico per le
 * pagine report; questo è la rete di sicurezza di ultima istanza.
 */
export default class AppErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorMsg: "" };
    }

    static getDerivedStateFromError(error) {
        return {
            hasError: true,
            errorMsg: (error && error.message) || "Errore di rendering sconosciuto",
        };
    }

    componentDidCatch(error, info) {
        try {
            console.error("[AppErrorBoundary]", error, info);
        } catch (_) {
            /* noop */
        }
    }

    render() {
        if (this.state.hasError) {
            return (
                <div
                    data-testid="app-error-boundary"
                    className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-8"
                >
                    <div className="max-w-md text-center space-y-4 border border-border rounded-md p-6 bg-card">
                        <div className="text-3xl" aria-hidden="true">🕯️</div>
                        <h2 className="text-lg font-semibold tracking-wide text-amber">
                            Un incantesimo è andato storto
                        </h2>
                        <p className="text-sm text-muted-foreground">
                            Questa pagina ha incontrato un errore imprevisto. La tua
                            gilda e i tuoi progressi sono al sicuro: nessun dato è
                            andato perso.
                        </p>
                        <p className="text-[10px] font-mono text-muted-foreground/60 break-words">
                            {this.state.errorMsg}
                        </p>
                        <div className="flex items-center justify-center gap-3 flex-wrap">
                            <button
                                type="button"
                                onClick={() => window.location.reload()}
                                data-testid="app-error-reload-btn"
                                className="text-xs px-3 py-1.5 border border-amber/60 text-amber rounded-sm hover:bg-amber/10"
                            >
                                ↻ Riprova
                            </button>
                            <button
                                type="button"
                                onClick={() => { window.location.href = "/dashboard"; }}
                                data-testid="app-error-home-btn"
                                className="text-xs px-3 py-1.5 border border-border rounded-sm hover:bg-secondary"
                            >
                                ⚑ Torna al Quartier Generale
                            </button>
                        </div>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}
