#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do generowania pytań dla istniejących plików w bazie
Uruchom po dodaniu nowej funkcjonalności aby wygenerować pytania dla już zindeksowanych plików
"""

from rag_system import RAGSystem, add_questions_for_file, load_suggested_questions
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_questions_for_existing_files():
    """Generuje pytania dla wszystkich plików już obecnych w bazie"""
    logger.info("="*70)
    logger.info("🤔 Generowanie pytań dla istniejących plików")
    logger.info("="*70)
    
    # Inicjalizacja systemu
    rag = RAGSystem()
    
    # Pobierz listę wszystkich plików w bazie
    try:
        collection = rag.vector_db.collection
        all_data = collection.get(include=['metadatas'])
        
        # Zbierz unikalne nazwy plików
        files = set()
        for meta in all_data['metadatas']:
            files.add(meta['source_file'])
        
        logger.info(f"📄 Znaleziono {len(files)} unikalnych plików w bazie")
        
        # Generuj pytania dla każdego pliku
        for idx, file_name in enumerate(sorted(files), 1):
            logger.info(f"\n[{idx}/{len(files)}] Przetwarzanie: {file_name}")
            try:
                add_questions_for_file(file_name, rag, max_questions=3)
            except Exception as e:
                logger.error(f"Błąd dla {file_name}: {e}")
                continue
        
        # Podsumowanie
        questions = load_suggested_questions()
        logger.info("\n" + "="*70)
        logger.info(f"✅ ZAKOŃCZONO")
        logger.info(f"📊 Łączna liczba wygenerowanych pytań: {len(questions)}")
        logger.info(f"📁 Pytania zapisane w: suggested_questions.json")
        logger.info("="*70)
        
        # Wyświetl przykłady
        if questions:
            logger.info("\n📋 Przykłady wygenerowanych pytań:")
            for q in questions[:5]:
                logger.info(f"   • {q['question']}")
                logger.info(f"     (źródło: {q['source_file']})")
        
    except Exception as e:
        logger.error(f"❌ Błąd: {e}", exc_info=True)

if __name__ == "__main__":
    generate_questions_for_existing_files()

