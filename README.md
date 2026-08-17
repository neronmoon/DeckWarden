# DeckWarden

Bitwarden vault access in Steam Deck Game Mode via the official Bitwarden CLI (`bw`). Log in with Bitwarden Cloud email + master password → search → type credentials into the focused game/launcher.

**Does not use `rbw`.**

## Requirements

1. [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
2. Official Bitwarden CLI (`bw`) on the Deck for the `deck` user
3. This plugin sideloaded into Decky

## Install Bitwarden CLI (Desktop Mode)

Switch to Desktop Mode. As `deck`:

```bash
mkdir -p ~/.local/bin
curl -L -o /tmp/bw.zip \
  "https://vault.bitwarden.com/download/?app=cli&platform=linux"
unzip -o /tmp/bw.zip -d /tmp/bw
chmod +x /tmp/bw/bw
mv /tmp/bw/bw ~/.local/bin/bw
bw --version
```

Game Mode PATH is thin — keep the binary at `~/.local/bin/bw` (DeckWarden looks there first). Optional: set `bw_path` in plugin settings if installed elsewhere.

Default server is Bitwarden Cloud. Self-hosted / Vaultwarden:

```bash
bw config server https://your-vault.example.com
```

Accounts with interactive 2FA may need a one-time Desktop `bw login` first, or an API-key flow (not in this MVP).

## Install DeckWarden

### Build

```bash
pnpm install
pnpm run build
```

### Sideload

1. Enable Decky Developer mode
2. Copy the plugin to `~/homebrew/plugins/DeckWarden` with at least:

   - `plugin.json`, `package.json`, `main.py`
   - `dist/index.js`
   - `py_modules/item_parse.py`

3. Restart Decky / reload plugins

## First run (Game Mode)

1. Open Quick Access → DeckWarden
2. Enter Bitwarden **email** + **master password** → Log in
3. Later sessions: unlock with master password only (email remembered)
4. Search entries (query persists across reopen)
5. Focus a game/launcher field, open DeckWarden, select a row:
   - **A** — type password
   - **X** — type username
   - **Y** — reveal password (5s)
6. Sync when the vault changed elsewhere; Lock when done

## Security

- Master password only in memory for login/unlock (`BW_PASSWORD` env for that subprocess); never written to plugin settings or logs
- Session key (`BW_SESSION`) kept in the plugin process memory only; cleared on Lock / unload
- Email may be saved in plugin settings for convenience
- Credentials fetched from `bw` only when typing or revealing
- No auto-unlock

## Smoke check

```bash
python3 tests/check.py
```

### Manual Game Mode checklist

- [ ] Log in with email + master password
- [ ] Wrong password shows an error
- [ ] Reopen → Unlock (email shown)
- [ ] Search filters; query persists
- [ ] A / X type into focused field and close QAM
- [ ] Y reveals then auto-hides
- [ ] Sync / Lock / Log out work

## Development

```bash
pnpm install
pnpm run build
pnpm run check
```
