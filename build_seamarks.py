"""Seezeichen aus OSM (osmium export … -f geojsonseq) in eine schlanke GeoJSON-Datei für die App.

Aufruf: python3 build_seamarks.py seamarks.geojsonseq seezeichen.geojson

Eigenschaften je Punkt: k = Symbol (siehe App: SeamarkLayer), n = Name
Betonnung nach IALA A (Europa): Backbord rot, Steuerbord grün.
"""
import json
import sys


def icon(t):
    ty = t.get("seamark:type", "")
    def g(key):
        return (t.get(f"seamark:{ty}:{key}") or "").lower()
    if ty in ("buoy_lateral", "beacon_lateral"):
        cat, col = g("category"), g("colour")
        red = cat == "port" or (cat not in ("starboard",) and col.startswith("red"))
        if cat in ("preferred_channel_port", "preferred_channel_starboard"):
            red = cat == "preferred_channel_starboard"
        side = "red" if red else "green"
        return f"{side}_beacon" if ty.startswith("beacon") else ("red_can" if red else "green_cone")
    if ty in ("buoy_cardinal", "beacon_cardinal"):
        cat = g("category")
        return "card_" + {"north": "n", "east": "e", "south": "s", "west": "w"}.get(cat, "n")
    if ty in ("buoy_safe_water", "beacon_safe_water"):
        return "safe"
    if ty in ("buoy_isolated_danger", "beacon_isolated_danger"):
        return "danger"
    if ty in ("buoy_special_purpose", "beacon_special_purpose"):
        return "special"
    if ty in ("light_major", "light_minor", "light_vessel"):
        return "light"
    if ty == "wreck":
        return "wreck"
    return None


def main():
    src, out = sys.argv[1], sys.argv[2]
    feats = []
    for line in open(src, encoding="utf-8"):
        line = line.strip().lstrip("\x1e")
        if not line:
            continue
        f = json.loads(line)
        if f["geometry"]["type"] != "Point":
            continue
        t = f["properties"]
        k = icon(t)
        if not k:
            continue
        lon, lat = f["geometry"]["coordinates"]
        props = {"k": k}
        name = t.get("seamark:name") or t.get("name")
        if name:
            props["n"] = name
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]}})
    json.dump({"type": "FeatureCollection", "features": feats}, open(out, "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"{len(feats)} Seezeichen")


if __name__ == "__main__":
    main()
