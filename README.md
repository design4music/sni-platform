# Strategic Narrative Intelligence (SNI) Platform

A web-based platform that aggregates global news, detects strategic narratives, and presents them in a narrative-centric UI rather than article-by-article.

## Project Structure

```
SNI/
├── docs/                    # Documentation
├── backend/                 # FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core business logic
│   ├── database/           # Database models & migrations
│   └── tests/              # Backend tests
├── frontend/               # React frontend
├── ml-pipeline/            # ML/NLP processing pipeline
├── etl-pipeline/           # Data ingestion pipeline
├── infrastructure/         # DevOps & deployment
└── scripts/                # Utility scripts

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose
- Git

### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd SNI

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up frontend
cd ../frontend
npm install

# Start development environment
docker-compose up -d
```

## Architecture

- **Backend**: FastAPI with PostgreSQL + pgvector
- **Frontend**: React with TypeScript
- **ML Pipeline**: sentence-transformers + DeepSeek/Claude LLMs
- **Data Processing**: Celery + Redis
- **Deployment**: Docker containers on Render/AWS

## Sprint Progress

- [x] Sprint 1 Day 1: Project setup and architecture decisions
- [ ] Sprint 1 Day 2-4: Core development
- [ ] Sprint 1 Day 5: Testing and optimization
- [ ] Sprint 1 Day 6: Deployment and review

## Contact

For questions about the project, contact the development team.