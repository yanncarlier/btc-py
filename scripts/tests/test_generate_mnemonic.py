#!/usr/bin/env python3
import json, subprocess, sys
from pathlib import Path

def test():
    cmd = [sys.executable, str(Path("derive/generate_mnemonic.py"))] + ['-s', '128']
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"
    actual = json.loads(result.stdout)
    assert "bip39_mnemonic" in actual
    assert len(actual["bip39_mnemonic"].split()) == 12
    assert "bip39_seed" in actual
    assert "bip32_root_key" in actual
    print("PASS: generate_mnemonic (random output, verifies structure)")

if __name__ == "__main__":
    test()
