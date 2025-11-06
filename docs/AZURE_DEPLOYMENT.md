# 🌐 Migracja RAG System v4.0 na Azure Virtual Machine

**Cel**: Przeniesienie kompletnego systemu RAG na Azure VM (Ubuntu Linux)  
**Dostęp**: Konsola szeregowa (terminal only - brak dostępu do systemu plików)  
**Wyzwanie**: Transfer plików, konfiguracja, deployment bez GUI  

---

## 📋 SPIS TREŚCI

1. [Wymagania Azure VM](#wymagania-azure-vm)
2. [Przygotowanie Lokalne](#przygotowanie-lokalne)
3. [Transfer Plików](#transfer-plików)
4. [Instalacja na Azure VM](#instalacja-na-azure-vm)
5. [Konfiguracja](#konfiguracja)
6. [Uruchomienie](#uruchomienie)
7. [Problemy i Rozwiązania](#problemy-i-rozwiązania)
8. [Bezpieczeństwo](#bezpieczeństwo)
9. [Monitoring i Maintenance](#monitoring-i-maintenance)

---

## WYMAGANIA AZURE VM

### Minimalne (CPU Mode - bez GPU):
```
- VM Size: Standard_D4s_v3 lub większy
- vCPU: 4 cores
- RAM: 16 GB
- Disk: 128 GB SSD (Premium SSD)
- OS: Ubuntu 22.04 LTS
- Network: Public IP + port 8501 otwarty
```

**Koszty**: ~$140/miesiąc

### Recommended (z GPU - dla pełnej wydajności):
```
- VM Size: Standard_NC6s_v3 (NVIDIA Tesla V100)
- vCPU: 6 cores
- RAM: 112 GB
- GPU: 16 GB VRAM
- Disk: 256 GB Premium SSD
- OS: Ubuntu 22.04 LTS (with CUDA drivers)
- Network: Public IP + port 8501
```

**Koszty**: ~$900/miesiąc

### Dla testów (budżetowa opcja):
```
- VM Size: Standard_B2ms
- vCPU: 2 cores
- RAM: 8 GB
- Disk: 64 GB
- Mode: CPU-only (wolniejsze, ale działa!)
```

**Koszty**: ~$60/miesiąc

---

## PRZYGOTOWANIE LOKALNE

### 1. Przygotuj pakiet do transferu

```bash
cd /home/rev/projects/RAG2

# Utwórz folder deployment
mkdir -p deployment_package

# Skopiuj niezbędne pliki (bez venv, vector_db, data)
cp *.py deployment_package/
cp *.sh deployment_package/
cp *.md deployment_package/
cp requirements.txt deployment_package/
cp auth_config.json deployment_package/

# Skopiuj folder another_and_old (dokumentacja)
cp -r another_and_old deployment_package/

# Utwórz tarball
tar -czf rag_system_v4.tar.gz deployment_package/

echo "✅ Pakiet utworzony: rag_system_v4.tar.gz"
ls -lh rag_system_v4.tar.gz
```

**Wielkość pakietu**: ~50-100 KB (bez modeli!)

### 2. Opcjonalnie: Przygotuj dane testowe

```bash
# Jeśli chcesz przenieść istniejącą bazę (szybszy start)
tar -czf vector_db_backup.tar.gz vector_db/

# Lub przygotuj małe pliki testowe
mkdir -p deployment_package/test_data
cp data_backup/dokument1\ \(3\).pdf deployment_package/test_data/
tar -czf rag_with_testdata.tar.gz deployment_package/
```

---

## TRANSFER PLIKÓW

### Metoda 1: GitHub (NAJLEPSZE - już masz repo!)

```bash
# LOKALNIE: Push wszystko na GitHub
cd /home/rev/projects/RAG2
git add -A
git commit -m "Deployment package for Azure VM"
git push origin main

# NA AZURE VM (przez konsolę szeregową):
git clone https://github.com/AuCourDe/RAG-System-Private.git
cd RAG-System-Private
```

✅ **Zalety**: Bezpieczne, proste, nie wymaga otwartych portów  
✅ **Najlepsza opcja** dla Ciebie!

### Metoda 2: SCP (wymaga SSH)

```bash
# LOKALNIE:
scp rag_system_v4.tar.gz azureuser@<AZURE_VM_IP>:~

# NA AZURE VM:
tar -xzf rag_system_v4.tar.gz
cd deployment_package
```

### Metoda 3: wget (przez URL tymczasowe)

```bash
# LOKALNIE: Upload do transfer.sh (darmowy, tymczasowy)
curl --upload-file rag_system_v4.tar.gz https://transfer.sh/rag_system.tar.gz

# Skopiuj otrzymany URL (ważny 14 dni)

# NA AZURE VM:
wget <URL_Z_TRANSFER_SH>
tar -xzf rag_system.tar.gz
```

### Metoda 4: Azure Storage (przez konsołę)

```bash
# LOKALNIE: Upload do Azure Blob Storage
az storage blob upload \
    --account-name <your_storage> \
    --container-name deployment \
    --name rag_system_v4.tar.gz \
    --file rag_system_v4.tar.gz

# NA AZURE VM:
az storage blob download \
    --account-name <your_storage> \
    --container-name deployment \
    --name rag_system_v4.tar.gz \
    --file rag_system_v4.tar.gz
```

---

## INSTALACJA NA AZURE VM

### Krok 1: Połącz się z VM (Konsola Szeregowa)

1. Azure Portal → Virtual Machines → Twoja VM
2. Kliknij "Serial console" (lewa sidebar)
3. Zaloguj się credentials VM

### Krok 2: Podstawowe narzędzia

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Niezbędne pakiety
sudo apt install -y \
    python3.12 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    tmux \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-pol

# Verify Python version
python3 --version  # Powinno być 3.12+
```

### Krok 3: Clone projektu z GitHub

```bash
# Skonfiguruj Git credentials
git config --global user.name "AuCourDe"
git config --global user.email "your@email.com"

# Clone repo (użyj Personal Access Token)
git clone https://github.com/AuCourDe/RAG-System-Private.git
cd RAG-System-Private

# Lub jeśli już jest lokalny package:
tar -xzf rag_system_v4.tar.gz
cd deployment_package
```

### Krok 4: Virtual Environment

```bash
# Utwórz venv
python3 -m venv venv_rag

# Aktywuj
source venv_rag/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Krok 5: Instalacja zależności

```bash
# Instaluj requirements (może potrwać 10-20 minut!)
pip install -r requirements.txt

# Verify kluczowe biblioteki
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import chromadb; print('ChromaDB: OK')"
python3 -c "import streamlit; print('Streamlit: OK')"
```

**PROBLEM 1**: Instalacja PyTorch może trwać długo (2-3 GB download)  
**ROZWIĄZANIE**: Użyj tmux aby nie stracić sesji:
```bash
tmux new -s installation
pip install -r requirements.txt
# Ctrl+B, potem D aby odłączyć
# tmux attach -t installation aby wrócić
```

### Krok 6: Instalacja Ollama

```bash
# Pobierz i zainstaluj Ollama
curl -fsSL https://ollama.com/install.sh | sudo sh

# Verify
ollama --version

# Pobierz model Gemma 3:12B (to zajmie ~10 minut, ~8 GB download)
ollama pull gemma3:12b

# Sprawdź czy działa
ollama list
```

**PROBLEM 2**: Pobieranie modelu może timeout w konsoli szeregowej  
**ROZWIĄZANIE**: Użyj tmux + nohup:
```bash
tmux new -s ollama_download
nohup ollama pull gemma3:12b > ollama_download.log 2>&1 &
# Sprawdź postęp: tail -f ollama_download.log
```

### Krok 7: Utwórz foldery

```bash
mkdir -p data vector_db temp
touch suggested_questions.json image_descriptions.json

echo "[]" > suggested_questions.json
echo "{}" > image_descriptions.json
```

---

## KONFIGURACJA

### 1. Firewall / Network Security Group

**W Azure Portal**:
1. Virtual Machines → Twoja VM → Networking
2. Add inbound port rule:
   - Port: 8501
   - Protocol: TCP
   - Source: * (lub Twoje IP dla bezpieczeństwa)
   - Name: Allow_Streamlit

**Na VM** (opcjonalnie - ufw):
```bash
sudo ufw allow 8501/tcp
sudo ufw enable
sudo ufw status
```

### 2. Konfiguracja auth_config.json

```bash
# Edytuj hasło (WAŻNE!)
nano auth_config.json

# Zmień hasło admin (min. 8 znaków!)
# Opcjonalnie: Dodaj OpenAI API key
```

**JSON sample**:
```json
{
  "users": {
    "admin": {
      "password_hash": "<WYGENERUJ NOWY HASH>",
      "name": "Administrator"
    }
  },
  "openai": {
    "api_key": "",
    "model": "gpt-4o-mini",
    "enabled": false
  }
}
```

**Generowanie hasła**:
```bash
python3 -c "import hashlib; print(hashlib.sha256('TWOJE_NOWE_HASLO'.encode()).hexdigest())"
```

### 3. Dostosuj start_all.sh

```bash
# Edytuj start_all.sh
nano start_all.sh

# Zmień SERVER_ADDRESS jeśli potrzeba:
# --server.address 0.0.0.0  # Dla dostępu z zewnątrz
# --server.address 127.0.0.1  # Tylko lokalnie (tunel SSH)
```

---

## URUCHOMIENIE

### Opcja A: Foreground (dla testów)

```bash
# W tmux (aby nie stracić przy rozłączeniu)
tmux new -s rag_system

# Uruchom
./start_all.sh

# Sprawdź czy działa
# Ctrl+B, D aby odłączyć
# tmux attach -s rag_system aby wrócić
```

### Opcja B: Background (dla produkcji)

```bash
# Utwórz systemd service
sudo nano /etc/systemd/system/rag-watcher.service
```

**rag-watcher.service**:
```ini
[Unit]
Description=RAG File Watcher
After=network.target ollama.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/RAG-System-Private
ExecStart=/home/azureuser/RAG-System-Private/venv_rag/bin/python3 file_watcher.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**rag-frontend.service**:
```ini
[Unit]
Description=RAG Streamlit Frontend
After=network.target rag-watcher.service

[Service]
Type=simple
User=azureuser
WorkingDirectory=/home/azureuser/RAG-System-Private
ExecStart=/home/azureuser/RAG-System-Private/venv_rag/bin/python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable services**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rag-watcher
sudo systemctl enable rag-frontend
sudo systemctl start rag-watcher
sudo systemctl start rag-frontend

# Sprawdź status
sudo systemctl status rag-watcher
sudo systemctl status rag-frontend
```

### Sprawdź czy działa

```bash
# Sprawdź procesy
ps aux | grep -E "streamlit|file_watcher"

# Sprawdź logi
tail -f rag_system.log
tail -f file_watcher.log

# Test lokalny
curl http://localhost:8501

# Test z zewnątrz (z Twojego komputera)
curl http://<AZURE_VM_PUBLIC_IP>:8501
```

### Dostęp z przeglądarki

```
http://<AZURE_VM_PUBLIC_IP>:8501
```

---

## PROBLEMY I ROZWIĄZANIA

### Problem 1: Brak GPU na Azure VM

**Objaw**:
```
CUDA not available
DeviceManager: wszystko na CPU
```

**Rozwiązanie**:
```bash
# Sprawdź GPU
nvidia-smi

# Jeśli brak GPU:
# 1. Upewnij się że używasz NC-series VM (NC6s_v3, etc)
# 2. Zainstaluj CUDA drivers:

wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-drivers cuda-toolkit-12-8

# Reboot VM
sudo reboot

# Sprawdź ponownie
nvidia-smi
```

**Fallback CPU Mode**:
Jeśli VM bez GPU, system automatycznie przełączy się na CPU (device_mode='auto').
- Embeddings: 10-20s → 30-60s
- LLM (Gemma): 30-60s → 120-300s (używaj OpenAI API!)

### Problem 2: Konsola szeregowa timeout

**Objaw**: Połączenie konsoli przerywa się po 10-15 minutach

**Rozwiązanie**:
```bash
# ZAWSZE używaj tmux dla długich operacji
tmux new -s mywork

# Twoja praca...

# Odłącz: Ctrl+B, potem D
# Wrócić: tmux attach -s mywork

# Lista sesji: tmux ls
```

### Problem 3: Brak dostępu do systemu plików (tylko konsola)

**Objaw**: Nie możesz skopiować plików drag&drop

**Rozwiązanie A - Git** (NAJLEPSZE):
```bash
# Wszystko przez GitHub
git clone <repo>
git pull  # Update
```

**Rozwiązanie B - curl/wget**:
```bash
# Download przez URL
wget https://example.com/file.pdf -O data/file.pdf
```

**Rozwiązanie C - base64 encoding** (dla małych plików):
```bash
# LOKALNIE:
base64 small_file.txt > encoded.txt
cat encoded.txt  # Skopiuj output

# NA VM (w konsoli szeregowej):
cat > encoded.txt << 'EOF'
<PASTE BASE64 HERE>
EOF

base64 -d encoded.txt > small_file.txt
```

**Rozwiązanie D - SSH + SCP** (jeśli masz SSH):
```bash
# Włącz SSH w Azure
# Networking → Add inbound rule → Port 22

# Z lokalnego komputera:
scp file.pdf azureuser@<IP>:~/RAG-System-Private/data/
```

### Problem 4: Ollama nie ma GPU (na NC-series VM)

**Objaw**:
```bash
ollama ps
# Shows: 100% CPU (zamiast 100% GPU)
```

**Rozwiązanie**:
```bash
# Sprawdź NVIDIA drivers
nvidia-smi

# Jeśli nie ma outputu - zainstaluj drivers
sudo ubuntu-drivers autoinstall
sudo reboot

# Sprawdź czy Ollama widzi GPU
sudo systemctl restart ollama
ollama run gemma3:12b "test"  # Powinno użyć GPU
```

### Problem 5: Port 8501 nie odpowiada

**Rozwiązanie**:
```bash
# Sprawdź czy Streamlit działa
ps aux | grep streamlit

# Sprawdź czy port jest otwarty
sudo netstat -tulpn | grep 8501

# Sprawdź firewall
sudo ufw status

# Sprawdź Azure NSG (Network Security Group)
# Portal → VM → Networking → Inbound rules
# Dodaj regułę dla port 8501
```

### Problem 6: Brak pamięci RAM

**Objaw**:
```
MemoryError
Killed (OOM)
```

**Rozwiązanie**:
```bash
# Dodaj SWAP (jeśli VM ma mało RAM)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Dodaj do /etc/fstab (persistent)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Sprawdź
free -h
```

### Problem 7: Wolne embeddings (CPU mode)

**Objaw**: Indeksowanie PDF trwa 5-10 minut (zamiast 30-60s)

**Rozwiązanie A - OpenAI API**:
```bash
# Użyj OpenAI Embeddings API (szybsze!)
# Edytuj auth_config.json:
"openai": {
    "api_key": "sk-...",
    "model": "gpt-4o-mini"
}

# Koszt: ~$0.0001 per 1000 tokens (bardzo tani)
```

**Rozwiązanie B - Mniejszy model**:
```python
# Zmień w rag_system.py:
# 'intfloat/multilingual-e5-large' → 'intfloat/multilingual-e5-base'
# Szybsze 2x, jakość 90%
```

### Problem 8: Ollama pull timeout

**Objaw**: `ollama pull gemma3:12b` przerywa się

**Rozwiązanie**:
```bash
# Pull w tle z retries
tmux new -s ollama
while ! ollama pull gemma3:12b; do 
    echo "Retry..."
    sleep 5
done

# Lub użyj mniejszego modelu:
ollama pull gemma2:9b  # 5.5 GB zamiast 8 GB
```

### Problem 9: ChromaDB permission denied

**Objaw**:
```
PermissionError: vector_db/chroma.sqlite3
```

**Rozwiązanie**:
```bash
# Fix permissions
sudo chown -R $USER:$USER ~/RAG-System-Private
chmod -R 755 ~/RAG-System-Private

# Utwórz foldery z właściwymi prawami
mkdir -p data vector_db temp
chmod 755 data vector_db temp
```

### Problem 10: Streamlit nie startuje (port zajęty)

**Rozwiązanie**:
```bash
# Znajdź proces na porcie 8501
sudo lsof -i :8501

# Zabij
sudo kill -9 <PID>

# Lub zmień port w start_all.sh:
# --server.port 8502
```

---

## BEZPIECZEŃSTWO

### 1. HTTPS (SSL/TLS)

**Opcja A: Nginx Reverse Proxy** (zalecane):

```bash
sudo apt install nginx certbot python3-certbot-nginx

# Konfiguracja Nginx
sudo nano /etc/nginx/sites-available/rag

# Zawartość:
server {
    listen 80;
    server_name <TWOJA_DOMENA_LUB_IP>;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL (jeśli masz domenę):
sudo certbot --nginx -d twoja-domena.pl
```

**Opcja B: Cloudflare Tunnel** (bez domeny):

```bash
# Zainstaluj cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Uruchom tunel (w tmux!)
tmux new -s cloudflare
cloudflared tunnel --url http://localhost:8501

# Otrzymasz URL: https://xyz.trycloudflare.com
# HTTPS automatyczne!
```

### 2. Firewall Hardening

```bash
# Ogranicz dostęp do konkretnych IP
sudo ufw allow from <TWOJE_IP> to any port 8501
sudo ufw deny 8501

# Lub w Azure NSG:
# Source: IP Addresses → <TWOJE_IP>/32
```

### 3. SSH Key (zamiast password)

```bash
# LOKALNIE: Wygeneruj klucz
ssh-keygen -t ed25519 -C "azure_rag_vm"

# Dodaj public key do Azure VM
# Portal → VM → Reset password → Upload SSH public key
```

### 4. Monitoring nieautoryzowanego dostępu

```bash
# Sprawdź audit logi
cat audit_log.jsonl | grep '"success": false' | wc -l

# Failed logins
cat audit_log.jsonl | grep '"event_type": "login"' | grep 'false'

# Setup fail2ban (opcjonalnie)
sudo apt install fail2ban
```

---

## MONITORING I MAINTENANCE

### 1. Sprawdzanie statusu

```bash
# Procesy
ps aux | grep -E "streamlit|file_watcher|ollama"

# Porty
sudo netstat -tulpn | grep -E "8501|11434"

# GPU usage (jeśli GPU VM)
watch -n 1 nvidia-smi

# Logs
tail -f rag_system.log
tail -f file_watcher.log
tail -f audit_log.jsonl
```

### 2. Backup bazy wektorowej

```bash
# Cron job - backup co 24h
crontab -e

# Dodaj linię:
0 2 * * * tar -czf ~/backups/vector_db_$(date +\%Y\%m\%d).tar.gz ~/RAG-System-Private/vector_db/

# Utwórz folder backups
mkdir -p ~/backups
```

### 3. Cleanup audit logs (GDPR - 90 dni)

```bash
# Utwórz cron job
crontab -e

# Dodaj:
0 3 * * 0 cd ~/RAG-System-Private && /home/azureuser/RAG-System-Private/venv_rag/bin/python3 -c "from audit_logger import get_audit_logger; get_audit_logger().cleanup_old_logs()"
```

### 4. Update systemu

```bash
# Co tydzień:
cd ~/RAG-System-Private
git pull origin main

# Restart services
sudo systemctl restart rag-watcher
sudo systemctl restart rag-frontend

# Lub jeśli używasz tmux:
tmux kill-session -t rag_system
./start_all.sh
```

### 5. Monitoring użycia zasobów

```bash
# CPU, RAM, Disk
htop

# Disk space
df -h

# VRAM (jeśli GPU)
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# Network
sudo iftop  # Może wymagać: sudo apt install iftop
```

---

## DEPLOYMENT CHECKLIST

### Przed migracją:
- [ ] Utworzono Azure VM (odpowiedni rozmiar)
- [ ] Skonfigurowano NSG (port 8501, opcjonalnie 22 dla SSH)
- [ ] Public IP assigned
- [ ] Dostęp do konsoli szeregowej działa

### Transfer:
- [ ] Kod na GitHub (git push)
- [ ] Hasła zmienione w auth_config.json
- [ ] Tokeny API przygotowane (OpenAI, Bing - opcjonalnie)

### Na Azure VM:
- [ ] System zaktualizowany (apt update && upgrade)
- [ ] Python 3.12+ zainstalowany
- [ ] Git, ffmpeg, tesseract zainstalowane
- [ ] Projekt sklonowany z GitHub
- [ ] venv utworzony
- [ ] requirements.txt zainstalowane (wszystkie biblioteki)
- [ ] Ollama zainstalowane + model gemma3:12b pobrany
- [ ] Foldery utworzone (data, vector_db, temp)
- [ ] Firewall skonfigurowany (ufw + Azure NSG)
- [ ] Services lub tmux skonfigurowane
- [ ] Aplikacja uruchomiona i dostępna

### Testy:
- [ ] http://<IP>:8501 dostępne z przeglądarki
- [ ] Logowanie działa
- [ ] Upload pliku → indeksowanie działa
- [ ] Zapytanie → odpowiedź z AI
- [ ] GPU używane (nvidia-smi) lub CPU fallback
- [ ] Logi zapisują się (audit_log.jsonl)

### Security:
- [ ] Hasło admin zmienione
- [ ] Firewall aktywny (tylko port 8501)
- [ ] HTTPS włączone (Nginx + SSL lub Cloudflare Tunnel)
- [ ] Backup skonfigurowany (cron)
- [ ] Monitoring setup

---

## KOSZTY MIESIĘCZNE (szacunkowe)

### Azure VM:
| Typ | Specs | Koszty | Use Case |
|-----|-------|--------|----------|
| B2ms (budżet) | 2 vCPU, 8 GB RAM | ~$60 | Testy, CPU-only |
| D4s_v3 (recommended CPU) | 4 vCPU, 16 GB RAM | ~$140 | Produkcja CPU |
| NC6s_v3 (GPU) | 6 vCPU, 112 GB, V100 16GB | ~$900 | Produkcja GPU |

### Storage:
- 128 GB Premium SSD: ~$20/m
- 256 GB Premium SSD: ~$40/m

### Bandwidth:
- Outbound: ~$0.08/GB (pierwsze 100 GB free)

### API (opcjonalnie):
- OpenAI (gpt-4o-mini): $0.50-5/m (100-1000 queries)
- Bing Search API: $7/1000 queries

**Total dla produkcji CPU**: $140-160/m  
**Total dla produkcji GPU**: $900-950/m  

---

## ALTERNATYWY (tańsze opcje)

### 1. Azure Container Instances

**Zalety**: Płacisz per sekunda użycia, automatyczne skalowanie  
**Wady**: Wymaga Dockerization  

**Koszty**: ~$30-50/m (jeśli używane 8h/dzień)

### 2. Azure App Service (Web Apps)

**Zalety**: PaaS, łatwe deployment  
**Wady**: Bez GPU, limited Python packages  

**Koszty**: ~$55-200/m

### 3. Azure Kubernetes Service (AKS)

**Zalety**: Scalable, production-grade  
**Wady**: Complex setup  

**Koszty**: ~$100-300/m (minimum)

### 4. Lokalna maszyna + Azure dla frontendu

**Strategia**: 
- Heavy processing (embeddings, LLM) → Twój komputer (RTX 3060)
- Frontend + Nginx → Azure VM (mała, tania)
- Komunikacja przez VPN lub API

**Zalety**: Używasz swojego GPU ($0), Azure tylko dla dostępu  
**Koszty**: Azure ~$30-60/m (tylko frontend)

---

## REKOMENDACJE

### Dla testów/development:
✅ **Standard_B2ms** (2 vCPU, 8 GB RAM) - $60/m  
✅ **OpenAI API** dla LLM (szybsze niż CPU)  
✅ **Cloudflare Tunnel** dla HTTPS (darmowe)

### Dla małej produkcji (<50 użytkowników):
✅ **Standard_D4s_v3** (4 vCPU, 16 GB RAM) - $140/m  
✅ **OpenAI gpt-4o-mini** dla najlepszych wyników  
✅ **Nginx + Let's Encrypt** dla SSL  

### Dla dużej produkcji (>100 użytkowników, GPU):
✅ **Standard_NC6s_v3** (V100 GPU) - $900/m  
✅ **Lokalny Gemma 3:12B** (darmowy, prywatny)  
✅ **Load balancer** + multiple instances  

---

## QUICK START (GitHub Method)

```bash
# 1. NA AZURE VM (konsola szeregowa):
sudo apt update && sudo apt install -y git python3-venv ffmpeg tesseract-ocr

# 2. Clone repo
git clone https://github.com/AuCourDe/RAG.git
cd RAG-System-Private

# 3. Setup
python3 -m venv venv_rag
source venv_rag/bin/activate
pip install -r requirements.txt

# 4. Ollama (w tmux!)
tmux new -s ollama_setup
curl -fsSL https://ollama.com/install.sh | sudo sh
ollama pull gemma3:12b
# Ctrl+B, D

# 5. Start (w tmux!)
tmux new -s rag
./start_all.sh
# Ctrl+B, D

# 6. Test
curl http://localhost:8501
# Z przeglądarki: http://<AZURE_IP>:8501
```

**Czas setup**: 30-60 minut (w większości pobieranie Ollama model)

---

## 📞 WSPARCIE

**Dokumenty**:
- `PLAN_ROZWOJU.md` - architektura v4.0
- `WORKFLOW_I_SKALOWANIE.md` - szczegóły techniczne
- `action_log.txt` - historia zmian

**Problemy?**:
1. Sprawdź logi: `tail -f rag_system.log`
2. Sprawdź procesy: `ps aux | grep python`
3. Sprawdź GPU: `nvidia-smi` (jeśli VM z GPU)

---

**Dokument utworzony**: 2025-11-04  
**Wersja**: 1.0  
**System**: RAG v4.0  
**Target**: Azure Virtual Machine (Ubuntu 22.04 LTS)

