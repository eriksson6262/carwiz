#!/bin/bash
# Spouští ho automaticky launchd (úloha cz.rxauto.generator) po startu Macu
# a vždy, když generátor neběží. Na rozdíl od Spustit_generator.command neotvírá prohlížeč.
cd "$(dirname "$0")"
PORT=8765
if ! lsof -i :$PORT -t >/dev/null 2>&1; then
    echo "$(date '+%d.%m.%Y %H:%M:%S') automatické spuštění generátoru" >> autostart.log
    nohup python3 -u server.py >> server.log 2>&1 &
    sleep 3
fi
echo "✅ Generátor běží (http://localhost:$PORT). Okno se za chvíli zavře."
sleep 2
osascript -e 'tell application "Terminal" to close (every window whose name contains "Autostart_generator")' >/dev/null 2>&1 &
exit 0
