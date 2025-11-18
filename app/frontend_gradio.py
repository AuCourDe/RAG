#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Gradio dla systemu RAG
Migracja z Streamlit - wersja stabilna
Modern UI 2025 - Glassmorphism Design
"""

import gradio as gr
from rag_system import RAGSystem, SourceReference, load_suggested_questions
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
import shutil

# Konfiguracja
SESSION_TIMEOUT_SECONDS = 600
CONFIG_FILE = Path("auth_config.json")
PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DATA_DIR = PROJECT_ROOT / "data"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Session store (globalny dla wszystkich użytkowników)
authenticated_users = {}  # {session_id: {username, expiry, session_id, history}}
query_history = {}  # {session_id: [{'question': ..., 'answer': ..., 'timestamp': ...}]}

# Inicjalizacja
audit_logger = get_audit_logger()
rag = None  # Będzie inicjalizowany po zalogowaniu

def load_credentials():
    """Ładuje dane logowania z auth_config.json"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Domyślne dane
        default_hash = hashlib.sha256("admin123".encode()).hexdigest()
        default_config = {
            "users": {
                "admin": {
                    "name": "Administrator",
                    "password_hash": default_hash
                }
            }
        }
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2)
        return default_config

def check_password(username: str, password: str) -> bool:
    """Sprawdza hasło użytkownika"""
    creds = load_credentials()
    if username not in creds['users']:
        return False
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    return creds['users'][username]['password_hash'] == password_hash

def update_password(username: str, new_password: str) -> bool:
    """Aktualizuje hasło użytkownika"""
    try:
        creds = load_credentials()
        if username not in creds['users']:
            return False
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        creds['users'][username]['password_hash'] = password_hash
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(creds, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Błąd podczas zmiany hasła: {e}")
        return False

def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """Autoryzacja użytkownika - zwraca (success, session_id)"""
    if check_password(username, password):
        session_id = str(uuid.uuid4())
        authenticated_users[session_id] = {
            "username": username,
            "expiry": time.time() + SESSION_TIMEOUT_SECONDS,
            "session_id": session_id[:8],
            "model_params": {
                'temperature': 0.1,
                'top_p': 0.85,
                'top_k': 30,
                'max_tokens': 1000
            }
        }
        query_history[session_id] = []
        audit_logger.log_login(user_id=username, success=True)
        logger.info(f"Użytkownik {username} zalogowany (session: {session_id[:8]})")
        return True, session_id
    else:
        audit_logger.log_login(user_id=username, success=False)
        logger.warning(f"Nieudana próba logowania: {username}")
        return False, ""

def check_session(session_id: str) -> tuple[bool, dict]:
    """Sprawdza czy sesja jest aktywna - zwraca (is_valid, user_data)"""
    if not session_id or session_id not in authenticated_users:
        return False, {}
    
    user_data = authenticated_users[session_id]
    if time.time() > user_data['expiry']:
        # Sesja wygasła
        authenticated_users.pop(session_id, None)
        query_history.pop(session_id, None)
        return False, {}
    
    # Przedłuż sesję
    user_data['expiry'] = time.time() + SESSION_TIMEOUT_SECONDS
    return True, user_data

def logout_user(session_id: str):
    """Wylogowuje użytkownika"""
    authenticated_users.pop(session_id, None)
    query_history.pop(session_id, None)
    logger.info(f"Użytkownik wylogowany (session: {session_id[:8] if session_id else 'unknown'})")

def get_rag_system():
    """Inicjalizuje system RAG (singleton)"""
    global rag
    if rag is None:
        logger.info("Inicjalizacja systemu RAG...")
        rag = RAGSystem()
    return rag

# === FUNKCJE HANDLERÓW ===

def handle_login(username: str, password: str):
    """Obsługa logowania - zwraca (status_message, session_id)"""
    if not username or not password:
        return "⚠️ Wprowadź nazwę użytkownika i hasło", ""
    
    success, session_id = authenticate_user(username, password)
    if success:
        creds = load_credentials()
        user_name = creds['users'][username]['name']
        return f"✅ Zalogowano jako {user_name}", session_id
    else:
        return "❌ Nieprawidłowe dane logowania", ""

def handle_search(question: str, search_mode: str, n_results: int, session_id: str):
    """Obsługa wyszukiwania"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła. Zaloguj się ponownie.", "", []
    
    if not question or not question.strip():
        return "⚠️ Wprowadź pytanie", "", []
    
    try:
        rag = get_rag_system()
        username = user_data['username']
        params = user_data.get('model_params', {'temperature': 0.1, 'top_p': 0.85, 'top_k': 30, 'max_tokens': 1000})
        
        logger.info(f"Wyszukiwanie: '{question}' (tryb: {search_mode}, użytkownik: {username})")
        
        # Wyszukiwanie w zależności od trybu
        sources = []
        if search_mode == "Tekst":
            results = rag.hybrid_search.search_bm25(question, top_k=n_results)
            for doc in results:
                sources.append({
                    'content': doc.get('content', ''),
                    'source_file': doc.get('metadata', {}).get('source_file', ''),
                    'page_number': doc.get('metadata', {}).get('page', 0),
                    'element_id': doc.get('metadata', {}).get('element_id', ''),
                    'distance': 1.0
                })
        elif search_mode == "Wektor":
            results = rag.vector_db.search(question, n_results=n_results)
            for doc in results:
                sources.append({
                    'content': doc.get('content', ''),
                    'source_file': doc.get('metadata', {}).get('source_file', ''),
                    'page_number': doc.get('metadata', {}).get('page', 0),
                    'element_id': doc.get('metadata', {}).get('element_id', ''),
                    'distance': doc.get('distance', 0.0)
                })
        else:
            # Hybrid search
            hybrid_results = rag.hybrid_search.search(question, top_k=n_results)
            for doc, score in hybrid_results:
                sources.append({
                    'content': doc.get('content', ''),
                    'source_file': doc.get('metadata', {}).get('source_file', ''),
                    'page_number': doc.get('metadata', {}).get('page', 0),
                    'element_id': doc.get('metadata', {}).get('element_id', ''),
                    'distance': 1.0 - score
                })
        
        if not sources:
            return "⚠️ Nie znaleziono odpowiednich dokumentów w bazie.", "", []
        
        # Priorytetyzacja wyników wideo
        question_lower = question.lower()
        video_keywords = ['film', 'wideo', 'video', 'movie', 'nagranie', 'klip', 'filmie']
        is_video_question = any(keyword in question_lower for keyword in video_keywords)
        
        if is_video_question and sources:
            video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
            video_sources = []
            other_sources = []
            
            for src in sources:
                file_ext = Path(src['source_file']).suffix.lower()
                element_id_lower = (src.get('element_id') or '').lower()
                if file_ext in video_extensions or 'video' in element_id_lower:
                    video_sources.append(src)
                else:
                    other_sources.append(src)
            
            if video_sources:
                sources = video_sources + other_sources[:max(1, n_results - len(video_sources))]
        
        # Generowanie odpowiedzi
        source_refs = [
            SourceReference(
                content=src['content'],
                source_file=src['source_file'],
                page_number=src['page_number'],
                element_id=src.get('element_id', ''),
                distance=src.get('distance', 0.0)
            )
            for src in sources
        ]
        
        answer = rag.query(
            question,
            n_results=n_results,
            user_id=username,
            session_id=user_data['session_id'],
            temperature=params['temperature'],
            top_p=params['top_p'],
            top_k=params['top_k'],
            max_tokens=params['max_tokens'],
            sources=source_refs
        )
        
        # Zapisz do historii
        if session_id in query_history:
            query_history[session_id].append({
                'question': question,
                'answer': answer,
                'sources_count': len(sources),
                'search_mode': search_mode,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            # Ogranicz do ostatnich 50 zapytań
            query_history[session_id] = query_history[session_id][-50:]
        
        # Formatowanie źródeł
        sources_text = "\n\n**Źródła:**\n"
        for i, src in enumerate(sources[:5], 1):
            sources_text += f"{i}. {src['source_file']} - Strona {src['page_number']}\n"
        
        return answer + sources_text, question, sources
        
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania: {e}", exc_info=True)
        return f"❌ Wystąpił błąd: {str(e)}", question, []

def handle_file_upload(files, session_id: str):
    """Obsługa uploadu plików"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła. Zaloguj się ponownie.", []
    
    if not files:
        return "⚠️ Nie wybrano plików", []
    
    try:
        saved_files = []
        for file in files:
            if file:
                filename = Path(file.name).name
                dest_path = UPLOAD_DATA_DIR / filename
                shutil.copy2(file.name, dest_path)
                saved_files.append(filename)
                logger.info(f"Plik zapisany: {filename}")
        
        # Indeksuj pliki
        rag = get_rag_system()
        indexed_count = 0
        for filename in saved_files:
            file_path = UPLOAD_DATA_DIR / filename
            try:
                rag.index_file(file_path)
                indexed_count += 1
                logger.info(f"Plik zindeksowany: {filename}")
            except Exception as e:
                logger.error(f"Błąd podczas indeksowania {filename}: {e}")
        
        # Rebuild BM25 index
        try:
            rag.rebuild_bm25_index()
        except Exception as e:
            logger.warning(f"Błąd podczas przebudowy BM25: {e}")
        
        return f"✅ Zapisano i zindeksowano {indexed_count}/{len(saved_files)} plik(ów)", saved_files
        
    except Exception as e:
        logger.error(f"Błąd podczas uploadu: {e}", exc_info=True)
        return f"❌ Błąd: {str(e)}", []

def get_file_list(session_id: str):
    """Pobiera listę plików w bazie"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return []
    
    try:
        rag = get_rag_system()
        collection = rag.vector_db.collection
        all_data = collection.get(include=['metadatas'])
        
        files_in_db = {}
        for meta in all_data['metadatas']:
            file_name = meta['source_file']
            if file_name not in files_in_db:
                files_in_db[file_name] = 0
            files_in_db[file_name] += 1
        
        file_list = [{"filename": name, "chunks": count} for name, count in sorted(files_in_db.items())]
        return file_list
    except Exception as e:
        logger.error(f"Błąd podczas pobierania listy plików: {e}")
        return []

def handle_delete_files(filenames: list, session_id: str):
    """Usuwa pliki z bazy i dysku"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła", []
    
    if not filenames:
        return "⚠️ Nie wybrano plików do usunięcia", []
    
    try:
        rag = get_rag_system()
        collection = rag.vector_db.collection
        all_data = collection.get(include=['metadatas', 'ids'])
        
        deleted_count = 0
        for filename in filenames:
            try:
                # Usuń plik z dysku
                file_path = UPLOAD_DATA_DIR / filename
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Usunięto plik: {filename}")
                
                # Usuń z bazy wektorowej
                ids_to_delete = []
                for idx, meta in enumerate(all_data['metadatas']):
                    if meta['source_file'] == filename:
                        ids_to_delete.append(all_data['ids'][idx])
                
                if ids_to_delete:
                    collection.delete(ids=ids_to_delete)
                    logger.info(f"Usunięto {len(ids_to_delete)} fragmentów z bazy dla {filename}")
                
                audit_logger.log_file_delete(
                    user_id=user_data['username'],
                    filename=filename,
                    session_id=user_data['session_id']
                )
                
                deleted_count += 1
            except Exception as e:
                logger.error(f"Błąd usuwania {filename}: {e}")
        
        # Rebuild BM25 index
        try:
            rag.rebuild_bm25_index()
        except Exception as e:
            logger.warning(f"Błąd podczas przebudowy BM25: {e}")
        
        return f"✅ Usunięto {deleted_count} plik(ów)", get_file_list(session_id)
        
    except Exception as e:
        logger.error(f"Błąd podczas usuwania plików: {e}", exc_info=True)
        return f"❌ Błąd: {str(e)}", []

def handle_reindex_all(session_id: str):
    """Reindeksuje wszystkie pliki w folderze data/"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła", []
    
    try:
        rag = get_rag_system()
        files = list(UPLOAD_DATA_DIR.glob("*"))
        files = [f for f in files if f.is_file()]
        
        indexed_count = 0
        for file_path in files:
            try:
                rag.index_file(file_path)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Błąd indeksowania {file_path.name}: {e}")
        
        # Rebuild BM25 index
        try:
            rag.rebuild_bm25_index()
        except Exception as e:
            logger.warning(f"Błąd podczas przebudowy BM25: {e}")
        
        return f"✅ Zindeksowano {indexed_count} plik(ów)", get_file_list(session_id)
        
    except Exception as e:
        logger.error(f"Błąd podczas reindeksacji: {e}", exc_info=True)
        return f"❌ Błąd: {str(e)}", []

def get_history(session_id: str):
    """Pobiera historię zapytań"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return []
    
    if session_id not in query_history:
        return []
    
    history = query_history[session_id][-10:]  # Ostatnie 10 zapytań
    return [f"[{h['timestamp']}] {h['question']} ({h['search_mode']})" for h in reversed(history)]

def handle_change_password(current_password: str, new_password: str, confirm_password: str, session_id: str):
    """Zmienia hasło użytkownika"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła"
    
    username = user_data['username']
    
    if not check_password(username, current_password):
        return "❌ Nieprawidłowe aktualne hasło"
    
    if not new_password:
        return "❌ Nowe hasło nie może być puste"
    
    if new_password != confirm_password:
        return "❌ Hasła nie są identyczne"
    
    if len(new_password) < 6:
        return "❌ Hasło musi mieć minimum 6 znaków"
    
    if update_password(username, new_password):
        return "✅ Hasło zmienione pomyślnie. Zaloguj się ponownie."
    else:
        return "❌ Błąd podczas zmiany hasła"

def update_model_params(temperature: float, top_p: float, top_k: int, max_tokens: int, session_id: str):
    """Aktualizuje parametry modelu"""
    is_valid, user_data = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła"
    
    user_data['model_params'] = {
        'temperature': temperature,
        'top_p': top_p,
        'top_k': int(top_k),
        'max_tokens': int(max_tokens)
    }
    return "✅ Parametry modelu zaktualizowane"

def get_gpu_stats():
    """Pobiera statystyki GPU"""
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

def get_system_stats(session_id: str):
    """Pobiera statystyki systemu"""
    is_valid, _ = check_session(session_id)
    if not is_valid:
        return "⚠️ Sesja wygasła"
    
    stats = []
    
    # GPU
    gpu = get_gpu_stats()
    if gpu:
        vram_percent = int(gpu['mem_used']/gpu['mem_total']*100)
        stats.append(f"**GPU:** {gpu['name']}")
        stats.append(f"- Wykorzystanie: {gpu['utilization']}%")
        stats.append(f"- VRAM: {vram_percent}% ({gpu['mem_used']}/{gpu['mem_total']} MB)")
        stats.append(f"- Temperatura: {gpu['temperature']}°C")
    else:
        stats.append("**GPU:** CPU (brak NVIDIA)")
    
    # CPU i RAM
    try:
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        stats.append(f"\n**CPU:** {cpu_percent}%")
        stats.append(f"**RAM:** {ram.used/1024**3:.1f}/{ram.total/1024**3:.1f} GB ({ram.percent}%)")
    except:
        pass
    
    return "\n".join(stats)

# === TWORZENIE INTERFEJSU GRADIO ===
def create_interface():
    """Tworzy główny interfejs Gradio"""
    
    with gr.Blocks(title="RAG System", theme=gr.themes.Soft()) as interface:
        session_state = gr.State("")  # Session ID
        
        gr.Markdown("# 🔍 RAG System")
        gr.Markdown("System odpowiedzi na pytania w oparciu o dokumenty z bazy wiedzy")
        
        # Status logowania
        login_status_display = gr.Markdown("")
        
        # Tabs
        with gr.Tabs() as tabs:
            # TAB 1: ZAPYTANIA
            with gr.Tab("Zapytania"):
                with gr.Row():
                    with gr.Column(scale=3):
                        question_input = gr.Textbox(label="Twoje pytanie", placeholder="Np. Jakie są kary za kradzież?")
                    with gr.Column(scale=1):
                        search_mode = gr.Dropdown(
                            choices=["Wektor + Tekst + Reranking", "Wektor + Tekst", "Wektor", "Tekst"],
                            value="Wektor + Tekst + Reranking",
                            label="Rodzaj wyszukiwania"
                        )
                    with gr.Column(scale=1):
                        n_results = gr.Number(label="Maks. wyników", value=5, minimum=1, maximum=50, step=1)
                
                search_btn = gr.Button("Szukaj odpowiedzi", variant="primary")
                
                answer_output = gr.Markdown(label="Odpowiedź")
                
                with gr.Accordion("Źródła", open=False):
                    sources_output = gr.JSON(label="Źródła")
                
                def on_search(question, mode, n_res, session):
                    answer, _, sources = handle_search(question, mode, n_res, session)
                    return answer, sources
                
                search_btn.click(
                    fn=on_search,
                    inputs=[question_input, search_mode, n_results, session_state],
                    outputs=[answer_output, sources_output]
                )
            
            # TAB 2: INDEKSOWANIE
            with gr.Tab("Indeksowanie"):
                gr.Markdown("### Upload plików")
                file_upload = gr.File(
                    label="Wybierz pliki do przesłania",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".xlsx", ".txt", ".mp4", ".mp3", ".jpg", ".png"]
                )
                upload_btn = gr.Button("Prześlij i zindeksuj", variant="primary")
                upload_status = gr.Markdown("")
                
                def on_upload(files, session):
                    status, file_list = handle_file_upload(files, session)
                    return status, file_list
                
                upload_btn.click(
                    fn=on_upload,
                    inputs=[file_upload, session_state],
                    outputs=[upload_status, gr.update()]
                )
                
                gr.Markdown("---")
                gr.Markdown("### Zarządzanie plikami")
                
                refresh_files_btn = gr.Button("Odśwież listę", variant="secondary")
                reindex_btn = gr.Button("Reindeksuj wszystkie pliki", variant="secondary")
                
                file_list_output = gr.Dataframe(
                    headers=["Plik", "Fragmentów"],
                    label="Pliki w bazie",
                    interactive=False
                )
                
                files_to_delete = gr.CheckboxGroup(
                    label="Wybierz pliki do usunięcia",
                    choices=[],
                    interactive=True
                )
                
                delete_btn = gr.Button("Usuń zaznaczone pliki", variant="stop")
                file_management_status = gr.Markdown("")
                
                def refresh_files(session):
                    files = get_file_list(session)
                    choices = [f["filename"] for f in files]
                    df_data = [[f["filename"], f["chunks"]] for f in files]
                    return df_data, gr.update(choices=choices)
                
                def on_reindex(session):
                    status, files = handle_reindex_all(session)
                    choices = [f["filename"] for f in files]
                    df_data = [[f["filename"], f["chunks"]] for f in files]
                    return status, df_data, gr.update(choices=choices)
                
                def on_delete(selected, session):
                    status, files = handle_delete_files(selected, session)
                    choices = [f["filename"] for f in files]
                    df_data = [[f["filename"], f["chunks"]] for f in files]
                    return status, df_data, gr.update(choices=choices)
                
                refresh_files_btn.click(
                    fn=refresh_files,
                    inputs=[session_state],
                    outputs=[file_list_output, files_to_delete]
                )
                
                reindex_btn.click(
                    fn=on_reindex,
                    inputs=[session_state],
                    outputs=[file_management_status, file_list_output, files_to_delete]
                )
                
                delete_btn.click(
                    fn=on_delete,
                    inputs=[files_to_delete, session_state],
                    outputs=[file_management_status, file_list_output, files_to_delete]
                )
            
            # TAB 3: HISTORIA
            with gr.Tab("Historia"):
                history_output = gr.Dataframe(
                    headers=["Zapytanie"],
                    label="Historia zapytań (ostatnie 10)",
                    interactive=False
                )
                
                refresh_history_btn = gr.Button("Odśwież historię", variant="secondary")
                
                def refresh_history(session):
                    history = get_history(session)
                    return [[h] for h in history]
                
                refresh_history_btn.click(
                    fn=refresh_history,
                    inputs=[session_state],
                    outputs=[history_output]
                )
            
            # TAB 4: USTAWIENIA
            with gr.Tab("Ustawienia"):
                gr.Markdown("### Zmiana hasła")
                
                current_password = gr.Textbox(label="Aktualne hasło", type="password")
                new_password = gr.Textbox(label="Nowe hasło", type="password")
                confirm_password = gr.Textbox(label="Potwierdź nowe hasło", type="password")
                change_password_btn = gr.Button("Zmień hasło", variant="primary")
                password_status = gr.Markdown("")
                
                change_password_btn.click(
                    fn=handle_change_password,
                    inputs=[current_password, new_password, confirm_password, session_state],
                    outputs=[password_status]
                )
                
                gr.Markdown("---")
                gr.Markdown("### Parametry modelu LLM")
                
                temperature = gr.Slider(label="Temperature", minimum=0.0, maximum=2.0, value=0.1, step=0.1)
                top_p = gr.Slider(label="Top P", minimum=0.0, maximum=1.0, value=0.85, step=0.05)
                top_k = gr.Slider(label="Top K", minimum=1, maximum=100, value=30, step=1)
                max_tokens = gr.Slider(label="Max Tokens", minimum=100, maximum=4000, value=1000, step=100)
                
                save_params_btn = gr.Button("Zapisz parametry", variant="primary")
                params_status = gr.Markdown("")
                
                save_params_btn.click(
                    fn=update_model_params,
                    inputs=[temperature, top_p, top_k, max_tokens, session_state],
                    outputs=[params_status]
                )
                
                gr.Markdown("---")
                gr.Markdown("### Statystyki systemu")
                
                refresh_stats_btn = gr.Button("Odśwież statystyki", variant="secondary")
                stats_output = gr.Markdown("")
                
                refresh_stats_btn.click(
                    fn=get_system_stats,
                    inputs=[session_state],
                    outputs=[stats_output]
                )
        
        # Przycisk wylogowania
        logout_btn = gr.Button("Wyloguj", variant="stop")
        
        def on_logout(session):
            logout_user(session)
            return "", ""
        
        logout_btn.click(
            fn=on_logout,
            inputs=[session_state],
            outputs=[question_input, answer_output]
        )
        
        # Sekcja logowania (widoczna gdy nie zalogowany)
        gr.Markdown("---")
        gr.Markdown("### Logowanie")
        
        with gr.Row():
            with gr.Column(scale=1):
                username_input_login = gr.Textbox(label="Nazwa użytkownika", placeholder="admin", value="admin")
                password_input_login = gr.Textbox(label="Hasło", type="password", placeholder="••••••••", value="admin123")
                login_btn_main = gr.Button("Zaloguj", variant="primary")
        
        login_status_main = gr.Markdown("")
        
        def on_login_main(username, password, current_session):
            if current_session:
                is_valid, _ = check_session(current_session)
                if is_valid:
                    return "✅ Już jesteś zalogowany", current_session
            status, session_id = handle_login(username, password)
            return status, session_id
        
        login_btn_main.click(
            fn=on_login_main,
            inputs=[username_input_login, password_input_login, session_state],
            outputs=[login_status_main, session_state]
        ).then(
            fn=lambda status, session: status if session else "",
            inputs=[login_status_main, session_state],
            outputs=[login_status_display]
        )
    
    return interface

# === URUCHOMIENIE ===
if __name__ == "__main__":
    # Upewnij się, że folder data istnieje
    UPLOAD_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Uruchamianie interfejsu Gradio...")
    
    # Utwórz i uruchom interfejs
    try:
        interface = create_interface()
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania Gradio: {e}", exc_info=True)
        raise
