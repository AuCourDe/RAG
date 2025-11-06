#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Search - moduł do wyszukiwania w intranecie/internecie.

Obsługuje:
- Bing Search API
- Web scraping (HTML → Markdown)
- Site filtering dla intranetu
- Cache wyników
"""

import logging
import requests
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import hashlib

logger = logging.getLogger(__name__)

# Lazy imports
try:
    from bs4 import BeautifulSoup
    _bs4_available = True
except ImportError:
    _bs4_available = False
    logger.warning("BeautifulSoup4 nie zainstalowane. Web scraping niedostępny.")

try:
    from markdownify import markdownify as md
    _markdownify_available = True
except ImportError:
    _markdownify_available = False
    logger.warning("Markdownify nie zainstalowane. Użyję plain text extraction.")


class BingSearchProvider:
    """
    Provider dla Bing Search API.
    
    Umożliwia wyszukiwanie w:
    - Całym internecie
    - Konkretnych domenach (site: filter) - dla intranetu
    """
    
    def __init__(self, api_key: str):
        """
        Inicjalizuje Bing Search provider.
        
        Args:
            api_key: Klucz API Bing Search
        """
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
        logger.info("BingSearchProvider zainicjalizowany")
    
    def search(
        self,
        query: str,
        count: int = 5,
        site: str = None,
        market: str = 'pl-PL'
    ) -> List[Dict[str, Any]]:
        """
        Wyszukuje używając Bing Search API.
        
        Args:
            query: Zapytanie
            count: Liczba wyników
            site: Ograniczenie do domeny (np. "wiki.firma.pl" dla intranetu)
            market: Rynek (domyślnie pl-PL)
            
        Returns:
            Lista wyników: [{'title', 'url', 'snippet'}, ...]
        """
        try:
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            
            # Dodaj site filter jeśli podano (dla intranetu)
            search_query = query
            if site:
                search_query = f"site:{site} {query}"
                logger.info(f"Wyszukiwanie ograniczone do: {site}")
            
            params = {
                'q': search_query,
                'count': count,
                'mkt': market,
            }
            
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                web_pages = data.get('webPages', {}).get('value', [])
                
                results = [
                    {
                        'title': page['name'],
                        'url': page['url'],
                        'snippet': page['snippet'],
                    }
                    for page in web_pages
                ]
                
                logger.info(f"Bing Search: znaleziono {len(results)} wyników dla '{query[:50]}...'")
                return results
                
            else:
                logger.error(f"Błąd Bing Search API: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Błąd podczas wyszukiwania Bing: {e}")
            return []
    
    def is_available(self) -> bool:
        """Sprawdza czy API jest dostępne"""
        try:
            headers = {'Ocp-Apim-Subscription-Key': self.api_key}
            response = requests.get(
                self.base_url,
                headers=headers,
                params={'q': 'test', 'count': 1},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


class WebScraper:
    """
    Web scraper - pobiera zawartość stron i konwertuje do tekstu.
    
    HTML → Markdown dla lepszej czytelności.
    """
    
    def __init__(self):
        """Inicjalizuje web scraper."""
        if not _bs4_available:
            raise ImportError("BeautifulSoup4 nie zainstalowane. Zainstaluj: pip install beautifulsoup4")
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (RAG System Bot) AppleWebKit/537.36'
        }
        
        logger.info("WebScraper zainicjalizowany")
    
    def scrape(self, url: str, max_length: int = 10000) -> Dict[str, Any]:
        """
        Scrape'uje stronę i konwertuje do tekstu.
        
        Args:
            url: URL strony
            max_length: Maksymalna długość treści (znaki)
            
        Returns:
            Dict: {'url', 'title', 'content', 'length', 'success'}
        """
        try:
            logger.info(f"Scraping: {url}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=10,
                allow_redirects=True
            )
            
            if response.status_code != 200:
                logger.warning(f"HTTP {response.status_code} dla {url}")
                return {
                    'url': url,
                    'title': '',
                    'content': f'Błąd HTTP: {response.status_code}',
                    'length': 0,
                    'success': False
                }
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Usuń niepotrzebne elementy
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
                element.decompose()
            
            # Wyciągnij tytuł
            title = soup.find('title')
            title_text = title.get_text().strip() if title else url
            
            # Wyciągnij główną zawartość
            # Priorytet: <article>, <main>, <body>
            main_content = soup.find('article') or soup.find('main') or soup.find('body')
            
            if not main_content:
                logger.warning(f"Nie znaleziono głównej zawartości dla {url}")
                return {
                    'url': url,
                    'title': title_text,
                    'content': '',
                    'length': 0,
                    'success': False
                }
            
            # Konwertuj do Markdown (jeśli dostępne)
            if _markdownify_available:
                content_md = md(str(main_content), heading_style="ATX")
            else:
                # Fallback: plain text
                content_md = main_content.get_text(separator='\n', strip=True)
            
            # Czyszczenie
            lines = content_md.split('\n')
            cleaned_lines = [
                line.strip()
                for line in lines
                if line.strip() and len(line.strip()) > 2  # Usuń bardzo krótkie linie
            ]
            content_md = '\n'.join(cleaned_lines)
            
            # Ogranicz długość
            if len(content_md) > max_length:
                content_md = content_md[:max_length] + "..."
                logger.info(f"Treść obcięta do {max_length} znaków")
            
            result = {
                'url': url,
                'title': title_text,
                'content': content_md,
                'length': len(content_md),
                'success': True
            }
            
            logger.info(f"Scraping sukces: {len(content_md)} znaków z {url}")
            return result
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout podczas scraping: {url}")
            return {
                'url': url,
                'title': '',
                'content': 'Timeout podczas pobierania strony',
                'length': 0,
                'success': False
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas scraping {url}: {e}")
            return {
                'url': url,
                'title': '',
                'content': f'Błąd: {str(e)}',
                'length': 0,
                'success': False
            }


class WebSearchCache:
    """
    Cache dla wyników web search.
    
    Zmniejsza koszty API i przyspiesza powtarzające się zapytania.
    """
    
    def __init__(self, cache_file: str = 'web_search_cache.json', ttl_hours: int = 24):
        """
        Inicjalizuje cache.
        
        Args:
            cache_file: Plik cache
            ttl_hours: Time to live w godzinach
        """
        self.cache_file = Path(cache_file)
        self.ttl_hours = ttl_hours
        self.cache = self._load_cache()
        
        logger.info(f"WebSearchCache zainicjalizowany: TTL={ttl_hours}h")
    
    def _load_cache(self) -> Dict[str, Any]:
        """Ładuje cache z pliku"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            logger.info(f"Załadowano {len(cache)} wpisów z cache")
            return cache
        except Exception as e:
            logger.error(f"Błąd podczas ładowania cache: {e}")
            return {}
    
    def _save_cache(self):
        """Zapisuje cache do pliku"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Błąd podczas zapisywania cache: {e}")
    
    def get(self, query: str, site: str = None) -> List[Dict[str, Any]]:
        """
        Pobiera wyniki z cache jeśli są świeże.
        
        Args:
            query: Zapytanie
            site: Site filter (opcjonalnie)
            
        Returns:
            Lista wyników lub None jeśli brak w cache / expired
        """
        cache_key = self._make_key(query, site)
        
        if cache_key not in self.cache:
            return None
        
        entry = self.cache[cache_key]
        
        # Sprawdź czy nie expired
        cached_time = datetime.fromisoformat(entry['timestamp'])
        now = datetime.now()
        
        if now - cached_time > timedelta(hours=self.ttl_hours):
            logger.info(f"Cache expired dla '{query[:30]}...'")
            del self.cache[cache_key]
            self._save_cache()
            return None
        
        logger.info(f"Cache hit dla '{query[:30]}...'")
        return entry['results']
    
    def set(self, query: str, results: List[Dict[str, Any]], site: str = None):
        """
        Zapisuje wyniki do cache.
        
        Args:
            query: Zapytanie
            results: Wyniki wyszukiwania
            site: Site filter (opcjonalnie)
        """
        cache_key = self._make_key(query, site)
        
        self.cache[cache_key] = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'site': site,
            'results': results
        }
        
        self._save_cache()
        logger.info(f"Zapisano do cache: '{query[:30]}...'")
    
    def _make_key(self, query: str, site: str = None) -> str:
        """Tworzy klucz cache"""
        key_str = f"{query}||{site or ''}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def cleanup(self):
        """Usuwa expired wpisy z cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, entry in self.cache.items():
            try:
                cached_time = datetime.fromisoformat(entry['timestamp'])
                if now - cached_time > timedelta(hours=self.ttl_hours):
                    expired_keys.append(key)
            except:
                expired_keys.append(key)  # Usuń nieprawidłowe wpisy
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self._save_cache()
            logger.info(f"Wyczyszczono {len(expired_keys)} expired wpisów z cache")


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    print("=== TEST: WebScraper ===\n")
    
    if _bs4_available:
        scraper = WebScraper()
        
        # Test scraping (użyj bezpiecznego URL)
        result = scraper.scrape('https://example.com')
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Content length: {result['length']}")
        print(f"Success: {result['success']}")
        print(f"Content preview: {result['content'][:200]}...")
    else:
        print("⚠️ BeautifulSoup4 nie zainstalowane, pomiń test")
    
    print("\n=== TEST: WebSearchCache ===\n")
    
    cache = WebSearchCache(cache_file='test_cache.json', ttl_hours=1)
    
    # Test cache
    test_results = [{'title': 'Test', 'url': 'http://test.com', 'snippet': 'Test snippet'}]
    
    cache.set('test query', test_results)
    cached = cache.get('test query')
    
    print(f"Set & Get: {cached == test_results}")
    
    # Cleanup
    import os
    if os.path.exists('test_cache.json'):
        os.remove('test_cache.json')
    
    print("\n✅ Testy zakończone")

