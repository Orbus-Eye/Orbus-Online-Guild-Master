/* ROUND 11.2 TASK 8 — Public minimal navbar for SEO-facing pages.
 *
 * Logged-out: logo + 2 CTA (Crea account / Accedi).
 * Logged-in: logo + link rapido al Dashboard (no spam visuale).
 * Used by `/traits` and `/stats` (anyone can land here from search).
 */
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";


export default function PublicNavbar() {
    const { user } = useAuth();
    const isAuthed = !!user;

    return (
        <header
            data-testid="public-navbar"
            className="border-b border-border/60 bg-background/95 backdrop-blur sticky top-0 z-20"
        >
            <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
                <Link
                    to="/"
                    data-testid="public-navbar-logo"
                    className="flex items-center gap-2 text-amber font-semibold tracking-wide"
                >
                    <span className="text-base">◆</span>
                    <span className="text-sm sm:text-base">ORBUS ONLINE</span>
                </Link>

                {isAuthed ? (
                    <Link
                        to="/dashboard"
                        data-testid="public-navbar-dashboard"
                        className="text-xs sm:text-sm border border-border rounded-sm px-3 py-1.5 hover:border-amber/60 hover:text-amber"
                    >
                        → Dashboard
                    </Link>
                ) : (
                    <div className="flex items-center gap-2">
                        <Link
                            to="/login"
                            data-testid="public-navbar-login"
                            className="text-xs sm:text-sm text-muted-foreground hover:text-foreground px-2 py-1.5"
                        >
                            Accedi
                        </Link>
                        <Link
                            to="/register"
                            data-testid="public-navbar-register"
                            className="text-xs sm:text-sm bg-amber/90 text-background px-3 py-1.5 rounded-sm font-semibold hover:bg-amber"
                        >
                            Crea account
                        </Link>
                    </div>
                )}
            </div>
        </header>
    );
}
