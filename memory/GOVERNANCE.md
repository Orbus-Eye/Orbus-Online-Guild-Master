# Orbus Online — Governance

**Updated:** 2026-07-28

## Lifecycle

```text
Discovery
→ PM adjudication
→ implementation
→ validation
→ closure
→ baseline increment
```

Il completamento di una fase non autorizza automaticamente la successiva.

## Regole

- discovery prima delle scritture;
- dry-run prima di apply quando applicabile;
- snapshot prima di operazioni DB;
- no hard delete;
- default OFF;
- no deploy automatico;
- no online flag automatico;
- no migration tester/live senza owner;
- no sealed modification senza sealed-break;
- no modifica retroattiva dei gate chiusi;
- no PRD append senza closure;
- manifest self-hash esterno soltanto;
- source of truth repository/codice;
- distinguere sempre local verification e remote verification;
- no claim non verificati;
- nessuna ricostruzione MVP delle fondamenta già presenti;
- preservare modifiche e untracked preesistenti non in scope;
- nessun cleanup opportunistico durante un gate;
- nessuna attivazione di Hall PLANNED senza readiness individuale;
- nessuna conversione automatica dei legacy null conflict in `recruit_unassigned`;
- nessun item effect runtime prima del gate dedicato e delle feature gate default-OFF.

## Regole item-first

Ogni iniziativa item player-facing deve dichiarare:

- classe/Hall di riferimento oppure `universal`;
- `item_binding_policy`: `hard`, `soft` o `universal`;
- slot canonico;
- tier, rarità, livello e fonte;
- stats/meccanica e budget;
- motivazione di compatibilità/incompatibilità;
- comportamento classless;
- comportamento flag-OFF;
- test di backward compatibility;
- impatto BSON, receipt e audit se usa effect runtime.

Un item non è considerato implementato se esiste soltanto nel registry ma non è leggibile, ottenibile, confrontabile ed equipaggiabile nel flusso previsto.

## Regole classless / Class Hall

- i nuovi avventurieri non ricevono una classe random nel comportamento target;
- la Class Hall assegna il sentiero, non si limita a riflettere una classe già assegnata;
- la prova safe-mode precede la conferma;
- assignment atomico e idempotente;
- audit/history persistenti;
- post-commit valido: reconcile-forward, non rollback distruttivo;
- solo Hall ACTIVE/readiness-approved;
- gear specializzato e spedizioni hard-block prima dell'assegnazione;
- universal item policy esplicita;
- nessuna vendita o trasferimento della Recluta;
- cap Reclute e XP idle verificati server-side.

## Working tree

Prima di scrivere:

1. inventariare tracked modificati e untracked;
2. attribuire ogni file a `IN_SCOPE`, `PRE_EXISTING_TRACKED_NON_SCOPE` o `PRE_EXISTING_UNTRACKED_NON_SCOPE`;
3. fermarsi se una modifica in scope si sovrappone a lavoro preesistente non attribuibile;
4. non aggiungere, eliminare, rinominare o normalizzare i file non in scope.

## Hash e terminatori di riga

Su Windows `core.autocrlf=true` può produrre un SHA256 worktree diverso dagli hash canonici Linux pur con `git diff` vuoto. Prima di dichiarare un mismatch:

1. verificare `git diff -- <file>`;
2. calcolare anche SHA256 su byte UTF-8 con CRLF normalizzato a LF;
3. confrontare l'hash normalizzato con il valore canonico;
4. non riscrivere il file per “correggere” i line ending.

Un hash normalizzato che non coincide resta un mismatch materiale.

## Context checkpoint

Prima di compact:

```text
gate
branch
HEAD
baseline
file consentiti
file modificati
test
pending
fail-stop
```

Dopo compact:

- rileggere `HANDOFF_CURRENT.md`;
- rileggere `ROADMAP_CURRENT.md`;
- ripetere gli anchor;
- verificare working tree;
- riclassificare le modifiche preesistenti;
- non assumere che un gate HOLD sia diventato autorizzato.

Mismatch:

```text
POST_COMPACT_STATE_MISMATCH
→ STOP
```

## Fail-stop principali

```text
CONTEXT_ANCHOR_FAIL
SEALED_INTEGRITY_VIOLATION
OPENAPI_PATH_COUNT_MISMATCH
POST_COMPACT_STATE_MISMATCH
PRE_EXISTING_WORK_OVERLAP
CLOSED_GATE_CONTRACT_CONFLICT
EFFECT_PERSISTENCE_LAYOUT_INFEASIBLE
ITEM_CLASSIFICATION_MISSING
CLASS_ASSIGNMENT_PRECONDITION_MISSING
LEGACY_NULL_AUTO_DERIVATION_ATTEMPT
SHARED_ENVIRONMENT_WRITE_ATTEMPT
```

Ogni fail-stop produce:

```text
STOP
→ nessuna ulteriore scrittura
→ evidenze
→ PM review
```

## Verifica minima prima di handoff

- `git status --short`;
- `git diff --check`;
- diff completo dei file in scope;
- test proporzionati al gate;
- sealed integrity;
- lore hash canonico;
- OpenAPI in-process quando richiesto;
- conferma baseline;
- conferma nessun file canonico/closed/sealed modificato;
- elenco test non eseguiti con motivo;
- nessun commit, push, deploy o DB write salvo autorizzazione esplicita.
