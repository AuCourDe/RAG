# 🛡️ BEZPIECZNA ARCHITEKTURA RAG

## 🔐 Rozwiązanie: Separacja embeddingów i tekstów

### Tradycyjne RAG (NIEBEZPIECZNE):
```
┌─────────────────────────────────────┐
│      BAZA WEKTOROWA (WSZYSTKO)      │
│  ┌───────────────────────────────┐  │
│  │  • Embeddingi (wektory)       │  │
│  │  • Teksty (PEŁNA TREŚĆ!)      │──┼──► Model zewnętrzny
│  │  • Metadane (nazwy plików)    │  │   ❌ Widzi wszystko!
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Bezpieczne RAG (ZALECANE):
```
┌──────────────────────────────────────────────────────────────────┐
│                      BEZPIECZNY SYSTEM RAG                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📤 BAZA PUBLICZNA (vector_db_public/)                          │
│  ┌────────────────────────────────────┐                         │
│  │  • Embeddingi (wektory 1024D)      │                         │
│  │  • Metadane okrojone:              │──► Model zewnętrzny    │
│  │    - page_number                   │    ✅ Bezpieczne!       │
│  │    - element_id                    │    ❌ NIE widzi tekstów │
│  │    - chunk_type                    │                         │
│  │  ❌ BRAK source_file                │                         │
│  │  ❌ BRAK oryginalnych tekstów       │                         │
│  └────────────────────────────────────┘                         │
│                      ↓                                           │
│              Zwraca tylko ID                                     │
│                      ↓                                           │
│  🔐 MAPOWANIE PRYWATNE (vector_db_private/)                     │
│  ┌────────────────────────────────────┐                         │
│  │  ID → tekst                         │                         │
│  │  ID → source_file                   │  Serwer lokalny        │
│  │  ID → pełne metadane                │  ✅ Pełna kontrola     │
│  └────────────────────────────────────┘                         │
│                      ↓                                           │
│              Zwraca teksty                                       │
│                      ↓                                           │
│              Generuje odpowiedź                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 📊 Porównanie

| Aspekt | Tradycyjne RAG | Bezpieczne RAG |
|--------|----------------|----------------|
| **Embeddingi** | ✅ W bazie | ✅ W bazie publicznej |
| **Teksty** | ✅ W bazie | 🔐 Oddzielnie (lokalnie) |
| **Nazwy plików** | ✅ W bazie | 🔐 Oddzielnie (lokalnie) |
| **Model zewnętrzny widzi** | ❌ WSZYSTKO | ✅ TYLKO embeddingi |
| **Możliwość odtworzenia** | ❌ TAK (100%) | ✅ NIE (brak tekstów) |
| **Rozmiar bazy publicznej** | 42 MB | 31 MB (-25%) |

---

## 🔄 Przepływ danych

### Scenariusz 1: Lokalne użycie (pełny dostęp)
```python
rag = SecureRAG()
results = rag.search_and_get_texts("Jakie kary za kradzież?")
# → Zwraca teksty z lokalnej bazy
```

### Scenariusz 2: Model zewnętrzny (ograniczony dostęp)
```python
# KROK 1: Model zewnętrzny wyszukuje (ma dostęp do vector_db_public/)
results = rag.search_public_only("Jakie kary za kradzież?")
# → Zwraca: ['ID1', 'ID2', 'ID3']
# ✅ Model NIE widzi tekstów!

# KROK 2: Serwer lokalny odczytuje teksty (ma dostęp do vector_db_private/)
texts = rag.get_texts_private(results['ids'][0])
# → Zwraca pełne teksty

# KROK 3: Serwer wysyła TYLKO wybrane fragmenty do modelu
# (nie całą bazę!)
```

---

## 📝 Pliki utworzone

```
vector_db/              → Oryginalna baza (używana lokalnie)
vector_db_public/       → BEZPIECZNA baza dla zewnętrznych modeli
                          • 31.35 MB
                          • 3,483 embeddingi
                          • ❌ BRAK tekstów
                          
vector_db_private/      → Prywatne mapowanie (NIE UDOSTĘPNIAJ!)
  └─ text_mapping.json  • 1.93 MB
                          • Mapowanie ID → tekst
                          • Pełne metadane
```

---

## 🎯 Przykłady użycia

### Test bezpieczeństwa:
```bash
python secure_rag_example.py
```

### Utworzenie bezpiecznych baz:
```bash
python create_secure_vector_db.py
```

---

## ✅ Zalety tego rozwiązania

1. ✅ **Bezpieczeństwo** - model zewnętrzny nie widzi treści
2. ✅ **Wydajność** - wyszukiwanie tak samo szybkie
3. ✅ **Kontrola** - ty decydujesz co udostępnić
4. ✅ **Zgodność** - działa z istniejącym kodem
5. ✅ **Skalowalność** - można udostępnić wielu modelom

---

## ⚠️ Ograniczenia

1. Model zewnętrzny może zobaczyć:
   - Liczba fragmentów w bazie
   - Numery stron (ale nie wie z jakiego dokumentu)
   - Strukturę ID elementów
   
2. Jeśli model ma dostęp do obu baz → wszystko widzi

**ZASADA:** NIGDY nie udostępniaj `vector_db_private/` zewnętrznym systemom!
