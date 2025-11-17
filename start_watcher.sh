#!/bin/bash
# Skrypt startowy dla watchdog (monitorowanie folderu data/)
# PORTABLE - używa ścieżek względnych

# Wykryj katalog skryptu
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Uruchamianie File Watcher - Automatyczne indeksowanie"
echo "=========================================================="
echo "Katalog projektu: $SCRIPT_DIR"
echo "Monitorowany folder: data/"
echo "Obslugiwane formaty: PDF, DOCX, XLSX, JPG, JPEG, PNG, BMP, MP3, MP4"
echo ""
echo "Dodaj nowy plik do folderu 'data/' aby go automatycznie zindeksowac"
echo "Nacisnij Ctrl+C aby zatrzymac"
echo ""

./venv_rag/bin/python3 app/file_watcher.py 2>&1 | tee logs/file_watcher.log


