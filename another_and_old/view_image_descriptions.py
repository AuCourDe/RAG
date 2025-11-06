#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do przeglądania opisów zdjęć wygenerowanych przez Gemma 3
Wyświetla wszystkie opisy obrazów z bazy wektorowej
"""

import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
from datetime import datetime

def view_image_descriptions():
    """Wyświetla wszystkie opisy obrazów z bazy wektorowej"""
    
    print("=" * 80)
    print("📷 OPISY OBRAZÓW WYGENEROWANE PRZEZ GEMMA 3:12B")
    print("=" * 80)
    print()
    
    # Ładowanie bazy wektorowej
    db_path = Path("vector_db")
    
    if not db_path.exists():
        print("❌ Baza wektorowa nie istnieje!")
        print(f"   Ścieżka: {db_path.absolute()}")
        return
    
    print(f"📂 Ładowanie bazy z: {db_path.absolute()}")
    
    try:
        client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        collection = client.get_collection("legal_documents")
        
        # Pobierz wszystkie dane
        all_data = collection.get(include=['documents', 'metadatas'])
        
        # Filtruj tylko opisy obrazów
        image_descriptions = []
        
        for i, metadata in enumerate(all_data['metadatas']):
            if metadata.get('chunk_type') == 'image_description':
                image_descriptions.append({
                    'id': all_data['ids'][i],
                    'description': all_data['documents'][i],
                    'source_file': metadata.get('source_file', 'N/A'),
                    'page_number': metadata.get('page_number', 'N/A'),
                    'element_id': metadata.get('element_id', 'N/A')
                })
        
        print(f"✅ Znaleziono {len(image_descriptions)} opisów obrazów\n")
        
        if len(image_descriptions) == 0:
            print("⚠️ Brak opisów obrazów w bazie.")
            print("   Możliwe przyczyny:")
            print("   1. Nie było obrazów w dokumentach")
            print("   2. Obrazy nie zostały jeszcze przetworzone")
            print("   3. Model Gemma 3 nie był dostępny podczas indeksowania")
            print()
            print("💡 Aby zindeksować obrazy, użyj:")
            print("   python reindex_images.py")
            return
        
        # Grupuj po plikach źródłowych
        by_file = {}
        for desc in image_descriptions:
            file = desc['source_file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(desc)
        
        # Wyświetl pogrupowane
        for file_idx, (file, descriptions) in enumerate(by_file.items(), 1):
            print("=" * 80)
            print(f"📄 PLIK #{file_idx}: {file}")
            print(f"   Liczba obrazów: {len(descriptions)}")
            print("=" * 80)
            print()
            
            for img_idx, desc in enumerate(descriptions, 1):
                print(f"  🖼️ OBRAZ #{img_idx}")
                print(f"     ID: {desc['id']}")
                print(f"     Strona: {desc['page_number']}")
                print(f"     Element ID: {desc['element_id']}")
                print()
                print(f"     📝 OPIS:")
                print(f"     {'-' * 70}")
                
                # Formatuj opis (zawijaj długie linie)
                description_text = desc['description']
                words = description_text.split()
                line = "     "
                for word in words:
                    if len(line) + len(word) + 1 > 76:
                        print(line)
                        line = "     " + word
                    else:
                        line += " " + word if line != "     " else word
                if line.strip():
                    print(line)
                
                print(f"     {'-' * 70}")
                print()
        
        print("=" * 80)
        print("📊 PODSUMOWANIE")
        print("=" * 80)
        print(f"Całkowita liczba obrazów: {len(image_descriptions)}")
        print(f"Liczba plików z obrazami: {len(by_file)}")
        print()
        
        # Zapisz do pliku JSON
        output_file = "image_descriptions.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generated_at': datetime.now().isoformat(),
                'total_images': len(image_descriptions),
                'total_files': len(by_file),
                'descriptions': image_descriptions
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Opisy zapisane do pliku: {output_file}")
        print()
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    view_image_descriptions()

