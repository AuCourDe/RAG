#!/bin/bash
# Skrypt do konfiguracji Nginx + SSL dla Streamlit RAG

echo "🔧 Konfiguracja Nginx + SSL dla Streamlit"
echo "=========================================="
echo ""

# 1. Instalacja Nginx i Certbot
echo "📦 Instalacja Nginx i Certbot..."
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx

# 2. Poproś o domenę (opcjonalne) lub użyj IP
read -p "Masz domenę? (tak/nie): " has_domain

if [ "$has_domain" = "tak" ]; then
    read -p "Wpisz swoją domenę (np. rag.example.com): " domain
    use_ssl=true
else
    echo "Używam stałego IP (bez SSL)"
    read -p "Wpisz swoje stałe IP: " domain
    use_ssl=false
fi

# 3. Utwórz konfigurację Nginx
echo "📝 Tworzenie konfiguracji Nginx..."
sudo tee /etc/nginx/sites-available/rag-system > /dev/null <<EOF
server {
    listen 80;
    server_name $domain;

    # Zwiększ limity dla dużych plików
    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header Host \$host;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }
}
EOF

# 4. Aktywuj konfigurację
sudo ln -sf /etc/nginx/sites-available/rag-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo "✅ Nginx skonfigurowany!"

# 5. SSL (jeśli ma domenę)
if [ "$use_ssl" = true ]; then
    echo "🔒 Konfiguracja SSL (Let's Encrypt)..."
    read -p "Podaj email dla certyfikatu SSL: " email
    sudo certbot --nginx -d $domain --non-interactive --agree-tos -m $email
    
    if [ $? -eq 0 ]; then
        echo "✅ SSL skonfigurowany! Dostęp: https://$domain"
    else
        echo "❌ Błąd SSL - sprawdź czy domena wskazuje na Twoje IP"
        echo "   Możesz spróbować ręcznie: sudo certbot --nginx"
    fi
else
    echo "✅ Dostęp: http://$domain"
fi

echo ""
echo "📋 PODSUMOWANIE:"
echo "=================="
echo "1. Streamlit uruchom: ./start_app.sh"
echo "2. Nginx automatycznie przekieruje na port 80 (lub 443 dla HTTPS)"
if [ "$use_ssl" = true ]; then
    echo "3. Dostęp: https://$domain"
else
    echo "3. Dostęp: http://$domain"
fi
echo "4. Login: admin / admin123 (ZMIEŃ hasło!)"
echo ""
echo "🔧 Przydatne komendy:"
echo "  sudo systemctl status nginx    - status Nginx"
echo "  sudo systemctl restart nginx   - restart Nginx"
echo "  sudo certbot renew            - odnów certyfikat SSL"

