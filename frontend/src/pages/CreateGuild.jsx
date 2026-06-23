import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Label } from "../components/ui/label";
import { Textarea } from "../components/ui/textarea";
import { toast } from "sonner";
import { useAuth } from "../context/AuthContext";

export default function CreateGuild() {
    const { user, createGuild, logout, formatApiError } = useAuth();
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [errorMsg, setErrorMsg] = useState("");

    const submit = async (e) => {
        e.preventDefault();
        setErrorMsg("");
        const trimmed = name.trim();
        if (trimmed.length < 3 || trimmed.length > 40) {
            setErrorMsg("Guild name must be 3–40 characters");
            return;
        }
        if (description.length > 300) {
            setErrorMsg("Description must be at most 300 characters");
            return;
        }
        setSubmitting(true);
        try {
            await createGuild(trimmed, description.trim());
            toast.success("Guild founded.");
            navigate("/dashboard", { replace: true });
        } catch (err) {
            const msg = formatApiError(err);
            setErrorMsg(msg);
            toast.error(msg);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background term-grid-bg">
            <header className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between border-b border-border">
                <div className="text-xs text-muted-foreground">
                    <span className="text-amber">◆</span> ORBUS // SETUP
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <span data-testid="header-username">@{user?.username}</span>
                    <button
                        onClick={logout}
                        data-testid="logout-btn"
                        className="text-muted-foreground hover:text-foreground"
                    >
                        logout
                    </button>
                </div>
            </header>

            <main className="max-w-3xl mx-auto px-6 py-12">
                <div className="text-xs text-amber tracking-widest mb-2">
                    :: STEP 02 / FOUND YOUR GUILD
                </div>
                <h1 className="text-3xl font-semibold mb-2">Found a guild</h1>
                <p className="text-sm text-muted-foreground mb-8 max-w-xl">
                    Every Guild Master commands one guild. Choose its banner carefully —
                    you cannot rename it later (until phase 4, at least).
                </p>

                <form
                    onSubmit={submit}
                    className="space-y-5 border border-border bg-card rounded-sm p-6 max-w-xl"
                    data-testid="create-guild-form"
                >
                    <div className="space-y-2">
                        <Label htmlFor="name" className="text-xs text-muted-foreground tracking-wider">
                            GUILD NAME <span className="text-muted-foreground">(3–40)</span>
                        </Label>
                        <Input
                            id="name"
                            data-testid="guild-name-input"
                            required
                            minLength={3}
                            maxLength={40}
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="bg-background border-border rounded-sm h-11 font-mono"
                            placeholder="The Iron Lantern"
                        />
                    </div>

                    <div className="space-y-2">
                        <Label htmlFor="description" className="text-xs text-muted-foreground tracking-wider">
                            DESCRIPTION <span className="text-muted-foreground">(optional, max 300)</span>
                        </Label>
                        <Textarea
                            id="description"
                            data-testid="guild-description-input"
                            maxLength={300}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            className="bg-background border-border rounded-sm font-mono min-h-[110px]"
                            placeholder="A small but ambitious order, headquartered in a coastal trade town."
                        />
                        <div className="text-right text-xs text-muted-foreground">
                            {description.length}/300
                        </div>
                    </div>

                    {errorMsg && (
                        <div
                            data-testid="create-guild-error"
                            className="text-xs text-destructive border border-destructive/40 bg-destructive/10 px-3 py-2 rounded-sm"
                        >
                            {errorMsg}
                        </div>
                    )}

                    <Button
                        type="submit"
                        data-testid="create-guild-submit-btn"
                        disabled={submitting}
                        className="w-full h-11 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm"
                    >
                        {submitting ? "founding…" : "Found guild →"}
                    </Button>
                </form>
            </main>
        </div>
    );
}
