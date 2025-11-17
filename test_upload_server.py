#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosta aplikacja testowa do uploadu plików
Test czy podstawowy upload działa poza Streamlit
"""

from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import os
import logging

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Folder do zapisu plików
UPLOAD_FOLDER = Path(__file__).parent / "data"
UPLOAD_FOLDER.mkdir(exist_ok=True, parents=True)

# Maksymalny rozmiar pliku: 200MB
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

@app.route('/')
def index():
    """Strona główna z formularzem uploadu"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Upload</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
                text-align: center;
                margin: 20px 0;
                background: #fafafa;
            }
            .upload-area.dragover {
                border-color: #6366f1;
                background: #f0f0ff;
            }
            input[type="file"] {
                margin: 20px 0;
            }
            button {
                background: #6366f1;
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background: #818cf8;
            }
            .status {
                margin-top: 20px;
                padding: 10px;
                border-radius: 5px;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .file-list {
                margin-top: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }
            .file-item {
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }
            .file-item:last-child {
                border-bottom: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Test Upload Plików</h1>
            <p>Prosta aplikacja testowa do weryfikacji uploadu plików</p>
            
            <div class="upload-area" id="uploadArea">
                <p>Przeciągnij pliki tutaj lub kliknij aby wybrać</p>
                <input type="file" id="fileInput" multiple>
            </div>
            
            <button onclick="uploadFiles()">Zapisz pliki</button>
            
            <div id="status"></div>
            
            <div class="file-list">
                <h3>Zapisane pliki:</h3>
                <div id="fileList">Ładowanie...</div>
            </div>
        </div>

        <script>
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('fileInput');
            const statusDiv = document.getElementById('status');
            const fileListDiv = document.getElementById('fileList');

            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                fileInput.files = e.dataTransfer.files;
            });

            uploadArea.addEventListener('click', () => {
                fileInput.click();
            });

            // Upload plików
            async function uploadFiles() {
                const files = fileInput.files;
                if (files.length === 0) {
                    showStatus('Nie wybrano żadnych plików', 'error');
                    return;
                }

                const formData = new FormData();
                for (let file of files) {
                    formData.append('files', file);
                }

                showStatus('Zapisywanie plików...', 'success');

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();
                    
                    if (result.success) {
                        showStatus(`Zapisano ${result.saved.length} plik(ów): ${result.saved.join(', ')}`, 'success');
                        loadFileList();
                    } else {
                        showStatus(`Błąd: ${result.error}`, 'error');
                    }
                } catch (error) {
                    showStatus(`Błąd: ${error.message}`, 'error');
                }
            }

            function showStatus(message, type) {
                statusDiv.innerHTML = `<div class="status ${type}">${message}</div>`;
            }

            // Załaduj listę plików
            async function loadFileList() {
                try {
                    const response = await fetch('/files');
                    const files = await response.json();
                    
                    if (files.length === 0) {
                        fileListDiv.innerHTML = '<p>Brak plików</p>';
                    } else {
                        fileListDiv.innerHTML = files.map(f => 
                            `<div class="file-item">${f.name} (${formatBytes(f.size)})</div>`
                        ).join('');
                    }
                } catch (error) {
                    fileListDiv.innerHTML = `<p>Błąd: ${error.message}</p>`;
                }
            }

            function formatBytes(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
            }

            // Załaduj listę przy starcie
            loadFileList();
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    """Endpoint do uploadu plików"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'Brak plików w żądaniu'}), 400
        
        files = request.files.getlist('files')
        
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': 'Nie wybrano żadnych plików'}), 400
        
        saved_files = []
        errors = []
        
        for file in files:
            if file.filename:
                try:
                    file_path = UPLOAD_FOLDER / file.filename
                    logger.info(f"Zapisywanie pliku: {file_path}")
                    
                    # Zapisz plik
                    file.save(str(file_path))
                    
                    # Weryfikacja
                    if file_path.exists() and file_path.stat().st_size > 0:
                        saved_files.append(file.filename)
                        logger.info(f"Plik zapisany: {file_path} ({file_path.stat().st_size} bytes)")
                    else:
                        errors.append(f"{file.filename}: Plik nie został zapisany")
                        logger.error(f"Błąd: Plik {file_path} nie został zapisany")
                except Exception as e:
                    error_msg = f"{file.filename}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(f"Błąd zapisu {file.filename}: {e}", exc_info=True)
        
        if saved_files:
            return jsonify({
                'success': True,
                'saved': saved_files,
                'errors': errors if errors else None
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nie udało się zapisać żadnych plików',
                'errors': errors
            }), 500
            
    except Exception as e:
        logger.error(f"Błąd w /upload: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """Lista zapisanych plików"""
    try:
        files = []
        for file_path in UPLOAD_FOLDER.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append({
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime
                })
        
        # Sortuj po dacie modyfikacji (najnowsze pierwsze)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify(files)
    except Exception as e:
        logger.error(f"Błąd w /files: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info(f"Uruchamianie serwera testowego")
    logger.info(f"Folder uploadu: {UPLOAD_FOLDER}")
    logger.info(f"Folder istnieje: {UPLOAD_FOLDER.exists()}")
    logger.info(f"Uprawnienia zapisu: {os.access(UPLOAD_FOLDER, os.W_OK)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

