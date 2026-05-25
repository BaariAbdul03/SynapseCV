<div align="center">

<img src="https://img.shields.io/badge/SynapseCV-Live-7c3aed?style=for-the-badge&logo=render&logoColor=white" />
<img src="https://img.shields.io/badge/Python-3.11.9-3776ab?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Flask-3.1.0-000000?style=for-the-badge&logo=flask&logoColor=white" />
<img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ecf8e?style=for-the-badge&logo=supabase&logoColor=white" />
<img src="https://img.shields.io/badge/Gemini-AI-4285f4?style=for-the-badge&logo=google&logoColor=white" />

# ⚡ SynapseCV

### AI-Powered Resume Intelligence Platform

**Parse, score, and analyse candidate resumes at scale — powered by Google Gemini AI.**

🌐 **[Live Demo → synapsecv.onrender.com](https://synapsecv.onrender.com/)**

</div>

---

## 📌 Overview

SynapseCV is a production-grade, AI-powered resume parsing platform built for modern recruiters and HR teams. Upload candidate resumes in bulk, match them against custom job descriptions, and receive structured, scored intelligence reports — all in seconds.

The platform uses **Google Gemini 2.5 Flash** with an automatic fallback to Gemini 2.0 Flash Lite, structured JSON parsing, exponential retry logic, and a strict penalty-based scoring algorithm to deliver consistent, industry-standard analysis.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Resume Parsing** | Extracts name, email, phone, GitHub, LinkedIn, education, and skills automatically |
| 📊 **Intelligent Scoring** | Penalty-based algorithm scores candidates 0–100 against a target role |
| 📋 **Job Description Matching** | Match resumes against custom JDs or choose from 15 curated role templates |
| 📂 **Bulk Processing** | Upload and analyse multiple candidate PDFs concurrently |
| 🗄️ **Candidate Archives** | Persistent result history saved to Supabase PostgreSQL |
| 🔑 **Developer REST API** | Full public API with Stripe-style API key authentication |
| 🔐 **Google OAuth** | One-click sign-in with Google, backed by Authlib |
| 🛡️ **Security Hardened** | Talisman CSP headers, rate limiting, MIME-type validation, and HTTPS enforcement |
| 🌙 **Persistent Database** | Background keep-alive daemon prevents Supabase free-tier sleep |
| 📄 **PDF Export** | Export structured analysis reports as PDF documents |

---

## 🏗️ Architecture

```
synapsecv/
├── app/
│   ├── __init__.py          # Application factory (ProxyFix, keep-alive, DB init)
│   ├── config.py            # Environment-specific configs (Dev, Prod, Test)
│   ├── extensions.py        # Centralised Flask extension instances
│   ├── models.py            # SQLAlchemy ORM: User, Analysis, ApiKey, RoleTemplate
│   ├── routes/
│   │   ├── auth.py          # Google OAuth + traditional login/register
│   │   ├── web.py           # Web UI routes + role library API
│   │   ├── parse.py         # PDF parsing & Gemini AI analysis endpoints
│   │   └── api.py           # Public REST API (API key-authenticated)
│   ├── services/
│   │   ├── gemini_service.py  # Gemini AI client with retry & fallback logic
│   │   ├── pdf_service.py     # PDF text extraction via pdfplumber
│   │   └── role_library.py    # 15 curated industry job description templates
│   └── utils/
│       ├── validators.py    # PDF MIME-type validation (native + magic fallback)
│       ├── keep_alive.py    # Supabase database keep-alive daemon
│       └── logging.py       # Structured logging with structlog
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JS, and SVG assets
├── tests/                   # pytest test suite (12 tests)
├── run.py                   # Production WSGI entry point
├── Procfile                 # Render/Heroku process definition
├── .python-version          # Pins Python 3.11.9
└── requirements.txt         # All Python dependencies
```

---

## 🧠 AI Scoring Algorithm

SynapseCV uses a **Strict Penalty System** rather than vague AI scores:

1. **Start** with a base score of **100**
2. **Deduct –25** for a critical foundational skill gap (e.g. a backend dev missing SQL)
3. **Deduct –10** for vague, unquantified experience bullet points
4. **Deduct –5** for poor formatting or missing contact information
5. **Final score** = 100 − total deductions (minimum: 0)

The AI is explicitly instructed that `match_percentage` in the JSON output **must exactly equal** the score computed in its `scoring_reasoning` text — eliminating inconsistencies.

---

## 🚀 Getting Started (Local Development)

### Prerequisites

- Python 3.11+
- A [Google Gemini API Key](https://aistudio.google.com/)
- (Optional) A [Supabase](https://supabase.com/) project for PostgreSQL

### 1. Clone the repository

```bash
git clone https://github.com/BaariAbdul03/Resume-Parser.git
cd Resume-Parser
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

```env
# .env
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Leave blank to use SQLite locally, or add Supabase URL for PostgreSQL
DATABASE_URL=

# Google OAuth (optional for local dev — app runs in Sandbox Mode without these)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

### 5. Run the development server

```bash
python run.py
```

The app will be available at `http://localhost:5000`.

> **Note**: Without `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`, the app runs in **Sandbox Mode** — a developer-friendly simulated OAuth flow so you can test the full platform locally.

---

## 🌐 Production Deployment (Render)

### Required Environment Variables (Render Dashboard → Environment)

| Variable | Description |
|---|---|
| `FLASK_ENV` | Set to `production` |
| `SECRET_KEY` | A strong random secret (generate with `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | Supabase Transaction Pooler connection string (port **6543**) |
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret |
| `PYTHON_VERSION` | `3.11.9` |

### Google OAuth Setup (Production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials
2. Create an **OAuth 2.0 Client ID** (Web application)
3. Add **Authorized redirect URI**: `https://your-service-name.onrender.com/auth/oauth/google/authorize`
4. Copy Client ID and Secret into Render environment variables

### Supabase Setup

1. Create a new project at [supabase.com](https://supabase.com/)
2. Go to **Project Settings → Database → Connection Pooling**
3. Copy the **Transaction Mode** connection string (port `6543`)
4. Set it as `DATABASE_URL` in Render — the app auto-creates all tables on first boot

---

## 🔌 Developer REST API

SynapseCV exposes a public REST API for programmatic resume parsing.

### Authentication

Generate an API key from the **Developer Portal** tab in the application, then pass it in request headers:

```http
X-API-Key: scv_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Endpoints

#### `POST /api/v1/parse`
Parse a single resume PDF and score it against an optional job description.

```bash
curl -X POST https://synapsecv.onrender.com/api/v1/parse \
  -H "X-API-Key: scv_live_your_key_here" \
  -F "resume=@candidate_cv.pdf" \
  -F "job_description=We are looking for a Python backend engineer..."
```

**Response**
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+1 555 000 1234",
  "github_url": "https://github.com/janedoe",
  "linkedin_url": "https://linkedin.com/in/janedoe",
  "education": ["B.Tech — Computer Science, MIT, 2022"],
  "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "detected_role": "Backend Engineer",
  "match_percentage": 85,
  "missing_keywords": ["Kubernetes", "Redis"],
  "profile_summary": "Strong backend engineer with solid API and database fundamentals...",
  "scoring_reasoning": "Started at 100. Deducted 10 for missing cloud experience. Deducted 5 for no metrics. Final: 85.",
  "db_id": 42
}
```

#### `GET /api/v1/results/{result_id}`
Retrieve a previously saved analysis by its database ID.

📖 **Interactive API Docs**: [synapsecv.onrender.com/api/docs](https://synapsecv.onrender.com/api/docs)

---

## 🧪 Running Tests

```bash
pytest
```

The test suite covers API endpoints, Gemini service resilience, PDF extraction, and MIME validation — **12 tests, all passing**.

---

## 🛡️ Security

- **Talisman** enforces strict Content Security Policy headers and HTTPS
- **MIME-type validation** uses native `%PDF` binary header checking (no OS dependencies)
- **Rate limiting** via Flask-Limiter prevents abuse of parsing and API endpoints  
- **Session cookies** are marked `Secure`, `HttpOnly`, and `SameSite=Lax`
- **API keys** are stored as SHA-256 hashes — plaintext is shown only once at generation
- **Werkzeug ProxyFix** ensures correct HTTPS scheme resolution behind Render's reverse proxy

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Flask 3.1, Python 3.11 |
| **AI Engine** | Google Gemini 2.5 Flash (+ 2.0 Flash Lite fallback) |
| **Database** | Supabase PostgreSQL (via psycopg2-binary + NullPool) |
| **ORM** | Flask-SQLAlchemy 3.1, Flask-Migrate |
| **Auth** | Flask-Login, Authlib (Google OAuth 2.0) |
| **Security** | Flask-Talisman (CSP), Flask-Limiter, Flask-CORS |
| **PDF Parsing** | pdfplumber, pdfminer.six |
| **API** | Flask-Smorest, Marshmallow, Pydantic |
| **Structured Logging** | structlog |
| **Server** | Gunicorn (WSGI) |
| **Hosting** | Render |
| **Testing** | pytest, pytest-flask |

---

## 📄 Licence

This project is open source and available under the [MIT Licence](LICENSE).

---

<div align="center">

Built with ⚡ by [BaariAbdul03](https://github.com/BaariAbdul03)

🌐 **[synapsecv.onrender.com](https://synapsecv.onrender.com/)**

</div>
