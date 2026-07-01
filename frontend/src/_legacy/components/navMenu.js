// ROUND 16.0 — Phase 5 — Shared navigation menu structure.
// Single source of truth used by both desktop dropdowns and the mobile drawer.
// Routes referenced here must already exist in /app/frontend/src/App.js — broken
// entries are intentionally omitted (no dead links).
//
// Macro-sections (8): Gilda, Avventurieri, Missioni, Economia,
// Competizione, Social, Guida, Account.

export const NAV_SECTIONS = [
    {
        id: "gilda",
        label: "Gilda",
        items: [
            { to: "/dashboard", label: "Home", testid: "menu-dashboard" },
            { to: "/achievements", label: "Imprese", testid: "menu-achievements" },
            { to: "/site-contracts", label: "Incarichi di Sede", testid: "menu-site-contracts", badge: "NEW" },
            { to: "/territory", label: "Territorio", testid: "menu-territory" },
            { to: "/chronicle", label: "Cronaca", testid: "menu-chronicle" },
        ],
    },
    {
        id: "avventurieri",
        label: "Avventurieri",
        items: [
            { to: "/adventurers", label: "Roster", testid: "menu-adventurers" },
            { to: "/recruitment", label: "Reclutamento", testid: "menu-recruitment" },
            { to: "/class-halls", label: "Sale di Classe", testid: "menu-class-halls" },
            { to: "/training", label: "Addestramento e Specializzazioni", testid: "menu-training" },
            { to: "/roster/manage", label: "Gestione Roster", testid: "menu-roster-manage" },
            { to: "/guide#traits-catalog", label: "Tratti", testid: "menu-traits-link", external: false },
        ],
    },
    {
        id: "missioni",
        label: "Missioni",
        items: [
            { to: "/dungeons", label: "Dungeon", testid: "menu-dungeons" },
            { to: "/expeditions", label: "Spedizioni", testid: "menu-expeditions" },
            { to: "/raids", label: "Raid", testid: "menu-raids" },
            { to: "/world-boss", label: "World Boss", testid: "menu-world-boss", badge: "NEW" },
            { to: "/squads", label: "Squadre", testid: "menu-squads" },
            { to: "/guide#minacce-contromisure", label: "Minacce e Contromisure", testid: "menu-threats" },
        ],
    },
    {
        id: "mondo",
        label: "Mondo",
        items: [
            { to: "/world", label: "Panoramica Mondo", testid: "menu-world", badge: "NEW" },
            { to: "/world-events", label: "Eventi", testid: "menu-world-events", badge: "NEW" },
            { to: "/world/resources", label: "Risorse", testid: "menu-world-resources", badge: "NEW" },
            { to: "/world/leaderboards", label: "Classifiche", testid: "menu-world-leaderboards", badge: "NEW" },
            { to: "/world/neighbors", label: "Gilde vicine", testid: "menu-world-neighbors" },
        ],
    },
    {
        id: "economia",
        label: "Economia",
        items: [
            { to: "/inventory", label: "Deposito", testid: "menu-inventory" },
            { to: "/market", label: "Mercato", testid: "menu-market" },
            { to: "/auction", label: "Asta", testid: "menu-auction" },
            { to: "/crafting", label: "Crafting", testid: "menu-crafting" },
            { to: "/forge", label: "Forgia", testid: "menu-forge" },
            { to: "/legendary-forge", label: "Forgia Leggendaria",
              testid: "menu-legendary-forge", badge: "NEW" },
            { to: "/arfus-forge", label: "Forgia di Arfus",
              testid: "menu-arfus-forge", badge: "NEW" },
            { to: "/guild-specialization", label: "Specializzazione",
              testid: "menu-guild-specialization", badge: "NEW" },
            { to: "/trade-pacts", label: "Patti Commerciali",
              testid: "menu-trade-pacts", badge: "NEW" },
            { to: "/contracts", label: "Contratti", testid: "menu-contracts" },
        ],
    },
    {
        id: "competizione",
        label: "Competizione",
        items: [
            { to: "/leaderboard", label: "Classifiche", testid: "menu-leaderboard" },
            { to: "/seasons", label: "Stagioni", testid: "menu-seasons" },
            { to: "/arena", label: "Arena", testid: "menu-arena" },
        ],
    },
    {
        id: "social",
        label: "Social",
        items: [
            { to: "/consortiums", label: "Consorzi", testid: "menu-consortiums" },
            { to: "/chat", label: "Chat", testid: "menu-chat" },
            { to: null, label: "Alleanze (in arrivo)", testid: "menu-alliances-disabled", disabled: true },
        ],
    },
    {
        id: "guida",
        label: "Guida",
        items: [
            { to: "/guide", label: "Guida generale", testid: "menu-guide" },
            { to: "/guide#classi-e-stats", label: "Classi e statistiche", testid: "menu-guide-classes" },
            { to: "/guide#classe-vs-spec", label: "Classe base vs Specializzazione", testid: "menu-guide-base-vs-spec" },
            { to: "/guide#sale-di-classe", label: "Sale di Classe", testid: "menu-guide-class-halls" },
            { to: "/guide#sblocco-sala-spec", label: "Sbloccare Sala e Spec.", testid: "menu-guide-unlock" },
            { to: "/guide#razze-sesso", label: "Razza e Sesso", testid: "menu-guide-races" },
            { to: "/guide#stat-colors", label: "Colori statistiche", testid: "menu-guide-stat-colors" },
            { to: "/guide#auto-equip", label: "Auto-Equipaggia", testid: "menu-guide-auto-equip" },
            { to: "/guide#traits-catalog", label: "Catalogo tratti", testid: "menu-guide-traits" },
            { to: "/guide#equip-compat", label: "Equipaggiamento per classe", testid: "menu-guide-equip" },
            { to: "/guide#dungeon", label: "Dungeon e Spedizioni", testid: "menu-guide-dungeon" },
            { to: "/guide#minacce-contromisure", label: "Minacce e Contromisure", testid: "menu-guide-threats" },
        ],
    },
    {
        id: "account",
        label: "Account",
        items: [
            // logout is rendered as a button, not a route entry.
        ],
    },
];

// Mobile bottom-nav primary tabs (5 fixed slots).
// Each slot defines a "match" predicate to highlight the active tab.
export const MOBILE_BOTTOM_TABS = [
    {
        key: "home",
        to: "/dashboard",
        label: "Home",
        icon: "Home",
        match: (p) => p === "/dashboard" || p === "/",
        testid: "mobile-bn-home",
    },
    {
        key: "advs",
        to: "/adventurers",
        label: "Avv.",
        icon: "Users",
        match: (p) => p.startsWith("/adventurers") || p.startsWith("/recruitment") ||
                       p.startsWith("/training") || p.startsWith("/roster"),
        testid: "mobile-bn-advs",
    },
    {
        key: "missions",
        to: "/dungeons",
        label: "Missioni",
        icon: "Swords",
        match: (p) => p.startsWith("/dungeons") || p.startsWith("/expeditions") ||
                       p.startsWith("/raids") || p.startsWith("/squads"),
        testid: "mobile-bn-missions",
    },
    {
        key: "economy",
        to: "/inventory",
        label: "Econ.",
        icon: "Coins",
        match: (p) => p.startsWith("/inventory") || p.startsWith("/market") ||
                       p.startsWith("/auction") || p.startsWith("/crafting") ||
                       p.startsWith("/forge") || p.startsWith("/contracts"),
        testid: "mobile-bn-economy",
    },
    {
        key: "menu",
        to: null,
        label: "Menu",
        icon: "Menu",
        match: () => false,
        testid: "mobile-bn-menu",
    },
];
