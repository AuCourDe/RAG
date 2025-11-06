#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do zarządzania użytkownikami w systemie RAG
"""

import json
import hashlib
from pathlib import Path
import sys

CONFIG_FILE = Path("auth_config.json")

def load_config():
    """Wczytuje konfigurację użytkowników"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": {}}

def save_config(config):
    """Zapisuje konfigurację użytkowników"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"✅ Zapisano konfigurację do {CONFIG_FILE}")

def hash_password(password):
    """Hashuje hasło SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, full_name):
    """Dodaje nowego użytkownika"""
    config = load_config()
    
    if username in config['users']:
        print(f"⚠️ Użytkownik '{username}' już istnieje!")
        response = input("Czy chcesz nadpisać? (tak/nie): ")
        if response.lower() != 'tak':
            print("❌ Anulowano")
            return
    
    config['users'][username] = {
        'password_hash': hash_password(password),
        'name': full_name
    }
    
    save_config(config)
    print(f"✅ Dodano użytkownika: {username} ({full_name})")

def list_users():
    """Wyświetla listę użytkowników"""
    config = load_config()
    
    if not config['users']:
        print("📭 Brak użytkowników")
        return
    
    print("\n👥 Lista użytkowników:")
    print("=" * 50)
    for username, data in config['users'].items():
        print(f"  • {username:20} - {data['name']}")
    print("=" * 50)
    print(f"Łącznie: {len(config['users'])} użytkowników\n")

def delete_user(username):
    """Usuwa użytkownika"""
    config = load_config()
    
    if username not in config['users']:
        print(f"❌ Użytkownik '{username}' nie istnieje!")
        return
    
    user_name = config['users'][username]['name']
    print(f"⚠️ Usuwanie użytkownika: {username} ({user_name})")
    response = input("Czy na pewno? (tak/nie): ")
    
    if response.lower() == 'tak':
        del config['users'][username]
        save_config(config)
        print(f"✅ Usunięto użytkownika: {username}")
    else:
        print("❌ Anulowano")

def interactive_mode():
    """Tryb interaktywny"""
    print("\n" + "=" * 50)
    print("👥 ZARZĄDZANIE UŻYTKOWNIKAMI - System RAG")
    print("=" * 50)
    
    while True:
        print("\nDostępne opcje:")
        print("  1. Dodaj użytkownika")
        print("  2. Lista użytkowników")
        print("  3. Usuń użytkownika")
        print("  4. Wyjście")
        
        choice = input("\nWybierz opcję (1-4): ").strip()
        
        if choice == '1':
            print("\n➕ Dodawanie nowego użytkownika")
            username = input("Login (bez spacji): ").strip()
            if not username:
                print("❌ Login nie może być pusty!")
                continue
            
            password = input("Hasło (min. 6 znaków): ").strip()
            if len(password) < 6:
                print("❌ Hasło musi mieć min. 6 znaków!")
                continue
            
            full_name = input("Pełne imię/nazwa: ").strip()
            if not full_name:
                full_name = username
            
            add_user(username, password, full_name)
        
        elif choice == '2':
            list_users()
        
        elif choice == '3':
            list_users()
            username = input("\nLogin użytkownika do usunięcia: ").strip()
            if username:
                delete_user(username)
        
        elif choice == '4':
            print("\n👋 Do widzenia!")
            break
        
        else:
            print("❌ Nieprawidłowa opcja!")

def main():
    """Główna funkcja"""
    if len(sys.argv) < 2:
        # Tryb interaktywny
        interactive_mode()
    else:
        command = sys.argv[1]
        
        if command == 'add':
            if len(sys.argv) < 5:
                print("Użycie: python manage_users.py add <login> <hasło> <imię>")
                return
            add_user(sys.argv[2], sys.argv[3], sys.argv[4])
        
        elif command == 'list':
            list_users()
        
        elif command == 'delete':
            if len(sys.argv) < 3:
                print("Użycie: python manage_users.py delete <login>")
                return
            delete_user(sys.argv[2])
        
        else:
            print("Nieznana komenda!")
            print("\nDostępne komendy:")
            print("  python manage_users.py                    - tryb interaktywny")
            print("  python manage_users.py add <login> <hasło> <imię>")
            print("  python manage_users.py list")
            print("  python manage_users.py delete <login>")

if __name__ == "__main__":
    main()


