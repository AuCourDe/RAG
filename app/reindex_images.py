#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do ponownego przetworzenia tylko obrazów
"""

import sys
from pathlib import Path
from rag_system import RAGSystem, DocumentProcessor, EmbeddingProcessor, VectorDatabase
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def reindex_images():
    """Przetwarza ponownie tylko obrazy"""
    print("Rozpoczynanie przetwarzania obrazów...")
    
    # Inicjalizacja komponentów
    doc_processor = DocumentProcessor()
    embedding_processor = EmbeddingProcessor()
    vector_db = VectorDatabase()
    
    # Znajdź obrazy w data/
    data_dir = Path("data")
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}
    images = [f for f in data_dir.rglob('*') if f.is_file() and f.suffix.lower() in image_extensions]
    
    print(f"Znaleziono {len(images)} obrazów do przetworzenia")
    
    all_chunks = []
    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Przetwarzanie: {img_path.name}")
        chunks = doc_processor.process_file(img_path)
        if chunks:
            print(f"  ✓ Wygenerowano {len(chunks)} fragmentów")
            all_chunks.extend(chunks)
        else:
            print(f"  ✗ Brak fragmentów")
    
    if all_chunks:
        print(f"\nTworzenie embeddingów dla {len(all_chunks)} fragmentów...")
        chunks_with_embeddings = embedding_processor.create_embeddings(all_chunks)
        
        print(f"Dodawanie do bazy wektorowej...")
        vector_db.add_documents(chunks_with_embeddings)
        
        print(f"\n✅ Zakończono! Dodano {len(all_chunks)} fragmentów z obrazów do bazy.")
    else:
        print("\n⚠️ Nie wygenerowano żadnych fragmentów z obrazów.")

if __name__ == "__main__":
    reindex_images()






