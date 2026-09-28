import streamlit as st
import os
import re
import json
import hashlib
from datetime import datetime
from groq import Groq
from gtts import gTTS
import io

# Configuração visual da página Web (Layout centralizado e limpo)
st.set_page_config(
    page_title="Senior English Voice Mentor",
    page_icon="🎓",
    layout="centered"
)

# --- CSS CUSTOMIZADO PARA LAYOUT COMPACTO, AUTO-SCROLL E ASSINATURA ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 800px;
    }
    .stChatMessage {
        padding: 0.6rem 0.8rem !important;
        margin-bottom: 0.4rem !important;
    }
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2, h3 {
        font-size: 1.3rem !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        min-height: 38px !important;
    }
    /* Assinatura fixa no canto inferior direito */
    .footer-credit {
        position: fixed;
        bottom: 10px;
        right: 15px;
        font-size: 0.75rem;
        color: #888;
        background: rgba(255, 255, 255, 0.9);
        padding: 3px 8px;
        border-radius: 4px;
        z-index: 99999;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Exibe a assinatura no rodapé inferior direito
st.markdown('<div class="footer-credit">Produced by Marcio Thomann</div>', unsafe_allow_html=True)

# --- 1. CONFIGURAÇÃO SEGURA DA CHAVE DA API (Local ou Nuvem) ---
MINHA_CHAVE_GROQ = "COLE_SUA_CHAVE_NOVA_AQUI"

try:
    if "GROQ_API_KEY" in st.secrets:
        MINHA_CHAVE_GROQ = st.secrets["GROQ_API_KEY"]
except Exception:
    pass # Ignora caso esteja rodando localmente sem secrets.toml

if MINHA_CHAVE_GROQ == "COLE_SUA_CHAVE_NOVA_AQUI" or not MINHA_CHAVE_GROQ.startswith("gsk_"):
    st.error("🚨 Atenção, Márcio! A chave da API da Groq não foi configurada.")
    st.info("Cole sua chave real da Groq diretamente aqui no código (para testes locais) ou configure os Secrets no Streamlit Cloud.")
    st.stop()

# --- 2. SISTEMA DE AUTENTICAÇÃO E BANCO DE DADOS DE USUÁRIOS ---
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# --- TELA DE LOGIN / CADASTRO ---
if not st.session_state.logged_in:
    st.title("🎓 Senior English Voice Mentor - Acesso")
    st.markdown("Faça login ou cadastre sua conta para acompanhar seu histórico pessoal de evolução.")
    
    tab_login, tab_register = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    users_db = load_users()
    
    with tab_login:
        st.subheader("Login de Usuário")
        login_user = st.text_input("Usuário", key="login_user").strip()
        login_pass = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Entrar no Sistema"):
            if login_user in users_db and users_db[login_user] == hash_password(login_pass):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("❌ Usuário ou senha inválidos.")
                
    with tab_register:
        st.subheader("Cadastro de Novo Aluno")
        new_user = st.text_input("Escolha um Nome de Usuário", key="new_user").strip()
        new_pass = st.text_input("Escolha uma Senha", type="password", key="new_pass")
        confirm_pass = st.text_input("Confirme a Senha", type="password", key="confirm_pass")
        
        if st.button("Cadastrar"):
            if not new_user or not new_pass:
                st.warning("⚠️ Preencha todos os campos.")
            elif new_user in users_db:
                st.error("❌ Este nome de usuário já existe. Escolha outro.")
            elif new_pass != confirm_pass:
                st.error("❌ As senhas não coincidem.")
            else:
                users_db[new_user] = hash_password(new_pass)
                save_users(users_db)
                st.success("✅ Conta criada com sucesso! Vá para a aba 'Entrar' para acessar.")
                
    st.stop()

# --- 3. PAINEL LATERAL: CONFIGURAÇÕES E NÍVEIS (A1 a C2) ---
st.sidebar.title(f"👤 Olá, {st.session_state.username}")
if st.sidebar.button("🚪 Sair (Logout)"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("⚙️ Configurações")

selected_level = st.sidebar.selectbox(
    "Nível de Inglês:",
    [
        "A1 (Beginner)", 
        "A2 (Elementary)", 
        "B1 (Intermediate)", 
        "B2 (Upper-Intermediate)", 
        "C1 (Advanced)", 
        "C2 (Proficient)"
    ],
    index=3 # B2 padrão
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Foco")
st.sidebar.markdown(f"- Histórico: `progress_memory_{st.session_state.username}.txt`\n- Viagem aos Estados Unidos\n- Online & Seguro")

# --- 4. SISTEMA DE MEMÓRIA E HISTÓRICO PERSISTENTE ---
MEMORY_FILE = f"progress_memory_{st.session_state.username}.txt"

def load_recent_insights():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            return "".join(lines[-15:]).strip()
    return "No previous data yet. Start tracking progress today."

def save_insight(insight_text):
    date_str = datetime.now().strftime("%d/%m/%Y")
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        clean_insight = insight_text.replace('\n', ' ').strip()
        f.write(f"[{date_str}] {clean_insight}\n")

# --- 5. FUNÇÃO BLINDADA DE LIMPEZA DE ÁUDIO ---
def clean_text_for_speech(text):
    """Remove rigorosamente emojis, markdown, travessões, hifens, asteriscos e aspas para o TTS falar apenas inglês puro."""
    text = re.sub(r'---.*', '', text, flags=re.DOTALL)
    text = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]|[\U0001f300-\U0001f5ff]|[\U0001f600-\U0001f64f]|[\U0001f680-\U0001f6ff]|[\U0001f700-\U0001f77f]|[\U0001f780-\U0001f7ff]|[\U0001f800-\U0001f8ff]|[\U0001f900-\U0001f9ff]|[\U0001fa00-\U0001fa6f]|[\U0001fa70-\U0001faff]|[\u2702-\u27B0]|[\u24C2-\U0001f251]', '', text)
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`]*`', '', text)
    text = re.sub(r'[*_#`~>\[\](){}]', ' ', text)
    text = re.sub(r'[—–\-\/\|\\+=]', ' ', text)
    text = re.sub(r'["""''`„«»]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

st.title("🎓 Senior English Voice Mentor")
st.markdown(f"**Usuário:** `{st.session_state.username}` | **Nível:** `{selected_level}` | Ambiente Online Ativo.")

# --- 6. INICIALIZAÇÃO E ATUALIZAÇÃO DINÂMICA DO MOTOR DA IA ---
if "client" not in st.session_state:
    st.session_state.client = Groq(api_key=MINHA_CHAVE_GROQ)
    st.session_state.model_id = "openai/gpt-oss-120b"
    st.session_state.last_level = selected_level
    st.session_state.display_messages = []

past_progress = load_recent_insights()

if "messages" not in st.session_state or st.session_state.get('last_level') != selected_level:
    st.session_state.last_level = selected_level
    
    st.session_state.messages = [
        {
            "role": "system",
            "content": f"""
            You are an elite, world-class Senior English Language Mentor and Cognitive Coach. 
            
            STUDENT PROFILE & TARGET LEVEL:
            - Student Username: {st.session_state.username}
            - Current Target Level: {selected_level}
            - Primary Goals: Conversação natural, imersão e fluência em situações cotidianas.
            - Upcoming Milestone: Traveling to the United States. Include travel, driving, logistics, and real-life scenarios.
            
            HISTORICAL EVOLUTION & PREVIOUS INSIGHTS:
            {past_progress}
            
            CORE OPERATIONAL RULES & CORRECTION LOOP:
            1. LANGUAGE SEPARATION (SCREEN vs AUDIO):
               - If the level is A1 or A2: Write your explanations, context, grammar tips, and corrections in **Portuguese** on the screen so the student understands clearly. Then, provide the practice sentence or dialogue in **English**. 
               - If the level is B1 to C2: Maintain natural conversational scaffolding appropriate to the level.
               - CRITICAL FOR AUDIO: At the very end of your response, you MUST include a clean line starting with '--- [Audio]: ' followed **ONLY** by the English sentence or phrase that the student needs to pronounce. Do NOT put Portuguese or emojis in the `--- [Audio]:` line.
            
            2. MANDATORY CORRECTION & PRACTICE LOOP:
               - Whenever the student's spoken sentence contains grammatical errors, awkward phrasing, or can be structured significantly better, **you MUST enter a Correction Loop**.
               - In this loop, explain the better structure clearly on screen (in Portuguese for A1/A2), provide the improved sentence, and **explicitly ask the student to repeat and pronounce this exact improved sentence right now**.
               - Do NOT move on to a new topic or question until the student practices and successfully repeats the corrected structure.
               - Ensure the `--- [Audio]:` tag contains *only* this corrected sentence so the student hears the ideal pronunciation.
            
            3. RESPONSE STRUCTURE: Reply clearly with text on screen. End with your audio tag '--- [Audio]: <english sentence>' and optionally '--- [Mentor Insights]: <tip>'.
            """
        }
    ]
    
    initial_greeting = f"Hello, {st.session_state.username}! I am your Senior English Mentor. We are operating at the {selected_level} level. Let's practice. What would you like to discuss today?"
    
    if not st.session_state.display_messages:
        st.session_state.display_messages.append({"role": "assistant", "content": initial_greeting})
    else:
        st.session_state.display_messages[0] = {"role": "assistant", "content": initial_greeting}

# --- RENDERIZAÇÃO DO HISTÓRICO VISUAL ---
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "user" and msg.get("audio"):
            st.audio(msg["audio"], format="audio/wav")

# --- 7. FERRAMENTA DE CORREÇÃO RÁPIDA DA ÚLTIMA TRANSCRIÇÃO ---
if "display_messages" in st.session_state and len(st.session_state.display_messages) > 1:
    with st.expander("✏️ A transcrição saiu errada? Corrija sua fala anterior aqui"):
        last_user_idx = -1
        for idx in range(len(st.session_state.display_messages) - 1, -1, -1):
            if st.session_state.display_messages[idx]["role"] == "user":
                last_user_idx = idx
                break
        
        if last_user_idx != -1:
            current_text = st.session_state.display_messages[last_user_idx]["content"]
            fixed_text = st.text_input("Ajuste o texto da sua fala:", value=current_text, key="quick_fix_input")
            if st.button("🔄 Atualizar Contexto e Recalcular"):
                if fixed_text:
                    if len(st.session_state.display_messages) > last_user_idx + 1:
                        st.session_state.display_messages.pop()
                    st.session_state.display_messages.pop()
                    
                    st.session_state.display_messages.append({"role": "user", "content": fixed_text})
                    st.rerun()

# --- 8. ENTRADA DE ÁUDIO (MICROFONE COM ALTA PRECISÃO WHISPER) ---
audio_file = st.audio_input("🎤 Falar em inglês:")

user_text = None
user_audio_bytes = None

if audio_file is not None:
    if "last_audio_id" not in st.session_state or st.session_state.last_audio_id != audio_file.file_id:
        st.session_state.last_audio_id = audio_file.file_id
        
        with st.spinner("Transcrevendo sua voz com precisão..."):
            try:
                user_audio_bytes = audio_file.read()
                audio_file_obj = io.BytesIO(user_audio_bytes)
                audio_file_obj.name = "audio.wav"
                
                transcription = st.session_state.client.audio.transcriptions.create(
                    file=(audio_file_obj.name, audio_file_obj.read()),
                    model="whisper-large-v3-turbo",
                    language="en",
                    prompt="English conversation practice for travel, airport, hotel, driving, and everyday situations.",
                    temperature=0.0
                )
                user_text = transcription.text
            except Exception as e:
                user_text = None
                user_audio_bytes = None

if not user_text:
    user_text = st.chat_input("Ou digite sua mensagem aqui...")

# --- 9. PROCESSAMENTO E RESPOSTA COM STREAMING E LOOP DE CORREÇÃO ---
if user_text:
    msg_data = {"role": "user", "content": user_text}
    if user_audio_bytes:
        msg_data["audio"] = user_audio_bytes
        
    st.session_state.display_messages.append(msg_data)
    
    with st.chat_message("user"):
        st.markdown(user_text)
        if user_audio_bytes:
            st.audio(user_audio_bytes, format="audio/wav")

    api_payload = [st.session_state.messages[0]]
    for msg in st.session_state.display_messages:
        api_payload.append({"role": msg["role"], "content": msg["content"]})

    with st.chat_message("assistant"):
        try:
            stream = st.session_state.client.chat.completions.create(
                model=st.session_state.model_id,
                messages=api_payload,
                temperature=0.6,
                max_tokens=800,
                stream=True
            )
            
            def response_generator():
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content

            mentor_reply = st.write_stream(response_generator())
            
            st.session_state.display_messages.append({"role": "assistant", "content": mentor_reply})
            
            if "--- [Mentor Insights]:" in mentor_reply:
                parts = mentor_reply.split("--- [Mentor Insights]:")
                if len(parts) > 1:
                    save_insight(parts[1].strip())
            
            if "--- [Audio]:" in mentor_reply:
                audio_part = mentor_reply.split("--- [Audio]:")[1].split("--- [Mentor Insights]:")[0].strip()
            else:
                audio_part = mentor_reply
            
            clean_speech = clean_text_for_speech(audio_part)
            
            if clean_speech:
                tts = gTTS(text=clean_speech, lang='en', tld='com')
                tts_fp = io.BytesIO()
                tts.write_to_fp(tts_fp)
                tts_fp.seek(0)
                st.audio(tts_fp, format='audio/mp3', autoplay=True)
                    
        except Exception as e:
            st.error("⚠️ Ocorreu um pequeno erro de comunicação. Tente novamente.")

# Script JavaScript persistente com MutationObserver para rolar a tela automaticamente
st.markdown("""
<script>
    const scrollObserver = new MutationObserver(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    });
    scrollObserver.observe(document.body, { childList: true, subtree: true });
</script>
""", unsafe_allow_html=True)