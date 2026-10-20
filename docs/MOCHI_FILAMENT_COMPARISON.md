# Mochi: zwei reale warme Bestandspaare

16.10.2026. Aktueller Benutzerplan unverändert. Keine Freigaben, Cloudaufrufe oder Druckstarts.

Verglichen wurden dieselben tatsächlichen Mochi-Außenflächen, derselbe unveränderliche Farbreferenzplan und dieselbe Methode: 19 unkalibrierte, linear im Licht interpolierte Rezeptfarben; lokale Albedo wird per CIEDE2000 quantisiert. Beide Vorder-/Seitenansichten haben identische Geometrie, Kamera, Beleuchtung und Rendering. Die Fehler unten beziehen sich auf die tatsächlich gerenderten und exportierbaren HEX-Palettenfarben; die internen ungerundeten Matchingwerte können geringfügig abweichen.

| Bestandspaar | Flächengewichtetes ΔE2000, kleiner besser | Median | P95 |
|---|---:|---:|---:|
| Aktuell: Bambu Beige31 `#F7E6DE` + ELEGOO Matte EarthBrown29 `#805947` | 15,216 | 15,151 | **17,279** |
| Alternative: Beige31 + ELEGOO PLA+ Brown28 `#9E6A4B` | **14,217** | **13,464** | 18,269 |

Brown28 verringert den flächengewichteten Gesamtfehler um 6,56 %. Es wirkt sichtbar wärmer, heller und damit näher am orangebraunen Original. Besonders Ohren und Schwanz profitieren. Für die schlechtesten Körperflächen fällt die Annäherung dagegen schlechter aus; die dunkleren Modellanteile werden mit dem helleren Basispaar weniger gut erreicht.

| Region | Aktuell: flächengewichtetes ΔE | Alternative | P95 aktuell → Alternative |
|---|---:|---:|---:|
| Körper | 15,116 | 14,651 | 16,402 → 19,032 |
| Rechtes Ohr | 14,791 | 12,553 | 17,745 → 14,282 |
| Linkes Ohr | 14,772 | 12,600 | 17,719 → 14,140 |
| Schwanz | 15,784 | 13,150 | 17,929 → 15,624 |

Einschätzung: **Brown28 ist eine sinnvolle wärmere Alternative für eine reale Mischprobe**, aber kein belegter physischer Gesamtsieger. Beide Paare verfehlen das ursprüngliche Orange deutlich; ohne gedruckte Mischkarte sind Deckkraft, Glanzunterschiede und sublayerabhängige Farbwirkung unbekannt. Nase/Augen bleiben bei beiden Varianten unverändert Black30. Der aktuelle Plan wurde nicht umgestellt.

## Dateien und Reproduktion

Vergleichsordner:
`benchmarks/mochi-material-comparison/comparison-2d50928161a54c4eaa9811f5f24e4f23/`

- `comparison-front-and-side.png`: links aktuelles EarthBrown29, rechts Brown28; Vorderansicht oben, Seite unten.
- `report.json`: Messmethode, konkrete Inventarspulen, Statistik pro Region, benutzte Rezeptzahlen.
- `brown-{29,28}.glb`, `brown-{29,28}-{front,right}.png`: dieselbe Originaloberfläche mit den jeweiligen berechneten Farben.
- `brown-28-plan-draft.json`: ausschließlich lokale Entwurfskopie, nicht im Projekt übernommen.
- Reproduktion der Berechnung: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python scripts/compare_mochi_materials.py` (neuer Laufordner). `render.py` im Vergleichslauf reproduziert Kamera/Beleuchtung.

Eine **zusätzliche** native Brown28-Profilvorlage ist vorbereitet:
`alternative-native-template/profiles-c6402ebc6726408ab1eaea6081596642/mochi-real-materials-profile-only.3mf`.

Slot1 Brown28, Slot2 Beige31, Slot3 Black30 plus 17 vorhandene virtuelle native Rezeptslots. Offizielle Bambu-CLI-Profilkonvertierung Exit0. ELEGOO PLA+ und eSUN Black verwenden bewusst **unkalibrierte Generic PLA @BBL H2D-Startprofile**, Beige das installierte Bambu PLA Basic-Profil. Keine behauptete ELEGOO-Spezialkalibrierung; keine Temperaturwerte erfunden. `profile-provenance.json` hält installierte Quellprofil-Hashes und tatsächliche Einstellungen fest. Neue GUI-/Slicer-/physische Abnahme dieser Alternative steht aus.

Reproduktion der Vorlage:
`PYTHONPATH=backend .venv/bin/python scripts/build_mochi_native_template.py --brown-id 28`.
Die Standardoption `--brown-id 29` bleibt für das bestätigte aktuelle Paar erhalten; jeder Aufruf erzeugt einen neuen Ordner.
