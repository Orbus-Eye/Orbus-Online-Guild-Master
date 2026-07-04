# Round 18.0 Follow-up — Roster Distribution Query (READ-ONLY)

**Data**: 2026-07-04T16:50Z
**Scope**: solo `find/aggregate` READ. Zero write. Scopo: sbloccare le decisioni **D7** (formula roster progressivo) e **D13** (hard cap 50 + grandfathering) con dati reali.
**Fonte**: MongoDB live snapshot 2026-07-04T16:47Z, DB `orbus_r16`.

**Criterio "test guild"** (documentato): una gilda è marcata `is_test=true` se soddisfa **una qualsiasi** di:
- `owner_email` contiene `@orbus.test` (dominio test infrastrutturale)
- `users.is_test == true` (flag esplicito sul user owner)
- `guild.name` contiene la sottostringa `"test"` (case-insensitive)

Le gilde con `owner_user_id=None` (seed batch senza utente reale) sono contate come `is_test=None` → **NON considerate reali** nella sezione 5 conservativa.

---

## Risultato 1 — Gilde con >50 adventurers

**Query MongoDB**:
```python
pipeline = [
    {"$group": {"_id": "$guild_id", "count": {"$sum": 1}}},
    {"$match": {"count": {"$gt": 50}}}
]
db.adventurers.aggregate(pipeline)
```

**Risultato**: **0 gilde** hanno più di 50 adventurers.

---

## Risultato 2 — Distribuzione soglie roster

**Query**:
```python
{"$group": {"_id": "$guild_id", "count": {"$sum": 1}}}
+ post-filter Python su count > N
```

| Soglia | Numero gilde |
| :---: | :---: |
| >50 | **0** |
| >60 | **0** |
| >75 | **0** |
| >100 | **0** |

**Nessuna gilda supera la soglia 50 in nessun modo.**

---

## Risultato 3 — Top 10 gilde per numero adventurers

| Rank | count | name | guild_id (prefix) | level | is_test | owner_email |
| :---: | :---: | --- | --- | :---: | :---: | --- |
| 1 | **37** | Test Admin Guild | (redacted) | 1 | ✅ true | admin@orbus.test |
| 2 | **23** | la lanterna di ferro | 30758454-… | 15 | ✅ true | tester@orbus.test |
| 3 | 20 | R5 e1a23 | (seed batch) | 1 | ⚪ None | — |
| 4 | 20 | R5 a478d | (seed batch) | 1 | ⚪ None | — |
| 5 | 20 | R5 79801 | (seed batch) | 1 | ⚪ None | — |
| 6 | 20 | R5 4872b | (seed batch) | 1 | ⚪ None | — |
| 7 | 20 | R5 da181 | (seed batch) | 1 | ⚪ None | — |
| 8 | 20 | R5 ea371 | (seed batch) | 1 | ⚪ None | — |
| 9 | 9 | OC 28fb95 | (seed batch) | 1 | ⚪ None | — |
| 10 | 8 | OC 3da6fd | (seed batch) | 1 | ⚪ None | — |

**Nota**: le 6 gilde "R5 xxxxx" sono probabili seed batch di R5 (roster synthetic pre-esistenti, `owner_user_id=None`), non veri player. Le "OC xxxxx" sono simili (Onboarding Cohort test batch). Le uniche gilde con più di 20 avventurieri sono `Test Admin Guild` (37) e `la lanterna di ferro` (23) — entrambe **test guild**.

---

## Risultato 4 — Test guilds count

**Query**:
```python
# join adventurers → guilds → users
# is_test = (email endsWith @orbus.test) OR (users.is_test) OR (name contains "test")
```

**Risultato**: **120 test guilds** su 391 totali (30.7%).

---

## Risultato 5 — Real guilds count

**Risultato**: **271 real guilds** su 391 totali (69.3%).

**Caveat**: nel numero "real" sono conteggiate anche le gilde con `owner_user_id=None` (seed batch senza user assegnato — R5/OC/altre synthetic cohort). Un criterio più stretto ("gilda ha owner reale con email non-test") ridurrebbe ulteriormente il numero. Per D13 conservatism-first: consideriamo tutte le non-test come "reali".

---

## Risultato 6 — Distribuzione roster size (percentili)

**Query**:
```python
counts = [pg['count'] for pg in per_guild_aggregation]
counts_sorted = sorted(counts)
percentile(counts_sorted, p) = counts_sorted[int(len(counts) * p / 100)]
```

### Tutti (391 gilde)

| Metric | Valore |
| --- | :---: |
| **min** | 5 |
| **max** | 37 |
| **mean** | 5.4 |
| **p50** | 5 |
| **p75** | 5 |
| **p90** | 5 |
| **p95** | 5 |
| **p99** | 20 |

### Solo real (271 gilde)

| Metric | Valore |
| --- | :---: |
| **min** | 5 |
| **max** | 20 |
| **mean** | 5.4 |
| **p50** | 5 |
| **p75** | 5 |
| **p90** | 5 |
| **p95** | 5 |
| **p99** | 20 |

**Osservazione**: la stragrande maggioranza delle gilde ha esattamente **5 adventurers** (starter roster default). Solo il top 1% (p99) arriva a 20. La distribuzione è **estremamente skewed**: quasi tutti i player restano al roster iniziale.

---

## Risultato 7 — Adventurers grandfathered se cap 50 attivato oggi

**Query**:
```python
excess_total = sum(pg['count'] for pg in per_guild if pg['count'] > 50)
excess_over_50 = sum((pg['count']-50) for pg in per_guild if pg['count'] > 50)
```

**Risultato**:
- Adventurers totali in gilde >50: **0**
- Di cui "eccesso" oltre 50: **0**

**Nessun adventurer va grandfathered.** Il cap 50 non tocca nessuno.

---

## Risultato 8 — Real guilds bloccate da cap 50

**Risultato**: **0 real guilds** verrebbero bloccate da nuove reclute con cap 50.

---

## § Impatto potenziale D7 (formula `min(50, 10 + guild_level × 2)`)

**Formula concreta per level** (già scalata a 50 come tetto):

| guild_level | cap D7 |
| :---: | :---: |
| 1 | 12 |
| 2 | 14 |
| 3 | 16 |
| 5 | 20 |
| 7 | 24 |
| 10 | 30 |
| 15 | 40 |
| 20 | 50 |

**Analisi live vs curva D7**:

| Stato | Gilde totali | Gilde real |
| --- | :---: | :---: |
| **Sopra la curva D7** (excess > 0) | 7 | **6** |
| **Sotto la curva D7** (margine crescita) | 384 | ~265 |

**Le 6 real over-D7** (top per eccesso):

| level | cap D7 | count | excess | name (prefix) |
| :---: | :---: | :---: | :---: | --- |
| 1 | 12 | 20 | +8 | R5 e1a23 |
| 1 | 12 | 20 | +8 | R5 a478d |
| 1 | 12 | 20 | +8 | R5 79801 |
| 1 | 12 | 20 | +8 | R5 4872b |
| 1 | 12 | 20 | +8 | R5 da181 |
| 1 | 12 | 20 | +8 | R5 ea371 |

**Nota interpretativa**: tutte le 6 sono gilde "R5 xxxxx" con `owner_user_id=None` — seed batch di Round 5 (roster synthetic Lv1×20 avv). Non sono player veri, ma **contano** come "real" nel criterio conservativo (nessun `@orbus.test` nel nome). Se il PM decide di escludere anche `owner_user_id=None`, il numero scende a **0 real over-D7**.

**Impatto reale D7**:
- Con criterio conservativo: 6 gilde bloccate (tutte seed R5, non veri player) → grandfathering necessario ma cosmetico.
- Con criterio stretto (esclusi `owner=None`): **0 gilde bloccate**.
- **Nessun player reale attualmente over-D7**.

**Note formula**:
- Player Lv 1 partono con 5 avv (osservato). Formula D7 dà cap 12 = ampio margine (7 avv liberi).
- Player Lv 5 raggiungono cap 20 = ampio margine.
- La formula non è restrittiva per il gioco attuale.
- La 6-per-seed R5 avrà cap 12 al Lv1 ma diventerà cap 20 al Lv 5 → auto-si-normalizza al primo level-up.

---

## § Impatto potenziale D13 (hard cap 50 + grandfathering)

**Numero real guilds sopra 50**: **0**
**Adventurers "eccesso" oltre 50**: **0**
**Migration path grandfathering**: **BANALE** (nulla da migrare).

Il cap 50 è **completamente non-restrittivo** oggi. Anche se applicato in modo hard, nessun player verrebbe impattato:
- 0 gilde reali con count > 50
- 0 avventurieri da grandfatherare
- 0 blocchi nuove reclute
- 0 comunicazione player richiesta pre-deploy

**Conclusione tecnica**: D13 A (hard cap 50 + grandfathering) è **effettivamente equivalente** a "hard cap 50 senza migration" perché non c'è nulla da migrare. Il grandfathering è una **safety net inutilizzata oggi**, ma **utile in futuro** se una gilda dovesse crescere oltre 50 durante il periodo tra decisione e implementation R18.3.

---

## § Raccomandazione aggiornata e1_dev su D7 e D13

**In base ai dati reali (391 gilde, max 37, p99=20, 0 gilde >50)**:

1. **D13 hard cap 50 A**: **SAFE ORA**. Zero migration, zero impatto player, zero risk. Approvazione senza rischio.
2. **D7 formula progressiva A**: **SAFE ORA** con criterio stretto (esclusi seed batch `owner=None`). Con criterio conservativo, 6 gilde seed R5 sono over-curva Lv1 ma auto-normalizzate al Lv 5. Nessun player reale bloccato.
3. **Ordine consigliato**: implementare D13 (hard cap 50) e D7 (curva progressiva) **insieme** in R18.1 come `max_roster_cap = min(D13_hard_cap, D7_formula_cap) = min(50, 10 + level × 2)`. La formula D7 diventa il vero constraint attivo per gilde Lv 1-20, D13 è tetto assoluto.
4. **Enforcement**: solo SOFT in R18.1 (schema + field computed), HARD in R18.3 (`POST /adventurers/create` deny se count ≥ cap). Grandfathering trivial data i numeri attuali.
5. **Query preventiva pre-R18.3**: rieseguire questa query prima del deploy R18.3 per verificare che nessuna gilda sia cresciuta oltre cap nel frattempo. Cost trivial (aggregation su ~400 gilde).

**Raccomandazione finale a PM**: **conferma D7 A + D13 A senza modifiche**. Zero rischio operativo. R18.1 può includere entrambi.

---

## Firma

**File**: `/app/memory/round180_roster_distribution_query.md`
**Autore**: E1 Coding Agent
**Data**: 2026-07-04T16:50Z
**Guardrail**: solo query `find/aggregate` READ. Zero write. Zero apply R18.1. Zero modifica DB/codice/seed.
