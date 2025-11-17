#!/usr/bin/env python3
"""
Test automatyczny w Selenium dla BUG-001: Upload plikow przez GUI
"""

import os
import time
import logging
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Konfiguracja ścieżek
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TEST_FILE = PROJECT_ROOT / "test" / "sample_test_files" / "test_document.pdf"

class TestRAGUpload:
    def __init__(self):
        self.driver = None
        self.wait = None
        
    def setup_driver(self):
        """Konfiguracja Chrome WebDriver"""
        logger.info("Inicjalizacja Chrome WebDriver...")
        
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Wyłączone dla debugowania
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 30)
        logger.info("WebDriver zainicjalizowany")
        
    def login(self, url="http://localhost:8501", username="admin", password="admin123"):
        """Logowanie do systemu"""
        logger.info(f"Otwieram {url}")
        self.driver.get(url)
        
        # Czekaj na załadowanie strony
        time.sleep(5)
        
        try:
            # Znajdź pola logowania
            logger.info("Szukam pola username...")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            logger.info("Szukam pola password...")
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            logger.info("Wypełniam dane logowania...")
            username_field.clear()
            username_field.send_keys(username)
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Kliknij przycisk Zaloguj
            logger.info("Klikam przycisk Zaloguj...")
            # Spróbuj różnych selektorów
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Zaloguj')]")
            except:
                # Alternatywny selector - szukaj przez typ submit
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[kind='primary']")
            
            login_button.click()
            
            # Czekaj na przekierowanie
            time.sleep(5)
            logger.info("Zalogowano pomyslnie")
            return True
            
        except Exception as e:
            logger.error(f"Blad podczas logowania: {e}")
            self.driver.save_screenshot(str(PROJECT_ROOT / "test" / "login_error.png"))
            return False
    
    def navigate_to_indexing_tab(self):
        """Przejście do zakładki Indeksowanie"""
        try:
            logger.info("Szukam zakladki Indeksowanie...")
            
            # Streamlit używa data-testid dla tabów
            tabs = self.driver.find_elements(By.CSS_SELECTOR, "button[data-baseweb='tab']")
            
            for tab in tabs:
                if "Indeksowanie" in tab.text or "indeksowanie" in tab.text.lower():
                    logger.info(f"Znaleziono zakladke: {tab.text}")
                    tab.click()
                    time.sleep(3)
                    return True
            
            # Alternatywnie spróbuj kliknąć drugi tab (po Zapytaniach)
            if len(tabs) >= 2:
                logger.info("Klikam drugi tab (Indeksowanie)...")
                tabs[1].click()
                time.sleep(3)
                return True
                
            logger.error("Nie znaleziono zakladki Indeksowanie")
            return False
            
        except Exception as e:
            logger.error(f"Blad podczas przechodzenia do zakladki: {e}")
            self.driver.save_screenshot(str(PROJECT_ROOT / "test" / "tab_error.png"))
            return False
    
    def upload_file(self, file_path):
        """Upload pliku przez GUI"""
        try:
            logger.info(f"Probuje upload pliku: {file_path}")
            
            if not Path(file_path).exists():
                logger.error(f"Plik nie istnieje: {file_path}")
                return False
            
            # Znajdź element file input (może być ukryty)
            logger.info("Szukam elementu file input...")
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            if not file_inputs:
                logger.error("Nie znaleziono elementu file input")
                self.driver.save_screenshot(str(PROJECT_ROOT / "test" / "no_file_input.png"))
                return False
            
            logger.info(f"Znaleziono {len(file_inputs)} file input(s)")
            
            # Użyj pierwszego file input
            file_input = file_inputs[0]
            
            # Wyślij ścieżkę pliku
            logger.info(f"Wysylam sciezke do pliku: {file_path}")
            file_input.send_keys(str(file_path))
            
            # Czekaj na przetworzenie
            time.sleep(5)
            
            logger.info("Upload zakonczony")
            return True
            
        except Exception as e:
            logger.error(f"Blad podczas uploadu: {e}")
            self.driver.save_screenshot(str(PROJECT_ROOT / "test" / "upload_error.png"))
            return False
    
    def verify_file_in_folder(self, filename):
        """Sprawdź czy plik pojawił się w folderze data/"""
        file_path = DATA_DIR / filename
        
        logger.info(f"Sprawdzam czy plik istnieje: {file_path}")
        
        # Czekaj do 30 sekund
        for i in range(30):
            if file_path.exists():
                file_size = file_path.stat().st_size
                logger.info(f"SUKCES: Plik znaleziony! Rozmiar: {file_size} bytes")
                return True
            time.sleep(1)
            if i % 5 == 0:
                logger.info(f"Czekam na plik... ({i}/30s)")
        
        logger.error(f"BLAD: Plik NIE pojawil sie w folderze data/ po 30 sekundach")
        return False
    
    def verify_in_watchdog_logs(self):
        """Sprawdź logi watchdog"""
        log_file = PROJECT_ROOT / "logs" / "file_watcher.log"
        
        if not log_file.exists():
            logger.warning(f"Log watchdog nie istnieje: {log_file}")
            return False
        
        logger.info("Sprawdzam logi watchdog...")
        with open(log_file, 'r', encoding='utf-8') as f:
            last_lines = f.readlines()[-50:]  # Ostatnie 50 linii
        
        for line in last_lines:
            if "Nowy plik wykryty" in line or "Przetwarzanie pliku" in line:
                logger.info(f"Watchdog wykryl plik: {line.strip()}")
                return True
        
        logger.warning("Watchdog NIE wykryl zadnego nowego pliku")
        return False
    
    def check_statistics(self):
        """Sprawdź statystyki bazy"""
        try:
            logger.info("Sprawdzam statystyki bazy...")
            
            # Szukaj tekstu "Fragmentów w bazie"
            stats = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Fragment')]")
            
            for stat in stats:
                logger.info(f"Statystyka: {stat.text}")
                if "Fragment" in stat.text and "0" not in stat.text:
                    logger.info("Statystyki zaktualizowane!")
                    return True
            
            logger.warning("Statystyki pozostaly na 0")
            return False
            
        except Exception as e:
            logger.error(f"Blad podczas sprawdzania statystyk: {e}")
            return False
    
    def run_test(self):
        """Główny test"""
        try:
            self.setup_driver()
            
            # 1. Logowanie
            logger.info("=== KROK 1: Logowanie ===")
            if not self.login():
                logger.error("FAIL: Logowanie nie powiodlo sie")
                return False
            
            # 2. Przejście do zakładki Indeksowanie
            logger.info("=== KROK 2: Przejscie do Indeksowanie ===")
            if not self.navigate_to_indexing_tab():
                logger.error("FAIL: Nie mozna przejsc do zakladki Indeksowanie")
                return False
            
            # 3. Upload pliku
            logger.info("=== KROK 3: Upload pliku ===")
            if not self.upload_file(TEST_FILE):
                logger.error("FAIL: Upload nie powiodl sie")
                return False
            
            # 4. Weryfikacja w folderze
            logger.info("=== KROK 4: Weryfikacja w folderze data/ ===")
            file_exists = self.verify_file_in_folder(TEST_FILE.name)
            
            # 5. Weryfikacja w logach watchdog
            logger.info("=== KROK 5: Weryfikacja w logach watchdog ===")
            watchdog_detected = self.verify_in_watchdog_logs()
            
            # 6. Sprawdzenie statystyk
            logger.info("=== KROK 6: Sprawdzenie statystyk ===")
            stats_updated = self.check_statistics()
            
            # Podsumowanie
            logger.info("=" * 60)
            logger.info("PODSUMOWANIE TESTU:")
            logger.info(f"  1. Logowanie: PASS")
            logger.info(f"  2. Przejscie do Indeksowanie: PASS")
            logger.info(f"  3. Upload pliku: PASS")
            logger.info(f"  4. Plik w folderze data/: {'PASS' if file_exists else 'FAIL'}")
            logger.info(f"  5. Watchdog wykryl plik: {'PASS' if watchdog_detected else 'FAIL'}")
            logger.info(f"  6. Statystyki zaktualizowane: {'PASS' if stats_updated else 'FAIL'}")
            logger.info("=" * 60)
            
            success = file_exists and watchdog_detected
            
            if success:
                logger.info("TEST PASSED: Plik zostal pomyslnie przeslany i zindeksowany")
            else:
                logger.error("TEST FAILED: BUG-001 nadal wystepuje")
            
            return success
            
        except Exception as e:
            logger.error(f"CRITICAL ERROR: {e}")
            return False
        finally:
            if self.driver:
                self.driver.save_screenshot(str(PROJECT_ROOT / "test" / "final_state.png"))
                self.driver.quit()
                logger.info("WebDriver zamkniety")


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("TEST AUTOMATYCZNY: Upload plikow przez GUI (BUG-001)")
    logger.info("=" * 60)
    
    test = TestRAGUpload()
    success = test.run_test()
    
    exit(0 if success else 1)

