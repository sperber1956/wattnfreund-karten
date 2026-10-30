#!/usr/bin/env bash
# Baut die Revierkarte für Watt'n Freund: OSM-Carto-Kacheln (PMTiles) und Seezeichen (GeoJSON).
# Voraussetzungen: docker (z. B. colima), osmium-tool, pmtiles, python3
set -euo pipefail
cd "$(dirname "$0")"
BBOX=6.55,53.25,8.45,54.25          # Borkum/Dollart bis Jade, Helgoland
W=6.55; S=53.25; E=8.45; N=54.25
ZMIN=8; ZMAX=15
IMAGE=overv/openstreetmap-tile-server:2.3.0
VERSION=$(date +%Y-%m-%d)
mkdir -p work out

echo "== OSM-Daten laden"
for r in germany/niedersachsen germany/schleswig-holstein germany/bremen netherlands/groningen; do
  curl -sfL -o "work/$(basename $r).osm.pbf" "https://download.geofabrik.de/europe/$r-latest.osm.pbf"
  osmium extract -b $BBOX "work/$(basename $r).osm.pbf" -o "work/cut-$(basename $r).osm.pbf" --overwrite
done
osmium merge work/cut-*.osm.pbf -o work/revier.osm.pbf --overwrite

echo "== Seezeichen"
osmium tags-filter work/revier.osm.pbf n/seamark:type -o work/seamarks.osm.pbf --overwrite
osmium export work/seamarks.osm.pbf -f geojsonseq -o work/seamarks.geojsonseq --overwrite
python3 build_seamarks.py work/seamarks.geojsonseq out/seezeichen.geojson

echo "== Import in den Kachelserver"
docker rm -f wf-tiles >/dev/null 2>&1 || true
docker volume rm wf-osm >/dev/null 2>&1 || true
docker volume create wf-osm >/dev/null
docker run --rm -e THREADS=6 -v "$PWD/work/revier.osm.pbf:/data/region.osm.pbf" -v wf-osm:/data/database/ $IMAGE import

echo "== Kacheln rendern (Zoom $ZMIN–$ZMAX)"
docker run -d --name wf-tiles -p 8080:80 -e THREADS=6 -v wf-osm:/data/database/ $IMAGE run >/dev/null
until curl -sf -o /dev/null --max-time 120 http://localhost:8080/tile/8/132/82.png; do sleep 3; done
python3 fetch_tiles.py $W $S $E $N $ZMIN $ZMAX work/revierkarte.mbtiles
docker rm -f wf-tiles >/dev/null
pmtiles convert work/revierkarte.mbtiles out/revierkarte.pmtiles

echo "== Manifest"
python3 make_manifest.py "$VERSION" out/revierkarte.pmtiles out/seezeichen.geojson > out/revierkarte.json
cat out/revierkarte.json
echo "Fertig. Hochladen: gh release upload revierkarte out/* --clobber"
