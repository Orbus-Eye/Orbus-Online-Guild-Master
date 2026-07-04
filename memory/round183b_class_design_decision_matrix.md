# ROUND 18.3b — Class Design Decision Matrix (Audit-only)
**Round**: R18.3b · **Data**: 2026-07-04T20:24:31.087724+00:00 · **Status**: OPEN — Decision Support

**Autorità**: PM-facing. Zero decisioni sigillate. Tutte le opzioni sono candidate.

---

## §1 · Executive summary

Il round R18.3 apply (migration reale 496 orphan) è **DEFERRED** finché il PM non decide un minimo di **7 domande P0** che riguardano le 5 classi migration-critical (paladino, guerriero, ladro, cacciatore_di_mostri, cacciatore_del_vuoto). Post-R18.3a le 2 classi target esistono in catalog con `role='TBD'` + `role_pm_decision_pending=true` — questo report fornisce il materiale per rispondere a Q7-Q24.

**Impatto migration futura**: **303 adv** (175 ranger → cacciatore_di_mostri + 128 warlock → cacciatore_del_vuoto) migreranno verso classi con `role='TBD'` e stat non definite. Senza P0 risolti, i 303 adv resterebbero con dati provvisori.

**Conteggi domande PM per priorità**:
- **P0**: 7 domande
- **P1**: 7 domande
- **P2**: 3 domande
- **P3**: 3 domande

**Ambiguità note su fonti**: OCR sporco su tabelle armor/scudi per 5-7 classi (Alchimista, Artificiere, Fabbro Arcano, Runista, Sciamano). Alcune classi hanno `fantasy_archetipo=TBD_source_readable_but_extraction_regex_missed_quote_marker` — testo leggibile ma citazione non estraibile via regex.

---

## §2 · Migration-Critical Classes (PRIORITÀ MASSIMA)

| # | Classe | Slug | Legacy mapping | Orphan | Role A | Role B | Stat prim A | Stat prim B | Armor | Scudi | Bridge pool | Rischio player-facing | Decisione PM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Paladino | `paladino` | priest → paladin | **190** | Tank | Healer | STR | CHA | H | Sì | 92 | 190 player vedranno la loro classe cambiare da 'priest' a 'Paladino' — banner UI IT necessario | P0: role finale + stat primary + armor tier (opzioni A=Tank/STR, B=Healer/CHA) |
| 2 | Guerriero | `guerriero` | berserker → warrior | **3** | Tank | DPS | STR | CON | H | Sì | 69 | 3 player vedranno la loro classe cambiare da 'berserker' a 'Guerriero' — banner UI IT necessario | P0: role finale + stat primary + armor tier (opzioni A=Tank/STR, B=DPS/CON) |
| 3 | Ladro | `ladro` | assassin → rogue | **0** | DPS | Utility | DEX | INT | L | N | 31 | Zero orphan (alias no-migration) | P0: role finale + stat primary + armor tier (opzioni A=DPS/DEX, B=Utility/INT) |
| 4 | Cacciatore di Mostri | `cacciatore_di_mostri` | ranger → cacciatore_di_mostri | **175** | DPS | Utility | DEX | WIS | M | N | 31 | 175 player vedranno la loro classe cambiare da 'ranger' a 'Cacciatore di Mostri' — banner UI IT necessario | P0: role finale + stat primary + armor tier (opzioni A=DPS/DEX, B=Utility/WIS) |
| 5 | Cacciatore del Vuoto | `cacciatore_del_vuoto` | warlock → cacciatore_del_vuoto | **128** | DPS | Control | INT | CHA | L | N | 18 | 128 player vedranno la loro classe cambiare da 'warlock' a 'Cacciatore del Vuoto' — banner UI IT necessario | P0: role finale + stat primary + armor tier (opzioni A=DPS/INT, B=Control/CHA) |

---

## §3 · Matrice completa 27 classi

Legenda ruoli: T=Tank · H=Healer · D=DPS · S=Support · C=Control · U=Utility · Su=Summoner · Hy=Hybrid

| # | Nome | Slug | Dadi | T | H | D | S | C | U | Su | Hy | Stat A | Stat B | Armor | Scudi | Risorse | Live adv | Bridge | Rischio |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Alchimista | `alchimista` | d6 |  |  |  | ✓ |  | ✓ |  |  | INT | DEX | L | TBD | ki, carica | 135 | — | basso |
| 2 | Artificiere | `artificiere` | d6 |  |  | ✓ | ✓ |  |  |  |  | INT | DEX | M | TBD | ki, carica, runa | — | — | medio |
| 3 | Astrologo | `astrologo` | 1d8 |  |  |  | ✓ | ✓ |  |  |  | WIS | INT | L | N | carica, carte, sangue | — | — | medio |
| 4 | Bardo | `bardo` | 1d6 |  |  |  | ✓ | ✓ |  |  |  | CHA | INT | L | N | vuoto, spiriti | 177 | — | basso |
| 5 | Burattinaio | `burattinaio` | 1d8 |  |  |  |  | ✓ |  | ✓ |  | INT | CHA | L | N | carica, dominio, vuoto | — | — | alto |
| 6 | Cacciatore del Sangue | `cacciatore_del_sangue` | 1d8 |  |  | ✓ |  |  |  |  |  | STR | DEX | M | N | mana, furia, sangue | — | — | medio |
| 7 | Cacciatore del Vuoto | `cacciatore_del_vuoto` | d8 |  |  | ✓ |  | ✓ |  |  |  | INT | CHA | L | N | mana, vuoto | — | 18 | alto |
| 8 | Cacciatore di Mostri | `cacciatore_di_mostri` | 1d10 |  |  | ✓ |  |  | ✓ |  |  | DEX | WIS | M | N | essenza, carica, carte | — | 31 | medio |
| 9 | Cartografo | `cartografo` | 1d8 |  |  |  | ✓ |  | ✓ |  |  | INT | WIS | L | N | carica, dominio | — | — | alto |
| 10 | Cavaliere della Morte | `cavaliere_della_morte` | 1d10 | ✓ |  | ✓ |  |  |  |  |  | STR | CON | H | Sì | mana, furia, essenza | — | — | alto |
| 11 | Cavaliere di Draghi | `cavaliere_dei_draghi` | d10 | ✓ |  | ✓ |  |  |  |  |  | STR | CHA | H | Sì | mana, furia, dominio | — | — | alto |
| 12 | Cronista | `cronista` | 1d6 |  |  |  | ✓ |  | ✓ |  |  | INT | CHA | L | N | carica, carte, sangue | — | — | medio |
| 13 | Druido | `druido` | d6 |  | ✓ |  |  |  |  |  | ✓ | WIS | CON | L | N | mana, vuoto, spiriti | 167 | — | medio |
| 14 | Fabbro Arcano | `fabbro_arcano` | 1d8 |  |  |  | ✓ |  | ✓ |  |  | INT | STR | M | TBD | carica, rune | — | — | medio |
| 15 | Giocatore d'Azzardo | `giocatore_dazzardo` | 1d8 |  |  |  |  |  | ✓ |  | ✓ | CHA | DEX | L | N | carica, carte, sangue | — | — | alto |
| 16 | Guerriero | `guerriero` | d10 | ✓ |  | ✓ |  |  |  |  |  | STR | CON | H | Sì | mana, furia, carica | 290 | 69 | basso |
| 17 | Ladro | `ladro` | 1d8 |  |  | ✓ |  |  | ✓ |  |  | DEX | INT | L | N | carica, vuoto, rune | 229 | 31 | basso |
| 18 | Mago | `mago` | 1d6 |  |  | ✓ |  | ✓ |  |  |  | INT | WIS | N | N | furia, carica, dominio | 218 | — | basso |
| 19 | Mercante | `mercante` | 1d8 |  |  |  | ✓ |  | ✓ |  |  | CHA | INT | L | N | carica, sangue, vuoto | — | — | alto |
| 20 | Monaco | `monaco` | 1d8 |  |  | ✓ |  |  |  |  | ✓ | DEX | WIS | N | N | furia, ki, essenza | 162 | — | basso |
| 21 | Negromante | `negromante` | 1d8 |  |  | ✓ |  |  |  | ✓ |  | INT | WIS | L | N | essenza, dominio | 0 | — | medio |
| 22 | Paladino | `paladino` | d10 | ✓ | ✓ |  |  |  |  |  |  | STR | CHA | H | Sì | mana, furia, essenza | 166 | 92 | basso |
| 23 | Parassita | `parassita` | 1d8 |  |  | ✓ |  | ✓ |  |  |  | CON | INT | N | N | mana, carica, dominio | — | — | alto |
| 24 | Pittore | `pittore` | 1d6 |  |  |  | ✓ | ✓ |  |  |  | CHA | INT | L | N | essenza, carica, sangue | — | — | alto |
| 25 | Runista | `runista` | 1d6 |  |  | ✓ | ✓ |  |  |  |  | INT | WIS | M | TBD | mana, essenza, carica | — | — | medio |
| 26 | Sciamano | `sciamano` | 1d6 |  | ✓ |  | ✓ |  |  |  |  | WIS | CHA | L | TBD | mana, furia, essenza | — | — | medio |
| 27 | Sognatore | `sognatore` | 1d6 |  |  |  | ✓ | ✓ |  |  |  | WIS | CHA | L | N | carica, dominio, sangue | — | — | alto |

**Note**: `27/27` classi con stat model candidato compilato, `27/27` con armor tier candidato, `18/27` senza live counterpart.

---

## §4 · Sovrapposizioni da risolvere (8 gruppi)

### OL1 · Mago vs Runista — livello **MEDIO**

- **Classi**: `mago`, `runista`
- **Rischio**: Mago = arcana pure caster (d6, INT), Runista = arcana rune-craft (d6, INT). Item pool arcana rischia duplicati.
- **Opzioni differenziazione**:
  - Opz A — Mago = damage pure (evocazione/blast), Runista = support/utility (buff/ward via runes)
  - Opz B — Mago = mana pool tradizionale, Runista = rune-consuming (risorsa dedicata)
  - Opz C — Mago = single-target, Runista = area/persistent effect (rune inscritte)
- **Decisione PM**: P1-1: Quale differenziazione per Mago vs Runista? (A/B/C/deferred)

### OL2 · Guerriero vs Paladino vs Cavaliere della Morte — livello **ALTO**

- **Classi**: `guerriero`, `paladino`, `cavaliere_della_morte`
- **Rischio**: 3 heavy melee STR-primary d10 armor pesante shield-yes. Rischio party composition ambigua: quale scegliere come Tank principale?
- **Opzioni differenziazione**:
  - Opz A — Guerriero=Tank puro, Paladino=Tank/Healer hybrid, Cavaliere Morte=Tank/DPS con risorsa essenza
  - Opz B — Distinguere via risorsa: Guerriero=furia, Paladino=mana+essenza divina, CDM=essenza + curse mechanic
  - Opz C — Distinguere via alignment: Guerriero=neutral, Paladino=light, CDM=dark → tema visivo/narrativo
- **Decisione PM**: P0-3: Differenziazione Guerriero/Paladino/Cavaliere Morte come Tank+DPS d10 STR-heavy (A/B/C)?

### OL3 · Cacciatore di Mostri vs Cacciatore del Sangue vs Cacciatore del Vuoto — livello **MEDIO**

- **Classi**: `cacciatore_di_mostri`, `cacciatore_del_sangue`, `cacciatore_del_vuoto`
- **Rischio**: 3 hunter archetypes. CdM=ranger lineage (DEX, d10, media armor), CdS=blood-magic DPS (STR/DEX, d8, media), CdV=warlock lineage (INT/CHA, d8, leggera). Rischio: item pool 'weapon+hunt gear' condiviso.
- **Opzioni differenziazione**:
  - Opz A — CdM=ranged physical (bow/crossbow, DEX), CdS=melee physical + blood-consume (STR), CdV=arcane ranged + void-consume (INT)
  - Opz B — CdM=nature/beast focus, CdS=corruption/blood focus, CdV=void/eldritch focus — differenziazione tematica
  - Opz C — Item pool separati (già in R18.3a: 31 items CdM, 18 items CdV, blood pool TBD)
- **Decisione PM**: P0-4: Differenziazione dei 3 cacciatori come archetype/stat/armor (A/B/C)?

### OL4 · Artificiere vs Fabbro Arcano — livello **ALTO**

- **Classi**: `artificiere`, `fabbro_arcano`
- **Rischio**: 2 tinker/craft classes con carica risorsa comune. Artificiere=Support/DPS d6 (INT/DEX), Fabbro Arcano=Support/Utility d8 (INT/STR). Rischio item pool 'crafted items' duplicato.
- **Opzioni differenziazione**:
  - Opz A — Artificiere=combat automaton (turrets/robots active), Fabbro Arcano=item enhancement (buff pre-battle)
  - Opz B — Artificiere=DPS-focused tinker, Fabbro Arcano=pure utility craftsman (0 combat presence, party enabler)
  - Opz C — Fondere in una singola classe (mossa più drastica: -1 canonical class)
- **Decisione PM**: P1-2: Differenziazione Artificiere vs Fabbro Arcano (A/B/C, C=merge)?

### OL5 · Sognatore vs Pittore — livello **MEDIO**

- **Classi**: `sognatore`, `pittore`
- **Rischio**: 2 abstract/psy caster d6 CHA/WIS. Sognatore=Control/Support (dream), Pittore=Support/Control (pigmenti-anima). Rischio: player confusion 'chi fa cosa mentale'.
- **Opzioni differenziazione**:
  - Opz A — Sognatore=mental control (charm/sleep/illusion), Pittore=area buff/debuff via 'canvases'
  - Opz B — Sognatore=INT-based (arcane oneiric), Pittore=CHA-based (art-charisma buff)
  - Opz C — Merge in singola 'Artista dell'Anima' con 2 rami talenti
- **Decisione PM**: P1-3: Differenziazione Sognatore vs Pittore (A/B/C, C=merge)?

### OL6 · Sciamano vs Druido — livello **ALTO**

- **Classi**: `sciamano`, `druido`
- **Rischio**: 2 nature/spirit healer. Druido=Healer/Hybrid d6 WIS (già live, druid, 167 adv), Sciamano=Healer/Support d6 WIS/CHA (nuova, 0 adv). Rischio: 167 druid live vs sciamano nuovo → chi ha priorità di feature?
- **Opzioni differenziazione**:
  - Opz A — Druido=nature transformation (forme animali), Sciamano=totem/spirit-bond (evocazione spiriti immateriali)
  - Opz B — Druido=WIS-primary (nature), Sciamano=CHA-primary (spirit voice)
  - Opz C — Sciamano diventa specializzazione Druido (2 rami talenti) invece che classe separata
- **Decisione PM**: P1-4: Differenziazione Druido (live 167 adv) vs Sciamano nuovo (A/B/C, C=spec merge)?

### OL7 · Mercante vs Giocatore d'Azzardo — livello **ALTO**

- **Classi**: `mercante`, `giocatore_dazzardo`
- **Rischio**: 2 economy/luck classes CHA-based d8. Rischio economico: entrambi possono manipolare drop/prezzi/oro → double abuse.
- **Opzioni differenziazione**:
  - Opz A — Mercante=economia strategica (prezzi/inventario), GdA=combat luck/dice/carte (in-fight variance)
  - Opz B — Mercante=guild-level buff (income+), GdA=party-level buff (single-encounter variance)
  - Opz C — Bandire una delle due (Mercante o GdA) come classe player e ridurla a NPC
- **Decisione PM**: P1-5: Differenziazione Mercante vs Giocatore d'Azzardo (A/B/C, C=demote NPC)?

### OL8 · Cartografo vs Cronista vs Astrologo — livello **MEDIO**

- **Classi**: `cartografo`, `cronista`, `astrologo`
- **Rischio**: 3 knowledge/utility. Cartografo=Utility/Support d8 (dominio/carica), Cronista=Support/Utility d6 (carte/sangue), Astrologo=Support/Control d8 (carte/sangue). Overlap su 'carte' risorsa.
- **Opzioni differenziazione**:
  - Opz A — Cartografo=exploration (map bonus, world-tier), Cronista=lore/party-XP boost, Astrologo=predictions/buff
  - Opz B — Distinguere via risorsa unica: Cartografo=dominio, Cronista=sangue, Astrologo=carte (già preliminare)
  - Opz C — Merge 2 delle 3 (es. Cartografo+Cronista = 'Scholar' con 2 rami)
- **Decisione PM**: P2-1: Differenziazione Cartografo/Cronista/Astrologo (A/B/C, C=merge scholar)?

---

## §5 · Stat model proposto (PRELIMINARE — PM può ridefinire)

Uso 6-stat standard (STR/DEX/CON/INT/WIS/CHA). Marca esplicitamente ogni entry come **candidato** — nessuna decisione sigillata.

| Slug | Primary A | Primary B | Secondary | Rationale |
|---|---|---|---|---|
| `alchimista` | **INT** | DEX | WIS, CON | d6 caster + carica risorsa → INT primary; DEX per bombe/pozioni physical |
| `artificiere` | **INT** | DEX | CON | d6 tinker + carica/runa → INT ; costruzione fisica → DEX |
| `astrologo` | **WIS** | INT | CHA | d8 divinazione + carte/sangue → WIS insight ; INT lettura arcana |
| `bardo` | **CHA** | INT | DEX | d6 support/control + vuoto/spiriti → CHA performance ; INT sapienza |
| `burattinaio` | **INT** | CHA | DEX | d8 summoner + dominio/vuoto → INT controllo ; CHA imposizione volontà |
| `cacciatore_del_sangue` | **STR** | DEX | CON | d8 DPS + furia/sangue → STR raw damage ; DEX weapon versatility |
| `cacciatore_del_vuoto` | **INT** | CHA | DEX, WIS | d8 DPS/Control + mana/vuoto → INT arcana ; CHA void bond (warlock lineage) |
| `cacciatore_di_mostri` | **DEX** | WIS | STR, INT | d10 DPS/Utility + essenza/carica/carte → DEX ranger lineage ; WIS hunt lore |
| `cartografo` | **INT** | WIS | CHA | d8 utility + carica/dominio → INT mapping ; WIS pathfinding |
| `cavaliere_della_morte` | **STR** | CON | INT | d10 Tank/DPS + mana/furia/essenza → STR martial ; CON undead resilience |
| `cavaliere_dei_draghi` | **STR** | CHA | CON | d10 Tank/DPS + mana/furia/dominio → STR mounted combat ; CHA dragon bond |
| `cronista` | **INT** | CHA | WIS | d6 utility + carica/carte/sangue → INT knowledge ; CHA storytelling |
| `druido` | **WIS** | CON | STR | d6 healer/hybrid + mana/vuoto/spiriti → WIS nature attunement |
| `fabbro_arcano` | **INT** | STR | CON | d8 support/utility + carica/rune → INT craft-lore ; STR forge labor |
| `giocatore_dazzardo` | **CHA** | DEX | INT | d8 hybrid + carica/carte/sangue → CHA luck-charm ; DEX sleight |
| `guerriero` | **STR** | CON | DEX | d10 Tank/DPS + mana/furia/carica → STR classic martial primary |
| `ladro` | **DEX** | INT | CHA | d8 DPS/Utility + carica/vuoto/rune → DEX classic rogue primary |
| `mago` | **INT** | WIS | CON | d6 DPS/Control + furia/carica/dominio → INT classic arcane primary |
| `mercante` | **CHA** | INT | WIS | d8 utility/support + carica/sangue/vuoto → CHA trade ; INT economics |
| `monaco` | **DEX** | WIS | STR | d8 DPS/Hybrid + furia/ki/essenza → DEX martial arts ; WIS ki mastery |
| `negromante` | **INT** | WIS | CON | d8 Summoner/DPS + essenza/dominio → INT arcana ; WIS death lore |
| `paladino` | **STR** | CHA | CON, WIS | d10 Tank/Healer + mana/furia/essenza → STR martial ; CHA divine channeling (priest lineage) |
| `parassita` | **CON** | INT | STR | d8 DPS/Control + mana/carica/dominio → CON biomass host ; INT infestation control |
| `pittore` | **CHA** | INT | WIS | d6 support/control + essenza/carica/sangue → CHA soul expression ; INT pigment arcana |
| `runista` | **INT** | WIS | CON | d6 support/DPS + mana/essenza/carica → INT rune-craft ; WIS ancient script |
| `sciamano` | **WIS** | CHA | CON | d6 healer/support + mana/furia/essenza → WIS spirit ; CHA totem-charm |
| `sognatore` | **WIS** | CHA | INT | d6 control/support + carica/dominio/sangue → WIS oneiric ; CHA dream-manipulation |

**Coverage**: 27/27 classi con proposta stat. Nessuna decisione applicata al catalog live.

---

## §6 · Armor tier + scudi (candidato)

Legenda: **H**=Pesante · **M**=Media · **L**=Leggera · **N**=Nessuna · **TBD**=OCR sporco

| Slug | Armor tier | Scudi | Note |
|---|---|---|---|
| `alchimista` | **L** | TBD | Base PDF menziona 'armature leggere' preliminare |
| `artificiere` | **M** | TBD | Costruzioni robotiche → medium armor plausible; TBD OCR |
| `astrologo` | **L** | N | Caster + carte → leggera consistent |
| `bardo` | **L** | N | Legacy bard armor leggera |
| `burattinaio` | **L** | N | Summoner tende leggera; TBD conferma OCR |
| `cacciatore_del_sangue` | **M** | N | Hunter tende media; furia/sangue melee → medium |
| `cacciatore_del_vuoto` | **L** | N | Warlock lineage → leggera consistente |
| `cacciatore_di_mostri` | **M** | N | Ranger lineage → media consistent; d10 supporta |
| `cartografo` | **L** | N | Utility explorer → leggera |
| `cavaliere_della_morte` | **H** | Sì | Death knight canonico H+shield |
| `cavaliere_dei_draghi` | **H** | Sì | Dragon knight mounted H+shield |
| `cronista` | **L** | N | Scholar → leggera |
| `druido` | **L** | N | Legacy druid natural armor (leggera + forme animali) |
| `fabbro_arcano` | **M** | TBD | Craft-heavy → media; TBD scudi |
| `giocatore_dazzardo` | **L** | N | Sleight-based → leggera |
| `guerriero` | **H** | Sì | Warrior canonico H+shield |
| `ladro` | **L** | N | Rogue canonico leggera |
| `mago` | **N** | N | Mage canonico no-armor (o robes → N) |
| `mercante` | **L** | N | Merchant → leggera |
| `monaco` | **N** | N | Monk canonico unarmored (ki-based) |
| `negromante` | **L** | N | Necro classic leggera + robes |
| `paladino` | **H** | Sì | Paladin canonico H+shield (priest lineage → optional shield) |
| `parassita` | **N** | N | Biomass host → nessuna (integrata nel corpo) |
| `pittore` | **L** | N | Artist → leggera |
| `runista` | **M** | TBD | Runecrafter → media plausible; TBD OCR |
| `sciamano` | **L** | TBD | Legacy shaman leggera; scudi tribal TBD |
| `sognatore` | **L** | N | Dreamweaver → leggera |

**Distribuzione armor**:
- H_pesante: 4 classi
- M_media: 5 classi
- L_leggera: 15 classi
- N_nessuna: 3 classi
- TBD: 0 classi

**Distribuzione scudi**:
- Sì: 4 classi
- N: 18 classi
- TBD: 5 classi

**Conflitti/ambiguità**: 5 classi con `scudi=TBD` (OCR sporco) — vedi P1-6.

---

## §7 · Risorse di classe (estratto dai file sorgente)

| Risorsa | Classi che la usano | N |
|---|---|---|
| `carica` | alchimista, artificiere, astrologo, burattinaio, cacciatore_di_mostri, cartografo, cronista, fabbro_arcano, giocatore_dazzardo, guerriero, ladro, mago, mercante, parassita, pittore, runista, sognatore | 17 |
| `mana` | cacciatore_del_sangue, cacciatore_del_vuoto, cavaliere_della_morte, cavaliere_dei_draghi, druido, guerriero, paladino, parassita, runista, sciamano | 10 |
| `furia` | cacciatore_del_sangue, cavaliere_della_morte, cavaliere_dei_draghi, guerriero, mago, monaco, paladino, sciamano | 8 |
| `essenza` | cacciatore_di_mostri, cavaliere_della_morte, monaco, negromante, paladino, pittore, runista, sciamano | 8 |
| `sangue` | astrologo, cacciatore_del_sangue, cronista, giocatore_dazzardo, mercante, pittore, sognatore | 7 |
| `dominio` | burattinaio, cartografo, cavaliere_dei_draghi, mago, negromante, parassita, sognatore | 7 |
| `vuoto` | bardo, burattinaio, cacciatore_del_vuoto, druido, ladro, mercante | 6 |
| `carte` | astrologo, cacciatore_di_mostri, cronista, giocatore_dazzardo | 4 |
| `ki` | alchimista, artificiere, monaco | 3 |
| `spiriti` | bardo, druido | 2 |
| `rune` | fabbro_arcano, ladro | 2 |
| `runa` | artificiere | 1 |

**Risorse candidate uniche**: 12 (proposte, PM deve sigillare — vedi P1-7).
**Classi con `TBD source_silent`** (nessuna risorsa estratta): 0.

---

## §8 · Domande PM finali (ordinate per priorità)

### P0 — 7 domande

- **`P0-1`** (§2) — Ruolo finale Paladino: Tank/Healer hybrid A o Healer/Tank B?
  - Risposta: `A / B / deferred`
  - Blocca: R18.3 apply (190 priest orphan)

- **`P0-2`** (§2) — Ruolo finale Cacciatore di Mostri: DPS puro A o Ranger/Support B?
  - Risposta: `A / B / deferred`
  - Blocca: R18.3 apply (175 ranger orphan)

- **`P0-3`** (§4 OL2) — Differenziazione Guerriero/Paladino/Cavaliere Morte come 3 tank-DPS d10 STR-heavy?
  - Risposta: `A (ruoli distinti) / B (risorse distinte) / C (alignment) / deferred`
  - Blocca: R18.3 apply + R18.4 item class-bound

- **`P0-4`** (§4 OL3) — Differenziazione dei 3 cacciatori (di Mostri / del Sangue / del Vuoto)?
  - Risposta: `A (physical vs blood vs arcane) / B (tematica) / C (item-pool) / deferred`
  - Blocca: R18.3 apply (303 hunter-ish orphan)

- **`P0-5`** (§2) — Ruolo finale Cacciatore del Vuoto: DPS/Caster A o Support/Control B?
  - Risposta: `A / B / deferred`
  - Blocca: R18.3 apply (128 warlock orphan)

- **`P0-6`** (§5) — Stat primaria Paladino: STR (martial) A o CHA (divine channeling) B?
  - Risposta: `A / B / entrambe (dual-primary) / deferred`
  - Blocca: R18.3 apply + R18.4 armor requirements

- **`P0-7`** (§6) — Armor tier finale Cacciatore di Mostri: Media (ranger lineage) o Leggera (agility)?
  - Risposta: `Media / Leggera / deferred`
  - Blocca: R18.3 apply + R18.4 item catalog

### P1 — 7 domande

- **`P1-1`** (§4 OL1) — Differenziazione Mago vs Runista (arcana caster overlap)?
  - Risposta: `A / B / C / deferred`
  - Blocca: R18.4 item class-bound (arcana items)

- **`P1-2`** (§4 OL4) — Differenziazione Artificiere vs Fabbro Arcano (tinker overlap)?
  - Risposta: `A / B / C=merge / deferred`
  - Blocca: R18.4 crafting items

- **`P1-3`** (§4 OL5) — Differenziazione Sognatore vs Pittore (abstract-psy overlap)?
  - Risposta: `A / B / C=merge / deferred`
  - Blocca: R18.4 caster items

- **`P1-4`** (§4 OL6) — Differenziazione Druido (167 live) vs Sciamano nuovo?
  - Risposta: `A / B / C=spec merge / deferred`
  - Blocca: R18.4 healer items + potential R18.3 druid impact

- **`P1-5`** (§4 OL7) — Differenziazione Mercante vs Giocatore d'Azzardo (economy/luck overlap)?
  - Risposta: `A / B / C=demote NPC / deferred`
  - Blocca: R18.4 economy items

- **`P1-6`** (§6) — Scudi Sì/No per: Alchimista, Artificiere, Fabbro Arcano, Runista, Sciamano (TBD OCR)?
  - Risposta: `Sì / No / per-classe / deferred`
  - Blocca: R18.4 item slot equipment

- **`P1-7`** (§7) — Risorse finali dominio + carica + essenza + vuoto + sangue + carte + spiriti + rune + furia + ki + mana → 11 candidate. Quali sigillare come canoniche (max 6-8 raccomandato)?
  - Risposta: `elenco slug sigillati / deferred`
  - Blocca: R18.4 combat resource system

### P2 — 3 domande

- **`P2-1`** (§4 OL8) — Differenziazione Cartografo vs Cronista vs Astrologo (knowledge overlap)?
  - Risposta: `A / B / C=merge scholar / deferred`
  - Blocca: R18.5 talent branch overlap

- **`P2-2`** (§3) — 3 rami talenti canonici per classe: nomi standard (es. per Paladino 'Vendetta', 'Devozione', 'Protezione')?
  - Risposta: `per-classe elenco / template comune / deferred`
  - Blocca: R18.5 talent tree naming

- **`P2-3`** (§3) — Bonus preliminari 5 tier x 4 talenti per ramo: pattern (es. +Damage / +Utility / +Defensive)?
  - Risposta: `pattern / per-classe custom / deferred`
  - Blocca: R18.5 talent bonus formula

### P3 — 3 domande

- **`P3-1`** (§3) — Achievement dedicati per classi non-live (17/27 senza adv attuali) — priorità high o low?
  - Risposta: `high / low / per-classe / deferred`
  - Blocca: R18.6+ achievement content

- **`P3-2`** (§3) — Set item cross-classe (es. 'Set del Cacciatore' per tutti e 3 i cacciatori) o item pool 100% separati?
  - Risposta: `cross / separati / deferred`
  - Blocca: R18.7 item expansion

- **`P3-3`** (§5) — Naming stat: adottare 6-stat standard (STR/DEX/CON/INT/WIS/CHA) o mantenere schema legacy Orbus (Strength/Agility/Intellect/Endurance/Faith)?
  - Risposta: `6-stat / legacy 5-stat / mapping / deferred`
  - Blocca: R18.X polish + adventurer_public serializer

---

## Rischi tecnici globali (top 5)

1. **Item pool bridge cacciatore_del_vuoto (18 items) insufficiente per 128 adv migrated**
   - Mitigation: R18.4 espandere pool warlock/void items OR abbassare item-slot requirement per migration graduale

2. **8 sovrapposizioni (Mago/Runista, 3 Tank d10, 3 Hunter, Artificiere/Fabbro, ecc.) generano item pool duplicati**
   - Mitigation: R18.3b PM decisioni P1-1..P1-5 + R18.4 item-pool audit per rimuovere duplicati

3. **17/27 classi senza live adventurers (0 baseline) → onboarding e recruitment devono creare rappresentazione**
   - Mitigation: R18.3 apply + recruit generator adapt (deferred a decisione P0)

4. **11 risorse candidate (mana/furia/carica/ki/carte/vuoto/sangue/essenza/dominio/rune/spiriti) → sistema combat troppo eterogeneo**
   - Mitigation: P1-7 sigillare max 6-8 risorse canoniche in R18.5 pre-implementation

5. **OCR sporco su alcuni PDF (armor_tier + scudi TBD per 5-7 classi)**
   - Mitigation: R18.3b PM P1-6 chiarire scudi via testo diretto anziché tabelle formattate

---

## Raccomandazione ordine risposta PM

- P0-1 (Paladino role) — 190 adv più grande gruppo migrato
- P0-2 (Cacciatore di Mostri role) — 175 adv
- P0-5 (Cacciatore del Vuoto role) — 128 adv
- P0-4 (differenziazione 3 hunter) — sblocca item pool R18.4
- P0-3 (differenziazione 3 tank) — sblocca item pool R18.4
- P0-6 (stat primary Paladino) — decide 190 adv equip
- P0-7 (armor CdM) — decide 175 adv equip

**Rationale**: Rispondere P0-1 per primo perché blocca R18.3 apply per il gruppo più numeroso (190 priest → paladin). Poi P0-2 + P0-5 per completare il quadro dei 493 orphan migrated (fuori i 3 berserker + 0 assassin, già alias no-brainer). P0-4 + P0-3 poi risolvono item pool conflicts. P0-6 + P0-7 sono raffinamenti dettagliati.

---

## Conferma vincoli R18.3b

- ✅ zero DB write
- ✅ zero migration
- ✅ zero seed
- ✅ zero UI player-facing
- ✅ zero item bridge nuovo
- ✅ zero talenti reali
- ✅ zero auto-equip/combat math modification
- ✅ all options CANDIDATE — PM decides

---

*Firma: e1 main agent · R18.3b OPEN · decision support only.*

---

## §9 · PM Decisions Sealed (P0-1..P0-7) — as design intent, NOT live DB values

⚠️ **STATUS**: le 7 answers PM alle domande P0 sono state **sigillate come design intent** in `round183b_pm_answers_p0.md` il 2026-07-04T20:40Z. Il catalog `adventurer_classes` NON è stato modificato in R18.3c (mode split `adventurer_class_slug_only`).

**Enum conflict identificato**:
- Schema live 5-stat (`strength/agility/intellect/endurance/faith`) vs PM 6-stat (`charisma/dexterity/constitution/intelligence/wisdom` + `strength`)
- `VALID_ROLES = ("Tank", "DPS", "Healer")` atomic vs PM composite (`Healer/Tank hybrid`, `Martial DPS/Tank`, `DPS/Utility`, `DPS Caster`)
- `base_*` schema catalog non ha `base_dexterity/constitution/wisdom/charisma`

**Reconciliation deferrita a R18.3b.1** (mini-round decisionale, PENDING).

### Sintesi 5 migration-critical (design intent)

| Classe | role_intent | primary_stat_intent | secondary_stats_intent | live DB (invariato) |
|---|---|---|---|---|
| **Paladino** | `Healer/Tank hybrid` | `charisma` | `[strength, constitution]` | role=Tank, primary=faith, secondary=[strength,endurance] |
| **Guerriero** | `Martial DPS/Tank` | `strength` | `[constitution, dexterity]` | role=Tank, primary=strength, secondary=[endurance] |
| **Ladro** | `DPS/Utility` | `dexterity` | `[intelligence, charisma]` | role=DPS, primary=agility, secondary=[strength] |
| **Cacciatore di Mostri** | `DPS/Utility` | `dexterity` | `[wisdom, constitution]` | role=TBD (R18.3a.1), primary=None |
| **Cacciatore del Vuoto** | `DPS Caster` | `intelligence` | `[constitution, dexterity]` | role=TBD (R18.3a.1), primary=None |

### Le altre 22 classi

Restano con placeholder TBD candidato — PM non ha ancora sigillato answers per P0-3/P0-4 in dettaglio esteso (Guerriero/Paladino/Cav Morte differentiation come "opzione A", 3 Cacciatori come "opzione B+C" combinate), né per P1-*/P2-*/P3-*.

**Deliverable R18.3b sealed**:
- `round183b_class_design_decision_matrix.md` (questo file, con §9)
- `round183b_class_design_decision_matrix.json` (aggiornato con `role_intent`/`primary_stat_intent`/`secondary_stats_intent` + `applied_to_live_db=false`)
- `round183b_pm_answers_p0.md` (7 answers PM sealed as design intent)

**R18.3b CLOSED & SEALED (as design intent) ✅ (2026-07-04T20:40Z).** Non riaprire senza brief PM.
