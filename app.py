import streamlit as st
import requests
import json

st.title("🎓 AI Placement Assistant")

api_key = st.text_input("Enter your API Key:", type="password")
user_input = st.text_input("Ask me about placements:")

if st.button("Get Answer"):
    if api_key and user_input:
        # We are using the v1beta endpoint directly
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        data = {"contents": [{"parts": [{"text": user_input}]}]}
        
        try:
            response = requests.post(url, headers=headers, json=data)
            result = response.json()
            
            if response.status_code == 200:
                answer = result['candidates'][0]['content']['parts'][0]['text']
                st.write(answer)
            else:
                st.error(f"Error {response.status_code}: {result.get('error', {}).get('message', 'Unknown Error')}")
        except Exception as e:
            st.write(f"An error occurred: {e}")
    else:
        st.warning("Please enter both the API Key and a question.")
