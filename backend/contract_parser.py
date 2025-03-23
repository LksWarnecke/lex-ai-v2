import fitz  # PyMuPDF
import re
from llama_index.core import Document
from llama_index.core import VectorStoreIndex
from typing import List

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts raw text from a PDF contract."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    return text.strip()

def split_into_clauses(text: str) -> List[str]:
    """Splits the contract text into separate clauses based on common patterns."""
    clauses = re.split(r"\n\s*\d+\.\s+", text)  # Split by numbered clauses (e.g., "1. Clause text")
    clauses = [clause.strip() for clause in clauses if clause.strip()]
    return clauses

def preprocess_clauses(clauses: List[str]) -> List[str]:
    """Cleans and structures clauses."""
    processed_clauses = []
    for clause in clauses:
        clause = re.sub(r"\s+", " ", clause)  # Remove excessive whitespace
        processed_clauses.append(clause)
    return processed_clauses

def build_contract_index(clauses: List[str]) -> VectorStoreIndex:
    """Creates an index for retrieval-based analysis."""
    documents = [Document(text=clause) for clause in clauses]
    return VectorStoreIndex.from_documents(documents)

def analyze_contract(pdf_path: str) -> VectorStoreIndex:
    """Main function to process a contract and return an index."""
    raw_text = extract_text_from_pdf(pdf_path)
    clauses = split_into_clauses(raw_text)
    processed_clauses = preprocess_clauses(clauses)
    return build_contract_index(processed_clauses)
