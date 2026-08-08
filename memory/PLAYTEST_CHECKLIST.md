# Playtest Checklist — Orbus Online: Guild Master

**Account principale**: `mr.gualmini@gmail.com` · gilda **"Sentiero di Efreto"**
**URL preview**: <https://drain-dispatch.preview.emergentagent.com/>
**URL produzione**: <https://orbusonline.net/>
**Data ultimo update checklist**: 2026-06-25
**Sessione email pipeline**: ✅ welcome ✅ password-reset (verificati live verso gmail.com)

> Spunta in ordine. Se una voce fallisce, annotala in "Note" in fondo con
> screenshot/timestamp e prosegui con le altre — non bloccarti.

---

## Auth & onboarding
- [ ] Login con email + password → arrivo alla Dashboard senza redirect loop
- [ ] OnboardingChecklist visibile se non completata · dismissibile
- [ ] LanguageSwitcher **EN | IT** in navbar, cambio istantaneo
- [ ] Refresh (F5) → lingua persiste (localStorage)
- [ ] Token JWT in localStorage, scadenza 7 giorni
- [ ] Logout → torno a `/` e localStorage svuotato

## Dashboard
- [ ] Mostra: livello gilda, oro, reputazione, **peak power** (max_team_power_ever), adventurer count
- [ ] Quick actions: Recruit · Adventurers · Dungeons · Inventory
- [ ] DailyQuestsCard visibile con 3 quest + countdown reset UTC midnight
- [ ] Recent expedition report card (se ci sono run completate)

## Recruitment
- [ ] `GET /api/recruitment/candidates` funziona (read-only, NON decrementa contatore)
- [ ] Refresh button mostra `3 free left today` o costo gold se passato il free
- [ ] Click **Refresh** → contatore decrementa, candidati cambiano
- [ ] Recluta 1 candidato → oro scalato correttamente, adventurer aggiunto al roster
- [ ] Daily quest **recruit** progress incrementa

## Adventurers
- [ ] Lista adventurer con stats (STR/AGI/INT/END/FAI) + livello/XP
- [ ] Trait baked **NON** presenti (verifica `phase13_unbaked: true` su almeno 1)
- [ ] Espandi **TraitPreviewWidget** ▸ → mostra base power, effective power, applied modifiers, XP gain %
- [ ] Trait italiani con stat names italianizzati (forza/agilità/intelletto/resistenza/fede)
- [ ] Trait di flavor mostrati in sezione separata "Trait di colore"
- [ ] Adventurer `is_available: false` quando in expedition

## Equipment
- [ ] Equip item da inventory → `reserved_qty` atomico (verifica DB)
- [ ] Tentativo di equip stesso item su 2 adventurer in parallelo: 1 succeeds 1 fail 409
- [ ] Unequip → `reserved_qty` decrementato
- [ ] Slot labels in italiano (Arma / Armatura / Accessorio)
- [ ] Daily quest **equip** progress incrementa

## Dungeons
- [ ] Lista 10 dungeon con **gates** espliciti (locked badge se requisiti non soddisfatti)
- [ ] Goblin Warrens sempre aperto
- [ ] Shadow Crypts / Dragon's Hoard con gate sticky **peak power**
- [ ] Click Start Expedition su dungeon locked → 403 con messaggio chiaro localizzato

## Expedition
- [ ] Seleziona 3 adventurer disponibili (richiesta team_size del dungeon)
- [ ] Vedi power stimato + composizione team (Tank/Healer/DPS) + success chance %
- [ ] Bonus composizione: +5 per ruolo, +10 se tutti e 3 presenti
- [ ] Send → expedition partita, status `in_progress`, adventurer `is_available=false`
- [ ] Dopo durata: status `completed` (lazy sweep su pageload) → report visibile
- [ ] Report mostra: success/failure, gold guadagnato, XP per membro, loot eventuale
- [ ] XP scalato dalle trait `xp_gain%` (verifica con adventurer che ha `Quick Learner`)
- [ ] Equipment delta narrato in IT/EN secondo locale
- [ ] **Replay Last Run** funziona se ultima run sbloccata
- [ ] Daily quest **expedition_complete** progress incrementa

## Inventory
- [ ] Filtri rarity (Common/Uncommon/Rare/Epic) in italiano
- [ ] Filtri item type (Weapon/Armor/Accessory) in italiano
- [ ] Item mostra rarity, slot, item type, power score, stat bonuses
- [ ] Equip dall'inventory → adventurer detail aggiornato in real-time

## Daily Quests
- [ ] 3 quest del giorno mostrate con titolo + reward in IT
- [ ] Progress increments cross-azione (expedition / recruit / equip)
- [ ] Claim funziona, gold +reward, `claimed=true` sticky fino a midnight UTC
- [ ] Double claim respinto con 409
- [ ] Reset alle 00:00 UTC → progress=0 / claimed=false su tutte e tre

## Leaderboard
- [ ] Lista guild ordinate per `max_team_power_ever` desc, poi level/reputation/created_at
- [ ] La tua gilda **"Sentiero di Efreto"** visibile e cliccabile
- [ ] Nessun dato sensibile esposto (no email, no `is_admin`, no `owner_user_id`)
- [ ] Paginazione/limit funziona

## Password reset (email pipeline)
- [ ] Logout
- [ ] "Hai dimenticato la password?" → submit email → toast "Se l'email esiste, è stata inviata"
- [ ] Email arriva su Gmail (subject IT: **Reset password — Orbus Online**)
- [ ] Click link → form reset → nuova password (min 8 char)
- [ ] Login con nuova password → 200
- [ ] Vecchia password → 401
- [ ] Re-use del token già consumato → 400 (one-time-use)
- [ ] Token oltre 60 minuti → 400 (TTL)
- [ ] **Audit log**: solo `token_hash=<12 char>`, mai `reset_token=<raw>` (verifica con tail backend.err.log)

## Welcome email
- [ ] Nuovo register su gmail → subject IT: **Benvenuto su Orbus, <username>**
- [ ] CTA "Entra nella dashboard" → link a APP_BASE_URL
- [ ] Header `Reply-To: admin@orbusonline.net` presente
- [ ] HTML rendering corretto in Gmail (dark card, accento ambra)

## Mobile 375px (iPhone SE-class)
- [ ] Dashboard senza overflow orizzontale
- [ ] Recruitment usabile (refresh button + candidate cards)
- [ ] Dungeons grid responsive
- [ ] DailyQuestsCard non sfora
- [ ] Navbar usabile (no testi tagliati in IT — `Reclutamento` / `Avventurieri` / `Dungeon`)
- [ ] LanguageSwitcher cliccabile

## Lingua IT/EN
- [ ] Switch in navbar visibile
- [ ] Tutti i menu/page principali in italiano corretto (no fallback EN evidente)
- [ ] Item type/rarity/slot tradotti
- [ ] Trait names + descrizioni in italiano (`tContent('trait', slug, …)`)
- [ ] Backend error messages localizzati lato frontend (`backendMessages.js`)
- [ ] Email transactional con subject + body nella lingua di `Accept-Language` (al register / reset)

## Edge cases / sicurezza
- [ ] Non posso vedere gilda di un altro utente (`GET /api/guilds/me` ritorna SOLO la mia)
- [ ] Non posso dispatching adventurer di un'altra gilda (404 cross-guild)
- [ ] Equip item appartenente ad altra gilda → 404
- [ ] JWT manomesso → 401 immediato, logout client-side automatico
- [ ] Brute force login (5 tentativi falliti) → backoff TTL su login_attempts
- [ ] OpenAPI `/api/openapi.json` esposto con esattamente **42 path** (assert invariant)
- [ ] Nessun `_id` ObjectId esposto nelle response JSON

## Performance smoke
- [ ] Dashboard cold-load < 2.5s con cache disabilitata
- [ ] List adventurers `n=20` < 800ms
- [ ] List candidates < 600ms
- [ ] Expedition complete sweep non lascia row `completing` orfane

---

## Note di sessione

> Annota qui qualsiasi bug, frizione UX, traduzione strana, bilanciamento off,
> screenshot path, timestamp. Esempio:
> - `[14:42 UTC] /dashboard mobile 375px: DailyQuestsCard overflow di 4px →
>   probabile gap-3 sui pulsanti claim.`
> - `[14:50 UTC] Trait "Iron-Willed" mostra `+10 endurance` in EN ma
>   `+10 resistenza` in IT solo dopo refresh — verifica i18n key.`

- 

---

## Stato pipeline email (post-rotazione password IONOS 2026-06-25)
- ✅ SMTP IONOS `smtp.ionos.it:587 STARTTLS` autentica con `admin@orbusonline.net`
- ✅ Welcome email IT verificata su `mr.gualmini+welcometest@gmail.com` (14:42 UTC)
- ✅ Password-reset email IT verificata su `mr.gualmini@gmail.com` (14:37 UTC)
- ✅ Token raw mai loggato — solo `token_hash` sha256[:12]
- ⚠️ Account test `mr.gualmini+welcometest@gmail.com` rimosso dal DB (cleanup completato)
