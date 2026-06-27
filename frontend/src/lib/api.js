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
