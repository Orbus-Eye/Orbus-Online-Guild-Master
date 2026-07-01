// Header applicativo condiviso.
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";

export default function AppShell({ children }) {
    const { user, logout } = useAuth();
    const nav = useNavigate();

    const onLogout = () => {
        logout();
        nav("/", { replace: true });
    };

    return (
        <div className="min-h-screen bg-background text-foreground term-scanline">
            <header
                data-testid="app-header"
                className="sticky top-0 z-40 border-b border-border/70 bg-background/90 backdrop-blur"
            >
                <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
                    <button
                        type="button"
                        onClick={() => nav("/dashboard")}
                        className="flex items-center gap-2 text-left"
                        data-testid="app-header-brand"
                    >
                        <span className="text-amber font-semibold tracking-tight">Orbus</span>
                        <span className="hidden text-xs uppercase tracking-widest text-muted-foreground sm:inline">
                            Guild Master
                        </span>
                    </button>
                    <div className="flex items-center gap-3">
                        <span
                            data-testid="app-header-username"
                            className="hidden text-xs text-muted-foreground sm:inline"
                        >
                            {user?.email}
                        </span>
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={onLogout}
                            data-testid="app-header-logout-btn"
                            className="border-border/70 text-xs"
                        >
                            Logout
                        </Button>
                    </div>
                </div>
            </header>
            <main className="mx-auto max-w-5xl px-4 py-6 sm:py-8">{children}</main>
        </div>
    );
}
