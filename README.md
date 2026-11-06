# 🏛️ Indian Law Acts RAG Chatbot

A production-grade Retrieval-Augmented Generation (RAG) system built on **10,860+ Indian Legislative Acts** from the India Code repository. This intelligent legal assistant combines advanced NLP, multi-lingual OCR, and conversational AI to provide accurate, context-aware answers to complex legal queries.

The live project is hosted at: [india-law-a-rag](https://lawbot-frontend.netlify.app/)

---

## Local setup for this checkout

The local Python environment, CPU embedding dependencies, MongoDB binary, and private
`backend/.env` configuration are prepared in this workspace. Service data and model
caches stay under `.local/`; the Chroma index stays under `backend/chroma_db/`.

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey)
   and put it in `backend/.env` as `GOOGLE_API_KEY=...`. Keep this file private.
   `GOOGLE_MODEL` defaults to `gemini-3.5-flash-lite` and can be changed there.
2. Build the starter index, without needing a Gemini key:
   ```bash
   backend/.venv/bin/python scripts/index_local.py
   ```
   This indexes the **RTI Act PDF from the Central Information Commission** and
   **two CGST Act PDFs from the GST Council** (the 2017 Act and the Jammu and
   Kashmir extension Act). It is a starter corpus for testing, not a complete or
   verified-current Indian law collection. To index your own text-based PDFs, use:
   ```bash
   backend/.venv/bin/python scripts/index_local.py --pdf-dir /absolute/path/to/pdfs
   ```
   Scanned PDFs need the original OCR pipeline and Tesseract with English/Hindi
   language data. Repeated indexing of the same PDF uses stable IDs.
3. Start local services from the repository root:
   ```bash
   bash scripts/start_local.sh
   ```
   Frontend: <http://127.0.0.1:8081> · API docs: <http://127.0.0.1:8000/docs>
   Stop an earlier running app before starting another. Ctrl+C stops services
   started by this script; an already-running MongoDB instance is reused.
   To open the app from another computer on the same Wi-Fi, set
   `VITE_API_BASE_URL=/api` in `frontend/.env`, then start with:
   ```bash
   FRONTEND_HOST=0.0.0.0 bash scripts/start_local.sh
   ```
   Open `http://<this-computer-LAN-IP>:8081` on the other computer. The Vite proxy
   forwards API requests; MongoDB and FastAPI keep listening on localhost.
4. Register your own account in the frontend. Without the Gemini key, registration,
   login, and conversations work; chat returns a clear setup error. After changing
   the key, restart the backend. Check <http://127.0.0.1:8000/> for configuration status.

Local admin preview: open <http://127.0.0.1:8081/admin/>. It uses a separate
sign-in page at <http://127.0.0.1:8081/admin/login/> and a separate admin
session from the chat app. Sign in with
`covakeel@gmail.com`. The generated local-only password is stored in
`.local/admin-access.txt` (mode 600); do not paste it into chat or commit it.
The admin dashboard has Overview, Legal Knowledge Management, Knowledge base,
Users, Conversations, System health, and Settings. Admins can upload text-based
PDFs up to 20 MB. The backend indexes them in the existing Chroma collection;
re-uploading the same filename replaces its earlier passages for new answers.
Scanned PDFs need OCR before upload. Removing a document removes its passages
from future retrieval, while existing chat history remains as it was.
Admin permission is stored in MongoDB and cannot be gained through signup.
This admin work is local only; it has not been deployed to the Hostinger VPS.

Backend regression checks:
```bash
cd backend
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip check
```

`backend/requirements-local.lock.txt` records the resolved Ubuntu 24.04 / Python 3.12
packages, including CPU PyTorch. MongoDB logs are in `.local/logs/mongodb.log`.
The starter source is <https://cic.gov.in/sites/default/files/RTI_English.pdf>.

## 🎯 Project Overview

This project represents a sophisticated RAG implementation that goes beyond basic Q&A systems. It tackles the unique challenges of processing Indian legal documents—spanning multiple languages (English and Hindi), diverse formats, and complex legislative structures—to deliver a production-ready legal chatbot.

---

## 🚀 Technical Highlights

### 1. **Large-Scale Web Scraping Pipeline**
- **10,863 Legislative Act URLs** extracted from indiacode.nic.in using BeautifulSoup
- **CloudScraper integration** to bypass anti-bot protection mechanisms and Cloudflare challenges
- **Concurrent downloading** with ThreadPoolExecutor (15 workers) for parallel PDF acquisition

### 2. **Advanced Multi-Modal Document Processing**

#### Language Detection System
- **Hybrid language detection** using Lingua library on middle-page sampling for efficiency
- Analyzes **middle 3 pages** of each PDF to determine language (Hindi vs. English) before processing
- **Bilingual support** for English and Hindi legal documents

#### Dual-Path Text Extraction
- **PyMuPDF (fitz)** for native text extraction from digitally-created PDFs
- **Pytesseract OCR** with Tesseract engine for scanned documents (300 DPI, optimized threading)
- **Automatic fallback mechanism**: Attempts direct extraction first, falls back to OCR if text extraction yields insufficient results
- **Page-limited OCR** (first 100 pages) to balance accuracy with processing time

#### Sophisticated Text Cleaning Pipeline
- **12-stage text sanitization** including:
  - Unicode normalization (NFC) for consistent character representation
  - Removal of PDF artifacts `(cid:NN)` and gibberish tokens
  - Hyphenation repair for line-broken words
  - Sentence reconstruction across line breaks
  - Devanagari-Latin script isolation for removing mixed-script artifacts
  - Token-level gibberish filtering (alphanumeric ratio analysis)
  - Section marker injection for hierarchical document structure `[SEC_N]`
  - Phrase deduplication to eliminate OCR repetition errors

### 3. **Intelligent Document Chunking & Metadata Enrichment**

- **RecursiveCharacterTextSplitter** with optimal parameters:
  - Chunk size: 2000 characters
  - Overlap: 500 characters for context continuity

- **Rich metadata extraction**:
  - Act year parsing from filenames (multiple regex patterns)
  - Act number extraction from document content
  - Keywords extraction (amendment, section, court, etc.)
  - Date pattern recognition
  - Source tracking with chunk position information
  - Document length statistics

- **Chunking intelligence**: Documents exceeding 2000 chars are intelligently split with metadata propagation across chunks

### 4. **High-Performance Vector Store Architecture**

#### Embedding Model
- **Sentence-Transformers** with `all-MiniLM-L6-v2` model:
  - 384-dimensional embeddings
  - Normalized embeddings for cosine similarity
  - CPU-optimized inference (GPU-ready)
  - Multilingual support for English-Hindi legal corpus

#### ChromaDB Implementation
- **Persistent vector storage** with collection-based organization (`indian_law_acts`)
- **Batch processing** (500 documents/batch) to manage memory efficiently
- **Incremental indexing** allowing resume after interruptions
- **Metadata-rich storage** preserving act names, years, keywords, and source references
- Generated vector store typically **3-5 GB** for full corpus

### 5. **Conversational RAG with Memory**

#### History-Aware Retrieval
- **LangChain's create_history_aware_retriever** for contextual query reformulation
- Standalone question generation from conversational context
- **Dynamic chat history** maintained across user sessions

#### Retrieval Strategy
- **Similarity search** with top-10 document retrieval (k=10)
- Context window optimization for LLM processing
- **Google Gemini 2.5-flash** as the LLM backbone:
  - Temperature: 0.4 for balanced creativity and accuracy
  - System message to human message conversion for compatibility

#### Conversation Buffer Memory
- **Persistent conversation state** using LangChain's ConversationBufferMemory
- Message history stored as `HumanMessage` and `AIMessage` objects
- Session-aware context for follow-up queries

### 6. **Asynchronous Backend Architecture**

- **FastAPI** with async/await patterns throughout
- **Thread pool executor** (4 workers) for blocking RAG operations
- **Non-blocking streaming responses** with Server-Sent Events (SSE)
- **Background task processing** for database persistence during streaming
- **Concurrent request handling** with event loop optimization
- **MongoDB Motor** for async database operations

### 7. **Production-Ready Features**

#### API Design
- RESTful API with OpenAPI documentation (Swagger UI at `/docs`)
- JWT authentication with secure password hashing (bcrypt)
- User-conversation-message relationship modeling
- Source document tracking for transparency

#### Streaming Chat
- **Word-by-word streaming** for better UX (20ms delay between words)
- Background response persistence without blocking streaming
- SSE (Server-Sent Events) with proper headers for real-time communication

#### Error Handling & Resilience
- Comprehensive error categorization during PDF downloading
- Progress persistence with JSON checkpointing
- Resume capability after interruptions
- Graceful degradation with fallback mechanisms

#### Monitoring & Logging
- Detailed logging with file and console handlers
- Processing statistics (time, throughput, success rate)
- Metadata summaries for corpus insights

---

## 📊 System Statistics

- **Total Legislative Acts**: 10,863 documents
- **Supported Languages**: English (EN), Hindi (HI)
- **Vector Store Size**: ~3-5 GB
- **Document Chunks**: Variable (depends on act length, ~50,000+ chunks)
- **Embedding Dimensions**: 384
- **Average Processing Time**: ~10-30 seconds per document (OCR path)
- **Retrieval Latency**: <2 seconds for top-10 similar documents

---

## 📸 Screenshots

<p align="center">
  <i>Add screenshots of your frontend here showing:</i>
</p>

<p align="center">
  <i>1. Landing page with project overview</i><br>
  <img src="screenshots/landing.png" alt="Landing Page" width="600">
</p>

<p align="center">
  <i>2. Login and Authentication</i><br>
  <img src="screenshots/login.png" alt="Login Page" width="600">
</p>

<p align="center">
  <i>3. Chat interface with conversation history</i><br>
  <img src="screenshots/chat.png" alt="Chat Interface" width="600">
</p>

<!-- <p align="center">
  <i>3. Query results with source document references</i><br>
  <img src="screenshots/sources.png" alt="Source Documents" width="600">
</p> -->

<p align="center">
  <i>4. User profile and conversation management</i><br>
  <img src="screenshots/profile.png" alt="User Profile" width="600">
</p>

---

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern async Python web framework
- **LangChain**: RAG pipeline orchestration
- **ChromaDB**: Vector database for semantic search
- **Sentence-Transformers**: Embedding generation
- **Google Gemini AI**: Large language model
- **MongoDB**: NoSQL database for user data & conversations
- **Motor**: Async MongoDB driver
- **PyMuPDF (fitz)**: PDF text extraction
- **Pytesseract**: OCR engine for scanned documents
- **Lingua**: Language detection library

### Frontend
- **React**: UI library
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Reusable component library
- **Bun**: JavaScript runtime & package manager

### Infrastructure
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy for frontend
- **Conda**: Python environment management

---

## 📋 Prerequisites

- **Conda** (Miniconda or Anaconda)
- **Python 3.10+**
- **MongoDB** (for local setup) or Docker
- **Tesseract OCR** (for document processing)
- **Poppler** (for PDF to image conversion)
- **Node.js 18+** or **Bun** (for frontend)
- **Google API Key** (for Gemini AI)
- **Docker & Docker Compose** (for containerized deployment)

### Install System Dependencies

#### macOS
```bash
brew install tesseract poppler
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-hin poppler-utils
```

#### Windows
Download and install:
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: http://blog.alivate.com.au/poppler-windows/

---

## 🚀 Setup Guide

### Part 1: Vector Store Creation (One-Time Setup)

This step processes all 10,860+ Indian Acts PDFs and creates the vector database. **This needs to be done once** and can take several hours depending on your machine.

#### Step 1: Create Conda Environment
```bash
# Create a new conda environment
conda create -n india-law-rag python=3.10 -y
conda activate india-law-rag
```

#### Step 2: Install Python Dependencies
```bash
# Navigate to backend directory
cd backend

# Install requirements
pip install -r requirements.txt

# Also install Jupyter for running the downloader notebook
pip install jupyter notebook
```

#### Step 3: Download PDF Documents
```bash
# Navigate to pdf-downloading directory
cd ../vector-store/pdf-downloading

# Start Jupyter Notebook
jupyter notebook

# Open pdfs_downloader.ipynb in your browser and run all cells
# This will:
# - Load 10,863 act URLs from acts.json
# - Download PDFs using parallel scraping (15 workers)
# - Save PDFs to ./acts_pdf/ folder
# - Takes ~2-4 hours depending on network speed
```

**Alternative (without Jupyter):**
```bash
# Convert notebook to Python script and run
jupyter nbconvert --to script pdfs_downloader.ipynb
python pdfs_downloader.py
```

#### Step 4: Preprocess PDFs (OCR & Text Extraction)
```bash
# Navigate to preprocessing directory
cd ../pdfs_preprocessing

# Copy the downloaded PDFs folder here
cp -r ../pdf-downloading/acts_pdf ./

# Run the preprocessor (this will take 6-12 hours)
python pdf_processor.py

# This will create processed_documents_acts.json (~500-800 MB)
# The JSON contains cleaned, OCR-processed text from all PDFs
```

**What happens during preprocessing:**
- Language detection (English vs Hindi)
- Dual-path extraction (PyMuPDF or OCR)
- 12-stage text cleaning pipeline
- Metadata enrichment
- Progress checkpointing (can resume if interrupted)

#### Step 5: Create Vector Store
```bash
# Navigate to vector store creation directory
cd ../vector_store_creation

# Copy the processed JSON here
cp ../pdfs_preprocessing/processed_documents_acts.json ./

# Run the vector store creator
python vector_store_creator.py

# This creates ./chroma_db folder (3-5 GB)
# Processing time: ~2-4 hours
```

**What happens during vector store creation:**
- Document chunking (2000 chars, 500 overlap)
- Embedding generation using all-MiniLM-L6-v2
- ChromaDB indexing with metadata
- Batch processing for memory efficiency

#### Step 6: Preserve Vector Store
```bash
# The chroma_db folder is critical - back it up!
# You'll need this for both local and Docker deployments

# For local setup: copy to backend
cp -r ./chroma_db ../../backend/

# For Docker setup: keep it safe, you'll mount/copy it later
```

---

### Part 2A: Local Development Setup

#### Step 1: Backend Setup
```bash
# Navigate to backend directory
cd backend

# Ensure conda environment is activated
conda activate india-law-rag

# Ensure chroma_db is present
ls chroma_db  # Should show the vector database files

# Start MongoDB (if not already running)
# macOS:
brew services start mongodb-community

# Ubuntu/Debian:
sudo systemctl start mongod

# Create .env file
cat > .env << EOF
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=india_law_ai_rag
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
GOOGLE_API_KEY=your-google-gemini-api-key-here
ENVIRONMENT=development
EOF

# Run the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Backend will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

#### Step 2: Frontend Setup
```bash
# Open a new terminal
cd frontend

# Install dependencies
npm install
# OR using Bun (faster)
bun install

# Create .env file
cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
EOF

# Run the frontend
npm run dev
# OR using Bun
bun run dev

# Frontend will be available at http://localhost:5173
```

#### Step 3: Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

### Part 2B: Docker Deployment

#### Step 1: Prepare Environment File
```bash
# Navigate to project root
cd /path/to/india-law-ai-rag

# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your favorite editor
```

**Required environment variables:**
```env
# MongoDB Configuration
MONGO_ROOT_USERNAME=admin
MONGO_ROOT_PASSWORD=your-secure-password
MONGO_DB=india_law_ai_rag

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Google AI Configuration
GOOGLE_API_KEY=your-google-gemini-api-key-here

# Application Configuration
ENVIRONMENT=production
VITE_API_BASE_URL=http://localhost:8000
```

#### Step 2: Build and Start Services
```bash
# Build and start all services
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Services will be available at:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8000
# - MongoDB: localhost:27019
```

#### Step 3: Copy Vector Store into Backend Container

**Option A: Copy before starting (Recommended)**
```bash
# Stop services if running
docker-compose down

# Ensure chroma_db is in the backend directory
cp -r vector-store/vector_store_creation/chroma_db backend/

# Add to backend/.dockerignore to exclude from build context if needed
# Then start services
docker-compose up -d --build
```

**Option B: Copy to running container**
```bash
# Copy chroma_db into running backend container
docker cp vector-store/vector_store_creation/chroma_db india-law-ai-backend:/app/

# Restart the backend service to reload
docker-compose restart backend
```

**Option C: Docker volume mount (for development)**
```bash
# Modify docker-compose.yml backend service volumes:
volumes:
  - ./backend/chroma_db:/app/chroma_db:ro

# Then start services
docker-compose up -d
```

#### Step 4: Verify Deployment
```bash
# Check backend health
curl http://localhost:8000/

# Check frontend
curl http://localhost:3000/

# View backend logs to ensure vector store loaded
docker-compose logs backend | grep -i "chroma"
```

#### Step 5: Stop and Cleanup
```bash
# Stop services
docker-compose down

# Remove volumes (WARNING: deletes MongoDB data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## 📁 Project Structure

```
india-law-ai-rag/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── controllers/               # API request handlers
│   │   │   ├── auth_controller.py
│   │   │   ├── chat_controller.py     # Chat & streaming endpoints
│   │   │   ├── conversation_controller.py
│   │   │   └── message_controller.py
│   │   ├── services/                  # Business logic layer
│   │   │   ├── rag_service.py         # RAG orchestration & threading
│   │   │   ├── retrieval_service.py   # Conversational RAG core
│   │   │   ├── auth_service.py
│   │   │   └── conversation_service.py
│   │   ├── models/                    # MongoDB ODM models
│   │   ├── schemas/                   # Pydantic validation schemas
│   │   ├── routes/                    # API route definitions
│   │   ├── core/                      # Security & config
│   │   ├── db/                        # Database connection
│   │   └── utils/                     # JWT & hashing utilities
│   ├── chroma_db/                     # Vector store (created after setup)
│   ├── requirements.txt               # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/                # React components
│   │   │   ├── Chat.tsx               # Main chat interface
│   │   │   ├── AppSidebar.tsx         # Conversation sidebar
│   │   │   └── ui/                    # Shadcn/ui components
│   │   ├── hooks/                     # Custom React hooks
│   │   │   ├── useAuth.tsx
│   │   │   └── useConversations.tsx
│   │   ├── pages/                     # Route pages
│   │   └── lib/                       # Utilities
│   ├── package.json
│   └── Dockerfile
├── vector-store/
│   ├── pdf-downloading/
│   │   ├── acts.json                  # 10,863 act URLs
│   │   └── pdfs_downloader.ipynb      # Web scraping notebook
│   ├── pdfs_preprocessing/
│   │   └── pdf_processor.py           # OCR & text cleaning
│   └── vector_store_creation/
│       └── vector_store_creator.py    # ChromaDB indexing
├── docker-compose.yml                 # Multi-container orchestration
├── .env.example                       # Environment template
└── README.md
```

---

## 🔍 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Conversations
- `GET /conversations` - List user's conversations
- `POST /conversations` - Create new conversation
- `DELETE /conversations/{id}` - Delete conversation

### Chat
- `POST /chat/` - Send message and get AI response
- `POST /chat/stream` - Send message and stream AI response
- `GET /chat/test-concurrent` - Test concurrent handling

### Messages
- `GET /messages/{conversationId}` - Get conversation messages

---

## 🔧 Configuration

### Backend Configuration
Edit `backend/.env`:
```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=india_law_ai_rag

# JWT Secret (generate a secure random string)
JWT_SECRET_KEY=<your-secret-key>

# Google Gemini API Key (get from https://makersuite.google.com/app/apikey)
GOOGLE_API_KEY=<your-api-key>

# Environment
ENVIRONMENT=development
```

### Frontend Configuration
Edit `frontend/.env`:
```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000
```

### RAG System Configuration
Edit `backend/app/services/retrieval_service.py`:
```python
# Retrieval settings
search_type="similarity"  # or "mmr" for diversity
search_kwargs={"k": 10}   # Top-K documents

# LLM settings
model="gemini-2.5-flash"  # or "gemini-2.5-pro"
temperature=0.4           # 0.0-1.0 (lower = more focused)

# Chunking settings (in vector_store_creator.py)
chunk_size=2000          # Characters per chunk
chunk_overlap=500        # Overlap between chunks
```

---

## 🐛 Troubleshooting

### Issue: Vector store not found
```bash
# Ensure chroma_db exists in backend directory
ls backend/chroma_db

# If missing, copy from vector-store creation
cp -r vector-store/vector_store_creation/chroma_db backend/
```

### Issue: MongoDB connection failed
```bash
# Check if MongoDB is running
mongosh  # Should connect successfully

# Check connection string in .env
# For Docker: mongodb://username:password@mongodb:27017
# For local: mongodb://localhost:27017
```

### Issue: Tesseract not found during PDF processing
```bash
# Install Tesseract with language packs
# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-hin

# Verify installation
tesseract --version
```

### Issue: Out of memory during vector store creation
```python
# Reduce batch size in vector_store_creator.py
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 100))  # Default was 500

# Or set environment variable
export BATCH_SIZE=100
python vector_store_creator.py
```

### Issue: Slow PDF processing
```bash
# Enable GPU for PyTorch (if available)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Adjust workers in pdf_processor.py
MAX_WORKERS = 10  # Increase for more parallelism (default: 5)
```

### Issue: Frontend can't connect to backend
```bash
# Check CORS settings in backend/app/main.py
# Ensure frontend URL is in allowed origins

# Verify .env file has correct API URL
cat frontend/.env
```

---

## 📈 Performance Optimization

### Vector Store Query Speed
- Use SSD storage for `chroma_db` folder
- Consider GPU acceleration for embedding generation
- Adjust `k` parameter in retrieval (lower = faster)

### PDF Processing Speed
- Increase `MAX_WORKERS` for parallel processing
- Use direct text extraction when possible (faster than OCR)
- Limit OCR to first N pages for very long documents

### API Response Time
- Enable caching for repeated queries
- Use streaming responses for better perceived performance
- Implement connection pooling for MongoDB

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **India Code (indiacode.nic.in)** for providing access to Indian legislative acts
- **LangChain** for the RAG framework
- **Google** for the Gemini AI model
- **ChromaDB** for efficient vector storage
- **Tesseract** for OCR capabilities

---

## 📞 Contact

**Developer**: Pankil Soni
**GitHub**: [@pankil-soni](https://github.com/pankil-soni)
**Project Repository**: [india-law-ai-rag](https://github.com/pankil-soni/india-law-ai-rag)

---

## 🌟 Star History

If you find this project useful, please consider giving it a star ⭐ on GitHub!

---

<p align="center">
  Made with ❤️ and ☕ by Pankil Soni
</p>
