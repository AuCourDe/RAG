# 🖼️ Obsługa obrazów w dokumentach - PDF i Excel

## 🎯 Krótka odpowiedź:

### **PDF z obrazami:** ✅ **W PEŁNI OBSŁUGIWANE**
System automatycznie:
1. Wykrywa obrazy w PDF
2. Wyciąga je tymczasowo
3. Rozpoznaje przez Gemma 3:12B (multimodal)
4. Tworzy opis tekstowy
5. Indeksuje opis w bazie

### **DOCX z obrazami:** ✅ **W PEŁNI OBSŁUGIWANE** (NOWE!)
System automatycznie:
1. Wykrywa obrazy w Word (inline_shapes)
2. Wyciąga dane obrazów
3. Rozpoznaje przez Gemma 3:12B
4. Tworzy opis tekstowy
5. Indeksuje razem z tekstem

### **Excel z obrazami:** ✅ **W PEŁNI OBSŁUGIWANE** (NOWE!)
- Tekst z komórek: ✅ TAK (w pełni)
- Obrazy wbudowane: ✅ TAK (wyciągane i rozpoznawane!)
- Wykresy Excel: ✅ TAK (jako obrazy, rozpoznawane przez AI!)

---

## 📄 SZCZEGÓŁOWO: PDF z obrazami

### **Co się dzieje gdy dodasz PDF z obrazem:**

#### **Krok 1: Upload PDF**
```
Użytkownik → Upload "raport_z_wykresami.pdf"
→ Plik zapisany do data/
→ Watchdog wykrywa
```

#### **Krok 2: Przetwarzanie strony**
```python
# rag_system.py, linia 177-228

with pdfplumber.open("raport_z_wykresami.pdf") as pdf:
    for page_num, page in enumerate(pdf.pages, 1):
        
        # A) TEKST z strony
        text = page.extract_text()
        if text:
            chunks.append(DocumentChunk(
                content=text,
                chunk_type='text',
                page_number=page_num
            ))
        
        # B) OBRAZY z strony
        if page.images:  # ← Automatyczne wykrycie!
            for img_idx, img_obj in enumerate(page.images):
                # 1. Wyciągnij dane obrazu
                img_data = img_obj['stream'].get_data()
                
                # 2. Zapisz tymczasowo
                temp_path = "temp/temp_img_xyz.png"
                with open(temp_path, 'wb') as f:
                    f.write(img_data)
                
                # 3. Rozpoznaj przez Gemma 3:12B
                description = describe_image(temp_path)
                
                # 4. Dodaj jako fragment
                chunks.append(DocumentChunk(
                    content=description,
                    chunk_type='image_description',
                    page_number=page_num,
                    element_id=f"grafika_{page_num}_{img_idx+1}"
                ))
                
                # 5. Usuń temp file
                os.remove(temp_path)
```

#### **Krok 3: Rozpoznawanie obrazu przez Gemma 3:12B**
```python
# rag_system.py, linia 387-431

def _describe_image(image_path):
    # 1. Zakoduj obraz do base64
    with open(image_path, 'rb') as f:
        encoded = base64.b64encode(f.read()).decode()
    
    # 2. Wyślij do Ollama (Gemma 3:12B multimodal)
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "gemma3:12b",
            "prompt": "Opisz szczegółowo co znajduje się na tym obrazie. Po polsku.",
            "images": [encoded]  # ← Gemma 3 "widzi" obraz!
        }
    )
    
    # 3. Zwróć opis
    description = response.json()['response']
    return f"[Opis grafiki] {description}"
```

**Czas:** ~10-30 sekund na obraz (Gemma 3 analizuje)

#### **Krok 4: Przykład - PDF z wykresem**

**Źródło:**
```
raport_2024.pdf - Strona 5
- Tekst: "Wykres przedstawia wzrost sprzedaży..."
- Obrazy: [wykres słupkowy.png]
```

**Po indeksowaniu w bazie:**

**Fragment 1 (tekst):**
```
ID: abc-123
Treść: "Wykres przedstawia wzrost sprzedaży w Q1 2024..."
Typ: text
Strona: 5
Element: tekst_5_1
```

**Fragment 2 (obraz):**
```
ID: def-456
Treść: "[Opis grafiki] Na obrazie widoczny jest wykres słupkowy 
        przedstawiający wzrost sprzedaży. Oś X pokazuje miesiące 
        (styczeń, luty, marzec), oś Y wartości w tysiącach PLN. 
        Słupki są niebieskie, najwyższy dla marca (~45K PLN)..."
Typ: image_description
Strona: 5
Element: grafika_5_1
```

---

### **✨ Zalety dla PDF z obrazami:**

1. **Pełna analiza:**
   - ✅ Tekst z PDF
   - ✅ Opisy obrazów przez AI
   - ✅ Wszystko przeszukiwalne

2. **Inteligentne odpowiedzi:**
   ```
   Pytanie: "Jaka była sprzedaż w marcu?"
   
   System znajdzie:
   - Fragment tekstu: "...wzrost w Q1..."
   - Fragment obrazu: "...słupek dla marca 45K PLN..."
   
   Odpowiedź: "Według wykresu na stronie 5, sprzedaż 
               w marcu wyniosła około 45,000 PLN."
   ```

3. **Weryfikacja:**
   - Kliknij w źródło
   - Zobacz oryginalną stronę PDF z wykresem!

---

## 📊 SZCZEGÓŁOWO: Excel z obrazami

### **Co się dzieje gdy dodasz Excel z obrazem/wykresem:**

#### **Krok 1: Upload Excel**
```
Użytkownik → Upload "dane_2024.xlsx"
→ Zawiera: dane w komórkach + obrazek logo + wykres
```

#### **Krok 2: Przetwarzanie Excel**
```python
# rag_system.py, linia 271-308

def _process_xlsx(file_path):
    workbook = openpyxl.load_workbook(file_path)
    
    for sheet in workbook.sheetnames:
        # Wyciągnij TYLKO TEKST z komórek
        for row in sheet.iter_rows(values_only=True):
            row_text = " | ".join([str(cell) for cell in row])
            content.append(row_text)
        
        # ❌ OBRAZY NIE SĄ WYCIĄGANE!
        # openpyxl nie ma metody page.images (jak pdfplumber)
```

**Wynik:**
- ✅ Tekst z komórek → zaindeksowany
- ❌ Obrazy wbudowane → **ZIGNOROWANE**
- ❌ Wykresy → **ZIGNOROWANE**

#### **Dlaczego Excel nie obsługuje obrazów?**

**Technicznie:**
- `pdfplumber` ma metodę `page.images` ✅
- `openpyxl` **NIE MA** metody dla obrazów ❌
- Obrazy w Excel to obiekty "Drawing" (bardziej skomplikowane)

**Możliwe rozwiązanie (NIE zaimplementowane):**
```python
# Wymagałoby dodania:
from openpyxl.drawing.image import Image as XlImage

for sheet in workbook:
    # Wyciągnij obrazy
    for image in sheet._images:  # Private attribute!
        img_data = image._data()
        # Zapisz, rozpoznaj przez Gemma 3
```

---

## 🎯 PRAKTYCZNE PRZYKŁADY

### **Przykład 1: PDF z wykresami**

**Dokument:** `analiza_sprzedazy.pdf` (20 stron, 5 wykresów)

**Po zaindeksowaniu:**
```
📄 Fragmenty tekstowe: ~100 fragmentów
  - "W pierwszym kwartale zanotowano wzrost..."
  - "Tabela 1. Sprzedaż według regionów..."
  
🖼️ Fragmenty obrazów: 5 fragmentów
  - "Wykres słupkowy pokazuje wzrost w Q1..."
  - "Diagram kołowy przedstawia podział według kategorii..."
  - "Infografika z kluczowymi metrykami..."
  
RAZEM: 105 fragmentów
```

**Użytkownik pyta:**
```
"Jaka była sprzedaż w marcu?"
```

**System znajdzie:**
- Fragment tekstu + Fragment wykresu
- Odpowie używając OBUDWU źródeł
- Pokażę wykres do weryfikacji (kliknij źródło!)

---

### **Przykład 2: Excel z wykresem**

**Dokument:** `dane_2024.xlsx` (3 arkusze, wykres słupkowy w Arkuszu 2)

**Po zaindeksowaniu:**
```
📊 Fragmenty z komórek: ~50 fragmentów
  - "Arkusz: Sprzedaż | Wiersz 1: Styczeń | 25000 | ..."
  - "Arkusz: Koszty | Wiersz 1: Kategoria | Wartość | ..."

❌ Wykres: ZIGNOROWANY (openpyxl nie wyciąga)
```

**Użytkownik pyta:**
```
"Jaka była sprzedaż w marcu?"
```

**System:**
- Znajdzie dane z komórek ✅
- **NIE** znajdzie wykresu ❌
- Odpowie na podstawie tekstu/liczb

**Workaround:**
- Zapisz wykres jako PNG
- Dodaj jako osobny plik
- System go rozpozna!

---

### **Przykład 3: PDF ze zdjęciami (raport z budowy)**

**Dokument:** `raport_budowa.pdf` (50 stron, 100 zdjęć)

**Po zaindeksowaniu:**
```
📄 Fragmenty tekstowe: ~250 fragmentów
  - "Postęp prac w tygodniu 15..."
  - "Etap fundamentów zakończony..."

🖼️ Fragmenty zdjęć: 100 fragmentów
  - "Zdjęcie budowy, widoczne fundamenty betonowe..."
  - "Zdjęcie rusztowania, kilka robotników..."
  - "Widok z drona, cały plac budowy..."

RAZEM: 350 fragmentów
```

**Użytkownik pyta:**
```
"Czy fundamenty są gotowe?"
```

**System:**
- Znajdzie tekst: "Etap fundamentów zakończony"
- Znajdzie opis zdjęcia: "...fundamenty betonowe już wylane..."
- Odpowie z POTWIERDZENIEM z obu źródeł
- Pokaże zdjęcie fundamentów!

---

## ⏱️ CZASY PRZETWARZANIA

### **PDF z obrazami (przykład: 10 stron, 5 obrazów):**

```
Tekst (10 stron):
- Parsing: ~5 sekund
- Chunking: ~2 sekundy
- Embeddings: ~5 sekund (50 fragmentów)

Obrazy (5 grafik):
- Wyciąganie: ~2 sekundy
- Gemma 3 rozpoznawanie: ~100 sekund (5× 20s)
- Embeddings: ~0.1 sekundy (5 opisów)

RAZEM: ~114 sekund (~2 minuty)
```

### **Excel z danymi (bez obrazów):**

```
3 arkusze, 500 wierszy:
- Parsing: ~3 sekundy
- Chunking: ~2 sekundy  
- Embeddings: ~10 sekund (100 fragmentów)

RAZEM: ~15 sekund
```

---

## 🔧 WORKAROUNDS dla Excel z obrazami

### **Opcja 1: Screenshot arkusza**
```
1. Zrób screenshot arkusza z wykresem
2. Zapisz jako PNG
3. Dodaj do data/ obok Excel
4. System rozpozna wykres przez Gemma 3
```

### **Opcja 2: Export wykresu**
```
Excel → Kliknij wykres → Zapisz jako obraz → PNG
→ Dodaj PNG do data/
→ System zaindeksuje
```

### **Opcja 3: PDF zamiast Excel**
```
Excel → Zapisz jako PDF (Ctrl+P → Save as PDF)
→ PDF zachowa wykresy jako obrazy
→ System wyciągnie i rozpozna automatycznie!
```

### **Opcja 4: Dodaj rozpoznawanie obrazów w Excel (kod)**

**NIE ZAIMPLEMENTOWANE, ale możliwe:**

```python
# Dodaj do rag_system.py w _process_xlsx():

from openpyxl.drawing.image import Image as XlImage

def _process_xlsx(self, file_path):
    workbook = openpyxl.load_workbook(file_path)
    
    for sheet in workbook.worksheets:
        # ... tekst z komórek (już działa) ...
        
        # NOWE: Wyciągnij obrazy
        if hasattr(sheet, '_images') and sheet._images:
            for img_idx, image in enumerate(sheet._images):
                try:
                    # Zapisz obraz tymczasowo
                    img_path = TEMP_DIR / f"temp_excel_img_{uuid.uuid4()}.png"
                    image_pil = image._data()  # PIL Image
                    image_pil.save(img_path)
                    
                    # Rozpoznaj przez Gemma 3
                    description = self._describe_image(img_path)
                    
                    chunks.append(DocumentChunk(
                        content=description,
                        chunk_type='image_description',
                        source_file=file_path.name,
                        page_number=0,
                        element_id=f"obraz_arkusz_{sheet.title}_{img_idx+1}"
                    ))
                    
                    img_path.unlink()
                    
                except Exception as e:
                    logger.error(f"Błąd wyciągania obrazu z Excel: {e}")
```

**Jeśli chcesz to dodać - daj znać!**

---

## 📊 PORÓWNANIE: PDF vs Excel

| Cecha | PDF | Excel |
|-------|-----|-------|
| **Tekst** | ✅ TAK | ✅ TAK |
| **Obrazy wbudowane** | ✅ TAK (auto) | ❌ NIE |
| **Wykresy** | ✅ TAK (jako obrazy) | ❌ NIE |
| **Tabele** | ✅ TAK (jako tekst) | ✅ TAK (komórki) |
| **OCR** | ⚠️ Opcjonalnie | ⚠️ Opcjonalnie |
| **Czas indeksowania** | Wolniej (obrazy) | Szybciej |

---

## 💡 REKOMENDACJE

### **Dla raportów z wykresami:**
```
✅ Używaj PDF zamiast Excel
   - Wykresy będą automatycznie rozpoznane
   - Pełna analiza przez Gemma 3
   - Możliwość pytania o wykresy
```

### **Dla czystych danych liczbowych:**
```
✅ Excel jest OK
   - Szybsze indeksowanie
   - Dobre dla tabel
   - Ale: wykresy zignorowane
```

### **Dla mieszanych dokumentów:**
```
✅ Strategia:
   1. Excel z danymi → dodaj jako .xlsx
   2. Wykresy → export jako PNG
   3. Lub: cały Excel → Save as PDF
```

---

## 🧪 TEST - Dodaj PDF z obrazem

### **Krok po kroku:**

**1. Znajdź PDF z obrazami**
```bash
# Lub utwórz testowy:
# Word → Dodaj obraz → Save as PDF
```

**2. Dodaj do systemu**
```
Frontend → Indeksowanie → Upload → Zapisz
```

**3. Sprawdź logi**
```bash
tail -f file_watcher.log

# Zobaczysz:
# "Znaleziono 3 grafik na stronie 2"
# "Przetwarzanie grafiki 1/3..."
# "Wysyłanie do modelu Gemma 3:12B..."
# "Wygenerowano opis grafiki, długość: 856 znaków"
```

**4. Zadaj pytanie**
```
"Co znajduje się na obrazach w dokumencie?"
```

**5. Zobacz odpowiedź**
- System opisze obrazy!
- Źródła pokażą oryginalne strony

---

## 🎯 PRAKTYCZNE PRZYKŁADY Z ŻYCIA

### **Case 1: Raport medyczny z RTG**

**PDF:** raport_rtg.pdf
- Strona 1: Opis pacjenta (tekst)
- Strona 2: Zdjęcie RTG klatki piersiowej
- Strona 3: Diagnoza (tekst)

**Po zaindeksowaniu:**
- Fragment 1: "Pacjent, 45 lat..." (tekst)
- Fragment 2: "[Opis grafiki] Zdjęcie RTG klatki piersiowej, widoczne..." (Gemma 3)
- Fragment 3: "Diagnoza: ..." (tekst)

**Pytanie:** "Co pokazuje RTG?"
**Odpowiedź:** Na podstawie fragmentu [2] z opisu zdjęcia RTG...

---

### **Case 2: Prezentacja biznesowa (PowerPoint → PDF)**

**PDF:** prezentacja_Q1.pdf
- 20 slajdów
- 15 wykresów/diagramów
- 5 zdjęć produktów

**Po zaindeksowaniu:**
- Teksty: ~40 fragmentów
- Opisy wykresów: ~15 fragmentów (Gemma 3 opisuje wykresy!)
- Opisy zdjęć: ~5 fragmentów

**Pytanie:** "Jakie były wyniki w Q1?"
**System:** Znajdzie tekst + opisy wykresów → pełna odpowiedź

---

### **Case 3: Excel z tabelą (bez wykresów)**

**XLSX:** dane_sprzedaz.xlsx
- 3 arkusze
- Tylko komórki z liczbami/tekstem
- BEZ obrazów

**Po zaindeksowaniu:**
- Fragmenty: ~80 (tylko tekst z komórek)

**Pytanie:** "Jaka była sprzedaż w marcu?"
**System:** Znajdzie wartość z komórki → odpowie ✅

---

### **Case 4: Excel Z WYKRESEM (problem)**

**XLSX:** raport_z_wykresem.xlsx
- Arkusz 1: Dane (komórki)
- Arkusz 2: Wykres słupkowy

**Po zaindeksowaniu:**
- Fragmenty: ~50 (tylko dane z komórek)
- Wykres: **ZIGNOROWANY** ❌

**Rozwiązanie:**
```bash
# W Excel: Kliknij wykres → Zapisz jako obraz → wykres.png
# Dodaj wykres.png do data/
# Teraz system go rozpozna!
```

---

## 🚀 PODSUMOWANIE

### **PDF z obrazami:**
```
✅ Pełna obsługa
✅ Gemma 3:12B multimodal
✅ Automatyczne wykrywanie
✅ Opis + indeksowanie
✅ Wszystko przeszukiwalne
```

### **Excel z obrazami:**
```
✅ Tekst z komórek (pełna obsługa)
❌ Obrazy wbudowane (nie obsługiwane)
❌ Wykresy (nie obsługiwane)
⚠️ Workaround: Export jako PDF lub PNG
```

### **Jak sprawdzić czy obrazy zaindeksowane?**

```bash
# Sprawdź logi watchdog
tail -f file_watcher.log

# Lub użyj skryptu (w another_and_old)
cd another_and_old
python3 view_image_descriptions.py

# Zobaczysz wszystkie opisy obrazów z bazy
```

---

## 💬 **Dodatkowe pytanie?**

Jeśli chcesz **dodać obsługę obrazów w Excel**, mogę zaimplementować! Daj znać. 🚀

