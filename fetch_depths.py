"""Tiefenlinien des BSH (Kartendienst „Hydrographic Data for Nautical Products“) als Rasterkacheln (MBTiles).

Zoom bis 11 aus den Küstenkarten, ab 12 aus den Ansteuerungskarten (mit 2-m-Linie). Über Zoom 14
vergrößert die App selbst. Nutzungsbedingungen des BSH: GeoNutzV, nicht zu Navigationszwecken.

Aufruf: python3 fetch_depths.py <west> <süd> <ost> <nord> <zmin> <zmax> <ausgabe.mbtiles>
"""
import math
import sqlite3
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

WMS = ("https://gdi.bsh.de/en/mapservice/Hydrographic-Data-for-Nautical-Products-WMS?SERVICE=WMS&VERSION=1.3.0"
       "&REQUEST=GetMap&STYLES=&CRS=EPSG:3857&WIDTH=256&HEIGHT=256&FORMAT=image/png&TRANSPARENT=true"
       "&LAYERS={layer}&BBOX={bbox}")
R = 20037508.342789244


def tile(lon, lat, z):
    n = 2 ** z
    return int((lon + 180) / 360 * n), int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)


def bbox(z, x, y):
    size = 2 * R / 2 ** z
    return f"{-R + x * size},{R - (y + 1) * size},{-R + (x + 1) * size},{R - y * size}"


def fetch(zxy):
    z, x, y = zxy
    layer = "Coastel_Depths_Depth_Contours" if z <= 11 else "Approach_Depths_Depth_Contours"
    url = WMS.format(layer=layer, bbox=bbox(z, x, y))
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WattnFreund-Revierkarte/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                if r.headers.get_content_type() == "image/png":
                    return z, x, y, data
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Kachel {z}/{x}/{y} fehlgeschlagen")


def main():
    w, s, e, n = map(float, sys.argv[1:5])
    zmin, zmax, out = int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
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
    db.executemany("INSERT INTO metadata VALUES (?, ?)", {
        "name": "Tiefenlinien", "format": "png", "type": "overlay", "minzoom": str(zmin), "maxzoom": str(zmax),
        "bounds": f"{w},{s},{e},{n}", "attribution": "Tiefen: © BSH"}.items())
    # Referenz für eine leere Kachel: ein Punkt im Binnenland, wo der BSH keine Daten hat
    empty = fetch((14, *tile(7.5, 53.3, 14)))[3]
    done = kept = 0
    # schonend: wenige gleichzeitige Abrufe beim BSH
    with ThreadPoolExecutor(4) as pool:
        for z, x, y, data in pool.map(fetch, jobs):
            done += 1
            # leere (ganz durchsichtige) Kacheln weglassen – die App zeigt dort einfach nichts
            if data != empty:
                db.execute("INSERT INTO tiles VALUES (?, ?, ?, ?)", (z, x, (2 ** z - 1) - y, data))
                kept += 1
            if done % 500 == 0:
                print(f"{done}/{len(jobs)}", flush=True)
                db.commit()
    db.commit()
    db.close()
    print(f"fertig: {len(jobs)} abgerufen, {kept} mit Inhalt")


if __name__ == "__main__":
    main()
