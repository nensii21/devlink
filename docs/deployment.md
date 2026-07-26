# DevLink Deployment Guide

This guide provides step-by-step instructions for deploying DevLink across local, Dockerized, and production environments, including reverse proxy configuration, environment variable management, and SSL termination.

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Local Setup](#local-setup)
- [Docker Deployment](#docker-deployment)
- [Production Deployment](#production-deployment)
- [Reverse Proxy Configuration (Nginx)](#reverse-proxy-configuration-nginx)
- [SSL & HTTPS Setup (Certbot)](#ssl--https-setup-certbot)

---

## Prerequisites

Before starting, ensure your host environment meets the following minimum requirements:

* **OS**: Linux (Ubuntu 22.04 LTS recommended), macOS, or Windows WSL2
* **Node.js**: v20.x or higher
* **Python**: v3.11 or higher
* **PostgreSQL**: v15 or higher
* **Redis**: v7.0 or higher
* **Docker & Docker Compose**: v24.0+ / v2.20+ (for containerized setup)

---

## Environment Variables

Create `.env` files in both the `backend/` and `frontend/` directories based on the following specifications:

### Backend `.env` (`backend/.env`)

```env
# Application Settings
ENVIRONMENT=production
DEBUG=False
PROJECT_NAME=DevLink

# Security & JWT Auth
SECRET_KEY=your_super_secret_random_key_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database Configuration
DATABASE_URL=postgresql://devlink_user:secure_password@localhost:5432/devlink_db

# Redis & Celery
REDIS_URL=redis://localhost:6379/0

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# AI & OpenAI Service
OPENAI_API_KEY=your_openai_api_key

# CORS Settings
ALLOWED_ORIGINS=https://devlink.example.com,http://localhost:3000
```

### Frontend `.env` (`frontend/.env`)

```env
VITE_API_URL=https://api.devlink.example.com
VITE_WS_URL=wss://api.devlink.example.com/ws
VITE_APP_NAME=DevLink
```

---

## Local Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be accessible at `http://localhost:5173`.

---

## Docker Deployment

DevLink can be containerized and run seamlessly using Docker Compose.

### Docker Compose Configuration (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: devlink_postgres
    environment:
      POSTGRES_USER: devlink_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: devlink_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U devlink_user -d devlink_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: devlink_redis
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: devlink_backend
    environment:
      DATABASE_URL: postgresql://devlink_user:secure_password@postgres:5432/devlink_db
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your_super_secret_random_key_here
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: devlink_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  postgres_data:
```

### Building & Launching

```bash
# Build and run containers in detached mode
docker-compose up -d --build

# View container logs
docker-compose logs -f

# Run database migrations in container
docker-compose exec backend alembic upgrade head
```

---

## Production Deployment

For production deployments (e.g. AWS EC2, DigitalOcean, Hetzner, or Vercel/Render):

1. **Frontend**: Build production assets with `npm run build` and serve via Nginx or host on Vercel/Cloudflare Pages.
2. **Backend**: Run FastAPI with Gunicorn worker management behind systemd or Docker.
3. **Database**: Use managed database instances (AWS RDS / DigitalOcean Managed Databases) for PostgreSQL and Redis.

### Systemd Backend Service (`/etc/systemd/system/devlink-backend.service`)

```ini
[Unit]
Description=DevLink FastAPI Application Service
After=network.target postgresql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/devlink/backend
ExecStart=/var/www/devlink/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable devlink-backend
sudo systemctl start devlink-backend
```

---

## Reverse Proxy Configuration (Nginx)

Nginx routes incoming traffic to the appropriate frontend static files and backend API services, including WebSocket proxying.

Create `/etc/nginx/sites-available/devlink`:

```nginx
server {
    listen 80;
    server_name devlink.example.com api.devlink.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name devlink.example.com;

    ssl_certificate /etc/letsencrypt/live/devlink.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/devlink.example.com/privkey.pem;

    # Frontend static files
    location / {
        root /var/www/devlink/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl http2;
    server_name api.devlink.example.com;

    ssl_certificate /etc/letsencrypt/live/devlink.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/devlink.example.com/privkey.pem;

    # Backend REST API
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSockets Proxy
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
```

Enable site configuration:

```bash
sudo ln -s /etc/nginx/sites-available/devlink /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL & HTTPS Setup (Certbot)

Obtain free SSL certificates via Let's Encrypt and Certbot:

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Obtain SSL Certificate and automatically configure Nginx
sudo certbot --nginx -d devlink.example.com -d api.devlink.example.com

# Test automatic renewal
sudo certbot renew --dry-run
```

---

## Related Documentation

* [Architecture Documentation](architecture.md)
* [Development Guide](development.md)
* [Coding Standards](coding-standards.md)
