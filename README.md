# DeckWarden

Bitwarden vault access in Steam Deck Game Mode via [`rbw`](https://github.com/doy/rbw) (unofficial Bitwarden CLI). Unlock → search → type username/password into the focused game/launcher.

## Requirements

1. [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
2. `rbw` installed and registered for the `deck` user
3. This plugin sideloaded into Decky

## Install rbw (Desktop Mode)

Switch to Desktop Mode. Open a terminal as `deck`.

### Binary via cargo

```bash
# install Rust if needed: https://rustup.rs
cargo install --locked rbw
mkdir -p ~/.local/bin
ln -sf ~/.cargo/bin/rbw ~/.local/bin/rbw
ln -sf ~/.cargo/bin/rbw-agent ~/.local/bin/rbw-agent
```

Or download a release binary into `~/.local/bin` and `chmod +x` it.

Game Mode PATH is thin. Prefer `~/.local/bin/rbw` (DeckWarden looks there first). You can also set `rbw_path` in plugin settings later if needed.

### Pinentry

`rbw` normally uses a GUI/curses pinentry. Game Mode has no useful GUI pinentry. DeckWarden ships `bin/pinentry-deckwarden` and points `rbw` at it on first unlock. Do **not** use `pinentry-mac` or other GUI pinentries for Game Mode.

Desktop Mode still works: when no unlock pin is supplied, the shim falls back to system `pinentry` / `pinentry-curses` / `pinentry-tty`.

### Register / login / sync (once)

```bash
rbw config set email your@email.com
# Vaultwarden / self-hosted: also set base_url / identity_url as needed
rbw register
rbw login
rbw sync
rbw unlock   # verify Desktop unlock works
rbw lock
```

Complete any 2FA prompts here in Desktop Mode. DeckWarden only unlocks an already-registered vault.

Optional: `rbw config set lock_timeout 3600` (seconds the agent keeps keys in memory).

## Install DeckWarden

### Build

```bash
pnpm install
pnpm run build
```

### Sideload

1. Enable Decky Developer mode
2. Copy the plugin folder to `~/homebrew/plugins/DeckWarden` on the Deck so it contains at least:

   - `plugin.json`
   - `package.json`
   - `main.py`
   - `dist/index.js`
   - `bin/pinentry-deckwarden` (from `defaults/bin` after install / or copy manually)
   - `py_modules/`

3. Restart Decky / reload plugins

Zip layout for distribution:

```text
DeckWarden/
  dist/index.js
  package.json
  plugin.json
  main.py
  bin/pinentry-deckwarden
  py_modules/list_parse.py
  README.md
  LICENSE
```

Decky copies `defaults/` into the plugin install dir; ensure `bin/pinentry-deckwarden` is executable.

## First run (Game Mode)

1. Open Quick Access → DeckWarden
2. Enter Bitwarden master password → Unlock
3. Search entries (query is saved across reopen)
4. Focus a game/launcher text field, open DeckWarden, select a row:
   - **A** — type password
   - **X** — type username
   - **Y** — reveal password (5s)
5. Use Sync when the vault changed on another device; Lock when done

`rbw-agent` keeps keys in memory until `lock_timeout` or Lock.

## Security

- Master password is only held in memory / `$XDG_RUNTIME_DIR` for the unlock call, then deleted
- Never written to plugin settings or logs
- Credentials are fetched from `rbw` only when typing or revealing
- No auto-unlock; no stored master password on disk
- Session state lives in `rbw-agent`, not in this plugin

## Smoke check

```bash
python3 tests/check.py
```

Checks the Assuan pinentry shim and list-line parsing.

### Manual Game Mode checklist

- [ ] Unlock with correct master password
- [ ] Wrong password shows an error
- [ ] Search filters name/username; reopen keeps last query
- [ ] A types password into focused field and closes QAM
- [ ] X types username
- [ ] Y reveals then auto-hides
- [ ] Sync refreshes list
- [ ] Lock returns to unlock screen

## Development

```bash
pnpm install
pnpm run build
pnpm run check
```
