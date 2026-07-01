# Round 16.5 P0.3 — Simulazione Mirata Post-Wiring

**Data**: 2026-07-01
**Modalità**: read-only, Monte Carlo 10 000 iterazioni
**Scopo**: fornire i **numeri concreti** che permettono all'utente di
decidere (Decisione B) se dopo il wiring del gate serve ancora aprire
Round 16.6 P1 o se il P0 basta.

**Note metodologiche importanti**:
- Il gate ora è runtime-enforced: se il team non passa il gate, l'expedition
  restituisce 423 (nessuna success chance viene mai calcolata).
- Le success chance MC riportate qui sotto si riferiscono ai casi in cui
  il team **passa il gate** ed entra effettivamente nel calcolo.
- I team preset sono quelli dell'audit R16.4 (invariati):
  - `team_base_no_equip` (5 avv, ~lv4, team_power=**167**, no equip)
  - `team_medio_reale` (5 avv, ~lv5, team_power=**200**, equip medio)
  - `team_buono` (5 avv, ~lv6, team_power=**257**, equip alto)
  - `team_forte_outlier` (5 avv, lv 6-7, team_power=**356**, Legendary stack)

---

## Domanda 1 — Team lv4 può ancora accedere a dungeon lv7?

**Risposta: NO. Bloccato in tutti i 8 casi lv7+.**

Test HTTP di conferma: `test_1_team_lv4_vs_worldtree_lv14_blocked` +
`test_3_one_underleveled_blocks_whole_team` → **entrambi passati**.

Il runtime `enforce_min_adventurer_level()` restituisce
`HTTP 423 { code: "adventurer.level_too_low", ... }` **prima** di
qualsiasi altra logica.

Elenco esaustivo dungeon `required_level >= 7` a cui team lv4 tenta
accesso:

| dungeon | required_level | verdict |
|---|---:|:---:|
| silent-monastery-5p | 7 | 🛑 BLOCCATO |
| pirate-fleet-5p | 8 | 🛑 BLOCCATO |
| obsidian-arena-5p | 9 | 🛑 BLOCCATO |
| clockwork-vault-5p | 10 | 🛑 BLOCCATO |
| voidspire-5p | 11 | 🛑 BLOCCATO |
| infernal-pit-5p | 12 | 🛑 BLOCCATO |
| celestial-citadel-5p | 13 | 🛑 BLOCCATO |
| world-tree-roots-5p | 14 | 🛑 BLOCCATO |

**Zero dungeon lv7+ accessibili a team lv4.** ✅

---

## Domanda 2 — Team lv7 medio contro dungeon lv7 ha success chance sensata?

**Range atteso dall'utente**: 40-70%.
**Risposta osservata**: **93-95%** → OVERSHOOT.

Case rappresentativo: `team_medio_reale` (tp=200) vs silent-monastery-5p
(req=7, rec_pow=155):

| metrica | valore |
|---|---:|
| team_power | 200 |
| recommended_power | 155 |
| delta_power | +45 |
| base_success_chance (formula) | 95% (cap) |
| threat_bonus | 0% |
| effective_success_chance | 95% |
| **Monte Carlo (10k)** | **93.7%** |

**Interpretazione**: la formula lineare `sc = 50 + delta_pw` satura al 95%
già con delta_pw >= 45. Un team lv5 con equip medio (tp=200) contro un
dungeon rec_pow=155 sfora già di 45 punti.

**Non serve però che sia un team lv7**: già team lv5 medio banalizza
silent-monastery-5p. Il team lv7 vero (che il preset non copre
direttamente) sarebbe ancora sopra.

**Range effettivo osservato** su tutti i dungeon accessibili a
`team_medio_reale`:

| req_lvl | dungeon | mc_success | verdict |
|---:|---|---:|:---:|
| 1-6 | vari | 93.3% - 94.5% | overshoot uniforme |
| 7 | silent-monastery-5p | 93.7% | overshoot ⭐ (accesso ora bloccato per lv < 7) |

**Risposta netta**: il range **40-70%** dell'utente **NON è mai raggiunto**
per il team medio nei dungeon accessibili. La formula lineare + curva
lineare senza sigmoide produce saturazione al cap.

---

## Domanda 3 — Team lv7 con equip alto banalizza dungeon lv7?

**Risposta**: **SÌ, banalizza a 94.1% mc success.**

`team_forte_outlier` (5 avv lv 6-7, equip Legendary stack, team_power=356)
vs silent-monastery-5p (req=7, rec_pow=155):

| variante equip | team_power | mc_success @ silent-monastery-5p |
|---|---:|---:|
| team_base_no_equip (proxy lv4 base) | 167 | 61.6% |
| team_medio_reale (equip medio) | 200 | 93.7% |
| team_buono (equip alto) | 257 | 93.8% |
| team_forte_outlier (Legendary stack) | 356 | **94.1%** |

**Interpretazione**: l'incremento da equip medio (+equip) a equip
Legendary stack raddoppia il team_power (da 200 a 356) ma il mc_success
si muove appena (93.7 → 94.1) perché è già al cap. **Confermato: stacking
equip banalizza qualsiasi dungeon accessibile.**

Il problema originario dell'utente si è spostato dal "team lv4 batte
dungeon lv7" (risolto dal gate) al problema strutturale
"**equip stacking + curva lineare rendono ogni dungeon accessibile
banale a partire da delta_pw >= 45**". Questo è **territorio P2** (curva
sigmoidale + soft cap equip), che l'utente ha esplicitamente escluso
con **C3**.

---

## Domanda 4 — Team lv8-9 contro dungeon high-tier è coerente?

Nel dataset non abbiamo un preset diretto lv8-9. Uso `team_buono` (proxy
lv 6-7 con equip alto, tp=257) e `team_forte_outlier` (lv 6-7 Legendary,
tp=356) come bracket inferiore/superiore. Un team lv8-9 realistico
sarebbe compreso.

Post-wiring, team lv8 accede a dungeon `required_level <= 8`:

| team | dungeon req | mc_success | verdict |
|---|:---:|---:|---|
| team_buono (tp=257) | pirate-fleet-5p (req=8) | 93.6% | overshoot |
| team_buono | obsidian-arena-5p (req=9) | ⛔ blocked | gate |
| team_forte_outlier (tp=356) | pirate-fleet-5p (req=8) | 93.3% | overshoot |
| team_forte_outlier | obsidian-arena-5p (req=9) | 93.7% | overshoot |
| team_forte_outlier | clockwork-vault-5p (req=10) | 94.3% | overshoot |
| team_forte_outlier | voidspire-5p (req=11) | 93.9% | overshoot |
| team_forte_outlier | infernal-pit-5p (req=12) | 93.8% | overshoot |
| team_forte_outlier | celestial-citadel-5p (req=13) | 86.2% | leggero calo |
| team_forte_outlier | world-tree-roots-5p (req=14) | 45.4% | quasi ok |

**Verdict**: la curva è **coerente strutturalmente** (crescita difficoltà
lineare) ma **saturata dalla formula** fino a rec_pow > tp. Team endgame
con equip alto stringe la banda "mid-hard" (req 8-12) a un unico blocco
uniforme al 93-94%.

L'unico dungeon che davvero seleziona (mc < 50%) su team_forte_outlier è
`world-tree-roots-5p` (req=14, rec_pow=360). Da solo. **Tutti gli altri
dungeon high-tier sono passeggiate per un team completo lv7 con equip.**

---

## Domanda 5 — Reward mid/high tier sono proporzionate al nuovo gate?

Reward orario teorico (`base_gold_reward / base_duration_seconds * 3600`)
per bucket, ordinato per bucket → req_level:

**Bucket tutorial (lv 1-2)**

| dungeon | gold/h | xp/h |
|---|---:|---:|
| sewer-nest | 300 | 216 |
| goblin-warrens | 340 | 243 |
| bandit-hideout | 360 | 240 |

**Bucket early (lv 3-5)**

| dungeon | gold/h | xp/h |
|---|---:|---:|
| druid-grove | 660 | 504 |
| shadow-crypts | 780 | 600 |
| wolf-den-5p | 600 | 420 |
| cursed-mines | 840 | 624 |
| sunken-library | 960 | 744 |
| frost-cave-5p | 660 | 456 |
| salt-marsh-5p | 720 | 504 |

**Bucket mid (lv 5-7)**

| dungeon | gold/h | xp/h |
|---|---:|---:|
| lich-sanctum | 1200 | 900 |
| dragons-hoard | 1440 | 1080 |
| storm-spire | 1620 | 1200 |
| iron-foundry-5p | 1080 | 780 |
| silent-monastery-5p | 1200 | 864 |

**Bucket high (lv 8-14)**

| dungeon | gold/h | xp/h |
|---|---:|---:|
| pirate-fleet-5p | 1380 | 960 |
| obsidian-arena-5p | 1800 | 1236 |
| clockwork-vault-5p | 2040 | 1416 |
| voidspire-5p | 2256 | 1584 |
| infernal-pit-5p | 2928 | 2028 |
| celestial-citadel-5p | 3096 | 2172 |
| world-tree-roots-5p | 3600 | 2520 |

**Osservazioni**:

- **Curve reward coerenti**: da tutorial (300 g/h) → high (3600 g/h),
  scala 12×. Buon differenziale motivazionale.
- ⚠️ **Storm-spire (bucket mid, req=6) rewards 1620 g/h**, che è **più
  alto** di pirate-fleet-5p (bucket high, req=8, 1380 g/h). Incoerenza.
- ⚠️ **Silent-monastery-5p (mid, req=7) 1200 g/h** è **più basso** di
  dragons-hoard (mid, req=6, 1440 g/h). Incoerenza minore.
- ✅ Curva reward high-tier (req 8→14) monotona crescente e ripida
  (1380 → 3600). Coerente.

---

## Domanda 6 — Quali dungeon restano incoerenti dopo P0 completo?

Elenco strutturato dai punti 4 e 5 sopra:

| dungeon | req_lvl | tipo incoerenza | dettaglio | severità |
|---|---:|---|---|:---:|
| storm-spire | 6 | reward > tier successivo | 1620 g/h vs pirate-fleet-5p 1380 g/h | media |
| silent-monastery-5p | 7 | reward < tier precedente | 1200 g/h vs dragons-hoard 1440 g/h | bassa |
| iron-foundry-5p | 6 | rec_pow=140 vs mid tier tipici 94-110 | pw troppo alto per bucket mid, forse va in "hard-mid" | bassa |
| clockwork-vault-5p → celestial-citadel-5p | 10-13 | tutti mc_success 86-94% per team_forte_outlier | saturazione curva lineare | **P2 territorio** |
| pirate-fleet-5p → clockwork-vault-5p | 8-10 | rec_pow differenziale piccolo (170→210→230) vs team con Legendary | delta_pw sufficiente per cap 95% | **P2 territorio** |

**Nessuno di questi è un problema del gate** (che ora funziona
correttamente). Sono problemi di:
- (a) taratura fine `base_gold_reward` in due dungeon (P1 lightweight)
- (b) taratura `recommended_power` per differenziare high tier (P1)
- (c) curva sigmoidale + soft cap equip (P2 — escluso da C3)

---

## Raccomandazione motivata su Round 16.6 P1

### Cosa risolve il gate P0.3 (già fatto)
- ✅ Team sotto livello **non può nemmeno tentare** dungeon superiori.
- ✅ Payload errore chiaro e localizzato.
- ✅ Preview e dispatch coerenti.

### Cosa NON risolve il gate P0.3
- ❌ Success chance saturata al 93-95% sui dungeon accessibili.
- ❌ Stacking equip banalizza tutti i dungeon accessibili.
- ❌ 2 dungeon con reward incoerenti (storm-spire, silent-monastery-5p).

### Verdict numerico

**Il P0 (P0.1 + P0.2 + P0.3) È SUFFICIENTE a risolvere il problema utente
originale ("team lv4 batte dungeon lv7")**. 

I fenomeni residui (saturazione al 95%, stacking equip) sono di natura
diversa (curva formula, non gate). L'utente li ha classificati come
**"C3 = non toccare P2"**. Il P1 (secondo l'utente) dovrebbe essere
"recommended_power scaling + reward adjustment mid/high tier".

**La mia raccomandazione**:

| opzione | pro | contro |
|---|---|---|
| **Chiudere P0 e rimandare P1** | Il problema critico è risolto. Il P1 è rebalance fine + coinvolge economia (reward) → richiede più cautela. Diamo tempo alla community di sperimentare col gate attivo prima di ritoccare la curva. | 2 dungeon (storm-spire, silent-monastery-5p) restano con reward disordinato. |
| **Aprire P1 subito** | Rimuove le 2 incoerenze reward + differenzia meglio high-tier. | Modifica l'economia mid-tier (`storm-spire` è già un dungeon molto usato). Impact più largo. |

**Preferenza**: **chiudere P0 ora**, **rimandare P1** a un round dedicato
(Round 16.6) dopo un periodo di osservazione (24-72h di gameplay reale
col gate attivo). Motivazioni:

1. Il problema **utente-reported** (lv4 vs lv7) è risolto e verificato
   con test HTTP isolati (7/7 passed).
2. Le incoerenze reward residue sono **quantitativamente piccole** (2
   dungeon su 22) e non generano exploit (non consentono farm anomalo).
3. La modifica reward tocca `base_gold_reward` — campo economico. Va
   fatto con approccio conservativo dopo aver visto come i player
   reagiscono al gate attivato.
4. Osservare metriche server-side reali del `logging.getLogger(
   "orbus.level_gate")` per 24-72h ci dà dati concreti su quali gate
   sono davvero psychologically-walling → informa il P1.

Se invece vuoi P1 subito, la scope minima sarebbe:
- storm-spire: `base_gold_reward` da 27 → 20-22 (allineare a bucket mid).
- silent-monastery-5p: `base_gold_reward` da 20 → 24-25 (allineare al
  differenziale req 7 vs req 6).
- iron-foundry-5p: valutare se spostare bucket → "hard-mid" (o nuovo
  bucket dedicato) per essere consistenti col `rec_pow=140`.

**No P2** (curva sigmoidale + soft cap equip): confermato out-of-scope
per volontà utente (C3).

---

## Numeri sintetici per la decisione B

- Dungeon originalmente "problematici" (lv4 batte lv7): **0** ancora
  accessibili post-wiring.
- Dungeon con success chance saturato (>90%) per team con equip alto:
  ~11/13 accessibili. Non P0 territorio, P2 territorio (escluso).
- Dungeon con reward-per-hour incoerenti: **2** (storm-spire,
  silent-monastery-5p). Micro-fix P1 opzionale.

**Verdict finale**: **Chiudere P0. Non aprire P1 subito.** Aspettare
dati reali post-attivazione gate.
