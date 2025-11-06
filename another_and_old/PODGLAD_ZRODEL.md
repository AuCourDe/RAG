# 📚 Podgląd Źródeł w Streamlit - Instrukcja

## 🎯 Nowa funkcjonalność

Od teraz w interfejsie Streamlit możesz **klikać w źródła** i natychmiast zobaczyć:
- 🖼️ **Obrazy** - pełny podgląd
- 📄 **Strony PDF** - renderowana konkretna strona jako obraz wysokiej jakości

---

## 🚀 Jak używać?

### Krok 1: Zadaj pytanie
```
Wpisz pytanie w interfejsie Streamlit, np:
"Co jest na obrazach słoni?"
"Jakie są kary za kradzież?"
```

### Krok 2: Zobacz odpowiedź
System wygeneruje odpowiedź na podstawie dokumentów.

### Krok 3: Kliknij w źródło
Pod odpowiedzią zobaczysz sekcję **"📚 Źródła (kliknij aby zobaczyć)"**

Każde źródło to **kliknialny expander** w formacie:
```
📄 [1] image (1).jpg - Strona 0
📄 [2] dokument1 (2).pdf - Strona 45
📄 [3] image (2).jpg - Strona 0
```

### Krok 4: Zobacz szczegóły
Po kliknięciu rozwinie się panel ze szczegółami:

#### Dla OBRAZÓW (jpg, jpeg, png, bmp):
- ✅ Fragment tekstu (opis wygenerowany przez Gemma 3)
- ✅ **Pełny podgląd obrazu** (wysokiej jakości)

#### Dla PDF:
- ✅ Fragment tekstu z dokumentu
- ✅ **Przycisk "⬇️ Pobierz pełny PDF"** - pobierz cały dokument
- ✅ **Podgląd konkretnej strony** - renderowana jako obraz (zoom 2x)

---

## 📸 Przykład użycia

### Pytanie o obrazy:
```
Pytanie: "Opisz zdjęcia słoni"
```

**Odpowiedź:**
- System wygeneruje opis na podstawie opisów Gemma 3
- Pokaże źródła: `image (1).jpeg - Strona 0`

**Kliknij źródło:**
- Zobaczysz:
  - Fragment: "Oto szczegółowy opis obrazu: Centralnym punktem obrazu jest duży, afrykański słoniątko..."
  - **Pełny obraz słonia** (wysokiej jakości)

### Pytanie o PDF:
```
Pytanie: "Jakie są zasady odpowiedzialności karnej?"
```

**Odpowiedź:**
- System wygeneruje odpowiedź z Kodeksu Karnego
- Pokaże źródła: `dokument1 (2).pdf - Strona 23`

**Kliknij źródło:**
- Zobaczysz:
  - Fragment tekstu z strony 23
  - Przycisk do pobrania pełnego PDF
  - **Renderowaną stronę 23** jako obraz (możesz przeczytać cały kontekst)

---

## 🎨 Zalety

### ✅ Weryfikacja źródeł
- Nie musisz wierzyć na słowo - zobacz źródło
- Sprawdź kontekst fragmentu użytego w odpowiedzi

### ✅ Wszystko w jednym miejscu
- Nie trzeba otwierać plików osobno
- Wszystko działa w przeglądarce
- Szybki dostęp do weryfikacji

### ✅ Wysoka jakość
- Obrazy w pełnej rozdzielczości
- Strony PDF renderowane z zoom 2x (czytelne)
- Przycisk do pobrania jeśli potrzebujesz więcej

---

## 🔧 Techniczne szczegóły

### Użyte technologie:
- **Streamlit** - interfejs użytkownika
- **PyMuPDF (fitz)** - renderowanie stron PDF do obrazów
- **Pillow** - wyświetlanie obrazów

### Renderowanie PDF:
```python
# PyMuPDF renderuje stronę z zoom 2x dla lepszej jakości
page = doc[page_number - 1]
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
img_bytes = pix.tobytes("png")
st.image(img_bytes)
```

### Obrazy:
```python
# Bezpośrednie wyświetlanie z pliku
st.image("data/image.jpg", use_container_width=True)
```

---

## 🐛 Rozwiązywanie problemów

### Nie widzę podglądu PDF
**Problem:** Komunikat "Zainstaluj PyMuPDF"

**Rozwiązanie:**
```bash
python3 -m pip install --break-system-packages PyMuPDF
```

### Plik nie istnieje
**Problem:** "⚠️ Plik nie istnieje"

**Przyczyny:**
1. Plik został usunięty z folderu `data/`
2. Baza wektorowa jest nieaktualna

**Rozwiązanie:**
- Zreindeksuj bazę: zakładka "Indeksowanie" → "Reindeksuj wszystko"
- Lub umieść plik z powrotem w `data/`

### Obraz się nie ładuje
**Problem:** Pusty podgląd obrazu

**Rozwiązanie:**
1. Sprawdź czy plik jest w `data/`
2. Sprawdź format pliku (obsługiwane: jpg, jpeg, png, bmp)
3. Sprawdź uprawnienia do pliku: `ls -la data/`

---

## 💡 Tips & Tricks

### 1. Porównywanie źródeł
Otwórz kilka expanderów na raz aby porównać różne źródła:
- System zwraca 3-5 najbardziej pasujących fragmentów
- Możesz zobaczyć wszystkie naraz

### 2. Pobieranie PDF
Użyj przycisku "Pobierz pełny PDF" jeśli:
- Chcesz przeczytać więcej kontekstu
- Potrzebujesz cytować dokument
- Chcesz zapisać na dysku

### 3. Zoom w przeglądarce
Możesz dodatkowo zoomować obrazy w przeglądarce:
- **Ctrl + Scroll** (mysz)
- **Ctrl + Plus/Minus** (klawiatura)
- Kliknij prawym → "Otwórz obraz w nowej karcie"

---

## 🎯 Przykłady pytań z weryfikacją

### Pytania o obrazy:
```
"Co znajduje się na obrazach?"
"Opisz zdjęcia zwierząt"
"Jakie mamy plany architektoniczne?"
```
→ Kliknij źródło aby zobaczyć oryginalny obraz

### Pytania o dokumenty prawne:
```
"Jakie są kary za kradzież?"
"Co grozi za włamanie?"
"Zasady odpowiedzialności karnej"
```
→ Kliknij źródło aby zobaczyć stronę z Kodeksu Karnego

### Pytania o dane mieszane:
```
"Pokaż wszystkie dostępne informacje"
"Co zawiera baza dokumentów?"
```
→ Zobaczysz zarówno obrazy jak i fragmenty PDF

---

## 📊 Statystyki

W obecnej bazie masz:
- **12 obrazów** z opisami Gemma 3
- **~3,476 fragmentów tekstowych** z PDF
- **Wszystko dostępne do podglądu** w jednym kliknięciu

---

## 🔒 Prywatność

### Co jest przechowywane?
- Oryginalne pliki w folderze `data/`
- Opisy obrazów w bazie wektorowej
- Fragmenty tekstów z PDF w bazie wektorowej

### Co NIE jest wysyłane na zewnątrz?
- ✅ Wszystko działa lokalnie
- ✅ Pliki są wyświetlane z dysku
- ✅ Żadne dane nie są wysyłane do internetu (poza Ollama lokalnie)

---

## 🚀 Następne kroki

Po wdrożeniu tej funkcji możesz:
1. ✅ Weryfikować każdą odpowiedź systemu
2. ✅ Sprawdzać kontekst użytych fragmentów
3. ✅ Pobierać dokumenty źródłowe
4. ✅ Przeglądać obrazy w pełnej jakości

**System RAG teraz z pełną transparentnością źródeł!** 🎉

