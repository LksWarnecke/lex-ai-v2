from llama_index.llms import GPTSimpleVectorIndex, SimpleDirectoryReader
from llama_index import VectorStoreIndex, ServiceContext, Document
from llama_index.llms import OpenAI
from typing import List
import os
import openai
from config import OPENAI_API_KEY

#test change

openai.api_key = OPENAI_API_KEY

# Initialize the LLM model (for simplicity using OpenAI model here, but can be replaced)
from langchain.llms import OpenAI

# Simple helper function for building an AI-driven query engine
def create_query_engine(index: VectorStoreIndex):
    """Creates a simple query engine based on the contract index."""
    query_engine = index.as_query_engine()
    return query_engine

def load_contract_index(index_path: str) -> VectorStoreIndex:
    """Loads the contract index (assuming it's saved as a pickled file or similar)."""
    # If your index is saved to a specific location, we can reload it here. For simplicity, it's loaded fresh.
    if os.path.exists(index_path):
        return VectorStoreIndex.load_from_disk(index_path)
    else:
        raise FileNotFoundError("Index file not found. Please upload a contract first.")

def chat_with_contract(index: VectorStoreIndex, user_query: str) -> str:
    """Process user query and get a response based on the contract clauses."""
    # Create query engine
    query_engine = create_query_engine(index)
    
    # Get response from the query engine based on the user query
    response = query_engine.query(user_query)
    
    # Return the AI's response
    return response.response
