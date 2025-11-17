#!/bin/bash
# Uruchamia całość: watchdog + frontend
# PORTABLE - używa ścieżek względnych

# Wykryj katalog skryptu
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Uruchamianie pelnego systemu RAG"
echo "===================================="
echo "Katalog projektu: $SCRIPT_DIR"
echo ""

# Inicjalizacja modeli AI
echo "Inicjalizacja modeli AI..."
echo "===================================="
./venv_rag/bin/python3 app/init_models.py
if [ $? -ne 0 ]; then
    echo "Blad podczas inicjalizacji modeli!"
    echo "Sprawdz logi powyzej i sprobuj ponownie."
    exit 1
fi
echo ""

# Uruchom watchdog w tle
echo "Uruchamianie File Watcher (tlo)..."
nohup ./venv_rag/bin/python3 app/file_watcher.py > logs/file_watcher.log 2>&1 &
WATCHER_PID=$!
echo "Watchdog uruchomiony (PID: $WATCHER_PID)"

# Poczekaj chwilę
sleep 2

# Uruchom frontend
echo ""
echo "Uruchamianie Frontend..."
echo "======================================"
echo ""
echo "Dostep lokalny: http://localhost:8501"
echo "Dostep siec lokalna: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "Logowanie: admin / admin123"
echo ""
echo "Watchdog dziala w tle - automatycznie indeksuje nowe pliki w data/"
echo "Nacisnij Ctrl+C aby zatrzymac (watchdog zostanie zatrzymany)"
echo ""

# Trap Ctrl+C
trap "echo ''; echo 'Zatrzymywanie...'; kill $WATCHER_PID 2>/dev/null; exit 0" INT TERM

./venv_rag/bin/python3 -m streamlit run app/app.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true


