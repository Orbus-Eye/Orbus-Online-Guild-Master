// ROUND 16.0 — Phase 5 — Mobile full-screen menu drawer.
// Triggered from MobileBottomNav's "Menu" tab. Renders 8 macro-section
// accordions. Only one accordion open at a time. Closes on any nav click.

import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { X, ChevronDown } from "lucide-react";
import { NAV_SECTIONS } from "./navMenu";
import { NavBadge } from "./AppHeader";
import { useAuth } from "../context/AuthContext";

export default function MobileMenuDrawer({ open, onClose }) {
    const { pathname } = useLocation();
    const { user, logout } = useAuth();
    const [openSection, setOpenSection] = useState(null);

    // Reset accordion state every time the drawer opens.
    useEffect(() => {
        if (open) setOpenSection(null);
    }, [open]);

    // Lock body scroll while drawer is open.
    useEffect(() => {
        if (!open) return;
        const prev = document.body.style.overflow;
        document.body.style.overflow = "hidden";
        return () => { document.body.style.overflow = prev; };
    }, [open]);

    if (!open) return null;

    const handleNavClick = () => onClose();
    const handleLogout = () => {
        onClose();
        logout();
    };

    const isActive = (to) => {
        if (!to) return false;
        // Anchor links → match by pathname before the hash.
        const [path] = to.split("#");
        return pathname === path;
    };

    return (
        <div
            data-testid="mobile-menu-drawer"
            role="dialog"
            aria-modal="true"
            aria-label="Menu di navigazione"
            className="md:hidden fixed inset-0 z-40 bg-background"
        >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-4 border-b border-border">
                <div className="flex items-center gap-2">
                    <span className="text-amber">◆</span>
                    <span className="text-xs tracking-widest text-muted-foreground">
                        MENU
                    </span>
                </div>
                <button
                    type="button"
                    data-testid="mobile-menu-close"
                    aria-label="Chiudi menu"
                    onClick={onClose}
                    className="p-2 rounded-sm hover:bg-secondary text-muted-foreground hover:text-foreground"
                    style={{ minWidth: 44, minHeight: 44 }}
                >
                    <X size={20} aria-hidden="true" />
                </button>
            </div>

            {/* Scrollable content */}
            <div className="overflow-y-auto" style={{ maxHeight: "calc(100vh - 64px)" }}>
                <ul className="divide-y divide-border">
                    {NAV_SECTIONS.map((sec) => {
                        const expanded = openSection === sec.id;
                        const isAccount = sec.id === "account";
                        // For Account, append a synthetic Logout entry below.
                        const items = sec.items || [];
                        return (
                            <li key={sec.id}>
                                <button
                                    type="button"
                                    data-testid={`mobile-menu-section-${sec.id}`}
                                    aria-expanded={expanded}
                                    onClick={() =>
                                        setOpenSection(expanded ? null : sec.id)
                                    }
                                    className="w-full flex items-center justify-between px-4 py-4 text-left hover:bg-secondary/40 active:bg-secondary/60 transition-colors"
                                    style={{ minHeight: 44 }}
                                >
                                    <span className="text-sm tracking-widest font-bold text-foreground">
                                        {sec.label.toUpperCase()}
                                    </span>
                                    <ChevronDown
                                        size={18}
                                        aria-hidden="true"
                                        className={`text-muted-foreground transition-transform ${expanded ? "rotate-180" : ""}`}
                                    />
                                </button>
                                {expanded && (
                                    <ul
                                        data-testid={`mobile-menu-items-${sec.id}`}
                                        className="bg-card/50 border-t border-border/60"
                                    >
                                        {items.map((it) => {
                                            const active = isActive(it.to);
                                            const cls = `flex items-center justify-between gap-2 px-6 py-3 text-sm transition-colors ${
                                                it.disabled
                                                    ? "text-muted-foreground/40 cursor-not-allowed"
                                                    : active
                                                        ? "text-amber bg-secondary/60"
                                                        : "text-foreground/85 hover:bg-secondary/40"
                                            }`;
                                            if (it.disabled || !it.to) {
                                                return (
                                                    <li key={it.testid}>
                                                        <span
                                                            data-testid={it.testid}
                                                            className={cls}
                                                            aria-disabled="true"
                                                            style={{ minHeight: 44 }}
                                                        >
                                                            <span>{it.label}</span>
                                                            {it.badge && <NavBadge label={it.badge} />}
                                                        </span>
                                                    </li>
                                                );
                                            }
                                            return (
                                                <li key={it.testid}>
                                                    <Link
                                                        to={it.to}
                                                        data-testid={it.testid}
                                                        onClick={handleNavClick}
                                                        className={cls}
                                                        style={{ minHeight: 44 }}
                                                        aria-current={active ? "page" : undefined}
                                                    >
                                                        <span>{it.label}</span>
                                                        {it.badge && <NavBadge label={it.badge} />}
                                                    </Link>
                                                </li>
                                            );
                                        })}
                                        {isAccount && (
                                            <li className="border-t border-border/40">
                                                <div className="px-6 py-3 text-xs text-muted-foreground">
                                                    Connesso come <span className="text-foreground">@{user?.username || "—"}</span>
                                                </div>
                                                <button
                                                    type="button"
                                                    data-testid="mobile-menu-logout"
                                                    onClick={handleLogout}
                                                    className="w-full text-left block px-6 py-3 text-sm text-foreground/85 hover:bg-secondary/40 active:bg-secondary/60"
                                                    style={{ minHeight: 44 }}
                                                >
                                                    Esci
                                                </button>
                                                {user?.is_admin && (
                                                    <>
                                                        <Link
                                                            to="/admin"
                                                            onClick={handleNavClick}
                                                            data-testid="mobile-menu-admin"
                                                            className="block px-6 py-3 text-sm text-foreground/85 hover:bg-secondary/40"
                                                            style={{ minHeight: 44 }}
                                                        >
                                                            Admin
                                                        </Link>
                                                        <Link
                                                            to="/admin/ops"
                                                            onClick={handleNavClick}
                                                            data-testid="mobile-menu-admin-ops"
                                                            className="block px-6 py-3 text-sm text-foreground/85 hover:bg-secondary/40"
                                                            style={{ minHeight: 44 }}
                                                        >
                                                            Admin Ops
                                                        </Link>
                                                        <Link
                                                            to="/admin/game-health"
                                                            onClick={handleNavClick}
                                                            data-testid="mobile-menu-admin-game-health"
                                                            className="block px-6 py-3 text-sm text-foreground/85 hover:bg-secondary/40"
                                                            style={{ minHeight: 44 }}
                                                        >
                                                            Game Health
                                                        </Link>
                                                    </>
                                                )}
                                            </li>
                                        )}
                                    </ul>
                                )}
                            </li>
                        );
                    })}
                </ul>
                <div className="px-4 py-6 text-[10px] text-muted-foreground italic text-center">
                    Orbus Online · Guild Master
                </div>
            </div>
        </div>
    );
}
