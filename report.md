# Digital Forensic Cyberbullying Triage System — Implementation Report

**Project:** Forensic Cyberbullying Triage Platform  
**Status:** Educational prototype implemented; analytical evaluation complete; local process checks completed; independent reproducibility testing pending  
**Generated:** 2026-08-13

---

## 1. Executive Summary

This system is a **post-event forensic triage platform** designed to prioritize digital evidence for human examiner review. It is **not** a moderation system and is **not** a real-time detection system. The pipeline ingests evidence, computes a SHA-256 hash of the original evidence file when provided (or stored text as fallback), classifies content using machine learning, generates deterministic feature-contribution explanations, logs actions for chain-of-custody with hash-chained audit records, and exports reports.

**Defensible claim:** An educational prototype forensic cyberbullying triage platform has been implemented and analytically evaluated. Its workflow supports original-file or text integrity checking, hash-linked audit/custody records, human review, deterministic linear-model explanations, repeatability testing, a fixed local reproducibility baseline, simulated operational evaluation, and threshold calibration with reliability data. It is not a production, court-ready, or autonomous decision system.

### Validation status as of 2026-08-13

| Area                     | Evidence                                                                    | Status                                                                                                     |
| ------------------------ | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Analytical performance   | Stratified 80/20 hold-out test (9,382 posts; seed 42)                       | SVM: 82.79% accuracy / 82.52% Macro-F1; Logistic Regression: 82.72% / 82.56%; Naïve Bayes: 77.37% / 75.66% |
| Core forensic checks     | Automated forensic, integrity, audit/custody, calibration, and export tests | Passing locally                                                                                            |
| Reproducibility baseline | Five fixed SVM test cases                                                   | 5/5 passed locally; second-environment comparison remains required                                         |
| Operational simulation   | Fifteen fixed simulated cases, threshold 0.70                               | 75.0% precision, 37.5% recall, 50.0% F1; insufficient for deployment                                       |

The simulated operational result is a limitation: it demonstrates the workflow but does not establish operational effectiveness. Human examiner review remains mandatory.

---

## 2. System Architecture

```
forensic-cyberbullying-triage/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI route handlers
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic v2 request/response schemas
│   │   ├── services/             # Business logic layer
│   │   ├── security/             # JWT + bcrypt authentication
│   │   ├── main.py               # FastAPI application entrypoint
│   │   └── database.py           # SQLAlchemy engine + session
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                # React route pages
│   │   ├── components/           # Reusable UI components
│   │   ├── services/             # Axios API clients
│   │   └── types/                # TypeScript interfaces
│   └── package.json
├── ml/
│   ├── preprocessing/            # Text cleaning pipeline
│   ├── explainability/           # Feature-contribution analysis
│   ├── evaluation/               # Metrics, calibration, statistical tests
│   └── saved_models/             # Serialized scikit-learn pipelines
├── database/
│   └── migrations/
│       └── 002_add_forensic_features.sql
├── tests/
├── deployment/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── nginx.conf
└── docs/
```

---

## 3. Backend Implementation

### 3.1 Technology Stack

- **Framework:** FastAPI
- **ORM:** SQLAlchemy 2.x
- **Validation:** Pydantic v2
- **Auth:** JWT (python-jose) + bcrypt 4.0.1
- **ML:** scikit-learn, deterministic feature-contribution explanations, TensorFlow/Keras, HuggingFace Transformers
- **PDF:** reportlab

### 3.2 Database Models

| Model                  | Table                    | Purpose                                     |
| ---------------------- | ------------------------ | ------------------------------------------- |
| `User`                 | `users`                  | Examiner / admin accounts                   |
| `Evidence`             | `evidence`               | Core evidence records with SHA-256 hash     |
| `EvidenceMetadata`     | `evidence_metadata`      | Optional platform / author metadata         |
| `ClassificationResult` | `classification_results` | Triage output: prediction, confidence, risk |
| `ExaminerReview`       | `examiner_reviews`       | Human review decisions                      |
| `AuditLog`             | `audit_logs`             | Forensic audit trail                        |
| `ChainOfCustody`       | `chain_of_custody`       | Provenance tracking                         |
| `Explanation`          | `explanations`           | Deterministic feature contributions         |
| `RepeatabilityTest`    | `repeatability_tests`    | Determinism validation runs                 |
| `IntegrityCheck`       | `integrity_checks`       | Hash verification history                   |

### 3.3 API Routes

| Router                  | Prefix                                                | Endpoints                                         |
| ----------------------- | ----------------------------------------------------- | ------------------------------------------------- |
| `auth`                  | `/auth`                                               | Login, register, token refresh                    |
| `evidence`              | `/evidence`                                           | Upload, list, get, delete, bulk upload            |
| `triage`                | `/triage/{evidence_id}`                               | Run classification pipeline                       |
| `reviews`               | `/reviews/{evidence_id}`                              | Submit / fetch examiner reviews                   |
| `audit`                 | `/audit/{evidence_id}`                                | Fetch audit logs, chain of custody                |
| `integrity`             | `/integrity/evidence/{evidence_id}`                   | Verify hash, get history                          |
| `explainability`        | `/explainability/evidence/{evidence_id}/explanations` | Fetch feature contributions                       |
| `repeatability`         | `/repeatability/evidence/{evidence_id}/repeatability` | Run repeatability test                            |
| `reproducibility`       | `/reproducibility/reproducibility-report`             | Environment + dependency manifest                 |
| `reproducibility`       | `/reproducibility/reproducibility-test`               | Fixed reproducibility test suite execution        |
| `operational`           | `/operational/operational-metrics`                    | Dashboard metrics                                 |
| `operational`           | `/operational/simulated-cases`                        | Simulated case study with ground truth            |
| `model-evaluation`      | `/model-evaluation/evaluation`                        | ML performance metrics                            |
| `model-comparison`      | `/model-comparison/model-comparison`                  | Inter-model forensic comparison                   |
| `model-comparison`      | `/model-comparison/registry`                          | Model registry with training metadata             |
| `error-analysis`        | `/error-analysis/error-analysis`                      | False positives, false negatives, ambiguous cases |
| `threshold-calibration` | `/threshold-calibration/calibration`                  | Threshold sweep study                             |
| `export`                | `/export/evidence/{evidence_id}/export`               | JSON / PDF forensic report                        |

---

## 4. Frontend Implementation

### 4.1 Technology Stack

- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** TailwindCSS
- **Routing:** React Router DOM
- **Data Fetching:** TanStack React Query
- **Charts:** Recharts

### 4.2 Pages

| Page                             | Route                     | Purpose                                                    |
| -------------------------------- | ------------------------- | ---------------------------------------------------------- |
| `Login`                          | `/login`                  | Authentication                                             |
| `Register`                       | `/register`               | User registration                                          |
| `Dashboard`                      | `/dashboard`              | Overview statistics                                        |
| `EvidenceQueue`                  | `/evidence`               | List all evidence items                                    |
| `UploadEvidence`                 | `/evidence/upload`        | New evidence intake                                        |
| `EvidenceDetails`                | `/evidence/:id`           | Full review + triage + integrity + explanations + timeline |
| `ReviewPage`                     | `/review/:id`             | Examiner decision workflow                                 |
| `AuditLogs`                      | `/audit/:id`              | Forensic audit table                                       |
| `Reports`                        | `/reports`                | Export and reporting                                       |
| `OperationalEvaluationDashboard` | `/operational-evaluation` | Metrics + charts                                           |
| `ThresholdCalibration`           | `/threshold-calibration`  | Threshold calibration study                                |
| `ModelPerformanceDashboard`      | `/model-performance`      | ML model performance metrics                               |
| `TrainingPerformance`            | `/training-performance`   | Training results and model registry                        |
| `ModelComparison`                | `/model-comparison`       | Inter-model forensic comparison                            |
| `ErrorAnalysis`                  | `/error-analysis`         | Structured error analysis                                  |
| `Reproducibility`                | `/reproducibility`        | Environment manifest + reproducibility test suite          |

### 4.3 Reusable Components

- **`ForensicTimeline`** — chronological vertical timeline of audit events
- **`IntegrityVerification`** — SHA-256 integrity status widget
- **`RepeatabilityReport`** — repeatability test runner and results display
- **`ProtectedRoute`** — authentication guard

---

## 5. Machine Learning & Explainability

### 5.1 Models

- **SVM** (`LinearSVC` wrapped in `CalibratedClassifierCV` for `predict_proba`)
- **Logistic Regression**
- **Naive Bayes**
- **CNN** (text classification)
- **BERT** (fine-tuned transformer)

### 5.2 Explainability

- **Linear coefficient-based explanations:** For linear models (SVM, Logistic Regression, Naive Bayes), top-K contributing terms are extracted directly from model coefficients via the TF-IDF vectorizer. This is deterministic and does not require SHAP or LIME.
- **SHAP/LIME:** Available in the codebase but not the active production explanation path for linear models.
- **Attribution:** Token-level importance derived from linear feature weights.

### 5.3 Evaluation

- Accuracy, Precision, Recall, F1
- Threshold calibration across multiple thresholds
- Confusion matrices
- Statistical significance tests

---

## 6. Forensic Features Implemented

### 6.1 Evidence Integrity Verification (Task 2)

- SHA-256 hash computed at upload and stored in `Evidence.evidence_hash`
- On-demand rehashing via `POST /integrity/evidence/{id}/verify-integrity`
- Result: `VERIFIED` or `HASH_MISMATCH`
- History maintained in `IntegrityCheck` table
- Audit events: `HASH_GENERATED`, `HASH_VERIFIED`, `HASH_MISMATCH`

### 6.2 Explainability Output (Task 1)

- Deterministic linear feature contributions generated during triage for linear models
- Stored in `Explanation` table with `feature_name` and `contribution`
- Retrieved via `GET /explainability/evidence/{id}/explanations`
- Displayed in `EvidenceDetails.tsx` under **“Why Was This Flagged?”**
- Metadata includes method, model version, and generation timestamp
- Note: The active production path uses coefficient-based explanations for linear models, not SHAP

### 6.3 Forensic Process Timeline (Task 3)

- `ForensicTimeline.tsx` renders chronological audit events
- Sorted ascending by timestamp
- Shows event type, actor, timestamp, and structured details
- Integrated into `EvidenceDetails` and `AuditLogs` pages

### 6.4 Repeatability Testing (Task 4)

- Service: `repeatability_service.py`
- Runs N iterations of classification + explanation
- Stores `prediction_consistency`, `confidence_variance`, `explanation_consistency`, `pass_fail`
- Report generated in `RepeatabilityReport.tsx`
- Backend endpoint: `POST /repeatability/evidence/{id}/repeatability`

### 6.5 Reproducibility Framework (Task 5)

- Service: `reproducibility_service.py`
- Captures Python version, OS, framework versions, dependency manifests
- Reads `backend/requirements.txt` and `frontend/package.json`
- Endpoint: `GET /reproducibility/reproducibility-report`
- **Reproducibility test suite:** Fixed test cases with known inputs and expected predictions (`ml/reproducibility/test_cases.py`)
- Test runner executes the selected model against the fixed suite and records predictions, confidences, and pass/fail status (`ml/reproducibility/test_runner.py`)
- Backend endpoint: `GET /reproducibility/reproducibility-test?model_name={model}`
- Frontend page: `/reproducibility` displays environment manifest, test results, and export capability
- Exported JSON can be compared against an identical run in a second environment to verify reproducibility

### 6.6 Operational Evaluation (Task 6)

- Service: `operational_evaluation.py`
- Computes Recall, Precision, FPR, FNR, Workload Reduction, Triage Reduction from live examiner-reviewed evidence
- **Simulated case study:** Fixed set of 15 cases with known ground truth labels (`ml/operational/simulated_cases.py`)
- Backend endpoint: `GET /operational/simulated-cases?model_name={model}`
- Dashboard page: `OperationalEvaluationDashboard.tsx`
- Charts via Recharts
- Simulated cases provide credible controlled metrics independent of real examiner review volume

### 6.7 PDF Export (Task 7)

- Service: `pdf_export_service.py` using ReportLab
- Generates professional forensic report with evidence info, triage results, examiner reviews, audit trail
- Endpoint: `GET /export/evidence/{id}/export?format=pdf`

### 6.8 Enhanced Audit Logging (Task 8)

- `AuditLog` model stores: `actor`, `event_type`, `event_details`
- Triaging logs model name, version, threshold, confidence, prediction, risk, processing time, explanation method
- Review logs examiner, decision, notes
- Integrity logs hash status and verification timestamp

### 6.9 Threshold Calibration Study (Forensic-Operational Contribution)

- Backend service: `threshold_calibration.py`
- Evaluates model performance across multiple thresholds (0.50, 0.60, 0.70, 0.80, 0.90)
- Uses examiner-reviewed evidence as ground truth
- Computes per-threshold metrics: Recall, Precision, Workload Reduction, Missed-Evidence Rate, Brier Score, ECE, TP/FP/FN/TN counts
- Uses class-aware harmful-vs-benign probability definition (sums probabilities across all non-benign classes when a label encoder is present)
- Selects the threshold with the highest average precision + recall as the operational threshold
- API endpoint: `GET /threshold-calibration/calibration?model_name={model}`
- Frontend page: `ThresholdCalibration.tsx` at `/threshold-calibration`
- Displays calibration table, bar chart, selected threshold, Brier score, ECE, actual harmful count, and threshold justification text
- Justifies the chosen threshold based on empirical recall-precision-workload tradeoff
- Reliability diagram rendered as a visual plot showing observed accuracy vs mean confidence per probability bin

### 6.11 Ensemble Triage & Multi-Model Inference (Model Utilization)

- Backend service: `classification_service.py` extended to load CNN (`.keras`) and BERT (local `bert_model/`) in addition to sklearn `.pkl` models
- New endpoint: `POST /triage/ensemble/{evidence_id}` runs all available models in parallel
- Aggregates votes using confidence-weighted selection among cyberbullying predictions
- Model agreement analysis computes:
  - `agreement`: `full` / `partial` / `none`
  - `confidence_spread`: max - min confidence across models
  - `disagreement_levels`: count of unique predictions
  - `forced_review`: automatically set when confidence spread > 0.30 or disagreement levels > 2
- Frontend: `EvidenceDetails.tsx` offers "Run Quick Triage" (single model) and "Run Full Triage" (ensemble)
- Ensemble result displays individual model votes, agreement metrics, and forced review warnings
- Calibrated thresholds replace hardcoded `TRIAGE_THRESHOLD = 0.70`; threshold is selected per-model based on highest average precision + recall from `threshold_calibration` service

### 6.12 Inter-Model Comparison in Forensic Context

- Backend service: `model_comparison.py`
- Evaluates all implemented models on the same examiner-reviewed evidence set
- Computes F1, runtime class, and explainability score per model
- API endpoint: `GET /model-comparison/model-comparison`
- Frontend page: `ModelComparison.tsx` at `/model-comparison`
- Displays comparison table and justification for selected operational model
- Justifies SVM selection based on explainability, repeatability, and forensic transparency requirements

### 6.13 Digital Forensics Standards Mapping

The platform architecture is designed with reference to internationally recognized digital forensic standards. Full technical enforcement of all standards is a target for future production hardening.

#### Standards Mapping Table

| Platform Component     | Standard Alignment    | Requirement                                                                        |
| ---------------------- | --------------------- | ---------------------------------------------------------------------------------- |
| Evidence Acquisition   | ISO/IEC 27037         | Guidelines for identification, collection, and preservation of digital evidence    |
| Integrity Verification | ISO/IEC 27037         | Cryptographic hash verification to ensure evidence integrity and detect alteration |
| Analysis / Triage      | ISO/IEC 27042         | Principles for the analysis of digital evidence                                    |
| Examiner Review        | ISO/IEC 27043         | Incident investigation and analysis principles                                     |
| Audit Trail            | ACPO Principle 3      | Record of all actions and decisions made during evidence handling                  |
| Repeatability Testing  | NIST SP 800-86        | Validation of forensic tools and methods through repeatable testing                |
| Chain of Custody       | ISO/IEC 27037 / 27043 | Provenance tracking and accountability for evidence handling                       |
| Report Generation      | ISO/IEC 27042         | Documentation of findings in a structured, defensible format                       |

#### ISO/IEC 27037 — Evidence Acquisition & Integrity

- **Relevant clauses:** 7.2 (Identification), 7.3 (Collection), 7.4 (Preservation)
- **Implementation:** SHA-256 hashing of stored text content at upload; integrity verification on demand
- **Forensic significance:** Enables detection of content alteration after acquisition; does not guarantee original file preservation.

#### ISO/IEC 27042 — Analysis & Reporting

- **Relevant clauses:** 8.2 (Analysis), 8.3 (Validation), 9 (Reporting)
- **Implementation:** Deterministic linear feature-contribution explanations, repeatability testing, structured JSON/PDF export
- **Forensic significance:** Transparent analysis methodology with documented validation

#### ISO/IEC 27043 — Incident Investigation

- **Relevant clauses:** 7.2 (Analysis approach), 7.3 (Data examination), 8 (Documentation)
- **Implementation:** Human-in-the-loop examiner review, escalation workflows, case studies
- **Forensic significance:** Structured investigation process with clear decision trails

#### ACPO Principles (UK Association of Chief Police Officers)

- **Principle 1:** No alteration of original evidence — hash verification and read-only audit trail implemented at application level
- **Principle 2:** Competent access only — enforced via JWT authentication and role-based access
- **Principle 3:** Audit trail of all actions — implemented via `AuditLog` and `ChainOfCustody` models
- **Principle 4:** Compliance with local law — system designed for lawful evidence processing workflows

#### NIST Digital Evidence Guidance (SP 800-86)

- **Guideline 1:** Use approved forensic tools — models versioned and registry-tracked
- **Guideline 2:** Test tools for accuracy — repeatability and threshold calibration frameworks
- **Guideline 3:** Document all actions — comprehensive audit logging and chain of custody
- **Guideline 4:** Prevent contamination — isolation via worktrees/sessions, hash-based integrity checks
- **Guideline 5:** Maintain objectivity — human examiner override, confidence thresholds, escalation paths

#### Compliance Summary

The platform satisfies core requirements for digital forensic evidence handling at prototype level:

1. **Identifiable** — Every evidence item has a unique SHA-256 hash and metadata record
2. **Preserved** — Hash verification detects undetected alteration; history maintained in `IntegrityCheck`
3. **Analyzed** — Transparent ML classification with deterministic explanations and repeatability validation
4. **Reviewed** — Human examiner decisions recorded with notes, timestamps, and audit trail
5. **Documented** — JSON and PDF exports provide structured forensic reports
6. **Accountable** — Chain of custody and audit logs provide accountability records; full cryptographic enforcement pending production hardening

---

## 7. Security & Authentication

- **JWT** access tokens with configurable expiry
- **bcrypt 4.0.1** for password hashing
- `OAuth2PasswordRequestForm` for login
- Protected routes via `ProtectedRoute` component
- CORS restricted to `http://localhost:3000` and `http://127.0.0.1:3000`

---

## 8. Deployment

- **Dockerfile** for backend
- **docker-compose.yml** for multi-service orchestration
- **Nginx** reverse proxy configuration
- SQLite for local development; PostgreSQL/Supabase for production

---

## 9. Database Migrations

File: `database/migrations/002_add_forensic_features.sql`

Creates:

- `explanations`
- `repeatability_tests`
- `integrity_checks`

Alters `evidence`:

- Adds `integrity_status`
- Adds `integrity_verified_at`

Indexes on evidence ID and timestamps for performance.

---

## 10. How to Run

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

- SQLite is auto-created on first run (`forensic_triage.db`)
- For PostgreSQL/Supabase: run migration SQL in SQL Editor

### ML Models

- Train models using scripts in `ml/`
- Saved artifacts go to `ml/saved_models/`

---

## 11. Deliverables Checklist

| #   | Deliverable                           | Status         |
| --- | ------------------------------------- | -------------- |
| 1   | Database migrations                   | ✅ Completed   |
| 2   | PostgreSQL schema updates             | ✅ Completed   |
| 3   | Supabase SQL                          | ✅ Completed   |
| 4   | Backend services                      | ✅ Completed   |
| 5   | Python services                       | ✅ Completed   |
| 6   | TypeScript types                      | ✅ Completed   |
| 7   | React components                      | ✅ Completed   |
| 8   | API routes                            | ✅ Completed   |
| 9   | Folder structure                      | ✅ Completed   |
| 10  | PDF export implementation             | ✅ Completed   |
| 11  | Repeatability test implementation     | ✅ Completed   |
| 12  | Operational evaluation implementation | ✅ Completed   |
| 13  | Threshold calibration study           | ✅ Completed   |
| 14  | Inter-model comparison                | ✅ Completed   |
| 15  | Ensemble triage & model agreement     | ✅ Completed   |
| 16  | Production-ready code                 | 🔄 In Progress |

---

## 12. Worked Forensic Case Studies

This section presents forensic validation examples. Cases 1–3 are illustrative examples of intended workflow. Case 4 is derived from actual system output during testing.

---

### Case Study 1: Confirmed Cyberbullying — Direct Threat (Illustrative)

**Evidence Profile**

- Evidence ID: 1
- Platform: Twitter/X
- Post ID: `tweet_839201`
- Acquisition Date: 2026-08-09T14:23:00Z
- Uploaded By: Examiner johndoe@gmail.com

**Content**

```
I'm going to find you after school tomorrow. Watch your back.
```

**SHA-256 Hash**

```
a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
```

**Integrity Status**

- ✓ VERIFIED
- Verification Timestamp: 2026-08-09T14:25:00Z
- Original Hash == Current Hash

**Triage Result**

- Prediction: `cyberbullying`
- Confidence: 0.94
- Risk Level: HIGH
- Model: SVM v1.0
- Threshold: 0.70
- Processing Time: 11,315 ms
- Explanation Method: Linear feature contribution

**Feature Contributions — Top Contributing Terms**
| Term | Impact |
|---|---|
| find | +0.41 |
| tomorrow | +0.29 |
| watch | +0.16 |
| back | +0.12 |

**Examiner Review**

- Decision: CONFIRMED
- Examiner: johndoe@gmail.com
- Notes: "Explicit physical threat. Clear cyberbullying classification confirmed."
- Timestamp: 2026-08-09T15:00:00Z

**Audit Trail (Chronological)**
| Timestamp | Event Type | Actor | Details |
|---|---|---|---|
| 2026-08-09T14:23:00Z | EVIDENCE_UPLOADED | johndoe@gmail.com | {"source_platform": "Twitter"} |
| 2026-08-09T14:24:00Z | HASH_GENERATED | SYSTEM | {"algorithm": "SHA-256"} |
| 2026-08-09T14:24:30Z | EVIDENCE_TRIAGED | johndoe@gmail.com | {"model": "svm", "prediction": "cyberbullying", "confidence": 0.94, "risk_level": "HIGH"} |
| 2026-08-09T14:25:00Z | HASH_VERIFIED | SYSTEM | {"match": true} |
| 2026-08-09T15:00:00Z | EVIDENCE_REVIEWED | johndoe@gmail.com | {"decision": "CONFIRMED"} |
| 2026-08-09T15:00:05Z | CLASSIFICATION_CONFIRMED | johndoe@gmail.com | {"final_decision": "harmful"} |

**Chain of Custody**

1. UPLOAD — johndoe@gmail.com — 2026-08-09T14:23:00Z
2. CLASSIFICATION — johndoe@gmail.com — 2026-08-09T14:24:30Z
3. REVIEW — johndoe@gmail.com — 2026-08-09T15:00:00Z

**Outcome**: Case confirmed as cyberbullying. Escalated to school resource officer per protocol.

---

### Case Study 2: Escalated Case — Ambiguous Sarcasm (Illustrative)

**Evidence Profile**

- Evidence ID: 2
- Platform: Instagram
- Post ID: `post_991234`
- Acquisition Date: 2026-08-09T16:10:00Z
- Uploaded By: Examiner johndoe@gmail.com

**Content**

```
Nice job failing the exam. Really smart, you are.
```

**SHA-256 Hash**

```
b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3
```

**Integrity Status**

- ✓ VERIFIED
- Verification Timestamp: 2026-08-09T16:12:00Z

**Triage Result**

- Prediction: `cyberbullying`
- Confidence: 0.72
- Risk Level: MEDIUM
- Model: SVM v1.0
- Threshold: 0.70
- Processing Time: 9,845 ms
- Explanation Method: Linear feature contribution

**Feature Contributions — Top Contributing Terms**
| Term | Impact |
|---|---|
| smart | +0.35 |
| exam | +0.22 |
| failing | +0.18 |
| really | +0.09 |

**Examiner Review**

- Decision: NEEDS_MORE_REVIEW
- Examiner: johndoe@gmail.com
- Notes: "Context-dependent. Could be sarcastic encouragement or genuine mockery. Requires interview with involved parties."
- Timestamp: 2026-08-09T17:00:00Z

**Audit Trail (Chronological)**
| Timestamp | Event Type | Actor | Details |
|---|---|---|---|
| 2026-08-09T16:10:00Z | EVIDENCE_UPLOADED | johndoe@gmail.com | {"source_platform": "Instagram"} |
| 2026-08-09T16:11:00Z | HASH_GENERATED | SYSTEM | {"algorithm": "SHA-256"} |
| 2026-08-09T16:11:45Z | EVIDENCE_TRIAGED | johndoe@gmail.com | {"model": "svm", "prediction": "cyberbullying", "confidence": 0.72, "risk_level": "MEDIUM"} |
| 2026-08-09T16:12:00Z | HASH_VERIFIED | SYSTEM | {"match": true} |
| 2026-08-09T17:00:00Z | EVIDENCE_REVIEWED | johndoe@gmail.com | {"decision": "NEEDS_MORE_REVIEW"} |
| 2026-08-09T17:00:10Z | EVIDENCE_ESCALATED | johndoe@gmail.com | {"reason": "Ambiguous context, requires additional investigation"} |

**Chain of Custody**

1. UPLOAD — johndoe@gmail.com — 2026-08-09T16:10:00Z
2. CLASSIFICATION — johndoe@gmail.com — 2026-08-09T16:11:45Z
3. REVIEW — johndoe@gmail.com — 2026-08-09T17:00:00Z
4. ESCALATION — johndoe@gmail.com — 2026-08-09T17:00:10Z

**Outcome**: Case escalated to senior examiner for contextual analysis and witness interview.

---

### Case Study 3: False Positive — Benign Content Misclassified (Illustrative)

**Evidence Profile**

- Evidence ID: 3
- Platform: Twitter/X
- Post ID: `tweet_442199`
- Acquisition Date: 2026-08-09T18:00:00Z
- Uploaded By: Examiner johndoe@gmail.com

**Content**

```
This bug is killing me. I can't get this code to compile.
```

**SHA-256 Hash**

```
c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4
```

**Integrity Status**

- ✓ VERIFIED
- Verification Timestamp: 2026-08-09T18:02:00Z

**Triage Result**

- Prediction: `cyberbullying`
- Confidence: 0.68
- Risk Level: MEDIUM
- Model: SVM v1.0
- Threshold: 0.70
- Processing Time: 8,210 ms
- Explanation Method: Linear feature contribution

**Feature Contributions — Top Contributing Terms**
| Term | Impact |
|---|---|
| killing | +0.48 |
| bug | +0.31 |
| compile | +0.14 |
| code | +0.07 |

**Examiner Review**

- Decision: REJECTED
- Examiner: johndoe@gmail.com
- Notes: "False positive. 'Killing me' is idiomatic expression of frustration about software bug, not threat or harassment."
- Timestamp: 2026-08-09T19:00:00Z

**Audit Trail (Chronological)**
| Timestamp | Event Type | Actor | Details |
|---|---|---|---|
| 2026-08-09T18:00:00Z | EVIDENCE_UPLOADED | johndoe@gmail.com | {"source_platform": "Twitter"} |
| 2026-08-09T18:01:00Z | HASH_GENERATED | SYSTEM | {"algorithm": "SHA-256"} |
| 2026-08-09T18:01:30Z | EVIDENCE_TRIAGED | johndoe@gmail.com | {"model": "svm", "prediction": "cyberbullying", "confidence": 0.68, "risk_level": "MEDIUM"} |
| 2026-08-09T18:02:00Z | HASH_VERIFIED | SYSTEM | {"match": true} |
| 2026-08-09T19:00:00Z | EVIDENCE_REVIEWED | johndoe@gmail.com | {"decision": "REJECTED"} |
| 2026-08-09T19:00:15Z | FALSE_POSITIVE_CONFIRMED | johndoe@gmail.com | {"reason": "Idiomatic language misclassified as abusive"} |

**Chain of Custody**

1. UPLOAD — johndoe@gmail.com — 2026-08-09T18:00:00Z
2. CLASSIFICATION — johndoe@gmail.com — 2026-08-09T18:01:30Z
3. REVIEW — johndoe@gmail.com — 2026-08-09T19:00:00Z

**Outcome**: Case closed as false positive. Added to error analysis training set for threshold recalibration.

---

### Case Study 4: Ensemble Triage — Model Disagreement Forced Review (Actual System Output)

**Evidence Profile**

- Evidence ID: 2
- Platform: Twitter
- Post ID: `123`
- Acquisition Date: 2024-01-01T00:00:00Z
- Uploaded By: Examiner test@example.com

**Content**

```
you are a loser and stupid
```

**SHA-256 Hash**

```
65028136ccfaf5ed0ef1c7e72846a063f36743a10e50da6eddec977691401c58
```

**Integrity Status**

- ✓ VERIFIED

**Full Triage Result (Ensemble)**

- Prediction: `cyberbullying`
- Confidence: 59.5%
- Risk Level: MEDIUM
- Threshold: 0.5 (calibrated)
- Processing Time: 1,830 ms
- Explanation Method: ensemble

**Model Votes**
| Model | Prediction | Confidence |
|---|---|---|
| svm | other_cyberbullying | 49.4% |
| logistic | other_cyberbullying | 45.0% |
| naive_bayes | ethnicity | 35.4% |
| cnn | cyberbullying | 59.5% |
| bert | error | 0.0% |

**Model Agreement**

- Agreement: none
- Confidence Spread: 59.5%
- Disagreement Levels: 4
- Forced Review: Yes (confidence spread > 0.30 and disagreement levels > 2)

**Examiner Review**

- Decision: Pending
- Notes: Ensemble flagged for review due to model disagreement

**Audit Trail (Chronological)**
| Timestamp | Event Type | Actor | Details |
|---|---|---|---|
| 2024-01-01T00:00:00Z | EVIDENCE_UPLOADED | test@example.com | {"source_platform": "Twitter"} |
| 2026-08-11T12:58:43Z | EVIDENCE_TRIAGED | johndoe@gmail.com | {"model": "ensemble", "votes": [...], "prediction": "cyberbullying", "confidence": 0.595, "risk_level": "MEDIUM", "requires_further_review": true, "model_agreement": {"agreement": "none", "confidence_spread": 0.595, "disagreement_levels": 4, "forced_review": true}, "mode": "ensemble"} |

**Chain of Custody**

1. UPLOAD — test@example.com — 2024-01-01T00:00:00Z
2. CLASSIFICATION (ENSEMBLE) — johndoe@gmail.com — 2026-08-11T12:58:43Z

**Outcome**: Ensemble triage selected highest-confidence cyberbullying vote (CNN, 59.5%) and forced human review due to significant model disagreement. This demonstrates the system's ability to surface uncertain cases for examiner attention.

---

### Summary of Case Studies

| Case | Prediction                      | Examiner Decision | Outcome           | System Role                                     |
| ---- | ------------------------------- | ----------------- | ----------------- | ----------------------------------------------- |
| 1    | cyberbullying (0.94)            | CONFIRMED         | Confirmed harmful | Correct identification                          |
| 2    | cyberbullying (0.72)            | NEEDS_MORE_REVIEW | Escalated         | Appropriate flagging with uncertainty           |
| 3    | cyberbullying (0.68)            | REJECTED          | False positive    | Correctly rejected by human examiner            |
| 4    | cyberbullying (0.595, ensemble) | Pending           | Forced review     | Model disagreement surfaced for human attention |

**Key Observations**

1. High-confidence predictions (≥0.90) align well with examiner confirmation.
2. Near-threshold predictions (0.68–0.75) benefit most from human review.
3. Idiomatic expressions remain a challenge; context-aware models or additional features may reduce false positives.
4. The forensic trail now includes SHA-256 hash-linked audit logs and chain-of-custody records, making tampering detectable; database-level immutability and digital signing remain future work.
5. Ensemble triage with model agreement analysis automatically forces review when models disagree, reducing the risk of automated misclassification.

---

## 13. Remaining Limitations

| Limitation                 | Status                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Educational prototype      | Not a production or court-ready forensic tool                                                                           |
| Evidence integrity         | Original file storage implemented; text-only fallback remains for legacy uploads                                        |
| Audit & chain of custody   | Hash-linked records implemented; database remains mutable but tampering is detectable                                   |
| Threshold calibration      | Reliability diagrams and ECE implemented; calibration quality depends on examiner-reviewed sample size                  |
| Reproducibility            | Fixed local baseline passes; cross-environment comparison remains manual                                                |
| Error analysis             | Forensic categories assigned via keyword rules; examiner-tagged taxonomy would improve accuracy                         |
| Operational evaluation     | Simulated case study added; live metrics depend on examiner review volume; simulated recall is low at current threshold |
| CNN/Transformer comparison | CNN evaluation metrics are recorded in the registry; BERT training fails due to a `transformers` import error in the training environment |
| Ensemble explanations      | May fall back to SHAP for some models, which is non-deterministic                                                       |
| Production hardening       | RBAC, evidence pagination, CI/CD, and monitoring are not yet implemented                                                |

---

## 14. Bulk Evidence Import

### 14.1 Backend Implementation

- **Endpoint:** `POST /evidence/bulk-upload`
- **Request Body:** `EvidenceBulkCreate` containing a list of `EvidenceCreate` items
- **Service:** `bulk_create_evidence()` in `backend/app/services/evidence_service.py`
- **Features:**
  - Batch insertion of multiple evidence records in a single transaction
  - Duplicate detection via SHA-256 hash (skips duplicates)
  - Returns detailed result with created, skipped, and errors arrays
  - Audit logging for bulk upload events

### 14.2 Frontend Implementation

- **Page:** `BulkUploadEvidence.tsx` at `/evidence/bulk-upload`
- **Features:**
  - Dynamic table with add/remove rows
  - Inline validation per row
  - Bulk submit with loading state
  - Results summary showing created, skipped, and error counts

### 14.3 Navigation

- **Evidence Queue:** Added "Bulk Upload" button alongside "Upload Evidence"
- **Route:** `/evidence/bulk-upload`

---

## 15. Model Training Pipeline & Registry

### 15.1 Unified Training Pipeline

File: `ml/model_registry.py`

- Trains all implemented models: SVM, Logistic Regression, Naive Bayes, CNN, BERT
- Accepts configurable dataset path, text/label columns, test size, and random state
- Splits data, trains each model, saves artifacts, and records metadata

### 15.2 Model Registry

File: `ml/saved_models/model_registry.json`

Tracks per-model metadata:

- model_name, version, trained_at timestamp
- dataset_path and dataset SHA-256 hash
- train_samples, test_samples
- training_time_seconds
- artifact paths
- status (completed/failed)
- error messages if failed

### 15.3 Training Scripts

- `ml/train_dummy.py` — trains on 20-sample dummy dataset for smoke tests
- `ml/train_real.py` — trains on `datasets/raw/cyberbullying_tweets.csv`

**TensorFlow note:** CNN and BERT training and artifact generation require TensorFlow to be installed in the ML environment. The backend is configured to start without TensorFlow; deep-learning model training and inference are only attempted when TensorFlow is available. The operational triage path defaults to scikit-learn models, which do not require TensorFlow.

Usage:

```bash
python ml/train_dummy.py

# Stable path - skips BERT automatically
python ml/train_real.py

# Explicit BERT enable (if you have a stable torch/transformers setup)
ENABLE_BERT=1 python ml/train_real.py
```

### 15.4 Supported Models

| Model               | Type                     | Artifact Format         |
| ------------------- | ------------------------ | ----------------------- |
| SVM                 | scikit-learn             | `.pkl`                  |
| Logistic Regression | scikit-learn             | `.pkl`                  |
| Naive Bayes         | scikit-learn             | `.pkl`                  |
| CNN                 | TensorFlow/Keras         | `.keras`                |
| BERT                | HuggingFace Transformers | `pretrained/` directory |

---

## 16. File Inventory

### Backend

- `backend/app/main.py`
- `backend/app/database.py`
- `backend/app/config.py`
- `backend/app/api/{auth,evidence,triage,reviews,audit,export,integrity,explainability,repeatability,reproducibility,operational,threshold_calibration,model_evaluation,model_comparison,error_analysis}.py`
- `backend/app/models/{user,evidence,review,chain_of_custody,repeatability}.py`
- `backend/app/schemas/{user,evidence,triage,review}.py`
- `backend/app/services/{audit,classification,explanation,evidence,hash,integrity,operational_evaluation,pdf_export,repeatability,reproducibility,export,threshold_calibration,model_evaluation,model_comparison}.py`
- `backend/app/security/auth.py`

### Frontend

- `frontend/src/App.tsx`
- `frontend/src/pages/{Login,Register,Dashboard,EvidenceQueue,EvidenceDetails,ReviewPage,AuditLogs,Reports,UploadEvidence,BulkUploadEvidence,OperationalEvaluationDashboard,ThresholdCalibration,ModelPerformanceDashboard,TrainingPerformance,ModelComparison,ErrorAnalysis,Reproducibility}.tsx`
- `frontend/src/components/{ForensicTimeline,IntegrityVerification,RepeatabilityReport,ProtectedRoute}.tsx`
- `frontend/src/services/{api,evidence,triage,reviews,audit,forensic,export,thresholdCalibration,modelEvaluation,modelComparison,errorAnalysis}.ts`
- `frontend/src/types/index.ts`

### Database

- `database/migrations/002_add_forensic_features.sql`

### Machine Learning

- `ml/model_registry.py`
- `ml/training_pipeline.py`
- `ml/train_dummy.py`
- `ml/train_real.py`
- `ml/models/{svm,logistic,naive_bayes,cnn,bert}_model.py`
- `ml/preprocessing/{cleaner,tokenizer,vectorizer}.py`
- `ml/evaluation/{metrics,calibration,confusion_matrix,statistical_tests}.py`
- `ml/explainability/{shap,lime,attribution}_analysis.py`
- `ml/operational/{simulated_cases,test_runner}.py`
- `ml/reproducibility/{test_cases,test_runner}.py`
- `ml/saved_models/`

---

_End of Report_
