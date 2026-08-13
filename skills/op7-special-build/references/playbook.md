# Knowledge loop + lookup

## Auto-updating flow
conversations → session digests (`docs/field-notes/sessions/`) → `session_to_notes.py` → `docs/field-notes/log.yml` → playbook sync workflow (fetches log + digests, regenerates `notes/` + `docs/09-*`) → searchable.

## lookup.py (in the playbook repo)
```
python3 scripts/lookup.py install testonly   # ranked matches, one line each
python3 scripts/lookup.py --id C1            # full detail for one entry
python3 scripts/lookup.py --sessions         # conversation digests
python3 scripts/lookup.py --tags             # all curated tags
```

## Notes layer layout
`notes/<slug>/INDEX.md` (keyword→ids, grep-able), `notes/<slug>/entries/<id>.md` (one problem+solution per file), `notes/<slug>/SESSIONS.md`, `notes/<slug>/index.json` (machine-readable). `docs/09-field-notes-journey.md` is the human table.

## Adding a new app / special build
1. Copy `projects/_template/` in the playbook; fill `manifest.yml` (`field_notes.repo/path`).
2. In the app's build repo, add `docs/field-notes/log.yml` (same shape) + `docs/field-notes/sessions/`.
3. Playbook sync picks it up automatically; agents then search it the same way.
