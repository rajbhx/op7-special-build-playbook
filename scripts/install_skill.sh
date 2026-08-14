#!/usr/bin/env bash
# One-command install of the op7-special-build skill for a new agent/machine.
#
# Installs the skill from the playbook repo into a Codex skills dir (default:
# $CODEX_HOME/skills or ~/.codex/skills), records the source commit marker,
# then runs the skill's own updater to confirm. Idempotent: if the skill is
# already installed it just refreshes it (same path the agent uses at session
# start).
#
# Usage:
#   bash scripts/install_skill.sh
# Env overrides:
#   PLAYBOOK_REPO   remote to install from (default: rajbhx/op7-special-build-playbook)
#   SKILLS_DIR      target skills directory (default: $CODEX_HOME/skills or ~/.codex/skills)
#   KEEP_CLONE      set to 1 to keep the temporary playbook clone (debugging)
set -euo pipefail

PLAYBOOK_REPO="${PLAYBOOK_REPO:-https://github.com/rajbhx/op7-special-build-playbook.git}"
SKILL_NAME="op7-special-build"
DEFAULT_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"
SKILLS_DIR="${SKILLS_DIR:-$DEFAULT_SKILLS}"
TARGET="$SKILLS_DIR/$SKILL_NAME"

log() { printf '[skill-install] %s\n' "$*"; }
die() { printf '[skill-install] ERROR: %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required"
remote_head="$(git ls-remote "$PLAYBOOK_REPO" HEAD 2>/dev/null | awk '{print $1}')"
if [[ -z "$remote_head" ]]; then
  die "cannot reach $PLAYBOOK_REPO (offline?) — install the skill manually from a playbook clone"
fi

if [[ -d "$TARGET" ]]; then
  log "skill already installed at $TARGET — refreshing"
  bash "$TARGET/scripts/update_skill.sh"
  exit $?
fi

log "installing $SKILL_NAME from $PLAYBOOK_REPO"
log "target: $TARGET"
mkdir -p "$SKILLS_DIR"

TMP="$(mktemp -d /tmp/skill-install.XXXXXX)"
# Cleanup must never flip the exit code (some sandboxes deny rm on git packs).
trap '[[ "${KEEP_CLONE:-}" != "1" ]] && { [ -d "$TMP" ] && rm -rf "$TMP" 2>/dev/null || true; }' EXIT

git clone --quiet --depth 1 --filter=blob:none --sparse "$PLAYBOOK_REPO" "$TMP/repo"
git -C "$TMP/repo" sparse-checkout set "skills/$SKILL_NAME" >/dev/null 2>&1
[[ -f "$TMP/repo/skills/$SKILL_NAME/SKILL.md" ]] \
  || die "playbook skill source missing SKILL.md — playbook layout changed?"

cp -a "$TMP/repo/skills/$SKILL_NAME" "$TARGET"
printf '%s' "$remote_head" > "$TARGET/.skill-installed-commit"
log "installed $remote_head"

# Verify with the skill's own updater (also leaves the marker consistent).
bash "$TARGET/scripts/update_skill.sh" || die "post-install update check failed"

log "done — skill registered at $TARGET"
log "next session of the agent will auto-load it; refresh anytime with:"
log "  bash $TARGET/scripts/update_skill.sh"
