// PasswordInput — reusable password field with show/hide toggle.
// Accessible: focusable button, Enter/Space activation, aria-label
// localized (i18n EN/IT). Preserves autocomplete + name attributes so
// password managers keep working. Default visibility is hidden.
import { useState, useId } from "react";
import { Eye, EyeOff } from "lucide-react";
import { Input } from "./ui/input";
import { useT } from "../i18n/I18nContext";

export default function PasswordInput({
    id,
    value,
    onChange,
    autoComplete = "current-password",
    minLength,
    required = true,
    name = "password",
    placeholder = "••••••••",
    testid,
    className = "",
    ...rest
}) {
    const { t } = useT();
    const [shown, setShown] = useState(false);
    const generatedId = useId();
    const inputId = id || generatedId;
    const toggleLabel = shown
        ? t("password_input.hide_label")
        : t("password_input.show_label");

    return (
        <div className="relative">
            <Input
                id={inputId}
                type={shown ? "text" : "password"}
                name={name}
                value={value}
                onChange={onChange}
                autoComplete={autoComplete}
                minLength={minLength}
                required={required}
                placeholder={placeholder}
                data-testid={testid}
                className={
                    "bg-background border-border rounded-sm h-11 font-mono pr-11 " +
                    className
                }
                {...rest}
            />
            <button
                type="button"
                onClick={() => setShown((s) => !s)}
                aria-label={toggleLabel}
                aria-pressed={shown}
                title={toggleLabel}
                tabIndex={0}
                data-testid={testid ? `${testid}-toggle` : "password-toggle"}
                className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-sm text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-amber"
            >
                {shown ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
        </div>
    );
}
