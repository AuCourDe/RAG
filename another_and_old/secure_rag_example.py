#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Przykład użycia BEZPIECZNEJ bazy wektorowej

ARCHITEKTURA:
1. Model zewnętrzny ma dostęp do: vector_db_public/ (tylko embeddingi)
2. Serwer lokalny ma: vector_db_private/ (mapowanie ID -> tekst)
3. Przepływ:
   Model → wyszukuje embeddingi → zwraca ID
   Serwer → odczytuje teksty lokalnie → zwraca do modelu
"""

import chromadb
from sentence_transformers import SentenceTransformer
import json

class SecureRAG:
    """Bezpieczny system RAG z separacją embeddingów i tekstów"""
    
    def __init__(self):
        # Publiczna baza - TYLKO embeddingi (dla zewnętrznych modeli)
        self.public_client = chromadb.PersistentClient(path='vector_db_public')
        self.public_collection = self.public_client.get_collection('embeddings_only')
        
        # Prywatne mapowanie - teksty (NIE UDOSTĘPNIAJ!)
        with open('vector_db_private/text_mapping.json', 'r', encoding='utf-8') as f:
            self.private_mapping = json.load(f)
        
        # Model do tworzenia embeddingów dla zapytań
        self.encoder = SentenceTransformer('intfloat/multilingual-e5-large')
        
        print("✅ SecureRAG zainicjalizowany")
        print(f"   📤 Publiczna baza: {self.public_collection.count()} embeddingów")
        print(f"   🔐 Prywatne mapowanie: {len(self.private_mapping)} tekstów")
    
    def search_public_only(self, query: str, n_results: int = 3):
        """
        KROK 1: Wyszukiwanie w publicznej bazie (bez dostępu do tekstów)
        To może zrobić model zewnętrzny - nie zobaczy treści!
        """
        print(f"\n🔍 Wyszukiwanie (publiczne): '{query}'")
        
        # Embedding zapytania
        query_embedding = self.encoder.encode([query]).tolist()
        
        # Wyszukiwanie - model zewnętrzny widzi tylko to:
        results = self.public_collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            include=['metadatas', 'distances']  # ❌ BEZ 'documents'!
        )
        
        print(f"   Znaleziono {len(results['ids'][0])} wyników")
        print(f"   Zwracane ID: {results['ids'][0][:2]}...")
        
        return results
    
    def get_texts_private(self, result_ids: list):
        """
        KROK 2: Odczyt tekstów z prywatnej bazy (tylko lokalnie!)
        Model zewnętrzny NIE ma do tego dostępu!
        """
        print(f"\n🔐 Odczyt tekstów (prywatnie):")
        
        texts = []
        for doc_id in result_ids:
            if doc_id in self.private_mapping:
                data = self.private_mapping[doc_id]
                texts.append({
                    'id': doc_id,
                    'text': data['text'],
                    'source': data['source_file'],
                    'page': data['page_number']
                })
        
        print(f"   Odczytano {len(texts)} tekstów z lokalnej bazy")
        return texts
    
    def search_and_get_texts(self, query: str, n_results: int = 3):
        """Pełne wyszukiwanie - dla lokalnego użycia"""
        # Krok 1: Wyszukaj w publicznej bazie
        public_results = self.search_public_only(query, n_results)
        
        # Krok 2: Pobierz teksty lokalnie
        texts = self.get_texts_private(public_results['ids'][0])
        
        return texts


def demo():
    """Demonstracja bezpiecznego RAG"""
    print("="*70)
    print("DEMO: BEZPIECZNY SYSTEM RAG")
    print("="*70)
    
    # Inicjalizacja
    rag = SecureRAG()
    
    # Test wyszukiwania
    query = "Jakie są zasady odpowiedzialności karnej?"
    
    print("\n" + "="*70)
    print("SCENARIUSZ: Model zewnętrzny wyszukuje w bazie")
    print("="*70)
    
    # To może zrobić model zewnętrzny
    public_results = rag.search_public_only(query, n_results=3)
    
    print("\n📊 CO WIDZI MODEL ZEWNĘTRZNY:")
    for i, (doc_id, meta, dist) in enumerate(zip(
        public_results['ids'][0],
        public_results['metadatas'][0],
        public_results['distances'][0]
    )):
        print(f"\n   [{i+1}] ID: {doc_id[:20]}...")
        print(f"       Metadane: strona={meta['page_number']}, element={meta['element_id']}")
        print(f"       Podobieństwo: {1-dist:.3f}")
        print(f"       ❌ TEKST: NIE WIDZI!")
    
    # To może zrobić tylko serwer lokalny
    print("\n" + "="*70)
    print("📥 SERWER LOKALNY - odczyt tekstów:")
    print("="*70)
    
    texts = rag.get_texts_private(public_results['ids'][0])
    
    for i, item in enumerate(texts[:2]):  # Pokaż 2 pierwsze
        print(f"\n   [{i+1}] {item['source']}, strona {item['page']}")
        print(f"       Tekst: {item['text'][:150]}...")
    
    print("\n" + "="*70)
    print("✅ BEZPIECZEŃSTWO ZAPEWNIONE!")
    print("   • Model widzi tylko embeddingi")
    print("   • Teksty odczytywane lokalnie")
    print("   • Pełna kontrola nad danymi!")
    print("="*70)

if __name__ == "__main__":
    demo()


