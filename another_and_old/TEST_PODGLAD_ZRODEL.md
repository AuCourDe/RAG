# 🧪 Test Podglądu Źródeł - Demo

## 🎯 Jak przetestować nową funkcjonalność

### Krok po kroku:

---

## 1️⃣ Uruchom aplikację

```bash
cd /home/rev/projects/RAG2
./start_all.sh
```

Otwórz przeglądarkę: **http://localhost:8501**

---

## 2️⃣ Zaloguj się

```
Login: admin
Hasło: admin123
```

---

## 3️⃣ TEST #1: Pytanie o obrazy

### Wpisz pytanie:
```
Co znajduje się na obrazach słoni?
```

### Oczekiwany rezultat:
1. ✅ System wygeneruje odpowiedź opisującą słonie
2. ✅ Pod odpowiedzią pojawi się sekcja "📚 Źródła (kliknij aby zobaczyć)"
3. ✅ Zobaczysz coś w stylu:
   ```
   📄 [1] image (1).jpeg - Strona 0
   📄 [2] image (1).jpeg - Strona 0
   ```

### Kliknij w pierwsze źródło:
- ✅ Rozwinie się panel
- ✅ Zobaczysz **opis tekstowy** wygenerowany przez Gemma 3
- ✅ Pod spodem zobaczysz **pełny obraz słonia** w wysokiej jakości

### Co powinieneś zobaczyć:
- Duży, wyraźny obraz słonia afrykańskiego
- Możliwość scrollowania jeśli obraz jest duży
- Obraz zajmuje pełną szerokość kontenera

---

## 4️⃣ TEST #2: Pytanie o dokumenty PDF

### Wpisz pytanie:
```
Jakie są kary za przestępstwo kradzieży?
```

### Oczekiwany rezultat:
1. ✅ System wygeneruje odpowiedź z Kodeksu Karnego
2. ✅ Zobaczysz źródła:
   ```
   📄 [1] dokument1 (2).pdf - Strona 45
   📄 [2] dokument1 (3).pdf - Strona 67
   ```

### Kliknij w pierwsze źródło:
- ✅ Rozwinie się panel
- ✅ Zobaczysz **fragment tekstu** z dokumentu
- ✅ Zobaczysz przycisk **"⬇️ Pobierz pełny PDF"**
- ✅ Pod spodem zobaczysz **renderowaną stronę 45** jako obraz

### Co powinieneś zobaczyć:
- Czytelny obraz strony PDF (zoom 2x)
- Możesz przeczytać cały kontekst strony
- Przycisk do pobrania pełnego PDF

---

## 5️⃣ TEST #3: Porównywanie źródeł

### Wpisz pytanie:
```
Pokaż wszystkie dostępne informacje
```

### Kliknij w kilka źródeł na raz:
- ✅ Możesz otworzyć wszystkie expandery jednocześnie
- ✅ Porównaj różne źródła obok siebie
- ✅ Zobacz zarówno obrazy jak i PDF

---

## 6️⃣ TEST #4: Obrazy techniczne

### Wpisz pytanie:
```
Jakie karty graficzne NVIDIA są obsługiwane?
```

### Oczekiwany rezultat:
1. ✅ System znajdzie obraz `Supported_GPU_List.png`
2. ✅ Kliknij w źródło
3. ✅ Zobaczysz **infografikę z listą kart NVIDIA**
4. ✅ Obraz będzie czytelny i wyraźny

---

## 7️⃣ TEST #5: Plany architektoniczne

### Wpisz pytanie:
```
Opisz plany domów
```

### Oczekiwany rezultat:
1. ✅ System znajdzie plany architektoniczne
2. ✅ Kliknij w źródło
3. ✅ Zobaczysz **plan domu z wymiarami**
4. ✅ Możesz przeczytać wymiary i nazwy pomieszczeń

---

## 8️⃣ TEST #6: Pobieranie PDF

### W dowolnym źródle PDF:
1. ✅ Kliknij przycisk **"⬇️ Pobierz pełny PDF"**
2. ✅ Plik zostanie pobrany do przeglądarki
3. ✅ Otwórz go i sprawdź czy to prawidłowy plik

---

## ✅ Checklist funkcjonalności

Po wykonaniu wszystkich testów sprawdź:

### Obrazy:
- [ ] Obrazy wyświetlają się w pełnej rozdzielczości
- [ ] Proporcje są zachowane
- [ ] Kolory są prawidłowe
- [ ] Możesz scrollować duże obrazy
- [ ] Opisz tekstowy jest widoczny

### PDF:
- [ ] Strony renderują się jako obrazy
- [ ] Tekst na stronie jest czytelny
- [ ] Przycisk pobierania działa
- [ ] Pobrany PDF otwiera się prawidłowo
- [ ] Numer strony jest prawidłowy

### Interface:
- [ ] Expandery otwierają się i zamykają
- [ ] Można otworzyć kilka na raz
- [ ] Scrollowanie działa płynnie
- [ ] Nie ma błędów w konsoli
- [ ] Wszystko ładuje się szybko

---

## 🐛 Możliwe problemy i rozwiązania

### Problem 1: "Zainstaluj PyMuPDF"
**Rozwiązanie:**
```bash
python3 -m pip install --break-system-packages PyMuPDF
```

### Problem 2: Obraz się nie ładuje
**Sprawdź:**
```bash
ls -la data/image\ \(1\).jpeg
```
Plik musi istnieć w folderze `data/`

### Problem 3: PDF nie renderuje się
**Sprawdź:**
```python
python3 -c "import fitz; print('OK')"
```
Jeśli błąd - przeinstaluj PyMuPDF

### Problem 4: Aplikacja się zawiesza
**Restart:**
```bash
pkill -f streamlit
./start_all.sh
```

---

## 📊 Przykładowe czasy ładowania

Na RTX 3060 12GB:

| Operacja | Czas |
|----------|------|
| Wygenerowanie odpowiedzi | ~30-60s |
| Renderowanie strony PDF | ~1-2s |
| Ładowanie obrazu | <1s |
| Otwieranie expandera | <0.1s |

---

## 🎓 Porady dla użytkowników

### 1. Weryfikuj odpowiedzi
Zawsze klikaj w źródła aby sprawdzić kontekst użytego fragmentu.

### 2. Pobieraj PDF dla większego kontekstu
Jeśli fragment nie wystarcza, pobierz pełny PDF.

### 3. Porównuj źródła
Otwórz kilka expanderów aby zobaczyć różne fragmenty na ten sam temat.

### 4. Zoomuj obrazy
Użyj Ctrl+Scroll aby powiększyć szczegóły na obrazach.

---

## 🎉 Gotowe!

Teraz masz pełną transparentność źródeł w systemie RAG!

**Sprawdź też:**
- `PODGLAD_ZRODEL.md` - pełna dokumentacja
- `README.md` - ogólne informacje o systemie
- `DEPLOY_INTERNET.md` - jak wystawić na internet

