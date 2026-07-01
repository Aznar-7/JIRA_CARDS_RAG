# tests/test_detect_changes.py
import json
from pathlib import Path
from scripts.transform.detect_changes import calculate_file_hash


def test_same_content_same_hash(tmp_path):
    p = tmp_path / "test.json"
    p.write_text(json.dumps({"key": "DEMO-001", "value": 42}))
    assert calculate_file_hash(p) == calculate_file_hash(p)


def test_different_content_different_hash(tmp_path):
    p1 = tmp_path / "a.json"
    p2 = tmp_path / "b.json"
    p1.write_text(json.dumps({"key": "DEMO-001"}))
    p2.write_text(json.dumps({"key": "DEMO-002"}))
    assert calculate_file_hash(p1) != calculate_file_hash(p2)


def test_hash_is_64_hex_chars(tmp_path):
    p = tmp_path / "test.json"
    p.write_text(json.dumps({"x": 1}))
    h = calculate_file_hash(p)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)
