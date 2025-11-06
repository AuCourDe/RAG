#!/bin/bash
# Uruchamia całość: watchdog + frontend
# PORTABLE - używa ścieżek względnych

# Wykryj katalog skryptu
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Uruchamianie pełnego systemu RAG"
echo "===================================="
echo "📁 Katalog projektu: $SCRIPT_DIR"
echo ""

# Uruchom watchdog w tle
echo "👁️  Uruchamianie File Watcher (tło)..."
nohup ./venv_rag/bin/python3 app/file_watcher.py > logs/file_watcher.log 2>&1 &
WATCHER_PID=$!
echo "   ✅ Watchdog uruchomiony (PID: $WATCHER_PID)"

# Poczekaj chwilę
sleep 2

# Uruchom frontend
echo ""
echo "🌐 Uruchamianie Frontend..."
echo "======================================"
echo ""
echo "📱 Dostęp lokalny: http://localhost:8501"
echo "🌐 Dostęp sieć lokalna: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "👤 Logowanie: admin / admin123"
echo ""
echo "💡 Watchdog działa w tle - automatycznie indeksuje nowe pliki w data/"
echo "⏹️  Naciśnij Ctrl+C aby zatrzymać (watchdog zostanie zatrzymany)"
echo ""

# Trap Ctrl+C
trap "echo ''; echo '⏹️  Zatrzymywanie...'; kill $WATCHER_PID 2>/dev/null; exit 0" INT TERM

./venv_rag/bin/python3 -m streamlit run app/app.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true


