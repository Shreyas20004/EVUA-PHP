# EVUA Testing & Verification Guide

Complete guide to test all implemented features of the PHP migration tool.

## 🚀 Quick Start Testing

### Step 1: Install Dependencies

```bash
# Backend
cd /e/Dev/major-proj/new_evua/evua/backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### Step 2: Start Services

**Terminal 1 - Backend:**
```bash
cd /e/Dev/major-proj/new_evua/evua/backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /e/Dev/major-proj/new_evua/evua/frontend
npm run dev
```

**Terminal 3 - Optional: Watch database**
```bash
# View database changes (Linux/Mac)
watch sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT * FROM migration_jobs LIMIT 5;"
```

## 📊 Testing Each Feature

### Feature 1: Monaco Editor Integration ✅

**Test in Frontend UI:**

1. Navigate to `http://localhost:5173`
2. Upload a PHP file (create test file if needed):
   ```php
   <?php
   $result = mysql_query("SELECT * FROM users");
   echo $result;
   ?>
   ```
3. Set source: 5.6, target: 8.0
4. Click "Migrate"
5. Wait for completion → Click "View Results"
6. **Expected:** Should see side-by-side code comparison in Monaco editor

**Test via API:**

```bash
# Get job results with code
curl http://localhost:8000/api/jobs/{job_id} | jq '.results[0] | {original_code, migrated_code}'

# Verify code is included
curl http://localhost:8000/api/jobs/{job_id} | jq '.results[0].original_code' | head -5
```

---

### Feature 2: Version Control ✅

**Test Version Creation:**

```bash
# Initialize version control
curl -X POST http://localhost:8000/api/versions/test-job-1/init

# Create a version (after migration)
curl -X POST http://localhost:8000/api/versions/{job_id}/create \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Initial migration complete",
    "stage": "initial",
    "files_changed": 5
  }'

# Get version history
curl http://localhost:8000/api/versions/{job_id}/history | jq '.'
```

**Test in Interactive Docs:**
1. Go to `http://localhost:8000/docs`
2. Find "version_control" section
3. Click `/api/versions/{job_id}/init` → Try it out
4. Enter job_id, Execute
5. **Expected:** Git repo created, commit SHA returned

**Database Verification:**

```bash
# Check versions in database
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT commit_hash, created_at, files_changed FROM version_snapshots;"

# Check if git repo exists
ls -la /e/Dev/major-proj/new_evua/evua/backend/storage/versions/
git log --oneline /e/Dev/major-proj/new_evua/evua/backend/storage/versions/{job_id}/
```

---

### Feature 3: Risk Assessment ✅

**Test Risk Scoring:**

```bash
# Assess a single file
curl -X POST http://localhost:8000/api/risk/assess \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-job-1",
    "file_path": "/path/to/file.php",
    "original_code": "<?php mysql_query(\"SELECT *\"); ?>",
    "migrated_code": "<?php mysqli_query($conn, \"SELECT *\"); ?>",
    "issue_count": 2,
    "ai_confidence": 0.85
  }' | jq '.'

# Get risk summary for job
curl http://localhost:8000/api/risk/{job_id}/summary | jq '.'

# Get critical files (HIGH/CRITICAL risk)
curl http://localhost:8000/api/risk/{job_id}/critical | jq '.'
```

**Test in Interactive Docs:**
1. Go to `http://localhost:8000/docs`
2. Find "risk_assessment" section
3. Try "assess_risk" endpoint
4. **Expected:** Risk score between 0-1, category returned

**Database Verification:**

```bash
# View all risk assessments
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT file_path, overall_score, risk_category FROM risk_assessments;"

# View high/critical files
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT file_path, overall_score FROM risk_assessments WHERE risk_category IN ('HIGH', 'CRITICAL');"
```

**Test Risk Metrics:**

```bash
# High-risk code example (should be CRITICAL)
python3 << 'EOF'
from pathlib import Path
import sys
sys.path.insert(0, '/e/Dev/major-proj/new_evua')

from backend.app.utils.risk_metrics import RiskMetricsCalculator

high_risk_code = """
<?php
eval($_POST['code']);
$$var = $value;
function create_dynamic() {
    for($i=0;$i<5;$i++) {
        for($j=0;$j<5;$j++) {
            for($k=0;$k<5;$k++) {
                mysql_query("SELECT *");
            }
        }
    }
}
?>
"""

factors = RiskMetricsCalculator.calculate_scores(high_risk_code, high_risk_code)
score, category = RiskMetricsCalculator.calculate_overall_risk(factors)
print(f"Score: {score:.2f}, Category: {category}")
print(f"Factors: {factors}")
EOF
```

---

### Feature 4: AI Verification ✅

**Test AI Verification:**

```bash
# Verify a single file
curl -X POST http://localhost:8000/api/ai/verify/test-job-1 \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/test.php",
    "original_code": "<?php mysql_connect(); ?>",
    "migrated_code": "<?php new PDO(); ?>",
    "risk_factors": {"complexity": 0.8, "dependencies": 0.6}
  }' | jq '.'

# Get AI verifications for job
curl http://localhost:8000/api/ai/verify/test-job-1/results | jq '.'

# Approve a suggestion
curl -X POST http://localhost:8000/api/ai/verify/{section_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer_notes": "Looks good to me"}' | jq '.'

# Apply the fix
curl -X POST http://localhost:8000/api/ai/verify/{section_id}/apply | jq '.'
```

**Test in Interactive Docs:**
1. Go to `http://localhost:8000/docs`
2. Find "ai_verification" section
3. Try "verify_code" endpoint
4. **Expected:** AI feedback, suggested fix, confidence score returned

**Database Verification:**

```bash
# View all AI verifications
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT file_path, review_status, confidence_score FROM ai_verifications;"

# View approved suggestions
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db \
  "SELECT section_id, file_path, approved_by_user FROM ai_verifications WHERE approved_by_user = 1;"
```

---

### Feature 5: Database Operations ✅

**Inspect Database:**

```bash
# Open SQLite database
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db

# Inside SQL shell:
.tables
.schema migration_jobs
SELECT * FROM migration_jobs;
SELECT * FROM risk_assessments;
SELECT * FROM ai_verifications;
SELECT * FROM version_snapshots;
SELECT * FROM change_history;
```

**Test Database Relationships:**

```bash
# Get all data for a job
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db << 'EOF'
SELECT
  j.job_id,
  j.status,
  COUNT(DISTINCT r.id) as risk_assessments,
  COUNT(DISTINCT a.id) as ai_verifications,
  COUNT(DISTINCT v.id) as versions
FROM migration_jobs j
LEFT JOIN risk_assessments r ON j.job_id = r.job_id
LEFT JOIN ai_verifications a ON j.job_id = a.job_id
LEFT JOIN version_snapshots v ON j.job_id = v.job_id
GROUP BY j.job_id;
EOF
```

---

## 🧪 Complete End-to-End Test

### Scenario: Migrate Single File and Test All Features

**Step 1: Prepare Test File**

```bash
cat > /tmp/test_migration.php << 'EOF'
<?php
// Legacy PHP 5.6 code with issues
$conn = mysql_connect("localhost", "user", "pass");
$result = mysql_query("SELECT * FROM users");

while ($row = mysql_fetch_assoc($result)) {
    echo $row['id'];
    eval("echo 'User: ' . $row['name'];");
    $$field = $row['value'];
}

mysql_close($conn);
?>
EOF
```

**Step 2: Manually Test Each API**

```bash
# 1. Upload file
JOB_ID=$(uuidgen)  # or use test-job-1

# 2. Create migration job (using existing API)
curl -X POST http://localhost:8000/api/migrate \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"source_version\": \"5.6\",
    \"target_version\": \"8.0\",
    \"file_paths\": [\"/tmp/test_migration.php\"],
    \"use_mock_ai\": true
  }" > response.json

# Extract job_id or use $JOB_ID
JOB_ID=$(jq -r '.job_id' response.json)

# 3. Wait for migration to complete
sleep 5

# 4. Get migration results
curl http://localhost:8000/api/jobs/$JOB_ID | jq '.results[0] | {file_path, status, original_code, migrated_code}' > migration_result.json

# 5. Extract codes from result
ORIG_CODE=$(jq -r '.original_code' migration_result.json)
MIG_CODE=$(jq -r '.migrated_code' migration_result.json)

# 6. Initialize version control
curl -X POST http://localhost:8000/api/versions/$JOB_ID/init | jq '.'

# 7. Create initial version
curl -X POST http://localhost:8000/api/versions/$JOB_ID/create \
  -H "Content-Type: application/json" \
  -d '{"message":"Initial migration","stage":"initial","files_changed":1}' | jq '.'

# 8. Assess risk
curl -X POST http://localhost:8000/api/risk/assess \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"file_path\": \"/tmp/test_migration.php\",
    \"original_code\": $ORIG_CODE,
    \"migrated_code\": $MIG_CODE,
    \"issue_count\": 3,
    \"ai_confidence\": 0.72
  }" | jq '.'

# 9. Get risk summary
curl http://localhost:8000/api/risk/$JOB_ID/summary | jq '.'

# 10. Get critical files
curl http://localhost:8000/api/risk/$JOB_ID/critical | jq '.'

# 11. Verify with AI
curl -X POST http://localhost:8000/api/ai/verify/$JOB_ID \
  -H "Content-Type: application/json" \
  -d "{
    \"file_path\": \"/tmp/test_migration.php\",
    \"original_code\": $ORIG_CODE,
    \"migrated_code\": $MIG_CODE,
    \"risk_factors\": {\"complexity\": 0.75, \"patterns\": 0.8}
  }" | jq '.' > verification_result.json

# 12. Extract section_id and test approval
SECTION_ID=$(jq -r '.section_id' verification_result.json)

# 13. Approve suggestion
curl -X POST http://localhost:8000/api/ai/verify/$SECTION_ID/approve \
  -H "Content-Type: application/json" \
  -d '{"reviewer_notes":"Verified and looks correct"}' | jq '.'

# 14. Apply fix
curl -X POST http://localhost:8000/api/ai/verify/$SECTION_ID/apply | jq '.corrected_code'

# 15. Get version history (should have multiple commits now)
curl http://localhost:8000/api/versions/$JOB_ID/history | jq '.versions | length'

# 16. Query database to see all records
sqlite3 /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db << 'EOF'
SELECT 'Jobs' as table_name, COUNT(*) as count FROM migration_jobs
UNION ALL
SELECT 'Risk Assessments', COUNT(*) FROM risk_assessments
UNION ALL
SELECT 'AI Verifications', COUNT(*) FROM ai_verifications
UNION ALL
SELECT 'Versions', COUNT(*) FROM version_snapshots;
EOF
```

---

## ✅ Verification Checklist

**Backend Services:**
- [ ] FastAPI starts without errors
- [ ] `/health` endpoint responds
- [ ] `/docs` shows all endpoints

**Database:**
- [ ] SQLite file created at `backend/storage/evua.db`
- [ ] All 5 tables created
- [ ] Data persists after restart

**Version Control:**
- [ ] Git repos created in `backend/storage/versions/`
- [ ] Commits are recorded
- [ ] History API returns commits

**Risk Assessment:**
- [ ] Risk scores between 0-1
- [ ] Categories assigned correctly
- [ ] Recommendations generated

**AI Verification:**
- [ ] AI feedback returned
- [ ] Confidence scores assigned
- [ ] Approve/reject endpoints work
- [ ] Fixes can be applied

**Frontend Monaco:**
- [ ] Code displays side-by-side
- [ ] Syntax highlighting works
- [ ] Statistics display (lines, bytes)

**Integration:**
- [ ] Frontend connects to backend
- [ ] Migration results show in UI
- [ ] All tabs work correctly

---

## 🐛 Troubleshooting

**401 Errors on Gemini:**
```
Solution: Use mock AI (use_mock_ai: true) or provide valid GEMINI_API_KEY
```

**Database Lock:**
```
Solution: Kill any old processes, delete database, restart
rm /e/Dev/major-proj/new_evua/evua/backend/storage/evua.db
```

**Git Permission Errors:**
```
Solution: Check folder permissions, ensure git is installed
git config --global user.email "test@evua.local"
git config --global user.name "EVUA Test"
```

**Monaco Not Loading:**
```
Solution: Clear npm cache, reinstall
npm cache clean --force
npm install
```

**Port Already in Use:**
```
Solution: Use different port
uvicorn app.main:app --port 8001
```

---

## 📈 Performance Testing

```bash
# Test multiple file processing
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/risk/assess \
    -H "Content-Type: application/json" \
    -d "{
      \"job_id\": \"bench-test\",
      \"file_path\": \"/file$i.php\",
      \"original_code\": \"<?php echo 'test'; ?>\",
      \"migrated_code\": \"<?php echo 'test'; ?>\",
      \"issue_count\": 1,
      \"ai_confidence\": 0.9
    }" &
done
wait

# Check response times in logs
```

---

## 📝 Test Results Template

Use this to document test results:

```markdown
# Test Results - [Date]

## Backend Status
- [ ] FastAPI: PASS / FAIL
- [ ] Database: PASS / FAIL
- [ ] Health endpoint: PASS / FAIL

## Feature Tests
- [ ] Monaco Editor: PASS / FAIL
- [ ] Version Control: PASS / FAIL
- [ ] Risk Assessment: PASS / FAIL
- [ ] AI Verification: PASS / FAIL
- [ ] Database: PASS / FAIL

## End-to-End
- [ ] E2E Migration: PASS / FAIL
- [ ] Full Workflow: PASS / FAIL

## Errors
(Note any errors here)

## Notes
(Additional observations)
```

---

## Next: Frontend Integration Testing

Once Phase 6 (frontend UI components) is complete, additional testing will focus on:
- UI rendering of version history
- Risk dashboard visualization
- AI review approval workflow
- Real-time updates
- Error handling
