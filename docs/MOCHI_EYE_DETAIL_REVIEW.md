# Mochi: Augenqualität, Original und gewichtete 150k-Kopie

16.10.2026. Rein lokale Untersuchung, zwei Blender-Threads. Original, vorhandene Arbeitskopie, Hauptplan, Preset und native Produktionsdateien unverändert. Keine API-Aufträge oder Freigaben.

## Befund

**Die globale Decimation verliert tatsächlich Augengeometrie.** Original und 150k-Kopie wurden unter derselben weichen Beleuchtung, Kamera und ausdrücklich gleichem Smooth-Shading gerendert; Normalmaps waren deaktiviert. Im neutralgrauen Kontrollrender hat das Original glatte Lidränder und Augenoberflächen, die Arbeitskopie dagegen deutliche polygonale Ring-/Normalenstufen. Das ist nicht allein ein Vorschau-Shaderproblem.

Die Originaltextur enthält allerdings bereits kantig gemalte Glanzpunkte und vereinfachte Augenzeichnungen. Mehr Geometrie kann diese aufgemalten Formen nicht erfinden oder verbessern. Die Untersuchung trennt daher reine Geometrieansichten und Originaltexturansichten.

| Modell | Gesamtdreiecke | Dreiecke Augen-ROI | Median Dreiecksfläche Augen-ROI |
|---|---:|---:|---:|
| Original | 2630056 | 10096 | 0,02727 mm² |
| Aktuelle globale Arbeitskopie | 150000 | 585 | 0,63575 mm² |
| Neuer gewichteter Versuch | 150000 | 10103 | 0,02710 mm² |

Augen-ROI: `6 < abs(x) <18`, `132 < z <148`, `y <-45`, in der bestehenden 180-mm-Z-up-Normalisierung. Der Unterschied der ROI-Zählung Original/Versuch entsteht an den ROI-Grenzen und der jeweiligen Modellnormalisierung, nicht aus neu erfundener Auflösung.

## Getrennter Vorbereitungstest

`benchmarks/mochi-eye-detail-20261016/weighted-eyes-150k.glb` wurde neu aus dem unveränderten Original erzeugt. Wie bisher: zusammenfallende UV-Nahtpositionen verschweißen, konsistente Orientierung, Blender Collapse und UV-/Materialexport. Zusätzlich werden zwei modellgebundene Augenellipsoide und eine Nasenellipsoidregion durch eine Vertexgruppe gegen Kollaps geschützt; eine schmale Übergangszone lockert den Schutz zum restlichen Körper. Keine Subdivision, Glättung, Formrekonstruktion oder Volumenremesh.

8441 geschützte und3012 Übergangsvertices; exakt150000 Ausgabedreiecke; etwa32 Sekunden inklusive Import/Export, zwei Threads. Nullgewicht schützt die betreffenden Kanten im offiziellen [Blender-Decimate-Quellcode](https://raw.githubusercontent.com/blender/blender/main/source/blender/bmesh/tools/bmesh_decimate_collapse.cc). Das Verfahren nutzt die dokumentierte [Vertexgruppensteuerung des Decimate-Modifikators](https://docs.blender.org/manual/en/4.0/modeling/modifiers/generate/decimate.html).

Wichtig: zusätzliche Gesichtsdreiecke werden aus demselben Gesamtbudget umverteilt. Der Rest des Modells erhält etwas weniger Geometrie. Es ist kein kostenloser Detailgewinn überall.

## Qualitätsmessung

Beide 150k-Kopien: eine geschlossene zusammenhängende Oberfläche, konsistente Orientierung, keine Rand-/Nonmanifoldkanten, endliche Koordinaten. Selbstüberschneidungen sind nicht erschöpfend zertifiziert.

Identische2000 flächengewichtet gezogene Punkte auf der ursprünglichen Augen-ROI, jeweils auf die neue Oberfläche projiziert:

| Lokale Augenmessung | Aktuell global | Gewichteter Versuch |
|---|---:|---:|
| Geometrieabstand Median | 0,01677 mm | **0,00588 mm** |
| Geometrieabstand P95 | 0,04572 mm | **0,02028 mm** |
| Größter gemessener Abstand | 0,08141 mm | **0,02163 mm** |
| Albedo ΔE2000 Median | 0,4625 | **0,1508** |
| Albedo ΔE2000 P95 | 4,8756 | **1,5309** |

Global,6000 flächengewichtete Punkte je Richtung Original↔Kopie, identischer deterministischer Seed:

| Gesamtmodell | Aktuell global | Gewichteter Versuch |
|---|---:|---:|
| Geometrieabstand Median | **0,01289 mm** | 0,01341 mm |
| Geometrieabstand P99 | **0,05802 mm** | 0,06149 mm |
| Größter gemessener Abstand | 0,10745 mm | **0,10223 mm** |
| Albedo ΔE2000 P95 | **1,7705** | 1,8704 |
| 6-Klassen-Farbzuordnungsabweichung | **1,483 %** | 1,633 % |

Damit ist die lokale Verbesserung nachvollziehbar und global nur ein kleiner Qualitätsverlust gemessen. Es bleiben endliche Stichproben; das ist weder ein vollständiger Hausdorffnachweis noch ein physischer Drucktest. Kleine Normalisierungsunterschiede durch geänderte Extrema gehören zur tatsächlich verwendeten Importpipeline.

## Dateien und Wiederholung

Prüfordner `benchmarks/mochi-eye-detail-20261016/`:

- `three-way-textured-comparison.png`: Original / aktuelle150k / gewichtete150k, gleiche Originaltextur.
- `three-way-neutral-comparison.png`: dieselbe Geometriekontrolle ohne Textur oder Normalmaps.
- `original-vs-working-face-comparison.png`: zweispaltiger Ausgangsbefund.
- `weighted-preparation.json`, `*-roi-metrics.json`, `working-global-quality.json`, `weighted-global-quality.json`, `local-eye-quality.json`.
- `render_detail.py`, `prepare_weighted.py`, `eye_qa.py`: genaue lokale Prüfschritte.

Nachvollziehbare neue Vorbereitung mit neuem UUID-Ordner:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --threads 2 --python scripts/blender_prepare_mochi_eyes.py --
```

## Empfehlung und Übernahmegrenze

Der gewichtete Entwurf verbessert die Augen sichtbar und messbar; er ist ein sinnvoller Kandidat für die nächste kontrollierte Meshvorbereitung. **Er ersetzt den laufenden Mochi-Stand nicht.** Das bisherige anatomische Preset ist an Quellhash,150k-Geometriesignatur und immutable Masken gebunden und muss diese neue Topologie weiterhin ablehnen.

Eine Übernahme braucht eine separate neue Meshversion: Mesh prüfen/freigeben, Quellfarb-/Anatomiemasken neu aus dem Original übertragen und validieren, geschlossene9-Teil-Konstruktion sowie Stifte/Klebeaugen/10 Montagepfade erneut prüfen, danach Preview-/Native-Rezeptparität und beide H2D-Slices wiederholen. Das bestehende Preset darf nicht durch einen geänderten Hashcheck scheinbar passend gemacht werden. Insbesondere sind die heutigen vier sehr kleinen schwarzen Augeneinsätze für die neue Topologie nicht bereits freigegeben.
