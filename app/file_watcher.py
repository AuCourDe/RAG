#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watchdog - automatyczne monitorowanie folderu data/ i indeksowanie nowych plików
"""

import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rag_system import DocumentProcessor, EmbeddingProcessor, VectorDatabase, RAGSystem, add_questions_for_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('file_watcher.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DocumentWatcher(FileSystemEventHandler):
    """Handler dla nowych plików w folderze data/"""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.embedding_processor = EmbeddingProcessor()
        self.vector_db = VectorDatabase()
        self.rag_system = RAGSystem()
        self.processing = False
        self.file_queue = []  # Kolejka plików do przetworzenia
        logger.info("✅ DocumentWatcher zainicjalizowany")
    
    def on_created(self, event):
        """Wywoływane gdy nowy plik został utworzony"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Sprawdź czy to obsługiwany format
        supported_formats = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.mp4', '.avi', '.mov', '.mkv', '.webm'}
        if file_path.suffix.lower() not in supported_formats:
            logger.debug(f"Pominięto plik (nieobsługiwany format): {file_path}")
            return
        
        # Poczekaj aż plik będzie w pełni zapisany
        time.sleep(2)
        
        # Dodaj do kolejki zamiast pomijać
        if file_path not in self.file_queue:
            self.file_queue.append(file_path)
            logger.info(f"🔍 Wykryto nowy plik (dodano do kolejki): {file_path.name}")
        
        # Jeśli nie przetwarzamy, rozpocznij
        if not self.processing:
            self.process_queue()
    
    def process_queue(self):
        """Przetwarza pliki z kolejki jeden po drugim"""
        while self.file_queue and not self.processing:
            file_path = self.file_queue.pop(0)
            logger.info(f"📥 Przetwarzam z kolejki ({len(self.file_queue)} pozostało): {file_path.name}")
            self.process_new_file(file_path)
    
    def process_new_file(self, file_path: Path):
        """Przetwarza i indeksuje nowy plik"""
        self.processing = True
        
        try:
            logger.info(f"📄 Rozpoczynanie przetwarzania: {file_path.name}")
            start_time = time.time()
            
            # Sprawdź czy plik już został dodany do bazy
            existing = self.vector_db.collection.get(where={"source_file": file_path.name})
            if existing and existing.get('ids'):
                logger.info(f"⏭️ Plik {file_path.name} już istnieje w bazie – pomijam automatyczne indeksowanie")
                return
            
            # Przetwórz plik
            chunks = self.doc_processor.process_file(file_path)
            
            if not chunks:
                logger.warning(f"⚠️ Brak fragmentów z pliku: {file_path.name}")
                return
            
            logger.info(f"📝 Znaleziono {len(chunks)} fragmentów")
            
            # Utwórz embeddingi
            logger.info("🔄 Tworzenie embeddingów...")
            chunks_with_embeddings = self.embedding_processor.create_embeddings(chunks)
            
            # Dodaj do bazy
            logger.info("💾 Dodawanie do bazy wektorowej...")
            self.vector_db.add_documents(chunks_with_embeddings)
            
            processing_time = time.time() - start_time
            logger.info(f"✅ Zakończono indeksowanie {file_path.name} w {processing_time:.2f} sekund")
            logger.info(f"   Dodano {len(chunks)} fragmentów do bazy")
            
            # Przebuduj BM25 index (dla hybrydowego wyszukiwania)
            logger.info("🔨 Przebudowywanie BM25 index...")
            try:
                self.rag_system.rebuild_bm25_index()
                logger.info("✅ BM25 index przebudowany")
            except Exception as e:
                logger.warning(f"⚠️ Błąd podczas przebudowy BM25 index: {e}")
            
            # Generuj pytania dla nowego pliku
            logger.info("🤔 Generowanie przykładowych pytań...")
            try:
                add_questions_for_file(file_path.name, self.rag_system, max_questions=3)
                logger.info("✅ Pytania wygenerowane i zapisane")
            except Exception as e:
                logger.error(f"⚠️ Błąd podczas generowania pytań: {e}")
            
        except Exception as e:
            logger.error(f"❌ Błąd podczas przetwarzania {file_path}: {e}", exc_info=True)
        finally:
            self.processing = False
            # Przetwórz następne pliki z kolejki
            if self.file_queue:
                logger.info(f"📋 Kolejka: {len(self.file_queue)} plików czeka na przetworzenie")
                self.process_queue()

def start_watcher(directory: str = "data"):
    """Uruchamia watchdog monitorujący folder"""
    logger.info("="*70)
    logger.info("🔍 WATCHDOG - Automatyczne indeksowanie nowych plików")
    logger.info("="*70)
    logger.info(f"📁 Monitorowany folder: {directory}")
    logger.info(f"📊 Obsługiwane formaty: PDF, DOCX, XLSX, JPG, PNG, BMP, MP3, WAV, FLAC, OGG, MP4, AVI, MOV, MKV, WEBM")
    logger.info("="*70)
    
    path = Path(directory)
    if not path.exists():
        logger.error(f"❌ Folder {directory} nie istnieje!")
        return
    
    # NOWE: Sprawdź czy są już pliki w folderze i zaindeksuj je
    event_handler = DocumentWatcher()
    
    logger.info("🔍 Sprawdzam istniejące pliki w folderze...")
    existing_files = []
    supported_formats = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', 
                        '.mp3', '.wav', '.flac', '.ogg', '.m4a',
                        '.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    for file_path in path.glob('*'):
        if file_path.is_file() and file_path.suffix.lower() in supported_formats:
            existing_files.append(file_path)
    
    if existing_files:
        logger.info(f"📦 Znaleziono {len(existing_files)} istniejących plików do indeksacji")
        for file_path in existing_files:
            logger.info(f"   📄 {file_path.name}")
        
        # Indeksuj istniejące pliki
        logger.info("🚀 Indeksuję istniejące pliki...")
        for file_path in existing_files:
            try:
                event_handler.process_new_file(file_path)
                logger.info(f"   ✅ {file_path.name} - zaindeksowany")
            except Exception as e:
                logger.error(f"   ❌ {file_path.name} - błąd: {e}")
        
        logger.info(f"✅ Indeksacja istniejących plików zakończona!")
    else:
        logger.info("📭 Brak istniejących plików do indeksacji")
    
    observer = Observer()
    observer.schedule(event_handler, str(path), recursive=True)
    observer.start()
    
    logger.info("✅ Watchdog uruchomiony - monitoruję folder...")
    logger.info("💡 Dodaj nowy plik do folderu 'data/' aby go automatycznie zindeksować")
    logger.info("⏹️  Naciśnij Ctrl+C aby zatrzymać")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Zatrzymywanie watchdog...")
        observer.stop()
    
    observer.join()
    logger.info("✅ Watchdog zatrzymany")

if __name__ == "__main__":
    start_watcher()


