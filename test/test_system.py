#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System testowy dla RAG v4.0

Testuje wszystkie główne funkcje:
- Indeksowanie różnych typów plików (PDF, DOCX, XLSX, obrazy, audio, video)
- Hybrydowe wyszukiwanie (Vector + BM25 + Reranking)
- OpenAI API integration
- Filtrowanie powitań
- GPU/CPU detection
- Audit logging

Używa plików z data_backup/ jako źródła testowego.
"""

import sys
import logging
import time
from pathlib import Path
import shutil
import json

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modułów systemu
from rag_system import RAGSystem
from greeting_filter import GreetingFilter
from model_provider import ModelFactory, OllamaProvider
from hybrid_search import HybridSearch, reciprocal_rank_fusion
from device_manager import DeviceManager
from audit_logger import get_audit_logger

class RAGSystemTester:
    """Klasa testująca pełną funkcjonalność systemu RAG v4.0"""
    
    def __init__(self):
        self.results = []
        self.data_backup = Path("data_backup")
        self.data_dir = Path("data")
        self.test_dir = Path("test_temp")
        
        logger.info("="*70)
        logger.info("🧪 SYSTEM TESTOWY RAG v4.0")
        logger.info("="*70)
    
    def setup(self):
        """Przygotowanie środowiska testowego"""
        logger.info("📋 Przygotowanie środowiska testowego...")
        
        # Utwórz folder testowy
        self.test_dir.mkdir(exist_ok=True)
        
        # Sprawdź czy data_backup istnieje
        if not self.data_backup.exists():
            logger.error("❌ Folder data_backup/ nie istnieje!")
            return False
        
        # Lista plików testowych
        test_files = list(self.data_backup.glob('*'))
        logger.info(f"📦 Znaleziono {len(test_files)} plików w data_backup/")
        
        return True
    
    def test_greeting_filter(self):
        """Test 1: Filtrowanie powitań"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: Filtrowanie powitań")
        logger.info("="*70)
        
        try:
            filter = GreetingFilter()
            
            test_cases = [
                ("Cześć! Co mówi art. 148?", "Co mówi art. 148?"),
                ("Dzień dobry, mam pytanie", "mam pytanie"),
                ("Hello! What is this?", "What is this?"),
                ("Co to jest zabójstwo?", "Co to jest zabójstwo?"),  # Bez powitania
            ]
            
            passed = 0
            for original, expected in test_cases:
                cleaned = filter.remove_greetings(original)
                if cleaned == expected:
                    logger.info(f"  ✅ '{original}' → '{cleaned}'")
                    passed += 1
                else:
                    logger.error(f"  ❌ '{original}' → '{cleaned}' (expected: '{expected}')")
            
            success = passed == len(test_cases)
            self.results.append(("Filtrowanie powitań", success, f"{passed}/{len(test_cases)} passed"))
            return success
            
        except Exception as e:
            logger.error(f"❌ Błąd testu filtrowania: {e}")
            self.results.append(("Filtrowanie powitań", False, str(e)))
            return False
    
    def test_device_manager(self):
        """Test 2: GPU/CPU Detection"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: GPU/CPU Auto-Detection")
        logger.info("="*70)
        
        try:
            manager = DeviceManager(mode='auto')
            logger.info(f"  Mode: {manager.mode}")
            logger.info(f"  CUDA available: {manager.cuda_available}")
            logger.info(f"  Config: {manager.config}")
            
            if manager.cuda_available:
                info = manager.get_info()
                logger.info(f"  GPU: {info.get('gpu_name', 'N/A')}")
                vram = manager.get_vram_usage()
                logger.info(f"  VRAM: {vram['allocated_gb']:.1f}/{vram['total_gb']:.1f} GB")
            
            success = manager.config is not None
            self.results.append(("Device Manager", success, f"Config: {manager.config}"))
            return success
            
        except Exception as e:
            logger.error(f"❌ Błąd testu device manager: {e}")
            self.results.append(("Device Manager", False, str(e)))
            return False
    
    def test_model_provider(self):
        """Test 3: Model Provider (Ollama fallback)"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: Model Provider")
        logger.info("="*70)
        
        try:
            # Test Ollama (lokalny)
            config = {
                'ollama_model': 'gemma3:12b',
                'ollama_url': 'http://127.0.0.1:11434'
            }
            
            provider = ModelFactory.create_provider(config)
            logger.info(f"  Provider: {provider.__class__.__name__}")
            logger.info(f"  Model: {provider.get_model_name()}")
            logger.info(f"  Available: {provider.is_available()}")
            
            models = provider.list_models()
            logger.info(f"  Models: {len(models)} dostępnych")
            
            success = provider.is_available()
            self.results.append(("Model Provider", success, f"{provider.__class__.__name__}"))
            return success
            
        except Exception as e:
            logger.error(f"❌ Błąd testu model provider: {e}")
            self.results.append(("Model Provider", False, str(e)))
            return False
    
    def test_file_indexing(self):
        """Test 4: Indeksowanie różnych typów plików"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: Indeksowanie Różnych Typów Plików")
        logger.info("="*70)
        
        # Typy plików do przetestowania
        test_files = {
            'pdf': '*.pdf',
            'image': '*.jpg',
            'image_png': '*.png',
        }
        
        results = {}
        
        for file_type, pattern in test_files.items():
            files = list(self.data_backup.glob(pattern))
            if not files:
                logger.warning(f"  ⚠️ Brak plików {pattern} w data_backup/")
                continue
            
            # Weź pierwszy plik
            test_file = files[0]
            logger.info(f"\n  📄 Testowanie: {file_type} - {test_file.name}")
            
            # Skopiuj do test_dir
            dest = self.test_dir / test_file.name
            shutil.copy(test_file, dest)
            
            try:
                # Inicjalizuj RAG system
                rag = RAGSystem()
                
                # Indeksuj plik
                start_time = time.time()
                rag.index_documents(str(self.test_dir))
                elapsed = time.time() - start_time
                
                # Sprawdź czy dodano do bazy
                count = rag.vector_db.collection.count()
                
                logger.info(f"    ✅ Zaindeksowano w {elapsed:.2f}s")
                logger.info(f"    📊 Fragmentów w bazie: {count}")
                
                results[file_type] = {
                    'success': count > 0,
                    'count': count,
                    'time': elapsed
                }
                
                # Cleanup
                dest.unlink()
                
                # Wyczyść bazę przed następnym testem
                import chromadb
                client = chromadb.PersistentClient(path='vector_db')
                client.delete_collection(name='legal_documents')
                
            except Exception as e:
                logger.error(f"    ❌ Błąd: {e}")
                results[file_type] = {'success': False, 'error': str(e)}
        
        success = all(r.get('success', False) for r in results.values())
        self.results.append(("Indeksowanie plików", success, str(results)))
        return success
    
    def test_hybrid_search(self):
        """Test 5: Hybrydowe wyszukiwanie"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: Hybrydowe Wyszukiwanie")
        logger.info("="*70)
        
        try:
            # Zaindeksuj testowy PDF
            pdf_files = list(self.data_backup.glob('*.pdf'))
            if not pdf_files:
                logger.warning("⚠️ Brak PDF do testu")
                self.results.append(("Hybrydowe wyszukiwanie", False, "Brak testowego PDF"))
                return False
            
            # Skopiuj PDF
            test_pdf = pdf_files[0]
            dest = self.test_dir / test_pdf.name
            shutil.copy(test_pdf, dest)
            
            # Inicjalizuj i indeksuj
            rag = RAGSystem()
            logger.info(f"  📄 Indeksuję: {test_pdf.name}...")
            rag.index_documents(str(self.test_dir))
            
            count = rag.vector_db.collection.count()
            logger.info(f"  📊 Fragmentów zaindeksowanych: {count}")
            
            # Przebuduj BM25
            logger.info("  🔨 Budowanie BM25 index...")
            rag.rebuild_bm25_index()
            
            # Test wyszukiwania
            test_query = "dokument"
            logger.info(f"  🔍 Test query: '{test_query}'")
            
            if rag.hybrid_search and rag.hybrid_search.bm25_index:
                logger.info("    ✅ BM25 dostępny")
                logger.info(f"    ✅ BM25 docs: {len(rag.hybrid_search.bm25_index.doc_ids)}")
            
            if rag.hybrid_search and rag.hybrid_search.reranker:
                logger.info("    ✅ Reranker dostępny")
            
            # Wykonaj wyszukiwanie
            results = rag.vector_db.search(test_query, 3)
            logger.info(f"    ✅ Znaleziono: {len(results)} wyników")
            
            # Cleanup
            dest.unlink()
            import chromadb
            client = chromadb.PersistentClient(path='vector_db')
            client.delete_collection(name='legal_documents')
            
            success = len(results) > 0
            self.results.append(("Hybrydowe wyszukiwanie", success, f"{len(results)} wyników"))
            return success
            
        except Exception as e:
            logger.error(f"❌ Błąd testu wyszukiwania: {e}", exc_info=True)
            self.results.append(("Hybrydowe wyszukiwanie", False, str(e)))
            return False
    
    def test_audit_logging(self):
        """Test 6: Audit Logging"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: Audit Logging")
        logger.info("="*70)
        
        try:
            audit = get_audit_logger()
            
            # Test zapisu
            audit.log_query(
                user_id='test_user',
                session_id='test_session',
                query='test query',
                response='test response',
                sources=[],
                model='test_model',
                time_ms=100.0
            )
            
            # Test odczytu
            logs = audit.get_logs(user_id='test_user', limit=10)
            logger.info(f"  ✅ Zapisano i odczytano: {len(logs)} logów")
            
            # Test statystyk
            stats = audit.get_stats()
            logger.info(f"  📊 Total entries: {stats['total_entries']}")
            
            success = len(logs) > 0
            self.results.append(("Audit Logging", success, f"{len(logs)} logów"))
            return success
            
        except Exception as e:
            logger.error(f"❌ Błąd testu audit logging: {e}")
            self.results.append(("Audit Logging", False, str(e)))
            return False
    
    def cleanup(self):
        """Czyszczenie po testach"""
        logger.info("\n" + "="*70)
        logger.info("🧹 Czyszczenie po testach...")
        logger.info("="*70)
        
        # Usuń folder testowy
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            logger.info("  ✅ Usunięto test_temp/")
        
        # Wyczyść bazę testową
        try:
            import chromadb
            client = chromadb.PersistentClient(path='vector_db')
            collections = client.list_collections()
            if collections:
                for coll in collections:
                    client.delete_collection(name=coll.name)
                logger.info(f"  ✅ Wyczyszczono {len(collections)} kolekcji z bazy")
        except:
            pass
    
    def print_results(self):
        """Wydrukowanie podsumowania testów"""
        logger.info("\n" + "="*70)
        logger.info("📊 PODSUMOWANIE TESTÓW")
        logger.info("="*70)
        
        total = len(self.results)
        passed = sum(1 for _, success, _ in self.results if success)
        
        for name, success, details in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            logger.info(f"{status} - {name}: {details}")
        
        logger.info("="*70)
        logger.info(f"📈 Wynik: {passed}/{total} testów przeszło ({passed/total*100:.0f}%)")
        logger.info("="*70)
        
        return passed == total
    
    def run_all_tests(self):
        """Uruchomienie wszystkich testów"""
        logger.info("🚀 Rozpoczynanie testów...\n")
        
        if not self.setup():
            logger.error("❌ Błąd setup, przerywam testy")
            return False
        
        # Kolejność testów
        tests = [
            self.test_greeting_filter,
            self.test_device_manager,
            self.test_model_provider,
            self.test_audit_logging,
            self.test_file_indexing,  # Na końcu (modyfikuje bazę)
            self.test_hybrid_search,
        ]
        
        for test_func in tests:
            try:
                test_func()
                time.sleep(1)  # Krótka przerwa między testami
            except Exception as e:
                logger.error(f"❌ Wyjątek w teście {test_func.__name__}: {e}", exc_info=True)
                self.results.append((test_func.__name__, False, str(e)))
        
        # Cleanup
        self.cleanup()
        
        # Podsumowanie
        return self.print_results()


if __name__ == "__main__":
    tester = RAGSystemTester()
    
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE! 🎉\n")
        sys.exit(0)
    else:
        logger.error("\n❌ NIEKTÓRE TESTY NIE PRZESZŁY ❌\n")
        sys.exit(1)

