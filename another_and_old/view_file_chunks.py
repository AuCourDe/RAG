#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do przeglądania fragmentów konkretnego pliku
"""

from rag_system import RAGSystem
import sys

def view_chunks(file_name):
    """Wyświetla wszystkie fragmenty dla danego pliku"""
    print("="*70)
    print(f"📄 Fragmenty pliku: {file_name}")
    print("="*70)
    
    rag = RAGSystem()
    collection = rag.vector_db.collection
    
    # Pobierz fragmenty dla tego pliku
    results = collection.get(
        where={"source_file": file_name},
        include=['documents', 'metadatas']
    )
    
    if not results['documents']:
        print(f"❌ Nie znaleziono fragmentów dla: {file_name}")
        return
    
    print(f"\n✅ Znaleziono {len(results['documents'])} fragmentów\n")
    
    # Wyświetl każdy fragment
    for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas']), 1):
        print(f"┌─ Fragment #{i} ─" + "─"*55)
        print(f"│ Strona: {meta['page_number']}")
        print(f"│ Typ: {meta['chunk_type']}")
        print(f"│ Element ID: {meta['element_id']}")
        print(f"│")
        print(f"│ Treść:")
        
        # Wyświetl treść z zawijaniem
        lines = doc.split('\n')
        for line in lines[:10]:  # Pierwsze 10 linii
            if len(line) > 65:
                print(f"│   {line[:65]}...")
            else:
                print(f"│   {line}")
        
        if len(lines) > 10:
            print(f"│   ... ({len(lines) - 10} więcej linii)")
        
        print(f"│ Długość: {len(doc)} znaków")
        print(f"└" + "─"*68)
        print()
    
    print("="*70)
    print(f"📊 Podsumowanie: {len(results['documents'])} fragmentów")
    print("="*70)

def main():
    if len(sys.argv) < 2:
        print("Użycie: python view_file_chunks.py <nazwa_pliku>")
        print("\nPrzykład:")
        print('  python view_file_chunks.py "image (1).jpeg"')
        print('  python view_file_chunks.py "dokument1 (2).pdf"')
        return
    
    file_name = sys.argv[1]
    view_chunks(file_name)

if __name__ == "__main__":
    main()

