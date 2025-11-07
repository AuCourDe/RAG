# ✅ CHECKLIST PORTABLE - RAG v7

## Sprawdzenie przed deploy na inną maszynę

### 1. Skrypty bash (.sh)
- ✅ start_all.sh - używa SCRIPT_DIR i ścieżek względnych
- ✅ start_app.sh - używa SCRIPT_DIR i ścieżek względnych  
- ✅ start_watcher.sh - używa SCRIPT_DIR i ścieżek względnych
- ✅ setup_nginx_ssl.sh - portable

### 2. Kod Python (app/)
- ✅ Brak hardcoded paths /home/rev/projects/RAG2
- ✅ Używa Path(__file__).parent dla ścieżek relatywnych
- ✅ Modele pobierane do ./models/ (wspólny katalog w projekcie)

### 3. Zależności
- ✅ requirements.txt - kompletny z wersjami
- ✅ Wszystkie biblioteki w PyPI

### 4. Konfiguracja
- ✅ auth_config.json - portable (nie zawiera paths)
- ✅ Bazy danych: relative paths (vector_db/, data/)

### 5. Modele AI
- ✅ Whisper: ./models/whisper/ (auto-download)
- ✅ Embeddings: ./models/embeddings/ (auto-download)
- ⚠️  Ollama: ~/.ollama/models/ (wymaga instalacji ollama)

### 6. Wymagania systemu
- Python 3.10+
- CUDA 11.8+ (dla GPU) lub CPU fallback
- ffmpeg (dla wideo/audio)
- Ollama (dla LLM)

## Instrukcje deploy na nową maszynę

### Krok 1: Clone repozytorium
```bash
git clone <repo-url>
cd RAG2
```

### Krok 2: Stwórz venv i zainstaluj zależności
```bash
python3 -m venv venv_rag
source venv_rag/bin/activate
pip install -r requirements.txt
```

### Krok 3: Zainstaluj Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull gemma3:12b
```

### Krok 4: Utwórz foldery
```bash
mkdir -p data logs temp vector_db models
```

### Krok 5: Uruchom
```bash
bash start_all.sh
```

## ✅ PROJEKT JEST PORTABLE!

Wszystkie ścieżki są względne, brak hardcoded paths.
