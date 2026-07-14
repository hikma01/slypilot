from __future__ import annotations
import pytest
from pathlib import Path
from slypilot.tools.filesystem.path_detector import detect_paths

def test_detect_paths_standard():
    raw = "analyse /Users/test/MonProjet"
    detected = detect_paths(raw)
    assert len(detected) == 1
    assert detected[0].raw_path == "/Users/test/MonProjet"

def test_detect_paths_with_spaces_and_quotes():
    raw = 'analyse "/Users/test/Mon Projet"'
    detected = detect_paths(raw)
    assert len(detected) == 1
    assert detected[0].raw_path == "/Users/test/Mon Projet"

def test_detect_paths_with_spaces_escaped():
    # En Python, \ devant un espace dans une chaîne brute ou normale doit être géré
    raw = "analyse /Users/test/Mon\\ Projet"
    detected = detect_paths(raw)
    assert len(detected) == 1
    # On s'attend à ce que le \ soit interprété ou conservé pour normalisation
    assert "Mon Projet" in detected[0].normalized_path

def test_detect_paths_multiple():
    raw = "compare /tmp/a et /tmp/b"
    detected = detect_paths(raw)
    assert len(detected) == 2
    assert detected[0].raw_path == "/tmp/a"
    assert detected[1].raw_path == "/tmp/b"

def test_detect_paths_with_single_quotes():
    raw = "regarde '/Users/test/Projet A'"
    detected = detect_paths(raw)
    assert len(detected) == 1
    assert detected[0].raw_path == "/Users/test/Projet A"
