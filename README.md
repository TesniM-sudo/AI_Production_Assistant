# AI Production Assistant

An AI-powered production assistant based on **Retrieval-Augmented Generation (RAG)**, designed to help operators retrieve relevant information from internal production documentation and interact with it through a conversational interface.

The system combines document ingestion, semantic search, vector storage, authentication, conversation management, and local language-model generation to provide context-aware answers.

## Overview

The AI Production Assistant is designed for industrial environments where operators need fast access to information contained in production and technical documentation.

Instead of relying only on a language model's pre-trained knowledge, the system retrieves relevant document content and uses it as context when generating responses.

### Main workflow

```text
Production Documents
        │
        ▼
   Document Ingestion
        │
        ▼
   Text Extraction
        │
        ▼
   Text Chunking
        │
        ▼
   Embeddings Generation
        │
        ▼
   Vector Database
        │
        ▼
     User Query
        │
        ▼
   Semantic Retrieval
        │
        ▼
 Retrieved Context
        │
        ▼
 Local LLM Generation
        │
        ▼
     AI Response
```

## Key Features

* **Retrieval-Augmented Generation (RAG)**

  * Retrieves relevant information from internal documents before generating an answer.
* **Semantic document search**

  * Uses embeddings to identify relevant document content based on meaning rather than exact keyword matching.
* **Vector storage**

  * Stores document embeddings for efficient similarity-based retrieval.
* **Local AI processing**

  * Supports local model generation through Ollama.
* **User authentication**

  * Provides authentication and password hashing.
* **Conversation management**

  * Stores and manages user conversations.
* **Web interface**

  * Provides a browser-based interface for interacting with the assistant.
* **REST API**

  * Backend services are exposed through FastAPI endpoints.

## Technologies

| Component            | Technology                     |
| -------------------- | ------------------------------ |
| Backend              | FastAPI                        |
| API Server           | Uvicorn                        |
| Programming Language | Python                         |
| RAG                  | Retrieval-Augmented Generation |
| Embeddings           | Sentence Transformers          |
| Vector Database      | ChromaDB                       |
| LLM Runtime          | Ollama                         |
| Database             | PostgreSQL                     |
| Document Processing  | PyMuPDF                        |
| Authentication       | bcrypt                         |
| Frontend             | HTML / CSS / JavaScript        |
| Containerization     | Docker Compose                 |
| Version Control      | Git / GitHub                   |

## Project Structure

```text
AI_Production_Assistant/
│
├── backend/
│   └── app/
│       ├── api/
│       │   └── v1/
│       │       └── endpoints/
│       │           ├── auth.py
│       │           └── chat.py
│       │
│       ├── db/
│       │   └── database.py
│       │
│       ├── rag/
│       │   ├── generator.py
│       │   ├── ingestion.py
│       │   └── vector_store.py
│       │
│       ├── services/
│       │   ├── auth.py
│       │   └── conversation.py
│       │
│       ├── static/
│       │   └── index.html
│       │
│       └── main.py
│
├── compose/
│   └── docker-compose.yml
│
├── frontend/
│   └── index.html
│
├── requirements.txt
├── .gitignore
└── README.md
```

## RAG Pipeline

The RAG pipeline consists of several stages.

### 1. Document ingestion

Production documents are processed and their textual content is extracted.

The project uses **PyMuPDF** for PDF document processing.

### 2. Text processing

Extracted content is divided into smaller chunks suitable for embedding and retrieval.

### 3. Embedding generation

The project uses **Sentence Transformers** to transform text chunks into numerical vector representations.

These embeddings allow the system to compare the semantic similarity between a user query and stored document content.

### 4. Vector storage

The generated embeddings are stored in **ChromaDB**.

When a user submits a question, the system searches the vector database for the most relevant document chunks.

### 5. Context retrieval

The retrieved chunks are provided as contextual information for the language model.

### 6. Response generation

The system sends the user question together with the retrieved context to a locally running language model through **Ollama**.

The generated response is then returned to the user through the FastAPI backend.

## Backend Architecture

The backend follows a modular structure separating API endpoints, services, database access, and RAG components.

```text
FastAPI
   │
   ├── Authentication API
   │
   ├── Chat API
   │
   ├── Conversation Service
   │
   └── RAG
        ├── Ingestion
        ├── Vector Store
        └── Generator
```

This separation makes the application easier to maintain and extend.

## Installation

### 1. Clone the repository

```bash
git clone git@github.com:TesniM-sudo/AI_Production_Assistant.git
cd AI_Production_Assistant
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

The application uses environment variables for configuration and sensitive information.

Create a `.env` file locally:

```env
DATABASE_URL=your_database_connection_string
POSTGRES_DB=your_database_name
POSTGRES_USER=your_database_user
POSTGRES_PASSWORD=your_database_password
```

**Do not commit `.env` to GitHub.**

The repository's `.gitignore` excludes environment files and other local development files.

## Running the Application

Start the FastAPI application with:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

The application can then be accessed through:

```text
http://localhost:8000
```

The API documentation is available through FastAPI's automatically generated documentation:

```text
http://localhost:8000/docs
```

## Docker Compose

The project also contains a Docker Compose configuration under:

```text
compose/docker-compose.yml
```

It can be used to manage supporting services such as PostgreSQL.

```bash
docker compose -f compose/docker-compose.yml up -d
```

## API

The backend exposes REST API endpoints under:

```text
/api/v1/
```

The current API includes functionality related to:

* Authentication
* Chat
* Conversations
* User interaction with the RAG assistant

Detailed endpoint documentation can be explored through the FastAPI Swagger interface at:

```text
/docs
```

## Security

The project follows several basic security practices:

* Environment variables are used for sensitive configuration.
* `.env` files are excluded from version control.
* Passwords are hashed using bcrypt.
* Authentication-related functionality is separated from the main application logic.
* Sensitive local development files are excluded through `.gitignore`.

Private credentials, API keys, passwords, and private SSH keys should never be committed to the repository.

## Future Improvements

Potential future improvements include:

* Agentic RAG capabilities
* Improved document chunking and retrieval strategies
* Retrieval evaluation and benchmarking
* Reranking of retrieved documents
* Better source citation in generated answers
* Expanded document formats
* Role-based access control
* Monitoring and logging
* Automated testing
* Improved frontend user experience
* Deployment automation

## Project Context

This project was developed as part of an internship focused on **Artificial Intelligence, Natural Language Processing, and Retrieval-Augmented Generation** for an industrial production-assistance use case.

## License

No open-source license has currently been specified for this project.
