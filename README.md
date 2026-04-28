# dotfiles

My Claude Code config, synced across every machine I use — laptop, work computer, and any Claude Code session running on the web.

## What lives here

```
dotfiles/
├── claude/
│   ├── CLAUDE.md       # global identity / preferences (loaded in every project)
│   ├── settings.json   # permissions + hooks (auto syntax-check, pre-commit build check, MCP seeding)
│   ├── mcp.json        # master MCP server list — copied into projects as .mcp.json (remote/http only)
│   └── skills/         # all my personal skills (brainstorming, writing-plans, etc.)
├── install.sh          # symlinks ~/.claude/ → this repo + seeds .mcp.json into the current project
├── bootstrap.sh        # one-shot setup for a fresh machine
└── README.md
```

## What this does in plain English

Normally, Claude Code reads your config from `~/.claude/`. Every machine has its own copy, so changes on one don't follow you anywhere else. This repo fixes that: the real files live here, and `install.sh` puts shortcuts (symlinks) inside `~/.claude/` that point back into this folder. When you edit `claude/CLAUDE.md` here, every machine sees the change. When you edit it from `~/.claude/CLAUDE.md` on any machine, you're really editing the file in this repo. Then `git push` from one machine, `git pull` on the next, and you're synced.

## How to use it on a new machine

### macOS (laptop / desktop)

Open **Terminal** (Cmd+Space → "Terminal") and paste this one line:

```bash
git clone https://github.com/lyndsaykerwin/dotfiles.git ~/dotfiles && bash ~/dotfiles/install.sh
```

If git isn't installed yet, the first `git` command will pop up a macOS dialog asking to install the Xcode Command Line Tools. Click **Install**, wait a few minutes, then re-run the line above.

### Linux / Claude Code cloud sandbox

Paste this into the terminal (or into the cloud sandbox's setup-script field):

```bash
sudo apt-get install -y git && git clone https://github.com/lyndsaykerwin/dotfiles.git ~/dotfiles && bash ~/dotfiles/install.sh
```

### What that does, in order

1. Installs git if it isn't already there (Linux only — Mac handles this via Xcode Command Line Tools).
2. **`git clone ... ~/dotfiles`** — downloads this whole repo to a folder called `dotfiles` in your home directory.
3. **`bash ~/dotfiles/install.sh`** — runs the install script, which makes the symlinks.

`bootstrap.sh` is a fancier version of the same thing — it also pulls the latest if the repo is already cloned, and it knows how to install git on macOS, Debian/Ubuntu, or via Homebrew. You can use either.

## What `install.sh` actually does

For each of these files, it:
1. Checks if a real file already exists at the target.
2. If yes, moves it into `~/.claude/backups/dotfiles-install-{timestamp}/` so nothing is lost.
3. Creates a symlink (a shortcut) from `~/.claude/{file}` pointing into `~/dotfiles/claude/{file}`.

It's safe to run as many times as you want. Running it twice won't double-back-up — if the symlink is already correct, it skips that file.

Files it manages:

| Symlink                         | Points at                         |
| ------------------------------- | --------------------------------- |
| `~/.claude/CLAUDE.md`           | `~/dotfiles/claude/CLAUDE.md`     |
| `~/.claude/settings.json`       | `~/dotfiles/claude/settings.json` |
| `~/.claude/skills` (whole dir)  | `~/dotfiles/claude/skills`        |

### How MCP config gets to projects

Claude Code does **not** read `~/.claude/mcp.json` — that path is ignored. The two real MCP config locations are `~/.claude.json` (in your home folder, personal) and `.mcp.json` at a project root (per-project). To make my MCPs available in every project without committing them to each repo:

1. **`install.sh` seeds `.mcp.json` into the current project root** when it's run from inside a git repo other than dotfiles itself. The cloud setup script invokes `install.sh` from the cloned repo, so the file lands in the right place *before* Claude Code launches.
2. **The `SessionStart` hook in `settings.json`** also drops `.mcp.json` into `$CLAUDE_PROJECT_DIR` if it isn't already there — covers local sessions where `install.sh` wasn't run inside the project.
3. **`enableAllProjectMcpServers: true`** in `settings.json` auto-approves every MCP from those `.mcp.json` files so I don't get a "trust this server?" prompt every session.

Each seeded `.mcp.json` is added to that repo's `.git/info/exclude` (the per-repo, never-committed equivalent of `.gitignore`) so it doesn't show as untracked in `git status`. If you actually want to commit `.mcp.json` to share with a team, remove the entry from `.git/info/exclude`.

## What is NOT in here

These were intentionally left out:

- **`.credentials.json`** — your auth tokens. Never commit these.
- **`settings.local.json`** — machine-specific overrides.
- **`agent-memory/`, `cache/`, `history.jsonl`, `projects/`, `sessions/`, etc.** — local state and history. Tied to a specific machine and would be useless on another one.
- **`agents/` (custom agents)** — currently unused, kept on the original machine only. Add later if I start using them.
- **Local stdio MCP servers** — any MCP that runs as a local process (e.g. a tool that shells out to your machine) can't work in a cloud sandbox. Those stay in a separate machine-specific config and are not synced here.
- **claude.ai Connectors** — MCPs you add under claude.ai → Settings → Connectors are account-level and do *not* inject into Claude Code sessions (verified April 2026). If you need an MCP in Claude Code sessions, add it to `mcp.json` in this repo instead. Currently synced here: **Supabase**, **Vercel**, **Gmail**, **Google Calendar** (all remote/http, so they work everywhere). Gmail and Google Calendar use OAuth — first use of each prompts a Google sign-in.

## Windows note

Real symlinks on Windows need TWO things:

1. **Developer Mode** turned on (Settings → For Developers → Developer Mode → On). One-time toggle, no reboot.
2. The `MSYS=winsymlinks:nativestrict` environment variable, which tells Git Bash to actually create native Windows symlinks instead of silently copying. The install script sets this for you automatically — you don't need to do anything.

With both in place, editing `~/.claude/CLAUDE.md` and editing the file inside this repo are the same operation: they're the same file under the hood. Edit either location → run `git add/commit/push` from `~/dotfiles` → on any other machine, `git pull` and you're synced.

If Developer Mode isn't on, the install script falls back to plain file copies and prints a message telling you so. In that mode the dotfiles repo is the source of truth — edit inside the repo, then re-run install.sh to push copies into `~/.claude/`.

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
