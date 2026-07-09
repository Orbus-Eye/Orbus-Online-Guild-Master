# R18.6.1 · Canonical 27 Class Halls Expansion — Design Documentale
**Round**: R18.6.1 · **Locked at (UTC)**: 2026-07-08T16:00:00Z
**Authority**: PM Orchestrator — R18.6.1 GO esplicito post-R18.6 CLOSED
**Regime**: **DOCUMENTAL ONLY** — estensione canonica di R18.6, NON riscrittura retroattiva. NO code · NO DB · NO migrations · NO class_slug apply · NO runtime bridge · NO automatic class assignment · NO auto-derive · NO live implementation · NO unlock 22 non-live · NO R18.5 modification (LOCKED) · NO R18.6 modification (LOCKED).
---
## Sezione 1 · Executive Summary
Il sistema Class Halls viene esteso da **5 Sale iniziali (R18.6 LOCKED)** a **27 Sale canoniche** — una per ciascuna delle 27 classi di Orbus Online. Ogni classe canonica ha **una e una sola Sala dedicata** (principio 1:1 rigoroso, NO Sale condivise).
**Stato operativo**:
- **5 ACTIVE-DESIGN-READY** (verbatim da R18.6): guerriero · ladro · mago · paladino · cacciatore_di_mostri
- **22 PLANNED / LOCKED-UNTIL-CLASS-READY**: le altre 22 classi hanno design canonico (nome Sala, lore, Maestro proposto, prova safe-mode, tratto simbolico) ma `main_stat`/`armor`/`weapon` = **PENDING_STAT_DESIGN** / **PENDING_PROFICIENCY_DESIGN**. **NO auto-unlock**.

**Regola canonica definitiva**: ogni nuovo avventuriero nasce **Senza Classe / Recluta** (`class_slug=null` · `recruit_unassigned`). Acquisisce classe **SOLO** tramite: ingresso Sala → prova safe-mode → conferma → assegnazione classe → assegnazione `class_slug` → sblocco identità/proficiency/equip. **NON esiste**: assegnazione casuale · auto-derivazione da equip/stat · scelta fuori dalle Sale · bridge legacy silente.

## Sezione 2 · Matrice Completa 27 Classi → 27 Sale (Riassuntiva)
| # | Classe IT | class_slug | hall_id | Sala | Stato | Hall Master |
|:--:|---|---|---|---|:--:|---|
| 1 | Alchimista | `alchimista` | `hall_alchimista` | Distilleria del Vapore Verde | 🔒 PLANNED | Maestra Distillatrice Ilyra Ottavia *(PENDING PM)* |
| 2 | Artificiere | `artificiere` | `hall_artificiere` | Officina Fumante di Rame | 🔒 PLANNED | Capo Artificiere Nolan Vent *(PENDING PM)* |
| 3 | Astrologo | `astrologo` | `hall_astrologo` | Osservatorio delle Costellazioni Fisse | 🔒 PLANNED | Astrologo Maggiore Cassian Vale *(PENDING PM)* |
| 4 | Bardo | `bardo` | `hall_bardo` | Taverna della Corda Spezzata | 🔒 PLANNED | Bardo Maggiore Ambroise *(PENDING PM)* |
| 5 | Burattinaio | `burattinaio` | `hall_burattinaio` | Teatro dei Fili di Ferro | 🔒 PLANNED | Prima Burattinaia Melisandre Corda *(PENDING PM)* |
| 6 | Cacciatore del Sangue | `cacciatore_del_sangue` | `hall_cacciatore_del_sangue` | Ossario del Cinghiale Bianco | 🔒 PLANNED | Cacciatore Solitario Grim Rohl *(PENDING PM)* |
| 7 | Cacciatore del Vuoto | `cacciatore_del_vuoto` | `hall_cacciatore_del_vuoto` | Faro Rovesciato di Onirade | 🔒 PLANNED | Cacciatrice del Vuoto Nael di Onirade *(PENDING PM)* |
| 8 | Cacciatore di Mostri | `cacciatore_di_mostri` | `hall_cacciatore_di_mostri` | Capanno del Sentiero Selvaggio | ✅ LIVE | Vecchio Falconiere Ovyr |
| 9 | Cartografo | `cartografo` | `hall_cartografo` | Camera delle Mappe Vive | 🔒 PLANNED | Capomastro Cartografo Odran il Mite *(PENDING PM)* |
| 10 | Cavaliere della Morte | `cavaliere_della_morte` | `hall_cavaliere_della_morte` | Cripta del Vessillo Nero | 🔒 PLANNED | Primo Cavaliere Nero Vaeric Rahn *(PENDING PM)* |
| 11 | Cavaliere di Draghi | `cavaliere_di_draghi` | `hall_cavaliere_di_draghi` | Ariale del Signore delle Fiamme | 🔒 PLANNED | Signora delle Fiamme Aelor Draconis *(PENDING PM)* |
| 12 | Cronista | `cronista` | `hall_cronista` | Scriptorium del Presente Eterno | 🔒 PLANNED | Cronista Maggiore Ambrose di Mnemos *(PENDING PM)* |
| 13 | Druido | `druido` | `hall_druido` | Radura del Salice Millenario | 🔒 PLANNED | Druido Anziano Bran del Salice *(PENDING PM)* |
| 14 | Fabbro Arcano | `fabbro_arcano` | `hall_fabbro_arcano` | Fucina degli Anelli Silenti | 🔒 PLANNED | Fabbro Anziano Corvus Anello *(PENDING PM)* |
| 15 | Giocatore d'Azzardo | `giocatore_d_azzardo` | `hall_giocatore_d_azzardo` | Sala dei Dadi di Ossidiana | 🔒 PLANNED | Croupier Perpetuo Sylas Nod *(PENDING PM)* |
| 16 | Guerriero | `guerriero` | `hall_guerriero` | Fortezza d'Acciaio | ✅ LIVE | Comandante Aldric del Ferro |
| 17 | Ladro | `ladro` | `hall_ladro` | Loggia dei Sussurri | ✅ LIVE | Maestra dei Sussurri Selene |
| 18 | Mago | `mago` | `hall_mago` | Circolo dei Nove Sigilli | ✅ LIVE | Arcimago Vessel di Memoria |
| 19 | Mercante | `mercante` | `hall_mercante` | Loggia del Bilico Onesto | 🔒 PLANNED | Prima Mercatrice Yara della Bilancia *(PENDING PM)* |
| 20 | Monaco | `monaco` | `hall_monaco` | Cortile della Corda di Cinabro | 🔒 PLANNED | Monaco Anziano Ren Silenzio *(PENDING PM)* |
| 21 | Negromante | `negromante` | `hall_negromante` | Ossario del Cerchio Chiuso | 🔒 PLANNED | Necromante Anziano Silas Nomeperduto *(PENDING PM)* |
| 22 | Paladino | `paladino` | `hall_paladino` | Reliquiario della Luce Fissa | ✅ LIVE | Custode Isabeau dell'Alba |
| 23 | Parassita | `parassita` | `hall_parassita` | Cripta della Radice Cava | 🔒 PLANNED | Parassita Anziana Ada Cava *(PENDING PM)* |
| 24 | Pittore | `pittore` | `hall_pittore` | Atelier dei Pigmenti Insanguinati | 🔒 PLANNED | Prima Pittrice Genoveva Rosso *(PENDING PM)* |
| 25 | Runista | `runista` | `hall_runista` | Cerchio delle Pietre Incise | 🔒 PLANNED | Runista Anziano Halvard Nove *(PENDING PM)* |
| 26 | Sciamano | `sciamano` | `hall_sciamano` | Capanna dei Tamburi Fermi | 🔒 PLANNED | Sciamano Anziano Vaska Tamburo *(PENDING PM)* |
| 27 | Sognatore | `sognatore` | `hall_sognatore` | Camera dei Sogni Aperti | 🔒 PLANNED | Sognatrice Anziana Elyrah dei Nove Sogni *(PENDING PM)* |

## Sezione 3 · Distinzione 5 ACTIVE-DESIGN-READY / 22 PLANNED
### 3.1 · 5 ACTIVE-DESIGN-READY (LIVE subito dopo Apply Phase gate)
Verbatim da R18.6 CLOSED · proficiency PM-lockata · design completo · NO modifica.

| class_slug | Sala | main_stat | armor | weapon |
|---|---|---|---|---|
| `cacciatore_di_mostri` | Capanno del Sentiero Selvaggio | **Destrezza** | cuoio · maglia | arco · balestra · spada · pugnale · lancia |
| `guerriero` | Fortezza d'Acciaio | **Forza** | maglia · piastre | spada · ascia · martello · scudo · lancia · arma_in_asta |
| `ladro` | Loggia dei Sussurri | **Destrezza** | cuoio | pugnale · spada · balestra |
| `mago` | Circolo dei Nove Sigilli | **Intelligenza** | stoffa | bastone · tomo · focus · pugnale |
| `paladino` | Reliquiario della Luce Fissa | **Saggezza** | stoffa | bastone · martello · focus · reliquia |

### 3.2 · 22 PLANNED (design canonico ma NON runtime-live)
Ogni Sala PLANNED ha nome epico, lore, Maestro (PENDING PM), prova safe-mode, tratto simbolico. Ma `main_stat` = `PENDING_STAT_DESIGN` e `armor/weapon proficiency` = `PENDING_PROFICIENCY_DESIGN`. **NO auto-unlock** finché PM non emette GO per Sala.

| class_slug | Sala | Ruolo indicativo | Stile gameplay |
|---|---|---|---|
| `alchimista` | Distilleria del Vapore Verde | Support | supporto tattico · pozioni · buff/debuff · utility crafting |
| `artificiere` | Officina Fumante di Rame | Support | supporto tecnico · torrette · dispositivi · engineering utility |
| `astrologo` | Osservatorio delle Costellazioni Fisse | Support | supporto arcano · buff basati su fasi · previsione danni · debuff cosmici |
| `bardo` | Taverna della Corda Spezzata | Support | supporto morale · buff di gruppo · debuff sonori · utility narrativa |
| `burattinaio` | Teatro dei Fili di Ferro | Support | controllo · summon marionette · debuff a distanza · pet management |
| `cacciatore_del_sangue` | Ossario del Cinghiale Bianco | DPS | melee bloody · self-sustain via emorragia inflitta · burst su prede ferite |
| `cacciatore_del_vuoto` | Faro Rovesciato di Onirade | DPS | ranged void · dispel · anti-summon · counter contro incorporei |
| `cartografo` | Camera delle Mappe Vive | Utility | utility esplorativa · scouting · reveal · buff di movimento |
| `cavaliere_della_morte` | Cripta del Vessillo Nero | Hybrid | melee tank/DPS ibrido · self-heal via necroenergia · aura di paura |
| `cavaliere_di_draghi` | Ariale del Signore delle Fiamme | DPS | melee/ranged con montatura draconica · burst di fiamma · aura draconica |
| `cronista` | Scriptorium del Presente Eterno | Support | supporto arcano/informativo · buff di narrativa · dispel via 'riscrittura' · utility investigativa |
| `druido` | Radura del Salice Millenario | Hybrid | hybrid caster/melee · shapeshift · healing naturale · elemental dot |
| `fabbro_arcano` | Fucina degli Anelli Silenti | Utility | crafting arcano · buff via infusion · gear enchant · utility runica |
| `giocatore_d_azzardo` | Sala dei Dadi di Ossidiana | Utility | utility caotica · buff/debuff RNG-based · effetti percentuali · risk-reward |
| `mercante` | Loggia del Bilico Onesto | Utility | utility economica · buff mercantili · dispel via 'contratto' · social utility |
| `monaco` | Cortile della Corda di Cinabro | DPS | melee unarmed · burst da combo · self-heal via disciplina · mobility |
| `negromante` | Ossario del Cerchio Chiuso | DPS | caster necroenergia · summon undead pet · dot · self-drain sostenuto |
| `parassita` | Cripta della Radice Cava | DPS | DPS bloody · leech · stat-steal su nemici · debuff drenanti |
| `pittore` | Atelier dei Pigmenti Insanguinati | Utility | utility illusoria · buff via 'immagini viventi' · debuff via ritratto · summon di immagini |
| `runista` | Cerchio delle Pietre Incise | Support | caster/support con rune permanenti · buff di area · trap runiche · dispel via 'runa rotta' |
| `sciamano` | Capanna dei Tamburi Fermi | Hybrid | hybrid healer/caster elementale · summon spiriti · buff totemici · elemental dot/hot |
| `sognatore` | Camera dei Sogni Aperti | Utility | caster onirico · debuff mentali · summon di sogni · utility psichica |

**Ordine di readiness (22 planned → active)**: `PENDING PM Q2 R18.6.1`.

## Sezione 4 · Flusso Recluta → Sala → Classe (esteso con Rite of Rebirth)
### 4.1 · Flusso base (6 step)
1. **Stato iniziale**: `class_slug=null · class_proficiency=null · recruit_status='recruit_unassigned' · classe=Senza Classe/Recluta`
2. **Ingresso Sala**: Recluta entra in una Sala (5 live selezionabili · 22 PLANNED NON selezionabili UI-live)
3. **Prova safe-mode**: encounter dedicato · mostra `main_stat` + `armor prof` + `weapon prof` + identità classe (evita scelta cieca)
4. **Conferma esplicita**: preview completa (descrizione · stile · forze · debolezze · equip tipico · ruolo · anteprima Sala · Maestro) · checkbox esplicito · **player-driven · gratuita · non casuale · non premium**
5. **Assegnazione classe**: `class_proficiency ← legacy label` · `canonical_class_slug ← slug canonico`
6. **Sblocco identità**: `class_slug` popolato · lock_state passa da C2 #3 (`locked_recruit_unassigned`) a C2 #10 (`equippable`) · proficiency + equip specializzato attivi

### 4.2 · Rite of Rebirth (una tantum · costo elevato non-premium · istantaneo)
Il rito **NON assegna direttamente** una nuova classe. Flusso in 6 step:

1. Classe attuale (esistente)
2. **Rite of Rebirth** (spesa risorse Gilda elevata · one-time per adventurer · no real-money · no shortcut)
3. **Ritorno temporaneo a Senza Classe** (`recruit_unassigned` re-attivato)
4. Scelta di un'altra Sala disponibile (fra le `ACTIVE-DESIGN-READY` vigenti · **NO Sala PLANNED**)
5. Nuova prova/rituale
6. Nuova classe · nuovo `class_slug`

**Constraint tecnici deferiti**: equip incompatibile · reset/riconversione · progressione (livello/talenti) · storico classe. **Gate tecnico futuro dedicato**, NON R18.6.1.

## Sezione 5 · Regole `recruit_unassigned` (dettagliate)
**Stato**: `class_slug=null AND class_proficiency=null AND recruit_status='recruit_unassigned'`. **Lock_state C2 #3** `locked_recruit_unassigned`.

### 5.1 · Vietato
- ❌ Nessuna classe · nessuna main stat di classe · nessuna proficiency specializzata
- ❌ Nessun equip di classe · nessun dungeon normale · nessun raid
- ❌ Nessuna progressione classe · idle XP = **0%**
- ❌ **NON** può essere venduto · **NON** può essere trasferito · **NON** può essere monetizzato

### 5.2 · Ammesso
- ✅ Resta nel roster · può essere **congedato/dismissed** (libera slot Gilda)
- ✅ Segue tutorial · visita le Sale (5 live) · affronta prova safe-mode
- ✅ Equip `universal_allowed` (consumable · material · cosmetic · trinket-universal)

### 5.3 · Cap
**Massimo 3 Reclute simultanee per Gilda** (Q6 R18.6=B, invariato). Dismissal libera slot.

## Sezione 6 · Class_slug Assignment Design
### 6.1 · Trigger
Confirmation step 4 del flusso · player explicit consent (checkbox 'La scelta è definitiva').

### 6.2 · Validation rules (immutable)
- `class_slug ∈ enum{27 canonical slug list}`
- `class_slug ← slug canonico Sala scelta` (immutable mapping · no user override)
- `class_slug` **NON** derivabile automaticamente da `class_proficiency` / equip / stat
- `class_slug` **NON** scelto fuori dalle 27 Sale
- `class_slug` **NON** assegnato tramite bridge legacy silente

### 6.3 · Fields updated atomically post-choice
`class_slug` · `class_proficiency` · `canonical_class_slug` · `class_hall_id` · `class_hall_assigned_at` · `hall_master_witness_npc` · `recruit_status` (→ `class_assigned`) · `narrative_intro_shown` (→ `true`)

### 6.4 · Runtime status
**DEFERRED to R18.3f + Apply Phase (HOLD)**. In R18.6.1: NO DB write · NO schema update · NO migration script · NO runtime bridge · NO auto-derive.

## Sezione 7 · Hall Profiles Completi (27 Sale · 20 campi ciascuna)
### 7.1 · Distilleria del Vapore Verde — *Alchimista*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_alchimista` · **class_slug**: `alchimista` · **classe_it**: Alchimista
- **Regione/Location**: sottotetto del Complesso · condotti di rame che scendono lungo le pareti
- **Lore source**: Fondata dopo il Vapore Verde che salvò la Prima Gilda dalla peste · un grammo separa cura e veleno (motto)
- **Identità architettonica**: Volta bassa con alambicchi ovali sospesi · pavimenti in mattonelle numerate · bilance rituali
- **Atmosfera**: Umido dolciastro · vapore verde che ristagna nei corridoi · fischio costante degli alambicchi
- **Simbolo**: Alambicco stilizzato dentro cerchio graduato
- **Colori**: verde vetro · rame lucido · avorio
- **Hall Master**: **Maestra Distillatrice Ilyra Ottavia** — Titolo di rispetto per chi separa cure dai veleni · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Goccia — separare correttamente una goccia curativa da una tossica con la sola bilancia
- **Rituale di assegnazione**: Ilyra siglia il grembiule del Recluta con la cera dell'alambicco · consegna della Bilancia Personale
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: supporto tattico · pozioni · buff/debuff · utility crafting
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Mano che Separa' · badge alambicco · flavor log 'L'Alchimista ha misurato e la Gilda è più leggera di un veleno'

### 7.2 · Officina Fumante di Rame — *Artificiere*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_artificiere` · **class_slug**: `artificiere` · **classe_it**: Artificiere
- **Regione/Location**: cortile interno del Complesso · tettoia aperta con camini bassi
- **Lore source**: Costruita dopo l'Ingranaggio Salvato che tenne aperta l'ultima cateratta · ciò che si rompe si rifà, ciò che si rifà migliora (motto)
- **Identità architettonica**: Officina a cielo semiaperto · morse ovunque · giranti e cinghie sui soffitti
- **Atmosfera**: Fumo di carbone dolce · scintille ordinate · rumore continuo di martello leggero
- **Simbolo**: Ingranaggio dentato dentro esagono di rame
- **Colori**: rame acceso · nero fuliggine · giallo lampone
- **Hall Master**: **Capo Artificiere Nolan Vent** — Nome del meccanico che serve l'ingranaggio più che l'ordine · status **PENDING_PM**
- **Prova safe-mode**: La Prova dell'Ingranaggio — rimontare un meccanismo composto da otto pezzi entro un giro di clessidra a sabbia rossa
- **Rituale di assegnazione**: Nolan consegna il Cacciavite Firmato · marchio a fuoco piccolo sull'incavo del pollice
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: supporto tecnico · torrette · dispositivi · engineering utility
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Mano che Ripara' · badge ingranaggio · flavor log 'L'Artificiere ha stretto la vite e la Gilda ha respirato'

### 7.3 · Osservatorio delle Costellazioni Fisse — *Astrologo*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_astrologo` · **class_slug**: `astrologo` · **classe_it**: Astrologo
- **Regione/Location**: torre bassa gemellare del Circolo dei Nove Sigilli · terrazza aperta al cielo settentrionale
- **Lore source**: Eretto per leggere le Costellazioni Fisse che non tramontano · ciò che è scritto in alto è già accaduto in basso (motto)
- **Identità architettonica**: Cupola scorrevole in bronzo · pavimento in mattonelle di ardesia numerate · sedia rotante centrale
- **Atmosfera**: Aria tersa notturna · odore lieve di ottone lucidato · silenzio della volta stellare
- **Simbolo**: Cerchio zodiacale con dodici tacche e una tredicesima invisibile
- **Colori**: blu profondo · argento notturno · nero indaco
- **Hall Master**: **Astrologo Maggiore Cassian Vale** — Nome del lettore di cieli senza casata · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Costellazione — riconoscere una costellazione fissa nell'orizzonte capovolto della cupola
- **Rituale di assegnazione**: Cassian consegna il Compasso Celeste · segna il palmo con inchiostro di stella nera
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: supporto arcano · buff basati su fasi · previsione danni · debuff cosmici
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha visto il Tredicesimo' · badge zodiaco tacca · flavor log 'L'Astrologo ha guardato in alto e la Gilda ha camminato dritta'

### 7.4 · Taverna della Corda Spezzata — *Bardo*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_bardo` · **class_slug**: `bardo` · **classe_it**: Bardo
- **Regione/Location**: ala ovest del Complesso · sala grande con palco basso e camino permanente
- **Lore source**: Nata dalla notte in cui una corda spezzata continuò a suonare da sola · una canzone rimasta a metà è un patto (motto)
- **Identità architettonica**: Sala unica con travi in legno scuro · palco basso a nord · gradinata di sedie disordinate
- **Atmosfera**: Odore di birra ambrata · voci mescolate · una nota di liuto sempre presente in sottofondo
- **Simbolo**: Liuto stilizzato con corda spezzata a metà
- **Colori**: rosso vino · legno miele · giallo candela
- **Hall Master**: **Bardo Maggiore Ambroise** — Nome del cantore che ha finito la Canzone Interrotta · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Nota Mancante — completare la Canzone Interrotta trovando la nota giusta al primo tentativo
- **Rituale di assegnazione**: Ambroise consegna la Fibbia della Corda · nome inciso sul retro del palco
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: supporto morale · buff di gruppo · debuff sonori · utility narrativa
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha completato la Canzone' · badge liuto e nota · flavor log 'Il Bardo ha cantato e la stanza ha smesso di temere'

### 7.5 · Teatro dei Fili di Ferro — *Burattinaio*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_burattinaio` · **class_slug**: `burattinaio` · **classe_it**: Burattinaio
- **Regione/Location**: cortile ovest del Complesso · teatro a cielo aperto con sipario perpetuo
- **Lore source**: Costruito per il Primo Burattino che si mosse da solo · il filo che tiene è il filo che libera (motto)
- **Identità architettonica**: Palcoscenico rialzato · fondale nero · impalcatura di travi sopra il palco per i fili
- **Atmosfera**: Silenzio da spettacolo appena finito · scricchiolii di legno · fili di ferro che vibrano appena
- **Simbolo**: Marionetta stilizzata con fili convergenti a una sola mano
- **Colori**: nero teatro · ferro brunito · rosso sipario
- **Hall Master**: **Prima Burattinaia Melisandre Corda** — Nome della donna che mosse il Primo Burattino · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Filo — muovere una marionetta di ferro attraverso il palco senza far cadere il campanello sospeso
- **Rituale di assegnazione**: Melisandre consegna la Mano di Ferro · marchio a inchiostro sul dorso della mano dominante
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: controllo · summon marionette · debuff a distanza · pet management
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha mosso il Ferro' · badge marionetta · flavor log 'Il Burattinaio ha tirato il filo e la scena ha risposto'

### 7.6 · Ossario del Cinghiale Bianco — *Cacciatore del Sangue*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cacciatore_del_sangue` · **class_slug**: `cacciatore_del_sangue` · **classe_it**: Cacciatore del Sangue
- **Regione/Location**: grotta al margine del bosco della Gilda · adiacente ma non affiliato al Capanno del Sentiero Selvaggio
- **Lore source**: Aperto dopo la Caccia del Cinghiale Bianco che sanguinò per tre notti · il sangue sa dove torna (motto)
- **Identità architettonica**: Grotta a volta bassa · ossa disposte in semicerchio · una vasca di pietra al centro
- **Atmosfera**: Umido di roccia · odore metallico appena percettibile · goccia costante da una stalattite
- **Simbolo**: Zanna di cinghiale bianco incastonata su goccia stilizzata
- **Colori**: rosso scuro · osso · nero cavernoso
- **Hall Master**: **Cacciatore Solitario Grim Rohl** — Nome del cacciatore che segue tracce di sangue senza pietà · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Traccia Rossa — seguire una scia di sangue di cinghiale spirito fino al punto di caduta
- **Rituale di assegnazione**: Grim segna la clavicola del Recluta con la Zanna del Bianco · nessun voto verbale, solo il gesto
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: melee bloody · self-sustain via emorragia inflitta · burst su prede ferite
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che segue il Rosso' · badge zanna e goccia · flavor log 'Il Cacciatore del Sangue ha trovato e la preda si è fermata'

### 7.7 · Faro Rovesciato di Onirade — *Cacciatore del Vuoto*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cacciatore_del_vuoto` · **class_slug**: `cacciatore_del_vuoto` · **classe_it**: Cacciatore del Vuoto
- **Regione/Location**: isolotto artificiale nel lago della Gilda · faro con la luce che punta verso il basso, verso l'acqua
- **Lore source**: Costruito dopo l'Ombra di Onirade che uscì dall'acqua e non tornò indietro · si caccia ciò che non ha peso (motto)
- **Identità architettonica**: Struttura di pietra rovesciata · lanterna verso il basso · scala a chiocciola discendente
- **Atmosfera**: Aria salmastra · silenzio dell'acqua ferma · lanterna che oscilla appena senza vento
- **Simbolo**: Lanterna rovesciata su cerchio interrotto
- **Colori**: grigio nebbia · blu abisso · nero senza riflesso
- **Hall Master**: **Cacciatrice del Vuoto Nael di Onirade** — Nome della donna che ha visto oltre l'acqua e non ha parlato · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Riflesso Vuoto — riconoscere il proprio riflesso nella lanterna rovesciata e non distoglierlo
- **Rituale di assegnazione**: Nael consegna la Lanterna Muta · nessuna parola, solo la lanterna
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: ranged void · dispel · anti-summon · counter contro incorporei
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che non ha distolto lo sguardo' · badge lanterna rovesciata · flavor log 'Il Cacciatore del Vuoto ha guardato e il vuoto ha guardato indietro'

### 7.8 · Capanno del Sentiero Selvaggio — *Cacciatore di Mostri*
- **Stato operativo**: ✅ **ACTIVE-DESIGN-READY**
- **hall_id**: `hall_cacciatore_di_mostri` · **class_slug**: `cacciatore_di_mostri` · **classe_it**: Cacciatore di Mostri
- **Regione/Location**: Capanno di legno grezzo sul limite del bosco della Gilda · trofei alle pareti, focolare aperto
- **Lore source**: Costruito dal primo cacciatore che tornò con la testa del Cinghiale Bianco · la bestia è vecchia, il cacciatore di più (motto)
- **Identità architettonica**: Baita di tronchi · focolare al centro · rastrelliera di archi lungo la parete est
- **Atmosfera**: Odore di legna bruciata e pelle conciata · fischi di rapaci notturni al di fuori
- **Simbolo**: Faretra ricurva su corno di cinghiale
- **Colori**: verde scuro · marrone corteccia · ocra
- **Hall Master**: **Vecchio Falconiere Ovyr** — Maestro del Capanno · status **LOCKED**
- **Prova safe-mode**: La Traccia del Primo Passo — seguire la traccia notturna di un cinghiale-fantasma fino all'alba
- **Rituale di assegnazione**: Ovyr consegna la Faretra del Sentiero · marchio a inchiostro d'ontano sulla mano · voto di silenzio nel bosco
- **main_stat**: Destrezza
- **armor_proficiency**: cuoio · maglia
- **weapon_proficiency**: arco · balestra · spada · pugnale · lancia
- **Stile gameplay**: ranged agile · trappole · knowledge di bestie
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Voce del Sentiero' · badge faretra e corno · flavor log 'Il Cacciatore ha camminato e il bosco lo ha lasciato passare'

### 7.9 · Camera delle Mappe Vive — *Cartografo*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cartografo` · **class_slug**: `cartografo` · **classe_it**: Cartografo
- **Regione/Location**: sala interna del Complesso · vicino all'Ufficio del Maestro Gilda
- **Lore source**: Aperta dopo la Prima Mappa che si aggiornò da sola · la mappa non descrive, la mappa ricorda (motto)
- **Identità architettonica**: Sala rettangolare con banconi lunghi · mappe appese al soffitto con corde tese · lenti d'ingrandimento sospese
- **Atmosfera**: Odore di carta antica e inchiostro fresco · brusio di penne · pergamene che frusciano appena
- **Simbolo**: Rosa dei venti con un punto cardinale in più
- **Colori**: seppia · verde muschio · blu inchiostro
- **Hall Master**: **Capomastro Cartografo Odran il Mite** — Nome del cartografo che ricorda ciò che non ha ancora camminato · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Mappa Cieca — disegnare una mappa di una stanza percorsa a occhi chiusi
- **Rituale di assegnazione**: Odran consegna il Compasso del Ricordo · marchio a inchiostro seppia sul polso
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: utility esplorativa · scouting · reveal · buff di movimento
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che disegna il Ricordo' · badge rosa dei venti · flavor log 'Il Cartografo ha inciso e la strada si è ricordata di sé'

### 7.10 · Cripta del Vessillo Nero — *Cavaliere della Morte*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cavaliere_della_morte` · **class_slug**: `cavaliere_della_morte` · **classe_it**: Cavaliere della Morte
- **Regione/Location**: sottosuolo del Complesso · cripta murata sotto l'armeria
- **Lore source**: Fondata sul Vessillo che sventolò dopo la Caduta della Prima Legione · la morte è già passata, io la seguo (motto)
- **Identità architettonica**: Cripta a volta bassa · sarcofagi lungo le pareti · vessillo nero sospeso al centro
- **Atmosfera**: Silenzio pesante · odore di cera vecchia e pietra fredda · una fiaccola sempre accesa in fondo
- **Simbolo**: Elmo chiuso su vessillo triangolare
- **Colori**: nero pece · argento freddo · rosso rappreso
- **Hall Master**: **Primo Cavaliere Nero Vaeric Rahn** — Nome del cavaliere che tornò dalla battaglia e non parlò più · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Vessillo — sostenere il Vessillo Nero per l'intero giro della cripta senza abbassarlo
- **Rituale di assegnazione**: Vaeric consegna la Cintura del Vessillo · nessuna parola, solo un cenno dell'elmo chiuso
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: melee tank/DPS ibrido · self-heal via necroenergia · aura di paura
- **Ruolo indicativo**: Hybrid
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha portato il Vessillo' · badge elmo e vessillo · flavor log 'Il Cavaliere della Morte è passato e la carne dei nemici ha ricordato di essere carne'

### 7.11 · Ariale del Signore delle Fiamme — *Cavaliere di Draghi*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cavaliere_di_draghi` · **class_slug**: `cavaliere_di_draghi` · **classe_it**: Cavaliere di Draghi
- **Regione/Location**: torre sud del Complesso · piattaforma aperta sul cielo · gabbia dei draconi giovani al piano inferiore
- **Lore source**: Aperta dopo il Patto delle Fiamme che salvò la Gilda dall'assedio · il drago non si comanda, si accompagna (motto)
- **Identità architettonica**: Piattaforma di pietra basaltica · anelli di ferro per catene · gradinata verso la gabbia dei draconi
- **Atmosfera**: Vento costante · odore di zolfo appena presente · ruggito basso da sotto
- **Simbolo**: Testa di drago stilizzata su ala aperta
- **Colori**: rosso brace · nero basalto · oro fuso
- **Hall Master**: **Signora delle Fiamme Aelor Draconis** — Nome della cavaliera che ha pattuito con il Drago Vecchio · status **PENDING_PM**
- **Prova safe-mode**: La Prova dello Sguardo — reggere lo sguardo di un draconcello senza distogliere gli occhi per un giro completo
- **Rituale di assegnazione**: Aelor consegna la Redine di Basalto · marchio a fuoco sul braccio non dominante
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: melee/ranged con montatura draconica · burst di fiamma · aura draconica
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha retto lo Sguardo' · badge drago e ala · flavor log 'Il Cavaliere di Draghi ha volato e il vento ha ricordato il suo nome'

### 7.12 · Scriptorium del Presente Eterno — *Cronista*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_cronista` · **class_slug**: `cronista` · **classe_it**: Cronista
- **Regione/Location**: biblioteca ovest del Complesso · adiacente al Circolo dei Nove Sigilli ma distinta
- **Lore source**: Fondato dopo il Giorno che non finì · ciò che viene scritto oggi accade oggi per sempre (motto)
- **Identità architettonica**: Sala lunga con banconi allineati · calamai di pietra fissi · pergamene stese su rulli sospesi
- **Atmosfera**: Silenzio di studio · gratta di penne d'oca · odore di inchiostro e cera
- **Simbolo**: Penna d'oca su clessidra ferma
- **Colori**: seppia scuro · verde salvia · pergamena chiara
- **Hall Master**: **Cronista Maggiore Ambrose di Mnemos** — Nome del cronista che tiene la memoria del presente · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Trascrizione Esatta — copiare senza errori un frammento di cronaca al primo tentativo
- **Rituale di assegnazione**: Ambrose consegna la Penna del Presente · marchio a inchiostro sul dorso della mano
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: supporto arcano/informativo · buff di narrativa · dispel via 'riscrittura' · utility investigativa
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha scritto senza cancellare' · badge penna e clessidra · flavor log 'Il Cronista ha inciso e la Gilda ha smesso di dimenticare'

### 7.13 · Radura del Salice Millenario — *Druido*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_druido` · **class_slug**: `druido` · **classe_it**: Druido
- **Regione/Location**: fuori dal Complesso · radura naturale nel bosco della Gilda · al centro un salice millenario
- **Lore source**: Consacrata dal Salice che parlò al Primo Druido · la foresta chiede prima di dare (motto)
- **Identità architettonica**: Radura circolare · salice al centro · pietre druidiche disposte a corona esterna
- **Atmosfera**: Odore di corteccia bagnata · canto lento di uccelli · vento che passa sempre da est
- **Simbolo**: Foglia di salice stilizzata su cerchio di pietre
- **Colori**: verde bosco · marrone tronco · grigio pietra
- **Hall Master**: **Druido Anziano Bran del Salice** — Nome del druido che parla ancora al Salice Millenario · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Silenzio della Foresta — ascoltare il Salice per un giro di sole senza rispondere
- **Rituale di assegnazione**: Bran incide una scaglia di corteccia sul braccio · nessun voto verbale, solo il gesto e il silenzio
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: hybrid caster/melee · shapeshift · healing naturale · elemental dot
- **Ruolo indicativo**: Hybrid
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha ascoltato il Salice' · badge foglia e pietra · flavor log 'Il Druido ha camminato e il bosco lo ha chiamato per nome'

### 7.14 · Fucina degli Anelli Silenti — *Fabbro Arcano*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_fabbro_arcano` · **class_slug**: `fabbro_arcano` · **classe_it**: Fabbro Arcano
- **Regione/Location**: sotterraneo del Complesso · adiacente all'armeria ma indipendente
- **Lore source**: Aperta dopo la Notte in cui un Anello suonò senza bocca · il metallo tace ma ricorda (motto)
- **Identità architettonica**: Fucina bassa e larga · incudini rune-incise · vasca di tempra piena di acqua argentata
- **Atmosfera**: Rumore di martello · odore di metallo bagnato · rune che brillano appena nell'ombra
- **Simbolo**: Anello circolare inciso di runa singola
- **Colori**: argento freddo · blu runico · nero forgia
- **Hall Master**: **Fabbro Anziano Corvus Anello** — Nome del fabbro che ha temprato l'Anello Silente · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Runa — incidere una runa semplice su anello grezzo al primo colpo di martello
- **Rituale di assegnazione**: Corvus consegna il Martello Personale · marchio a fuoco piccolo sull'incavo del gomito
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: crafting arcano · buff via infusion · gear enchant · utility runica
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha inciso al Primo Colpo' · badge anello runato · flavor log 'Il Fabbro Arcano ha battuto e il metallo ha ascoltato'

### 7.15 · Sala dei Dadi di Ossidiana — *Giocatore d'Azzardo*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_giocatore_d_azzardo` · **class_slug**: `giocatore_d_azzardo` · **classe_it**: Giocatore d'Azzardo
- **Regione/Location**: ala est del Complesso · sala circolare bassa · tavoli neri di ossidiana
- **Lore source**: Aperta dopo il Lancio che salvò la Gilda con un tredici impossibile · la sorte è un patto scritto in nero (motto)
- **Identità architettonica**: Sala circolare · quattro tavoli di ossidiana disposti a cardinale · sedie basse senza spalliera
- **Atmosfera**: Suono di dadi che rotolano · brusio contenuto · odore di brace e vino secco
- **Simbolo**: Dado ottaedrico con tredicesima faccia invisibile
- **Colori**: nero ossidiana · rosso patto · oro sfumato
- **Hall Master**: **Croupier Perpetuo Sylas Nod** — Nome del croupier che ha tirato il tredici impossibile · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Tredicesimo — lanciare un dado di ossidiana e leggere la faccia invisibile senza sbagliare
- **Rituale di assegnazione**: Sylas consegna i Dadi Personali (due, mai tre) · marchio con inchiostro nero sul palmo
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: utility caotica · buff/debuff RNG-based · effetti percentuali · risk-reward
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha letto il Tredicesimo' · badge dado ottaedrico · flavor log 'Il Giocatore d'Azzardo ha lanciato e la Gilda non ha perso'

### 7.16 · Fortezza d'Acciaio — *Guerriero*
- **Stato operativo**: ✅ **ACTIVE-DESIGN-READY**
- **hall_id**: `hall_guerriero` · **class_slug**: `guerriero` · **classe_it**: Guerriero
- **Regione/Location**: Ala nord del Complesso Gilda, adiacente all'armeria
- **Lore source**: Fondata al primo assedio della Gilda · l'acciaio non si spezza, si tempra (motto)
- **Identità architettonica**: Bastioni bassi in pietra grigia · piastre metalliche a soffitto · incudine centrale sempre accesa
- **Atmosfera**: Rumore di incudini · ordini gridati · odore di ferro caldo e olio d'armi
- **Simbolo**: Ascia rituale sopra sigillo circolare
- **Colori**: grigio ferro · rosso brace · ottone spento
- **Hall Master**: **Comandante Aldric del Ferro** — Comandante della Fortezza · status **LOCKED**
- **Prova safe-mode**: La Prova del Peso — sollevare l'ascia rituale e mantenere la posizione per un giro completo del braciere
- **Rituale di assegnazione**: Il Recluta impugna l'ascia · Aldric lo marchia con il Sigillo del Ferro sulla spalla · voto verbale di tempra
- **main_stat**: Forza
- **armor_proficiency**: maglia · piastre
- **weapon_proficiency**: spada · ascia · martello · scudo · lancia · arma_in_asta
- **Stile gameplay**: melee frontale · scudo/piastra · tempra sostenuta
- **Ruolo indicativo**: Tank
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Portatore del Sigillo del Ferro' · badge acciaio · flavor log 'La brace non si spegne finché il Guerriero veglia'

### 7.17 · Loggia dei Sussurri — *Ladro*
- **Stato operativo**: ✅ **ACTIVE-DESIGN-READY**
- **hall_id**: `hall_ladro` · **class_slug**: `ladro` · **classe_it**: Ladro
- **Regione/Location**: Sottoscala del Complesso Gilda · corridoi di legno scuro senza torce, solo candele
- **Lore source**: Fondata dalla prima spia entrata nella Gilda · l'ombra è alleata, il rumore è nemico (motto)
- **Identità architettonica**: Passaggi stretti · pannelli scorrevoli · pavimenti rivestiti in feltro · una sola sedia al centro
- **Atmosfera**: Silenzio innaturale · candele lente · un campanello sospeso nel corridoio finale
- **Simbolo**: Campanello immobile su cordone reciso
- **Colori**: nero corvino · verde muschio · argento spento
- **Hall Master**: **Maestra dei Sussurri Selene** — Maestra della Loggia · status **LOCKED**
- **Prova safe-mode**: La Prova del Silenzio — attraversare la Sala Buia senza far tintinnare il campanello sospeso
- **Rituale di assegnazione**: Selene consegna il Marchio della Loggia · giuramento sussurrato all'orecchio · nessun testimone se non l'ombra
- **main_stat**: Destrezza
- **armor_proficiency**: cuoio
- **weapon_proficiency**: pugnale · spada · balestra
- **Stile gameplay**: melee/ranged agile · critical strike · elusione
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Voce che non Cade' · badge campanello inciso · flavor log 'Il Ladro passa e la porta non lo ricorda'

### 7.18 · Circolo dei Nove Sigilli — *Mago*
- **Stato operativo**: ✅ **ACTIVE-DESIGN-READY**
- **hall_id**: `hall_mago` · **class_slug**: `mago` · **classe_it**: Mago
- **Regione/Location**: Torre superiore del Complesso · biblioteca a spirale, candele arcane sospese
- **Lore source**: Fondato dai Nove che sopravvissero al Rogo delle Pergamene · ogni parola letta è una parola scagliata (motto)
- **Identità architettonica**: Torre a base ottagonale · nove nicchie con altrettanti sigilli · scala a spirale interna
- **Atmosfera**: Aria fredda e ferma · pergamena vergine sempre pronta · candele che non sfrigolano
- **Simbolo**: Nove sigilli disposti a ruota attorno a un occhio aperto
- **Colori**: blu notte · oro pallido · viola violetta
- **Hall Master**: **Arcimago Vessel di Memoria** — Custode del Circolo · status **LOCKED**
- **Prova safe-mode**: Il Rito dei Nove Sigilli — tracciare il proprio sigillo personale su pergamena vergine sotto lo sguardo di Vessel
- **Rituale di assegnazione**: Vessel apre l'ottava nicchia e vi ripone il sigillo tracciato · consegna la Chiave dei Nove · nome inciso sulla parete
- **main_stat**: Intelligenza
- **armor_proficiency**: stoffa
- **weapon_proficiency**: bastone · tomo · focus · pugnale
- **Stile gameplay**: caster puro · burst magico · controllo
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Nono Sigillo' · badge sigillo tracciato · flavor log 'Il Mago ha scritto e la parola è stata udita'

### 7.19 · Loggia del Bilico Onesto — *Mercante*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_mercante` · **class_slug**: `mercante` · **classe_it**: Mercante
- **Regione/Location**: ala sud del Complesso · adiacente al mercato interno · loggia aperta a colonne
- **Lore source**: Fondata dal primo Bilico che pesò senza mentire · il prezzo giusto è quello che entrambi accettano (motto)
- **Identità architettonica**: Loggia rettangolare a colonne · bilance appese al soffitto · registri incatenati ai banconi
- **Atmosfera**: Odore di spezie, cera e pergamena · brusio di trattative · tintinnio costante di monete
- **Simbolo**: Bilancia in equilibrio perfetto su moneta stilizzata
- **Colori**: oro brunito · marrone pergamena · verde smeraldo
- **Hall Master**: **Prima Mercatrice Yara della Bilancia** — Nome della mercatrice che ha stabilito il Prezzo Giusto · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Bilico Onesto — pesare due merci diverse e stabilirne il valore equo al primo tentativo
- **Rituale di assegnazione**: Yara consegna la Bilancia Personale (piccola) · marchio a inchiostro d'oliva sul mignolo
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: utility economica · buff mercantili · dispel via 'contratto' · social utility
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha pesato senza mentire' · badge bilancia in equilibrio · flavor log 'Il Mercante ha contrattato e la Gilda ha guadagnato'

### 7.20 · Cortile della Corda di Cinabro — *Monaco*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_monaco` · **class_slug**: `monaco` · **classe_it**: Monaco
- **Regione/Location**: cortile interno del Complesso · lastricato in pietra grigia · corda cinabrina tesa tra due pilastri
- **Lore source**: Aperto dal Primo Monaco che camminò sulla Corda senza cadere · il corpo è la prima disciplina (motto)
- **Identità architettonica**: Cortile quadrato · pilastri a nord e sud · corda cinabrina tesa a mezza altezza · pietre piatte disposte a spirale
- **Atmosfera**: Silenzio spezzato solo dal passo · odore di pietra fredda · aria ferma
- **Simbolo**: Corda cinabrina tesa tra due pilastri
- **Colori**: rosso cinabro · grigio pietra · bianco osso
- **Hall Master**: **Monaco Anziano Ren Silenzio** — Nome del monaco che ha camminato sulla Corda al Primo Tentativo · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Corda — attraversare la Corda di Cinabro per l'intera lunghezza senza toccare terra
- **Rituale di assegnazione**: Ren consegna il Nastro Personale di stoffa rossa · nessuna parola, solo il nastro annodato al polso
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: melee unarmed · burst da combo · self-heal via disciplina · mobility
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha camminato sulla Corda' · badge corda annodata · flavor log 'Il Monaco ha respirato e la stanza ha rallentato'

### 7.21 · Ossario del Cerchio Chiuso — *Negromante*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_negromante` · **class_slug**: `negromante` · **classe_it**: Negromante
- **Regione/Location**: cripta profonda del Complesso · sotto la Cripta del Vessillo Nero ma indipendente
- **Lore source**: Aperto dopo il Cerchio che si chiuse da solo · ciò che è finito continua se sa il proprio nome (motto)
- **Identità architettonica**: Sala circolare · pareti rivestite di ossa disposte a mosaico · cerchio inciso al centro
- **Atmosfera**: Aria stantia dolciastra · candele nere che non si consumano · silenzio pesante
- **Simbolo**: Cerchio chiuso con teschio stilizzato al centro
- **Colori**: nero pece · viola cadaverico · osso vecchio
- **Hall Master**: **Necromante Anziano Silas Nomeperduto** — Nome del negromante che ha chiamato l'Ultima Volta · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Nome — pronunciare correttamente il proprio nome specchiato senza sbagliare la cadenza
- **Rituale di assegnazione**: Silas consegna l'Anello del Nome · nessuna parola udibile, solo il gesto e l'anello
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: caster necroenergia · summon undead pet · dot · self-drain sostenuto
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha pronunciato il Nome' · badge cerchio e teschio · flavor log 'Il Negromante ha chiamato e ciò che era finito ha risposto'

### 7.22 · Reliquiario della Luce Fissa — *Paladino*
- **Stato operativo**: ✅ **ACTIVE-DESIGN-READY**
- **hall_id**: `hall_paladino` · **class_slug**: `paladino` · **classe_it**: Paladino
- **Regione/Location**: Cappella nella corte interna del Complesso · vetrate ambrate, brace sempre accesa sull'altare
- **Lore source**: Consacrato dalla prima Custode all'alba della fondazione · la luce non chiede, la luce impone (motto)
- **Identità architettonica**: Aula a navata singola · altare centrale con brace perpetua · vetrate ambrate a occidente
- **Atmosfera**: Silenzio sacro · odore di cera e reliquia · alba filtrata attraverso l'ambra
- **Simbolo**: Brace stilizzata dentro reliquiario ovale
- **Colori**: ambra profondo · bianco crema · oro brunito
- **Hall Master**: **Custode Isabeau dell'Alba** — Custode del Reliquiario · status **LOCKED**
- **Prova safe-mode**: La Veglia della Brace — vegliare la brace dell'altare per una notte intera senza lasciare che si spenga
- **Rituale di assegnazione**: Alla prima luce Isabeau consegna il Reliquiario Personale · benedizione sull'ambra · voto di custodia
- **main_stat**: Saggezza
- **armor_proficiency**: stoffa
- **weapon_proficiency**: bastone · martello · focus · reliquia
- **Stile gameplay**: healer/support sacro · protezione · resurrezione
- **Ruolo indicativo**: Healer
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Vegliante dell'Alba' · badge brace incorniciata · flavor log 'Il Paladino veglia e la Gilda respira'

### 7.23 · Cripta della Radice Cava — *Parassita*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_parassita` · **class_slug**: `parassita` · **classe_it**: Parassita
- **Regione/Location**: grotta ipogea del Complesso · sotto il giardino della Radura del Salice Millenario ma non collegata
- **Lore source**: Aperta dopo la Radice Cava che nutrì la Gilda mangiando qualcosa d'altro · si vive di ciò che si trova (motto)
- **Identità architettonica**: Grotta bassa · pareti coperte di radici cave color osso · una vasca centrale bassa di terra scura
- **Atmosfera**: Odore terroso · gocciolio dalle radici · silenzio umido interrotto da fruscii
- **Simbolo**: Radice cava avvolta su cerchio incompleto
- **Colori**: grigio radice · marrone umido · verde muffa
- **Hall Master**: **Parassita Anziana Ada Cava** — Nome della donna che si nutrì delle Radici Cave e non morì · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Radice — riconoscere quale radice cava è viva e quale è già cava attraverso il solo tatto
- **Rituale di assegnazione**: Ada segna il collo del Recluta con una goccia di linfa scura · nessun voto verbale
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: DPS bloody · leech · stat-steal su nemici · debuff drenanti
- **Ruolo indicativo**: DPS
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha toccato la Radice Cava' · badge radice avvolta · flavor log 'Il Parassita è passato e ciò che era vivo si è ricordato che poteva anche non esserlo'

### 7.24 · Atelier dei Pigmenti Insanguinati — *Pittore*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_pittore` · **class_slug**: `pittore` · **classe_it**: Pittore
- **Regione/Location**: torretta sud-ovest del Complesso · luce zenitale · tetto a lucernario largo
- **Lore source**: Fondato dal Primo Pittore che dipinse con il proprio sangue e visse · il colore giusto costa (motto)
- **Identità architettonica**: Atelier ottagonale · cavalletti disposti a raggio · tavolozze in pietra levigata · lucernario centrale
- **Atmosfera**: Odore di olio di lino, pigmento e vernice fresca · silenzio di concentrazione · luce zenitale ferma
- **Simbolo**: Pennello incrociato con tavolozza forata
- **Colori**: rosso sangue · bianco tela · oro pigmento
- **Hall Master**: **Prima Pittrice Genoveva Rosso** — Nome della pittrice che ha dipinto la Prima Immagine Viva · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Colore Vivo — mescolare il pigmento giusto perché una tela dipinta si muova appena
- **Rituale di assegnazione**: Genoveva consegna il Pennello Personale · marchio a olio di lino sul mento
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: utility illusoria · buff via 'immagini viventi' · debuff via ritratto · summon di immagini
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha dipinto il Vivo' · badge pennello e tavolozza · flavor log 'Il Pittore ha steso il colore e il muro ha respirato'

### 7.25 · Cerchio delle Pietre Incise — *Runista*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_runista` · **class_slug**: `runista` · **classe_it**: Runista
- **Regione/Location**: prato aperto oltre il Complesso · nove pietre alte disposte in cerchio · una centrale sepolta
- **Lore source**: Consacrato dal Cerchio che si chiuse alla Prima Runa · la runa non descrive, la runa impone (motto)
- **Identità architettonica**: Cerchio di nove menhir · pietra centrale sepolta al bordo del cerchio · erba corta calpestata
- **Atmosfera**: Aria aperta · odore di pietra bagnata · fischio del vento tra le rune quando le tocchi
- **Simbolo**: Runa singola incisa dentro cerchio di pietre
- **Colori**: grigio pietra · blu runico · verde erba
- **Hall Master**: **Runista Anziano Halvard Nove** — Nome del runista che ha inciso la Nona Runa · status **PENDING_PM**
- **Prova safe-mode**: La Prova della Nona Runa — incidere una runa semplice sulla pietra centrale al primo colpo di scalpello
- **Rituale di assegnazione**: Halvard consegna lo Scalpello Personale · marchio a inchiostro di pietra sull'indice
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: caster/support con rune permanenti · buff di area · trap runiche · dispel via 'runa rotta'
- **Ruolo indicativo**: Support
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha inciso la Nona' · badge runa e cerchio · flavor log 'Il Runista ha inciso e la terra ha ricordato la parola'

### 7.26 · Capanna dei Tamburi Fermi — *Sciamano*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_sciamano` · **class_slug**: `sciamano` · **classe_it**: Sciamano
- **Regione/Location**: fuori dal Complesso · su una collina bassa · capanna di legno grezzo circondata da tamburi appesi
- **Lore source**: Fondata dallo Sciamano Vecchio che fermò i Tamburi Rotti · lo spirito non parla, lo spirito ricorda (motto)
- **Identità architettonica**: Capanna circolare · tamburi appesi lungo il perimetro esterno · focolare centrale spento
- **Atmosfera**: Odore di legna bruciata vecchia · silenzio dei tamburi fermi · vento che li tocca ma non li suona
- **Simbolo**: Tamburo fermo dentro cerchio di piume
- **Colori**: marrone terroso · rosso ocra · nero fumo
- **Hall Master**: **Sciamano Anziano Vaska Tamburo** — Nome dello sciamano che ha fermato i Tamburi Rotti · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Tamburo Fermo — battere un tamburo perché lo spirito risponda senza svegliare i Tamburi Rotti
- **Rituale di assegnazione**: Vaska consegna la Piuma Personale · nessuna parola, solo la piuma legata al colletto
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: hybrid healer/caster elementale · summon spiriti · buff totemici · elemental dot/hot
- **Ruolo indicativo**: Hybrid
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha fermato il Tamburo' · badge tamburo e piuma · flavor log 'Lo Sciamano ha battuto una volta e lo spirito ha risposto'

### 7.27 · Camera dei Sogni Aperti — *Sognatore*
- **Stato operativo**: 🔒 **PLANNED**
- **hall_id**: `hall_sognatore` · **class_slug**: `sognatore` · **classe_it**: Sognatore
- **Regione/Location**: sottotetto del Complesso · camera con soffitto affrescato di stelle · una branda al centro
- **Lore source**: Aperta dopo il Sogno che continuò svegli · il sogno è già accaduto, solo non lo sappiamo (motto)
- **Identità architettonica**: Camera quadrata bassa · affresco di stelle sul soffitto · branda di legno al centro · finestra chiusa a ovest
- **Atmosfera**: Silenzio di riposo · odore di lino e cera · aria appena tiepida
- **Simbolo**: Stella con nove punte dentro cerchio aperto
- **Colori**: blu notte · viola sogno · bianco lino
- **Hall Master**: **Sognatrice Anziana Elyrah dei Nove Sogni** — Nome della sognatrice che ha sognato il Nono Sogno e lo ha ricordato · status **PENDING_PM**
- **Prova safe-mode**: La Prova del Sogno Aperto — descrivere al risveglio un sogno guidato senza modificare alcun dettaglio
- **Rituale di assegnazione**: Elyrah consegna la Coperta dei Nove Sogni · nessuna parola, solo la coperta stesa sulla branda
- **main_stat**: PENDING_STAT_DESIGN
- **armor_proficiency**: PENDING_PROFICIENCY_DESIGN
- **weapon_proficiency**: PENDING_PROFICIENCY_DESIGN
- **Stile gameplay**: caster onirico · debuff mentali · summon di sogni · utility psichica
- **Ruolo indicativo**: Utility
- **Tratto simbolico non-combat (Q8 R18.6)**: Titolo 'Che ha sognato senza modificare' · badge stella nove punte · flavor log 'Il Sognatore ha dormito e la stanza ha ricordato ciò che non era ancora accaduto'

## Sezione 8 · 27 Hall Masters (5 LOCKED + 22 PENDING PM)
| # | class_slug | Hall Master | Titolo | Status |
|:--:|---|---|---|:--:|
| 1 | `alchimista` | **Maestra Distillatrice Ilyra Ottavia** | Titolo di rispetto per chi separa cure dai veleni | 🟡 **PENDING PM** |
| 2 | `artificiere` | **Capo Artificiere Nolan Vent** | Nome del meccanico che serve l'ingranaggio più che l'ordine | 🟡 **PENDING PM** |
| 3 | `astrologo` | **Astrologo Maggiore Cassian Vale** | Nome del lettore di cieli senza casata | 🟡 **PENDING PM** |
| 4 | `bardo` | **Bardo Maggiore Ambroise** | Nome del cantore che ha finito la Canzone Interrotta | 🟡 **PENDING PM** |
| 5 | `burattinaio` | **Prima Burattinaia Melisandre Corda** | Nome della donna che mosse il Primo Burattino | 🟡 **PENDING PM** |
| 6 | `cacciatore_del_sangue` | **Cacciatore Solitario Grim Rohl** | Nome del cacciatore che segue tracce di sangue senza pietà | 🟡 **PENDING PM** |
| 7 | `cacciatore_del_vuoto` | **Cacciatrice del Vuoto Nael di Onirade** | Nome della donna che ha visto oltre l'acqua e non ha parlato | 🟡 **PENDING PM** |
| 8 | `cacciatore_di_mostri` | **Vecchio Falconiere Ovyr** | Maestro del Capanno | 🔒 **LOCKED** |
| 9 | `cartografo` | **Capomastro Cartografo Odran il Mite** | Nome del cartografo che ricorda ciò che non ha ancora camminato | 🟡 **PENDING PM** |
| 10 | `cavaliere_della_morte` | **Primo Cavaliere Nero Vaeric Rahn** | Nome del cavaliere che tornò dalla battaglia e non parlò più | 🟡 **PENDING PM** |
| 11 | `cavaliere_di_draghi` | **Signora delle Fiamme Aelor Draconis** | Nome della cavaliera che ha pattuito con il Drago Vecchio | 🟡 **PENDING PM** |
| 12 | `cronista` | **Cronista Maggiore Ambrose di Mnemos** | Nome del cronista che tiene la memoria del presente | 🟡 **PENDING PM** |
| 13 | `druido` | **Druido Anziano Bran del Salice** | Nome del druido che parla ancora al Salice Millenario | 🟡 **PENDING PM** |
| 14 | `fabbro_arcano` | **Fabbro Anziano Corvus Anello** | Nome del fabbro che ha temprato l'Anello Silente | 🟡 **PENDING PM** |
| 15 | `giocatore_d_azzardo` | **Croupier Perpetuo Sylas Nod** | Nome del croupier che ha tirato il tredici impossibile | 🟡 **PENDING PM** |
| 16 | `guerriero` | **Comandante Aldric del Ferro** | Comandante della Fortezza | 🔒 **LOCKED** |
| 17 | `ladro` | **Maestra dei Sussurri Selene** | Maestra della Loggia | 🔒 **LOCKED** |
| 18 | `mago` | **Arcimago Vessel di Memoria** | Custode del Circolo | 🔒 **LOCKED** |
| 19 | `mercante` | **Prima Mercatrice Yara della Bilancia** | Nome della mercatrice che ha stabilito il Prezzo Giusto | 🟡 **PENDING PM** |
| 20 | `monaco` | **Monaco Anziano Ren Silenzio** | Nome del monaco che ha camminato sulla Corda al Primo Tentativo | 🟡 **PENDING PM** |
| 21 | `negromante` | **Necromante Anziano Silas Nomeperduto** | Nome del negromante che ha chiamato l'Ultima Volta | 🟡 **PENDING PM** |
| 22 | `paladino` | **Custode Isabeau dell'Alba** | Custode del Reliquiario | 🔒 **LOCKED** |
| 23 | `parassita` | **Parassita Anziana Ada Cava** | Nome della donna che si nutrì delle Radici Cave e non morì | 🟡 **PENDING PM** |
| 24 | `pittore` | **Prima Pittrice Genoveva Rosso** | Nome della pittrice che ha dipinto la Prima Immagine Viva | 🟡 **PENDING PM** |
| 25 | `runista` | **Runista Anziano Halvard Nove** | Nome del runista che ha inciso la Nona Runa | 🟡 **PENDING PM** |
| 26 | `sciamano` | **Sciamano Anziano Vaska Tamburo** | Nome dello sciamano che ha fermato i Tamburi Rotti | 🟡 **PENDING PM** |
| 27 | `sognatore` | **Sognatrice Anziana Elyrah dei Nove Sogni** | Nome della sognatrice che ha sognato il Nono Sogno e lo ha ricordato | 🟡 **PENDING PM** |

**5 LOCKED**: nomi confermati verbatim da R18.6 Q2=A (non rinominare).
**22 PENDING PM**: nomi proposti · nessuno diventa canonico senza review PM esplicita per Sala.

## Sezione 9 · 27 Safe-Mode Trial Concepts
Una prova per Sala · concept breve · design layer only · runtime enforcement deferred a R18.6 live.

| # | class_slug | Prova safe-mode | Status |
|:--:|---|---|:--:|
| 1 | `alchimista` | La Prova della Goccia — separare correttamente una goccia curativa da una tossica con la sola bilancia | 🟡 PENDING PM |
| 2 | `artificiere` | La Prova dell'Ingranaggio — rimontare un meccanismo composto da otto pezzi entro un giro di clessidra a sabbia rossa | 🟡 PENDING PM |
| 3 | `astrologo` | La Prova della Costellazione — riconoscere una costellazione fissa nell'orizzonte capovolto della cupola | 🟡 PENDING PM |
| 4 | `bardo` | La Prova della Nota Mancante — completare la Canzone Interrotta trovando la nota giusta al primo tentativo | 🟡 PENDING PM |
| 5 | `burattinaio` | La Prova del Filo — muovere una marionetta di ferro attraverso il palco senza far cadere il campanello sospeso | 🟡 PENDING PM |
| 6 | `cacciatore_del_sangue` | La Prova della Traccia Rossa — seguire una scia di sangue di cinghiale spirito fino al punto di caduta | 🟡 PENDING PM |
| 7 | `cacciatore_del_vuoto` | La Prova del Riflesso Vuoto — riconoscere il proprio riflesso nella lanterna rovesciata e non distoglierlo | 🟡 PENDING PM |
| 8 | `cacciatore_di_mostri` | La Traccia del Primo Passo — seguire la traccia notturna di un cinghiale-fantasma fino all'alba | 🔒 LOCKED |
| 9 | `cartografo` | La Prova della Mappa Cieca — disegnare una mappa di una stanza percorsa a occhi chiusi | 🟡 PENDING PM |
| 10 | `cavaliere_della_morte` | La Prova del Vessillo — sostenere il Vessillo Nero per l'intero giro della cripta senza abbassarlo | 🟡 PENDING PM |
| 11 | `cavaliere_di_draghi` | La Prova dello Sguardo — reggere lo sguardo di un draconcello senza distogliere gli occhi per un giro completo | 🟡 PENDING PM |
| 12 | `cronista` | La Prova della Trascrizione Esatta — copiare senza errori un frammento di cronaca al primo tentativo | 🟡 PENDING PM |
| 13 | `druido` | La Prova del Silenzio della Foresta — ascoltare il Salice per un giro di sole senza rispondere | 🟡 PENDING PM |
| 14 | `fabbro_arcano` | La Prova della Runa — incidere una runa semplice su anello grezzo al primo colpo di martello | 🟡 PENDING PM |
| 15 | `giocatore_d_azzardo` | La Prova del Tredicesimo — lanciare un dado di ossidiana e leggere la faccia invisibile senza sbagliare | 🟡 PENDING PM |
| 16 | `guerriero` | La Prova del Peso — sollevare l'ascia rituale e mantenere la posizione per un giro completo del braciere | 🔒 LOCKED |
| 17 | `ladro` | La Prova del Silenzio — attraversare la Sala Buia senza far tintinnare il campanello sospeso | 🔒 LOCKED |
| 18 | `mago` | Il Rito dei Nove Sigilli — tracciare il proprio sigillo personale su pergamena vergine sotto lo sguardo di Vessel | 🔒 LOCKED |
| 19 | `mercante` | La Prova del Bilico Onesto — pesare due merci diverse e stabilirne il valore equo al primo tentativo | 🟡 PENDING PM |
| 20 | `monaco` | La Prova della Corda — attraversare la Corda di Cinabro per l'intera lunghezza senza toccare terra | 🟡 PENDING PM |
| 21 | `negromante` | La Prova del Nome — pronunciare correttamente il proprio nome specchiato senza sbagliare la cadenza | 🟡 PENDING PM |
| 22 | `paladino` | La Veglia della Brace — vegliare la brace dell'altare per una notte intera senza lasciare che si spenga | 🔒 LOCKED |
| 23 | `parassita` | La Prova della Radice — riconoscere quale radice cava è viva e quale è già cava attraverso il solo tatto | 🟡 PENDING PM |
| 24 | `pittore` | La Prova del Colore Vivo — mescolare il pigmento giusto perché una tela dipinta si muova appena | 🟡 PENDING PM |
| 25 | `runista` | La Prova della Nona Runa — incidere una runa semplice sulla pietra centrale al primo colpo di scalpello | 🟡 PENDING PM |
| 26 | `sciamano` | La Prova del Tamburo Fermo — battere un tamburo perché lo spirito risponda senza svegliare i Tamburi Rotti | 🟡 PENDING PM |
| 27 | `sognatore` | La Prova del Sogno Aperto — descrivere al risveglio un sogno guidato senza modificare alcun dettaglio | 🟡 PENDING PM |

## Sezione 10 · 27 Symbolic Non-Combat Traits (Q8 R18.6 verbatim)
**Vincolo**: solo simbolico/narrativo/UI flavor. **NO stat bonus · NO combat bonus · NO economy bonus · NO ranking bonus · NO progression bonus**. I talenti veri sono **gate futuro separato**.

| # | class_slug | Tratto simbolico |
|:--:|---|---|
| 1 | `alchimista` | Titolo 'Mano che Separa' · badge alambicco · flavor log 'L'Alchimista ha misurato e la Gilda è più leggera di un veleno' |
| 2 | `artificiere` | Titolo 'Mano che Ripara' · badge ingranaggio · flavor log 'L'Artificiere ha stretto la vite e la Gilda ha respirato' |
| 3 | `astrologo` | Titolo 'Che ha visto il Tredicesimo' · badge zodiaco tacca · flavor log 'L'Astrologo ha guardato in alto e la Gilda ha camminato dritta' |
| 4 | `bardo` | Titolo 'Che ha completato la Canzone' · badge liuto e nota · flavor log 'Il Bardo ha cantato e la stanza ha smesso di temere' |
| 5 | `burattinaio` | Titolo 'Che ha mosso il Ferro' · badge marionetta · flavor log 'Il Burattinaio ha tirato il filo e la scena ha risposto' |
| 6 | `cacciatore_del_sangue` | Titolo 'Che segue il Rosso' · badge zanna e goccia · flavor log 'Il Cacciatore del Sangue ha trovato e la preda si è fermata' |
| 7 | `cacciatore_del_vuoto` | Titolo 'Che non ha distolto lo sguardo' · badge lanterna rovesciata · flavor log 'Il Cacciatore del Vuoto ha guardato e il vuoto ha guardato indietro' |
| 8 | `cacciatore_di_mostri` | Titolo 'Voce del Sentiero' · badge faretra e corno · flavor log 'Il Cacciatore ha camminato e il bosco lo ha lasciato passare' |
| 9 | `cartografo` | Titolo 'Che disegna il Ricordo' · badge rosa dei venti · flavor log 'Il Cartografo ha inciso e la strada si è ricordata di sé' |
| 10 | `cavaliere_della_morte` | Titolo 'Che ha portato il Vessillo' · badge elmo e vessillo · flavor log 'Il Cavaliere della Morte è passato e la carne dei nemici ha ricordato di essere carne' |
| 11 | `cavaliere_di_draghi` | Titolo 'Che ha retto lo Sguardo' · badge drago e ala · flavor log 'Il Cavaliere di Draghi ha volato e il vento ha ricordato il suo nome' |
| 12 | `cronista` | Titolo 'Che ha scritto senza cancellare' · badge penna e clessidra · flavor log 'Il Cronista ha inciso e la Gilda ha smesso di dimenticare' |
| 13 | `druido` | Titolo 'Che ha ascoltato il Salice' · badge foglia e pietra · flavor log 'Il Druido ha camminato e il bosco lo ha chiamato per nome' |
| 14 | `fabbro_arcano` | Titolo 'Che ha inciso al Primo Colpo' · badge anello runato · flavor log 'Il Fabbro Arcano ha battuto e il metallo ha ascoltato' |
| 15 | `giocatore_d_azzardo` | Titolo 'Che ha letto il Tredicesimo' · badge dado ottaedrico · flavor log 'Il Giocatore d'Azzardo ha lanciato e la Gilda non ha perso' |
| 16 | `guerriero` | Titolo 'Portatore del Sigillo del Ferro' · badge acciaio · flavor log 'La brace non si spegne finché il Guerriero veglia' |
| 17 | `ladro` | Titolo 'Voce che non Cade' · badge campanello inciso · flavor log 'Il Ladro passa e la porta non lo ricorda' |
| 18 | `mago` | Titolo 'Nono Sigillo' · badge sigillo tracciato · flavor log 'Il Mago ha scritto e la parola è stata udita' |
| 19 | `mercante` | Titolo 'Che ha pesato senza mentire' · badge bilancia in equilibrio · flavor log 'Il Mercante ha contrattato e la Gilda ha guadagnato' |
| 20 | `monaco` | Titolo 'Che ha camminato sulla Corda' · badge corda annodata · flavor log 'Il Monaco ha respirato e la stanza ha rallentato' |
| 21 | `negromante` | Titolo 'Che ha pronunciato il Nome' · badge cerchio e teschio · flavor log 'Il Negromante ha chiamato e ciò che era finito ha risposto' |
| 22 | `paladino` | Titolo 'Vegliante dell'Alba' · badge brace incorniciata · flavor log 'Il Paladino veglia e la Gilda respira' |
| 23 | `parassita` | Titolo 'Che ha toccato la Radice Cava' · badge radice avvolta · flavor log 'Il Parassita è passato e ciò che era vivo si è ricordato che poteva anche non esserlo' |
| 24 | `pittore` | Titolo 'Che ha dipinto il Vivo' · badge pennello e tavolozza · flavor log 'Il Pittore ha steso il colore e il muro ha respirato' |
| 25 | `runista` | Titolo 'Che ha inciso la Nona' · badge runa e cerchio · flavor log 'Il Runista ha inciso e la terra ha ricordato la parola' |
| 26 | `sciamano` | Titolo 'Che ha fermato il Tamburo' · badge tamburo e piuma · flavor log 'Lo Sciamano ha battuto una volta e lo spirito ha risposto' |
| 27 | `sognatore` | Titolo 'Che ha sognato senza modificare' · badge stella nove punte · flavor log 'Il Sognatore ha dormito e la stanza ha ricordato ciò che non era ancora accaduto' |

## Sezione 11 · Readiness Matrix
| # | class_slug | stats | prof | equip | gameplay | guide | tech | Overall |
|:--:|---|:--:|:--:|:--:|:--:|:--:|:--:|:--|
| 1 | `alchimista` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 2 | `artificiere` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 3 | `astrologo` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 4 | `bardo` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 5 | `burattinaio` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 6 | `cacciatore_del_sangue` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 7 | `cacciatore_del_vuoto` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 8 | `cacciatore_di_mostri` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACTIVE-DESIGN-READY** |
| 9 | `cartografo` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 10 | `cavaliere_della_morte` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 11 | `cavaliere_di_draghi` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 12 | `cronista` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 13 | `druido` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 14 | `fabbro_arcano` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 15 | `giocatore_d_azzardo` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 16 | `guerriero` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACTIVE-DESIGN-READY** |
| 17 | `ladro` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACTIVE-DESIGN-READY** |
| 18 | `mago` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACTIVE-DESIGN-READY** |
| 19 | `mercante` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 20 | `monaco` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 21 | `negromante` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 22 | `paladino` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **ACTIVE-DESIGN-READY** |
| 23 | `parassita` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 24 | `pittore` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 25 | `runista` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 26 | `sciamano` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |
| 27 | `sognatore` | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | **PLANNED** |

**Totale ACTIVE-DESIGN-READY**: 5/27 · **Totale PLANNED**: 22/27.

## Sezione 12 · Risk Register (15 rischi)
| ID | Rischio | Severity | Status |
|:--:|---|:--:|:--:|
| **R1** | 22 Hall Masters con nomi PENDING PM diventano canonici senza review | MEDIUM | DOCUMENTED |
| **R2** | Player tenta di scegliere una delle 22 Sale PLANNED prima del readiness | MEDIUM | DESIGNED |
| **R3** | Naming collision tra 'Cacciatore di Mostri' (live) e 'Cacciatore del Sangue' / 'Cacciatore del Vuoto' (planned) | LOW-MEDIUM | DOCUMENTED |
| **R4** | 'Paladino' confuso con 'priest/prete' o 'Monaco' confuso con religione | MEDIUM | DOCUMENTED |
| **R5** | Rite of Rebirth abuso via multi-account o farming risorse | MEDIUM | DESIGNED |
| **R6** | 27 classi = complessità UI/balancing | HIGH-INFO | PLANNED |
| **R7** | Hall trait simbolico Q8 R18.6 (no gameplay bonus) confuso con talenti veri | LOW | DOCUMENTED |
| **R8** | Naming NPC hall_master planned può collidere con lore Orbus esistente | LOW | OPEN_PM |
| **R9** | Player si sente forzato a scegliere Sala live (5) senza attesa realistica per 22 planned | LOW-MEDIUM | DESIGNED |
| **R10** | Registry v2 (1500 items) tocca solo 5 classi live (300×5=1500) · 22 planned senza gear canonico | MEDIUM | TRACKED |
| **R11** | Cap 3 Reclute per Gilda troppo stretto se 27 classi disponibili | LOW | DESIGNED |
| **R12** | Prova safe-mode design 27 concept può richiedere risorse UI/asset elevate | LOW-MEDIUM | DESIGNED |
| **R13** | 22 Sale planned senza gameplay identity chiara → player choice paralysis quando andranno live | MEDIUM | DOCUMENTED |
| **R14** | Rite of Rebirth applica a classi legacy (5) verso planned (22) prima che PLANNED siano live | MEDIUM | DESIGNED |
| **R15** | R18.6 design file modification accidentale (contro governance) | HIGH-BLOCK | ENFORCED |

## Sezione 13 · PM Open Questions + Implementation Recommendation
### 13.1 · PM Open Questions (8)
- **Q1** · *22 Hall Masters PENDING PM · confermo verbatim o rewrite?*
  - a) confermo tutti verbatim (22 nomi accettati)
  - b) confermo alcuni + rewrite altri (PM specifica quali)
  - c) rewrite completo (PM propone lista alternativa)
- **Q2** · *Ordine di readiness delle 22 Sale planned (quale classe passa a ACTIVE-DESIGN-READY per prima?)*
  - a) roadmap PM ordinata (specificare ordine)
  - b) release parallela in batch da 5-7 per volta
  - c) release event-driven (feedback player + priorità narrative)
- **Q3** · *Rite of Rebirth: quale costo elevato non-premium (risorse gilda specifiche · timer cooldown · trade-off progression)?*
  - a) risorse gilda alte + reset livello parziale
  - b) risorse gilda alte + reset equip specializzato
  - c) risorse gilda alte + narrativa penalty (Log Gilda pubblico)
  - d) design tecnico dedicato futuro
- **Q4** · *Prova safe-mode 27 concept · confermo storyline/mechanic o richiedo iterazione?*
  - a) confermo tutti
  - b) confermo 5 live + itero 22 planned
  - c) confermo alcuni + rewrite mirato
- **Q5** · *Cavaliere di Draghi (montatura draconica) · come integra con sistema stables esistente (Round 16.3 Phase 8)?*
  - a) draconi = subtype narrativo del sistema stables · no schema change
  - b) draconi = collection separata · gate tecnico futuro
  - c) draconi = flavor-only in R18.6.1 (no gameplay bond runtime)
- **Q6** · *Cacciatore del Sangue vs Parassita vs Negromante · overlap tematico da chiarire?*
  - a) 3 classi distinte con overlap accettato (design gradual differentiation)
  - b) merge di 2 di queste in un unica classe (PM specifica quali)
  - c) attesa iterazione dedicata di design bilanciamento
- **Q7** · *Sognatore / Pittore / Bardo (classi 'creative') · come si distinguono a livello gameplay?*
  - a) Sognatore=onirico/mentale · Pittore=illusioni visive · Bardo=sonoro/morale (design tripartito)
  - b) iterazione dedicata post-R18.6.1 con matrice comparativa
  - c) unificazione parziale (PM specifica)
- **Q8** · *27 Sale · design layout Complesso Gilda accomoda tutte fisicamente o alcune sono off-site?*
  - a) mix on-site (Complesso principale) + off-site (bosco/lago/collina/isolotto/etc)
  - b) tutte on-site (Complesso espansione futura)
  - c) 27 Sale sono narrative-only · location generica

### 13.2 · Implementation Recommendation
Ordine gate suggeriti (tutti 🔒 HOLD in attesa PM):

| # | Gate | Status |
|:--:|---|:--:|
| 1 | R18.6.1 PM review + ACK | PENDING |
| 2 | R18.3f Class Slug Migration Readiness | HOLD |
| 3 | R18.6 live implementation (5 Sale) | HOLD |
| 4 | 22 Sale planned progressive activation (una alla volta o batch) | HOLD |
| 5 | Rite of Rebirth technical gate | HOLD |
| 6 | Progressive Discovery Legendary Finalization (P1-P4) | HOLD |
| 7 | Apply Phase (Registry / Drop / Backfill / Runtime enforcement) | HOLD |
| 8 | Marketing Brief | DEFERRED |

**Explicit recommendation**:
- APPROVE R18.6.1 design (27 halls canonical · 5 ACTIVE-DESIGN-READY + 22 PLANNED · slug errata canonica applicata)
- HOLD assoluto su implementazione live e su unlock automatico 22 planned
- Rispondere a PM open questions Q1-Q8 in round dedicato prima di prossimo gate
- NO code · NO DB · NO migrations · NO runtime enforcement · NO R18.5/R18.6 modification

---

## Governance Snapshot R18.6.1
| Voce | Stato |
|---|:--:|
| Documental only regime | ENFORCED ✅ |
| Italian output | ENFORCED ✅ |
| 36 sealed files byte-identical | ✅ |
| `lore_meta.py` INVARIATO (`a18f708b…`) | ✅ |
| DB writes / code changes / migrations | 0 / 0 / 0 ✅ |
| R18.5 modification / R18.6 modification | 0 / 0 ✅ (entrambi LOCKED) |
| Auto-unlock 22 planned | BLOCKED ✅ |
| R18.3f auto-start / Apply Phase / R18.6 live | BLOCKED ✅ |
| Marketing Brief | DEFERRED ✅ |
| File deliverable R18.6.1 | 2 (`.md` + `.json`) |
| Sezioni scope coperte | 13/13 ✅ |
| Sale canoniche totali | **27 / 27** ✅ |
| ACTIVE-DESIGN-READY | 5 (guerriero · ladro · mago · paladino · cacciatore_di_mostri) |
| PLANNED | 22 |

---

## 🛑 STOP after R18.6.1 design

**Non procedere oltre senza nuovo GO PM esplicito.**

Attendo PM review + risposte a Q1-Q8 prima di qualunque handoff verso R18.3f · R18.6 live · 22 planned activation · Apply Phase · Progressive Discovery · Marketing Brief.
