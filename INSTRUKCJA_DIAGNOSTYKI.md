# Instrukcja diagnostyki uploadu plikow

## Status aplikacji

Aplikacja uruchomiona z pelnym logowaniem diagnostycznym.

- **Watchdog:** PID 114645 - monitoruje folder data/
- **Streamlit:** PID 114665 - http://localhost:8501
- **Logi:** Wszystkie akcje sa logowane z prefiksem "DIAGNOSTYKA"

## Jak testowac

1. Otworz http://localhost:8501
2. Zaloguj sie (admin/admin123)
3. Przejdz do zakladki "Indeksowanie"
4. Kliknij "Browse files" (file_uploader)
5. Wybierz plik PDF
6. Sprawdz logi (ponizej)

## Monitorowanie logow

### Opcja 1: W czasie rzeczywistym (nowy terminal)

```bash
cd /home/rev/projects/RAG-Reborn/source_reference
bash test/monitor_logs.sh
```

### Opcja 2: Tylko ostatnie logi

```bash
tail -f rag_system.log | grep DIAGNOSTYKA
```

### Opcja 3: Wszystkie logi diagnostyczne

```bash
grep -E "DIAGNOSTYKA|PRZYCISK|KLIKNIETY" rag_system.log | tail -50
```

## Co jest logowane

### File Uploader
- Przed i po st.file_uploader()
- Wartosc uploaded_files
- Zapis do session_state.pending_uploaded_files

### Przycisk "Zapisz pliki"
- Klikniecie przycisku
- Liczba plikow do zapisania
- Sciezki zapisu
- Status zapisu

### Przycisk "Odswiez liste"
- Klikniecie przycisku
- Stan session_state

### Przycisk "Reindeksuj wszystkie pliki"
- Klikniecie przycisku
- Zawartosc folderu data/
- Pliki do przetworzenia

## Oczekiwane logi podczas testu

1. **Po kliknieciu "Browse files":**
   ```
   DIAGNOSTYKA: File uploader - przed st.file_uploader()
   DIAGNOSTYKA: File uploader - po st.file_uploader()
   DIAGNOSTYKA: uploaded_files type: <class 'list'>
   DIAGNOSTYKA: uploaded_files len: 1
   DIAGNOSTYKA: - Uploaded file: nazwa.pdf, size: 123456
   DIAGNOSTYKA: Zapisano 1 plikow do session_state.pending_uploaded_files
   ```

2. **Po kliknieciu "Zapisz pliki":**
   ```
   DIAGNOSTYKA: PRZYCISK 'Zapisz pliki' KLIKNIETY!
   DIAGNOSTYKA: Liczba plikow do zapisania: 1
   DIAGNOSTYKA: PROJECT_ROOT = /path/to/project
   DIAGNOSTYKA: data_dir = /path/to/project/data
   DIAGNOSTYKA: File saved successfully: /path/to/project/data/nazwa.pdf
   ```

3. **Po kliknieciu "Odswiez liste":**
   ```
   DIAGNOSTYKA: PRZYCISK 'Odswiez liste' KLIKNIETY!
   ```

4. **Po kliknieciu "Reindeksuj wszystkie pliki":**
   ```
   DIAGNOSTYKA: PRZYCISK 'Reindeksuj wszystkie pliki' KLIKNIETY!
   DIAGNOSTYKA: data_dir = /path/to/project/data
   DIAGNOSTYKA: Wszystkie pliki w data/: X
   DIAGNOSTYKA: Pliki do przetworzenia: X
   ```

## Rozwiazywanie problemow

### Problem: uploaded_files len: 0
- **Przyczyna:** Streamlit file_uploader nie przekazuje plikow
- **Sprawdz:** Czy plik zostal wybrany w file_uploader?
- **Sprawdz:** Czy nie ma bledow w konsoli przegladarki?

### Problem: files_to_process z session_state: 0 plikow
- **Przyczyna:** Pliki nie zostaly zapisane do session_state
- **Sprawdz:** Czy pojawil sie log "Zapisano X plikow do session_state"?

### Problem: Plik nie pojawia sie w data/
- **Przyczyna:** Przycisk "Zapisz pliki" nie zostal klikniety lub blad zapisu
- **Sprawdz:** Czy pojawil sie log "PRZYCISK 'Zapisz pliki' KLIKNIETY!"?
- **Sprawdz:** Czy pojawil sie log "File saved successfully"?

