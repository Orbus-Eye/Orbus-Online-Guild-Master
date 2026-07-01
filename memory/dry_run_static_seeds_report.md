# Dry-Run Report — 6 Seed Statici Cataloghi (STEP 1)

Data: 2026-07-01 12:45 UTC
DB target: `orbus_r16` (attivo, seedato dal lifespan)
Metodologia: `python -m app.scripts.<name> --dry-run`; per script che non caricano `.env` da soli si è fatto `export $(cat .env | xargs)` prima.

## Sintesi
| # | script | verdetto |
|---|---|---|
| 1 | `round160_seed_classes_v2.py` | 🔴 **DO-NOT-APPLY** — bug: manca `import uuid`, il modulo crasha su `NameError: name 'uuid' is not defined` quando prova a creare `warlock` |
| 2 | `round160_seed_races.py` | ✅ SAFE-TO-APPLY |
| 3 | `round160_seed_class_halls.py` | 🟡 **NEEDS-REVIEW** — inserirà **1510 halls** (10 per gilda × 151 gilde nel DB). Idempotente e non distruttivo, ma il numero è elevato per un DB pulito da 3 gilde reali; da valutare cleanup gilde-junk prima |
| 4 | `round15_seed_achievements.py` | ✅ SAFE-TO-APPLY — nota: usa collection `achievements_catalog` (non `achievements`) |
| 5 | `round15_seed_class_identity.py` | ✅ SAFE-TO-APPLY — richiede `export $(cat .env | xargs)` prima (no `load_dotenv` interno) |
| 6 | `round15_seed_item_tags.py` | ✅ SAFE-TO-APPLY — richiede `export $(cat .env | xargs)` prima (no `load_dotenv` interno) |

---

## 1) `round160_seed_classes_v2.py` — 🔴 DO-NOT-APPLY

1. **Path**: `/app/backend/app/scripts/round160_seed_classes_v2.py`
2. **Cosa fa**: marca 9 base classes esistenti con `is_base_class=true`; inserisce `warlock` come 10ª base; soft-deprecate `berserker/assassin/necromancer` (flag `is_active=false`, `deprecated_at`, `successor_slug`); upsert 30 specializzazioni in `class_specializations` (3 per base).
3. **`--dry-run` nativo**: SI (`argparse` + `dry_run: bool`).
4. **Output dry-run**:
   ```
   NameError: name 'uuid' is not defined
     File ".../round160_seed_classes_v2.py", line 329
     doc = {**entry, "id": str(uuid.uuid4()), ...
   ```
5. **Analisi statica**:
   - Collection scritte: `adventurer_classes` (update+insert), `class_specializations` (insert), `audit_events` (via `write_audit`).
   - Collection lette: `adventurer_classes` (`find_one` by slug), `class_specializations` (`find_one` by slug).
   - Operazioni: `update_one({"$set":...})` per base+deprecations, `insert_one` per warlock e le 30 specs, `write_audit` per ogni change.
   - Chiavi di idempotenza: `slug` (unica per classe / specialization).
6. **Count PRIMA**:
   - `adventurer_classes`: 12 (le 12 attese sono tutte attive, `warlock` MISSING).
   - `class_specializations`: 0 (collection non presente).
7. **Count previsto DOPO** (se il bug fosse fix):
   - `adventurer_classes`: 12 → 13 (aggiunta `warlock`); 9 aggiornate con `is_base_class=true`; 3 (berserker/assassin/necromancer) impostate `is_active=false, deprecated_at=…`.
   - `class_specializations`: 0 → 30.
   - `audit_events`: +42 (audit su ogni change).
8. **Idempotenza**: SI (design: legge `find_one`, skip se già come atteso).
9. **Se rilanciato**: skip base già flaggate, skip deprecations già impostate, skip specializations già presenti. Nessun duplicato.
10. **Ristrutturazione 12 → 11 base + specializzazioni** (analisi esplicita richiesta):
    - Le 12 classi correnti = warrior, rogue, mage, priest, ranger, paladin, druid, monk, bard, berserker, assassin, necromancer.
    - Lo script produce 10 base classes (le prime 9 flaggate + warlock nuova) e 3 deprecate (berserker→warrior/berserker_spec, assassin→rogue/assassin_spec, necromancer→mage/necromancer_spec).
    - Il **puzzle 11 vs 10 base**: il commento del brief utente parla di "11 classi base" ma questo script implementa **10 base + 30 specializzazioni**. Non 11.
    - **Le vecchie 3 classi (berserker/assassin/necromancer) NON vengono cancellate ma marcate `is_active=false` + successor mapping**. Coerente con la regola "no hard delete".
    - Le specializzazioni corrispondenti (`berserker_spec`, `assassin_spec`, `necromancer_spec`) sono inserite in `class_specializations` con `is_legacy_migration_target=True`, pronte per la migration di adventurers legacy (che va fatta da `round160_migrate_adventurers_deprecated_classes.py` — script BLACKLISTED).
    - **Nessun avventuriero viene toccato** da questo script (solo cataloghi).
11. **Rischi**:
    - 🔴 **ALTO**: bug `NameError: uuid` — il modulo crasha PRIMA di scrivere qualsiasi cosa. Sia dry-run che apply falliranno perché `warlock` è MISSING → entra nel branch di insert.
    - Fix richiesto (1 riga): aggiungere `import uuid` in cima al file. Modifica minima, autorizzazione utente necessaria per toccare il codice legacy.
    - Il bug è **preesistente** (già nel `_legacy`) — non causato dal recovery.
12. **Verdetto**: 🔴 **DO-NOT-APPLY** finché il bug non è fixato.

---

## 2) `round160_seed_races.py` — ✅ SAFE-TO-APPLY

1. **Path**: `/app/backend/app/scripts/round160_seed_races.py`
2. **Cosa fa**: inserisce 50 razze giocabili (30 common + 12 uncommon + 6 rare + 2 epic) in `races`. Ogni entry ha slug, name_it, name_en, rarity, lore_group, `stat_modifiers={}`, `is_playable=true`, `is_active=true`.
3. **`--dry-run` nativo**: SI.
4. **Output dry-run**: `{'dry_run': True, 'inserted': 50, 'skipped': 0, 'total': 50}`.
5. **Analisi statica**:
   - Collection scritte: `races` (insert_one), `audit_events` (via `write_audit`).
   - Chiave idempotenza: `slug` (find_one prima, skip se presente).
6. **Count PRIMA**: `races: 0`.
7. **Count previsto DOPO**: `races: 50` + `audit_events: +50`.
8. **Idempotenza**: SI.
9. **Se rilanciato**: `inserted=0, skipped=50`.
10. **Nota**: valida la distribuzione via `assert` (30+12+6+2=50), fallisce fast se qualcuno modifica la lista senza rispettare i totali.
11. **Rischi**: BASSO.
12. **Verdetto**: ✅ **SAFE-TO-APPLY**.

---

## 3) `round160_seed_class_halls.py` — 🟡 NEEDS-REVIEW

1. **Path**: `/app/backend/app/scripts/round160_seed_class_halls.py`
2. **Cosa fa**: per ogni gilda non archiviata (`archived_pre_launch != true`), crea 10 righe in `class_halls` (una per base class). Se la gilda ha almeno un avventuriero di quella classe, la hall viene marcata `is_unlocked=true`.
3. **`--dry-run` nativo**: SI.
4. **Output dry-run**: `{'guilds_seen': 151, 'halls_inserted': 1510, 'halls_skipped': 0}`.
5. **Analisi statica**:
   - Collection scritte: `class_halls` (insert_many via `seed_class_halls_for_guild` di `app.class_halls.services`).
   - Collection lette: `guilds` (find archived≠true), `adventurers` (dentro il service per determinare `is_unlocked`).
   - Idempotenza: sì (`seed_class_halls_for_guild` fa skip se già presenti per il guild_id).
6. **Count PRIMA**: `class_halls: 0`, `guilds (non archived): 151`.
7. **Count previsto DOPO**: `class_halls: 1510` (10 × 151).
8. **Idempotenza**: SI.
9. **Se rilanciato**: `halls_inserted=0, halls_skipped=1510`.
10. **⚠️ Perché NEEDS-REVIEW**:
    - `orbus_r16` è stato creato pulito 20 minuti fa. All'inizio (dopo lifespan boot) c'erano 3 gilde. Ora sono **151**. La differenza (148 gilde) è stata creata dai test pytest che ho lanciato in background prima e dai boot ripetuti. È dato "spazzatura di test", non gilde di giocatori reali.
    - Applicare questo script *ora* creerà 1510 halls per 148 gilde-junk. Non è distruttivo (idempotente), ma inquina il DB.
    - **Suggerimento**: prima di applicare, valutare cleanup delle gilde tester junk. Uno script candidato è `round14_cleanup_archive_demo_guilds.py` (usa `archived_pre_launch=true` per taggare le gilde demo, che questo script poi salterebbe). MA quello script è nella tua lista "sicura o rischiosa"? Non è in blacklist ma andrebbe letto prima.
    - Alternativa: applicare comunque (l'idempotenza ci salva), accettando il rumore.
11. **Rischi**: BASSO-MEDIO (idempotente ma il numero 1510 dipende dal numero di gilde correnti; se il DB si popola ancora prima dell'apply, cambierà).
12. **Verdetto**: 🟡 **NEEDS-REVIEW** — chiedi tu se procedere ora oppure fare cleanup gilde-junk prima.

---

## 4) `round15_seed_achievements.py` — ✅ SAFE-TO-APPLY

1. **Path**: `/app/backend/app/scripts/round15_seed_achievements.py`
2. **Cosa fa**: costruisce un catalog di achievement (dichiarato 100 nel commento, in realtà 110 nel `build_catalog()`), inserisce/aggiorna in `achievements_catalog`. Rewards **cosmetici only** (whitelist: `xp_points`, `xp_points_title`, `xp_points_badge`, `xp_points_frame`). Whitelist strict su chiavi payload (`gold`, `xp_boost`, `drop_boost` ecc. sollevano ValueError).
3. **`--dry-run` nativo**: SI.
4. **Output dry-run**:
   ```
   === Catalog build: 110 entries ===
     classi_stats        12
     consorzi             3
     crafting             8
     dungeon             12
     economia             6
     equipaggiamento     10
     leaderboard          5
     lore                 8
     meta_beta            4
     primi_passi          8
     pvp_stagioni         8
     raid                 8
     roster              10
     territorio           8
   ```
5. **Analisi statica**:
   - Collection scritte: `achievements_catalog` (insert_one o update_one), `achievement_progress` (solo create_index).
   - Collection lette: `achievements_catalog` (find_one per slug).
   - Chiave idempotenza: `slug` (dedup validato in memoria + upsert su DB).
6. **Count PRIMA**: `achievements_catalog: 0` (collection non presente nel db list); `achievements: 0`.
7. **Count previsto DOPO**: `achievements_catalog: 110`.
8. **Idempotenza**: SI — se `slug` esiste, `update_one({"$set": delta})`; altrimenti `insert_one` con `achievement_id: uuid4()` e `created_at`.
9. **Se rilanciato**: `inserted=0, updated=110` (`updated_at` cambia sempre).
10. **Anti-P2W enforcement**: `_ach()` valida `reward_type ∈ ALLOWED_REWARD_TYPES` e `FORBIDDEN_PAYLOAD_KEYS` — se un futuro contributor prova a mettere `gold` in reward_payload, il seed fallisce.
11. **Rischi**: BASSO.
12. **Verdetto**: ✅ **SAFE-TO-APPLY**.
13. **⚠️ Nota di attenzione**: crea 2 index nuovi in fase apply (`slug` unique + `category`), e su `achievement_progress` un index composito `(guild_id, achievement_slug)` unique. Sono `create_index` idempotenti, no issue.

---

## 5) `round15_seed_class_identity.py` — ✅ SAFE-TO-APPLY (con env export)

1. **Path**: `/app/backend/app/scripts/round15_seed_class_identity.py`
2. **Cosa fa**: backfill di 9 campi descrittivi (`primary_stat`, `secondary_stats`, `allowed_weapon_tags`, `allowed_armor_tags`, `preferred_item_tags`, `role_tags`, `xp_primary_stat_policy`, `guide_description_it`, `guide_description_en`) su ogni classe attiva. Include tutte e 12 le classi (comprese le 3 legacy).
3. **`--dry-run` nativo**: SI, ma **richiede `export $(cat .env | xargs)` prima** (no `load_dotenv()` interno — bug preesistente minore).
4. **Output dry-run** (con env esportate):
   ```
   adventurer_classes — total=12, active=12
   [dry-run] warrior:   would update ['allowed_armor_tags', 'allowed_weapon_tags', 'display_name_it', 'guide_description_en', 'guide_description_it', 'preferred_item_tags', 'primary_stat', 'role_tags', 'secondary_stats', 'updated_at', 'xp_primary_stat_policy']
   [dry-run] paladin:   would update [stesso set]
   ... (11 classi in totale, 12 updates)
   === SUMMARY === updated: 12, untouched: 0, conflicts: 0
   ```
5. **Analisi statica**:
   - Collection scritte: `adventurer_classes` (update_one `$set`), `audit_logs` (append event `class_identity_updated_round15`).
   - Chiave idempotenza: `slug` + diff sui campi (`doc.get(k) != v` → aggiorna solo se diverso).
6. **Count PRIMA**: 12 classi active, tutte con `primary_stat: null` (verificato).
7. **Count previsto DOPO**: 12 classi con `primary_stat`, tags, guide description tutti popolati.
8. **Idempotenza**: SI — al 2° run: `updated=0, untouched=12`.
9. **Se rilanciato**: nessuna scrittura, output `untouched=12`.
10. **Interazione con classes_v2**: se applicato DOPO `classes_v2` (che deprecates berserker/assassin/necromancer), quelle 3 vengono skippate come `is_active=false` (variabile `skipped_inactive`). Meglio applicarlo PRIMA di classes_v2 per popolare i loro campi (utili come "storia" prima della deprecazione).
11. **Rischi**: BASSO.
12. **Verdetto**: ✅ **SAFE-TO-APPLY**.

---

## 6) `round15_seed_item_tags.py` — ✅ SAFE-TO-APPLY (con env export)

1. **Path**: `/app/backend/app/scripts/round15_seed_item_tags.py`
2. **Cosa fa**: backfill di 8 campi compatibilità (`weapon_tags`, `armor_tags`, `class_tags`, `role_tags`, `stat_tags`, `recommended_classes`, `is_universal`, `required_class_optional`) su ogni item attivo non-test. Signature items → hard-lock su classe (mappatura in `SIGNATURE_CLASS_MAP`, es. `drake_slayer_blade` → warrior).
3. **`--dry-run` nativo**: SI, ma richiede export env come #5.
4. **Output dry-run**:
   ```
   === SUMMARY ===
     items scanned:    131
     updated:          131
     untouched:        0
     sample updates:
       - dragon_essence      → ['class_tags','recommended_classes','role_tags','stat_tags','updated_at']
       - drake_slayer_helm   → [+armor_tags,+required_class_optional]
       - drake_slayer_blade  → [+weapon_tags,+required_class_optional]
   ```
5. **Analisi statica**:
   - Collection scritte: `items` (update_one `$set`), `audit_logs` (event `item_tags_seeded_round15_phase2`).
   - Chiave idempotenza: `id` dell'item + diff sui campi (build_delta ritorna solo i campi diversi).
6. **Count PRIMA**: `items` attive non-test: 131.
7. **Count previsto DOPO**: 131 items taggati (stessi record, campi arricchiti).
8. **Idempotenza**: SI — al 2° run: `updated=0, untouched=131`.
9. **Rischi**: BASSO. Le regole di inferenza sono deterministiche (regex su nome), quindi output stabile.
10. **Interazione con classes_v2**: NESSUNA — `item_tags` non tocca `adventurer_classes`.
11. **Interazione con class_identity**: NESSUNA — `item_tags` legge stat_bonus dai documenti items, non da classes.
12. **Verdetto**: ✅ **SAFE-TO-APPLY**.

---

## Verdetto complessivo

**4 SAFE, 1 NEEDS-REVIEW, 1 DO-NOT-APPLY.**

Non posso dichiarare *"tutti safe, apply in blocco"* per due motivi bloccanti:

1. **`round160_seed_classes_v2.py` ha un bug reale** (`NameError: uuid`) — pre-esistente al recovery, ma bloccante. Richiede fix minimo (1 riga): aggiungere `import uuid` sulle import. Modifica al codice legacy → autorizzazione utente esplicita richiesta.

2. **`round160_seed_class_halls.py` inserirebbe 1510 rows** per gilde majoritariamente junk. Serve tua decisione: applicare comunque (accettando rumore) o cleanup gilde prima.

Ordine consigliato una volta risolti i punti sopra:

1. **`round15_seed_class_identity.py`** (backfill primary_stat + guide prima di deprecazioni)
2. **`round160_seed_classes_v2.py`** (dopo fix `import uuid`)
3. **`round160_seed_races.py`**
4. **`round160_seed_class_halls.py`** (dopo tua decisione su cleanup gilde)
5. **`round15_seed_achievements.py`**
6. **`round15_seed_item_tags.py`**

## Note tecniche
- Modifica di `.env` non richiesta per questi 6 apply. Solo il `class_identity` e `item_tags` richiedono `export $(cat .env | xargs)` sulla shell che li lancia (o `set -a; source .env; set +a`).
- Nessuno di questi seed è nella blacklist utente.
- Nessuno modifica dati di gioco dinamici (spedizioni, PvP battle, forge orders, ecc.).

## Autorizzazione richiesta

Prima di STEP 2 apply, dimmi:

- (A) autorizzo `import uuid` a essere aggiunto in `round160_seed_classes_v2.py`?
- (B) applico `class_halls` ora anche con 148 gilde-junk (idempotente + inquinamento accettabile) oppure prima cleanup?
- Se (A) e (B) risolti, dai "**procedi apply**" per l'esecuzione nell'ordine sopra.
