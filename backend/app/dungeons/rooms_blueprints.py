"""FASE 8C (2026-08-08) — Blueprint stanze per TUTTI i dungeon canonici.

Estende il pilota Fase 5 a 22 dungeon (training-yard resta single-block:
è il tutorial day-1 e porta la logica starter-fallback dedicata).

DSL di authoring:
  * `_r(slug, name, kind, share, loot, txt)` — una stanza; `share` pesa
    durata/oro/XP (le share di ogni PERCORSO completo sommano ≈ 1.0,
    verificato dai test).
  * `_fork(fork_id, prompt, *options)` — un BIVIO: il giocatore sceglie
    il percorso; `_opt(key, label, desc, chance_mod, rooms)` definisce
    l'opzione (chance_mod si applica alle stanze dell'opzione: la via
    sicura è più facile, quella rischiosa rende di più).
  * Un'opzione può avere `rooms=[]` → SCORCIATOIA (salta alla prossima
    sezione, rinunciando a oro/XP di quel tratto).

Regole autoriali (testate):
  * il boss chiude sempre il dungeon (mai dentro un fork, mai seguito
    da altro);
  * numero stanze per difficoltà: iniziale 3, intermedio 4-6,
    avanzato 6-7, endgame 7-8 (percorso più lungo).
"""
from __future__ import annotations


def _r(slug: str, name: str, kind: str, share: float,
       loot: bool = False, txt: str = "") -> dict:
    return {
        "type": "room", "slug": slug, "name_it": name, "kind": kind,
        "duration_share": share, "gold_share": share, "xp_share": share,
        "has_loot": loot, "narrative_it": txt,
    }


def _opt(key: str, label: str, desc: str, chance_mod: int,
         rooms: list[dict]) -> dict:
    return {
        "key": key, "label_it": label, "description_it": desc,
        "chance_modifier": chance_mod, "rooms": rooms,
    }


def _fork(fork_id: str, prompt: str, *options: dict) -> dict:
    return {
        "type": "fork", "fork_id": fork_id, "prompt_it": prompt,
        "options": list(options),
    }


ROOM_BLUEPRINTS: dict[str, list[dict]] = {
    # ══ TUTORIAL / INIZIALI (3 stanze) ═════════════════════════════════
    "sewer-nest": [
        _r("cunicoli", "I Cunicoli Allagati", "ambient", 0.3, False,
           "L'acqua putrida arriva alle ginocchia. Qualcosa si muove."),
        _r("covo-ratti", "Il Covo dei Ratti", "guard", 0.3, True,
           "Un tappeto di code e denti a guardia di monete perdute."),
        _r("madre-nido", "La Madre del Nido", "boss", 0.4, True,
           "Cieca, enorme e furiosa: non lascerà passare nessuno."),
    ],
    "bandit-hideout": [
        _r("sentinelle", "Il Passo delle Sentinelle", "guard", 0.3, False,
           "Due vedette annoiate e una balestra puntata sul sentiero."),
        _r("accampamento", "L'Accampamento", "treasure", 0.3, True,
           "Tende, bottino rubato e un fuoco ancora acceso."),
        _r("capobanda", "Il Capobanda", "boss", 0.4, True,
           "Ride mentre estrae due lame: una è la tua, rubata ieri."),
    ],
    "goblin-warrens": [
        _r("posto-guardia", "Il Posto di Guardia", "guard", 0.22, False,
           "Sentinelle goblin sonnecchiano accanto a un gong d'allarme."),
        _fork(
            "via-tane", "Le tane si biforcano: da che parte?",
            _opt("cunicolo", "Cunicolo stretto",
                 "Passaggio sicuro ma povero: i goblin non ci nascondono nulla.",
                 +5, [
                     _r("cunicolo", "Il Cunicolo Stretto", "ambient", 0.2,
                        False, "Si striscia nel buio, ma nessuno vi vede."),
                 ]),
            _opt("sala-bottino", "Sala del bottino",
                 "Casse rubate alle carovane… e molte lance goblin.",
                 -8, [
                     _r("sala-bottino", "La Sala del Bottino", "treasure",
                        0.25, True,
                        "Casse sigillate: i goblin non sanno cosa valgono."),
                 ]),
        ),
        _r("trappole", "Il Corridoio delle Trappole", "ambient", 0.2, False,
           "Fili tesi e secchi di pece: ingegneria goblin al suo peggio."),
        _r("re-goblin", "La Corte del Re Goblin", "boss", 0.33, True,
           "Su un trono di ossa siede il Re, con una corona troppo grande."),
    ],

    # ══ Lv10 (4 stanze) ════════════════════════════════════════════════
    "druid-grove": [
        _r("sentiero", "Il Sentiero Invaso", "ambient", 0.2, False,
           "Rovi che si muovono controvento. Il bosco osserva."),
        _r("cerchio", "Il Cerchio di Pietre", "guard", 0.25, False,
           "Custodi di corteccia vegliano sulle pietre erette."),
        _r("radura", "La Radura delle Offerte", "treasure", 0.25, True,
           "Doni antichi ricoperti di muschio: il bosco non li reclama più."),
        _r("druido", "Il Druido Corrotto", "boss", 0.3, True,
           "Linfa nera cola dal suo bastone. La natura urla."),
    ],
    "shadow-crypts": [
        _r("scalinata", "La Scalinata Fredda", "ambient", 0.2, False,
           "Ogni gradino verso il basso ruba un po' di calore."),
        _r("ossari", "Gli Ossari", "guard", 0.25, False,
           "Le ossa nelle nicchie tremano al passaggio del gruppo."),
        _r("sala-lapidi", "La Sala delle Lapidi", "treasure", 0.25, True,
           "Corredi funebri dimenticati. I morti non ne hanno bisogno."),
        _r("ombra", "L'Ombra Senza Nome", "boss", 0.3, True,
           "Non ha volto: indossa quello di chi la guarda troppo a lungo."),
    ],
    "wolf-den-5p": [
        _r("tracce", "Le Tracce nel Fango", "ambient", 0.2, False,
           "Impronte enormi, e tutte nella stessa direzione."),
        _r("branco", "Il Branco", "guard", 0.3, False,
           "Occhi gialli tra gli alberi: sono più di quanti pensassi."),
        _r("carcasse", "La Radura delle Carcasse", "treasure", 0.2, True,
           "Ciò che i lupi non mangiano resta con le sue borse."),
        _r("alfa", "L'Alfa", "boss", 0.3, True,
           "Grigio come il ferro e il doppio degli altri."),
    ],

    # ══ Lv15 (4-5 stanze, primo bivio serio) ═══════════════════════════
    "cursed-mines": [
        _r("ingresso", "L'Ingresso Franato", "ambient", 0.18, False,
           "Le travi cedono. I picconi giacciono dove sono caduti."),
        _r("gallerie", "Le Gallerie Sussurranti", "guard", 0.22, False,
           "I minatori maledetti scavano ancora. Non serve più a nessuno."),
        _fork(
            "via-mine", "Un pozzo scende nel buio: caravella o corda?",
            _opt("montacarichi", "Montacarichi",
                 "La via dei carrelli: lenta ma battuta.", +5, [
                     _r("carrelli", "La Via dei Carrelli", "ambient", 0.2,
                        False, "Binari storti, ma il buio qui è meno fitto."),
                 ]),
            _opt("pozzo", "Il Pozzo Profondo",
                 "Dritto nel filone: la vena più ricca, i colpi più duri.",
                 -8, [
                     _r("filone", "Il Filone Ricco", "treasure", 0.25, True,
                        "Gemme grezze brillano nella roccia viva."),
                 ]),
        ),
        _r("caposquadra", "Il Caposquadra Maledetto", "boss", 0.35, True,
           "Il piccone gli è cresciuto nelle mani. Non smette di scavare."),
    ],
    "sunken-library": [
        _r("atrio", "L'Atrio Sommerso", "ambient", 0.2, False,
           "Libri gonfi d'acqua galleggiano come meduse."),
        _r("archivi", "Gli Archivi Proibiti", "guard", 0.25, False,
           "I bibliotecari annegati rimettono a posto i volumi. Per sempre."),
        _r("sala-lettura", "La Sala di Lettura", "treasure", 0.25, True,
           "Un leggio d'oro regge un tomo perfettamente asciutto."),
        _r("custode", "Il Custode del Silenzio", "boss", 0.3, True,
           "Zittisce il gruppo con un dito alle labbra. Poi attacca."),
    ],
    "frost-cave-5p": [
        _r("soglia", "La Soglia di Ghiaccio", "ambient", 0.2, False,
           "Il respiro si congela a mezz'aria."),
        _r("stalattiti", "La Sala delle Stalattiti", "guard", 0.25, False,
           "Ogni rumore può far scendere una lancia di ghiaccio."),
        _r("cuore", "Il Cuore Gelato", "treasure", 0.25, True,
           "Nel ghiaccio è intrappolato l'equipaggiamento di chi ha osato."),
        _r("gelo", "Lo Spirito del Gelo", "boss", 0.3, True,
           "Il freddo qui ha un volto, e sorride."),
    ],

    # ══ Lv20-25 (5-6 stanze, bivi con conseguenze) ═════════════════════
    "lich-sanctum": [
        _r("cancello", "Il Cancello d'Ossa", "ambient", 0.15, False,
           "Il cancello si apre da solo. Un invito, non una cortesia."),
        _r("guardia-morta", "La Guardia Morta", "guard", 0.2, False,
           "Cavalieri caduti si rialzano con la spada in pugno."),
        _fork(
            "via-sanctum", "Corridoio illuminato o cripta ossea?",
            _opt("corridoio", "Corridoio dei Ceri",
                 "Ceri accesi da secoli: la via del rituale, sorvegliata ma nota.",
                 +5, [
                     _r("ceri", "Il Corridoio dei Ceri", "ambient", 0.2,
                        False, "La cera cola verso l'alto. Meglio non chiedersi perché."),
                 ]),
            _opt("cripta", "Cripta Ossea",
                 "Il tesoro funebre del lich: ricco, e difeso dai suoi campioni.",
                 -8, [
                     _r("cripta", "La Cripta Ossea", "treasure", 0.25, True,
                        "Sarcofagi ricolmi: il lich colleziona i suoi trofei."),
                 ]),
        ),
        _r("laboratorio", "Il Laboratorio del Lich", "treasure", 0.15, True,
           "Filatteri incompleti e appunti di non-vita."),
        _r("lich", "Il Lich", "boss", 0.3, True,
           "«Mortali. Che noia meravigliosa.»"),
    ],
    "salt-marsh-5p": [
        _r("acquitrino", "L'Acquitrino", "ambient", 0.2, False,
           "Il fango tira le caviglie come mani."),
        _r("nebbie", "Le Nebbie Salmastre", "ambient", 0.2, False,
           "Le sagome nella nebbia non sono sempre del gruppo."),
        _r("villaggio", "Il Villaggio Affondato", "treasure", 0.25, True,
           "Tetti che spuntano dal fango: sotto, intere dispense."),
        _r("idra", "L'Idra della Palude", "boss", 0.35, True,
           "Ogni testa ha fame. E sono tante."),
    ],
    "dragons-hoard": [
        _r("passo", "Il Passo Bruciato", "ambient", 0.14, False,
           "Roccia vetrificata: qui il fuoco ha già vinto una volta."),
        _r("vedette", "Le Vedette Coboldi", "guard", 0.18, False,
           "I coboldi venerano il drago. E mordono per lui."),
        _fork(
            "via-tesoro", "La montagna offre due strade verso la tana.",
            _opt("cengia", "La Cengia Esterna",
                 "Vento e vertigine, ma nessuna guardia.", +5, [
                     _r("cengia", "La Cengia Esterna", "ambient", 0.18,
                        False, "Un passo falso e il dungeon finisce male."),
                 ]),
            _opt("caverne", "Le Caverne del Tributo",
                 "Dove i coboldi ammassano i doni per il drago.", -8, [
                     _r("tributo", "Le Caverne del Tributo", "treasure",
                        0.22, True,
                        "Offerte luccicanti: il drago non sentirà la differenza. Forse."),
                 ]),
        ),
        _r("anticamera", "L'Anticamera d'Oro", "treasure", 0.18, True,
           "Monete fuse in colate: il calore del padrone di casa."),
        _r("drago", "Il Drago", "boss", 0.32, True,
           "Apre un occhio. «Ladri. Che gioia.»"),
    ],
    "storm-spire": [
        _r("scala", "La Scala Sferzata", "ambient", 0.18, False,
           "Il vento vuole strappare il gruppo dalla guglia."),
        _r("parafulmini", "La Sala dei Parafulmini", "guard", 0.22, False,
           "Elementali d'aria danzano tra i conduttori."),
        _r("osservatorio", "L'Osservatorio", "treasure", 0.25, True,
           "Strumenti d'ottone che leggono i fulmini. Valgono una fortuna."),
        _r("signore-tempeste", "Il Signore delle Tempeste", "boss", 0.35,
           True, "Parla col tuono, e il tuono risponde."),
    ],
    "iron-foundry-5p": [
        _r("piazzale", "Il Piazzale delle Scorie", "ambient", 0.18, False,
           "Montagne di scarti. Alcune si muovono."),
        _r("catene", "La Catena di Montaggio", "guard", 0.22, False,
           "Golem incompleti sorvegliano i propri pezzi di ricambio."),
        _r("fonderia", "Il Crogiolo", "treasure", 0.25, True,
           "Metallo fuso e lingotti pronti: il cuore della fonderia."),
        _r("mastro-forgiatore", "Il Mastro Forgiatore", "boss", 0.35, True,
           "Metà uomo, metà incudine. Interamente ostile."),
    ],

    # ══ Lv30-45 (6 stanze, bivi + boss opzionale) ═════════════════════
    "silent-monastery-5p": [
        _r("chiostro", "Il Chiostro Muto", "ambient", 0.15, False,
           "Nessun uccello. Nessun vento. Nemmeno i passi fanno rumore."),
        _r("novizi", "I Novizi Vuoti", "guard", 0.18, False,
           "Monaci che meditano da decenni. Aprono gli occhi tutti insieme."),
        _fork(
            "via-monastero", "Il silenzio si divide in due sentieri.",
            _opt("giardino", "Il Giardino di Sabbia",
                 "Un passaggio contemplativo: nulla da temere, poco da prendere.",
                 +5, [
                     _r("giardino", "Il Giardino di Sabbia", "ambient",
                        0.17, False, "I solchi nella sabbia disegnano una preghiera."),
                 ]),
            _opt("reliquiario", "Il Reliquiario",
                 "Le reliquie dei maestri: sacre, preziose, sorvegliate.",
                 -8, [
                     _r("reliquiario", "Il Reliquiario", "treasure", 0.2,
                        True, "Ampolle e rosari d'ambra dei maestri scomparsi."),
                 ]),
        ),
        _r("campana", "La Campana Spezzata", "treasure", 0.17, True,
           "La campana che nessuno deve suonare. Attorno, offerte di secoli."),
        _r("abate", "L'Abate del Silenzio", "boss", 0.33, True,
           "Il suo voto di silenzio finisce ora. Il primo suono è un urlo."),
    ],
    "pirate-fleet-5p": [
        _r("molo", "Il Molo Nero", "ambient", 0.15, False,
           "Navi legate come bestie. Odore di polvere da sparo."),
        _r("ponte", "Il Ponte di Coperta", "guard", 0.18, False,
           "Sciabole, uncini e sorrisi senza denti."),
        _fork(
            "via-flotta", "Sottocoperta o cabina del capitano?",
            _opt("stiva", "La Stiva",
                 "Rotta sicura tra botti e casse comuni.", +5, [
                     _r("stiva", "La Stiva", "ambient", 0.17, False,
                        "Rum, corde e ratti. Il solito inventario pirata."),
                 ]),
            _opt("cabina", "La Cabina del Capitano",
                 "Mappe, oro e la guardia personale del capitano.", -8, [
                     _r("cabina", "La Cabina del Capitano", "treasure",
                        0.2, True, "Il forziere personale, con le iniziali raschiate."),
                 ]),
        ),
        _r("santabarbara", "La Santabarbara", "treasure", 0.17, True,
           "Polveri, palle di cannone e paghe non distribuite."),
        _r("ammiraglio", "L'Ammiraglio Fantasma", "boss", 0.33, True,
           "La sua nave è affondata trent'anni fa. Lui non l'ha accettato."),
    ],
    "obsidian-arena-5p": [
        _r("tunnel", "Il Tunnel dei Gladiatori", "ambient", 0.15, False,
           "Graffiti di vincitori. Molti di più dei perdenti."),
        _r("gabbie", "Le Gabbie", "guard", 0.18, False,
           "Ciò che l'arena tiene in gabbia non è mai stato umano."),
        _r("armeria", "L'Armeria dei Campioni", "treasure", 0.18, True,
           "Le armi dei caduti, affilate per il prossimo."),
        _fork(
            "via-arena", "La sabbia chiama: sfida aperta o passaggio dei vinti?",
            _opt("passaggio", "Il Passaggio dei Vinti",
                 "Sotto l'arena, tra i resti di chi ha perso.", +5, [
                     _r("vinti", "Il Passaggio dei Vinti", "ambient", 0.16,
                        False, "Qui l'arena getta ciò che non applaude più."),
                 ]),
            _opt("campione", "Il Campione in Carica",
                 "Boss opzionale: sconfiggilo e prendi la sua borsa.", -10, [
                     _r("campione", "Il Campione in Carica", "boss", 0.2,
                        True, "La folla non c'è. A lui basta il sangue."),
                 ]),
        ),
        _r("maestro-arena", "Il Maestro dell'Arena", "boss", 0.33, True,
           "Ha smesso di combattere per gli altri. Ora colleziona campioni."),
    ],
    "clockwork-vault-5p": [
        _r("ingranaggi", "La Sala degli Ingranaggi", "ambient", 0.15, False,
           "Il pavimento ruota. Le pareti contano i secondi."),
        _r("sentinelle", "Le Sentinelle a Molla", "guard", 0.18, False,
           "Si caricano a vicenda. Non dormono mai."),
        _fork(
            "via-vault", "Due condotti nel meccanismo.",
            _opt("condotto", "Il Condotto di Servizio",
                 "Stretto e unto, ma lontano dagli ingranaggi grossi.", +5, [
                     _r("condotto", "Il Condotto di Servizio", "ambient",
                        0.16, False, "Olio ovunque. Almeno non ci sono lame."),
                 ]),
            _opt("camera-molle", "La Camera delle Molle",
                 "Il deposito dei pezzi pregiati, tra pistoni impazziti.",
                 -8, [
                     _r("molle", "La Camera delle Molle", "treasure", 0.2,
                        True, "Rotismi d'oro e rubini-cuscinetto."),
                 ]),
        ),
        _r("caveau", "Il Caveau Interno", "treasure", 0.18, True,
           "La cassaforte dentro la cassaforte."),
        _r("orologiaio", "L'Orologiaio Folle", "boss", 0.33, True,
           "Ha smontato se stesso per capirsi. Ora vuole smontare voi."),
    ],
    "voidspire-5p": [
        _r("soglia-vuoto", "La Soglia del Vuoto", "ambient", 0.15, False,
           "La torre non proietta ombra. La ruba."),
        _r("eco", "La Sala degli Echi", "guard", 0.18, False,
           "Gli echi arrivano prima delle voci. E non sono d'accordo."),
        _r("frammenti", "Il Giardino di Frammenti", "treasure", 0.18, True,
           "Schegge di realtà fluttuano: alcune contengono stanze intere."),
        _fork(
            "via-vuoto", "La guglia si piega: salita esterna o cuore del Vuoto?",
            _opt("salita", "La Salita Esterna",
                 "Gravità incerta, ma il Vuoto non guarda fuori.", +5, [
                     _r("salita", "La Salita Esterna", "ambient", 0.16,
                        False, "Un gradino su tre esiste davvero."),
                 ]),
            _opt("cuore", "Il Cuore del Vuoto",
                 "Dove la torre tiene ciò che ha cancellato.", -10, [
                     _r("cuore", "Il Cuore del Vuoto", "treasure", 0.2,
                        True, "Oggetti che il mondo ha dimenticato di possedere."),
                 ]),
        ),
        _r("annientatore", "L'Annientatore", "boss", 0.33, True,
           "Non ti odia. Semplicemente non crede che tu esista."),
    ],

    # ══ Lv60-70 endgame (7-8 stanze) ═══════════════════════════════════
    "infernal-pit-5p": [
        _r("orlo", "L'Orlo della Fossa", "ambient", 0.12, False,
           "Il calore sale a ondate, come un respiro."),
        _r("catene-dannati", "Le Catene dei Dannati", "guard", 0.15, False,
           "Le catene si tendono verso il gruppo. Vogliono compagnia."),
        _r("fucine-nere", "Le Fucine Nere", "treasure", 0.15, True,
           "Armi forgiate nel tormento: il fuoco le ricorda tutte."),
        _fork(
            "via-fossa", "La fossa si avvita: ponte di basalto o gola di fiamma?",
            _opt("ponte", "Il Ponte di Basalto",
                 "Lungo, esposto, ma solido.", +5, [
                     _r("ponte", "Il Ponte di Basalto", "ambient", 0.14,
                        False, "Sotto, il magma applaude."),
                 ]),
            _opt("gola", "La Gola di Fiamma",
                 "La via dei tributi: ricchezze fuse e guardiani di brace.",
                 -10, [
                     _r("gola", "La Gola di Fiamma", "treasure", 0.17, True,
                        "Oro liquido raccolto in coppe d'ossidiana."),
                 ]),
        ),
        _r("corte-brace", "La Corte di Brace", "guard", 0.12, False,
           "Duchi minori del fuoco discutono il vostro arrivo."),
        _r("trono-cenere", "Il Trono di Cenere", "treasure", 0.1, True,
           "Ciò che resta di chi sedette qui prima del Signore."),
        _r("signore-fossa", "Il Signore della Fossa", "boss", 0.32, True,
           "«Finalmente. Il fuoco si annoiava.»"),
    ],
    "celestial-citadel-5p": [
        _r("gradinata", "La Gradinata di Luce", "ambient", 0.12, False,
           "I gradini esistono solo finché ci credi."),
        _r("araldi", "Gli Araldi", "guard", 0.15, False,
           "Annunciano il gruppo con trombe. Non è un onore: è un allarme."),
        _r("navata", "La Navata delle Stelle", "treasure", 0.15, True,
           "Costellazioni intere appese come lampadari."),
        _fork(
            "via-cittadella", "La cittadella offre giudizio o contemplazione.",
            _opt("contemplazione", "La Sala della Contemplazione",
                 "Pace vera. Persino il bottino qui è sereno.", +5, [
                     _r("contemplazione", "La Sala della Contemplazione",
                        "ambient", 0.14, False,
                        "Per un attimo, nessuno ricorda perché combattete."),
                 ]),
            _opt("giudizio", "Il Tribunale Celeste",
                 "I giudici pesano l'anima. E confiscano i beni.", -10, [
                     _r("giudizio", "Il Tribunale Celeste", "treasure",
                        0.17, True,
                        "Le prove confiscate di mille processi: reliquie, armi, corone."),
                 ]),
        ),
        _r("coro", "Il Coro Immoto", "guard", 0.14, False,
           "Un canto che non cambia nota da mille anni. Fino a oggi."),
        _r("arcangelo", "L'Arcangelo del Crepuscolo", "boss", 0.32, True,
           "Le sue ali coprono il cielo. La sua spada È il cielo."),
    ],
    "world-tree-roots-5p": [
        _r("radici-esterne", "Le Radici Esterne", "ambient", 0.11, False,
           "Radici grandi come cattedrali. Il legno respira."),
        _r("linfa", "Le Vene di Linfa", "ambient", 0.12, False,
           "Linfa dorata scorre come fiumi in piena."),
        _r("guardiani-corteccia", "I Guardiani di Corteccia", "guard",
           0.13, False, "L'Albero si difende con ciò che è: legno e furia."),
        _fork(
            "via-radici", "Le radici si intrecciano: due discese possibili.",
            _opt("spirale", "La Spirale Dolce",
                 "La via della linfa: lunga, luminosa, sorvegliata appena.",
                 +5, [
                     _r("spirale", "La Spirale Dolce", "ambient", 0.12,
                        False, "La discesa canta. L'Albero sogna."),
                 ]),
            _opt("cavita", "Le Cavità Marce",
                 "Dove l'Albero è malato: il marciume nasconde tesori inghiottiti.",
                 -10, [
                     _r("cavita", "Le Cavità Marce", "treasure", 0.15, True,
                        "Interi regni inghiottiti dalle radici, ancora carichi d'oro."),
                 ]),
        ),
        _r("cuore-radice", "Il Cuore della Radice", "treasure", 0.14, True,
           "Ambra viva racchiude i doni dei primi popoli."),
        _r("nodo", "Il Nodo del Mondo", "guard", 0.13, False,
           "Qui l'Albero stringe il mondo. E il mondo stringe i denti."),
        _r("radice-prima", "La Radice Prima", "boss", 0.32, True,
           "La prima radice, quella che tiene tutto. Si è svegliata."),
    ],
}


__all__ = ["ROOM_BLUEPRINTS"]
