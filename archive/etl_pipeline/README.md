# Strategic Narrative Intelligence ETL Pipeline

A comprehensive, production-ready ETL pipeline for processing global news feeds with multilingual support, real-time trending analysis, and ML integration. Built for strategic narrative intelligence with content filtering, Named Entity Recognition (NER), and automated quality assessment.

## 🚀 Features

### Core Capabilities
- **Multi-source Ingestion**: RSS feeds, REST APIs, and web scrapers
- **Multilingual Processing**: English, Russian, German, French support
- **Content Filtering**: Intelligent filtering for geopolitics, military, energy, AI topics
- **Named Entity Recognition**: Advanced NER with spaCy and HuggingFace models
- **Real-time Trending**: Automatic trending topic detection and analysis
- **Quality Assessment**: Automated content quality and relevance scoring

### Architecture
- **Scalable Design**: Microservices architecture with Docker containerization
- **Distributed Processing**: Celery-based task queue with Redis backend
- **Robust Database**: PostgreSQL with pgvector for similarity search
- **API-First**: Complete REST API with FastAPI
- **Monitoring**: Comprehensive metrics with Prometheus and Grafana
- **Alerting**: Multi-channel alert system (Slack, email)

### Production Features
- **4-hour Processing Window**: Optimized for daily 50-80 feed processing
- **Error Recovery**: Intelligent retry mechanisms and error handling
- **Data Quality**: Automated quality validation and reporting
- **Security**: Token-based authentication and secure deployments
- **Observability**: Structured logging and distributed tracing

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL 15+ with pgvector extension
- Redis 7+
- 8GB+ RAM recommended
- 50GB+ storage for production

## 🏃 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/etl-pipeline.git
cd etl-pipeline

# Create environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Check service health
curl http://localhost:8000/health

# Access the API documentation
open http://localhost:8000/docs

# Monitor with Grafana
open http://localhost:3000  # admin/admin

# View task monitoring with Flower
open http://localhost:5555
```

### Local Development

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
python -m spacy download ru_core_news_sm
python -m spacy download de_core_news_sm
python -m spacy download fr_core_news_sm

# Set up database
createdb narrative_intelligence
psql narrative_intelligence -c "CREATE EXTENSION vector;"

# Run migrations
alembic upgrade head

# Start services
uvicorn api.main:app --reload  # API server
celery -A core.tasks.celery_app worker --loglevel=info  # Worker
celery -A core.tasks.celery_app beat --loglevel=info    # Scheduler
```

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   News Feeds    │    │  Web Scrapers   │    │   REST APIs     │
│   (RSS/Atom)    │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼───────────────┐
                    │      Feed Ingestor          │
                    │   (Parallel Processing)     │
                    └─────────────┬───────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │     Content Processor       │
                    │  (Filtering, NER, Quality)  │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼───────┐    ┌───────────▼────────────┐    ┌──────▼───────┐
│   PostgreSQL   │    │      Redis Cache       │    │   ML Pipeline │
│   + pgvector   │    │    + Task Queue        │    │   (CLUST/GEN) │
└────────────────┘    └────────────────────────┘    └──────────────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                    ┌─────────────▼───────────────┐
                    │       FastAPI Server        │
                    │    (REST API + WebSocket)   │
                    └─────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌──────────▼──────────┐    ┌─────────▼────────┐
│   Monitoring    │    │      Alerting       │    │    Dashboards    │
│  (Prometheus)   │    │  (Slack + Email)    │    │    (Grafana)     │
└─────────────────┘    └─────────────────────┘    └──────────────────┘
```

## 📊 Monitoring & Observability

### Metrics
- **Pipeline Metrics**: Execution time, throughput, success rates
- **Feed Metrics**: Ingestion rates, failure counts, response times
- **Content Metrics**: Quality scores, relevance distribution, language stats
- **System Metrics**: Memory usage, CPU utilization, queue depths

### Dashboards
- **Pipeline Overview**: High-level pipeline health and performance
- **Feed Performance**: Individual feed statistics and reliability
- **Content Analytics**: Content quality and categorization metrics
- **System Health**: Infrastructure monitoring and alerts

### Alerting Rules
- Pipeline execution failures
- Feed ingestion errors (>3 feeds failing)
- Processing delays (>4 hour window)
- High error rates (>10%)
- System resource alerts
- Data quality degradation

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=narrative_intelligence
DB_USER=postgres
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Pipeline Configuration
DAILY_SCHEDULE="0 2 * * *"  # 2 AM daily
PROCESSING_WINDOW_HOURS=4
MIN_RELEVANCE_THRESHOLD=0.3
MIN_QUALITY_THRESHOLD=0.4

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your_secret_key

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=8090
LOG_LEVEL=INFO

# Alerting Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_RECIPIENTS=admin@company.com,ops@company.com
```

### Feed Configuration

Add news feeds via the API or database:

```python
# Example feed configuration
{
    "name": "Reuters World News",
    "url": "https://feeds.reuters.com/reuters/worldNews",
    "feed_type": "rss",
    "language": "en",
    "is_active": true,
    "priority": 1,
    "fetch_interval_minutes": 60
}
```

## 🔄 Pipeline Operations

### Manual Pipeline Execution

```bash
# Trigger full pipeline
curl -X POST http://localhost:8000/pipelines/trigger \
  -H "Authorization: Bearer your_token"

# Ingest specific feed
curl -X POST http://localhost:8000/feeds/{feed_id}/ingest \
  -H "Authorization: Bearer your_token"

# Run trending analysis
curl -X POST http://localhost:8000/trending/analyze \
  -H "Authorization: Bearer your_token"
```

### Celery Task Management

```bash
# Check active tasks
celery -A core.tasks.celery_app inspect active

# Check scheduled tasks
celery -A core.tasks.celery_app inspect scheduled

# Cancel specific task
celery -A core.tasks.celery_app control revoke task_id

# Scale workers
celery -A core.tasks.celery_app control pool_grow N
```

## 📈 Performance Optimization

### Database Optimization
- **Indexes**: Optimized indexes for common query patterns
- **Partitioning**: Time-based partitioning for large tables
- **Connection Pooling**: Efficient connection management
- **Query Optimization**: Analyzed and optimized slow queries

### Processing Optimization
- **Batch Processing**: Configurable batch sizes for optimal throughput
- **Parallel Processing**: Multi-worker content processing
- **Caching**: Redis caching for frequently accessed data
- **Memory Management**: Efficient memory usage with cleanup routines

### Scaling Guidelines
- **Horizontal Scaling**: Add more worker containers
- **Database Scaling**: Read replicas for query optimization
- **Queue Scaling**: Separate queues for different task types
- **Resource Allocation**: CPU and memory limits per service

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Coverage report
pytest --cov=core --cov-report=html
```

### Load Testing

```bash
# API load testing
k6 run tests/performance/api-load-test.js

# Pipeline stress testing
python tests/performance/pipeline-stress-test.py
```

## 🚀 Deployment

### Development
```bash
docker-compose up -d
```

### Staging
```bash
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD Pipeline
- **GitHub Actions**: Automated testing, building, and deployment
- **Security Scanning**: Trivy vulnerability scanning
- **Blue-Green Deployment**: Zero-downtime production deployments
- **Performance Testing**: Automated load testing on staging

## 📝 API Documentation

### Key Endpoints

```
GET    /health                    # Health check
GET    /metrics                   # Prometheus metrics
GET    /status                    # System status

GET    /articles                  # List articles with filtering
GET    /articles/{id}             # Get specific article
GET    /articles/{id}/entities    # Get article entities

GET    /feeds                     # List news feeds
POST   /feeds/{id}/ingest         # Trigger feed ingestion

GET    /pipelines/runs            # Pipeline execution history
POST   /pipelines/trigger         # Trigger manual pipeline

GET    /trending                  # Current trending topics
POST   /trending/analyze          # Trigger trending analysis

GET    /analytics/summary         # Analytics dashboard data
```

Full API documentation available at `/docs` when running.

## 🛠️ Development

### Code Style
- **Black**: Code formatting
- **isort**: Import sorting  
- **flake8**: Linting
- **mypy**: Type checking

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

### Adding New Features
1. Create feature branch from `develop`
2. Implement with tests
3. Update documentation
4. Submit pull request
5. Automated CI/CD testing
6. Code review and merge

## 🔒 Security

### Security Features
- **Token-based Authentication**: JWT tokens for API access
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Protection**: Parameterized queries
- **Rate Limiting**: API rate limiting and DDoS protection
- **Container Security**: Non-root containers and minimal base images

### Security Scanning
- **Dependency Scanning**: Automated vulnerability scanning
- **Container Scanning**: Docker image security analysis
- **Code Analysis**: Static security analysis with bandit

## 📞 Support & Contributing

### Getting Help
- **Documentation**: Check this README and `/docs` endpoint
- **Issues**: Open GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit pull request with clear description

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📊 Project Status

![CI/CD Status](https://github.com/your-org/etl-pipeline/workflows/CI/CD%20Pipeline/badge.svg)
![Coverage](https://codecov.io/gh/your-org/etl-pipeline/branch/main/graph/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

**Current Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: January 2025