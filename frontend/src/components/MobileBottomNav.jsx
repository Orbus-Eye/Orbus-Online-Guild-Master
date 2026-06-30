// ROUND 16.0 — Phase 5 — Mobile bottom navigation bar.
// Visible on <md only. 5 fixed slots. 4 quick-jump tabs + 1 "Menu" toggle
// that opens the full drawer. Tap targets ≥ 44px tall. Italian labels.

import { Link, useLocation } from "react-router-dom";
import { Home, Users, Swords, Coins, Menu as MenuIcon } from "lucide-react";
import { MOBILE_BOTTOM_TABS } from "./navMenu";

const ICONS = {
    Home,
    Users,
    Swords,
    Coins,
    Menu: MenuIcon,
};

export default function MobileBottomNav({ onOpenMenu }) {
    const { pathname } = useLocation();
    return (
        <nav
            data-testid="mobile-bottom-nav"
            className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-background/95 backdrop-blur border-t border-border"
            style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
            role="navigation"
            aria-label="Navigazione principale"
        >
            <ul className="flex items-stretch justify-around h-16">
                {MOBILE_BOTTOM_TABS.map((tab) => {
                    const Icon = ICONS[tab.icon] || MenuIcon;
                    const active = tab.match(pathname);
                    const baseCls = `flex flex-col items-center justify-center flex-1 min-w-[44px] py-1 text-[10px] tracking-wider transition-colors ${
                        active
                            ? "text-amber bg-secondary/40"
                            : "text-muted-foreground hover:text-foreground"
                    }`;
                    if (tab.key === "menu") {
                        return (
                            <li key={tab.key} className="flex-1">
                                <button
                                    type="button"
                                    data-testid={tab.testid}
                                    aria-label="Apri menu"
                                    onClick={onOpenMenu}
                                    className={`${baseCls} w-full`}
                                    style={{ minHeight: 44 }}
                                >
                                    <Icon size={20} aria-hidden="true" />
                                    <span className="mt-0.5">{tab.label}</span>
                                </button>
                            </li>
                        );
                    }
                    return (
                        <li key={tab.key} className="flex-1">
                            <Link
                                to={tab.to}
                                data-testid={tab.testid}
                                aria-label={tab.label}
                                aria-current={active ? "page" : undefined}
                                className={baseCls}
                                style={{ minHeight: 44 }}
                            >
                                <Icon size={20} aria-hidden="true" />
                                <span className="mt-0.5">{tab.label}</span>
                            </Link>
                        </li>
                    );
                })}
            </ul>
        </nav>
    );
}
