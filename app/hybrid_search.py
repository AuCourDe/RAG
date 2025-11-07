#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hybrydowe wyszukiwanie - łączenie Vector Search + BM25 Text Search + Reranking.

Komponenty:
1. BM25 Index - lexical search (dokładne dopasowania słów kluczowych)
2. Vector Search - semantic search (rozumienie znaczenia)
3. Reciprocal Rank Fusion - łączenie wyników
4. Cross-Encoder Reranker - dokładne określenie relevance
"""

import logging
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
RERANKER_MODELS_DIR = MODELS_DIR / "reranker"
RERANKER_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Lazy imports - nie ładuj jeśli nie używasz
_bm25_available = False
_reranker_available = False

try:
    from rank_bm25 import BM25Okapi
    _bm25_available = True
except ImportError:
    logger.warning("rank-bm25 nie zainstalowane. BM25 search niedostępny.")

try:
    from sentence_transformers import CrossEncoder
    _reranker_available = True
except ImportError:
    logger.warning("sentence-transformers CrossEncoder niedostępny. Reranking niedostępny.")


class BM25Index:
    """
    BM25 index dla wyszukiwania leksykalnego.
    
    Świetny dla:
    - Dokładnych dopasowań słów kluczowych
    - Nazw własnych, numerów artykułów
    - Akronimów i skrótów
    - Terminologii specjalistycznej
    """
    
    def __init__(self, cache_dir: Path = None):
        """
        Inicjalizuje BM25 index.
        
        Args:
            cache_dir: Katalog do cache'owania indeksu
        """
        if not _bm25_available:
            raise ImportError("rank-bm25 nie zainstalowane. Zainstaluj: pip install rank-bm25")
        
        self.cache_dir = cache_dir or Path("vector_db")
        self.cache_file = self.cache_dir / "bm25_index.pkl"
        
        self.bm25_index = None
        self.doc_ids = []
        self.tokenized_corpus = []
        
        logger.info("BM25Index zainicjalizowany")
    
    def build_index(self, documents: List[Dict[str, Any]]):
        """
        Buduje BM25 index z dokumentów.
        
        Args:
            documents: Lista dokumentów z polami 'id' i 'content'
        """
        logger.info(f"Budowanie BM25 index dla {len(documents)} dokumentów...")
        
        # Tokenizacja (prosta - lowercase + split)
        self.tokenized_corpus = []
        self.doc_ids = []
        
        for doc in documents:
            # Tokenizacja: lowercase + split po spacjach
            tokens = doc['content'].lower().split()
            self.tokenized_corpus.append(tokens)
            self.doc_ids.append(doc['id'])
        
        # Buduj BM25 index
        self.bm25_index = BM25Okapi(self.tokenized_corpus)
        
        logger.info(f"BM25 index zbudowany: {len(self.doc_ids)} dokumentów")
        
        # Zapisz do cache
        self._save_cache()
    
    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """
        Wyszukuje dokumenty używając BM25.
        
        Args:
            query: Zapytanie użytkownika
            top_k: Liczba wyników do zwrócenia
            
        Returns:
            Lista (doc_id, score) posortowana malejąco po score
        """
        if self.bm25_index is None:
            logger.warning("BM25 index nie jest zbudowany!")
            return []
        
        # Tokenizacja zapytania
        query_tokens = query.lower().split()
        
        # Oblicz BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Pobierz top_k indeksów
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Zwróć (doc_id, score)
        results = [
            (self.doc_ids[idx], scores[idx])
            for idx in top_indices
            if scores[idx] > 0  # Tylko wyniki z niezerowym score
        ]
        
        logger.info(f"BM25 search: znaleziono {len(results)} wyników dla '{query[:50]}...'")
        
        return results
    
    def _save_cache(self):
        """Zapisuje index do cache"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump({
                    'bm25_index': self.bm25_index,
                    'doc_ids': self.doc_ids,
                    'tokenized_corpus': self.tokenized_corpus
                }, f)
            logger.info(f"BM25 index zapisany do cache: {self.cache_file}")
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania BM25 cache: {e}")
    
    def load_cache(self) -> bool:
        """
        Ładuje index z cache.
        
        Returns:
            True jeśli załadowano, False jeśli brak cache
        """
        if not self.cache_file.exists():
            logger.info("Brak cache BM25 index")
            return False
        
        try:
            with open(self.cache_file, 'rb') as f:
                data = pickle.load(f)
            
            self.bm25_index = data['bm25_index']
            self.doc_ids = data['doc_ids']
            self.tokenized_corpus = data['tokenized_corpus']
            
            logger.info(f"BM25 index załadowany z cache: {len(self.doc_ids)} dokumentów")
            return True
            
        except Exception as e:
            logger.error(f"Błąd podczas ładowania BM25 cache: {e}")
            return False


class Reranker:
    """
    Cross-encoder reranker dla dokładnego określenia relevance.
    
    Używa modelu sentence-transformers cross-encoder do oceny
    dopasowania (query, document) pair.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2", device: str = "cuda"):
        """
        Inicjalizuje reranker.
        
        Args:
            model_name: Nazwa modelu cross-encoder
            device: 'cuda' lub 'cpu'
        """
        if not _reranker_available:
            raise ImportError("sentence-transformers CrossEncoder niedostępny. Zainstaluj: pip install sentence-transformers")
        
        logger.info(f"Ładowanie reranker model: {model_name}")
        
        try:
            self.model = CrossEncoder(
                model_name,
                device=device,
                cache_folder=str(RERANKER_MODELS_DIR)
            )
            logger.info(f"Reranker załadowany na {device}")
        except Exception as e:
            logger.warning(f"Nie można załadować na {device}, próbuję CPU: {e}")
            self.model = CrossEncoder(
                model_name,
                device='cpu',
                cache_folder=str(RERANKER_MODELS_DIR)
            )
            logger.info("Reranker załadowany na CPU")
    
    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Reranguje dokumenty według relevance do zapytania.
        
        Args:
            query: Zapytanie użytkownika
            documents: Lista dokumentów do rerankingu
            top_k: Liczba najlepszych wyników do zwrócenia
            
        Returns:
            Lista dokumentów posortowana po relevance score (malejąco)
        """
        if not documents:
            return []
        
        logger.info(f"Reranking {len(documents)} dokumentów...")
        
        # Przygotuj pary (query, document_content)
        pairs = [(query, doc['content']) for doc in documents]
        
        # Oblicz relevance scores
        scores = self.model.predict(pairs)
        
        # Dodaj scores do dokumentów
        for doc, score in zip(documents, scores):
            doc['rerank_score'] = float(score)
        
        # Sortuj malejąco po score
        reranked = sorted(documents, key=lambda x: x['rerank_score'], reverse=True)
        
        # Zwróć top_k
        result = reranked[:top_k]
        
        logger.info(f"Reranking zakończony: zwracam top {len(result)} dokumentów")
        
        return result


def reciprocal_rank_fusion(
    results_list: List[List[Tuple[str, float]]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    Reciprocal Rank Fusion - łączy wyniki z wielu źródeł.
    
    RRF score = sum(1 / (k + rank_i)) dla wszystkich źródeł
    
    Args:
        results_list: Lista list wyników z różnych źródeł
                     Każda lista to [(doc_id, score), ...]
        k: Constant (domyślnie 60)
        
    Returns:
        Lista (doc_id, rrf_score) posortowana malejąco
    """
    # Zbierz wszystkie unikalne doc_ids
    all_doc_ids = set()
    for results in results_list:
        all_doc_ids.update([doc_id for doc_id, _ in results])
    
    # Oblicz RRF score dla każdego doc_id
    rrf_scores = {}
    
    for doc_id in all_doc_ids:
        rrf_score = 0.0
        
        # Dla każdego źródła wyników
        for results in results_list:
            # Znajdź pozycję (rank) doc_id w tym źródle
            for rank, (result_id, _) in enumerate(results, start=1):
                if result_id == doc_id:
                    rrf_score += 1.0 / (k + rank)
                    break
        
        rrf_scores[doc_id] = rrf_score
    
    # Sortuj malejąco po RRF score
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_results


class HybridSearch:
    """
    Hybrydowe wyszukiwanie łączące Vector Search + BM25 + Reranking.
    
    Pipeline:
    1. Vector Search (semantic) → top 20
    2. BM25 Search (lexical) → top 20
    3. RRF merge → top 30-40
    4. Reranking (cross-encoder) → top 10
    """
    
    def __init__(
        self,
        vector_db,
        cache_dir: Path = None,
        use_bm25: bool = True,
        use_reranker: bool = True,
        reranker_device: str = "cuda"
    ):
        """
        Inicjalizuje hybrydowe wyszukiwanie.
        
        Args:
            vector_db: Instancja VectorDatabase z rag_system.py
            cache_dir: Katalog dla cache BM25
            use_bm25: Czy używać BM25 (False = tylko vector search)
            use_reranker: Czy używać rerankera
            reranker_device: 'cuda' lub 'cpu'
        """
        self.vector_db = vector_db
        self.use_bm25 = use_bm25 and _bm25_available
        self.use_reranker = use_reranker and _reranker_available
        
        # BM25 Index
        self.bm25_index = None
        if self.use_bm25:
            try:
                self.bm25_index = BM25Index(cache_dir=cache_dir)
                # Spróbuj załadować z cache
                if not self.bm25_index.load_cache():
                    logger.info("BM25 index wymaga zbudowania przy pierwszym wyszukiwaniu")
            except ImportError as e:
                logger.warning(f"BM25 niedostępny: {e}")
                self.use_bm25 = False
        
        # Reranker
        self.reranker = None
        if self.use_reranker:
            try:
                self.reranker = Reranker(device=reranker_device)
            except ImportError as e:
                logger.warning(f"Reranker niedostępny: {e}")
                self.use_reranker = False
        
        logger.info(f"HybridSearch zainicjalizowany: BM25={self.use_bm25}, Reranker={self.use_reranker}")
    
    def build_bm25_index(self):
        """Buduje BM25 index z dokumentów w bazie wektorowej."""
        if not self.use_bm25 or self.bm25_index is None:
            logger.warning("BM25 nie jest włączone lub niedostępne")
            return
        
        # Pobierz wszystkie dokumenty z ChromaDB
        try:
            all_data = self.vector_db.collection.get(
                include=['documents', 'metadatas']
            )
            
            if not all_data['ids']:
                logger.warning("Brak dokumentów w bazie wektorowej")
                return
            
            # Przygotuj dokumenty dla BM25
            documents = [
                {
                    'id': doc_id,
                    'content': content
                }
                for doc_id, content in zip(all_data['ids'], all_data['documents'])
            ]
            
            # Buduj index
            self.bm25_index.build_index(documents)
            logger.info(f"BM25 index zbudowany dla {len(documents)} dokumentów")
            
        except Exception as e:
            logger.error(f"Błąd podczas budowania BM25 index: {e}")
    
    def search_bm25_only(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Wyszukiwanie tylko przez BM25 (tekstowe).
        
        Args:
            query: Zapytanie użytkownika
            top_k: Liczba wyników
            
        Returns:
            Lista dokumentów posortowana po BM25 score
        """
        logger.info(f"BM25-only wyszukiwanie: '{query[:50]}...'")
        
        if not (self.use_bm25 and self.bm25_index and self.bm25_index.bm25_index):
            logger.warning("BM25 niedostępny!")
            return []
        
        try:
            bm25_list = self.bm25_index.search(query, top_k=top_k)
            doc_ids = [doc_id for doc_id, _ in bm25_list]
            
            # Pobierz pełne dane
            docs_data = self.vector_db.collection.get(
                ids=doc_ids,
                include=['documents', 'metadatas']
            )
            
            documents = []
            for i, doc_id in enumerate(docs_data['ids']):
                documents.append({
                    'id': doc_id,
                    'content': docs_data['documents'][i],
                    'metadata': docs_data['metadatas'][i],
                    'bm25_score': dict(bm25_list)[doc_id]
                })
            
            logger.info(f"BM25: zwracam {len(documents)} wyników")
            return documents
            
        except Exception as e:
            logger.error(f"Błąd BM25 search: {e}")
            return []
    
    def search(self, query: str, top_k: int = 10, use_reranker: bool = True) -> List[Dict[str, Any]]:
        """
        Hybrydowe wyszukiwanie z opcjonalnym rerankerem.
        
        Args:
            query: Zapytanie użytkownika
            top_k: Liczba końcowych wyników
            use_reranker: Czy użyć rerankera (domyślnie True)
            
        Returns:
            Lista dokumentów posortowana po relevance
        """
        logger.info(f"Hybrydowe wyszukiwanie: '{query[:50]}...'")
        
        results_lists = []
        
        # 1. VECTOR SEARCH (semantic)
        logger.info("Etap 1/4: Vector Search (semantic)")
        try:
            vector_results = self.vector_db.collection.query(
                query_texts=[query],
                n_results=20,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Konwertuj do formatu (doc_id, score)
            vector_list = [
                (doc_id, 1.0 - dist)  # Distance → similarity
                for doc_id, dist in zip(vector_results['ids'][0], vector_results['distances'][0])
            ]
            results_lists.append(vector_list)
            logger.info(f"Vector search: {len(vector_list)} wyników")
            
        except Exception as e:
            logger.error(f"Błąd vector search: {e}")
            vector_results = None
        
        # 2. BM25 SEARCH (lexical) - opcjonalne
        if self.use_bm25 and self.bm25_index and self.bm25_index.bm25_index:
            logger.info("Etap 2/4: BM25 Search (lexical)")
            try:
                bm25_list = self.bm25_index.search(query, top_k=20)
                results_lists.append(bm25_list)
                logger.info(f"BM25 search: {len(bm25_list)} wyników")
            except Exception as e:
                logger.error(f"Błąd BM25 search: {e}")
        else:
            logger.info("Etap 2/4: BM25 pominięte (wyłączone lub brak indeksu)")
        
        # 3. RECIPROCAL RANK FUSION
        logger.info("Etap 3/4: Reciprocal Rank Fusion")
        if len(results_lists) > 1:
            merged_results = reciprocal_rank_fusion(results_lists, k=60)
            logger.info(f"RRF: połączono {len(merged_results)} unikalnych dokumentów")
        elif len(results_lists) == 1:
            merged_results = results_lists[0]
            logger.info("RRF: tylko jedno źródło, pomijam fuzję")
        else:
            logger.warning("Brak wyników do fuzji!")
            return []
        
        # Pobierz top 30-40 dla rerankingu
        top_for_rerank = merged_results[:40]
        
        # Pobierz pełne dane dokumentów
        doc_ids_for_rerank = [doc_id for doc_id, _ in top_for_rerank]
        
        try:
            docs_data = self.vector_db.collection.get(
                ids=doc_ids_for_rerank,
                include=['documents', 'metadatas']
            )
            
            # Przygotuj dokumenty
            documents = []
            for i, doc_id in enumerate(docs_data['ids']):
                documents.append({
                    'id': doc_id,
                    'content': docs_data['documents'][i],
                    'metadata': docs_data['metadatas'][i],
                    'rrf_score': dict(top_for_rerank)[doc_id]
                })
        
        except Exception as e:
            logger.error(f"Błąd pobierania dokumentów: {e}")
            return []
        
        # 4. RERANKING - opcjonalne (kontrolowane przez parametr use_reranker)
        if use_reranker and self.use_reranker and self.reranker:
            logger.info(f"Etap 4/4: Reranking {len(documents)} dokumentów")
            try:
                reranked = self.reranker.rerank(query, documents, top_k=top_k)
                logger.info(f"Reranking zakończony: zwracam top {len(reranked)}")
                return reranked
            except Exception as e:
                logger.error(f"Błąd rerankingu: {e}")
                # Fallback: użyj RRF scores
                logger.info("Fallback: używam RRF scores bez rerankingu")
                return documents[:top_k]
        else:
            logger.info("Etap 4/4: Reranking pominięty (wyłączony lub nie wybrany)")
            return documents[:top_k]


if __name__ == "__main__":
    # Testy
    logging.basicConfig(level=logging.INFO)
    
    print("=== TEST: Reciprocal Rank Fusion ===")
    
    # Symulacja wyników z 2 źródeł
    vector_results = [
        ('doc1', 0.95),
        ('doc2', 0.90),
        ('doc3', 0.85),
        ('doc5', 0.80),
    ]
    
    bm25_results = [
        ('doc2', 12.5),
        ('doc4', 10.2),
        ('doc1', 8.7),
        ('doc6', 7.1),
    ]
    
    merged = reciprocal_rank_fusion([vector_results, bm25_results], k=60)
    
    print("\nWyniki RRF:")
    for doc_id, score in merged[:5]:
        print(f"  {doc_id}: {score:.4f}")
    
    print("\n✅ Test zakończony")

