# ✨ Generator Opowiadań AI

Aplikacja Streamlit, która generuje krótkie opowiadania na podstawie wybranego gatunku, tonu, długości oraz opcjonalnej inspiracji użytkownika. Projekt pokazuje praktyczne połączenie interfejsu Streamlit z modelem GPT oraz dodanie warstwy logiki, bezpieczeństwa treści i analizy wygenerowanego tekstu.

---

## 🎯 Funkcje

- 3 gatunki do wyboru: **Bajka**, **Romans**, **Kryminał**
- Dynamiczny dobór tonów zależnie od gatunku
- Filtry bezpieczeństwa treści (bez wulgaryzmów, przemocy, treści 18+)
- Wybór długości opowiadania
- Licznik słów, zdań i szacowany czas czytania
- Historia poprzednich opowiadań w sidebarze
- Pobieranie wygenerowanego tekstu do pliku `.txt`
- Estetyczne UI i animacja gwiazdek na ekranie startowym

---

## 🚀 Demo

🔗 **(tu dodasz link po wdrożeniu na Streamlit Cloud)**

---

## 🛠 Tech stack

- Python 3.11+
- Streamlit
- OpenAI API (gpt-4o)
- CSS / animacje tła
- `.streamlit/secrets.toml` do przechowywania kluczy

---

## 💻 Jak uruchomić lokalnie

### 1. Wymagania

Zanim uruchomisz aplikację, upewnij się, że masz:

- **Python 3.11+**  
  Projekt był tworzony i testowany na Pythonie 3.11. Starsze wersje mogą działać, ale nie są wspierane.  
- **pip**  
  Standardowy menedżer pakietów Pythona, używany do instalowania zależności z pliku `requirements.txt`.  
- **Konto w OpenAI + klucz API**  
  Potrzebujesz aktywnego klucza API, aby aplikacja mogła komunikować się z modelem GPT i generować treści.  
- *(Opcjonalnie, ale zalecane)* **Git** i edytor kodu (np. VS Code), jeśli chcesz rozwijać projekt dalej.

Aplikacja była testowana na Windows i Linux; powinna działać również na macOS przy spełnieniu powyższych warunków.

---

### 2. Sklonuj repozytorium

```bash
git clone https://github.com/multifuture/generator-opowiadan-ai.git
cd generator-opowiadan-ai