import streamlit as st
import google.generativeai as genai

st.title("AI Assistant")
api_key = st.text_input("Enter your API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Using the most basic model available
    model = genai.GenerativeModel("gemini-pro")
    
    prompt = st.text_input("Ask a question:")
    if st.button("Get Answer"):
        try:
            response = model.generate_content(prompt)
            st.write(response.text)
        except Exception as e:
            st.error("The API key is invalid or doesn't have Gemini access.")
            st.write(f"Technical error: {e}")
