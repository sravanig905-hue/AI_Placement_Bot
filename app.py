import streamlit as st
from huggingface_hub import InferenceClient

st.title("🎓 AI Placement Assistant")

# Use a free, high-performance model
client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2")

user_input = st.text_input("Ask me about placements:")

if st.button("Get Answer"):
    if user_input:
        try:
            # Generate response
            response = client.text_generation(user_input, max_new_tokens=250)
            st.write(response)
        except Exception as e:
            st.error("Error: Could not connect to the model. Try again in a few seconds.")
            st.write(f"Details: {e}")
    else:
        st.warning("Please ask a question.")
