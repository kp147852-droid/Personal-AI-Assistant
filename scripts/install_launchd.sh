#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="/Users/kyleparker/Documents/New project 2/data/AI assistant"
PLIST_SRC="$ROOT_DIR/deploy/com.focusmate.backend.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.focusmate.backend.plist"

mkdir -p "$HOME/Library/LaunchAgents"
mkdir -p "$ROOT_DIR/backend/data"

cp "$PLIST_SRC" "$PLIST_DST"
launchctl unload "$PLIST_DST" >/dev/null 2>&1 || true
launchctl load "$PLIST_DST"

printf "Installed and started: %s\n" "$PLIST_DST"
printf "Check status: launchctl list | grep focusmate\n"
printf "Stop: launchctl unload %s\n" "$PLIST_DST"
printf "Start: launchctl load %s\n" "$PLIST_DST"
