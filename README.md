# Watt'n Freund – Revierkarte

Offline-Karte für die App **Watt'n Freund**: Ostfriesisches Wattenmeer von Borkum und dem Dollart bis zur Jade, dazu Helgoland.

Die Dateien liegen im Release [`revierkarte`](../../releases/tag/revierkarte):

| Datei | Inhalt |
|---|---|
| `revierkarte-<Datum>.pmtiles` | Rasterkacheln Zoom 8–15 im Stil OpenStreetMap Carto (PMTiles) |
| `seezeichen-<Datum>.geojson` | Seezeichen aus OpenStreetMap (Tonnen, Pricken, Kardinal-, Sonderzeichen, Feuer, Wracks) |
| `tiefenlinien-<Datum>.pmtiles` | Tiefenlinien des BSH (Küsten- und Ansteuerungskarten), Zoom 9–14 |
| `revierkarte.json` | Stand der Daten, Dateigrößen und SHA-256-Prüfsummen |

Die App lädt die Karte unter „Mein Boot → Offline-Karte“ und zeigt sie, wenn kein Netz verfügbar ist.

**Nicht zur Navigation.** Maßgeblich sind amtliche Seekarten, Bekanntmachungen und die Betonnung vor Ort.

## Neu bauen

**Automatisch:** Die GitHub Action [`Revierkarte bauen`](.github/workflows/revierkarte.yml) baut die Karte
am 1. April und am 1. Juli neu und veröffentlicht sie, sofern die Prüfung (`check.py`: Zoomstufen,
Kachelzahl, Größe, Seezeichen) besteht. Von Hand starten: Actions → „Revierkarte bauen“ → „Run workflow“.
Neue Dateien tragen das Datum im Namen, das Manifest wird zuletzt ersetzt.

Die Tiefenlinien übernimmt die Action aus dem bisherigen Release – die Vermessung ändert sich selten, und der
BSH-Dienst liefert an GitHub nur sehr langsam. Neu abrufen: beim Start von Hand „Tiefenlinien neu beim BSH
abrufen“ ankreuzen (bis zu 3 Stunden), oder lokal `DEPTHS_REFRESH=1 ./build.sh`. Die App lädt bei einer neuen
Version nur die Dateien, die sich geändert haben.

**Lokal:** Voraussetzungen Docker (z. B. `colima`), `osmium-tool`, `pmtiles`, Python 3.

```sh
./build.sh
```

Das Skript lädt die OSM-Auszüge von Geofabrik, importiert sie in einen lokalen
[OpenStreetMap-Kachelserver](https://github.com/Overv/openstreetmap-tile-server), rendert die Kacheln
und schreibt Seezeichen und Manifest.

## Lizenz

Kartendaten © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), verfügbar unter der
Open Database License (ODbL). Tiefenlinien © Bundesamt für Seeschifffahrt und Hydrographie (BSH), nach GeoNutzV,
nicht zu Navigationszwecken. Kartenstil [OpenStreetMap Carto](https://github.com/gravitystorm/openstreetmap-carto) (CC0).
Die Skripte in diesem Repo stehen unter der MIT-Lizenz.
