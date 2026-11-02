"""CLI показывает справку и запускает покерный пример."""
import json
import subprocess
import sys
from pathlib import Path


def test_core_cli_help():
    result = subprocess.run([sys.executable, "-m", "core", "--help"], capture_output=True)
    assert result.returncode == 0, result.stderr
    assert b"input" in result.stdout
    assert not result.stderr



def test_example_input_runs_through_cli():
    result = subprocess.run(
        [sys.executable, "-m", "core", "example_input.json"], capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    params = json.loads(Path("example_input.json").read_text(encoding="utf-8"))
    assert output["simulations"] == params["simulations"]
    assert output["recommendation"] == "CHECK"

