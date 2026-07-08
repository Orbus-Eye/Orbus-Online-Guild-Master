# R18.6 · Class Halls · Classless Start · Adventurer Identity — Design Documentale

**Round**: R18.6 (dedicated PM design, differito da C5 Q6 e planned in C6 handoff)
**Locked at (UTC)**: 2026-07-08T15:00:00Z
**Authority**: PM Orchestrator — R18.6 GO esplicito post-Phase C ACK
**Regime**: **DOCUMENTAL ONLY** — 13 sezioni scope. **NO code · NO DB · NO migrations · NO Class Halls implementation · NO UI code · NO runtime enforcement · NO class_slug migration apply · NO Apply Phase · NO R18.5 modification (LOCKED) · NO R18.3f auto-start**.

---

## Sezione 1 · Executive Summary

Ogni **nuovo avventuriero** in Orbus Online nasce come **`Senza Classe / Recluta`** (`recruit_unassigned`): esiste nel roster della gilda, riceve un'identità narrativa base, ma **non è ancora un membro operativo pieno**. Prima di essere schierato in dungeon/raid o di poter equipaggiare gear specializzato deve **scegliere una Sala di Classe** presso il Complesso della Gilda: la scelta consacra l'avventuriero come **Guerriero · Ladro · Mago · Paladino · Cacciatore di Mostri**.

**Cinque Sale di Classe live** (una per classe canonica R18.5). Ogni Sala determina in blocco: `main_stat`, `armor proficiency`, `weapon proficiency`, `class_proficiency` (legacy label per registry runtime v1), `canonical_class_slug` (target R18.3f). L'assegnazione è **irreversibile in fase live** (con eventuale future "Rite of Rebirth" documentato nelle open questions PM).

Il design è **coerente con R18.5 LOCKED**: usa esattamente il lock_state matrix C2 (10 stati) e i campi Registry v2 (23 fields) senza modificarli. R18.6 non attiva runtime, non popola `class_slug` in DB, non crea items, non modifica il catalogo 1500 — è un **layer di design UI/UX + governance** che verrà applicato solo dopo R18.3f (Class Slug Migration Readiness) + Apply Phase.

**Regola gameplay PM (verbatim)**:
- Nuovo avventuriero → Senza Classe / Recluta
- Scelta Sala → Assegnazione classe
- Classe → main stat + armor proficiency + weapon proficiency + equip eligibility + identità gameplay

**Regola classless (verbatim)**:
- ✅ Può esistere nel roster · ✅ Può essere visualizzato · ✅ Può ricevere tutorial/prompt
- ❌ NON può equipaggiare gear specializzato · ❌ NON può essere mandato normalmente in dungeon/raid · ❌ NON deve ricevere `class_slug` auto-derivato
- ⚙️ Deve scegliere una Sala di Classe per sbloccarsi

---

## Sezione 2 · Stato iniziale avventuriero classless / recruit_unassigned

### 2.1 · Campi adventurer al `recruit_unassigned`

| Campo | Valore init | Note |
|---|---|---|
| `adventurer_id` | UUID generato | invariato da R18.5 |
| `nome` | assegnato via generator narrativo | uniforme con roster corrente |
| `level` | 1 | invariato |
| `class_proficiency` | `null` | **NON** popolato auto (regola PM) |
| `class_slug` | `null` | **NON** popolato auto (bridge R18.3f) |
| `class_hall_assigned_at` | `null` | nuovo campo documentale (attivazione R18.3f/Apply) |
| `class_hall_id` | `null` | id della Sala scelta (documentale) |
| `hall_master_witness_npc` | `null` | popolato post-scelta (narrative marker) |
| `recruit_status` | `"recruit_unassigned"` | enum documentale, live in Apply |
| `narrative_intro_shown` | `false` → `true` dopo tutorial | onboarding tracker |

**NB**: questi campi sono **design layer**. In Registry v2 il campo `class_slug_resolution_status='deferred_to_r18_3f'` copre già la nullabilità per gli item. Su `adventurer` il handling live richiede R18.3f + Apply Phase.

### 2.2 · Regola PM su auto-derive

**NO auto-bridge** da `class_proficiency` → `class_slug` (C2 regola PM). Se `class_proficiency` è popolato ma `class_slug` è null, il lock_state resta `locked_class_slug_null` (C2 #4), non `locked_recruit_unassigned` (C2 #3). Sono due stati distinti, entrambi validi.

### 2.3 · Capacità del Recluta (whitelist esplicita)

| Azione | Ammesso | Motivazione |
|---|:---:|---|
| Comparire nel roster | ✅ | esistenza narrativa base |
| Ricevere nome/livello iniziale | ✅ | onboarding di base |
| Ricevere tutorial/prompt | ✅ | necessario per guidare la scelta di Sala |
| Ricevere quest tutorial "assegna Sala di Classe" | ✅ | driver del funnel R18.6 |
| Equipaggiare consumable/material/cosmetic | ✅ (via `universal_allowed` C2 #5) | bypass proficiency, senza gameplay impact |
| Equipaggiare gear specializzato (armor_type/weapon_family) | ❌ | `locked_recruit_unassigned` (C2 #3) |
| Essere assegnato a dungeon/raid regolare | ❌ | filtro roster dungeon (design R18.6) |
| Essere assegnato a "Prova di Sala" (encounter tutorial pre-scelta) | ✅ | scripted encounter safe-mode, no reward gear |
| Essere venduto / dismesso / trasferito | ⚙️ da confermare PM (Q3) | pending PM decision |
| Ricevere XP passivo (idle tick) | ⚙️ da confermare PM (Q4) | pending PM decision |

---

## Sezione 3 · Class Halls Design (5 Sale)

Ogni Sala è un **luogo narrativo permanente nel Complesso della Gilda** (non un building temporaneo), con un `hall_master` NPC dedicato e un rito di consacrazione. Il layout resta **testuale minimalista** coerente con il tone Orbus (MMO gestionale testuale).

### 3.1 · Sala del Guerriero — *Fortezza d'Acciaio*

- **canonical_class_slug**: `guerriero` · **canonical_class_name_it**: Guerriero · **legacy_class_label**: Warrior
- **main_stat**: **Forza**
- **armor**: maglia · piastre
- **weapon**: spada · ascia · martello · scudo · lancia · arma_in_asta
- **hall_master NPC (documentale)**: `Comandante Aldric del Ferro`
- **posizione narrativa**: ala nord del Complesso, adiacente all'armeria — rumore di incudini e ordini gridati
- **lore hook**: "L'acciaio non si spezza. Si tempra." — motto della Fortezza
- **unlock rite**: la Prova del Peso — il Recluta solleva l'ascia rituale e riceve il **Sigillo del Ferro**
- **narrative micro-log post-scelta**: "*{nome} ha giurato fedeltà alla Fortezza d'Acciaio. Da oggi è un Guerriero.*"

### 3.2 · Sala del Ladro — *Loggia dei Sussurri*

- **canonical_class_slug**: `ladro` · **canonical_class_name_it**: Ladro · **legacy_class_label**: Rogue
- **main_stat**: **Destrezza**
- **armor**: cuoio
- **weapon**: pugnale · spada · balestra
- **hall_master NPC (documentale)**: `Maestra dei Sussurri Selene`
- **posizione narrativa**: sottoscala del Complesso, corridoi di legno scuro senza torce — solo candele
- **lore hook**: "L'ombra è alleata. Il rumore è nemico." — motto della Loggia
- **unlock rite**: la Prova del Silenzio — il Recluta attraversa la Sala Buia senza far cadere il campanello — riceve il **Marchio della Loggia**
- **narrative micro-log post-scelta**: "*{nome} ha attraversato la Sala Buia. Da oggi è un Ladro.*"

### 3.3 · Sala del Mago — *Circolo dei Nove Sigilli*

- **canonical_class_slug**: `mago` · **canonical_class_name_it**: Mago · **legacy_class_label**: Mage
- **main_stat**: **Intelligenza**
- **armor**: stoffa
- **weapon**: bastone · tomo · focus · pugnale
- **hall_master NPC (documentale)**: `Arcimago Vessel di Memoria`
- **posizione narrativa**: torre superiore, biblioteca a spirale, candele arcane sospese
- **lore hook**: "Ogni parola letta è una parola scagliata." — motto del Circolo
- **unlock rite**: il Rito dei Nove Sigilli — il Recluta traccia il proprio sigillo personale su pergamena vergine e riceve la **Chiave dei Nove**
- **narrative micro-log post-scelta**: "*{nome} ha tracciato il proprio sigillo. Da oggi è un Mago.*"

### 3.4 · Sala del Paladino — *Reliquiario della Luce Fissa*

- **canonical_class_slug**: `paladino` · **canonical_class_name_it**: **Paladino** ⚠️ *(NON priest/prete)* · **legacy_class_label**: Priest
- **main_stat**: **Saggezza**
- **armor**: stoffa
- **weapon**: bastone · martello · focus · reliquia
- **hall_master NPC (documentale)**: `Custode Isabeau dell'Alba`
- **posizione narrativa**: cappella nella corte interna, vetrate ambrate, brace sempre accesa nell'altare
- **lore hook**: "La luce non chiede. La luce impone." — motto del Reliquiario
- **unlock rite**: la Veglia della Brace — il Recluta veglia la brace per una notte, alla prima luce dell'alba riceve il **Reliquiario Personale**
- **narrative micro-log post-scelta**: "*{nome} ha vegliato la brace fino all'alba. Da oggi è un Paladino.*"
- ⚠️ **Nota terminologica critica**: nel worldbuilding Orbus la classe **NON è** "prete" né "priest". L'UI, i log, i tutorial e i tooltip devono usare esclusivamente **Paladino** (nome IT) o `paladino` (canonical slug).

### 3.5 · Sala del Cacciatore di Mostri — *Capanno del Sentiero Selvaggio*

- **canonical_class_slug**: `cacciatore_di_mostri` · **canonical_class_name_it**: **Cacciatore di Mostri** *(underscore composto nello slug)* · **legacy_class_label**: Ranger
- **main_stat**: **Destrezza**
- **armor**: cuoio · maglia
- **weapon**: arco · balestra · spada · pugnale · lancia
- **hall_master NPC (documentale)**: `Vecchio Falconiere Ovyr`
- **posizione narrativa**: capanno di legno grezzo sul limite del bosco della Gilda, trofei alle pareti, focolare aperto
- **lore hook**: "La bestia è vecchia. Il cacciatore, di più." — motto del Capanno
- **unlock rite**: la Traccia del Primo Passo — il Recluta segue la traccia notturna di un cinghiale-fantasma fino all'alba e riceve la **Faretra del Sentiero**
- **narrative micro-log post-scelta**: "*{nome} ha seguito la traccia fino all'alba. Da oggi è un Cacciatore di Mostri.*"
- ⚠️ **Nota terminologica critica**: nel worldbuilding Orbus la classe **NON è** "ranger" né "cacciatore" da solo. L'UI, i log, i tutorial e i tooltip devono usare esclusivamente **Cacciatore di Mostri** (nome IT) o `cacciatore_di_mostri` (canonical slug, con underscore).

---

## Sezione 4 · Flusso Scelta Classe (onboarding → modal → conferma → lock)

### 4.1 · Trigger del funnel

Il funnel si attiva quando entrambe le condizioni sono vere sull'avventuriero:

```
adventurer.class_slug IS NULL
AND adventurer.class_proficiency IS NULL
AND adventurer.recruit_status = "recruit_unassigned"
```

Corrisponde al lock_state C2 **#3 `locked_recruit_unassigned`**.

### 4.2 · Sequenza player-facing (7 step)

1. **Onboarding banner** sul dashboard della Gilda (dopo il primo reclutamento di un Recluta).
2. **Roster badge** persistente su ogni Recluta (`ambra · icona porta`, coerente con lock_state UI badge C2).
3. **Tap sul badge** o sulla riga del Recluta → apre la scheda avventuriero con **CTA "Assegna Sala di Classe"**.
4. **Modal "Le 5 Sale"**: lista testuale delle 5 Sale con `main_stat` + `armor` + `weapon` + hall_master name + lore hook (una riga per Sala).
5. **Preview Sala**: tap su una Sala → apre il dettaglio (rito di consacrazione, elenco proficiency completo, un tooltip di riepilogo).
6. **Conferma "Consacra {nome} come {classe}"** con dialogo di conferma esplicita (checkbox "Ho letto e confermo. La scelta è definitiva.").
7. **Post-conferma**: narrative micro-log della Sala scelta appare nel log della Gilda; il Recluta assume il `canonical_class_slug` e la `class_proficiency` legacy; il badge cambia da "Recluta" a nome classe IT; lock_state passa da `locked_recruit_unassigned` a `equippable` (o altro lock_state applicabile a valle dei check 6/7/8 C2).

### 4.3 · Reversibilità

- **Fase live iniziale (post-Apply Phase)**: **irreversibile**. Documentazione PM: la scelta è definitiva, in linea con l'identità narrativa.
- **Fase futura eventuale ("Rite of Rebirth")**: **HOLD · pending PM decision** (vedi Q1 open questions). Se autorizzata, richiederà spesa risorse gilda + reset progression parziale + narrative "resa dei conti" — design dedicato non in R18.6.

### 4.4 · Lock post-scelta

Dopo la scelta:
- `adventurer.class_hall_assigned_at` = timestamp UTC
- `adventurer.class_hall_id` = id sala scelta (uno di `hall_guerriero · hall_ladro · hall_mago · hall_paladino · hall_cacciatore_di_mostri`)
- `adventurer.class_proficiency` = legacy label canonical (uno di Warrior/Rogue/Mage/Priest/Ranger)
- `adventurer.canonical_class_slug` = slug canonico IT (uno di guerriero/ladro/mago/paladino/cacciatore_di_mostri)
- `adventurer.recruit_status` = `"class_assigned"`
- `adventurer.narrative_intro_shown` = `true`

**Nessuna scrittura DB avviene in R18.6.** Sopra è pseudo-schema per R18.3f + Apply Phase.

---

## Sezione 5 · Regole di Blocco Classless (derivate da C2)

R18.6 **non introduce nuovi lock_state**. Riusa esattamente il lock_state matrix C2 (10 stati). I 4 stati rilevanti per il Recluta sono:

| Lock_state (C2 #) | Condizione | UI badge (C2) | CTA (C2) | Comportamento equip | Comportamento roster |
|---|---|---|---|---|---|
| **#3 `locked_recruit_unassigned`** | `class_slug=null` **AND** `class_proficiency=null` | ambra · icona porta | ✅ "Assegna Sala di Classe" | ❌ blocca equip gear specializzato | ⚠️ escluso da dungeon/raid roster picker (default off) |
| **#4 `locked_class_slug_null`** | `class_slug=null` **AND** `class_proficiency` popolato canonical | ambra · icona chiave | ❌ (bridge post-R18.3f) | ⚠️ equip permesso via `class_proficiency` fallback (legacy runtime v1) | ✅ operativo, ma con warning "aggiornamento identità pendente" |
| **#5 `universal_allowed`** | `is_cosmetic` OR slot ∈ {`trinket-universal`, `consumable`, `material`} | verde · icona lente | — | ✅ bypass proficiency check | ✅ operativo per consumable/cosmetic |
| **#10 `equippable`** | tutti i check passati | verde · icona spunta | — | ✅ equip completo | ✅ operativo pieno |

**Note operative per il Recluta (`locked_recruit_unassigned`)**:
- **Roster picker dungeon/raid**: filtro default `exclude(recruit_status='recruit_unassigned')`. Override manuale player: pop-up warning "*Questo avventuriero non ha ancora scelto una Sala di Classe. Non può equipaggiare gear specializzato né ricevere loot corrispondente. Continuare?*" — blocca per default, richiede conferma esplicita.
- **Loot handling** in scenario override: il Recluta riceve XP tutorial ridotto, drop gear specializzato **non assegnabili** (finiscono nell'inventario gilda).
- **Combat participation**: no auto-partecipazione se `recruit_unassigned`.
- **Tutorial "Prova di Sala"** (encounter scripted, safe-mode, no reward gear): unica eccezione consentita — è progettata per essere superata da un Recluta.

---

## Sezione 6 · Class Hall → Classe → Proficiency Matrix (lockata PM)

| Class Hall | canonical_class_slug | canonical_class_name_it | legacy_class_label | main_stat | armor_type whitelist | weapon_family whitelist |
|---|---|---|---|---|---|---|
| Fortezza d'Acciaio | `guerriero` | Guerriero | Warrior | **Forza** | maglia · piastre | spada · ascia · martello · scudo · lancia · arma_in_asta |
| Loggia dei Sussurri | `ladro` | Ladro | Rogue | **Destrezza** | cuoio | pugnale · spada · balestra |
| Circolo dei Nove Sigilli | `mago` | Mago | Mage | **Intelligenza** | stoffa | bastone · tomo · focus · pugnale |
| Reliquiario della Luce Fissa | `paladino` | **Paladino** | Priest | **Saggezza** | stoffa | bastone · martello · focus · reliquia |
| Capanno del Sentiero Selvaggio | `cacciatore_di_mostri` | **Cacciatore di Mostri** | Ranger | **Destrezza** | cuoio · maglia | arco · balestra · spada · pugnale · lancia |

**Enforcement runtime**: la matrice sarà consumata dal validator `equip_eligibility_check` (C2, lock_states #6 e #7). R18.6 non implementa runtime — la matrice è **design layer**.

**Nessuna eccezione implicita** (regola PM). Se in futuro il PM autorizza cross-class weapon (es. Guerriero con arco), sarà un design dedicato distinto da R18.6.

---

## Sezione 7 · UI/UX Player-Facing (testuale, MMO gestionale)

Stile: **testuale minimalista Orbus**, coerente con il tone del prodotto (no sprite, no canvas, no illustrazioni).

### 7.1 · Componenti UI (design layer)

| Componente | Placement | Contenuto | Interazione |
|---|---|---|---|
| **Dashboard banner** | top Dashboard Gilda, dismissable | `"⚠️ Hai {N} recluta/e senza classe. Assegna una Sala per attivarli."` | tap → apre Roster filtrato |
| **Roster row (Recluta)** | tab Roster / Adventurers | nome · livello · badge `[Recluta · Senza Classe]` (colore ambra) · icona porta | tap → scheda avventuriero |
| **Scheda avventuriero (Recluta)** | modal-full | nome · livello · badge lock_state · **CTA primario `Assegna Sala di Classe`** · secondari (disabilitati con tooltip) | tap CTA → modal "Le 5 Sale" |
| **Modal "Le 5 Sale"** | modal-full, list-based | 5 righe: `nome sala` · `classe` · `main_stat` · one-liner lore hook · tap-through | tap riga → preview Sala |
| **Preview Sala (drawer)** | side drawer o expand | dettagli completi (armor · weapon · hall_master · rito · logica gameplay) · CTA `Consacra {nome}` | tap CTA → conferma |
| **Dialogo di conferma** | modal, blocca | testo esplicito + checkbox `Confermo. La scelta è definitiva.` + `Consacra` (disabilitato finché non è flaggato) | tap `Consacra` → esegue |
| **Confirmation banner** | toast/log | `"✨ {nome} è ora {classe}. Log della Gilda aggiornato."` (dura 6s) | dismiss auto |
| **Log Gilda entry** | timeline log Gilda | narrative micro-log della Sala scelta (vedi 3.1–3.5) | persistente |
| **Tooltip lock_state** | hover/tap-hold badge | copy IT specifica per lock_state (vedi Sezione 8) | passivo |
| **Dungeon roster picker** | tab Dungeons/Raids, avventuriero selection | Reclute filtrate di default, override con warning modal | override → mostra warning modal |
| **Warning modal override** | modal | testo warning full (vedi 8.5) + `Continua comunque` + `Annulla` | player decision |

### 7.2 · Principi UI

- **Testuale**: nessun asset grafico, solo testo + icone Lucide/FontAwesome (porta, chiave, spunta, lente, ambra).
- **Colori accent**: ambra per `locked_recruit_unassigned`, verde per `equippable/universal_allowed`, rosso per lock hard (armor/weapon proficiency mismatch).
- **Copy in italiano** per tutto il player-facing (log, tooltip, warning, banner, modal).
- **Nessuna gamification eccessiva**: nessun countdown, nessun timer di scelta forzata — la scelta di Sala può essere fatta a tempo indefinito, il Recluta resta nel roster.
- **Accessibilità**: contrasto alto (ambra su nero), font legibile, no autoplay di narrative micro-log.
- **Coerenza R18.5 UI badge C2**: `ambra · icona porta` per `locked_recruit_unassigned` — direttamente da C2 UI badge matrix, non re-inventato.

### 7.3 · Non fare

- ❌ Nessuna cutscene / animazione lunga per il rito (è testuale, un micro-log basta).
- ❌ Nessun paywall / premium currency sulla scelta.
- ❌ Nessuna "loot box" o RNG sulla Sala assegnata.
- ❌ Nessuna raccomandazione algoritmica automatica ("La Sala migliore per te è…"): la scelta è del player, informata.

---

## Sezione 8 · Tutorial / Prompt Copy (italiano, canonical)

Tutti i messaggi sono in **italiano**, coerenti con il worldbuilding Orbus e con la terminologia canonica (Paladino, Cacciatore di Mostri).

### 8.1 · Welcome tooltip nuovo avventuriero (first-time)

> **"Un nuovo Recluta si è unito alla tua Gilda."**
> "*{nome}* è arrivato senza una classe assegnata. Prima di poterlo mandare in dungeon o equipaggiare con armi e armature specializzate, dovrai portarlo in una delle **Cinque Sale** del Complesso della Gilda."
> `[Vai al Roster] [Ho capito]`

### 8.2 · Roster badge tooltip (Recluta)

> **"Recluta · Senza Classe"**
> "Questo avventuriero non ha ancora scelto una Sala di Classe. Assegnagli una Sala per sbloccarne l'equipaggiamento e le assegnazioni."
> `[Assegna Sala di Classe]`

### 8.3 · Modal "Le 5 Sale" — subtitle

> **"Cinque Sale. Cinque destini. Una scelta definitiva."**
> "*Ogni Sala forgia una classe distinta. Ogni classe porta con sé una diversa arte del combattimento, una diversa armatura, un diverso incontro con il mondo. Scegli con cura: la scelta è irrevocabile.*"

### 8.4 · Preview Sala — subtitle (esempio Reliquiario della Luce Fissa)

> **"Reliquiario della Luce Fissa · Paladino"**
> "*La luce non chiede. La luce impone.* — Sotto la Custode Isabeau dell'Alba, il tuo Recluta veglierà la brace fino all'alba. Alla prima luce, riceverà il Reliquiario Personale e diverrà un **Paladino** della Gilda."
> `[Consacra {nome} come Paladino]`

### 8.5 · Warning modal override roster dungeon (Recluta forzato)

> **"⚠️ Recluta senza Sala"**
> "*{nome}* non ha ancora scelto una Sala di Classe. Se lo mandi in dungeon adesso:
> — non potrà equipaggiare gear specializzato;
> — il loot che gli sarebbe destinato finirà nell'inventario della Gilda;
> — la sua partecipazione al combattimento sarà limitata.
>
> Ti consigliamo di **assegnargli prima una Sala**."
> `[Assegna Sala di Classe] [Manda comunque]`

### 8.6 · Blocco equip gear specializzato (lock_state #3)

> **"Assegna una Sala di Classe."**
> "*{nome}* è un Recluta senza classe: non può equipaggiare questo oggetto. Portalo in una delle Cinque Sale per sbloccare l'equipaggiamento."
> `[Vai al Complesso della Gilda]`

### 8.7 · Blocco equip legacy pending (lock_state #4)

> **"Identità in aggiornamento."**
> "Il sistema di identità di *{nome}* è in aggiornamento (bridge canonico). Puoi equipaggiare questo oggetto, ma alcune funzionalità saranno disponibili dopo la migrazione."
> `[Ho capito]`

### 8.8 · Confirmation banner post-scelta (esempio Cacciatore di Mostri)

> **"✨ *{nome}* ha seguito la traccia fino all'alba. Da oggi è un Cacciatore di Mostri."**

### 8.9 · Log Gilda entry (esempio Paladino)

> `[timestamp] · Rito completato:` "*{nome} ha vegliato la brace fino all'alba. Da oggi è un Paladino.*" — Custode Isabeau dell'Alba lo ha benedetto nel Reliquiario della Luce Fissa.

---

## Sezione 9 · Interazione con R18.5 (LOCKED · reference only)

R18.5 Phase C è **CLOSED · PM APPROVED · LOCKED**. R18.6 **legge** ma **non modifica** i seguenti artefatti R18.5:

| Artefatto R18.5 | Uso in R18.6 | Modifica? |
|---|---|---|
| **Lock_state matrix C2 (10 stati)** | R18.6 usa esattamente C2 #3, #4, #5, #10 per gestire Recluta / classless / equip check | ❌ NO modifica |
| **Proficiency matrix C2** (armor + weapon + main_stat per classe) | R18.6 replica la matrice per la Sezione 6, invariata rispetto a C2 e a Q6 C5 | ❌ NO modifica |
| **Registry v2 23 fields** | R18.6 non tocca i campi item; usa `class_proficiency`, `armor_type`, `weapon_family` come input runtime del validator equip | ❌ NO modifica |
| **Canonical class slug C5/C6** (guerriero/ladro/mago/paladino/cacciatore_di_mostri) | R18.6 usa esattamente questi 5 slug + naming IT + slug errata Q1+Q5 | ❌ NO modifica |
| **`runtime_apply_ready=false` 1500/1500** | R18.6 rispetta il regime dry-run: nessun equip effettivo in runtime | ❌ NO modifica |
| **UI badge matrix C2** (ambra · icona porta per `locked_recruit_unassigned`) | R18.6 riusa esattamente il badge design | ❌ NO modifica |
| **Q7 C2 handling di `class_slug=null`** | R18.6 conferma NO auto-derive, differisce a R18.3f | ❌ NO modifica |

**Nessuna richiesta di modifica a R18.5.** Se emergono gap non copribili senza modifica R18.5, sono segnalati nei PM open questions come blocker (nessuno emerso in questa fase R18.6).

---

## Sezione 10 · Interazione con R18.3f (HOLD · handoff readiness)

R18.3f Class Slug Migration Readiness è **🔒 HOLD**. R18.6 **non avvia R18.3f**, **non genera migration script**, **non applica `class_slug`**. Documenta solo il **bisogno futuro** che R18.3f dovrà coprire per abilitare R18.6 live.

### 10.1 · Requisiti che R18.3f dovrà soddisfare per R18.6 live

| # | Requisito | Motivazione R18.6 |
|---|---|---|
| RQ-1 | **Schema `adventurer.class_slug` (nullable string, enum={5 canonical slug live})** | popolato via Class Hall UI post-scelta |
| RQ-2 | **Schema `adventurer.class_hall_id` (nullable string, enum={hall_guerriero · hall_ladro · hall_mago · hall_paladino · hall_cacciatore_di_mostri})** | traccia narrativa della Sala scelta |
| RQ-3 | **Schema `adventurer.class_hall_assigned_at` (nullable datetime UTC)** | audit/telemetria + reversibilità futura |
| RQ-4 | **Schema `adventurer.recruit_status` (enum={"recruit_unassigned","class_assigned"})** | driver del funnel R18.6 |
| RQ-5 | **Migration script per adventurer legacy pre-R18.6** | popolamento retroattivo `class_slug` dai `class_proficiency` legacy (Warrior→guerriero, ecc.) tramite tabella di mapping — **esclusivamente in R18.3f, NON in R18.6** |
| RQ-6 | **Backwards-compat check**: legacy client che non conoscono `class_slug` non devono rompersi | R18.3f gate |
| RQ-7 | **Translation layer legacy_class_label → canonical_class_slug** (mapping 5-tuple) | evita drift terminologico UI/backend |
| RQ-8 | **Validator `equip_eligibility_check` runtime** consuma `canonical_class_slug` primario, fallback su `class_proficiency` legacy | R18.3f + Apply Phase gate |

### 10.2 · Legacy EN → canonical IT translation policy (documentale)

Mapping obbligatorio (già lockato in C5/C6 slug errata Q1+Q5):

```
Warrior → guerriero
Rogue   → ladro
Mage    → mago
Priest  → paladino          ⚠️ (NON priest, NON prete)
Ranger  → cacciatore_di_mostri
```

R18.3f dovrà implementare questo mapping come **immutable lookup table** (no user-editable, no i18n runtime — è terminologia canonica, non traduzione UI).

### 10.3 · NO cross-contamination

- R18.6 **NON scrive** in DB, **NON popola** `class_slug`, **NON altera** schema.
- R18.6 **NON avvia** R18.3f: R18.3f resta HOLD in attesa di GO PM esplicito separato.
- R18.6 **NON attiva** Class Halls implementation (l'UI live richiede R18.3f + Apply Phase).

---

## Sezione 11 · Risk Register

| ID | Rischio | Severity | Mitigazione | Status |
|---|---|---|---|---|
| **R1** | Player confonde "Paladino" con "priest/prete" (legacy naming eredità) | MEDIUM | UI copy sempre "Paladino" · lore doc esplicito · tooltip di disambiguazione al primo incontro · slug canonical `paladino` obbligatorio in R18.3f | DOCUMENTED |
| **R2** | Player confonde "Cacciatore di Mostri" con "Ranger" o "Cacciatore" generico (pattern match falliti) | MEDIUM | UI copy sempre "Cacciatore di Mostri" · slug canonical `cacciatore_di_mostri` (underscore) · immutable lookup, no pattern match | DOCUMENTED |
| **R3** | Player si sente forzato a scegliere subito, abbandona onboarding | LOW-MEDIUM | Reclute possono restare classless a tempo indefinito · nessun countdown · dashboard banner dismissable | DESIGNED |
| **R4** | Player sceglie Sala sbagliata e la scelta è irreversibile → frustrazione | MEDIUM | Preview Sala esplicita · dialogo di conferma con checkbox esplicita · lore doc leggibile pre-scelta · "Rite of Rebirth" futuro come open question PM (Q1) | MITIGATED |
| **R5** | Roster picker dungeon include Reclute senza classe → loot sprecato | LOW | Filtro default `exclude(recruit_unassigned)` + warning modal override | DESIGNED |
| **R6** | Recluta perde XP tick idle → perdita valore percepito | LOW | XP tick idle per Recluta = pending PM decision (Q4). Design default: XP tick 50% ridotto fino a scelta Sala | OPEN (Q4) |
| **R7** | Class Hall NPC hall_master conflitto con lore Orbus esistente | LOW | Nomi NPC scelti come new-additions non collidenti con roster NPC noto · PM può rinominare in R18.6 review | DOCUMENTED |
| **R8** | Legacy adventurer pre-R18.6 con `class_proficiency` popolato ma `class_slug=null` → falsa Recluta | HIGH-INFO | lock_state C2 #4 (`locked_class_slug_null`) copre esattamente questo caso · R18.6 li tratta come "operativo con warning" · migration retroattiva in R18.3f (RQ-5) | DESIGNED |
| **R9** | Applicazione R18.6 senza R18.3f prep → schema drift + rollback difficile | HIGH-BLOCK | R18.6 vieta l'apply · Apply Phase richiede 7 preconditions (backup DB · dry-run tech · rollback plan · seal governance · migration order · failure recovery · PM approval) esplicitamente elencate nel PM Final ACK di C6 | ENFORCED |
| **R10** | Terminologia UI localizzata (es. inglese `Priest` in log legacy) resiste al deploy | MEDIUM | R18.3f translation layer + audit UI copy pre-R18.6 live · translation policy documentata in Sezione 10.2 | TRACKED to R18.3f + R18.6-live |
| **R11** | 4 Progressive Discovery Legendary (P1-P4) sono class-locked (Mage/Priest→Paladino/Rogue→Ladro/Ranger→Cacciatore di Mostri) → interazione con Reclute non ovvia | LOW | Reclute non equipaggiano gear specializzato (C2 #3), quindi Progressive Discovery non li tocca finché non scelgono Sala · Progressive Discovery finalization resta HOLD (PG1 C6) | DESIGNED |
| **R12** | UI mobile stretta (viewport < 400px) rende Modal "Le 5 Sale" affollato | LOW | Design testuale one-liner per riga · Preview Sala in drawer separato (non stacked) | DESIGNED |

---

## Sezione 12 · PM Open Questions

Domande aperte che richiedono decisione PM esplicita **fuori scope R18.6 documentale**. R18.6 chiude senza forzare risposte.

| ID | Domanda | Options |
|---|---|---|
| **Q1** | **Rite of Rebirth** (reversibilità scelta Sala) — abilitare in future PM design? | (a) NO, scelta permanente per identità narrativa · (b) SÌ, con costo risorse gilda + reset progression parziale · (c) SÌ, ma solo una volta per adventurer, con costo elevato · (d) DEFER decisione a post-launch metrics |
| **Q2** | **Nome/genere dei 5 hall_master NPC** (Comandante Aldric · Maestra Selene · Arcimago Vessel · Custode Isabeau · Vecchio Falconiere Ovyr) — confermare o proporre lore alternative? | (a) confermo verbatim · (b) mantengo ruolo ma cambio nomi · (c) rewrite completo (PM propone) |
| **Q3** | **Fate di un Recluta**: può essere venduto/dismesso/trasferito ad altra gilda pre-scelta? | (a) SÌ, come qualunque altro adventurer · (b) NO, deve prima scegliere Sala · (c) SÌ ma con penalty (metà rimborso) |
| **Q4** | **XP tick idle Recluta**: ridotto, pieno, o zero? | (a) zero (Recluta non guadagna XP finché non sceglie) · (b) 50% (design default proposto) · (c) 100% (nessuna penalty) |
| **Q5** | **Prova di Sala** (encounter scripted safe-mode pre-scelta): abilitare come tutorial pratico? | (a) SÌ, uno per Sala (5 tutorial, opt-in) · (b) SÌ, uno generico "prova le 5" · (c) NO, solo lore text |
| **Q6** | **Numero massimo Reclute simultanei nella Gilda**: cap? | (a) nessun cap · (b) cap = 3 (evita overflow onboarding) · (c) cap dinamico (livello gilda) |
| **Q7** | **Rito di consacrazione**: durata narrativa (istantaneo vs "una notte in-game" con timer sim)? | (a) istantaneo (design default) · (b) 1 tick in-game (feel narrative) · (c) 8 ore reali (deep narrative, ma frustration risk) |
| **Q8** | **Interazione con Adventurer Identity narrative hooks**: ogni Sala aggiunge tratti passivi narrativi (es. Paladino ha `virtù_dell_alba` +1)? | (a) NO, solo proficiency (design default) · (b) SÌ, un tratto passivo simbolico per Sala (design espanso) · (c) SÌ, con impatto gameplay leggero |

---

## Sezione 13 · GO/HOLD Recommendation

### 13.1 · Recommendation per la fase successiva

**R18.6 design documentale è COMPLETO** e pronto per PM review. **NON procedere oltre senza GO PM esplicito**.

Ordine suggerito post-R18.6 (in attesa PM sign-off):

| # | Fase | Status | Precondition |
|---|---|---|---|
| 1 | **R18.6 PM review + ACK** | 🟡 PENDING | PM legge i deliverable, risponde a Q1–Q8 |
| 2 | **R18.3f Class Slug Migration Readiness** | 🔒 HOLD | GO PM esplicito post-R18.6 ACK · design migration script + adventurer schema update |
| 3 | **Progressive Discovery Legendary Finalization (P1-P4)** | 🔒 HOLD | dedicated PM gate post-C6 · può procedere in parallelo a R18.3f prep |
| 4 | **Apply Phase (Registry + Drop + Backfill + Class_slug + Runtime enforcement)** | 🔒 HOLD | richiede 7 preconditions (backup DB · dry-run tech · rollback · seal governance · migration order · failure recovery · PM approval) |
| 5 | **R18.6 live (Class Halls UI + funnel scelta + lock_state runtime)** | 🔒 HOLD | richiede R18.3f apply + Apply Phase completata |
| 6 | **Marketing Brief** | ⏸️ DEFERRED | no priority |

### 13.2 · Recommendation esplicita

- ✅ **APPROVE R18.6 design documentale** (13 sezioni complete, matrice PM verbatim, slug errata canonica applicata, C2/C5/C6 reference locked)
- 🔒 **HOLD** su tutte le fasi successive
- ❓ **Rispondere ai PM open questions (Q1–Q8)** in un round dedicato prima di R18.3f GO
- 🛑 **NO apply · NO R18.3f start · NO migration script · NO code · NO UI implementation · NO Marketing Brief**

---

## Sezione 14 · Governance Snapshot

| Voce | Stato |
|---|:--:|
| Documental only regime | ENFORCED ✅ |
| Italian output | ENFORCED ✅ |
| 36 sealed files byte-identical | ✅ |
| `lore_meta.py` invariato | ✅ (SHA256 `a18f708b…`) |
| DB writes | ZERO ✅ |
| Code changes | ZERO ✅ |
| Migrations | ZERO ✅ |
| Sealed file modification | ZERO ✅ |
| R18.5 modification | ZERO ✅ (LOCKED) |
| R18.3f auto-start | BLOCKED ✅ |
| Apply Phase kickoff | BLOCKED ✅ |
| Class Halls UI implementation | BLOCKED ✅ |
| Marketing Brief | BLOCKED ✅ |
| Class slug auto-derivation | BLOCKED ✅ |
| Runtime bridge | ZERO ✅ |
| Files deliverable R18.6 | 2 (.md + .json) |

---

## 🛑 STOP after R18.6 Design

**Non procedere oltre senza nuovo GO PM esplicito.**

Attendo PM review + risposte a Q1–Q8 prima di qualunque handoff verso R18.3f, Progressive Discovery, o Apply Phase.
