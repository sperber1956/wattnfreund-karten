"""Holt gerenderte OSM-Carto-Kacheln vom lokalen Kachelserver und schreibt sie in eine MBTiles-Datei.

Aufruf: python3 fetch_tiles.py <west> <süd> <ost> <nord> <zmin> <zmax> <ausgabe.mbtiles>
"""
import math
import sqlite3
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SERVER = "http://localhost:8080/tile/{z}/{x}/{y}.png"


def tile(lon, lat, z):
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def fetch(zxy):
    z, x, y = zxy
    for _ in range(5):
        try:
            with urllib.request.urlopen(SERVER.format(z=z, x=x, y=y), timeout=300) as r:
                return z, x, y, r.read()
        except Exception:
            pass
    raise RuntimeError(f"Kachel {z}/{x}/{y} fehlgeschlagen")


def main():
    w, s, e, n = map(float, sys.argv[1:5])
    zmin, zmax = int(sys.argv[5]), int(sys.argv[6])
    out = sys.argv[7]
    jobs = []
    for z in range(zmin, zmax + 1):
        x0, y0 = tile(w, n, z)
        x1, y1 = tile(e, s, z)
        jobs += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    db = sqlite3.connect(out)
    db.executescript("""
        DROP TABLE IF EXISTS metadata; DROP TABLE IF EXISTS tiles;
        CREATE TABLE metadata (name TEXT, value TEXT);
        CREATE TABLE tiles (zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_data BLOB);
        CREATE UNIQUE INDEX tile_index ON tiles (zoom_level, tile_column, tile_row);
    """)
    meta = {"name": "Watt'n Freund Revierkarte", "format": "png", "type": "baselayer",
            "minzoom": str(zmin), "maxzoom": str(zmax), "bounds": f"{w},{s},{e},{n}",
            "attribution": "© OpenStreetMap-Mitwirkende"}
    db.executemany("INSERT INTO metadata VALUES (?, ?)", meta.items())
    done = 0
    with ThreadPoolExecutor(6) as pool:
        for z, x, y, data in pool.map(fetch, jobs):
            # MBTiles zählt Zeilen von unten (TMS)
            db.execute("INSERT INTO tiles VALUES (?, ?, ?, ?)", (z, x, (2 ** z - 1) - y, data))
            done += 1
            if done % 500 == 0:
                print(f"{done}/{len(jobs)}", flush=True)
                db.commit()
    db.commit()
    db.close()
    print(f"fertig: {len(jobs)} Kacheln")


if __name__ == "__main__":
    main()
