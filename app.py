import streamlit as st
import google.generativeai as genai
import os
import tempfile
from dotenv import load_dotenv

# ==========================================
# 1. API Configuration (SECURE WAY)
# ==========================================
# Yeh line automatically .env file se saare secrets load kar degi
load_dotenv()

# Ab hum key ko securely system environment se fetch kar rahe hain
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("🚨 API Key nahi mili! Please check karein ki aapne sahi se .env file banayi hai.")
    st.stop()

genai.configure(api_key=api_key)

SYNC_PERSONA = """
You are Sync, the intelligent AI study companion powering PrepMate.

FEATURE 3 - NOTES SUMMARIZER:
When summarizing, provide a structured summary with: Key concepts, Important definitions, and Likely exam questions.

FEATURE 4 - QUIZ GENERATOR:
When generating a quiz, provide 3-5 challenging questions based on the topic or document. Provide the questions first, and instruct the student to try answering them!
"""

# Google ka best reasoning model
model = genai.GenerativeModel(
    model_name="gemini-1.5-pro-latest",
    system_instruction=SYNC_PERSONA
)

# ==========================================
# 2. Streamlit UI & Custom CSS 
# ==========================================
st.set_page_config(page_title="PrepMate", page_icon="⚡", layout="wide")

custom_css = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    div.stButton > button:first-child {
        background-color: #4F46E5;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #4338CA;
        transform: translateY(-2px);
    }
    
    [data-testid="stSidebar"] {
        background-color: #111827;
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Main Title Area
col_title, col_space = st.columns([3, 1])
with col_title:
    st.title("⚡ PrepMate")
    st.caption("Advanced AI Study Hub • Powered by Gemini 1.5 Pro")
st.divider()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "model", "content": "Welcome to PrepMate! 🚀 Drop your notes in the sidebar or let's start chatting. How can I help you level up today?"}
    ]

# ==========================================
# 3. Sidebar: Document Upload & Quick Actions
# ==========================================
action_triggered = None

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4204/4204928.png", width=80)
    st.header("📂 Knowledge Base")
    uploaded_file = st.file_uploader("Upload PDFs or Images", type=["pdf", "txt", "png", "jpg", "jpeg"])
    
    uploaded_gemini_file = None
    if uploaded_file is not None:
        with st.spinner("Analyzing document..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            uploaded_gemini_file = genai.upload_file(tmp_file_path)
            st.success(f"File Active: {uploaded_file.name}")
            os.remove(tmp_file_path)

    st.write("---")
    st.header("⚡ Smart Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Summary", use_container_width=True):
            action_triggered = "Analyze the uploaded document or recent chat. Give me a clean summary with key concepts, definitions, and potential exam questions."
    with col2:
        if st.button("🃏 Quiz Me", use_container_width=True):
            action_triggered = "Create a tough practice quiz (3-5 questions) based on the uploaded document or our recent chat. Ask the questions first!"

# ==========================================
# 4. Chat Interface
# ==========================================
chat_col_left, chat_col_main, chat_col_right = st.columns([1, 6, 1])

with chat_col_main:
    for message in st.session_state.chat_history:
        avatar_icon = "😎" if message["role"] == "user" else "🤖"
        with st.chat_message(message["role"], avatar=avatar_icon):
            st.markdown(message["content"])

# ==========================================
# 5. Core Engine & Input
# ==========================================
user_input = st.chat_input("Type your study question here...")

if action_triggered:
    user_input = action_triggered

if user_input:
    with chat_col_main:
        with st.chat_message("user", avatar="😎"):
            if action_triggered:
                display_text = "✨ *Action Triggered: " + ("Summary Generator*" if "Summary" in action_triggered else "Quiz Generator*")
                st.markdown(display_text)
                st.session_state.chat_history.append({"role": "user", "content": display_text})
            else:
                st.markdown(user_input)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # Format history
        formatted_history = []
        for msg in st.session_state.chat_history[1:]:
            role = "user" if msg["role"] == "user" else "model"
            clean_content = msg["content"].replace("✨ *Action Triggered: ", "")
            formatted_history.append({"role": role, "parts": [clean_content]})
        
        # Generate Response
        with st.chat_message("model", avatar="🤖"):
            message_placeholder = st.empty()
            
            try:
                chat = model.start_chat(history=formatted_history[:-1])
                
                if uploaded_gemini_file:
                    response = chat.send_message([uploaded_gemini_file, user_input], stream=True)
                else:
                    response = chat.send_message(user_input, stream=True)
                
                full_response = ""
                for chunk in response:
                    full_response += chunk.text
                    message_placeholder.markdown(full_response + "▌")
                
                message_placeholder.markdown(full_response)
                st.session_state.chat_history.append({"role": "model", "content": full_response})
                
            except Exception as e:
                st.error(f"Error fetching response: {e}")