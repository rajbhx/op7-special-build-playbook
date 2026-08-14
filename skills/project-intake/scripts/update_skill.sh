#!/usr/bin/env bash
# Self-update for the skill that contains this script (any skills/<name>).
#
# The skill's source of truth is the playbook repo
# (github.com/rajbhx/op7-special-build-playbook, skills/op7-special-build/).
# This script keeps any installed copy in sync with that source:
#   - cheap check first: one `git ls-remote` (no clone) comparing the remote
#     HEAD against the installed marker (.skill-installed-commit)
#   - only on change: sparse shallow clone of the skill dir, validate, then an
#     atomic swap with a timestamped backup; the previous install is restored
#     if the swap fails
#   - offline/rate-limited: keeps the current install and warns (never breaks
#     an agent session)
#
# Usage (run from anywhere; resolves its own install root):
#   bash scripts/update_skill.sh
# Env overrides:
#   PLAYBOOK_REPO       remote to update from (default: rajbhx/op7-special-build-playbook)
#   SKILL_ROOT          install root (default: parent of this skill's directory)
#   EXTRA_SKILL_ROOTS   space-separated extra roots to update in place
set -euo pipefail

PLAYBOOK_REPO="${PLAYBOOK_REPO:-https://github.com/rajbhx/op7-special-build-playbook.git}"

# Resolve this skill's real location (follows symlinks, e.g. ~/.codex/skills).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
SKILL_NAME="$(basename "$SKILL_DIR")"  # generic: works for any skills/<name> in the playbook
DEFAULT_ROOT="$(dirname "$SKILL_DIR")"
SKILL_ROOT="${SKILL_ROOT:-$DEFAULT_ROOT}"
MARKER="$SKILL_DIR/.skill-installed-commit"

log() { printf '[skill-update] %s\n' "$*"; }
die() { printf '[skill-update] ERROR: %s\n' "$*" >&2; exit 1; }

roots="$SKILL_ROOT"
if [[ -n "${EXTRA_SKILL_ROOTS:-}" ]]; then
  roots="$roots $EXTRA_SKILL_ROOTS"
fi

remote_head=""
if ! remote_head="$(git ls-remote "$PLAYBOOK_REPO" HEAD 2>/dev/null | awk '{print $1}')" || [[ -z "$remote_head" ]]; then
  log "offline or unreachable ($PLAYBOOK_REPO) — keeping current skill, nothing changed"
  exit 0
fi

update_root() {
  local root="$1" target marker installed
  target="$root/$SKILL_NAME"
  marker="$target/.skill-installed-commit"
  installed="$(cat "$marker" 2>/dev/null || true)"

  if [[ "$installed" == "$remote_head" ]]; then
    log "$root: up to date ($(echo "$remote_head" | cut -c1-12))"
    return 0
  fi

  log "$root: updating $installed -> $remote_head"
  local tmp backup
  tmp="$(mktemp -d /tmp/skill-update.XXXXXX)"
  backup="$root/$SKILL_NAME.backup-$(date +%Y%m%d-%H%M%S)"

  if ! git clone --quiet --depth 1 --filter=blob:none --sparse "$PLAYBOOK_REPO" "$tmp/repo"; then
    log "$root: clone failed, keeping current skill"
    return 1
  fi
  git -C "$tmp/repo" sparse-checkout set "skills/$SKILL_NAME" >/dev/null 2>&1
  if [[ ! -f "$tmp/repo/skills/$SKILL_NAME/SKILL.md" ]]; then
    log "$root: fetched skill is missing SKILL.md — refusing to install"
    return 1
  fi

  # Atomic swap: keep the previous install as a timestamped backup.
  if [[ -d "$target" ]]; then
    mv "$target" "$backup"
  fi
  if cp -a "$tmp/repo/skills/$SKILL_NAME" "$target" && \
     printf '%s' "$remote_head" > "$marker"; then
    log "$root: installed $remote_head (previous kept at $(basename "$backup"))"
  else
    log "$root: swap failed — restoring previous install"
    if [[ -d "$backup" && ! -d "$target" ]]; then
      mv "$backup" "$target"
    fi
    return 1
  fi
  return 0
}

rc=0
for root in $roots; do
  if [[ ! -d "$root" ]]; then
    log "skip missing root: $root"
    continue
  fi
  update_root "$root" || rc=1
done

log "done (remote $remote_head)"
exit "$rc"
