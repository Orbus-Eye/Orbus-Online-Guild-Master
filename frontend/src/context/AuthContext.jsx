import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, setUnauthorizedHandler, TOKEN_STORAGE_KEY } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY));
    const [user, setUser] = useState(null);
    const [guild, setGuild] = useState(null);
    const [loading, setLoading] = useState(true);

    const logout = useCallback(() => {
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        setToken(null);
        setUser(null);
        setGuild(null);
    }, []);

    // 401 handler
    useEffect(() => {
        setUnauthorizedHandler(() => logout());
    }, [logout]);

    // Bootstrap: se abbiamo un token, carica user + gilda
    const refresh = useCallback(async () => {
        const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
        if (!stored) {
            setUser(null);
            setGuild(null);
            setLoading(false);
            return;
        }
        try {
            const { data: me } = await api.get("/auth/me");
            setUser(me);
            try {
                const { data: g } = await api.get("/guilds/mine");
                setGuild(g);
            } catch (err) {
                if (err?.response?.status === 404) setGuild(null);
                else throw err;
            }
        } catch {
            // interceptor già gestisce 401
            setUser(null);
            setGuild(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const login = useCallback(
        async (email, password) => {
            const { data } = await api.post("/auth/login", { email, password });
            localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
            setToken(data.access_token);
            setUser(data.user);
            // fetch guild
            try {
                const { data: g } = await api.get("/guilds/mine");
                setGuild(g);
            } catch (err) {
                if (err?.response?.status === 404) setGuild(null);
                else throw err;
            }
            return data.user;
        },
        [],
    );

    const register = useCallback(async (email, password) => {
        const { data } = await api.post("/auth/register", { email, password });
        localStorage.setItem(TOKEN_STORAGE_KEY, data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        setGuild(null);
        return data.user;
    }, []);

    const createGuild = useCallback(async (name, description) => {
        const { data } = await api.post("/guilds", { name, description });
        setGuild(data);
        return data;
    }, []);

    const value = useMemo(
        () => ({
            token,
            user,
            guild,
            loading,
            isAuthenticated: !!token && !!user,
            hasGuild: !!guild,
            login,
            register,
            logout,
            createGuild,
            refresh,
        }),
        [token, user, guild, loading, login, register, logout, createGuild, refresh],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth deve essere usato dentro AuthProvider");
    return ctx;
}
