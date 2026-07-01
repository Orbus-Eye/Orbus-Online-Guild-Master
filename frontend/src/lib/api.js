// Client HTTP centralizzato per le chiamate al backend Orbus.
// Usa REACT_APP_BACKEND_URL (obbligatorio) e allega automaticamente
// il token JWT salvato in localStorage. Su 401 forza il logout.
import axios from "axios";

const BASE_URL = process.env.REACT_APP_BACKEND_URL;
if (!BASE_URL) {
    // eslint-disable-next-line no-console
    console.error("REACT_APP_BACKEND_URL non definito in frontend/.env");
}

export const TOKEN_STORAGE_KEY = "orbus.token";

export const api = axios.create({
    baseURL: `${BASE_URL}/api`,
    headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (token) {
        config.headers = { ...config.headers, Authorization: `Bearer ${token}` };
    }
    return config;
});

// Callback registrata dall'AuthContext per gestire il logout automatico
let onUnauthorized = null;
export function setUnauthorizedHandler(fn) {
    onUnauthorized = fn;
}

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error?.response?.status === 401 && onUnauthorized) {
            onUnauthorized();
        }
        return Promise.reject(error);
    },
);

// Helper: estrae messaggio d'errore leggibile dalla response FastAPI.
export function errorMessage(err, fallback = "Errore imprevisto. Riprova.") {
    const detail = err?.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
    return fallback;
}
