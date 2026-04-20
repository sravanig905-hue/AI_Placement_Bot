import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(page_title="AI Placement Assistant", layout="centered")
st.title("🎓 AI Placement Assistant")

# API Key Session State
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

# Input API Key if not already set
if not st.session_state["api_key"]:
    st.info("Please enter your Google Gemini API Key to start.")
    key = st.text_input("Enter API Key", type="password")
    if st.button("Start Chat"):
        st.session_state["api_key"] = key
        st.rerun()
    st.stop()

# Configure Generative AI
try:
    genai.configure(api_key=st.session_state["api_key"])
    # Using gemini-1.0-pro for stability
    model = genai.GenerativeModel("gemini-1.0-pro") 
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask me about placements..."):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant response
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("Model Error: Failed to generate response. Please check your API Key or model access.")
            st.write(f"Technical Details: {e}")

# Sidebar for controls
with st.sidebar:
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
