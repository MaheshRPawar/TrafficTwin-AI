"""
Smoke test suite for TrafficTwin AI (Module M0 Gate)
"""

from pathlib import Path

import fastapi
import numpy
import pandas
import pydantic
import sumolib
import traci
import yaml


def test_core_imports():
    """Verify core simulation and web dependencies can be imported."""
    assert traci is not None
    assert sumolib is not None
    assert fastapi is not None
    assert pydantic is not None
    assert pandas is not None
    assert numpy is not None


def test_params_yaml_exists_and_valid():
    """Verify params.yaml exists and contains required safety and network keys."""
    params_path = Path("backend/config/params.yaml")
    assert params_path.exists(), f"Missing config file at {params_path}"

    with open(params_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "simulation" in config
    assert "network" in config
    assert "safety_firewall" in config
    assert "wave_forecast" in config
    assert "fairness" in config
    assert "emergency_preemption" in config
    assert "reliability" in config

    fw = config["safety_firewall"]
    assert fw["min_green_s"] > 0
    assert fw["max_green_s"] > fw["min_green_s"]
    assert fw["yellow_s"] > 0
    assert fw["all_red_s"] >= 0


def test_directory_structure():
    """Verify canonical MVP directories exist."""
    required_dirs = [
        Path("backend/app"),
        Path("backend/config"),
        Path("sumo/net"),
        Path("sumo/routes"),
        Path("sumo/scenarios"),
        Path("sumo/output"),
        Path("shared/schemas"),
        Path("experiments/results"),
        Path("data/recorded"),
        Path("tests/unit"),
        Path("tests/integration"),
        Path("docs"),
        Path("scripts"),
    ]
    for p in required_dirs:
        assert p.is_dir(), f"Expected directory {p} to exist"
