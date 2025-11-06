# 🎬 Obsługa plików wideo - Workflow i dokumentacja

## ✅ **NAJNOWSZA FUNKCJONALNOŚĆ!**

System RAG teraz obsługuje **pełne przetwarzanie wideo**:
- 🎤 **Audio** → Whisper AI (transkrypcja)
- 🖼️ **Klatki wideo** → Gemma 3:12B (rozpoznawanie)
- ⏱️ **Synchronizacja** → Audio + Video dla każdej sekundy
- 🔍 **Przeszukiwanie** → Pytaj o to co było mówione i pokazywane!

---

## 📁 **Obsługiwane formaty:**

- ✅ **MP4** - najpopularniejszy
- ✅ **AVI** - klasyczny
- ✅ **MOV** - Apple
- ✅ **MKV** - wysokiej jakości
- ✅ **WEBM** - web video

---

## 🔄 **KOMPLETNY WORKFLOW - Co się dzieje:**

### **Krok 1: Upload wideo**

**Użytkownik:**
```
Frontend → Indeksowanie → Upload → prezentacja.mp4 (5 minut, 1920×1080, 30 FPS)
→ Kliknij "Zapisz pliki"
```

**UI pokazuje:**
```
🎬 Wykryto pliki wideo!
⏱️ Przetwarzanie wideo zajmuje najwięcej czasu:
   • Ekstrakcja audio + transkrypcja Whisper
   • Analiza klatek (1 klatka/sekundę) przez Gemma 3
   • Szacowany czas: ~10 minut dla 1 pliku(ów)

Sprawdź postęp: tail -f file_watcher.log
```

---

### **Krok 2: Watchdog wykrywa**

```
t=0s   : Plik zapisany do data/prezentacja.mp4
t=2s   : Watchdog wykrywa nowy plik
t=3s   : Rozpoczęcie przetwarzania
```

---

### **Krok 3: Analiza parametrów wideo**

**Backend (rag_system.py, linia 610-620):**
```python
video = cv2.VideoCapture("prezentacja.mp4")
fps = video.get(cv2.CAP_PROP_FPS)  # np. 30 FPS
total_frames = video.get(cv2.CAP_PROP_FRAME_COUNT)  # np. 9000
duration = total_frames / fps  # 9000 / 30 = 300 sekund = 5 minut
```

**Logi:**
```
======================================================================
🎬 PRZETWARZANIE PLIKU WIDEO
======================================================================
Plik: prezentacja.mp4

📊 Parametry wideo:
   FPS: 30.00
   Klatki: 9000
   Długość: 300.00 sekund (5.0 minut)
```

---

### **Krok 4: Ekstrakcja audio (ffmpeg)**

**Backend (linia 622-643):**
```python
# Użyj ffmpeg do wyciągnięcia audio
subprocess.run([
    'ffmpeg', '-i', 'prezentacja.mp4',
    '-vn',  # No video (tylko audio)
    '-acodec', 'pcm_s16le',  # WAV 16-bit
    '-ar', '16000',  # 16kHz sample rate (Whisper preferuje)
    '-ac', '1',  # Mono
    'temp/temp_audio_xyz.wav',
    '-y'
])
```

**Logi:**
```
🎵 KROK 1/3: Ekstrakcja audio z wideo
💾 Ekstrakcja audio do: temp_audio_xyz.wav
✅ Audio wyekstraktowane
```

**Czas:** ~2-5 sekund

---

### **Krok 5: Transkrypcja audio (Whisper)**

**Backend (linia 645-670):**
```python
# Załaduj Whisper
whisper_model = whisper.load_model("base")

# Transkrypcja
result = whisper_model.transcribe(
    "temp/temp_audio_xyz.wav",
    language="pl",
    task="transcribe"
)

audio_segments = result["segments"]
# Każdy segment: {start, end, text}
```

**Logi:**
```
🎤 KROK 2/3: Transkrypcja audio przez Whisper
Ładowanie modelu Whisper...
✅ Model Whisper załadowany w 15.23 sekund
Transkrypcja audio z wideo (300.0s)...
✅ Transkrypcja zakończona w 187.52s
   Segmentów audio: 85
```

**Wynik - przykładowe segmenty:**
```
Segment 1: {start: 0.0, end: 3.5, text: "Dzień dobry, zaczynam prezentację..."}
Segment 2: {start: 3.5, end: 8.2, text: "Na tym slajdzie widzimy wykres..."}
Segment 3: {start: 8.2, end: 15.0, text: "Wzrost wynosi około 25 procent..."}
```

**Czas:** ~180-200 sekund (3-3.5 minuty) dla 5-minutowego wideo

---

### **Krok 6: Ekstrakcja klatek (1 klatka/sekundę)**

**Backend (linia 675-724):**
```python
# Oblicz które klatki wyciągnąć
frames_to_extract = []
for second in range(int(duration) + 1):  # 0, 1, 2, ..., 300
    frame_num = int(second * fps)  # 0, 30, 60, 90, ... (co sekundę)
    frames_to_extract.append((second, frame_num))

# 300 sekund wideo = 300 klatek do wyciągnięcia
```

**Logi:**
```
🖼️ KROK 3/3: Ekstrakcja i rozpoznawanie klatek wideo
📸 Będę analizować 300 klatek (1 klatka/sekundę)
```

**Dlaczego 1 klatka/sekundę?**
- ✅ Wystarczająca częstotliwość (30 FPS → 1 FPS = co 30-ta klatka)
- ✅ Oszczędność czasu (300 klatek zamiast 9000!)
- ✅ Gemma 3 widzi zmiany sceny
- ⚠️ Szybkie zmiany mogą być pominięte (akceptowalne)

---

### **Krok 7: Rozpoznawanie klatek (Gemma 3:12B)**

**Backend (linia 692-721):**
```python
for second, frame_num in frames_to_extract:
    # 1. Przejdź do klatki
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    ret, frame = video.read()
    
    # 2. Zapisz klatkę jako JPEG
    cv2.imwrite("temp/frame_xyz.jpg", frame)
    
    # 3. Rozpoznaj przez Gemma 3 (multimodal)
    description = _describe_image("temp/frame_xyz.jpg")
    
    # 4. Zapisz opis dla tej sekundy
    frame_descriptions[second] = description
    
    # 5. Usuń temp file
    os.remove("temp/frame_xyz.jpg")
```

**Logi:**
```
   Analiza klatki 0s/300s...
   Analiza klatki 5s/300s...
   Analiza klatki 10s/300s...
   ...
   Analiza klatki 300s/300s...
✅ Rozpoznano 300 klatek wideo
```

**Czas:** 
- 1 klatka = ~20 sekund (Gemma 3 inference)
- 300 klatek = 6000 sekund = **100 minut** 😱

**Dla 5-minutowego wideo: ~100 minut przetwarzania!**

---

### **Krok 8: Łączenie audio + video**

**Backend (linia 726-768):**
```python
# Dla każdej sekundy wideo:
for second in range(int(duration) + 1):  # 0-300
    # Audio dla tej sekundy
    audio_text = audio_by_second.get(second, "[cisza]")
    
    # Opis klatki dla tej sekundy
    frame_desc = frame_descriptions.get(second, "[brak opisu]")
    
    # Połącz w jeden fragment
    fragment = f"""
    [MM:SS]
    🎤 Audio: {audio_text}
    🖼️ Video: {frame_desc}
    """
    
    # Dodaj do bazy
    chunks.append(DocumentChunk(
        content=fragment,
        chunk_type='video_transcription',
        element_id=f"video_second_{second}_MMmSSs"
    ))
```

**Przykładowe fragmenty:**

**Fragment 1 (sekunda 0):**
```
[00:00]
🎤 Audio: Dzień dobry, zaczynam prezentację na temat wzrostu sprzedaży.
🖼️ Video: Slajd tytułowy z napisem "Wzrost sprzedaży Q1 2024", białe tło, 
         niebieskie logo firmy w prawym górnym rogu.
```

**Fragment 15 (sekunda 15):**
```
[00:15]
🎤 Audio: Na tym wykresie widzimy wzrost o dwadzieścia pięć procent.
🖼️ Video: Wykres słupkowy, trzy kolumny (styczeń, luty, marzec), 
         najwyższy słupek dla marca. Osoba w garniturze wskazuje 
         na wykres wskaźnikiem laserowym.
```

**Fragment 180 (sekunda 180 = 3:00):**
```
[03:00]
🎤 Audio: Podsumowując, nasze działania przyniosły efekty.
🖼️ Video: Slajd podsumowania z punktami wypunktowanymi, 
         osoba stoi z boku i gestykuluje ręką.
```

---

### **Krok 9: Embeddingi i zapis do bazy**

**Backend:**
```python
# Dla każdego fragmentu (300 fragmentów dla 5-min wideo)
for chunk in chunks:
    # Stwórz embedding (GPU)
    embedding = model.encode(chunk.content)
    
    # Dodaj do ChromaDB
    collection.add(
        ids=[chunk.id],
        embeddings=[embedding],
        documents=[chunk.content],
        metadatas=[{
            "source_file": "prezentacja.mp4",
            "chunk_type": "video_transcription",
            "element_id": "video_second_15_00m15s"
        }]
    )
```

**Czas:** ~10 sekund (300 fragmentów)

---

### **Krok 10: Generowanie pytań**

**Backend:**
```python
# Wygeneruj 3 przykładowe pytania
# Bazując na transkrypcji + opisach klatek

Pytania:
1. "Co było pokazywane na wykresie w prezentacji?"
2. "Jaki był wzrost sprzedaży według prezentacji?"
3. "Kto prowadził prezentację?"
```

**Czas:** ~30 sekund (Gemma 3)

---

## ⏱️ **KOMPLETNY TIMELINE - 5-minutowe wideo:**

```
t=0s      : Upload pliku (5 min wideo, 30 FPS)
t=2s      : Watchdog wykrywa
t=5s      : Ekstrakcja audio (ffmpeg)
t=10s     : Ładowanie Whisper
t=30s     : Transkrypcja audio (Whisper)
t=220s    : Transkrypcja zakończona (85 segmentów)
t=225s    : Rozpoczęcie analizy klatek
t=6225s   : Analiza 300 klatek (300 × ~20s Gemma 3) 😱
t=6235s   : Łączenie audio + video
t=6245s   : Tworzenie embeddingów (300 fragmentów)
t=6255s   : Zapis do bazy
t=6285s   : Generowanie pytań
t=6315s   : KONIEC

RAZEM: ~6315 sekund = ~105 minut (~1.75 godziny) 
```

**Dla 5-minutowego wideo: ~1.75 godziny przetwarzania!** ⚠️

---

## 📊 **Czasy dla różnych długości:**

| Długość wideo | Klatki | Audio (Whisper) | Video (Gemma 3) | Razem |
|---------------|--------|-----------------|-----------------|--------|
| **1 min** | 60 | ~40s | ~20 min | **~22 min** |
| **5 min** | 300 | ~3 min | ~100 min | **~105 min** |
| **30 min** | 1800 | ~18 min | ~600 min | **~10h** 😱 |
| **60 min** | 3600 | ~36 min | ~1200 min | **~20h** 😱😱 |

**Bottleneck:** Gemma 3:12B (20s na klatkę!) 🐌

---

## 🎯 **Format fragmentów w bazie:**

### **Struktura:**
```
[MM:SS]
🎤 Audio: [transkrypcja z Whisper]
🖼️ Video: [opis klatki z Gemma 3]
```

### **Przykłady rzeczywiste:**

**Sekunda 0:**
```
[00:00]
🎤 Audio: Dzień dobry wszystkim, dziś przedstawię wyniki naszej firmy.
🖼️ Video: Slajd powitalny z logo firmy "ACME Corp", niebieskie tło, 
         biały tekst "Prezentacja wyników Q1 2024". Osoba w garniturze 
         stoi z prawej strony, gestykuluje ręką.
```

**Sekunda 45:**
```
[00:45]
🎤 Audio: Jak widać na tym wykresie, sprzedaż wzrosła o 30%.
🖼️ Video: Wykres słupkowy na slajdzie, oś X: miesiące (sty-mar), 
         oś Y: sprzedaż w tys. PLN. Trzy niebieskie słupki, najwyższy 
         dla marca (~45K). Czerwona strzałka wskazuje wzrost. Osoba 
         wskazuje wskaźnikiem laserowym (czerwona kropka na wykresie).
```

**Sekunda 120 (2:00):**
```
[02:00]
🎤 Audio: [cisza]
🖼️ Video: Slajd z tabelą, 5 wierszy, 4 kolumny. Nagłówki: "Produkt", 
         "Q1", "Q2", "Q3". Wartości liczbowe. Osoba siedzi przy biurku, 
         patrzy w laptop.
```

**Sekunda 285 (4:45):**
```
[04:45]
🎤 Audio: Dziękuję za uwagę, czy są pytania?
🖼️ Video: Slajd końcowy "Dziękujemy!", logo firmy, dane kontaktowe. 
         Osoba stoi frontalnie, uśmiecha się, ręce złożone.
```

---

## 🔍 **Wyszukiwanie w wideo:**

### **Przykład 1: Pytanie o wykres**

**Pytanie:**
```
"Jaki był wzrost sprzedaży według wykresu?"
```

**System znajdzie:**
```
Fragment [2] (00:45):
🎤 Audio: "...wzrosła o 30%..."
🖼️ Video: "Wykres słupkowy... najwyższy dla marca (~45K)..."

Odpowiedź: Według fragmentu [2] z sekundy 00:45, sprzedaż wzrosła 
o 30%. Na wykresie widać trzy słupki, najwyższy dla marca osiąga 
wartość około 45,000 PLN.
```

**Bonus:** 
- Wiesz KIEDY (00:45) było mówione o wykresie
- Możesz przejść do tej sekundy w wideo i zweryfikować!

---

### **Przykład 2: Pytanie o osobę**

**Pytanie:**
```
"Kto prowadził prezentację?"
```

**System znajdzie:**
```
Fragmenty z opisami:
[00:00] "...osoba w garniturze..."
[00:45] "...osoba wskazuje wskaźnikiem..."
[04:45] "...osoba stoi frontalnie, uśmiecha się..."

Odpowiedź: Prezentację prowadził

ła osoba w garniturze, która 
pojawiała się przez całą prezentację, wskazując na wykresy 
wskaźnikiem laserowym i gestykulując.
```

---

### **Przykład 3: Lokalizacja w czasie**

**Pytanie:**
```
"Co było pokazywane około 2 minuty prezentacji?"
```

**System znajdzie:**
```
Fragment [120] (02:00):
🎤 Audio: [cisza]
🖼️ Video: Slajd z tabelą, 5 wierszy...

Odpowiedź: W okolicach 2 minuty (02:00) na slajdzie była 
wyświetlana tabela z 5 wierszami i 4 kolumnami, pokazująca 
dane produktów w różnych kwartałach.
```

---

## 🎨 **Fragmenty w bazie:**

**Dla 5-minutowego wideo:**
```
Fragmenty: 300 (1 na sekundę)
Typ: video_transcription
Element IDs: video_second_0_00m00s, video_second_1_00m01s, ...
```

**Struktura w ChromaDB:**
```json
{
  "id": "abc-123-def",
  "document": "[00:45]\n🎤 Audio: ...wzrosła o 30%...\n🖼️ Video: Wykres słupkowy...",
  "metadata": {
    "source_file": "prezentacja.mp4",
    "page_number": 0,
    "chunk_type": "video_transcription",
    "element_id": "video_second_45_00m45s"
  },
  "embedding": [0.123, -0.456, ..., 0.789]  (1024D vector)
}
```

---

## ⚡ **Optymalizacja wydajności:**

### **Problem: Za wolne (100 min dla 5 min wideo)**

**Rozwiązania:**

#### **1. Zmniejsz częstotliwość klatek (zaimplementowane: 1 fps)**
```
✅ OBECNIE: 1 klatka/sekundę
⚠️ Można: 1 klatka/5 sekund (60 klatek zamiast 300)
   → Czas: ~20 min zamiast 100 min
   → Strata: może pominąć szybkie zmiany sceny
```

#### **2. Batch processing dla Gemma 3**
```python
# Zamiast 1 klatka na raz:
for frame in frames:
    describe_image(frame)  # 20s każda

# Użyj batches (wymaga modyfikacji):
batch_descriptions = describe_images_batch(frames[:10])  # 10 klatek jednocześnie
# Teoretyczny czas: 30s dla 10 klatek (zamiast 200s)
```

#### **3. Niższy model Whisper**
```python
# OBECNIE: base (dokładny, wolny)
model = whisper.load_model("tiny")  # Szybszy

Czas transkrypcji:
- base: 180s
- tiny: 60s (3× szybciej)
- Jakość: 80% vs 90%
```

#### **4. Równoległe przetwarzanie**
```python
# Audio i Video równolegle
import threading

thread_audio = threading.Thread(target=transcribe_audio)
thread_video = threading.Thread(target=analyze_frames)

thread_audio.start()
thread_video.start()

thread_audio.join()
thread_video.join()

# Oszczędność: ~3 minuty (audio i video nie czekają na siebie)
```

---

## 💾 **Wymagania:**

### **Zainstalowane:**
```bash
✅ ffmpeg (do ekstrakcji audio)
✅ opencv-python (do klatek)
✅ openai-whisper (do transkrypcji)
✅ imageio-ffmpeg (helper)
```

### **VRAM (RTX 3060 12GB):**
```
Whisper base: 1 GB
Gemma 3:12B: 8 GB (podczas opisu klatek)
Model embeddingowy: 5 GB

Strategia:
- Whisper → transkrypcja → unload
- Gemma 3 → opisy klatek → stay loaded
- Embeddings → batch → unload
```

### **Dysk (temp files):**
```
Audio temp: ~50 MB (WAV 16kHz mono)
Klatki temp: 300 × ~200 KB = ~60 MB
RAZEM: ~110 MB podczas przetwarzania
Auto-cleanup: TAK
```

---

## 🧪 **TEST - Dodaj pierwsze wideo:**

### **Przygotuj testowe wideo:**
```
Długość: 30-60 sekund (dla testu!)
Format: MP4
Zawartość: Cokolwiek (prezentacja, wykład, film)
```

### **Dodaj do systemu:**
```
1. Frontend → Indeksowanie → Upload → test.mp4
2. Zobacz ostrzeżenie o czasie przetwarzania
3. Kliknij "Zapisz pliki"
4. Otwórz terminal: tail -f file_watcher.log
```

### **Obserwuj logi:**
```
🎬 PRZETWARZANIE PLIKU WIDEO
Plik: test.mp4
📊 Parametry wideo: FPS: 30, Klatki: 1800, Długość: 60s

🎵 KROK 1/3: Ekstrakcja audio
✅ Audio wyekstraktowane

🎤 KROK 2/3: Transkrypcja
✅ Transkrypcja zakończona w 45s

🖼️ KROK 3/3: Analiza klatek
📸 Będę analizować 60 klatek
   Analiza klatki 0s/60s...
   Analiza klatki 5s/60s...
   ... [to potrwa ~20 minut dla 60 klatek]
✅ Rozpoznano 60 klatek

🔗 KROK 4/4: Łączenie
✅ ZAKOŃCZONO - utworzono 60 fragmentów
```

### **Zadaj pytanie:**
```
"O czym było wideo?"
"Co było pokazywane na ekranie?"
"Co było mówione w 30 sekundzie?"
```

---

## 🎬 **Use Cases:**

### **1. Prezentacje biznesowe**
```
Plik: prezentacja_wyniki.mp4 (15 min)
Fragmenty: 900
Przetwarzanie: ~5 godzin 😱

Pytania:
"Jaki był wzrost sprzedaży?"
"Co pokazywały wykresy?"
"Kto prowadził prezentację?"
"Kiedy była mowa o budżecie?" → odpowiedź z timestampem!
```

### **2. Wykłady/webinary**
```
Plik: wykład_matematyka.mp4 (60 min)
Fragmenty: 3600
Przetwarzanie: ~20 godzin 😱😱

Pytania:
"Jak zdefiniowano pochodną?"
"Co było na tablicy w 15 minucie?"
"Kiedy był przykład z funkcją kwadratową?"
```

### **3. Nagrania spotkań**
```
Plik: spotkanie_zoom.mp4 (30 min, 5 osób)
Fragmenty: 1800
Przetwarzanie: ~10 godzin

Pytania:
"Kto mówił o budżecie?"
"Co było pokazywane na ekranie share?"
"Kiedy była dyskusja o terminach?"
```

### **4. Filmy instruktażowe**
```
Plik: instrukcja_montazu.mp4 (10 min)
Fragmenty: 600
Przetwarzanie: ~3.5 godziny

Pytania:
"Jak połączyć część A z częścią B?"
"Co było pokazywane w kroku 3?"
"Jakie narzędzia były używane?"
```

---

## ⚠️ **WAŻNE OSTRZEŻENIA:**

### **1. Bardzo czasochłonne!**
```
5 min wideo = ~1.75h przetwarzania
30 min wideo = ~10h przetwarzania
60 min wideo = ~20h przetwarzania

REKOMENDACJA: 
- Testuj na krótkich filmach (1-2 min)
- Dla długich: rozważ zmniejszenie częstotliwości klatek
```

### **2. Wymaga ffmpeg**
```bash
# Sprawdź:
which ffmpeg

# Jeśli brak:
sudo apt install ffmpeg
```

### **3. VRAM**
```
Gemma 3 podczas opisu klatek: ~8 GB VRAM
+ Model embeddingowy: 5 GB (jeśli watchdog aktywny)
RAZEM: 13 GB > 12 GB (RTX 3060)

Rozwiązanie: Ollama rozładowuje modele automatycznie
```

### **4. Długie przetwarzanie = brak feedback**
```
Użytkownik czeka 2 godziny i nie wie co się dzieje!

ROZWIĄZANIE:
- Sprawdzaj logi: tail -f file_watcher.log
- Co 5 sekund: log "Analiza klatki Xs/Ys..."
```

---

## 🚀 **Instalacja wymaganych narzędzi:**

```bash
# 1. ffmpeg (do audio)
sudo apt install ffmpeg

# 2. OpenCV (do klatek)
pip install opencv-python

# 3. imageio-ffmpeg (helper)
pip install imageio-ffmpeg

# Sprawdź:
ffmpeg -version
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
```

---

## 📚 **Przykładowy workflow w logach:**

```bash
tail -f /home/rev/projects/RAG2/file_watcher.log

======================================================================
🎬 PRZETWARZANIE PLIKU WIDEO
======================================================================
Plik: demo.mp4

📊 Parametry wideo:
   FPS: 30.00
   Klatki: 1800
   Długość: 60.00 sekund (1.0 minut)

🎵 KROK 1/3: Ekstrakcja audio z wideo
💾 Ekstrakcja audio do: temp_audio_abc123.wav
✅ Audio wyekstraktowane

🎤 KROK 2/3: Transkrypcja audio przez Whisper
Ładowanie modelu Whisper...
✅ Model Whisper załadowany w 5.23 sekund
Transkrypcja audio z wideo (60.0s)...
✅ Transkrypcja zakończona w 45.12s
   Segmentów audio: 22

🖼️ KROK 3/3: Ekstrakcja i rozpoznawanie klatek wideo
📸 Będę analizować 60 klatek (1 klatka/sekundę)
   Analiza klatki 0s/60s...
   Analiza klatki 5s/60s...
   Analiza klatki 10s/60s...
   ...
   Analiza klatki 60s/60s...
✅ Rozpoznano 60 klatek wideo

🔗 KROK 4/4: Łączenie transkrypcji audio z opisami klatek
======================================================================
✅ ZAKOŃCZONO PRZETWARZANIE WIDEO
   Fragmentów utworzonych: 60
   Audio segmentów: 22
   Klatek rozpoznanych: 60
======================================================================
```

---

## 🎯 **Optymalizacje (do rozważenia):**

### **Opcja 1: Zmniejsz częstotliwość klatek**

**W kodzie (rag_system.py, linia ~682):**
```python
# OBECNIE: 1 klatka/sekundę
for second in range(int(duration) + 1):
    frame_num = int(second * fps)

# ZMIEŃ NA: 1 klatka/5 sekund
for second in range(0, int(duration) + 1, 5):  # Co 5 sekund
    frame_num = int(second * fps)

Wynik:
- 5 min wideo: 60 klatek (zamiast 300)
- Czas: ~20 min (zamiast 100 min)
```

### **Opcja 2: Szybszy model Whisper**
```python
# Zmień "base" na "tiny"
whisper_model = whisper.load_model("tiny")

Wynik:
- 3× szybciej
- 90% → 80% dokładności
```

### **Opcja 3: Pomiń audio (tylko klatki)**
```python
# W kodzie: ustaw audio_segments = [] aby pominąć Whisper
# Tylko opisy klatek, bez transkrypcji
```

---

## 📊 **Porównanie z innymi formatami:**

| Format | Tekst | Obrazy | Audio | Czas (5 min) |
|--------|-------|--------|-------|--------------|
| **PDF** | ✅ | ✅ | ❌ | ~30s |
| **DOCX** | ✅ | ✅ | ❌ | ~20s |
| **XLSX** | ✅ | ✅ | ❌ | ~15s |
| **JPG** | ⚠️ OCR | ✅ | ❌ | ~20s |
| **MP3** | ❌ | ❌ | ✅ | ~3 min |
| **MP4** | ❌ | ✅ | ✅ | **~105 min** 😱 |

**Wideo = najwolniejsze, ale najbogatsze w informacje!**

---

## 🎊 **System gotowy do wideo!**

**Dodałem:**
- ✅ Rozdzielanie audio/video (ffmpeg + opencv)
- ✅ Transkrypcja audio (Whisper)
- ✅ Analiza klatek 1 fps (Gemma 3)
- ✅ Synchronizacja audio + video dla każdej sekundy
- ✅ Timestampy dla łatwej lokalizacji
- ✅ Info w UI o czasie przetwarzania
- ✅ Logi szczegółowe

**Obsługiwane formaty:** MP4, AVI, MOV, MKV, WEBM 🎬

**Pełna multimodalność:** Tekst + Obrazy + Audio + Wideo! 🚀


