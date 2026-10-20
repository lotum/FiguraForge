# Mochi · Ein Körper mit 20 Farbwerten · H2D

Diese neue Variante hat 180 mm Höhe. Rumpf, Beine, Kopf, Ohren, Schwanz und braune/helle Iris sind ein geschlossener Druckkörper. Nur schwarze Nase (Steckstift, 0,05 mm radial) und vier schwarze Augendetails (Kleben) sind separat. Die vier Augenumrisse sind aus der feineren Original-Albedo neu abgetastet. Der alte FiguraForge-Projektstand bleibt erhalten.

## In Bambu Studio öffnen

1. Bambu Studio neu öffnen, falls das Fenster nicht reagiert. Datei → Projekt öffnen → `Mochi-Koerper-20-Farben-H2D.3mf`. Vorhandene Projekt-/Prozesseinstellungen übernehmen.
2. Im H2D-Projekt die tatsächlichen Spulen zuordnen: Slot 1 ELEGOO Matte Earth Brown Nr.29 (#805947), Slot 2 Bambu PLA Basic Beige Nr.31 (#F7E6DE). Der Körper verwendet ausschließlich diese zwei physischen Filamente; 18 virtuelle Mischprofile ergeben zusammen mit den zwei reinen Endfarben genau 20 Zielfarben. Alle 20 werden tatsächlich auf Körperflächen verwendet.
3. Platte slicen und die Stützen/Schnittvorschau prüfen. Körper: aufrecht, 0,16-mm-Schichten, zwei Wände, 5% Lightning, Baumstützen. Prognose rund 32 h 46 min / 329,29 g inklusive Slicerzusätzen. Die braune Fremdmarke verwendet ein unkalibriertes offizielles Generic-PLA-H2D-Profil; die optische Vorschau ist ebenfalls unkalibriert.
4. Danach separat `Mochi-Schwarze-Details-H2D.3mf` als Projekt öffnen. Slot 3: eSUN ePLA-Lite Black Nr.30 (#272729), einer vorhandenen Düse zuordnen. Tatsächlich druckt diese Platte nur Schwarz. 0,12-mm-Schichten, drei Raftlagen und Baumstützen für die gekrümmten Rückseiten; ca.11 Minuten /0,44 g. Stützen entfernen, zunächst trocken anpassen, die vier kleinen Augeneinsätze kleben. Druckstart bleibt bei Richard.

## Prüfstand

Beide echten nativen Dateien gesliced (CLI Exit0/Result0), vollständige unabhängige Extrusions-Footprints und gemeinsame H2D-Fläche geprüft. Vorschau und native Mischrezepte stimmen überein, Prozesseinstellungen bleiben nach dem Slicen erhalten. Kein Druckauftrag gesendet. Native GUI-Nachprüfung war wegen der nicht verfügbaren Bambu-Fenstersteuerung nicht möglich; der lokale CLI-Prüflauf ist davon getrennt. Reale Passung/Farben und Stützentfernung sind noch zu testen.

Die 20 Beigeanteile in Prozent sind: 0,10,15,19,24,29,34,38,43,48,52,57,62,66,71,76,81,85,90,100. Die inneren Mischungen halten die belegte native 10–90%-Grenze ein; die Abstände zu den reinen Endpunkten sind deshalb größer. `mixed-recipes.json` enthält konkrete Prozentanteile und nominale Unterlagenstärken bei 0,16 mm. Farben sind optische Näherungen, keine gemessenen Filamentmischungen.

Optionales wärmeres Farbpaar als Empfehlung: Bambu PLA Basic Brown (#9D432C) mit Bambu PLA Basic Beige (#F7E6DE). Brown ist rötlicher als vorhandenes Earth Brown und dürfte dem Rotpanda näher kommen. Die Empfehlung ist eine Einschätzung anhand der Hersteller-HEX-Werte, keine Druckmessung. Quelle: https://store.bblcdn.eu/s8/default/903b60b06ac142e9b1b49ad53cfa4c82/Bambu_PLA_Basic_Hex_Code.pdf . Die gelieferten Dateien sind auf die vorhandenen Spulen29/31 abgestimmt; keine Bestellung vorgenommen.


## Dateien und unabhängige Belege

- [Körper · natives H2D-Projekt](../benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c/Mochi-Koerper-20-Farben-H2D.3mf)
- [Schwarze Details · natives H2D-Projekt](../benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c/Mochi-Schwarze-Details-H2D.3mf)
- [Importpaket mit beiden Projekten und Anleitung](../benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c/Mochi-H2D-Importpaket.zip)
- [Kopfquelle und regionale Form-/UV-Prüfung](mochi-unified-head-verification.json)
- [Aktuelle native Dateien, Slices, GCode-Hashes und vollständige Druckpfade](mochi-unified-print-verification.json)
- [507 Python-Tests / 55,38 Sekunden](test-results-mochi-unified-final.xml), beide Frontend-Harness zusätzlich bestanden.

Gesamtprognose beider finaler Slices: **32 h 56 min 38 s / 329,73 g**. Alle **4.272.941** positiven Extrusionssegmente einschließlich unterstützter Druckbögen unabhängig geprüft; keine Inter-Owner-Footprintkonflikte, gemeinsame H2D-XY-Grenzen eingehalten. Körper nutzt tatsächlich physische Slots1/2, Details nur Slot3. Alle20 Farbwerte werden verwendet; Vorschau-/Export-Rezeptparität positiv. Die vollständige Bibliothek enthält daher drei reale Profile, obwohl pro Druckplatte maximal zwei reale Filamente extrudiert werden.

Kopf: 299.998 Quellflächen, alter Körper an/unterZ110 unverändert, neue Punkte auf das2,63-Mio.-Original projiziert. Kopf-Medianfehler0,01584→0,00752mm; Stirn/Augen/Ohren gesondert dokumentiert. Keine bloße zusätzliche Unterteilung mit erfundenen Details. V2-Abstammung bleibt nachvollziehbar; unsichere Projektions-/UV-Fälle bleiben auf ihrer geprüften V2-Geometrie beziehungsweise UV-Interpolation. Endgültige Konstruktion: sechs geschlossene verbundene Einzelteile, ein Steckstift plus vier Klebeeinsätze; 308.152 Dreiecke über alle sechs Teile, unter350.000.

Aktuelle lokale Browserprüfung: [Vorschau](http://127.0.0.1:8011/Mochi-Vorschau.html). Front, Kopf, Seite/Rückseite und Explosion persönlich betrachtet; [Kopf](../screenshots/mochi-unified-final-head.png), [Front](../screenshots/mochi-unified-final-front.png), [Explosion](../screenshots/mochi-unified-final-exploded.png), [Seite/Rückseite](../screenshots/mochi-unified-final-side-rear.png). Die Vorschau lädt Geometriedaten aus lokalen JSON-Dateien, damit die Bedienung nicht an einem riesigen HTML-Dokument scheitert.

Reproduzierbare Werkzeuge: `scripts/build_mochi_head.py`, `scripts/build_mochi_unified_template.py`, `scripts/verify_mochi_unified_recipes.py`, `scripts/build_mochi_unified.py`, `scripts/slice_native_plates.py`, `scripts/check_gcode_paths.py`. Alle neuen Skripte kompiliert; keine kostenpflichtige Generierung und keine Änderung der alten Projekt-/Freigabedaten. Die Variante liegt als eigenständiges Bambu-Importpaket und lokale Vorschau vor; der bisherige Neunteile-Workflow in FiguraForge wurde nicht überschrieben.

**Befunde → Korrekturen:** Ganze Kopfzone statt nur Augen/Nase verfeinert; V2-Texturgrenzen an Pupillen durch neue feinere Albedoabtastung ersetzt; Ohren/Schwanz nicht mehr geschnitten; 20 tatsächlich verwendete Farbwerte statt der bisherigen19-Standardbibliothek; explizite lokale Lightning-/Wandstärken-Profilabweichungen gegen Bambu-Vererbung erhalten. Bestehende Standardrezepte anderer Projekte bleiben unverändert.

**Buddy:** Die gemeldeten25,328kg gehören weiterhin zum vorherigen 15%-Infill-/2-Wände-/Support-/Tower-Profil. Richards neue Präferenz für eine leichte dekorative Lightning-Konstruktion ist erfasst. Buddy wurde in diesem ausschließlich Mochi betreffenden Auftrag nicht erneut berechnet; aus dem alten Ergebnis wird kein Lightning-Verbrauch behauptet.
