#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Streamlit dla systemu RAG
Z autoryzacją hasłem i możliwością udostępnienia w sieci
Modern UI 2025 - Glassmorphism Design
"""

import streamlit as st
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
            color: {text_primary};
            font-weight: 700;
        }}
        
        /* Spinner */
        .stSpinner > div {{
            border-top-color: {accent_color};
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: {card_bg};
            backdrop-filter: blur(10px);
            border: 1px solid {card_border};
            border-radius: 12px;
            padding: 8px 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: {shadow};
        }}
        
        .theme-toggle:hover {{
            transform: scale(1.05);
        }}
        
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
@st.cache_resource(ttl=10)
def init_rag_system():
    """Inicjalizacja systemu RAG (cache na 10s, auto odświeża listę plików)"""
    with st.spinner("Inicjalizacja systemu RAG..."):
        return RAGSystem()

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

def main():
    """Główna funkcja aplikacji"""
    
    # Inicjalizacja session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
    
    if 'theme' not in st.session_state:
        st.session_state.theme = 'dark'
    
    # Load CSS
    load_css()
    
    # Theme Toggle (tylko dla zalogowanych)
    if st.session_state.authenticated:
        col_theme_1, col_theme_2, col_theme_3 = st.columns([6, 1, 1])
        with col_theme_2:
            if st.button("☀" if st.session_state.theme == 'dark' else "🌙", key="theme_toggle"):
                st.session_state.theme = 'light' if st.session_state.theme == 'dark' else 'dark'
                st.rerun()
    
    # === EKRAN LOGOWANIA ===
    if not st.session_state.authenticated:
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
        st.subheader("System")
        
        # Auto-refresh co 10 sekund dla monitoringu GPU
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        # Odświeżaj co 10 sekund automatycznie
        current_time = time.time()
        if current_time - st.session_state.last_refresh > 10:
            st.session_state.last_refresh = current_time
            st.rerun()
        
        # Wykryj GPU i monitoring w czasie rzeczywistym
        gpu_stats = get_gpu_stats()
        
        if gpu_stats:
            st.markdown(f"**GPU:** {gpu_stats['name']}")
            
            # Metryki GPU (odświeżane co 10s)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("GPU", f"{gpu_stats['utilization']}%")
            with col2:
                vram_percent = int(gpu_stats['mem_used']/gpu_stats['mem_total']*100)
                st.metric("VRAM", f"{vram_percent}%")
            with col3:
                st.metric("Temp", f"{gpu_stats['temperature']}°C")
        else:
            st.markdown("**GPU:** CPU (brak NVIDIA)")
        
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
        
        # Informacja o auto-refresh
        time_since_refresh = int(current_time - st.session_state.last_refresh)
        next_refresh = 10 - time_since_refresh
        st.caption(f"Następne odświeżenie: {next_refresh}s")
    
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
        col1, col2 = st.columns([4, 1])
        
        with col1:
            question = st.text_input(
                "Twoje pytanie:",
                placeholder="Np. Jakie są kary za kradzież?",
                key="question_input"
            )
        
        with col2:
            n_results = st.number_input(
                "Wyników:",
                min_value=1,
                max_value=10,
                value=3,
                key="n_results"
            )
        
        if st.button("Szukaj odpowiedzi", type="primary", use_container_width=True):
            if not question:
                st.warning("Proszę wprowadzić pytanie")
            else:
                with st.spinner("Szukam odpowiedzi... (może potrwać 30-60 sekund)"):
                    try:
                        rag = init_rag_system()
                        
                        # Pobierz źródła osobno
                        sources = rag.vector_db.search(question, n_results)
                        
                        # Wygeneruj odpowiedź
                        answer = rag.query(
                            question, 
                            n_results=n_results,
                            user_id=st.session_state.username,
                            session_id=st.session_state.get('session_id', 'unknown')
                        )
                        
                        # Zapisz w session state
                        st.session_state['last_answer'] = answer
                        st.session_state['last_sources'] = sources
                        st.session_state['last_question'] = question
                        
                        # Wyświetl odpowiedź
                        st.success("Odpowiedź wygenerowana")
                        st.markdown("### Odpowiedź:")
                        st.markdown(answer)
                        
                        # Wyświetl źródła z możliwością podglądu
                        st.markdown("---")
                        st.markdown("### Źródła (kliknij aby zobaczyć):")
                        
                        for i, source in enumerate(sources):
                            with st.expander(f"[{i+1}] {source.source_file} - Strona {source.page_number}"):
                                # Wyświetl fragment tekstu
                                st.markdown("**Fragment:**")
                                st.text_area("", source.content, height=150, key=f"content_{i}", disabled=True)
                                
                                # Sprawdź czy to obraz czy PDF
                                file_path = Path("data") / source.source_file
                                
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
                        
                    except Exception as e:
                        st.error(f"Błąd: {e}")
                        logger.error(f"Błąd podczas przetwarzania pytania: {e}", exc_info=True)
        
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
        
        st.markdown("""
        System automatycznie indeksuje nowe pliki i aktualizuje bazę po dodaniu/usunięciu dokumentów.
        
        **Obsługiwane formaty:** 
        - Dokumenty: PDF, DOCX, XLSX (+ obrazy/wykresy wewnątrz)
        - Obrazy: JPG, JPEG, PNG, BMP
        - Audio: MP3, WAV, FLAC, OGG, M4A (transkrypcja Whisper + mówcy)
        - Wideo: MP4, AVI, MOV, MKV, WEBM (audio Whisper + klatki Gemma 3)
        """)
        
        # Upload nowych plików
        st.subheader("Dodaj nowe dokumenty")
        uploaded_files = st.file_uploader(
            "Przeciągnij pliki tutaj lub kliknij aby wybrać",
            accept_multiple_files=True,
            type=None,
            key="file_uploader"
        )
        
        if uploaded_files:
            # Walidacja formatów
            supported_formats = {'.pdf', '.docx', '.xlsx', '.jpg', '.jpeg', '.png', '.bmp', 
                               '.mp3', '.wav', '.flac', '.ogg', '.m4a', 
                               '.mp4', '.avi', '.mov', '.mkv', '.webm'}
            
            valid_files = []
            invalid_files = []
            
            for f in uploaded_files:
                ext = Path(f.name).suffix.lower()
                if ext in supported_formats:
                    valid_files.append(f)
                else:
                    invalid_files.append(f.name)
            
            if invalid_files:
                st.error(f"Nieobsługiwane formaty: {', '.join(invalid_files)}")
                st.info("Obsługiwane formaty: PDF, DOCX, XLSX, JPG, PNG, BMP, MP3, WAV, FLAC, OGG, M4A, MP4, AVI, MOV, MKV, WEBM")
            
            uploaded_files = valid_files
            
            if not uploaded_files:
                st.warning("Nie wybrano żadnych prawidłowych plików")
            else:
                # Sprawdź czy są pliki audio lub wideo
                audio_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']]
                video_files = [f for f in uploaded_files if Path(f.name).suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.webm']]
                
                if video_files:
                    st.warning("Wykryto pliki wideo")
                    st.info(f"Przetwarzanie wideo zajmuje najwięcej czasu. Szacowany czas: ~{len(video_files) * 10} minut")
                    st.markdown("**Sprawdź postęp:** `tail -f file_watcher.log`")
                
                if audio_files:
                    whisper_cache = os.path.expanduser("~/.cache/whisper")
                    model_file = os.path.join(whisper_cache, "base.pt")
                    
                    if not os.path.exists(model_file):
                        st.warning("Wykryto pliki audio")
                        st.info("Model Whisper zostanie pobrany przy pierwszym użyciu (~145 MB, ~1-2 minuty)")
                    else:
                        st.info(f"Wykryto {len(audio_files)} plik(ów) audio. Czas przetwarzania: ~3 min na każde 5 min nagrania")
                
                if st.button("Zapisz pliki", use_container_width=True, type="primary"):
                    data_dir = Path("data")
                    success_count = 0
                    audio_count = 0
                    video_count = 0
                    
                    for uploaded_file in uploaded_files:
                        try:
                            file_path = data_dir / uploaded_file.name
                            with open(file_path, 'wb') as f:
                                f.write(uploaded_file.getbuffer())
                            st.success(f"Zapisano: {uploaded_file.name}")
                            success_count += 1
                            
                            # Audit log
                            audit_logger.log_file_upload(
                                user_id=st.session_state.username,
                                filename=uploaded_file.name,
                                file_size=uploaded_file.size,
                                file_type=Path(uploaded_file.name).suffix.lower(),
                                session_id=st.session_state.get('session_id', 'unknown')
                            )
                            
                            file_ext = Path(uploaded_file.name).suffix.lower()
                            if file_ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a']:
                                audio_count += 1
                            elif file_ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                                video_count += 1
                                
                        except Exception as e:
                            st.error(f"Błąd przy {uploaded_file.name}: {e}")
                    
                    if success_count > 0:
                        if video_count > 0:
                            st.warning(f"{video_count} plik(ów) wideo zostanie przetworzonych")
                            st.info(f"Szacowany czas: ~{video_count * 10} minut")
                        elif audio_count > 0:
                            st.info(f"{audio_count} plik(ów) audio zostanie przetworzonych przez Whisper")
                        else:
                            st.info("Pliki zostaną automatycznie zindeksowane w ciągu kilku sekund")
                        time.sleep(2)
                        st.rerun()
        
        st.markdown("---")
        
        # Zarządzanie istniejącymi plikami
        st.subheader("Dokumenty w bazie")
        
        col_refresh, col_spacer = st.columns([1, 3])
        with col_refresh:
            if st.button("Odśwież listę", help="Odśwież listę plików z bazy"):
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
                                    file_path = Path("data") / file_name
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
        
        whisper_cache = os.path.expanduser("~/.cache/whisper")
        models_status = {}
        
        for model_name, size in [("tiny", "75 MB"), ("base", "145 MB"), ("small", "470 MB"), ("medium", "1.5 GB"), ("large-v3", "3 GB")]:
            model_file = os.path.join(whisper_cache, f"{model_name}.pt")
            models_status[model_name] = os.path.exists(model_file)
        
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
        st.caption("Lokalizacja: ~/.cache/whisper/")

if __name__ == "__main__":
    main()
