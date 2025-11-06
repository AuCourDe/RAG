#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł do filtrowania powitań i fraz uprzejmościowych z zapytań użytkowników.

Używany jako preprocessing przed wysłaniem zapytania do modelu LLM,
aby zredukować niepotrzebne tokeny i poprawić jakość odpowiedzi.
"""

import re
from typing import Tuple


# Wzorce powitań w języku polskim i angielskim
GREETING_PATTERNS = [
    # Polskie powitania
    r'\b(cześć|czesc|hej|hey|siema|witaj|witam|witajcie)\b',
    r'\b(dzień dobry|dzien dobry|dobry dzień|dobry dzien)\b',
    r'\b(dobry wieczór|dobry wieczor|dobry wieczór|dobry wieczor)\b',
    r'\b(dobry poranek|dobry popoludnie|dobranoc)\b',
    r'\b(dzień dobry państwu|witam państwa|witam serdecznie)\b',
    
    # Pożegnania
    r'\b(do widzenia|dowidzenia|do zobaczenia|żegnaj|zegnaj)\b',
    r'\b(papa|pa pa|na razie|nara|cześć|czesc)\b',
    r'\b(miłego dnia|milego dnia|miłego wieczoru|dobrego dnia)\b',
    
    # Angielskie powitania
    r'\b(hello|hi|hey|greetings)\b',
    r'\b(good morning|good afternoon|good evening|good night)\b',
    r'\b(goodbye|bye|see you|farewell)\b',
    r'\b(have a nice day|have a good day)\b',
    
    # Zwroty grzecznościowe
    r'\b(proszę|prosze|dziękuję|dziekuje|dzięki|dzieki)\b',
    r'\b(przepraszam|sorry|excuse me|pardon)\b',
    r'\b(please|thank you|thanks)\b',
    
    # Pytania uprzejmościowe (opcjonalne - zachowawcze podejście)
    r'^(jak się masz|jak sie masz|co słychać|co slychac|jak leci)\??$',
    r'^(how are you|what\'s up|whats up)\??$',
    
    # Wykrzykniki na początku/końcu
    r'^[\!]+\s*',
    r'\s*[\!]+$',
    
    # Emotikony i emoji
    r'[😀😃😄😁😆😅🤣😂🙂🙃😉😊😇🥰😍🤩😘😗😚😙🥲😋😛😜🤪😝🤗🤭🤫🤔🤐🤨😐😑😶😏😒🙄😬🤥😌😔😪🤤😴😷🤒🤕🤢🤮🤧🥵🥶🥴😵🤯🤠🥳😎🤓🧐😕😟🙁☹️😮😯😲😳🥺😦😧😨😰😥😢😭😱😖😣😞😓😩😫🥱😤😡😠🤬😈👿💀☠️👹👺👻👽👾🤖💩😺😸😹😻😼😽🙀😿😾👋🤚🖐️✋🖖👌🤌🤏✌️🤞🤟🤘🤙👈👉👆🖕👇☝️👍👎✊👊🤛🤜👏🙌👐🤲🤝🙏]',
]

# Wzorce do czyszczenia po usunięciu powitań
CLEANUP_PATTERNS = [
    r'^\s*[,\.\!]+\s*',  # Przecinki, kropki, wykrzykniki na początku
    r'\s*[,\.\!]+\s*$',  # Przecinki, kropki, wykrzykniki na końcu
    r'\s{2,}',           # Wielokrotne spacje
]


class GreetingFilter:
    """
    Filtr do usuwania powitań i fraz uprzejmościowych z tekstu.
    
    Przykłady użycia:
        >>> filter = GreetingFilter()
        >>> filter.remove_greetings("Cześć! Mam pytanie o art. 148")
        'Mam pytanie o art. 148'
        
        >>> filter.has_greeting("Dzień dobry, jak się masz?")
        True
    """
    
    def __init__(self):
        """Inicjalizuje filtr z prekompilowanymi wzorcami regex."""
        self.patterns = [
            re.compile(pattern, re.IGNORECASE | re.UNICODE | re.MULTILINE)
            for pattern in GREETING_PATTERNS
        ]
        
        self.cleanup_patterns = [
            re.compile(pattern, re.UNICODE)
            for pattern in CLEANUP_PATTERNS
        ]
    
    def remove_greetings(self, text: str) -> str:
        """
        Usuwa powitania i frazy uprzejmościowe z tekstu.
        
        Args:
            text: Tekst wejściowy
            
        Returns:
            Tekst po usunięciu powitań
            
        Examples:
            >>> filter = GreetingFilter()
            >>> filter.remove_greetings("Cześć! Co mówi art. 148?")
            'Co mówi art. 148?'
            
            >>> filter.remove_greetings("Dzień dobry, 😊 mam pytanie")
            'mam pytanie'
        """
        if not text:
            return text
            
        cleaned = text
        
        # Usuń wszystkie wzorce powitań
        for pattern in self.patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Cleanup - usuń nadmiarowe znaki interpunkcyjne i spacje
        for pattern in self.cleanup_patterns:
            cleaned = pattern.sub(' ', cleaned)
        
        # Trim whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def has_greeting(self, text: str) -> bool:
        """
        Sprawdza czy tekst zawiera powitanie.
        
        Args:
            text: Tekst do sprawdzenia
            
        Returns:
            True jeśli tekst zawiera powitanie, False w przeciwnym razie
        """
        if not text:
            return False
            
        return any(pattern.search(text) for pattern in self.patterns)
    
    def filter_with_info(self, text: str) -> Tuple[str, bool, str]:
        """
        Filtruje tekst i zwraca dodatkowe informacje.
        
        Args:
            text: Tekst wejściowy
            
        Returns:
            Tuple (przefiltrowany_tekst, czy_bylo_powitanie, oryginał)
            
        Examples:
            >>> filter = GreetingFilter()
            >>> cleaned, had_greeting, original = filter.filter_with_info("Cześć! Co to?")
            >>> print(f"Oryginał: '{original}'")
            Oryginał: 'Cześć! Co to?'
            >>> print(f"Oczyszczone: '{cleaned}'")
            Oczyszczone: 'Co to?'
            >>> print(f"Miało powitanie: {had_greeting}")
            Miało powitanie: True
        """
        original = text
        has_greet = self.has_greeting(text)
        cleaned = self.remove_greetings(text)
        
        return cleaned, has_greet, original


# Instancja globalna do użytku w innych modułach
_filter_instance = None

def get_greeting_filter() -> GreetingFilter:
    """
    Zwraca singleton instancję GreetingFilter.
    
    Returns:
        Instancja GreetingFilter
    """
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = GreetingFilter()
    return _filter_instance


if __name__ == "__main__":
    # Testy
    filter = GreetingFilter()
    
    test_cases = [
        "Cześć! Mam pytanie o Kodeks karny",
        "Dzień dobry, co mówi art. 148?",
        "Hello! 😊 What does this mean?",
        "Hej! Hey! Siema! Co to jest?",
        "Co to jest zabójstwo?",  # Bez powitania
        "Witam serdecznie, proszę o informację",
        "Dziękuję! Papa! Do widzenia!",
        "",  # Pusty string
        "Cześć",  # Samo powitanie
    ]
    
    print("=== TEST FILTROWANIA POWITAŃ ===\n")
    
    for i, test in enumerate(test_cases, 1):
        cleaned = filter.remove_greetings(test)
        has_greet = filter.has_greeting(test)
        
        print(f"Test {i}:")
        print(f"  Oryginał:     '{test}'")
        print(f"  Oczyszczone:  '{cleaned}'")
        print(f"  Powitanie:    {'✓ TAK' if has_greet else '✗ NIE'}")
        print(f"  Zmiana:       {'✓' if test != cleaned else '-'}")
        print()

