#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit Logger - system logowania aktywności użytkowników.

Loguje:
- Zapytania użytkowników (prompty)
- Odpowiedzi systemu
- Źródła użyte do odpowiedzi
- Upload i usuwanie plików
- Logowania użytkowników
- Timestamp, user_id, session_id

Format: JSONL (JSON Lines) - jeden JSON per linia
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logger aktywności użytkowników dla compliance i monitoringu.
    
    Features:
    - JSONL format (łatwy parsing)
    - Privacy: opcjonalne hashowanie promptów
    - Retention policy: automatyczne czyszczenie starych logów
    - GDPR compliance: możliwość usunięcia logów użytkownika
    """
    
    def __init__(self, log_file: str = 'audit_log.jsonl', retention_days: int = 90):
        """
        Inicjalizuje audit logger.
        
        Args:
            log_file: Ścieżka do pliku logów
            retention_days: Ile dni przechowywać logi (GDPR compliance)
        """
        self.log_file = Path(log_file)
        self.retention_days = retention_days
        
        # Setup Python logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(self.log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        
        # Nie propaguj do root logger (unikamy duplikatów)
        self.logger.propagate = False
        
        logger.info(f"AuditLogger zainicjalizowany: {self.log_file}, retention={retention_days} dni")
    
    def log_query(
        self,
        user_id: str,
        session_id: str,
        query: str,
        response: str,
        sources: List[Dict[str, Any]],
        model: str,
        time_ms: float,
        ip_address: str = None,
        hash_query: bool = False
    ):
        """
        Loguje zapytanie użytkownika i odpowiedź systemu.
        
        Args:
            user_id: ID użytkownika
            session_id: ID sesji
            query: Zapytanie użytkownika
            response: Odpowiedź systemu
            sources: Lista źródeł użytych do odpowiedzi
            model: Nazwa modelu (GPT-4, Gemma, etc.)
            time_ms: Czas generowania odpowiedzi (ms)
            ip_address: IP użytkownika (opcjonalnie)
            hash_query: Czy hashować query dla privacy
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'query',
            'user_id': user_id,
            'session_id': session_id,
            'query': query if not hash_query else None,
            'query_hash': hashlib.sha256(query.encode()).hexdigest()[:16] if hash_query else None,
            'query_length': len(query),
            'response': response,
            'response_length': len(response),
            'sources': [
                {
                    'file': s.get('source_file', ''),
                    'page': s.get('page', ''),
                    'element_id': s.get('element_id', ''),
                    'chunk_type': s.get('chunk_type', 'text')
                }
                for s in sources
            ],
            'sources_count': len(sources),
            'model': model,
            'time_ms': time_ms,
            'ip_address': ip_address,
        }
        
        self._write_log(log_entry)
    
    def log_file_upload(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        file_type: str = None,
        session_id: str = None
    ):
        """
        Loguje upload pliku.
        
        Args:
            user_id: ID użytkownika
            filename: Nazwa pliku
            file_size: Rozmiar w bajtach
            file_type: Typ pliku (pdf, docx, etc.)
            session_id: ID sesji
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_upload',
            'user_id': user_id,
            'session_id': session_id,
            'filename': filename,
            'file_size_bytes': file_size,
            'file_type': file_type,
        }
        
        self._write_log(log_entry)
    
    def log_file_delete(
        self,
        user_id: str,
        filename: str,
        session_id: str = None
    ):
        """
        Loguje usunięcie pliku.
        
        Args:
            user_id: ID użytkownika
            filename: Nazwa pliku
            session_id: ID sesji
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'file_delete',
            'user_id': user_id,
            'session_id': session_id,
            'filename': filename,
        }
        
        self._write_log(log_entry)
    
    def log_login(
        self,
        user_id: str,
        success: bool,
        ip_address: str = None,
        user_agent: str = None
    ):
        """
        Loguje próbę logowania.
        
        Args:
            user_id: ID użytkownika
            success: Czy logowanie się powiodło
            ip_address: IP użytkownika
            user_agent: User agent przeglądarki
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'login',
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
        }
        
        self._write_log(log_entry)
    
    def log_logout(
        self,
        user_id: str,
        session_id: str = None
    ):
        """
        Loguje wylogowanie.
        
        Args:
            user_id: ID użytkownika
            session_id: ID sesji
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'logout',
            'user_id': user_id,
            'session_id': session_id,
        }
        
        self._write_log(log_entry)
    
    def log_settings_change(
        self,
        user_id: str,
        setting_name: str,
        old_value: Any = None,
        new_value: Any = None,
        session_id: str = None
    ):
        """
        Loguje zmianę ustawień.
        
        Args:
            user_id: ID użytkownika
            setting_name: Nazwa ustawienia
            old_value: Poprzednia wartość
            new_value: Nowa wartość
            session_id: ID sesji
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': 'settings_change',
            'user_id': user_id,
            'session_id': session_id,
            'setting_name': setting_name,
            'old_value': str(old_value) if old_value is not None else None,
            'new_value': str(new_value) if new_value is not None else None,
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """Zapisuje wpis do logu (JSONL format)"""
        try:
            self.logger.info(json.dumps(log_entry, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania audit log: {e}")
    
    def get_logs(
        self,
        user_id: str = None,
        event_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Pobiera logi z pliku z filtrowaniem.
        
        Args:
            user_id: Filtruj po user_id
            event_type: Filtruj po event_type
            start_date: Od tej daty
            end_date: Do tej daty
            limit: Maksymalna liczba wyników
            
        Returns:
            Lista wpisów logów
        """
        if not self.log_file.exists():
            return []
        
        logs = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Filtry
                        if user_id and entry.get('user_id') != user_id:
                            continue
                        
                        if event_type and entry.get('event_type') != event_type:
                            continue
                        
                        if start_date or end_date:
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                        
                        logs.append(entry)
                        
                        if len(logs) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        logger.warning(f"Nieprawidłowy wpis JSON w audit log: {line[:50]}")
                        continue
        
        except Exception as e:
            logger.error(f"Błąd podczas czytania audit log: {e}")
        
        return logs
    
    def cleanup_old_logs(self):
        """
        Usuwa logi starsze niż retention_days (GDPR compliance).
        
        Tworzy nowy plik z tylko aktualnymi logami.
        """
        if not self.log_file.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        temp_file = self.log_file.with_suffix('.tmp')
        
        kept_count = 0
        removed_count = 0
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        if not line.strip():
                            continue
                        
                        try:
                            entry = json.loads(line)
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            
                            if entry_date >= cutoff_date:
                                outfile.write(line)
                                kept_count += 1
                            else:
                                removed_count += 1
                                
                        except (json.JSONDecodeError, KeyError):
                            # Zachowaj nieprawidłowe wpisy (nie usuwaj danych)
                            outfile.write(line)
                            kept_count += 1
            
            # Zamień pliki
            temp_file.replace(self.log_file)
            
            logger.info(f"Cleanup audit logs: zachowano {kept_count}, usunięto {removed_count}")
            
        except Exception as e:
            logger.error(f"Błąd podczas cleanup audit logs: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def delete_user_logs(self, user_id: str):
        """
        Usuwa wszystkie logi użytkownika (GDPR - right to be forgotten).
        
        Args:
            user_id: ID użytkownika którego logi usunąć
        """
        if not self.log_file.exists():
            return
        
        temp_file = self.log_file.with_suffix('.tmp')
        
        kept_count = 0
        removed_count = 0
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        if not line.strip():
                            continue
                        
                        try:
                            entry = json.loads(line)
                            
                            if entry.get('user_id') != user_id:
                                outfile.write(line)
                                kept_count += 1
                            else:
                                removed_count += 1
                                
                        except json.JSONDecodeError:
                            # Zachowaj nieprawidłowe wpisy
                            outfile.write(line)
                            kept_count += 1
            
            # Zamień pliki
            temp_file.replace(self.log_file)
            
            logger.info(f"Usunięto logi użytkownika {user_id}: {removed_count} wpisów, zachowano {kept_count}")
            
        except Exception as e:
            logger.error(f"Błąd podczas usuwania logów użytkownika: {e}")
            if temp_file.exists():
                temp_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Zwraca statystyki z logów.
        
        Returns:
            Słownik ze statystykami
        """
        if not self.log_file.exists():
            return {}
        
        stats = {
            'total_entries': 0,
            'event_types': {},
            'users': set(),
            'oldest_entry': None,
            'newest_entry': None,
        }
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        stats['total_entries'] += 1
                        
                        # Count event types
                        event_type = entry.get('event_type', 'unknown')
                        stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1
                        
                        # Collect users
                        if 'user_id' in entry:
                            stats['users'].add(entry['user_id'])
                        
                        # Track dates
                        timestamp = entry.get('timestamp')
                        if timestamp:
                            if stats['oldest_entry'] is None:
                                stats['oldest_entry'] = timestamp
                            stats['newest_entry'] = timestamp
                            
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            logger.error(f"Błąd podczas obliczania statystyk: {e}")
        
        stats['users'] = len(stats['users'])
        
        return stats


# Singleton instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """
    Zwraca singleton instancję AuditLogger.
    
    Returns:
        Instancja AuditLogger
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("=== TEST: AuditLogger ===\n")
    
    # Utwórz logger
    audit = AuditLogger(log_file='test_audit.jsonl', retention_days=30)
    
    # Test 1: Log query
    print("Test 1: Logowanie zapytania...")
    audit.log_query(
        user_id='admin',
        session_id='sess123',
        query='Co mówi art. 148?',
        response='Art. 148 mówi o...',
        sources=[
            {'source_file': 'kodeks.pdf', 'page': 10, 'element_id': 'art_148'}
        ],
        model='gpt-4o-mini',
        time_ms=1234.56
    )
    
    # Test 2: Log upload
    print("Test 2: Logowanie uploadu...")
    audit.log_file_upload(
        user_id='admin',
        filename='dokument.pdf',
        file_size=1024000,
        file_type='pdf',
        session_id='sess123'
    )
    
    # Test 3: Log login
    print("Test 3: Logowanie logowania...")
    audit.log_login(
        user_id='admin',
        success=True,
        ip_address='192.168.1.1'
    )
    
    # Test 4: Get stats
    print("\nTest 4: Statystyki...")
    stats = audit.get_stats()
    print(f"Total entries: {stats['total_entries']}")
    print(f"Event types: {stats['event_types']}")
    print(f"Users: {stats['users']}")
    
    # Test 5: Get logs
    print("\nTest 5: Pobieranie logów...")
    logs = audit.get_logs(user_id='admin', limit=10)
    print(f"Pobrano {len(logs)} logów użytkownika 'admin'")
    
    # Cleanup
    import os
    if os.path.exists('test_audit.jsonl'):
        os.remove('test_audit.jsonl')
    
    print("\n✅ Testy zakończone")

