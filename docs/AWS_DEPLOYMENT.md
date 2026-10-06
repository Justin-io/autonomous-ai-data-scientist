# AWS Production Deployment Guide
## Autonomous AI Data Scientist Platform

### 1. Architectural Topology on AWS

```
                              [Internet / Corporate VPN]
                                         │
                                         ▼
                            [AWS Application Load Balancer]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [Amazon ECS / Fargate Service]                  [Amazon ECS / Fargate Service]
     (FastAPI Backend + React SPA)                   (FastAPI Backend + React SPA)
                 │                                               │
                 ├───────────────────────┬───────────────────────┤
                 ▼                       ▼                       ▼
    [Amazon RDS PostgreSQL 17]     [Amazon S3]          [OpenTelemetry Collector]
    (Read-Only Analytical Replica) (Reports, Parquet,   (Traces & CloudWatch Logs)
                                    Evidence Hashes)             │
                                                                 ▼
                                                        [Amazon Managed Grafana]
```

---

### 2. AWS Components & Best Practices

#### 2.1 Compute: Amazon ECS on AWS Fargate
- **Task Definition**:
  - CPU: 2 vCPU, Memory: 4 GB
  - Container image hosted in Amazon ECR (`<account_id>.dkr.ecr.<region>.amazonaws.com/auto-data-scientist:latest`).
  - Autoscaling: Target Tracking on CPU utilization (65%) and request count per target.
- **Security Group**: Ingress from ALB only on port 8000; egress to RDS port 5432 and S3 via VPC Endpoint.

#### 2.2 Analytical Storage: Amazon RDS for PostgreSQL (Read Replica)
- Dedicated read-only replica user: `analyst_ro`
  ```sql
  CREATE ROLE analyst_ro WITH LOGIN PASSWORD 'strong_random_secret';
  GRANT CONNECT ON DATABASE analytics_warehouse TO analyst_ro;
  GRANT USAGE ON SCHEMA public TO analyst_ro;
  GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst_ro;
  ALTER ROLE analyst_ro SET default_transaction_read_only = on;
  ALTER ROLE analyst_ro SET statement_timeout = '30000';
  ```
- Protects operational transaction processing from heavy analytical scans.

#### 2.3 Artifact & Evidence Storage: Amazon S3
- Bucket: `s3://company-auto-data-scientist-artifacts-prod/`
- Immutable evidence object hashes and final analyst reports persisted with SSE-KMS encryption and versioning.

#### 2.4 Secrets Management: AWS Secrets Manager
- Connection strings, API keys, and database credentials injected as container environment variables at task launch.

#### 2.5 Observability: OpenTelemetry & CloudWatch
- OpenTelemetry collector sidecar exporting traces to AWS X-Ray and CloudWatch Metrics.
- MLflow tracking server backed by S3 and RDS for prompt and model evaluation tracking.

---

### 3. Step-by-Step Deployment Commands

```bash
# 1. Authenticate with Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# 2. Build and Tag Multi-Stage Docker Image
docker build -t auto-data-scientist:latest .
docker tag auto-data-scientist:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/auto-data-scientist:latest

# 3. Push to ECR
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/auto-data-scientist:latest

# 4. Update ECS Service
aws ecs update-service \
  --cluster auto-ds-cluster \
  --service auto-ds-service \
  --force-new-deployment
```
