# System Summary

## Purpose
Post-event forensic triage prototype for prioritising social-media evidence for human examination. Not a real-time moderation service and does not determine criminality, intent, authorship, admissibility, or guilt.

## Core Architecture

### Backend
- **Framework:** FastAPI with SQLAlchemy ORM and SQLite
- **Auth:** JWT-based authentication (`python-jose`, `bcrypt`)
- **Models:** scikit-learn pipelines (`svm`, `logistic`, `naive_bayes`), TensorFlow/Keras CNN, HuggingFace DistilBERT
- **Services:** Classification, model-specific feature explanations, threshold calibration, audit logging, chain-of-custody, evidence management, repeatability/reproducibility tests, operational evaluation, error analysis, model comparison

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

### Dataset and split
- Source CSV: 47,692 parsed rows. Missing values, blank labels, and rows where label equals text each removed 0 rows.
- Cleaned-text/label deduplication removed 785 rows, leaving 46,907 examples.
- Stratified split (seed 42): 37,525 train / 9,382 test.

### 3. ML Triage
Supported models: SVM, Logistic Regression, Naive Bayes, CNN, and DistilBERT. When their training dependencies are available, the registry evaluates each on the same six-class hold-out split and reports a training-set majority-class baseline.

**Primary path:** SVM triage using a `TfidfVectorizer` + `CalibratedClassifierCV(LinearSVC)` pipeline. Calibrated probabilities enable threshold-based risk assignment.

**Secondary path:** Ensemble triage counts one equal plurality vote per successful model over the shared six labels. Per-model confidence is informational only. Ties, more than two distinct predictions, or no valid predictions force human review.

### 4. Threshold Calibration
- Uses app-recorded reviewer decisions marked confirmed/rejected as reference labels; the app does not verify reviewer qualifications.
- Sweeps thresholds (default: 0.5, 0.6, 0.7, 0.8, 0.9).
- Targets 95% recall using the harmful-risk score (sum of probabilities for all five non-benign labels). If the target is met, selects the highest tested threshold that meets it; otherwise selects the lowest threshold among those with the highest observed recall.
- Metrics per threshold: recall, precision, workload reduction, missed-evidence rate, Brier score, ECE, reliability data.
- Reports Wilson 95% intervals for threshold precision and recall; current intervals remain wide because the review sample is tiny.
- The operational threshold defaults to 0.7 if no eligible reviewed evidence exists. In the 2026-11-05 snapshot, only two eligible positive reviews existed; target recall was not met, and the conservative fallback selected 0.50 (1/2 recall; 50% workload reduction).
- Current project-root DB snapshot: 2 app-recorded eligible confirmed/rejected reviews, both confirmed. Reviewer qualifications are not verified. All recall estimates are based on only two positive cases and are not stable estimates or independent practitioner validation.

### 5. Risk Classification
- Single-model `risk_score` is probability mass over the five cyberbullying labels; ensemble `risk_score` is the share of valid model votes for those labels. Ensemble scores are vote fractions, not probabilities.
- `LOW`: risk score < threshold. `MEDIUM`: threshold <= risk score < max(threshold, 0.80). `HIGH`: risk score >= max(threshold, 0.80). Medium and high risk require review.
- Ensemble threshold is 0.50; single-model threshold is selected per model against the 95% recall target from app-recorded reviewer decisions (fallback 0.70 only when no eligible records exist), whose authors' qualifications are not verified.
- Ensemble confidence is the winning label's vote share. Per-model top-class confidence scores are shown but never compared or weighted across models.
- Tied plurality, more than two distinct predictions, or no valid predictions also force review. No valid votes yield `UNKNOWN` risk.

### 6. Explainability
- **SVM / Logistic Regression:** Positive term contributions use TF-IDF multiplied by the target class coefficient; SVM coefficients are averaged across calibration folds.
- **Naive Bayes:** Term contributions use TF-IDF multiplied by the target-versus-strongest-alternative log-probability contrast.
- A deletion assessment on 500 held-out posts measures the probability drop after removing up to three top positive word features.
- **CNN / DistilBERT:** Leave-one-word-out probability-change explanations are returned for the selected neural prediction; deletion tests are reported on 100-post samples.

### 7. Examiner Review
- Examiners inspect triage results, explanations, and evidence details.
- Decisions: `CONFIRMED`, `REJECTED`, `ESCALATED`.
- Decisions feed back into threshold calibration and operational evaluation.

### 8. Audit & Chain of Custody
- Every significant action (upload, triage, review, export) creates an `AuditLog`.
- Per-evidence audit hashes chain the previous hash, event type, actor, event details, and timestamp; verification checks both links and recomputed entry hashes.
- Tampering test changes persisted event details without updating the hash and expects verification failure: `tests/forensic/test_audit_and_custody.py::test_audit_chain_verification_fails_after_persisted_log_entry_is_tampered`.
- The separate `ChainOfCustody` chain hashes the previous entry hash, action, performer, and timestamp.

### 9. Reporting
- JSON and PDF forensic-report exports include predictions, thresholds, explanations, audit summaries, and chain-of-custody verification status.

### 10. Model Training & Registry
- `ml/train_real.py` trains all enabled models and writes artifacts to `ml/saved_models/`.
- A `model_registry.json` records version, timestamp, dataset hash, train/test sample counts, training time, and evaluation metrics (accuracy, macro F1, weighted F1, per-class report).
- CNN and DistilBERT were retrained on the shared six-class split and evaluated on all 9,382 test posts; registry results are version 2.0.

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
- Current SVM run on the fixed 15-case challenge set at selected threshold 0.50: TP=4, FP=3, FN=4, TN=4; recall 4/8 (50.0%, Wilson 95% CI 21.52–78.48%), precision 4/7 (57.14%, CI 25.05–84.18%), accuracy 8/15 (53.33%, CI 30.12–75.19%). Labels are author-assigned from training-data patterns; this is not independent validation or a deployment estimate.
- Challenge labels were author-assigned from training-data annotation patterns, so the simulation is not independent validation. There is no independent two-annotator set, agreement statistic, or verified practitioner decision set. Case-study reviewer identities are placeholders; recorded app decisions do not establish practitioner credentials. Prediction/review disagreements are reported by reviewer account ID; intentional overrides are not separately recorded.
- The case studies preserve former binary outputs and scores for historical illustration, not as results from current six-class models. Two stored `LABEL_1` outputs are legacy unmapped records from ensemble v1.0; they are excluded from current metrics and labeled as legacy in error analysis and forensic report exports. Current DistilBERT uses canonical six-class labels.
- Neural models have held-out six-class metrics, but these results do not establish operational suitability; human review remains mandatory.
- CNN and DistilBERT explanations use leave-one-word-out target-class probability changes. On the seed-42, 100-post sample, attributed-word deletion beat same-size random deletion in 97/98 CNN pairs and 99/99 DistilBERT pairs; mean paired advantages were 62.39 pp and 51.91 pp, respectively.
- RBAC, evidence pagination, CI/CD, and monitoring are not yet implemented.
- The classifier is a prioritisation aid; human review is always required.
