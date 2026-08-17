#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/defaults/bin/bw"
mkdir -p "$(dirname "$DEST")"
if [[ -f "$DEST" ]]; then
  chmod +x "$DEST"
  echo "bw already present: $DEST"
  exit 0
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -fsSL -o "$TMP/bw.zip" "https://vault.bitwarden.com/download/?app=cli&platform=linux"
unzip -qo "$TMP/bw.zip" -d "$TMP"
mv "$TMP/bw" "$DEST"
chmod +x "$DEST"
if [[ "$(uname -s)" == "Linux" ]]; then
  "$DEST" --version
fi
ls -lh "$DEST"
echo "fetched $DEST"
