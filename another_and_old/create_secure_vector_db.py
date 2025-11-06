#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt tworzący BEZPIECZNĄ bazę wektorową - tylko embeddingi, BEZ tekstów
Użycie: python create_secure_vector_db.py
"""

import chromadb
from chromadb.config import Settings
import json
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_secure_vector_db():
    """
    Tworzy dwie bazy:
    1. PUBLICZNA (vector_db_public/) - tylko embeddingi + metadane (BEZ TEKSTÓW)
    2. PRYWATNA (vector_db_private/) - mapowanie ID -> tekst (lokalnie)
    """
    
    logger.info("🔒 Tworzenie BEZPIECZNEJ bazy wektorowej...")
    
    # Otwórz istniejącą bazę
    logger.info("Ładowanie oryginalnej bazy...")
    original_client = chromadb.PersistentClient(
        path="vector_db",
        settings=Settings(anonymized_telemetry=False)
    )
    original_collection = original_client.get_collection("legal_documents")
    
    # Pobierz wszystkie dane
    logger.info("Pobieranie wszystkich danych z oryginalnej bazy...")
    all_data = original_collection.get(include=['embeddings', 'metadatas', 'documents'])
    
    total = len(all_data['ids'])
    logger.info(f"Znaleziono {total} fragmentów")
    
    # === 1. BAZA PUBLICZNA - BEZ TEKSTÓW ===
    logger.info("\n📤 Tworzenie PUBLICZNEJ bazy (tylko embeddingi)...")
    Path("vector_db_public").mkdir(exist_ok=True)
    
    public_client = chromadb.PersistentClient(
        path="vector_db_public",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Usuń kolekcję jeśli istnieje
    try:
        public_client.delete_collection("embeddings_only")
    except:
        pass
    
    public_collection = public_client.get_or_create_collection("embeddings_only")
    
    # Dodaj tylko ID, embeddingi i OKROJONE metadane
    public_metadatas = []
    for meta in all_data['metadatas']:
        # Usuń nazwę pliku źródłowego - zostaw tylko ogólne info
        secure_meta = {
            'page_number': meta['page_number'],
            'chunk_type': meta['chunk_type'],
            'element_id': meta['element_id'],
            # ❌ NIE dodajemy 'source_file' - to poufne!
        }
        public_metadatas.append(secure_meta)
    
    logger.info("Dodawanie embeddingów do publicznej bazy...")
    public_collection.add(
        ids=all_data['ids'],
        embeddings=all_data['embeddings'],
        metadatas=public_metadatas,
        # ❌ NIE dodajemy documents - to poufne teksty!
    )
    
    logger.info(f"✅ Baza publiczna utworzona: {total} embeddingów (BEZ tekstów)")
    
    # === 2. PRYWATNE MAPOWANIE - lokalnie ===
    logger.info("\n🔐 Tworzenie PRYWATNEGO mapowania (ID -> tekst)...")
    Path("vector_db_private").mkdir(exist_ok=True)
    
    # Zapisz mapowanie ID -> pełne dane (lokalnie, NIE udostępniaj!)
    private_mapping = {}
    for i, doc_id in enumerate(all_data['ids']):
        private_mapping[doc_id] = {
            'text': all_data['documents'][i],
            'source_file': all_data['metadatas'][i]['source_file'],
            'page_number': all_data['metadatas'][i]['page_number'],
            'element_id': all_data['metadatas'][i]['element_id']
        }
    
    with open('vector_db_private/text_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(private_mapping, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ Prywatne mapowanie zapisane: {len(private_mapping)} wpisów")
    
    # === PORÓWNANIE ROZMIARÓW ===
    logger.info("\n📊 PORÓWNANIE ROZMIARÓW:")
    
    import os
    
    def get_size(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total += os.path.getsize(fp)
        return total
    
    original_size = get_size("vector_db") / (1024*1024)
    public_size = get_size("vector_db_public") / (1024*1024)
    private_size = get_size("vector_db_private") / (1024*1024)
    
    logger.info(f"  Oryginalna baza:  {original_size:.2f} MB (teksty + embeddingi)")
    logger.info(f"  PUBLICZNA baza:   {public_size:.2f} MB (TYLKO embeddingi) ✅ BEZPIECZNA")
    logger.info(f"  PRYWATNE dane:    {private_size:.2f} MB (teksty, LOKALNIE)")
    logger.info(f"  Oszczędność:      {original_size - public_size:.2f} MB ({(original_size - public_size)/original_size*100:.1f}%)")
    
    # === INSTRUKCJE ===
    logger.info("\n" + "="*70)
    logger.info("✅ SUKCES! Utworzono bezpieczną konfigurację:")
    logger.info("="*70)
    logger.info("\n📤 UDOSTĘPNIJ ZEWNĘTRZNEMU MODELOWI:")
    logger.info("   → vector_db_public/  (tylko embeddingi, BEZ tekstów)")
    logger.info("\n🔐 TRZYMAJ LOKALNIE (NIE UDOSTĘPNIAJ!):")
    logger.info("   → vector_db_private/ (mapowanie ID -> tekst)")
    logger.info("\n🔍 JAK TO DZIAŁA:")
    logger.info("   1. Model zewnętrzny wyszukuje w vector_db_public (ma tylko embeddingi)")
    logger.info("   2. Zwraca Ci ID pasujących fragmentów")
    logger.info("   3. Ty lokalnie odczytujesz teksty z vector_db_private/")
    logger.info("   4. Model NIE widzi treści dokumentów! ✅")
    logger.info("="*70)
    
    return True

if __name__ == "__main__":
    create_secure_vector_db()


