"""Plausibilitätsprüfung vor dem Veröffentlichen – bricht mit Fehler ab, wenn etwas fehlt.

Aufruf: python3 check.py <revierkarte.mbtiles> <revierkarte.pmtiles> <seezeichen.geojson> [<tiefenlinien.pmtiles>]
"""
import json
import os
import sqlite3
import sys

mbtiles, pmtiles, seamarks = sys.argv[1:4]
depths = sys.argv[4] if len(sys.argv) > 4 else None
errors = []

db = sqlite3.connect(mbtiles)
counts = dict(db.execute("SELECT zoom_level, COUNT(*) FROM tiles GROUP BY zoom_level"))
total = sum(counts.values())
# Erwartet: Zoom 8–15 vollständig, zusammen gut 36 000 Kacheln
if sorted(counts) != list(range(8, 16)):
    errors.append(f"Zoomstufen unvollständig: {sorted(counts)}")
if total < 35000:
    errors.append(f"nur {total} Kacheln")
# leere oder fehlerhafte Kacheln (Renderfehler liefern winzige Antworten)
tiny = db.execute("SELECT COUNT(*) FROM tiles WHERE length(tile_data) < 100").fetchone()[0]
if tiny > total * 0.02:
    errors.append(f"{tiny} verdächtig kleine Kacheln")

size = os.path.getsize(pmtiles)
if size < 100_000_000:
    errors.append(f"PMTiles nur {size // 1_000_000} MB")

n = len(json.load(open(seamarks, encoding="utf-8"))["features"])
if n < 2000:
    errors.append(f"nur {n} Seezeichen")

if depths:
    dsize = os.path.getsize(depths)
    if dsize < 1_000_000:
        errors.append(f"Tiefenlinien nur {dsize // 1000} kB")
    print(f"Tiefenlinien {dsize // 1_000_000} MB")

print(f"{total} Kacheln, {size // 1_000_000} MB, {n} Seezeichen")
if errors:
    print("FEHLER: " + "; ".join(errors))
    sys.exit(1)
print("Prüfung bestanden")
