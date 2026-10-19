#!/bin/bash
# Dvojklikem spustí generátor smluv a otevře ho v prohlížeči.
cd "$(dirname "$0")"

PORT=8765

echo "🚗 RX Auto — Generátor smluv"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if lsof -i :$PORT -t >/dev/null 2>&1; then
    echo "Server už běží."
else
    echo "Kontroluji potřebné knihovny..."
    if ! python3 -c "import reportlab, PIL, lxml, anthropic, requests" >/dev/null 2>&1; then
        echo "Instaluji chybějící knihovny (jen při prvním spuštění, chvíli to potrvá)..."
        pip3 install -r requirements.txt --quiet --break-system-packages 2>/dev/null \
            || pip3 install -r requirements.txt --quiet
    fi

    echo "Spouštím server..."
    nohup python3 server.py > server.log 2>&1 &
    for i in 1 2 3 4 5 6 7 8 9 10; do
        sleep 1
        lsof -i :$PORT -t >/dev/null 2>&1 && break
    done
fi

open "http://localhost:$PORT"
echo "✅ Hotovo — generátor běží na http://localhost:$PORT"
echo "Toto okno můžeš zavřít, server běží dál na pozadí."
