# STRUKTURA PROJEKTU RAG v4

## 📁 Główne foldery

```
RAG2/
├── app/                    # Aplikacja główna
│   ├── app.py             # Frontend Streamlit
│   ├── rag_system.py      # System RAG (core)
│   ├── model_provider.py  # Provider LLM (Ollama/OpenAI)
│   ├── hybrid_search.py   # Wyszukiwanie hybrydowe
│   ├── device_manager.py  # Zarządzanie GPU/CPU
│   ├── audit_logger.py    # Logowanie audytu
│   ├── file_watcher.py    # Automatyczna indeksacja
│   ├── web_search.py      # Wyszukiwanie webowe
│   ├── greeting_filter.py # Filtr powitań
│   ├── manage_users.py    # Zarządzanie użytkownikami
│   └── reindex_images.py  # Reindeksacja obrazów
│
├── docs/                   # Dokumentacja
│   ├── README.md
│   ├── AZURE_DEPLOYMENT.md
│   ├── AUDIO_INSTRUKCJA.md
│   ├── VIDEO_WORKFLOW.md
│   └── ... (inne *.md)
│
├── logs/                   # Logi systemowe
│   ├── rag_system.log
│   ├── streamlit.log
│   ├── file_watcher.log
│   └── ... (inne *.log, test_*.log)
│
├── test/                   # Testy i pliki testowe
│   ├── sample_test_file/  # Audio do testów
│   ├── sample_test_files/ # PDF, Image, Video
│   ├── test_*.py          # Skrypty testowe
│   ├── rozmowa_*_SPEAKERS.json  # Transkrypcje
│   └── video_description.json
│
├── models/                 # Cache modeli AI
│   ├── whisper/           # Modele Whisper (będzie)
│   ├── embeddings/        # Modele embedding (będzie)
│   └── spkrec_model/      # Speaker recognition (będzie)
│
├── data/                   # Dane użytkownika (upload)
├── data_backup/            # Backupy danych
├── vector_db/              # Baza wektorowa ChromaDB
├── temp/                   # Pliki tymczasowe
├── another_and_old/        # Stare wersje/archiwum
│
├── venv_rag/               # Virtual environment Python
│
├── requirements.txt        # Zależności Python
├── action_log.txt          # Log zmian w projekcie
├── auth_config.json        # Konfiguracja auth
├── audit_log.jsonl         # Audit trail
├── image_descriptions.json # Cache opisów obrazów
├── suggested_questions.json
│
├── start_all.sh            # Uruchomienie kompletne
├── start_app.sh            # Tylko frontend
├── start_watcher.sh        # Tylko file watcher
└── setup_nginx_ssl.sh      # Setup dla produkcji
```

## 🎯 Główne komponenty

### Backend (app/)
- `rag_system.py` - Core RAG: przetwarzanie dokumentów, embeddings, query
- `model_provider.py` - Integracja z LLM (Ollama, OpenAI)
- `hybrid_search.py` - Wyszukiwanie: Vector + BM25 + Reranker
- `device_manager.py` - Auto GPU/CPU detection

### Frontend (app/)
- `app.py` - Streamlit UI (modern glassmorphism)

### Modele AI
- Whisper large-v3 (~3 GB) - transkrypcja audio
- intfloat/multilingual-e5-large - embeddings (1024 dim)
- Gemma 3 Vision - analiza obrazów/wideo
- gemma3:12b (Ollama) - generowanie odpowiedzi

## 🚀 Uruchomienie

```bash
# Pełny system (watcher + frontend)
bash start_all.sh

# Tylko frontend
bash start_app.sh

# Tylko watcher
bash start_watcher.sh
```

## 📊 Monitoring
- GPU: NVIDIA RTX 3060 (12.9 GB VRAM)
- CPU: Real-time monitoring
- RAM: Real-time monitoring
- Auto-refresh: co 2s
