#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt inicjalizacyjny - pobiera wszystkie modele AI przed uruchomieniem aplikacji.
Weryfikuje dostępność modeli i pobiera je jeśli nie istnieją.
"""

import os
import sys
from pathlib import Path
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Konfiguracja ścieżek
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
WHISPER_MODELS_DIR = MODELS_DIR / "whisper"
EMBEDDING_MODELS_DIR = MODELS_DIR / "embeddings"
RERANKER_MODELS_DIR = MODELS_DIR / "reranker"

# Tworzenie katalogów
for directory in [MODELS_DIR, WHISPER_MODELS_DIR, EMBEDDING_MODELS_DIR, RERANKER_MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

def check_whisper_model(model_name: str = "base") -> bool:
    """Sprawdza czy model Whisper jest pobrany"""
    model_file = WHISPER_MODELS_DIR / f"{model_name}.pt"
    return model_file.exists()

def download_whisper_model(model_name: str = "base") -> bool:
    """Pobiera model Whisper"""
    try:
        logger.info(f"Pobieranie modelu Whisper: {model_name}...")
        import whisper
        whisper.load_model(model_name, download_root=str(WHISPER_MODELS_DIR))
        logger.info(f"✅ Model Whisper {model_name} pobrany pomyślnie")
        return True
    except Exception as e:
        logger.error(f"❌ Błąd podczas pobierania Whisper {model_name}: {e}")
        return False

def check_embedding_model(model_name: str = "intfloat/multilingual-e5-large") -> bool:
    """Sprawdza czy model embeddingów jest pobrany"""
    # Sprawdź czy katalog modelu istnieje
    model_path = EMBEDDING_MODELS_DIR / f"models--{model_name.replace('/', '--')}"
    return model_path.exists()

def download_embedding_model(model_name: str = "intfloat/multilingual-e5-large") -> bool:
    """Pobiera model embeddingów"""
    try:
        logger.info(f"Pobieranie modelu embeddingów: {model_name}...")
        from sentence_transformers import SentenceTransformer
        
        # Pobierz model do naszego katalogu
        model = SentenceTransformer(
            model_name,
            device='cpu',  # CPU dla pobierania (szybsze)
            cache_folder=str(EMBEDDING_MODELS_DIR)
        )
        
        logger.info(f"✅ Model embeddingów {model_name} pobrany pomyślnie")
        return True
    except Exception as e:
        logger.error(f"❌ Błąd podczas pobierania embeddings {model_name}: {e}")
        return False

def check_reranker_model(model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2") -> bool:
    """Sprawdza czy model rerankera jest pobrany"""
    model_path = RERANKER_MODELS_DIR / f"models--{model_name.replace('/', '--')}"
    return model_path.exists()

def download_reranker_model(model_name: str = "cross-encoder/ms-marco-MiniLM-L-12-v2") -> bool:
    """Pobiera model rerankera"""
    try:
        logger.info(f"Pobieranie modelu rerankera: {model_name}...")
        from sentence_transformers import CrossEncoder
        import shutil
        
        # CrossEncoder w sentence-transformers 3.0.0 używa zawsze ~/.cache/huggingface
        # Pobieramy tam, potem kopiujemy do naszego katalogu
        default_cache = Path.home() / ".cache" / "huggingface" / "hub"
        model_cache_name = f"models--{model_name.replace('/', '--')}"
        
        model = CrossEncoder(model_name, device='cpu')
        
        # Skopiuj z ~/.cache do models/reranker
        source_path = default_cache / model_cache_name
        target_path = RERANKER_MODELS_DIR / model_cache_name
        
        if source_path.exists() and not target_path.exists():
            logger.info(f"Kopiowanie modelu z {source_path} do {target_path}...")
            shutil.copytree(source_path, target_path)
            logger.info(f"✅ Model skopiowany do {target_path}")
        
        logger.info(f"✅ Model rerankera {model_name} pobrany pomyślnie")
        return True
    except Exception as e:
        logger.error(f"❌ Błąd podczas pobierania reranker {model_name}: {e}")
        return False

def init_all_models():
    """Inicjalizuje wszystkie modele"""
    logger.info("="*70)
    logger.info("INICJALIZACJA MODELI AI")
    logger.info("="*70)
    
    success = True
    
    # 1. Whisper (dla audio/wideo)
    logger.info("\n[1/3] Sprawdzanie modelu Whisper...")
    whisper_model = "base"  # Można zmienić na "large-v3" jeśli potrzebne
    
    if check_whisper_model(whisper_model):
        logger.info(f"✅ Model Whisper {whisper_model} już istnieje")
    else:
        logger.info(f"⚠️  Model Whisper {whisper_model} nie znaleziony, rozpoczynam pobieranie...")
        if not download_whisper_model(whisper_model):
            success = False
    
    # 2. Embeddings (dla wyszukiwania semantycznego)
    logger.info("\n[2/3] Sprawdzanie modelu embeddingów...")
    embedding_model = "intfloat/multilingual-e5-large"
    
    if check_embedding_model(embedding_model):
        logger.info(f"✅ Model embeddingów już istnieje")
    else:
        logger.info(f"⚠️  Model embeddingów nie znaleziony, rozpoczynam pobieranie...")
        if not download_embedding_model(embedding_model):
            success = False
    
    # 3. Reranker (dla dokładniejszego wyszukiwania)
    logger.info("\n[3/3] Sprawdzanie modelu rerankera...")
    reranker_model = "cross-encoder/ms-marco-MiniLM-L-12-v2"
    
    if check_reranker_model(reranker_model):
        logger.info(f"✅ Model rerankera już istnieje")
    else:
        logger.info(f"⚠️  Model rerankera nie znaleziony, rozpoczynam pobieranie...")
        if not download_reranker_model(reranker_model):
            success = False
    
    # Podsumowanie
    logger.info("\n" + "="*70)
    if success:
        logger.info("✅ WSZYSTKIE MODELE GOTOWE")
        logger.info("="*70)
        return 0
    else:
        logger.error("❌ NIEKTÓRE MODELE NIE ZOSTAŁY POBRANE")
        logger.info("="*70)
        return 1

if __name__ == "__main__":
    sys.exit(init_all_models())

