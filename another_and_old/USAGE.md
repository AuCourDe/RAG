# System RAG - Instrukcja użycia

System RAG (Retrieval-Augmented Generation) dla dokumentów prawnych w języku polskim.

## Wymagania
- Python 3.12
- Ollama z modelem Gemma 3:12B
- Środowisko wirtualne `venv_rag`

## Instalacja

```bash
# Aktywacja środowiska
source venv_rag/bin/activate

# Instalacja bibliotek (jeśli jeszcze nie zainstalowano)
pip install -r requirements.txt
```

## Użycie

### 1. Indeksowanie dokumentów

```bash
python rag_system.py index data/
```

To polecenie:
- Przetwarza wszystkie pliki PDF, DOCX, XLSX, obrazy z katalogu `data/`
- Tworzy embeddingi dla fragmentów dokumentów
- Zapisuje do bazy wektorowej `vector_db/`

### 2. Zadawanie pytań

```bash
python rag_system.py query "Twoje pytanie?"
```

Przykłady pytań:
```bash
python rag_system.py query "Jakie są główne tematy w dokumentach?"
python rag_system.py query "Co mówi dokument o..."
```

### 3. Test systemu

```bash
python test_rag.py
```

## Obsługiwane formaty
- PDF (z ekstrakcją tekstu i grafik)
- DOCX
- XLSX
- Obrazy: JPG, JPEG, PNG, BMP (z OCR i opisem AI)

## Statystyki ostatniego indeksowania

**Data:** 2025-10-08
- **Dokumenty:** 3 pliki PDF
- **Fragmenty:** 3476
- **Czas indeksowania:** 133 sekundy
- **Czas odpowiedzi:** ~117 sekund

## Baza wektorowa
- **Lokalizacja:** `vector_db/`
- **Typ:** ChromaDB
- **Model embeddingów:** intfloat/multilingual-e5-large

## Model LLM
- **Model:** Ollama Gemma 3:12B (multimodal)
- **Endpoint:** http://localhost:11434
- **Procesor:** 100% GPU (NVIDIA RTX 3060 12GB)
- **Używany do:** 
  - Rozpoznawania obrazów (główna metoda)
  - Generowania odpowiedzi na pytania
- **Wydajność:** Rozpoznawanie obrazu: ~10-30 sekund (GPU) vs ~2-3 minuty (CPU)

## Logi
- **Główny log:** `rag_system.log`
- **Log działań:** `action_log.txt`





