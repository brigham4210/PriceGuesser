#!/usr/bin/env bash
# Copy the Flask game from the repository root into the iOS app's sources.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$(dirname "$here")"
dest="$here/src/pgweb"

rm -rf "$dest"
mkdir -p "$dest"
cp "$root"/main.py "$root"/game.py "$root"/forms.py "$dest"/
cp -R "$root"/Zillow "$root"/templates "$root"/static "$dest"/
find "$dest" -name __pycache__ -type d -prune -exec rm -rf {} +
touch "$dest/__init__.py"
cp "$root/LICENSE" "$here/LICENSE"
echo "Copied the web app into $dest"
