"""
Deployment and Infrastructure Configuration for Strategic Narrative Intelligence API
Production-ready deployment configurations with Docker, Kubernetes, and cloud services
"""

import os
from typing import Any, Dict, List

# ============================================================================
# DOCKER CONFIGURATION
# ============================================================================

DOCKERFILE_CONTENT = """
# Multi-stage build for Strategic Narrative Intelligence API

# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    libpq-dev \\
    libssl-dev \\
    libffi-dev \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    libpq5 \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY . .

# Set environment variables
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Change ownership to appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/api/v1/admin/health || exit 1

# Start command
CMD ["uvicorn", "strategic_narrative_api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
"""

DOCKER_COMPOSE_CONTENT = """
version: '3.8'

services:
  # Main API service
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/strategic_narratives
      - REDIS_URL=redis://redis:6379/0
      - ELASTICSEARCH_URL=http://elasticsearch:9200
      - CELERY_BROKER_URL=redis://redis:6379/2
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
    depends_on:
      - db
      - redis
      - elasticsearch
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/admin/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Background worker
  worker:
    build: .
    command: celery -A strategic_narrative_api.celery worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/strategic_narratives
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/2
      - SECRET_KEY=${SECRET_KEY:-change-this-in-production}
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  # Task scheduler
  scheduler:
    build: .
    command: celery -A strategic_narrative_api.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/strategic_narratives
      - CELERY_BROKER_URL=redis://redis:6379/2
    depends_on:
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  # PostgreSQL database
  db:
    image: pgvector/pgvector:pg15
    environment:
      - POSTGRES_DB=strategic_narratives
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init_db.sql:/docker-entrypoint-initdb.d/init_db.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis for caching and message broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Elasticsearch for search
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  # Grafana for dashboards
  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  elasticsearch_data:
  prometheus_data:
  grafana_data:
"""

# ============================================================================
# KUBERNETES CONFIGURATION
# ============================================================================

KUBERNETES_NAMESPACE = """
apiVersion: v1
kind: Namespace
metadata:
  name: strategic-narrative
  labels:
    name: strategic-narrative
"""

KUBERNETES_CONFIGMAP = """
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: strategic-narrative
data:
  API_TITLE: "Strategic Narrative Intelligence API"
  API_VERSION: "1.0.0"
  HOST: "0.0.0.0"
  PORT: "8000"
  WORKERS: "4"
  LOG_LEVEL: "INFO"
  DEFAULT_PAGE_SIZE: "20"
  MAX_PAGE_SIZE: "100"
  RATE_LIMIT_DEFAULT: "100/minute"
  CACHE_TTL_SECONDS: "300"
  ELASTICSEARCH_INDEX_PREFIX: "strategic_narratives"
  EMBEDDING_DIMENSION: "384"
  MIN_CLUSTER_SIZE: "5"
"""

KUBERNETES_SECRET = """
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: strategic-narrative
type: Opaque
data:
  # Base64 encoded values
  SECRET_KEY: <base64-encoded-secret-key>
  DATABASE_URL: <base64-encoded-database-url>
  REDIS_URL: <base64-encoded-redis-url>
  ELASTICSEARCH_URL: <base64-encoded-elasticsearch-url>
  NEWS_API_KEY: <base64-encoded-news-api-key>
  TWITTER_API_KEY: <base64-encoded-twitter-api-key>
"""

KUBERNETES_DEPLOYMENT = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: strategic-narrative-api
  namespace: strategic-narrative
  labels:
    app: strategic-narrative-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: strategic-narrative-api
  template:
    metadata:
      labels:
        app: strategic-narrative-api
    spec:
      containers:
      - name: api
        image: strategic-narrative/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: REDIS_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: SECRET_KEY
        envFrom:
        - configMapRef:
            name: api-config
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/admin/health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/admin/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
      imagePullSecrets:
      - name: registry-secret
"""

KUBERNETES_SERVICE = """
apiVersion: v1
kind: Service
metadata:
  name: strategic-narrative-api-service
  namespace: strategic-narrative
spec:
  selector:
    app: strategic-narrative-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP
"""

KUBERNETES_INGRESS = """
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: strategic-narrative-ingress
  namespace: strategic-narrative
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
spec:
  tls:
  - hosts:
    - api.strategicnarrative.com
    secretName: api-tls-secret
  rules:
  - host: api.strategicnarrative.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: strategic-narrative-api-service
            port:
              number: 80
"""

KUBERNETES_HPA = """
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: strategic-narrative-api-hpa
  namespace: strategic-narrative
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: strategic-narrative-api
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
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
"""

# ============================================================================
# TERRAFORM CONFIGURATION (AWS)
# ============================================================================

TERRAFORM_MAIN = """
# Terraform configuration for AWS deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "strategic-narrative-terraform-state"
    key    = "infrastructure/terraform.tfstate"
    region = "us-west-2"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Strategic Narrative Intelligence"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-west-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "domain_name" {
  description = "Domain name for the API"
  type        = string
  default     = "api.strategicnarrative.com"
}

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "strategic-narrative-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "strategic-narrative-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "strategic-narrative-public-${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "strategic-narrative-private-${count.index + 1}"
    Type = "Private"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "strategic-narrative-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "strategic-narrative-alb-sg"
  description = "Security group for Application Load Balancer"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "ecs" {
  name        = "strategic-narrative-ecs-sg"
  description = "Security group for ECS tasks"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "strategic-narrative"
  
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
    weight           = 1
  }
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "strategic-narrative-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id
  
  enable_deletion_protection = false
}

resource "aws_lb_target_group" "api" {
  name        = "strategic-narrative-api-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 10
    interval            = 30
    path                = "/api/v1/admin/health"
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }
}

resource "aws_lb_listener" "api" {
  load_balancer_arn = aws_lb.main.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.main.arn
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}

# RDS Database
resource "aws_db_subnet_group" "main" {
  name       = "strategic-narrative-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "rds" {
  name        = "strategic-narrative-rds-sg"
  description = "Security group for RDS database"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_db_instance" "main" {
  identifier             = "strategic-narrative-db"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.medium"
  allocated_storage      = 100
  max_allocated_storage  = 1000
  storage_type           = "gp3"
  storage_encrypted      = true
  
  db_name  = "strategic_narratives"
  username = "postgres"
  password = random_password.db_password.result
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  
  performance_insights_enabled = true
  monitoring_interval         = 60
  monitoring_role_arn        = aws_iam_role.rds_enhanced_monitoring.arn
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "main" {
  name       = "strategic-narrative-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "redis" {
  name        = "strategic-narrative-redis-sg"
  description = "Security group for Redis cluster"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id         = "strategic-narrative-redis"
  description                  = "Redis cluster for Strategic Narrative API"
  
  node_type                    = "cache.t3.medium"
  port                         = 6379
  parameter_group_name         = "default.redis7"
  
  num_cache_clusters           = 2
  automatic_failover_enabled   = true
  multi_az_enabled            = true
  
  subnet_group_name           = aws_elasticache_subnet_group.main.name
  security_group_ids          = [aws_security_group.redis.id]
  
  at_rest_encryption_enabled  = true
  transit_encryption_enabled  = true
  
  snapshot_retention_limit    = 5
  snapshot_window            = "03:00-05:00"
  maintenance_window         = "sun:05:00-sun:07:00"
}

# Outputs
output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  sensitive   = true
}
"""

# ============================================================================
# MONITORING AND LOGGING CONFIGURATION
# ============================================================================

PROMETHEUS_CONFIG = """
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'strategic-narrative-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgresql'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch-exporter:9114']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
"""

GRAFANA_DASHBOARD_CONFIG = """
{
  "dashboard": {
    "id": null,
    "title": "Strategic Narrative Intelligence API Dashboard",
    "tags": ["strategic-narrative", "api", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{handler}}"
          }
        ],
        "yAxes": [
          {
            "label": "Requests/sec"
          }
        ]
      },
      {
        "id": 2,
        "title": "Response Time",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "singlestat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "id": 4,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active Connections"
          }
        ]
      }
    ],
    "refresh": "5s",
    "schemaVersion": 16,
    "version": 0
  }
}
"""

LOGGING_CONFIG = """
version: 1
disable_existing_loggers: False

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  
  json:
    format: '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: /app/logs/api.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: /app/logs/error.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  strategic_narrative_api:
    level: INFO
    handlers: [console, file]
    propagate: no
  
  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: no
  
  sqlalchemy.engine:
    level: WARNING
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console, file, error_file]
"""

# ============================================================================
# DEPLOYMENT HELPER FUNCTIONS
# ============================================================================


def generate_deployment_files(output_dir: str = "./deployment"):
    """Generate all deployment configuration files."""
    import os

    os.makedirs(output_dir, exist_ok=True)

    files = {
        "Dockerfile": DOCKERFILE_CONTENT,
        "docker-compose.yml": DOCKER_COMPOSE_CONTENT,
        "kubernetes/namespace.yaml": KUBERNETES_NAMESPACE,
        "kubernetes/configmap.yaml": KUBERNETES_CONFIGMAP,
        "kubernetes/secret.yaml": KUBERNETES_SECRET,
        "kubernetes/deployment.yaml": KUBERNETES_DEPLOYMENT,
        "kubernetes/service.yaml": KUBERNETES_SERVICE,
        "kubernetes/ingress.yaml": KUBERNETES_INGRESS,
        "kubernetes/hpa.yaml": KUBERNETES_HPA,
        "terraform/main.tf": TERRAFORM_MAIN,
        "monitoring/prometheus.yml": PROMETHEUS_CONFIG,
        "monitoring/grafana-dashboard.json": GRAFANA_DASHBOARD_CONFIG,
        "config/logging.yaml": LOGGING_CONFIG,
    }

    for file_path, content in files.items():
        full_path = os.path.join(output_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, "w") as f:
            f.write(content.strip())

    print(f"Deployment files generated in {output_dir}")


def get_environment_config(environment: str) -> Dict[str, Any]:
    """Get environment-specific configuration."""

    configs = {
        "development": {
            "replicas": 1,
            "cpu_limit": "500m",
            "memory_limit": "1Gi",
            "cpu_request": "250m",
            "memory_request": "512Mi",
            "db_instance_class": "db.t3.micro",
            "redis_node_type": "cache.t3.micro",
            "enable_debug": True,
            "log_level": "DEBUG",
        },
        "staging": {
            "replicas": 2,
            "cpu_limit": "1000m",
            "memory_limit": "2Gi",
            "cpu_request": "500m",
            "memory_request": "1Gi",
            "db_instance_class": "db.t3.small",
            "redis_node_type": "cache.t3.small",
            "enable_debug": False,
            "log_level": "INFO",
        },
        "production": {
            "replicas": 5,
            "cpu_limit": "2000m",
            "memory_limit": "4Gi",
            "cpu_request": "1000m",
            "memory_request": "2Gi",
            "db_instance_class": "db.r5.large",
            "redis_node_type": "cache.r5.large",
            "enable_debug": False,
            "log_level": "WARNING",
        },
    }

    return configs.get(environment, configs["production"])


def generate_requirements_txt() -> str:
    """Generate requirements.txt for the project."""

    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "pydantic==2.5.0",
        "sqlalchemy==2.0.23",
        "alembic==1.12.1",
        "asyncpg==0.29.0",  # PostgreSQL async driver
        "redis==5.0.1",
        "celery==5.3.4",
        "elasticsearch==8.11.0",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.6",
        "slowapi==0.1.9",  # Rate limiting
        "prometheus-client==0.19.0",  # Metrics
        "structlog==23.2.0",  # Structured logging
        "sentence-transformers==2.2.2",  # ML embeddings
        "scikit-learn==1.3.2",  # Clustering
        "numpy==1.24.4",
        "pandas==2.1.4",
        "psycopg2-binary==2.9.9",  # PostgreSQL driver
        "python-dotenv==1.0.0",  # Environment variables
        "httpx==0.25.2",  # HTTP client
        "websockets==12.0",  # WebSocket support
        "cachetools==5.3.2",  # In-memory caching
        "aioredis==2.0.1",  # Async Redis
        "pytest==7.4.3",  # Testing
        "pytest-asyncio==0.21.1",  # Async testing
        "pytest-cov==4.1.0",  # Coverage
        "black==23.11.0",  # Code formatting
        "isort==5.12.0",  # Import sorting
        "flake8==6.1.0",  # Linting
        "mypy==1.7.1",  # Type checking
    ]

    return "\n".join(requirements)


def get_security_checklist() -> List[str]:
    """Get security checklist for deployment."""

    return [
        "[ ] Change default SECRET_KEY in production",
        "[ ] Use strong, unique passwords for all services",
        "[ ] Enable SSL/TLS certificates",
        "[ ] Configure proper firewall rules",
        "[ ] Enable database encryption at rest",
        "[ ] Use secrets management (AWS Secrets Manager, etc.)",
        "[ ] Configure proper CORS origins",
        "[ ] Enable API rate limiting",
        "[ ] Set up monitoring and alerting",
        "[ ] Configure log aggregation",
        "[ ] Enable container image scanning",
        "[ ] Use least privilege IAM roles",
        "[ ] Enable VPC flow logs",
        "[ ] Configure backup and disaster recovery",
        "[ ] Set up WAF (Web Application Firewall)",
        "[ ] Enable DDoS protection",
        "[ ] Configure input validation and sanitization",
        "[ ] Use parameterized queries for SQL",
        "[ ] Enable security headers (HSTS, CSP, etc.)",
        "[ ] Regular security updates and patches",
    ]


# ============================================================================
# DEPLOYMENT SCRIPTS
# ============================================================================

DEPLOY_SCRIPT = """#!/bin/bash
set -e

# Strategic Narrative Intelligence API Deployment Script

echo "Starting deployment of Strategic Narrative Intelligence API..."

# Configuration
ENVIRONMENT=${1:-production}
AWS_REGION=${2:-us-west-2}
CLUSTER_NAME="strategic-narrative"

echo "Environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"

# Pre-deployment checks
echo "Running pre-deployment checks..."

# Check required tools
command -v docker >/dev/null 2>&1 || { echo "ERROR: Docker is required but not installed."; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl is required but not installed."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "ERROR: AWS CLI is required but not installed."; exit 1; }

# Build and push Docker image
echo "Building Docker image..."
docker build -t strategic-narrative/api:latest .
docker tag strategic-narrative/api:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/strategic-narrative/api:latest

echo "Pushing Docker image to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/strategic-narrative/api:latest

# Deploy to Kubernetes
echo "Deploying to Kubernetes..."
kubectl apply -f kubernetes/namespace.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/secret.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/ingress.yaml
kubectl apply -f kubernetes/hpa.yaml

# Wait for deployment
echo "Waiting for deployment to be ready..."
kubectl rollout status deployment/strategic-narrative-api -n strategic-narrative --timeout=600s

# Run health check
echo "Running health check..."
kubectl get pods -n strategic-narrative
kubectl get services -n strategic-narrative

# Get service URL
SERVICE_URL=$(kubectl get ingress strategic-narrative-ingress -n strategic-narrative -o jsonpath='{.spec.rules[0].host}')
echo "Deployment completed successfully!"
echo "API URL: https://$SERVICE_URL"
echo "Health Check: https://$SERVICE_URL/api/v1/admin/health"
"""

ROLLBACK_SCRIPT = """#!/bin/bash
set -e

# Strategic Narrative Intelligence API Rollback Script

echo "Starting rollback of Strategic Narrative Intelligence API..."

NAMESPACE="strategic-narrative"
DEPLOYMENT="strategic-narrative-api"

# Get current revision
CURRENT_REVISION=$(kubectl rollout history deployment/$DEPLOYMENT -n $NAMESPACE | tail -n 1 | awk '{print $1}')
PREVIOUS_REVISION=$((CURRENT_REVISION - 1))

echo "Current revision: $CURRENT_REVISION"
echo "Rolling back to revision: $PREVIOUS_REVISION"

# Confirm rollback
read -p "Are you sure you want to rollback? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled"
    exit 1
fi

# Perform rollback
echo "Performing rollback..."
kubectl rollout undo deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollback
echo "Waiting for rollback to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

# Verify rollback
echo "Rollback completed successfully!"
kubectl get pods -n $NAMESPACE
"""

if __name__ == "__main__":
    # Generate all deployment files
    generate_deployment_files()
    print("All deployment configuration files generated successfully!")

    # Print security checklist
    print("\nSecurity Checklist:")
    for item in get_security_checklist():
        print(f"  {item}")

    # Print requirements.txt
    print(f"\nRequirements.txt content:\n{generate_requirements_txt()}")
