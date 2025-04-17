import streamlit as st
import requests

# Backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Rental Contract AI", layout="wide")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

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

    # ✅ Add user message to local chat history
    st.session_state.chat_history.append({"role": "user", "text": user_input})

    # 🔄 Send request to chat endpoint
    response = requests.post(f"{BACKEND_URL}/chat/", json={"user_message": user_input})
    
    if response.status_code == 200:
        ai_response = response.json().get("ai_response", "Error retrieving response.")
        st.session_state.chat_history.append({"role": "assistant", "text": ai_response})
        with st.chat_message("assistant"):
            st.write(ai_response)
    else:
        st.error(f"❌ Error: {response.text}")

# New Section for Evidence Upload (Image Upload)
st.header("📸 Upload Evidence (Image)")
uploaded_image = st.file_uploader("Upload an image for evidence", type=["jpg", "jpeg", "png", "bmp"])

if uploaded_image is not None:
    with st.spinner("Uploading and analyzing evidence..."):
        files = {"file": uploaded_image.getvalue()}
        response = requests.post(f"{BACKEND_URL}/upload-evidence/", files=files)

    if response.status_code == 200:
        matched_clauses = response.json().get("matched_clauses", [])
        if matched_clauses:
            st.success("✅ Evidence processed and matched with clauses!")
            st.subheader("Matched Clauses:")
            for match in matched_clauses:
                st.write(f"**Clause {match['clause_number']}:** {match['clause_text']}")
                if match['matched']:
                    st.markdown("**Status:** Matched ✔️")
                else:
                    st.markdown("**Status:** Not Matched ❌")
        else:
            st.error("❌ No matching clauses found.")
    else:
        st.error(f"❌ Error: {response.text}")

# 📝 Generate Formal Letter from Selected Messages
st.header("📜 Generate Formal Letter (Select Messages)")

# Create a multiselect to let the user pick which chat history items to include
chat_options = [
    f"{msg['role'].capitalize()}: {msg['text'][:100]}..."  # truncate preview
    for msg in st.session_state.chat_history
]
selected_indices = st.multiselect("Select messages to include in the letter:", options=list(range(len(chat_options))), format_func=lambda i: chat_options[i])

# Button to generate the letter from selected messages
if st.button("Generate Letter from Selected"):
    if not selected_indices:
        st.warning("Please select at least one message.")
    else:
        # Collect selected message texts only
        selected_messages = [st.session_state.chat_history[i]['text'] for i in selected_indices]

        with st.spinner("Generating letter..."):
            response = requests.post(
                f"{BACKEND_URL}/generate-letter-from-selection/",
                json=selected_messages
            )

        if response.status_code == 200:
            letter_text = response.json().get("letter", "Error generating letter.")
            st.success("✅ Letter generated successfully!")
            st.subheader("📜 Generated Letter:")
            st.write(letter_text)
        else:
            st.error(f"❌ Error: {response.text}")
