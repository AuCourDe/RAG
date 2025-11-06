# JAK DZIAŁA OLLAMA - Wyjaśnienie

## 🤔 Czym jest Ollama?

**Ollama** to **osobny serwis** (daemon), który działa w tle na systemie Linux i udostępnia modele LLM przez API HTTP.

---

## 🔄 Jak to działa w RAG2?

### 1. **Ollama działa NIEZALEŻNIE od aplikacji RAG**

```
┌─────────────────────┐      HTTP API       ┌──────────────────┐
│  Ollama Service     │ ◄──────────────────► │   RAG App        │
│  (localhost:11434)  │                      │   (Streamlit)    │
│                     │                      │                  │
│  - gemma3:12b       │                      │  - query()       │
│  - mistral          │                      │  - generate()    │
│  - llama2           │                      │                  │
└─────────────────────┘                      └──────────────────┘
```

### 2. **Ollama uruchamianie**

Ollama **NIE jest uruchamiany przez aplikację RAG**. Musi być uruchomiony **ręcznie** lub jako **systemd service**.

#### Opcja A: Uruchomienie ręczne
```bash
# Sprawdź czy działa
ollama list

# Uruchom serwis (jeśli nie działa)
ollama serve

# W tle (daemon)
nohup ollama serve > /dev/null 2>&1 &
```

#### Opcja B: Systemd service (automatyczne uruchomienie)
```bash
# Ollama instaluje się jako systemd service
systemctl status ollama

# Uruchom
sudo systemctl start ollama

# Włącz auto-start przy bootowaniu
sudo systemctl enable ollama
```

### 3. **Sprawdzenie stanu Ollama**

```bash
# Sprawdź czy serwis działa
curl http://localhost:11434/api/tags

# Lista załadowanych modeli
ollama list

# Sprawdź załadowany model
ollama ps
```

---

## 💻 Co robi aplikacja RAG?

Aplikacja RAG **tylko łączy się** do Ollama przez HTTP, **nie uruchamia** Ollama.

### W `model_provider.py`:

```python
class OllamaProvider:
    def __init__(self, model_name="gemma3:12b", base_url="http://127.0.0.1:11434"):
        self.base_url = base_url  # Adres serwisu Ollama
        self.model_name = model_name
        
    def generate(self, prompt, **kwargs):
        # Wysyła request HTTP do Ollama
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                ...
            }
        )
        return response.json()
```

### Przepływ:
1. Użytkownik zadaje pytanie w aplikacji RAG
2. RAG znajduje odpowiednie dokumenty (vector search)
3. RAG przygotowuje prompt z kontekstem
4. RAG **wysyła request HTTP** do Ollama (port 11434)
5. Ollama generuje odpowiedź używając modelu gemma3:12b
6. RAG otrzymuje odpowiedź i wyświetla użytkownikowi

---

## 🚀 Ollama - Start automatyczny

### Sprawdź czy Ollama działa przy starcie systemu:

```bash
# Status
systemctl status ollama

# Jeśli nie działa, włącz
sudo systemctl enable ollama
sudo systemctl start ollama
```

### Logi Ollama:
```bash
# Logi systemd
journalctl -u ollama -f

# Lub sprawdź proces
ps aux | grep ollama
```

---

## 📊 Zarządzanie modelami w Ollama

### Pobieranie modeli:
```bash
# Pobierz model
ollama pull gemma3:12b
ollama pull mistral
ollama pull llama2

# Lista pobranych
ollama list
```

### Modele są przechowywane w:
```bash
~/.ollama/models/
```

### Usunięcie modelu:
```bash
ollama rm gemma3:12b
```

---

## ⚙️ Konfiguracja w RAG

### W `auth_config.json`:
```json
{
  "ollama": {
    "model": "gemma3:12b",
    "base_url": "http://127.0.0.1:11434"
  }
}
```

### Zmiana modelu:
W aplikacji RAG (Streamlit UI):
- Sidebar → "Model LLM" → Wybierz model z listy

---

## 🔧 Troubleshooting

### Problem: "Connection refused" lub "Ollama niedostępny"

**Przyczyna:** Ollama nie działa

**Rozwiązanie:**
```bash
# Uruchom Ollama
ollama serve

# Lub jako systemd
sudo systemctl start ollama

# Sprawdź
curl http://localhost:11434/api/tags
```

### Problem: Model nie jest dostępny

**Przyczyna:** Model nie został pobrany

**Rozwiązanie:**
```bash
ollama pull gemma3:12b
```

### Problem: Ollama zużywa dużo VRAM

**Przyczyna:** Model jest załadowany w pamięci GPU

**Rozwiązanie:**
```bash
# Wyładuj model
ollama stop gemma3:12b

# Lub restartuj Ollama
sudo systemctl restart ollama
```

---

## 📈 Wydajność

### Ollama auto-zarządza VRAM:
- **Pierwszy request:** Ładuje model do VRAM (~5-10s)
- **Kolejne requesty:** Model już w pamięci (szybkie, <1s)
- **Idle:** Po kilku minutach bezczynności wyładowuje model

### Monitoring:
```bash
# GPU usage
nvidia-smi

# Ollama proces
ollama ps
```

---

## 🎯 Podsumowanie

| Pytanie | Odpowiedź |
|---------|-----------|
| **Czy Ollama działa cały czas?** | TAK, jako service w tle (daemon) |
| **Czy RAG uruchamia Ollama?** | NIE, tylko łączy się przez HTTP |
| **Czy Ollama musi działać?** | TAK, inaczej RAG nie wygeneruje odpowiedzi |
| **Gdzie są modele?** | `~/.ollama/models/` |
| **Jak zmienić model?** | W UI Streamlit lub `auth_config.json` |
| **Czy można wyłączyć Ollama?** | TAK: `sudo systemctl stop ollama` |

---

## 🌐 Alternatywy dla Ollama

Aplikacja RAG obsługuje też:
- **OpenAI API** (GPT-4, GPT-3.5) - wymaga klucza API
- **Inne kompatybilne API** (LM Studio, text-generation-webui)

Konfiguracja w `model_provider.py` i `auth_config.json`.

---

**✅ Wnioski:**
- Ollama = osobny serwis, działa w tle
- RAG = klient HTTP, wysyła zapytania do Ollama
- Ollama można uruchomić raz i zostawić (auto-zarządza VRAM)

