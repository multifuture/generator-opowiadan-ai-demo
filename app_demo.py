import streamlit as st
from openai import OpenAI
import time
import re
from datetime import datetime, timedelta
from langfuse.openai import openai as langfuse_openai
from langfuse import Langfuse
import requests
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Generator Opowiadań AI",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Langfuse
try:
    langfuse = Langfuse(
        secret_key=st.secrets["LANGFUSE_SECRET_KEY"],
        public_key=st.secrets["LANGFUSE_PUBLIC_KEY"],
        host=st.secrets.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
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
if 'selected_genre' not in st.session_state:
    st.session_state.selected_genre = None
if 'selected_tone' not in st.session_state:
    st.session_state.selected_tone = None
if 'selected_length' not in st.session_state:
    st.session_state.selected_length = None

# Image generation session state
if 'generating_image' not in st.session_state:
    st.session_state.generating_image = False
if 'story_image_url' not in st.session_state:
    st.session_state.story_image_url = None
if 'story_image_data' not in st.session_state:
    st.session_state.story_image_data = None

# Authentication session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'auth_expiry' not in st.session_state:
    st.session_state.auth_expiry = None

# Check if session expired (24h)
if st.session_state.authenticated and st.session_state.auth_expiry:
    if datetime.now() > st.session_state.auth_expiry:
        st.session_state.authenticated = False
        st.session_state.auth_expiry = None
        st.session_state.page = 'landing'
        st.info("⏰ Twoja sesja wygasła. Wpisz kod dostępu ponownie.")

# Authentication wall
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .auth-container {
            max-width: 500px;
            margin: 5rem auto;
            padding: 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .auth-title {
            text-align: center;
            color: white;
            font-size: 2rem;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .auth-subtitle {
            text-align: center;
            color: rgba(255,255,255,0.9);
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)
    st.markdown('<h1 class="auth-title">🔒 Generator Opowiadań AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="auth-subtitle">Wpisz kod dostępu aby korzystać z demo</p>', unsafe_allow_html=True)
    
    password = st.text_input("Kod dostępu:", type="password", key="access_code")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Uzyskaj dostęp", use_container_width=True, type="primary"):
            if password == st.secrets.get("ACCESS_PASSWORD", "demo2024"):
                st.session_state.authenticated = True
                st.session_state.auth_expiry = datetime.now() + timedelta(hours=24)
                st.success("✅ Dostęp przyznany na 24 godziny!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Nieprawidłowy kod dostępu")
    
    st.info("💡 Demo dostępne przez 24 godziny od momentu logowania")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Show remaining time in sidebar (optional)
if st.session_state.authenticated and st.session_state.auth_expiry:
    time_left = st.session_state.auth_expiry - datetime.now()
    hours_left = int(time_left.total_seconds() / 3600)
    minutes_left = int((time_left.total_seconds() % 3600) / 60)
    
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
            <div style='text-align: center; color: rgba(255,255,255,0.7); font-size: 12px;'>
                ⏰ Sesja aktywna jeszcze: {hours_left}h {minutes_left}min
            </div>
        """, unsafe_allow_html=True)

# Genre-Tone mapping
GENRE_TONES = {
    "🧚 Bajka": {
        "😄 Zabawna": "Zabawna",
        "💫 Magiczna": "Magiczna",
        "🎓 Mądra": "Mądra"
    },
    "❤️ Romans": {
        "💕 Romantyczna": "Romantyczna",
        "🔥 Namiętna": "Namiętna",
        "💔 Poruszająca": "Poruszająca"
    },
    "🔍 Kryminał": {
        "🕵️ Detektywistyczna": "Detektywistyczna",
        "😰 Pełna napięcia": "Pełna napięcia",
        "🧠 Psychologiczna": "Psychologiczna"
    }
}

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
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def count_words_and_sentences(text):
    words = len(text.split())
    sentences = len(re.findall(r'[.!?]+', text))
    reading_time = max(1, round(words / 200))
    return words, sentences, reading_time

def get_safety_rules(genre, tone):
    """Return safety rules based on genre and tone combination"""
    
    base_genre = genre.split(" ", 1)[1] if " " in genre else genre
    
    safety_rules = {
        "Bajka": """
            ABSOLUTNIE ZAKAZANE:
            - Przemoc fizyczna lub psychiczna
            - Śmierć postaci
            - Alkohol, narkotyki, papierosy
            - Treści seksualne w jakiejkolwiek formie
            - Wulgaryzmy i brzydkie słowa
            - Straszenie dzieci
            - Sceny smutne lub przerażające
            
            WYMAGANE:
            - Pozytywne, szczęśliwe zakończenie
            - Przyjazne, sympatyczne postacie
            - Język prosty, zrozumiały dla dzieci 5-10 lat
            - Wartości: dobroć, przyjaźń, uczciwość
            - Magia i fantazja w pozytywnym kontekście
        """,
        "Romans": """
            ABSOLUTNIE ZAKAZANE:
            - Treści seksualne explicit (opisy aktów)
            - Zdrada jako pozytywny element
            - Przemoc w związku
            - Toksyczne relacje jako wzorzec
            - Wulgaryzmy
            
            DOPUSZCZALNE:
            - Romantyczne uczucia i emocje
            - Delikatne opisy fizycznej bliskości (objęcia, pocałunki)
            - Napięcie emocjonalne między bohaterami
            - Happy ending lub bittersweet zakończenie
            - Dojrzałe relacje oparte na szacunku
        """,
        "Kryminał": """
            ABSOLUTNIE ZAKAZANE:
            - Brutalna przemoc (szczegółowe opisy ran, tortur, krwi)
            - Gloryfikacja przemocy lub przestępstw
            - Szczegółowe instrukcje popełnienia przestępstwa
            - Przemoc wobec dzieci
            - Drastyczne sceny
            
            DOPUSZCZALNE:
            - Tajemnica do rozwiązania
            - Napięcie psychologiczne i suspens
            - Inteligentne śledztwo
            - Sprawiedliwość i kara dla winnych
            - Detektywistyczna logika
            - Zwroty akcji i zagadki
        """
    }
    
    return safety_rules.get(base_genre, "")

def create_story(story_prompt, genre, length, tone):
    length_map = {
        "📄 Krótka": "100-200",
        "📑 Średnia": "200-400",
        "📚 Długa": "400-600"
    }
    
    # Get base genre name
    base_genre = genre.split(" ", 1)[1] if " " in genre else genre
    base_tone = tone.split(" ", 1)[1] if " " in tone else tone
    base_length = length.split(" ")[1] if " " in length else length
    
    # Get safety rules
    safety = get_safety_rules(genre, tone)
    
    # Genre-specific instructions
    genre_instructions = {
        "Bajka": f"""
            Ton: {base_tone}
            
            MUSISZ zawrzeć:
            - Prostą, zrozumiałą fabułę
            - Elementy magiczne lub fantastyczne
            - Wyraźne postacie dobre
            - Szczęśliwe zakończenie z morałem
            - Język dla dzieci 5-10 lat
            
            Dostosuj styl do tonu "{base_tone}":
            {"- Używaj humoru, żartów, komicznych sytuacji" if "Zabawna" in tone else ""}
            {"- Dodaj wartości moralne, mądrość życiową, pouczenie" if "Mądra" in tone else ""}
            {"- Stwórz magiczny świat pełen czarów i cudów" if "Magiczna" in tone else ""}
        """,
        "Romans": f"""
            Ton: {base_tone}
            
            MUSISZ zawrzeć:
            - Relację romantyczną między bohaterami
            - Rozwój uczuć i emocji
            - Chemię między postaciami
            - Romantyczne gesty lub wyznania
            - Zakończenie dające nadzieję
            
            Dostosuj styl do tonu "{base_tone}":
            {"- Delikatne uczucia, czułe gesty, miłe słowa" if "Romantyczna" in tone else ""}
            {"- Intensywne emocje, namiętność, silne uczucia" if "Namiętna" in tone else ""}
            {"- Głębokie emocje, może smutek, refleksja" if "Poruszająca" in tone else ""}
        """,
        "Kryminał": f"""
            Ton: {base_tone}
            
            MUSISZ zawrzeć:
            - Przestępstwo lub tajemnicę do rozwiązania
            - Detektywa lub głównego bohatera-śledczego
            - Poszlaki i tropy
            - Logiczne rozwiązanie zagadki
            - Sprawiedliwość na końcu
            
            Dostosuj styl do tonu "{base_tone}":
            {"- Klasyczne śledztwo, dedukcja, logika jak Sherlock Holmes" if "Detektywistyczna" in tone else ""}
            {"- Buduj napięcie, suspens, trzymaj w niepewności" if "Pełna napięcia" in tone else ""}
            {"- Gra psychologiczna, manipulacja, tajemnice umysłu" if "Psychologiczna" in tone else ""}
        """
    }
    
    system_prompt = f"""
    Jesteś mistrzem opowiadań w gatunku {base_genre}.
    
    === ZASADY BEZPIECZEŃSTWA ===
    {safety}
    
    === GATUNEK I TON ===
    {genre_instructions.get(base_genre, "")}
    
    === DŁUGOŚĆ ===
    Napisz DOKŁADNIE {length_map[length]} słów.
    
    === STRUKTURA ===
    1. WSTĘP: Przedstaw bohaterów i sytuację
    2. ROZWINIĘCIE: Rozwiń akcję zgodnie z gatunkiem i tonem
    3. ZAKOŃCZENIE: Zakończ zgodnie z konwencją gatunku
    
    === WAŻNE ===
    - NIE pisz tytułu
    - Opowiadanie MUSI być w języku polskim
    - Zachowaj ton "{base_tone}" przez całe opowiadanie
    - Przestrzegaj WSZYSTKICH zasad bezpieczeństwa
    """
    
    user_message = f"Napisz opowiadanie na podstawie: {story_prompt}"
    
    # Langfuse trace
    trace = None
    generation = None
    
    if langfuse:
        try:
            trace = langfuse.trace(
                name="story_generation",
                user_id=st.session_state.get("user_id", "demo_user"),
                metadata={
                    "genre": base_genre,
                    "tone": base_tone,
                    "length": base_length,
                    "prompt_length": len(story_prompt),
                    "session_id": id(st.session_state)
                }
            )
            
            generation = trace.generation(
                name="gpt4o_story",
                model="gpt-4o",
                model_parameters={
                    "temperature": 0.8,
                    "max_tokens": 1000
                },
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            )
        except Exception as e:
            st.warning(f"Langfuse logging błąd: {e}")
    
    # Call OpenAI API
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0.8
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
        "content": response.choices[0].message.content,
        "prompt": story_prompt,
        "genre": base_genre,
        "tone": base_tone,
        "length": base_length
    }

def generate_story_image(story_content, genre, tone):
    """Generate illustration for the story using DALL-E 3"""
    
    # Skróć opowiadanie do pierwszych 300 znaków dla promptu
    story_snippet = story_content[:300].replace('\n', ' ') + "..."
    
    # Style map dla różnych gatunków
    style_map = {
        "Bajka": "colorful children's book illustration, whimsical and magical, soft watercolor style, warm and friendly",
        "Romans": "romantic and dreamy illustration, elegant and emotional, soft pastel colors, intimate atmosphere",
        "Kryminał": "noir detective style illustration, mysterious atmosphere, dramatic lighting, suspenseful mood"
    }
    
    style = style_map.get(genre, "professional book illustration, artistic and engaging")
    
    # Stwórz prompt dla DALL-E
    image_prompt = f"""
Create a beautiful, professional book illustration for a {genre} story with {tone} emotional tone.

Story context: {story_snippet}

Art style: {style}
Quality: High-quality, professional book cover illustration
Requirements: 
- NO text or words in the image
- Appropriate for the story genre and tone
- Visually engaging and atmospheric
- Polish cultural context if applicable
"""
    
    # Langfuse trace dla obrazu
    trace = None
    generation = None
    
    if langfuse:
        try:
            trace = langfuse.trace(
                name="image_generation",
                metadata={
                    "genre": genre,
                    "tone": tone,
                    "model": "dall-e-3"
                }
            )
            
            generation = trace.generation(
                name="dalle3_image",
                model="dall-e-3",
                model_parameters={
                    "size": "1024x1024",
                    "quality": "standard"
                },
                input=image_prompt
            )
        except:
            pass
    
    # Wywołaj DALL-E 3
    try:
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=image_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        
        # Pobierz obrazek i zapisz jako bytes (żeby można było pobrać)
        img_response = requests.get(image_url)
        image_bytes = BytesIO(img_response.content)
        
        # Log do Langfuse
        if langfuse and generation:
            try:
                generation.end(
                    output=image_url,
                    metadata={
                        "revised_prompt": response.data[0].revised_prompt if hasattr(response.data[0], 'revised_prompt') else None
                    }
                )
            except:
                pass
        
        return image_url, image_bytes
        
    except Exception as e:
        st.error(f"Błąd generowania obrazu: {e}")
        return None, None

# ==================== LANDING PAGE ====================
if st.session_state.page == 'landing':
    # Floating particles (snowflakes)
    particles_html = "".join([f'<div class="particle"></div>' for _ in range(20)])
    st.markdown(particles_html, unsafe_allow_html=True)
    
    # Landing content
    st.markdown("""
        <div class="landing-content">
            <h1 class="landing-title">✨ Generator Magicznych Opowieści ✨</h1>
            <p class="landing-subtitle">
                Stwórz wyjątkową historię za pomocą magii sztucznej inteligencji<br>
                Bajki dla dzieci • Romanse • Kryminały
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
            ✨ Generator Magicznych Opowieści
        </h1>
    """, unsafe_allow_html=True)
    
    # Info box at the top
    if not st.session_state.current_story:
        st.info("👉 Wypełnij poniższy formularz i kliknij 'Stwórz Magiczną Historię'")
    
    # Main content - Single column layout
    st.markdown("<div style='max-width: 900px; margin: 0 auto;'>", unsafe_allow_html=True)
    
    # GENRE SELECTION
    st.markdown("<div class='section-header'>📚 Wybierz gatunek:</div>", unsafe_allow_html=True)
    genre_cols = st.columns(3)
    genres = ["🧚 Bajka", "❤️ Romans", "🔍 Kryminał"]
    
    for idx, genre in enumerate(genres):
        with genre_cols[idx]:
            button_type = "primary" if st.session_state.selected_genre == genre else "secondary"
            if st.button(genre, key=f"genre_{genre}", use_container_width=True, type=button_type):
                st.session_state.selected_genre = genre
                st.session_state.selected_tone = None  # Reset tone when genre changes
                st.rerun()
    
    # TONE SELECTION (dynamic based on genre)
    if st.session_state.selected_genre:
        st.markdown("<div class='section-header'>🎭 Wybierz ton narracji:</div>", unsafe_allow_html=True)
        
        available_tones = list(GENRE_TONES[st.session_state.selected_genre].keys())
        tone_cols = st.columns(3)
        
        for idx, tone in enumerate(available_tones):
            with tone_cols[idx]:
                button_type = "primary" if st.session_state.selected_tone == tone else "secondary"
                if st.button(tone, key=f"tone_{tone}", use_container_width=True, type=button_type):
                    st.session_state.selected_tone = tone
                    st.rerun()
    
    # LENGTH SELECTION
    st.markdown("<div class='section-header'>📏 Wybierz długość:</div>", unsafe_allow_html=True)
    length_options = {
        "📄 Krótka": "⏱️ ~1 min",
        "📑 Średnia": "⏱️ ~2 min",
        "📚 Długa": "⏱️ ~3 min"
    }
    
    length_cols = st.columns(3)
    for idx, (length, time_label) in enumerate(length_options.items()):
        with length_cols[idx]:
            button_label = f"{length}\n{time_label}"
            button_type = "primary" if st.session_state.selected_length == length else "secondary"
            if st.button(button_label, key=f"length_{length}", use_container_width=True, type=button_type):
                st.session_state.selected_length = length
                st.rerun()
    
    # TEXT INPUT
    st.markdown("<div class='section-header'>💭 Wprowadź inspirację:</div>", unsafe_allow_html=True)
    user_input = st.text_area(
        "",
        max_chars=1000,
        height=150,
        placeholder="Wpisz pomysł, postać lub sytuację, która zainspiruje Twoją historię...",
        help="To będzie punkt wyjścia dla Twojej historii",
        label_visibility="collapsed"
    )
    
    # Character counter
    char_count = len(user_input)
    st.markdown(f"""
        <div style='text-align: right; color: rgba(255,255,255,0.8); font-size: 14px; margin-top: -10px; margin-bottom: 1rem;'>
            {char_count}/1000 znaków
        </div>
    """, unsafe_allow_html=True)
    
    # GENERATE BUTTON
    can_generate = all([
        st.session_state.selected_genre,
        st.session_state.selected_tone,
        st.session_state.selected_length,
        user_input.strip()
    ])
    
    if st.button("✨ Stwórz Magiczną Historię", disabled=not can_generate, use_container_width=True, type="primary"):
        st.session_state.generating = True
        st.session_state.current_story = None
        st.session_state.story_image_url = None
        st.session_state.story_image_data = None
        st.rerun()
    
    # Separator
    st.markdown("<hr style='border: 1px solid rgba(255,255,255,0.2); margin: 2rem 0;'>", unsafe_allow_html=True)
    
    # Generate story
    if st.session_state.generating:
        with st.spinner(""):
            st.markdown(f"""
                <div class='loading-text'>
                    🪄 Czaruję opowiadanie...<br>
                    📚 Gatunek: <b>{st.session_state.selected_genre}</b><br>
                    🎭 Ton: <b>{st.session_state.selected_tone}</b>
                </div>
            """, unsafe_allow_html=True)
            
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.02)
                progress.progress(i + 1)
            
            story = create_story(
                user_input,
                st.session_state.selected_genre,
                st.session_state.selected_length,
                st.session_state.selected_tone
            )
            st.session_state.current_story = story
            st.session_state.story_history.append(story)
            st.session_state.generating = False
            st.rerun()
    
    # Generate image for story
    if st.session_state.generating_image and st.session_state.current_story:
        with st.spinner(""):
            st.markdown("""
                <div class='loading-text'>
                    🎨 Tworzę ilustrację do opowiadania...<br>
                    To może potrwać do 60 sekund<br>
                    💰 Koszt: ~$0.04
                </div>
            """, unsafe_allow_html=True)
            
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.15)
                progress.progress(i + 1)
            
            image_url, image_bytes = generate_story_image(
                st.session_state.current_story['content'],
                st.session_state.current_story['genre'],
                st.session_state.current_story['tone']
            )
            
            if image_url:
                st.session_state.story_image_url = image_url
                st.session_state.story_image_data = image_bytes
                st.success("✅ Ilustracja wygenerowana!")
            
            st.session_state.generating_image = False
            time.sleep(1)
            st.rerun()
    
    # Display story
    if st.session_state.current_story:
        story = st.session_state.current_story
        
        st.markdown("<h3 style='color: white; text-align: center; margin-top: 2rem;'>📖 Twoja Opowieść</h3>", unsafe_allow_html=True)
        
        # Story metadata
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.1); padding: 10px; border-radius: 10px; margin-bottom: 10px;'>
                <span style='color: white;'>
                    📚 <b>Gatunek:</b> {story['genre']} | 
                    🎭 <b>Ton:</b> {story['tone']} | 
                    📏 <b>Długość:</b> {story['length']}
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
                    <span style='font-size: 14px; opacity: 0.8;'>⏱️ Czas:</span>
                    <span style='font-size: 20px; font-weight: bold; margin-left: 8px;'>{reading_time} min</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Display generated image if exists
        if st.session_state.story_image_url:
            st.markdown("<h4 style='color: white; text-align: center; margin-top: 2rem;'>🎨 Ilustracja</h4>", unsafe_allow_html=True)
            col_img1, col_img2, col_img3 = st.columns([0.5, 2, 0.5])
            with col_img2:
                st.image(st.session_state.story_image_url, use_container_width=True, caption="...")
        
        # Story content
        st.markdown(f"""
            <div class='story-content'>
                {story['content']}
            </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col_b1, col_b2, col_b3 = st.columns(3)
        
        with col_b1:
            story_data = f"""OPOWIADANIE
Gatunek: {story['genre']}
Ton: {story['tone']}
Inspiracja: {story['prompt']}

---

{story['content']}
"""
            st.download_button(
                label="💾 Pobierz tekst",
                data=story_data,
                file_name=f"opowiadanie_{story['genre'].lower()}_{int(time.time())}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_b2:
            if st.session_state.story_image_data:
                st.download_button(
                    label="🖼️ Pobierz obraz",
                    data=st.session_state.story_image_data.getvalue(),
                    file_name=f"ilustracja_{story['genre'].lower()}_{int(time.time())}.png",
                    mime="image/png",
                    use_container_width=True
                )
            else:
                if st.button("🎨 Generuj grafikę", use_container_width=True, key="generate_image"):
                    st.session_state.generating_image = True
                    st.rerun()
        
        with col_b3:
            if st.button("🔄 Nowa wersja", use_container_width=True):
                st.session_state.generating = True
                st.session_state.story_image_url = None
                st.session_state.story_image_data = None
                st.rerun()
    
    # Close single column container
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ========== MULTI-FUTURE BUTTON ==========
    st.markdown("<div style='height: 3rem;'></div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='text-align: center;'>
            <a href='https://www.multi-future.pl' target='_blank' style='
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
                🌐 Multi-Future.pl
            </a>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    # =========================================
    
    # Sidebar with history
    with st.sidebar:
        st.markdown("### 📚 Historia Opowieści")
        
        if st.session_state.story_history:
            st.markdown(f"*Utworzono {len(st.session_state.story_history)} opowieści*")
            
            for i, story in enumerate(reversed(st.session_state.story_history[-5:]), 1):
                with st.expander(f"📖 {story['genre']} - {story['tone']}"):
                    st.write(f"**Inspiracja:** {story['prompt'][:50]}...")
                    st.write(f"**Fragment:** {story['content'][:100]}...")
                    if st.button(f"Wczytaj", key=f"load_{i}"):
                        st.session_state.current_story = story
                        st.rerun()
            
            if st.button("🗑️ Wyczyść historię", use_container_width=True):
                st.session_state.story_history = []
                st.session_state.current_story = None
                st.session_state.story_image_url = None
                st.session_state.story_image_data = None
                st.rerun()
        else:
            st.info("Brak historii")
        
        st.markdown("---")
        st.markdown("""
            <div style='text-align: center; color: rgba(255,255,255,0.7); font-size: 12px;'>
                Made with ❤️ by Multi-Future<br>
                Powered by GPT-4o & DALL-E 3
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("← Powrót do strony głównej", use_container_width=True):
            st.session_state.page = 'landing'
            st.rerun()