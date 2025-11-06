#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skrypt testowy dla systemu RAG
"""

import sys
import logging
from pathlib import Path

# Dodanie ścieżki do modułów
sys.path.append(str(Path(__file__).parent))

from rag_system import RAGSystem

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_rag_system():
    """Test podstawowej funkcjonalności systemu RAG"""
    print("="*60)
    print("TEST SYSTEMU RAG")
    print("="*60)
    
    try:
        # Inicjalizacja systemu
        print("1. Inicjalizacja systemu RAG...")
        rag = RAGSystem()
        print("✓ System RAG zainicjalizowany pomyślnie")
        
        # Test zapytania
        print("\n2. Test zapytania...")
        test_questions = [
            "Co zawiera dokument?",
            "Jakie są podstawowe informacje?",
            "O czym mowa w dokumencie?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\nTest {i}: {question}")
            try:
                answer = rag.query(question, n_results=2)
                if answer and len(answer) > 50:
                    print(f"✓ Odpowiedź otrzymana ({len(answer)} znaków)")
                    print(f"Fragment odpowiedzi: {answer[:100]}...")
                else:
                    print("⚠ Odpowiedź zbyt krótka lub pusta")
            except Exception as e:
                print(f"✗ Błąd podczas zapytania: {e}")
        
        print("\n" + "="*60)
        print("TEST ZAKOŃCZONY")
        print("="*60)
        
    except Exception as e:
        print(f"✗ Błąd podczas inicjalizacji systemu: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_rag_system()

