# ✨ Generator Opowiadań AI - Demo

Interaktywna aplikacja webowa do generowania spersonalizowanych opowiadań z ilustracjami przy użyciu GPT-4o i DALL-E 3. Projekt demonstracyjny pokazujący integrację dużych modeli językowych z interfejsem użytkownika, monitoring Langfuse oraz zabezpieczenia treści.

---

## 🎯 Funkcje

### **Generowanie opowiadań:**
- ✨ **3 gatunki literackie:** Bajka, Romans, Kryminał
- 🎭 **Dynamiczne tony narracji:** Każdy gatunek ma 3 unikalne tony (np. Bajka: Zabawna, Magiczna, Mądra)
- 📏 **3 długości:** Krótka (~100-200 słów), Średnia (~200-400 słów), Długa (~400-600 słów)
- 🎨 **Generowanie ilustracji:** DALL-E 3 tworzy profesjonalne ilustracje dopasowane do opowiadania
- 💾 **Pobieranie:** Eksport opowiadania do `.txt` i ilustracji do `.png`

### **Bezpieczeństwo i jakość:**
- 🛡️ **Filtry bezpieczeństwa treści:** Specyficzne dla każdego gatunku (brak przemocy, wulgaryzmów, treści +18)
- 🔒 **Zabezpieczenie hasłem:** Demo dostępne przez 24h po zalogowaniu
- 📊 **Langfuse monitoring:** Automatyczne śledzenie kosztów, tokenów i jakości odpowiedzi

### **Interfejs użytkownika:**
- ❄️ **Animowane tło:** Płatki śniegu (sezonowe, można zmienić na gwiazdki)
- 📱 **Responsywny design:** Działa na desktop i mobile
- 📚 **Historia opowiadań:** Sidebar z ostatnimi 5 wygenerowanymi historiami
- 📊 **Statystyki:** Liczba słów, zdań, szacowany czas czytania

---

## 🚀 Demo na żywo

🔗 **[Zobacz demo](https://twoj-link-do-demo.streamlit.app)** *(dostępne po wdrożeniu)*

**Kod dostępu:** Skontaktuj się, aby otrzymać hasło demo (ważne 24h)

---

## 📸 Screenshot

*(Dodaj screenshot aplikacji tutaj)*

---

## 🛠 Tech Stack

**Backend:**
- Python 3.11+
- Streamlit 1.32+
- OpenAI API (GPT-4o + DALL-E 3)
- Langfuse 2.50+ (monitoring i analytics)

**Frontend:**
- Custom CSS z animacjami
- Responsive layout
- Pills UI pattern

**Deployment:**
- Streamlit Cloud / DigitalOcean
- Secrets management via `.streamlit/secrets.toml`

---

## 💻 Instalacja lokalna

### **1. Wymagania**

**System:**
- Python 3.11+ *(testowane na 3.11.13)*
- pip 23+
- Git

**Konta i klucze API:**
- [OpenAI API key](https://platform.openai.com/api-keys) - dla GPT-4o i DALL-E 3
- [Langfuse account](https://cloud.langfuse.com) - darmowe konto (public key + secret key)

**Koszty API:** *(szacunkowe, zależne od użycia)*
- GPT-4o: ~$0.005-0.015 za opowiadanie (w zależności od długości)
- DALL-E 3: ~$0.04 za ilustrację (1024x1024, standard quality)

---

### **2. Sklonuj repozytorium**

```bash
git clone https://github.com/multifuture/generator-opowiadan-demo.git
cd generator-opowiadan-demo
```

---

### **3. Zainstaluj zależności**

**Stwórz środowisko wirtualne (zalecane):**

```bash
# Conda
conda create -n story_gen python=3.11
conda activate story_gen

# lub venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```

**Zainstaluj pakiety:**

```bash
pip install -r requirements.txt
```

---

### **4. Konfiguracja kluczy API**

**Stwórz plik `.streamlit/secrets.toml`:**

```bash
mkdir .streamlit
touch .streamlit/secrets.toml  # Linux/Mac
# lub stwórz ręcznie w Windows
```

**Dodaj klucze:**

```toml
# OpenAI
OPENAI_API_KEY = "sk-proj-twoj_klucz_tutaj"

# Access password (24h demo)
ACCESS_PASSWORD = "twoje_haslo_demo"

# Langfuse
LANGFUSE_PUBLIC_KEY = "pk-lf-twoj_klucz"
LANGFUSE_SECRET_KEY = "sk-lf-twoj_klucz"
LANGFUSE_HOST = "https://cloud.langfuse.com"
```

**⚠️ WAŻNE:** 
- Nigdy nie commituj pliku `secrets.toml` do repozytorium!
- Plik jest już w `.gitignore`

---

### **5. Dodaj logo (opcjonalne)**

```bash
mkdir assets
# Skopiuj swoje logo do assets/logo.png
```

Jeśli nie masz logo, zakomentuj sekcję z logo w kodzie lub usuń odniesienie.

---

### **6. Uruchom aplikację**

```bash
streamlit run app.py
```

Aplikacja otworzy się w przeglądarce pod adresem: `http://localhost:8501`

---

## 📦 Struktura projektu

```
generator-opowiadan-demo/
├── app_demo.py                      # Główny plik aplikacji
├── requirements.txt            # Zależności Python
├── README.md                   # Ten plik
├── .gitignore                  # Pliki ignorowane przez Git
├── .streamlit/
│   └── secrets.toml           # Klucze API (NIE commitować!)
└── assets/
    └── logo.png               # Logo Multi-Future (opcjonalne)
```

---

## 🎨 Customizacja

### **Zmiana kolorów tła:**

W pliku `app.py`, znajdź sekcję CSS (linia ~170):

```css
.stApp {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}
```

Zmień kolory hex na własne.

---

### **Zmiana animacji (śnieżynki → gwiazdki):**

W sekcji CSS, zmień `.particle` (linia ~210):

```css
.particle {
    background: rgba(255, 215, 0, 0.8);  /* Złoty kolor */
    box-shadow: 0 0 10px rgba(255, 215, 0, 0.6);
}
```

---

### **Wyłączenie generowania obrazów:**

Zakomentuj przycisk "Generuj grafikę" w sekcji Action buttons (linia ~1020).

---

## 📊 Monitoring w Langfuse

Po uruchomieniu aplikacji i wygenerowaniu opowiadań, zaloguj się do [Langfuse Dashboard](https://cloud.langfuse.com):

**Co zobaczysz:**
- 📈 **Traces:** Każde wywołanie GPT-4o i DALL-E 3
- 💰 **Koszty:** Automatycznie liczone per request
- 🔢 **Tokeny:** Input/output dla każdego requestu
- ⏱️ **Latency:** Czas odpowiedzi API
- 📝 **Pełne prompty:** System + user messages

---

## 🔒 Bezpieczeństwo

**Obecne zabezpieczenia:**
- ✅ Hasło dostępu (24h sesja)
- ✅ Klucze API w `secrets.toml` (nie w kodzie)
- ✅ Content safety rules dla każdego gatunku
- ✅ Rate limiting (poprzez session state)

**Dla produkcji dodaj:**
- 🔐 OAuth/SSO dla użytkowników
- 💳 System płatności
- 📊 Rate limiting per user
- 🛡️ CORS i CSP headers
- 📝 Logging i audit trail

---

## 💡 Rozwój projektu

**Możliwe rozszerzenia:**
- 🌍 Tłumaczenie opowiadań na inne języki
- 🎙️ Text-to-speech (odczytywanie opowiadań)
- 📖 Eksport do PDF z formatowaniem
- 🎨 Wybór stylu ilustracji przez użytkownika
- 👥 Multi-user support z kontami
- 💾 Baza danych dla opowiadań
- 🔄 Regeneracja fragmentów opowiadania
- ⭐ System ocen i ulubione opowiadania

---

## 🐛 Znane problemy

**Deprecation warning:**
```
use_column_width parameter has been deprecated
```
**Fix:** Zamień `use_column_width=True` na `use_container_width=True` w linii ~1040

---

## 📝 Licencja

MIT License - możesz swobodnie używać i modyfikować projekt.

---

## 👨‍💻 Autor

**Multi-Future**  
🌐 [www.multi-future.pl](https://www.multi-future.pl)  
💼 Data Science | AI Automation | Business Solutions

---

## 🙏 Podziękowania

- OpenAI za GPT-4o i DALL-E 3
- Streamlit za framework
- Langfuse za monitoring tools

---

## 📧 Kontakt

Pytania? Problemy? Chcesz współpracować?

📩 przemek@multi-future.pl 
🔗 [GitHub Issues](https://github.com/multifuture/generator-opowiadan-demo/issues)

---

**⭐ Jeśli projekt Ci się podoba, zostaw gwiazdkę na GitHub!**