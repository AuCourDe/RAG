#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test naprawionych funkcjonalności:
1. Dodawanie plików
2. Wyszukiwanie danych
"""

import sys
from pathlib import Path

# Dodaj ścieżkę do app
sys.path.insert(0, str(Path(__file__).parent / "app"))

def test_file_upload_conversion():
    """Test konwersji wyników hybrid_search do SourceReference"""
    print("=" * 60)
    print("TEST 1: Konwersja wyników hybrid_search")
    print("=" * 60)
    
    try:
        from app import convert_hybrid_results_to_sources
        
        # Symulacja wyników z hybrid_search
        hybrid_results = [
            {
                'id': 'doc1',
                'content': 'Test content 1',
                'metadata': {
                    'source_file': 'test.pdf',
                    'page_number': 1,
                    'element_id': 'elem1',
                    'chunk_type': 'text'
                },
                'rerank_score': 0.95
            },
            {
                'id': 'doc2',
                'content': 'Test content 2',
                'metadata': {
                    'source_file': 'test2.pdf',
                    'page_number': 2,
                    'element_id': 'elem2',
                    'chunk_type': 'text'
                },
                'rrf_score': 0.85
            }
        ]
        
        sources = convert_hybrid_results_to_sources(hybrid_results)
        
        assert len(sources) == 2, f"Oczekiwano 2 źródła, otrzymano {len(sources)}"
        assert sources[0].source_file == 'test.pdf', f"Oczekiwano 'test.pdf', otrzymano '{sources[0].source_file}'"
        assert sources[0].page_number == 1, f"Oczekiwano page_number=1, otrzymano {sources[0].page_number}"
        assert sources[0].content == 'Test content 1', "Nieprawidłowa zawartość"
        
        print("✅ TEST 1: Konwersja wyników hybrid_search - SUKCES")
        return True
        
    except Exception as e:
        print(f"❌ TEST 1: Błąd - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_source_reference_creation():
    """Test tworzenia SourceReference z różnych formatów metadanych"""
    print("\n" + "=" * 60)
    print("TEST 2: Tworzenie SourceReference")
    print("=" * 60)
    
    try:
        from rag_system import SourceReference
        
        # Test 1: Podstawowe tworzenie
        source1 = SourceReference(
            content="Test content",
            source_file="test.pdf",
            page_number=1,
            element_id="elem1",
            distance=0.1
        )
        
        assert source1.content == "Test content"
        assert source1.source_file == "test.pdf"
        assert source1.page_number == 1
        assert source1.element_id == "elem1"
        assert source1.distance == 0.1
        
        print("✅ TEST 2: Tworzenie SourceReference - SUKCES")
        return True
        
    except Exception as e:
        print(f"❌ TEST 2: Błąd - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_search_conversion_in_rag_system():
    """Test konwersji w rag_system.py"""
    print("\n" + "=" * 60)
    print("TEST 3: Konwersja w rag_system.py")
    print("=" * 60)
    
    try:
        # Sprawdź czy kod w rag_system.py nie używa 'id' w SourceReference
        with open('app/rag_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Sprawdź czy nie ma próby użycia 'id' w SourceReference
        lines = content.split('\n')
        in_conversion = False
        found_id_usage = False
        
        for i, line in enumerate(lines):
            if 'SourceReference(' in line and 'id=' in line:
                found_id_usage = True
                print(f"⚠️  Znaleziono użycie 'id=' w SourceReference w linii {i+1}: {line.strip()}")
        
        if found_id_usage:
            print("❌ TEST 3: Znaleziono użycie 'id=' w SourceReference - BŁĄD")
            return False
        else:
            print("✅ TEST 3: Brak użycia 'id=' w SourceReference - SUKCES")
            return True
        
    except Exception as e:
        print(f"❌ TEST 3: Błąd - {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Uruchom wszystkie testy"""
    print("\n" + "=" * 60)
    print("TESTOWANIE NAPRAWIONYCH FUNKCJONALNOŚCI")
    print("=" * 60 + "\n")
    
    results = []
    results.append(test_file_upload_conversion())
    results.append(test_source_reference_creation())
    results.append(test_hybrid_search_conversion_in_rag_system())
    
    print("\n" + "=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Testy zaliczone: {passed}/{total}")
    
    if passed == total:
        print("✅ WSZYSTKIE TESTY ZALICZONE")
        return 0
    else:
        print("❌ NIEKTÓRE TESTY NIE ZALICZONE")
        return 1

if __name__ == "__main__":
    sys.exit(main())
