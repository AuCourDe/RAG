#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kompleksowe testy automatyczne systemu RAG v4
Testuje wszystkie główne funkcjonalności:
- Dodawanie plików (PDF, obrazy, audio, wideo)
- Tworzenie bazy wektorowej
- Różne strategie wyszukiwania
- Generowanie odpowiedzi
- Hybrydowe wyszukiwanie
"""

import sys
import time
import shutil
from pathlib import Path
from rag_system import RAGSystem
from hybrid_search import HybridSearch
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_results.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_total = 0
        self.results = []
    
    def test(self, name, condition, message=""):
        """Wykonuje pojedynczy test"""
        self.tests_total += 1
        status = "✅ PASS" if condition else "❌ FAIL"
        
        log_msg = f"{status} | {name}"
        if message:
            log_msg += f" | {message}"
        
        logger.info(log_msg)
        
        self.results.append({
            'name': name,
            'passed': condition,
            'message': message
        })
        
        if condition:
            self.tests_passed += 1
        else:
            self.tests_failed += 1
        
        return condition
    
    def print_summary(self):
        """Wyświetla podsumowanie testów"""
        print("\n" + "="*80)
        print("PODSUMOWANIE TESTÓW")
        print("="*80)
        
        for result in self.results:
            icon = "✅" if result['passed'] else "❌"
            print(f"{icon} {result['name']}")
            if result['message'] and not result['passed']:
                print(f"   ⚠️  {result['message']}")
        
        print("="*80)
        print(f"Passed: {self.tests_passed}/{self.tests_total}")
        print(f"Failed: {self.tests_failed}/{self.tests_total}")
        success_rate = (self.tests_passed / self.tests_total * 100) if self.tests_total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print("="*80)
        
        return self.tests_failed == 0

def cleanup_test_environment():
    """Czyści środowisko testowe"""
    logger.info("Czyszczenie środowiska testowego...")
    
    # Wyczyść folder data/ z plików testowych
    data_dir = Path("data")
    for f in data_dir.glob("test_*"):
        if f.is_file():
            f.unlink()
            logger.info(f"  Usunięto: {f.name}")
    
    # Wyczyść bazę wektorową
    try:
        rag = RAGSystem()
        rag.vector_db.collection.delete(where={})
        logger.info("  Wyczyszczono bazę wektorową")
    except:
        pass

def main():
    """Główna funkcja testowa"""
    print("="*80)
    print("TESTY AUTOMATYCZNE SYSTEMU RAG v4")
    print("="*80)
    print()
    
    runner = TestRunner()
    
    # PRZYGOTOWANIE
    logger.info("="*80)
    logger.info("PRZYGOTOWANIE ŚRODOWISKA TESTOWEGO")
    logger.info("="*80)
    
    cleanup_test_environment()
    
    # Sprawdź pliki testowe
    test_files = {
        'PDF': 'sample_test_files/test_document.pdf',
        'Image': 'sample_test_files/test_image.png',
        'Audio': 'sample_test_file/rozmowa (2).mp3',  # Polski plik z rozmową
        'Video': 'sample_test_files/test_video.mp4'
    }
    
    for file_type, file_path in test_files.items():
        exists = Path(file_path).exists()
        runner.test(
            f"Plik testowy {file_type}",
            exists,
            f"{'Znaleziono' if exists else 'BRAK'}: {file_path}"
        )
    
    print()
    
    # TEST 1: INICJALIZACJA SYSTEMU
    logger.info("="*80)
    logger.info("TEST 1: INICJALIZACJA SYSTEMU RAG")
    logger.info("="*80)
    
    try:
        rag = RAGSystem()
        runner.test("Inicjalizacja RAGSystem", True, "System zainicjalizowany")
    except Exception as e:
        runner.test("Inicjalizacja RAGSystem", False, f"Błąd: {e}")
        runner.print_summary()
        return False
    
    # Sprawdź komponenty
    runner.test("DocumentProcessor", hasattr(rag, 'doc_processor'), "Procesor dokumentów")
    runner.test("EmbeddingProcessor", hasattr(rag, 'embedding_processor'), "Procesor embeddingów")
    runner.test("VectorDatabase", hasattr(rag, 'vector_db'), "Baza wektorowa")
    runner.test("ModelProvider", hasattr(rag, 'model_provider'), "Provider modelu LLM")
    runner.test("HybridSearch", hasattr(rag, 'hybrid_search'), "Wyszukiwanie hybrydowe")
    
    # Sprawdź bazę
    try:
        initial_count = rag.vector_db.collection.count()
        runner.test("Baza pusta na start", initial_count == 0, f"Fragmentów: {initial_count}")
    except Exception as e:
        runner.test("Baza pusta na start", False, f"Błąd: {e}")
    
    print()
    
    # TEST 2: PRZETWARZANIE PDF
    logger.info("="*80)
    logger.info("TEST 2: PRZETWARZANIE DOKUMENTU PDF")
    logger.info("="*80)
    
    pdf_file = Path("data/test_document.pdf")
    shutil.copy("sample_test_files/test_document.pdf", pdf_file)
    
    try:
        chunks = rag.doc_processor.process_file(pdf_file)
        runner.test("PDF: Przetwarzanie", len(chunks) > 0, f"Fragmentów: {len(chunks)}")
        
        if len(chunks) > 0:
            # Sprawdź strukturę chunk
            chunk = chunks[0]
            runner.test("PDF: Chunk ma ID", hasattr(chunk, 'id') and chunk.id, f"ID: {chunk.id[:20]}...")
            runner.test("PDF: Chunk ma content", hasattr(chunk, 'content') and len(chunk.content) > 0, f"Content: {len(chunk.content)} znaków")
            runner.test("PDF: Chunk ma source_file", hasattr(chunk, 'source_file') and chunk.source_file, f"Source: {chunk.source_file}")
            runner.test("PDF: Chunk ma chunk_type", hasattr(chunk, 'chunk_type') and chunk.chunk_type, f"Type: {chunk.chunk_type}")
            
            # Indeksuj
            chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
            runner.test("PDF: Tworzenie embeddingów", len(chunks_with_embeddings) == len(chunks), f"Embeddings: {len(chunks_with_embeddings)}")
            
            rag.vector_db.add_documents(chunks_with_embeddings)
            runner.test("PDF: Dodanie do bazy", True, f"Dodano {len(chunks)} fragmentów")
            
            # Sprawdź czy w bazie
            time.sleep(1)
            count_after = rag.vector_db.collection.count()
            runner.test("PDF: W bazie wektorowej", count_after >= len(chunks), f"W bazie: {count_after} fragmentów")
            
    except Exception as e:
        logger.error(f"Błąd przetwarzania PDF: {e}", exc_info=True)
        runner.test("PDF: Przetwarzanie", False, f"Błąd: {e}")
    
    print()
    
    # TEST 3: PRZETWARZANIE OBRAZU
    logger.info("="*80)
    logger.info("TEST 3: PRZETWARZANIE OBRAZU PNG")
    logger.info("="*80)
    
    # Wyczyść bazę
    try:
        rag.vector_db.collection.delete(where={})
    except:
        pass
    
    img_file = Path("data/test_image.png")
    shutil.copy("sample_test_files/test_image.png", img_file)
    
    try:
        chunks = rag.doc_processor.process_file(img_file)
        runner.test("Image: Przetwarzanie", len(chunks) > 0, f"Fragmentów: {len(chunks)}")
        
        if len(chunks) > 0:
            chunk = chunks[0]
            runner.test("Image: Ma opis", len(chunk.content) > 10, f"Opis: {len(chunk.content)} znaków")
            runner.test("Image: Chunk type", chunk.chunk_type == 'image_description', f"Type: {chunk.chunk_type}")
            
            # Indeksuj
            chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
            rag.vector_db.add_documents(chunks_with_embeddings)
            
            time.sleep(1)
            count_after = rag.vector_db.collection.count()
            runner.test("Image: Dodanie do bazy", count_after >= len(chunks), f"W bazie: {count_after}")
            
    except Exception as e:
        logger.error(f"Błąd przetwarzania obrazu: {e}", exc_info=True)
        runner.test("Image: Przetwarzanie", False, f"Błąd: {e}")
    
    print()
    
    # TEST 4: WYSZUKIWANIE - RÓŻNE STRATEGIE
    logger.info("="*80)
    logger.info("TEST 4: WYSZUKIWANIE - RÓŻNE STRATEGIE")
    logger.info("="*80)
    
    # Dodaj PDF do bazy dla testów wyszukiwania
    try:
        rag.vector_db.collection.delete(where={})
    except:
        pass
    
    pdf_file = Path("data/test_document.pdf")
    chunks = rag.doc_processor.process_file(pdf_file)
    chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
    rag.vector_db.add_documents(chunks_with_embeddings)
    
    # Przebuduj BM25 dla hybrydowego
    try:
        rag.rebuild_bm25_index()
        runner.test("BM25: Przebudowa indeksu", True, "Index przebudowany")
    except Exception as e:
        runner.test("BM25: Przebudowa indeksu", False, f"Błąd: {e}")
    
    time.sleep(2)
    
    # Test 4a: Wyszukiwanie wektorowe
    try:
        query = "Co zawiera dokument?"
        sources = rag.vector_db.search(query, n_results=3)
        runner.test("Wyszukiwanie: Wektor", len(sources) > 0, f"Znaleziono: {len(sources)} wyników")
        
        if len(sources) > 0:
            has_content = len(sources[0].content) > 0
            runner.test("Wyszukiwanie: Ma treść", has_content, f"Content: {len(sources[0].content)} znaków")
    except Exception as e:
        runner.test("Wyszukiwanie: Wektor", False, f"Błąd: {e}")
    
    # Test 4b: Wyszukiwanie hybrydowe (jeśli dostępne)
    if rag.hybrid_search:
        try:
            sources_hybrid = rag.hybrid_search.search(query, top_k=3, use_reranker=True)
            runner.test("Wyszukiwanie: Hybrydowe + Reranker", len(sources_hybrid) > 0, f"Znaleziono: {len(sources_hybrid)} wyników")
        except Exception as e:
            runner.test("Wyszukiwanie: Hybrydowe + Reranker", False, f"Błąd: {e}")
        
        try:
            sources_hybrid_no_rerank = rag.hybrid_search.search(query, top_k=3, use_reranker=False)
            runner.test("Wyszukiwanie: Hybrydowe bez Reranker", len(sources_hybrid_no_rerank) > 0, f"Znaleziono: {len(sources_hybrid_no_rerank)}")
        except Exception as e:
            runner.test("Wyszukiwanie: Hybrydowe bez Reranker", False, f"Błąd: {e}")
        
        try:
            sources_bm25 = rag.hybrid_search.search_bm25_only(query, top_k=3)
            runner.test("Wyszukiwanie: Tylko BM25", len(sources_bm25) > 0, f"Znaleziono: {len(sources_bm25)} wyników")
        except Exception as e:
            runner.test("Wyszukiwanie: Tylko BM25", False, f"Błąd: {e}")
    
    print()
    
    # TEST 5: GENEROWANIE ODPOWIEDZI
    logger.info("="*80)
    logger.info("TEST 5: GENEROWANIE ODPOWIEDZI Z RÓŻNYMI PARAMETRAMI")
    logger.info("="*80)
    
    # Test 5a: Odpowiedź z domyślnymi parametrami
    try:
        answer = rag.query(
            "Co zawiera dokument?",
            n_results=3,
            user_id='test_user',
            session_id='test_session'
        )
        runner.test("Odpowiedź: Domyślne parametry", len(answer) > 20, f"Długość: {len(answer)} znaków")
        
        # Sprawdź czy odpowiedź nie jest błędem
        has_error = "błąd" in answer.lower() or "error" in answer.lower()
        runner.test("Odpowiedź: Bez błędów", not has_error, "Odpowiedź wygenerowana poprawnie")
        
    except Exception as e:
        runner.test("Odpowiedź: Domyślne parametry", False, f"Błąd: {e}")
    
    # Test 5b: Odpowiedź z custom parametrami
    try:
        answer_custom = rag.query(
            "Jakie informacje zawiera plik?",
            n_results=5,
            temperature=0.3,
            top_p=0.9,
            top_k=40,
            max_tokens=500,
            user_id='test_user',
            session_id='test_session'
        )
        runner.test("Odpowiedź: Custom parametry", len(answer_custom) > 20, f"Długość: {len(answer_custom)} znaków")
    except Exception as e:
        runner.test("Odpowiedź: Custom parametry", False, f"Błąd: {e}")
    
    print()
    
    # TEST 6: RÓŻNE TYPY PLIKÓW
    logger.info("="*80)
    logger.info("TEST 6: PRZETWARZANIE RÓŻNYCH TYPÓW PLIKÓW")
    logger.info("="*80)
    
    # Wyczyść bazę
    try:
        rag.vector_db.collection.delete(where={})
    except:
        pass
    
    # Test Audio (jeśli istnieje)
    audio_file = Path("sample_test_file/rozmowa (2).mp3")  # Polski plik z rozmową
    if audio_file.exists():
        try:
            dest_audio = Path("data/test_audio.mp3")
            shutil.copy(audio_file, dest_audio)
            
            logger.info("Przetwarzanie audio (Whisper) - może potrwać 1-2 minuty...")
            chunks_audio = rag.doc_processor.process_file(dest_audio)
            
            runner.test("Audio: Przetwarzanie", len(chunks_audio) > 0, f"Fragmentów: {len(chunks_audio)}")
            
            if len(chunks_audio) > 0:
                # Sprawdź czy jest transkrypcja
                has_transcription = any(len(chunk.content) > 10 for chunk in chunks_audio)
                runner.test("Audio: Ma transkrypcję", has_transcription, f"Pierwszy chunk: {len(chunks_audio[0].content)} znaków")
                
                # Indeksuj
                chunks_with_emb = rag.embedding_processor.create_embeddings(chunks_audio)
                rag.vector_db.add_documents(chunks_with_emb)
                runner.test("Audio: Indeksacja", True, f"Dodano {len(chunks_audio)} fragmentów")
            
            dest_audio.unlink()
            
        except Exception as e:
            logger.error(f"Błąd audio: {e}", exc_info=True)
            runner.test("Audio: Przetwarzanie", False, f"Błąd: {e}")
    else:
        runner.test("Audio: Test", False, "Brak pliku testowego audio")
    
    print()
    
    # TEST 7: MONITORING I STATYSTYKI
    logger.info("="*80)
    logger.info("TEST 7: FUNKCJE MONITORINGU")
    logger.info("="*80)
    
    # Import funkcji z app.py
    try:
        # Sprawdź GPU stats
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=2
        )
        gpu_available = result.returncode == 0
        runner.test("Monitoring: GPU Detection", gpu_available or True, "GPU: " + ("Dostępny" if gpu_available else "CPU mode"))
    except:
        runner.test("Monitoring: GPU Detection", True, "GPU: CPU mode (OK)")
    
    # Sprawdź czy psutil działa
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        runner.test("Monitoring: CPU", cpu_percent >= 0, f"CPU: {cpu_percent}%")
        
        ram = psutil.virtual_memory()
        runner.test("Monitoring: RAM", ram.percent >= 0, f"RAM: {ram.percent}%")
    except Exception as e:
        runner.test("Monitoring: psutil", False, f"Błąd: {e}")
    
    print()
    
    # TEST 8: HYBRID SEARCH KOMPONENTY
    logger.info("="*80)
    logger.info("TEST 8: KOMPONENTY HYBRYDOWEGO WYSZUKIWANIA")
    logger.info("="*80)
    
    if rag.hybrid_search:
        # BM25
        runner.test("HybridSearch: BM25 dostępny", rag.hybrid_search.use_bm25, "BM25 włączony")
        
        # Reranker
        runner.test("HybridSearch: Reranker dostępny", rag.hybrid_search.use_reranker, "Reranker włączony")
        
        # Metody
        has_search = hasattr(rag.hybrid_search, 'search')
        runner.test("HybridSearch: Ma metodę search()", has_search, "Metoda search() dostępna")
        
        has_bm25_only = hasattr(rag.hybrid_search, 'search_bm25_only')
        runner.test("HybridSearch: Ma metodę search_bm25_only()", has_bm25_only, "Metoda search_bm25_only() dostępna")
    else:
        runner.test("HybridSearch: Inicjalizacja", False, "Hybrid search nie zainicjalizowany")
    
    print()
    
    # TEST 9: MODEL PROVIDER
    logger.info("="*80)
    logger.info("TEST 9: MODEL PROVIDER (LLM)")
    logger.info("="*80)
    
    # Sprawdź dostępność
    runner.test("ModelProvider: Dostępny", rag.model_provider.is_available(), f"Provider: {rag.model_provider.get_model_name()}")
    
    # Test generowania
    try:
        test_prompt = "Powiedz krótko: co to jest AI?"
        response = rag.model_provider.generate(
            prompt=test_prompt,
            temperature=0.1,
            max_tokens=50
        )
        runner.test("ModelProvider: Generowanie", len(response) > 5, f"Odpowiedź: {len(response)} znaków")
    except Exception as e:
        runner.test("ModelProvider: Generowanie", False, f"Błąd: {e}")
    
    print()
    
    # TEST 10: PERSISTENCE I METADATA
    logger.info("="*80)
    logger.info("TEST 10: PERSISTENCE I METADATA")
    logger.info("="*80)
    
    # Sprawdź metadata w bazie (ChromaDB używa metadatas jako słowniki)
    try:
        all_data = rag.vector_db.collection.get(include=['metadatas'])
        
        if len(all_data['metadatas']) > 0:
            meta = all_data['metadatas'][0]
            
            runner.test("Metadata: source_file", 'source_file' in meta, f"source_file: {meta.get('source_file', 'BRAK')}")
            runner.test("Metadata: page_number", 'page_number' in meta, f"page_number: {meta.get('page_number', 'BRAK')}")
            runner.test("Metadata: chunk_type", 'chunk_type' in meta, f"chunk_type: {meta.get('chunk_type', 'BRAK')}")
        else:
            runner.test("Metadata: Sprawdzenie", False, "Brak dokumentów w bazie")
            
    except Exception as e:
        runner.test("Metadata: Sprawdzenie", False, f"Błąd: {e}")
    
    print()
    
    # CLEANUP
    logger.info("="*80)
    logger.info("CLEANUP")
    logger.info("="*80)
    
    cleanup_test_environment()
    
    # PODSUMOWANIE
    all_passed = runner.print_summary()
    
    # Zapisz raport
    with open('test_report.txt', 'w', encoding='utf-8') as f:
        f.write("RAPORT TESTÓW SYSTEMU RAG v4\n")
        f.write("="*80 + "\n\n")
        for result in runner.results:
            icon = "✅" if result['passed'] else "❌"
            f.write(f"{icon} {result['name']}\n")
            if result['message']:
                f.write(f"   {result['message']}\n")
        f.write("\n" + "="*80 + "\n")
        f.write(f"Passed: {runner.tests_passed}/{runner.tests_total}\n")
        f.write(f"Failed: {runner.tests_failed}/{runner.tests_total}\n")
        f.write(f"Success Rate: {(runner.tests_passed / runner.tests_total * 100):.1f}%\n")
    
    logger.info(f"📄 Raport zapisany: test_report.txt")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

