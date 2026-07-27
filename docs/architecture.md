# DevLink System Architecture & Mermaid Diagrams

This document provides comprehensive architectural specifications and visual Mermaid diagrams for DevLink, including authentication flows, request lifecycle pipelines, component architecture, database entity relationships (ERD), and containerized deployment topology.

---

## 📑 Table of Contents

1. [Authentication Architecture](#1-authentication-architecture)
2. [Request Lifecycle Pipeline](#2-request-lifecycle-pipeline)
3. [Component Architecture](#3-component-architecture)
4. [Database Entity Relationship Diagram (ERD)](#4-database-entity-relationship-diagram-erd)
5. [Deployment Architecture Topology](#5-deployment-architecture-topology)

---

## 1. Authentication Architecture

DevLink supports dual authentication pathways: standard **JWT Credentials** (email/password with bcrypt hashing) and **GitHub OAuth 2.0**.

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / User
    participant Web as Frontend (React 19)
    participant Auth as FastAPI Auth Router
    participant GH as GitHub OAuth Provider
    participant DB as PostgreSQL DB
    participant Redis as Redis Session Cache

    alt 1. JWT Email/Password Login
        User->>Web: Submit Email & Password
        Web->>Auth: POST /api/auth/login
        Auth->>DB: Query user by email
        DB-->>Auth: User Record & Password Hash
        Auth->>Auth: Verify Bcrypt Password Hash
        Auth->>Auth: Generate JWT Access & Refresh Tokens
        Auth-->>Web: Return { access_token, refresh_token }
        Web->>Web: Save JWT in Secure Local Storage / HttpOnly Cookie
    else 2. GitHub OAuth 2.0 Authorization
        User->>Web: Click "Login with GitHub"
        Web->>Auth: GET /api/auth/github
        Auth-->>Web: Return GitHub Authorize URL
        Web->>GH: Redirect User to GitHub Consent Screen
        User->>GH: Grant Application Scope Permissions
        GH-->>Web: Redirect back to /auth/callback?code=AUTH_CODE
        Web->>Auth: GET /api/auth/github/callback?code=AUTH_CODE
        Auth->>GH: POST /login/oauth/access_token { code, client_secret }
        GH-->>Auth: Return GitHub access_token
        Auth->>GH: GET /user (Fetch Profile & Primary Email)
        GH-->>Auth: Return GitHub User Profile JSON
        Auth->>DB: Find existing or register new User record
        DB-->>Auth: Saved User Record
        Auth->>Auth: Generate DevLink JWT Tokens
        Auth-->>Web: Return JWT Tokens & User Session
    end
    Web->>Redis: Cache Active Session Metadata
```

---

## 2. Request Lifecycle Pipeline

Every incoming HTTP request traverses a series of security, rate limiting, and validation middleware layers before reaching business services and returning a response.

```mermaid
graph TD
    Client[Client Browser / Application] -->|HTTP POST/GET Request| Ingress[Nginx Ingress / Reverse Proxy]
    
    subgraph Middleware Pipeline
        Ingress --> Middleware1[RequestID Middleware: Tag X-Request-ID]
        Middleware1 --> Middleware2[Security Headers Middleware: CSP, HSTS, X-Frame]
        Middleware2 --> Middleware3[Activity Tracking Middleware: Log Client IP & Path]
        Middleware3 --> Middleware4[SlowAPI Rate Limiter: Check Rate Limits]
        Middleware4 --> Middleware5[CORS Middleware: Validate Origin & Headers]
    end

    subgraph API Execution & Serialization
        Middleware5 -->|Valid Request| Router[FastAPI APIRouter Route Handler]
        Router --> Pydantic[Pydantic Schema Validation]
        Pydantic -->|Validation Error 422| ErrResponse[Return 422 Unprocessable Entity]
        Pydantic -->|Valid Payload| Service[Business Logic Service Layer]
        
        Service -->|Query Cache| Redis[(Redis Cache)]
        Redis -->|Cache Hit| Service
        
        Service -->|DB Query| ORM[SQLAlchemy Async Engine]
        ORM --> DB[(PostgreSQL Database)]
        DB --> ORM
        ORM --> Service

        Service --> TaskQueue[Async Event Bus / Celery Worker]
    end

    Service -->|Success JSON| HTTP200[HTTP 200/201 JSON Response]
    HTTP200 --> Client
```

---

## 3. Component Architecture

DevLink is structured into decoupled frontend presentation modules and modular backend domain routers/services.

```mermaid
graph TB
    subgraph Frontend Application Layer React 19 / TypeScript
        UI[Pages & Layout Components]
        Routes[TanStack Router / App Routes]
        Contexts[Sidebar, Auth & Theme Contexts]
        
        subgraph Feature Components
            ProfileComp[Profile & Teammate Cards]
            ProjectComp[Project Marketplace & Filters]
            ChatComp[WebSocket Direct Messenger]
            SearchComp[Global Search & Suggestions]
        end

        Query[TanStack React Query Cache]
        APIClient[Axios / Fetch API Client Layer]
        
        UI --> Routes
        Routes --> Feature Components
        Feature Components --> Contexts
        Feature Components --> Query
        Query --> APIClient
    end

    subgraph Backend Application Layer FastAPI / Python
        APIClient -->|REST & WebSockets| APIGateway[FastAPI Application Gateway]

        subgraph Router Modules
            AuthRouter[app/routers/auth.py]
            UserRouter[app/routers/users.py]
            ProjRouter[app/routers/projects.py]
            MsgRouter[app/routers/messages.py]
            RecRouter[app/routers/recommendations.py]
            WSRouter[app/routers/websockets.py]
        end

        subgraph Core Business Services
            AuthService[Authentication & Password Hash Service]
            MatchService[Teammate Matching Engine]
            WSService[WebSocket Connection Manager]
            QualityService[Repo Quality Scoring Service]
        end

        APIGateway --> Router Modules
        AuthRouter --> AuthService
        UserRouter --> QualityService
        ProjRouter --> MatchService
        RecRouter --> MatchService
        WSRouter --> WSService
        MsgRouter --> WSService
    end

    subgraph Infrastructure Layer
        AuthService --> DB[(PostgreSQL)]
        MatchService --> Redis[(Redis)]
        WSService --> Redis
    end
```

---

## 4. Database Entity Relationship Diagram (ERD)

The PostgreSQL relational schema models users, projects, applications, direct messages, bookmarks, and activity feeds.

```mermaid
erDiagram
    USERS {
        uuid id PK
        string email UK
        string username UK
        string password_hash
        string full_name
        string headline
        text bio
        string avatar_url
        string github_username
        jsonb skills
        jsonb social_links
        timestamp created_at
    }

    PROJECTS {
        uuid id PK
        uuid owner_id FK
        string title
        string tagline
        text description
        string category
        jsonb tech_stack
        jsonb open_roles
        string repository_url
        int stars_count
        timestamp created_at
    }

    APPLICATIONS {
        uuid id PK
        uuid project_id FK
        uuid applicant_id FK
        string role_applied
        text cover_note
        string status
        timestamp created_at
    }

    MESSAGES {
        uuid id PK
        uuid conversation_id FK
        uuid sender_id FK
        text content
        boolean read_status
        timestamp created_at
    }

    CONVERSATIONS {
        uuid id PK
        uuid participant_a FK
        uuid participant_b FK
        timestamp updated_at
    }

    BOOKMARKS {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        timestamp created_at
    }

    BUILDER_FLARES {
        uuid id PK
        uuid user_id FK
        string title
        text content
        jsonb tags
        timestamp created_at
    }

    FOLLOWERS {
        uuid id PK
        uuid follower_id FK
        uuid following_id FK
        timestamp created_at
    }

    USERS ||--o{ PROJECTS : "creates and owns"
    USERS ||--o{ APPLICATIONS : "submits"
    PROJECTS ||--o{ APPLICATIONS : "receives"
    USERS ||--o{ BOOKMARKS : "saves"
    PROJECTS ||--o{ BOOKMARKS : "bookmarked by"
    USERS ||--o{ MESSAGES : "sends"
    CONVERSATIONS ||--o{ MESSAGES : "contains"
    USERS ||--o{ CONVERSATIONS : "participates in"
    USERS ||--o{ BUILDER_FLARES : "posts"
    USERS ||--o{ FOLLOWERS : "follows / followed by"
```

---

## 5. Deployment Architecture Topology

Production deployment topology using containerized microservices behind a high-availability reverse proxy and managed cloud infrastructure.

```mermaid
graph TB
    subgraph Internet & Edge Security
        User[End Users / Developers]
        Cloudflare[Cloudflare CDN & DDoS Protection]
    end

    subgraph Cloud Infrastructure VPC
        subgraph Public Subnet
            Ingress[Nginx Ingress Controller SSL/TLS Termination]
        end

        subgraph Container Orchestration Cluster Docker / K8s
            FrontendPod[Frontend Container React 19 / Vite Node Server]
            BackendPod1[FastAPI Backend Container Replica 1]
            BackendPod2[FastAPI Backend Container Replica 2]
            WorkerPod[Celery Background Task Worker]
        end

        subgraph Private Database Subnet
            PostgresMaster[(Managed PostgreSQL Primary)]
            PostgresReplica[(Managed PostgreSQL Read Replica)]
            RedisCluster[(Redis Sentinel Cluster Cache & Broker)]
        end

        subgraph Cloud Storage
            S3[Cloud Object Storage Avatars & Assets]
        end
    end

    User --> Cloudflare
    Cloudflare --> Ingress
    Ingress -->|Static / SSR| FrontendPod
    Ingress -->|API & WebSocket| BackendPod1
    Ingress -->|API & WebSocket| BackendPod2

    BackendPod1 --> PostgresMaster
    BackendPod2 --> PostgresMaster
    BackendPod1 --> RedisCluster
    BackendPod2 --> RedisCluster
    
    BackendPod1 --> WorkerPod
    WorkerPod --> PostgresMaster
    WorkerPod --> RedisCluster
    WorkerPod --> S3
    BackendPod1 --> S3
    PostgresMaster -.->|Replication| PostgresReplica
```

---

## 🔗 Related Documentation

* [API Reference](api.md)
* [Development Setup](development.md)
* [Deployment Guide](deployment.md)
* [Coding Standards](coding-standards.md)
