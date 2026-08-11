// FASE 9P — RoomProgressTimer: barra temporale della stanza corrente.
// Clock finto (jest.useFakeTimers): nessuno sleep reale.
import { render, screen, act } from "@testing-library/react";
import RoomProgressTimer, {
    formatRemaining,
    progressPercent,
    shouldShowRoomTimer,
} from "../components/RoomProgressTimer";

describe("formatRemaining", () => {
    it("formatta i secondi", () => {
        expect(formatRemaining(43)).toBe("43s");
        expect(formatRemaining(0)).toBe("0s");
    });
    it("formatta i minuti", () => {
        expect(formatRemaining(222)).toBe("3m 42s");
        expect(formatRemaining(60)).toBe("1m 0s");
    });
    it("formatta le ore", () => {
        expect(formatRemaining(4320)).toBe("1h 12m");
        expect(formatRemaining(3600)).toBe("1h 0m");
    });
    it("mai negativo", () => {
        expect(formatRemaining(-15)).toBe("0s");
    });
});

describe("progressPercent (elapsed / total)", () => {
    it("inizio stanza → 0%", () => {
        expect(progressPercent(600, 600)).toBe(0);
    });
    it("metà tempo → 50%", () => {
        expect(progressPercent(300, 600)).toBe(50);
    });
    it("fine stanza → 100%", () => {
        expect(progressPercent(0, 600)).toBe(100);
    });
    it("mai oltre 100 né sotto 0", () => {
        expect(progressPercent(-30, 600)).toBe(100);   // remaining clampato
        expect(progressPercent(900, 600)).toBe(0);     // remaining > total
        expect(progressPercent(0, 0)).toBe(100);       // durata assente
    });
});

describe("shouldShowRoomTimer — timer SOLO sulla stanza corrente", () => {
    const base = {
        status: "in_progress",
        mode: "rooms",
        room_state: "in_room",
        current_room_idx: 2,
        room_duration_seconds: 600,
    };
    it("stanza corrente attiva → visibile", () => {
        expect(shouldShowRoomTimer(base, 2)).toBe(true);
    });
    it("stanza futura o completata → nessun timer", () => {
        expect(shouldShowRoomTimer(base, 3)).toBe(false);
        expect(shouldShowRoomTimer(base, 1)).toBe(false);
    });
    it("attesa scelta / bivio → nessun timer", () => {
        expect(shouldShowRoomTimer(
            { ...base, room_state: "awaiting_choice" }, 2,
        )).toBe(false);
    });
    it("run conclusa o legacy senza durata → nessun timer", () => {
        expect(shouldShowRoomTimer({ ...base, status: "completed" }, 2)).toBe(false);
        expect(shouldShowRoomTimer({ ...base, room_duration_seconds: 0 }, 2)).toBe(false);
        expect(shouldShowRoomTimer(null, 2)).toBe(false);
    });
});

describe("RoomProgressTimer (fake timers)", () => {
    beforeEach(() => { jest.useFakeTimers(); });
    afterEach(() => { jest.useRealTimers(); });

    it("mostra il tempo residuo dentro la barra e scala col tick locale", () => {
        render(
            <RoomProgressTimer durationSeconds={600} secondsRemaining={222} />,
        );
        expect(screen.getByTestId("room-progress-label"))
            .toHaveTextContent("3m 42s rimanenti");
        act(() => { jest.advanceTimersByTime(2000); });
        expect(screen.getByTestId("room-progress-label"))
            .toHaveTextContent("3m 40s rimanenti");
    });

    it("la barra cresce da ~0% verso 100%", () => {
        render(
            <RoomProgressTimer durationSeconds={100} secondsRemaining={100} />,
        );
        const bar = screen.getByTestId("room-progress-timer");
        expect(bar).toHaveAttribute("aria-valuenow", "0");
        act(() => { jest.advanceTimersByTime(50_000); });
        expect(bar).toHaveAttribute("aria-valuenow", "50");
        act(() => { jest.advanceTimersByTime(60_000); });   // oltre la fine
        expect(bar).toHaveAttribute("aria-valuenow", "100"); // mai > 100
    });

    it("a zero mostra 'Completamento in corso…' e chiama onExpired UNA volta", () => {
        const onExpired = jest.fn();
        render(
            <RoomProgressTimer
                durationSeconds={600}
                secondsRemaining={2}
                onExpired={onExpired}
            />,
        );
        act(() => { jest.advanceTimersByTime(3000); });
        expect(screen.getByTestId("room-progress-label"))
            .toHaveTextContent("Completamento in corso…");
        act(() => { jest.advanceTimersByTime(10_000); });
        expect(onExpired).toHaveBeenCalledTimes(1); // niente loop aggressivi
    });

    it("il refetch del server risincronizza il countdown", () => {
        const { rerender } = render(
            <RoomProgressTimer durationSeconds={600} secondsRemaining={10} />,
        );
        act(() => { jest.advanceTimersByTime(4000); });
        expect(screen.getByTestId("room-progress-label"))
            .toHaveTextContent("6s rimanenti");
        // Il poll della pagina riporta il valore autoritativo del server.
        rerender(
            <RoomProgressTimer durationSeconds={600} secondsRemaining={300} />,
        );
        expect(screen.getByTestId("room-progress-label"))
            .toHaveTextContent("5m 0s rimanenti");
    });
});
