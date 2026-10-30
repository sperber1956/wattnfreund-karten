# Watt'n Freund – Revierkarte

Offline-Karte für die App **Watt'n Freund**: Ostfriesisches Wattenmeer von Borkum und dem Dollart bis zur Jade, dazu Helgoland.

Die Dateien liegen im Release [`revierkarte`](../../releases/tag/revierkarte):

| Datei | Inhalt |
|---|---|
| `revierkarte.pmtiles` | Rasterkacheln Zoom 8–15 im Stil OpenStreetMap Carto (PMTiles) |
| `seezeichen.geojson` | Seezeichen aus OpenStreetMap (Tonnen, Pricken, Kardinal-, Sonderzeichen, Feuer, Wracks) |
| `revierkarte.json` | Stand der Daten, Dateigrößen und SHA-256-Prüfsummen |

Die App lädt die Karte unter „Mein Boot → Offline-Karte“ und zeigt sie, wenn kein Netz verfügbar ist.

**Nicht zur Navigation.** Maßgeblich sind amtliche Seekarten, Bekanntmachungen und die Betonnung vor Ort.

## Neu bauen

Voraussetzungen: Docker (z. B. `colima`), `osmium-tool`, `pmtiles`, Python 3.

```sh
./build.sh
gh release upload revierkarte out/* --clobber
```

Das Skript lädt die OSM-Auszüge von Geofabrik, importiert sie in einen lokalen
[OpenStreetMap-Kachelserver](https://github.com/Overv/openstreetmap-tile-server), rendert die Kacheln
und schreibt Seezeichen und Manifest.

## Lizenz

Kartendaten © [OpenStreetMap-Mitwirkende](https://www.openstreetmap.org/copyright), verfügbar unter der
Open Database License (ODbL). Kartenstil [OpenStreetMap Carto](https://github.com/gravitystorm/openstreetmap-carto) (CC0).
Die Skripte in diesem Repo stehen unter der MIT-Lizenz.
