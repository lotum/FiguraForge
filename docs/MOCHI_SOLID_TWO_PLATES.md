# Mochi · Braun/Beige ohne Mixed · 17.10.2026

**Korrektur vom 18.10.:** Die alte Zwei-Platten-Datei konnte beim nativen Speichern die Nase mit der Körpergeometrie verwechseln. Die Körperplatte bleibt der gute gedruckte Stand. Für schwarze Details und neue Exporte ausschließlich die [korrigierten Dateien und Nachweise](MOCHI_USER_EDITION.md) verwenden. Der folgende Bericht erhält den früheren Prüfstand; die damaligen CLI-Tests deckten diesen Speicherfehler nicht auf.

[**Ein natives H2D-Projekt mit beiden Platten**](../benchmarks/mochi-solid-production/Mochi-Braun-Beige-H2D-2-Platten.3mf)

| Platte | Inhalt | Filamente | Prozess |
|---|---|---|---|
| 1 | Körper einschließlich Kopf, Ohren, Beine und Schwanz; 180 mm | Slot 1: ELEGOO PLA Matte Earth Brown, Bestand 29; Slot 2: Bambu PLA Basic Beige, Bestand 31 | 0,16 mm, Lightning 5 %, 2 Wände, automatische Baumstützen 20°, Spülturm |
| 2 | Schwarze Stecknase und vier schwarze Augeneinsätze | Slot 3: eSUN ePLA-Lite Black, Bestand 30 | 0,12 mm als Objektüberschreibung; drei Raftschichten, Baumstützen, getrennte sichere Positionen |

Keine virtuellen Filamente, keine Mischrezepte, `enable_mixed_color_sublayer=0`.
Beide ursprünglichen Braun-Materialklassen sind Braun; die ursprüngliche helle Klasse ist Beige. Klassifikation gegen die originalen Albedo-Materialfarben, nicht gegen die tatsächlichen Spulen-HEX: Andernfalls könnten helle anatomische Bereiche fälschlich Braun werden. Neue Innenflächen des Körpers bleiben Braun. Es gibt keine zusätzlichen Druckfarben für Texturschatten.

[Ansichten von vorn, schräg und hinten](../benchmarks/mochi-solid-production/build-f27e2b682e094abeac68fb0cb90c36e9/Mochi-Braun-Beige-Vorschau.png) zeigen dieselben nativen Flächenfarben. HEX-basierte Anzeige und Beleuchtung sind unkalibriert.

## Import und Druck

1. In Bambu Studio **Datei → Projekt öffnen** und die oben verlinkte Datei öffnen; als Projekt mit Einstellungen laden.
2. Platte 1 enthält den Körper, Platte 2 die fünf schwarzen Details. Eine gewünschte Platte wählen.
3. H2D mit 0,4-mm-Düsen sowie die tatsächlichen AMS-/Düsenzuordnungen prüfen: Körper Braun links/Beige rechts; bei Platte 2 Schwarz dem rechten Extruder zuordnen. Die Projekt-Slots sind keine fest zugesagten AMS-Fachnummern.
4. Gewählte Platte slicen und die Vorschau prüfen. Der Agent sendet keinen Druckauftrag.

Die zweite Platte ist optional für den neuen Körper: Die vorhandenen schwarzen Teile passen geometrisch auch zur bereits gedruckten Mixed-Version. Die Nase hat denselben Stift und dasselbe 0,05-mm-Spiel; die Augen bleiben Klebeeinsätze.

## Bestehende Mixed-Version bleibt erhalten

- [Mixed-Körper, 20 Farbwerte](../benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c/Mochi-Koerper-20-Farben-H2D.3mf)
- [**Noch benötigte schwarze Details der Mixed-Version**](../benchmarks/mochi-unified-production/build-83f51796f58841c7be1371687fbe528c/Mochi-Schwarze-Details-H2D.3mf)
- [Bisherige Anleitung und Nachweise](MOCHI_UNIFIED_PRINT.md)

Alle alten 3MF-Dateien und sechs NPZ-Teile wurden vor/nach dem Aufbau über SHA256 unverändert bestätigt. Keine Originale, Projekte oder Freigaben ersetzt; keine Anbieteraufrufe oder Druckersends.

## Tatsächliche Verifikation

**510 Python-Tests bestanden, 0 Fehler, 39,91 Sekunden.** [JUnit](test-results-mochi-solid-two-plates.xml). Drei neue Regressionen prüfen Zwei-Platten-Zuordnung, unveränderte Mesh-Payloads, Prozessüberschreibungen, den nativen XML-Namespace und die reine Zweifarbenzuordnung.

[Maschinenlesbarer Nachweis](mochi-solid-two-plates-verification.json) bindet die finale Datei-SHA an beide tatsächlich gesliceten Platten und deren G-Code-SHAs.

- Sechs identische Geometrien, zusammen 308.152 Dreiecke. Maximaler numerischer Weltkoordinatenunterschied gegenüber dem Mixed-Export unter 1e-12 mm nach Abzug des nativen zweiten Plattenursprungs.
- Bambu Studio 02.07.01.62 CLI: `--slice 1` und `--slice 2` auf **derselben** finalen Projektdatei, beide Exit 0 / Result 0. Nur Veröffentlichungskontrollen deaktiviert, niemals `--no-check`.
- Native Import-/Exportprüfung: Flächenfarben und Dreiecksindizes unverändert; Weltkoordinaten nach Slicerexport maximal 4,1e-7 mm abweichend. Der CLI-Sliceexport enthält jeweils die gewählte Platte; das Eingangsprojekt enthält beide. Die CLI vereinheitlicht zur Laufzeit `filament_prime_volume` von `[45,30,45]` auf `[45,45,45]`; alle übrigen Projekteinstellungen bleiben gleich.
- Vollständige unabhängige Extrusions-Footprintprüfung einschließlich G17-I/J-Bögen: **3.030.926 Segmente**, beide Platten ohne Owner-Überschneidungen. Alle extrudierten Owner-Footprints liegen innerhalb des gemeinsamen H2D-Bereichs X25–325 / Y0–320 mm.
- Körperprognose **13 h 18 min 45 s / 196,11 g**, schwarze Details **10 min 48 s / 0,44 g**. Gesamt etwa **13 h 30 min / 196,55 g** einschließlich Slicerzusätzen. Keine Laufzeit-/Materialgarantie.

GUI-Import dieser neuen Datei und physischer Zweifarbdruck sind noch nicht abgenommen. Nutzer meldet die erhaltene Mixed-Körperversion bereits als gut aussehend; ihr Druck war zum Rückmeldezeitpunkt noch nicht abgeschlossen. Schwarze Details waren noch nicht gedruckt. Keine neue physische Montagefreigabe.

## Reproduzierbarkeit und Geltungsbereich

`scripts/build_mochi_unified_template.py --solid-only` erstellt mit der nativen CLI drei passend dimensionierte physische Profile. `scripts/build_mochi_solid.py` lädt ausschließlich die gespeicherten sechs fertigen Teile und schreibt einen neuen Exportordner. `native_plates.merge_two_native_plates` kombiniert die kompatiblen nativen Einzelplatten, nummeriert Objekt-/Plattenbezüge neu, erhält Mesh-Payloads und legt die zweite Platte auf den von Bambu verwendeten 420-mm-Rasterabstand. Veraltete Thumbnails/G-Code-Caches werden im **neuen Archiv** nicht übernommen. Ein erster ungültiger Entwicklungsversuch mit XML-Namespacepräfixen bleibt als unfreigegebener Benchmark erhalten; nur die oben verlinkte finale Datei ist geprüft.

Die neue Hilfsfunktion ist für zwei kompatible native H2D-Platten geprüft. Eine allgemeine Ein-Datei-Ausgabe aller Projekte mit beliebig vielen Platten ist noch keine zugesagte Funktion der Weboberfläche.
