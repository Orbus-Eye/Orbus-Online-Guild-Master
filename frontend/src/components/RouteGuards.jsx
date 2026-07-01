import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

function FullScreenLoader() {
    return (
        <div
            data-testid="auth-bootstrap-loader"
            className="min-h-screen flex items-center justify-center bg-background text-muted-foreground text-sm"
        >
            <span className="opacity-70">Caricamento…</span>
            <span className="caret-blink" />
        </div>
    );
}

/** Reindirizza a /dashboard se l'utente è già loggato (login/register pages). */
export function GuestOnly({ children }) {
    const { loading, isAuthenticated, hasGuild } = useAuth();
    if (loading) return <FullScreenLoader />;
    if (isAuthenticated) return <Navigate to={hasGuild ? "/dashboard" : "/create-guild"} replace />;
    return children;
}

/** Richiede autenticazione: se manca, redirect a /login. */
export function RequireAuth({ children }) {
    const { loading, isAuthenticated } = useAuth();
    if (loading) return <FullScreenLoader />;
    if (!isAuthenticated) return <Navigate to="/login" replace />;
    return children;
}

/** Richiede che l'utente abbia già una gilda; altrimenti → /create-guild. */
export function RequireGuild({ children }) {
    const { loading, hasGuild } = useAuth();
    if (loading) return <FullScreenLoader />;
    if (!hasGuild) return <Navigate to="/create-guild" replace />;
    return children;
}

/** Opposto: pagina raggiungibile solo se NON hai ancora una gilda. */
export function RequireNoGuild({ children }) {
    const { loading, hasGuild } = useAuth();
    if (loading) return <FullScreenLoader />;
    if (hasGuild) return <Navigate to="/dashboard" replace />;
    return children;
}
