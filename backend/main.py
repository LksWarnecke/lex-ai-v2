from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import easyocr
from langchain_openai import ChatOpenAI
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.settings import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.query_engine import RetrieverQueryEngine
from contract_parser import extract_text_from_pdf, split_into_clauses, preprocess_clauses

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize LangChain Chatbot & LlamaIndex
chatbot = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key="")  # Example model
Settings.llm = chatbot

# Set OpenAI API key for embeddings
Settings.embed_model = OpenAIEmbedding(model="text-embedding-ada-002", api_key="")

# Initialize OCR (EasyOCR)
ocr_reader = easyocr.Reader(['en'])

# Initialize variables for contract text and index
index = None
contract_text = ""
clauses = []

# Store clauses with metadata and index them
def build_rag_index(clauses_list):
    """Creates an index of the contract clauses for retrieval-based Q&A."""
    global index
    documents = [Document(text=clause, metadata={"clause_id": i + 1}) for i, clause in enumerate(clauses_list)]
    index = VectorStoreIndex.from_documents(documents)

@app.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    """Uploads a contract, processes it, and creates a RAG index."""
    global contract_text, clauses
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    contract_text = extract_text_from_pdf(file_path)
    clauses = split_into_clauses(contract_text)
    clauses = preprocess_clauses(clauses)
    build_rag_index(clauses)

    return {"message": "Contract uploaded and analyzed successfully."}

@app.post("/upload-evidence/")
async def upload_evidence(file: UploadFile = File(...)):
    """Uploads an image, runs OCR, and checks for evidence in contract clauses."""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 1: Run OCR on the uploaded image
    ocr_result = ocr_reader.readtext(file_path)
    detected_text = " ".join([item[1] for item in ocr_result])

    # Step 2: Check if the detected text matches any clauses in the contract
    matched_clauses = []
    for i, clause in enumerate(clauses):
        if detected_text.lower() in clause.lower():
            matched_clauses.append({"clause_number": i+1, "clause_text": clause, "matched": True})
        else:
            matched_clauses.append({"clause_number": i+1, "clause_text": clause, "matched": False})

    return {"matched_clauses": matched_clauses}

chat_history = []  # Store conversation history

@app.post("/chat/")
async def chat_with_ai(request: dict = Body(...)):
    """Chats with the AI using the uploaded contract."""
    if not index:
        raise HTTPException(status_code=400, detail="No contract uploaded.")

    user_message = request.get("user_message")
    if not user_message:
        raise HTTPException(status_code=400, detail="User message is missing.")

    query_engine = index.as_query_engine(response_mode="compact")
    response = query_engine.query(user_message)

    # Extract matching source clause(s)
    sources = []
    for node in response.source_nodes:
        clause_id = node.metadata.get("clause_id", "N/A")
        clause_text = node.text.strip()
        sources.append(f'Clause {clause_id}: "{clause_text}"')

    sources_text = "\n".join(sources) if sources else "No specific clause found."

    # Format AI's final response
    formatted_response = f"Answer: {response.response.strip()}\n\nSource:\n{sources_text}"

    # Append to chat history (user question and assistant's response)
    chat_history.append({"role": "user", "text": user_message})
    chat_history.append({"role": "assistant", "text": formatted_response})

    return {"ai_response": formatted_response}

@app.post("/generate-letter/", response_model=dict)
async def generate_letter():
    """Generates a formal letter based on the conversation history."""
    if not chat_history:
        raise HTTPException(status_code=400, detail="No conversation history found.")
    if not contract_text:
        raise HTTPException(status_code=400, detail="No contract uploaded.")

    # Extract just the clean dialogue without clause sources
    cleaned_history = []
    for msg in chat_history:
        if msg["role"] == "user":
            cleaned_history.append(f"User: {msg['text']}")
        elif msg["role"] == "assistant":
            answer_only = msg["text"].split("\n\nSource:")[0].strip()
            cleaned_history.append(f"Assistant: {answer_only}")

    formatted_history = "\n".join(cleaned_history)

    prompt = f"""
    Based on the following conversation between a tenant and an AI assistant,
    generate a formal letter addressing the landlord about the concerns raised.

    Contract details (excerpt):
    {contract_text[:1000]}

    Conversation:
    {formatted_history}

    The letter should be concise, professional, and clearly state the concerns and requests.
    """

    letter_response = chatbot.invoke(prompt)

    return {"letter": letter_response.content}

@app.post("/generate-letter-from-selection/", response_model=dict)
async def generate_letter_from_selection(selected_messages: list = Body(...)):
    """Generates a letter from selected chat history items sent by the frontend."""
    if not selected_messages:
        raise HTTPException(status_code=400, detail="No selected messages provided.")
    if not contract_text:
        raise HTTPException(status_code=400, detail="No contract uploaded.")

    formatted_history = "\n".join(selected_messages)

    prompt = f"""
    Based on the following conversation between a tenant and an AI assistant,
    generate a formal letter addressing the landlord about the concerns raised.

    Contract details (excerpt):
    {contract_text[:1000]}

    Selected Conversation:
    {formatted_history}

    The letter should be concise, professional, and clearly state the concerns and requests.
    """

    letter_response = chatbot.invoke(prompt)

    return {"letter": letter_response.content}

@app.get("/")
def read_root():
    return {"message": "Rental Agreement AI Backend is running!"}