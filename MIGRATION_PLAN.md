# Plan Migracji Frontendu RAG-Reborn

## Analiza Obecnego Stanu

### Funkcjonalności do przeniesienia:
1. **Autoryzacja** - logowanie z hasłem, sesje, timeout
2. **Upload plików** - wielokrotny upload, progress, walidacja
3. **Wyszukiwanie** - 4 strategie (Wektor, Tekst, Hybrid, Reranking)
4. **Wyświetlanie wyników** - odpowiedzi, źródła, podgląd PDF
5. **Zarządzanie plikami** - lista plików, reindeksacja, usuwanie
6. **Historia** - zapytania i odpowiedzi
7. **Parametry modelu** - temperature, top_p, top_k, max_tokens
8. **UI** - glassmorphism design, dark/light theme
9. **Logi** - wyświetlanie logów systemu
10. **Flask endpoint** - już istnieje dla uploadu (port 5001)

---

## OPCJA 1: Gradio (REKOMENDOWANA) ⭐

### Zalety:
- ✅ Najbliższe Streamlit w użyciu
- ✅ Łatwa migracja (podobna składnia)
- ✅ Doskonałe wsparcie dla ML/AI
- ✅ Wbudowane komponenty (upload, chat, interface)
- ✅ Automatyczne API
- ✅ Łatwe wdrożenie
- ✅ Dobra dokumentacja

### Wady:
- ⚠️ Mniej elastyczne niż własny frontend
- ⚠️ Ograniczone możliwości customizacji UI

### Plan Implementacji:

#### KROK 1: Przygotowanie środowiska
```bash
pip install gradio
# Gradio zastąpi Streamlit
```

#### KROK 2: Struktura nowego frontendu
```
app/
  ├── frontend_gradio.py      # Nowy frontend Gradio
  ├── rag_system.py           # Bez zmian
  ├── audit_logger.py         # Bez zmian
  └── ...
```

#### KROK 3: Migracja komponentów
- `st.text_input` → `gr.Textbox`
- `st.button` → `gr.Button`
- `st.selectbox` → `gr.Dropdown`
- `st.file_uploader` → `gr.File`
- `st.markdown` → `gr.Markdown`
- `st.expander` → `gr.Accordion`
- `st.columns` → `gr.Row`, `gr.Column`

#### KROK 4: Funkcjonalności
1. **Autoryzacja** - custom HTML block + session state
2. **Upload** - `gr.File` z `file_count="multiple"`
3. **Wyszukiwanie** - `gr.Interface` lub `gr.Blocks`
4. **Wyniki** - `gr.Markdown` + `gr.Accordion` dla źródeł
5. **Historia** - `gr.Dataframe` lub `gr.JSON`

#### KROK 5: UI/UX
- CSS custom styling przez `gr.HTML`
- Theme przez `theme` parameter
- Layout przez `gr.Blocks` z `gr.Row`/`gr.Column`

#### KROK 6: Integracja z Flask
- Flask endpoint (port 5001) pozostaje bez zmian
- Gradio (port 7860) komunikuje się z Flask API

#### KROK 7: Testy i weryfikacja
- Test wszystkich funkcjonalności
- Test uploadu plików
- Test wyszukiwania (wszystkie strategie)
- Test autoryzacji

#### Szacowany czas: 4-6 godzin

---

## OPCJA 2: FastAPI + Prosty Frontend (HTML/JS)

### Zalety:
- ✅ Pełna kontrola nad UI
- ✅ REST API gotowe do użycia
- ✅ Wysoka wydajność
- ✅ Łatwe skalowanie
- ✅ Możliwość użycia React/Vue w przyszłości

### Wady:
- ⚠️ Więcej pracy (więcej kodu)
- ⚠️ Trzeba napisać frontend od zera
- ⚠️ Więcej czasu na implementację

### Plan Implementacji:

#### KROK 1: Przygotowanie środowiska
```bash
pip install fastapi uvicorn jinja2 python-multipart
```

#### KROK 2: Struktura projektu
```
app/
  ├── api/
  │   ├── __init__.py
  │   ├── main.py           # FastAPI app
  │   ├── routes/
  │   │   ├── auth.py       # Autoryzacja
  │   │   ├── search.py      # Wyszukiwanie
  │   │   ├── upload.py     # Upload plików
  │   │   └── files.py      # Zarządzanie plikami
  │   └── models.py         # Pydantic models
  ├── templates/
  │   ├── base.html
  │   ├── index.html
  │   ├── login.html
  │   └── search.html
  ├── static/
  │   ├── css/
  │   │   └── style.css     # Glassmorphism design
  │   ├── js/
  │   │   └── app.js        # Frontend logic
  │   └── images/
  └── ...
```

#### KROK 3: API Endpoints
```python
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/search?query=...&mode=...
POST   /api/upload
GET    /api/files
DELETE /api/files/{filename}
POST   /api/reindex
GET    /api/history
```

#### KROK 4: Frontend (HTML/CSS/JS)
- **HTML** - szablony Jinja2
- **CSS** - przeniesienie obecnego glassmorphism design
- **JavaScript** - fetch API do komunikacji z backendem
- **Komponenty**:
  - Formularz logowania
  - Upload plików (drag & drop)
  - Formularz wyszukiwania
  - Wyświetlanie wyników
  - Historia zapytań

#### KROK 5: Integracja z RAG System
- RAG system jako service layer
- FastAPI jako wrapper
- Session management przez cookies/JWT

#### KROK 6: Testy
- Test API endpoints
- Test frontendu
- Test integracji

#### Szacowany czas: 8-12 godzin

---

## OPCJA 3: Flask + Jinja2 (Rozbudowa obecnego Flask)

### Zalety:
- ✅ Flask już jest w projekcie (upload endpoint)
- ✅ Prostsze niż FastAPI
- ✅ Jinja2 templates
- ✅ Mniej zależności

### Wady:
- ⚠️ Mniej nowoczesne niż FastAPI
- ⚠️ Trzeba napisać frontend od zera
- ⚠️ Mniej funkcji out-of-the-box

### Plan Implementacji:

#### KROK 1: Rozbudowa Flask app
```python
# app/flask_app.py
from flask import Flask, render_template, request, jsonify, session

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Routes
@app.route('/')
def index():
    if not session.get('authenticated'):
        return redirect('/login')
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    # Integracja z RAG system
    pass
```

#### KROK 2: Struktura (podobna do FastAPI)
```
app/
  ├── flask_app.py          # Główna aplikacja Flask
  ├── routes/
  │   ├── auth.py
  │   ├── search.py
  │   └── upload.py
  ├── templates/
  │   └── (jak w FastAPI)
  └── static/
      └── (jak w FastAPI)
```

#### KROK 3-6: Podobne do FastAPI, ale prostsze

#### Szacowany czas: 6-10 godzin

---

## Porównanie Opcji

| Kryterium | Gradio | FastAPI + HTML/JS | Flask + Jinja2 |
|-----------|--------|------------------|----------------|
| **Czas implementacji** | 4-6h | 8-12h | 6-10h |
| **Trudność** | Łatwa | Średnia | Średnia |
| **Elastyczność UI** | Ograniczona | Pełna | Pełna |
| **Wydajność** | Dobra | Bardzo dobra | Dobra |
| **Skalowalność** | Średnia | Wysoka | Średnia |
| **Dokumentacja** | Doskonała | Dobra | Dobra |
| **Wsparcie ML/AI** | Doskonałe | Średnie | Średnie |
| **Rekomendacja** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## REKOMENDACJA: Gradio

**Dlaczego Gradio?**
1. Najszybsza migracja (podobna składnia do Streamlit)
2. Doskonałe wsparcie dla aplikacji ML/AI
3. Wbudowane komponenty dla uploadu, chat, interface
4. Automatyczne API
5. Łatwe wdrożenie i utrzymanie
6. Aktywna społeczność

**Kiedy wybrać FastAPI/Flask?**
- Jeśli potrzebujesz pełnej kontroli nad UI
- Jeśli planujesz rozbudowany frontend (React/Vue)
- Jeśli potrzebujesz bardzo wysokiej wydajności
- Jeśli chcesz REST API dla innych klientów

---

## Plan Działania (Gradio - REKOMENDOWANA)

### Faza 1: Przygotowanie (30 min)
1. Instalacja Gradio
2. Utworzenie `app/frontend_gradio.py`
3. Backup obecnego `app/app.py`

### Faza 2: Podstawowa struktura (1h)
1. Importy i konfiguracja
2. Funkcja autoryzacji
3. Podstawowy layout

### Faza 3: Upload plików (1h)
1. Komponent `gr.File`
2. Integracja z Flask endpoint (lub bezpośrednio)
3. Progress indicator

### Faza 4: Wyszukiwanie (1.5h)
1. Formularz wyszukiwania
2. Integracja z RAG system
3. Wyświetlanie wyników

### Faza 5: Dodatkowe funkcje (1h)
1. Historia zapytań
2. Zarządzanie plikami
3. Parametry modelu

### Faza 6: UI/UX (1h)
1. Custom CSS
2. Theme
3. Layout improvements

### Faza 7: Testy i optymalizacja (30 min)
1. Test wszystkich funkcjonalności
2. Fix błędów
3. Dokumentacja

---

## Decyzja

**Wybierz opcję:**
1. **Gradio** - szybka migracja, podobna do Streamlit
2. **FastAPI + HTML/JS** - pełna kontrola, REST API
3. **Flask + Jinja2** - prostsze, już używamy Flask

**Gotowy do implementacji!** 🚀

