#!/bin/bash
# Jednorázově: nastaví, aby se generátor spouštěl sám po startu Macu
# a znovu se spustil, kdyby spadl (kontrola každé 2 minuty).
# Odinstalace: spusť tento soubor s parametrem "odinstalovat" (nebo smaž
# ~/Library/LaunchAgents/cz.rxauto.generator.plist a odhlas se).
DIR="$(cd "$(dirname "$0")" && pwd)"
LABEL="cz.rxauto.generator"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null
if [ "$1" = "odinstalovat" ]; then
    rm -f "$PLIST"; echo "Automatické spouštění vypnuto."; exit 0
fi
chmod +x "$DIR/Autostart_generator.command"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/sh</string><string>-c</string>
    <string>/usr/sbin/lsof -i :8765 -t &gt;/dev/null 2&gt;&amp;1 || /usr/bin/open -g -a Terminal "$DIR/Autostart_generator.command"</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>StartInterval</key><integer>120</integer>
</dict>
</plist>
PL
launchctl bootstrap "gui/$(id -u)" "$PLIST" && echo "✅ Hotovo — generátor se bude spouštět sám po startu Macu a hlídá se každé 2 minuty." \
  || echo "⚠️ Nepodařilo se zaregistrovat úlohu (launchctl)."
