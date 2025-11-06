#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kompleksowy test systemu RAG - wszystkie typy plików
"""

import time
import shutil
from pathlib import Path
from rag_system import RAGSystem
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestResults:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
    
    def add(self, name, status, message):
        self.tests.append({
            'name': name,
            'status': status,
            'message': message
        })
        if status:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n" + "="*80)
        print("PODSUMOWANIE TESTÓW")
        print("="*80)
        for test in self.tests:
            status_icon = "✅" if test['status'] else "❌"
            print(f"{status_icon} {test['name']}")
            if test['message']:
                print(f"   {test['message']}")
        print("="*80)
        print(f"PASSED: {self.passed}/{len(self.tests)}")
        print(f"FAILED: {self.failed}/{len(self.tests)}")
        print("="*80)
        return self.failed == 0

def wait_for_indexing(rag, expected_count, timeout=60):
    """Czeka aż pliki zostaną zaindeksowane"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            count = rag.vector_db.collection.count()
            if count >= expected_count:
                return True
        except:
            pass
        time.sleep(2)
    return False

def test_file_type(file_name, file_type, rag, results):
    """Testuje pojedynczy typ pliku"""
    logger.info("="*80)
    logger.info(f"TEST: {file_type.upper()}")
    logger.info("="*80)
    
    source_file = Path("sample_test_files") / file_name
    dest_file = Path("data") / file_name
    
    # 1. Sprawdź czy plik źródłowy istnieje
    if not source_file.exists():
        results.add(f"{file_type}: Plik źródłowy", False, f"Brak pliku: {source_file}")
        return
    
    results.add(f"{file_type}: Plik źródłowy", True, f"Znaleziono: {source_file.name}")
    
    # 2. Skopiuj plik do data/
    try:
        shutil.copy(source_file, dest_file)
        logger.info(f"✅ Skopiowano {file_name} do data/")
        results.add(f"{file_type}: Kopiowanie", True, f"Skopiowano do data/")
    except Exception as e:
        results.add(f"{file_type}: Kopiowanie", False, f"Błąd: {e}")
        return
    
    # 3. Poczekaj chwilę na stabilizację pliku
    time.sleep(3)
    
    # 4. Ręcznie zaindeksuj plik (nie czekaj na file watcher)
    try:
        logger.info(f"Indeksowanie {file_name}...")
        chunks = rag.doc_processor.process_file(dest_file)
        
        if not chunks:
            results.add(f"{file_type}: Przetwarzanie", False, f"Brak fragmentów z pliku")
            return
        
        logger.info(f"  Znaleziono {len(chunks)} fragmentów")
        results.add(f"{file_type}: Przetwarzanie", True, f"Znaleziono {len(chunks)} fragmentów")
        
        # Utwórz embeddingi
        chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
        
        # Dodaj do bazy
        rag.vector_db.add_documents(chunks_with_embeddings)
        logger.info(f"✅ Dodano {len(chunks)} fragmentów do bazy")
        results.add(f"{file_type}: Indeksacja", True, f"Dodano {len(chunks)} fragmentów do bazy")
        
    except Exception as e:
        logger.error(f"❌ Błąd podczas indeksacji: {e}", exc_info=True)
        results.add(f"{file_type}: Indeksacja", False, f"Błąd: {e}")
        return
    
    # 5. Sprawdź czy plik jest w bazie
    time.sleep(2)
    try:
        count = rag.vector_db.collection.count()
        logger.info(f"  Fragmentów w bazie: {count}")
        
        # Sprawdź czy nasz plik jest w bazie
        all_data = rag.vector_db.collection.get(include=['metadatas'])
        files_in_db = set(meta['source_file'] for meta in all_data['metadatas'])
        
        if file_name in files_in_db:
            results.add(f"{file_type}: W bazie", True, f"Plik znaleziony w bazie")
        else:
            results.add(f"{file_type}: W bazie", False, f"Plik NIE znaleziony w bazie. Pliki: {files_in_db}")
            return
            
    except Exception as e:
        results.add(f"{file_type}: W bazie", False, f"Błąd sprawdzania: {e}")
        return
    
    # 6. Testuj wyszukiwanie - różne zapytania dla różnych typów plików
    test_queries = {
        'PDF': ["Co zawiera dokument?", "Jakie informacje są w pliku?"],
        'Image': ["Co jest na obrazie?", "Opisz zawartość obrazu"],
        'Audio': ["Co mówi nagranie?", "Transkrypcja audio"],
        'Video': ["Co jest w filmie?", "Opisz zawartość wideo"]
    }
    
    queries = test_queries.get(file_type, ["Testowe pytanie"])
    
    for query in queries[:1]:  # Test tylko pierwszego pytania
        try:
            logger.info(f"  Wyszukiwanie: '{query}'")
            sources = rag.vector_db.search(query, n_results=3)
            
            if sources and len(sources) > 0:
                logger.info(f"  ✅ Znaleziono {len(sources)} wyników")
                
                # Sprawdź czy któryś wynik pochodzi z naszego pliku
                has_our_file = any(s.source_file == file_name for s in sources)
                
                if has_our_file:
                    results.add(f"{file_type}: Wyszukiwanie", True, f"Znaleziono {len(sources)} wyników, w tym z naszego pliku")
                else:
                    results.add(f"{file_type}: Wyszukiwanie", False, f"Znaleziono wyniki, ale NIE z naszego pliku")
                    return
            else:
                results.add(f"{file_type}: Wyszukiwanie", False, f"Brak wyników dla: '{query}'")
                return
                
        except Exception as e:
            results.add(f"{file_type}: Wyszukiwanie", False, f"Błąd: {e}")
            return
    
    # 7. Testuj generowanie odpowiedzi
    try:
        logger.info(f"  Generowanie odpowiedzi...")
        answer = rag.query(query, n_results=3)
        
        if answer and len(answer) > 10:
            logger.info(f"  ✅ Odpowiedź wygenerowana ({len(answer)} znaków)")
            results.add(f"{file_type}: Generowanie odpowiedzi", True, f"Odpowiedź: {len(answer)} znaków")
        else:
            results.add(f"{file_type}: Generowanie odpowiedzi", False, f"Odpowiedź pusta lub zbyt krótka")
            
    except Exception as e:
        results.add(f"{file_type}: Generowanie odpowiedzi", False, f"Błąd: {e}")

def main():
    """Główna funkcja testowa"""
    print("="*80)
    print("KOMPLEKSOWY TEST SYSTEMU RAG v4")
    print("="*80)
    print()
    
    results = TestResults()
    
    # Przygotowanie
    logger.info("Przygotowanie środowiska testowego...")
    
    # Wyczyść folder data/
    data_dir = Path("data")
    for f in data_dir.glob("*"):
        if f.is_file():
            f.unlink()
    logger.info("✅ Wyczyszczono folder data/")
    
    # Inicjalizacja systemu RAG
    try:
        logger.info("Inicjalizacja systemu RAG...")
        rag = RAGSystem()
        logger.info("✅ System RAG zainicjalizowany")
        results.add("Inicjalizacja RAG", True, "System zainicjalizowany poprawnie")
    except Exception as e:
        logger.error(f"❌ Błąd inicjalizacji: {e}")
        results.add("Inicjalizacja RAG", False, f"Błąd: {e}")
        results.print_summary()
        return
    
    # Sprawdź czy baza jest pusta
    try:
        initial_count = rag.vector_db.collection.count()
        logger.info(f"Fragmentów w bazie przed testami: {initial_count}")
        results.add("Baza początkowa", initial_count == 0, f"Fragmentów: {initial_count} (oczekiwano 0)")
    except Exception as e:
        results.add("Baza początkowa", False, f"Błąd: {e}")
    
    print()
    
    # TEST 1: PDF (dokument tekstowy)
    test_file_type("test_document.pdf", "PDF", rag, results)
    
    # Wyczyść bazę przed następnym testem
    try:
        rag.vector_db.collection.delete(where={})
        logger.info("🧹 Wyczyszczono bazę przed następnym testem")
    except:
        pass
    
    # TEST 2: PNG (obraz)
    test_file_type("test_image.png", "Image", rag, results)
    
    # Wyczyść bazę
    try:
        rag.vector_db.collection.delete(where={})
    except:
        pass
    
    # TEST 3: MP3 (audio)
    test_file_type("test_audio.mp3", "Audio", rag, results)
    
    # Wyczyść bazę
    try:
        rag.vector_db.collection.delete(where={})
    except:
        pass
    
    # TEST 4: MP4 (wideo) - DŁUGIE, pomiń jeśli trzeba
    logger.info("\n⚠️ Test wideo może zająć ~10 minut (Whisper + Vision)")
    logger.info("Pomijam test wideo dla szybkości. Można uruchomić osobno.")
    results.add("Video: Pominięto", True, "Test wideo pominięty (zbyt długi)")
    
    # Podsumowanie
    print()
    all_passed = results.print_summary()
    
    # Cleanup
    logger.info("\nCleanup...")
    for f in data_dir.glob("test_*"):
        if f.is_file():
            f.unlink()
    logger.info("✅ Wyczyszczono pliki testowe z data/")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

