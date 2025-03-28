from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import easyocr
from langchain_openai import ChatOpenAI
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.settings import Settings
from llama_index.embeddings.openai import OpenAIEmbedding
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

def build_rag_index(text: str):
    """Creates an index of the contract for retrieval-based Q&A."""
    global index
    document = Document(text=text)
    index = VectorStoreIndex.from_documents([document])

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
    build_rag_index(contract_text)
    
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

    query_engine = index.as_query_engine()
    response = query_engine.query(user_message)

    # Store conversation history
    chat_history.append({"role": "user", "text": user_message})
    chat_history.append({"role": "assistant", "text": response.response})

    return {"ai_response": response.response}

@app.post("/generate-letter/", response_model=dict)
async def generate_letter():
    """Generates a formal letter based on the conversation history."""
    if not chat_history:
        raise HTTPException(status_code=400, detail="No conversation history found.")
    if not contract_text:
        raise HTTPException(status_code=400, detail="No contract uploaded.")

    prompt = f"""
    Based on the following conversation between a tenant and an AI assistant,
    generate a formal letter addressing the landlord about the concerns raised.
    
    Contract details:
    {contract_text[:1000]}  # Limit contract text for efficiency
    
    Conversation:
    {chat_history}

    The letter should be concise, professional, and clearly state the concerns and requests.
    """

    letter_response = chatbot.invoke(prompt)

    return {"letter": letter_response}


@app.get("/")
def read_root():
    return {"message": "Rental Agreement AI Backend is running!"}
