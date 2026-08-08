// FASE 4 (2026-08-08) — GameImage: catena di fallback.
import { render, screen, fireEvent } from "@testing-library/react";
import GameImage from "../components/GameImage";
import { avatarSources, dungeonImageSources } from "../utils/gameAssets";

test("passa al fallback quando la sorgente fallisce", () => {
    render(
        <GameImage
            sources={["/assets/x/manca.svg", "/assets/themes/default.svg"]}
            alt="img di prova"
        />
    );
    const img = screen.getByAltText("img di prova");
    expect(img).toHaveAttribute("src", "/assets/x/manca.svg");
    fireEvent.error(img);
    expect(img).toHaveAttribute("src", "/assets/themes/default.svg");
});

test("catena esaurita: non renderizza nulla (mai icone rotte)", () => {
    render(<GameImage sources={["/solo-una.svg"]} alt="img di prova" />);
    const img = screen.getByAltText("img di prova");
    fireEvent.error(img);
    expect(screen.queryByAltText("img di prova")).not.toBeInTheDocument();
});

test("avatarSources: razza+genere con fallback default", () => {
    expect(avatarSources({ race_slug: "tiefling", gender: "female" })).toEqual([
        "/assets/avatars/tiefling_female.svg",
        "/assets/avatars/default.svg",
    ]);
    // Senza razza → solo default.
    expect(avatarSources({})).toEqual(["/assets/avatars/default.svg"]);
    // Upload custom (Fase 6) in testa alla catena.
    expect(
        avatarSources({ custom_avatar_url: "/u/x.png", race_slug: "orc", gender: "male" })[0]
    ).toBe("/u/x.png");
});

test("dungeonImageSources: specifico → tema → default", () => {
    expect(dungeonImageSources("lich-sanctum")).toEqual([
        "/assets/dungeons/lich-sanctum.svg",
        "/assets/themes/crypt.svg",
        "/assets/themes/default.svg",
    ]);
    expect(dungeonImageSources("slug-ignoto")).toEqual([
        "/assets/dungeons/slug-ignoto.svg",
        "/assets/themes/default.svg",
    ]);
});
