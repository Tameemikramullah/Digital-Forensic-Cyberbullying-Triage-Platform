import platform
import sys
import sklearn
import sqlalchemy
import fastapi
from typing import Dict, Any, List


def _parse_requirements(path: str) -> list:
    reqs = []
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    reqs.append(line)
    except Exception:
        pass
    return reqs


def get_reproducibility_report() -> Dict[str, Any]:
    backend_reqs = _parse_requirements("./backend/requirements.txt")

    try:
        import json
        with open("./frontend/package.json") as f:
            pkg = json.load(f)
        frontend_deps = pkg.get("dependencies", {})
    except Exception:
        frontend_deps = {}

    return {
        "python_version": sys.version,
        "os": f"{platform.system()} {platform.release()}",
        "python_implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "backend_dependencies": backend_reqs,
        "frontend_dependencies": frontend_deps,
        "framework_versions": {
            "fastapi": fastapi.__version__,
            "sqlalchemy": sqlalchemy.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }


def run_reproducibility_test(model_name: str = "svm") -> Dict[str, Any]:
    from ml.reproducibility.test_runner import run_reproducibility_test as _run
    return _run(model_name=model_name)
