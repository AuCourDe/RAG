# 📚 System RAG - Dokumenty z Multimodalnym AI

System RAG (Retrieval-Augmented Generation) z frontendem Streamlit, automatycznym monitorowaniem plików, multimodalnym AI (Gemma 3:12B) i zabezpieczeniem hasłem.

## ✨ Funkcje

- 🤖 **Multimodalny AI** - Gemma 3:12B do analizy tekstów i obrazów
- 🔍 **RAG System** - odpowiedzi oparte TYLKO na Twoich dokumentach
- 🌐 **Frontend Streamlit** - nowoczesny interfejs webowy z logowaniem
- 👁️ **Auto-indeksowanie** - watchdog automatycznie indeksuje nowe pliki
- 🖼️ **Podgląd źródeł** - kliknij i zobacz oryginalną stronę PDF lub obraz
- 📊 **Embeddingi GPU** - intfloat/multilingual-e5-large na CUDA
- 🔐 **Bezpieczeństwo** - autoryzacja hasłem, hashowane SHA256
- 🚀 **Gotowe do wdrożenia** - instrukcje dla localhost i internet

## 🎯 Główne cechy

### Restrykcyjny prompt - zero halucynacji
- Odpowiedzi TYLKO na podstawie dostarczonych dokumentów
- Brak używania ogólnej wiedzy modelu
- Jasna informacja gdy brak danych w dokumentach
- Pełna weryfikowalność źródeł

### Interaktywny podgląd źródeł
- Kliknij w źródło → zobacz oryginalną stronę PDF
- Kliknij w źródło → zobacz pełny obraz
- Weryfikuj każdą odpowiedź manualnie
- Przycisk pobierania pełnych dokumentów

### Obsługiwane formaty
- **Dokumenty:** PDF, DOCX, XLSX
- **Obrazy:** JPG, JPEG, PNG, BMP (rozpoznawane przez Gemma 3)
- **Baza:** ChromaDB z embeddingami GPU

## 🚀 Szybki start

### Wymagania

```bash
- Python 3.12
- NVIDIA GPU (CUDA 12.x)
- Ollama z modelem Gemma 3:12B
- 8-12 GB RAM
- ~2 GB wolnego miejsca
```

### Instalacja

1. **Klonuj repo:**
```bash
git clone <your-repo-url>
cd RAG2
```

2. **Utwórz środowisko wirtualne:**
```bash
python3 -m venv venv_rag
source venv_rag/bin/activate
```

3. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

4. **Zainstaluj Ollama i model:**
```bash
# Zainstaluj Ollama (jeśli nie masz)
curl -fsSL https://ollama.com/install.sh | sh

# Pobierz model Gemma 3:12B
ollama pull gemma3:12b
```

5. **Dodaj dokumenty:**
```bash
# Umieść swoje pliki w folderze data/
cp your_documents.pdf data/
cp your_images.jpg data/
```

6. **Indeksuj dokumenty:**
```bash
python rag_system.py index data/
```

7. **Uruchom system:**
```bash
./start_all.sh
```

8. **Otwórz przeglądarkę:**
```
http://localhost:8501
Login: admin
Hasło: admin123
```

⚠️ **ZMIEŃ hasło po pierwszym logowaniu!** (zakładka Ustawienia)

## 📁 Struktura projektu

```
RAG2/
├── app.py                        # Frontend Streamlit
├── rag_system.py                 # Główny system RAG
├── file_watcher.py               # Auto-indeksowanie
├── requirements.txt              # Zależności Python
├── start_all.sh                  # Uruchom wszystko
├── start_app.sh                  # Tylko frontend
├── start_watcher.sh              # Tylko watchdog
├── data/                         # Twoje dokumenty (gitignore)
│   └── .gitkeep
├── vector_db/                    # Baza wektorowa (gitignore)
├── temp/                         # Pliki tymczasowe
└── *.md                          # Dokumentacja
```

## 📚 Dokumentacja

- **README.md** - Główny opis systemu (PL)
- **USAGE.md** - Szczegółowa instrukcja użycia
- **DEPLOY_INTERNET.md** - Jak wystawić na internet (4 opcje)
- **PODGLAD_ZRODEL.md** - Jak korzystać z podglądu źródeł
- **RESTRYKCYJNY_PROMPT.md** - Jak działa prompt bez halucynacji
- **TEST_PODGLAD_ZRODEL.md** - Testy krok po kroku
- **QUICK_START.md** - Szybki start
- **ARCHITEKTURA_BEZPIECZNA.md** - Architektura bezpieczeństwa
- **BEZPIECZENSTWO_BAZY.md** - Bezpieczeństwo danych
- **MODEL_EMBEDDINGOWY.md** - Info o modelu embeddingów

## 🎯 Przykłady użycia

### Pytania o dokumenty PDF:
```
"Jakie są kary za przestępstwo kradzieży?"
"Co grozi za włamanie?"
"Zasady odpowiedzialności karnej"
```

### Pytania o obrazy:
```
"Co znajduje się na obrazach?"
"Opisz zdjęcia zwierząt"
"Jakie są plany architektoniczne?"
```

### System odpowiada TYLKO na podstawie Twoich dokumentów!

## 🔒 Bezpieczeństwo

- ✅ Hasła hashowane SHA256
- ✅ Autoryzacja na poziomie aplikacji
- ✅ Możliwość HTTPS (instrukcje w DEPLOY_INTERNET.md)
- ✅ Firewall i ograniczenie IP
- ✅ Brak wysyłania danych na zewnątrz (poza Ollama lokalnie)

## 🌐 Wdrożenie na internet

Masz stałe IP? Zobacz **DEPLOY_INTERNET.md** z 4 opcjami:

1. **Nginx + SSL** (zalecane dla produkcji) - domena + HTTPS
2. **Bezpośrednie wystawienie** (najprostsze) - stałe IP + port
3. **Cloudflare Tunnel** (darmowa domena + SSL)
4. **ngrok** (szybki test)

## ⚙️ Konfiguracja

### Zmiana domyślnego hasła:
1. Zaloguj się: admin / admin123
2. Zakładka "Ustawienia" → "Zmiana hasła"
3. Min. 6 znaków

### Dostosowanie modelu:
Edytuj `rag_system.py`:
```python
VISION_MODEL = "gemma3:12b"  # Model do obrazów
LLM_MODEL = "gemma3:12b"     # Model do odpowiedzi
```

### Parametry wyszukiwania:
```python
# W interfejsie Streamlit:
n_results = 3  # Liczba fragmentów (3-10)
```

## 🐛 Rozwiązywanie problemów

### Port 8501 zajęty:
```bash
pkill -f "streamlit run app.py"
```

### Ollama nie działa:
```bash
ollama ps  # Sprawdź czy działa
ollama serve  # Uruchom jeśli nie działa
```

### PyMuPDF nie zainstalowany:
```bash
pip install --break-system-packages PyMuPDF
```

### Baza nie działa:
```bash
# Zreindeksuj wszystko
python rag_system.py index data/
```

## 📊 Wydajność

**GPU: NVIDIA RTX 3060 12GB**

| Operacja | Czas |
|----------|------|
| Indeksowanie PDF (100 stron) | ~10-20s |
| Rozpoznawanie obrazu | ~10-30s |
| Generowanie odpowiedzi | ~30-120s |
| Wyszukiwanie w bazie | ~1-3s |

## 🤝 Wkład

To jest prywatne repo. Jeśli chcesz dodać funkcje:

1. Fork repo
2. Utwórz branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Otwórz Pull Request

## 📝 Changelog

Zobacz `action_log.txt` dla pełnej historii zmian.

### Najnowsze funkcje (2025-10-12):
- ✅ Interaktywny podgląd źródeł (PDF + obrazy)
- ✅ Restrykcyjny prompt (zero halucynacji)
- ✅ PyMuPDF rendering stron PDF
- ✅ Dokumentacja wdrożenia na internet

## 📜 Licencja

Prywatny projekt. Wszelkie prawa zastrzeżone.

## 📞 Kontakt

Jeśli masz pytania - sprawdź dokumentację w plikach `.md` lub action_log.txt.

---

**System RAG - Twoje dokumenty, Twoje odpowiedzi, Twoja kontrola.** 🚀

