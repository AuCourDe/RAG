#!/bin/bash
# Uruchomienie frontendu Gradio dla systemu RAG

cd "$(dirname "$0")"

# Aktywuj venv jeśli istnieje
if [ -d "venv_rag" ]; then
    source venv_rag/bin/activate
fi

# Uruchom Gradio
echo "Uruchamianie frontendu Gradio..."
echo "======================================"
echo "Dostęp lokalny: http://localhost:7860"
echo "Dostęp sieci lokalna: http://$(hostname -I | awk '{print $1}'):7860"
echo "Logowanie: admin / admin123"
echo "Naciśnij Ctrl+C aby zatrzymać"
echo ""

python3 app/frontend_gradio.py

