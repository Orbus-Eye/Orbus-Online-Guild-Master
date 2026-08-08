import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { I18nProvider } from "@/i18n/I18nContext";
import { ProtectedRoute, GuildGate, GuestOnly } from "@/components/RouteGuards";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import CreateGuild from "@/pages/CreateGuild";
import Dashboard from "@/pages/Dashboard";
import Recruitment from "@/pages/Recruitment";
import Adventurers from "@/pages/Adventurers";
import ClassHalls from "@/pages/ClassHalls";
import Dungeons from "@/pages/Dungeons";
import ExpeditionNew from "@/pages/ExpeditionNew";
import Expeditions from "@/pages/Expeditions";
import ExpeditionReport from "@/pages/ExpeditionReport";
import Inventory from "@/pages/Inventory";
import Admin from "@/pages/Admin";
import AdventurerEquipment from "@/pages/AdventurerEquipment";
import PasswordResetRequest from "@/pages/PasswordResetRequest";
import PasswordResetConfirm from "@/pages/PasswordResetConfirm";
import Leaderboard from "@/pages/Leaderboard";
import Crafting from "@/pages/Crafting";
import Market from "@/pages/Market";
import Consortiums from "@/pages/Consortiums";
import Forge from "@/pages/Forge";
import Raids from "@/pages/Raids";
import RaidBuilder from "@/pages/RaidBuilder";
import RaidReport from "@/pages/RaidReport";
import Guide from "@/pages/Guide";
import Achievements from "@/pages/Achievements";
import TraitsPublic from "@/pages/TraitsPublic";  // ROUND 11.2 TASK 8 — SEO
import StatsPublic from "@/pages/StatsPublic";    // ROUND 11.2 TASK 8 — SEO
import MaterialsPublic from "@/pages/MaterialsPublic";  // ROUND 11.2 EXT S3 — SEO
import Chat from "@/pages/Chat";
import Auction from "@/pages/Auction";
import Squads from "@/pages/Squads";
import SquadBuilder from "@/pages/SquadBuilder";
import Territory from "@/pages/Territory";
import RosterManage from "@/pages/RosterManage";
import Chronicle from "@/pages/Chronicle";
import Training from "@/pages/Training";
import Contracts from "@/pages/Contracts";
import AdminOps from "@/pages/AdminOps";  // ROUND 11.2 TASK 5b
import AdminGameHealth from "@/pages/AdminGameHealth";  // ROUND 14.v3
import AdminAudit from "@/pages/AdminAudit";  // ROUND 16.A Phase 3
import WorldBoss from "@/pages/WorldBoss";  // ROUND 16.3 Phase 1
import WorldBossEvent from "@/pages/WorldBossEvent";
import WorldBossReport from "@/pages/WorldBossReport";
import World from "@/pages/World";  // ROUND 16.3 Phase 2
import WorldContinent from "@/pages/WorldContinent";
import WorldNeighbors from "@/pages/WorldNeighbors";
import WorldEvents from "@/pages/WorldEvents";  // ROUND 16.3 Phase 3
import AdminWorldEvents from "@/pages/AdminWorldEvents";  // ROUND 16.5.1 B.1
import AdminTesterTools from "@/pages/AdminTesterTools";  // ROUND 16.5.1 B.2
import SiteContracts from "@/pages/SiteContracts";
import Resources from "@/pages/Resources";  // ROUND 16.3 Phase 4
import ResourceGather from "@/pages/ResourceGather";
import ResourceMissions from "@/pages/ResourceMissions";
import ContinentLeaderboards from "@/pages/ContinentLeaderboards";
import LegendaryForge from "@/pages/LegendaryForge";  // ROUND 16.3 Phase 5A
import LegendaryForgeRecipe from "@/pages/LegendaryForgeRecipe";
import LegendaryForgeOrders from "@/pages/LegendaryForgeOrders";
import ArfusForge from "@/pages/ArfusForge";  // ROUND 16.3 Phase 5B
import ArfusTechDetail from "@/pages/ArfusTechDetail";
import ArfusResearch from "@/pages/ArfusResearch";
import ArfusActive from "@/pages/ArfusActive";
import TradePacts from "@/pages/TradePacts";  // ROUND 16.3 Phase 6
import TradePactRequest from "@/pages/TradePactRequest";
import GuildSpecialization from "@/pages/GuildSpecialization";
import GuildSpecializationCatalog from "@/pages/GuildSpecializationCatalog";
import Seasons from "@/pages/Seasons";  // ROUND 12
import Arena from "@/pages/Arena";  // ROUND 12
// ROUND 16.3 Phase 7A — PvP Continentale
import PvpOpponents from "@/pages/PvpOpponents";
import PvpChallenge from "@/pages/PvpChallenge";
import PvpBattles from "@/pages/PvpBattles";
import PvpBattleReport from "@/pages/PvpBattleReport";
// ROUND 16.3 Phase 7B — PvP Season pages
import PvpSeasonOverview from "@/pages/PvpSeasonOverview";
import PvpSeasonLeaderboardDetail from "@/pages/PvpSeasonLeaderboardDetail";
import PvpSeasonCosmetics from "@/pages/PvpSeasonCosmetics";
// ROUND 16.3 Phase 8 V1 — Stables & Mounts
import Stables from "@/pages/Stables";
import ReportErrorBoundary from "@/components/ReportErrorBoundary";
import AppErrorBoundary from "@/components/AppErrorBoundary";

function App() {
    return (
        <div className="App min-h-screen bg-background text-foreground">
            <BrowserRouter>
                <I18nProvider>
                    <AuthProvider>
                    <AppErrorBoundary>
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route
                            path="/login"
                            element={
                                <GuestOnly>
                                    <Login />
                                </GuestOnly>
                            }
                        />
                        <Route
                            path="/register"
                            element={
                                <GuestOnly>
                                    <Register />
                                </GuestOnly>
                            }
                        />
                        <Route
                            path="/password-reset/request"
                            element={
                                <GuestOnly>
                                    <PasswordResetRequest />
                                </GuestOnly>
                            }
                        />
                        <Route
                            path="/password-reset/confirm"
                            element={
                                <GuestOnly>
                                    <PasswordResetConfirm />
                                </GuestOnly>
                            }
                        />
                        <Route
                            path="/create-guild"
                            element={
                                <GuildGate>
                                    <CreateGuild />
                                </GuildGate>
                            }
                        />
                        <Route
                            path="/dashboard"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Dashboard />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/recruitment"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Recruitment />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/adventurers"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Adventurers />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/adventurers/:id/equipment"
                            element={
                                <ProtectedRoute requireGuild>
                                    <AdventurerEquipment />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/class-halls"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ClassHalls />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/dungeons"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Dungeons />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/dungeons/:slug/start"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ExpeditionNew />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/expeditions"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Expeditions />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/achievements"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Achievements />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/crafting"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Crafting />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/market"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Market />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/auction"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Auction />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/expeditions/:id"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ReportErrorBoundary
                                        fallbackTitle="Report unavailable"
                                        fallbackBody="Some details of this expedition could not be displayed. Your run is safe; please try again or contact support."
                                    >
                                        <ExpeditionReport />
                                    </ReportErrorBoundary>
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/inventory"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Inventory />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/squads"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Squads />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/squads/new"
                            element={
                                <ProtectedRoute requireGuild>
                                    <SquadBuilder />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/squads/:id/edit"
                            element={
                                <ProtectedRoute requireGuild>
                                    <SquadBuilder />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/territory"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Territory />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/roster/manage"
                            element={
                                <ProtectedRoute requireGuild>
                                    <RosterManage />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/admin"
                            element={
                                <ProtectedRoute>
                                    <Admin />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/admin/ops"
                            element={
                                <ProtectedRoute>
                                    <AdminOps />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/admin/game-health"
                            element={
                                <ProtectedRoute>
                                    <AdminGameHealth />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/admin/audit"
                            element={
                                <ProtectedRoute>
                                    <AdminAudit />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.5.1 B.1 — Admin Continent Events CRUD */}
                        <Route
                            path="/admin/world-events"
                            element={
                                <ProtectedRoute>
                                    <AdminWorldEvents />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.5.1 B.2 — Admin Tester Tools */}
                        <Route
                            path="/admin/tester-tools"
                            element={
                                <ProtectedRoute>
                                    <AdminTesterTools />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 1 — World Boss */}
                        <Route
                            path="/world-boss"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldBoss />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world-boss/:eventId"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldBossEvent />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world-boss/:eventId/report"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldBossReport />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 2 — Mondo & 8 Mastocontinenti */}
                        <Route
                            path="/world"
                            element={
                                <ProtectedRoute requireGuild>
                                    <World />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world/continents/:slug"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldContinent />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world/neighbors"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldNeighbors />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 3 — Continent events + Site contracts */}
                        <Route
                            path="/world-events"
                            element={
                                <ProtectedRoute requireGuild>
                                    <WorldEvents />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/site-contracts"
                            element={
                                <ProtectedRoute requireGuild>
                                    <SiteContracts />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 4 — Continent resources + leaderboards */}
                        <Route
                            path="/world/resources"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Resources />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world/resource-gather"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ResourceGather />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world/resource-missions"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ResourceMissions />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/world/leaderboards"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ContinentLeaderboards />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/leaderboard" element={<Leaderboard />} />
                        <Route path="/guide" element={<Guide />} />
                        {/* ROUND 12 — Seasons + Arena */}
                        <Route
                            path="/seasons"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Seasons />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/arena"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Arena />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 11.2 TASK 8 — Public SEO routes (no auth, no redirect) */}
                        <Route path="/traits" element={<TraitsPublic />} />
                        <Route path="/stats" element={<StatsPublic />} />
                        {/* ROUND 11.2 EXT S3 — Public SEO materials page */}
                        <Route path="/materials" element={<MaterialsPublic />} />
                        <Route
                            path="/chronicle"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Chronicle />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/training"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Training />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/contracts"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Contracts />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/chat"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Chat />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/consortiums"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Consortiums />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/forge"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Forge />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/raids"
                            element={
                                <ProtectedRoute requireGuild>
                                    <Raids />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/raids/build/:slug"
                            element={
                                <ProtectedRoute requireGuild>
                                    <RaidBuilder />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/raids/:raid_id/report"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ReportErrorBoundary
                                        fallbackTitle="Raid report unavailable"
                                        fallbackBody="Some details of this raid report could not be displayed. Your raid run is safe; please try again or contact support."
                                    >
                                        <RaidReport />
                                    </ReportErrorBoundary>
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 5A — Forgia Leggendaria */}
                        <Route
                            path="/legendary-forge"
                            element={
                                <ProtectedRoute requireGuild>
                                    <LegendaryForge />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/legendary-forge/recipe/:slug"
                            element={
                                <ProtectedRoute requireGuild>
                                    <LegendaryForgeRecipe />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/legendary-forge/orders"
                            element={
                                <ProtectedRoute requireGuild>
                                    <LegendaryForgeOrders />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 5B — Forgia di Arfus */}
                        <Route
                            path="/arfus-forge"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ArfusForge />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/arfus-forge/tech/:slug"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ArfusTechDetail />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/arfus-forge/research"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ArfusResearch />
                                </ProtectedRoute>
                            }
                        />
                        <Route
                            path="/arfus-forge/active"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ArfusActive />
                                </ProtectedRoute>
                            }
                        />
                        {/* ROUND 16.3 Phase 6 — Trade Pacts + Guild Specialization */}
                        <Route path="/trade-pacts" element={
                            <ProtectedRoute requireGuild><TradePacts /></ProtectedRoute>} />
                        <Route path="/trade-pacts/request" element={
                            <ProtectedRoute requireGuild><TradePactRequest /></ProtectedRoute>} />
                        <Route path="/guild-specialization" element={
                            <ProtectedRoute requireGuild><GuildSpecialization /></ProtectedRoute>} />
                        <Route path="/guild-specialization/catalog" element={
                            <ProtectedRoute requireGuild><GuildSpecializationCatalog /></ProtectedRoute>} />
                        {/* ROUND 16.3 Phase 7A — PvP Continentale */}
                        <Route path="/pvp" element={
                            <ProtectedRoute requireGuild><PvpOpponents /></ProtectedRoute>} />
                        <Route path="/pvp/challenge/:defenderGuildId" element={
                            <ProtectedRoute requireGuild><PvpChallenge /></ProtectedRoute>} />
                        <Route path="/pvp/battles" element={
                            <ProtectedRoute requireGuild><PvpBattles /></ProtectedRoute>} />
                        <Route path="/pvp/battles/:battleId" element={
                            <ProtectedRoute requireGuild><PvpBattleReport /></ProtectedRoute>} />
                        {/* ROUND 16.3 Phase 7B — PvP Season */}
                        <Route path="/pvp-season" element={
                            <ProtectedRoute requireGuild><PvpSeasonOverview /></ProtectedRoute>} />
                        <Route path="/pvp-season/leaderboard/:continentSlug" element={
                            <ProtectedRoute requireGuild><PvpSeasonLeaderboardDetail /></ProtectedRoute>} />
                        <Route path="/pvp-season/cosmetics" element={
                            <ProtectedRoute requireGuild><PvpSeasonCosmetics /></ProtectedRoute>} />
                        {/* ROUND 16.3 Phase 8 V1 — Stables & Mounts */}
                        <Route path="/stables" element={
                            <ProtectedRoute requireGuild><Stables /></ProtectedRoute>} />
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                    </AppErrorBoundary>
                    </AuthProvider>
                </I18nProvider>
            </BrowserRouter>
            <Toaster
                theme="dark"
                position="top-right"
                toastOptions={{
                    style: {
                        background: "#131316",
                        border: "1px solid #2a2a2e",
                        color: "#e5e5e5",
                        fontFamily: "JetBrains Mono, monospace",
                        fontSize: "13px",
                    },
                }}
            />
        </div>
    );
}

export default App;
