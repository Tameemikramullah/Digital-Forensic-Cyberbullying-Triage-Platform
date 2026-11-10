# Digital Forensic Cyberbullying Triage Platform

An educational **post-event forensic triage prototype** for prioritising social-media evidence for human examination. It is not a real-time moderation service and does not determine criminality, intent, authorship, admissibility, or guilt.

## What the prototype demonstrates

- Evidence intake with source metadata and optional original-file preservation.
- SHA-256 integrity verification of the uploaded original file, or stored text when no file was supplied.
- Hash-linked audit logs and chain-of-custody records, with verification endpoints.
- Human examiner decisions: confirm, reject, or escalate.
- Threshold-based SVM triage with deterministic coefficient-based feature contributions.
- Held-out evaluation of SVM, Logistic Regression, and Naïve Bayes.
- Calibration outputs: threshold table, workload reduction, missed-evidence rate, Brier score, ECE, and reliability data.
- Repeatability tests, a fixed reproducibility baseline, structured error analysis, and simulated operational cases.
- JSON/PDF forensic-report exports.

## Evaluated models

The source CSV has 47,692 parsed rows. Preparation removes missing values, blank labels, and rows where the label equals the text (0 rows for each in this dataset), normalizes text, then removes 785 duplicates keyed by cleaned text and label. The final dataset has 46,907 rows. A stratified 80/20 split (seed 42) uses 37,525 training and 9,382 held-out test posts.

| Model                       | Accuracy | Macro-F1 | Weighted-F1 |
| --------------------------- | -------: | -------: | ----------: |
| Six-class majority baseline |   16.99% |    4.84% |       4.93% |
| SVM                         |   82.79% |   82.52% |      82.76% |
| Logistic Regression         |   82.73% |   82.57% |      82.81% |
| Naïve Bayes                 |   77.37% |   75.66% |      75.89% |
| CNN                         |   82.53% |   82.33% |      82.55% |
| DistilBERT                  |   85.66% |   85.44% |      85.61% |

SVM is the primary triage model because it has comparable Macro-F1 to Logistic Regression, faster training, calibrated probabilities, and deterministic feature-contribution explanations. Naïve Bayes is retained as a classical model benchmark.

### Ensemble and risk definitions

The ensemble requires the shared six labels (`age`, `ethnicity`, `gender`, `not_cyberbullying`, `other_cyberbullying`, `religion`) and gives each successful, distinct model one equal vote. It selects the plurality label; per-model top-class confidence values are shown for context but never compared or weighted. Ensemble `confidence` is the winning-label vote share. Ensemble `risk_score` is the fraction of successful votes assigned to any label except `not_cyberbullying`; it is not a probability. Single-model `risk_score` instead sums that model's probabilities for the five cyberbullying labels.

For risk threshold `T`, `LOW` means `risk_score < T`, `MEDIUM` means `T <= risk_score < max(T, 0.80)`, and `HIGH` means `risk_score >= max(T, 0.80)`. Ensemble `T` is 0.50. Single-model `T` is selected per model from app-recorded reviewer decisions against the 95% recall target, falling back to 0.70 only when no eligible reviewed data exists; reviewer qualifications are not verified. Medium and high scores require review. Ensemble ties, more than two distinct predictions, or no valid predictions also require review; no valid votes produce `UNKNOWN` risk. A tied plurality is returned deterministically by alphabetical label order, with review forced.

The threshold-calibration screen reports Wilson 95% confidence intervals for precision and recall. These intervals remain wide with the current two reviewed cases.

All five models were trained and evaluated on the same stratified six-class split (37,525 training posts; 9,382 test posts; seed 42). DistilBERT was fine-tuned for one epoch and evaluated on the full test set. These held-out metrics do not establish operational suitability; human review remains required. Per-class F1 scores are recorded in `report.md` and the model registry.

Single-model thresholds are selected against a 95% recall target using the harmful-risk score, defined as the sum of probabilities for the five non-benign classes. If a tested threshold meets the target, the highest such threshold is selected to reduce flagged workload. If none meet it, the lowest threshold among those with the highest observed recall is selected. In the 2026-11-05 project-root database snapshot, only two eligible review records were available and both were positive; no tested threshold reached 95% recall. The fallback threshold was 0.50, with observed recall 1/2 (50%) and workload reduction 1/2 (50%). This tiny, single-class sample cannot support a dependable recall target or an independent practitioner-validation claim.

## Setup

Prerequisites: **Python 3.12**, **Node.js 20+** (developed against Python 3.12.3 and Node 24.14), and a C toolchain for the compiled dependencies in `backend/requirements.txt` (notably `shap`, `scikit-learn`, `cryptography`, and the CPU builds of `torch`/`tensorflow`). Expect roughly 4–6 GB of downloads and several minutes, because TensorFlow, PyTorch, and Transformers are unpinned.

### Ubuntu

```bash
# 1. System packages (Python 3.12 + headers, build tools, Node.js)
sudo apt update
sudo apt install -y python3 python3-venv python3-dev build-essential git curl
sudo apt install -y nodejs npm        # or use nvm / NodeSource if the distro node is older than 20

# 2. Get the code
cd ~/Projects
git clone <repository-url> forensic-cyberbullying-triage
cd forensic-cyberbullying-triage

# 3. Python environment
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# 4. Environment file — see the .env block below, then create it at the project root
printf 'DATABASE_URL=sqlite:///./forensic_triage.db\nALGORITHM=HS256\nACCESS_TOKEN_EXPIRE_MINUTES=60\nUPLOAD_DIR=./uploads\nMAX_UPLOAD_SIZE=10485760\nSECRET_KEY=%s\n' "$(python -c 'import secrets; print(secrets.token_urlsafe(48))')" > .env

# 5. Train the models — required on a fresh clone, see "Train the evaluated models"
PYTHONPATH=. python ml/train_real.py
PYTHONPATH=. ENABLE_BERT=1 python ml/train_real.py

# 6. Backend, from the project root
PYTHONPATH=. uvicorn backend.app.main:app --reload

# 7. Frontend, in a second terminal
cd frontend
npm install
npm run dev
```

Model artifacts are git-ignored, so step 5 is not optional on a fresh clone; the backend starts without them but triage returns `FileNotFoundError` until they exist.

### Windows (PowerShell)

```powershell
# 1. Check prerequisites
python --version      # must be 3.12
node --version        # must be 20+

# 2. Get the code
cd $HOME\Projects
git clone <repository-url> forensic-cyberbullying-triage
cd forensic-cyberbullying-triage

# 3. Python environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt

# 4. Environment file — see the .env block below, then create it at the project root
$secret = python -c "import secrets; print(secrets.token_urlsafe(48))"
@"
DATABASE_URL=sqlite:///./forensic_triage.db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
SECRET_KEY=$secret
"@ | Set-Content -Encoding utf8 .env

# 5. Train the models — required on a fresh clone, see "Train the evaluated models"
$env:PYTHONPATH = "."
python ml\train_real.py

# 6. Backend, from the project root
$env:PYTHONPATH = "."
python -m uvicorn backend.app.main:app --reload

# 7. Frontend, in a second PowerShell window
cd frontend
npm install
npm run dev
```

Model artifacts are git-ignored, so step 5 is not optional on a fresh clone; the backend starts without them but triage returns `FileNotFoundError` until they exist.

If PowerShell blocks activation, allow local scripts for the current user and retry:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### `.env`

`.env` is git-ignored and there is no `.env.example` in the repository, so create it yourself at the project root before the first run. It is read relative to the directory you launch uvicorn from, which is why the root is the right place.

```env
DATABASE_URL=sqlite:///./forensic_triage.db
SECRET_KEY=change-me-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE=10485760
```

Generate a real `SECRET_KEY` rather than reusing the placeholder; existing tokens will not verify after it changes.

### Database

Tables are created automatically on backend startup (`Base.metadata.create_all`), so a fresh checkout needs no manual step. Migrations are only for databases created by earlier versions:

```bash
sqlite3 forensic_triage.db < database/migrations/003_evidence_files_and_hash_chains.sql
```

For PostgreSQL or Supabase, run the scripts in `database/migrations/` in order (`001`, then `002_add_explanations_and_integrity.sql`, then `003`) and set `DATABASE_URL` accordingly. Note that `002_add_forensic_features.sql` is an earlier, superseded variant of `002_add_explanations_and_integrity.sql`; do not run both.

### First run

Register an examiner or admin account through the UI at `http://localhost:3000/register`, or via the API:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"examiner@example.com","password":"your-password","role":"INVESTIGATOR"}'
```

Backend runs on `http://localhost:8000` (`GET /health` for a readiness check); the Vite dev server runs on `http://localhost:3000` and proxies `/auth`, `/evidence`, `/triage`, and the other API prefixes to port 8000, per `frontend/vite.config.ts`. CORS allows only the two localhost:3000 origins, so call the backend through the Vite proxy rather than directly from a browser page on another host.

### Known issue on some hosts

Importing `transformers` inside a request thread can crash on the way to Triton (`torch._dynamo` → `triton/knobs.py`), taking the worker down with a segmentation fault and no Python traceback. `backend/app/main.py` now imports `torch` and `transformers.models.auto.modeling_auto` at module load, before the event loop starts, so Triton's native initialiser runs on the main thread. If you invoke uvicorn through another entry point, keep that pre-import, or the crash returns only when a DistilBERT request is handled.

## Train the evaluated models

`ml/saved_models/` is git-ignored, so a fresh clone contains no model artifacts and triage cannot run until you train them.

```bash
# Ubuntu
source .venv/bin/activate
PYTHONPATH=. python ml/train_real.py

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "."
python ml\train_real.py

python -m json.tool ml/saved_models/model_registry.json
```

Artifacts and metrics are written to `ml/saved_models/`. Restart the backend after training so it loads the current artifacts.

Deep-learning artifacts are best-effort. `train_real.py` trains the three scikit-learn models and CNN, recording failures in `model_registry.json` instead of aborting the run. DistilBERT is skipped unless enabled with `ENABLE_BERT=1` on Ubuntu, or `$env:ENABLE_BERT=1` in PowerShell. The current registry contains completed six-class CNN and DistilBERT runs. The backend loads these models only when their artifacts exist.

## Verify the prototype

```bash
# Ubuntu
source .venv/bin/activate
python -m pytest tests/ -q

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m pytest tests\ -q

# Fixed five-case reproducibility baseline
# Ubuntu
PYTHONPATH=. python -c "from ml.reproducibility.test_runner import run_reproducibility_test; print(run_reproducibility_test('svm'))"
# Windows PowerShell
$env:PYTHONPATH = "."; python -c "from ml.reproducibility.test_runner import run_reproducibility_test; print(run_reproducibility_test('svm'))"
```

`tests/run_tests.sh` runs the same suite and forwards any extra arguments to pytest:

```bash
./tests/run_tests.sh            # equivalent to python -m pytest -v
./tests/run_tests.sh -k ensemble -x
```

It uses the project-root `.venv` and resolves the project root itself, so it can be invoked from any directory. The root still matters for correctness: `pytest.ini` sets `pythonpath = backend`, and relative paths such as `.env`, `sqlite:///./forensic_triage.db`, and `UPLOAD_DIR` must resolve against the project root. Invoke pytest directly on Windows, where this bash script does not run.

## Intended workflow

1. Upload text evidence and, where available, the original evidence file.
2. Verify the stored SHA-256 hash before analysis.
3. Run single-model triage; use ensemble output only as a secondary disagreement signal.
4. Inspect prediction, calibrated threshold, confidence, and feature contributions.
5. The examiner confirms, rejects, or escalates the item.
6. Verify/export the audit and custody records.

## Audit hash-chain validation

Each evidence item's first audit record starts with an empty previous hash. Every following record stores the prior record's SHA-256 entry hash. An entry hash covers that previous hash, event type, actor, event details, and canonical timestamp. Verification recomputes each hash and checks the chain links.

The tampering test creates a two-entry chain, verifies it, changes the first stored event-details value without updating its hash, and verifies that integrity checking fails with an entry-hash mismatch:

```bash
.venv/bin/pytest -q tests/forensic/test_audit_and_custody.py::test_audit_chain_verification_fails_after_persisted_log_entry_is_tampered
```

## Limitations

- This is an educational prototype, not a production or court-ready forensic tool.
- Hash chains detect later record changes but do not provide digital signatures, WORM storage, or true append-only persistence.
- Reproducibility baseline passes locally; independent reproducibility still requires manual comparison in a second environment.
- Current SVM run on the fixed 15-case challenge set at selected threshold 0.50: TP=4, FP=3, FN=4, TN=4; recall 50.0% (95% Wilson CI 21.52–78.48%), precision 57.14% (CI 25.05–84.18%), and accuracy 53.33% (CI 30.12–75.19%). Labels follow training-data patterns, so this is not independent validation or a deployment estimate.
- The challenge-set labels were assigned by the project author from training-data annotation patterns. They were not independently adjudicated, and are not real practitioner decisions. No independent two-annotator set or agreement statistic is available. Reviewer accounts in example case studies are placeholders; database review records do not establish examiner credentials. The application reports prediction/review disagreement by reviewer account ID, but does not record intentional overrides.
- The case studies in §12 preserve historical binary outputs and scores; they are not results from the retrained six-class models. Historical `LABEL_1` values stored under ensemble v1.0 are legacy unmapped records, excluded from current metrics and marked as such in error analysis and report exports. New DistilBERT outputs use the canonical six-class mapping.
- DistilBERT (HuggingFace Transformers; internal key `bert`) has a completed one-epoch six-class run, evaluated on the full 9,382-post test set. This is held-out analytical evaluation, not operational validation.
- Ensemble risk is a vote share and must not be interpreted as a calibrated probability; per-model scores have different calibration properties.
- Advanced permissions (RBAC), evidence pagination, CI/CD, and monitoring are not yet implemented.
- The classifier is a prioritisation aid; human review is always required.
