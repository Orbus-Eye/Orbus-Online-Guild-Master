import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const TOKEN_KEY = "orbus_token";

// ROUND 11.1 Slice 2 — Auth migration to httpOnly cookies + CSRF.
//   * `withCredentials: true` → browser sends/receives the `access_token`
//     httpOnly cookie on every API call.
//   * `csrf_token` (memory-only) → echoed in `X-CSRF-Token` header on
//     POST/PATCH/PUT/DELETE for the backend double-submit check.
//   * `Authorization: Bearer` fallback retained for 14 days post-deploy so
//     legacy clients (and the existing test suite) keep working without
//     immediate rewrite.

export const api = axios.create({
    baseURL: API,
    headers: { "Content-Type": "application/json" },
    withCredentials: true,
});

// In-memory CSRF token. NEVER persisted to localStorage (so XSS cannot
// read it; double-submit cookie + header is the protection mechanism).
let _csrfToken = null;
export function setCsrfToken(tok) { _csrfToken = tok || null; }
export function getCsrfToken() { return _csrfToken; }

api.interceptors.request.use((config) => {
    // Bearer fallback (14gg post-deploy). Cookie auth takes precedence
    // server-side, but we keep emitting the header so legacy clients keep
    // working through the transition window.
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    // CSRF double-submit header for mutating methods.
    const method = (config.method || "get").toLowerCase();
    if (["post", "patch", "put", "delete"].includes(method) && _csrfToken) {
        config.headers["X-CSRF-Token"] = _csrfToken;
    }
    return config;
});

// register a global 401 handler from AuthContext at runtime
let onUnauthorized = null;
export const setUnauthorizedHandler = (fn) => {
    onUnauthorized = fn;
};

// Avoid infinite CSRF refresh loop on the SAME failing request.
const _csrfRetryFlag = "__csrfRetried";

async function _refreshCsrf() {
    try {
        const r = await axios.get(`${API}/auth/csrf`, { withCredentials: true });
        setCsrfToken(r.data?.csrf_token || null);
        return r.data?.csrf_token || null;
    } catch (_e) {
        return null;
    }
}

api.interceptors.response.use(
    (res) => res,
    async (err) => {
        const status = err?.response?.status;
        const _detail = err?.response?.data?.detail;
        if (typeof _detail === "string") {
            err.normalizedMessage = _detail;
        } else if (_detail && typeof _detail === "object") {
            err.normalizedMessage = _detail.user_message
                || _detail.message
                || _detail.code
                || JSON.stringify(_detail);
        }
        // ROUND 11.1 Slice 2 — CSRF 403 single-retry path.
        if (
            status === 403 &&
            _detail && _detail.code === "auth.csrf.invalid" &&
            !err.config?.[_csrfRetryFlag]
        ) {
            err.config[_csrfRetryFlag] = true;
            const fresh = await _refreshCsrf();
            if (fresh) {
                err.config.headers["X-CSRF-Token"] = fresh;
                return api.request(err.config);
            }
            toast.error("Token CSRF non valido. Aggiorna la pagina.");
        }
        if (status === 401 && typeof onUnauthorized === "function") {
            onUnauthorized();
        }
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
    return formatErrorDetail(detail);
}

export function formatErrorDetail(detail) {
    if (detail == null) return "Something went wrong.";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
        return detail
            .map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e)))
            .filter(Boolean)
            .join(" ");
    }
    if (typeof detail === "object") {
        if (typeof detail.user_message === "string") return detail.user_message;
        if (typeof detail.message === "string") return detail.message;
        if (typeof detail.msg === "string") return detail.msg;
        if (typeof detail.code === "string") return detail.code;
    }
    return String(detail);
}

// Phase 13.1 — lazy trait preview for an adventurer
export async function getTraitPreview(adventurerId) {
    const { data } = await api.get(`/adventurers/${adventurerId}/trait-preview`);
    return data;
}

// ROUND 11.1 Slice 2 — fetch + cache the CSRF token. Exposed for AuthContext
// to call after login and at app boot.
export async function refreshCsrfToken() {
    return _refreshCsrf();
}
