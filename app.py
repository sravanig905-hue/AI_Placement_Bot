import streamlit as st
import google.generativeai as genai
import os

# Page Config
st.set_page_config(page_title="AI Placement Assistant", layout="centered")

st.title("🎓 AI Placement Assistant")

# API Key ఎంటర్ చేసే సెక్షన్ (మొదటి సారి మాత్రమే)
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

if not st.session_state["api_key"]:
    st.info("ప్రారంభించడానికి మీ Google Gemini API Keyని ఎంటర్ చేయండి.")
    api_key_input = st.text_input("Enter your API Key", type="password")
    if st.button("Start Chat"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            st.rerun()
        else:
            st.warning("దయచేసి API Key ఇవ్వండి.")
    st.stop()

# GenAI Config - 'gemini-pro' ని ఉపయోగిస్తున్నాం ఎందుకంటే ఇది మోడల్ ఎర్రర్స్ రాకుండా ఉంటుంది
genai.configure(api_key=st.session_state["api_key"])
model = genai.GenerativeModel("gemini-pro")

# Chat History నిర్వహణ (ChatGPT లాగా)
if "messages" not in st.session_state:
    st.session_state.messages = []

# పాత మెసేజ్‌లను చూపించడం
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# యూజర్ నుండి ఇన్‌పుట్ తీసుకోవడం
if prompt := st.chat_input("Ask me anything about placements..."):
    # యూజర్ మెసేజ్ డిస్‌ప్లే
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # అసిస్టెంట్ రెస్పాన్స్ (Error Handling తో)
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error: {e}")
            st.write("మోడల్ ఎర్రర్ వచ్చింది, దయచేసి API Key చెక్ చేసుకోండి.")

# సైడ్ బార్ లో Clear Chat ఆప్షన్
with st.sidebar:
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
