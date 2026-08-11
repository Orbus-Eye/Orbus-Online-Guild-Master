# FASE 4 + 8F + 9G — Manifest asset (procedurali → art definitiva)
Data: 2026-08-11 · Generatori: `scripts/fase4_genera_assets.py` (v2),
`scripts/fase9_genera_emblemi_classi.py` (FASE 9G)

## FASE 9G — Identità visiva delle 27 classi — `assets/classes/`
- `{class_slug}.svg` — 27 EMBLEMI unici (240×240): ogni classe ha un
  GLIFO disegnato ad hoc (identity map sotto), sfondo radiale con la
  palette della classe, anello colorato per RUOLO (rosso DPS, azzurro
  TANK, verde HEALER) e glow. NON sono 27 icone fotocopiate.
- `{class_slug}_banner.svg` — 27 banner (800×200) con emblema, nome,
  identità e badge ruolo (per header Sala di Classe / card).
- Identity map (registry `backend/app/classes/registry.py`,
  campo `emblem_symbol` — verificabile nel codice):
  guerriero=spade incrociate · ladro=pugnale nell'ombra ·
  mago=sigillo a 9 punte · monaco=pugno e corda · negromante=teschio
  nel cerchio · cacciatore_del_vuoto=occhio-lanterna nel vuoto ·
  artificiere=ingranaggio · cartografo=rosa dei venti · runista=runa ·
  burattinaio=maschera coi fili · giocatore_d_azzardo=dadi ·
  pittore=pennello · cacciatore_del_sangue=zanna e sangue ·
  paladino=scudo con fiamma · cacciatore_di_mostri=bestia e lancia ·
  fabbro_arcano=incudine runica · parassita=radice a spirale ·
  cavaliere_della_morte=elmo e vessillo · cavaliere_di_draghi=drago
  sulla lancia · alchimista=alambicco · bardo=lira · druido=salice ·
  sciamano=tamburo · cronista=penna · mercante=bilancia ·
  astrologo=costellazione · sognatore=mezzaluna sull'occhio.
- Art definitiva: sostituire i file mantenendo i nomi (zero cambi FE).
  Priorità pittorica: gli emblemi restano validi a lungo; i banner
  di classe sono i primi candidati a un'illustrazione dipinta.

**v2 — FASE 8F**: tutti i 132 SVG sono stati rigenerati con il
generatore potenziato: i ritratti hanno ora volto (occhi, sopracciglia,
bocca), collo, spallacci corazzati con finitura ed emblema,
capigliatura per genere e luci/ombre derivate dalla palette del gruppo
lore; i banner hanno campo stellare deterministico, tre quinte di
paesaggio, bagliore (feGaussianBlur) sul glifo e cornice ornamentale
con angoli decorati. Restano art *procedurale*: presentabili come
identità visiva coerente, ma non sostituiscono illustrazioni dipinte.

Tutti gli asset sono SVG in `frontend/public/assets/`.
**Per sostituirli con l'art definitiva basta rimpiazzare i file
mantenendo gli stessi nomi** (va bene anche cambiare estensione in .png/.webp:
in quel caso aggiornare le catene in `frontend/src/utils/gameAssets.js`).
Il componente `<GameImage/>` ha fallback automatico: un file mancante
non rompe mai la UI.

## Avatar avventurieri — `assets/avatars/`
- `{race_slug}_{male|female}.svg` — 50 razze × 2 generi = 100 file
  (slug identici a `round160_seed_races.py`). Placeholder: busto
  stilizzato con tratti per gruppo lore (orecchie elfiche, corna,
  zanne, barba, aureola, ingranaggi, ...) e variante di genere.
- `default.svg` — fallback finale.
- Priorità art definitiva: le 8 razze più comuni (human, high_elf,
  wood_elf, dwarf_mountain, half_orc, halfling_lightfoot, tiefling,
  dragonborn_red).

## Temi dungeon — `assets/themes/`
19 temi + `default.svg`: tutorial, caves, beast, nature, crypt, mines,
library, frost, marsh, forge, sea, arena, clockwork, storm, dragon,
void, infernal, celestial, worldtree.
Mapping slug→tema in `gameAssets.js` (`DUNGEON_THEME`). Per un'immagine
DEDICATA a un singolo dungeon: creare `assets/dungeons/{slug}.svg` —
ha priorità automatica sul tema (la cartella oggi non esiste: è il
primo elemento della catena di fallback).

## Raid — `assets/raids/`
`moonfall-vigil.svg`, `broken-bastion-siege.svg`,
`necropolis-bells.svg`, `dragon-vault.svg`.

## Banner sezioni — `assets/banners/`
`dashboard.svg` (hero della home), `dungeons.svg`, `raids.svg`,
`crafting.svg`, `inventory.svg`, `adventurers.svg`, `alchemy.svg`.

## Dove sono usati oggi
- Dashboard: hero banner con nome gilda (`sectionBanner("dashboard")`).
- Dungeons: header immagine su ogni card (tema per slug) + card-fantasy.
- Raids: banner su ogni card raid.
- Adventurers: ritratto in tabella desktop, card mobile e scheda modale.
- Crafting / Inventory: banner di sezione.
- CSS: `.card-fantasy`, `.banner-fantasy`, `.font-fantasy`,
  `.divider-fantasy` in `index.css`.

## Cosa richiede DAVVERO art esterna (valutazione onesta, FASE 8F)
Il procedurale copre bene icone, banner atmosferici e ritratti
stilizzati. NON può raggiungere qualità da illustrazione per:
1. **Hero della Dashboard** (`banners/dashboard.svg`) — è la prima
   cosa che il giocatore vede: merita un'illustrazione dipinta.
2. **Ritratti delle 8 razze più giocate** (human, high_elf, wood_elf,
   dwarf_mountain, half_orc, halfling_lightfoot, tiefling,
   dragonborn_red × 2 generi = 16 immagini): i volti procedurali sono
   riconoscibili ma geometrici.
3. **I 4 banner raid** — i raid sono il contenuto premium; un glifo
   con glow non trasmette la scala di un assedio o di un drago.
4. **Immagini dedicate per i dungeon endgame** (`assets/dungeons/
   {slug}.svg|png` — cartella già prevista dalla catena di fallback):
   almeno dragons-hoard, infernal-pit-5p, celestial-citadel-5p,
   world-tree-roots-5p, voidspire-5p.
Formati accettati: PNG/WEBP/SVG con gli stessi nomi file (per PNG/WEBP
aggiornare le catene in `gameAssets.js`). Nessun cambio di codice per
gli SVG. Tutto il resto (tema-banner, sezioni, 42 razze minori) è
coperto in modo adeguato dal procedurale v2.

## Specifiche per l'art definitiva
- Avatar: quadrato ≥256×256, soggetto centrato, sfondo scuro o
  trasparente (viene ritagliato in cerchio).
- Banner temi/raid/sezioni: ~800×320 (ratio 2.5:1), soggetto centrale,
  bordi scuri (la UI applica una vignettatura in basso per i titoli).
- Rigenerare i placeholder in qualsiasi momento:
  `python scripts/fase4_genera_assets.py` (idempotente).
