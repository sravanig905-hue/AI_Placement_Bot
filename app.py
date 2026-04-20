import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="AI Placement Assistant")
st.title("🎓 AI Placement Assistant")

# API Key సెషన్
if "api_key" not in st.session_state:
    st.session_state["api_key"] = None

if not st.session_state["api_key"]:
    st.info("API Key ఎంటర్ చేయండి:")
    key = st.text_input("Enter API Key", type="password")
    if st.button("Start Chat"):
        st.session_state["api_key"] = key
        st.rerun()
    st.stop()

# జనరేటివ్ AI సెటప్
try:
    genai.configure(api_key=st.session_state["api_key"])
    # మోడల్ ని ఇక్కడ మారుస్తున్నాం
    model = genai.GenerativeModel("gemini-1.5-pro") 
except Exception as e:
    st.error(f"Error: {e}")
    st.stop()

# చాట్ హిస్టరీ
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# చాట్ ఇన్‌పుట్
if prompt := st.chat_input("Ask me about placements..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error("API Error: మీ కీ చెక్ చేసుకోండి లేదా AI Studio లో అనుమతులు సరిచూసుకోండి.")
            st.write(f"Details: {e}")
