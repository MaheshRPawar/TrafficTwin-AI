#!/usr/bin/env python3
"""
TrafficTwin AI - Environment Verification Script (Module M0)

Verifies the local engineering environment:
- Python version (>= 3.11)
- SUMO CLI binary (`sumo`)
- SUMO GUI binary (`sumo-gui`)
- Netconvert binary (`netconvert`)
- TraCI Python library
- Sumolib Python library
- Core dependencies: FastAPI, Pydantic, PyYAML, Pandas, Matplotlib, Pytest, Ruff, Bandit, pip-audit
- Core configuration: backend/config/params.yaml

Outputs 'M0 ENVIRONMENT CHECK PASSED' strictly if all checks pass.
"""

from __future__ import annotations

import shutil
import subprocess  # nosec B404
import sys
from pathlib import Path


def check_python() -> bool:
    print(f"[CHECK] Python version: {sys.version.split()[0]} ({sys.executable})")
    if sys.version_info < (3, 11):
        print(f"[FAIL] Python >= 3.11 required, found {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print("  -> OK")
    return True


def check_binary(name: str, version_arg: str = "--version") -> bool:
    path = shutil.which(name)
    if not path:
        print(f"[FAIL] Binary '{name}' not found on PATH.")
        return False

    try:
        res = subprocess.run([name, version_arg], capture_output=True, text=True, check=True)  # nosec B603
        first_line = res.stdout.strip().split("\n")[0] if res.stdout else "OK"
        print(f"[CHECK] {name}: {path} ({first_line})")
        print("  -> OK")
        return True
    except (subprocess.SubprocessError, OSError) as e:
        print(f"[FAIL] Error running '{name} {version_arg}': {e}")
        return False


def check_python_module(module_name: str, pkg_name: str | None = None) -> bool:
    pkg = pkg_name or module_name
    try:
        mod = __import__(module_name)
        ver = getattr(mod, "__version__", "installed")
        print(f"[CHECK] Python library '{pkg}': {ver}")
        print("  -> OK")
        return True
    except ImportError as e:
        print(f"[FAIL] Cannot import Python module '{module_name}': {e}")
        return False


def check_params_yaml() -> bool:
    params_path = Path("backend/config/params.yaml")
    if not params_path.exists():
        print(f"[FAIL] Config file not found at {params_path}")
        return False

    try:
        import yaml
        with open(params_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict) or "safety_firewall" not in data:
            print("[FAIL] params.yaml does not contain expected keys")
            return False
        print(f"[CHECK] Config params.yaml verified: {params_path}")
        print("  -> OK")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to load params.yaml: {e}")
        return False


def main() -> int:
    print("=" * 60)
    print("TrafficTwin AI — Local Environment Verification (M0)")
    print("=" * 60)

    checks = []

    # 1. Python runtime
    checks.append(("Python >= 3.11", check_python()))

    # 2. SUMO toolchain binaries
    checks.append(("sumo CLI", check_binary("sumo")))
    # On Windows, GUI executable is sumo-gui or sumo-gui.exe
    checks.append(("sumo-gui binary", check_binary("sumo-gui") or check_binary("sumo-gui.exe")))
    checks.append(("netconvert binary", check_binary("netconvert")))

    # 3. TraCI & Sumolib
    checks.append(("traci", check_python_module("traci")))
    checks.append(("sumolib", check_python_module("sumolib")))

    # 4. Core stack libraries
    core_libs = [
        ("pydantic", "pydantic"),
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("yaml", "PyYAML"),
        ("pandas", "pandas"),
        ("matplotlib", "matplotlib"),
        ("pytest", "pytest"),
        ("ruff", "ruff"),
        ("bandit", "bandit"),
        ("pip_audit", "pip-audit"),
    ]
    for mod, pkg in core_libs:
        checks.append((pkg, check_python_module(mod, pkg)))

    # 5. Configuration
    checks.append(("params.yaml", check_params_yaml()))

    print("=" * 60)
    failed = [name for name, passed in checks if not passed]
    if failed:
        print(f"[RESULT] FAILED checks: {', '.join(failed)}")
        return 1

    print("[RESULT] ALL CHECKS PASSED")
    print("M0 ENVIRONMENT CHECK PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
