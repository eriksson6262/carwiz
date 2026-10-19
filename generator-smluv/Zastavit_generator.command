#!/bin/bash
# Dvojklikem vypne běžící generátor smluv.
PORT=8765

PID=$(lsof -i :$PORT -t 2>/dev/null)

if [ -z "$PID" ]; then
    echo "Generátor smluv aktuálně neběží."
else
    kill -9 $PID
    echo "✅ Generátor smluv byl vypnut."
fi

echo ""
read -p "Stiskni Enter pro zavření tohoto okna... " _
