# tests/test_detect_changes.py
import json
import tempfile
from pathlib import Path
from scripts.transform.detect_changes import calculate_file_hash


def test_same_content_same_hash():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"key": "DEMO-001", "value": 42}, f)
        path = Path(f.name)

    hash1 = calculate_file_hash(path)
    hash2 = calculate_file_hash(path)
    assert hash1 == hash2
    path.unlink()


def test_different_content_different_hash():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f1:
        json.dump({"key": "DEMO-001"}, f1)
        path1 = Path(f1.name)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f2:
        json.dump({"key": "DEMO-002"}, f2)
        path2 = Path(f2.name)

    assert calculate_file_hash(path1) != calculate_file_hash(path2)
    path1.unlink()
    path2.unlink()


def test_hash_is_64_hex_chars():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"x": 1}, f)
        path = Path(f.name)

    h = calculate_file_hash(path)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
    path.unlink()
