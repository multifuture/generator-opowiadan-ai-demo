import os
import sys
import streamlit as st
from openai import OpenAI
import time
import re
from datetime import datetime, timedelta
from langfuse.openai import openai as langfuse_openai
from langfuse import Langfuse
import requests
from io import BytesIO

# Set UTF-8 encoding for Windows to handle Polish characters
if sys.platform == 'win32':
    # This helps with UTF-8 encoding issues on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# Page config
st.set_page_config(
    page_title="Generator Bajek AI dla Dzieci",
    page_icon="🧚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_secret(name, default=None):
    """Pobiera sekrety najpierw ze st.secrets, a jak ich nie ma – z ENV (np. na DO)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)

# Initialize Langfuse
try:
    langfuse_secret = get_secret("LANGFUSE_SECRET_KEY")
    langfuse_public = get_secret("LANGFUSE_PUBLIC_KEY")
    langfuse_host = get_secret("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if langfuse_secret and langfuse_public:
        langfuse = Langfuse(
            secret_key=langfuse_secret,
            public_key=langfuse_public,
            host=langfuse_host,
        )
    else:
        langfuse = None
except Exception as e:
    st.error(f"Błąd inicjalizacji Langfuse: {e}")
    langfuse = None

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'landing'
if 'story_history' not in st.session_state:
    st.session_state.story_history = []
if 'current_story' not in st.session_state:
    st.session_state.current_story = None
if 'generating' not in st.session_state:
    st.session_state.generating = False
if 'child_name' not in st.session_state:
    st.session_state.child_name = None
if 'child_age' not in st.session_state:
    st.session_state.child_age = None
if 'lesson' not in st.session_state:
    st.session_state.lesson = None

# Audio narration session state
if 'generating_audio' not in st.session_state:
    st.session_state.generating_audio = False
if 'story_audio_data' not in st.session_state:
    st.session_state.story_audio_data = None



# Custom CSS
st.markdown("""
<style>
    /* LANDING PAGE STYLES */
    .landing-page {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }
    
    /* FLOATING PARTICLES - SNOWFLAKES */
    @keyframes float1 {
        0% { transform: translateY(100vh) translateX(0); opacity: 0; }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translateY(-100px) translateX(30px); opacity: 0; }
    }
    @keyframes float2 {
        0% { transform: translateY(100vh) translateX(0); opacity: 0; }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translateY(-100px) translateX(-30px); opacity: 0; }
    }
    @keyframes float3 {
        0% { transform: translateY(100vh) translateX(0); opacity: 0; }
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translateY(-100px) translateX(15px); opacity: 0; }
    }
    
    .particle {
        position: fixed;
        width: 6px;
        height: 6px;
        background: rgba(255, 255, 255, 0.9);
        border-radius: 50%;
        box-shadow: 0 0 8px rgba(255, 255, 255, 0.8), 0 0 15px rgba(200, 230, 255, 0.6);
        pointer-events: none;
        z-index: 1;
    }
    
    .particle:nth-child(1) { left: 10%; animation: float1 15s infinite; animation-delay: 0s; width: 4px; height: 4px; }
    .particle:nth-child(2) { left: 20%; animation: float2 18s infinite; animation-delay: 2s; width: 6px; height: 6px; }
    .particle:nth-child(3) { left: 30%; animation: float3 20s infinite; animation-delay: 4s; width: 5px; height: 5px; }
    .particle:nth-child(4) { left: 40%; animation: float1 17s infinite; animation-delay: 1s; width: 7px; height: 7px; }
    .particle:nth-child(5) { left: 50%; animation: float2 16s infinite; animation-delay: 3s; width: 4px; height: 4px; }
    .particle:nth-child(6) { left: 60%; animation: float3 19s infinite; animation-delay: 5s; width: 6px; height: 6px; }
    .particle:nth-child(7) { left: 70%; animation: float1 21s infinite; animation-delay: 2s; width: 5px; height: 5px; }
    .particle:nth-child(8) { left: 80%; animation: float2 14s infinite; animation-delay: 6s; width: 7px; height: 7px; }
    .particle:nth-child(9) { left: 90%; animation: float3 22s infinite; animation-delay: 1s; width: 4px; height: 4px; }
    .particle:nth-child(10) { left: 15%; animation: float1 16s infinite; animation-delay: 4s; width: 6px; height: 6px; }
    .particle:nth-child(11) { left: 25%; animation: float2 19s infinite; animation-delay: 3s; width: 5px; height: 5px; }
    .particle:nth-child(12) { left: 35%; animation: float3 15s infinite; animation-delay: 5s; width: 7px; height: 7px; }
    .particle:nth-child(13) { left: 45%; animation: float1 20s infinite; animation-delay: 2s; width: 4px; height: 4px; }
    .particle:nth-child(14) { left: 55%; animation: float2 17s infinite; animation-delay: 6s; width: 6px; height: 6px; }
    .particle:nth-child(15) { left: 65%; animation: float3 18s infinite; animation-delay: 1s; width: 5px; height: 5px; }
    .particle:nth-child(16) { left: 75%; animation: float1 21s infinite; animation-delay: 4s; width: 7px; height: 7px; }
    .particle:nth-child(17) { left: 85%; animation: float2 16s infinite; animation-delay: 3s; width: 4px; height: 4px; }
    .particle:nth-child(18) { left: 95%; animation: float3 19s infinite; animation-delay: 5s; width: 6px; height: 6px; }
    .particle:nth-child(19) { left: 12%; animation: float1 14s infinite; animation-delay: 2s; width: 5px; height: 5px; }
    .particle:nth-child(20) { left: 88%; animation: float2 22s infinite; animation-delay: 6s; width: 7px; height: 7px; }
    
    /* LANDING CONTENT */
    .landing-content {
        text-align: center;
        color: white;
        z-index: 10;
        position: relative;
        padding: 3rem;
    }
    
    .landing-title {
        font-size: 4rem;
        font-weight: bold;
        margin-bottom: 1rem;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.5), 0 0 40px rgba(200, 230, 255, 0.3);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(255, 255, 255, 0.5), 0 0 40px rgba(200, 230, 255, 0.3); }
        to { text-shadow: 0 0 30px rgba(255, 255, 255, 0.8), 0 0 60px rgba(200, 230, 255, 0.5); }
    }
    
    .landing-subtitle {
        font-size: 1.5rem;
        margin-bottom: 3rem;
        color: rgba(255, 255, 255, 0.9);
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    /* GENERATOR PAGE - SIMPLIFIED STYLES */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Pills styling */
    .pill-container {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 15px 0;
    }
    
    .pill {
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 25px;
        padding: 12px 24px;
        color: white;
        font-size: 16px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        text-align: center;
        min-width: 150px;
    }
    
    .pill:hover {
        background: rgba(255, 255, 255, 0.3);
        border-color: rgba(255, 255, 255, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .pill.selected {
        background: rgba(255, 255, 255, 0.9);
        border-color: rgba(255, 255, 255, 1);
        color: #667eea;
        font-weight: bold;
        box-shadow: 0 6px 20px rgba(255, 255, 255, 0.4);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid #667eea !important;
        border-radius: 15px !important;
        font-size: 16px !important;
        color: #333333 !important;
        padding: 12px !important;
    }

    .stTextArea textarea::placeholder {
        color: #999999 !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
        
    .stTextArea label {
        color: white !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 50px;
        font-weight: bold;
        font-size: 18px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 255, 255, 0.4);
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 20px rgba(57, 255, 20, 0.9);
    }
    
    /* SELECTED BUTTON (primary) */
    .stButton > button[kind="primary"] {
        background: rgba(255, 255, 255, 0.4) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.8) !important;
        font-weight: bold !important;
        box-shadow: 0 0 15px rgba(255, 255, 255, 0.6) !important;
    }

    /* UNSELECTED BUTTON (secondary) */
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    /* Story content */
    .story-content {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        color: #333;
        line-height: 1.8;
        font-size: 16px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    /* Section headers */
    .section-header {
        color: white;
        font-size: 20px;
        font-weight: bold;
        margin: 25px 0 15px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        text-align: center;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    .loading-text {
        animation: pulse 1.5s infinite;
        color: white;
        font-size: 20px;
        text-align: center;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
openai_api_key = get_secret("OPENAI_API_KEY")
if not openai_api_key:
    st.error("Brak klucza OPENAI_API_KEY w secrets lub zmiennych środowiskowych.")
    st.stop()

# Create plain OpenAI client (not wrapped by Langfuse to avoid encoding issues)
openai_client = OpenAI(api_key=openai_api_key)

# Note: We're using manual Langfuse logging instead of automatic wrapping
# to avoid UTF-8/ASCII encoding issues with Polish characters in HTTP headers

def count_words_and_sentences(text):
    words = len(text.split())
    sentences = len(re.findall(r'[.!?]+', text))
    reading_time = max(1, round(words / 200))
    return words, sentences, reading_time

def get_safety_rules():
    """Return enhanced safety rules for children's fairy tales"""
    return """
=== ABSOLUTNE ZAKAZY (ZERO TOLERANCJI) ===
NIGDY nie pisz o:
- Śmierci, umieraniu, zabijaniu (nawet złych postaci)
- Przemocy fizycznej (bicie, kopanie, krzywdzenie)
- Przemocy psychicznej (zastraszanie, upokarzanie, wykluczanie)
- Tematach seksualnych lub romantycznych (całowanie, "miłość" między postaciami)
- Alkoholu, papierosach, narkotykach, lekach
- Strasznych potworach, duchach, zombie, czarownicach
- Krwi, ranach, urazach, bólu
- Wulgaryzmach, brzydkich słowach, przekleństwach
- Smutnych, traumatycznych scenach
- Krzywdzie zwierząt
- Opuszczeniu, samotności dziecka, zgubieniu się
- Kłótniach rodziców lub dorosłych
- Chorobach, szpitalach, lekarzach, dentystach
- Ciemności, nocy jako czegoś strasznego
- Kłamstwach jako głównym motywie

=== BEZPIECZNE KONFLIKTY (jeśli potrzebne) ===
Jeśli historia wymaga drobnego konfliktu, użyj TYLKO:
- Zagubienie przedmiotu → szybkie odnalezienie z pomocą przyjaciół
- Drobna pomyłka → łatwa do naprawienia, wszyscy się śmieją
- Niezrozumienie między przyjaciółmi → wyjaśnione przez rozmowę
- Łagodna przeszkoda → przekraczalna razem, bez stresu
- Drobne niepowodzenie → prowadzące do nauki i sukcesu

=== OBOWIĄZKOWE ELEMENTY ===
KAŻDA bajka MUSI zawierać:
- Wyłącznie pozytywne emocje (radość, ciekawość, ekscytacja, duma)
- Przyjazne, pomocne postacie (wszyscy są mili)
- Bezpieczne, kolorowe, przyjazne środowisko
- Szczęśliwe zakończenie (ZAWSZE - bez wyjątków)
- Język pełen ciepła, zachęty i pozytywnego wzmocnienia
- Poczucie bezpieczeństwa przez całą narrację
- Zero dramatyzmu, napięcia lub niepokoju
- Zero negatywnych konsekwencji dla bohaterów
- Współpraca zamiast konkurencji
- Sukces i radość dla wszystkich postaci

=== STYL NARRACJI ===
- Używaj słów: "cudowny", "wspaniały", "radosny", "wesoły", "kolorowy"
- Opisuj przyjemne detale: kolory, zapachy, przyjemne dźwięki
- Buduj atmosferę bezpieczeństwa, ciepła i komfortu
- Każda postać jest dobra, życzliwa i pomocna
- Magia jest zawsze pomocna, kolorowa, nigdy groźna
- Przyroda jest przyjazna (słońce, kwiaty, motyle)
- Zwierzęta są przyjaciółmi, nigdy zagrożeniem

=== TON UNIWERSALNY ===
Każda bajka ma ton: ciepły, magiczny, z nutką humoru.
- Delikatny humor (śmieszne sytuacje, nie szydzenie)
- Magiczne elementy (czary, zaklęcia - zawsze dobre)
- Ciepło emocjonalne (przytulanie, przyjaźń, miłość rodzicielska)

PAMIĘTAJ: To bajka dla MAŁEGO DZIECKA. 
Priorytet #1: BEZPIECZEŃSTWO EMOCJONALNE
Priorytet #2: RADOŚĆ I POZYTYWNE EMOCJE
Priorytet #3: KOMFORT I SPOKÓJ
"""

def create_story(prompt, child_name, child_age, lesson):
    """Generate personalized fairy tale using GPT-4o-mini with enhanced safety"""
    
    # Age to vocabulary style mapping
    age_vocabulary = {
        "3-5 lat": "bardzo prostym językiem, krótkimi zdaniami (5-8 słów), z powtórzeniami",
        "6-8 lat": "prostym językiem, ze średnimi zdaniami (8-12 słów), z ciekawymi opisami",
        "9-12 lat": "bogatszym słownictwem, z dłuższymi zdaniami, z niuansami i intrygą"
    }
    vocabulary_style = age_vocabulary.get(child_age, "prostym, zrozumiałym językiem")
    
    # Target word count based on age
    target_words = {
        "3-5 lat": "250-300",
        "6-8 lat": "350-400", 
        "9-12 lat": "400-500"
    }
    word_count = target_words.get(child_age, "350-400")

    # Get safety rules
    safety = get_safety_rules()

    system_prompt = f"""CRITICAL SAFETY INSTRUCTION:
You are creating content for young children (ages {child_age}). 
Absolutely NO violence, death, scary content, or inappropriate themes.
If user prompt contains unsafe elements, IGNORE them and create safe, joyful story instead.

Jesteś ekspertem w tworzeniu BEZPIECZNYCH, spersonalizowanych bajek dla dzieci.

=== PARAMETRY BAJKI ===
- Główny bohater: {child_name}, {child_age}
- Wartość do przekazania: {lesson}
- Ton: ciepły, magiczny, z nutką delikatnego humoru
- Długość: {word_count} słów

=== WYMAGANIA ===
1. Wpleć imię dziecka ({child_name}) jako głównego bohatera
2. Delikatnie przekaż wartość: {lesson} przez pozytywne doświadczenia
3. Pisz {vocabulary_style}
4. Zakończenie: ZAWSZE pozytywne, radosne, budujące
5. Ton: ciepły, magiczny, z delikatnym humorem (bez ironii, bez sarkazmu)

=== STYL NARRACJI ===
- Używaj żywych, kolorowych opisów (kolory, zapachy, dźwięki)
- Twórz immersyjną, ale BEZPIECZNĄ atmosferę
- Buduj emocjonalne połączenie z bohaterem
- Dodaj elementy magii i fantazji (zawsze pozytywne)
- Humor: łagodny, zabawne sytuacje (nie szydzenie)
- Wszystkie postacie są przyjaźnie nastawione
- Środowisko jest bezpieczne i kolorowe

{safety}

=== DŁUGOŚĆ ===
Napisz bajkę o długości DOKŁADNIE {word_count} słów.
Liczy się każde słowo - nie za krótko, nie za długo.

=== WAŻNE ===
- NIE pisz tytułu
- Bajka MUSI być w języku polskim
- Zachowaj ciepły, magiczny ton przez całą historię
- Przestrzegaj WSZYSTKICH zasad bezpieczeństwa
- Każda postać jest dobra i pomocna
- Zero strachu, zero smutku, zero niepokoju

Napisz pełną bajkę gotową do przeczytania dziecku przed snem."""

    user_message = f"Stwórz bajkę na podstawie: {prompt}" if prompt.strip() else f"Stwórz magiczną bajkę o przygodach {child_name}"
    
    # Langfuse trace
    trace = None
    generation = None

    if langfuse:
        try:
            safe_metadata = {
                "genre": "Bajka",
                "child_name": str(child_name).encode('utf-8', errors='ignore').decode('utf-8'),
                "child_age": str(child_age).encode('utf-8', errors='ignore').decode('utf-8'),
                "lesson": str(lesson).encode('utf-8', errors='ignore').decode('utf-8'),
                "prompt_length": len(prompt),
                "session_id": str(id(st.session_state)),
                "model": "gpt-4o-mini"
            }
            trace = langfuse.trace(
                name="story_generation",
                user_id="demo_user",
                metadata=safe_metadata
            )

            generation = trace.generation(
                name="gpt4o_mini_story",
                model="gpt-4o-mini",
                model_parameters={
                    "temperature": 0.8,
                    "max_tokens": 1500
                },
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
        except Exception as e:
            st.warning(f"Langfuse logging błąd: {e}")
    
    # Call OpenAI API with GPT-4o-mini
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.8,
        max_tokens=1500
    )
    
    # Log output to Langfuse
    if langfuse and generation:
        try:
            generation.end(
                output=response.choices[0].message.content,
                usage={
                    "input": response.usage.prompt_tokens,
                    "output": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                }
            )
        except Exception as e:
            st.warning(f"Langfuse end logging błąd: {e}")

    return {
        'content': response.choices[0].message.content,
        'genre': '🧚 Bajka',
        'child_name': child_name,
        'child_age': child_age,
        'lesson': lesson,
        'prompt': prompt if prompt.strip() else "Magiczna przygoda",
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def generate_audio_narration(story_content, child_name):
    """Generate audio narration using OpenAI TTS with nova voice"""
    try:
        # Langfuse trace dla audio
        trace = None
        generation = None
        
        if langfuse:
            try:
                safe_metadata = {
                    "child_name": str(child_name).encode('utf-8', errors='ignore').decode('utf-8'),
                    "model": "tts-1",
                    "voice": "nova",
                    "text_length": len(story_content)
                }
                trace = langfuse.trace(
                    name="audio_generation",
                    metadata=safe_metadata
                )
                
                generation = trace.generation(
                    name="openai_tts",
                    model="tts-1",
                    model_parameters={
                        "voice": "nova",
                        "response_format": "mp3"
                    },
                    input=story_content[:100] + "..."  # First 100 chars for logging
                )
            except:
                pass
        
        # Generate audio using OpenAI TTS
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=story_content
        )
        
        # Convert to BytesIO for download button
        audio_buffer = BytesIO(response.content)
        
        # Log to Langfuse
        if langfuse and generation:
            try:
                generation.end(
                    output="audio_generated",
                    metadata={
                        "audio_size_bytes": len(response.content)
                    }
                )
            except:
                pass
        
        return audio_buffer
        
    except Exception as e:
        st.error(f"Błąd generowania audio: {e}")
        return None

# ==================== LANDING PAGE ====================
if st.session_state.page == 'landing':
    # Floating particles (snowflakes)
    particles_html = "".join([f'<div class="particle"></div>' for _ in range(20)])
    st.markdown(particles_html, unsafe_allow_html=True)
    
    # Landing content
    st.markdown("""
        <div class="landing-content">
            <h1 class="landing-title">🧚 Generator Bajek AI dla Dzieci</h1>
            <p class="landing-subtitle">
                Spersonalizowana bajka + audio w 2 minuty!<br>
                Prosto, szybko, magicznie ✨
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Center the button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 WEJDŹ", key="enter_app", use_container_width=True):
            st.session_state.page = 'generator'
            st.rerun()

# ==================== GENERATOR PAGE ====================
else:
    # Floating particles (snowflakes on generator too)
    particles_html = "".join([f'<div class="particle"></div>' for _ in range(15)])
    st.markdown(particles_html, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <h1 style='text-align: center; color: white; margin-top: 0; margin-bottom: 2rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            🧚 Stwórz Bajkę dla Twojego Dziecka
        </h1>
    """, unsafe_allow_html=True)

    # Info box at the top
    if not st.session_state.current_story:
        st.info("✨ Wypełnij formularz i wygeneruj spersonalizowaną bajkę + audio!")
   
    # Name input
    child_name_input = st.text_input(
            "👶 Imię dziecka *",
            value=st.session_state.child_name or "",
            placeholder="np. Zosia, Janek, Mikołaj...",
            key="child_name_input",
            help="Główny bohater bajki"
        )

        # Age selection
    child_age_input = st.select_slider(
            "🎂 Wiek dziecka *",
            options=["3-5 lat", "6-8 lat", "9-12 lat"],
            value=st.session_state.child_age or "6-8 lat",
            key="child_age_input",
            help="Dostosujemy język i styl do wieku"
        )

        # Lesson/value
    lesson_options = [
            "Odwaga",
            "Przyjaźń", 
            "Uczciwość",
            "Dobroć",
            "Wytrwałość",
            "Dzielenie się",
            "Szacunek",
            "Cierpliwość",
            "Kreatywność",
            "Pomoc innym"
        ]
    lesson_input = st.selectbox(
            "💡 Co chcesz przekazać dziecku? *",
            options=lesson_options,
            index=lesson_options.index(st.session_state.lesson) if st.session_state.lesson in lesson_options else 0,
            key="lesson_input",
            help="Wartość wpleciona w fabułę"
        )

    st.markdown("<hr style='margin: 1.5rem 0; border: 1px solid rgba(102,126,234,0.2);'>", unsafe_allow_html=True)

        # Story idea (optional)
    user_input = st.text_area(
            "💭 Pomysł na bajkę (opcjonalnie)",
            max_chars=500,
            height=120,
            placeholder="np. Przygoda w magicznym lesie, podróż do krainy dinozaurów, spotkanie z wróżkami...\n\nMożesz zostawić puste - stworzymy magiczną historię!",
            help="Zostaw puste dla losowej, magicznej przygody",
            label_visibility="visible",
            key="story_prompt_input"
        )

        # Character counter
    char_count = len(user_input)
    st.markdown(f"""
            <div style='text-align: right; color: #666; font-size: 12px; margin-top: -10px;'>
                {char_count}/500 znaków
            </div>
        """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

        # GENERATE BUTTON
    col_gen1, col_gen2, col_gen3 = st.columns([1, 2, 1])
    with col_gen2:
            can_generate = bool(child_name_input.strip() and child_age_input and lesson_input)
            
            if st.button("✨ Stwórz Bajkę + Audio", disabled=not can_generate, use_container_width=True, type="primary", key="generate_story"):
                st.session_state.child_name = child_name_input.strip()
                st.session_state.child_age = child_age_input
                st.session_state.lesson = lesson_input
                st.session_state.user_prompt = user_input.strip() if user_input.strip() else ""
                st.session_state.generating = True
                st.session_state.current_story = None
                st.session_state.story_audio_data = None
                st.rerun()
        
    if not can_generate:
            st.markdown("""
                <div style='text-align: center; color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 1rem;'>
                    ⚠️ Wypełnij wymagane pola (*)
                </div>
            """, unsafe_allow_html=True)
            st.session_state.current_story = None
            st.session_state.story_image_url = None
            st.session_state.story_image_data = None
            st.session_state.user_prompt = user_input.strip()
            st.rerun()
    
    # Separator
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Generate story
    if st.session_state.generating:
        with st.spinner(""):
            st.markdown(f"""
                <div class='loading-text'>
                    🪄 Tworzę spersonalizowaną bajkę dla {st.session_state.child_name}...<br>
                    💡 Wartość: <b>{st.session_state.lesson}</b><br>
                    🎯 Model: GPT-4o-mini
                </div>
            """, unsafe_allow_html=True)

            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress.progress(i + 1)

            story = create_story(
                st.session_state.user_prompt,
                st.session_state.child_name,
                st.session_state.child_age,
                st.session_state.lesson
            )
            st.session_state.current_story = story
            st.session_state.story_history.append(story)
            st.session_state.generating = False
            st.rerun()
    
    # Generate audio narration for story
    if st.session_state.generating_audio and st.session_state.current_story:
        with st.spinner(""):
            st.markdown(f"""
                <div class='loading-text'>
                    🎧 Tworzę narrację audio dla {st.session_state.current_story['child_name']}...<br>
                    Głos: Nova (OpenAI TTS)<br>
                    To może potrwać 10-20 sekund<br>
                    💰 Koszt: ~$0.015
                </div>
            """, unsafe_allow_html=True)
            
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.05)  # Faster progress for OpenAI TTS
                progress.progress(i + 1)
            
            audio_buffer = generate_audio_narration(
                st.session_state.current_story['content'],
                st.session_state.current_story['child_name']
            )
            
            if audio_buffer:
                st.session_state.story_audio_data = audio_buffer
                st.success("✅ Narracja audio wygenerowana!")
            
            st.session_state.generating_audio = False
            time.sleep(1)
            st.rerun()
    
    # Display story
    if st.session_state.current_story:
        story = st.session_state.current_story

        st.markdown("<h3 style='color: white; text-align: center; margin-top: 2rem;'>📖 Twoja Bajka</h3>", unsafe_allow_html=True)

        # Story metadata - simplified
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; margin-bottom: 15px;'>
                <span style='color: white; font-size: 16px;'>
                    👧 <b>Dla:</b> {story['child_name']} ({story['child_age']}) | 
                    💡 <b>Wartość:</b> {story['lesson']}
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        # Stats w jednej linii
        words, sentences, reading_time = count_words_and_sentences(story['content'])
        st.markdown(f"""
            <div style='display: flex; justify-content: space-around; margin: 1rem 0; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px;'>
                <div style='text-align: center; color: white;'>
                    <span style='font-size: 14px; opacity: 0.8;'>📊 Słowa:</span>
                    <span style='font-size: 20px; font-weight: bold; margin-left: 8px;'>{words}</span>
                </div>
                <div style='text-align: center; color: white;'>
                    <span style='font-size: 14px; opacity: 0.8;'>📝 Zdania:</span>
                    <span style='font-size: 20px; font-weight: bold; margin-left: 8px;'>{sentences}</span>
                </div>
                <div style='text-align: center; color: white;'>
                    <span style='font-size: 14px; opacity: 0.8;'>⏱️ Czas czytania:</span>
                    <span style='font-size: 20px; font-weight: bold; margin-left: 8px;'>{reading_time} min</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Display audio player if exists
        if st.session_state.story_audio_data:
            st.markdown("<h4 style='color: white; text-align: center; margin-top: 2rem;'>🎧 Posłuchaj Bajki</h4>", unsafe_allow_html=True)
            col_aud1, col_aud2, col_aud3 = st.columns([0.5, 2, 0.5])
            with col_aud2:
                st.audio(st.session_state.story_audio_data, format='audio/mp3')
        
        # Story content
        st.markdown(f"""
            <div class='story-content'>
                {story['content']}
            </div>
        """, unsafe_allow_html=True)
        
        # Action buttons - 3 columns now
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            story_data = f"""BAJKA DLA {story['child_name'].upper()}
Wiek: {story['child_age']}
Wartość: {story['lesson']}
Pomysł: {story['prompt']}

---

{story['content']}
"""
            st.download_button(
                label="💾 Pobierz tekst",
                data=story_data.encode('utf-8'),
                file_name=f"bajka_{story['child_name'].lower()}_{int(time.time())}.txt",
                mime="text/plain; charset=utf-8",
                use_container_width=True
            )
        
        with col_b2:
            if st.session_state.story_audio_data:
                st.download_button(
                    label="🎧 Pobierz audio",
                    data=st.session_state.story_audio_data.getvalue(),
                    file_name=f"bajka_{story['child_name'].lower()}_{int(time.time())}.mp3",
                    mime="audio/mpeg",
                    use_container_width=True
                )
            else:
                if st.button("🎧 Czytaj bajkę", use_container_width=True, key="generate_audio"):
                    st.session_state.generating_audio = True
                    st.rerun()
        
        with col_b3:
            if st.button("🔄 Nowa bajka", use_container_width=True):
                st.session_state.generating = True
                st.session_state.story_audio_data = None
                st.rerun()
    
    # Close single column container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== MULTI-FUTURE BUTTON ==========
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center;'>
            <a href='https://multi-future.pl/blog' target='_blank' style='
                display: inline-block;
                padding: 12px 32px;
                background: linear-gradient(135deg, #39ff14 0%, #32cd32 100%);
                color: #1a1a1a;
                text-decoration: none;
                border-radius: 30px;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 4px 15px rgba(57, 255, 20, 0.5);
                transition: all 0.3s ease;
            '>
                BLOG
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    # =========================================
    
    # Sidebar with history
    with st.sidebar:
        st.markdown("### 📚 Historia Bajek")

        if st.session_state.story_history:
            st.markdown(f"*Utworzono {len(st.session_state.story_history)} bajek*")

            for i, story in enumerate(reversed(st.session_state.story_history[-5:]), 1):
                with st.expander(f"📖 Dla: {story['child_name']}"):
                    st.write(f"**Wiek:** {story['child_age']}")
                    st.write(f"**Wartość:** {story['lesson']}")
                    st.write(f"**Fragment:** {story['content'][:100]}...")
                    if st.button(f"Wczytaj", key=f"load_{i}"):
                        st.session_state.current_story = story
                        st.rerun()

            if st.button("🗑️ Wyczyść historię", use_container_width=True):
                st.session_state.story_history = []
                st.session_state.current_story = None
                st.session_state.story_image_url = None
                st.session_state.story_image_data = None
                st.session_state.story_audio_data = None
                st.rerun()
        else:
            st.info("Brak historii")
        
        st.markdown("---")
        st.markdown("""
            <div style='text-align: center; color: rgba(255,255,255,0.7); font-size: 12px;'>
                Made with ❤️ by Multi-Future<br>
                Powered by GPT-4o-mini & OpenAI TTS
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("← Powrót do strony głównej", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()