# 📚 Co to są "fragmenty" w bazie RAG?

## 🎯 Definicja

**Fragment** (ang. *chunk*) = mały kawałek dokumentu przechowywany w bazie wektorowej

---

## 🖼️ **Obrazy: 2-4 fragmenty**

### Przykład: `image (1).jpeg` → **3 fragmenty**

**Fragment 1:**
```
[Opis grafiki] Oto szczegółowy opis tego, co widnieje na obrazie:

**Główny obiekt:**
- Centralnym punktem obrazu jest duży, afrykański słoniątko.
- Słoń stoi frontalnie do widza...
- Widać jego grube nogi, masywne ciało...

(1203 znaki)
```

**Fragment 2:**
```
[Opis grafiki] Oto szczegółowy opis obrazu:

**Centralny obiekt:**
- Na pierwszym planie widać ogromnego słonia afrykańskiego...
- Widać jego masywną sylwetkę, głowę, trąbę...

(848 znaków)
```

**Fragment 3:**
```
[Opis grafiki] Na zdjęciu widoczny jest ogromny słoń...

**Szczegółowy opis:**
- Skóra słonia jest szara i pokryta zmarszczkami...
- Tło: Słoń stoi na czerwonej powierzchni...

(1029 znaków)
```

### Dlaczego 3 fragmenty dla jednego obrazu?

- ✅ Gemma 3:12B generuje **kilka opisów** tego samego obrazu
- ✅ Z różnych perspektyw (ogólny widok, szczegóły, tło, kompozycja)
- ✅ Im więcej opisów → lepsze wyszukiwanie
- ✅ System znajduje najbardziej pasujący opis do pytania

---

## 📄 **PDF: setki-tysiące fragmentów**

### Przykład: `dokument1 (2).pdf` → **1251 fragmentów**

**Fragment 1087 (strona 206):**
```
Uprawnienie powyższe nie przysługuje małżonkowi, jeżeli wspólne 
pożycie małżonków ustało za życia spadkodawcy.

Art. 940. § 1. Małżonek jest wyłączony od dziedziczenia, jeżeli 
spadkodawca wystąpił o orzeczenie rozwodu...

(279 znaków)
```

**Fragment 1088 (strona 206):**
```
Wyłączenie małżonka od dziedziczenia następuje na mocy orzeczenia 
sądu. Wyłączenia może żądać każdy z pozostałych spadkobierców...

(456 znaków)
```

**Fragment 1089 (strona 206):**
```
Rozrządzić majątkiem na wypadek śmierci można jedynie przez 
testament. Art. 942. Testament może zawierać rozrządzenia...

(156 znaków)
```

### Dlaczego 1251 fragmentów dla jednego PDF?

- ✅ Dokument ma **236 stron**
- ✅ Każda strona podzielona na **~5-6 fragmentów**
- ✅ Każdy fragment to **150-500 znaków** (1-2 akapity)
- ✅ **236 stron × 5 fragmentów = ~1180 fragmentów** + nagłówki, artykuły

---

## 🔍 **Jak system używa fragmentów?**

### Przykład 1: Pytanie o obrazy

**Pytanie:** "Co znajduje się na obrazach słoni?"

**Proces:**
1. System tworzy embedding pytania
2. Przeszukuje wszystkie **3,483 fragmenty** w bazie
3. Znajduje **3 najbardziej podobne**:
   ```
   Fragment #124 (0.23 similarity): "...słoń afrykański..." 
                                     z image (1).jpeg
   Fragment #125 (0.25 similarity): "...masywne ciało słonia..." 
                                     z image (1).jpeg
   Fragment #126 (0.28 similarity): "...słoń w sawannie..." 
                                     z image (1).jpeg
   ```
4. Używa tych 3 fragmentów do odpowiedzi

### Przykład 2: Pytanie o dokument prawny

**Pytanie:** "Jakie są kary za kradzież?"

**Proces:**
1. Embedding pytania
2. Przeszukuje **1251 fragmentów** z Kodeksu Karnego
3. Znajduje najbardziej pasujące:
   ```
   Fragment #456 (strona 42): "Art. 278. § 1. Kto zabiera w celu..."
   Fragment #457 (strona 42): "...kara pozbawienia wolności..."
   Fragment #458 (strona 43): "...kradzież z włamaniem..."
   ```
4. Generuje odpowiedź TYLKO z tych fragmentów

---

## 📊 **Statystyki z Twojej bazy:**

| Typ pliku | Liczba plików | Fragmenty na plik | Łącznie |
|-----------|---------------|-------------------|---------|
| **Obrazy** | 8 | 2-4 | ~23 |
| **PDF** | 3 | 746-1479 | ~3,476 |
| **SUMA** | 11 | - | **3,499** |

---

## 💡 **Dlaczego podział na fragmenty?**

### 1. **Lepsze wyszukiwanie**
```
✅ Małe fragmenty = precyzyjne dopasowanie
❌ Cały dokument = za ogólne
```

### 2. **Szybkość**
```
✅ Embedding małego fragmentu: ~0.02s
❌ Embedding całej strony: ~0.5s
```

### 3. **Jakość odpowiedzi**
```
✅ Model dostaje konkretny kontekst
❌ Model dostaje za dużo informacji naraz
```

### 4. **Limity modelu**
```
✅ Gemma 3:12B: max ~4000 tokenów kontekstu
❌ Cały dokument (236 stron): ~200,000 tokenów
```

---

## 🎯 **Optymalne rozmiary fragmentów:**

### **Obrazy:**
- 1-4 opisy na obraz
- ~500-1500 znaków na opis
- Wystarczy do pełnego opisu

### **PDF:**
- ~200-500 znaków na fragment
- 1-2 akapity tekstu
- Zachowuje kontekst

---

## 🔧 **Jak zobaczyć fragmenty konkretnego pliku:**

```bash
cd /home/rev/projects/RAG2
python3 view_file_chunks.py "NAZWA_PLIKU"
```

**Przykłady:**
```bash
python3 view_file_chunks.py "image (1).jpeg"
python3 view_file_chunks.py "dokument1 (2).pdf"
python3 view_file_chunks.py "Supported_GPU_List.png"
```

---

## 📈 **Przykład z życia:**

### Użytkownik pyta: "Jakie są zasady dziedziczenia?"

**System:**
1. Znajduje 3 najbardziej pasujące fragmenty:
   - Fragment #1087 (strona 206): art. o małżonku
   - Fragment #1095 (strona 207): art. o testamentach
   - Fragment #1100 (strona 208): art. o formie testamentu

2. Generuje odpowiedź używając TYLKO tych 3 fragmentów

3. Pokazuje źródła z numerami stron - możesz kliknąć i zweryfikować!

---

## ✨ **Podsumowanie:**

**Fragmenty to klucz do działania RAG:**
- 🔍 Precyzyjne wyszukiwanie
- ⚡ Szybkie przetwarzanie
- 🎯 Trafne odpowiedzi
- 📚 Weryfikowalne źródła

**Więcej fragmentów = lepsza jakość odpowiedzi!**

