# Enterprise Project Management Platform (EPMP) - Architecture Documentation

This document describes the software architecture, repository organization, directory layouts, and engineering guidelines for the **Enterprise Project Management Platform (EPMP)**.

---

## 1. Architectural Style & Separation of Concerns

EPMP uses a **Modular Monolith** style for the backend and a **Feature-Driven Architecture** for the frontend. Every component is loosely coupled, enabling scale to thousands of organizations and hundreds of thousands of users.

### The Backend Architectural Layers:
1. **API Router Layer (`app/main.py` & `app/modules/*/router.py`)**:
   Handles incoming HTTP requests, API versioning (version `v1` prefix), paths, and OpenAPI schema documentation. No business logic lives here.
2. **Schemas Layer (`app/modules/*/schemas.py`)**:
   Uses **Pydantic** for input validation, serialization, and defining API payload structures.
3. **Services Layer (`app/modules/*/services.py` & `app/services/`)**:
   Contains all business workflow execution, calculations, side effects (sending emails, purging cache), and transaction control.
4. **Repositories Layer (`app/modules/*/repositories.py` & `app/repositories/`)**:
   Abstracts database queries. All SQLAlchemy queries, filters, joins, and database mutations live here.
5. **Models Layer (`app/modules/*/models.py` & `app/core/database.py`)**:
   Defines the SQLAlchemy declarative database models, field types, constraint conventions, and primary keys.

---

## 2. Directory Layouts

### Backend Structure (`backend/`)

```
backend/
├── alembic.ini                   # Alembic database migrations configuration
├── pyproject.toml                # Poetry configuration, lint/format settings & dependencies
├── Dockerfile                    # Production-ready Multi-stage slim Docker image
├── requirements.txt              # Pinned dependencies for Docker/local development
├── app/
│   ├── main.py                   # FastAPI Application initialization and routing
│   ├── core/
│   │   ├── config.py             # Pydantic Settings management & logging setup
│   │   └── database.py           # Database connection, async engines, sessions & mixins
│   ├── middleware/               # CORS, logging, security, rate limiters
│   ├── repositories/             # Shared database repository classes
│   ├── schemas/                  # Shared data validation schemas
│   ├── utils/                    # Shared utility helper methods
│   ├── services/                 # Shared domain services
│   │   ├── caching/              # Redis caching adapters
│   │   ├── storage/              # S3 attachment upload & storage interface
│   │   └── email/                # MailHog SMTP handlers
│   └── modules/                  # Isolated domain feature modules
│       ├── auth/
│       ├── organizations/
│       ├── teams/
│       ├── projects/
│       ├── tasks/
│       ├── labels/
│       ├── comments/
│       ├── notifications/
│       ├── attachments/
│       ├── dashboards/
│       ├── analytics/
│       ├── administration/
│       ├── search/
│       ├── audit_logs/
│       ├── invitations/
│       └── integrations/
│           ├── __init__.py
│           ├── router.py         # HTTP endpoints for the module
│           ├── models.py         # SQLAlchemy domain database tables
│           ├── schemas.py        # Pydantic request/response payload schemas
│           ├── services.py       # Core business workflows
│           ├── repositories.py   # Database query abstractions
│           ├── validators.py     # Custom business validation checks
│           └── permissions.py    # Custom RBAC/authorization rules
└── tests/                        # Tests (pytest, pytest-asyncio, httpx)
    ├── conftest.py
    └── test_main.py
```

### Frontend Structure (`frontend/`)

We structure our React/Next.js client using a **Feature-First Architecture** inside the Next.js App Router layout:

```
frontend/
├── Dockerfile                    # Next.js Node dev environment
├── tsconfig.json                 # Pinned TypeScript configurations
├── next.config.ts                # Next.js optimization configuration
├── src/
│   ├── app/                      # Next.js App Router pages, routing and layouts
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/               # Global presentation elements
│   │   ├── ui/                   # Reusable base elements (buttons, inputs, alerts)
│   │   ├── layout/               # Header, sidebar, layouts
│   │   ├── forms/                # Generic reusable form inputs
│   │   └── tables/               # Reusable paginated tables
│   ├── features/                 # Domain-specific components, hooks and state
│   │   ├── auth/
│   │   ├── organizations/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   └── tasks/
│   ├── hooks/                    # Reusable custom hooks (e.g. useLocalStorage)
│   ├── services/                 # API Clients and adapters (axios, fetch wrapper)
│   ├── types/                    # Core typescript interface declarations
│   └── utils/                    # Text parsing, date formatting helper utilities
```

---

## 3. Database Conventions & Primary Keys

- **UUID v4 Primary Keys**: All database primary keys are configured as Postgres `UUID` (handled via SQLAlchemy's `UUID(as_uuid=True)`). This prevents ID enumeration attacks and facilitates horizontal scaling.
- **Audit Columns**: Our base model (`EnterpriseBaseModel` in `backend/app/core/database.py`) automatically maps:
  - `id`
  - `created_at` (timezone aware UTC)
  - `updated_at` (updated automatically on update)
  - `is_deleted` (Soft-delete support boolean flag)
  - `deleted_at` (soft-deletion timestamp)
  - `created_by_id` / `updated_by_id` (record creators)
- **Soft Deletes**: Soft deletion strategy is utilized project-wide to ensure data integrity and audit compliance.

---

## 4. Developing a New Feature Module

When developing a new feature (e.g., adding `tasks` features):
1. **Create Models**: Define the SQLAlchemy database entities in `backend/app/modules/tasks/models.py` inheriting from `EnterpriseBaseModel`.
2. **Create Database Migrations**: Run `docker compose exec backend alembic revision --autogenerate -m "create_tasks_table"`.
3. **Implement Repository**: Write the specific queries in `backend/app/modules/tasks/repositories.py`.
4. **Implement Service**: Put business actions in `backend/app/modules/tasks/services.py`.
5. **Define Schemas**: Create request/response shapes in `backend/app/modules/tasks/schemas.py`.
6. **Register Router**: Declare endpoint handlers in `backend/app/modules/tasks/router.py` and register it inside `backend/app/main.py`.
