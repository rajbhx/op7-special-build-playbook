#!/usr/bin/env bash
# One-command install of ALL playbook skills (op7-special-build,
# project-intake, ...) for a new agent/machine.
#
# Installs each skill from the playbook repo into a Codex skills dir (default:
# $CODEX_HOME/skills or ~/.codex/skills), records the source commit marker,
# then runs each skill's own updater to confirm. Idempotent: already-installed
# skills are just refreshed.
#
# Usage:
#   bash scripts/install_skill.sh
# Env overrides:
#   PLAYBOOK_REPO   remote to install from (default: rajbhx/op7-special-build-playbook)
#   SKILL_NAMES     space-separated subset to install (default: all skills/ dirs)
#   SKILLS_DIR      target skills directory (default: $CODEX_HOME/skills or ~/.codex/skills)
#   KEEP_CLONE      set to 1 to keep the temporary playbook clone (debugging)
set -euo pipefail

PLAYBOOK_REPO="${PLAYBOOK_REPO:-https://github.com/rajbhx/op7-special-build-playbook.git}"
SKILL_NAMES="${SKILL_NAMES:-}"
DEFAULT_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"
SKILLS_DIR="${SKILLS_DIR:-$DEFAULT_SKILLS}"

log() { printf '[skill-install] %s\n' "$*"; }
die() { printf '[skill-install] ERROR: %s\n' "$*" >&2; exit 1; }

command -v git >/dev/null 2>&1 || die "git is required"
remote_head="$(git ls-remote "$PLAYBOOK_REPO" HEAD 2>/dev/null | awk '{print $1}')"
if [[ -z "$remote_head" ]]; then
  die "cannot reach $PLAYBOOK_REPO (offline?) — install the skill manually from a playbook clone"
fi

TMP="$(mktemp -d /tmp/skill-install.XXXXXX)"
# Cleanup must never flip the exit code (some sandboxes deny rm on git packs).
trap '[[ "${KEEP_CLONE:-}" != "1" ]] && { [ -d "$TMP" ] && rm -rf "$TMP" 2>/dev/null || true; }' EXIT

log "fetching playbook (skills/)"
git clone --quiet --depth 1 --filter=blob:none --sparse "$PLAYBOOK_REPO" "$TMP/repo"
git -C "$TMP/repo" sparse-checkout set skills >/dev/null 2>&1
[[ -d "$TMP/repo/skills" ]] || die "no skills/ directory in $PLAYBOOK_REPO"

if [[ -z "$SKILL_NAMES" ]]; then
  SKILL_NAMES="$(find "$TMP/repo/skills" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
fi
[[ -n "$SKILL_NAMES" ]] || die "no skills found in playbook skills/"

mkdir -p "$SKILLS_DIR"
rc=0
for name in $SKILL_NAMES; do
  target="$SKILLS_DIR/$name"
  if [[ -d "$target" ]]; then
    log "skill '$name' already installed at $target — refreshing"
    if [[ -x "$target/scripts/update_skill.sh" ]]; then
      bash "$target/scripts/update_skill.sh" || rc=1
    else
      log "  (no bundled updater; skipping — refresh manually)"
    fi
    continue
  fi
  [[ -f "$TMP/repo/skills/$name/SKILL.md" ]] || { log "skip '$name': no SKILL.md in source"; continue; }
  cp -a "$TMP/repo/skills/$name" "$target"
  printf '%s' "$remote_head" > "$target/.skill-installed-commit"
  log "installed '$name' ($remote_head)"
  if [[ -x "$target/scripts/update_skill.sh" ]]; then
    bash "$target/scripts/update_skill.sh" || rc=1
  fi
done

log "done — skills registered under $SKILLS_DIR"
log "refresh anytime with:  bash $SKILLS_DIR/<skill>/scripts/update_skill.sh"
exit "$rc"
