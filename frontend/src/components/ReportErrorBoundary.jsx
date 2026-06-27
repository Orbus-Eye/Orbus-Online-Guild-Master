import React from "react";

/**
 * Phase 19.1 hotfix — local error boundary for the Expedition / Raid report
 * pages. Catches any unexpected runtime error (e.g. an undefined `lang`
 * reference in a future helper) and renders a graceful fallback instead of
 * unmounting the whole React tree (which would show a blank black screen).
 *
 * Usage:
 *   <ReportErrorBoundary fallbackTitle="Report unavailable" fallbackBody="...">
 *     <ExpeditionReportPage />
 *   </ReportErrorBoundary>
 */
export default class ReportErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorMsg: "" };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, errorMsg: (error && error.message) || "Unknown render error" };
    }

    componentDidCatch(error, info) {
        // best-effort log; never crash on logger failure
        try {
            // eslint-disable-next-line no-console
            console.error("[ReportErrorBoundary]", error, info);
        } catch (_) {
            /* noop */
        }
    }

    render() {
        if (this.state.hasError) {
            const title = this.props.fallbackTitle || "Report not available";
            const body =
                this.props.fallbackBody ||
                "Some details of this report could not be displayed, but your run is safe. Try again later or contact support.";
            return (
                <div
                    data-testid="report-error-boundary"
                    className="min-h-screen bg-bg text-fg flex flex-col items-center justify-center p-8"
                >
                    <div className="max-w-md text-center space-y-4 border border-fg/15 rounded-md p-6 bg-card/60">
                        <h2 className="text-lg font-semibold tracking-wide text-amber">
                            {title}
                        </h2>
                        <p className="text-sm text-fg/70">{body}</p>
                        <p className="text-[10px] font-mono text-fg/40">
                            {this.state.errorMsg}
                        </p>
                        <button
                            onClick={() => window.history.back()}
                            data-testid="report-error-back-btn"
                            className="text-xs px-3 py-1 border border-fg/30 rounded-sm hover:bg-card"
                        >
                            ← Back
                        </button>
                    </div>
                </div>
            );
        }
        return this.props.children;
    }
}
