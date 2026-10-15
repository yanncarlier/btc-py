#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

def test():
    cmd = [sys.executable, str(Path("derive/m-0-i.py"))] + ["-n", "2", "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"
    with open(Path(__file__).parent / "fixtures" / Path(__file__).with_suffix(".json").name) as f:
        golden = json.load(f)
    actual = json.loads(result.stdout)
    assert actual == golden, f"Golden file mismatch: {Path(__file__).with_suffix('.json')}"
    print("PASS: m-0-i (matches golden file)")

if __name__ == "__main__":
    test()
