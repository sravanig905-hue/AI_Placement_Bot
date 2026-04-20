import streamlit as st
import google.generativeai as genai
import os
import json
from datetime import datetime
from jobs import get_job_links

# Page Config
st.set_page_config(page_title="AI Placement Assistant", layout="centered")
st.title("🎓 AI Placement Assistant")

# API Key సెటప్
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

# API కీ ఎంటర్ చేసే సెక్షన్
if not st.session_state["api_key"]:
    st.info("ప్రారంభించడానికి మీ Google Gemini API Keyని ఎంటర్ చేయండి.")
    api_key_input = st.text_input("Enter your API Key", type="password")
    if st.button("Start Chat"):
        if api_key_input:
            st.session_state["api_key"] = api_key_input
            st.rerun()
        else:
            st.error("దయచేసి సరైన API Key ఇవ్వండి.")
    st.stop() # కీ ఇచ్చే వరకు కింద కోడ్ రన్ అవ్వదు

# API Config
genai.configure(api_key=st.session_state["api_key"])
model = genai.GenerativeModel("gemini-1.5-flash")

# Chat History
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# Chat ని రన్ చేయడం
for chat in st.session_state["chat_history"]:
    with st.chat_message(chat["role"]):
        st.write(chat["text"])

# యూజర్ మెసేజ్
if prompt := st.chat_input("Ask me anything about placements..."):
    # యూజర్ చాట్
    st.session_state["chat_history"].append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # అసిస్టెంట్ రెస్పాన్స్
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(f"You are a helpful placement assistant. {prompt}")
            answer = response.text
            st.write(answer)
            st.session_state["chat_history"].append({"role": "assistant", "text": answer})
        except Exception as e:
            st.error(f"Error: {e}")

    # Job Links (చివరగా చూపిస్తుంది)
    st.markdown("---")
    st.subheader("Related Job Links")
    links = get_job_links(prompt)
    if links:
        for link in links:
            st.write(link)
