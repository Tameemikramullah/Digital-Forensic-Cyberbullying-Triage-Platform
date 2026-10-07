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

Training uses a stratified 80/20 split of `datasets/raw/cyberbullying_tweets.csv` (9,382 held-out test posts; seed 42).

| Model | Accuracy | Macro-F1 | Weighted-F1 |
|---|---:|---:|---:|
| SVM | 82.79% | 82.52% | 82.76% |
| Logistic Regression | 82.72% | 82.56% | 82.81% |
| Naïve Bayes | 77.37% | 75.66% | 75.89% |
| CNN | 84.40% | 71.80% | 84.40% |
| BERT | 85.40% | 57.40% | 79.50% |

SVM is the primary triage model because it has comparable Macro-F1 to Logistic Regression, faster training, calibrated probabilities, and deterministic feature-contribution explanations. Naïve Bayes is retained as a baseline.

CNN and BERT code exist in the repository, but they are **not validated operational models**. Full-dataset BERT fine-tuning is infeasible on this CPU-only host (~33.8 s/batch, no GPU); it is evaluated on a small stratified subsample only.

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

or

$env:ENABLE_BERT="1"; python ml\train_real.py

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

Importing `transformers` inside a request thread can crash on the way to Triton (`torch._dynamo` → `triton/knobs.py`), taking the worker down with a segmentation fault and no Python traceback. `backend/app/main.py` now imports `torch` and `transformers.models.auto.modeling_auto` at module load, before the event loop starts, so Triton's native initialiser runs on the main thread. If you invoke uvicorn through another entry point, keep that pre-import, or the crash returns only when a BERT request is handled.

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

or

$env:ENABLE_BERT="1"; python ml\train_real.py

python -m json.tool ml/saved_models/model_registry.json
```

Artifacts and metrics are written to `ml/saved_models/`. Restart the backend after training so it loads the current artifacts.

Deep-learning artifacts are best-effort. `train_real.py` trains the three scikit-learn models unconditionally and attempts CNN, recording any failure in `model_registry.json` instead of aborting the run. BERT is skipped entirely unless enabled with `ENABLE_BERT=1` on Ubuntu, or `$env:ENABLE_BERT=1` in PowerShell, which is impractical on a CPU-only host. The backend loads CNN and BERT only when their artifacts exist, so a missing artifact degrades to the scikit-learn models instead of raising.

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

