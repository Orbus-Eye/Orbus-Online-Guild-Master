import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute, GuildGate, GuestOnly } from "@/components/RouteGuards";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import CreateGuild from "@/pages/CreateGuild";
import Dashboard from "@/pages/Dashboard";
import Recruitment from "@/pages/Recruitment";
import Adventurers from "@/pages/Adventurers";

function App() {
    return (
        <div className="App min-h-screen bg-background text-foreground">
            <BrowserRouter>
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
                        <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                </AuthProvider>
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
