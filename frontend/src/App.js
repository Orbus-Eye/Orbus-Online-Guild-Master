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
                            path="/expeditions/:id"
                            element={
                                <ProtectedRoute requireGuild>
                                    <ExpeditionReport />
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
                            path="/admin"
                            element={
                                <ProtectedRoute>
                                    <Admin />
                                </ProtectedRoute>
                            }
                        />
                        <Route path="/leaderboard" element={<Leaderboard />} />
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
                                    <RaidReport />
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
