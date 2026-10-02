# System Summary

## Purpose
Post-event forensic triage prototype for prioritising social-media evidence for human examination. Not a real-time moderation service and does not determine criminality, intent, authorship, admissibility, or guilt.

## Core Architecture

### Backend
- **Framework:** FastAPI with SQLAlchemy ORM and SQLite
- **Auth:** JWT-based authentication (`python-jose`, `bcrypt`)
- **Models:** scikit-learn pipelines (`svm`, `logistic`, `naive_bayes`), TensorFlow/Keras CNN, HuggingFace Transformers BERT
- **Services:** Classification, explanation (SHAP), threshold calibration, audit logging, chain-of-custody, evidence management, repeatability/reproducibility tests, operational evaluation, error analysis, model comparison

### Frontend
- **Framework:** React with TypeScript, Tailwind CSS, React Query, Recharts
- **Routes:** Dashboard, evidence queue, upload/bulk upload, evidence details, review page, audit logs, reports, operational evaluation, threshold calibration, model performance, model comparison, training performance, error analysis, reproducibility

### Data Layer
- **Database:** SQLite via SQLAlchemy
- **Models:** `User`, `Evidence`, `EvidenceMetadata`, `ClassificationResult`, `ExaminerReview`, `AuditLog`, `ChainOfCustody`, `Explanation`, `RepeatabilityTest`, `IntegrityCheck`
- **Migrations:** Alembic

---

## How It Works

### 1. Evidence Intake
- Examiners upload text evidence with source metadata (platform, post ID, acquisition date, author, URL, timestamp).
- Optional original file upload is stored on disk; otherwise, a SHA-256 hash of the text content is computed.
- Duplicate detection prevents re-uploading evidence with an identical content hash.
- Status: `PENDING` -> `TRIAGED` -> `REVIEWED`

### 2. Text Preprocessing
Text is normalised before feature extraction:
- Lowercasing
- URL replacement with `urltoken`
- User-mention replacement with `usertoken`
- Hashtag word retention (e.g., `#StopTheHate` -> `stopthehate`)
- Punctuation normalisation
- Whitespace collapse

### 3. ML Triage
Supported models: SVM, Logistic Regression, Naive Bayes, CNN, BERT.

**Primary path:** SVM triage using a `TfidfVectorizer` + `CalibratedClassifierCV(LinearSVC)` pipeline. Calibrated probabilities enable threshold-based risk assignment.

**Secondary path:** Ensemble triage across multiple models. The highest-confidence cyberbullying vote wins. Model agreement is checked; large confidence spreads or multi-class disagreement force human review.

### 4. Threshold Calibration
- Uses examiner-reviewed evidence with confirmed/rejected decisions as ground truth.
- Sweeps thresholds (default: 0.5, 0.6, 0.7, 0.8, 0.9).
- Metrics per threshold: recall, precision, workload reduction, missed-evidence rate, Brier score, ECE, reliability data.
- The operational threshold defaults to 0.7 if no reviewed evidence exists.

### 5. Risk Classification
- `LOW`: prediction is `not_cyberbullying` or confidence < threshold
- `MEDIUM`: confidence >= 0.5 and < 0.8
- `HIGH`: confidence >= 0.8
- `requires_further_review` is true when prediction is cyberbullying above threshold, or when ensemble agreement is poor.

### 6. Explainability
- **SVM / Logistic / Naive Bayes:** SHAP-based feature contributions via `shap.Explainer` on the pipeline's predict_proba.
- **CNN / BERT:** Native model predictions; explainability may be unavailable or fall back to non-deterministic methods.
- Top features (term + impact) are stored and displayed.

### 7. Examiner Review
- Examiners inspect triage results, explanations, and evidence details.
- Decisions: `CONFIRMED`, `REJECTED`, `ESCALATED`.
- Decisions feed back into threshold calibration and operational evaluation.

### 8. Audit & Chain of Custody
- Every significant action (upload, triage, review, export) creates an `AuditLog`.
- A `ChainOfCustody` hash chain is maintained per evidence item. Each entry hashes the previous entry's hash, action, performer, and timestamp.
- Verification endpoints validate chain integrity by recomputing hashes.

### 9. Reporting
- JSON and PDF forensic-report exports include predictions, thresholds, explanations, audit summaries, and chain-of-custody verification status.

### 10. Model Training & Registry
- `ml/train_real.py` trains all enabled models and writes artifacts to `ml/saved_models/`.
- A `model_registry.json` records version, timestamp, dataset hash, train/test sample counts, training time, and evaluation metrics (accuracy, macro F1, weighted F1, per-class report).
- CNN evaluation metrics are recorded; BERT training currently fails due to a `transformers` import error in the training environment.

---

## Key Endpoints
| Prefix | Purpose |
|--------|---------|
| `/auth` | Register, login, token refresh |
| `/evidence` | Upload, bulk upload, list, retrieve, delete evidence |
| `/triage` | Single-model and ensemble triage |
| `/reviews` | Examiner decisions |
| `/audit` | Audit log retrieval |
| `/export` | JSON/PDF report generation |
| `/integrity` | SHA-256 and chain-of-custody verification |
| `/explainability` | Explanation retrieval |
| `/repeatability` | Repeatability test execution |
| `/reproducibility` | Fixed reproducibility baseline |
| `/operational` | Simulated operational evaluation |
| `/threshold-calibration` | Threshold sweep and calibration results |
| `/model-evaluation` | Held-out evaluation metrics |
| `/error-analysis` | Error analysis by category |
| `/model-comparison` | Model registry and comparison |

---

## Limitations
- Educational prototype, not production or court-ready.
- Hash chains detect later record changes but do not provide digital signatures, WORM storage, or true append-only persistence.
- Reproducibility baseline passes locally; cross-environment comparison remains manual.
- The fixed 15-case operational simulation has low recall at the current 0.70 threshold.
- BERT training currently fails due to a `transformers` import error in the training environment.
- Ensemble explanations may fall back to SHAP for some models, which can be non-deterministic.
- RBAC, evidence pagination, CI/CD, and monitoring are not yet implemented.
- The classifier is a prioritisation aid; human review is always required.
