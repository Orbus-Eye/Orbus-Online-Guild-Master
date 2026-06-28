import { createContext, useContext, useEffect, useState, useCallback } from "react";
import {
    api, TOKEN_KEY, setUnauthorizedHandler, formatApiError,
    refreshCsrfToken, setCsrfToken,
} from "../lib/api";

const AuthContext = createContext(null);

// ROUND 11.1 Slice 2 — Auth migration to httpOnly cookies + CSRF.
//
// Order at boot:
//   1. Try `GET /api/auth/me` (sends `withCredentials` → cookie auth).
//   2. If 401, fall back to Bearer if a legacy token still in localStorage
//      (14gg fallback window). If `me` succeeds via cookie *and* a legacy
//      token is present, opportunistically clear it.
//   3. Fetch CSRF token if user is authenticated.

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(undefined);
    const [guild, setGuild] = useState(undefined);

    const logout = useCallback(async () => {
        // ROUND 11.1 Slice 2 P1 — best-effort + always-clean.
        //   1. Call backend logout WITHOUT a body so Pydantic doesn't reject
        //      a `{}` payload (LogoutIn is now Optional but historical
        //      builds may still expect omitted body for cleanest semantics).
        //   2. ALWAYS scrub in-memory state + legacy localStorage token,
        //      independent of the backend response. The cookies are server-
        //      cleared on 200; if the network failed or the server errored,
        //      `setUser(null)` still drops the UI to /login so the user
        //      isn't left in an ambiguous "looks logged out" state with a
        //      live session.
        try {
            await api.post("/auth/logout");
        } catch (_e) { /* idempotent, swallow */ }
        localStorage.removeItem(TOKEN_KEY);
        setCsrfToken(null);
        setUser(null);
        setGuild(null);
    }, []);

    useEffect(() => {
        setUnauthorizedHandler(() => { logout(); });
    }, [logout]);

    const refreshMe = useCallback(async () => {
        // Try cookie auth first (no token in localStorage required).
        try {
            const { data } = await api.get("/auth/me");
            setUser(data.user);
            // Opportunistic cleanup: if cookie auth worked and a legacy
            // token is still in localStorage, scrub it.
            if (localStorage.getItem(TOKEN_KEY)) {
                localStorage.removeItem(TOKEN_KEY);
            }
            await refreshCsrfToken();
            return;
        } catch (err) {
            const status = err?.response?.status;
            if (status !== 401) {
                setUser(null);
                setGuild(null);
                return;
            }
        }
        // 401 → no cookie session. Bearer fallback (14gg window).
        const legacyToken = localStorage.getItem(TOKEN_KEY);
        if (!legacyToken) {
            setUser(null);
            setGuild(null);
            return;
        }
        try {
            const { data } = await api.get("/auth/me");
            setUser(data.user);
            await refreshCsrfToken();
        } catch {
            localStorage.removeItem(TOKEN_KEY);
            setUser(null);
            setGuild(null);
        }
    }, []);

    const refreshGuild = useCallback(async () => {
        try {
            const { data } = await api.get("/guilds/me");
            setGuild(data.guild);
        } catch (err) {
            if (err?.response?.status === 404) setGuild(null);
        }
    }, []);

    useEffect(() => { refreshMe(); }, [refreshMe]);

    useEffect(() => { if (user) refreshGuild(); }, [user, refreshGuild]);

    const login = async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        // ROUND 11.1 Slice 2 — no localStorage write in new flow. The
        // `access_token` cookie is set httpOnly by the backend. We still
        // *receive* `data.access_token` in the body for transition
        // compatibility, but we DO NOT persist it.
        setUser(data.user);
        await refreshCsrfToken();
        return data.user;
    };

    const register = async (email, username, password) => {
        const { data } = await api.post("/auth/register", { email, username, password });
        setUser(data.user);
        setGuild(null);
        await refreshCsrfToken();
        return data.user;
    };

    const createGuild = async (name, description) => {
        const { data } = await api.post("/guilds", { name, description });
        setGuild(data.guild);
        return data.guild;
    };

    return (
        <AuthContext.Provider value={{
            user, guild, login, logout, register, createGuild,
            refreshGuild, formatApiError,
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
};
