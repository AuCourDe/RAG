# PLAN ROZWOJU SYSTEMU RAG - v4.0

**Data utworzenia**: 2025-11-04  
**Priorytet**: NAJWAŻNIEJSZA JEST JAKOŚĆ WYSZUKANYCH DANYCH  
**Status**: Plan do realizacji

---

## SPIS TREŚCI

1. [Przegląd i Priorytety](#przegląd-i-priorytety)
2. [Hybrydowe Wyszukiwanie - PRIORYTET 1](#1-hybrydowe-wyszukiwanie---priorytet-1)
3. [Optymalizacja Rozmiaru Chunków - PRIORYTET 1](#2-optymalizacja-rozmiaru-chunków---priorytet-1)
4. [Integracja OpenAI API - PRIORYTET 2](#3-integracja-openai-api---priorytet-2)
5. [Filtrowanie Powitań - PRIORYTET 2](#4-filtrowanie-powitań---priorytet-2)
6. [GPU/CPU Switch - PRIORYTET 3](#5-gpucpu-switch---priorytet-3)
7. [System Logowania + Microsoft Purview - PRIORYTET 3](#6-system-logowania--microsoft-purview---priorytet-3)
8. [Obsługa Intranetu - PRIORYTET 4](#7-obsługa-intranetu---priorytet-4)
9. [Timeline i Harmonogram](#timeline-i-harmonogram)
10. [Wymagania Sprzętowe](#wymagania-sprzętowe)

---

## PRZEGLĄD I PRIORYTETY

### Obecny Stan Systemu (v3.0)
✅ Multimodalne przetwarzanie (PDF, DOCX, XLSX, obrazy, audio, wideo)  
✅ Embeddingi GPU (intfloat/multilingual-e5-large)  
✅ LLM lokalny (Gemma 3:12B)  
✅ Wyszukiwanie wektorowe (ChromaDB + HNSW)  
✅ Restrykcyjny system prompt  
✅ Frontend Streamlit z autoryzacją  
✅ Auto-indeksowanie (watchdog)  

### Główne Cele v4.0
🎯 **PRIORYTET 1**: Maksymalizacja jakości wyszukiwania  
🎯 **PRIORYTET 2**: Elastyczność (OpenAI API + lokalne modele)  
🎯 **PRIORYTET 3**: Monitoring i compliance  
🎯 **PRIORYTET 4**: Rozszerzenie źródeł danych (intranet)  

---

## 1. HYBRYDOWE WYSZUKIWANIE - PRIORYTET 1

### 🎯 CEL: Zwiększenie jakości i trafności wyszukanych fragmentów

**PROBLEM**: Obecne wyszukiwanie czysto wektorowe (HNSW) może przegapić:
- Dokładne dopasowania słów kluczowych
- Specjalistyczną terminologię prawną
- Nazwy własne, numery artykułów
- Akronimy i skróty

**ROZWIĄZANIE**: Hybrydowe wyszukiwanie = Vector Search + Text Search + Reranking

### Architektura Hybrydowego Wyszukiwania

```
Pytanie użytkownika
         |
         v
    [Preprocessing]
         |
         +------------------+------------------+
         |                                     |
         v                                     v
   [Vector Search]                      [Text Search]
   (HNSW Semantic)                       (BM25 Lexical)
         |                                     |
         | Top 20 wyników                      | Top 20 wyników
         |                                     |
         +------------------+------------------+
                           |
                           v
                     [Merge & Deduplicate]
                           |
                           v (Top 30-40 wyników)
                        [Reranker]
                     (Cross-encoder)
                           |
                           v (Top 5-10 wyników)
                    [Final Context]
                           |
                           v
                      [LLM Response]
```

### Komponenty

#### 1.1 Vector Search (obecne)
- **Model**: intfloat/multilingual-e5-large (1024D)
- **Index**: HNSW w ChromaDB
- **Zalety**: Rozumienie semantyczne, podobieństwo kontekstowe
- **Wady**: Może przegapić exact matches

#### 1.2 Text Search (NOWE - BM25)
- **Algorytm**: BM25 (Best Matching 25)
- **Implementacja**: `rank-bm25` library lub własna
- **Zalety**: 
  - Dokładne dopasowanie słów kluczowych
  - Szybkie (nie wymaga GPU)
  - Świetne dla nazw, numerów, akronimów
- **Parametry**:
  - k1 = 1.5 (częstość terminów)
  - b = 0.75 (normalizacja długości dokumentu)

#### 1.3 Reranker (NOWE - Cross-Encoder)
- **Model**: `cross-encoder/ms-marco-MiniLM-L-12-v2` (122M params)
- **Alternatywa PL**: `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (multilingual)
- **Funkcja**: Dokładne określenie relevance każdego fragmentu do pytania
- **Input**: (pytanie, fragment) → Output: relevance score [0-1]
- **Zalety**: 
  - Wyższa precyzja niż bi-encoder (embeddings)
  - Uwzględnia interakcję między pytaniem a fragmentem
- **Wady**: Wolniejsze (wymaga forward pass dla każdej pary)

### Strategia Łączenia Wyników

**Reciprocal Rank Fusion (RRF)**:
```python
score_RRF = sum(1 / (k + rank_i))
```
- k = 60 (constant)
- rank_i = pozycja w danym rankingu (vector/text)

**Zalety RRF**:
- Nie wymaga tuningu wag
- Równomiernie traktuje oba źródła
- Odporne na outliers

### Implementacja

#### Krok 1: Dodanie BM25 Index
```python
# rag_system.py
from rank_bm25 import BM25Okapi
import pickle

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        self.bm25_index = None
        self.bm25_docs = []
        
    def _build_bm25_index(self):
        """Buduje BM25 index dla wszystkich dokumentów"""
        # Pobierz wszystkie dokumenty z ChromaDB
        all_docs = self.collection.get()
        
        # Tokenizacja (prosta - split + lowercase)
        tokenized = [doc.lower().split() for doc in all_docs['documents']]
        self.bm25_docs = all_docs['ids']
        
        # Buduj index
        self.bm25_index = BM25Okapi(tokenized)
        
        # Zapisz do pickle (szybsze ładowanie)
        with open('vector_db/bm25_index.pkl', 'wb') as f:
            pickle.dump((self.bm25_index, self.bm25_docs), f)
```

#### Krok 2: Hybrydowe Wyszukiwanie
```python
def hybrid_search(self, query: str, top_k: int = 10):
    """Wyszukiwanie hybrydowe: vector + BM25 + reranking"""
    
    # 1. VECTOR SEARCH (semantic)
    vector_results = self.collection.query(
        query_texts=[query],
        n_results=20
    )
    
    # 2. BM25 SEARCH (lexical)
    query_tokens = query.lower().split()
    bm25_scores = self.bm25_index.get_scores(query_tokens)
    top_bm25_indices = bm25_scores.argsort()[-20:][::-1]
    bm25_results = [self.bm25_docs[i] for i in top_bm25_indices]
    
    # 3. MERGE + RRF
    merged = self._reciprocal_rank_fusion(
        vector_results['ids'][0],
        bm25_results,
        k=60
    )
    
    # 4. RERANKING (top 30 -> top 10)
    reranked = self._rerank(query, merged[:30], top_k=top_k)
    
    return reranked
```

#### Krok 3: Reranking
```python
from sentence_transformers import CrossEncoder

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2')
        
    def _rerank(self, query: str, doc_ids: list, top_k: int = 10):
        """Reranking używając cross-encodera"""
        
        # Pobierz dokumenty
        docs = self.collection.get(ids=doc_ids)
        
        # Przygotuj pary (query, doc)
        pairs = [(query, doc) for doc in docs['documents']]
        
        # Oblicz relevance scores
        scores = self.reranker.predict(pairs)
        
        # Sortuj według score (malejąco)
        ranked_indices = scores.argsort()[::-1][:top_k]
        
        # Zwróć top_k ID
        return [doc_ids[i] for i in ranked_indices]
```

### Timeline Implementacji
- **Tydzień 1**: Dodanie BM25 index (2-3 dni)
- **Tydzień 1**: RRF merging (1 dzień)
- **Tydzień 2**: Reranker integration (2-3 dni)
- **Tydzień 2**: Testy A/B (jakość vs obecny system) (2 dni)
- **Tydzień 3**: Optymalizacja performance (2 dni)
- **Tydzień 3**: Frontend - toggle hybrydowe/wektorowe (1 dzień)

### Koszty (VRAM)
- BM25: 0 GB (CPU)
- Reranker: ~0.5 GB VRAM (batch processing)
- **RAZEM**: +0.5 GB (zmieści się w RTX 3060)

### Oczekiwane Rezultaty
- **Precision@5**: +15-25% (więcej trafnych wyników w top 5)
- **Recall**: +10-15% (mniej przegapionych dokumentów)
- **Czas wyszukiwania**: +0.5-1s (reranking)
- **Jakość odpowiedzi**: Znacząco lepsza (mniej halucynacji)

---

## 2. OPTYMALIZACJA ROZMIARU CHUNKÓW - PRIORYTET 1

### 🎯 CEL: Optymalne rozmiary chunków dla każdego typu mediów

**PROBLEM**: Obecny system używa jednego rozmiaru chunka dla wszystkich mediów
- PDF: 500 znaków (może być za małe dla kontekstu prawnego)
- Audio: 1 segment Whisper (zmienne, 5-30s)
- Video: 1 sekunda (może być za granularne)

**ROZWIĄZANIE**: Adaptacyjne chunking per typ mediów

### Rekomendowane Rozmiary Chunków

#### 2.1 PDF / DOCX (Dokumenty Tekstowe)

**ANALIZA**:
- Kodeks karny: długie artykuły, kontekst prawny
- Embedding model: max 512 tokens (~400 słów PL ~2000 znaków)
- Trade-off: kontekst vs granularność

**REKOMENDACJA**:
```python
CHUNK_SIZE_TEXT = {
    'standard': 800,      # znaki (default)
    'legal': 1200,        # dokumenty prawne (więcej kontekstu)
    'technical': 1000,    # dokumentacja techniczna
    'short_form': 500     # artykuły, notatki
}
OVERLAP = 200  # znaki (25% overlap dla kontekstu)
```

**STRATEGIE PODZIAŁU**:
1. **Semantic chunking** (preferowane):
   - Dziel po paragrafach
   - Zachowaj kompletne zdania
   - Nie przerywaj w środku artykułu/sekcji
   
2. **Fixed-size with overlap** (fallback):
   - Stały rozmiar + overlap
   - Dla tekstów bez wyraźnej struktury

#### 2.2 AUDIO (Transkrypcje)

**ANALIZA**:
- Whisper segments: zmienne (2-30s)
- Kontekst: pytanie-odpowiedź lub temat
- User needs: zlokalizowanie w nagraniu

**REKOMENDACJA**:
```python
AUDIO_CHUNK_STRATEGY = {
    'per_speaker_turn': True,    # Dziel gdy zmienia się mówca
    'max_duration': 60,           # sekundy (1 minuta max)
    'min_duration': 10,           # sekundy (minimum kontekstu)
    'merge_short': True,          # Łącz krótkie segmenty (<10s)
}
```

**STRATEGIA**:
- Grupuj segmenty tego samego mówcy (do 60s)
- Zachowaj timestampy początku/końca
- Metadata: speaker ID, czas

#### 2.3 VIDEO (Transkrypcja + Klatki)

**ANALIZA**:
- Obecne: 1 fragment = 1 sekunda
- Problem: 300 fragmentów dla 5-min video (za dużo!)
- Kontekst: potrzeba połączyć audio+video dla dłuższego okresu

**REKOMENDACJA**:
```python
VIDEO_CHUNK_STRATEGY = {
    'duration': 10,              # sekund per fragment (10s zamiast 1s)
    'frame_sampling': 2,         # klatki: co 2s (zamiast co 1s)
    'audio_alignment': True,     # Wyrównaj z segmentami audio
    'scene_detection': False,    # TODO: wykrywanie zmiany sceny (przyszłość)
}
```

**EFEKT**:
- 5-min video: 30 fragmentów (zamiast 300)
- Każdy fragment: 10s audio + 5 klatek (co 2s)
- **Oszczędność czasu**: ~10x (10 min zamiast 100 min!)

#### 2.4 OBRAZY (Opisy)

**ANALIZA**:
- Gemma 3 generuje opisy (50-300 słów)
- Nie wymaga chunkingu (jeden opis = jeden obraz)

**REKOMENDACJA**:
```python
IMAGE_CHUNK_STRATEGY = {
    'chunk_size': None,          # Cały opis jako jeden fragment
    'metadata': {
        'width': True,
        'height': True,
        'format': True
    }
}
```

### Konfiguracja - Frontend vs Kod

**DECYZJA**: **Hybrid approach** (config w kodzie + override w frontend dla zaawansowanych)

```python
# config.py (default values)
CHUNK_CONFIG = {
    'pdf': {
        'size': 800,
        'overlap': 200,
        'strategy': 'semantic'  # lub 'fixed'
    },
    'audio': {
        'max_duration': 60,
        'min_duration': 10,
        'per_speaker': True
    },
    'video': {
        'duration': 10,
        'frame_sampling': 2
    }
}
```

**Frontend - Ustawienia (dla zaawansowanych)**:
- Tab "⚙️ Ustawienia" → Nowa sekcja "Chunking"
- Slidery dla rozmiaru chunków
- Checkbox "Semantic chunking" dla PDF
- Info tooltip: "Większe chunki = więcej kontekstu, mniejsze = lepsza granularność"

### Implementacja

```python
# rag_system.py
from config import CHUNK_CONFIG

class RAGSystem:
    def __init__(self, chunk_config=None):
        self.chunk_config = chunk_config or CHUNK_CONFIG
        
    def _chunk_text(self, text: str, doc_type: str = 'pdf'):
        """Adaptive chunking based on document type"""
        config = self.chunk_config.get(doc_type, {})
        
        if config.get('strategy') == 'semantic':
            return self._semantic_chunking(text, config['size'], config['overlap'])
        else:
            return self._fixed_chunking(text, config['size'], config['overlap'])
            
    def _semantic_chunking(self, text: str, target_size: int, overlap: int):
        """Dzieli po paragrafach/zdaniach zachowując kontekst"""
        # Split by paragraphs
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= target_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        # Add overlap
        return self._add_overlap(chunks, overlap)
```

### Timeline
- **Tydzień 4**: Implementacja adaptive chunking (3 dni)
- **Tydzień 4**: Config file + frontend controls (2 dni)
- **Tydzień 5**: Reindeksowanie z nowymi chunks (1 dzień)
- **Tydzień 5**: Testy jakości (2 dni)

---

## 3. INTEGRACJA OPENAI API - PRIORYTET 2

### 🎯 CEL: Elastyczność - użyj OpenAI jeśli jest token, fallback na Gemma

**ARCHITEKTURA**:
```
User Query
     |
     v
[Check OpenAI Token]
     |
     +--- Token exists? ---+
     |                     |
    YES                   NO
     |                     |
     v                     v
[OpenAI API]         [Gemma 3:12B Local]
 (GPT-4, GPT-3.5)    (Ollama)
     |                     |
     +----------+----------+
                |
                v
           [Response]
```

### Komponenty

#### 3.1 Token Management

```python
# auth_config.json (rozszerzone)
{
    "users": {...},
    "openai_api_key": "",           # Token OpenAI (opcjonalny)
    "openai_model": "gpt-4o-mini",  # Default model
    "openai_enabled": false         # Auto-detect based on key
}
```

#### 3.2 Model Provider Abstraction

```python
# model_provider.py (NOWY PLIK)
from abc import ABC, abstractmethod
import os
import openai
import requests

class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: str, **kwargs) -> str:
        pass
        
    @abstractmethod
    def is_available(self) -> bool:
        pass

class OpenAIProvider(ModelProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        openai.api_key = api_key
        
    def generate(self, prompt: str, context: str, **kwargs) -> str:
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": context}
        ]
        
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get('temperature', 0.1),
            max_tokens=kwargs.get('max_tokens', 1000)
        )
        
        return response.choices[0].message.content
        
    def is_available(self) -> bool:
        try:
            openai.Model.list()
            return True
        except:
            return False

class OllamaProvider(ModelProvider):
    def __init__(self, model: str = "gemma3:12b"):
        self.model = model
        self.base_url = "http://127.0.0.1:11434"
        
    def generate(self, prompt: str, context: str, **kwargs) -> str:
        # Existing Ollama code from rag_system.py
        full_prompt = f"{prompt}\n\nKontekst:\n{context}"
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": full_prompt,
                "temperature": kwargs.get('temperature', 0.1),
                "num_predict": kwargs.get('max_tokens', 1000),
                "stream": False
            }
        )
        
        return response.json()['response']
        
    def is_available(self) -> bool:
        try:
            requests.get(f"{self.base_url}/api/tags", timeout=2)
            return True
        except:
            return False

class ModelFactory:
    @staticmethod
    def create_provider(config: dict) -> ModelProvider:
        """Factory pattern - wybiera provider based on config"""
        openai_key = config.get('openai_api_key', '').strip()
        
        # Try OpenAI first if key exists
        if openai_key:
            provider = OpenAIProvider(
                api_key=openai_key,
                model=config.get('openai_model', 'gpt-4o-mini')
            )
            if provider.is_available():
                print("✅ Using OpenAI API")
                return provider
            else:
                print("⚠️ OpenAI key invalid, falling back to Ollama")
        
        # Fallback to Ollama
        provider = OllamaProvider()
        if provider.is_available():
            print("✅ Using Ollama (local)")
            return provider
        else:
            raise Exception("❌ No model provider available!")
```

#### 3.3 Integration w RAG System

```python
# rag_system.py (modified)
from model_provider import ModelFactory

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        
        # Load config
        with open('auth_config.json', 'r') as f:
            config = json.load(f)
            
        # Initialize model provider
        self.model_provider = ModelFactory.create_provider(config)
        
    def query(self, query_text: str, top_k: int = 5):
        # ... wyszukiwanie jak poprzednio ...
        
        # Generate response using selected provider
        response = self.model_provider.generate(
            prompt=self.system_prompt,
            context=formatted_context,
            temperature=0.1,
            max_tokens=1000
        )
        
        return response
```

#### 3.4 Frontend - Wybór Modelu

**app.py - Nowa sekcja w Ustawieniach**:
```python
# Tab: Ustawienia
with st.expander("🤖 Model API"):
    st.write("**OpenAI API (opcjonalne)**")
    
    # Token input
    current_key = config.get('openai_api_key', '')
    masked_key = current_key[:8] + "..." if current_key else ""
    
    new_key = st.text_input(
        "API Key",
        value=masked_key,
        type="password",
        help="Zostaw puste aby używać lokalnego modelu Ollama"
    )
    
    # Model selection (only if key exists)
    if new_key:
        model_options = [
            "gpt-4o",           # Najnowszy, najdroższy
            "gpt-4o-mini",      # Zbalansowany (REKOMENDOWANY)
            "gpt-3.5-turbo"     # Tańszy, szybszy
        ]
        
        selected_model = st.selectbox(
            "Model",
            options=model_options,
            index=1,  # default: gpt-4o-mini
            help="gpt-4o-mini: najlepszy stosunek jakość/cena"
        )
        
        # Pricing info
        st.info(f"""
        **Szacunkowe koszty (gpt-4o-mini)**:
        - Input: $0.15 / 1M tokens
        - Output: $0.60 / 1M tokens
        - ~100 zapytań: $0.50-2.00
        """)
        
    # Save button
    if st.button("💾 Zapisz ustawienia API"):
        config['openai_api_key'] = new_key if new_key != masked_key else current_key
        config['openai_model'] = selected_model if new_key else ""
        
        # Save to file
        with open('auth_config.json', 'w') as f:
            json.dump(config, f, indent=2)
            
        st.success("✅ Zapisano! Odśwież stronę aby zastosować zmiany.")
        st.rerun()
    
    # Current status
    st.divider()
    if current_key:
        st.success("🟢 **Aktywny model**: OpenAI API")
        st.caption(f"Model: {config.get('openai_model', 'N/A')}")
    else:
        st.info("🔵 **Aktywny model**: Ollama (lokalny, darmowy)")
        st.caption("Model: Gemma 3:12B")
```

### Modele OpenAI - Rekomendacje

| Model | Koszt (input/output) | Prędkość | Jakość | Rekomendacja |
|-------|---------------------|----------|--------|--------------|
| gpt-4o | $5/$15 per 1M tokens | Wolny | ⭐⭐⭐⭐⭐ | Najwyższa jakość |
| **gpt-4o-mini** | **$0.15/$0.60** | **Średni** | **⭐⭐⭐⭐** | **NAJLEPSZY** |
| gpt-3.5-turbo | $0.50/$1.50 | Szybki | ⭐⭐⭐ | Budżetowy |

**REKOMENDACJA**: **gpt-4o-mini** (15x tańszy niż gpt-4o, jakość zbliżona)

### Timeline
- **Tydzień 6**: Model abstraction layer (2 dni)
- **Tydzień 6**: OpenAI integration (2 dni)
- **Tydzień 7**: Frontend - API settings (2 dni)
- **Tydzień 7**: Testing (1 dzień)

### Koszty (przykład: 1000 zapytań/miesiąc)
- **Gemma 3 (local)**: $0 (tylko energia ~$5/m)
- **GPT-4o-mini**: ~$10-20/m (zależy od długości)
- **GPT-4o**: ~$100-150/m

---

## 4. FILTROWANIE POWITAŃ - PRIORYTET 2

### 🎯 CEL: Ignorowanie powitań użytkownika aby nie trafiały do promptu

**PROBLEM**:
```
User: "Cześć! Dzień dobry! Mam pytanie o Kodeks karny..."
System prompt: <- trafia całość z "Cześć! Dzień dobry!"
```

**EFEKT**: Niepotrzebne tokeny, zmniejsza kontekst, model może odpowiedzieć na powitanie

**ROZWIĄZANIE**: Preprocessing - detekcja i usuwanie powitań

### Strategie Filtrowania

#### 4.1 Pattern Matching (Szybkie)

```python
# greeting_filter.py (NOWY PLIK)
import re

GREETING_PATTERNS = [
    # Polskie powitania
    r'\b(cześć|czesc|hej|hey|siema|witaj|witam|dzień dobry|dobry wieczór|dobry dzień)\b',
    r'\b(dzien dobry|dobry wieczor)\b',
    r'\b(do widzenia|dowidzenia|papa|na razie)\b',
    
    # Angielskie (jeśli obsługujemy)
    r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
    r'\b(goodbye|bye|see you)\b',
    
    # Wykrzykniki
    r'^[\!]+$',
    
    # Emotikony (opcjonalne)
    r'[😀😃😄😁😊🙂🙃😉👋]',
]

class GreetingFilter:
    def __init__(self):
        # Kompiluj patterns (szybciej)
        self.patterns = [
            re.compile(p, re.IGNORECASE | re.UNICODE) 
            for p in GREETING_PATTERNS
        ]
        
    def remove_greetings(self, text: str) -> str:
        """Usuwa powitania z tekstu"""
        cleaned = text
        
        # Remove patterns
        for pattern in self.patterns:
            cleaned = pattern.sub('', cleaned)
            
        # Clean up extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Clean up punctuation at start
        cleaned = re.sub(r'^[,\.\!]+\s*', '', cleaned)
        
        return cleaned
        
    def has_greeting(self, text: str) -> bool:
        """Sprawdza czy tekst zawiera powitanie"""
        return any(pattern.search(text) for pattern in self.patterns)
```

#### 4.2 NLP-based (Zaawansowane - opcjonalne)

```python
# Używa spaCy do wykrywania intencji
import spacy

class AdvancedGreetingFilter:
    def __init__(self):
        self.nlp = spacy.load('pl_core_news_sm')  # Polski model
        
        # Greeting intents
        self.greeting_intents = {
            'GREETING', 'GOODBYE', 'THANKS'
        }
        
    def remove_greetings(self, text: str) -> str:
        """NLP-based greeting removal"""
        doc = self.nlp(text)
        
        # Analyze sentences
        cleaned_sentences = []
        for sent in doc.sents:
            # Check if sentence is greeting
            if not self._is_greeting_sentence(sent):
                cleaned_sentences.append(sent.text)
                
        return ' '.join(cleaned_sentences)
        
    def _is_greeting_sentence(self, sent) -> bool:
        """Sprawdza czy zdanie to powitanie"""
        # Heurystyka: krótkie zdania (<5 słów) z greeting keywords
        if len(sent) < 5:
            text_lower = sent.text.lower()
            return any(g in text_lower for g in ['cześć', 'hej', 'witaj', 'dzień dobry'])
        return False
```

**DECYZJA**: Użyj **Pattern Matching** (szybsze, wystarczające, bez dodatkowych zależności)

### Implementacja

```python
# rag_system.py (modified)
from greeting_filter import GreetingFilter

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        self.greeting_filter = GreetingFilter()
        
    def query(self, query_text: str, top_k: int = 5):
        # NOWY: Filtruj powitania
        original_query = query_text
        query_text = self.greeting_filter.remove_greetings(query_text)
        
        # Log if greeting was removed
        if original_query != query_text:
            self.logger.info(f"Removed greeting: '{original_query}' -> '{query_text}'")
            
        # Sprawdź czy zostało coś po filtrowaniu
        if not query_text or len(query_text) < 3:
            return {
                'answer': "Proszę zadaj pytanie dotyczące dokumentów.",
                'sources': [],
                'time': 0
            }
            
        # ... reszta kodu jak poprzednio ...
```

### Frontend Info

```python
# app.py - info dla użytkownika
st.info("""
ℹ️ **Wskazówka**: Możesz pisać naturalnie! 
System automatycznie ignoruje powitania i skupia się na Twoim pytaniu.

❌ „Cześć! Dzień dobry! Co mówi art. 148?"
✅ „Co mówi art. 148?"  <- To samo dla systemu
""")
```

### Przykłady

| Input | Po filtrze | Zmiana |
|-------|------------|--------|
| "Cześć! Mam pytanie o art. 148" | "Mam pytanie o art. 148" | ✅ |
| "Dzień dobry, co mówi Kodeks?" | "co mówi Kodeks?" | ✅ |
| "Hej! 😊 Czy można..." | "Czy można..." | ✅ |
| "Co to jest zabójstwo?" | "Co to jest zabójstwo?" | - (brak powitania) |

### Timeline
- **Tydzień 7**: Implementacja pattern matching (1 dzień)
- **Tydzień 7**: Testing z różnymi wariantami (0.5 dnia)
- **Tydzień 7**: Frontend info (0.5 dnia)

---

## 5. GPU/CPU SWITCH - PRIORYTET 3

### 🎯 CEL: Możliwość wyboru trybu działania (GPU/CPU)

**USE CASES**:
- Server bez GPU → CPU mode
- Development/testing → CPU mode (oszczędność VRAM)
- Production → GPU mode (wydajność)
- Hybrydowy → Embeddings GPU, LLM CPU (jeśli małe VRAM)

### Architektura

```python
# config.py
DEVICE_CONFIG = {
    'mode': 'auto',  # 'auto', 'gpu', 'cpu', 'hybrid'
    'embeddings_device': 'cuda',  # 'cuda' lub 'cpu'
    'llm_device': 'cuda',
    'reranker_device': 'cuda',
}
```

### Implementacja

```python
# device_manager.py (NOWY PLIK)
import torch

class DeviceManager:
    def __init__(self, mode='auto'):
        self.mode = mode
        self.cuda_available = torch.cuda.is_available()
        
        # Detect best configuration
        if mode == 'auto':
            self.config = self._auto_detect()
        else:
            self.config = self._manual_config(mode)
            
    def _auto_detect(self):
        """Auto-detect best device configuration"""
        if not self.cuda_available:
            print("⚠️ GPU not available, using CPU")
            return {
                'embeddings': 'cpu',
                'llm': 'cpu',
                'reranker': 'cpu'
            }
            
        # Check VRAM
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU available: {torch.cuda.get_device_name(0)} ({vram_gb:.1f} GB)")
        
        if vram_gb >= 12:
            # Full GPU mode
            return {
                'embeddings': 'cuda',
                'llm': 'cuda',
                'reranker': 'cuda'
            }
        elif vram_gb >= 8:
            # Hybrid: embeddings GPU, LLM depends on Ollama
            return {
                'embeddings': 'cuda',
                'llm': 'cuda',
                'reranker': 'cpu'  # Save VRAM
            }
        else:
            # Embeddings only on GPU
            return {
                'embeddings': 'cuda',
                'llm': 'cpu',
                'reranker': 'cpu'
            }
            
    def get_device(self, component: str):
        """Get device for specific component"""
        return self.config.get(component, 'cpu')
```

### Integration

```python
# rag_system.py (modified)
from device_manager import DeviceManager

class RAGSystem:
    def __init__(self, device_mode='auto'):
        self.device_manager = DeviceManager(device_mode)
        
        # Initialize embeddings with device
        embeddings_device = self.device_manager.get_device('embeddings')
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-large",
            model_kwargs={'device': embeddings_device}
        )
        
        # Reranker with device
        reranker_device = self.device_manager.get_device('reranker')
        self.reranker = CrossEncoder(
            'cross-encoder/ms-marco-MiniLM-L-12-v2',
            device=reranker_device
        )
        
        print(f"🔧 Device config: {self.device_manager.config}")
```

### Frontend Control

```python
# app.py - Settings
with st.expander("⚙️ GPU/CPU"):
    device_mode = st.selectbox(
        "Tryb urządzenia",
        options=['auto', 'gpu', 'cpu', 'hybrid'],
        index=0,
        help="""
        - auto: Automatyczne wykrywanie (rekomendowane)
        - gpu: Wymuś GPU (wymaga CUDA)
        - cpu: Tylko CPU (wolniejsze, ale działa wszędzie)
        - hybrid: Embeddings GPU, reszta CPU
        """
    )
    
    if st.button("🔄 Zastosuj i restartuj"):
        # Save to config
        config['device_mode'] = device_mode
        with open('config.json', 'w') as f:
            json.dump(config, f)
        st.warning("Restartuj aplikację aby zastosować zmiany")
```

### Timeline
- **Tydzień 8**: Device manager (1 dzień)
- **Tydzień 8**: Integration (1 dzień)
- **Tydzień 8**: Testing CPU/GPU modes (1 dzień)
- **Tydzień 8**: Frontend controls (0.5 dnia)

---

## 6. SYSTEM LOGOWANIA + MICROSOFT PURVIEW - PRIORYTET 3

### 🎯 CEL: Logowanie aktywności użytkowników + compliance

**REQUIREMENTS**:
- Log wszystkich promptów użytkowników
- Log odpowiedzi systemu
- Log źródeł użytych do odpowiedzi
- Timestamp, user ID, session ID
- Integracja z Microsoft Purview (audit, compliance)

### Architektura Logowania

```python
# audit_logger.py (NOWY PLIK)
import json
import logging
from datetime import datetime
from typing import Dict, List
import hashlib

class AuditLogger:
    def __init__(self, log_file='audit_log.jsonl'):
        self.log_file = log_file
        
        # Setup logging
        self.logger = logging.getLogger('audit')
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
    def log_query(self, 
                  user_id: str,
                  session_id: str,
                  query: str,
                  response: str,
                  sources: List[Dict],
                  model: str,
                  time_ms: float):
        """Log user query and system response"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'query',
            'user_id': user_id,
            'session_id': session_id,
            'query': query,
            'query_hash': hashlib.sha256(query.encode()).hexdigest()[:16],  # Privacy
            'response': response,
            'response_length': len(response),
            'sources': [
                {
                    'file': s.get('source_file', ''),
                    'page': s.get('page', ''),
                    'element_id': s.get('element_id', '')
                }
                for s in sources
            ],
            'sources_count': len(sources),
            'model': model,
            'time_ms': time_ms,
        }
        
        # Write as JSON line
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        
    def log_file_upload(self, user_id: str, filename: str, file_size: int):
        """Log file upload event"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_upload',
            'user_id': user_id,
            'filename': filename,
            'file_size_bytes': file_size,
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        
    def log_file_delete(self, user_id: str, filename: str):
        """Log file deletion"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_delete',
            'user_id': user_id,
            'filename': filename,
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        
    def log_login(self, user_id: str, success: bool, ip: str):
        """Log login attempt"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'login',
            'user_id': user_id,
            'success': success,
            'ip_address': ip,
        }
        self.logger.info(json.dumps(log_entry, ensure_ascii=False))
```

### Integracja w RAG System

```python
# rag_system.py (modified)
from audit_logger import AuditLogger

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        self.audit_logger = AuditLogger()
        
    def query(self, query_text: str, top_k: int = 5, user_id: str = None, session_id: str = None):
        start_time = time.time()
        
        # ... existing query code ...
        
        # LOG QUERY
        self.audit_logger.log_query(
            user_id=user_id or 'anonymous',
            session_id=session_id or 'unknown',
            query=query_text,
            response=answer,
            sources=sources,
            model=self.model_provider.model_name,
            time_ms=(time.time() - start_time) * 1000
        )
        
        return result
```

### Microsoft Purview Integration

**API**: Microsoft Graph API + Audit Log

```python
# purview_integration.py (NOWY PLIK)
import requests
import json
from typing import Dict

class PurviewIntegration:
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.token = None
        
    def authenticate(self):
        """Get access token"""
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://graph.microsoft.com/.default'
        }
        
        response = requests.post(url, data=data)
        self.token = response.json()['access_token']
        
    def send_audit_event(self, event: Dict):
        """Send audit event to Purview"""
        if not self.token:
            self.authenticate()
            
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        # Transform to Purview format
        purview_event = {
            'activityDateTime': event['timestamp'],
            'activityType': event['event_type'],
            'userId': event['user_id'],
            'userType': 'Member',
            'clientIP': event.get('ip_address', ''),
            'additionalDetails': json.dumps(event)
        }
        
        # Send to Purview (via Azure AD Audit Log)
        url = f"{self.base_url}/auditLogs/directoryAudits"
        response = requests.post(url, headers=headers, json=purview_event)
        
        return response.status_code == 201
        
    def batch_send_logs(self, log_file='audit_log.jsonl'):
        """Send batch of logs to Purview"""
        with open(log_file, 'r') as f:
            for line in f:
                event = json.loads(line)
                self.send_audit_event(event)
```

### Konfiguracja Purview

```python
# auth_config.json (extended)
{
    "users": {...},
    "purview": {
        "enabled": false,
        "tenant_id": "",
        "client_id": "",
        "client_secret": "",
        "sync_interval_hours": 24  # Sync co 24h
    }
}
```

### Frontend - Logs Viewer

```python
# app.py - nowa zakładka "📊 Logi"
if user_role == 'admin':
    tab_logs = st.tabs(["Zapytania", "Ustawienia"])[0]
    
    with tab_logs:
        st.title("📊 Logi aktywności")
        
        # Load logs
        logs = []
        with open('audit_log.jsonl', 'r') as f:
            for line in f:
                logs.append(json.loads(line))
        logs = logs[-100:]  # Last 100
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            user_filter = st.selectbox("Użytkownik", ["Wszyscy"] + list(set(l['user_id'] for l in logs)))
        with col2:
            event_filter = st.selectbox("Typ", ["Wszystkie"] + list(set(l['event_type'] for l in logs)))
            
        # Filter logs
        filtered = logs
        if user_filter != "Wszyscy":
            filtered = [l for l in filtered if l['user_id'] == user_filter]
        if event_filter != "Wszystkie":
            filtered = [l for l in filtered if l['event_type'] == event_filter]
            
        # Display as table
        import pandas as pd
        df = pd.DataFrame(filtered)
        st.dataframe(df[['timestamp', 'event_type', 'user_id', 'query', 'time_ms']])
        
        # Export
        if st.button("📥 Eksportuj do CSV"):
            csv = df.to_csv(index=False)
            st.download_button("Download", csv, "audit_logs.csv", "text/csv")
```

### Timeline
- **Tydzień 9**: Audit logger implementation (2 dni)
- **Tydzień 9**: Purview integration (2 dni)
- **Tydzień 10**: Frontend logs viewer (2 dni)
- **Tydzień 10**: Testing + GDPR compliance review (1 dzień)

### Compliance (GDPR)
- ✅ Logs zawierają user_id (nie email)
- ✅ Query hash dla prywatności (opcjonalnie)
- ✅ Możliwość usunięcia logów użytkownika
- ✅ Retention policy (domyślnie 90 dni)

---

## 7. OBSŁUGA INTRANETU - PRIORYTET 4

### 🎯 CEL: Rozszerzenie źródeł danych o intranet/internet

**USE CASES**:
- Wyszukiwanie w wewnętrznej wiki firmy
- Dodanie kontekstu z dokumentacji online
- Real-time data (gdy dokumenty się zmieniają)

### Architektura

```
User Query
     |
     v
[Detect: Local DB or Web Search?]
     |
     +------------+-------------+
     |                          |
[Local DB]              [Web Search]
(Existing)              (Bing Search API)
     |                          |
     |                          v
     |                  [Scrape Top N URLs]
     |                          |
     |                          v
     |                  [Convert to Text]
     |                  (HTML → Markdown)
     |                          |
     |                          v
     |                   [Chunk & Embed]
     |                          |
     +------------+-------------+
                  |
                  v
           [Merge Results]
                  |
                  v
            [Rerank & LLM]
```

### Komponenty

#### 7.1 Bing Search API

```python
# web_search.py (NOWY PLIK)
import requests
from typing import List, Dict

class BingSearchProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        
    def search(self, query: str, count: int = 5, site: str = None) -> List[Dict]:
        """
        Search Bing
        
        Args:
            query: Search query
            count: Number of results
            site: Limit to specific site (e.g. "site:example.com")
        """
        headers = {
            'Ocp-Apim-Subscription-Key': self.api_key
        }
        
        # Add site filter if provided (for intranet)
        if site:
            query = f"site:{site} {query}"
            
        params = {
            'q': query,
            'count': count,
            'mkt': 'pl-PL',  # Polski rynek
        }
        
        response = requests.get(self.base_url, headers=headers, params=params)
        results = response.json()
        
        # Parse results
        parsed = []
        for item in results.get('webPages', {}).get('value', []):
            parsed.append({
                'title': item['name'],
                'url': item['url'],
                'snippet': item['snippet'],
            })
            
        return parsed
```

#### 7.2 Web Scraping

```python
# web_scraper.py (NOWY PLIK)
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (RAG System Bot)'
        }
        
    def scrape(self, url: str, max_depth: int = 0) -> Dict:
        """
        Scrape webpage and convert to text
        
        Args:
            url: URL to scrape
            max_depth: Crawling depth (0 = single page only)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
                
            # Extract title
            title = soup.find('title').get_text() if soup.find('title') else url
            
            # Convert to Markdown (cleaner than plain text)
            content_html = str(soup.find('body') or soup)
            content_md = md(content_html)
            
            # Clean up
            content_md = '\n'.join([
                line.strip() 
                for line in content_md.split('\n') 
                if line.strip()
            ])
            
            return {
                'url': url,
                'title': title,
                'content': content_md,
                'length': len(content_md)
            }
            
        except Exception as e:
            return {
                'url': url,
                'title': 'Error',
                'content': f'Failed to scrape: {str(e)}',
                'length': 0
            }
```

#### 7.3 Integration w RAG

```python
# rag_system.py (modified)
from web_search import BingSearchProvider
from web_scraper import WebScraper

class RAGSystem:
    def __init__(self):
        # ... existing code ...
        
        # Web search (opcjonalne)
        bing_key = config.get('bing_search_key', '')
        self.web_search = BingSearchProvider(bing_key) if bing_key else None
        self.web_scraper = WebScraper()
        
    def query(self, query_text: str, top_k: int = 5, use_web: bool = False, intranet_site: str = None):
        """Query with optional web search"""
        
        # 1. LOCAL SEARCH (always)
        local_results = self.hybrid_search(query_text, top_k=top_k)
        
        # 2. WEB SEARCH (if enabled)
        web_results = []
        if use_web and self.web_search:
            # Search Bing
            search_results = self.web_search.search(
                query_text, 
                count=3,  # Top 3 URLs
                site=intranet_site  # Limit to intranet if provided
            )
            
            # Scrape each URL
            for result in search_results:
                scraped = self.web_scraper.scrape(result['url'])
                
                # Chunk and embed
                chunks = self._chunk_text(scraped['content'], 'web')
                for chunk in chunks:
                    # Create embedding
                    embedding = self.embeddings.embed_query(chunk)
                    
                    # Add to temporary collection (not persisted)
                    web_results.append({
                        'content': chunk,
                        'source': result['url'],
                        'title': result['title'],
                        'embedding': embedding
                    })
            
            # Rerank: local + web
            all_results = local_results + web_results
            reranked = self._rerank(query_text, all_results, top_k=top_k)
        else:
            reranked = local_results
            
        # 3. GENERATE RESPONSE
        # ... as before ...
```

### Konfiguracja

```python
# auth_config.json (extended)
{
    "bing_search_key": "",  # Bing Search API key (opcjonalny)
    "intranet_sites": [     # Lista dozwolonych domen intranetowych
        "wiki.firma.pl",
        "docs.firma.pl"
    ],
    "web_search": {
        "enabled": false,
        "max_results": 3,
        "max_depth": 0,  # 0 = tylko pojedyncze strony
        "cache_ttl_hours": 24  # Cache wyników przez 24h
    }
}
```

### Frontend

```python
# app.py - query section
with st.form("query_form"):
    query = st.text_area("Zadaj pytanie", height=100)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        use_web = st.checkbox(
            "🌐 Przeszukaj także intranet/web",
            value=False,
            help="Wyszukuje dodatkowo w określonych źródłach online"
        )
    with col2:
        submit = st.form_submit_button("🔍 Szukaj", use_container_width=True)
        
    if submit and query:
        with st.spinner("Szukam..."):
            result = rag_system.query(
                query,
                use_web=use_web,
                intranet_site=config.get('intranet_sites', [None])[0]
            )
        # ... display results ...
```

### Głębokość Crawlingu

**REKOMENDACJA**: `max_depth = 0` (tylko pojedyncze strony)

**Dlaczego?**:
- Szybkość: 1 strona = ~2-5s, 10 stron = ~20-50s
- Relevance: Głębsze strony często mniej istotne
- Koszt: Bing Search API: $7/1000 queries

**Opcje**:
- `max_depth = 0`: Tylko URL z Bing Search
- `max_depth = 1`: URL + linki z tej strony (do 10)
- `max_depth = 2`: Recursive (nie rekomendowane - za wolne)

### Timeline
- **Tydzień 11**: Bing Search API integration (2 dni)
- **Tydzień 11**: Web scraping + HTML→Markdown (2 dni)
- **Tydzień 12**: Integration w RAG (2 dni)
- **Tydzień 12**: Frontend controls + testing (1 dzień)

### Koszty
- **Bing Search API**: $7/1000 queries (~$0.007 per query)
- **Przykład**: 100 queries/dzień = $21/miesiąc

---

## TIMELINE I HARMONOGRAM

### Faza 1: Jakość Wyszukiwania (3 tygodnie)
**Tydzień 1-3**: Hybrydowe wyszukiwanie + Chunking
- ✅ BM25 index
- ✅ Reranking
- ✅ Adaptive chunking
- ✅ A/B testing

**Deliverables**:
- Zwiększona jakość wyszukiwania o 15-25%
- Optymalne chunki per media type
- Dokumentacja zmian

### Faza 2: Elastyczność (2 tygodnie)
**Tydzień 4-5**: OpenAI API + Filtrowanie
- ✅ Model abstraction layer
- ✅ OpenAI integration
- ✅ Greeting filter
- ✅ Frontend controls

**Deliverables**:
- Możliwość użycia GPT-4/3.5
- Automatyczne filtrowanie powitań
- Instrukcje dla użytkowników

### Faza 3: Monitoring (2 tygodnie)
**Tydzień 6-7**: GPU/CPU + Logging
- ✅ Device manager
- ✅ Audit logger
- ✅ Logs viewer (frontend)

**Deliverables**:
- Możliwość wyboru GPU/CPU
- Kompletne logowanie aktywności
- GDPR compliance

### Faza 4: Purview + Intranet (2 tygodnie)
**Tydzień 8-9**: Microsoft Purview + Web Search
- ✅ Purview integration
- ✅ Bing Search API
- ✅ Web scraping
- ✅ Testing

**Deliverables**:
- Integracja z Purview
- Możliwość wyszukiwania w intranecie
- Dokumentacja konfiguracji

### Faza 5: Testing & Optimization (1 tydzień)
**Tydzień 10**: Końcowe testy i optymalizacja
- ✅ Performance testing
- ✅ User acceptance testing
- ✅ Documentation
- ✅ Deployment

---

## WYMAGANIA SPRZĘTOWE

### Obecny System (v3.0)
- **GPU**: RTX 3060 12GB
- **RAM**: 16GB (recommended 32GB)
- **Disk**: 50GB (models + data)

### Po Implementacji (v4.0)

#### Minimal (CPU Mode)
- **CPU**: 8 cores (Intel i7 / AMD Ryzen 7)
- **RAM**: 32GB
- **GPU**: Optional
- **Disk**: 50GB

**Performance**:
- Query: ~10-15s (embeddings CPU)
- Reranking: ~2s (CPU)

#### Recommended (GPU Mode)
- **GPU**: RTX 3060 12GB (lub lepsza)
- **RAM**: 32GB
- **CPU**: 8 cores
- **Disk**: 100GB SSD

**Performance**:
- Query: ~3-5s (all GPU)
- Reranking: ~0.5s (GPU)

#### Production (Full Features)
- **GPU**: RTX 4070 16GB lub RTX 3090 24GB
- **RAM**: 64GB
- **CPU**: 16 cores
- **Disk**: 500GB NVMe SSD
- **Network**: 100 Mbps+ (for web search)

**Supports**:
- Concurrent users: 10-20
- Database size: 15GB+
- Web search + Purview
- All features enabled

---

## ZALEŻNOŚCI (Nowe Biblioteki)

```txt
# requirements.txt (ADDITIONS)

# Hybrydowe wyszukiwanie
rank-bm25>=0.2.2
sentence-transformers>=2.2.2  # Already present, ensure version

# OpenAI API
openai>=1.0.0

# Web search & scraping
beautifulsoup4>=4.12.0
markdownify>=0.11.6
requests>=2.31.0  # Already present

# Microsoft Purview
msal>=1.24.0  # Microsoft Authentication Library
azure-identity>=1.14.0

# Device management
torch>=2.0.0  # Already present, ensure version

# Optional: NLP for greeting detection (if advanced version)
# spacy>=3.7.0
# python-Levenshtein>=0.21.0
```

---

## PODSUMOWANIE PRIORYTETÓW

### ⭐⭐⭐ NAJWYŻSZY PRIORYTET (Tydzień 1-3)
1. **Hybrydowe wyszukiwanie**: BM25 + Vector + Reranking
2. **Optymalizacja chunków**: Adaptive per media type

**Uzasadnienie**: Bezpośrednio wpływa na jakość odpowiedzi (główny cel!)

### ⭐⭐ WYSOKI PRIORYTET (Tydzień 4-7)
3. **OpenAI API integration**: Elastyczność + lepszy model
4. **Filtrowanie powitań**: UX improvement
5. **GPU/CPU switch**: Elastyczność deployment
6. **System logowania**: Podstawowe compliance

**Uzasadnienie**: Zwiększa elastyczność i użyteczność systemu

### ⭐ ŚREDNI PRIORYTET (Tydzień 8-10)
7. **Microsoft Purview**: Enterprise compliance
8. **Obsługa intranetu**: Rozszerzenie źródeł

**Uzasadnienie**: Ważne dla enterprise, ale nie krytyczne dla działania

---

## RYZYKA I MITIGACJE

### Ryzyko 1: Reranking wolny
**Mitigacja**: Batch processing, cache, GPU acceleration

### Ryzyko 2: OpenAI API koszty
**Mitigacja**: Fallback na Gemma, monitoring kosztów, rate limiting

### Ryzyko 3: Web scraping niestabilne
**Mitigacja**: Timeout, retry logic, cache, error handling

### Ryzyko 4: VRAM overflow (reranker + embeddings)
**Mitigacja**: Device manager, offloading, batch size reduction

### Ryzyko 5: Purview integration complexity
**Mitigacja**: Dokumentacja Microsoft, przykłady, etapowe wdrożenie

---

## METRYKI SUKCESU

### Jakość (v4.0 vs v3.0)
- ✅ Precision@5: +15-25%
- ✅ Recall: +10-15%
- ✅ User satisfaction: +20%

### Performance
- ✅ Query time: <5s (GPU), <15s (CPU)
- ✅ Uptime: >99%

### Adoption
- ✅ Daily active users: Tracking
- ✅ Queries per day: Tracking
- ✅ Documents indexed: Tracking

---

**Dokument utworzony**: 2025-11-04  
**Wersja**: 1.0  
**Autor**: AI Assistant  
**Status**: Do akceptacji przez użytkownika

**Następne kroki**:
1. Przegląd i akceptacja planu
2. Rozpoczęcie Fazy 1 (Hybrydowe wyszukiwanie)
3. Regularne przeglądy postępu (co tydzień)

