# 🚀 Szybki Start - System RAG

## 1️⃣ Uruchom system (wszystko naraz):

```bash
cd /home/rev/projects/RAG2
./start_all.sh
```

## 2️⃣ Otwórz przeglądarkę:

**Lokalnie:**
```
http://localhost:8501
```

**W sieci lokalnej (z innego komputera):**
```
http://172.29.211.186:8501
```

## 3️⃣ Zaloguj się:

```
👤 Użytkownik: admin
🔑 Hasło: admin123
```

⚠️ **ZMIEŃ hasło** w zakładce "Ustawienia"!

---

## ✅ Co działa:

- ✅ **Frontend** - interfejs webowy
- ✅ **Watchdog** - automatyczne indeksowanie nowych plików
- ✅ **GPU** - pełne wykorzystanie (RTX 3060)
- ✅ **Gemma 3** - rozpoznawanie obrazów i odpowiedzi
- ✅ **Autoryzacja** - zabezpieczenie hasłem

---

## 💡 Jak użyć:

### Zadawanie pytań:
1. Zakładka "💬 Zapytania"
2. Wpisz pytanie (np. "Co grozi za kradzież?")
3. Kliknij "🔍 Szukaj odpowiedzi"
4. Poczekaj ~30-60 sekund
5. Zobacz odpowiedź z referencjami do źródeł

### Dodawanie nowych dokumentów:
1. Zakładka "📤 Indeksowanie"
2. Przeciągnij pliki (PDF/DOCX/XLSX/obrazy)
3. Kliknij "💾 Zapisz i zaindeksuj"
4. Watchdog automatycznie przetworzy pliki

LUB po prostu:
```bash
cp nowy_dokument.pdf data/
# Watchdog automatycznie wykryje i zaindeksuje!
```

---

## 🌐 Udostępnienie w internecie:

### Opcja 1: ngrok (5 minut)

```bash
# Terminal 1: Uruchom aplikację
./start_all.sh

# Terminal 2: Uruchom tunel
snap install ngrok
ngrok http 8501
```

Otrzymasz URL: `https://abc123.ngrok.io` ✅

### Opcja 2: Cloudflare (darmowy, bez limitów)

```bash
# Zainstaluj cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared-linux-amd64.deb

# Uruchom aplikację
./start_all.sh

# W nowym terminalu: uruchom tunel
cloudflared tunnel --url http://localhost:8501
```

Otrzymasz URL: `https://xyz.trycloudflare.com` ✅

---

## 🛑 Zatrzymanie systemu:

```bash
# W terminalu gdzie działa aplikacja:
Ctrl + C

# Lub zabij proces:
pkill -f streamlit
pkill -f file_watcher
```

---

## 📝 Troubleshooting:

**Problem: Port zajęty**
```bash
lsof -i :8501
kill -9 $(lsof -t -i:8501)
```

**Problem: Gemma 3 używa CPU zamiast GPU**
```bash
ollama ps
# Powinno pokazać: "100% GPU"
```

**Problem: Watchdog nie wykrywa plików**
```bash
tail -f file_watcher.log
```

---

## 📚 Więcej informacji:

- `README.md` - pełna dokumentacja
- `USAGE.md` - instrukcje użycia
- `action_log.txt` - historia zmian

---

**TO WSZYSTKO! System gotowy do użycia! 🎉**


