# Round 17.0 — Game Systems Refoundation Audit

**Data**: 2026-07-03T21:30Z (UTC).
**Tipo**: audit strategico **READ-ONLY** — nessuna modifica applicata al codice o al DB.
**Ambito preview**: `guild-master-5.preview.emergentagent.com`, DB `orbus_r16` (289 guilde reali).
**Autore**: E1 refoundation audit agent.

---

## Sezione 1 — Executive Summary

Verdetto sintetico sulle 10 domande fondamentali del PM. Ogni voce riflette lo stato del player medio (non del tester@orbus.test, che è super-buffato). Legenda: ✅ SÌ · ⚠️ PARZIALE · ❌ NO.

| # | Domanda | Verdetto | Riga di riepilogo |
| --- | --- | --- | --- |
| 1 | Il player capisce cosa fare? | ⚠️ | Daily Loop e "Next Recommended Actions" ci sono; ma 96 guilde su 289 sono a Prestigio Lv0 e non hanno mai completato una singola spedizione. |
| 2 | Il player capisce quale classe scegliere? | ❌ | 14 classi con nomi IT ma nessuna guida in-app su ruoli, sinergie o pesi di stat. Distribuzione classi tra avventurieri fortemente squilibrata (berserker=3, warrior=290). |
| 3 | Il player capisce quali statistiche servono? | ❌ | 5 statistiche (str/agi/int/end/faith) ma la Dashboard non spiega mai cosa impatta cosa. Nessuna tooltip. Endurance non è primary_stat per nessuna classe. |
| 4 | Il player capisce quale equip è migliore? | ⚠️ | Auto-Equip fixed in R16.5.4c (report IT, no leak EN). Ma il player non sa quali item cercare né quale rarità puntare. Manca il "why this item". |
| 5 | Il player capisce perché può/non può fare un dungeon? | ⚠️ | `required_level` + `recommended_power` esistono nel catalog ma la UI non evidenzia il perché di un fail. Il narrative post-fail è generico. |
| 6 | Il player capisce come cresce la gilda? | ✅ (fix R16.5.4d) | Dopo R16.5.4d la Prestigio Card mostra XP, prossima soglia, azioni consigliate. Prima era opaco. |
| 7 | Il player capisce cosa sblocca dopo? | ❌ | Nessuna roadmap in-game. Non si sa cosa succede a Prestigio Lv5, Lv10, Lv15. Nessun unlock visibile. Territory, Legendary Forge, Continents esistono ma sono nascosti. |
| 8 | Il reward è proporzionato allo sforzo? | ⚠️ | Rewards per dungeon esistono (base_gold_reward, base_xp_reward) ma non sono visibili PRIMA di lanciare la spedizione, solo dopo. Grind percepito. |
| 9 | Il loop giornaliero è chiaro? | ⚠️ | "Daily Loop" (WHAT TO DO TODAY) esiste ma è in EN, generico ("Complete 1 expedition today"), non citato nell'onboarding. |
| 10 | I sistemi avanzati sono collegati bene al core loop? | ❌ | World Boss, Continents, Legendary Forge, Territory, Stables, PvP-Season, Arfus Forge — 7+ sistemi esistono in DB ma non sono referenziati dal core loop. Il player non li scopre. |

**Verdetto complessivo**: lo scheletro è ricco (14 classi, 158 item, 22 dungeon, 8 continenti, Legendary Forge, ecc.) ma la **connective tissue** che spiega e collega i sistemi al player manca. Il game loop non è comprensibile senza reverse-engineering.

**Segnale duro dal DB**: su 289 guilde, **3 spedizioni totali** sono state avviate all-time (2 in progress + 1 completata). 1966/2040 adventurers sono ancora al livello 1. **La quasi totalità dei player registrati non è mai riuscita a fare la prima azione di gameplay.**

---

## Sezione 2 — Problemi P0 gameplay (bloccanti)

### P0-1 · Onboarding non tracciato / il player si perde subito

- **Gravità**: P0
- **Impatto player**: 96 guilde su 289 hanno `guild_xp` inesistente (campo mancante), 0 spedizioni completate all-time su tutto il DB, 1966 adventurer su 2040 fermi al Lv1. Il player si registra, crea la gilda, e poi non sa cosa fare. La collezione `onboarding_states` ha 0 documenti.
- **File/sistema**: `frontend/src/pages/Dashboard.jsx`, `backend/app/onboarding/*`, mancanza di funnel tracking.
- **Fix suggerito**: (a) attivare tracking `onboarding_states` con stage funnel (registered → guild_created → first_recruit → first_class_assigned → first_equip → first_expedition_launched → first_expedition_completed → first_level_up); (b) UI wizard interattivo che si sblocca step-by-step invece della lista statica "Daily Loop".
- **Rischio**: basso (feature additiva).
- **Stima**: R17.1 dedicated round (~3 giorni).

### P0-2 · Achievements collection vuota ma 578 unlock in audit

- **Gravità**: P0
- **Impatto player**: gli achievement esistono come codice hardcoded (`il-primo-passo`, `beta-tester`, `specialista-*`, `equip-*`, `erede-di-irthe`) ma NON esistono come documenti nella collection `achievements`. `db.achievements.count() = 0`. Se un player va su `/achievements` per vedere cosa sbloccare, non trova nulla di programmatico da esplorare.
- **File/sistema**: `backend/app/achievements/engine.py`, collection `achievements` mai popolata.
- **Fix suggerito**: seed idempotente della collection `achievements` con tutti gli slug canonici dal codice, includendo titolo IT/EN, descrizione, tier, categoria, ricompensa XP Prestigio. Frontend `/achievements` deve fetcharli e mostrare progressione.
- **Rischio**: medio (bisogna capire quale sorgente-di-verità usare).
- **Stima**: 1-2 giorni.

### P0-3 · Raids collection ha 1 documento null

- **Gravità**: P0
- **Impatto player**: `db.raids.count() = 1` ma il documento è tutto None. Il player che va nella sezione Raid trova… niente. Ma `raid_completed` è un hook XP attivo. C'è codice per raids ma nessun contenuto.
- **File/sistema**: `backend/app/raids/*`, catalog non seedato.
- **Fix suggerito**: (a) seed di almeno 5-6 raid con `required_level` scalato (Lv5, Lv8, Lv11, Lv14) + reward + narrativa; (b) rimuovere il doc null orfano con soft-delete.
- **Rischio**: medio (design dei raid come mid-late game endgame).
- **Stima**: 3-5 giorni (design + seed + integrazione UI).

### P0-4 · Resource missions collection vuota

- **Gravità**: P0
- **Impatto player**: `resource_gathering_missions` ha 0 documenti, `continent_resource_catalog` ha 8 (i continenti). Il hook `resource_mission_completed` (+10 XP Prestigio) è wired in `resources/__init__.py:386` ma non c'è NESSUN dato da completare. Il player non può contribuire con resource missions a salire di Prestigio.
- **File/sistema**: `backend/app/resources/*`, generatore missioni assente o dormiente.
- **Fix suggerito**: attivare generator giornaliero di resource missions per continente (es. "Raccogli 5 legno" — reward oro + material + XP Prestigio). Un cron o hook triggerato dall'onboarding.
- **Rischio**: basso.
- **Stima**: 2 giorni.

### P0-5 · Il player scarso non completa mai una prima spedizione

- **Gravità**: P0
- **Impatto player**: 3 spedizioni totali su tutto il DB. Su ~193 guilde con Prestigio Lv3 (ricevuto tutto da achievement unlock), NESSUNA ha fatto una spedizione. Le cause probabili sono: (a) recruit richiede oro; (b) equip richiede scelte; (c) party building non è guidato; (d) minimo team size = 3 non è ovvio; (e) primo dungeon (sewer-nest) richiede power 35 che con adventurer base Lv1 non è banale.
- **File/sistema**: `frontend/src/pages/Expeditions*.jsx`, funnel drop-off.
- **Fix suggerito**: (a) starter dungeon dedicato con power 15-20 (winnable con 3 rookie Lv1 base); (b) primo Lancio guidato con auto-team + auto-equip suggerito; (c) toast "Sei pronto! Lancia la tua prima spedizione".
- **Rischio**: basso (aggiunge, non tocca).
- **Stima**: 3 giorni.

---

## Sezione 3 — Problemi P1 gameplay (importanti, non bloccanti)

### P1-1 · Distribuzione classi squilibrata su primary_stat

- **Gravità**: P1
- **Impatto player**: 5 classi intellect, 4 agility, 3 faith, 2 strength, **0 endurance**. Endurance esiste ma nessuna classe la usa come primary. Il player che vuole "il tank vero" non ha una scelta identitaria chiara — Warrior e Paladin lo coprono ma con strength/faith.
- **File/sistema**: `adventurer_classes` catalog.
- **Fix suggerito**: rifattorizzare 1-2 classi per bilanciare (opzione: Berserker → strength/endurance hybrid con endurance-primary variant, o introdurre "Sentinel" endurance-primary in un round futuro).
- **Rischio**: alto se si rinomina (breaking).
- **Stima**: analisi 1 giorno, decisione strategica.

### P1-2 · Adventurer level plateau a Lv1

- **Gravità**: P1
- **Impatto player**: 96% degli adventurer sono a Lv1. Curva XP interna adventurer non gira. Corollario di P0-5.
- **File/sistema**: `expeditions/services.py` distribuzione XP, `adventurers/services.py` level curve.
- **Fix suggerito**: contestuale a P0-5 (più spedizioni → più XP adventurer). Considerare XP boost su primo tier di dungeon.
- **Rischio**: basso.
- **Stima**: incluso in R17.1.

### P1-3 · Nessuna guida in-app su classi e stat

- **Gravità**: P1
- **Impatto player**: quando il player recluta un avventuriero deve scegliere classe (o classe assegnata post-recruit). La UI mostra `Warrior · Tank · lvl 10` ma non spiega cosa fa "Tank", quali stat lo definiscono, quali dungeon preferisce. Nessuna sezione "Class Guide" nel menu Guida.
- **File/sistema**: `frontend/src/pages/*Guide*.jsx` (se esiste), i18n class descriptions.
- **Fix suggerito**: pagina statica per classe con ruolo, primary_stat, secondary, best-in-slot generico, esempio narrativo. Anche solo in italiano.
- **Rischio**: basso.
- **Stima**: 2-3 giorni FE + testi.

### P1-4 · Coverage item disomogenea tra classi

- **Gravità**: P1
- **Impatto player**: `paladin` ha 34 weapon / 29 armor / 27 accessory (grazie a shared tags "strength/faith"). `alchemist` e `warlock` hanno solo 4 weapon / 3 armor / 3 accessory (pure-class dopo R16.5.4c). Un Alchemist Lv10 potrebbe non trovare mai un pezzo migliore. Monk ha 1 solo accessory.
- **File/sistema**: `items` collection, item seed generator.
- **Fix suggerito**: seed pass per portare ogni classe ad almeno 8-10 item per slot spalmati su rarity (2 Common, 2 Uncommon, 2 Rare, 2 Epic, 1 Legendary). Nessun power creep (rispettato in R16.5.4c ADJ-3).
- **Rischio**: medio (item design + naming lore).
- **Stima**: 4-5 giorni.

### P1-5 · Dungeon curve termina a Lv14

- **Gravità**: P1
- **Impatto player**: dungeon più alto = `world-tree-roots-5p` Lv14 recpwr=360. Nessun endgame. Un player che raggiunge Lv15 non ha più dungeon da fare.
- **File/sistema**: `dungeons` catalog.
- **Fix suggerito**: aggiungere 3-4 dungeon Lv15-20 con recpwr 400-600. Legare a Legendary Forge come reward.
- **Rischio**: medio.
- **Stima**: R17.3 endgame round.

### P1-6 · Prestigio curve troppo ripida oltre Lv3

- **Gravità**: P1
- **Impatto player**: 192 guilde bloccate a Prestigio Lv3 con ~300 XP. Il gap Lv3→Lv4 è +250 XP = ~17 spedizioni successful (a +15) o 4 raid (a +80 con cap 1/day). Anche con daily play, servono giorni. E i raid non esistono (P0-3).
- **File/sistema**: `app/achievements/levels.py`, `xp_hooks.py`.
- **Fix suggerito**: NON toccare curva senza dati. Prima ottieni gioco effettivo (P0-1..P0-5). Poi telemetria di 2-4 settimane. Poi decisione. Curva attuale (100/250/500/900/1500/2200/3000/4000/5000) è ok se le ricompense fluiscono.
- **Rischio**: alto se si tocca curva senza dati.
- **Stima**: Round dedicato futuro con telemetria.

---

## Sezione 4 — Problemi P2 polish (cosmetici / UX marginali)

- **P2-1** · Naming italiano/inglese misto: label backend narrative in EN ("The expedition succeeded. Team power (320) is well above the recommended (35)."). Già tracciato in R16.5.4f.
- **P2-2** · Adventurer name generici (`MaxAdv-d7f067`). Nessuna narrativa/lore per singolo avventuriero. Non impatta funzione ma appiattisce l'attaccamento.
- **P2-3** · Nessuna preview "team power previsto" quando il player seleziona 3 adventurer. Il player deve andare alla spedizione per scoprire il match.
- **P2-4** · Item description generiche (`Smoothed by sea-salt. Floats in any cup of water.`). Charme narrativo ma non didattiche.
- **P2-5** · Dashboard `NEXT RECOMMENDED ACTIONS` in inglese (label + copy dei bullet).
- **P2-6** · `1/6 today's actions` in inglese.

---

## Sezione 5 — Audit classi / stat / equip

Tabella per ognuna delle **14 classi**. Coverage item indicativa (item_types weapon/armor/accessory con class_tag corrispondente; conta includere item shared con altre classi, non solo pure-class).

| Classe | Ruolo | Primary | Secondary | W | A | X | Coverage item verdetto |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **warrior** | Tank | strength | endurance | 26 | 27 | 14 | ✅ ricca |
| **berserker** | DPS | strength | endurance | 25 | 23 | 14 | ✅ ricca (ma solo 3 adventurer nel gioco) |
| **paladin** | Tank/Support | faith | strength, endurance | 34 | 29 | 27 | ✅ ricchissima (best-covered) |
| **assassin** | DPS burst | agility | strength | 21 | 6 | 4 | ⚠️ armor/accessory scarse |
| **rogue** | DPS/Utility | agility | strength | 21 | 6 | 4 | ⚠️ armor/accessory scarse |
| **ranger** | DPS ranged | agility | endurance | 21 | 6 | 4 | ⚠️ armor/accessory scarse |
| **monk** | DPS/Support | agility | endurance, faith | 13 | 6 | **1** | ❌ accessory quasi assenti (1 solo!) |
| **mage** | DPS magic | intellect | endurance | 16 | 4 | 14 | ⚠️ armor scarse |
| **necromancer** | DPS/Debuff | intellect | agility | 16 | 4 | 14 | ⚠️ armor scarse |
| **bard** | Support | intellect | agility, faith | 11 | 4 | 14 | ⚠️ armor scarse |
| **warlock** | DPS magic | intellect | faith, agility | 4 | 3 | 3 | ❌ pure-class coverage minima (fixata parzialmente in R16.5.4c) |
| **alchemist** | Utility | intellect | agility, endurance | 4 | 3 | 3 | ❌ pure-class coverage minima |
| **druid** | Support/Heal | faith | intellect | 10 | 7 | 16 | ⚠️ weapon/armor low |
| **priest** | Heal | faith | intellect | 10 | 5 | 16 | ⚠️ weapon/armor low |

**Riepilogo**:
- Classi sane: warrior, berserker, paladin.
- Classi problematiche: monk (accessory=1!), warlock, alchemist (pure-class low).
- Item mancanti: **~40 item da seedare** per portare tutte le classi a ≥8 item per slot.
- Mismatch stat: nessuna classe usa `endurance` come primary; considerare rebalance strategico (non urgente).

---

## Sezione 6 — Audit item coverage (weapon / armor / accessory × rarity)

Distribuzione globale item nel catalog (158 totali):

| Slot / Rarity | Common | Uncommon | Rare | Epic | Legendary | Totale |
| --- | --- | --- | --- | --- | --- | --- |
| weapon | 17 | 13 | 10 | 14 | 3 | 57 |
| armor | 14 | 7 | 7 | 8 | 4 | 40 |
| accessory | 11 | 7 | 9 | 7 | 4 | 38 |
| shield | 0 | 0 | 1 | 1 | 0 | 2 |
| material | 3 | 3 | 2 | 0 | 0 | 8 |
| material_continental | 0 | 0 | 3 | 5 | 0 | 8 |
| material_event | 0 | 0 | 0 | 3 | 0 | 3 |
| consumable | 2 | 0 | 0 | 0 | 0 | 2 |
| **totale** | 47 | 30 | 32 | 38 | 11 | **158** |

**Gap identificati**:
1. **Shield slot**: solo 2 shield (1 Rare, 1 Epic). Se `shield` è uno slot valido, serve un intero pass di seeding.
2. **Consumable slot**: 2 consumable Common e nient'altro. Il player non ha pozioni/tonici da usare.
3. **Weapon Legendary**: solo 3 in tutto il gioco. Un Lv15+ player rischia di non trovare mai un'arma epic-plus.
4. **Cluster**: molta densità Common (47) e pochissima Legendary (11). Distribuzione asimmetrica.
5. **Livelli item**: `required_level` non risulta popolato in ~tutti gli item (audit_query ritorna None per min/max). Rischio: player Lv1 vede item Lv15 nel roster; oppure il campo è chiamato diversamente (`min_level`?).

---

## Sezione 7 — Audit dungeon / raid curve

### Dungeon (22 totali) — livelli 1-14

| Slug | Req Lv | Rec Pwr | Team | Difficoltà | Legacy |
| --- | --- | --- | --- | --- | --- |
| sewer-nest | 1 | 35 | 3p | starter | no |
| goblin-warrens | 2 | 45 | 3p | starter+ | no |
| bandit-hideout | 2 | 50 | 3p | starter+ | no |
| shadow-crypts | 3 | 75 | 3p | mid | no |
| druid-grove | 3 | 69 | 3p | mid | no |
| wolf-den-5p | 3 | 80 | 5p | mid | no |
| cursed-mines | 4 | 78 | 3p | mid | no |
| sunken-library | 4 | 85 | 3p | mid | no |
| frost-cave-5p | 4 | 90 | 5p | mid | no |
| lich-sanctum | 5 | 94 | 3p | mid+ | no |
| salt-marsh-5p | 5 | 100 | 5p | mid+ | no |
| dragons-hoard | 6 | 100 | 3p | mid+ | no |
| storm-spire | 6 | 110 | 3p | mid+ | no |
| iron-foundry-5p | 6 | 140 | 5p | high | no |
| silent-monastery-5p | 7 | 155 | 5p | high | no |
| pirate-fleet-5p | 8 | 170 | 5p | high | no |
| obsidian-arena-5p | 9 | 210 | 5p | high | no |
| clockwork-vault-5p | 10 | 230 | 5p | endgame- | no |
| voidspire-5p | 11 | 250 | 5p | endgame | no |
| infernal-pit-5p | 12 | 290 | 5p | endgame | no |
| celestial-citadel-5p | 13 | 320 | 5p | endgame | no |
| world-tree-roots-5p | 14 | 360 | 5p | endgame+ | no |

**Verdetto curva**:
- ✅ Progressione lineare `required_level → recommended_power` sensata (35 @ Lv1 → 360 @ Lv14).
- ✅ Bipolarità 3p/5p buona per varietà: 3p per skirmish, 5p per raid-lite.
- ❌ Terminazione secca a Lv14. Nessun Lv15/16/17+ endgame.
- ❌ Rewards NON esposti in questa vista (esistono come `base_gold_reward`/`base_xp_reward` ma player non li vede prima di lanciare).
- ⚠️ Sewer-nest richiede power 35 mentre 3 avv rookie Lv1 base ne fanno ~20-25 → **la prima spedizione è già frustrante** per il player nudo.

### Raid (1 doc collection null)

- `db.raids.count() = 1`, ma il doc è vuoto (tutte le chiavi None).
- Hook `raid_completed` (+80 XP) esiste e ha già emesso 1 evento (tester).
- **Conclusione**: raid come feature esiste solo sull'osso del hook. Nessun contenuto reale.

---

## Sezione 8 — Audit progressione gilda

### Curva Prestigio (`app/achievements/levels.py`)

```
Lv1 = 0
Lv2 = 100
Lv3 = 250
Lv4 = 500
Lv5 = 900
Lv6 = 1500
Lv7 = 2200
Lv8 = 3000
Lv9 = 4000
Lv10 = 5000
Lv11 = 6500
Lv12 = 8000
Lv13 = 9500
Lv14 = 11500
Lv15 = 13500
Lv16 = 16000
Lv17 = 18500
Lv18 = 21500
Lv19 = 24500
Lv20 = 28000
```

### Stima tempo per livello (ottimistico, player attivo)

Ipotesi: 4 spedizioni/giorno (successful, +60 XP) + 1 raid/giorno (victory, +80 XP) + 3 resource missions/giorno (a +30 XP) = **+170 XP/giorno**.

| Livello | XP richiesto | Giorni |
| --- | --- | --- |
| Lv2 | 100 | 0.6 |
| Lv3 | 250 | 1.5 |
| Lv5 | 900 | 5.3 |
| Lv7 | 2200 | 13 |
| Lv10 | 5000 | 29 |
| Lv15 | 13500 | 79 |
| Lv20 | 28000 | 165 |

**Realistico** (player casual, non usa raid, no resource missions perché il sistema è vuoto): +30 XP/giorno (2 spedizioni). Lv20 → 933 giorni. **Curva rotta senza raid/resource attivi**.

### Azioni che danno Prestigio (audit codice)

| Azione | XP | Cap/day | Status |
| --- | --- | --- | --- |
| Expedition success | +15 | 8/day | ✅ attivo |
| Expedition fail | +5 | 8/day | ✅ attivo |
| Raid victory | +80 | 1/day | ⚠️ hook attivo ma NO contenuto |
| Raid partial | +40 | 1/day | ⚠️ come sopra |
| Raid defeat | +15 | 1/day | ⚠️ come sopra |
| Resource mission | +10 | 6/day | ⚠️ hook attivo ma NO contenuto |
| Achievement unlock | +XP variabile | — | ✅ attivo (dominato da 2 achievement iniziali) |

### Azioni che DOVREBBERO dare Prestigio ma non lo danno

- Reclutamento avventuriere raro/epic (non tracciato).
- Crafting legendary item (Legendary Forge esiste ma non è wired su hook Prestigio).
- Territorio: upgrade struttura (non wired).
- Continenti: primo ingresso in continente (non wired).
- Prima classe hall unlock (non wired).

### Proposta curva migliorata (bozza, non applicare in R17.0)

Se raid + resource missions vengono attivati, la curva attuale regge. Se restano dormenti, considerare:
- ridurre gap Lv3→Lv4 da 250 a 175
- aggiungere achievement mid-tier (~+50 XP ognuno) come milestone visibili
- daily quest reward (+30 XP) esplicita

**Non toccare curva prima di attivare i sistemi dormienti** (P0-3, P0-4).

---

## Sezione 9 — Audit loot / materiali / economia

### Drop rate percepito

Non ho dati di telemetria per un tasso reale. Ipotesi da codice:
- Ogni spedizione success = 0-2 loot item (drop_table nel dungeon).
- Loot filtrato per class_tag: se il team è male-scalabile, drop trash.
- Nessuna comunicazione della probabilità di drop al player.

### Materiali

- 3 material Common, 3 Uncommon, 2 Rare, 5 Epic (`material_continental`), 3 Epic (`material_event`).
- Non è chiaro dove il player ottiene material (drop dungeon? resource mission?).
- `resource_gathering_missions` collection vuota (P0-4).
- Verdetto: material esistono in catalog ma **flusso di ingresso non funzionante**.

### Crafting

- Collezione `recipes`: 5 ricette.
- Collezione `legendary_recipe_catalog`: 6 ricette.
- Collezione `legendary_forge_crafting_orders`: 0 (nessuno ha mai craftato).
- Verdetto: crafting esiste ma **non è mai stato utilizzato** dal player-base.

### Inventario

- Non ho dati sul cap per inventario né sul rate di intasamento. Da telemetria futura.

### Coerenza reward vs costi

- Recruit cost: nessun dato tabellare qui, ma la creazione base gilda dà 500 gold e i primi recruit costano oro. Se un player non vince nulla, drena oro senza rimpiazzarlo.
- **Rischio economia**: player scarso può bloccarsi senza oro per reclutare, senza oro non fa raid/dungeon avanzati. Anti-loop.

---

## Sezione 10 — Audit onboarding / dashboard (player simulation)

Simulazione di un nuovo player, step-by-step, con osservazioni.

### Step 1 — Registrazione
- Il player registra email+password su `/register`.
- ✅ Funziona.
- ❌ Nessun tutorial welcome. Nessuna intro narrativa.

### Step 2 — Creazione gilda
- Wizard richiede nome+description gilda.
- ✅ Funziona.
- ❌ Nessuna spiegazione: "cos'è una gilda in Orbus? Cosa farà?".

### Step 3 — Primi avventurieri
- Player va su "Avv." e trova 5 avventurieri starter.
- ⚠️ Non è ovvio che ci siano già 5 starter. Nessuna toast di benvenuto "Hai già la tua prima squadra".
- Player deve intuire cosa fare con loro.

### Step 4 — Prima classe
- La classe è già assegnata a ognuno? Sì (verificato: post-R16.5.4c `class_slug` è backfilled).
- ❌ Player non sa cosa vuol dire "Warrior · Tank · lvl 1". Nessuna guida.

### Step 5 — Primo equip
- Player va su Inventario → Adventurer Equipment → Auto-Equip.
- ✅ Auto-Equip funziona (fix R16.5.4c). Report IT chiaro.
- ⚠️ Ma player non ha item nell'inventario iniziale (o pochi). Auto-Equip mostra "Nessun oggetto migliore" e player non sa dove trovarli.

### Step 6 — Primo dungeon
- Player va su Missioni → Spedizioni.
- Trova sewer-nest Lv1 recpwr=35.
- Player seleziona 3 avv Lv1 base. Team power calcolato ~20-25.
- ⚠️ **Warning "sotto power consigliato" ma no blocco**. Player può lanciare comunque.
- Spedizione dura N minuti. Player aspetta.

### Step 7 — Primo report
- ✅ Report Spedizione IT (fix R16.5.4d).
- ⚠️ Se fallisce, narrativa in EN ("The expedition failed. Team power (25) is well below the recommended (35).") — R16.5.4f follow-up.
- Player ottiene 0 gold, 0 XP se fallisce.
- **Loop di frustrazione**: player scarso → team scarso → fail → no reward → drena oro → non recluta → team scarso.

### Step 8 — Primo level up
- ⚠️ Non arriva praticamente mai (dati DB: 1966/2040 fermi al Lv1).
- Se arriva: nessuna celebrazione, no toast, no tutorial "cosa cambia a Lv2".

### Step 9 — Prima missione mondo
- Resource missions vuote (P0-4). **Non esistono**.
- Player non ha alternative al dungeon fallito.

### Step 10 — Primo raid
- Raid catalog vuoto (P0-3). **Non esistono**.

**Conclusione onboarding**: il funnel si rompe allo Step 6 (primo dungeon fallito senza rete di sicurezza). Da lì il player abbandona.

---

## Sezione 11 — Cosa sistemare prima (Top 10 azioni prioritizzate)

Ordinate per impact/effort ratio:

1. **[P0]** Attivare onboarding tracked funnel con checkpoint visibili (registered → first_expedition_completed). Include starter dungeon a power 15-20 auto-winnable.
2. **[P0]** Seed collection `achievements` con tutti gli slug codificati; aggiungere reward XP Prestigio milestone visibile.
3. **[P0]** Seed collection `resource_gathering_missions` — generatore giornaliero (1 mission per continente, semplice).
4. **[P0]** Seed collection `raids` — 5 raid Lv5/8/11/14 con reward Legendary Forge material.
5. **[P0]** Fix crash `territory/services.py:53` (KeyError 'library') tramite fallback graceful — R16.5.4e già tracciato.
6. **[P1]** Pagina statica "Guida Classi" per le 14 classi con ruolo, stat, esempi.
7. **[P1]** Item seed pass per portare monk/warlock/alchemist a ≥8 item per slot.
8. **[P1]** UI "Recommended power vs your team power" preview PRIMA di lanciare spedizione.
9. **[P2]** Localization sweep IT completo (R16.5.4f).
10. **[P2]** Dungeon Lv15-20 endgame.

---

## Sezione 12 — Roadmap consigliata (R17.1 / R17.2 / R17.3)

Tre round tematici sequenziali che, se eseguiti in ordine, trasformano lo scheletro attuale in un gioco funzionante.

### R17.1 — Onboarding & First Player Success (P0)
- **Obiettivo**: portare il nuovo player dallo Step 1 (register) allo Step 7 (first expedition completed) senza churn.
- **Scope IN**:
  - Onboarding funnel tracked (collection `onboarding_states` popolata, event log).
  - Starter dungeon dedicato (power 15-20, guarantee win con team rookie).
  - UI wizard interattivo Dashboard che si sblocca step-by-step al posto della Daily Loop statica.
  - Toast di celebrazione ai milestone (primo recruit, primo equip, primo dungeon launched, primo dungeon completed).
  - "Cosa succede se fallisci?" fallback: 20% del team XP anche in fail, no total loss.
  - Fix R16.5.4e territory KeyError (piggyback: unblocca la pagina Territorio per il funnel post-first-success).
- **Scope OUT**: raid, resource missions, achievements, endgame.
- **Deliverable**: onboarding tracked + starter dungeon + wizard UI + tost. Metrica: >50% dei nuovi player completa Step 7 entro 30 min.
- **Stima**: 5-7 giorni.
- **Dipendenze**: nessuna.

### R17.2 — World Content Activation (P0/P1)
- **Obiettivo**: attivare i sistemi "esistenti-ma-morti" (raid, resource missions, achievements catalog, materials flow) per dare al player mid-game qualcosa da fare oltre le spedizioni base.
- **Scope IN**:
  - Seed `achievements` collection: 40-50 achievement con XP Prestigio reward.
  - Seed `raids` catalog: 5 raid con narrativa lore, party 5p, reward endgame material.
  - Generator `resource_gathering_missions`: 1 daily mission per continente (8), auto-generata via cron.
  - UI Achievements page (fetch da collection, non hardcoded).
  - UI Raid launch flow (già presente nel codice, agganciarlo al catalog seedato).
  - UI Resource Mission entry point nel main menu.
- **Scope OUT**: bilanciamento pesi XP, crafting UI, PvP.
- **Deliverable**: 3 sistemi ATTIVI. Metrica: prime 10 gilde completano ≥1 raid e ≥1 resource mission nella prima settimana.
- **Stima**: 7-10 giorni.
- **Dipendenze**: R17.1 (perché player deve arrivare al mid-game per usare questi sistemi).

### R17.3 — Endgame & Class Depth (P1)
- **Obiettivo**: dare al player Lv10+ ragioni per continuare oltre la routine, e differenziare le classi.
- **Scope IN**:
  - Dungeon Lv15-20 (4-5 nuovi, endgame).
  - Item seed pass per bilanciare coverage classi (monk, warlock, alchemist).
  - Legendary Forge crafting attivato (recipes esistono in `legendary_recipe_catalog`).
  - Pagina statica "Guida Classi" in-app (14 pagine).
  - Skill/ability hint per classe (semplice testo iniziale).
  - Localization sweep IT residuo (R16.5.4f consolidato).
- **Scope OUT**: rebalancing Prestigio curve (rimandato a Round dedicato con telemetria post-R17.2).
- **Deliverable**: endgame reach + class depth + IT-completeness. Metrica: >20% delle gilde attive raggiunge Prestigio Lv8.
- **Stima**: 10-14 giorni.
- **Dipendenze**: R17.1, R17.2 attivi da almeno 2 settimane per telemetria.

---

## Risposta finale alla domanda del PM

> **"Quali 3 round dobbiamo fare adesso per trasformare lo scheletro in un gioco solido?"**

**R17.1 → R17.2 → R17.3, in questa sequenza.**

Motivazione sintetica in tre righe:
1. **R17.1** sblocca il "primo giorno" del player (oggi il 96% delle guilde non completa nulla). Senza R17.1, ogni altra feature è invisibile.
2. **R17.2** attiva i sistemi già scritti ma dormienti (achievements, raid, resource missions). Il gioco esiste già a livello di codice; questo round lo rende reale.
3. **R17.3** dà profondità al mid-late game e differenzia le classi. Solo dopo che R17.1 e R17.2 hanno generato telemetria, ha senso ottimizzare classi e curve.

**Bug critico trovato durante audit ma NON fixato (come da vincolo)**:
- `territory/services.py:53` KeyError 'library' → tracciato in R16.5.4e (backlog). Bloccante per pagina Territorio.

**Cosa NON è nell'audit** (esplicitamente):
- PvP, Stalla, World Boss, Continents avanzati, Monetizzazione, nuove feature.

**Fine audit R17.0.**
