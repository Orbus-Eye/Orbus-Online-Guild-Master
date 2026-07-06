# R18.5 Phase B — Gate 1 PM Decisions Lock (DOCUMENTAL ONLY)

- **Round**: `R18.5 — Itemization, ILVL & Gear Progression Rework`
- **Sottotitolo**: *Lv60 cap, item-centered endgame, lore-driven equipment*
- **Gate**: **Gate 1** (unlocks Phase C0 = PM item table drafting support)
- **Autorità**: PM Orchestrator
- **Locked at UTC**: `2026-07-06T18:00:00Z`
- **Governance**: DOCUMENTAL ONLY — 36 sigilli byte-identical, zero DB writes, zero code changes.
- **Predecessori**: `r18_5_phase_b1_design_lock.md/.json` (patched) + `r18_5_phase_b2_implementation_plan.md/.json` (patched)
- **File authoritative su**: SQ11-SQ18, lore-driven rules, legendary policy. In caso di conflitto con B.1/B.2 → **questo file prevale**.

---

## 1. Direction correction (verbatim PM)

Il round è **item-centered / ILVL-centered / lore-driven**. NON leveling / NON XP curve refactor.

### Level cap policy
- `MAX_ADVENTURER_LEVEL = 60` (**hard cap gameplay**, NON solo UI)
- `MAX_EQUIPMENT_REQUIRED_LEVEL = 60`
- Nessun adventurer > Lv60. Nessun item required > Lv60.
- XP oltre Lv60 **NON aumenta** il livello. Progressione post-Lv60 = **ILVL/equip**.
- Deprecato: `MAX_VISIBLE_LEVEL=60 UI-only` (B.1 originale).

### Player-facing item metric
- **ILVL** è la metrica principale player-facing degli oggetti.
- `equipment_pwr` è metrica calcolata secondaria (dry-run/simulazione).
- `total_power` retro-compat (nessun break).
- Range ILVL R18.5: **1-60**.

---

## 2. SQ11-SQ18 — Decisioni PM verbatim (lock definitivo)

### SQ11 — Soglia starter → endgame slot transition
**Decisione**: **Lv30 confermato**.
- Lv1-29 = **starter** (3 slot: weapon, armor, accessory).
- Lv30+ = **endgame** (6 slot: weapon, helm, chest, legs, accessory, shield).
- **Shield senza modifica distruttiva schema**: nessun gate PM aperto per shield rework, mapping R18.4 SQ1a (shield → slot_type=armor) resta valido.

### SQ12 — Tier badge colors + dual-label
**Decisione**: dual-label rarity/tier con **colori standard fantasy**.

| Tier | Rarity | Colore badge |
|---|---|---|
| T1 | Common | grigio |
| T2 | Uncommon | verde |
| T3 | Rare | blu |
| T4 | Epic | viola |
| T5 | Legendary | oro |

- **Non usare solo colore**: usare testo + `aria-label` (accessibility).
- **Rarity** = label primaria testuale.
- **Tier** = badge secondario (tooltip + colore).

### SQ13 — Signature policy
**Decisione**:
- Signature R18.5: **min 15 / target 18 / max 25**.
- Max **1 signature equipped** per adventurer (uniqueness constraint runtime).
- **Drop only**: NO crafting signature in R18.5.
- NO signature per classi non player-facing (berserker, assassin sono dormant → nessuna signature dedicata in R18.5).
- **Ogni signature approvata dal PM** individualmente (nessun auto-generate).

### SQ14 — Batch primo lotto (dimensione + distribuzione)
**Decisione**: **80 item totali** (non 100, non 120).

| Tier | Count |
|---|---|
| T1 | 24 |
| T2 | 20 |
| T3 | 20 |
| T4 | 12 |
| T5 | 4 |
| **Totale** | **80** |

- **Cap hard**: 80. Non superare senza nuovo gate PM esplicito.
- Legendary count nel batch: **max 4** (identità con T5).

### SQ15 — Endgame dungeon naming
**Decisione**: **"Cripta delle Faglie di Ambash"** (placeholder PM-approved).
- Ruolo: dungeon endgame Lv50-60.
- Fonte principale drop **T4/T5**.
- **Nessun impatto** su Goblin Warrens (resta early-only).
- Descrizione, boss, drop rate, affissi/modifier: **richiedono ulteriore GO PM** (non lockati in questo Gate 1).

### SQ16 — min_level / required_adventurer_level normalization
**Decisione**: coesistenza mantenuta con regola precedenza esplicita.

```
effective_required_level = required_adventurer_level if exists else min_level
```

- **Dry-run cross-check obbligatorio**: count entrambi campi, count divergenti, lista divergenti, proposta normalizzazione.
- **Zero write** durante dry-run.
- **No migration** senza gate PM successivo (Gate 2).

### SQ17 — Workshop level per tier
**Decisione**:

| Tier | Workshop Lv |
|---|---|
| T1 | Lv1 |
| T2 | Lv2 |
| T3 | Lv3 |
| T4 | Lv4 |
| T5 | Lv5 |

- T1 early game.
- T4/T5 **non disponibili early game**.
- **Signature fuori dal forge** (drop-only, SQ13 lock).
- **Workshop locked**: se locked al momento del test, documentare + simulare, **non forzare unlock**.

### SQ18 — Formula equipment_pwr (ricentrata su ILVL)
**Decisione**: formula riformulata intorno a ILVL.

```
equipment_pwr = ilvl + tier_bonus + slot_weight_bonus + utility_weight_bonus
```

**ILVL range per tier**:
| Tier | ILVL range |
|---|---|
| T1 | 1-15 |
| T2 | 16-30 |
| T3 | 31-45 |
| T4 | 46-55 |
| T5 | 56-60 |

**Tier bonus**:
| Tier | Bonus |
|---|---|
| T1 | +0 |
| T2 | +3 |
| T3 | +8 |
| T4 | +15 |
| T5 | +25 |

**Slot weight bonus**:
| Slot | Weight |
|---|---|
| weapon | 1.20 |
| chest | 1.15 |
| helm | 1.00 |
| legs | 1.00 |
| shield | 1.10 |
| accessory | 0.80 |

**Utility weight bonus**:
| Utility level | Bonus |
|---|---|
| none | +0 |
| minor | +3 |
| major | +8 |
| legendary | +15 |

**Vincoli formula**:
- **Solo per dry-run / simulazione**.
- **NON sostituisce** `total_power` esistente.
- **NO enforcement runtime automatico** — deve restare metrica opzionale finché non arriva Gate ulteriore per attivarla runtime.

---

## 3. Lore-driven itemization rules (verbatim PM)

### Fonti lore valide per item Rare+
Le fonti lore approvate per item T3+ (Rare, Epic, Legendary):

```
Ambash, Irthe, Velur, Efreto, Halodi, Alevora, Soe, Aveol, Ergolat,
Krastlov, Adalan, Greatwood / Elfwood, Alberi della Vita, Faglie arcane,
Vuoto, Luna Morta, Ciclo delle anime
```

### Regola tassativa
Item importanti (T3+) **NON devono essere solo "+stat"**. Devono avere **utility unica lore-legata**.

**Esempio approvato**:
> *"Lama della Faglia Quieta"* (fonte lore: **Ambash**) — riduce rischio evento arcano instabile nei dungeon magici.

**Esempio rifiutato**:
> *"Spada Epica +15 Forza"* — solo stat, nessuna utility lore-linked, nessuna fonte.

### Applicazione
- Ogni item **T3+** nel batch R18.5 avrà `lore_source` obbligatorio.
- Item **T1/T2** possono essere generic (no lore source richiesto).
- Ogni item T3+ deve dichiarare **utility narrativa** (campo dedicato in tabella C0).

---

## 4. Legendary policy (verbatim PM)

- **Massimo 4 Legendary** nel primo batch R18.5 (SQ14 lock).
- **Non craftabili** normalmente (drop only via Cripta delle Faglie di Ambash o boss encounter approvati).
- **Non ottenibili** da shop / premium / paywall.
- **Non necessari** per completare il gioco base.
- **Utility unica**, **lore-legata**, **memorabile**.
- Ogni Legendary R18.5 richiede lore source + utility approvate individualmente dal PM in C0.

---

## 5. Governance recap

- Questo file è **authoritative** su SQ11-SQ18, lore rules, legendary policy.
- In caso di conflitto con B.1/B.2 (patched) → **Gate 1 prevale**.
- Nessuna decisione di questo file è auto-attivata: tutte richiedono implementazione tramite Phase C0 → C tech → D → E.
- **Zero code change / Zero DB write** contestualmente a questo lock.

## 6. Cosa sblocca Gate 1

Con Gate 1 lockato, l'agente è autorizzato a produrre **Phase C0 — PM Item Table Drafting Support** (nuovo deliverable documentale). **NON è autorizzata** Phase C tech dry-run finché il PM non compila/approva la tabella item C0.

## 7. Cosa NON sblocca Gate 1

Gate 1 **NON autorizza**:
- Phase C tech dry-run scripts.
- Registry runtime.
- Migration reale.
- Item creation live.
- Naming finale player-facing (deve passare da C0 tabella PM).
- Stat numerici finali (idem).
- Utility narrative finali (idem).
- Drop rate finali (idem).
- Signature finali (idem).
- Legendary finali (idem).

## Self-check Gate 1

- [x] SQ11 lockato (Lv30)
- [x] SQ12 lockato (colori + dual-label + accessibility)
- [x] SQ13 lockato (15/18/25, drop-only, no dormant class signature)
- [x] SQ14 lockato (80 total: 24/20/20/12/4)
- [x] SQ15 lockato (Cripta delle Faglie di Ambash)
- [x] SQ16 lockato (precedenza + dry-run obbligatorio + no auto-fix)
- [x] SQ17 lockato (workshop Lv1-Lv5, signature out-of-forge)
- [x] SQ18 lockato (formula ILVL-based, solo dry-run, no runtime enforce)
- [x] Lore sources elencate (17 valide)
- [x] Legendary policy (4 max, non craft, non shop, utility unica)
- [x] Direction correction esplicita (level cap hard, ILVL player-facing)
- [x] Authoritative override dichiarato

**Gate 1 CLOSED**. Prossimo: **Phase C0** (documentale).
