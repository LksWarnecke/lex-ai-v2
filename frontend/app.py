import streamlit as st
import requests

# Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Rental Contract AI", layout="wide")

# Title
st.title("🏠 Rental Contract AI")

# File Upload Section
st.header("📄 Upload Rental Contract")
uploaded_file = st.file_uploader("Upload a PDF rental contract", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Uploading and analyzing..."):
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{BACKEND_URL}/upload-contract/", files=files)

    if response.status_code == 200:
        st.success("✅ Contract uploaded and analyzed successfully!")
    else:
        st.error(f"❌ Error: {response.text}")

# Chat Section
st.header("💬 Chat with AI")
chat_history = st.session_state.get("chat_history", [])

# Display chat history
for msg in chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

# User Input
user_input = st.text_input("Ask a question about your contract:")
if user_input:
    with st.chat_message("user"):
        st.write(user_input)

    response = requests.get(f"{BACKEND_URL}/chat/", params={"user_message": user_input})
    
    if response.status_code == 200:
        ai_response = response.json().get("ai_response", "Error retrieving response.")
        st.session_state.chat_history.append({"role": "assistant", "text": ai_response})
        with st.chat_message("assistant"):
            st.write(ai_response)
    else:
        st.error(f"❌ Error: {response.text}")
