#!/usr/bin/env python3
"""
Skrypt diagnostyczny do testowania uploadu plikow przez GUI
Symuluje akcje uzytkownika i loguje wszystkie zdarzenia
"""

import sys
import time
import logging
from pathlib import Path

# Dodaj folder app do PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

# Konfiguracja logowania
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('diagnostic_upload.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def test_file_uploader_behavior():
    """Testuje zachowanie Streamlit file_uploader"""
    logger.info("=" * 60)
    logger.info("TEST: Zachowanie Streamlit file_uploader")
    logger.info("=" * 60)
    
    try:
        import streamlit as st
        
        logger.info("Streamlit zaimportowany")
        logger.info(f"Streamlit version: {st.__version__}")
        
        # Symulacja file_uploader
        logger.info("Symulacja: st.file_uploader()")
        logger.info("  - accept_multiple_files=True")
        logger.info("  - type=None")
        logger.info("  - key='file_uploader'")
        
        # Sprawdź session_state
        logger.info("Sprawdzam session_state...")
        if hasattr(st, 'session_state'):
            logger.info("  - session_state dostępne")
            logger.info(f"  - pending_uploaded_files: {st.session_state.get('pending_uploaded_files', 'BRAK')}")
            logger.info(f"  - file_uploader: {st.session_state.get('file_uploader', 'BRAK')}")
        else:
            logger.warning("  - session_state NIE dostępne (to normalne poza kontekstem Streamlit)")
        
    except Exception as e:
        logger.error(f"Błąd podczas testu: {e}", exc_info=True)

def test_path_resolution():
    """Testuje rozwiązywanie ścieżek"""
    logger.info("=" * 60)
    logger.info("TEST: Rozwiązywanie ścieżek")
    logger.info("=" * 60)
    
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    
    logger.info(f"PROJECT_ROOT: {PROJECT_ROOT}")
    logger.info(f"DATA_DIR: {DATA_DIR}")
    logger.info(f"DATA_DIR exists: {DATA_DIR.exists()}")
    logger.info(f"DATA_DIR is_dir: {DATA_DIR.is_dir()}")
    
    if DATA_DIR.exists():
        files = list(DATA_DIR.glob('*'))
        logger.info(f"Pliki w data/: {len(files)}")
        for f in files:
            logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

def test_session_state_simulation():
    """Symuluje session_state dla uploadu"""
    logger.info("=" * 60)
    logger.info("TEST: Symulacja session_state")
    logger.info("=" * 60)
    
    # Symulacja klasy UploadedFile
    class MockUploadedFile:
        def __init__(self, name, size):
            self.name = name
            self.size = size
        
        def getbuffer(self):
            return b"test content"
    
    mock_file = MockUploadedFile("test.pdf", 1024)
    
    logger.info(f"Mock file: {mock_file.name}, size: {mock_file.size}")
    logger.info(f"getbuffer() type: {type(mock_file.getbuffer())}")
    
    # Test zapisu
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    test_file = DATA_DIR / "diagnostic_test.txt"
    
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(test_file, 'wb') as f:
            f.write(mock_file.getbuffer())
        logger.info(f"Test zapisu: SUKCES - {test_file}")
        test_file.unlink()
        logger.info("Plik testowy usunięty")
    except Exception as e:
        logger.error(f"Test zapisu: BŁĄD - {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SKRYPT DIAGNOSTYCZNY: Upload plikow")
    logger.info("=" * 60)
    
    test_path_resolution()
    test_session_state_simulation()
    test_file_uploader_behavior()
    
    logger.info("=" * 60)
    logger.info("KONIEC TESTU")
    logger.info("=" * 60)

