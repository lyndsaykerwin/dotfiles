#!/usr/bin/env bash
# bootstrap.sh — One-shot setup for a fresh machine.
# Clones this repo to ~/dotfiles and runs install.sh.
#
# Use this in the Claude Code cloud sandbox's "setup script" field, or
# paste it into a fresh Ubuntu shell.
set -euo pipefail

if ! command -v git >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq && sudo apt-get install -y git
  else
    echo "git is not installed and I don't know your package manager. Install git, then re-run." >&2
    exit 1
  fi
fi

REPO_URL="${DOTFILES_REPO:-https://github.com/lyndsaykerwin/dotfiles.git}"
TARGET="${HOME}/dotfiles"

if [ -d "${TARGET}/.git" ]; then
  echo "[bootstrap] dotfiles already cloned at ${TARGET} — pulling latest"
  git -C "${TARGET}" pull --ff-only
else
  echo "[bootstrap] cloning ${REPO_URL} → ${TARGET}"
  git clone "${REPO_URL}" "${TARGET}"
fi

bash "${TARGET}/install.sh"
