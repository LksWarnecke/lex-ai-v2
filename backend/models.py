from pydantic import BaseModel
from typing import List, Optional

class Contract(BaseModel):
    """Model to represent the uploaded contract."""
    file_name: str
    text: str
    clauses: Optional[List[str]] = []

class Clause(BaseModel):
    """Model to represent individual clauses in the contract."""
    clause_number: int
    clause_text: str
    matched: bool  # True if the clause's promises are matched, else False
