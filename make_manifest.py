"""Manifest der Revierkarte: Version (Stand der OSM-Daten), Gebiet, Dateien mit Größe und SHA-256.

Aufruf: python3 make_manifest.py <version> <datei> [<datei> …] > revierkarte.json
"""
import hashlib
import json
import os
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


version, files = sys.argv[1], sys.argv[2:]
print(json.dumps({
    "version": version,
    "area": "Ostfriesisches Wattenmeer, Ems bis Jade, Helgoland",
    "maxZoom": 15,
    "files": [{"name": os.path.basename(p), "size": os.path.getsize(p), "sha256": sha256(p)} for p in files],
}, indent=2, ensure_ascii=False))
