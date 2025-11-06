#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Device Manager - zarządzanie urządzeniami (GPU/CPU) dla różnych komponentów systemu.

Obsługuje:
- Auto-detection GPU/CPU
- Manual override (gpu, cpu, hybrid modes)
- Per-component device assignment (embeddings, llm, reranker)
- VRAM monitoring i optymalizacja
"""

import logging
from typing import Dict, Any
import warnings

logger = logging.getLogger(__name__)

# Lazy import torch (nie wszędzie zainstalowany)
_torch_available = False
try:
    import torch
    _torch_available = True
except ImportError:
    warnings.warn("PyTorch nie zainstalowany. GPU detection niedostępne.")


class DeviceManager:
    """
    Zarządza przypisaniem urządzeń (GPU/CPU) dla komponentów systemu.
    
    Modes:
    - 'auto': Automatyczna detekcja (recommended)
    - 'gpu': Wymuś GPU (fail jeśli niedostępne)
    - 'cpu': Wymuś CPU (zawsze działa)
    - 'hybrid': Embeddings GPU, reszta CPU (oszczędność VRAM)
    """
    
    def __init__(self, mode: str = 'auto'):
        """
        Inicjalizuje device manager.
        
        Args:
            mode: 'auto', 'gpu', 'cpu', lub 'hybrid'
        """
        self.mode = mode
        self.cuda_available = _torch_available and torch.cuda.is_available()
        
        # Device configuration per component
        self.config = {}
        
        # Wykryj konfigurację
        if mode == 'auto':
            self.config = self._auto_detect()
        elif mode == 'gpu':
            self.config = self._force_gpu()
        elif mode == 'cpu':
            self.config = self._force_cpu()
        elif mode == 'hybrid':
            self.config = self._hybrid_mode()
        else:
            logger.warning(f"Nieznany mode: {mode}, używam 'auto'")
            self.config = self._auto_detect()
        
        logger.info(f"DeviceManager: mode={mode}, config={self.config}")
    
    def _auto_detect(self) -> Dict[str, str]:
        """Auto-detection optymalnej konfiguracji"""
        if not self.cuda_available:
            logger.info("⚠️ GPU (CUDA) niedostępne, używam CPU dla wszystkich komponentów")
            return {
                'embeddings': 'cpu',
                'llm': 'cpu',
                'reranker': 'cpu',
                'vision': 'cpu'
            }
        
        # CUDA dostępne - sprawdź VRAM
        try:
            device_props = torch.cuda.get_device_properties(0)
            vram_gb = device_props.total_memory / 1e9
            device_name = torch.cuda.get_device_name(0)
            
            logger.info(f"✅ GPU dostępne: {device_name} ({vram_gb:.1f} GB VRAM)")
            
            # Strategia według VRAM
            if vram_gb >= 16:
                # Duża karta (RTX 4070+, 3090, 4090)
                # Wszystko na GPU
                logger.info("Duża karta GPU (≥16GB) - używam GPU dla wszystkich komponentów")
                return {
                    'embeddings': 'cuda',
                    'llm': 'cuda',
                    'reranker': 'cuda',
                    'vision': 'cuda'
                }
                
            elif vram_gb >= 12:
                # Średnia karta (RTX 3060, 4060)
                # GPU dla wszystkich, ale Ollama sam zarządza pamięcią
                logger.info("Średnia karta GPU (≥12GB) - używam GPU, Ollama auto-zarządza VRAM")
                return {
                    'embeddings': 'cuda',
                    'llm': 'cuda',  # Ollama offload jeśli brak VRAM
                    'reranker': 'cuda',
                    'vision': 'cuda'
                }
                
            elif vram_gb >= 8:
                # Mała karta (RTX 3050, 2060)
                # Hybrid: embeddings GPU, reranker CPU
                logger.info("Mała karta GPU (≥8GB) - tryb hybrydowy (embeddings GPU, reranker CPU)")
                return {
                    'embeddings': 'cuda',
                    'llm': 'cuda',
                    'reranker': 'cpu',  # Oszczędność VRAM
                    'vision': 'cuda'
                }
                
            else:
                # Bardzo mała karta (<8GB)
                # Tylko embeddings na GPU
                logger.info("Bardzo mała karta GPU (<8GB) - tylko embeddings na GPU")
                return {
                    'embeddings': 'cuda',
                    'llm': 'cpu',
                    'reranker': 'cpu',
                    'vision': 'cpu'
                }
                
        except Exception as e:
            logger.error(f"Błąd podczas detekcji GPU: {e}")
            logger.info("Fallback: używam CPU")
            return self._force_cpu()
    
    def _force_gpu(self) -> Dict[str, str]:
        """Wymusza GPU dla wszystkich komponentów"""
        if not self.cuda_available:
            raise RuntimeError("GPU wymagane ale niedostępne! CUDA not available.")
        
        logger.info("Mode: GPU - wszystkie komponenty na GPU")
        return {
            'embeddings': 'cuda',
            'llm': 'cuda',
            'reranker': 'cuda',
            'vision': 'cuda'
        }
    
    def _force_cpu(self) -> Dict[str, str]:
        """Wymusza CPU dla wszystkich komponentów"""
        logger.info("Mode: CPU - wszystkie komponenty na CPU")
        return {
            'embeddings': 'cpu',
            'llm': 'cpu',
            'reranker': 'cpu',
            'vision': 'cpu'
        }
    
    def _hybrid_mode(self) -> Dict[str, str]:
        """Tryb hybrydowy: embeddings GPU, reszta CPU"""
        if not self.cuda_available:
            logger.warning("GPU niedostępne dla hybrid mode, używam CPU")
            return self._force_cpu()
        
        logger.info("Mode: Hybrid - embeddings GPU, llm/reranker CPU")
        return {
            'embeddings': 'cuda',
            'llm': 'cpu',
            'reranker': 'cpu',
            'vision': 'cpu'
        }
    
    def get_device(self, component: str) -> str:
        """
        Zwraca device dla danego komponentu.
        
        Args:
            component: 'embeddings', 'llm', 'reranker', lub 'vision'
            
        Returns:
            'cuda' lub 'cpu'
        """
        return self.config.get(component, 'cpu')
    
    def get_vram_usage(self) -> Dict[str, Any]:
        """
        Zwraca aktualne użycie VRAM.
        
        Returns:
            Dict z: total_gb, used_gb, free_gb, percent
        """
        if not self.cuda_available:
            return {
                'available': False,
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'percent': 0
            }
        
        try:
            total = torch.cuda.get_device_properties(0).total_memory / 1e9
            allocated = torch.cuda.memory_allocated(0) / 1e9
            reserved = torch.cuda.memory_reserved(0) / 1e9
            
            return {
                'available': True,
                'total_gb': total,
                'allocated_gb': allocated,
                'reserved_gb': reserved,
                'free_gb': total - reserved,
                'percent': (reserved / total) * 100
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas odczytu VRAM: {e}")
            return {'available': False}
    
    def get_info(self) -> Dict[str, Any]:
        """
        Zwraca pełne informacje o konfiguracji urządzeń.
        
        Returns:
            Dict z informacjami o GPU/CPU, konfiguracji, VRAM
        """
        info = {
            'mode': self.mode,
            'cuda_available': self.cuda_available,
            'config': self.config,
        }
        
        if self.cuda_available:
            try:
                info['gpu_name'] = torch.cuda.get_device_name(0)
                info['cuda_version'] = torch.version.cuda
                info['vram'] = self.get_vram_usage()
            except:
                pass
        
        return info


if __name__ == "__main__":
    # Tests
    logging.basicConfig(level=logging.INFO)
    
    print("=== TEST: DeviceManager ===\n")
    
    # Test 1: Auto mode
    print("Test 1: Auto mode")
    manager = DeviceManager(mode='auto')
    print(f"  Config: {manager.config}")
    print(f"  CUDA available: {manager.cuda_available}")
    
    if manager.cuda_available:
        vram = manager.get_vram_usage()
        print(f"  VRAM: {vram['allocated_gb']:.1f}/{vram['total_gb']:.1f} GB ({vram['percent']:.1f}%)")
    
    # Test 2: Get device for components
    print("\nTest 2: Device per component")
    for component in ['embeddings', 'llm', 'reranker', 'vision']:
        device = manager.get_device(component)
        print(f"  {component}: {device}")
    
    # Test 3: Info
    print("\nTest 3: Full info")
    info = manager.get_info()
    print(f"  Mode: {info['mode']}")
    if 'gpu_name' in info:
        print(f"  GPU: {info['gpu_name']}")
    
    print("\n✅ Testy zakończone")

