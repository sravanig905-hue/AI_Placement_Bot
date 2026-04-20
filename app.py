import streamlit as st
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(page_title="AI Placement Assistant", layout="centered")
st.title("🎓 AI Placement Assistant")

# 2. API Key సెషన్
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

# API Key ఎంటర్ చేయమని అడుగుతుంది
if not st.session_state["api_key"]:
    st.info("ప్రారంభించడానికి మీ Google Gemini API Keyని ఎంటర్ చేయండి.")
    key = st.text_input("Enter API Key", type="password")
    if st.button("Start Chat"):
        st.session_state["api_key"] = key
        st.rerun()
    st.stop()

# 3. Model Configuration - 'gemini-1.5-flash' వాడదాం
try:
    genai.configure(api_key=st.session_state["api_key"])
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    st.error(f"Config Error: {e}")
    st.stop()

# 4. Chat History నిర్వహణ
if "messages" not in st.session_state:
    st.session_state.messages = []

# పాత మెసేజ్ లు చూపించడం
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. ChatGPT లాగా చాట్ ఇన్‌పుట్
if prompt := st.chat_input("Ask me about placements..."):
    # యూజర్ మెసేజ్ సేవ్ & డిస్ప్లే
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # అసిస్టెంట్ రిప్లై
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("API Error: కీ తప్పుగా ఉండవచ్చు లేదా మోడల్ యాక్సెస్ లేదు.")
            st.write(f"Details: {e}")

# 6. Sidebar లో క్లియర్ ఆప్షన్
with st.sidebar:
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()
