#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Streamlit dla systemu RAG
Z autoryzacją hasłem i możliwością udostępnienia w sieci
Modern UI 2025 - Glassmorphism Design
"""

import streamlit as st
import streamlit.components.v1 as components
from rag_system import RAGSystem, load_suggested_questions
from audit_logger import get_audit_logger
import logging
from pathlib import Path
import hashlib
import json
import time
import os
import subprocess
import requests
import uuid
from collections import deque
import threading
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

SESSION_TIMEOUT_SECONDS = 600


@st.cache_resource
def get_session_store():
    """Przechowywanie aktywnych sesji (token -> dane)."""
    return {}


def tail_file(path: Path, max_lines: int = 100, fallback: Path | None = None) -> str:
    """
    Zwraca ostatnie max_lines linii z pliku logów.
    """
    if not path.exists() and fallback:
        path = fallback
    if not path.exists():
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return "".join(deque(f, maxlen=max_lines))
    except Exception:
        return ""

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
WHISPER_MODELS_DIR = MODELS_DIR / "whisper"
EMBEDDINGS_MODELS_DIR = MODELS_DIR / "embeddings"
RERANKER_MODELS_DIR = MODELS_DIR / "reranker"
UPLOAD_DATA_DIR = PROJECT_ROOT / "data"

for path in [MODELS_DIR, WHISPER_MODELS_DIR, EMBEDDINGS_MODELS_DIR, RERANKER_MODELS_DIR, UPLOAD_DATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# Flask endpoint dla uploadu plików (działa w tle)
FLASK_UPLOAD_PORT = 5001
flask_app = None
flask_thread = None

def create_flask_upload_endpoint():
    """Tworzy Flask endpoint do uploadu plików"""
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB
    
    # CORS headers - pozwól na żądania z Streamlit
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    @app.route('/upload', methods=['POST', 'OPTIONS'])
    def upload_file():
        # Obsługa preflight request
        if request.method == 'OPTIONS':
            return '', 200
        try:
            if 'files' not in request.files:
                return jsonify({'success': False, 'error': 'Brak plików'}), 400
            
            files = request.files.getlist('files')
            if not files or files[0].filename == '':
                return jsonify({'success': False, 'error': 'Nie wybrano plików'}), 400
            
            saved_files = []
            errors = []
            
            for file in files:
                if file.filename:
                    try:
                        filename = secure_filename(file.filename)
                        file_path = UPLOAD_DATA_DIR / filename
                        
                        file.save(str(file_path))
                        
                        if file_path.exists() and file_path.stat().st_size > 0:
                            saved_files.append(filename)
                            logger.info(f"FLASK UPLOAD: Zapisano {file_path} ({file_path.stat().st_size} bytes)")
                        else:
                            errors.append(f"{filename}: Nie zapisano")
                    except Exception as e:
                        errors.append(f"{file.filename}: {str(e)}")
                        logger.error(f"FLASK UPLOAD ERROR: {e}", exc_info=True)
            
            if saved_files:
                return jsonify({'success': True, 'saved': saved_files, 'errors': errors if errors else None})
            else:
                return jsonify({'success': False, 'error': 'Nie zapisano plików', 'errors': errors}), 500
                
        except Exception as e:
            logger.error(f"FLASK UPLOAD ERROR: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return app

@st.cache_resource
def get_flask_upload_endpoint():
    """Uruchamia Flask endpoint w tle"""
    global flask_app, flask_thread
    
    if flask_thread is None or not flask_thread.is_alive():
        flask_app = create_flask_upload_endpoint()
        flask_thread = threading.Thread(
            target=lambda: flask_app.run(host='0.0.0.0', port=FLASK_UPLOAD_PORT, debug=False, use_reloader=False),
            daemon=True
        )
        flask_thread.start()
        # Czekaj dłużej na start i sprawdź czy działa
        for i in range(10):
            time.sleep(0.5)
            try:
                response = requests.get(f'http://localhost:{FLASK_UPLOAD_PORT}/upload', timeout=0.5)
                break
            except:
                if i == 9:
                    logger.warning(f"FLASK UPLOAD: Serwer może nie być gotowy na porcie {FLASK_UPLOAD_PORT}")
                continue
        logger.info(f"FLASK UPLOAD: Serwer uruchomiony na porcie {FLASK_UPLOAD_PORT}")
    
    return flask_app

# Konfiguracja strony
st.set_page_config(
    page_title="RAG System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS - Glassmorphism Design with Light/Dark Theme
def load_css():
    """Ładuje nowoczesny CSS z obsługą motywów"""
    theme = st.session_state.get('theme', 'dark')
    
    if theme == 'dark':
        bg_gradient = "linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #2d2d2d 100%)"
        card_bg = "rgba(40, 40, 40, 0.7)"
        card_border = "rgba(255, 255, 255, 0.1)"
        text_primary = "#ffffff"
        text_secondary = "#b0b0b0"
        accent_color = "#6366f1"
        accent_hover = "#818cf8"
        input_bg = "rgba(50, 50, 50, 0.8)"
        shadow = "0 8px 32px 0 rgba(0, 0, 0, 0.6)"
    else:
        bg_gradient = "#ffffff"
        card_bg = "rgba(255, 255, 255, 0.9)"
        card_border = "rgba(0, 0, 0, 0.08)"
        text_primary = "#1a1a1a"
        text_secondary = "#4a5568"
        accent_color = "#6366f1"
        accent_hover = "#818cf8"
        input_bg = "rgba(255, 255, 255, 0.95)"
        shadow = "0 4px 20px 0 rgba(0, 0, 0, 0.08)"
    
    st.markdown(f"""
        <style>
        /* Global Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        /* Main Background */
        .stApp {{
            background: {bg_gradient};
            color: {text_primary};
        }}
        
        /* Hide Streamlit Branding */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        
        /* Fix Sidebar Collapse Button */
        [data-testid="collapsedControl"] {{
            display: flex !important;
            visibility: visible !important;
            background: {card_bg} !important;
            backdrop-filter: blur(10px) !important;
            border: 1px solid {card_border} !important;
            border-radius: 8px !important;
            padding: 8px !important;
            box-shadow: {shadow} !important;
        }}
        
        [data-testid="collapsedControl"] svg {{
            fill: {text_primary} !important;
        }}
        
        [data-testid="collapsedControl"]:hover {{
            background: {accent_color} !important;
            border-color: {accent_color} !important;
            transform: scale(1.05);
            transition: all 0.3s ease;
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border-right: 1px solid {card_border};
            box-shadow: {shadow};
        }}
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: {text_primary};
        }}
        
        /* Glass Card Effect */
        .glass-card {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 1px solid {card_border};
            padding: 24px;
            box-shadow: {shadow};
            transition: all 0.3s ease;
        }}
        
        .glass-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.2);
        }}
        
        /* Buttons */
        .stButton > button {{
            background: linear-gradient(135deg, {accent_color} 0%, {accent_hover} 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: {shadow};
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.4);
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {{
            background: {input_bg};
            backdrop-filter: blur(10px);
            border: 1px solid {card_border};
            border-radius: 12px;
            color: {text_primary};
            padding: 12px 16px;
            transition: all 0.3s ease;
        }}
        
        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus {{
            border-color: {accent_color};
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background: {card_bg};
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 8px;
            border: 1px solid {card_border};
        }}
        
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            color: {text_secondary};
            font-weight: 500;
            padding: 12px 24px;
            transition: all 0.3s ease;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: {accent_color};
            color: white;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {text_primary};
            font-size: 32px;
            font-weight: 700;
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {text_secondary};
            font-weight: 500;
        }}
        
        /* Expanders */
        .streamlit-expanderHeader {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 1px solid {card_border};
            color: {text_primary};
            font-weight: 500;
            transition: all 0.3s ease;
        }}
        
        .streamlit-expanderHeader:hover {{
            border-color: {accent_color};
        }}
        
        /* Success/Error Messages */
        .stSuccess, .stError, .stWarning, .stInfo {{
            border-radius: 12px;
            backdrop-filter: blur(10px);
        }}
        
        /* File Uploader */
        [data-testid="stFileUploader"] {{
            background: {card_bg};
            backdrop-filter: blur(10px);
            border-radius: 12px;
            border: 2px dashed {card_border};
            padding: 24px;
            transition: all 0.3s ease;
        }}
        
        [data-testid="stFileUploader"]:hover {{
            border-color: {accent_color};
        }}
        
        /* Headings */
        h1, h2, h3 {{
            color: {text_primary} !important;
            font-weight: 700;
        }}
        
        /* Paragraphs and text */
        p, span, div {{
            color: {text_primary};
        }}
        
        /* Labels */
        label {{
            color: {text_primary} !important;
        }}
        
        /* Captions */
        .stCaption {{
            color: {text_secondary} !important;
        }}
        
        /* Code blocks */
        code {{
            color: {text_primary};
            background: {input_bg};
        }}
        
        /* Spinner */
        .stSpinner > div {{
            border-top-color: {accent_color};
        }}
        
        /* Theme Toggle Button - removed old fixed positioning */
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.1);
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {accent_color};
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {accent_hover};
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease;
        }}
        </style>
    """, unsafe_allow_html=True)

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ścieżka do konfiguracji
CONFIG_FILE = Path("auth_config.json")

# Audit logger
audit_logger = get_audit_logger()

def load_credentials():
    """Ładuje lub tworzy plik z credentials"""
    if not CONFIG_FILE.exists():
        # Domyślne hasło: "admin123"
        default_hash = hashlib.sha256("admin123".encode()).hexdigest()
        creds = {
            "users": {
                "admin": {
                    "password_hash": default_hash,
                    "name": "Administrator"
                }
            }
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(creds, f, indent=2)
        return creds
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def check_password(username: str, password: str) -> bool:
    """Sprawdza poprawność hasła"""
    creds = load_credentials()
    if username not in creds['users']:
        return False
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return creds['users'][username]['password_hash'] == password_hash

def update_password(username: str, new_password: str):
    """Aktualizuje hasło użytkownika"""
    creds = load_credentials()
    if username in creds['users']:
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        creds['users'][username]['password_hash'] = password_hash
        with open(CONFIG_FILE, 'w') as f:
            json.dump(creds, f, indent=2)
        return True
    return False

# Inicjalizacja systemu RAG (cache z TTL)
@st.cache_resource(ttl=10, show_spinner=False)
def init_rag_system():
    """Inicjalizacja systemu RAG (cache na 10s, auto odświeża listę plików)"""
    # Wyłączony spinner przez show_spinner=False w dekoratorze
    return RAGSystem()


def _save_files_flask_style(files_to_process, logger, audit_logger, PROJECT_ROOT, st):
    """
    Zapisuje pliki używając tego samego mechanizmu co Flask (działa!)
    Prosty, bezpośredni zapis bez dodatkowych warstw abstrakcji
    """
    try:
        # Walidacja formatów
        supported_formats = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', 
                           '.mp3', '.wav', '.flac', '.ogg', '.m4a', 
                           '.mp4', '.avi', '.mov', '.mkv', '.webm'}
        
        valid_files = []
        invalid_files = []
        
        for f in files_to_process:
            ext = Path(f.name).suffix.lower()
            if ext in supported_formats:
                valid_files.append(f)
            else:
                invalid_files.append(f.name)
        
        if invalid_files:
            st.error(f"Nieobsługiwane formaty: {', '.join(invalid_files)}")
        
        if not valid_files:
            return
        
        # Zapisz pliki - TAK SAMO JAK W FLASK
        logger.info(f"DIAGNOSTYKA: Zapisywanie {len(valid_files)} plikow (metoda Flask)")
        data_dir = PROJECT_ROOT / "data"
        data_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"DIAGNOSTYKA: data_dir = {data_dir}")
        logger.info(f"DIAGNOSTYKA: data_dir.exists() = {data_dir.exists()}")
        
        saved_names = []
        saved_paths = []
        errors = []
        
        for uploaded_file in valid_files:
            try:
                file_path = data_dir / uploaded_file.name
                logger.info(f"DIAGNOSTYKA: Zapisywanie pliku: {file_path}")
                logger.info(f"DIAGNOSTYKA: Rozmiar pliku: {uploaded_file.size} bytes")
                
                # TAK SAMO JAK W FLASK - bezpośredni zapis
                with open(file_path, 'wb') as f:
                    file_data = uploaded_file.getbuffer()
                    logger.info(f"DIAGNOSTYKA: Zapisuję {len(file_data)} bytes")
                    f.write(file_data)
                
                # Weryfikacja - TAK SAMO JAK W FLASK
                if file_path.exists() and file_path.stat().st_size > 0:
                    logger.info(f"DIAGNOSTYKA: Plik zapisany: {file_path} ({file_path.stat().st_size} bytes)")
                    saved_names.append(uploaded_file.name)
                    saved_paths.append(file_path)
                    
                    # Audit log
                    audit_logger.log_file_upload(
                        user_id=st.session_state.username,
                        filename=uploaded_file.name,
                        file_size=uploaded_file.size,
                        file_type=Path(uploaded_file.name).suffix.lower(),
                        session_id=st.session_state.get('session_id', 'unknown')
                    )
                else:
                    error_msg = f"{uploaded_file.name}: Plik nie został zapisany"
                    errors.append(error_msg)
                    logger.error(f"DIAGNOSTYKA: {error_msg}")
            except Exception as e:
                error_msg = f"{uploaded_file.name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"DIAGNOSTYKA: Błąd zapisu {uploaded_file.name}: {e}", exc_info=True)
        
        if saved_names:
            message = f"Zapisano {len(saved_names)} plik(ów): {', '.join(saved_names)}"
            st.success(message)
            st.toast(f"Zapisano {len(saved_names)} plik(ów)", icon="check")
            logger.info(f"DIAGNOSTYKA: {message}")
            
            # File watcher automatycznie wykryje pliki i zacznie indeksację
            if errors:
                st.warning(f"Ostrzeżenia: {', '.join(errors)}")
        else:
            error_msg = "Nie udało się zapisać żadnych plików"
            if errors:
                error_msg += f": {', '.join(errors)}"
            st.error(error_msg)
            logger.error(f"DIAGNOSTYKA: {error_msg}")
    except Exception as e:
        logger.error(f"DIAGNOSTYKA: Błąd w _save_files_flask_style: {e}", exc_info=True)
        st.error(f"Błąd podczas zapisu: {e}")

def index_files_now(file_paths, progress_callback=None):
    """Natychmiastowe indeksowanie wskazanych plików."""
    if not file_paths:
        return 0
    
    rag = init_rag_system()
    total = len(file_paths)
    indexed_count = 0
    
    for idx, file_path in enumerate(file_paths, start=1):
        stage = "done"
        error = None
        try:
            collection = rag.vector_db.collection
            existing = collection.get(where={"source_file": file_path.name})
            if existing and existing.get('ids'):
                stage = "skip"
            else:
                chunks = rag.doc_processor.process_file(file_path)
                if not chunks:
                    stage = "empty"
                else:
                    chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
                    rag.vector_db.add_documents(chunks_with_embeddings)
                    indexed_count += 1
                    # weryfikacja czy dokument trafił do bazy
                    verify = collection.get(where={"source_file": file_path.name}, include=['ids'])
                    if not verify.get('ids'):
                        logger.warning("Dokument %s nie został odnaleziony po dodaniu.", file_path.name)
                    else:
                        logger.info("Dodano %s (fragmentów: %d)", file_path.name, len(chunks))
        except Exception as exc:
            stage = "error"
            error = exc
            logging.error("Błąd podczas indeksowania %s: %s", file_path.name, exc, exc_info=True)
        finally:
            if progress_callback:
                progress_callback(idx, total, file_path, stage, error)
    
    try:
        rag.rebuild_bm25_index()
    except Exception as exc:
        logging.warning("Błąd podczas przebudowy BM25 po indeksowaniu: %s", exc)
    
    st.cache_resource.clear()
    return indexed_count

def get_gpu_stats():
    """Pobiera statystyki GPU (nie cache - zawsze świeże dane)"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            data = result.stdout.strip().split(',')
            return {
                'name': data[0].strip().replace("NVIDIA GeForce ", ""),
                'mem_total': int(data[1].strip()),
                'mem_used': int(data[2].strip()),
                'utilization': int(data[3].strip()),
                'temperature': int(data[4].strip())
            }
    except:
        pass
    return None

# Cache dla CPU stats (aby interval=None działał poprawnie)
_cpu_last_call = None

def get_cpu_stats():
    """Pobiera statystyki CPU"""
    global _cpu_last_call
    try:
        import psutil
        
        # Pierwsze wywołanie - użyj interval=0.5 dla dokładnego pomiaru
        if _cpu_last_call is None:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            _cpu_last_call = time.time()
        else:
            # Kolejne wywołania - użyj interval=None (szybciej)
            cpu_percent = psutil.cpu_percent(interval=None)
            _cpu_last_call = time.time()
        
        # Jeśli nadal 0, spróbuj z interval=0.3
        if cpu_percent == 0:
            cpu_percent = psutil.cpu_percent(interval=0.3)
        
        logger.debug(f"CPU stats: utilization={cpu_percent}%")
        
        # Temperatura CPU (Linux)
        cpu_temp = None
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                cpu_temp = int(temps['coretemp'][0].current)
            elif 'cpu_thermal' in temps:
                cpu_temp = int(temps['cpu_thermal'][0].current)
            elif temps:
                # Użyj pierwszej dostępnej temperatury
                for key, values in temps.items():
                    if values:
                        cpu_temp = int(values[0].current)
                        break
        except Exception as e:
            logger.debug(f"Nie można pobrać temperatury CPU: {e}")
        
        return {
            'utilization': int(cpu_percent) if cpu_percent > 0 else 0,
            'temperature': cpu_temp
        }
    except Exception as e:
        logger.error(f"Błąd pobierania statystyk CPU: {e}", exc_info=True)
        return None

def get_ram_stats():
    """Pobiera statystyki RAM (rzeczywista pamięć systemowa, nie shared memory GPU)"""
    try:
        import psutil
        # Użyj virtual_memory() - to jest rzeczywista pamięć RAM systemu
        ram = psutil.virtual_memory()
        
        # Weryfikacja - sprawdź czy to nie jest shared memory
        # virtual_memory() powinno zwracać całkowitą pamięć systemu
        total_gb = ram.total / (1024**3)
        used_gb = ram.used / (1024**3)
        available_gb = ram.available / (1024**3)
        
        # Logowanie dla diagnostyki
        logger.info(f"RAM DIAGNOSTYKA: total={total_gb:.1f}GB, used={used_gb:.1f}GB, available={available_gb:.1f}GB, percent={ram.percent}%")
        logger.info(f"RAM DIAGNOSTYKA: ram.total={ram.total} bytes, ram.used={ram.used} bytes")
        
        # Sprawdź czy total jest rozsądne (więcej niż 4GB, mniej niż 1TB)
        if total_gb < 4 or total_gb > 1024:
            logger.warning(f"RAM DIAGNOSTYKA: Podejrzana wartość total={total_gb:.1f}GB - może to nie być rzeczywista pamięć RAM")
        
        return {
            'total': total_gb,      # GB - całkowita pamięć RAM
            'used': used_gb,        # GB - używana pamięć RAM
            'available': available_gb,  # GB - dostępna pamięć RAM
            'percent': int(ram.percent)  # Procent użycia RAM
        }
    except Exception as e:
        logger.error(f"Błąd pobierania statystyk RAM: {e}", exc_info=True)
        return None

def main():
    """Główna funkcja aplikacji"""
    
    # Inicjalizacja session state
    current_time = time.time()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
    if 'auth_expiry' not in st.session_state:
        st.session_state.auth_expiry = 0
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None
    
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    # Parametry modelu
    if 'model_params' not in st.session_state:
        st.session_state.model_params = {
            'temperature': 0.1,
            'top_p': 0.85,
            'top_k': 30,
            'max_tokens': 1000
        }
    
    # Chunk sizes
    if 'chunk_sizes' not in st.session_state:
        st.session_state.chunk_sizes = {
            'text': 500,
            'image_desc': 300,
            'audio': 200
        }
    
    # Whisper model
    if 'whisper_model' not in st.session_state:
        st.session_state.whisper_model = 'base'
    
    # Upload progress
    if 'upload_progress' not in st.session_state:
        st.session_state.upload_progress = {'status': None, 'percent': 0, 'message': ''}
    
    if 'upload_feedback' not in st.session_state:
        st.session_state.upload_feedback = ""
    if 'upload_feedback_shown' not in st.session_state:
        st.session_state.upload_feedback_shown = ""
    if 'processing_status' not in st.session_state:
        st.session_state.processing_status = ""
    if 'pending_uploaded_files' not in st.session_state:
        st.session_state.pending_uploaded_files = []
    if 'processing_status_shown' not in st.session_state:
        st.session_state.processing_status_shown = ""
    
    # Sesje wielokrotne (obsługa odświeżenia)
    session_store = get_session_store()
    # Porządki
    expired_tokens = [token for token, data in session_store.items() if data['expiry'] < current_time]
    for token in expired_tokens:
        session_store.pop(token, None)
    
    qp_value = st.query_params.get("token")
    if isinstance(qp_value, list):
        qp_token = qp_value[0] if qp_value else None
    else:
        qp_token = qp_value
    
    if not st.session_state.authenticated and qp_token and qp_token in session_store:
        session_data = session_store[qp_token]
        if session_data['expiry'] > current_time:
            st.session_state.authenticated = True
            st.session_state.username = session_data['username']
            st.session_state.session_token = qp_token
            st.session_state.auth_expiry = session_data['expiry']
            st.session_state.session_id = session_data.get('session_id', 'unknown')
            session_data['expiry'] = current_time + SESSION_TIMEOUT_SECONDS
        else:
            session_store.pop(qp_token, None)
            if "token" in st.query_params:
                del st.query_params["token"]
    
    # Load CSS
    load_css()
    
    # Theme Toggle (tylko dla zalogowanych)
    session_expired = False
    if st.session_state.authenticated:
        if current_time > st.session_state.get('auth_expiry', 0):
            session_expired = True
            if st.session_state.session_token:
                session_store.pop(st.session_state.session_token, None)
                if "token" in st.query_params:
                    del st.query_params["token"]
                st.session_state.session_token = None
            st.session_state.authenticated = False
            st.session_state.username = None
        else:
            st.session_state.auth_expiry = current_time + SESSION_TIMEOUT_SECONDS
            token = st.session_state.session_token or str(uuid.uuid4())
            st.session_state.session_token = token
            session_store[token] = {
                "username": st.session_state.username,
                "expiry": current_time + SESSION_TIMEOUT_SECONDS,
                "session_id": st.session_state.get('session_id', 'unknown')
            }
            st.query_params["token"] = token

    if st.session_state.authenticated:
        col_theme_1, col_theme_2 = st.columns([8, 2])
        with col_theme_2:
            # Użyj Unicode zamiast emoji dla lepszego wyświetlania
            theme_label = "☀️ Jasny" if st.session_state.theme == 'light' else "🌙 Ciemny"
            if st.button(theme_label, key="theme_toggle", use_container_width=True):
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.rerun()

    if st.session_state.get('upload_feedback') and st.session_state.upload_feedback != st.session_state.upload_feedback_shown:
        st.toast(st.session_state.upload_feedback, icon="✅")
        st.session_state.upload_feedback_shown = st.session_state.upload_feedback
    if st.session_state.get('processing_status') and st.session_state.processing_status != st.session_state.processing_status_shown:
        st.toast(st.session_state.processing_status, icon="ℹ️")
        st.session_state.processing_status_shown = st.session_state.processing_status
    
    # === EKRAN LOGOWANIA ===
    if not st.session_state.authenticated:
        if session_expired:
            st.warning("Sesja wygasła po 10 minutach bezczynności. Zaloguj się ponownie.")
        st.markdown("<div class='fade-in'>", unsafe_allow_html=True)
        st.title("Logowanie do systemu RAG")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("---")
            with st.form("login_form"):
                username = st.text_input("Nazwa użytkownika", placeholder="admin")
                password = st.text_input("Hasło", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Zaloguj", use_container_width=True)
                
                if submit:
                    if check_password(username, password):
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.session_id = str(uuid.uuid4())[:8]
                        token = str(uuid.uuid4())
                        st.session_state.session_token = token
                        session_store[token] = {
                            "username": username,
                            "expiry": time.time() + SESSION_TIMEOUT_SECONDS,
                            "session_id": st.session_state.session_id
                        }
                        st.query_params["token"] = token
                        st.session_state.auth_expiry = time.time() + SESSION_TIMEOUT_SECONDS
                        audit_logger.log_login(user_id=username, success=True)
                        st.success("Zalogowano pomyślnie")
                        st.rerun()
                    else:
                        audit_logger.log_login(user_id=username, success=False)
                        st.error("Nieprawidłowe dane logowania")
        
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # === UŻYTKOWNIK ZALOGOWANY ===
    
    # Sidebar
    with st.sidebar:
        st.title("RAG System")
        creds = load_credentials()
        user_name = creds['users'][st.session_state.username]['name']
        st.write(f"Użytkownik: **{user_name}**")
        
        if st.button("Wyloguj", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            if st.session_state.session_token:
                session_store.pop(st.session_state.session_token, None)
                if "token" in st.query_params:
                    del st.query_params["token"]
            st.session_state.session_token = None
            st.rerun()
        
        st.markdown("---")
        
        # Statystyki bazy
        st.subheader("Statystyki bazy")
        try:
            rag = init_rag_system()
            collection = rag.vector_db.collection
            count = collection.count()
            st.metric("Fragmentów w bazie", f"{count:,}")
            
            # Pobierz metadane
            results = collection.get(limit=count, include=['metadatas'])
            files = set(meta['source_file'] for meta in results['metadatas'])
            st.metric("Dokumentów", len(files))
            
            # Lista plików
            st.subheader("Dokumenty")
            for f in sorted(files):
                st.text(f"• {f}")
                
        except Exception as e:
            st.error(f"Błąd: {e}")
        
        st.markdown("---")
        
        # Dynamiczne informacje o systemie
        st.markdown("### <span style='font-size: 0.9em; color: #888;'>System</span>", unsafe_allow_html=True)
        
        # Auto-refresh co 1 sekundę dla monitoringu
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        # Odświeżaj co 1 sekundę automatycznie
        current_time = time.time()
        refresh_interval = 1
        if current_time - st.session_state.last_refresh > refresh_interval:
            st.session_state.last_refresh = current_time
            st.rerun()
        
        # Placeholder na komunikaty o przetwarzaniu plików
        if st.session_state.get('upload_feedback'):
            st.success(st.session_state.upload_feedback)
            if st.button("Ukryj powiadomienie", key="clear_upload_feedback"):
                st.session_state.upload_feedback = ""
                st.session_state.upload_feedback_shown = ""
                st.rerun()
        if st.session_state.get('processing_status'):
            st.info(st.session_state.processing_status)
            if st.button("Ukryj komunikat", key="clear_processing_status"):
                st.session_state.processing_status = ""
                st.session_state.processing_status_shown = ""
                st.rerun()
        
        # Wykryj GPU i monitoring w czasie rzeczywistym
        gpu_stats = get_gpu_stats()
        cpu_stats = get_cpu_stats()
        ram_stats = get_ram_stats()
        
        # Styl dla metryk systemowych - wartości mają taką samą czcionkę jak opisy
        metric_style = """
        <style>
        .stMetric {
            font-size: 0.85em;
        }
        .stMetric [data-testid="stMetricValue"] {
            font-size: 0.85em !important;
            color: #aaa;
        }
        .stMetric [data-testid="stMetricLabel"] {
            font-size: 0.85em !important;
            color: #aaa;
        }
        </style>
        """
        st.markdown(metric_style, unsafe_allow_html=True)
        
        if gpu_stats:
            st.markdown(f"<span style='font-size: 0.85em; color: #aaa;'>GPU: {gpu_stats['name']}</span>", unsafe_allow_html=True)
            
            # Metryki GPU (odświeżane co 1s) - użycie, VRAM, temperatura
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("GPU", f"{gpu_stats['utilization']}%", label_visibility="visible")
            with col2:
                vram_percent = int(gpu_stats['mem_used']/gpu_stats['mem_total']*100)
                st.metric("VRAM", f"{vram_percent}%", label_visibility="visible")
            with col3:
                st.metric("Temp", f"{gpu_stats['temperature']}°C", label_visibility="visible")
        else:
            st.markdown("<span style='font-size: 0.85em; color: #aaa;'>GPU: CPU (brak NVIDIA)</span>", unsafe_allow_html=True)
        
        # CPU Stats - kolejność: CPU, RAM, Temp
        if cpu_stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("CPU", f"{cpu_stats['utilization']}%", label_visibility="visible")
            with col2:
                # RAM w środku
                if ram_stats:
                    st.metric("RAM", f"{ram_stats['used']:.1f}/{ram_stats['total']:.1f} GB", label_visibility="visible")
                else:
                    st.empty()
            with col3:
                # Temp na końcu
                if cpu_stats['temperature']:
                    st.metric("Temp", f"{cpu_stats['temperature']}°C", label_visibility="visible")
                else:
                    st.metric("Temp", "N/A", label_visibility="visible")
        else:
            # Jeśli brak CPU stats, pokaż tylko RAM
            if ram_stats:
                st.metric("RAM", f"{ram_stats['used']:.1f}/{ram_stats['total']:.1f} GB ({ram_stats['percent']}%)", label_visibility="visible")
        
        # Wykryj model LLM (Ollama)
        try:
            ollama_models = requests.get("http://localhost:11434/api/tags", timeout=1).json()
            if ollama_models.get("models"):
                model_names = [m for m in ollama_models["models"] if "gemma3" in m["name"].lower()]
                if model_names:
                    model_full = model_names[0]["name"]
                    model_parts = model_full.split(":")
                    model_name = model_parts[0].title()
                    
                    # Wykryj quantization
                    quant = ""
                    if len(model_parts) > 1:
                        tag = model_parts[1].lower()
                        if "q4" in tag:
                            quant = "Q4"
                        elif "q8" in tag:
                            quant = "Q8"
                        elif "fp16" in tag or "f16" in tag:
                            quant = "FP16"
                    
                    if quant:
                        st.markdown(f"**Model:** {model_name} ({quant})")
                    else:
                        st.markdown(f"**Model:** {model_name}")
                else:
                    first_model = ollama_models["models"][0]["name"].split(":")[0].title()
                    st.markdown(f"**Model:** {first_model}")
            else:
                st.markdown("**Model:** Gemma 3:12B")
        except:
            st.markdown("**Model:** Gemma 3:12B")
        
        # Informacja o auto-refresh (mniejsza czcionka)
        time_since_refresh = int(current_time - st.session_state.last_refresh)
        next_refresh = refresh_interval - time_since_refresh
        st.markdown(f"<span style='font-size: 0.7em; color: #666;'>Odświeżenie: {next_refresh}s</span>", unsafe_allow_html=True)
        
        # Checkbox do wyświetlania logów
        if 'show_logs' not in st.session_state:
            st.session_state.show_logs = False
        
        st.session_state.show_logs = st.checkbox("Pokaż logi konsoli", value=st.session_state.show_logs)
        
        if st.session_state.show_logs:
            with st.expander("Logi systemu (ostatnie 100 linii)", expanded=True):
                if 'log_source' not in st.session_state:
                    st.session_state.log_source = "rag_system.log"
                log_choice = st.radio(
                    "Źródło logów",
                    options=("rag_system.log", "logs/file_watcher.log"),
                    index=0 if st.session_state.log_source == "rag_system.log" else 1,
                    key="log_source_radio"
                )
                st.session_state.log_source = log_choice
                if log_choice == "rag_system.log":
                    log_path = Path("rag_system.log")
                    fallback = Path("logs/rag_system.log")
                else:
                    log_path = Path("logs/file_watcher.log")
                    fallback = None
                log_content = tail_file(log_path, fallback=fallback)
                if log_content:
                    st.code(log_content, language="log")
                else:
                    st.info("Brak wpisów w wybranym logu")
    
    # Główna zawartość
    st.title("RAG System")
    st.markdown("System odpowiedzi na pytania w oparciu o dokumenty z bazy wiedzy")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["Zapytania", "Indeksowanie", "Ustawienia"])
    
    # === TAB 1: ZAPYTANIA ===
    with tab1:
        st.header("Zadaj pytanie")
        
        # Przykładowe pytania (dynamiczne)
        suggested_questions = load_suggested_questions()
        
        if suggested_questions:
            with st.expander(f"Przykładowe pytania ({len(suggested_questions)} dostępnych)", expanded=False):
                st.markdown("**Kliknij w pytanie aby je zadać:**")
                st.caption("Pytania generowane automatycznie na podstawie zawartości dokumentów")
                st.markdown("---")
                
                # Grupuj pytania po plikach źródłowych
                by_file = {}
                for q in suggested_questions:
                    file = q.get('source_file', 'Nieznane')
                    if file not in by_file:
                        by_file[file] = []
                    by_file[file].append(q['question'])
                
                # Wyświetl pogrupowane
                for file_name, questions in by_file.items():
                    st.markdown(f"**{file_name}** ({len(questions)} pytań)")
                    for idx, q in enumerate(questions):
                        if st.button(q, key=f"suggested_q_{file_name}_{idx}", use_container_width=True):
                            st.session_state['question_input'] = q
                            st.rerun()
                    st.markdown("")
        else:
            with st.expander("Przykładowe pytania (domyślne)"):
                st.markdown("""
                - Co grozi za przestępstwo kradzieży?
                - Jakie są zasady odpowiedzialności karnej?
                - Co znajduje się na obrazach?
                - Jakie dokumenty zawiera baza?
                
                *Po dodaniu dokumentów system automatycznie wygeneruje pytania specyficzne dla Twoich plików*
                """)
        
        # Formularz pytania
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            question = st.text_input(
                "Twoje pytanie:",
                placeholder="Np. Jakie są kary za kradzież?",
                key="question_input"
            )
            # DEBUG: Sprawdź wartość pytania
            logger.info(f"DIAGNOSTYKA: Wartość z text_input: '{question}' (typ: {type(question)}, len: {len(question) if question else 0})")
        
        with col2:
            n_results = st.number_input(
                "Maks. wyników:",
                min_value=1,
                max_value=50,
                value=5,
                key="n_results",
                help="Liczba fragmentów dokumentów do analizy"
            )
        
        with col3:
            search_mode = st.selectbox(
                "Rodzaj wyszukiwania:",
                options=["Wektor + Tekst + Reranking", "Wektor + Tekst", "Wektor", "Tekst"],
                index=0,
                key="search_mode",
                help="Wybierz strategię wyszukiwania dokumentów"
            )
        
        # DEBUG: Sprawdź czy przycisk jest renderowany
        logger.info(f"DIAGNOSTYKA: Renderowanie przycisku 'Szukaj odpowiedzi' (question='{question}', len={len(question) if question else 0})")
        logger.info(f"DIAGNOSTYKA: Session state question_input: '{st.session_state.get('question_input', 'BRAK')}'")
        
        button_clicked = st.button("Szukaj odpowiedzi", type="primary", use_container_width=True, key="search_button")
        logger.info(f"DIAGNOSTYKA: Przycisk kliknięty: {button_clicked}")
        logger.info(f"DIAGNOSTYKA: Session state search_button: {st.session_state.get('search_button', 'BRAK')}")
        
        # Inicjalizuj flagę wyszukiwania w session state
        if 'should_search' not in st.session_state:
            st.session_state.should_search = False
        
        # Jeśli przycisk został kliknięty, ustaw flagę wyszukiwania
        if button_clicked:
            st.session_state.should_search = True
            logger.info("DIAGNOSTYKA: Flaga should_search ustawiona na True")
        
        # Wykonaj wyszukiwanie jeśli flaga jest ustawiona
        if st.session_state.should_search:
            logger.info(f"DIAGNOSTYKA: Wewnątrz if should_search, question='{question}'")
            if not question:
                logger.warning("DIAGNOSTYKA: Pytanie jest puste!")
                st.warning("Proszę wprowadzić pytanie")
                # Reset flagi gdy pytanie jest puste i odśwież interfejs
                st.session_state.should_search = False
                st.rerun()
            else:
                logger.info(f"DIAGNOSTYKA: Użytkownik zadał pytanie: '{question}'")
                with st.spinner("Szukam odpowiedzi... (może potrwać 30-60 sekund)"):
                    try:
                        logger.info("DIAGNOSTYKA: Inicjalizacja systemu RAG...")
                        rag = init_rag_system()
                        logger.info("DIAGNOSTYKA: System RAG zainicjalizowany")
                        
                        # Wybierz strategię wyszukiwania na podstawie wyboru użytkownika
                        from rag_system import SourceReference
                        
                        logger.info(f"DIAGNOSTYKA: Wybrana strategia wyszukiwania: {search_mode}")
                        
                        if search_mode == "Wektor":
                            logger.info("DIAGNOSTYKA: Wyszukiwanie wektorowe...")
                            # Tylko wyszukiwanie wektorowe (zwraca SourceReference)
                            try:
                                sources = rag.vector_db.search(question, n_results)
                                logger.info(f"DIAGNOSTYKA: Wyszukiwanie wektorowe zakończone: {len(sources)} wyników")
                            except Exception as e:
                                logger.error(f"DIAGNOSTYKA: Błąd wyszukiwania wektorowego: {e}", exc_info=True)
                                st.error(f"Błąd wyszukiwania wektorowego: {e}")
                                sources = []
                        elif search_mode == "Tekst":
                            logger.info("DIAGNOSTYKA: Wyszukiwanie BM25 (tekstowe)...")
                            # Tylko BM25 (tekstowe) - zwraca dict, trzeba przekonwertować
                            if hasattr(rag, 'hybrid_search') and rag.hybrid_search:
                                hybrid_results = rag.hybrid_search.search_bm25_only(question, n_results)
                                # Konwertuj dict do SourceReference
                                sources = []
                                for doc in hybrid_results:
                                    # BM25 zwraca 'bm25_score'
                                    score = doc.get('bm25_score') or doc.get('score', 0.5)
                                    sources.append(SourceReference(
                                        content=doc.get('content', ''),
                                        source_file=doc.get('metadata', {}).get('source_file', ''),
                                        page_number=doc.get('metadata', {}).get('page', 0),
                                        element_id=doc.get('metadata', {}).get('element_id', ''),
                                        distance=1.0 - score
                                    ))
                            else:
                                st.warning("BM25 search niedostępny, używam wyszukiwania wektorowego")
                                sources = rag.vector_db.search(question, n_results)
                        elif search_mode == "Wektor + Tekst":
                            logger.info("DIAGNOSTYKA: Wyszukiwanie hybrydowe (bez rerankingu)...")
                            # Hybrydowe bez rerankingu - zwraca dict, trzeba przekonwertować
                            if hasattr(rag, 'hybrid_search') and rag.hybrid_search:
                                try:
                                    hybrid_results = rag.hybrid_search.search(question, n_results, use_reranker=False)
                                    logger.info(f"DIAGNOSTYKA: Hybrydowe wyszukiwanie zakończone: {len(hybrid_results)} wyników")
                                except Exception as e:
                                    logger.error(f"DIAGNOSTYKA: Błąd hybrydowego wyszukiwania: {e}", exc_info=True)
                                    st.error(f"Błąd hybrydowego wyszukiwania: {e}")
                                    hybrid_results = []
                                
                                # Konwertuj dict do SourceReference
                                sources = []
                                if hybrid_results:
                                    for doc in hybrid_results:
                                        # Sprawdź różne możliwe klucze dla score
                                        score = doc.get('rrf_score') or doc.get('bm25_score') or doc.get('score', 0.5)
                                        sources.append(SourceReference(
                                            content=doc.get('content', ''),
                                            source_file=doc.get('metadata', {}).get('source_file', ''),
                                            page_number=doc.get('metadata', {}).get('page', 0),
                                            element_id=doc.get('metadata', {}).get('element_id', ''),
                                            distance=1.0 - score
                                        ))
                            else:
                                sources = rag.vector_db.search(question, n_results)
                        else:  # "Wektor + Tekst + Reranking"
                            logger.info("DIAGNOSTYKA: Wyszukiwanie hybrydowe (z rerankerem)...")
                            # Pełne hybrydowe z rerankerem - zwraca dict, trzeba przekonwertować
                            if hasattr(rag, 'hybrid_search') and rag.hybrid_search:
                                try:
                                    hybrid_results = rag.hybrid_search.search(question, n_results, use_reranker=True)
                                    logger.info(f"DIAGNOSTYKA: Hybrydowe wyszukiwanie z rerankerem zakończone: {len(hybrid_results)} wyników")
                                except Exception as e:
                                    logger.error(f"DIAGNOSTYKA: Błąd hybrydowego wyszukiwania z rerankerem: {e}", exc_info=True)
                                    st.error(f"Błąd hybrydowego wyszukiwania z rerankerem: {e}")
                                    hybrid_results = []
                                
                                # Konwertuj dict do SourceReference
                                sources = []
                                if hybrid_results:
                                    for doc in hybrid_results:
                                        # Sprawdź różne możliwe klucze dla score
                                        score = doc.get('rerank_score') or doc.get('rrf_score') or doc.get('bm25_score') or doc.get('score', 0.5)
                                        sources.append(SourceReference(
                                            content=doc.get('content', ''),
                                            source_file=doc.get('metadata', {}).get('source_file', ''),
                                            page_number=doc.get('metadata', {}).get('page', 0),
                                            element_id=doc.get('metadata', {}).get('element_id', ''),
                                            distance=1.0 - score
                                        ))
                            else:
                                sources = rag.vector_db.search(question, n_results)
                        
                        logger.info(f"DIAGNOSTYKA: Znaleziono {len(sources)} źródeł (typ: {type(sources[0]) if sources else 'brak'})")
                        
                        # DEBUG: Wyświetl źródła
                        if sources:
                            logger.info("DIAGNOSTYKA: Znalezione źródła:")
                            for i, src in enumerate(sources[:5], 1):  # Pokaż pierwsze 5
                                logger.info(f"  [{i}] {src.source_file} (strona: {src.page_number}, element: {src.element_id[:50] if src.element_id else 'brak'})")
                                logger.info(f"      Fragment: {src.content[:100]}...")
                        
                        # PRIORYTETYZACJA: Jeśli pytanie dotyczy filmu/wideo, priorytetyzuj wyniki z plików wideo
                        question_lower = question.lower()
                        video_keywords = ['film', 'wideo', 'video', 'movie', 'nagranie', 'klip', 'filmie', 'wideo']
                        is_video_question = any(keyword in question_lower for keyword in video_keywords)
                        
                        if is_video_question and sources:
                            logger.info("DIAGNOSTYKA: Pytanie dotyczy filmu - priorytetyzuję wyniki z plików wideo")
                            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
                            
                            # Podziel źródła na wideo i inne
                            video_sources = []
                            other_sources = []
                            
                            for src in sources:
                                file_ext = Path(src.source_file).suffix.lower()
                                element_id_lower = (src.element_id or '').lower()
                                if file_ext in video_extensions or 'video' in element_id_lower:
                                    video_sources.append(src)
                                else:
                                    other_sources.append(src)
                            
                            # Jeśli znaleziono źródła z wideo, użyj ich jako priorytet
                            if video_sources:
                                logger.info(f"DIAGNOSTYKA: Znaleziono {len(video_sources)} źródeł z wideo, {len(other_sources)} z innych plików")
                                # Użyj wszystkich źródeł z wideo + część z innych (maksymalnie n_results)
                                sources = video_sources + other_sources[:max(1, n_results - len(video_sources))]
                                logger.info(f"DIAGNOSTYKA: Po priorytetyzacji: {len(sources)} źródeł ({len(video_sources)} z wideo)")
                            else:
                                logger.info("DIAGNOSTYKA: Nie znaleziono źródeł z wideo, używam wszystkich wyników")
                        
                        # Wygeneruj odpowiedź (użyj parametrów z ustawień)
                        # WAŻNE: Przekaż już znalezione sources, aby uniknąć podwójnego wyszukiwania
                        params = st.session_state.model_params
                        logger.info(f"DIAGNOSTYKA: Przekazuję {len(sources)} znalezionych źródeł do rag.query()")
                        logger.info(f"DIAGNOSTYKA: Rozpoczynam generowanie odpowiedzi...")
                        
                        if not sources:
                            logger.warning("DIAGNOSTYKA: Brak źródeł do przekazania - wyszukiwanie nie zwróciło wyników")
                            st.warning("Nie znaleziono odpowiednich dokumentów w bazie. Spróbuj zmienić pytanie lub strategię wyszukiwania.")
                            answer = "Nie znaleziono odpowiednich informacji w bazie danych."
                            # Zapisz odpowiedź w session state
                            st.session_state['last_answer'] = answer
                            st.session_state['last_sources'] = []
                            st.session_state['last_question'] = question
                            # Wyświetl odpowiedź
                            st.markdown("### Odpowiedź:")
                            st.markdown(answer)
                            # Reset flagi nawet gdy brak wyników i odśwież interfejs
                            st.session_state.should_search = False
                            st.rerun()
                        else:
                            try:
                                answer = rag.query(
                                    question, 
                                    n_results=n_results,
                                    user_id=st.session_state.username,
                                    session_id=st.session_state.get('session_id', 'unknown'),
                                    temperature=params['temperature'],
                                    top_p=params['top_p'],
                                    top_k=params['top_k'],
                                    max_tokens=params['max_tokens'],
                                    sources=sources  # Przekaż już znalezione sources
                                )
                                logger.info(f"DIAGNOSTYKA: Odpowiedź wygenerowana (długość: {len(answer)} znaków)")
                            except Exception as e:
                                logger.error(f"DIAGNOSTYKA: Błąd podczas generowania odpowiedzi: {e}", exc_info=True)
                                st.error(f"Błąd podczas generowania odpowiedzi: {e}")
                                answer = f"Wystąpił błąd podczas generowania odpowiedzi: {str(e)}"
                                # Zapisz odpowiedź w session state
                                st.session_state['last_answer'] = answer
                                st.session_state['last_sources'] = sources
                                st.session_state['last_question'] = question
                                # Wyświetl odpowiedź
                                st.markdown("### Odpowiedź:")
                                st.markdown(answer)
                                # Reset flagi w przypadku błędu i odśwież interfejs
                                st.session_state.should_search = False
                                st.rerun()
                        
                        # Zapisz w session state (tylko jeśli nie było błędu - w przypadku błędu już zapisaliśmy)
                        if 'last_answer' not in st.session_state or st.session_state.get('last_answer') != answer:
                            st.session_state['last_answer'] = answer
                            st.session_state['last_sources'] = sources
                            st.session_state['last_question'] = question
                            logger.info("DIAGNOSTYKA: Odpowiedź zapisana w session state")
                        
                        # WAŻNE: Zapisz do historii
                        if 'history' not in st.session_state:
                            st.session_state.history = []
                        st.session_state.history.append({
                            'question': question,
                            'answer': answer,
                            'sources_count': len(sources),
                            'search_mode': search_mode
                        })
                        
                        # Wyświetl odpowiedź
                        logger.info("DIAGNOSTYKA: Wyświetlanie odpowiedzi w interfejsie...")
                        st.success(f"Odpowiedź wygenerowana (strategia: {search_mode})")
                        st.markdown("### Odpowiedź:")
                        st.markdown(answer)
                        logger.info("DIAGNOSTYKA: Odpowiedź wyświetlona w interfejsie")
                        
                        # Wyświetl źródła z możliwością podglądu
                        st.markdown("---")
                        st.markdown(f"### Źródła ({len(sources)} dokumentów):")
                        
                        for i, source in enumerate(sources):
                            with st.expander(f"[{i+1}] {source.source_file} - Strona {source.page_number}"):
                                # Wyświetl fragment tekstu
                                st.markdown("**Fragment:**")
                                st.text_area("Fragment tekstu", source.content, height=150, key=f"content_{i}", disabled=True, label_visibility="collapsed")
                                
                                # Sprawdź czy to obraz czy PDF
                                file_path = PROJECT_ROOT / "data" / source.source_file
                                
                                if file_path.exists():
                                    file_ext = file_path.suffix.lower()
                                    
                                    # OBRAZY
                                    if file_ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                                        st.markdown("**Podgląd obrazu:**")
                                        st.image(str(file_path), use_container_width=True)
                                    
                                    # PDF
                                    elif file_ext == '.pdf':
                                        st.markdown(f"**Plik PDF - Strona {source.page_number}**")
                                        
                                        # Przycisk do pobrania
                                        with open(file_path, 'rb') as f:
                                            pdf_bytes = f.read()
                                            st.download_button(
                                                label="Pobierz pełny PDF",
                                                data=pdf_bytes,
                                                file_name=source.source_file,
                                                mime="application/pdf",
                                                key=f"download_{i}"
                                            )
                                        
                                        # Wyświetl konkretną stronę
                                        try:
                                            import fitz  # PyMuPDF
                                            doc = fitz.open(str(file_path))
                                            page_num = source.page_number - 1
                                            
                                            if 0 <= page_num < len(doc):
                                                page = doc[page_num]
                                                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                                                img_bytes = pix.tobytes("png")
                                                
                                                st.markdown(f"**Podgląd strony {source.page_number}:**")
                                                st.image(img_bytes, use_container_width=True)
                                            else:
                                                st.warning(f"Strona {source.page_number} nie istnieje w dokumencie")
                                            
                                            doc.close()
                                        except ImportError:
                                            st.info("Zainstaluj PyMuPDF aby zobaczyć podgląd strony: pip install PyMuPDF")
                                        except Exception as e:
                                            st.error(f"Błąd podczas ładowania strony PDF: {e}")
                                else:
                                    st.warning(f"Plik nie istnieje: {file_path}")
                        
                        # WAŻNE: Wyczyść flagę wyszukiwania i odśwież interfejs, aby umożliwić kolejne wyszukiwania
                        # Musi być na końcu, po wyświetleniu wszystkich wyników
                        st.session_state.should_search = False
                        logger.info("DIAGNOSTYKA: Flaga should_search zresetowana na False - odświeżam interfejs")
                        # Odśwież interfejs, aby umożliwić kolejne kliknięcia
                        st.rerun()
                        
                    except Exception as e:
                        error_msg = f"Błąd podczas przetwarzania pytania: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"BŁĄD W APLIKACJI: {error_msg}", exc_info=True)
                        import traceback
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        # Wyświetl szczegóły błędu dla użytkownika
                        with st.expander("Szczegóły błędu (kliknij aby rozwinąć)"):
                            st.code(traceback.format_exc())
        
        # Historia
        st.markdown("---")
        st.subheader("Historia zapytań")
        
        if 'history' not in st.session_state:
            st.session_state.history = []
        
        if st.session_state.history:
            for i, item in enumerate(reversed(st.session_state.history[-5:])):
                with st.expander(f"{item['question'][:50]}..."):
                    st.markdown(f"**Pytanie:** {item['question']}")
                    st.markdown(f"**Odpowiedź:** {item['answer'][:200]}...")
        else:
            st.info("Brak historii zapytań")
    
    # === TAB 2: INDEKSOWANIE ===
    with tab2:
        st.header("Zarządzanie dokumentami")
        
        if st.session_state.get('upload_feedback'):
            st.success(st.session_state.upload_feedback)
        if st.session_state.get('processing_status'):
            st.info(st.session_state.processing_status)
        
        st.markdown("""
        System automatycznie indeksuje nowe pliki i aktualizuje bazę po dodaniu/usunięciu dokumentów.
        
        **Obsługiwane formaty:** 
        - Dokumenty: PDF, DOCX, XLSX (+ obrazy/wykresy wewnątrz)
        - Obrazy: JPG, JPEG, PNG, BMP
        - Audio: MP3, WAV, FLAC, OGG, M4A (transkrypcja Whisper + mówcy)
        - Wideo: MP4, AVI, MOV, MKV, WEBM (audio Whisper + klatki Gemma 3)
        """)
        
        # Upload nowych plików - UŻYWAMY FLASK ENDPOINT PRZEZ HTML KOMPONENT
        st.subheader("Dodaj nowe dokumenty")
        logger.info("=" * 60)
        logger.info("DIAGNOSTYKA: Upload section - start (Flask endpoint)")
        
        # Uruchom Flask endpoint w tle
        get_flask_upload_endpoint()
        
        # Sprawdź status uploadu z session_state
        if 'upload_status' in st.session_state:
            if st.session_state.upload_status.get('success'):
                st.success(f"Zapisano: {', '.join(st.session_state.upload_status.get('saved', []))}")
                if st.session_state.upload_status.get('errors'):
                    st.warning(f"Ostrzeżenia: {', '.join(st.session_state.upload_status['errors'])}")
                st.session_state.upload_status = None  # Wyczyść po wyświetleniu
            else:
                st.error(f"Błąd: {st.session_state.upload_status.get('error', 'Nieznany błąd')}")
                st.session_state.upload_status = None
        
        # HTML komponent z formularzem uploadu (Flask endpoint)
        upload_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .upload-container {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                .upload-area {{
                    border: 2px dashed #6366f1;
                    border-radius: 10px;
                    padding: 40px;
                    text-align: center;
                    background: rgba(99, 102, 241, 0.05);
                    cursor: pointer;
                    transition: all 0.3s;
                }}
                .upload-area:hover {{
                    background: rgba(99, 102, 241, 0.1);
                    border-color: #818cf8;
                }}
                .upload-area.dragover {{
                    background: rgba(99, 102, 241, 0.2);
                    border-color: #818cf8;
                }}
                input[type="file"] {{
                    display: none;
                }}
                .upload-button {{
                    background: #6366f1;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    margin-top: 20px;
                }}
                .upload-button:hover {{
                    background: #818cf8;
                }}
                .upload-button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                }}
                .status {{
                    margin-top: 15px;
                    padding: 10px;
                    border-radius: 5px;
                    display: none;
                }}
                .status.success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                    display: block;
                }}
                .status.error {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    display: block;
                }}
            </style>
        </head>
        <body>
            <div class="upload-container">
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                    <p style="font-size: 18px; margin: 0;">📁 Przeciągnij pliki tutaj lub kliknij aby wybrać</p>
                    <p style="color: #666; font-size: 14px; margin-top: 10px;">Limit: 200MB na plik</p>
                </div>
                <input type="file" id="fileInput" multiple>
                <button class="upload-button" id="uploadButton" onclick="uploadFiles()">Zapisz pliki</button>
                <div id="status" class="status"></div>
            </div>
            
            <script>
                const uploadArea = document.getElementById('uploadArea');
                const fileInput = document.getElementById('fileInput');
                const uploadButton = document.getElementById('uploadButton');
                const statusDiv = document.getElementById('status');
                
                // Drag and drop
                uploadArea.addEventListener('dragover', (e) => {{
                    e.preventDefault();
                    uploadArea.classList.add('dragover');
                }});
                
                uploadArea.addEventListener('dragleave', () => {{
                    uploadArea.classList.remove('dragover');
                }});
                
                uploadArea.addEventListener('drop', (e) => {{
                    e.preventDefault();
                    uploadArea.classList.remove('dragover');
                    fileInput.files = e.dataTransfer.files;
                    updateFileList();
                }});
                
                fileInput.addEventListener('change', () => {{
                    updateFileList();
                }});
                
                function updateFileList() {{
                    const files = fileInput.files;
                    if (files.length > 0) {{
                        uploadArea.innerHTML = `<p style="font-size: 18px; margin: 0;">Wybrano ${{files.length}} plik(ów)</p>`;
                        for (let i = 0; i < files.length; i++) {{
                            uploadArea.innerHTML += `<p style="color: #666; font-size: 14px; margin: 5px 0;">• ${{files[i].name}} (${{(files[i].size / 1024).toFixed(1)}} KB)</p>`;
                        }}
                    }}
                }}
                
                async function uploadFiles() {{
                    const files = fileInput.files;
                    if (files.length === 0) {{
                        showStatus('Nie wybrano żadnych plików', 'error');
                        return;
                    }}
                    
                    uploadButton.disabled = true;
                    uploadButton.textContent = 'Zapisywanie...';
                    showStatus('Zapisywanie plików...', 'success');
                    
                    const formData = new FormData();
                    for (let file of files) {{
                        formData.append('files', file);
                    }}
                    
                    try {{
                        const response = await fetch('http://localhost:{FLASK_UPLOAD_PORT}/upload', {{
                            method: 'POST',
                            body: formData,
                            mode: 'cors'
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{response.statusText}}`);
                        }}
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showStatus(`Zapisano ${{result.saved.length}} plik(ów): ${{result.saved.join(', ')}}`, 'success');
                            // Odśwież Streamlit
                            setTimeout(() => {{
                                window.parent.postMessage({{type: 'streamlit:setFrameHeight', height: 0}}, '*');
                                window.location.reload();
                            }}, 1500);
                        }} else {{
                            showStatus(`Błąd: ${{result.error}}`, 'error');
                            uploadButton.disabled = false;
                            uploadButton.textContent = 'Zapisz pliki';
                        }}
                    }} catch (error) {{
                        // Sprawdź czy to błąd CORS czy inny
                        const errorMsg = error.message.includes('Failed to fetch') || error.message.includes('CORS') 
                            ? 'Błąd połączenia z serwerem. Plik może być zapisany - sprawdź folder data/'
                            : `Błąd: ${{error.message}}`;
                        showStatus(errorMsg, 'error');
                        uploadButton.disabled = false;
                        uploadButton.textContent = 'Zapisz pliki';
                        console.error('Upload error:', error);
                    }}
                }}
                
                function showStatus(message, type) {{
                    statusDiv.textContent = message;
                    statusDiv.className = 'status ' + type;
                }}
            </script>
        </body>
        </html>
        '''
        
        components.html(upload_html, height=300)
        
        # Przycisk do ręcznego odświeżenia (opcjonalny)
        if st.button("Odśwież listę plików"):
            st.rerun()
        
        st.markdown("---")
        
        # Ręczna reindeksacja wszystkich plików
        st.subheader("Reindeksacja")
        st.markdown("**Jeśli pliki nie zostały automatycznie zaindeksowane, możesz wymusić reindeksację:**")
        
        col_reindex, col_spacer = st.columns([1, 3])
        with col_reindex:
            logger.info("DIAGNOSTYKA: Przygotowanie przycisku 'Reindeksuj wszystkie pliki'")
            if st.button("Reindeksuj wszystkie pliki", type="secondary", use_container_width=True):
                logger.info("=" * 60)
                logger.info("DIAGNOSTYKA: PRZYCISK 'Reindeksuj wszystkie pliki' KLIKNIETY!")
                logger.info(f"  PROJECT_ROOT: {PROJECT_ROOT}")
                logger.info(f"  session_state.pending_uploaded_files: {st.session_state.get('pending_uploaded_files', 'BRAK')}")
                st.session_state.processing_status = (
                    "Tworzenie bazy dla istniejących plików (ręczna reindeksacja)... "
                    "Postęp możesz śledzić w logach."
                )
                with st.spinner("Reindeksowanie plików w toku..."):
                    try:
                        data_dir = PROJECT_ROOT / "data"
                        logger.info(f"DIAGNOSTYKA: data_dir = {data_dir}")
                        logger.info(f"DIAGNOSTYKA: data_dir.exists() = {data_dir.exists()}")
                        supported_formats = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', 
                                           '.mp3', '.wav', '.flac', '.ogg', '.m4a',
                                           '.mp4', '.avi', '.mov', '.mkv', '.webm'}
                        
                        all_files = list(data_dir.glob('*'))
                        logger.info(f"DIAGNOSTYKA: Wszystkie pliki w data/: {len(all_files)}")
                        for f in all_files:
                            logger.info(f"  - {f.name} (is_file: {f.is_file()}, suffix: {f.suffix.lower()})")
                        
                        files_to_process = [f for f in data_dir.glob('*') 
                                          if f.is_file() and f.suffix.lower() in supported_formats]
                        logger.info(f"DIAGNOSTYKA: Pliki do przetworzenia: {len(files_to_process)}")
                        
                        if files_to_process:
                            rag = init_rag_system()
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            success_count = 0
                            for idx, file_path in enumerate(files_to_process):
                                try:
                                    progress = (idx + 1) / len(files_to_process)
                                    progress_bar.progress(progress)
                                    status_text.text(f"Indeksowanie: {file_path.name} ({idx + 1}/{len(files_to_process)})")
                                    
                                    # Sprawdź czy plik już jest w bazie
                                    collection = rag.vector_db.collection
                                    existing = collection.get(where={"source_file": file_path.name})
                                    
                                    if existing and len(existing['ids']) > 0:
                                        status_text.text(f"Pomijam (już w bazie): {file_path.name}")
                                        time.sleep(0.5)
                                        continue
                                    
                                    # Przetwórz plik
                                    chunks = rag.doc_processor.process_file(file_path)
                                    if chunks:
                                        chunks_with_embeddings = rag.embedding_processor.create_embeddings(chunks)
                                        rag.vector_db.add_documents(chunks_with_embeddings)
                                        success_count += 1
                                        
                                except Exception as e:
                                    st.error(f"Błąd przy {file_path.name}: {e}")
                            
                            progress_bar.empty()
                            status_text.empty()
                            
                            if success_count > 0:
                                st.success(f"✅ Zaindeksowano {success_count} nowych plików")
                                st.session_state.processing_status = "Reindeksacja zakończona."
                                # Przebuduj BM25 index
                                try:
                                    rag.rebuild_bm25_index()
                                except:
                                    pass
                                st.cache_resource.clear()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.info("Wszystkie pliki już są w bazie")
                                st.session_state.processing_status = ""
                        else:
                            st.warning("Brak plików do zindeksowania w folderze data/")
                            st.session_state.processing_status = ""
                            
                    except Exception as e:
                        st.error(f"Błąd podczas reindeksacji: {e}")
        
        st.markdown("---")
        
        # Zarządzanie istniejącymi plikami
        st.subheader("Dokumenty w bazie")
        
        col_refresh, col_spacer = st.columns([1, 3])
        with col_refresh:
            logger.info("DIAGNOSTYKA: Przygotowanie przycisku 'Odswiez liste'")
            if st.button("Odśwież listę", help="Odśwież listę plików z bazy"):
                logger.info("=" * 60)
                logger.info("DIAGNOSTYKA: PRZYCISK 'Odswiez liste' KLIKNIETY!")
                logger.info(f"  session_state.pending_uploaded_files: {st.session_state.get('pending_uploaded_files', 'BRAK')}")
                logger.info(f"  session_state.file_uploader: {st.session_state.get('file_uploader', 'BRAK')}")
                st.cache_resource.clear()
                st.rerun()
        
        try:
            rag = init_rag_system()
            collection = rag.vector_db.collection
            all_data = collection.get(include=['metadatas'])
            
            # Zbierz unikalne pliki
            files_in_db = {}
            for meta in all_data['metadatas']:
                file_name = meta['source_file']
                if file_name not in files_in_db:
                    files_in_db[file_name] = 0
                files_in_db[file_name] += 1
            
            if files_in_db:
                st.write(f"**Znaleziono {len(files_in_db)} dokumentów w bazie:**")
                
                if 'files_to_delete' not in st.session_state:
                    st.session_state.files_to_delete = []
                
                # Wyświetl tabelę z plikami
                for file_name, chunk_count in sorted(files_in_db.items()):
                    col1, col2, col3 = st.columns([0.7, 2, 1])
                    
                    with col1:
                        is_checked = st.checkbox(
                            "Usuń",
                            key=f"del_{file_name}",
                            label_visibility="collapsed"
                        )
                        if is_checked and file_name not in st.session_state.files_to_delete:
                            st.session_state.files_to_delete.append(file_name)
                        elif not is_checked and file_name in st.session_state.files_to_delete:
                            st.session_state.files_to_delete.remove(file_name)
                    
                    with col2:
                        st.markdown(f"**{file_name}**")
                    
                    with col3:
                        st.caption(f"{chunk_count} fragmentów")
                
                # Przycisk usuwania zaznaczonych
                if st.session_state.files_to_delete:
                    st.markdown("---")
                    st.warning(f"Zaznaczono {len(st.session_state.files_to_delete)} plik(ów) do usunięcia")
                    
                    if st.button(f"Usuń zaznaczone pliki ({len(st.session_state.files_to_delete)})", 
                                use_container_width=True, type="secondary"):
                        with st.spinner("Usuwanie plików i aktualizacja bazy..."):
                            deleted_count = 0
                            
                            for file_name in st.session_state.files_to_delete:
                                try:
                                    file_path = PROJECT_ROOT / "data" / file_name
                                    if file_path.exists():
                                        file_path.unlink()
                                        logger.info(f"Usunięto plik: {file_name}")
                                    
                                    # Usuń z bazy wektorowej
                                    ids_to_delete = []
                                    for idx, meta in enumerate(all_data['metadatas']):
                                        if meta['source_file'] == file_name:
                                            ids_to_delete.append(all_data['ids'][idx])
                                    
                                    if ids_to_delete:
                                        collection.delete(ids=ids_to_delete)
                                        logger.info(f"Usunięto {len(ids_to_delete)} fragmentów z bazy dla {file_name}")
                                    
                                    deleted_count += 1
                                    
                                    audit_logger.log_file_delete(
                                        user_id=st.session_state.username,
                                        filename=file_name,
                                        session_id=st.session_state.get('session_id', 'unknown')
                                    )
                                    
                                except Exception as e:
                                    st.error(f"Błąd usuwania {file_name}: {e}")
                                    logger.error(f"Błąd usuwania {file_name}: {e}")
                            
                            if deleted_count > 0:
                                st.success(f"Usunięto {deleted_count} plik(ów)")
                                st.session_state.files_to_delete = []
                                st.cache_resource.clear()
                                time.sleep(1)
                                st.rerun()
            else:
                st.info("Baza jest pusta. Dodaj dokumenty powyżej")
                
        except Exception as e:
            st.error(f"Błąd: {e}")
            logger.error(f"Błąd zarządzania plikami: {e}")
    
    # === TAB 3: USTAWIENIA ===
    with tab3:
        st.header("Ustawienia")
        
        st.subheader("Zmiana hasła")
        st.info("Domyślne hasło: **admin123**")
        
        with st.form("change_password"):
            current_password = st.text_input("Aktualne hasło", type="password")
            new_password = st.text_input("Nowe hasło", type="password")
            new_password_confirm = st.text_input("Potwierdź nowe hasło", type="password")
            
            if st.form_submit_button("Zmień hasło"):
                if not check_password(st.session_state.username, current_password):
                    st.error("Nieprawidłowe aktualne hasło")
                elif not new_password:
                    st.error("Nowe hasło nie może być puste")
                elif new_password != new_password_confirm:
                    st.error("Hasła nie są identyczne")
                elif len(new_password) < 6:
                    st.error("Hasło musi mieć minimum 6 znaków")
                else:
                    if update_password(st.session_state.username, new_password):
                        st.success("Hasło zmienione pomyślnie")
                        st.info("Zaloguj się ponownie z nowym hasłem")
                    else:
                        st.error("Błąd podczas zmiany hasła")
        
        st.markdown("---")
        
        st.subheader("Model API (OpenAI)")
        
        # Wczytaj obecną konfigurację
        config = load_credentials()
        openai_cfg = config.get('openai', {})
        current_key = openai_cfg.get('api_key', '')
        current_model = openai_cfg.get('model', '')
        
        # Maskuj klucz
        masked_key = current_key[:12] + "..." + current_key[-4:] if len(current_key) > 16 else current_key
        
        with st.form("openai_config"):
            st.markdown("**OpenAI API (opcjonalne)**")
            st.info("Zostaw puste aby używać lokalnego modelu Ollama (Gemma 3:12B)")
            
            api_key_input = st.text_input(
                "API Key",
                value=masked_key if current_key else "",
                type="password",
                help="Klucz API z platform.openai.com"
            )
            
            model_help = "Model zostanie automatycznie wybrany (gpt-4o-mini) jeśli pozostawisz puste"
            
            if current_key and api_key_input == masked_key:
                model_input = st.text_input(
                    "Model (opcjonalnie)",
                    value=current_model,
                    help=model_help
                )
            else:
                model_input = st.text_input(
                    "Model (opcjonalnie)",
                    value="",
                    placeholder="np. gpt-4o-mini (zostaw puste dla auto)",
                    help=model_help
                )
            
            st.caption("""
            **Szacunkowe koszty (gpt-4o-mini)**:
            - Input: $0.15 / 1M tokens
            - Output: $0.60 / 1M tokens
            - ~100 zapytań: $0.50-2.00
            """)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                submit_btn = st.form_submit_button("Zapisz ustawienia API", use_container_width=True)
            
            with col2:
                clear_btn = st.form_submit_button("Usuń klucz API", use_container_width=True)
            
            if submit_btn:
                try:
                    if api_key_input and api_key_input != masked_key:
                        new_key = api_key_input.strip()
                    elif api_key_input == masked_key:
                        new_key = current_key
                    else:
                        new_key = ""
                    
                    config['openai'] = {
                        'api_key': new_key,
                        'model': model_input.strip() if model_input else "",
                        'enabled': bool(new_key)
                    }
                    
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    st.success("Ustawienia zapisane! Odśwież stronę aby zastosować zmiany")
                    st.info("Naciśnij F5 lub kliknij przycisk odśwież w przeglądarce")
                    
                except Exception as e:
                    st.error(f"Błąd podczas zapisywania: {e}")
            
            if clear_btn:
                try:
                    config['openai'] = {
                        'api_key': '',
                        'model': '',
                        'enabled': False
                    }
                    
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)
                    
                    st.success("Klucz API usunięty! Używam Ollama (lokalny model)")
                    st.info("Odśwież stronę aby zastosować zmiany (F5)")
                    
                except Exception as e:
                    st.error(f"Błąd podczas usuwania: {e}")
        
        st.markdown("---")
        
        # Parametry modelu LLM
        st.subheader("Parametry modelu LLM")
        st.info("Parametry wpływają na sposób generowania odpowiedzi przez model")
        
        col1, col2 = st.columns(2)
        
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=st.session_state.model_params['temperature'],
                step=0.1,
                help="Kontroluje losowość odpowiedzi. Niższe wartości = bardziej deterministyczne"
            )
            
            top_k = st.slider(
                "Top K",
                min_value=1,
                max_value=100,
                value=st.session_state.model_params['top_k'],
                step=1,
                help="Wybiera K najbardziej prawdopodobnych tokenów"
            )
        
        with col2:
            top_p = st.slider(
                "Top P",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.model_params['top_p'],
                step=0.05,
                help="Nucleus sampling - alternatywa dla Top K"
            )
            
            max_tokens = st.slider(
                "Max Tokens",
                min_value=100,
                max_value=4000,
                value=st.session_state.model_params['max_tokens'],
                step=100,
                help="Maksymalna długość odpowiedzi"
            )
        
        if st.button("Zapisz parametry modelu"):
            st.session_state.model_params = {
                'temperature': temperature,
                'top_p': top_p,
                'top_k': top_k,
                'max_tokens': max_tokens
            }
            st.success("Parametry modelu zaktualizowane!")
            st.info("Nowe parametry będą użyte w następnym zapytaniu")
        
        st.markdown("---")
        
        # Wybór modelu Whisper
        st.subheader("Model Whisper (transkrypcja audio/wideo)")
        
        whisper_models = {
            'tiny': 'Tiny (75 MB) - najszybszy, najmniej dokładny',
            'base': 'Base (145 MB) - dobry balans (domyślny)',
            'small': 'Small (470 MB) - bardziej dokładny',
            'medium': 'Medium (1.5 GB) - bardzo dokładny',
            'large-v3': 'Large v3 (3 GB) - najdokładniejszy'
        }
        
        available_models = []
        for model_name in whisper_models.keys():
            model_file = WHISPER_MODELS_DIR / f"{model_name}.pt"
            if model_file.exists():
                available_models.append(model_name)
        
        if available_models:
            st.info(f"Dostępne modele: {', '.join(available_models)}")
        else:
            st.warning("Brak pobranych modeli. Wybrany model zostanie automatycznie pobrany przy pierwszym użyciu")
        
        selected_whisper = st.selectbox(
            "Wybierz model Whisper",
            options=list(whisper_models.keys()),
            index=list(whisper_models.keys()).index(st.session_state.whisper_model),
            format_func=lambda x: whisper_models[x],
            help="Większe modele są dokładniejsze ale wolniejsze i wymagają więcej RAM"
        )
        
        if st.button("Zapisz model Whisper"):
            st.session_state.whisper_model = selected_whisper
            st.success(f"Model Whisper ustawiony na: {selected_whisper}")
            st.info("Nowy model będzie użyty dla kolejnych plików audio/wideo")
        
        st.markdown("---")
        
        # Chunk sizes
        st.subheader("Rozmiary fragmentów (chunks)")
        st.info("Kontroluje jak tekst jest dzielony na fragmenty podczas indeksowania")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            text_chunk = st.number_input(
                "Tekst (znaki)",
                min_value=100,
                max_value=2000,
                value=st.session_state.chunk_sizes['text'],
                step=50,
                help="Maksymalny rozmiar fragmentu tekstu"
            )
        
        with col2:
            image_chunk = st.number_input(
                "Opis obrazu (znaki)",
                min_value=100,
                max_value=1000,
                value=st.session_state.chunk_sizes['image_desc'],
                step=50,
                help="Maksymalny rozmiar opisu obrazu"
            )
        
        with col3:
            audio_chunk = st.number_input(
                "Audio (znaki)",
                min_value=100,
                max_value=1000,
                value=st.session_state.chunk_sizes['audio'],
                step=50,
                help="Maksymalny rozmiar fragmentu transkrypcji"
            )
        
        if st.button("Zapisz rozmiary fragmentów"):
            st.session_state.chunk_sizes = {
                'text': text_chunk,
                'image_desc': image_chunk,
                'audio': audio_chunk
            }
            st.success("Rozmiary fragmentów zaktualizowane!")
            st.warning("Uwaga: Zmiana dotyczy tylko nowo dodanych dokumentów")
        
        st.markdown("---")
        
        st.subheader("Informacje systemowe")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Model embeddingów:**
            - intfloat/multilingual-e5-large
            - Wymiar: 1024
            - Urządzenie: GPU (CUDA)
            
            **Model LLM:**
            - Gemma 3:12B (multimodal)
            - Procesor: GPU
            - Endpoint: localhost:11434
            """)
        
        with col2:
            st.markdown("""
            **Baza wektorowa:**
            - ChromaDB
            - Lokalizacja: vector_db/
            
            **GPU:**
            - NVIDIA RTX 3060 12GB
            - CUDA: 12.8
            """)
        
        st.markdown("---")
        
        st.subheader("Modele audio (Whisper)")
        
        models_status = {}
        
        for model_name, size in [("tiny", "75 MB"), ("base", "145 MB"), ("small", "470 MB"), ("medium", "1.5 GB"), ("large-v3", "3 GB")]:
            model_file = WHISPER_MODELS_DIR / f"{model_name}.pt"
            models_status[model_name] = model_file.exists()
        
        st.markdown("**Status modeli Whisper:**")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            for model_name in ["tiny", "base"]:
                size = "75 MB" if model_name == "tiny" else "145 MB"
                icon = "[OK]" if models_status[model_name] else "[---]"
                default = " (domyślny)" if model_name == "base" else ""
                st.text(f"{icon} {model_name}{default} ({size})")
        
        with col_b:
            for model_name in ["small", "medium"]:
                size = "470 MB" if model_name == "small" else "1.5 GB"
                icon = "[OK]" if models_status[model_name] else "[---]"
                st.text(f"{icon} {model_name} ({size})")
        
        with col_c:
            for model_name in ["large-v3"]:
                size = "3 GB"
                icon = "[OK]" if models_status[model_name] else "[---]"
                st.text(f"{icon} {model_name} ({size})")
        
        if not any(models_status.values()):
            st.warning("Brak modeli Whisper. Model zostanie automatycznie pobrany przy pierwszym użyciu")
        elif not models_status.get("base"):
            st.info("Model 'base' zostanie pobrany przy pierwszym pliku audio (~145 MB)")
        
        st.caption("Modele pobierają się automatycznie przy pierwszym użyciu pliku audio")
        st.caption(f"Lokalizacja: {WHISPER_MODELS_DIR}")

if __name__ == "__main__":
    main()
