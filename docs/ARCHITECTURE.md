# EVUA Architecture Documentation

Complete architectural overview of the PHP migration tool.

## 📐 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐       │
│  │   Upload     │  │   Monitor    │  │  Results Page   │       │
│  │   Page       │  │   Progress   │  │  (Monaco Editor)│       │
│  └──────────────┘  └──────────────┘  └─────────────────┘       │
│         │                 │                     │                │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐       │
│  │   Version    │  │     Risk     │  │   AI Review     │       │
│  │   Control    │  │  Dashboard   │  │   Interface     │       │
│  │   UI         │  │              │  │                 │       │
│  └──────────────┘  └──────────────┘  └─────────────────┘       │
│         │                 │                     │                │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            Zustand State Management                   │       │
│  │  (migrationStore.js - stores job/version/risk/ai)   │       │
│  └──────────────────────────────────────────────────────┘       │
│                           │                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │            API Clients (axios)                       │       │
│  │  - api.js (migration)       - versionApi.js         │       │
│  │  - riskApi.js               - aiVerifyApi.js        │       │
│  └──────────────────────────────────────────────────────┘       │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │ HTTP REST
                            │ (http://localhost:8000)
┌───────────────────────────────────────────────────────────────────┐
│                  BACKEND (FastAPI - uvicorn)                       │
├───────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────┐      │
│  │              API Routes Layer                           │      │
│  ├────────────────────────────────────────────────────────┤      │
│  │  migration.py    │  versions.py    │  risk.py          │      │
│  │  (POST /migrate  │  (version       │  (risk assess-    │      │
│  │   GET /jobs)     │   management)   │   ment)           │      │
│  │                  │                  │                   │      │
│  │  files.py        │  ai_verify.py                       │      │
│  │  (upload)        │  (AI verification)                 │      │
│  └────────────────────────────────────────────────────────┘      │
│                            │                                      │
│  ┌────────────────────────────────────────────────────────┐      │
│  │             Services Layer                             │      │
│  ├────────────────────────────────────────────────────────┤      │
│  │                                                         │      │
│  │  ┌─────────────────────────┐                          │      │
│  │  │ Migration Service       │                          │      │
│  │  │ - Wraps engine pipeline │                          │      │
│  │  │ - Handles job queue     │                          │      │
│  │  │ - Builds responses      │                          │      │
│  │  └─────────────────────────┘                          │      │
│  │           │                                            │      │
│  │           ▼                                            │      │
│  │  ┌──────────────────────────────────────────┐         │      │
│  │  │       Migration Engine (Python)          │         │      │
│  │  │  ┌─────────┐  ┌──────────┐  ┌────────┐ │         │      │
│  │  │  │AST      │▶ │Rule      │▶ │AI      │ │         │      │
│  │  │  │Parser   │  │Engine    │  │Proc    │ │         │      │
│  │  │  └─────────┘  └──────────┘  └────────┘ │         │      │
│  │  └──────────────────────────────────────────┘         │      │
│  │                                                         │      │
│  │  ┌─────────────────────────┐                          │      │
│  │  │ Version Control Service │                          │      │
│  │  │ - Git wrapper           │                          │      │
│  │  │ - Commit management     │                          │      │
│  │  │ - Diff generation       │                          │      │
│  │  └─────────────────────────┘                          │      │
│  │                                                         │      │
│  │  ┌─────────────────────────┐                          │      │
│  │  │ Risk Assessment Service │                          │      │
│  │  │ - Metrics calculation   │                          │      │
│  │  │ - Risk scoring          │                          │      │
│  │  │ - Recommendations       │                          │      │
│  │  └─────────────────────────┘                          │      │
│  │                                                         │      │
│  │  ┌─────────────────────────┐                          │      │
│  │  │ AI Verification Service │                          │      │
│  │  │ - Gemini API integration│                          │      │
│  │  │ - Async processing      │                          │      │
│  │  │ - Suggestion tracking   │                          │      │
│  │  └─────────────────────────┘                          │      │
│  │                                                         │      │
│  └────────────────────────────────────────────────────────┘      │
│                            │                                      │
│  ┌────────────────────────────────────────────────────────┐      │
│  │          Database Layer (SQLAlchemy ORM)              │      │
│  ├────────────────────────────────────────────────────────┤      │
│  │                                                         │      │
│  │  Models:                                               │      │
│  │  • MigrationJobModel                                  │      │
│  │  • VersionSnapshotModel                               │      │
│  │  • RiskAssessmentModel                                │      │
│  │  • AIVerificationModel                                │      │
│  │  • ChangeHistoryModel                                 │      │
│  │                                                         │      │
│  └────────────────────────────────────────────────────────┘      │
│                            │                                      │
└───────────┬────────────────┼────────────────────────┬──────────────┘
            │                │                        │
            ▼                ▼                        ▼
    ┌──────────────┐  ┌──────────────┐   ┌─────────────────────┐
    │   SQLite     │  │  Git Repos   │   │  External Services  │
    │   Database   │  │  (per job)   │   │  • Gemini API       │
    │              │  │              │   │  • File Storage     │
    │ evua.db      │  │ versions/    │   └─────────────────────┘
    │              │  │ {job_id}/    │
    └──────────────┘  └──────────────┘
```

## 🔄 Data Flow

### Migration Workflow

```
1. USER UPLOADS FILES
   └─> POST /api/files/upload
       └─> Files stored in /backend/storage/uploads/

2. USER INITIATES MIGRATION
   └─> POST /api/migrate
       ├─> Job created in migration_jobs table
       ├─> Version control initialized
       │   └─> Git repo created at /versions/{job_id}/
       └─> AsyncJob submitted to queue

3. ENGINE PROCESSES FILES (Async)
   └─> MigrationPipeline.run_file()
       ├─> AST Parser
       ├─> Rule Engine (auto-fixes applied)
       ├─> Collects AI-required issues
       └─> Returns MigrationResult

4. INITIAL VERSION COMMITTED
   └─> Commit 1: Initial migration
       └─> Stored in git repo + tracked in version_snapshots

5. RISK ASSESSMENT TRIGGERED
   └─> RiskAssessmentService.assess_file()
       ├─> Calculates 6 risk factors
       ├─> Generates overall score
       ├─> Categorizes as LOW/MEDIUM/HIGH/CRITICAL
       └─> Stores in risk_assessments table

6. AI VERIFICATION (Auto for HIGH/CRITICAL)
   └─> AIVerificationService.verify_file() [ASYNC]
       ├─> Identifies high-risk sections
       ├─> Sends to Gemini API
       ├─> Parses response
       ├─> Stores suggestions in ai_verifications
       └─> Awaits user approval

7. USER REVIEWS via FRONTEND
   └─> Sees: Original code | Migrated code (Monaco Editor)
       ├─> Risk metrics displayed
       ├─> AI suggestions shown
       └─> Can approve/reject/apply

8. USER APPLIES FIXES
   └─> POST /api/ai/verify/{section_id}/apply
       ├─> Fix applied to code
       ├─> Version Control: Commit 2: AI fixes applied
       └─> Database: fix_applied flag set

9. READY FOR DEPLOYMENT
   └─> User can:
       ├─> Download migrated code
       ├─> Revert to any previous version
       ├─> Review full audit trail
       └─> Deploy with confidence
```

## 📦 Database Schema

```
migration_jobs (1:N)
├─ job_id (PK)
├─ status (pending → running → completed/failed)
├─ source_version, target_version
├─ file counts (total, completed, failed, skipped)
├─ git_repo_path
└─ summary (JSON)

    ├─> version_snapshots (N)
    │   ├─ id (PK)
    │   ├─ commit_hash (Git SHA)
    │   ├─ created_at (timestamp)
    │   ├─ files_changed, insertions, deletions
    │   ├─ migration_stage
    │   └─ metadata (JSON)
    │
    ├─> risk_assessments (N)
    │   ├─ id (PK)
    │   ├─ file_path
    │   ├─ overall_score (0-1)
    │   ├─ risk_category (LOW/MEDIUM/HIGH/CRITICAL)
    │   ├─ detailed factors (6 components)
    │   ├─ metrics (LOC, nesting, functions)
    │   └─ recommendations (JSON array)
    │
    ├─> ai_verifications (N)
    │   ├─ id (PK)
    │   ├─ section_id (unique code section)
    │   ├─ original_code, migrated_code (TEXT)
    │   ├─ review_status (pending/reviewed/accepted/rejected)
    │   ├─ ai_feedback (full response)
    │   ├─ suggested_fix (corrected code)
    │   ├─ confidence_score (0-1)
    │   ├─ issues_found (JSON array)
    │   ├─ approved_by_user (boolean)
    │   ├─ fix_applied (boolean)
    │   └─ reviewed_at (timestamp)
    │
    └─> change_history (N)
        ├─ id (PK)
        ├─ timestamp
        ├─ action (migrated/risk_assessed/ai_verified/reverted)
        ├─ description
        └─ metadata (JSON)
```

## 🔌 API Endpoints Overview

### Migration API
```
POST   /api/migrate                    Create migration job
GET    /api/jobs/{job_id}              Poll job status
GET    /api/jobs                       List all jobs
```

### Version Control API
```
POST   /api/versions/{job_id}/init                  Initialize version control
GET    /api/versions/{job_id}/history              Get version history
POST   /api/versions/{job_id}/create                Create new version
GET    /api/versions/{job_id}/diff                 Get diff between versions
GET    /api/versions/{job_id}/file-diff            Get file-specific diff
GET    /api/versions/{job_id}/revert-preview       Preview revert changes
POST   /api/versions/{job_id}/revert               Apply revert
GET    /api/versions/{job_id}/file                 Get file at version
```

### Risk Assessment API
```
POST   /api/risk/assess                   Assess single file risk
POST   /api/risk/assess-job/{job_id}      Assess all files
GET    /api/risk/{job_id}/summary         Get risk summary
GET    /api/risk/{job_id}/critical        Get critical files
```

### AI Verification API
```
POST   /api/ai/verify/{job_id}            Verify single file
POST   /api/ai/verify-batch/{job_id}      Batch verify files
GET    /api/ai/verify/{job_id}/results    Get verifications
POST   /api/ai/verify/{section_id}/approve Approve suggestion
POST   /api/ai/verify/{section_id}/reject  Reject suggestion
POST   /api/ai/verify/{section_id}/apply   Apply fix
```

## 🗂️ File Organization

```
backend/app/
├── api/routes/                    # HTTP endpoints
│   ├── migration.py              # Migration endpoints
│   ├── versions.py               # Version control endpoints
│   ├── risk.py                   # Risk assessment endpoints
│   ├── ai_verify.py              # AI verification endpoints
│   ├── files.py                  # File upload endpoints
│   └── health.py                 # Health check
│
├── services/                      # Business logic
│   ├── migration_service.py       # Orchestrates engine
│   ├── version_control_service.py # Git operations
│   ├── risk_assessment_service.py # Risk scoring
│   └── ai_verification_service.py # AI processing
│
├── db/                           # Database layer
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # ORM models
│   └── __init__.py
│
├── schemas/                      # Request/response models
│   ├── migration.py
│   ├── version.py
│   ├── risk.py
│   └── ai_verify.py
│
├── utils/                        # Utilities
│   └── risk_metrics.py          # Risk calculation algorithms
│
├── core/
│   ├── config.py                # Settings/environment
│   └── dependencies.py          # DI helpers
│
└── main.py                       # FastAPI app factory
```

## 🔐 Security Considerations

### Input Validation
- All requests validated with Pydantic
- File uploads size-restricted
- PHP code validated before processing

### Data Protection
- Database in secure storage directory
- Git repos with proper permissions
- No sensitive data in logs

### External API Security
- Gemini API key stored in environment variables
- Async processing isolates sensitive operations
- Rate limiting on AI requests

## 📈 Performance Characteristics

### Scalability
```
Single Job:
- 1-100 files: < 5 seconds
- 100-1000 files: 30-120 seconds (concurrent processing)
- Risk assessment: O(n) linear with files
- AI verification: Async, non-blocking

Database:
- SQLite: Single-file, good for < 100K records
- Upgrade path: PostgreSQL for production

Git:
- Per-job repos minimize conflicts
- Shallow clones for faster operations
```

### Memory Usage
```
Per Job:
- AST parsing: ~10MB per 1000 lines of code
- Service instances: < 50MB each
- Database connections pooled

Optimization:
- Streaming file processing
- Async/await for I/O
- Batch operations where possible
```

## 🛠️ Deployment Scenarios

### Development
```bash
uvicorn app.main:app --reload --port 8000
```

### Production (Single Server)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### Production (Docker)
```bash
docker build -t evua-backend .
docker run -p 8000:8000 evua-backend
```

### Production (Docker Compose)
```bash
docker-compose up -d
```

## 🔄 Integration Points

### With CI/CD
```
1. Upload code to EVUA
2. Run migration
3. Check risk scores
4. Block deployment if CRITICAL
5. Auto-create tickets for HIGH
6. Deploy if all cleared
```

### With Version Control
```
1. Git hooks trigger migration
2. EVUA processes files
3. Results committed to feature branch
4. Pull request created for review
5. CI checks results before merge
```

### With Package Managers
```
1. Dependency changes detected
2. Risk assessment triggered
3. AI verification of changed code
4. Report generated
5. Integration test execution
```

## 📊 Monitoring & Observability

### Logging
```python
logger.info("Migrated file: %s → %s", original_path, migrated_path)
logger.warning("High-risk code detected: %s (score: %.2f)", file, score)
logger.error("AI verification failed: %s", error)
```

### Metrics to Track
```
- Migration success rate
- Average risk score
- AI verification coverage
- Performance per file size
- Database size growth
- Git repo disk usage
```

### Health Checks
```
GET /health
├─ Database connectivity
├─ Git repo access
├─ Gemini API availability (optional)
└─ Disk space availability
```

## 🚀 Future Enhancements

### Phase 6+
1. Frontend UI components for all services
2. Real-time notifications/WebSocket updates
3. Parallel processing improvements
4. Advanced filtering/search
5. Custom rule creation
6. Integration with popular CI/CD systems
7. Multi-tenancy support
8. Advanced reporting/analytics

### Known Limitations
- SQLite for single-file deployments only
- Sequential AI verification (can batch)
- In-memory job queue (needs Redis for distributed)
- No distributed tracing yet
