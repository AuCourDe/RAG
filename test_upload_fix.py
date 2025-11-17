#!/usr/bin/env python3
"""
Test sprawdzajacy czy pliki zapisywane sa do wlasciwego folderu data/
"""

import sys
from pathlib import Path

# Emulacja jak w app.py
PROJECT_ROOT = Path(__file__).resolve().parent
print(f"PROJECT_ROOT: {PROJECT_ROOT}")

# Stara wersja (BLAD)
data_dir_old = Path("data")
print(f"Stara wersja Path('data'): {data_dir_old.resolve()}")

# Nowa wersja (POPRAWIONA)
data_dir_new = PROJECT_ROOT / "data"
print(f"Nowa wersja PROJECT_ROOT / 'data': {data_dir_new}")

# Sprawdz czy folder istnieje
if data_dir_new.exists():
    print(f"Folder {data_dir_new} istnieje")
    files = list(data_dir_new.glob('*'))
    print(f"Liczba plikow w folderze: {len(files)}")
    if files:
        print("Pliki w folderze:")
        for f in files[:10]:  # Pokaz pierwsze 10
            print(f"  - {f.name}")
else:
    print(f"UWAGA: Folder {data_dir_new} NIE istnieje!")
    
# Test zapisu
test_file = data_dir_new / "test_upload_fix.txt"
try:
    data_dir_new.mkdir(exist_ok=True)
    with open(test_file, 'w') as f:
        f.write("Test poprawki uploadu")
    print(f"Test zapisu: OK - plik utworzony w {test_file}")
    test_file.unlink()  # Usun testowy plik
    print("Plik testowy usuniety")
except Exception as e:
    print(f"Test zapisu: BLAD - {e}")

