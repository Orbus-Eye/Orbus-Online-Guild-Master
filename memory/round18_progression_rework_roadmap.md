# ROUND 18 — Progression Rework Roadmap (Working Document)

**Autore:** e1 main agent · **Data creazione:** 2026-07-04 · **Round trigger:** R18.1.1 PM directive
**Status doc:** DRAFT — soggetto a revisione R18.0b (Class Canon Audit)
**Scope:** roadmap + material decisionale · **NON è specifica implementativa**

---

## Indice

- [Sezione 1 — Onboarding avventurieri: nuova direzione](#s1)
- [Sezione 2 — 15 classi canoniche + Class Canon Audit R18.0b](#s2)
- [Sezione 3 — Talent tree stile RPG](#s3)
- [Sezione 4 — PWR solo da oggetti](#s4)
- [Sezione 5 — Livello max = 60 + 3 varianti curva XP](#s5)
- [Sezione 6 — Item power tier ogni 10 livelli (2 modelli)](#s6)
- [Sezione 7 — Item class-bound (roadmap 5 fasi)](#s7)
- [Sezione 8 — 100 dungeon + 20 raid: proposta distribuzione](#s8)
- [Sezione 9 — Progressione Grade Common→Legendary](#s9)
- [Sezione 10 — Tomi & Maestria di Classe](#s10)
- [Sezione 11 — Roster max 50 (già chiuso in R18.1)](#s11)
- [Sezione 12 — Dungeon/raid rework obbligatorio](#s12)
- [Roadmap Fasi R18 aggiornata](#roadmap-fasi)
- [Decisioni PM ancora aperte](#open-questions)

---

<a id="s1"></a>
## Sezione 1 — Onboarding avventurieri: nuova direzione

**Contesto:**
Con R18.4 (Grade + Class-Bound HARD) e R18.3 (Training Fields), la logica attuale di onboarding — dove ogni nuovo avventuriero riceve una classe random alla creazione — deve essere ripensata.

**Decisione PM (registrata 2026-07-04):**
- Ogni nuovo avventuriero parte come **Common + Recluta + non specializzato** (`grade=common`, `class_slug=recruit`, no talenti)
- La classe viene scelta dal player tramite un **campo di addestramento** (Training Field) — non è random
- La **prima scelta classe è gratuita**; retrain successivi hanno costo (da definire in R18.3)

**Opzioni implementative (per R18.3, non ora):**
- **Op-A**: Training Field come edificio di gilda (già esistono guild_structures) — riusa infrastruttura
- **Op-B**: Training Field come istanza globale, non attaccato a gilda — più semplice, meno lore
- **Op-C**: Training Field come flow narrativo one-shot alla creazione (tutorial in-game)

**Rischi:**
- Retrocompatibilità con adventurers già esistenti (recruit_unassigned già gestisce parziale)
- UX confusa per player early-game: "perché ho un adventurer senza classe?"
- Balance economico: quanto costa il retrain?

**D11 riaperta:**
La precedente D11 aveva sigillato: "random class + `is_recruit=true` per 24h + retrain gratis nel range". **PM: REOPENED** — la nuova direzione la sovrascrive parzialmente. Registrare come DECISION-PENDING per R18.3.

**Domande aperte al PM:**
1. Il Training Field è per-guild o globale?
2. Costo retrain (oro / oggetto / tempo)?
3. Come gestire retrocompatibilità sui 2125 adventurer esistenti (grade backfill già fatto in R18.1)?

---

<a id="s2"></a>
## Sezione 2 — 15 classi canoniche + Class Canon Audit R18.0b

**Contesto:**
Il PM ha comunicato target **15 classi canoniche** per il gioco maturo. Attualmente ce ne sono 14 nel catalog (`adventurer_classes` collection, esclusa `recruit_unassigned` tecnica).

L'audit R18.0 aveva mappato le classi ma **NON** aveva distinto tra canonical e sottoclasse/spec/ramo talento.

**Decisione PM (nuovo step di audit):**
Introdurre **R18.0b — Class Canon & Archetype Audit** (audit-only, read-only, no data write). Obiettivo:
1. Determinare quali delle 14 classi attuali sono **davvero canoniche**
2. Identificare classi che sono in realtà **sottoclassi/specializzazioni/rami talento**
3. Proporre 1-2 classi nuove per raggiungere 15 (senza scegliere)

**Esempio dal PM:** Mago vs Arcanista → Arcanista **probabilmente** è ramo talento del Mago, non classe canonica.

### Tabella template — Class Canon Audit R18.0b

**Da compilare in R18.0b, NON ora.** Righe placeholder per le 14 classi attuali:

| classe attuale | ruolo | primary_stat | secondary_stats | fantasia/archetipo | quanto è distinta | classe canonica? | ramo talento? | merge possibile? | rischio balance | note PM |
|---|---|---|---|---|---|---|---|---|---|---|
| warrior | Tank | strength | endurance | Guerriero classico | ALTA | ? | ? | ? | ? | ? |
| paladin | Tank/Support | strength/faith | endurance | Cavaliere sacro | ALTA | ? | ? | ? | ? | fusione Guardian già fatta R18.1 |
| ranger | DPS | agility | strength | Arciere/tracker | ALTA | ? | ? | ? | ? | ? |
| mage | DPS | intellect | ? | Mago classico | ALTA | ? | ? | ? | ? | ? |
| priest | Healer | faith | intellect | Sacerdote guaritore | ALTA | ? | ? | ? | ? | fusione Cleric già fatta R18.1 |
| rogue | DPS | agility | intellect | Ladro/assassino | ALTA | ? | ? | ? | ? | ? |
| warlock | DPS | intellect | faith | Stregone oscuro | MEDIA | ? | ramo mage? | ? | ? | pattern rune |
| bard | Support | intellect | agility | Bardo | MEDIA | ? | ramo priest? | ? | ? | ? |
| druid | Hybrid | intellect/faith | endurance | Druido | MEDIA | ? | ? | ? | ? | ? |
| monk | DPS | agility | endurance | Monaco marziale | MEDIA | ? | ? | ? | ? | ? |
| barbarian | DPS/Tank | strength | endurance | Barbaro | MEDIA | ? | ramo warrior? | ? | ? | ? |
| alchemist | Support | intellect | agility | Alchimista | BASSA | ? | ramo bard? | ? | ? | seed R160 |
| necromancer | DPS | intellect | faith | Necromante | MEDIA | ? | ramo warlock? | ? | ? | ? |
| berserker | DPS | strength | agility | Berserker | BASSA | ? | ramo barbarian? | ? | ? | ? |

**Nota:** questa tabella è un **placeholder scaffolding**. Le colonne "canonica?", "ramo talento?", "merge?" verranno compilate durante R18.0b dopo:
- Audit uso classi nei dungeon/raid attuali (utilizzo effettivo)
- Analisi ruoli coperti/scoperti (Tank / Healer / DPS / Support / Hybrid)
- Interviste PM/design lead

**NON IMPLEMENTARE ORA:** né rimozione classi, né aggiunta 15ª, né rebalance ruoli, né talent tree.

**Rischi:**
- Rimuovere classi "esistenti" = player identity loss → sempre migration soft con alias
- Aggiungere 15ª classe senza contenuto dedicato = ghost class

**Domande aperte al PM:**
4. Le 15 devono coprire 5 ruoli con 3 classi ciascuno (Tank/Healer/DPS/Support/Hybrid × 3)?
5. Merge/alias sono permessi in R18.0b (audit-only) o vanno delegati a R18.3?

---

<a id="s3"></a>
## Sezione 3 — Talent tree stile RPG

**Contesto:**
Schema scaffolding già pronto da R18.1 (`talent_tree_definitions`, `adventurer_talent_progress`, `career_history` — verificato da test_14/15).

**Vincoli di design (PM sigillati):**
- **3 rami** × **5 tier** × **4 talenti** = **60 slot / classe**
- **30 punti massimi** allocabili (metà slot)
- **Scopo talenti:**
  - Potenziare stat base (strength/agility/intellect/endurance/faith)
  - Orientare verso ruolo (Tank / Healer / DPS / Support / Hybrid)
  - Creare identità build (es. Mago-Fuoco vs Mago-Gelo vs Mago-Arcane)
  - Sbloccare abilità passive (chance crit, resist elem, aura, ecc.)

**NON DECIDERE ORA:**
- Nomi rami per ciascuna classe
- Bonus stat numerici (es. "+5 STR" o "+3% crit")
- Nomi talent slot
- UI completa (design agent gestirà in R18.2 UI)

**Roadmap:**
- **R18.2** — Talent Tree Engine + UI beta (gilde volontarie via `r18_beta_opt_in`)
  - Backend endpoint: `GET/POST /api/adventurers/{id}/talents`
  - UI: `/talents/:adventurerId` route protetta
  - Feature flag `R18_REWORK_ENABLED=false` NON serve per il beta gate (usa `r18_beta_opt_in`)
- **R18.2+**: seed talent tree per 3 classi pilota (candidati: warrior/mage/priest — coprono Tank/DPS/Healer)

**Rischi:**
- Balance: 30 punti su 60 slot = molte permutation → hell tuning
- Player choice paralysis se troppi rami/tier
- Retroattività: cosa succede ai talenti quando cambia il livello classe?

**Domande aperte al PM:**
6. I punti talento crescono col **livello avventuriero** (1 punto/lvl) o col **livello classe** (nuovo concetto, sez. 10)?
7. Respec possibile? Costo?

---

<a id="s4"></a>
## Sezione 4 — PWR solo da oggetti

**Contesto:**
Attualmente il PWR di un adventurer è somma di:
- Stat base (strength/agility/intellect/endurance/faith)
- Equipment (weapon + armor + accessory)
- Bonus specialization
- Bonus traits

**Decisione PM (registrata):**
- PWR = **solo equipment power**
- Stat base possono crescere via: livello avventuriero, maestria classe, talenti, grade, tratti → **ma NON aumentano PWR**

**Motivazione:**
- Item progression più chiara
- Player capisce "sale PWR → nuovo item"
- Level up = crescita stat base per uso nei calcoli combat/damage (non PWR display)

**Registrare come:** **R18.5 — PWR Solo-Equip + XP Curve + Item Tier Rework**

**NON IMPLEMENTARE ORA. NON MODIFICARE FORMULA `total_power` IN R18.1.1.**

**Rischi:**
- Se PWR è solo equip, che valore ha un adv lvl 60 senza equipment? Zero PWR → invisible in ranking?
- Serve rivedere `power_score` in tutti gli item (100 dungeon × 3-5 item ≈ 300+ item da rebalancing)
- Impact su algoritmi matchmaking PvP, dungeon threshold, raid gate

**Domande aperte al PM:**
8. Naked adventurer PWR = 0 o minimum 1?
9. PWR incorpora talenti (che boostano equip effect) o è pure gear score?

---

<a id="s5"></a>
## Sezione 5 — Livello max = 60 + 3 varianti curva XP

**Contesto:**
Target lvl cap **60** (attualmente 30). Il PM chiede che:
- Lv 1-30 sia **rapida** (onboarding, feel-good progression)
- Lv 31-60 sia **sempre più difficile** (endgame long-tail)

### Modello formula base
`xp_required(lvl) = base * lvl^exponent + linear_step * lvl`

Con 3 varianti:

### Variante A — Casual
- `base=50, exponent=1.5, linear_step=25`
- xp(30) ≈ 8'950 · xp(60) ≈ 24'800
- **Cumul Lv1→30:** ≈ 90k xp
- **Cumul Lv30→60:** ≈ 250k xp
- **Ratio 30-60/1-30:** ~2.8×
- **Tempo Lv1→30 con dungeon medio (500 xp/run):** ~180 run
- **Tempo Lv30→60:** ~500 run
- **Grind:** BASSO
- **Rischio power creep:** ALTO (endgame veloce)

### Variante B — Standard (default proposto)
- `base=100, exponent=1.8, linear_step=50`
- xp(30) ≈ 25'800 · xp(60) ≈ 76'400
- **Cumul Lv1→30:** ≈ 280k xp
- **Cumul Lv30→60:** ≈ 1.15M xp
- **Ratio 30-60/1-30:** ~4.1×
- **Tempo Lv1→30 con dungeon medio (700 xp/run):** ~400 run
- **Tempo Lv30→60:** ~1'600 run
- **Grind:** MEDIO
- **Rischio power creep:** MEDIO

### Variante C — Hardcore
- `base=200, exponent=2.1, linear_step=100`
- xp(30) ≈ 88'900 · xp(60) ≈ 305'000
- **Cumul Lv1→30:** ≈ 950k xp
- **Cumul Lv30→60:** ≈ 4.5M xp
- **Ratio 30-60/1-30:** ~4.7×
- **Tempo Lv1→30 con dungeon medio (900 xp/run):** ~1'000 run
- **Tempo Lv30→60:** ~5'000 run
- **Grind:** ALTO
- **Rischio power creep:** BASSO (long-tail estrema)

### Impatto item progression
- Var-A: 6 tier item (1 ogni 10 lvl) forse eccessivi (giocatore corre da tier 3 a tier 6 rapidamente)
- Var-B: 6 tier bilanciati, endgame gear = obiettivo raggiungibile
- Var-C: 6 tier troppo lenti — servono 3 tier ogni 20 lvl?

**NON APPLICARE.** Solo proposta.

**Domande aperte al PM:**
10. Variante preferita? A/B/C? (default suggerito: B)
11. La curva XP è per adventurer o esiste anche un "class level" separato (sez. 10)?

---

<a id="s6"></a>
## Sezione 6 — Item power tier ogni 10 livelli (2 modelli)

**Contesto:**
100 dungeon + 20 raid × Lv 1-60 → serve struttura item tier.

### Modello A — Bracket-based (6 tier)
Fasce di livello coperte:

| Tier | Livelli | Power range | Rarity primaria | Slot coperti | Rischio power creep |
|---|---|---|---|---|---|
| T1 | 1-10 | 1-20 | Common | weapon, armor | BASSO |
| T2 | 11-20 | 21-45 | Common, Uncommon | + accessory | BASSO |
| T3 | 21-30 | 46-80 | Uncommon, Rare | full | MEDIO |
| T4 | 31-40 | 81-130 | Rare | full + set piece | MEDIO |
| T5 | 41-50 | 131-200 | Rare, Epic | full + set | ALTO |
| T6 | 51-60 | 201-300 | Epic, Legendary | full + set + trinket | ALTO |

**Pro:** semplice mental model, coerente col Lv cap 60
**Contro:** salti bruschi a Lv 11/21/31 → un item T1 obsoleto istantaneamente

### Modello B — Breakpoint-based (7 breakpoint)
Item **rilasciati** a livelli chiave, senza fascia:

| Breakpoint | Lvl min | Power target | Rarity | Slot coperti |
|---|---|---|---|---|
| BP1 | 1 | 5 | Common | weapon, armor |
| BP2 | 10 | 25 | Common | + accessory |
| BP3 | 20 | 60 | Uncommon | full |
| BP4 | 30 | 110 | Rare | full |
| BP5 | 40 | 170 | Rare/Epic | + trinket |
| BP6 | 50 | 240 | Epic | + set piece |
| BP7 | 60 | 320 | Legendary | full + set + trinket |

**Pro:** curva continua tra breakpoint (item scala con lvl), no cliff-drops
**Contro:** più difficile spiegare al player, richiede power interpolation

**Relazione con dungeon/raid (proposta):**
- Ogni breakpoint/tier = 15-20 dungeon dedicati
- 1-3 raid per breakpoint (BP4+ have raid)

**NON IMPLEMENTARE.** Solo proposta.

**Domande aperte al PM:**
12. Modello A o B?
13. Legendary solo BP7 (Lv60) o disponibile earlier con requirement grade?

---

<a id="s7"></a>
## Sezione 7 — Item class-bound (roadmap 5 fasi)

**Contesto:**
Item attualmente non hanno restrizione di classe (`recommended_classes` field è opzionale, non enforced).

**Roadmap 5 fasi (R18.4):**

### Fase 1 — Warning SOFT (R18.4 P0)
- Field `recommended_classes: list[str]` sui doc `items` (già esistente, non enforced)
- UI mostra warning giallo se player equip off-class: "⚠️ Item non ottimizzato per questa classe"
- **Nessun blocco backend.** Nessun malus stat.

### Fase 2 — Audit migration (R18.4 P1)
- Script read-only: scannerizza `equipped_items` + verifica `class_slug` adv vs `recommended_classes` item
- Report: N adventurers con equip off-class (baseline)
- Grandfathering preview: cosa succederebbe con enforcement

### Fase 3 — HARD block (R18.4 P2)
- Backend enforce su `POST /adventurers/{id}/equip`
- 400 se `class_slug` non in `item.recommended_classes` (e non `null`)
- User message IT esplicito
- **Grandfathered** adventurers con equip pre-esistente off-class: no auto-unequip, ma no re-equip possibile

### Fase 4 — Smart loot (R18.5+)
- Drop table pesa presenza classi in party
- Es. 3-p party con 2 mage + 1 warrior → più drop intellect-item
- Algoritmo weighted random su `party_class_composition`

### Fase 5 — Auto-equip class-aware (R18.5+)
- `POST /adventurers/{id}/auto-equip` rispetta class-bound
- Se nessun item disponibile per la classe → mantiene attuale (grandfathered)

**Set di classe (item_sets):**
- **FUTURI** (R18.6+). Definire bonus set-2 e set-4 per ogni classe canonica.
- **NON progettare ora.**

**NON FARE HARD SWITCH ORA.**

**Rischi:**
- Migrazione: 2125 adventurers × 3 slot = ~6000 equipped_items da audit
- UX: player frustration se un item "buono trovato" non è equipaggiabile
- Balance: se class-bound HARD è troppo stretto, riduce build diversity

**Domande aperte al PM:**
14. Fase 3 (HARD) è opt-in per beta gilde prima del rilascio globale?
15. Item legacy senza `recommended_classes` → considerati universali (nessun blocco) o forzati "warrior-only" per default?

---

<a id="s8"></a>
## Sezione 8 — 100 dungeon + 20 raid: proposta distribuzione

**Contesto:**
Attualmente: **23 dungeon** attivi, **3 raid**. Target: **100 dungeon**, **20 raid**.

### Dungeon — Proposta distribuzione (100 target)

| Fascia lvl | Team size dominante | # dungeon | Rarity drop | Tier item | Note |
|---|---|---|---|---|---|
| 1-10 | 3-p | 20 | Common | T1-T2 | onboarding, ~2 tomi lore |
| 11-20 | 3-p + 5-p | 15 (10×3-p, 5×5-p) | Common/Uncommon | T2 | prima team composition |
| 21-30 | 5-p (dominant) | 15 | Uncommon/Rare | T3 | prime raid unlock |
| 31-40 | 5-p + 7-p | 15 (10×5-p, 5×7-p) | Rare | T4 | mid-game peak |
| 41-50 | 7-p | 15 | Rare/Epic | T5 | endgame prep |
| 51-60 | 7-p + elite | 20 (15×7-p, 5×elite) | Epic/Legendary | T6 | endgame + legendary path |

**Party size distribution (100 dungeon):**
- 3-player: 30 dungeon
- 5-player: 40 dungeon
- 7-player: 25 dungeon
- Elite (soloable or scaling): 5 dungeon

### Raid — Proposta distribuzione (20 target)

| Fascia lvl | Team size | # raid | Item tier | Rarity | Note |
|---|---|---|---|---|---|
| 25-30 | 10-p | 3 | T3 | Rare | primi raid, soft intro |
| 31-40 | 10-p + 15-p | 5 (3×10, 2×15) | T4 | Rare/Epic | main content |
| 41-50 | 15-p + 20-p | 6 (3×15, 3×20) | T5 | Epic | mid-endgame |
| 51-60 | 20-p + 40-p | 6 (3×20, 3×40) | T6 | Epic/Legendary | endgame chase |

**Party size distribution (20 raid):**
- 10-player: 6 raid
- 15-player: 5 raid
- 20-player: 6 raid
- 40-player (world boss): 3 raid

**Reward relation:**
- Ogni raid ≥ Lv 40 può droppare Tomi Maestria (sez. 10)
- Raid 40-p (world boss) ha probabilità Legendary drop
- Class-bound drop attivo (sez. 7)
- Grade progression contribution (sez. 9): ogni raid completato "valido" conta

**NON CREARE CONTENUTI.** Solo modello.

**Rischi:**
- Content production: 100 dungeon × ~5 balance parameters + name + lore + drop table = ~500 doc catalog
- Test coverage: ogni dungeon deve avere balance monte carlo
- Team size 40-p: infrastruttura raid multi-guild? Cross-guild party?

**Domande aperte al PM:**
16. Raid 40-p sono world-boss stile (multi-guild, tempo limitato) o guild-only (single-guild pool)?
17. Distribuzione 3-p/5-p/7-p accettabile o si preferisce peso diverso?

---

<a id="s9"></a>
## Sezione 9 — Progressione Grade Common→Legendary

**Contesto:**
Grade è stato scaffolded in R18.1 (`grade='common'` backfilled su tutti i 2125 adventurers). R18.4 introdurrà la progressione.

**Soglie richieste PM (livello di difficoltà):**

| Grade | Difficoltà upgrade | % adventurers stimata attesa (endgame) |
|---|---|---|
| Common | (start) | 100% |
| Common → Uncommon | facile | ~60% |
| Uncommon → Rare | difficile | ~20% |
| Rare → Epic | molto difficile | ~5% |
| Epic → Legendary | dedicazione estrema | ~0.5% |

**Requirement Legendary (PM sigillato):**
- **≥ 100 raid validi**
- **≥ 1000 dungeon validi**
- Livello adv **≥ 55** (proposta, PM confermi)
- Oggetti/materiali speciali (Tomi Legendary, essenze, ecc.)

### Definizione "valido" — 3 criteri anti-farm proposti

**Criterio 1 — Level bracket** (proposto default):
- Dungeon valido: `dungeon.required_level ∈ [adv.level - 5, adv.level + 10]`
- Es. adv Lv 50 in dungeon Lv 45-60 → conta; in dungeon Lv 20 → non conta

**Criterio 2 — Contribution real** (per raid):
- Raid valido solo se `adventurer.contribution >= threshold`
- Threshold: es. 5% del damage totale party, o 3+ ability usate, o 30+ min real time

**Criterio 3 — Fascia adv/dungeon "utile"** (proposto default):
- Dungeon valido: rewards `grade_progression_points > 0` (dungeon low-level danno 0 punti per adv high-level)
- Vantaggio: implicito via reward table, no state machine complessa

**Combinazione proposta:** applicare **Criterio 1 + Criterio 3** su dungeon, **Criterio 2** su raid.

**NON IMPLEMENTARE.** Solo proposta.

**Rischi:**
- **Farm risk:** senza anti-farm, player alt-farm dungeon low → Legendary in 2 settimane
- **Grind risk:** 1000 dungeon × 30 min = 500 ore reali → alienazione casual
- **Esclusività:** 0.5% Legendary = target ok, ma serve NON generare frustrazione (visibilità pubblica del progress)
- **Casual alienation:** un player casual non arriverà mai a Legendary → dev'essere accettato o compensato con reward intermedie

**Domande aperte al PM:**
18. Level bracket window (proposto -5/+10) è la finestra corretta o va allargata/stretta?
19. Contribution threshold per raid valido: 5% damage o metrica diversa?
20. Legendary è cosmetic-only (badge visibile) o dà bonus stat/PWR?

---

<a id="s10"></a>
## Sezione 10 — Tomi & Maestria di Classe

**Contesto:**
Nuovo sistema di progressione **parallelo** al livello avventuriero, focus sul mastering della classe.

**Modello (PM sigillato):**

### Tomi
- **Tomi della Conoscenza** — sblocco talenti / punti talento base
- **Tomi della Maestria** — sblocco tier avanzati talent tree (t3-t5)
- Drop da dungeon high-lvl + raid + shop (in R18.6+)

### Livello di Classe (nuovo concetto)
- **Separato** dal livello avventuriero
- Cresce quando l'adv completa attività **usando la propria classe** (dungeon-run count con class-matched drop, o metrica simile)
- Max class level: proposta **10** (allineato con 5 tier talenti × 2)

### Ogni class level up dà:
- 1 punto talento (extra al pool base)
- Piccolo bump stat base (es. +1 primary_stat)
- Sblocco graduale ability class-locked
- Aiuto ruolo (es. Tank guadagna endurance passiva)

### Full class mastery richiede:
- Livello adventurer minimo (proposta: Lv 40)
- N Tomi Conoscenza consumati
- N Tomi Maestria consumati
- M dungeon completati class-matched
- Oggetti speciali (materiali crafting classe-specifici)

**NON IMPLEMENTARE DROP TOMI. NON CREARE TOMI. Solo roadmap.**

**Rischi:**
- Complessità: player deve capire adv level vs class level vs grade vs talent points
- UI overload: dashboard adventurer già dense
- Balance: class level ambigua → matching dungeon class-mismatch

**Domande aperte al PM:**
21. Class level ha reset se player cambia classe? (retrain sez. 1)
22. Tomi sono tradeable (market) o bound-on-pickup?

---

<a id="s11"></a>
## Sezione 11 — Roster max 50 (già chiuso in R18.1 + R18.1.1)

**Contesto:**
Cap roster **50** è il target endgame confermato PM.

**Formula finale (R18.1.1 sigillata):**
```
effective_level = max(guild.level or 0, guild.guild_level or 0, 1)
max_roster_cap  = min(50, 10 + effective_level * 2)
```

**Stato attuale (post R18.1.1 hotfix):**
- 303/303 guilds hanno cap computed
- 7 guilds grandfathered (roster > cap): 6 R5 test data + Test Admin Guild
- La Lanterna di Ferro (real player kyrie.shepard): cap 22 → **40** (fixato)
- Nessun blocco HARD attivo (SOFT enforce, feature flag OFF)

**Rivalutare più avanti:**
- Il field `guild_level` è legacy (pre-R18)? Se sì, sostituire con "prestige level" o "guild rank" in R18.7?
- Nuovo livello gilda R18 potrebbe superare 20 → cap sempre 50 (min clamp)

**NULLA DA IMPLEMENTARE.** Verificato in R18.1.1.

---

<a id="s12"></a>
## Sezione 12 — Dungeon/raid rework obbligatorio (R18.6 / R18.7)

**Contesto:**
La combinazione di:
- Lv cap 60 (era 30)
- 100 dungeon target (erano 23)
- 20 raid target (erano 3)
- Item tier ogni 10 lvl (nuovi 6 tier)
- Class-bound drop
- Grade progression con "valido" anti-farm
- PWR solo-equip
- Smart loot

→ obbliga a un **rework completo** dei 23 dungeon esistenti + 3 raid.

**Scope R18.6 (Content Rebalance Plan, audit-only):**
1. Audit 23 dungeon attuali → mappare su nuovo tier system
2. Rebalance drop table per class-bound
3. Rebalance PWR requirement per T1-T3 (le fasce basse)
4. Migration path: dungeon completed da player esistenti → contano per grade?

**Scope R18.7 (Large Content Expansion):**
1. Design 77 nuovi dungeon (100 - 23)
2. Design 17 nuovi raid (20 - 3)
3. XP curve nuova (variante A/B/C — sez. 5)
4. Item tier nuovi (modello A/B — sez. 6)
5. Smart loot algoritmo
6. Grade requirement seeding

**NON IMPLEMENTARE. Solo roadmap.**

**Rischi:**
- Content bottleneck: 77 dungeon × 1 dev-week = 1.5 anni-dev = fuori scope per team piccolo
- Automated content? LLM-assisted dungeon generator?
- Balance regression: 23 dungeon attuali migrati male → break player esistenti

**Domande aperte al PM:**
23. R18.7 = full team focus o parallel track?
24. Content generation automatizzata (LLM) accettabile per dungeon "filler" bassi tier?

---

<a id="roadmap-fasi"></a>
## Roadmap Fasi R18 aggiornata

| Fase | Nome | Status | Scope key |
|---|---|---|---|
| **R18.1** | Schema Foundation & Backfill | ✅ CLOSED (post R18.1.1) | Feature flag, orphans, grade, roster cap |
| **R18.1.1** | Safety Hotfix + Roadmap Expansion | ✅ IN PROGRESS | Canonical cap formula + recruit_unassigned guard + this doc |
| **R18.0b** | Class Canon & Archetype Audit | 🔜 PENDING (audit-only) | Compilare tabella sez.2, decidere 15 classi |
| **R18.2** | Talent Tree Engine Schema + Beta | ⏸ WAITING R18.0b | Endpoint API + UI beta gate (no talenti reali) |
| **R18.3** | Training Fields + Class Choice + Class Mastery/Tomes | ⏸ WAITING R18.2 | Recruit path, class level, tomi drop |
| **R18.4** | Grade System + Class-Bound Soft/Hard Migration | ⏸ WAITING R18.3 | 5 fasi item class-bound (sez.7) + grade thresholds |
| **R18.5** | PWR Solo-Equip + XP Curve + Item Tier Rework | ⏸ WAITING R18.4 | Var A/B/C curva, modello A/B tier, PWR-only-equip |
| **R18.6** | Dungeon/Raid Content Rebalance Plan | ⏸ AUDIT-ONLY | Audit 23 dungeon + 3 raid esistenti |
| **R18.7** | Large Content Expansion: 100 Dungeon / 20 Raid | ⏸ HEAVY LIFT | 77 dungeon + 17 raid nuovi |

**Nota importante:** questa sequenza è **modificabile** dal Class Canon Audit R18.0b. Se emergono constraint imprevisti (es. 3 classi da fondere), potrebbe servire un R18.2.5 di ristrutturazione talent tree schema.

---

<a id="open-questions"></a>
## Decisioni PM ancora aperte (numerate)

Lista pool di 24 domande sparse nel documento, ordinate per priorità:

### P0 — blocking prima di R18.0b/R18.2
1. **[Sez.1 D11 REOPENED]** Retrain gratuito o a costo? Training Field per-guild o globale?
2. **[Sez.2]** Le 15 classi devono coprire 5 ruoli × 3 classi ciascuno?
3. **[Sez.2]** Merge/alias sono permessi in R18.0b o vanno delegati a R18.3?
4. **[Sez.3]** Punti talento crescono col livello avventuriero o col livello classe (nuovo)?
5. **[Sez.5]** Variante curva XP preferita? A/B/C? (default suggerito: B)

### P1 — blocking prima di R18.4/R18.5
6. **[Sez.4]** Naked adventurer PWR = 0 o min 1?
7. **[Sez.4]** PWR incorpora talenti o è pure gear score?
8. **[Sez.5]** Class level è separato dal livello adv?
9. **[Sez.6]** Modello A (bracket 6 tier) o B (breakpoint 7)?
10. **[Sez.6]** Legendary solo BP7 o disponibile earlier con requirement grade?
11. **[Sez.7]** Fase 3 (HARD class-bound) opt-in beta prima di rilascio globale?
12. **[Sez.7]** Item legacy senza `recommended_classes` → universali o warrior-only default?

### P2 — blocking prima di R18.6/R18.7
13. **[Sez.8]** Raid 40-p world-boss multi-guild o guild-only?
14. **[Sez.8]** Distribuzione 3/5/7-p accettabile?
15. **[Sez.9]** Level bracket window (-5/+10) è corretta?
16. **[Sez.9]** Contribution threshold raid valido (5% damage)?
17. **[Sez.9]** Legendary è cosmetic-only o dà bonus stat/PWR?
18. **[Sez.10]** Class level resetta a retrain classe?
19. **[Sez.10]** Tomi tradeable o bound-on-pickup?

### P3 — long-term
20. **[Sez.1]** Come gestire retrocompatibilità sui 2125 adv esistenti?
21. **[Sez.3]** Respec talenti possibile? Costo?
22. **[Sez.12]** R18.7 = full team focus o parallel track?
23. **[Sez.12]** Content generation automatizzata (LLM) accettabile per dungeon filler?
24. **[Sez.2 tabella]** 1-2 classi nuove per raggiungere 15 (candidate?)

---

## Raccomandazione prossimo step

**Suggerimento: R18.0b (Class Canon Audit) PRIMA di R18.2.**

**Motivazione:**
1. La struttura talent tree in R18.2 (60 slot/classe × 15 classi = 900 slot totali) dipende dal N esatto di classi canoniche
2. Se emerge che 3 classi attuali sono in realtà rami talento, R18.2 va progettato con quello constraint
3. R18.0b è **audit-only** → 1-2 giorni di lavoro, sblocca decisioni P0 (5 domande) + P1 (7 domande)
4. R18.2 partirebbe con brief consolidato invece di rework mid-flight

**Alternative:**
- **R18.2 diretto:** rischio di dover rimappare talent tree se Class Canon rivela merge. -50% velocità globale.
- **R18.2 parallelo a R18.0b:** possibile solo se il team è ≥ 2 dev. Con team singolo → sequential.

**Prossimo brief PM richiesto:**
> "R18.0b — Class Canon & Archetype Audit. Scope: read-only audit sulle 14 classi attuali. Deliverable: tabella sez.2 compilata + proposta merge/alias/keep per ogni classe + candidate 1-2 nuove classi. Zero data write, zero UI change."

---

**Firmato:** e1 main agent · 2026-07-04 · R18.1.1 Roadmap Expansion (working document)
