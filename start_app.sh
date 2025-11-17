#!/bin/bash
# Skrypt startowy dla aplikacji Streamlit
# PORTABLE - używa ścieżek względnych

# Wykryj katalog skryptu
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Uruchamianie Systemu RAG - Frontend"
echo "======================================"
echo "Katalog projektu: $SCRIPT_DIR"
echo ""
echo "Dostep lokalny: http://localhost:8501"
echo "Dostep siec lokalna: http://$(hostname -I | awk '{print $1}'):8501"
echo ""
echo "Logowanie: admin / admin123"
echo ""

./venv_rag/bin/python3 -m streamlit run app/app.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true


