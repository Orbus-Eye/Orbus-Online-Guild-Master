import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useT } from "../i18n/I18nContext";
import LanguageSwitcher from "./LanguageSwitcher";

const NavLink = ({ to, label, testid }) => {
    const { pathname } = useLocation();
    const active = pathname === to;
    return (
        <Link
            to={to}
            data-testid={testid}
            className={`px-3 py-1.5 text-xs tracking-widest rounded-sm transition-colors ${
                active
                    ? "text-amber bg-secondary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/60"
            }`}
        >
            {label}
        </Link>
    );
};

export default function AppHeader({ subtitle, subtitleKey = "nav.brand_subtitle_dashboard" }) {
    const { user, guild, logout } = useAuth();
    const { t } = useT();
    // Backward-compat: explicit `subtitle` prop (raw string) wins over i18n key.
    const subtitleText = subtitle != null ? subtitle : t(subtitleKey);
    return (
        <header className="border-b border-border bg-background/95 backdrop-blur sticky top-0 z-20">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 sm:gap-4 min-w-0">
                    <Link
                        to="/dashboard"
                        className="flex items-center gap-2 text-xs whitespace-nowrap"
                        data-testid="brand-link"
                    >
                        <span className="text-amber">◆</span>
                        <span className="text-muted-foreground tracking-widest hidden sm:inline">
                            ORBUS // {subtitleText}
                        </span>
                        <span className="text-muted-foreground tracking-widest sm:hidden">
                            ORBUS
                        </span>
                    </Link>
                    {guild && (
                        <>
                            <span className="text-border hidden sm:inline">|</span>
                            <nav className="flex items-center gap-1 overflow-x-auto">
                                <NavLink to="/dashboard" label={t("nav.dashboard")} testid="nav-dashboard" />
                                <NavLink to="/adventurers" label={t("nav.adventurers")} testid="nav-adventurers" />
                                <NavLink to="/recruitment" label={t("nav.recruitment")} testid="nav-recruitment" />
                                <NavLink to="/dungeons" label={t("nav.dungeons")} testid="nav-dungeons" />
                                <NavLink to="/expeditions" label={t("nav.expeditions")} testid="nav-expeditions" />
                                <NavLink to="/inventory" label={t("nav.inventory")} testid="nav-inventory" />
                                <NavLink to="/crafting" label={t("nav.crafting")} testid="nav-crafting" />
                                <NavLink to="/market" label={t("nav.market")} testid="nav-market" />
                                <NavLink to="/forge" label={t("nav.forge")} testid="nav-forge" />
                                <NavLink to="/consortiums" label={t("nav.consortiums")} testid="nav-consortiums" />
                                <NavLink to="/leaderboard" label={t("nav.leaderboard")} testid="nav-leaderboard" />
                                {user?.is_admin && (
                                    <NavLink to="/admin" label={t("nav.admin")} testid="nav-admin" />
                                )}
                            </nav>
                        </>
                    )}
                </div>
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
                    <span
                        data-testid="header-username"
                        className="text-muted-foreground hidden sm:inline"
                    >
                        @{user?.username}
                    </span>
                    <button
                        onClick={logout}
                        data-testid="logout-btn"
                        className="text-muted-foreground hover:text-foreground px-2 py-1 rounded-sm border border-border hover:bg-secondary"
                    >
                        {t("nav.logout")}
                    </button>
                </div>
            </div>
        </header>
    );
}
