import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const Loading = () => (
    <div
        data-testid="route-loading"
        className="min-h-screen flex items-center justify-center bg-background text-muted-foreground text-sm"
    >
        <span>loading</span>
        <span className="caret-blink" />
    </div>
);

export const ProtectedRoute = ({ children, requireGuild = false }) => {
    const { user, guild } = useAuth();
    if (user === undefined) return <Loading />;
    if (!user) return <Navigate to="/login" replace />;
    if (requireGuild) {
        if (guild === undefined) return <Loading />;
        if (!guild) return <Navigate to="/create-guild" replace />;
    }
    return children;
};

export const GuildGate = ({ children }) => {
    // page shown only to users who DON'T have a guild yet
    const { user, guild } = useAuth();
    if (user === undefined) return <Loading />;
    if (!user) return <Navigate to="/login" replace />;
    if (guild === undefined) return <Loading />;
    if (guild) return <Navigate to="/dashboard" replace />;
    return children;
};

export const GuestOnly = ({ children }) => {
    const { user } = useAuth();
    if (user === undefined) return <Loading />;
    if (user) return <Navigate to="/dashboard" replace />;
    return children;
};
