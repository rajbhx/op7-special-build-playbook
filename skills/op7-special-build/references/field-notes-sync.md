# Field-notes log schema + sync (canonical gotchas)

Learned while registering `deepdenoiser-op7` and `rain-op7` with the playbook
sync. The sync is the ONLY auto-update path; a malformed project log used to
crash the whole workflow. Current scripts are defensive, but keep logs canonical.

## Canonical log shape (docs/field-notes/log.yml)

```yaml
# header comments (optional, one line each)
sections:
  - id: A
    title: Build pipeline
    entries:
      - id: A1
        problem: "one line, quoted"
        cause: "one line, quoted"
        solution: "one line, quoted"
        tags: [word1, word2]      # flat list of lowercase single words
```

Rules:
- Top level MUST be a dict with a `sections:` key. A bare YAML list of sections
  (missing `sections:`) is malformed — the sync scripts now tolerate it, but the
  canonical writers (session_to_notes.py render) always emit `sections:`.
- `tags:` MUST be a flat list of strings. `tags: [[a, b]]` (nested) breaks
  keyword derivation; it comes from parsing a digest line `tags: [a, b]`
  without stripping the brackets. session_to_notes.py strips brackets now.
- Long `problem:` scalars get line-wrapped by some writers (PyYAML safe_dump).
  Dedupe in session_to_notes.py compares PARSED problem texts, so wrapping no
  longer causes duplicate entries. Avoid wrapping anyway: keep fields one line.
- Entry ids stay stable once referenced; never renumber, delete duplicates only.

## Journey doc selection

`docs/09-field-notes-journey.md` is built from the project with the MOST
entries (not the first alphabetically) so a young project registering first can
never shrink the human journey. Per-project cards live in `projects/<slug>/README.md`.

## Adding a NEW project (checklist)

1. Playbook: `projects/<slug>/manifest.yml` (copy `_template`), `field_notes.repo/path`.
2. Build repo: `docs/field-notes/log.yml` in the canonical shape above.
3. Build repo: `docs/field-notes/sessions/` (+ `_template.md`) and
   `automation/op7/session_to_notes.py` + `conversation_to_notes.py`
   (copy from `rajbhx/iceraven-op7`; paths are derived, no edits needed).
4. Validate locally: `python3 scripts/generate_project_docs.py <logs-dir>`
   and `python3 scripts/build_notes.py <logs-dir>` before dispatching sync.
5. Dispatch `playbook-sync.yml` and confirm a green auto-commit.
