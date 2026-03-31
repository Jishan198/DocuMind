# 🧠 DocuMind - Multi-Tenant AI Document Intelligence Platform

DocuMind is an enterprise-grade, Software-as-a-Service (SaaS) platform built with Django. It empowers businesses to upload, process, and query their internal knowledge bases using advanced Natural Language Processing and Retrieval-Augmented Generation (RAG). 

By leveraging **Gemini AI**, **pgvector**, and asynchronous background processing, DocuMind allows users to chat with their PDFs, DOCX files, and text documents in real-time, extracting precise insights instantly.

---

## ✨ Features

- **🏢 Multi-Tenant Architecture:** Secure data isolation between different organizations, allowing multiple businesses to use the platform simultaneously without data bleeding.
- **🔐 Robust Security & RBAC:** Object-level permissions using `django-guardian`, ensuring users can only access their organization's documents.
- **🤖 Retrieval-Augmented Generation (RAG):** Document-aware AI chat querying powered by `LangChain`, `Google Gemini`, and `pgvector` for highly accurate vector search.
- **⚡ Asynchronous Processing:** Heavy document parsing, text chunking, and vector embedding are offloaded to **Celery + Redis**, keeping the web interface blazingly fast.
- **🔥 Real-Time WebSocket Updates:** Live progress bars and status indicators for document ingestion, powered by **Django Channels** and `htmx`.
- **🛡️ Enterprise Hardened:** Complete with custom endpoint rate limiting (`django-ratelimit`), proactive input HTML sanitization (`bleach`), and comprehensive system audit logging.

## 🛠️ Technology Stack

**Backend & Data**
- **Framework:** Django 5.1 & Django REST Framework
- **Database:** PostgreSQL with `pgvector`
- **Background Tasks:** Celery & Redis
- **WebSockets:** Django Channels & Daphne (ASGI)

**AI & Search**
- **Orchestration:** LangChain
- **LLM Engine:** Google Gemini Pro

**Infrastructure & Deployment**
- **Containerization:** Docker & Docker Compose
- **Reverse Proxy:** NGINX
- **Database GUI:** pgAdmin 4

**Frontend**
- **Interactivity:** HTMX (for dynamic, single-page application feel without the JS bloat)
- **Styling:** CSS3 & HTML5

---

## 🚀 Local Development Setup

To run this project locally on your machine, follow these steps:

### Prerequisites:
- Python 3.12+
- Redis (running locally or via Docker)
- PostgreSQL with the `pgvector` extension installed.

### 1. Clone the repository
```bash
git clone https://github.com/YourUsername/DocuMind.git
cd DocuMind
```

### 2. Set up the Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file from the example template:
```bash
cp .env.example .env
```
Ensure you provide your database credentials and `GEMINI_API_KEY`.

### 4. Database Migrations
```bash
python manage.py migrate
```

### 5. Run the Application
You will need two terminal windows:
**Terminal 1 (Web Server):**
```bash
python manage.py runserver
```
**Terminal 2 (Celery Worker):**
```bash
celery -A config worker --loglevel=info --pool=solo
```

Navigate to `http://127.0.0.1:8000` to register your first organization and start querying!

---

## 🐳 Production Deployment (AWS & Docker)

Deploying DocuMind is handled entirely through Docker Compose, making it cloud-agnostic and incredibly simple.

1. Provision an **Ubuntu Server 24.04** on AWS EC2 (t3.small or larger recommended).
2. Install **Docker** and **Git**.
3. Clone this repository to the server.
4. Configure your `.env` file with secure passwords and your server's IP in `ALLOWED_HOSTS`.
5. Start the stack:
```bash
docker compose up -d --build
```
> The `entrypoint.sh` script will automatically handle collecting static files and applying migrations. NGINX will serve the application on port 80 and handle upgrading WebSocket connections automatically.
