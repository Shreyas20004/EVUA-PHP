# evua — Full Project Setup Guide

## Overview
evua is a PHP codebase migration tool with:
- **Engine** (Python) — AST parser + rule engine + Gemini AI processor
- **Backend** (FastAPI) — REST API wrapping the engine
- **Frontend** (React) — UI for uploads, progress, diffs, and reports

---

## Step-by-Step Folder Structure

Run these commands from your project root to create the full structure:

```bash
# 1. Root scaffold
mkdir evua && cd evua

# 2. Engine (already built — copy the engine/ folder here)
# engine/ is provided as the Python migration engine

# 3. Backend (FastAPI)
mkdir -p backend/app/{api/routes,core,schemas,services,workers}
touch backend/app/__init__.py
touch backend/app/main.py                    # FastAPI app entry point
touch backend/app/core/config.py             # env vars / settings
touch backend/app/core/dependencies.py       # DI helpers
touch backend/app/api/__init__.py
touch backend/app/api/routes/__init__.py
touch backend/app/api/routes/migration.py    # POST /migrate, GET /jobs/{id}
touch backend/app/api/routes/files.py        # upload endpoints
touch backend/app/api/routes/health.py       # health check
touch backend/app/schemas/migration.py       # Pydantic request/response models
touch backend/app/services/migration_service.py  # wraps MigrationPipeline
touch backend/app/workers/job_queue.py       # background task management
touch backend/requirements.txt
touch backend/Dockerfile
touch backend/.env.example

# 4. Frontend (React + Vite)
mkdir -p frontend/src/{components,pages,hooks,services,store,styles,utils}
mkdir -p frontend/src/components/{layout,migration,diff,reports,ui}
touch frontend/src/main.jsx
touch frontend/src/App.jsx
touch frontend/src/components/layout/Sidebar.jsx
touch frontend/src/components/layout/Header.jsx
touch frontend/src/components/migration/UploadZone.jsx
touch frontend/src/components/migration/VersionSelector.jsx
touch frontend/src/components/migration/JobProgress.jsx
touch frontend/src/components/diff/DiffViewer.jsx
touch frontend/src/components/diff/IssueList.jsx
touch frontend/src/components/reports/SummaryCard.jsx
touch frontend/src/pages/Dashboard.jsx
touch frontend/src/pages/MigratePage.jsx
touch frontend/src/pages/ResultsPage.jsx
touch frontend/src/services/api.js            # axios client to FastAPI
touch frontend/src/hooks/useMigration.js
touch frontend/src/store/migrationStore.js    # zustand/redux store
touch frontend/package.json
touch frontend/vite.config.js
touch frontend/Dockerfile
touch frontend/.env.example

# 5. Shared config / infra
touch docker-compose.yml
touch .env.example
touch README.md
```

---

## Complete Directory Tree

```
evua/
├── engine/                         ← Python migration engine (built)
│   ├── __init__.py
│   ├── requirements.txt
│   ├── ast_parser/
│   │   ├── __init__.py
│   │   ├── php_parser.py           ← Tokenizer + recursive AST builder
│   │   └── visitor.py              ← Visitor pattern / node finders
│   ├── rule_engine/
│   │   ├── __init__.py
│   │   ├── base_rule.py            ← Rule ABC + RuleRegistry
│   │   └── rules.py                ← All built-in migration rules
│   ├── ai_processor/
│   │   ├── __init__.py
│   │   └── gemini_processor.py     ← Gemini API client + MockAIProcessor
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── migration_pipeline.py   ← Orchestration: scan→parse→rules→AI
│   ├── models/
│   │   ├── __init__.py
│   │   └── migration_models.py     ← Dataclasses: MigrationResult, etc.
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_scanner.py         ← .php file discovery
│   │   ├── diff_generator.py       ← Unified diff output
│   │   └── version_detector.py     ← Heuristic PHP version detection
│   └── tests/
│       ├── __init__.py
│       └── test_engine.py          ← Full test suite (35 tests)
│
├── backend/                        ← FastAPI backend
│   ├── app/
│   │   ├── main.py                 ← FastAPI entry point
│   │   ├── core/
│   │   │   ├── config.py           ← Pydantic Settings (env vars)
│   │   │   └── dependencies.py     ← Injection helpers
│   │   ├── api/routes/
│   │   │   ├── migration.py        ← POST /migrate, GET /jobs/{id}
│   │   │   ├── files.py            ← File upload endpoints
│   │   │   └── health.py           ← GET /health
│   │   ├── schemas/
│   │   │   └── migration.py        ← Request/response Pydantic models
│   │   ├── services/
│   │   │   └── migration_service.py ← Wraps MigrationPipeline
│   │   └── workers/
│   │       └── job_queue.py        ← Background tasks / job tracking
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/                       ← React + Vite frontend
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── layout/             ← Sidebar, Header
│   │   │   ├── migration/          ← UploadZone, VersionSelector, JobProgress
│   │   │   ├── diff/               ← DiffViewer, IssueList
│   │   │   └── reports/            ← SummaryCard, SeverityChart
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── MigratePage.jsx
│   │   │   └── ResultsPage.jsx
│   │   ├── services/
│   │   │   └── api.js              ← axios client → FastAPI
│   │   ├── hooks/
│   │   │   └── useMigration.js
│   │   └── store/
│   │       └── migrationStore.js
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml              ← Runs backend + frontend together
└── .env.example                    ← GEMINI_API_KEY, etc.
```

---

## Key Configuration Files to Create

### `backend/.env.example`
```env
GEMINI_API_KEY=your-gemini-api-key-here
MAX_UPLOAD_SIZE_MB=50
MAX_CONCURRENCY=5
CORS_ORIGINS=http://localhost:5173
```

### `frontend/.env.example`
```env
VITE_API_BASE_URL=http://localhost:8000
```

### `docker-compose.yml`
```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./engine:/app/engine

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_BASE_URL=http://localhost:8000
```

---

## Engine Usage (Python API)

```python
from engine.pipeline import MigrationPipeline
from engine.models.migration_models import PHPVersion

pipeline = MigrationPipeline(
    source_version=PHPVersion.PHP_5_6,
    target_version=PHPVersion.PHP_8_0,
    gemini_api_key="your-key",
)

# Single file
result = pipeline.run_file("path/to/file.php")
print(result.migrated_code)
print(result.stats)

# Entire directory
summary = pipeline.run_directory("path/to/project/", output_dir="path/to/output/")
print(summary.summary)
```

---

## Running Tests

```bash
cd evua
pip install pytest pytest-asyncio httpx
pytest engine/tests/ -v
```

---

## How the Hybrid Pipeline Works

```
PHP File
   │
   ▼
[AST Parser]          ← Tokenizes PHP + builds lightweight AST
   │
   ▼
[Rule Engine]         ← Applies 15+ rules (regex + AST-aware)
   │                    Auto-fixes: ereg→preg, split→preg_split,
   │                    magic_quotes→false, etc.
   │
   ├─ auto_fixable → applied immediately, source updated in-place
   │
   └─ requires_ai  → collected into issue list
          │
          ▼
    [Gemini API]      ← Receives: partially-migrated code + issue list
                        Returns: fully-migrated code + change log
                        Handles: mysql→PDO/mysqli rewrites,
                                 create_function→closures,
                                 dynamic property declarations, etc.
```
