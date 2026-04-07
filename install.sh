#!/usr/bin/env bash
# install.sh — Sync dotfiles into ~/.claude via symlinks.
#
# Safe to run multiple times. Anything already at the target path that
# is NOT already the correct symlink gets moved into a timestamped
# backup folder before being replaced.
#
# Targets handled:
#   ~/.claude/CLAUDE.md     → claude/CLAUDE.md
#   ~/.claude/settings.json → claude/settings.json
#   ~/.claude/mcp.json      → claude/mcp.json (stub — see file)
#   ~/.claude/skills        → claude/skills (whole directory symlinked)

set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${CLAUDE_DIR}/backups/dotfiles-install-${TIMESTAMP}"

mkdir -p "${CLAUDE_DIR}"

link() {
  local src="$1"
  local dest="$2"

  # If a symlink already points at the right place, do nothing.
  if [ -L "${dest}" ] && [ "$(readlink "${dest}")" = "${src}" ]; then
    echo "  ✓ already linked: ${dest}"
    return
  fi

  # If anything else is at the destination, back it up first.
  if [ -e "${dest}" ] || [ -L "${dest}" ]; then
    mkdir -p "${BACKUP_DIR}"
    local backup_name
    backup_name="$(basename "${dest}")"
    mv "${dest}" "${BACKUP_DIR}/${backup_name}"
    echo "  → backed up existing ${dest} to ${BACKUP_DIR}/${backup_name}"
  fi

  mkdir -p "$(dirname "${dest}")"
  ln -s "${src}" "${dest}"
  echo "  ✓ linked: ${dest} → ${src}"
}

echo "[install] dotfiles dir: ${DOTFILES_DIR}"
echo "[install] target dir:   ${CLAUDE_DIR}"
echo

link "${DOTFILES_DIR}/claude/CLAUDE.md"     "${CLAUDE_DIR}/CLAUDE.md"
link "${DOTFILES_DIR}/claude/settings.json" "${CLAUDE_DIR}/settings.json"
link "${DOTFILES_DIR}/claude/mcp.json"      "${CLAUDE_DIR}/mcp.json"
link "${DOTFILES_DIR}/claude/skills"        "${CLAUDE_DIR}/skills"

echo
if [ -d "${BACKUP_DIR}" ]; then
  echo "[install] Done. Replaced files were backed up to ${BACKUP_DIR}"
else
  echo "[install] Done. Nothing needed backing up."
fi
