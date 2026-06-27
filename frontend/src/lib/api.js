import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const TOKEN_KEY = "orbus_token";

export const api = axios.create({
    baseURL: API,
    headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// register a global 401 handler from AuthContext at runtime
let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
    onUnauthorized = fn;
};

api.interceptors.response.use(
    (res) => res,
    (err) => {
        const status = err?.response?.status;
        if (status === 401 && typeof onUnauthorized === "function") {
            onUnauthorized();
        }
        // ROUND 6B.2b — Global 423 Locked handler (feature.locked from territory guards).
        // ROUND 6B.3 Wave 1.5 — Extended to handle roster_over_capacity and
        // adventurers.retired_in_set, both of which surface as 423 with a
        // structured detail.code and a user-friendly user_message.
        if (status === 423) {
            const detail = err?.response?.data?.detail;
            if (detail && detail.code === "feature.locked") {
                const msg = detail.user_message
                    || `Funzione bloccata: richiede ${detail.required_structure_name_it || detail.required_structure} Lv${detail.required_level}`;
                toast.warning(msg, {
                    action: {
                        label: "Vai al Territorio",
                        onClick: () => { window.location.href = "/territory"; },
                    },
                    duration: 6000,
                });
            } else if (detail && detail.code === "roster_over_capacity") {
                toast.warning(detail.user_message
                    || `Roster oltre capacità: ${detail.current}/${detail.cap}.`, {
                    action: {
                        label: "Gestisci capacità",
                        onClick: () => { window.location.href = "/roster/manage"; },
                    },
                    duration: 7000,
                });
            } else if (detail && detail.code === "adventurers.retired_in_set") {
                toast.error(detail.user_message
                    || `Selezione include ${detail.count} avventurieri congedati.`, {
                    duration: 6000,
                });
            } else if (detail && detail.code === "equip.target_retired") {
                toast.error(detail.user_message
                    || "Non puoi equipaggiare un avventuriero congedato.", {
                    duration: 6000,
                });
            }
        }
        return Promise.reject(err);
    },
);

export function formatApiError(err) {
    const detail = err?.response?.data?.detail;
    if (detail == null) return err?.message || "Something went wrong.";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
            .filter(Boolean)
            .join(" ");
    }
    if (detail && typeof detail.msg === "string") return detail.msg;
    return String(detail);
}

// Phase 13.1 — lazy trait preview for an adventurer
export async function getTraitPreview(adventurerId) {
    const { data } = await api.get(`/adventurers/${adventurerId}/trait-preview`);
    return data;
}
