# SentinelVision

[![Backend CI](https://github.com/eminosmanatci/sentinel-vision/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/eminosmanatci/sentinel-vision/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/eminosmanatci/sentinel-vision/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/eminosmanatci/sentinel-vision/actions/workflows/frontend-ci.yml)

AI-powered security video analytics platform with RAG-based natural language querying.

## Tech Stack

| Layer          | Technology                                                            |
| -------------- | --------------------------------------------------------------------- |
| **Backend**    | Python, FastAPI, SQLAlchemy 2.0 (async), Alembic                      |
| **AI/ML**      | YOLOv8 (object detection), OpenAI GPT-4o-mini, text-embedding-3-small |
| **Database**   | PostgreSQL 16 + pgvector (1536-dim vector search)                     |
| **Task Queue** | Celery + Redis (background video processing)                          |
| **Frontend**   | React 18, TypeScript, Vite, Zustand, TailwindCSS                      |
| **DevOps**     | Docker, Docker Compose, GitHub Actions CI/CD                          |

## Architecture

┌─────────────┐ ┌─────────────┐ ┌─────────────────┐
│ React │────▶│ FastAPI │────▶│ PostgreSQL+ │
│ (Vite/TS) │◄────│ (Python) │◄────│ pgvector │
└─────────────┘ └──────┬──────┘ └─────────────────┘
│
┌──────▼──────┐
│ Celery │
│ + Redis │
└─────────────┘
│
┌──────▼──────┐
│ YOLOv8 │
│ OpenAI │
└─────────────┘

## Key Features

- **Real-time Object Detection**: YOLOv8 processes video frames at 1 FPS
- **Anomaly Detection**: 4 rule-based anomaly types (night intrusion, restricted zone, abandoned object, loitering)
- **RAG Pipeline**: Natural language queries via vector similarity search + LLM
- **Vector Search**: pgvector cosine similarity on 1536-dim OpenAI embeddings
- **Background Processing**: Async video analysis with Celery workers
- **Clean Architecture**: Domain-driven design with repository pattern

## Quick Start

````bash
git clone https://github.com/eminosmanatci/sentinel-vision.git
cd sentinel-vision
cp .env.example .env
# Add your OPENAI_API_KEY to .env
make up

API Endpoints
Table
Endpoint	Method	Description
/api/v1/upload	POST	Upload video (triggers background processing)
/api/v1/videos	GET	List all videos
/api/v1/videos/{id}	GET	Get video details
/api/v1/videos/{id}/detections	GET	Get detections for a video
/api/v1/chat	POST	RAG-based natural language query

Project Structure
plain
backend/
  app/
    core/           # Config, logging, exceptions
    domain/         # Entities (Video, Detection)
    repositories/   # Abstract interfaces
    infrastructure/ # DB, AI models, Celery
    services/       # Business logic
    api/            # HTTP routes
    schemas/        # Pydantic models
frontend/
  src/
    components/     # Reusable UI
    pages/          # Route pages
    stores/         # Zustand state
    api/            # HTTP client
    types/          # TypeScript interfaces
License
MIT


---

### 6.5 Commit & Push

```powershell
cd C:\Users\ACER\Desktop\sentinel-vision

git add .
git commit -m "feat: add CI/CD, production polish, professional README

- GitHub Actions CI for backend (lint, type-check, test, coverage)
- GitHub Actions CI for frontend (lint, type-check, build)
- Static file serving for video playback
- Professional README with architecture diagram
- API documentation and feature list"
git push origin main
````
