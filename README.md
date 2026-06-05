# SentinelVision

AI-powered security video analytics platform with RAG-based natural language querying.

## Architecture

- **Backend**: FastAPI, Clean Architecture, PostgreSQL + pgvector, Redis, YOLOv8, OpenAI
- **Frontend**: React 18, TypeScript, Vite, Zustand, TailwindCSS
- **Infrastructure**: Docker, GitHub Actions CI/CD

## Quick Start

```bash
# 1. Clone
git clone [https://github.com/eminosmanatci/sentinel-vision.git](https://github.com/eminosmanatci/sentinel-vision.git)
cd sentinel-vision

# 2. Environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Start
make up

# 4. Access
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
# API: http://localhost:8000
```
