# 📚 RAG - System testowy v4.0

System RAG (Retrieval-Augmented Generation) z multimodalnym AI, hybrydowym wyszukiwaniem, frontendem Streamlit i pełnym audit loggingiem.

**Odpowiedzi na pytania TYLKO na podstawie Twoich dokumentów - zero halucynacji!**

## ⭐ Nowe funkcje v4.0

### 🎯 Hybrydowe Wyszukiwanie (PRIORYTET 1)
- **Vector Search** (semantic) + **BM25 Text Search** (lexical) + **Cross-Encoder Reranking**
- **+15-25% lepsza jakość** wyników wyszukiwania
- Świetne dla: terminologii prawnej, nazw własnych, numerów artykułów

### 🤖 OpenAI API Integration
- **Dynamiczne pobieranie modeli** z OpenAI API
- Automatyczny wybór: **gpt-4o-mini** (najlepszy stosunek jakość/cena)
- **Fallback**: Gemma 3:12B (lokalny, darmowy)
- Konfiguracja przez UI (zakładka Ustawienia)

### 📊 Audit Logging + GDPR Compliance
- Pełne **logowanie aktywności użytkowników**: zapytania, odpowiedzi, źródła, upload, delete
- Format: **JSONL** (łatwy parsing)
- **GDPR**: retention 90 dni, prawo do bycia zapomnianym
- Session tracking + privacy options

### ⚙️ GPU/CPU Auto-Detection
- **Automatyczne dostosowanie** do dostępnego sprzętu
- Modes: auto, gpu, cpu, hybrid
- Per-component: embeddings, llm, reranker
- Działa na CPU-only systemach!

### 🌐 Web Search (Intranet/Internet)
- **Bing Search API** + Web Scraping
- Site filtering dla **intranetu** (site:firma.pl)
- HTML → Markdown conversion
- Cache 24h (oszczędność kosztów)

### 🔍 UX Improvements
- **Automatyczne filtrowanie powitań** ("Cześć!", "Dzień dobry")
- Oszczędność tokenów + lepsza jakość odpowiedzi

## 🚀 Szybki start

### 1. Uruchom kompletny system:
```bash
./start_all.sh
```

To uruchomi:
- ✅ Watchdog (automatyczne indeksowanie nowych plików)
- ✅ Frontend Streamlit (http://localhost:8501)

### 2. Zaloguj się:
```
👤 Użytkownik: admin
🔑 Hasło: admin123
```

⚠️ **ZMIEŃ hasło po pierwszym logowaniu!** (zakładka Ustawienia)

---

## 📦 Komponenty systemu

### 1. 👁️ File Watcher (automatyczne indeksowanie)

Monitoruje folder `data/` i automatycznie indeksuje nowe pliki.

**Uruchomienie:**
```bash
./start_watcher.sh
```

**Obsługiwane formaty:**
- PDF, DOCX, XLSX
- JPG, JPEG, PNG, BMP (rozpoznawane przez Gemma 3:12B)

**Jak działa:**
1. Dodaj plik do folderu `data/`
2. Watchdog wykrywa nowy plik
3. Automatycznie przetwarza i dodaje do bazy wektorowej
4. Gotowe! (czas: 10-60 sekund zależnie od rozmiaru)

---

### 2. 🌐 Frontend Streamlit

Interfejs webowy do przeszukiwania dokumentów.

**Uruchomienie:**
```bash
./start_app.sh
```

**Dostęp:**
- Lokalny: http://localhost:8501
- Sieć lokalna: http://[IP_KOMPUTERA]:8501

**Funkcje:**
- 💬 Zadawanie pytań o dokumenty
- 📤 Upload i indeksowanie nowych plików
- 📊 Statystyki bazy wektorowej
- 🔐 Zmiana hasła
- ⚙️ Konfiguracja systemu

---

## 🌐 Udostępnienie w internecie

### Opcja 1: ngrok (najprostsza)

```bash
# Zainstaluj
snap install ngrok

# Uruchom aplikację
./start_app.sh

# W nowym terminalu:
ngrok http 8501
```

Otrzymasz publiczny URL: `https://xyz.ngrok.io`

### Opcja 2: Cloudflare Tunnel (darmowy, stały URL)

```bash
# Zainstaluj
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Uruchom tunel
cloudflared tunnel --url http://localhost:8501
```

### Opcja 3: SSH Tunnel (własny serwer)

```bash
ssh -R 8501:localhost:8501 user@twoj-serwer.com
```

⚠️ **BEZPIECZEŃSTWO:**
- Zawsze zmieniaj domyślne hasło!
- Używaj HTTPS w internecie
- Rozważ ograniczenie IP (firewall)

---

## 🔧 Ręczne użycie

### Indeksowanie dokumentów:
```bash
python rag_system.py index data/
```

### Zadawanie pytań:
```bash
python rag_system.py query "Twoje pytanie?"
```

### Tylko obrazy:
```bash
python reindex_images.py
```

### Bezpieczna baza (bez tekstów):
```bash
python create_secure_vector_db.py
```

---

## 📊 Architektura

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM RAG                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📁 data/                                               │
│     ↓ (watchdog monitoruje)                            │
│  👁️ File Watcher                                        │
│     ↓ (automatyczne indeksowanie)                       │
│  🔄 Document Processor                                  │
│     • PDF → pdfplumber → tekst                         │
│     • Obrazy → Gemma 3:12B (GPU) → opis                │
│     ↓                                                    │
│  🧮 Embeddings (intfloat/multilingual-e5-large, GPU)   │
│     ↓                                                    │
│  💾 ChromaDB (vector_db/)                               │
│     • 3,483 fragmenty                                   │
│     • 42 MB                                             │
│     ↓                                                    │
│  🌐 Streamlit Frontend (port 8501)                      │
│     • Autoryzacja hasłem                                │
│     • Interface użytkownika                             │
│     • Upload nowych plików                              │
│     ↓                                                    │
│  🤖 Gemma 3:12B (GPU)                                   │
│     • Generuje odpowiedzi                               │
│     • Z referencjami do źródeł                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔐 Bezpieczeństwo

### Domyślne dane logowania:
- Użytkownik: `admin`
- Hasło: `admin123`

### Zmiana hasła:
1. Zaloguj się
2. Przejdź do zakładki "Ustawienia"
3. Wypełnij formularz zmiany hasła
4. Minimum 6 znaków

### Hasła są hashowane (SHA256)
- Przechowywane w: `auth_config.json`
- Nie ma możliwości odczytania hasła
- Tylko porównanie hashy

---

## ⚙️ Wymagania

- Python 3.12
- NVIDIA GPU (RTX 3060 12GB)
- CUDA 12.8
- Ollama z modelem Gemma 3:12B
- 2-3 GB RAM dla frontendu

---

## 📁 Struktura projektu

```
/home/rev/projects/RAG2/
├── app.py                        # Frontend Streamlit
├── file_watcher.py               # Watchdog (auto-indeksowanie)
├── rag_system.py                 # Główny kod RAG
├── start_all.sh                  # ⭐ Uruchom wszystko
├── start_app.sh                  # Tylko frontend
├── start_watcher.sh              # Tylko watchdog
├── requirements.txt              # Biblioteki Python
├── data/                         # Dokumenty źródłowe
├── vector_db/                    # Baza wektorowa (pełna)
├── vector_db_public/             # Baza bez tekstów (bezpieczna)
├── vector_db_private/            # Mapowanie ID→tekst (lokalnie)
└── venv_rag/                     # Środowisko Python
```

---

## 📈 Wydajność

**GPU: NVIDIA RTX 3060 12GB**

| Operacja | Czas | Procesor |
|----------|------|----------|
| Indeksowanie PDF (100 stron) | ~10-20 sek | GPU |
| Rozpoznawanie obrazu | ~10-30 sek | GPU (Gemma 3) |
| Tworzenie embeddingów | ~0.02 sek/fragment | GPU |
| Generowanie odpowiedzi | ~30-120 sek | GPU (Gemma 3) |
| Wyszukiwanie w bazie | ~1-3 sek | GPU |

---

## 🐛 Rozwiązywanie problemów

### Frontend nie startuje:
```bash
# Sprawdź czy port 8501 jest wolny
lsof -i :8501

# Zabij proces jeśli zajęty
kill -9 $(lsof -t -i:8501)
```

### Ollama nie używa GPU:
```bash
ollama ps
# Powinno pokazać: "100% GPU"
# Jeśli "100% CPU" - sprawdź instalację Ollama
```

### Watchdog nie indeksuje:
```bash
# Sprawdź logi
tail -f file_watcher.log
```

---

## 📝 Logi

- `rag_system.log` - główny log systemu
- `file_watcher.log` - log watchdoga
- `action_log.txt` - log wszystkich działań
- `audit_log.jsonl` - **NOWE!** audit trail użytkowników (JSONL)
- `streamlit.log` - logi frontendu (jeśli są)

---

## 🎯 Przykładowe pytania

- "Co grozi za przestępstwo kradzieży?"
- "Jakie są zasady odpowiedzialności karnej?"
- "Co znajduje się na obrazach?"
- "Opisz zawartość dokumentu o..."

---

## 📞 Dokumentacja

### **Główne dokumenty:**
- 📄 **WORKFLOW_I_SKALOWANIE.md** - Kompletny opis działania systemu, workflow, skalowanie (1 GB → 2 TB), zabezpieczenia
- 📄 **action_log.txt** - Historia wszystkich zmian i działań

### **Dodatkowa dokumentacja:**
Znajduje się w folderze `another_and_old/`:
- Instrukcje użycia (USAGE.md, QUICK_START.md)
- Wdrożenie na internet (DEPLOY_INTERNET.md)
- Bezpieczeństwo (ARCHITEKTURA_BEZPIECZNA.md, BEZPIECZENSTWO_BAZY.md)
- Funkcje systemu (PODGLAD_ZRODEL.md, RESTRYKCYJNY_PROMPT.md)
- Pomocnicze skrypty Python

---

## 👥 Zarządzanie użytkownikami

```bash
# Dodaj użytkownika
python3 manage_users.py add LOGIN HASŁO "Imię"

# Lista użytkowników
python3 manage_users.py list

# Tryb interaktywny (menu)
python3 manage_users.py
```

---

## ⚙️ Konfiguracja (auth_config.json)

### OpenAI API (opcjonalne)
```json
"openai": {
  "api_key": "sk-...",           // Klucz z platform.openai.com
  "model": "gpt-4o-mini",        // Lub zostaw puste dla auto
  "enabled": true
}
```

### Bing Search API (opcjonalne - dla web search)
```json
"web_search": {
  "enabled": true,
  "bing_api_key": "YOUR_KEY",    // Klucz z azure.microsoft.com
  "intranet_sites": ["wiki.firma.pl"],  // Domeny intranetu
  "max_results": 3,
  "cache_ttl_hours": 24
}
```

### Device Mode (opcjonalne)
Domyślnie: 'auto' (automatyczna detekcja GPU/CPU)
```python
# W kodzie lub przez UI
rag_system = RAGSystem(device_mode='auto')  # auto, gpu, cpu, hybrid
```

---

**Autor:** System RAG v4.0  
**Data:** 2025-11-04  
**Status:** ✅ Produkcja - Hybrydowe wyszukiwanie + OpenAI API + Audit Logging

**Zobacz także:** 
- 📄 **PLAN_ROZWOJU.md** - Plan rozwoju i dokumentacja techniczna v4.0 (wszystkie 6 funkcji)


