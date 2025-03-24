Current State:
The application allows users to chat with a PDF rental contract.
Next Functionalities to Implement:
Enhanced Contract Analysis:
Ensure the contract is analyzed meticulously, with a focus on accuracy and detail.
Improve the clause extraction and understanding logic to avoid errors if needed.
Evidence Upload and Analysis:
Implement a feature using PyTorch where users can upload evidence (e.g., images).
Analyze the evidence to verify if it matches the clauses discussed in the chat.
Automated Message Generation:
Add a button to end the chat.
At the end of the chat, generate a message addressing the landlord.
The message should be based only on the chat history and uploaded evidence.
Include all topics discussed in the chat where the user sees unmatched promises made in the contract, ensuring clarity and relevance.
Implementation Guidelines:
Keep the implementation simple and aligned with the existing codebase.
Extend the current structure without introducing unnecessary complexity.
Maintain the existing folder structure:
rental_contract_ai/
│── backend/                  # FastAPI backend
│   ├── main.py               # Main FastAPI application
│   ├── models.py             # Data models
│   ├── contract_parser.py    # Contract text extraction & analysis
│   ├── chatbot.py            # Chatbot logic (LangChain & AI)
│   ├── requirements.txt      # Backend dependencies
│   ├── uploads/              # Uploaded PDFs
│── frontend/                 # Streamlit frontend
│   ├── app.py                # Streamlit UI
│   ├── requirements.txt      # Frontend dependencies
│── .gitignore                # Ignore unnecessary files
│── README.md                 # Project documentation
│── setup.sh                  # (Optional) Script to set up environment
