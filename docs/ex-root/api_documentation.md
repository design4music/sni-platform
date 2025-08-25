# Strategic Narrative Intelligence API Documentation

## Overview

The Strategic Narrative Intelligence API provides comprehensive access to narrative analysis, clustering, and real-time intelligence capabilities. This REST API supports rapid development cycles and enables building sophisticated frontends for narrative exploration and analysis.

## Base Information

- **Base URL**: `https://api.strategicnarrative.com/api/v1`
- **Authentication**: Bearer Token (JWT)
- **Content Type**: `application/json`
- **Rate Limiting**: Varies by endpoint (see individual endpoint documentation)
- **API Version**: 1.0.0

## Authentication Strategy

### JWT Token-Based Authentication

```http
Authorization: Bearer <access_token>
```

**Token Lifecycle:**
- Access tokens expire after 30 minutes
- Refresh tokens expire after 7 days
- Automatic token refresh via `/auth/refresh` endpoint

### API Key Authentication (Alternative)

```http
X-API-Key: <api_key>
```

**Rate Limits by Role:**
- **Viewer**: 100 requests/minute
- **Analyst**: 500 requests/minute  
- **Admin**: 1000 requests/minute

## Error Handling

### Standard Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {
    "field": "specific error details"
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_abc123"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no content returned |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (duplicate, etc.) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Validation Error Response

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "validation_errors": [
    {
      "field": "email",
      "message": "Invalid email format",
      "invalid_value": "not-an-email"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Rate Limiting Strategy

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
X-RateLimit-Retry-After: 60
```

### Rate Limits by Endpoint Type

| Endpoint Type | Rate Limit | Burst Limit |
|---------------|------------|-------------|
| Authentication | 10/minute | 20/hour |
| Search | 50/minute | 200/hour |
| Narratives (GET) | 100/minute | 1000/hour |
| Narratives (POST/PUT) | 20/minute | 100/hour |
| Analytics | 50/minute | 500/hour |
| WebSocket Connections | 10/minute | 50/hour |
| Pipeline Tasks | 10/minute | 50/hour |
| Admin Operations | 20/minute | 100/hour |

### Rate Limit Exceeded Response

```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again in 60 seconds.",
  "details": {
    "limit": 100,
    "window": "1 minute",
    "retry_after": 60
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Pagination Pattern

### Request Parameters

```http
GET /api/v1/narratives?page=1&size=20
```

### Response Format

```json
{
  "items": [...],
  "total": 1250,
  "page": 1,
  "size": 20,
  "pages": 63,
  "has_next": true,
  "has_prev": false
}
```

### Pagination Limits

- **Default page size**: 20 items
- **Maximum page size**: 100 items
- **Maximum pages**: 500 (use filters to narrow results)

## Caching Strategy

### Cache Headers

```http
Cache-Control: public, max-age=300
ETag: "abc123def456"
Last-Modified: Mon, 15 Jan 2024 10:30:00 GMT
```

### Cache Levels

1. **CDN Cache**: 5 minutes for public endpoints
2. **API Cache**: 2 minutes for computed data
3. **Database Cache**: Query result caching
4. **Client Cache**: ETags for conditional requests

### Cache Invalidation

- Real-time updates via WebSocket
- Cache-busting on data modifications
- Stale-while-revalidate for improved UX

## API Versioning Approach

### URL Versioning

```http
GET /api/v1/narratives
GET /api/v2/narratives
```

### Version Lifecycle

| Version | Status | Support Until | Breaking Changes |
|---------|--------|---------------|------------------|
| v1.0 | Active | 2025-12-31 | None planned |
| v2.0 | Development | TBD | Enhanced filtering |

### Deprecation Headers

```http
Sunset: Sat, 31 Dec 2025 23:59:59 GMT
Deprecation: true
Link: </api/v2/narratives>; rel="successor-version"
```

---

# Endpoint Documentation

## Authentication Endpoints

### POST /api/v1/auth/register

Register a new user account.

**Rate Limit**: 5/minute

**Request Body**:
```json
{
  "username": "analyst1",
  "email": "analyst@company.com",
  "password": "SecurePassword123!",
  "role": "analyst"
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "analyst1",
  "email": "analyst@company.com",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validation Rules**:
- `username`: 3-50 characters, alphanumeric + underscore
- `email`: Valid email format
- `password`: Minimum 8 characters, mixed case + numbers + symbols
- `role`: One of: viewer, analyst, admin

### POST /api/v1/auth/login

Authenticate user and return access tokens.

**Rate Limit**: 10/minute

**Request Body**:
```json
{
  "username": "analyst1",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### POST /api/v1/auth/refresh

Refresh access token using refresh token.

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### GET /api/v1/auth/me

Get current user information.

**Headers**: `Authorization: Bearer <token>`

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "analyst1",
  "email": "analyst@company.com",
  "role": "analyst",
  "is_active": true,
  "last_login": "2024-01-15T10:25:00Z",
  "created_at": "2024-01-15T09:00:00Z"
}
```

---

## Narrative Endpoints

### GET /api/v1/narratives

Get paginated list of narratives with filtering.

**Rate Limit**: 100/minute

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (≥1) |
| `size` | integer | 20 | Items per page (1-100) |
| `topic` | string | - | Filter by topic |
| `alignment` | enum | - | positive, negative, neutral, mixed |
| `status` | enum | - | active, emerging, declining, dormant |
| `trending` | enum | - | 1h, 6h, 24h, 7d, 30d |

**Example Request**:
```http
GET /api/v1/narratives?page=1&size=20&topic=Technology&alignment=positive&trending=24h
```

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "AI Revolution in Healthcare",
      "topic": "Technology",
      "alignment": "positive",
      "status": "active",
      "confidence_score": 0.89,
      "impact_score": 0.76,
      "article_count": 234,
      "trend_momentum": 0.23,
      "last_activity": "2024-01-15T10:25:00Z"
    }
  ],
  "total": 1250,
  "page": 1,
  "size": 20,
  "pages": 63,
  "has_next": true,
  "has_prev": false
}
```

### GET /api/v1/narratives/{narrative_id}

Get detailed narrative information by ID.

**Rate Limit**: 200/minute

**Path Parameters**:
- `narrative_id` (UUID): Narrative identifier

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_timeline` | boolean | true | Include timeline events |
| `include_excerpts` | boolean | true | Include source excerpts |
| `include_tensions` | boolean | false | Include narrative tensions |

**Example Request**:
```http
GET /api/v1/narratives/550e8400-e29b-41d4-a716-446655440000?include_tensions=true
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "AI Revolution in Healthcare",
  "description": "Comprehensive analysis of AI adoption in healthcare systems worldwide, focusing on diagnostic improvements and patient outcomes.",
  "topic": "Technology",
  "alignment": "positive",
  "status": "active",
  "confidence_score": 0.89,
  "impact_score": 0.76,
  "tags": ["healthcare", "artificial-intelligence", "diagnostics"],
  "timeline": [
    {
      "timestamp": "2024-01-10T08:00:00Z",
      "event_description": "Major breakthrough in AI-powered medical imaging announced by Stanford",
      "impact_score": 0.8,
      "supporting_articles": ["660e8400-e29b-41d4-a716-446655440001"]
    }
  ],
  "source_excerpts": [
    {
      "article_id": "660e8400-e29b-41d4-a716-446655440001",
      "excerpt": "The new AI system demonstrated 95% accuracy in detecting early-stage tumors, significantly outperforming traditional methods.",
      "relevance_score": 0.92,
      "timestamp": "2024-01-10T08:15:00Z"
    }
  ],
  "tensions": [
    {
      "opposing_narrative_id": "770e8400-e29b-41d4-a716-446655440002",
      "tension_score": 0.65,
      "key_differences": ["Privacy concerns vs. medical benefits", "Cost implications"],
      "timeline_overlap": {"overlap_score": 0.3}
    }
  ],
  "cluster_id": "880e8400-e29b-41d4-a716-446655440003",
  "article_count": 234,
  "trend_momentum": 0.23,
  "last_activity": "2024-01-15T10:25:00Z",
  "created_at": "2024-01-05T12:00:00Z",
  "updated_at": "2024-01-15T10:25:00Z"
}
```

### POST /api/v1/narratives

Create a new narrative.

**Rate Limit**: 20/minute  
**Required Role**: analyst

**Request Body**:
```json
{
  "title": "New Narrative Title",
  "description": "Detailed description of the narrative",
  "topic": "Technology",
  "alignment": "positive",
  "status": "emerging",
  "confidence_score": 0.75,
  "impact_score": 0.60,
  "tags": ["technology", "innovation"]
}
```

**Response** (201 Created):
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "title": "New Narrative Title",
  "description": "Detailed description of the narrative",
  "topic": "Technology",
  "alignment": "positive",
  "status": "emerging",
  "confidence_score": 0.75,
  "impact_score": 0.60,
  "tags": ["technology", "innovation"],
  "timeline": [],
  "source_excerpts": [],
  "tensions": [],
  "article_count": 0,
  "trend_momentum": 0.0,
  "last_activity": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### PUT /api/v1/narratives/{narrative_id}

Update an existing narrative.

**Rate Limit**: 50/minute  
**Required Role**: analyst

**Request Body** (partial update allowed):
```json
{
  "title": "Updated Narrative Title",
  "status": "active",
  "confidence_score": 0.85,
  "tags": ["technology", "innovation", "healthcare"]
}
```

### DELETE /api/v1/narratives/{narrative_id}

Delete a narrative (soft delete).

**Rate Limit**: 10/minute  
**Required Role**: admin

**Response**: 204 No Content

---

## Article Endpoints

### GET /api/v1/articles

Get paginated list of articles with filtering.

**Rate Limit**: 100/minute

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `size` | integer | 20 | Items per page |
| `source_type` | enum | - | news, social, blog, academic, government |
| `language` | string | - | ISO 639-1 language code |
| `date_from` | datetime | - | Filter articles after this date |
| `date_to` | datetime | - | Filter articles before this date |

**Example Request**:
```http
GET /api/v1/articles?source_type=news&language=en&date_from=2024-01-01T00:00:00Z
```

### GET /api/v1/articles/{article_id}

Get article by ID.

**Rate Limit**: 200/minute

**Response** (200 OK):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "title": "Breakthrough in AI Medical Imaging",
  "content": "Full article content...",
  "url": "https://example.com/article",
  "author": "Dr. Jane Smith",
  "published_at": "2024-01-10T08:00:00Z",
  "source": {
    "name": "Medical News Today",
    "type": "news",
    "url": "https://medicalnewstoday.com",
    "credibility_score": 0.87,
    "bias_score": 0.05
  },
  "language": "en",
  "tags": ["healthcare", "ai", "medical-imaging"],
  "sentiment_score": 0.65,
  "relevance_score": 0.89,
  "narrative_ids": ["550e8400-e29b-41d4-a716-446655440000"],
  "created_at": "2024-01-10T08:15:00Z",
  "updated_at": "2024-01-10T08:15:00Z"
}
```

### POST /api/v1/articles

Create a new article.

**Rate Limit**: 50/minute  
**Required Role**: analyst

**Request Body**:
```json
{
  "title": "Article Title",
  "content": "Full article content...",
  "url": "https://example.com/unique-article",
  "author": "Author Name",
  "published_at": "2024-01-15T10:00:00Z",
  "source": {
    "name": "Example News",
    "type": "news",
    "url": "https://example.com",
    "credibility_score": 0.75,
    "bias_score": 0.1
  },
  "language": "en",
  "tags": ["tag1", "tag2"]
}
```

---

## Search Endpoints

### POST /api/v1/search

Advanced search with filtering and faceting.

**Rate Limit**: 100/minute

**Request Body**:
```json
{
  "query": "artificial intelligence healthcare",
  "filters": {
    "topics": ["Technology", "Healthcare"],
    "alignments": ["positive"],
    "statuses": ["active", "emerging"],
    "source_types": ["news", "academic"],
    "date_from": "2024-01-01T00:00:00Z",
    "date_to": "2024-01-15T23:59:59Z",
    "min_confidence": 0.7,
    "min_impact": 0.5,
    "trending_period": "24h"
  },
  "sort_by": "relevance",
  "sort_order": "desc"
}
```

**Response** (200 OK):
```json
{
  "narratives": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "AI Revolution in Healthcare",
      "topic": "Technology",
      "alignment": "positive",
      "status": "active",
      "confidence_score": 0.89,
      "impact_score": 0.76,
      "article_count": 234,
      "trend_momentum": 0.23,
      "last_activity": "2024-01-15T10:25:00Z"
    }
  ],
  "total": 42,
  "query_time_ms": 23.5,
  "suggestions": [
    "artificial intelligence in medicine",
    "AI diagnostic tools",
    "machine learning healthcare"
  ],
  "facets": {
    "topics": {
      "Technology": 25,
      "Healthcare": 17
    },
    "alignments": {
      "positive": 30,
      "neutral": 8,
      "negative": 4
    },
    "statuses": {
      "active": 35,
      "emerging": 7
    }
  }
}
```

### GET /api/v1/search/suggestions

Get search query suggestions for autocomplete.

**Rate Limit**: 50/minute

**Query Parameters**:
- `query` (string, required): Partial search query (min 2 chars)
- `limit` (integer, optional): Max suggestions (1-20, default 10)

**Example Request**:
```http
GET /api/v1/search/suggestions?query=artific&limit=5
```

**Response** (200 OK):
```json
[
  "artificial intelligence",
  "artificial intelligence healthcare",
  "artificial intelligence ethics",
  "artificial neural networks",
  "artificial intelligence automation"
]
```

---

## Analytics Endpoints

### GET /api/v1/analytics/trending

Get trending narratives for specified time period.

**Rate Limit**: 50/minute

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | enum | 24h | 1h, 6h, 24h, 7d, 30d |
| `limit` | integer | 20 | Max results (1-100) |

**Example Request**:
```http
GET /api/v1/analytics/trending?period=24h&limit=10
```

**Response** (200 OK):
```json
[
  {
    "narrative_id": "550e8400-e29b-41d4-a716-446655440000",
    "period": "24h",
    "growth_rate": 1.75,
    "velocity": 0.85,
    "acceleration": 0.25,
    "volume": 156,
    "engagement_score": 0.78
  }
]
```

### GET /api/v1/analytics/temporal/{narrative_id}

Get temporal analytics for a specific narrative.

**Rate Limit**: 100/minute

**Path Parameters**:
- `narrative_id` (UUID): Narrative identifier

**Query Parameters**:
- `period` (enum): Time window (1h, 6h, 24h, 7d, 30d)

**Response** (200 OK):
```json
{
  "narrative_id": "550e8400-e29b-41d4-a716-446655440000",
  "time_series": {
    "2024-01-15T08:00:00Z": 0.75,
    "2024-01-15T09:00:00Z": 0.82,
    "2024-01-15T10:00:00Z": 0.89
  },
  "trend_direction": "up",
  "seasonality_detected": false,
  "anomalies": ["2024-01-14T15:30:00Z"],
  "forecast_7d": [0.91, 0.94, 0.89, 0.85, 0.88, 0.92, 0.87]
}
```

### GET /api/v1/analytics/global

Get global platform metrics.

**Rate Limit**: 20/minute

**Response** (200 OK):
```json
{
  "total_narratives": 1250,
  "active_narratives": 850,
  "total_articles": 45000,
  "articles_last_24h": 350,
  "top_topics": [
    {"topic": "Technology", "count": 125},
    {"topic": "Politics", "count": 98},
    {"topic": "Healthcare", "count": 87}
  ],
  "sentiment_distribution": {
    "positive": 400,
    "negative": 250,
    "neutral": 350,
    "mixed": 250
  },
  "processing_lag_minutes": 2.5
}
```

---

## Clustering Endpoints

### GET /api/v1/clusters

Get list of narrative clusters.

**Rate Limit**: 50/minute

**Query Parameters**:
- `min_size` (integer): Minimum cluster size (default: 5)
- `min_coherence` (float): Minimum coherence score (0-1, default: 0.5)

**Response** (200 OK):
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "name": "AI Healthcare Cluster",
    "description": "Narratives focused on AI applications in healthcare",
    "centroid_vector": [0.1, 0.2, 0.3, ...],
    "coherence_score": 0.87,
    "size": 25,
    "narrative_ids": ["550e8400-e29b-41d4-a716-446655440000", ...],
    "representative_articles": ["660e8400-e29b-41d4-a716-446655440001", ...],
    "topic_keywords": ["healthcare", "artificial-intelligence", "medical"],
    "temporal_distribution": {
      "2024-01-01": 5,
      "2024-01-02": 8,
      "2024-01-03": 12
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

### GET /api/v1/clusters/{cluster_id}

Get cluster details by ID.

**Rate Limit**: 100/minute

---

## Pipeline Endpoints

### POST /api/v1/pipeline/tasks

Create and queue a new pipeline task.

**Rate Limit**: 20/minute  
**Required Role**: analyst

**Request Body**:
```json
{
  "type": "cluster",
  "parameters": {
    "algorithm": "kmeans",
    "min_size": 5,
    "max_clusters": 20
  },
  "priority": 5
}
```

**Response** (201 Created):
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "type": "cluster",
  "status": "pending",
  "progress": 0.0,
  "parameters": {
    "algorithm": "kmeans",
    "min_size": 5,
    "max_clusters": 20
  },
  "result": null,
  "error_message": null,
  "started_at": null,
  "completed_at": null,
  "estimated_duration_seconds": 1800,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/pipeline/tasks

List pipeline tasks with optional filtering.

**Rate Limit**: 50/minute  
**Required Role**: analyst

**Query Parameters**:
- `status_filter` (enum): pending, running, completed, failed
- `limit` (integer): Max results (1-100, default: 20)

### GET /api/v1/pipeline/tasks/{task_id}

Get pipeline task status and results.

**Rate Limit**: 100/minute  
**Required Role**: analyst

**Response** (200 OK):
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "type": "cluster",
  "status": "completed",
  "progress": 100.0,
  "parameters": {
    "algorithm": "kmeans",
    "min_size": 5,
    "max_clusters": 20
  },
  "result": {
    "clusters_created": 15,
    "narratives_clustered": 180,
    "avg_coherence_score": 0.78
  },
  "error_message": null,
  "started_at": "2024-01-15T10:35:00Z",
  "completed_at": "2024-01-15T11:05:00Z",
  "estimated_duration_seconds": 1800,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /api/v1/pipeline/rai-analysis/{narrative_id}

Trigger RAI (Responsible AI) analysis for a narrative.

**Rate Limit**: 10/minute  
**Required Role**: analyst

**Response** (201 Created):
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "type": "rai_analysis",
  "status": "pending",
  "progress": 0.0,
  "parameters": {
    "narrative_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "estimated_duration_seconds": 3600,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## WebSocket Endpoints

### WebSocket /api/v1/ws/narratives

Real-time narrative updates and notifications.

**Authentication**: Required (token in query param or header)

**Connection Example**:
```javascript
const ws = new WebSocket('wss://api.strategicnarrative.com/api/v1/ws/narratives?token=your_jwt_token');
```

**Subscribe to Channels**:
```json
{
  "type": "subscribe",
  "channels": ["narrative_updates", "trending_updates"],
  "filters": {
    "topics": ["Technology"],
    "min_impact": 0.7
  }
}
```

**Server Response**:
```json
{
  "type": "subscription_confirmed",
  "channels": ["narrative_updates", "trending_updates"],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Narrative Update Message**:
```json
{
  "type": "narrative_updated",
  "data": {
    "narrative_id": "550e8400-e29b-41d4-a716-446655440000",
    "changes": {
      "confidence_score": 0.92,
      "article_count": 235,
      "trend_momentum": 0.28
    },
    "event": "new_article_added"
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

**Trending Update Message**:
```json
{
  "type": "trending_update",
  "data": {
    "period": "1h",
    "top_narratives": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "AI Revolution in Healthcare",
        "growth_rate": 1.8,
        "momentum": 0.65
      }
    ]
  },
  "timestamp": "2024-01-15T10:35:00Z"
}
```

### WebSocket /api/v1/ws/analytics

Real-time analytics and system metrics.

**Available Channels**:
- `trending_updates`: Trending narrative changes
- `system_metrics`: System performance metrics (admin only)
- `pipeline_updates`: Pipeline task status updates

---

## Admin Endpoints

### GET /api/v1/admin/health

System health check for monitoring.

**Rate Limit**: Unlimited (monitoring)

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 86400,
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "elasticsearch": "healthy",
    "celery": "healthy"
  }
}
```

### GET /api/v1/admin/metrics

Detailed system metrics for monitoring.

**Rate Limit**: 10/minute  
**Required Role**: admin

**Response** (200 OK):
```json
{
  "api": {
    "requests_per_minute": 450,
    "avg_response_time_ms": 125,
    "error_rate": 0.02,
    "active_connections": 1250
  },
  "database": {
    "connection_pool_usage": 0.65,
    "query_avg_time_ms": 45,
    "active_connections": 12,
    "slow_queries": 3
  },
  "pipeline": {
    "pending_tasks": 5,
    "processing_tasks": 2,
    "avg_task_duration_minutes": 8.5,
    "failed_tasks_last_hour": 0
  },
  "cache": {
    "hit_ratio": 0.85,
    "memory_usage_mb": 2048,
    "evictions_per_minute": 12
  }
}
```

---

## OpenAPI Documentation Structure

The API automatically generates comprehensive OpenAPI 3.0 documentation available at:

- **Interactive Documentation**: `/api/v1/docs` (Swagger UI)
- **ReDoc Documentation**: `/api/v1/redoc` (ReDoc interface)
- **OpenAPI Spec**: `/api/v1/openapi.json` (Raw OpenAPI JSON)

### Key Documentation Features

1. **Interactive Testing**: Try endpoints directly from the documentation
2. **Schema Validation**: Request/response schema examples and validation
3. **Authentication Integration**: Test with your actual API tokens
4. **Code Generation**: Generate client SDKs in multiple languages
5. **API Versioning**: Clear version differences and migration guides

### Custom Documentation Tags

All endpoints are organized with descriptive tags:

- `authentication`: User auth and token management
- `narratives`: Core narrative operations
- `articles`: Article management and retrieval
- `clustering`: Narrative clustering and analysis
- `analytics`: Metrics and trending data
- `search`: Search and filtering operations
- `real-time`: WebSocket connections
- `pipeline`: Background processing
- `admin`: Administrative operations

This comprehensive API specification provides everything needed to build sophisticated frontends for the Strategic Narrative Intelligence platform, with proper authentication, rate limiting, caching, error handling, and real-time capabilities.