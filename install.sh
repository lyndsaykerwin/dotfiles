#!/usr/bin/env bash
# install.sh — Sync dotfiles into ~/.claude.
#
# On Linux/Mac (and on Windows with Developer Mode enabled): uses real
# symlinks, so editing a file in either location updates both.
#
# On regular Windows (no Developer Mode / no admin): falls back to
# copying. The dotfiles repo is then the source of truth — edit inside
# the repo, then re-run install.sh to push the updated copies into
# ~/.claude/. See README.md for the Windows workflow.
#
# Safe to run multiple times. Existing files are backed up to a
# timestamped folder before being replaced — but if the destination is
# already byte-identical to the source, the script skips it (no
# pointless backups).
#
# Targets handled:
#   ~/.claude/CLAUDE.md     → claude/CLAUDE.md
#   ~/.claude/settings.json → claude/settings.json
#   ~/.claude/mcp.json      → claude/mcp.json (stub — see file)
#   ~/.claude/skills        → claude/skills (whole directory)

set -euo pipefail

# On Git Bash for Windows, MSYS needs this to actually create native
# Windows symlinks instead of silently copying. Harmless on Linux/Mac.
# Requires Developer Mode ON in Windows (Settings → For developers).
export MSYS="${MSYS:-}${MSYS:+ }winsymlinks:nativestrict"

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="${CLAUDE_DIR}/backups/dotfiles-install-${TIMESTAMP}"

mkdir -p "${CLAUDE_DIR}"

# Detect whether we can make real symlinks on this OS.
# Probe by trying to create one in a temp location.
USE_SYMLINKS=true
_probe_dir="$(mktemp -d 2>/dev/null || echo "/tmp/dotfiles-probe-$$")"
mkdir -p "${_probe_dir}"
echo test > "${_probe_dir}/src"
if ln -s "${_probe_dir}/src" "${_probe_dir}/dst" 2>/dev/null && [ -L "${_probe_dir}/dst" ]; then
  USE_SYMLINKS=true
else
  USE_SYMLINKS=false
fi
rm -rf "${_probe_dir}"

if [ "${USE_SYMLINKS}" = true ]; then
  echo "[install] Real symlinks supported — will use ln -s"
else
  echo "[install] Real symlinks NOT supported on this system (likely Windows without Developer Mode)"
  echo "[install] Falling back to file copies. Edit files inside ${DOTFILES_DIR}/claude/"
  echo "[install] and re-run this script to push changes into ~/.claude/."
fi
echo

# Compare two paths for "are they the same content".
# Works for both files (cmp) and directories (diff -r).
same_content() {
  local a="$1" b="$2"
  if [ -d "$a" ] && [ -d "$b" ]; then
    diff -r "$a" "$b" >/dev/null 2>&1
  elif [ -f "$a" ] && [ -f "$b" ]; then
    cmp -s "$a" "$b"
  else
    return 1
  fi
}

link() {
  local src="$1"
  local dest="$2"

  # Already a symlink to the right place — done.
  if [ -L "${dest}" ] && [ "$(readlink "${dest}")" = "${src}" ]; then
    echo "  ✓ already linked: ${dest}"
    return
  fi

  # Not a symlink, but content already matches the source.
  # Only short-circuit when we're in copy-mode — if symlinks are
  # supported, we still want to upgrade copies to real symlinks.
  if [ "${USE_SYMLINKS}" = false ] && [ -e "${dest}" ] && same_content "${src}" "${dest}"; then
    echo "  ✓ already up to date (copy): ${dest}"
    return
  fi

  # Anything else at the destination — back it up first.
  if [ -e "${dest}" ] || [ -L "${dest}" ]; then
    mkdir -p "${BACKUP_DIR}"
    local backup_name
    backup_name="$(basename "${dest}")"
    mv "${dest}" "${BACKUP_DIR}/${backup_name}"
    echo "  → backed up existing ${dest} to ${BACKUP_DIR}/${backup_name}"
  fi

  mkdir -p "$(dirname "${dest}")"

  if [ "${USE_SYMLINKS}" = true ]; then
    ln -s "${src}" "${dest}"
    echo "  ✓ linked: ${dest} → ${src}"
  else
    if [ -d "${src}" ]; then
      cp -r "${src}" "${dest}"
    else
      cp "${src}" "${dest}"
    fi
    echo "  ✓ copied: ${src} → ${dest}"
  fi
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
