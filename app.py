import streamlit as st
import google.generativeai as genai
import os
import json
import time
from datetime import datetime
from jobs import get_job_links

# API key setup
def _load_local_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" not in line: continue
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass

_load_local_env()

# Try loading key
env_key = os.environ.get("PSSKEY") or os.environ.get("GENAI_API_KEY")

if "api_key" not in st.session_state:
    st.session_state["api_key"] = env_key

provided_key = st.session_state.get("api_key")

if not provided_key:
    st.warning("API key missing. Please provide it.")
    entered = st.text_input("Enter API key", type="password")
    if st.button("Set API key") and entered:
        st.session_state["api_key"] = entered
        st.rerun()
else:
    genai.configure(api_key=provided_key)
    # Default model updated to gemini-1.5-flash
    if "model_name" not in st.session_state:
        st.session_state["model_name"] = "gemini-1.5-flash"

st.title("🎓 AI Placement Assistant")

# Chat history
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "chat_history.json")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def append_history(entry):
    h = load_history()
    h.append(entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = load_history()

# Render chat
for item in st.session_state["chat_history"]:
    role = "You" if item["role"] == "user" else "Assistant"
    st.markdown(f"**{role}**: {item['text']}")

# Input
msg = st.text_input("Type your message")
if st.button("Send") and msg:
    user_entry = {"role": "user", "text": msg, "time": datetime.utcnow().isoformat()}
    st.session_state["chat_history"].append(user_entry)
    append_history(user_entry)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(msg)
        text = response.text
    except Exception as e:
        text = f"Generation failed: {e}"
        
    assistant_entry = {"role": "assistant", "text": text, "time": datetime.utcnow().isoformat()}
    st.session_state["chat_history"].append(assistant_entry)
    append_history(assistant_entry)
    st.rerun()

# Job links
st.markdown("---")
st.subheader("Job Links")
last_user = next((h["text"] for h in reversed(st.session_state["chat_history"]) if h["role"] == "user"), None)
if last_user:
    for link in get_job_links(last_user):
        st.write(link)
