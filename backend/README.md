# Indian Law Acts RAG Chatbot API

A FastAPI-based backend for a Retrieval-Augmented Generation (RAG) chatbot focused on Indian Law Acts. The API leverages vector search (ChromaDB), Google Gemini LLM, and LangChain to provide context-aware, conversational answers based on legal documents.

---

## Features

- **User Management**: Register, update, and delete users.
- **Authentication**: Secure JWT-based login.
- **Conversations**: Create, list, update, and delete chat conversations.
- **Messages**: Send, retrieve, and delete messages within conversations.
- **Chatbot**: Ask questions and receive contextually relevant answers using RAG.
- **Streaming**: Stream chatbot responses for real-time interaction.
- **Vector Search**: Uses ChromaDB for document retrieval.
- **LLM Integration**: Google Gemini for answer generation.

---

## Project Structure

```
.
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── routes/                # API route definitions
│   ├── controllers/           # Endpoint logic
│   ├── services/              # Business logic (RAG, user, message, etc.)
│   ├── models/                # Data models
│   ├── schemas/               # Pydantic schemas
│   ├── db/                    # Database utilities
│   ├── core/                  # Security, config
│   └── utils/                 # Utility functions
├── chroma_db/                 # Chroma vector store (ignored by git)
├── requirements.txt           # Python dependencies
└── .gitignore
```

---

## Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd indian-rag-api
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Create a `.env` file in the root directory and add your Google API key:
   ```
   GOOGLE_API_KEY=your-google-api-key
   ```

---

## Running the App

```bash
uvicorn app.main:app --reload
```

The API will be available at [http://localhost:8000](http://localhost:8000).

---

## API Overview

### Authentication

- `POST /auth/login` — Obtain JWT token

### Users

- `POST /users/register` — Register a new user
- `GET /users/{user_id}` — Get user details
- `PUT /users/{user_id}` — Update user
- `DELETE /users/{user_id}` — Delete user

### Conversations

- `POST /conversations/` — Create a conversation
- `GET /conversations/` — List user's conversations
- `GET /conversations/{conv_id}` — Get conversation details
- `PUT /conversations/{conv_id}` — Update conversation
- `DELETE /conversations/{conv_id}` — Delete conversation

### Messages

- `POST /messages/` — Send a message
- `GET /messages/by_conversation/{conv_id}` — List messages in a conversation
- `GET /messages/{msg_id}` — Get message details
- `DELETE /messages/{msg_id}` — Delete message

### Chatbot

- `POST /chat/` — Ask a question (returns answer)
- `POST /chat/stream` — Stream answer (real-time)

---

## Security

- Uses OAuth2 with JWT tokens for authentication.
- Most endpoints require a valid JWT token in the `Authorization: Bearer <token>` header.

---

## RAG System

- **Vector Store**: Uses ChromaDB (`chroma_db/` directory) for storing and retrieving document embeddings.
- **LLM**: Google Gemini (via `langchain-google-genai`).
- **Embeddings**: Sentence Transformers (`all-MiniLM-L6-v2`).
- **Retrieval**: Context-aware, history-augmented question answering.

---

## Development

- Linting, formatting, and type checking are recommended for contributions.
- The `.gitignore` is set up for Python, FastAPI, and common IDEs.

---

## License

[MIT](LICENSE) (or specify your license) 