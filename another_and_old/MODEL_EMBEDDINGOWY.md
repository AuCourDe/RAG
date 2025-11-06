# 📊 Model do embeddingów

## Aktualny model: `intfloat/multilingual-e5-large`

### Specyfikacja:

| Parametr | Wartość |
|----------|---------|
| **Nazwa** | intfloat/multilingual-e5-large |
| **Typ** | Sentence Transformer |
| **Wymiar wektora** | **1024** |
| **Max długość** | 512 tokenów (~500 znaków) |
| **Języki** | Multilingual (w tym **polski**) |
| **Urządzenie** | **GPU (CUDA)** |
| **Rozmiar modelu** | ~560 MB |

### Wydajność na RTX 3060:

```
✅ GPU: NVIDIA RTX 3060 12GB
✅ CUDA: 12.8
✅ Batch size: 32 fragmenty
✅ Czas: ~0.02 sekundy per fragment
✅ Throughput: ~50 fragmentów/sekundę
```

---

## 📈 Dlaczego właśnie ten model?

### 1. **Multilingual**
- Wspiera **100+ języków**, w tym polski
- Trenowany na multilingual data
- Najlepszy dla dokumentów po polsku

### 2. **Wysoka jakość**
- State-of-the-art dla zadań multilingual
- Doskonałe wyniki w podobieństwie semantycznym
- Ranking: Top 3 na MTEB Leaderboard (multilingual)

### 3. **Optymalny rozmiar**
- 1024 wymiary - świetny balans precision/performance
- Nie za duży (nie overfit), nie za mały (dobra precyzja)

### 4. **GPU-optimized**
- Pełne wsparcie dla CUDA
- Szybkie batch processing
- Efektywne wykorzystanie VRAM

---

## 🔄 Alternatywne modele

### Jeśli chcesz zmienić model:

| Model | Wymiary | Języki | Szybkość | Jakość |
|-------|---------|--------|----------|--------|
| **intfloat/multilingual-e5-large** (AKTUALNY) | 1024 | Multi | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| intfloat/multilingual-e5-base | 768 | Multi | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| intfloat/multilingual-e5-small | 384 | Multi | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| paraphrase-multilingual-mpnet-base-v2 | 768 | Multi | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| sdadas/mmlw-roberta-large | 1024 | PL/Multi | ⭐⭐⭐ | ⭐⭐⭐⭐ |

### Jak zmienić model:

W pliku `rag_system.py`, linia 439:
```python
self.model = SentenceTransformer('intfloat/multilingual-e5-large')
```

Zmień na np.:
```python
self.model = SentenceTransformer('intfloat/multilingual-e5-base')  # Szybszy
```

⚠️ **UWAGA:** Po zmianie modelu musisz przeindeksować wszystkie dokumenty!

---

## 🧮 Jak działa embedding?

### Proces:

```
Tekst → Tokenizacja → Model → Wektor 1024D
```

### Przykład:

```python
Tekst: "Kto popełnia przestępstwo podlega karze"
       ↓
Embedding: [0.020, -0.009, -0.009, -0.065, 0.017, ...]
           (1024 liczby zmiennoprzecinkowe)
```

### Co reprezentuje wektor?

- **Semantyczne znaczenie** tekstu
- Podobne teksty → podobne wektory
- Odległość między wektorami = podobieństwo semantyczne

### Wyszukiwanie:

```python
Zapytanie: "Jakie kary za kradzież?"
Embedding zapytania: [0.034, -0.012, ...]

Porównanie z bazą (3,483 wektory):
  Fragment 1: odległość 0.15 ← NAJBLIŻSZY! ✅
  Fragment 2: odległość 0.32
  Fragment 3: odległość 0.89
  ...
```

---

## 📊 Statystyki z Twojej bazy:

```
✅ Fragmentów: 3,483
✅ Embeddingów: 3,483 wektory × 1024 wymiary
✅ Rozmiar: ~14 MB (same embeddingi)
✅ Czas tworzenia: ~77 sekund (całość)
✅ Czas per fragment: ~0.022 sekundy
```

---

## 🔍 Jakość embeddingów

Model `multilingual-e5-large` jest wytrenowany na:

- **1 miliard** par (pytanie, odpowiedź)
- **100+ języków**
- Dane z Wikipedia, StackExchange, Reddit
- Fine-tuned na similarity tasks

**Wynik:** Doskonałe rozpoznawanie podobieństwa semantycznego w języku polskim! ✅
