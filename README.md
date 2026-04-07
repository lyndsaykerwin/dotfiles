# dotfiles

My Claude Code config, synced across every machine I use — laptop, work computer, and any Claude Code session running on the web.

## What lives here

```
dotfiles/
├── claude/
│   ├── CLAUDE.md       # global identity / preferences (loaded in every project)
│   ├── settings.json   # permissions + hooks (auto syntax-check, pre-commit build check)
│   ├── mcp.json        # placeholder — MCPs are managed at claude.ai, not here
│   └── skills/         # all my personal skills (brainstorming, writing-plans, etc.)
├── install.sh          # creates symlinks from ~/.claude/ → this repo (with backups)
├── bootstrap.sh        # one-shot setup for a fresh machine
└── README.md
```

## What this does in plain English

Normally, Claude Code reads your config from `~/.claude/`. Every machine has its own copy, so changes on one don't follow you anywhere else. This repo fixes that: the real files live here, and `install.sh` puts shortcuts (symlinks) inside `~/.claude/` that point back into this folder. When you edit `claude/CLAUDE.md` here, every machine sees the change. When you edit it from `~/.claude/CLAUDE.md` on any machine, you're really editing the file in this repo. Then `git push` from one machine, `git pull` on the next, and you're synced.

## How to use it on a new machine

Paste this one line into the terminal (or into the Claude Code cloud sandbox's setup-script field):

```bash
sudo apt-get install -y git && git clone https://github.com/lyndsaykerwin/dotfiles.git ~/dotfiles && bash ~/dotfiles/install.sh
```

What that does, in order:
1. **`sudo apt-get install -y git`** — installs git if it isn't already there. (No-op if it already is.)
2. **`git clone ... ~/dotfiles`** — downloads this whole repo to a folder called `dotfiles` in your home directory.
3. **`bash ~/dotfiles/install.sh`** — runs the install script, which makes the symlinks.

`bootstrap.sh` is a fancier version of the same thing — it also pulls the latest if the repo is already cloned. You can use either.

## What `install.sh` actually does

For each of these files, it:
1. Checks if a real file already exists at the target.
2. If yes, moves it into `~/.claude/backups/dotfiles-install-{timestamp}/` so nothing is lost.
3. Creates a symlink (a shortcut) from `~/.claude/{file}` pointing into `~/dotfiles/claude/{file}`.

It's safe to run as many times as you want. Running it twice won't double-back-up — if the symlink is already correct, it skips that file.

Files it manages:

| Symlink                         | Points at                       |
| ------------------------------- | ------------------------------- |
| `~/.claude/CLAUDE.md`           | `~/dotfiles/claude/CLAUDE.md`   |
| `~/.claude/settings.json`       | `~/dotfiles/claude/settings.json` |
| `~/.claude/mcp.json`            | `~/dotfiles/claude/mcp.json`    |
| `~/.claude/skills` (whole dir)  | `~/dotfiles/claude/skills`      |

## What is NOT in here

These were intentionally left out:

- **`.credentials.json`** — your auth tokens. Never commit these.
- **`settings.local.json`** — machine-specific overrides.
- **`agent-memory/`, `cache/`, `history.jsonl`, `projects/`, `sessions/`, etc.** — local state and history. Tied to a specific machine and would be useless on another one.
- **`agents/` (custom agents)** — currently unused, kept on the original machine only. Add later if I start using them.
- **MCP server configs** — Lyndsay's Gmail/HubSpot/Calendar/Slack/Vercel MCPs are managed in claude.ai under Settings → Connectors. They follow the account, not the machine. Nothing to sync here.

## Windows note

Real symlinks on Windows require either admin rights or "Developer Mode" turned on (Settings → For Developers → Developer Mode). Lyndsay's machine doesn't have either, so on Windows the install script falls back to **copying files** instead of linking them. That means:

- Cloud Ubuntu sessions (Linux): real symlinks. Edit anywhere, it syncs everywhere automatically. ✨
- Lyndsay's local Windows machine: file copies. The dotfiles repo is the source of truth — **edit files inside `~/dotfiles/claude/...` directly**, then re-run `install.sh` to push the new copies into `~/.claude/`. Editing inside `~/.claude/` directly won't propagate back to the repo.

The install script auto-detects which mode it's in and tells you on every run.

## Updating

After editing anything in this repo:

```bash
cd ~/dotfiles
git status        # see what changed
git add -A
git commit -m "describe what you changed"
git push
```

On every other machine:

```bash
cd ~/dotfiles && git pull
```

That's the whole sync flow.
