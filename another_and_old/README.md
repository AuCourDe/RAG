# 📁 Another and Old - Dodatkowa dokumentacja i narzędzia

Ten folder zawiera dodatkowe pliki dokumentacji i pomocnicze skrypty, które nie są niezbędne do podstawowego działania systemu RAG.

---

## 📚 Dokumentacja dodatkowa (11 plików .md)

### Instrukcje i przewodniki:
- **USAGE.md** - Szczegółowa instrukcja użycia systemu
- **QUICK_START.md** - Szybki start
- **DEPLOY_INTERNET.md** - Jak wystawić aplikację na internet (4 opcje)
- **TEST_PODGLAD_ZRODEL.md** - Testy funkcji podglądu źródeł

### Dokumentacja techniczna:
- **ARCHITEKTURA_BEZPIECZNA.md** - Architektura zabezpieczeń
- **BEZPIECZENSTWO_BAZY.md** - Bezpieczeństwo bazy wektorowej
- **MODEL_EMBEDDINGOWY.md** - Informacje o modelu embeddingów
- **FRAGMENTY_WYJASNIONE.md** - Co to są fragmenty w bazie
- **RESTRYKCYJNY_PROMPT.md** - Jak działa prompt bez halucynacji
- **PODGLAD_ZRODEL.md** - Funkcjonalność podglądu PDF/obrazów

### Specjalne:
- **README_GITHUB.md** - README dla GitHub (publiczne repo)

---

## 🛠️ Pomocnicze skrypty (5 plików .py)

### Narzędzia diagnostyczne:
- **view_image_descriptions.py** - Podgląd opisów obrazów wygenerowanych przez Gemma 3
- **view_file_chunks.py** - Podgląd fragmentów konkretnego pliku

### Narzędzia jednorazowe:
- **generate_questions_for_existing.py** - Generowanie pytań dla już zaindeksowanych plików
- **create_secure_vector_db.py** - Tworzenie bezpiecznej bazy (tylko embeddingi, bez tekstów)
- **secure_rag_example.py** - Przykład bezpiecznej konfiguracji

---

## 💡 Kiedy używać tych plików?

### Użyj dokumentacji jeśli:
- Chcesz wystawić aplikację na internet → **DEPLOY_INTERNET.md**
- Potrzebujesz szczegółowych instrukcji → **USAGE.md**
- Chcesz zrozumieć bezpieczeństwo → **BEZPIECZENSTWO_BAZY.md**
- Testujesz funkcje → **TEST_PODGLAD_ZRODEL.md**

### Użyj skryptów jeśli:
- Chcesz zobaczyć opisy obrazów → `python view_image_descriptions.py`
- Debugujesz fragmenty → `python view_file_chunks.py "plik.pdf"`
- Potrzebujesz bezpiecznej bazy → `python create_secure_vector_db.py`

---

## 📦 Struktura głównego folderu (po uporządkowaniu)

W głównym folderze `/home/rev/projects/RAG2/` pozostały tylko **niezbędne pliki**:

```
RAG2/
├── app.py                     # Frontend Streamlit ⭐
├── rag_system.py              # Główny system RAG ⭐
├── file_watcher.py            # Auto-indeksowanie ⭐
├── manage_users.py            # Zarządzanie użytkownikami ⭐
├── reindex_images.py          # Reindeksowanie obrazów
├── test_rag.py                # Testy systemu
├── start_all.sh               # Uruchom wszystko ⭐
├── start_app.sh               # Uruchom frontend
├── start_watcher.sh           # Uruchom watchdog
├── setup_nginx_ssl.sh         # Setup Nginx + SSL
├── requirements.txt           # Zależności Python ⭐
├── .gitignore                 # Git config
├── README.md                  # Główna dokumentacja ⭐
├── WORKFLOW_I_SKALOWANIE.md   # Workflow + skalowanie ⭐
├── action_log.txt             # Historia zmian
├── data/                      # Dokumenty źródłowe
├── vector_db/                 # Baza wektorowa
└── another_and_old/           # Dodatkowa dokumentacja
```

---

## 🔄 Przeniesienie z powrotem

Jeśli potrzebujesz jakiegoś pliku:

```bash
# Skopiuj z powrotem
cp another_and_old/PLIK.md ./

# Lub zobacz zawartość
cat another_and_old/PLIK.md
```

---

**Pliki w tym folderze są bezpieczne i mogą być użyte w razie potrzeby.**


