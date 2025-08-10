# Strategic Narrative Intelligence Platform - System Architecture

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL INTERFACES                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  News Feeds (50-80)  │  LLM Services  │  Web Clients  │  Admin Dashboard       │
│  RSS/API/Scraping    │  DeepSeek/GPT  │  React SPA    │  React Admin           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 API GATEWAY                                     │
│                           (Kong/AWS API Gateway)                               │
│                      Rate Limiting │ Auth │ Routing                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MICROSERVICES LAYER                               │
├─────────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│   News Ingestion    │   ML Pipeline   │    Narrative    │    Query & API      │
│     Service         │    Service      │     Service     │      Service        │
│                     │                 │                 │                     │
│ • Feed Management   │ • CLUST-1-4     │ • GEN-1-3       │ • User Queries      │
│ • Article Parsing   │ • Vector Ops    │ • NSF-1 Schema  │ • Real-time API     │
│ • Deduplication     │ • Anomaly Det.  │ • Narrative     │ • Analytics         │
│ • Language Det.     │ • Clustering    │   Updates       │ • Search            │
└─────────────────────┴─────────────────┴─────────────────┴─────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              MESSAGE QUEUE LAYER                               │
│                              (Redis/RabbitMQ)                                  │
│         Pipeline Jobs │ Notifications │ Real-time Updates │ Batch Processing   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               DATA LAYER                                       │
├─────────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│   PostgreSQL        │   Vector Store  │   Object Store  │     Cache Layer     │
│   (Primary DB)      │   (pgvector)    │   (MinIO/S3)    │     (Redis)         │
│                     │                 │                 │                     │
│ • Articles          │ • Embeddings    │ • Raw Articles  │ • Query Cache       │
│ • Narratives        │ • Similarity    │ • Media Files   │ • Session Data      │
│ • Users/Auth        │ • Clustering    │ • Models        │ • Rate Limits       │
│ • Analytics         │ • Search        │ • Backups       │ • Temp Results      │
└─────────────────────┴─────────────────┴─────────────────┴─────────────────────┘
                                        │
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            INFRASTRUCTURE LAYER                                │
│                         (Docker/Kubernetes/Cloud)                              │
│    Monitoring │ Logging │ Metrics │ Alerting │ Auto-scaling │ Load Balancing   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. Core Processing Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NARRATIVE INTELLIGENCE PIPELINE                      │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Ingestion│────│  Preprocessing  │────│   ML Pipeline   │────│   Generation    │
│                 │    │                 │    │    (CLUST)      │    │   (GEN)         │
│ • RSS Feeds     │    │ • Language Det. │    │                 │    │                 │
│ • API Polling   │    │ • Cleaning      │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ • Web Scraping  │    │ • Deduplication │    │ │   CLUST-1   │ │    │ │    GEN-1    │ │
│ • Article Parse │    │ • Translation   │    │ │  Thematic   │ │    │ │  Narrative  │ │
│                 │    │ • Normalization │    │ │ Clustering  │ │    │ │  Builder    │ │
└─────────────────┘    └─────────────────┘    │ └─────────────┘ │    │ └─────────────┘ │
                                              │ ┌─────────────┐ │    │ ┌─────────────┐ │
                                              │ │   CLUST-2   │ │    │ │    GEN-2    │ │
                                              │ │Interpretive │ │    │ │  Updates &  │ │
                                              │ │Segmentation │ │    │ │ Enhancement │ │
                                              │ └─────────────┘ │    │ └─────────────┘ │
                                              │ ┌─────────────┐ │    │ ┌─────────────┐ │
                                              │ │   CLUST-3   │ │    │ │    GEN-3    │ │
                                              │ │  Temporal   │ │    │ │Contradiction│ │
                                              │ │   Anomaly   │ │    │ │ Detection & │ │
                                              │ │  Detection  │ │    │ │ Resolution  │ │
                                              │ └─────────────┘ │    │ └─────────────┘ │
                                              │ ┌─────────────┐ │    └─────────────────┘
                                              │ │   CLUST-4   │ │
                                              │ │Consolidation│ │
                                              │ │& Refinement │ │
                                              │ └─────────────┘ │
                                              └─────────────────┘
                                                       │
┌─────────────────────────────────────────────────────┼─────────────────────────────────┐
│                                 STORAGE LAYER       │                                 │
│                                                      ▼                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Raw Articles  │  │   Embeddings    │  │   Narratives    │  │   Relationships │  │
│  │   PostgreSQL    │  │   pgvector      │  │   NSF-1 Schema  │  │   Graph Store   │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## 3. Component Breakdown and Responsibilities

### 3.1 News Ingestion Service
**Primary Responsibilities:**
- Feed management and health monitoring
- Multi-protocol data acquisition (RSS, REST APIs, web scraping)
- Content parsing and normalization
- Language detection and initial classification
- Duplicate detection and content deduplication
- Data quality validation and filtering

**Key Components:**
```python
# Core service structure
class NewsIngestionService:
    - FeedManager: Manages 50-80 news sources
    - ContentParser: Extracts structured data from various formats
    - LanguageDetector: Identifies article languages
    - DeduplicationEngine: Prevents duplicate content
    - QualityValidator: Ensures content meets standards
```

**Technologies:**
- FastAPI for service framework
- aiohttp for async HTTP operations
- BeautifulSoup/scrapy for web scraping
- langdetect for language identification
- PostgreSQL for feed metadata and scheduling

### 3.2 ML Pipeline Service
**Primary Responsibilities:**
- Executes 4-stage CLUST pipeline (CLUST-1 through CLUST-4)
- Vector embedding generation and management
- Clustering algorithms implementation
- Temporal anomaly detection
- Pipeline orchestration and monitoring

**CLUST Pipeline Breakdown:**

**CLUST-1: Thematic Clustering**
```python
class ThematicClusterer:
    - EmbeddingGenerator: Creates article embeddings using sentence-transformers
    - SemanticClusterer: Groups articles by semantic similarity (HDBSCAN/K-means)
    - TopicExtractor: Identifies dominant themes per cluster
    - QualityScorer: Evaluates cluster coherence
```

**CLUST-2: Interpretive Segmentation**
```python
class InterpretiveSegmenter:
    - FrameAnalyzer: Identifies narrative frames and perspectives
    - ContextExtractor: Captures contextual information
    - StanceDetector: Determines article stance/bias
    - SegmentationEngine: Groups by interpretive patterns
```

**CLUST-3: Temporal Anomaly Detection**
```python
class TemporalAnomalyDetector:
    - TimeSeriesAnalyzer: Tracks narrative evolution over time
    - AnomalyDetector: Identifies unusual patterns or spikes
    - TrendAnalyzer: Detects emerging or declining narratives
    - SignificanceScorer: Rates anomaly importance
```

**CLUST-4: Consolidation & Refinement**
```python
class ConsolidationEngine:
    - CrossClusterMerger: Combines related clusters across stages
    - QualityRefiner: Improves cluster quality through iteration
    - HierarchyBuilder: Creates narrative hierarchies
    - FinalValidator: Ensures output quality standards
```

### 3.3 Narrative Service
**Primary Responsibilities:**
- Executes 3-stage GEN pipeline (GEN-1 through GEN-3)
- Manages NSF-1 schema compliance
- Handles narrative lifecycle management
- Provides narrative update and versioning

**GEN Pipeline Breakdown:**

**GEN-1: Narrative Builder**
```python
class NarrativeBuilder:
    - StructureGenerator: Creates initial narrative structure using NSF-1
    - ContentSynthesizer: Generates narrative content from clusters
    - MetadataExtractor: Extracts key actors, events, timelines
    - QualityAssessor: Validates narrative completeness
```

**GEN-2: Updates & Enhancement**
```python
class NarrativeUpdater:
    - ChangeDetector: Identifies when narratives need updates
    - ContentMerger: Integrates new information
    - VersionManager: Handles narrative versioning
    - EnhancementEngine: Improves narrative quality over time
```

**GEN-3: Contradiction Detection & Resolution**
```python
class ContradictionProcessor:
    - ContradictionDetector: Identifies conflicting information
    - EvidenceWeigher: Evaluates source credibility and evidence strength
    - ResolutionEngine: Resolves conflicts through analysis
    - UncertaintyManager: Handles unresolvable contradictions
```

**NSF-1 Schema Implementation:**
```python
class NSF1Schema:
    - NarrativeMetadata: ID, title, summary, confidence
    - TemporalDimension: Timeline, key events, evolution
    - SpatialDimension: Geographic scope, locations
    - ActorDimension: Key entities, roles, relationships
    - ThematicDimension: Core themes, sub-narratives
    - EvidentialDimension: Supporting articles, confidence scores
    - RelationalDimension: Links to other narratives
```

### 3.4 Query & API Service
**Primary Responsibilities:**
- Provides RESTful API endpoints for frontend
- Handles real-time queries and search
- Manages user authentication and authorization
- Provides analytics and reporting capabilities
- Handles WebSocket connections for real-time updates

**Key Components:**
```python
class QueryAPIService:
    - AuthenticationManager: JWT-based auth with role-based access
    - QueryProcessor: Handles complex narrative queries
    - SearchEngine: Full-text and vector search capabilities
    - AnalyticsEngine: Generates insights and reports
    - WebSocketManager: Real-time updates to clients
    - CacheManager: Optimizes response times
```

### 3.5 Scheduler Service
**Primary Responsibilities:**
- Orchestrates daily automated pipeline execution
- Manages on-demand RAI (Rapid Analysis and Intelligence) requests
- Handles pipeline dependencies and error recovery
- Provides pipeline monitoring and alerting

**Key Components:**
```python
class SchedulerService:
    - PipelineOrchestrator: Manages multi-stage pipeline execution
    - TaskScheduler: Handles cron-like scheduling (Celery/APScheduler)
    - DependencyManager: Ensures proper execution order
    - ErrorHandler: Manages failures and retries
    - MonitoringAgent: Tracks pipeline health and performance
```

## 4. Technology Stack Justification

### 4.1 Backend Framework: FastAPI
**Choice Rationale:**
- **High Performance**: ASGI-based async framework with excellent performance characteristics
- **Auto-documentation**: Built-in OpenAPI/Swagger documentation generation
- **Type Safety**: Pydantic integration for request/response validation
- **Modern Python**: Full support for Python 3.8+ features including async/await
- **WebSocket Support**: Native WebSocket support for real-time features
- **Dependency Injection**: Built-in DI system for clean architecture

**Alternative Considerations:**
- Django: Too heavyweight for API-focused microservices
- Flask: Lacks built-in async support and modern features
- Node.js: JavaScript ecosystem, but Python preferred for ML/NLP integration

### 4.2 Database: PostgreSQL + pgvector
**Choice Rationale:**
- **ACID Compliance**: Critical for narrative consistency and data integrity
- **JSON Support**: Native JSONB for flexible NSF-1 schema storage
- **Vector Extensions**: pgvector for efficient embedding similarity search
- **Scalability**: Proven scaling patterns with read replicas and partitioning
- **Full-text Search**: Built-in search capabilities with multilingual support
- **Mature Ecosystem**: Extensive tooling and operational knowledge

**Vector Store Integration:**
```sql
-- pgvector enables efficient similarity search
CREATE EXTENSION vector;
CREATE TABLE article_embeddings (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    embedding vector(768),  -- sentence-transformer dimension
    model_version VARCHAR(50)
);
CREATE INDEX ON article_embeddings USING ivfflat (embedding vector_cosine_ops);
```

### 4.3 Message Queue: Redis + Celery
**Choice Rationale:**
- **Dual Purpose**: Redis serves as both message broker and cache
- **Proven Integration**: Celery has excellent FastAPI integration
- **Pipeline Orchestration**: Complex workflow support with chains and groups
- **Monitoring**: Built-in monitoring with Flower
- **Reliability**: Redis persistence and clustering for reliability

**Pipeline Implementation:**
```python
# Celery task chain for daily pipeline
@celery.task
def ingest_news_daily():
    return "ingestion_complete"

@celery.task  
def run_clust_pipeline(ingestion_result):
    return "clustering_complete"

@celery.task
def run_gen_pipeline(clustering_result):
    return "generation_complete"

# Chain execution
daily_pipeline = chain(
    ingest_news_daily.s(),
    run_clust_pipeline.s(),
    run_gen_pipeline.s()
)
```

### 4.4 Caching Strategy: Multi-layer Redis
**Implementation:**
- **L1 Cache**: In-memory application cache for hot data
- **L2 Cache**: Redis cluster for shared cache across services
- **Query Cache**: Cached narrative search results with TTL
- **Rate Limiting**: Redis-based rate limiting for API endpoints

### 4.5 LLM Integration Architecture
**Primary: DeepSeek API**
- Cost-effective for high-volume processing
- Good performance for narrative generation tasks
- API reliability and scaling

**Fallback: Claude/GPT**
- Quality assurance for critical narratives
- Complex reasoning tasks requiring higher capability
- Final quality validation

**Integration Pattern:**
```python
class LLMRouter:
    async def generate_narrative(self, cluster_data, quality_level="standard"):
        if quality_level == "premium":
            return await self.claude_client.generate(cluster_data)
        else:
            try:
                return await self.deepseek_client.generate(cluster_data)
            except Exception:
                return await self.claude_client.generate(cluster_data)
```

### 4.6 Frontend: React + TypeScript
**Choice Rationale:**
- **Component Architecture**: Modular components for complex narrative visualization
- **TypeScript Safety**: Type safety for complex data structures (NSF-1 schema)
- **Real-time Updates**: Excellent WebSocket integration
- **Rich Ecosystem**: Extensive libraries for data visualization and charts
- **State Management**: Redux Toolkit for complex application state

### 4.7 Vector Search: pgvector vs Alternatives
**pgvector Advantages:**
- **Single Database**: No additional infrastructure complexity
- **ACID Transactions**: Consistent updates with relational data
- **SQL Integration**: Complex queries combining vector and relational data
- **Cost Effective**: No separate vector database licensing

**Performance Considerations:**
- Suitable for 50-80 feeds with millions of articles
- HNSW indexing for approximate nearest neighbor search
- Horizontal scaling through read replicas

### 4.8 Monitoring and Observability
**Stack Selection:**
- **Metrics**: Prometheus + Grafana for system metrics  
- **Logging**: Structured logging with ELK stack (Elasticsearch, Logstash, Kibana)
- **Tracing**: OpenTelemetry for distributed tracing
- **Alerting**: AlertManager for intelligent alerting
- **Health Checks**: Built-in FastAPI health endpoints

### 4.9 Language Processing Pipeline
**Core Libraries:**
```python
# Key ML/NLP dependencies
sentence_transformers==2.2.2    # Embeddings generation
scikit_learn==1.3.0            # Clustering algorithms  
hdbscan==0.8.29                # Density-based clustering
langdetect==1.0.9              # Language identification
transformers==4.30.0           # Hugging Face models
numpy==1.24.3                  # Numerical computing
pandas==2.0.3                  # Data manipulation
```

**Rationale for Choices:**
- **sentence-transformers**: Best-in-class embeddings for semantic similarity
- **HDBSCAN**: Superior density-based clustering for narrative discovery
- **langdetect**: Reliable language identification for multilingual content
- **transformers**: Direct access to state-of-the-art NLP models

## 5. Scalability Considerations and Patterns

### 5.1 Horizontal Scaling Architecture

**Database Scaling:**
```
┌─────────────────────────────────────────────────────────────────┐
│                     DATABASE SCALING PATTERN                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │
│  │   Primary DB    │────│  Read Replica 1 │    │Read Replica │  │
│  │   (Write)       │    │   (Analytics)   │    │   2 (API)   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
│           │                        │                      │      │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────┐  │  
│  │  Vector Store   │    │   Cached Views  │    │ Search Index│  │
│  │   (pgvector)    │    │    (Redis)      │    │ (Elastic)   │  │
│  └─────────────────┘    └─────────────────┘    └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Service Scaling Strategy:**
- **News Ingestion**: Horizontal pod scaling based on feed count
- **ML Pipeline**: GPU-enabled nodes with queue-based auto-scaling  
- **Narrative Service**: CPU-optimized instances with memory scaling
- **API Service**: Load-balanced pods with aggressive caching

### 5.2 Performance Optimization Patterns

**Connection Pooling:**
```python
# Database connection pooling configuration
from sqlalchemy.pool import QueuePool

DATABASE_CONFIG = {
    "poolclass": QueuePool,
    "pool_size": 20,
    "max_overflow": 30,
    "pool_pre_ping": True,
    "pool_recycle": 3600
}
```

**Caching Strategy Implementation:**
```python
class CacheStrategy:
    # L1: In-memory cache for hot narratives
    hot_cache: Dict[str, Any] = {}
    
    # L2: Redis for cross-service cache
    async def get_cached_narrative(self, narrative_id: str):
        # Check L1 first
        if narrative_id in self.hot_cache:
            return self.hot_cache[narrative_id]
        
        # Check L2 Redis
        cached = await redis.get(f"narrative:{narrative_id}")
        if cached:
            # Promote to L1
            self.hot_cache[narrative_id] = json.loads(cached)
            return self.hot_cache[narrative_id]
        
        return None
```

### 5.3 Data Partitioning Strategy

**Temporal Partitioning for Articles:**
```sql
-- Monthly partitioning for article storage
CREATE TABLE articles (
    id SERIAL,
    title TEXT,
    content TEXT,
    published_date DATE,
    source_id INTEGER,
    PRIMARY KEY (id, published_date)
) PARTITION BY RANGE (published_date);

-- Create monthly partitions
CREATE TABLE articles_2024_01 PARTITION OF articles
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
    
CREATE TABLE articles_2024_02 PARTITION OF articles  
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

**Geographic Partitioning for Narratives:**
```sql  
-- Regional partitioning for narrative storage
CREATE TABLE narratives (
    id SERIAL,
    title TEXT,
    region VARCHAR(50),
    data JSONB,
    PRIMARY KEY (id, region)
) PARTITION BY LIST (region);

CREATE TABLE narratives_americas PARTITION OF narratives
    FOR VALUES IN ('US', 'CA', 'MX', 'BR');
    
CREATE TABLE narratives_europe PARTITION OF narratives
    FOR VALUES IN ('UK', 'DE', 'FR', 'IT');
```

### 5.4 Queue-based Processing Scale

**Multi-Queue Architecture:**
```python
# Priority-based queue routing
class QueueRouter:
    QUEUES = {
        'urgent': 'rai_urgent',      # On-demand RAI requests
        'daily': 'pipeline_daily',   # Scheduled daily processing  
        'batch': 'pipeline_batch',   # Large batch operations
        'ml': 'ml_processing'        # ML-intensive tasks
    }
    
    def route_task(self, task_type: str, priority: str = 'normal'):
        if priority == 'urgent':
            return self.QUEUES['urgent']
        elif task_type == 'ml_processing':
            return self.QUEUES['ml']
        elif task_type == 'daily_pipeline':
            return self.QUEUES['daily']
        else:
            return self.QUEUES['batch']
```

### 5.5 Auto-scaling Configuration

**Kubernetes HPA Configuration:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: narrative-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: narrative-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

**ML Pipeline Scaling:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler  
metadata:
  name: ml-pipeline-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ml-pipeline
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Pods
    pods:
      metric:
        name: pending_jobs
      target:
        type: AverageValue
        averageValue: "5"
```

### 5.6 Load Testing and Capacity Planning

**Expected Load Characteristics:**
- **News Ingestion**: 50-80 feeds, ~10,000 articles/day
- **API Requests**: 1000 concurrent users, 10,000 RPM peak
- **ML Processing**: Daily batch + on-demand RAI requests
- **Storage Growth**: ~1GB/day (articles + embeddings + narratives)

**Performance Targets:**
- **API Response**: <200ms for cached queries, <2s for complex searches
- **Pipeline Processing**: Complete daily cycle within 4 hours
- **RAI Requests**: Results within 5 minutes
- **Database Queries**: <100ms for narrative retrieval

### 5.7 Cost Optimization Strategies

**Resource Right-sizing:**
```python
# Dynamic resource allocation based on load
class ResourceOptimizer:
    def calculate_optimal_resources(self, current_load):
        base_cpu = 0.5  # cores
        base_memory = 1024  # MB
        
        # Scale based on queue depth
        cpu_multiplier = min(current_load / 100, 4.0)
        memory_multiplier = min(current_load / 50, 3.0)
        
        return {
            'cpu': base_cpu * cpu_multiplier,
            'memory': base_memory * memory_multiplier
        }
```

**Intelligent Caching:**
- **Hot Path Caching**: Cache frequently accessed narratives for 1 hour
- **Cold Storage**: Archive old articles to cheaper storage after 6 months
- **Compression**: Use PostgreSQL compression for historical data
- **CDN Integration**: Cache static assets and API responses

## 6. Security Architecture

### 6.1 Authentication and Authorization

**Multi-tier Authentication System:**
```python
# JWT-based authentication with role-based access
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

class SecurityManager:
    def __init__(self):
        self.security = HTTPBearer()
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)):
        try:
            payload = jwt.decode(credentials.credentials, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
    
    def require_role(self, required_role: str):
        def role_checker(token_data: dict = Depends(self.verify_token)):
            user_roles = token_data.get("roles", [])
            if required_role not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            return token_data
        return role_checker
```

**Role-Based Access Control (RBAC):**
```python
class Roles:
    ADMIN = "admin"           # Full system access
    ANALYST = "analyst"       # Read narratives, trigger RAI
    VIEWER = "viewer"         # Read-only access
    API_CLIENT = "api_client" # Programmatic access
    
class Permissions:
    READ_NARRATIVES = "read:narratives"
    WRITE_NARRATIVES = "write:narratives"
    TRIGGER_RAI = "trigger:rai"
    MANAGE_FEEDS = "manage:feeds"
    VIEW_ANALYTICS = "view:analytics"
    ADMIN_USERS = "admin:users"
```

### 6.2 API Security Implementation

**Rate Limiting Strategy:**
```python
# Redis-based rate limiting
from fastapi import Request
from redis import Redis
import time

class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def check_rate_limit(self, request: Request, 
                              limit: int = 100, 
                              window: int = 3600):
        # Use IP + user ID for rate limiting
        user_id = getattr(request.state, 'user_id', None)
        client_ip = request.client.host
        key = f"rate_limit:{user_id or client_ip}:{int(time.time() / window)}"
        
        current_requests = await self.redis.incr(key)
        if current_requests == 1:
            await self.redis.expire(key, window)
        
        if current_requests > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return current_requests
```

**Input Validation and Sanitization:**
```python
from pydantic import BaseModel, validator, Field
import bleach

class NarrativeQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    filters: dict = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove potential XSS vectors
        return bleach.clean(v, tags=[], strip=True)
    
    @validator('filters')
    def validate_filters(cls, v):
        allowed_keys = {'date_range', 'region', 'source', 'confidence'}
        if not set(v.keys()).issubset(allowed_keys):
            raise ValueError("Invalid filter keys")
        return v
```

### 6.3 Data Protection and Privacy

**Encryption Strategy:**
```python
# Data encryption for sensitive information
from cryptography.fernet import Fernet
import hashlib

class DataProtection:
    def __init__(self):
        self.encryption_key = os.getenv("DATA_ENCRYPTION_KEY").encode()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive content before storage"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive content after retrieval"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def hash_personal_identifier(self, identifier: str) -> str:
        """Hash personal identifiers for privacy"""
        return hashlib.sha256(identifier.encode()).hexdigest()
```

**Database Security Configuration:**
```sql
-- Row-level security for multi-tenant access
ALTER TABLE narratives ENABLE ROW LEVEL SECURITY;

-- Policy to restrict access based on user organization
CREATE POLICY narrative_org_policy ON narratives
    FOR ALL TO authenticated_users
    USING (organization_id = current_setting('app.current_org_id')::integer);

-- Audit logging for sensitive operations
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    action VARCHAR(50),
    table_name VARCHAR(50),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    ip_address INET
);
```

### 6.4 Network Security

**API Gateway Security:**
```yaml
# Kong API Gateway security configuration
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: security-plugin
plugin: cors
config:
  origins:
    - "https://app.narrativeintel.com"
    - "https://admin.narrativeintel.com"
  methods:
    - GET
    - POST
    - PUT
    - DELETE
  headers:
    - Accept
    - Authorization
    - Content-Type
  credentials: true
  max_age: 3600
---
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rate-limiting
plugin: rate-limiting
config:
  minute: 100
  hour: 1000
  policy: redis
  redis_host: redis-cluster
```

**TLS and Certificate Management:**
```yaml
# Automatic TLS with cert-manager
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: narrative-intel-tls
  namespace: production
spec:
  secretName: narrative-intel-tls-secret
  dnsNames:
  - api.narrativeintel.com
  - app.narrativeintel.com
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

### 6.5 Content Security and Compliance

**Content Sanitization Pipeline:**
```python
class ContentSecurity:
    def __init__(self):
        self.pii_detector = PIIDetector()
        self.malware_scanner = MalwareScanner()
    
    async def scan_article_content(self, article: Article) -> SecurityReport:
        report = SecurityReport()
        
        # Detect and redact PII
        pii_results = await self.pii_detector.scan(article.content)
        if pii_results.found_pii:
            article.content = pii_results.redacted_content
            report.add_finding("PII_DETECTED", pii_results.entities)
        
        # Scan for malicious content
        malware_results = await self.malware_scanner.scan(article.url)
        if malware_results.is_malicious:
            report.add_finding("MALWARE_DETECTED", malware_results.threats)
            raise SecurityException("Malicious content detected")
        
        return report
```

**Compliance Framework:**
```python
class ComplianceManager:
    def __init__(self):
        self.gdpr_processor = GDPRProcessor()
        self.data_retention = DataRetentionPolicy()
    
    async def handle_data_request(self, request_type: str, user_id: str):
        if request_type == "EXPORT":
            # GDPR Article 20 - Data portability
            return await self.export_user_data(user_id)
        elif request_type == "DELETE":
            # GDPR Article 17 - Right to erasure
            return await self.delete_user_data(user_id)
        elif request_type == "RECTIFY":
            # GDPR Article 16 - Right to rectification
            return await self.update_user_data(user_id)
    
    async def apply_retention_policy(self):
        # Automatically delete data past retention period
        cutoff_date = datetime.now() - timedelta(days=2555)  # 7 years
        await self.data_retention.cleanup_old_records(cutoff_date)
```

### 6.6 Infrastructure Security

**Container Security:**
```dockerfile
# Multi-stage build for security
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --chown=app:app . .

# Security scanning
RUN pip audit --desc

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Kubernetes Security Policies:**
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: narrative-intel-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

## 7. Deployment Architecture

### 7.1 Containerization Strategy

**Multi-Service Docker Composition:**
```yaml
# docker-compose.yml for development
version: '3.8'

services:
  # API Gateway
  kong:
    image: kong:3.4
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: postgres
      KONG_PG_DATABASE: kong
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kong
    ports:
      - "8000:8000"
      - "8443:8443"
      - "8001:8001"
    depends_on:
      - postgres

  # News Ingestion Service
  news-ingestion:
    build: 
      context: ./services/news-ingestion
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/narrative_intel
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  # ML Pipeline Service  
  ml-pipeline:
    build:
      context: ./services/ml-pipeline
      dockerfile: Dockerfile.gpu
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/narrative_intel
      REDIS_URL: redis://redis:6379/1
      DEEPSEEK_API_KEY: ${DEEPSEEK_API_KEY}
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # Narrative Service
  narrative-service:
    build: ./services/narrative-service
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/narrative_intel
      REDIS_URL: redis://redis:6379/2
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

  # Query API Service
  query-api:
    build: ./services/query-api
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/narrative_intel
      REDIS_URL: redis://redis:6379/3
    ports:
      - "8080:8000"
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  # PostgreSQL with pgvector
  postgres:
    image: pgvector/pgvector:pg15
    environment:
      POSTGRES_DB: narrative_intel
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"

  # Redis Cluster
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  redis_data:
  grafana_data:
```

### 7.2 Kubernetes Production Deployment

**Namespace and Resource Configuration:**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: narrative-intel-prod
  labels:
    environment: production
---
# resource-quotas.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: narrative-intel-prod
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
```

**Core Service Deployments:**
```yaml
# ml-pipeline-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-pipeline
  namespace: narrative-intel-prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ml-pipeline
  template:
    metadata:
      labels:
        app: ml-pipeline
    spec:
      serviceAccountName: ml-pipeline-sa
      containers:
      - name: ml-pipeline
        image: narrativeintel/ml-pipeline:v1.0.0
        resources:
          requests:
            cpu: 2000m
            memory: 4Gi
            nvidia.com/gpu: 1
          limits:
            cpu: 4000m
            memory: 8Gi
            nvidia.com/gpu: 1
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**Database StatefulSet:**
```yaml
# postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: narrative-intel-prod
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: pgvector/pgvector:pg15
        resources:
          requests:
            cpu: 2000m
            memory: 8Gi
          limits:
            cpu: 4000m
            memory: 16Gi
        env:
        - name: POSTGRES_DB
          value: narrative_intel
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-credentials
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        - name: init-scripts
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: init-scripts
        configMap:
          name: postgres-init-scripts
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 1Ti
      storageClassName: ssd-storage
```

### 7.3 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Security scan
      run: |
        bandit -r src/
        safety check

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    strategy:
      matrix:
        service: [news-ingestion, ml-pipeline, narrative-service, query-api]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v5
      with:
        context: ./services/${{ matrix.service }}
        push: true
        tags: |
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}:latest
          ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}:${{ github.sha }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy to Kubernetes
      run: |
        # Update image tags
        kubectl set image deployment/news-ingestion \
          news-ingestion=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/news-ingestion:${{ github.sha }} \
          -n narrative-intel-prod
        
        kubectl set image deployment/ml-pipeline \
          ml-pipeline=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/ml-pipeline:${{ github.sha }} \
          -n narrative-intel-prod
        
        # Wait for rollout
        kubectl rollout status deployment/news-ingestion -n narrative-intel-prod
        kubectl rollout status deployment/ml-pipeline -n narrative-intel-prod
    
    - name: Run smoke tests
      run: |
        kubectl run smoke-test \
          --image=curlimages/curl \
          --restart=Never \
          --rm -i \
          -- curl -f http://query-api:8000/health
```

### 7.4 Infrastructure as Code

**Terraform Configuration:**
```hcl
# main.tf
terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }
}

# Kubernetes cluster
resource "kubernetes_namespace" "narrative_intel" {
  metadata {
    name = "narrative-intel-prod"
    labels = {
      environment = "production"
      team        = "platform"
    }
  }
}

# PostgreSQL via Helm
resource "helm_release" "postgresql" {
  name       = "postgresql"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "postgresql"
  namespace  = kubernetes_namespace.narrative_intel.metadata[0].name

  values = [
    yamlencode({
      auth = {
        database = "narrative_intel"
        username = "app_user"
      }
      primary = {
        persistence = {
          size = "1Ti"
          storageClass = "ssd-storage"
        }
        resources = {
          requests = {
            memory = "8Gi"
            cpu    = "2000m"
          }
          limits = {
            memory = "16Gi"
            cpu    = "4000m"
          }
        }
      }
      image = {
        repository = "pgvector/pgvector"
        tag       = "pg15"
      }
    })
  ]
}

# Redis cluster
resource "helm_release" "redis" {
  name       = "redis"
  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  namespace  = kubernetes_namespace.narrative_intel.metadata[0].name

  values = [
    yamlencode({
      architecture = "replication"
      auth = {
        enabled = true
      }
      replica = {
        replicaCount = 2
      }
    })
  ]
}

# Monitoring stack
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace.narrative_intel.metadata[0].name

  values = [
    yamlencode({
      grafana = {
        persistence = {
          enabled = true
          size    = "10Gi"
        }
      }
      prometheus = {
        prometheusSpec = {
          retention = "30d"
          storageSpec = {
            volumeClaimTemplate = {
              spec = {
                storageClassName = "ssd-storage"
                accessModes      = ["ReadWriteOnce"]
                resources = {
                  requests = {
                    storage = "100Gi"
                  }
                }
              }
            }
          }
        }
      }
    })
  ]
}
```

### 7.5 Environment-Specific Configurations

**Production ConfigMap:**
```yaml
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: narrative-intel-prod
data:
  redis-url: "redis://redis-master:6379/0"
  database-max-connections: "50"
  ml-batch-size: "1000"
  cache-ttl: "3600"
  log-level: "INFO"
  pipeline-schedule: "0 2 * * *"
  rai-timeout: "300"
---
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
  namespace: narrative-intel-prod
type: Opaque
stringData:
  deepseek-api-key: "${DEEPSEEK_API_KEY}"
  claude-api-key: "${CLAUDE_API_KEY}"
  openai-api-key: "${OPENAI_API_KEY}"
  jwt-secret: "${JWT_SECRET_KEY}"
```

**Development Override:**
```yaml
# development-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: narrative-intel-dev
data:
  redis-url: "redis://redis:6379/0"
  database-max-connections: "10"
  ml-batch-size: "100"
  cache-ttl: "300"
  log-level: "DEBUG"
  pipeline-schedule: "0 */6 * * *"
  rai-timeout: "60"
```

## 8. Integration Points and API Contracts

### 8.1 External API Integrations

**LLM Service Integration Contracts:**
```python
# Abstract LLM interface for consistent integration
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from pydantic import BaseModel

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    context: Optional[Dict] = None

class LLMResponse(BaseModel):
    content: str
    usage: Dict[str, int]
    model: str
    confidence: float
    processing_time: float

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass

# DeepSeek implementation
class DeepSeekProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            response = await self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": request.system_prompt or ""},
                    {"role": "user", "content": request.prompt}
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                usage=response.usage.dict(),
                model="deepseek-chat",
                confidence=0.85,  # DeepSeek confidence scoring
                processing_time=response.response_time
            )
        except Exception as e:
            raise LLMException(f"DeepSeek API error: {str(e)}")

# Claude implementation
class ClaudeProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=request.system_prompt or "",
                messages=[{"role": "user", "content": request.prompt}]
            )
            
            return LLMResponse(
                content=response.content[0].text,
                usage={"prompt_tokens": response.usage.input_tokens, 
                       "completion_tokens": response.usage.output_tokens},
                model="claude-3-sonnet",
                confidence=0.92,  # Claude confidence scoring
                processing_time=response.processing_time
            )
        except Exception as e:
            raise LLMException(f"Claude API error: {str(e)}")
```

**News Feed Integration Framework:**
```python
# Generic news feed adapter
class NewsFeedAdapter(ABC):
    @abstractmethod
    async def fetch_articles(self, since: datetime) -> List[RawArticle]:
        pass
    
    @abstractmethod
    async def validate_feed_health(self) -> FeedHealthStatus:
        pass

class RSSFeedAdapter(NewsFeedAdapter):
    def __init__(self, feed_url: str, source_config: Dict):
        self.feed_url = feed_url
        self.source_config = source_config
        self.session = aiohttp.ClientSession()
    
    async def fetch_articles(self, since: datetime) -> List[RawArticle]:
        async with self.session.get(self.feed_url) as response:
            feed_data = await response.text()
            
        feed = feedparser.parse(feed_data)
        articles = []
        
        for entry in feed.entries:
            if self._is_newer_than(entry, since):
                article = RawArticle(
                    title=entry.title,
                    content=entry.description,
                    url=entry.link,
                    published=self._parse_date(entry.published),
                    source=feed.feed.title,
                    language=self._detect_language(entry.description)
                )
                articles.append(article)
        
        return articles

class APIFeedAdapter(NewsFeedAdapter):
    def __init__(self, api_url: str, api_key: str, source_config: Dict):
        self.api_url = api_url
        self.api_key = api_key
        self.source_config = source_config
    
    async def fetch_articles(self, since: datetime) -> List[RawArticle]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {
            "since": since.isoformat(),
            "limit": self.source_config.get("batch_size", 100)
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(self.api_url, headers=headers, params=params) as response:
                data = await response.json()
                
        return [RawArticle(**article) for article in data["articles"]]
```

### 8.2 Internal Service API Contracts

**News Ingestion Service API:**
```python
# FastAPI routes for News Ingestion Service
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

@router.post("/feeds", response_model=FeedResponse)
async def add_news_feed(
    feed_config: FeedConfig,
    current_user: User = Depends(get_current_user)
):
    """Add a new news feed source"""
    if not current_user.has_permission("manage:feeds"):
        raise HTTPException(403, "Insufficient permissions")
    
    feed = await feed_service.create_feed(feed_config)
    return FeedResponse.from_orm(feed)

@router.get("/feeds/{feed_id}/status", response_model=FeedStatus)
async def get_feed_status(feed_id: int):
    """Get current status of a news feed"""
    status = await feed_service.get_feed_status(feed_id)
    return status

@router.post("/feeds/{feed_id}/trigger", response_model=TaskResponse)
async def trigger_feed_fetch(
    feed_id: int,
    background_tasks: BackgroundTasks
):
    """Manually trigger feed ingestion"""
    task_id = await feed_service.trigger_fetch(feed_id)
    background_tasks.add_task(monitor_task, task_id)
    return TaskResponse(task_id=task_id, status="queued")

@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    skip: int = 0,
    limit: int = 100,
    source: Optional[str] = None,
    since: Optional[datetime] = None
):
    """List ingested articles with filters"""
    articles = await article_service.list_articles(
        skip=skip, limit=limit, source=source, since=since
    )
    return ArticleListResponse(articles=articles, total=len(articles))
```

**ML Pipeline Service API:**
```python
# ML Pipeline Service API contracts
@router.post("/pipeline/trigger", response_model=PipelineResponse)
async def trigger_ml_pipeline(
    pipeline_config: PipelineConfig,
    current_user: User = Depends(require_role("analyst"))
):
    """Trigger ML pipeline execution"""
    pipeline_id = await ml_service.start_pipeline(pipeline_config)
    return PipelineResponse(
        pipeline_id=pipeline_id,
        status="started",
        estimated_duration="4 hours"
    )

@router.get("/pipeline/{pipeline_id}/status", response_model=PipelineStatus)
async def get_pipeline_status(pipeline_id: str):
    """Get current pipeline execution status"""
    status = await ml_service.get_pipeline_status(pipeline_id)
    return status

@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(
    stage: ClusterStage = ClusterStage.ALL,
    limit: int = 50
):
    """List generated clusters by stage"""
    clusters = await cluster_service.list_clusters(stage=stage, limit=limit)
    return ClusterListResponse(clusters=clusters)

@router.post("/rai", response_model=RAIResponse)
async def trigger_rai_analysis(
    query: RAIQuery,
    current_user: User = Depends(require_role("analyst"))
):
    """Trigger Rapid Analysis and Intelligence request"""
    rai_id = await rai_service.submit_query(query, current_user.id)
    return RAIResponse(
        rai_id=rai_id,
        status="processing",
        estimated_completion=datetime.now() + timedelta(minutes=5)
    )
```

**Narrative Service API:**
```python
# Narrative Service API contracts
@router.get("/narratives", response_model=NarrativeListResponse)
async def list_narratives(
    skip: int = 0,
    limit: int = 20,
    confidence_threshold: float = 0.7,
    region: Optional[str] = None,
    time_range: Optional[TimeRange] = None
):
    """List narratives with filtering options"""
    narratives = await narrative_service.list_narratives(
        skip=skip,
        limit=limit,
        confidence_threshold=confidence_threshold,
        region=region,
        time_range=time_range
    )
    return NarrativeListResponse(narratives=narratives)

@router.get("/narratives/{narrative_id}", response_model=NarrativeDetail)
async def get_narrative(narrative_id: str):
    """Get detailed narrative information"""
    narrative = await narrative_service.get_narrative(narrative_id)
    if not narrative:
        raise HTTPException(404, "Narrative not found")
    return NarrativeDetail.from_orm(narrative)

@router.get("/narratives/{narrative_id}/evolution", response_model=NarrativeEvolution)
async def get_narrative_evolution(narrative_id: str):
    """Get narrative evolution over time"""
    evolution = await narrative_service.get_evolution(narrative_id)
    return evolution

@router.post("/narratives/{narrative_id}/update", response_model=UpdateResponse)
async def update_narrative(
    narrative_id: str,
    update_request: NarrativeUpdateRequest,
    current_user: User = Depends(require_role("analyst"))
):
    """Trigger narrative update with new information"""
    task_id = await narrative_service.queue_update(narrative_id, update_request)
    return UpdateResponse(task_id=task_id, status="queued")
```

### 8.3 WebSocket Integration for Real-time Updates

**Real-time Communication Contract:**
```python
# WebSocket manager for real-time updates
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        self.active_connections[user_id].remove(websocket)
    
    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(json.dumps(message))
    
    async def broadcast_narrative_update(self, narrative_update: NarrativeUpdateEvent):
        message = {
            "type": "narrative_update",
            "data": narrative_update.dict()
        }
        for user_connections in self.active_connections.values():
            for connection in user_connections:
                await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and handle client messages
            data = await websocket.receive_text()
            client_message = json.loads(data)
            
            if client_message["type"] == "subscribe_narrative":
                await narrative_service.subscribe_to_updates(
                    user_id, client_message["narrative_id"]
                )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
```

### 8.4 Event-Driven Architecture Contracts

**Inter-Service Event Schema:**
```python
# Event schemas for service communication
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class EventType(str, Enum):
    ARTICLE_INGESTED = "article.ingested"
    CLUSTER_CREATED = "cluster.created"
    NARRATIVE_GENERATED = "narrative.generated"
    NARRATIVE_UPDATED = "narrative.updated"
    CONTRADICTION_DETECTED = "contradiction.detected"
    RAI_COMPLETED = "rai.completed"
    PIPELINE_STARTED = "pipeline.started"
    PIPELINE_COMPLETED = "pipeline.completed"
    PIPELINE_FAILED = "pipeline.failed"

class BaseEvent(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: datetime
    source_service: str
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

class ArticleIngestedEvent(BaseEvent):
    event_type: EventType = EventType.ARTICLE_INGESTED
    article_id: str
    source: str
    language: str
    word_count: int

class NarrativeGeneratedEvent(BaseEvent):
    event_type: EventType = EventType.NARRATIVE_GENERATED
    narrative_id: str
    title: str
    confidence: float
    cluster_ids: List[str]
    region: Optional[str]

class ContradictionDetectedEvent(BaseEvent):
    event_type: EventType = EventType.CONTRADICTION_DETECTED
    narrative_id: str
    conflicting_narrative_id: str
    contradiction_type: str
    evidence: Dict[str, Any]

# Event handlers for each service
class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event: BaseEvent) -> None:
        pass

class NarrativeUpdateHandler(EventHandler):
    def __init__(self, narrative_service: NarrativeService):
        self.narrative_service = narrative_service
    
    async def handle(self, event: BaseEvent) -> None:
        if isinstance(event, ArticleIngestedEvent):
            # Check if new article affects existing narratives
            await self.narrative_service.check_for_updates(event.article_id)
        elif isinstance(event, ContradictionDetectedEvent):
            # Handle contradiction resolution
            await self.narrative_service.resolve_contradiction(
                event.narrative_id, event.conflicting_narrative_id
            )
```

### 8.5 Database Integration Contracts

**NSF-1 Schema Implementation:**
```sql
-- Complete NSF-1 schema for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Narratives table implementing NSF-1 schema
CREATE TABLE narratives (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metadata Dimension
    title VARCHAR(500) NOT NULL,
    summary TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1,
    
    -- Temporal Dimension
    temporal_data JSONB NOT NULL DEFAULT '{}',
    -- Contains: timeline, key_events, evolution_stages, temporal_markers
    
    -- Spatial Dimension  
    spatial_data JSONB NOT NULL DEFAULT '{}',
    -- Contains: geographic_scope, locations, spatial_entities
    
    -- Actor Dimension
    actor_data JSONB NOT NULL DEFAULT '{}',
    -- Contains: key_entities, roles, relationships, influence_scores
    
    -- Thematic Dimension
    thematic_data JSONB NOT NULL DEFAULT '{}',
    -- Contains: core_themes, sub_narratives, topic_clusters
    
    -- Evidential Dimension
    evidential_data JSONB NOT NULL DEFAULT '{}',
    -- Contains: supporting_articles, confidence_scores, source_reliability
    
    -- Relational Dimension
    relational_data JSONB NOT NULL DEFAULT '{}'
    -- Contains: related_narratives, contradiction_links, evolution_chains
);

-- Indexes for efficient querying
CREATE INDEX idx_narratives_confidence ON narratives(confidence);
CREATE INDEX idx_narratives_temporal ON narratives USING GIN(temporal_data);
CREATE INDEX idx_narratives_spatial ON narratives USING GIN(spatial_data);
CREATE INDEX idx_narratives_thematic ON narratives USING GIN(thematic_data);
CREATE INDEX idx_narratives_updated_at ON narratives(updated_at);

-- Articles table
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url VARCHAR(2048) UNIQUE,
    published_date TIMESTAMP,
    ingested_date TIMESTAMP DEFAULT NOW(),
    source_id INTEGER REFERENCES news_sources(id),
    language VARCHAR(10),
    word_count INTEGER,
    metadata JSONB DEFAULT '{}'
) PARTITION BY RANGE (published_date);

-- Article embeddings for vector search
CREATE TABLE article_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    embedding vector(768),
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON article_embeddings USING ivfflat (embedding vector_cosine_ops);

-- Clusters table for ML pipeline results
CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stage VARCHAR(20) NOT NULL, -- CLUST-1, CLUST-2, CLUST-3, CLUST-4
    pipeline_run_id UUID NOT NULL,
    cluster_data JSONB NOT NULL,
    article_ids UUID[] NOT NULL,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 8.6 Monitoring and Observability Integration

**Metrics Collection Contracts:**
```python
# Prometheus metrics integration
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Service-level metrics
REQUEST_COUNT = Counter(
    'api_requests_total', 
    'Total API requests', 
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

PIPELINE_DURATION = Histogram(
    'pipeline_duration_seconds',
    'ML pipeline execution time',
    ['stage', 'status']
)

NARRATIVE_COUNT = Gauge(
    'active_narratives_total',
    'Total active narratives'
)

ARTICLE_INGESTION_RATE = Counter(
    'articles_ingested_total',
    'Total articles ingested',
    ['source', 'language']
)

# Custom middleware for metrics collection
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path, 
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method, 
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

## 9. Data Flow Architecture and Processing Pipelines

### 9.1 Complete Data Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            STRATEGIC NARRATIVE INTELLIGENCE                     │
│                                  DATA FLOW ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NEWS SOURCES  │    │   INGESTION     │    │  PREPROCESSING  │    │   ML PIPELINE   │
│                 │    │   LAYER         │    │     LAYER       │    │     LAYER       │
│ • RSS Feeds     │────│                 │────│                 │────│                 │
│ • API Sources   │    │ • Feed Manager  │    │ • Language Det. │    │ • Embedding     │
│ • Web Scraping  │    │ • Content Parse │    │ • Deduplication │    │ • Clustering    │
│ • 50-80 Sources │    │ • Validation    │    │ • Normalization │    │ • Anomaly Det.  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                               PERSISTENT STORAGE                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  Raw Articles   │  │   Embeddings    │  │    Clusters     │  │    Narratives    │  │
│  │   PostgreSQL    │  │   pgvector      │  │   PostgreSQL    │  │  NSF-1 Schema    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────────────┘
                                                │
                                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GENERATION    │    │    NARRATIVE    │    │      API        │    │   REAL-TIME     │
│   PIPELINE      │    │    SERVICE      │    │    GATEWAY      │    │    UPDATES     │
│                 │    │                 │    │                 │    │                 │
│ • GEN-1 Builder │────│ • NSF-1 Mgmt   │────│ • Query Proc.   │────│ • WebSocket     │
│ • GEN-2 Updates │    │ • Updates       │    │ • Auth/Rate     │    │ • Notifications │
│ • GEN-3 Resolve │    │ • Versioning    │    │ • Caching       │    │ • Live Events   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                            ┌─────────────────┐
                                            │   FRONTEND      │
                                            │   CLIENTS       │
                                            │                 │
                                            │ • React Web App │
                                            │ • Admin Portal  │
                                            │ • Mobile Apps   │
                                            └─────────────────┘
```

### 9.2 Daily Pipeline Execution Flow

**Automated Daily Processing:**
```python
# Daily pipeline orchestration
import asyncio
from datetime import datetime, timedelta
from celery import chain, group
from typing import List, Dict

class DailyPipelineOrchestrator:
    def __init__(self):
        self.pipeline_id = None
        self.start_time = None
        self.stages = []
    
    async def execute_daily_pipeline(self) -> str:
        """Execute complete daily narrative intelligence pipeline"""
        self.pipeline_id = f"daily_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        
        try:
            # Stage 1: News Ingestion (30 minutes)
            ingestion_result = await self._execute_ingestion_stage()
            
            # Stage 2: ML Pipeline - CLUST-1-4 (2.5 hours)
            clustering_result = await self._execute_clustering_stage(ingestion_result)
            
            # Stage 3: Generation Pipeline - GEN-1-3 (1 hour)
            generation_result = await self._execute_generation_stage(clustering_result)
            
            # Stage 4: Quality Assurance & Publishing (30 minutes)
            final_result = await self._execute_qa_stage(generation_result)
            
            await self._send_completion_notification(final_result)
            return final_result
            
        except Exception as e:
            await self._handle_pipeline_failure(e)
            raise
    
    async def _execute_ingestion_stage(self) -> Dict:
        """Stage 1: Ingest new articles from all sources"""
        print(f"[{datetime.now()}] Starting ingestion stage...")
        
        # Get cutoff time (articles since last successful run)
        last_run = await self._get_last_successful_run()
        cutoff_time = last_run or (datetime.now() - timedelta(hours=24))
        
        # Parallel ingestion from all sources
        ingestion_tasks = []
        news_sources = await self._get_active_news_sources()
        
        for source in news_sources:
            task = self._ingest_from_source.delay(source.id, cutoff_time)
            ingestion_tasks.append(task)
        
        # Wait for all ingestion tasks
        results = await asyncio.gather(*ingestion_tasks, return_exceptions=True)
        
        # Aggregate results
        total_articles = 0
        failed_sources = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_sources.append(news_sources[i].name)
            else:
                total_articles += result.get('article_count', 0)
        
        stage_result = {
            'stage': 'ingestion',
            'total_articles': total_articles,
            'failed_sources': failed_sources,
            'completion_time': datetime.now(),
            'duration': datetime.now() - self.start_time
        }
        
        self.stages.append(stage_result)
        print(f"Ingestion completed: {total_articles} articles ingested")
        return stage_result
    
    async def _execute_clustering_stage(self, ingestion_result: Dict) -> Dict:
        """Stage 2: Execute CLUST-1 through CLUST-4"""
        print(f"[{datetime.now()}] Starting clustering stage...")
        stage_start = datetime.now()
        
        # Get new articles for processing
        new_articles = await self._get_articles_since(ingestion_result['completion_time'])
        
        if len(new_articles) < 10:
            print("Insufficient new articles for clustering, skipping...")
            return {'stage': 'clustering', 'skipped': True, 'reason': 'insufficient_data'}
        
        # CLUST-1: Thematic Clustering
        clust1_result = await self._execute_clust1(new_articles)
        
        # CLUST-2: Interpretive Segmentation
        clust2_result = await self._execute_clust2(clust1_result['clusters'])
        
        # CLUST-3: Temporal Anomaly Detection
        clust3_result = await self._execute_clust3(clust2_result['segments'])
        
        # CLUST-4: Consolidation & Refinement
        clust4_result = await self._execute_clust4(clust3_result['anomalies'])
        
        stage_result = {
            'stage': 'clustering',
            'articles_processed': len(new_articles),
            'final_clusters': len(clust4_result['refined_clusters']),
            'completion_time': datetime.now(),
            'duration': datetime.now() - stage_start,
            'clust_results': {
                'clust1': clust1_result,
                'clust2': clust2_result, 
                'clust3': clust3_result,
                'clust4': clust4_result
            }
        }
        
        self.stages.append(stage_result)
        print(f"Clustering completed: {len(clust4_result['refined_clusters'])} final clusters")
        return stage_result
    
    async def _execute_generation_stage(self, clustering_result: Dict) -> Dict:
        """Stage 3: Execute GEN-1 through GEN-3"""
        print(f"[{datetime.now()}] Starting generation stage...")
        stage_start = datetime.now()
        
        clusters = clustering_result['clust_results']['clust4']['refined_clusters']
        
        # GEN-1: Narrative Builder
        gen1_result = await self._execute_gen1(clusters)
        
        # GEN-2: Updates & Enhancement
        gen2_result = await self._execute_gen2(gen1_result['new_narratives'])
        
        # GEN-3: Contradiction Detection & Resolution
        gen3_result = await self._execute_gen3(gen2_result['updated_narratives'])
        
        stage_result = {
            'stage': 'generation',
            'new_narratives': len(gen1_result['new_narratives']),
            'updated_narratives': len(gen2_result['updated_narratives']),
            'contradictions_resolved': len(gen3_result['resolved_contradictions']),
            'completion_time': datetime.now(),
            'duration': datetime.now() - stage_start,
            'gen_results': {
                'gen1': gen1_result,
                'gen2': gen2_result,
                'gen3': gen3_result
            }
        }
        
        self.stages.append(stage_result)
        print(f"Generation completed: {stage_result['new_narratives']} new narratives")
        return stage_result
```

### 9.3 Real-time RAI (Rapid Analysis Intelligence) Flow

**On-Demand Analysis Pipeline:**
```python
class RAIProcessor:
    def __init__(self):
        self.rai_queue = "rai_urgent"
        self.timeout = 300  # 5 minutes
    
    async def process_rai_request(self, query: RAIQuery, user_id: str) -> RAIResult:
        """Process urgent analysis request within 5 minutes"""
        rai_id = f"rai_{uuid.uuid4().hex[:8]}"
        start_time = datetime.now()
        
        try:
            # Step 1: Query Understanding (30 seconds)
            parsed_query = await self._parse_rai_query(query)
            
            # Step 2: Relevant Data Retrieval (60 seconds)
            relevant_data = await self._retrieve_relevant_data(parsed_query)
            
            # Step 3: Rapid Clustering (90 seconds)
            clusters = await self._rapid_clustering(relevant_data)
            
            # Step 4: Narrative Synthesis (90 seconds)
            narrative = await self._synthesize_narrative(clusters, parsed_query)
            
            # Step 5: Quality Check (10 seconds)
            validated_result = await self._validate_rai_result(narrative)
            
            duration = datetime.now() - start_time
            
            result = RAIResult(
                rai_id=rai_id,
                query=query.query_text,
                narrative=validated_result,
                confidence=validated_result.confidence,
                processing_time=duration.total_seconds(),
                data_freshness=self._calculate_data_freshness(relevant_data),
                sources_used=len(relevant_data['articles'])
            )
            
            # Cache result for potential follow-up queries
            await self._cache_rai_result(rai_id, result)
            
            return result
            
        except TimeoutError:
            return RAIResult(
                rai_id=rai_id,
                error="Analysis timeout - query too complex for 5-minute window",
                processing_time=self.timeout
            )
    
    async def _rapid_clustering(self, data: Dict) -> List[RapidCluster]:
        """Optimized clustering for speed over completeness"""
        articles = data['articles']
        
        # Use pre-computed embeddings when available
        embeddings = await self._get_cached_embeddings(articles)
        
        # Fast clustering with reduced precision
        clusterer = FastHDBSCAN(
            min_cluster_size=3,
            min_samples=2,
            cluster_selection_epsilon=0.3
        )
        
        cluster_labels = clusterer.fit_predict(embeddings)
        
        clusters = []
        for label in set(cluster_labels):
            if label != -1:  # Ignore noise
                cluster_articles = [articles[i] for i, l in enumerate(cluster_labels) if l == label]
                
                cluster = RapidCluster(
                    id=f"rapid_cluster_{label}",
                    articles=cluster_articles,
                    theme=await self._extract_rapid_theme(cluster_articles),
                    confidence=self._calculate_cluster_confidence(cluster_articles)
                )
                clusters.append(cluster)
        
        return clusters
```

### 9.4 Data Quality and Monitoring Flow

**Quality Assurance Pipeline:**
```python
class DataQualityManager:
    def __init__(self):
        self.quality_metrics = {}
        self.alert_thresholds = {
            'article_ingestion_rate': 0.8,  # 80% of expected rate
            'clustering_quality': 0.7,      # 70% coherence minimum
            'narrative_confidence': 0.6,    # 60% confidence minimum
            'source_reliability': 0.75      # 75% reliability threshold
        }
    
    async def monitor_pipeline_quality(self, pipeline_result: Dict) -> QualityReport:
        """Comprehensive quality monitoring across all pipeline stages"""
        
        report = QualityReport(
            pipeline_id=pipeline_result['pipeline_id'],
            timestamp=datetime.now()
        )
        
        # Ingestion Quality Metrics
        ingestion_quality = await self._assess_ingestion_quality(
            pipeline_result['stages'][0]
        )
        report.add_section('ingestion', ingestion_quality)
        
        # Clustering Quality Metrics
        clustering_quality = await self._assess_clustering_quality(
            pipeline_result['stages'][1]
        )
        report.add_section('clustering', clustering_quality)
        
        # Generation Quality Metrics
        generation_quality = await self._assess_generation_quality(
            pipeline_result['stages'][2]
        )
        report.add_section('generation', generation_quality)
        
        # Overall Pipeline Health
        overall_health = self._calculate_overall_health(report)
        report.overall_score = overall_health
        
        # Generate alerts if thresholds exceeded
        alerts = await self._generate_quality_alerts(report)
        report.alerts = alerts
        
        return report
    
    async def _assess_clustering_quality(self, clustering_result: Dict) -> Dict:
        """Assess quality of clustering operations"""
        clust4_result = clustering_result['clust_results']['clust4']
        clusters = clust4_result['refined_clusters']
        
        # Calculate silhouette score for cluster quality
        silhouette_scores = []
        for cluster in clusters:
            if len(cluster['articles']) > 2:
                score = await self._calculate_silhouette_score(cluster)
                silhouette_scores.append(score)
        
        avg_silhouette = np.mean(silhouette_scores) if silhouette_scores else 0
        
        # Calculate cluster coherence
        coherence_scores = []
        for cluster in clusters:
            coherence = await self._calculate_topic_coherence(cluster)
            coherence_scores.append(coherence)
        
        avg_coherence = np.mean(coherence_scores) if coherence_scores else 0
        
        # Assess temporal anomaly detection effectiveness
        anomaly_precision = await self._assess_anomaly_precision(
            clustering_result['clust_results']['clust3']
        )
        
        return {
            'avg_silhouette_score': avg_silhouette,
            'avg_coherence_score': avg_coherence,
            'anomaly_detection_precision': anomaly_precision,
            'total_clusters': len(clusters),
            'quality_grade': self._grade_clustering_quality(avg_silhouette, avg_coherence)
        }
```

### 9.5 Error Handling and Recovery Flow

**Resilient Pipeline Architecture:**
```python
class PipelineRecoveryManager:
    def __init__(self):
        self.recovery_strategies = {
            'ingestion_failure': self._recover_ingestion_failure,
            'clustering_failure': self._recover_clustering_failure,
            'generation_failure': self._recover_generation_failure,
            'data_corruption': self._recover_data_corruption
        }
    
    async def handle_pipeline_failure(self, error: Exception, stage: str, context: Dict):
        """Intelligent error recovery based on failure type and stage"""
        
        failure_type = self._classify_failure(error, stage)
        
        print(f"Pipeline failure detected: {failure_type} in stage {stage}")
        
        # Attempt recovery
        recovery_strategy = self.recovery_strategies.get(failure_type)
        if recovery_strategy:
            try:
                recovery_result = await recovery_strategy(error, context)
                if recovery_result['success']:
                    print(f"Recovery successful: {recovery_result['message']}")
                    return recovery_result
            except Exception as recovery_error:
                print(f"Recovery failed: {recovery_error}")
        
        # If recovery fails, implement graceful degradation
        return await self._graceful_degradation(failure_type, stage, context)
    
    async def _recover_ingestion_failure(self, error: Exception, context: Dict) -> Dict:
        """Recover from news ingestion failures"""
        failed_sources = context.get('failed_sources', [])
        
        # Retry failed sources with exponential backoff
        retry_results = []
        for source in failed_sources:
            retry_result = await self._retry_source_ingestion(source, max_retries=3)
            retry_results.append(retry_result)
        
        successful_retries = [r for r in retry_results if r['success']]
        
        if len(successful_retries) > len(failed_sources) * 0.7:  # 70% recovery rate
            return {
                'success': True,
                'message': f"Recovered {len(successful_retries)}/{len(failed_sources)} sources",
                'recovered_sources': successful_retries
            }
        
        # Partial recovery - continue with available data
        return {
            'success': False,
            'partial_recovery': True,
            'message': f"Partial recovery: {len(successful_retries)} sources recovered",
            'continue_pipeline': len(successful_retries) > 0
        }
    
    async def _graceful_degradation(self, failure_type: str, stage: str, context: Dict) -> Dict:
        """Implement graceful degradation when recovery fails"""
        
        if stage == 'ingestion':
            # Use cached articles from recent runs
            cached_articles = await self._get_cached_articles(hours=48)
            if len(cached_articles) > 100:
                return {
                    'degraded_mode': True,
                    'message': f"Using {len(cached_articles)} cached articles",
                    'continue_pipeline': True,
                    'data_source': 'cache'
                }
        
        elif stage == 'clustering':
            # Use simpler clustering algorithm
            return {
                'degraded_mode': True,
                'message': "Falling back to simple k-means clustering",
                'continue_pipeline': True,
                'algorithm': 'k_means_fallback'
            }
        
        elif stage == 'generation':
            # Use template-based generation instead of LLM
            return {
                'degraded_mode': True,
                'message': "Using template-based narrative generation",
                'continue_pipeline': True,
                'method': 'template_generation'
            }
        
        # Complete failure - abort pipeline
        return {
            'success': False,
            'degraded_mode': False,
            'message': f"Pipeline aborted at stage {stage}",
            'continue_pipeline': False
        }
```

### 9.6 Performance Optimization Flow

**Adaptive Performance Management:**
```python
class PerformanceOptimizer:
    def __init__(self):
        self.performance_history = {}
        self.optimization_strategies = {}
    
    async def optimize_pipeline_performance(self, pipeline_metrics: Dict) -> Dict:
        """Dynamically optimize pipeline performance based on metrics"""
        
        optimizations = []
        
        # Optimize ingestion based on source performance
        ingestion_opts = await self._optimize_ingestion(pipeline_metrics['ingestion'])
        optimizations.extend(ingestion_opts)
        
        # Optimize clustering based on data characteristics
        clustering_opts = await self._optimize_clustering(pipeline_metrics['clustering'])
        optimizations.extend(clustering_opts)
        
        # Optimize generation based on narrative quality vs speed
        generation_opts = await self._optimize_generation(pipeline_metrics['generation'])
        optimizations.extend(generation_opts)
        
        return {
            'optimizations_applied': optimizations,
            'expected_improvement': self._calculate_expected_improvement(optimizations),
            'next_optimization_check': datetime.now() + timedelta(days=7)
        }
    
    async def _optimize_clustering(self, clustering_metrics: Dict) -> List[Dict]:
        """Optimize clustering performance"""
        optimizations = []
        
        avg_cluster_time = clustering_metrics.get('avg_processing_time', 0)
        cluster_quality = clustering_metrics.get('avg_coherence_score', 0)
        
        # If clustering is slow but high quality, consider parallelization
        if avg_cluster_time > 1800 and cluster_quality > 0.8:  # 30 minutes, 80% quality
            optimizations.append({
                'type': 'parallelization',
                'description': 'Enable parallel clustering processing',
                'expected_speedup': 0.4,  # 40% faster
                'quality_impact': -0.05   # 5% quality decrease
            })
        
        # If quality is low, suggest algorithm tuning
        if cluster_quality < 0.7:
            optimizations.append({
                'type': 'algorithm_tuning',
                'description': 'Adjust clustering parameters for better quality',
                'expected_speedup': -0.1,  # 10% slower
                'quality_impact': 0.15     # 15% quality increase
            })
        
        return optimizations
```

This comprehensive architecture provides a production-ready, scalable foundation for your Strategic Narrative Intelligence platform. The design emphasizes:

1. **Resilience**: Multiple fallback strategies and graceful degradation
2. **Scalability**: Horizontal scaling patterns and optimization strategies  
3. **Security**: Multi-layered security with encryption and compliance
4. **Observability**: Comprehensive monitoring and quality assurance
5. **Flexibility**: Modular design allowing for easy component updates
6. **Performance**: Optimized data flows and caching strategies

The architecture can handle the complex ML/NLP pipeline requirements while maintaining the reliability needed for strategic intelligence operations.