# GitHub Actions & Docker Guide
<!-- Domain Zero Protocol v8.11.0 - Offline Reference -->

**Agent**: Panda (Build & Integration Specialist)
**Last Updated**: 2025-12-26
**Sources**: [GitHub Actions](https://docs.github.com/en/actions), [Docker](https://docs.docker.com/)

---

## Table of Contents

1. [GitHub Actions Overview](#github-actions-overview)
2. [Workflow Syntax](#workflow-syntax)
3. [Common Workflows](#common-workflows)
4. [Docker Fundamentals](#docker-fundamentals)
5. [Dockerfile Best Practices](#dockerfile-best-practices)
6. [Docker Compose](#docker-compose)
7. [CI/CD Integration](#cicd-integration)
8. [Security Best Practices](#security-best-practices)

---

## GitHub Actions Overview

GitHub Actions automates software workflows directly in your GitHub repository.

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Workflow** | Automated process defined in YAML |
| **Event** | Trigger that starts a workflow |
| **Job** | Set of steps that execute on same runner |
| **Step** | Individual task within a job |
| **Action** | Reusable unit of code |
| **Runner** | Server that runs workflows |

### Workflow File Location

```
.github/
  workflows/
    ci.yml
    deploy.yml
    release.yml
```

---

## Workflow Syntax

### Basic Structure

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build
```

### Events (Triggers)

```yaml
on:
  # Push events
  push:
    branches: [main, 'releases/**']
    tags: ['v*']
    paths:
      - 'src/**'
      - '!src/**/*.md'

  # Pull request events
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

  # Schedule (cron)
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC

  # Manual trigger
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

  # Repository dispatch (external trigger)
  repository_dispatch:
    types: [deploy]
```

### Job Configuration

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    # Run on multiple configurations
    strategy:
      matrix:
        node-version: [18, 20, 22]
        os: [ubuntu-latest, windows-latest]
      fail-fast: false

    # Job dependencies
    needs: [lint]

    # Conditional execution
    if: github.event_name == 'push'

    # Environment variables
    env:
      CI: true

    # Timeout
    timeout-minutes: 30

    # Concurrency control
    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: true

    steps:
      - uses: actions/checkout@v4
```

### Steps

```yaml
steps:
  # Using an action
  - name: Checkout
    uses: actions/checkout@v4
    with:
      fetch-depth: 0

  # Running a command
  - name: Install dependencies
    run: npm ci

  # Multi-line command
  - name: Build and test
    run: |
      npm run build
      npm test

  # Conditional step
  - name: Deploy
    if: github.ref == 'refs/heads/main'
    run: npm run deploy

  # Continue on error
  - name: Optional step
    continue-on-error: true
    run: npm run optional-task

  # Using secrets
  - name: Deploy
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: ./deploy.sh
```

### Outputs and Artifacts

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.value }}

    steps:
      - name: Get version
        id: version
        run: echo "value=$(cat package.json | jq -r .version)" >> $GITHUB_OUTPUT

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/
          retention-days: 5

  deploy:
    needs: build
    runs-on: ubuntu-latest

    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/

      - name: Use output from build
        run: echo "Deploying version ${{ needs.build.outputs.version }}"
```

---

## Common Workflows

### Node.js CI

```yaml
name: Node.js CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run type-check

      - name: Test
        run: npm test -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### Python CI

```yaml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with ruff
        run: ruff check .

      - name: Type check with mypy
        run: mypy src/

      - name: Test with pytest
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

### Docker Build and Push

```yaml
name: Docker Build

on:
  push:
    branches: [main]
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKER_USERNAME }}
          password: ${{ secrets.DOCKER_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: myorg/myapp
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Reusable Workflow

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      deploy_key:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}

    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          DEPLOY_KEY: ${{ secrets.deploy_key }}
        run: ./deploy.sh ${{ inputs.environment }}

# Usage in another workflow
jobs:
  call-deploy:
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
    secrets:
      deploy_key: ${{ secrets.DEPLOY_KEY }}
```

---

## Docker Fundamentals

### Basic Commands

```bash
# Build image
docker build -t myapp:latest .

# Run container
docker run -d -p 8080:80 --name myapp myapp:latest

# List containers
docker ps -a

# View logs
docker logs -f myapp

# Execute command in container
docker exec -it myapp /bin/sh

# Stop and remove
docker stop myapp
docker rm myapp

# Remove image
docker rmi myapp:latest

# Clean up
docker system prune -a
```

### Basic Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

---

## Dockerfile Best Practices

### Multi-Stage Builds

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production

WORKDIR /app

# Copy only production dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Run as non-root user
USER node

EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Layer Optimization

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (changes rarely)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (changes sometimes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (changes frequently)
COPY . .

CMD ["python", "app.py"]
```

### Security Hardening

```dockerfile
FROM node:20-alpine

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Change ownership
COPY --chown=nodejs:nodejs . .

# Install dependencies
RUN npm ci --only=production

# Switch to non-root user
USER nodejs

# Don't run as PID 1
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

### Python Production Dockerfile

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home appuser
WORKDIR /home/appuser/app
USER appuser

# Copy application
COPY --chown=appuser:appuser . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

---

## Docker Compose

### Basic Compose File

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://user:pass@db:5432/myapp
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=myapp
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Development Override

```yaml
# docker-compose.override.yml (auto-loaded)
version: '3.8'

services:
  web:
    build:
      context: .
      target: development
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: npm run dev

  db:
    ports:
      - "5432:5432"
```

### Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f web

# Execute command
docker-compose exec web npm run migrate

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

---

## CI/CD Integration

### Complete CI/CD Pipeline

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/test

  build:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push'

    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Deploy to staging
        run: echo "Deploying to staging"

  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to production
        run: echo "Deploying to production"
```

---

## Security Best Practices

### Secrets Management

```yaml
# Use GitHub secrets
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: ./deploy.sh

# Use environment secrets
jobs:
  deploy:
    environment: production
    steps:
      - name: Deploy
        env:
          API_KEY: ${{ secrets.PRODUCTION_API_KEY }}
        run: ./deploy.sh
```

### OIDC Authentication

```yaml
# No long-lived credentials needed
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read

    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-actions
          aws-region: us-east-1
```

### Container Security

```yaml
# Scan for vulnerabilities
- name: Run Trivy vulnerability scanner
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    format: 'table'
    exit-code: '1'
    severity: 'CRITICAL,HIGH'

# Sign images
- name: Sign image
  uses: sigstore/cosign-installer@v3
- run: cosign sign ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
```

### Dependency Security

```yaml
# Enable Dependabot
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    groups:
      production-dependencies:
        patterns:
          - "*"
        exclude-patterns:
          - "@types/*"
          - "*eslint*"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Quick Reference

### GitHub Actions Contexts

```yaml
${{ github.sha }}           # Commit SHA
${{ github.ref }}           # Branch/tag ref
${{ github.ref_name }}      # Branch/tag name
${{ github.actor }}         # User who triggered
${{ github.event_name }}    # Event type
${{ github.workspace }}     # Workspace path
${{ runner.os }}            # Runner OS
${{ secrets.SECRET_NAME }}  # Secret value
${{ env.VAR_NAME }}         # Environment variable
```

### Docker Commands

```bash
# Build
docker build -t image:tag .
docker build -f Dockerfile.prod -t image:tag .

# Run
docker run -d -p 8080:80 --name container image:tag
docker run -it --rm image:tag /bin/sh

# Manage
docker ps -a
docker logs -f container
docker exec -it container /bin/sh
docker stop container
docker rm container

# Images
docker images
docker rmi image:tag
docker tag image:tag newimage:tag

# Clean up
docker system prune -a
docker volume prune
```

---

**Online References**:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
