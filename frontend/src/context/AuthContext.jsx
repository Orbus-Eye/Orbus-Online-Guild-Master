import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api, TOKEN_KEY, setUnauthorizedHandler, formatApiError } from "../lib/api";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    // user states: undefined = loading, null = guest, object = authenticated
    const [user, setUser] = useState(undefined);
    const [guild, setGuild] = useState(undefined); // undefined = unknown, null = none, object = guild

    const logout = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
        setUser(null);
        setGuild(null);
    }, []);

    useEffect(() => {
        setUnauthorizedHandler(() => logout());
    }, [logout]);

    const refreshMe = useCallback(async () => {
        const token = localStorage.getItem(TOKEN_KEY);
        if (!token) {
            setUser(null);
            setGuild(null);
            return;
        }
        try {
            const { data } = await api.get("/auth/me");
            setUser(data.user);
        } catch {
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

    useEffect(() => {
        refreshMe();
    }, [refreshMe]);

    useEffect(() => {
        if (user) {
            refreshGuild();
        }
    }, [user, refreshGuild]);

    const login = async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        localStorage.setItem(TOKEN_KEY, data.access_token);
        setUser(data.user);
        return data.user;
    };

    const register = async (email, username, password) => {
        const { data } = await api.post("/auth/register", { email, username, password });
        localStorage.setItem(TOKEN_KEY, data.access_token);
        setUser(data.user);
        setGuild(null);
        return data.user;
    };

    const createGuild = async (name, description) => {
        const { data } = await api.post("/guilds", { name, description });
        setGuild(data.guild);
        return data.guild;
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                guild,
                login,
                logout,
                register,
                createGuild,
                refreshGuild,
                formatApiError,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
    return ctx;
};
