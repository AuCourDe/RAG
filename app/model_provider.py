#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Provider - abstrakcja dla różnych dostawców modeli LLM.

Obsługuje:
- OpenAI API (GPT-4, GPT-3.5, etc.) - dynamiczne pobieranie listy modeli
- Ollama (lokalne modele jak Gemma 3:12B)

Pattern: Factory + Strategy
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import requests
import json

logger = logging.getLogger(__name__)


class ModelProvider(ABC):
    """Abstrakcyjna klasa bazowa dla dostawców modeli"""
    
    @abstractmethod
    def generate(self, prompt: str, context: str = "", **kwargs) -> str:
        """
        Generuje odpowiedź na podstawie promptu i kontekstu.
        
        Args:
            prompt: System prompt
            context: Kontekst użytkownika (pytanie + dokumenty)
            **kwargs: Dodatkowe parametry (temperature, max_tokens, etc.)
            
        Returns:
            Wygenerowana odpowiedź
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Sprawdza czy provider jest dostępny"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Zwraca nazwę używanego modelu"""
        pass
    
    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """Zwraca listę dostępnych modeli"""
        pass


class OpenAIProvider(ModelProvider):
    """
    Provider dla OpenAI API.
    
    Obsługuje dynamiczne pobieranie listy modeli i wybór modelu.
    """
    
    def __init__(self, api_key: str, model: str = None):
        """
        Inicjalizuje OpenAI provider.
        
        Args:
            api_key: Klucz API OpenAI
            model: Nazwa modelu (opcjonalne - jeśli None, użyje pierwszego dostępnego)
        """
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self._model = model
        self._available_models = None
        
        logger.info("Inicjalizacja OpenAI Provider")
        
        # Pobierz listę modeli jeśli nie podano konkretnego
        if not self._model:
            models = self.list_models()
            if models:
                # Preferuj GPT-4o-mini jako default (najlepszy stosunek jakość/cena)
                default_models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo', 'gpt-4']
                for preferred in default_models:
                    if any(preferred in m['id'] for m in models):
                        self._model = next(m['id'] for m in models if preferred in m['id'])
                        break
                
                # Fallback: użyj pierwszego GPT model
                if not self._model:
                    gpt_models = [m for m in models if 'gpt' in m['id'].lower()]
                    if gpt_models:
                        self._model = gpt_models[0]['id']
                    else:
                        self._model = models[0]['id'] if models else 'gpt-3.5-turbo'
        
        logger.info(f"OpenAI Provider: używam modelu {self._model}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Pobiera listę dostępnych modeli z API OpenAI.
        
        Returns:
            Lista słowników z informacjami o modelach
        """
        if self._available_models is not None:
            return self._available_models
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('data', [])
                
                # Filtruj tylko modele GPT (chat completion models)
                # Sortuj: najpierw GPT-4, potem GPT-3.5
                gpt_models = [m for m in models if 'gpt' in m['id'].lower()]
                gpt_models.sort(key=lambda x: (
                    'gpt-4' not in x['id'],  # GPT-4 na początku
                    'gpt-4o' not in x['id'],  # GPT-4o na początku GPT-4
                    x['id']  # Alfabetycznie
                ))
                
                self._available_models = gpt_models
                logger.info(f"Pobrano {len(gpt_models)} modeli GPT z OpenAI")
                return gpt_models
            else:
                logger.error(f"Błąd pobierania modeli OpenAI: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy modeli OpenAI: {e}")
            return []
    
    def generate(self, prompt: str, context: str = "", **kwargs) -> str:
        """
        Generuje odpowiedź używając OpenAI API.
        
        Args:
            prompt: System prompt
            context: User message (pytanie + kontekst)
            **kwargs: temperature, max_tokens, etc.
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Przygotuj messages
            messages = [
                {"role": "system", "content": prompt}
            ]
            
            if context:
                messages.append({"role": "user", "content": context})
            
            # Parametry
            data = {
                "model": self._model,
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.1),
                "max_tokens": kwargs.get('max_tokens', 1000),
            }
            
            # Dodatkowe parametry jeśli podane
            if 'top_p' in kwargs:
                data['top_p'] = kwargs['top_p']
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=kwargs.get('timeout', 120)
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result['choices'][0]['message']['content']
                
                # Log usage
                usage = result.get('usage', {})
                logger.info(f"OpenAI usage: {usage.get('total_tokens', 0)} tokens "
                           f"(in: {usage.get('prompt_tokens', 0)}, out: {usage.get('completion_tokens', 0)})")
                
                return answer
            else:
                error_msg = f"OpenAI API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Błąd podczas generowania odpowiedzi OpenAI: {e}")
            raise
    
    def is_available(self) -> bool:
        """Sprawdza czy OpenAI API jest dostępne"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def get_model_name(self) -> str:
        """Zwraca nazwę używanego modelu"""
        return self._model
    
    def set_model(self, model: str):
        """Zmienia używany model"""
        self._model = model
        logger.info(f"Zmieniono model OpenAI na: {model}")


class OllamaProvider(ModelProvider):
    """
    Provider dla lokalnego Ollama.
    
    Obsługuje modele lokalne jak Gemma 3:12B.
    """
    
    def __init__(self, model: str = "gemma3:12b", base_url: str = "http://127.0.0.1:11434"):
        """
        Inicjalizuje Ollama provider.
        
        Args:
            model: Nazwa modelu w Ollama
            base_url: URL serwera Ollama
        """
        self.model = model
        self.base_url = base_url
        logger.info(f"Inicjalizacja Ollama Provider: model={model}, url={base_url}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Pobiera listę dostępnych modeli lokalnych"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                logger.info(f"Pobrano {len(models)} modeli z Ollama")
                return models
            else:
                logger.error(f"Błąd pobierania modeli Ollama: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy modeli Ollama: {e}")
            return []
    
    def generate(self, prompt: str, context: str = "", **kwargs) -> str:
        """
        Generuje odpowiedź używając Ollama.
        
        Args:
            prompt: System prompt + kontekst (Ollama nie ma oddzielnego system message)
            context: Dodatkowy kontekst (opcjonalny)
            **kwargs: temperature, num_predict, etc.
        """
        try:
            # Połącz prompt i context
            full_prompt = prompt
            if context:
                full_prompt = f"{prompt}\n\n{context}"
            
            data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": kwargs.get('temperature', 0.1),
                    "num_predict": kwargs.get('max_tokens', 1000),
                    "top_k": kwargs.get('top_k', 30),
                    "top_p": kwargs.get('top_p', 0.85),
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=kwargs.get('timeout', 300)
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                # Log stats
                if 'total_duration' in result:
                    duration = result['total_duration'] / 1e9  # nanoseconds to seconds
                    logger.info(f"Ollama generation time: {duration:.2f}s")
                
                return answer
            else:
                error_msg = f"Ollama API error: {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Błąd podczas generowania odpowiedzi Ollama: {e}")
            raise
    
    def is_available(self) -> bool:
        """Sprawdza czy Ollama jest dostępne"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def get_model_name(self) -> str:
        """Zwraca nazwę używanego modelu"""
        return self.model
    
    def set_model(self, model: str):
        """Zmienia używany model"""
        self.model = model
        logger.info(f"Zmieniono model Ollama na: {model}")


class ModelFactory:
    """
    Factory do tworzenia odpowiedniego providera modelu.
    
    Strategia:
    1. Jeśli jest klucz OpenAI i działa -> użyj OpenAI
    2. Fallback -> Ollama (lokalny)
    """
    
    @staticmethod
    def create_provider(config: Dict[str, Any]) -> ModelProvider:
        """
        Tworzy odpowiedni provider na podstawie konfiguracji.
        
        Args:
            config: Słownik z konfiguracją:
                - openai_api_key: klucz API OpenAI (opcjonalny)
                - openai_model: preferowany model OpenAI (opcjonalny)
                - ollama_model: model Ollama (domyślnie gemma3:12b)
                - ollama_url: URL Ollama (domyślnie localhost:11434)
        
        Returns:
            Instancja ModelProvider
        """
        openai_key = config.get('openai_api_key', '').strip()
        openai_model = config.get('openai_model', None)
        
        # Próba 1: OpenAI (jeśli jest klucz)
        if openai_key:
            try:
                logger.info("Próba inicjalizacji OpenAI Provider...")
                provider = OpenAIProvider(api_key=openai_key, model=openai_model)
                
                if provider.is_available():
                    logger.info(f"[OK] Używam OpenAI API - model: {provider.get_model_name()}")
                    logger.info(f"   Dostępne modele: {len(provider.list_models())}")
                    return provider
                else:
                    logger.warning("[WARNING] OpenAI API niedostępne (błąd autoryzacji?)")
                    
            except Exception as e:
                logger.warning(f"[WARNING] Nie udało się zainicjalizować OpenAI: {e}")
        
        # Fallback: Ollama (lokalny)
        logger.info("Fallback: próba inicjalizacji Ollama Provider...")
        ollama_model = config.get('ollama_model', 'gemma3:12b')
        ollama_url = config.get('ollama_url', 'http://127.0.0.1:11434')
        
        provider = OllamaProvider(model=ollama_model, base_url=ollama_url)
        
        if provider.is_available():
            logger.info(f"[OK] Używam Ollama (lokalny) - model: {provider.get_model_name()}")
            logger.info(f"   Dostępne modele: {len(provider.list_models())}")
            return provider
        else:
            error_msg = "[ERROR] Brak dostępnego providera! Sprawdź OpenAI API key lub uruchom Ollama."
            logger.error(error_msg)
            raise Exception(error_msg)


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Test 1: Ollama (lokalny)
    print("\n=== TEST 1: Ollama Provider ===")
    try:
        config = {
            'ollama_model': 'gemma3:12b',
            'ollama_url': 'http://127.0.0.1:11434'
        }
        provider = ModelFactory.create_provider(config)
        print(f"Provider: {provider.__class__.__name__}")
        print(f"Model: {provider.get_model_name()}")
        print(f"Available: {provider.is_available()}")
        print(f"Models: {len(provider.list_models())}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: OpenAI (wymaga klucza API)
    print("\n=== TEST 2: OpenAI Provider ===")
    print("(Podaj klucz API OpenAI aby przetestować, lub pomiń)")
    # api_key = input("OpenAI API key (lub Enter aby pominąć): ").strip()
    # if api_key:
    #     config = {'openai_api_key': api_key}
    #     provider = ModelFactory.create_provider(config)
    #     print(f"Provider: {provider.__class__.__name__}")
    #     print(f"Model: {provider.get_model_name()}")
    #     print(f"Models: {[m['id'] for m in provider.list_models()[:5]]}")

