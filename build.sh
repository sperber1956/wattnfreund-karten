#!/usr/bin/env bash
# Baut die Revierkarte für Watt'n Freund: OSM-Carto-Kacheln (PMTiles) und Seezeichen (GeoJSON).
# Voraussetzungen: docker, osmium-tool, pmtiles, python3
# Ergebnis in out/: revierkarte-<Datum>.pmtiles, seezeichen-<Datum>.geojson, tiefenlinien-<Datum>.pmtiles, revierkarte.json
set -euo pipefail
cd "$(dirname "$0")"
BBOX=6.55,53.25,8.45,54.25          # Borkum/Dollart bis Jade, Helgoland
W=6.55; S=53.25; E=8.45; N=54.25
ZMIN=8; ZMAX=15
THREADS=${THREADS:-6}
IMAGE=overv/openstreetmap-tile-server:2.3.0
VERSION=${VERSION:-$(date -u +%Y-%m-%dT%H%M)}
TILES=revierkarte-$VERSION.pmtiles
SEAMARKS=seezeichen-$VERSION.geojson
DEPTHS=tiefenlinien-$VERSION.pmtiles
rm -rf out && mkdir -p work out

echo "== OSM-Daten laden"
for r in germany/niedersachsen germany/schleswig-holstein germany/bremen netherlands/groningen; do
  curl -sfL -o "work/$(basename $r).osm.pbf" "https://download.geofabrik.de/europe/$r-latest.osm.pbf"
  osmium extract -b $BBOX "work/$(basename $r).osm.pbf" -o "work/cut-$(basename $r).osm.pbf" --overwrite
  rm "work/$(basename $r).osm.pbf"
done
osmium merge work/cut-*.osm.pbf -o work/revier.osm.pbf --overwrite

echo "== Seezeichen"
osmium tags-filter work/revier.osm.pbf n/seamark:type -o work/seamarks.osm.pbf --overwrite
osmium export work/seamarks.osm.pbf -f geojsonseq -o work/seamarks.geojsonseq --overwrite
python3 build_seamarks.py work/seamarks.geojsonseq "out/$SEAMARKS"

echo "== Tiefenlinien (BSH)"
# Die Vermessung ändert sich selten und der BSH-Dienst ist von GitHub aus sehr langsam:
# normalerweise die bisherige Version übernehmen, neu abrufen nur mit DEPTHS_REFRESH=1 oder wenn keine da ist
if [ "${DEPTHS_REFRESH:-0}" != 1 ] && gh release download revierkarte -p "tiefenlinien-*.pmtiles" -D work --clobber 2>/dev/null; then
  echo "übernehme $(ls work/tiefenlinien-*.pmtiles)"
  mv work/tiefenlinien-*.pmtiles "out/$DEPTHS"
elif timeout 3h python3 fetch_depths.py $W $S $E $N 9 14 work/tiefenlinien.mbtiles; then
  pmtiles convert work/tiefenlinien.mbtiles "out/$DEPTHS"
else
  echo "Tiefenlinien nicht abrufbar – übernehme die bisherige Version"
  gh release download revierkarte -p "tiefenlinien-*.pmtiles" -D work --clobber
  mv work/tiefenlinien-*.pmtiles "out/$DEPTHS"
fi

echo "== Import in den Kachelserver"
docker rm -f wf-tiles >/dev/null 2>&1 || true
docker volume rm wf-osm >/dev/null 2>&1 || true
docker volume create wf-osm >/dev/null
docker run --rm -e THREADS=$THREADS -v "$PWD/work/revier.osm.pbf:/data/region.osm.pbf" -v wf-osm:/data/database/ $IMAGE import

echo "== Kacheln rendern (Zoom $ZMIN–$ZMAX)"
docker run -d --name wf-tiles -p 8080:80 -e THREADS=$THREADS -v wf-osm:/data/database/ $IMAGE run >/dev/null
until curl -sf -o /dev/null --max-time 300 http://localhost:8080/tile/8/132/82.png; do sleep 5; done
python3 fetch_tiles.py $W $S $E $N $ZMIN $ZMAX work/revierkarte.mbtiles
docker rm -f wf-tiles >/dev/null
pmtiles convert work/revierkarte.mbtiles "out/$TILES"

echo "== Prüfen"
python3 check.py work/revierkarte.mbtiles "out/$TILES" "out/$SEAMARKS" "out/$DEPTHS"

echo "== Manifest"
python3 make_manifest.py "$VERSION" "out/$TILES" "out/$SEAMARKS" "out/$DEPTHS" > out/revierkarte.json
cat out/revierkarte.json
