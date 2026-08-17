# DeckWarden

Bitwarden vault access in Steam Deck Game Mode via the official Bitwarden CLI (`bw`). Log in with Bitwarden Cloud email + master password → search → type credentials into the focused game/launcher.

**Does not use `rbw`.**

## Requirements

1. [Decky Loader](https://github.com/SteamDeckHomebrew/decky-loader)
2. This plugin (ships the official Linux `bw` CLI inside the package)

No separate `bw` / `rbw` install on the Deck.

Self-hosted / Vaultwarden (optional, Desktop once):

```bash
~/homebrew/plugins/DeckWarden/bin/bw config server https://your-vault.example.com
```

Accounts with 2FA: use **I have 2FA** (or enter email/password first — the plugin prompts if Bitwarden asks). Supported methods: Authenticator, Email code, YubiKey. Duo / FIDO2 WebAuthn are not supported by `bw` CLI.

## Install DeckWarden

### Build

```bash
pnpm install
pnpm run build   # also downloads Linux bw into defaults/bin/
```

Or use the GitHub Actions **DeckWarden** artifact zip.

### Sideload

1. Enable Decky Developer mode
2. Install the built zip / copy the plugin to `~/homebrew/plugins/DeckWarden` with at least:

   - `plugin.json`, `package.json`, `main.py`
   - `dist/index.js`
   - `bin/bw` (executable — from `defaults/bin` after Decky install)
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

## Logs

On the Deck:

```bash
tail -f ~/homebrew/logs/DeckWarden/plugin.log
```

Password and session keys are never written there — only steps, exit codes, and short error tails.

Login/unlock time out after 120s (often hung before on interactive 2FA prompts).

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
