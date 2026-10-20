# Unabhängige lokale G-Code-Footprintprüfung

`scripts/check_gcode_paths.py` liest tatsächlich erzeugten G-Code. Die Prüfung ergänzt den Slicer: Ein echter GUI-Pfadkonflikt der alten Mochi-v1-Platte blieb bei CLI-Exit0 und leerem Warnfeld bestehen. Ein erfolgreicher Slice allein ist deshalb keine vollständige Pfadfreigabe.

## Unterstützter Vertrag

- Positive Extrusion: G0/G1 sowie G2/G3 in G17/XY mit relativen I/J-Mittelpunkten; CW/CCW und vollständige Kreise, einschließlich P1.
- Modalzustand: G90/G91, M82/M83 und G92; fehlende Achsen behalten ihre Position. I/J bleiben relativ zum Bogenanfang, unabhängig vom Positionsmodus.
- Besitzwechsel nur über `start printing object`/`stop printing object`; `OBJECT_ID` kann schon vor dem Wischen des vorherigen Objekts stehen und ist kein Besitzerwechsel.
- Einzelobjekt-CLI-Dateien ohne diese Marker brauchen eine passende `result.json` mit genau einem Objekt. Mehrere unbekannte Besitzer werden abgewiesen.
- Tatsächliche FEATURE/LINE_WIDTH/LAYER_HEIGHT: Linienbreiten-erweiterte Footprints und physische Beadintervalle `[Z−LAYER_HEIGHT,Z]`. Nur gleiche Top-Z-Werte wären für Mixed-Unterschichten unvollständig.
- STRtree prüft Footprints unterschiedlicher Bauteile, Support/Modell und Spülturm/Modell. Bereits global disjunkte Owner-XY-Bounds beweisen die betreffende räumliche Trennung unabhängig von den einzelnen Z-Höhen.

Druckende Helices, G18/G19, R-Bögen, absolute Mittelpunkte G90.1, mehrere Windungen und ungültige Kreise werden ausdrücklich abgewiesen. Nicht extrudierende Startup-/Travel-Bögen aktualisieren ihren exakten Endpunkt, erzeugen aber keine angeblich geprüfte Druckbahn. Das betrifft beispielsweise Bambu-Startup `G3 Z0.4 I1.217 J0 P1` ohne E.

## Bogenfehler

Maximaler Fehler0,005 mm. Die Teilungszahl folgt der analytischen Sehnenabweichung `r·(1−cos(Δθ/2))`. Kleine Radiusabweichungen gerundeter I/J-Endpunkte verbrauchen denselben Fehleretat vollständig; mehr als0,0025 mm werden abgewiesen. Endpunkte bleiben exakt. Jede Bogensehne erhält zusätzlich das Doppelte ihres konservativen Fehlers als LINE_WIDTH-Zuschlag, damit der Footprint den approximierten Bogen umschließt. Globale XY-Bounds verwenden dieselbe Erweiterung.

Die Footprintprüfung verwendet weiterhin0,02 mm Überlappungstoleranz. Ein Ergebnis ist eine geometrische Prüfung unter diesem Vertrag, keine Düsen-/Schlitten-, Dynamik-, Thermik-, Haftungs- oder physische Druckzertifizierung. Gleichteilinterne Pfade werden nicht als fremde Bauteilkollisionen behandelt. Keine Slicerprüfung wird deaktiviert; kein Druckauftrag wird gesendet.

## Tatsächliche Pip-Nachprüfung

Quelle: `benchmarks/pip-native-slicer/corrected/slice-12a565d4fcf5474f9d4cc8a3cc23c3de/plate-01..10/plate_1.gcode`.

| Messung | Tatsächlicher Wert |
|---|---:|
| Geprüfte Platten | 10/10 bestanden |
| Tatsächliche/segmentierte Extrusionssegmente | 5.671.524 |
| Druckende Kreisbogenbefehle | 843.410 |
| Daraus erzeugte Sehnen | 4.029.786 |
| Maximaler konservativer Fehler | 0,004999997 mm |
| Größte gerundete Radiusabweichung | 0,002063039 mm |
| Summe finale lokale Prüflaufzeit unter paralleler Last | 100,32 s |
| Unterschiedliche Owner-XY-Bounds je Platte | Alle disjunkt, inklusive Linienbreite und Bogenfehler |

Getrackter Nachweis mit G-Code-/Implementierungs-/Test-SHA: `docs/pip-gcode-footprint-verification.json`. Vollständiger Bericht auch im genannten Benchmarkstamm.25 gezielte Parser-/Winding-/Endpunkt-/Ownership-/Kollision-/Ungültigkeits- und Broadphase-Gleichheitsregressionen bestanden in0,43 s. Der echte Kreisbogen-Ownership-Test würde mit einer bloßen geraden Verbindung zwischen den Endpunkten die Kollision verpassen.

Die frühere Mochi-Negativkontrolle sowie die fünf isolierten Mochi-Platten bleiben separat unter `docs/mochi-v2-extrusion-footprint-verification.json` dokumentiert. Die genaue GUI-Sublayernummer3310 wird ausdrücklich nicht mit dem3310. sortierten G-Code-Z verwechselt.

## Optimierte Owner-Broadphase, unveränderte Prüflogik

Der Prüfer baut je Owner einen eigenen STRtree. Ausschließlich andere Owner werden räumlich abgefragt; dieselben geometrischen Abstände, Beadintervalle, Featureklassen und Toleranzen bleiben verbindlich. Eine eingefrorene Version des vorherigen All-Owner-Algorithmus wird auf240 deterministischen, unterschiedlich breiten/hohen Modell-/Support-/Turmsegmenten und vier Z-Auswahlen mit der neuen Version verglichen: sämtliche Trefferidentitäten, Abstände und Kategorienzahlen exakt gleich.24 gezielte Tests bestanden. Dieselbe reale GUI-Negativdatei liefert im selben Z-Fenster weiterhin exakt103 Support↔Model- und1580 Model↔Model-Treffer. [Quell-/Testhash und echter Gleichheitsnachweis](gcode-owner-tree-equivalence.json). Frühere Nachweise behalten ausdrücklich ihre ursprünglich geprüfte Implementierungs-SHA; neue Prüfberichte werden mit aktueller SHA erzeugt.

Vor Shapely folgt inzwischen ein zusätzlicher konservativer NumPy-AABB-Filter: Beide beteiligten Segment-Bounds enthalten ihre vollständige halbe Linienbreite einschließlich Bogenfehler. Nur Segmentboxen ohne jede Überlappungsmöglichkeit mit der Gesamtbox eines anderen Owners entfallen aus der Broadphase. Die Originalindices und die Gesamtzahl gelesener Segmente bleiben erhalten.25 gezielte Tests sowie dieselbe tatsächliche Negativkontrolle bestätigen identische Treffermengen und Abstände; keine QA-Regel wird übersprungen. [Finaler AABB-/Owner-Gleichheitsnachweis](gcode-owner-bbox-equivalence.json).

Die zehn Pip-Dateien wurden nach beiden Broadphase-Optimierungen tatsächlich erneut vollständig geprüft. Alle G-Code-Hashes, Segmentzahlen und Ergebnisse stimmen mit dem vorherigen Lauf überein; der kanonische getrackte JSON-Bericht nennt jetzt die endgültige aktuelle Script-/Test-SHA. Der vorherige Nachweis liegt separat unter `docs/pip-gcode-footprint-verification-before-owner-bbox.json`. Finale gemessene Gesamtlaufzeit unter paralleler lokaler Last: 100,32 s; keine generelle Beschleunigungsbehauptung aus unterschiedlichen Lastbedingungen.
