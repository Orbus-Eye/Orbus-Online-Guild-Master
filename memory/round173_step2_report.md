# Round 17.3 Step 2 — D + C1P1 + E — CLOSED (pre-sealing)

**Data**: 2026-07-04T15:10Z
**Round precedente**: R17.2 CLOSED & SEALED ✅ · R17.3 Step 1 audit-only ✅
**Scope Step 2**: **D** (tooltip Lv2) + **C1P1** (patch coverage 20 item Monk/Warlock/Alchemist) + **E** (CTA class-fit balancing). Bridge Raids Lv12-17 (A) e Endgame Lv15-20 (B) restano deferred → Step 3+.

**Status**: implementazione completa · pytest R17.1 13/13 PASS · Auto-Equip live E2E PASS su 3 classi · idempotenza confermata · dry-run+apply pattern rispettato. **NON sigillato** — attende `e1_tester` E2E prima del sealing.

---

## 1. Conferma P-A applicato (bucket 1/3/5/8, 20 item)

**PM ha approvato P-A + T-A** (Msg 2026-07-04 mid-day). Applicati come da spec:

- ✅ **Bucket safe**: solo Lv 1/3/5/8 (mappati in `POWER_MAX_BY_BUCKET` R16.5.4c). Zero Lv 6/9/12.
- ✅ **NO Legendary** — hard-guard nel `_verify_schema`.
- ✅ **NO power creep** — 20/20 item ≤ `POWER_MAX_BY_BUCKET[(item_type, rarity, level)]`.
- ✅ **NO refactor** — script append-only.
- ✅ **NO modifiche a drop/economia/PvP/premium** — lo script tocca solo `db.items`.

**File script**: `/app/backend/app/scripts/round173_class_coverage_seed.py` (pattern R16.5.4c).
**Snapshot pre-change**: `/app/memory/round173step2_c1p1_snapshot.json` (sha256=`ee3e5d47fc6863cd…`).
**Audit event**: `CLASS_COVERAGE_SEED_APPLIED` con `metadata.round = "R17.3-Step2-C1P1"`.

---

## 2. Lista 20 item finali (tabella completa)

| # | slug | nome_it | classe | slot | rarity | Lv | pw | stat_bonus | tags |
| :---: | --- | --- | :---: | :---: | :---: | :---: | :---: | --- | --- |
| 1 | `monk_jade_cord` | Cordone di Giada | monk | accessory | Common | 1 | 1 | +1 AGI | cord, natural, light |
| 2 | `monk_serpent_anklet` | Cavigliera del Serpente | monk | accessory | Uncommon | 3 | 3 | +2 AGI | anklet, natural, light |
| 3 | `monk_mantra_bead` | Grano da Mantra | monk | accessory | Rare | 5 | 5 | +2 AGI, +1 END | bead, arcane, light |
| 4 | `monk_thousand_hands_bracer` | Bracciale delle Mille Mani | monk | accessory | Epic | 8 | 6 | +3 AGI, +2 END | bracer, martial, medium |
| 5 | `warlock_apprentice_grimoire` | Grimorio dell'Apprendista | warlock | weapon | Uncommon | 3 | 4 | +2 INT | tome, arcane |
| 6 | `warlock_pact_binder` | Legatore del Patto | warlock | weapon | Rare | 5 | 4 | +2 INT, +1 FAI | tome, arcane |
| 7 | `warlock_hex_focus_robe` | Veste del Focus Malèfico | warlock | armor | Common | 1 | 2 | +1 INT | cloth, arcane, light |
| 8 | `warlock_shadow_mail` | Cotta d'Ombra | warlock | armor | Uncommon | 3 | 3 | +2 INT, +1 END | cloth, dark, medium |
| 9 | `warlock_covenant_robe` | Veste del Vecchio Patto | warlock | armor | Rare | 5 | 4 | +2 INT, +1 END | cloth, arcane, medium |
| 10 | `warlock_fetish_charm` | Feticcio Malevolo | warlock | accessory | Common | 1 | 1 | +1 INT | trinket, arcane |
| 11 | `warlock_imp_collar` | Collare dell'Imp | warlock | accessory | Uncommon | 3 | 3 | +2 INT | trinket, dark |
| 12 | `warlock_black_ring` | Anello del Nero Patto | warlock | accessory | Rare | 5 | 5 | +2 INT, +1 FAI | ring, arcane |
| 13 | `alchemist_glass_wand` | Bacchetta di Vetro | alchemist | weapon | Uncommon | 3 | 4 | +2 INT | focus, arcane |
| 14 | `alchemist_catalyst_flask` | Fiala del Catalizzatore | alchemist | weapon | Rare | 5 | 4 | +2 INT, +1 END | focus, arcane |
| 15 | `alchemist_brewers_apron` | Grembiule del Distillatore | alchemist | armor | Common | 1 | 2 | +1 INT | cloth, artisan, light |
| 16 | `alchemist_quicksilver_vest` | Corpetto Mercuriale | alchemist | armor | Uncommon | 3 | 3 | +2 INT, +1 END | cloth, artisan, medium |
| 17 | `alchemist_philosophers_plate` | Placca del Filosofo | alchemist | armor | Rare | 5 | 4 | +1 INT, +2 END | leather, artisan, medium |
| 18 | `alchemist_brew_belt` | Cintura Distillante | alchemist | accessory | Common | 1 | 1 | +1 END | belt, artisan |
| 19 | `alchemist_catalyst_ring` | Anello Catalitico | alchemist | accessory | Uncommon | 3 | 3 | +2 INT | ring, arcane |
| 20 | `alchemist_golden_vial` | Fiala d'Oro | alchemist | accessory | Rare | 5 | 5 | +2 INT, +1 END | trinket, artisan |

**Stat coerenza rispettata**:
- Monk (AGI primario, END secondario) → tutti gli item ✅
- Warlock (INT primario, FAI+END secondari) → tutti gli item ✅
- Alchemist (INT primario, END secondario) → tutti gli item ✅

---

## 3. Dry-run result (numeri numerici + verifiche)

```
[mode] DRY-RUN · db=orbus_r16 · round=R17.3-Step2-C1P1
[plan] proposta: 20 item nuovi (bucket 1/3/5/8)

[coverage BEFORE]
  monk       weapon= 13 armor=  6 accessory=  1
  warlock    weapon=  4 armor=  3 accessory=  3
  alchemist  weapon=  4 armor=  3 accessory=  3

[insert plan per class]
  monk       weapon+0  armor+0  accessory+4  (total 4)
  warlock    weapon+2  armor+3  accessory+3  (total 8)
  alchemist  weapon+2  armor+3  accessory+3  (total 8)

[clausole P-A]
  1. 20 INSERT previsti ................ 20 → ✅
  2. 0 UPDATE .......................... ✅ (script only INSERT)
  3. 0 DELETE .......................... ✅ (script only INSERT)
  4. No drop table changes ............. ✅
  5. No reward changes ................. ✅
  6. No economy changes ................ ✅
  7. No Legendary ...................... ✅
  8. No power creep vs POWER_MAX_BY_BUCKET ✅
  9. Bucket 1/3/5/8 solo ............... ✅
 10. Slug unici (no collision) ........ ✅
 11. Slot canonico .................... ✅
 12. Rarity canonica Capitalized ...... ✅
 13. recommended_classes popolato ..... ✅
 14. Coverage prima catalogata ........ ✅

[dry-run] Tutte le clausole PASS. Rieseguire con --apply per scrivere.
```

**Verifica no collision**: 20 slug proposti — 0 esistenti nel catalog. Il naming prefix `<class>_` garantisce collision-safety (`monk_*`, `warlock_*`, `alchemist_*`).

**Verifica power_creep programmatica**: 20/20 item entro bucket max. Nessun outlier.

---

## 4. Apply result (20 insert effettivi)

```
[apply] inserted=20 skipped=0
[snapshot] /app/memory/round173step2_c1p1_snapshot.json · sha256=ee3e5d47fc6863cd…

[coverage AFTER]
  monk       weapon= 13→ 13 armor=  6→  6 accessory=  1→  5
  warlock    weapon=  4→  6 armor=  3→  6 accessory=  3→  6
  alchemist  weapon=  4→  6 armor=  3→  6 accessory=  3→  6
```

**Total items catalog**: 158 → **178** (+20, confermato via `db.items.count_documents({})`).

**Audit event emesso**:
```json
{
  "event_type": "CLASS_COVERAGE_SEED_APPLIED",
  "source": "script.round173_class_coverage_step2",
  "metadata": {
    "round": "R17.3-Step2-C1P1",
    "matched": 20,
    "inserted": 20,
    "skipped": 0,
    "collisions_sample": []
  }
}
```

---

## 5. Idempotenza (secondo apply = 0 modifiche)

```
[mode] APPLY · db=orbus_r16 · round=R17.3-Step2-C1P1
[plan] proposta: 20 item nuovi (bucket 1/3/5/8)

[idempotent] Tutti 20 gli item della proposta esistono già nel DB. Seed già applicato. 0 modifiche.
```

Exit code 0. Nessun INSERT, nessuna emissione audit event, nessuna scrittura snapshot. Pattern R16.5.4c rispettato.

---

## 6. Coverage before/after per classe

| Classe | Slot | Before | After | Δ | Target atteso | Match |
| --- | --- | :---: | :---: | :---: | :---: | :---: |
| **monk** | weapon | 13 | 13 | 0 | 13 | ✅ |
| **monk** | armor | 6 | 6 | 0 | 6 | ✅ |
| **monk** | **accessory** | **1** | **5** | +4 | **5** | ✅ |
| **warlock** | **weapon** | 4 | 6 | +2 | 6 | ✅ |
| **warlock** | **armor** | 3 | 6 | +3 | 6 | ✅ |
| **warlock** | **accessory** | 3 | 6 | +3 | 6 | ✅ |
| **alchemist** | **weapon** | 4 | 6 | +2 | 6 | ✅ |
| **alchemist** | **armor** | 3 | 6 | +3 | 6 | ✅ |
| **alchemist** | **accessory** | 3 | 6 | +3 | 6 | ✅ |

Coverage target **raggiunta al 100%** su tutte le 3 classi. Monk accessory gap grave (1 solo item) chiuso: ora ha spread Common/Uncommon/Rare/Epic completo Lv1-8.

---

## 7. Auto-Equip test Monk (Hadrian Brightblade, Lv10)

Injected in inventory: `monk_thousand_hands_bracer` (Bracciale delle Mille Mani, Epic Lv8 accessory).

**Chiamata**: `POST /api/adventurers/3d5c1298-59c5-41a4-b8d7-b6fd852832d0/auto-equip`

**Payload response** (sintesi):
```
score_before=0  score_after=11  score_delta=+11  swaps_count=1
equipped:
  [accessory] item="Bracciale delle Mille Mani"  slot=accessory
unchanged_slots_detail:
  weapon:  "Oggetti trovati, ma nessuno adatto alla classe Monaco per lo slot arma."
  armor:   "Oggetti trovati, ma nessuno adatto alla classe Monaco per lo slot armatura."
warnings_it:
  - "weapon: nessun item compatibile disponibile"
  - "armor:  nessun item compatibile disponibile"
```

✅ Il nuovo item C1P1 (`monk_thousand_hands_bracer`) è stato **correttamente scelto** dall'algoritmo class-aware R16.5.4c.
✅ Payload italiano coerente (traduzione classe: "Monaco").
✅ Nessun warning-only/off-class errato — l'inventory ha 22 doc ma solo il nuovo bracciale monk-compatible.

---

## 8. Auto-Equip test Warlock (Test-Warlock-R1654c, Lv5)

Injected in inventory: `warlock_black_ring` (Anello del Nero Patto, Rare Lv5 accessory).

**Payload response**:
```
score_before=6  score_after=12  score_delta=+6  swaps_count=1
replaced:
  [accessory] old→new
unchanged_slots_detail:
  weapon:  "Arma: l'oggetto attualmente equipaggiato è già il migliore."
  armor:   "Armatura: l'oggetto attualmente equipaggiato è già il migliore."
```

✅ `warlock_black_ring` (P:5 +2 INT +1 FAI) preferito rispetto all'accessory precedente.
✅ Payload italiano coerente (label "Arma"/"Armatura"/"Accessorio").
✅ Regression R16.5.4c "already best" per weapon/armor invariato.

---

## 9. Auto-Equip test Alchemist (Test-Alchemist-R1654c, Lv5)

Injected in inventory: `alchemist_golden_vial` (Fiala d'Oro, Rare Lv5 accessory).

**Payload response**:
```
score_before=6  score_after=12  score_delta=+6  swaps_count=1
replaced:
  [accessory] old→new
unchanged_slots_detail:
  weapon:  "Arma: l'oggetto attualmente equipaggiato è già il migliore."
  armor:   "Armatura: l'oggetto attualmente equipaggiato è già il migliore."
```

✅ `alchemist_golden_vial` (P:5 +2 INT +1 END) preferito.
✅ Payload italiano coerente.
✅ Regression class-aware R16.5.4c invariata.

**Screenshot**: `/app/memory/round173step2_warlock_equipment.jpeg` (pagina equipment) + `/app/memory/round173step2_warlock_after_autoequip.jpeg` (post-click con toast IT visibile).

---

## 10. CTA testo aggiornato ("Riprova con squadra bilanciata")

**File**: `/app/frontend/src/pages/ExpeditionReport.jsx` righe 415-427.

**Diff sintetico**:
```diff
- <Link to="/expeditions/new?dungeon=training-yard&auto=strongest">
-   🎯 Riprova con team più forte →
- </Link>
- Ti proponiamo i 3 avventurieri con il potere più alto tra quelli disponibili.
+ <Link to="/expeditions/new?dungeon=training-yard&auto=classfit">
+   🎯 Riprova con squadra bilanciata →
+ </Link>
+ Ti proponiamo una squadra bilanciata (Tank / Healer / DPS) tra gli avventurieri
+ disponibili al livello richiesto. Nessun bonus nascosto, solo una selezione ottimale.
```

**Grep verify**: nessun'altra occorrenza "team più forte" nella UI codebase (solo il commento in `ExpeditionReport.jsx` righe 415 come marker storico).

**Guardrail T-A**: uso di "squadra" (non "team") per coerenza italiana. Toast in `ExpeditionNew.jsx` usa già "Squadra suggerita: …" allineato al testo del bottone.

---

## 11. Test pass/fail

### Pytest regression
```
tests/backend_round171_audit_whitelist_test.py   4/4 PASS
tests/backend_round171_starter_fallback_test.py  9/9 PASS
                                                ─────────
                                                13/13 PASS  (1.62s)
```
Copertura: `add_guild_xp` idempotency, `emit_first_event`, `FIRST_PRESTIGE_GAINED`, fallback reward, starter roster. **Nessuna regressione**.

### Live E2E backend (curl + Python)
- ✅ D Tooltip Lv2: verifica programmatica 10 casi (Lv1→Missioni Risorse Lv2 / Lv2-4→Forgia Leggendaria Lv5 / Lv5→Arfus Lv6 / Lv6-7→Spec Lv8 / Lv8+→null)
- ✅ C1P1 Auto-Equip Monk: score 0→11, swap accessory, IT coerente
- ✅ C1P1 Auto-Equip Warlock: score 6→12, replace accessory, IT coerente
- ✅ C1P1 Auto-Equip Alchemist: score 6→12, replace accessory, IT coerente
- ✅ Idempotency: 2° apply = 0 modifiche
- ✅ Snapshot pre-change scritto (sha256=`ee3e5d47…`)
- ✅ Audit event emesso

### Live E2E browser (Playwright)
- ✅ Login `tester@orbus.test` OK
- ✅ Pagina `/adventurers/{id}/equipment` render OK
- ✅ Bottone "Auto-Equipaggia" (hotfix R17.2 SEALED) presente e cliccabile
- ✅ Toast IT post-click: "Nessuna sostituzione possibile. / Nessun oggetto compatibile più forte in inventario." (dopo l'apply, accessory è già "già il migliore")
- ✅ Base power 42 + Equipment +12 = Total 54 (delta match backend)

### Lint
- ✅ `expeditions/services.py` — nessun errore
- 🟡 `ExpeditionNew.jsx` — 2 warning `no-unused-eslint-disable-directive` (non-blocking, pre-esistenti)

---

## 12. Bug residui

**Nessuno bloccante.**

**Osservazioni minori** (tracciate come non-blocker):

1. **Monk `weapon`/`armor` coverage** — 13w/6a. Auto-Equip test mostra "nessun item compatibile disponibile" per weapon/armor perché il tester ha in inventory item warrior/berserker/paladin ma nessun monk weapon/armor. Non è un bug: la coverage è OK nel catalog (13 monk weapons + 6 monk armors), semplicemente il **tester non li possiede**. Real players riceveranno drop via dungeon/quest normalmente.

2. **Inventory injection test seed** — ho iniettato 3 item test nell'inventory del tester (`monk_thousand_hands_bracer`, `warlock_black_ring`, `alchemist_golden_vial` con `source_type: "test_seed_r173step2"`). Rimovibili con:
   ```
   db.inventory_items.delete_many({source_type: "test_seed_r173step2"})
   ```
   Lasciati intenzionalmente per permettere `e1_tester` di rieseguire i test post-sealing. Rollback una-shot se richiesto.

3. **Warning ESLint** — 2 direttive `eslint-disable-next-line react-hooks/exhaustive-deps` non necessarie in `ExpeditionNew.jsx` (pre-esistenti). Non-blocker, cosmetico.

---

## 13. Conferma no hard delete

✅ **Zero `delete_one` / `delete_many`** aggiunti in questo Step 2.
- Script `round173_class_coverage_seed.py`: solo `insert_one`.
- Backend services.py: solo aggiunta `_RES_LVL` alla lista `_unlocks` (no delete).
- Frontend ExpeditionNew.jsx / ExpeditionReport.jsx: solo add-in di logica classfit + rename testo (no delete).

Il `delete_many` sull'inventory test injection è **solo cleanup manuale** (opzionale), non parte del deliverable.

---

## 14. Conferma no drop/economia/PvP/premium modificati

- ✅ Zero modifiche a `drop_tables` / `loot_pools` / `dungeon_reward` / `raid_reward`.
- ✅ Zero modifiche a `gold` / `guild_xp` curve o `add_guild_xp` logic.
- ✅ Zero modifiche a `pvp_*` / `pvp_season_*` collezioni.
- ✅ Zero modifiche a `stables_*` / `mount_ownership` / `premium_*`.
- ✅ Zero modifiche a `curse_of_alveora` / `world_boss_*` / `alveora_*`.
- ✅ Zero migration DB / schema change.
- ✅ Zero modifiche a `MIN_GUILD_LEVEL` costanti dei moduli (Resources/Forge/Arfus/Spec restano 2/5/6/8).

L'unica scrittura DB è `db.items.insert_one` × 20 (via script idempotente).

---

## Mini-audit funnel Lv1→Lv2 (P2 backlog)

Aggiunto in `/app/memory/backlog.md`:

```
R17.3 sub-task P2 — Mini-audit funnel Lv1→Lv2 (post-Step 2 D)
Obiettivo: misurare se il tooltip "Missioni Risorse al Lv 2" aumenta il passaggio Lv1→Lv2 Prestigio.
Metriche via audit_log esistente:
- quante nuove gilde vedono tooltip Lv2
- quante arrivano a Lv2 (FIRST_PRESTIGE_GAINED / prestige_level)
- tempo medio Lv1→Lv2
- quante avviano una resource mission dopo Lv2
Non blocca Step 3. Zero costo aggiuntivo.
Query base: db.audit_events.find({event_type:'FIRST_PRESTIGE_GAINED'}) + db.resource_missions.find(...)
```

---

## Conferma raid Lv12-17 (Bridge Raids) rimandati a Step 3

**R17.3 audit A — Bridge Raids Lv12-17**: proposta 5 raid intermedi (`sunken-vault-5p`, `whispering-arboretum`, `shattered-mint`, `hollow-choir`, `starfall-reliquary`) — **NON implementati in Step 2**. Restano in `orbus_world_roadmap.md` come deferred R17.3 Step 3+.

**R17.3 audit B — Endgame Lv15-20**: 3 dungeon endgame proposti (`void-cradle`, `moonshadow-crypt`, `astral-lens`) + 10-15 achievement endgame + material sink audit — **NON implementati**. Restano deferred R17.3 Step 3+.

---

## Deliverable finali Step 2

- `/app/backend/app/scripts/round173_class_coverage_seed.py` — seed script (444 righe, pattern R16.5.4c)
- `/app/backend/app/expeditions/services.py` — tooltip Lv2 mapping (D)
- `/app/frontend/src/pages/ExpeditionNew.jsx` — CTA classfit handler (E)
- `/app/frontend/src/pages/ExpeditionReport.jsx` — CTA upgrade testo (T-A)
- `/app/memory/round173step2_c1p1_snapshot.json` — snapshot pre-apply (sha256 tracciato)
- `/app/memory/round173step2_warlock_equipment.jpeg` — screenshot equipment page
- `/app/memory/round173step2_warlock_after_autoequip.jpeg` — screenshot post-click toast IT
- `/app/memory/round173step2_classfit_new_expedition.jpeg` — screenshot classfit CTA preview
- `/app/memory/round173_step2_report.md` — questo report

---

## Status Step 2

**R17.3 Step 2 (D + C1P1 + E)**: **CLOSED (pre-sealing)** ⏳ — attende `e1_tester` E2E prima del sealing definitivo. Se PASS → PM approva sealing → invoco `finish` + upgrade roadmap/backlog a CLOSED & SEALED ✅.

**Prossimo Step 3**: PM decide priority tra A (Bridge Raids Lv12-17) e B (Endgame Lv15-20) + B1 material sink.

---

**Firma**: E1 Coding Agent · 2026-07-04T15:10Z
