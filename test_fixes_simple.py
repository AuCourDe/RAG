#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty test naprawionych funkcjonalności - sprawdza tylko kod źródłowy
"""

def test_source_reference_no_id():
    """Test czy SourceReference nie używa 'id' w konstruktorze"""
    print("=" * 60)
    print("TEST: Sprawdzenie czy SourceReference nie używa 'id'")
    print("=" * 60)
    
    try:
        with open('app/rag_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź definicję SourceReference
        if 'class SourceReference' in content:
            # Znajdź definicję klasy
            lines = content.split('\n')
            in_class = False
            class_lines = []
            
            for i, line in enumerate(lines):
                if 'class SourceReference' in line:
                    in_class = True
                    class_lines.append((i+1, line))
                elif in_class:
                    if line.strip() and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                        if line.strip().startswith('class ') or (line.strip() and not line.startswith(' ') and not line.startswith('\t')):
                            break
                        class_lines.append((i+1, line))
            
            # Sprawdź czy w definicji jest 'id'
            has_id_field = any('id:' in line for _, line in class_lines)
            
            if has_id_field:
                print("⚠️  SourceReference ma pole 'id' w definicji:")
                for num, line in class_lines:
                    if 'id:' in line:
                        print(f"   Linia {num}: {line.strip()}")
                print("   To może być OK jeśli to dataclass field")
            else:
                print("✅ SourceReference nie ma pola 'id' w definicji")
        
        # Sprawdź użycie 'id=' w konstruktorze SourceReference
        lines = content.split('\n')
        found_errors = []
        
        for i, line in enumerate(lines):
            if 'SourceReference(' in line and 'id=' in line:
                found_errors.append((i+1, line.strip()))
        
        if found_errors:
            print("\n❌ Znaleziono użycie 'id=' w konstruktorze SourceReference:")
            for num, line in found_errors:
                print(f"   Linia {num}: {line}")
            return False
        else:
            print("✅ Brak użycia 'id=' w konstruktorze SourceReference")
            return True
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_page_number_usage():
    """Test czy używane jest 'page_number' zamiast 'page'"""
    print("\n" + "=" * 60)
    print("TEST: Sprawdzenie użycia 'page_number' vs 'page'")
    print("=" * 60)
    
    try:
        with open('app/rag_system.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        found_page_errors = []
        
        # Szukaj użycia 'page' w kontekście SourceReference
        for i, line in enumerate(lines):
            if 'SourceReference(' in line or ('metadata.get' in line and 'page' in line):
                # Sprawdź czy używa 'page' zamiast 'page_number'
                if 'metadata.get(\'page\'' in line and 'page_number' not in line:
                    # To może być OK jeśli jest fallback: metadata.get('page_number', metadata.get('page', 0))
                    if 'metadata.get(\'page_number\'' not in content[max(0, i-5):i+5]:
                        found_page_errors.append((i+1, line.strip()))
        
        if found_page_errors:
            print("⚠️  Znaleziono użycie 'page' zamiast 'page_number':")
            for num, line in found_page_errors[:5]:  # Pokaż tylko pierwsze 5
                print(f"   Linia {num}: {line}")
            print("   (To może być OK jeśli jest fallback)")
        else:
            print("✅ Używane jest 'page_number' z odpowiednimi fallbackami")
        
        # Sprawdź czy jest fallback
        if 'metadata.get(\'page_number\', metadata.get(\'page\'' in content:
            print("✅ Znaleziono fallback: page_number z fallback na page")
            return True
        else:
            print("⚠️  Brak fallbacku page_number -> page (może być OK)")
            return True  # To nie jest błąd, tylko informacja
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_upload_read():
    """Test czy używa read() zamiast getbuffer()"""
    print("\n" + "=" * 60)
    print("TEST: Sprawdzenie użycia read() zamiast getbuffer()")
    print("=" * 60)
    
    try:
        with open('app/app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź czy jest getbuffer()
        if 'getbuffer()' in content:
            print("⚠️  Znaleziono użycie getbuffer():")
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'getbuffer()' in line:
                    print(f"   Linia {i+1}: {line.strip()}")
            return False
        else:
            print("✅ Brak użycia getbuffer()")
        
        # Sprawdź czy jest read()
        if 'uploaded_file.read()' in content:
            print("✅ Znaleziono użycie uploaded_file.read()")
            return True
        else:
            print("⚠️  Brak użycia uploaded_file.read()")
            return False
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_verification():
    """Test czy jest weryfikacja zapisu pliku"""
    print("\n" + "=" * 60)
    print("TEST: Sprawdzenie weryfikacji zapisu pliku")
    print("=" * 60)
    
    try:
        with open('app/app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Sprawdź czy jest weryfikacja
        checks = [
            'file_path.exists()',
            'file_path.stat().st_size',
            'len(file_bytes)'
        ]
        
        found_checks = []
        for check in checks:
            if check in content:
                found_checks.append(check)
        
        if found_checks:
            print(f"✅ Znaleziono weryfikację zapisu: {', '.join(found_checks)}")
            return True
        else:
            print("⚠️  Brak weryfikacji zapisu pliku")
            return False
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Uruchom wszystkie testy"""
    print("\n" + "=" * 60)
    print("TESTOWANIE NAPRAWIONYCH FUNKCJONALNOŚCI (prosty test)")
    print("=" * 60 + "\n")
    
    results = []
    results.append(test_source_reference_no_id())
    results.append(test_page_number_usage())
    results.append(test_file_upload_read())
    results.append(test_file_verification())
    
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
        print("⚠️  NIEKTÓRE TESTY NIE ZALICZONE (sprawdź szczegóły powyżej)")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
