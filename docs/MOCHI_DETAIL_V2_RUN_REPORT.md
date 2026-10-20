# Mochi Detail-v2: unabhängiger neuer Anatomieentwurf

16.10.2026. Neuer, quellgebundener Entwurf aus dem gewichteten Augen-/Nasenmesh. Die v1-Quelle und ihre Guards bleiben gültig und unverändert. Hauptprojekt-Adoption als neue lokale Version am 16.10.2026 durchgeführt. Keine Cloudgenerierung und keine automatische Freigabe.

## Bindungen

| Bestandteil | SHA-256 / Kennung |
|---|---|
| Preset | `mochi-anatomical-detail-v2` |
| Neue GLB-Bytes | `bdb9e145f308d7c9a1a6a49ba2111f1bbea658f1bfdf00f9ead2b353e50f29e7` |
| Meshhash bei180-mm/Y-up | `8b3049e9f9bd3d0ad66be9d1be5e8ed9cae045fa246ff1fd06f63c6583fc3548` |
| Normalisierte Geometriesignatur | `1d03ad837398f2c0a9cee65884f2091064ca210ff8981a85e9006e6e9f590675` |
| Originale neue4-Klassenmaske, little-endian uint32 | `30300ff10765421f0c39c08f03045d4c37c42864b23913d530f7c39efa478d22` |
| Kanonische9-Anatomieregionen, little-endian uint32 | `c5cce0376d6c66fa26d750580f8d5b60d39970b0c31c9000b813fc6fe884b979` |

Die neuen Module `geometry/mochi_detail_masks.py` und `services/mochi_detail_pipeline.py` prüfen diese Bindungen. Keine globale Quellen-Whitelist wurde gelockert; v1 lehnt die neue Geometrie weiterhin ab. Geänderte Masken werden nicht stillschweigend ignoriert.

Vier ursprüngliche Materialklassen wurden mit derselben Methode auf der neuen Albedo neu bestimmt: nächste Farbe unter den drei Originalfarbklassen `#AF440A/#852F06/#EFB27C`, danach die ursprüngliche neutrale Dunkelreserve L<22 und Chroma<12. Resultat94238/22821/30245/2696 Flächen. Einfaches Nearest unter allen vier Klassen wäre falsch: es würde warme dunkle Irisanteile zusätzlich schwarz klassifizieren. Dieses Verfahren wurde deshalb nicht verwendet.

## Erneute Konstruktion

Finaler lokaler Lauf: `benchmarks/mochi-eye-detail-20261016/v2-draft-218d971813354ec1a4b70c7ce9f81fb4/`,34,3 Sekunden einschließlich Farbvorschau und Core-3MF-Roundtrips.

- 9 geschlossene, jeweils zusammenhängende Teile,7 Stifte,10 kombinierte Montagepfadprüfungen bestanden.
- Nase R1,5/L3 mm; Ohren/Schwanz R1,2/L2,5 mm; Keyed-Profile mit tatsächlicher Socket-Footprint-Prüfung des aktuellen Kerns.
- **0,05 mm radiales Spiel**, entsprechend der akzeptierten realen Nasenprobe; V2 lehnt stillschweigend engere oder weitere Einstellungen ab. Die Nasenprobe war kein physischer Gesamttest aller neuen Teile.
- Vier Augeneinsätze ausdrücklich `connector_mode='glue'`, ohne Pinversuche. Kein nachträgliches Entfernen erzeugter Pins. Klebespiel/Haftung und Druckbarkeit feiner Ränder bleiben physisch zu prüfen.
- Finale konservative Aufteilung: fünf Platten – Körper, rechtes Ohr, linkes Ohr und Schwanz jeweils separat; Nase/Augen Black30 gemeinsam. Brown29/Beige31 bleiben das identische Basispaar. Keine dritte Spule am Körper.

| Teil | Dreiecke | Volumen mm³ |
|---|---:|---:|
| Körper | 104070 | 394485,222 |
| Nase | 4328 | 119,219 |
| Rechtes Ohr | 5254 | 6036,234 |
| Linkes Ohr | 4968 | 5976,665 |
| Schwanz | 38626 | 69513,779 |
| Augen1/2/3/4 | 576/368/352/752 | 3,879/14,314/14,972/4,775 |

## Konkret gefundene neue Fehler

1. Die besser aufgelöste Quelle enthält nun eine getrennte dunkle Mundlinie bei Z≈122 mm. Die alte Nasensaat120..135 mm nahm sie fälschlich als zweite Naseninsel mit auf; deren Kappe verließ den Solid. V2-Nasensaat124..135 mm umfasst die ganze Nase, schließt die Mundlinie ausdrücklich aus. Keine Toleranz gelockert.
2. Der alte linke Ohrschnitt ließ eine Kappe0,079 mm aus dem unveränderten Solid treten. Neue ausschließlich analytische Schnittparameter Taubin30/Concavity.06 halten sie innerhalb. Die zunächst ebenfalls innenliegende Variante.03 erzeugte eine verzweigte Root-Grenze und wurde verworfen. Erst die vollständige geschlossene Konstruktion einschließlich Steckprofilen galt als Erfolg.
3. Selbst0,0001-mm-Schwerpunktnähe genügte beim feineren Mesh nicht: zehn neue innere Kappen-/Taschenflächen lagen extrem nah an der Originalhaut; vier hätten am Körper fälschlich Black30 eingeführt. Eine weitere bloße Abstandsheuristik wurde nicht als Lösung übernommen.

Stattdessen prüft `geometry.compare.unchanged_source_faces()` bei V2 die **Identität aller drei Dreiecksecken**, permutationsunabhängig und innerhalb1e-6 mm. Damit werden auch neue koplanare kleine Kappen mit demselben Schwerpunkt korrekt ausgeschlossen. Generische verfeinerte/gekachelte Pfade behalten ihre eigene Abstandsmethode.

Unabhängige zweite Kontrolle über ursprüngliche Vertex-ID-Dreieckstripel bestätigt: alle150000 Originaldreiecke exakt einmal erhalten,0 verloren,0 dupliziert. Der neue Eckidentitätshelper liefert auf allen neun Teilen exakt dieselbe Zuordnung. Beleg `v2-exterior-provenance.json` im Prüfordner.

## Erscheinung und bewusste Materialabweichung

`v1-vs-v2-actual-print-colors.png` zeigt dieselbe Gesichts-Kamera und Beleuchtung mit den tatsächlich berechneten Bestandsfarben. V2 bewahrt die Augen-/Lidgeometrie und Nasenvertiefungen deutlich besser. Originaltextur, neutrale Geometrie und berechnete Druckfarben sind getrennt verglichen; siehe auch `docs/MOCHI_EYE_DETAIL_REVIEW.md`.

Die dunkle Mundlinie bleibt **als ursprüngliche vertiefte Körpergeometrie**, wird aber mit Brown/Beige angenähert. Sie ist keine erhaltene schwarze Druckfarbe, kein zusätzliches schwarzes Bauteil und kein fragiler separat zu druckender Mundfetzen. Im weichen Licht bleibt die Mundform durch ihre echte Geometrie lesbar. Dieser sichtbare Unterschied ist ein bewusster9-Teile-Vorschlag.

Trotz besserer Augenoberfläche bleiben die per-face-Palettenränder an Cremefell/Glanzpunkten teilweise sichtbar polygonal. Die neue Kopie ist keine Behauptung perfekter Augenzeichnung oder kontinuierlich gedruckter Textur. Bestandsorange und echte gemessene Mischfarben fehlen weiterhin.

## Reproduktion und noch folgende Prüfung

```sh
PYTHONPATH=backend .venv/bin/python scripts/build_mochi_detail_production.py \
  --source benchmarks/mochi-eye-detail-20261016/weighted-eyes-150k.glb \
  --reference-plan benchmarks/mochi-eye-detail-20261016/v2-reference-plan.json
```

Optional `--native-template PFAD` erzeugt zusätzlich neue native Platten; immer neuer UUID-Ordner, nur lesender Zugriff auf Inventar/Einstellungen. Quelle wird byteweise gegen den fest gebundenen SHA geprüft. 12 gezielte V2-Tests und3 Eckidentitätstests bestanden; vorhandene Quellenreferenzen wurden dabei nicht gepatcht oder überschrieben.

Native Material-/Rezeptparität und tatsächliches Slicing aller fünf finalen Platten sind unten belegt. Geometrie-, Masken- und physische Freigaben aus v1 gelten nicht automatisch für V2.

## Abschließender nativer Material-/Geometrieabgleich

Frühe native Dateien des Materialvergleichs liegen in `native-export/`. **Die kompakte Zweiplatten-Anordnung ist überholt und darf nicht als finale Druckanordnung verwendet werden:** Der reale v1-GUI-Slice meldete bei Schicht3310 einen G-Code-Konflikt zwischen Baumstützen von Körper und Schwanz. Die Geometrie-/Materialparität dieser Vergleichsdateien bleibt gültig:

- `plate-01-H2D-regional-native.3mf`: Körper, beide Ohren, Schwanz; reale Slots1/2 = EarthBrown29/Beige31. Maximaler Weltgeometriefehler0,000007491 mm.
- `plate-02-H2D-regional-native.3mf`: Nase und vier Glue-Augen; Slot3 = Black30. Maximaler Weltgeometriefehler0,000000257 mm.

150000 Original-Außenflächen wurden direkt zwischen finaler Teilevorschau und den tatsächlich geschriebenen nativen Dreiecks-/Filamentslotfarben verglichen; maximale RGB-Abweichung2,97e-8 (Float32-Rundung). Alle neun Teile halten das Limit von zwei tatsächlichen Spulen ein; kein Schwarz am Körper. Neue innere Flächen sind nur in der Vorschau neutralgrau und drucken mit dem dominanten tatsächlichen Material ihres jeweiligen Teils. Beleg `native-export/preview-native-parity.json`.

Beide Projekte nutzen die bestehenden echten H2D-.4-mm-/PLA-Profile der bestätigten Brown29/Beige31/Black30-Vorlage, inklusive ausdrücklich unkalibrierter Generic-PLA-Startprofile für Fremdmarken. Prozesswerte pro Platte:0,2-mm-Layer,Tree-Support,Schwelle20°,nur vom Bett; Platte1Raft0/AutoBrim5,Platte2Raft3/OuterOnly5. AUTO-Support folgt den verifizierten echten Objektdefaults. Material-/Thermalprofile wurden für den neuen Entwurf nicht erfunden oder per HEX-Umetikettierung ersetzt.

## Finale fünf Platten: echtes Bambu-Slicing bestanden

Finale native Projekte: `native-isolated-9a2bdc806b284303987694cb7339da2c/plate-01-native.3mf` bis `plate-05-native.3mf` im obigen Entwurfsordner. Große Teile stehen einzeln; die fünf schwarzen Kleinteile halten mindestens12 mm Abstand. Plattenrand mindestens25 mm. Auch an diesen fünf konkreten Dateien wurde der vollständige Vorschau-/Native-Farbabgleich erneut ausgeführt:150000 ursprüngliche Außenflächen, maximale RGB-Abweichung2,97e-8; vier Mixedteile ausschließlich physische Slots1/2, Nase/Augen ausschließlich Slot3. Beleg `native-isolated-9a2bdc806b284303987694cb7339da2c/preview-native-parity.json`; Reproduktion `benchmarks/mochi-eye-detail-20261016/verify_native_v2_isolated.py`.

Die frühere CLI231-Grenze ist geklärt: Offizielles `--normative-check=0` deaktiviert ausschließlich MakerWorld-Normative-Exportprüfungen. Die **G-Code-Gültigkeitsprüfungen bleiben aktiviert**, insbesondere ohne `--no-check`. Das beweist keine vollständige Pfadkonfliktfreiheit: Eine Negativkontrolle der alten, in der GUI nachweislich konfliktbehafteten v1-Platte liefert ebenfalls CLI-Exit0 und ein leeres Warnfeld. CLI-Erfolg ist deshalb ausschließlich ein tatsächlicher Slice-/G-Code-Exportnachweis. `scripts/slice_native_plates.py` führt diese Prüfung reproduzierbar aus. Alle fünf tatsächlichen Slices endeten mit Exit0/Success und leerem `warning_message`; neue G-Code-Dateien wurden erzeugt. Keine Druckerkommunikation.

| Platte | Inhalt | Slicer-Zeitprognose | Gesamtmaterial inkl. Spülen/Stützen |
|---|---|---:|---:|
| 1 | Körper | 15h36m34s | 184,61 g |
| 2 | Rechtes Ohr | 3h40m47s | 36,68 g |
| 3 | Linkes Ohr | 3h37m07s | 36,47 g |
| 4 | Schwanz | 8h56m02s | 79,10 g |
| 5 | Nase + vier Augen | 9m27s | 0,46 g |
| Gesamt | 9 Teile | 31h59m57s | 337,33 g |

Die getrennten Mixed-Platten erhöhen Spül-/Turmaufwand deutlich. Das ist ein bewusst konservativer Ausgangspunkt gegen den belegten Stützpfadkonflikt, keine Druckkostenoptimierung und keine automatische Pfadfreigabe. Slice-Nachweise mit Quell-/G-Code-Hashes: `docs/mochi-v2-five-plates-slicer-verification.json` sowie `benchmarks/mochi-local-slicer/slice-3a8e77094cf64560b7b6ef170262d420/verification.json`.

Für die vorherige schwarze V2-Plattenanordnung liegt zusätzlich ein echter GUI-Slice vor:31 Schichten/6,4 mm/0,46 g/9m25, ausschließlich Slot3, Raft3 und Supports. G-Code: `benchmarks/nose-fit-comparison/native-supported-20261016/Mochi-V2-schwarze-Details-GUI-geprueft.gcode.3mf`. Dieser GUI-Nachweis ist keine Behauptung, alle fünf finalen Dateien in der GUI geöffnet zu haben.

Die unveränderten offiziellen Generic-PLA-Startprofile melden beim GUI-Slice `bed_temperature_too_high_than_filament`: Textured-PEI55 °C gegenüber Glasübergangsangabe45 °C. Der Hinweis wird nicht durch erfundene Temperaturwerte versteckt. Die Fremdmarkenprofile und tatsächlichen Mischfarben bleiben unkalibriert. Gesamtdruck, Stützentfernung, Kleben und neue Steckpassungen sind physisch noch nicht geprüft; nur die ursprüngliche reale Nasenprobe begründet0,05 mm radial.

## Hauptprojekt: versionierte Übernahme

Die autorisierte lokale API-Übernahme antwortete mit HTTP200/Revision20. Neuer Source-Pfad `versions/f292af4f7eb14186ad71b8349df2acc1/detail-source.glb`; vollständiger alter Projektstand `versions/f292af4f7eb14186ad71b8349df2acc1/previous-project.json`. Beide Pfade relativ zu `data/projects/1b0e2fdd463d4f15ac64f1c7b3e8acc7/`. Alte Dateien bleiben erhalten. Meshhash und Quell-SHA entsprechen den Bindungen dieses Berichts.

Der neue Plan hat getrennte unveränderliche Referenzen für die ursprünglichen vier Materialklassen und die neun kanonischen Anatomiebereiche. Vorherige Mesh-/Farb-/Konstruktions-/Exportfreigaben werden invalidiert; `automatic_approval=false`. Die normale UI berechnet anschließend neue Teile und native Platten aus der neuen Quelle. Ein fehlender generischer Refinement-Zähler verursachte zunächst einen UI-Anzeigefehler; der Hauptagent korrigierte die Darstellung quellgebundener Presets. Die tatsächliche Meshqualität enthält weiterhin150000 Dreiecke und den regulären geschlossenen Qualitätsbericht.

Vollsuite vor Serverneustart und Übernahme:378 Tests bestanden (31,64 s); lokale API-Adoptionstests arbeiten ausschließlich mit temporären Projekten. Physische oder menschliche Freigaben werden durch diese Tests nicht erzeugt.

Nach Serverneustart erneut gezielt geprüft:19 V2-/Adoptions-/Eckidentitätstests bestanden (3,78 s), einschließlich des regulären Meshqualitätsvertrags mit150000 Dreiecken, gültigem Solid und0 offenen/Non-Manifold-Kanten.

## Unabhängige Z-/Clippingkontrolle nach echtem Slicing

Negative `result.json`-Objektbbox-Z-Werte wurden ausdrücklich unabhängig untersucht. `verify_slice_world_bounds.py` liest die nativen XML-Vertices sowie jede Komponenten-/Build-Transformkette selbst, ohne trimesh-Loader. Vergleich vor/nach tatsächlichem Bambu-Slice: alle neun gespeicherten World-Vertexarrays exakt gleich, maximale Koordinatenänderung0 mm; keine reale Meshhaut unter dem Bett (numerisches Minimum−7,3e-10 mm). Die CLI-Bbox verwendet die transformierten Ecken der **lokalen achsenparallelen Boundingbox**: Bei gedrehten Teilen entstehen dadurch leere Ecken unter dem Bett. Alle gemeldeten negativen CLI-Werte passen genau zu dieser Rechnung.

| Teil | Tatsächliche World-Z-Spanne mm | Gemeldetes konservatives Bbox-MinZ mm |
|---|---:|---:|
| Schwanz | 0..80,424958 | −4,295356 |
| Nase | 0..5,445235 | −1,101371 |
| Auge1 | 0..1,770356 | −1,053940 |
| Auge2 | 0..1,459475 | −0,446429 |
| Auge3 | 0..1,402376 | −0,703495 |
| Auge4 | 0..1,613168 | −1,260671 |

Nasenhöhe5,445 mm plus ungefähr0,95 mm Raft erklärt die tatsächliche GUI-Gesamthöhe6,4 mm. Die größere CLI-Bbox-Höhe7,916 mm ist keine echte Nasenhöhe. Dieser Befund widerlegt geometrisches Unterbett-Clipping aus den Bbox-Zahlen; er ersetzt keine Prüfung der erzeugten Extrusionsbahnen. Beleg `native-isolated-9a2bdc806b284303987694cb7339da2c/slice-world-bounds-verification.json`. Physische Druckfreigabe bleibt offen.

Regulärer Hauptprojektlauf danach tatsächlich abgeschlossen: Konstruktion9 Teile/7 Pins/5 Platten, Export `runs/1193d7be224742cd92134900f1124ece/export`. Unabhängiger Abgleich `docs/mochi-v2-main-native-parity.json`: alle fünf nativen Platten haben identische tatsächliche Prozess-/Materialsettings, identische Dreiecksfarbcodes und World-Vertexabweichung0 gegenüber den oben tatsächlich gesliceten Vergleichsdateien. Reproduktion `scripts/verify_native_parity.py`. Das ist eine technische Paritätsprüfung, keine zusätzliche physische Abnahme.

## Unabhängige Extrusionspfadprüfung

`scripts/check_gcode_paths.py` liest das tatsächliche G-Code-Programm; sechs Modal-/Ownership-/Fehlerregressionen plus ein Mixed-Sublayer-Test bestanden. Eigentümer stammen aus `start printing object`/`stop printing object`; vorangestellte `OBJECT_ID`-Kommentare gelten ausdrücklich nicht als Besitzerwechsel. Die vier CLI-Einzelobjektplatten haben keine Owner-Kommentare: Hier belegt ausschließlich das unveränderte `result.json` mit genau einem gesliceten Objekt den Owner. Mehrere unbekannte Objekte, Arc-Extrusionen oder nichtplanare Extrusion werden abgewiesen. M82/M83, G90/G91, G92, tatsächlich positives E sowie FEATURE, LINE_WIDTH und LAYER_HEIGHT werden berücksichtigt.

Die bekannte konfliktbehaftete GUI-v1-Datei wird unabhängig abgelehnt:30.118 gleichhohe Support↔Model-Footprintüberlappungen sowie weitere Kreuzungen verschiedener Owner. Die genaue GUI-Sublayernummer3310 darf nicht mit dem3310. sortierten Extrusions-Z gleichgesetzt werden; die exakte Indexzuordnung bleibt ausdrücklich ungeklärt. Der tatsächliche Gesamt-Negativkontrollnachweis ist davon getrennt.

Alle fünf finalen v2-G-Code-Dateien wurden vollständig erneut gelesen: **2.766.148 echte Extrusionssegmente**. Alle Linienbreiten-erweiterten globalen XY-Bounds unterschiedlicher Owner sind bereits disjunkt – Körper/Ohren/Schwanz jeweils gegenüber dem Spülturm, auf der Schwarzplatte alle fünf Bauteile einschließlich zugehöriger Supports/Rafts untereinander. Damit gibt es bei diesen Dateien auch über unterschiedliche Z-Sublayer hinweg keine geometrische Footprintüberlappung zwischen verschiedenen Bauteilen oder Spülturm und Modell. Der Prüfer unterstützt zusätzlich tatsächliche Z-Beadintervalle `[Z−LAYER_HEIGHT,Z]`, wenn XY-Bounds überlappen; bloße gleiche Top-Z-Werte wären bei Mixed-Filament sonst unvollständig.

Getrackter Nachweis: `docs/mochi-v2-extrusion-footprint-verification.json`, vollständige Benchmarkausgabe `benchmarks/mochi-local-slicer/isolated-volumetric-path-screening.json`. Dies ist eine zusätzliche geometrische Pfadprüfung mit erfolgreicher Negativkontrolle, keine vollständige Düsen-/Schlitten-/Dynamik- oder physische Druckzertifizierung. Keine Druckerkommunikation und kein neues Produktionsgate.

Auch eine separate Prüfung des engen Z-Nachbarschaftsfensters um sortierten Index3310 weist in der alten Vergleichsplatte103 Support↔Model- und1580 Model↔Model-Footprintüberlappungen mit tatsächlich überlappenden Beadhöhen nach. Das genaue GUI-Indexmapping wird weiterhin nicht behauptet. Implementierungs-/Testdatei-SHA stehen im getrackten JSON-Nachweis.
