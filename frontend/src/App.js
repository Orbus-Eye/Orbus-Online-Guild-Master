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
import Seasons from "@/pages/Seasons";  // ROUND 12
import Arena from "@/pages/Arena";  // ROUND 12
import ReportErrorBoundary from "@/components/ReportErrorBoundary";

function App() {
    return (
        <div className="App min-h-screen bg-background text-foreground">
            <BrowserRouter>
                <I18nProvider>
                    <AuthProvider>
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
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
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
