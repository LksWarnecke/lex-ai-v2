from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import openai
from langchain_openai import ChatOpenAI
from llama_index.core import VectorStoreIndex, Document
from llama_index.core.settings import Settings
from contract_parser import extract_text_from_pdf

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

# Set the OpenAI API key (if not already set in the environment)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize LangChain Chatbot & LlamaIndex
chatbot = ChatOpenAI(model_name="gpt-3.5-turbo")  # Example model
Settings.llm = chatbot
index = None
contract_text = ""

def build_rag_index(text: str):
    """Creates an index of the contract for retrieval-based Q&A."""
    global index
    document = Document(text=text)
    index = VectorStoreIndex.from_documents([document])

@app.post("/upload-contract/")
async def upload_contract(file: UploadFile = File(...)):
    global contract_text
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    contract_text = extract_text_from_pdf(file_path)
    build_rag_index(contract_text)
    
    return {"message": "Contract uploaded and analyzed successfully."}

@app.post("/chat/")
async def chat_with_ai(user_message: str):
    if not index:
        raise HTTPException(status_code=400, detail="No contract uploaded.")
    
    query_engine = index.as_query_engine()
    response = query_engine.query(user_message)
    
    return {"ai_response": response.response}

@app.get("/")
def read_root():
    return {"message": "Rental Agreement AI Backend is running!"}
