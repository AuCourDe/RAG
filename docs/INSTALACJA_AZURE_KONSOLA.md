# 🚀 INSTALACJA RAG NA AZURE VM - KONSOLA SZEREGOWA

## Instrukcja krok po kroku dla Azure Virtual Machine

**Dostęp:** Tylko konsola szeregowa (Serial Console)  
**System:** Ubuntu 20.04+ lub 22.04 LTS  
**Czas instalacji:** ~30-45 minut (zależnie od prędkości sieci)

---

## 📋 WYMAGANIA WSTĘPNE

### 1. Azure VM - minimalna konfiguracja:
- **CPU:** 4 vCPU (zalecane: 8 vCPU)
- **RAM:** 16 GB (zalecane: 32 GB)
- **Dysk:** 100 GB SSD
- **GPU:** Opcjonalnie NVIDIA (dla lepszej wydajności)
- **OS:** Ubuntu 22.04 LTS
- **Porty:** 8501 (Streamlit), 11434 (Ollama)

### 2. Dostęp do konsoli szeregowej:
- Azure Portal → Virtual Machines → Twoja VM → Serial Console
- Login: użytkownik z sudo

---

## 🔧 INSTALACJA - KROK PO KROKU

### KROK 1: Aktualizacja systemu i instalacja podstawowych narzędzi

```bash
# Zaloguj się do konsoli szeregowej
# Login: <twoj_user>
# Password: <twoje_haslo>

# Sprawdź system
uname -a
cat /etc/os-release

# Aktualizacja
sudo apt update
sudo apt upgrade -y

# Instalacja podstawowych narzędzi
sudo apt install -y \
    git \
    python3 \
    python3-venv \
    python3-pip \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-pol \
    curl \
    wget \
    htop \
    nano \
    build-essential

# Sprawdź wersje
python3 --version  # Powinno być 3.10+
git --version
ffmpeg -version
```

**Oczekiwany czas:** 5-10 minut

---

### KROK 2: Instalacja Ollama (LLM backend)

```bash
# Pobierz i zainstaluj Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Sprawdź instalację
systemctl status ollama

# Jeśli nie działa, uruchom:
sudo systemctl start ollama
sudo systemctl enable ollama

# Pobierz model gemma3:12b (~7 GB, może potrwać 10-20 minut)
ollama pull gemma3:12b

# Sprawdź czy działa
ollama list
curl http://localhost:11434/api/tags

# Powinieneś zobaczyć gemma3:12b na liście
```

**Oczekiwany czas:** 15-25 minut (pobieranie modelu)

---

### KROK 3: Clone repozytorium RAG

```bash
# Przejdź do home directory
cd ~

# Clone projektu (publiczne repo)
git clone https://github.com/AuCourDe/RAG.git

# Wejdź do folderu
cd RAG

# Sprawdź strukturę
ls -la

# Powinieneś zobaczyć:
# app/, docs/, test/, start_all.sh, requirements.txt
```

**Oczekiwany czas:** 1-2 minuty

---

### KROK 4: Utworzenie Python Virtual Environment

```bash
# W folderze RAG
cd ~/RAG

# Stwórz venv
python3 -m venv venv_rag

# Aktywuj venv
source venv_rag/bin/activate

# Sprawdź czy aktywny (zobaczysz (venv_rag) przed promptem)
which python3
# Powinno pokazać: ~/RAG/venv_rag/bin/python3
```

**Oczekiwany czas:** 1 minuta

---

### KROK 5: Instalacja zależności Python

```bash
# Upewnij się że venv jest aktywny
source venv_rag/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Instalacja zależności (~5-15 minut, wiele pakietów)
pip install -r requirements.txt

# To zainstaluje:
# - streamlit (UI)
# - chromadb (vector database)
# - sentence-transformers (embeddings)
# - openai-whisper (audio transcription)
# - opencv-python (video processing)
# - librosa (audio analysis)
# - scikit-learn (clustering)
# - ~50+ innych bibliotek

# UWAGA: Możliwe ostrzeżenia o dependency conflicts - to normalne
```

**Oczekiwany czas:** 10-20 minut (zależnie od prędkości sieci)

**Możliwe problemy:**
- **Error: "Could not build wheels for..."** → Instaluj `build-essential`: `sudo apt install build-essential`
- **Slow download** → To normalne, pakietów jest dużo

---

### KROK 6: Utworzenie potrzebnych folderów

```bash
# W folderze RAG
cd ~/RAG

# Utwórz foldery
mkdir -p data logs temp vector_db models

# Sprawdź strukturę
ls -la

# Powinieneś zobaczyć wszystkie foldery
```

**Oczekiwany czas:** < 1 minuta

---

### KROK 7: Konfiguracja firewall (NSG na Azure)

**W Azure Portal (nie w konsoli):**

1. Przejdź do: Virtual Machines → Twoja VM → Networking
2. Kliknij: "Add inbound port rule"
3. Dodaj regułę:
   - **Destination port ranges:** 8501
   - **Protocol:** TCP
   - **Priority:** 1000
   - **Name:** AllowStreamlit
   - **Action:** Allow
4. Kliknij: "Add"

**Opcjonalnie - dla Ollama (jeśli chcesz zdalny dostęp):**
- **Port:** 11434
- **Name:** AllowOllama

**Dla konsoli SSH (jeśli jeszcze nie ma):**
- **Port:** 22
- **Name:** AllowSSH

---

### KROK 8: (Opcjonalnie) GPU - instalacja CUDA

**TYLKO jeśli masz VM z GPU (NC-series, NV-series)**

```bash
# Sprawdź czy masz GPU
lspci | grep -i nvidia

# Jeśli TAK, zainstaluj CUDA
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-2 nvidia-driver-535

# Restart wymagany
sudo reboot

# Po restarcie sprawdź
nvidia-smi

# Powinieneś zobaczyć kartę GPU
```

**Oczekiwany czas:** 20-30 minut + restart

**JEŚLI NIE MASZ GPU:** Pomiń ten krok, aplikacja będzie działać na CPU.

---

### KROK 9: Test instalacji

```bash
# W folderze RAG
cd ~/RAG
source venv_rag/bin/activate

# Test importów
python3 -c "import streamlit; import chromadb; import torch; print('✅ Importy OK')"

# Test Ollama
curl http://localhost:11434/api/tags

# Sprawdź modele
ollama list
# Powinien być: gemma3:12b
```

**Oczekiwany czas:** < 1 minuta

---

### KROK 10: Uruchomienie aplikacji

#### Opcja A: Przez start_all.sh (zalecane)

```bash
cd ~/RAG
source venv_rag/bin/activate
bash start_all.sh
```

**Co się uruchomi:**
- File Watcher (tło) - automatyczna indeksacja plików
- Streamlit Frontend - UI na porcie 8501

**Zobaczysz:**
```
🚀 Uruchamianie pełnego systemu RAG
====================================
📁 Katalog projektu: /home/<user>/RAG

👁️  Uruchamianie File Watcher (tło)...
   ✅ Watchdog uruchomiony (PID: XXXX)

🌐 Uruchamianie Frontend...
======================================

📱 Dostęp lokalny: http://localhost:8501
🌐 Dostęp sieć lokalna: http://<IP>:8501

👤 Logowanie: admin / admin123

💡 Watchdog działa w tle
⏹️  Naciśnij Ctrl+C aby zatrzymać
```

#### Opcja B: Uruchomienie w tle (daemon)

```bash
cd ~/RAG
source venv_rag/bin/activate

# Uruchom w tle
nohup bash start_all.sh > logs/start_all.log 2>&1 &

# Sprawdź logi
tail -f logs/start_all.log

# Zatrzymanie
pkill -f streamlit
pkill -f file_watcher
```

**Oczekiwany czas:** 1-2 minuty (pierwsze uruchomienie - pobieranie modeli)

---

### KROK 11: Dostęp do aplikacji

#### A. Z konsoli szeregowej (lokalnie):

```bash
# Nie możesz otworzyć przeglądarki w konsoli szeregowej
# Użyj tunelu SSH lub publiczny IP
```

#### B. Przez publiczny IP Azure:

1. Znajdź publiczny IP:
   ```bash
   curl ifconfig.me
   # Lub w Azure Portal: Overview → Public IP address
   ```

2. Otwórz w przeglądarce:
   ```
   http://<PUBLICZNY_IP>:8501
   ```

3. Login:
   - Username: `admin`
   - Password: `admin123`

#### C. Przez SSH Tunnel (bezpieczniejsze):

**Na twoim lokalnym komputerze:**

```bash
# Utwórz tunel SSH
ssh -L 8501:localhost:8501 <user>@<PUBLICZNY_IP_VM>

# Teraz otwórz w przeglądarce lokalnie:
http://localhost:8501
```

---

### KROK 12: Weryfikacja działania

**W przeglądarce (http://<IP>:8501):**

1. ✅ **Login:** admin / admin123
2. ✅ **Upload test file:** Dodaj PDF lub obraz
3. ✅ **Sprawdź indeksację:** Plik powinien być przetworzony
4. ✅ **Zadaj pytanie:** Wpisz pytanie i kliknij "Szukaj odpowiedzi"
5. ✅ **Sprawdź monitoring:** GPU/CPU/RAM powinny się odświeżać

**W konsoli szeregowej:**

```bash
# Sprawdź procesy
ps aux | grep streamlit
ps aux | grep file_watcher

# Sprawdź logi
tail -f logs/rag_system.log
tail -f logs/streamlit.log

# Sprawdź Ollama
ollama ps
```

---

### KROK 13: (Opcjonalnie) Automatyczne uruchomienie przy starcie VM

#### Utwórz systemd service:

```bash
# Utwórz plik service
sudo nano /etc/systemd/system/rag-system.service
```

**Wklej:**
```ini
[Unit]
Description=RAG System - Streamlit + File Watcher
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
User=<TWOJ_USER>
WorkingDirectory=/home/<TWOJ_USER>/RAG
Environment="PATH=/home/<TWOJ_USER>/RAG/venv_rag/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/home/<TWOJ_USER>/RAG/venv_rag/bin/python3 -m streamlit run app/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Zapisz:** Ctrl+X, Y, Enter

```bash
# Przeładuj systemd
sudo systemctl daemon-reload

# Włącz autostart
sudo systemctl enable rag-system

# Uruchom
sudo systemctl start rag-system

# Sprawdź status
sudo systemctl status rag-system

# Logi
journalctl -u rag-system -f
```

---

## 🔒 BEZPIECZEŃSTWO

### 1. Zmień domyślne hasło

```bash
cd ~/RAG
source venv_rag/bin/activate
python3 app/manage_users.py
```

Wybierz: Zmień hasło dla `admin`

### 2. Firewall VM (opcjonalnie)

```bash
# Włącz UFW
sudo ufw enable

# Pozwól SSH
sudo ufw allow 22/tcp

# Pozwól Streamlit
sudo ufw allow 8501/tcp

# Sprawdź status
sudo ufw status
```

### 3. SSL/HTTPS (opcjonalnie, dla produkcji)

```bash
cd ~/RAG
sudo bash setup_nginx_ssl.sh
```

**To zainstaluje:**
- Nginx (reverse proxy)
- Certbot (SSL certificates)
- Auto-redirect HTTP → HTTPS

---

## 📊 MONITORING I DIAGNOSTYKA

### Sprawdź czy wszystko działa:

```bash
# 1. Ollama
systemctl status ollama
ollama list
curl http://localhost:11434/api/tags

# 2. Streamlit
ps aux | grep streamlit
netstat -tulpn | grep 8501

# 3. File Watcher
ps aux | grep file_watcher

# 4. Logi
tail -f ~/RAG/logs/rag_system.log
tail -f ~/RAG/logs/streamlit.log

# 5. GPU (jeśli masz)
nvidia-smi

# 6. RAM/CPU
htop
```

### Logi w czasie rzeczywistym:

```bash
# Terminal 1: RAG system log
tail -f ~/RAG/logs/rag_system.log

# Terminal 2: Streamlit log
tail -f ~/RAG/logs/streamlit.log

# Terminal 3: File watcher log
tail -f ~/RAG/logs/file_watcher.log
```

---

## 🐛 TROUBLESHOOTING

### Problem: "Port 8501 already in use"

```bash
# Zabij proces na porcie 8501
sudo lsof -ti:8501 | xargs kill -9

# Lub
pkill -f streamlit
```

### Problem: "Ollama connection refused"

```bash
# Sprawdź czy działa
systemctl status ollama

# Uruchom
sudo systemctl start ollama

# Test
curl http://localhost:11434/api/tags
```

### Problem: "No module named 'streamlit'"

```bash
# Sprawdź czy venv jest aktywny
which python3
# Powinno być: ~/RAG/venv_rag/bin/python3

# Jeśli nie, aktywuj:
source ~/RAG/venv_rag/bin/activate
```

### Problem: "CUDA not available" (jeśli masz GPU)

```bash
# Sprawdź drivers
nvidia-smi

# Jeśli brak, zainstaluj:
sudo apt install -y nvidia-driver-535
sudo reboot
```

### Problem: "Cannot access http://<IP>:8501"

```bash
# 1. Sprawdź czy Streamlit działa
ps aux | grep streamlit

# 2. Sprawdź firewall Azure (NSG)
# Azure Portal → VM → Networking → Sprawdź port 8501

# 3. Sprawdź local firewall
sudo ufw status
sudo ufw allow 8501/tcp

# 4. Sprawdź czy słucha na 0.0.0.0
netstat -tulpn | grep 8501
# Powinno być: 0.0.0.0:8501 (nie 127.0.0.1)
```

---

## 📝 NOTATKI I WSKAZÓWKI

### 1. Konsola szeregowa - ograniczenia:
- ❌ Brak copy-paste (w niektórych przypadkach)
- ❌ Brak przeglądarki
- ✅ Pełny dostęp do systemu
- ✅ Działa nawet gdy SSH nie działa

**Obejście:** Użyj SSH gdy już skonfigurujesz VM

### 2. Pierwsze uruchomienie - wolne:
- Pobieranie modeli Whisper (~3 GB)
- Pobieranie modeli Embeddings (~2 GB)
- Kompilacja niektórych bibliotek
- **Kolejne uruchomienia:** Szybkie (modele w cache)

### 3. Monitoring zasobów:

```bash
# RAM usage
free -h

# Disk usage
df -h

# GPU (jeśli masz)
watch -n 1 nvidia-smi

# Procesy Python
ps aux | grep python3
```

### 4. Zatrzymanie aplikacji:

```bash
# Ctrl+C w terminalu gdzie działa start_all.sh

# Lub kill processes:
pkill -f streamlit
pkill -f file_watcher

# Sprawdź czy zatrzymane
ps aux | grep streamlit
```

---

## 🔄 AKTUALIZACJA DO NOWSZEJ WERSJI

```bash
cd ~/RAG

# Zatrzymaj aplikację
pkill -f streamlit
pkill -f file_watcher

# Pull latest
git pull origin main

# Sprawdź nowe tagi
git tag -l

# Checkout konkretnej wersji (opcjonalnie)
git checkout v7

# Aktywuj venv i update dependencies
source venv_rag/bin/activate
pip install -r requirements.txt --upgrade

# Uruchom ponownie
bash start_all.sh
```

---

## 📊 TESTOWANIE PO INSTALACJI

### Quick test:

```bash
cd ~/RAG
source venv_rag/bin/activate

# Test basic
python3 -c "
from app.rag_system import RAGSystem
rag = RAGSystem()
print('✅ RAG System działa!')
"

# Test Ollama integration
python3 -c "
from app.model_provider import ModelFactory
provider = ModelFactory.create_provider()
print(f'✅ Model provider: {provider}')
"
```

### W przeglądarce:
1. Upload test PDF
2. Zadaj pytanie: "Co zawiera dokument?"
3. Sprawdź czy odpowiedź się generuje

---

## 🎯 CHECKLIST KOŃCOWY

Po instalacji sprawdź:

- [ ] Ollama działa (`systemctl status ollama`)
- [ ] Model gemma3:12b pobrany (`ollama list`)
- [ ] Python venv działa (`source venv_rag/bin/activate`)
- [ ] Wszystkie dependencies zainstalowane (`pip list`)
- [ ] Foldery utworzone (`ls -la ~/RAG`)
- [ ] Port 8501 otwarty w NSG (Azure Portal)
- [ ] Streamlit odpowiada (`curl http://localhost:8501`)
- [ ] Możesz zalogować się w przeglądarce
- [ ] Upload pliku działa
- [ ] Generowanie odpowiedzi działa

**Jeśli wszystko ✅ → Instalacja kompletna!** 🎉

---

## 📞 WSPARCIE

### Logi do diagnostyki:

```bash
# System RAG
~/RAG/logs/rag_system.log

# Streamlit
~/RAG/logs/streamlit.log

# File Watcher
~/RAG/logs/file_watcher.log

# Ollama
journalctl -u ollama -n 100

# System
journalctl -xe
```

### Restart wszystkiego:

```bash
# Zatrzymaj
pkill -f streamlit
pkill -f file_watcher

# Restart Ollama
sudo systemctl restart ollama

# Uruchom ponownie
cd ~/RAG
source venv_rag/bin/activate
bash start_all.sh
```

---

## 🚀 GOTOWE!

Po wykonaniu wszystkich kroków:

✅ RAG System działa  
✅ Dostępny przez przeglądarkę: `http://<IP>:8501`  
✅ Ollama backend aktywny  
✅ File watcher monitoruje folder `data/`  
✅ Wszystko logowane do `logs/`  

**Aplikacja gotowa do użycia!** 🎉

---

**Czas instalacji total:** ~40-60 minut  
**Autor instrukcji:** 2025-11-06  
**Wersja:** v7

