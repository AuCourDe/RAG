# 📁 STRUKTURA PROJEKTU RAG v4 - NOWA ORGANIZACJA

## Zmiana struktury (2025-11-06)

Projekt został zreorganizowany dla lepszej przejrzystości i łatwiejszego zarządzania.

---

## 🗂️ Nowa struktura folderów

```
RAG2/
│
├── 📂 app/                         # APLIKACJA GŁÓWNA
│   ├── app.py                      # Frontend Streamlit
│   ├── rag_system.py               # Core RAG system
│   ├── model_provider.py           # Provider LLM (Ollama/OpenAI)
│   ├── hybrid_search.py            # Wyszukiwanie hybrydowe
│   ├── device_manager.py           # GPU/CPU management
│   ├── audit_logger.py             # Logging audytu
│   ├── file_watcher.py             # Auto-indeksacja (watchdog)
│   ├── web_search.py               # Web search integration
│   ├── greeting_filter.py          # Filtr powitań
│   ├── manage_users.py             # Zarządzanie użytkownikami
│   └── reindex_images.py           # Reindeksacja obrazów
│
├── 📂 docs/                        # DOKUMENTACJA
│   ├── README.md                   # Główny README
│   ├── AZURE_DEPLOYMENT.md         # Deploy na Azure
│   ├── AUDIO_INSTRUKCJA.md         # Obsługa audio
│   ├── VIDEO_WORKFLOW.md           # Obsługa wideo
│   ├── JAK_DZIALA_OLLAMA.md        # Wyjaśnienie Ollama
│   ├── LISTA_ZMIAN_V4.md           # Changelog v4
│   ├── PLAN_ROZWOJU.md             # Roadmap
│   └── ... (inne instrukcje)
│
├── 📂 logs/                        # LOGI SYSTEMOWE
│   ├── rag_system.log              # Główny log systemu RAG
│   ├── streamlit.log               # Log Streamlit
│   ├── file_watcher.log            # Log watchdog
│   ├── action_log.txt              # Historia zmian w projekcie
│   └── test_*.log                  # Logi testów
│
├── 📂 test/                        # TESTY
│   ├── 📁 sample_test_file/        # Pliki audio testowe
│   │   ├── rozmowa (1).mp3
│   │   └── rozmowa (2).mp3
│   ├── 📁 sample_test_files/       # Inne pliki testowe
│   │   ├── test_document.pdf
│   │   ├── test_image.png
│   │   └── test_video.mp4
│   ├── test_full_system.py         # Testy kompletne
│   ├── test_comprehensive.py
│   ├── analyze_speakers.py         # Analiza mówców
│   ├── rozmowa_*_SPEAKERS.json     # Transkrypcje z mówcami
│   └── video_description.json      # Opis wideo
│
├── 📂 models/                      # CACHE MODELI AI
│   ├── whisper/                    # Modele Whisper (symlink)
│   ├── embeddings/                 # Modele embedding (symlink)
│   └── reranker/                   # Modele reranker
│
├── 📂 data/                        # DANE UŻYTKOWNIKA
│   └── (pliki uploadowane przez UI)
│
├── 📂 data_backup/                 # BACKUPY
│   └── (backupy plików)
│
├── 📂 vector_db/                   # BAZA WEKTOROWA
│   ├── chroma.sqlite3
│   ├── bm25_index.pkl
│   └── (kolekcje ChromaDB)
│
├── 📂 temp/                        # PLIKI TYMCZASOWE
│   └── (audio z wideo, tmp files)
│
├── 📂 another_and_old/             # ARCHIWUM
│   └── (stare wersje skryptów)
│
├── 📂 venv_rag/                    # VIRTUAL ENVIRONMENT
│   └── (Python packages)
│
├── 📄 requirements.txt             # Zależności Python
├── 📄 action_log.txt               # Log zmian projektu
├── 📄 auth_config.json             # Konfiguracja auth
├── 📄 audit_log.jsonl              # Audit trail
├── 📄 image_descriptions.json      # Cache opisów obrazów
├── 📄 suggested_questions.json     # Sugerowane pytania
│
├── 🚀 start_all.sh                 # Start kompletny (watcher + UI)
├── 🚀 start_app.sh                 # Start tylko UI
├── 🚀 start_watcher.sh             # Start tylko watcher
└── 🚀 setup_nginx_ssl.sh           # Setup produkcji (nginx + SSL)
```

---

## 🔄 Migracja cache modeli

### Modele są teraz w:
- **Whisper:** `~/.cache/whisper/` → symlink w `models/whisper/`
- **Embeddings:** `~/.cache/huggingface/` → symlink w `models/embeddings/`
- **Ollama:** `~/.ollama/models/` (osobny serwis, nie w projekcie)

### Dlaczego symlinki?
- Nie duplikujemy wielkich modeli (Whisper large-v3 = 3 GB)
- Modele są współdzielone między projektami
- Łatwe zarządzanie cache

---

## 🚀 Uruchomienie po reorganizacji

Wszystko działa **bez zmian**:

```bash
# Standardowo
bash start_all.sh

# Aplikacja uruchamia się z app/app.py
# File watcher z app/file_watcher.py
# Logi zapisują się do logs/
```

---

## 📦 Deployment

### Co kopiować na Azure:
```bash
# Podstawowe
app/                    # Aplikacja
docs/                   # Dokumentacja
data/                   # (pusty folder)
vector_db/              # (pusty folder)
temp/                   # (pusty folder)
venv_rag/               # Lub zainstaluj przez requirements.txt
requirements.txt
auth_config.json
*.sh                    # Skrypty startowe

# Opcjonalne
test/                   # Testy (nie wymagane w produkcji)
models/                 # Cache modeli (zbuduje się automatycznie)
```

### Nie kopiować:
- `logs/` - logi lokalne
- `another_and_old/` - archiwum
- `__pycache__/` - cache Python
- `.git/` - historia git

---

## 💡 Zalety nowej struktury

✅ **Przejrzystość:** Kod aplikacji w `app/`, dokumentacja w `docs/`  
✅ **Logi oddzielone:** Łatwiejsze debugowanie  
✅ **Testy oddzielone:** Nie mieszają się z produkcją  
✅ **Portable:** Wszystkie ścieżki względne w skryptach  
✅ **Gotowe do deploy:** Prosta struktura dla Azure/Docker  

---

## 🔧 Aktualizacja requirements.txt

Po reorganizacji dodano:
- `librosa>=0.11.0` - analiza audio (MFCC, pitch)
- `scikit-learn>=1.3.0` - clustering mówców
- `speechbrain>=1.0.0` - speaker recognition (opcjonalnie)
- `pyannote.audio>=3.1.0` - speaker diarization (opcjonalnie)

---

**Data reorganizacji:** 2025-11-06  
**Wersja:** v4  
**Status:** ✅ Production ready

