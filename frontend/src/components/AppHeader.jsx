import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronDown } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import LanguageSwitcher from "./LanguageSwitcher";
import MobileBottomNav from "./MobileBottomNav";
import MobileMenuDrawer from "./MobileMenuDrawer";
import { NAV_SECTIONS } from "./navMenu";

// ──────────────────────────────────────────────────────────────────────────
// ROUND 16.1.1 HOTFIX — Desktop dropdown menu refactor.
// - Lift `openId` to AppHeader so only ONE dropdown is open at a time.
// - Click-based open + click-outside listener (no more competing hover states).
// - Result: no more overlapping dropdowns when user moves between buttons.
// ──────────────────────────────────────────────────────────────────────────
const DesktopMenuButton = ({ section, isActive, openId, setOpenId }) => {
    const isOpen = openId === section.id;
    const items = section.items || [];
    return (
        <div className="relative">
            <button
                type="button"
                data-testid={`desktop-menu-trigger-${section.id}`}
                data-dropdown-region="trigger"
                onClick={() => setOpenId(isOpen ? null : section.id)}
                onMouseEnter={() => {
                    // Auto-switch dropdown on hover ONLY if another one is already open
                    // (keeps mouse-driven exploration smooth without spurious opens).
                    if (openId && openId !== section.id) setOpenId(section.id);
                }}
                aria-expanded={isOpen}
                aria-haspopup="menu"
                className={`px-3 py-1.5 text-xs tracking-widest font-bold rounded-sm transition-colors inline-flex items-center gap-1 ${
                    isActive
                        ? "text-amber bg-secondary"
                        : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
                }`}
            >
                {section.label.toUpperCase()}
                <ChevronDown size={12} aria-hidden="true" />
            </button>
            {isOpen && items.length > 0 && (
                <ul
                    data-testid={`desktop-menu-items-${section.id}`}
                    data-dropdown-region="panel"
                    role="menu"
                    className="absolute left-0 top-full mt-1 min-w-[220px] bg-card border border-border rounded-sm shadow-lg py-1 z-50"
                >
                    {items.map((it) => {
                        if (it.disabled || !it.to) {
                            return (
                                <li key={it.testid} role="none">
                                    <span
                                        data-testid={`desktop-${it.testid}`}
                                        className="block px-4 py-2 text-xs text-muted-foreground/50 cursor-not-allowed"
                                        aria-disabled="true"
                                    >
                                        {it.label}
                                    </span>
                                </li>
                            );
                        }
                        return (
                            <li key={it.testid} role="none">
                                <Link
                                    to={it.to}
                                    data-testid={`desktop-${it.testid}`}
                                    role="menuitem"
                                    onClick={() => setOpenId(null)}
                                    className="block px-4 py-2 text-xs text-foreground/85 hover:bg-secondary/60 hover:text-amber transition-colors"
                                >
                                    {it.label}
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            )}
        </div>
    );
};

// Render the Account dropdown specially to include user info + logout + admin.
const DesktopAccountMenu = ({ user, onLogout, openId, setOpenId }) => {
    const isOpen = openId === "account";
    return (
        <div className="relative">
            <button
                type="button"
                data-testid="desktop-menu-trigger-account"
                data-dropdown-region="trigger"
                onClick={() => setOpenId(isOpen ? null : "account")}
                onMouseEnter={() => { if (openId && openId !== "account") setOpenId("account"); }}
                aria-expanded={isOpen}
                aria-haspopup="menu"
                className="px-3 py-1.5 text-xs tracking-widest font-bold rounded-sm transition-colors inline-flex items-center gap-1 text-muted-foreground hover:text-foreground hover:bg-secondary/60"
            >
                ACCOUNT
                <ChevronDown size={12} aria-hidden="true" />
            </button>
            {isOpen && (
                <ul
                    role="menu"
                    data-testid="desktop-menu-items-account"
                    data-dropdown-region="panel"
                    className="absolute right-0 top-full mt-1 min-w-[220px] bg-card border border-border rounded-sm shadow-lg py-1 z-50"
                >
                    <li className="px-4 py-2 text-[10px] text-muted-foreground border-b border-border/60">
                        Connesso come <span className="text-foreground">@{user?.username || "—"}</span>
                    </li>
                    {user?.is_admin && (
                        <>
                            <li>
                                <Link
                                    to="/admin"
                                    data-testid="desktop-menu-admin"
                                    onClick={() => setOpenId(null)}
                                    className="block px-4 py-2 text-xs text-foreground/85 hover:bg-secondary/60 hover:text-amber"
                                >
                                    Admin
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/admin/ops"
                                    data-testid="desktop-menu-admin-ops"
                                    onClick={() => setOpenId(null)}
                                    className="block px-4 py-2 text-xs text-foreground/85 hover:bg-secondary/60 hover:text-amber"
                                >
                                    Admin Ops
                                </Link>
                            </li>
                            <li>
                                <Link
                                    to="/admin/game-health"
                                    data-testid="desktop-menu-admin-game-health"
                                    onClick={() => setOpenId(null)}
                                    className="block px-4 py-2 text-xs text-foreground/85 hover:bg-secondary/60 hover:text-amber"
                                >
                                    Game Health
                                </Link>
                            </li>
                            <li className="border-t border-border/40 my-1" aria-hidden="true" />
                        </>
                    )}
                    <li>
                        <button
                            type="button"
                            data-testid="desktop-menu-logout"
                            onClick={() => { setOpenId(null); onLogout(); }}
                            className="w-full text-left block px-4 py-2 text-xs text-foreground/85 hover:bg-secondary/60 hover:text-amber"
                        >
                            Esci
                        </button>
                    </li>
                </ul>
            )}
        </div>
    );
};

// Detect "is this section currently active" by matching pathname against any item.
function sectionIsActive(section, pathname) {
    return (section.items || []).some((it) => {
        if (!it.to) return false;
        const [path] = it.to.split("#");
        return pathname === path;
    });
}

export default function AppHeader({ subtitle, subtitleKey = "nav.brand_subtitle_dashboard" }) {
    const { user, guild, logout } = useAuth();
    const { t } = useT();
    const { pathname } = useLocation();
    const [menuOpen, setMenuOpen] = useState(false);
    // ROUND 16.1.1 HOTFIX — lifted single `openId` controls all desktop dropdowns.
    const [openId, setOpenId] = useState(null);
    const subtitleText = subtitle != null ? subtitle : t(subtitleKey);

    // ROUND 16.1.1 HOTFIX (v2) — robust click-away listener using
    // `data-dropdown-region` markers. Closes the open dropdown when the
    // click target is NOT inside a trigger button OR an open panel.
    // Why data-attributes instead of `navRef.contains`: the previous
    // approach failed if the click landed on the empty side area of the
    // sticky <header> (technically inside the header but outside the
    // inner container ref). Marker-based detection works regardless of
    // DOM layout.
    useEffect(() => {
        if (!openId) return;
        const handler = (e) => {
            const target = e.target;
            if (target && typeof target.closest === "function" &&
                target.closest('[data-dropdown-region]')) {
                return; // click landed on a trigger or open panel — keep open
            }
            setOpenId(null);
        };
        // mousedown fires before click, so by the time the click event
        // would re-open the same trigger it's already closed → toggle works.
        document.addEventListener("mousedown", handler);
        document.addEventListener("touchstart", handler);
        return () => {
            document.removeEventListener("mousedown", handler);
            document.removeEventListener("touchstart", handler);
        };
    }, [openId]);

    // Close on route change (defensive — Link onClick already handles it).
    useEffect(() => { setOpenId(null); }, [pathname]);

    // Sections rendered on desktop: all except "account" (rendered separately on the right).
    const sectionsLeft = NAV_SECTIONS.filter((s) => s.id !== "account");

    return (
        <>
            <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-20">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
                    {/* Brand + desktop nav */}
                    <div className="flex items-center gap-2 sm:gap-4 min-w-0 flex-1">
                        <Link
                            to="/dashboard"
                            className="flex items-center gap-2 text-xs whitespace-nowrap shrink-0"
                            data-testid="brand-link"
                        >
                            <span className="text-amber">◆</span>
                            <span className="text-muted-foreground tracking-widest hidden lg:inline">
                                ORBUS // {subtitleText}
                            </span>
                            <span className="text-muted-foreground tracking-widest lg:hidden">
                                ORBUS
                            </span>
                        </Link>
                        {guild && (
                            <>
                                <span className="text-border hidden md:inline">|</span>
                                <nav
                                    className="hidden md:flex items-center gap-1 min-w-0 flex-wrap"
                                    aria-label="Navigazione principale"
                                >
                                    {sectionsLeft.map((sec) => (
                                        <DesktopMenuButton
                                            key={sec.id}
                                            section={sec}
                                            isActive={sectionIsActive(sec, pathname)}
                                            openId={openId}
                                            setOpenId={setOpenId}
                                        />
                                    ))}
                                </nav>
                            </>
                        )}
                    </div>

                    {/* Right side: language + gold + account */}
                    <div className="flex items-center gap-3 text-xs whitespace-nowrap">
                        <LanguageSwitcher />
                        {guild && (
                            <span
                                data-testid="header-gold"
                                className="hidden sm:inline text-amber"
                                title={t("dashboard.stats.gold")}
                            >
                                {guild.gold}{t("common.gold_short")}
                            </span>
                        )}
                        {guild ? (
                            <div className="hidden md:block">
                                <DesktopAccountMenu
                                    user={user}
                                    onLogout={logout}
                                    openId={openId}
                                    setOpenId={setOpenId}
                                />
                            </div>
                        ) : (
                            <button
                                onClick={logout}
                                data-testid="logout-btn"
                                className="text-muted-foreground hover:text-foreground px-2 py-1 rounded-sm border border-border hover:bg-secondary"
                            >
                                {t("nav.logout")}
                            </button>
                        )}
                        {/* On mobile the logout is reachable via the drawer; keep username
                            visible if there's room. */}
                        {guild && (
                            <span
                                data-testid="header-username"
                                className="text-muted-foreground hidden lg:inline md:hidden"
                            >
                                @{user?.username}
                            </span>
                        )}
                    </div>
                </div>
            </header>

            {/* Mobile-only bottom nav + drawer. Hidden on ≥md. */}
            {guild && (
                <>
                    <MobileBottomNav onOpenMenu={() => setMenuOpen(true)} />
                    <MobileMenuDrawer open={menuOpen} onClose={() => setMenuOpen(false)} />
                </>
            )}
        </>
    );
}
