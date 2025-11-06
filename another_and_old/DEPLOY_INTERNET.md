# 🌍 Wystawienie Systemu RAG na Internet

Masz **stałe IP** - świetnie! Masz kilka opcji wystawienia aplikacji na zewnątrz.

---

## ⚡ SZYBKI START (najprostsze)

### Krok 1: Uruchom aplikację
```bash
cd /home/rev/projects/RAG2
./start_app.sh
```

### Krok 2: Otwórz port w firewall/routerze
- Przekieruj port **8501** na swój komputer
- Lub użyj innego portu zewnętrznego

### Krok 3: Dostęp z internetu
```
http://TWOJE_STALE_IP:8501
```

### Krok 4: Zaloguj się
```
Login: admin
Hasło: admin123
```

⚠️ **ZMIEŃ hasło natychmiast** w zakładce "Ustawienia"!

---

## 🔒 Opcja 1: Nginx + SSL (ZALECANE dla produkcji)

To da Ci **HTTPS** (szyfrowanie) i darmowy certyfikat SSL.

### Potrzebujesz:
- **Domenę** (opcjonalne, ale zalecane): np. `rag.twojafirma.pl`
- Domena musi wskazywać na Twoje stałe IP (rekord A w DNS)

### Automatyczna instalacja:
```bash
cd /home/rev/projects/RAG2
sudo ./setup_nginx_ssl.sh
```

Skrypt:
1. Zainstaluje Nginx i Certbot
2. Skonfiguruje reverse proxy
3. Ustawi SSL (jeśli masz domenę)
4. Automatycznie odnawia certyfikat co 90 dni

### Dostęp:
```
https://twoja-domena.pl
```

### Zalety:
- ✅ Szyfrowane połączenie (HTTPS)
- ✅ Automatyczne odnowienie certyfikatu
- ✅ Profesjonalny wygląd
- ✅ Lepsza wydajność
- ✅ Możliwość wielu aplikacji na jednym IP

---

## 🚀 Opcja 2: Bezpośrednie wystawienie (bez domeny)

Jeśli **nie masz domeny** lub chcesz szybkie rozwiązanie.

### 1. Aplikacja już nasłuchuje na 0.0.0.0:8501
```bash
./start_app.sh
```

### 2. Skonfiguruj firewall na serwerze:
```bash
# Zainstaluj ufw (jeśli nie masz)
sudo apt install ufw

# Opcja A: Dostęp dla wszystkich (mniej bezpieczne)
sudo ufw allow 8501/tcp

# Opcja B: Dostęp tylko dla konkretnego IP (bezpieczniejsze)
sudo ufw allow from IP_UZYTKOWNIKA to any port 8501

# Włącz firewall
sudo ufw enable

# Sprawdź status
sudo ufw status
```

### 3. Skonfiguruj router:
- Wejdź do panelu routera
- Znajdź "Port Forwarding" lub "Przekierowanie portów"
- Przekieruj port **8501** (zewnętrzny) → **8501** (wewnętrzny) → IP Twojego komputera

### 4. Dostęp z internetu:
```
http://TWOJE_STALE_IP:8501
```

### Zalety:
- ✅ Najprostsze
- ✅ Działa od razu
- ✅ Nie wymaga domeny

### Wady:
- ❌ Brak HTTPS (nieszyfrowane)
- ❌ Port w URL wygląda nieprofesjonalnie
- ❌ Mniej bezpieczne

---

## 🌐 Opcja 3: Cloudflare Tunnel (darmowa domena + SSL)

Jeśli **nie masz własnej domeny**, Cloudflare da Ci darmową subdomenę + SSL.

### Instalacja:
```bash
# Pobierz cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Uruchom aplikację
cd /home/rev/projects/RAG2
./start_app.sh
```

### W nowym terminalu:
```bash
# Zaloguj się do Cloudflare (otworzy przeglądarkę)
cloudflared tunnel login

# Utwórz tunel
cloudflared tunnel create rag-system

# Skonfiguruj tunel
cat > ~/.cloudflared/config.yml << EOF
tunnel: rag-system
credentials-file: /home/rev/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: rag.twoja-domena.com
    service: http://localhost:8501
  - service: http_status:404
EOF

# Uruchom tunel
cloudflared tunnel run rag-system
```

### Dostęp:
```
https://rag.twoja-domena.com
```

### Zalety:
- ✅ Darmowa subdomena Cloudflare
- ✅ Automatyczne HTTPS
- ✅ DDoS protection
- ✅ Nie wymaga otwierania portów
- ✅ Działa za NAT

---

## 🔐 Opcja 4: ngrok (szybki test)

Najszybsza opcja do **testowania** (nie do długoterminowego użytku).

### Instalacja:
```bash
# Zainstaluj
sudo snap install ngrok

# Zarejestruj się na ngrok.com i dodaj token
ngrok config add-authtoken TWOJ_TOKEN
```

### Użycie:
```bash
# Uruchom aplikację
cd /home/rev/projects/RAG2
./start_app.sh

# W nowym terminalu:
ngrok http 8501
```

### Dostęp:
```
https://xyz123.ngrok.io  (URL zmienia się przy każdym uruchomieniu)
```

### Zalety:
- ✅ Działa od razu
- ✅ Automatyczne HTTPS
- ✅ Nie wymaga konfiguracji

### Wady:
- ❌ URL zmienia się przy każdym uruchomieniu (w darmowej wersji)
- ❌ Limit 40 połączeń/minutę (darmowa wersja)
- ❌ Nie dla produkcji

---

## 🔒 BEZPIECZEŃSTWO - WAŻNE!

### 1. Zmień domyślne hasło
```
1. Zaloguj się: admin / admin123
2. Zakładka "Ustawienia" → "Zmiana hasła"
3. Ustaw silne hasło (min. 12 znaków)
```

### 2. Firewall
```bash
# Zezwól tylko na porty, których używasz
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 22/tcp      # SSH (dla Ciebie)
sudo ufw enable
```

### 3. Fail2ban (opcjonalne, ale zalecane)
```bash
# Blokuje IP po wielu nieudanych logowaniach
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### 4. Regularne aktualizacje
```bash
sudo apt update
sudo apt upgrade
```

### 5. Ograniczenie IP (jeśli znasz IP użytkownika)
```bash
# Nginx - edytuj /etc/nginx/sites-available/rag-system
# Dodaj w sekcji server:
allow IP_UZYTKOWNIKA;
deny all;
```

---

## 📊 Porównanie opcji

| Opcja | Trudność | HTTPS | Domena | Koszt | Produkcja |
|-------|----------|-------|--------|-------|-----------|
| **Nginx + SSL** | ⭐⭐⭐ | ✅ | Wymagana | 0 PLN | ✅ |
| **Bezpośrednie** | ⭐ | ❌ | Nie | 0 PLN | ⚠️ |
| **Cloudflare** | ⭐⭐ | ✅ | Darmowa | 0 PLN | ✅ |
| **ngrok** | ⭐ | ✅ | Losowy URL | 0-20 USD/m | ❌ |

---

## 🎯 Moja rekomendacja

### Masz domenę?
→ **Użyj Nginx + SSL** (Opcja 1)

### Nie masz domeny, ale chcesz profesjonalnie?
→ **Cloudflare Tunnel** (Opcja 3)

### Chcesz szybko przetestować?
→ **ngrok** (Opcja 4)

### Chcesz najprostsze rozwiązanie?
→ **Bezpośrednie wystawienie** (Opcja 2)

---

## 🛠️ Utrzymanie

### Sprawdź czy aplikacja działa:
```bash
curl http://localhost:8501
```

### Sprawdź logi:
```bash
tail -f /home/rev/projects/RAG2/rag_system.log
```

### Restart aplikacji:
```bash
# Znajdź proces
ps aux | grep streamlit

# Zabij proces
kill PID

# Uruchom ponownie
./start_app.sh
```

### Automatyczne uruchomienie po restarcie serwera:
```bash
# Utwórz usługę systemd
sudo tee /etc/systemd/system/rag-system.service > /dev/null <<EOF
[Unit]
Description=RAG System Streamlit
After=network.target

[Service]
Type=simple
User=rev
WorkingDirectory=/home/rev/projects/RAG2
ExecStart=/home/rev/projects/RAG2/venv_rag/bin/python3 -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Włącz usługę
sudo systemctl enable rag-system
sudo systemctl start rag-system

# Sprawdź status
sudo systemctl status rag-system
```

---

## 📞 Testowanie

### Sprawdź dostęp z internetu:
```bash
# Z innego komputera lub smartfona (poza siecią domową)
curl -I http://TWOJE_STALE_IP:8501

# Powinno zwrócić: HTTP/1.1 200 OK
```

### Sprawdź SSL (jeśli używasz):
```bash
curl -I https://twoja-domena.pl

# Powinno zwrócić: HTTP/2 200
```

---

## 🆘 Rozwiązywanie problemów

### Port 8501 zajęty:
```bash
# Znajdź proces
sudo lsof -i :8501

# Zabij proces
kill -9 PID
```

### Nginx nie działa:
```bash
# Sprawdź logi
sudo tail -f /var/log/nginx/error.log

# Test konfiguracji
sudo nginx -t

# Restart
sudo systemctl restart nginx
```

### SSL nie działa:
```bash
# Sprawdź czy domena wskazuje na Twoje IP
nslookup twoja-domena.pl

# Ręcznie odnów certyfikat
sudo certbot renew --dry-run
```

### Nie mogę się połączyć z internetu:
1. Sprawdź firewall serwera: `sudo ufw status`
2. Sprawdź port forwarding w routerze
3. Sprawdź czy masz stałe IP: `curl ifconfig.me`
4. Sprawdź czy port jest otwarty: https://www.yougetsignal.com/tools/open-ports/

---

## 📚 Dodatkowe zasoby

- [Let's Encrypt](https://letsencrypt.org/)
- [Nginx Docs](https://nginx.org/en/docs/)
- [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [ngrok](https://ngrok.com/)
- [Streamlit Deployment](https://docs.streamlit.io/knowledge-base/deploy)

---

**Powodzenia!** 🚀

Jeśli masz pytania, sprawdź najpierw:
- `README.md` - ogólny opis systemu
- `USAGE.md` - instrukcja użycia
- `action_log.txt` - historia zmian

