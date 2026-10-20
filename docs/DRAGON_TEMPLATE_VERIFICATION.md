# Prüfung der bereitgestellten H2D-Mischvorlage

## GUI-Abnahme am 16. Oktober 2026: Mixed-Würfel bestanden

Nach Richards ausdrücklicher Freigabe zum Verwerfen der ungespeicherten
Bambu-Änderungen wurde der native Export in Bambu Studio 02.07.01.62 geöffnet,
als neue Datei gespeichert und tatsächlich gesliced. Die älteren Abschnitte
zur noch fehlenden GUI-Abnahme beschreiben den Stand vor dieser Prüfung.

**Import, nativer Save-Roundtrip und Slicing für den 85/15-Testwürfel bestanden.**
Die acht Mischrezepte bleiben nach dem GUI-Speichern erhalten. Der exportierte
G-Code enthält 59 Unterschichten mit 0,17 mm und 59 mit 0,03 mm: zusammen
0,20 mm mit 85/15-Aufteilung. Gedruckt wurde nicht; physische Farbwirkung und
Montage sind damit nicht abgenommen.

Die GUI-Prüfung fand zwei zuvor vom Geometrievergleich nicht erfasste Fehler:

- CLI-Konvertierung lieferte `printable="0"` → der Builder setzt die Markierung
  erst nach erfolgreicher Prüfung gegen den echten gemeinsamen Düsenraum und
  ergänzt die native Platten-Instanzzuordnung.
- Ein allgemeiner XML-Neuaufbau entfernte das ungenutzte Bambu-Namespace und
  wurde von der GUI als fremdes 3MF interpretiert → das Hauptmodell bleibt
  bytegetreu bis auf gezielt ersetzte Printable-Attribute.

Die echte H2D-Vorlage besitzt einen gemeinsamen Düsenraum **X 25–325,
Y 0–320, Z 0–320 mm**. FiguraForges normaler 300-mm-Packrahmen beginnt bei X=0;
native Platten bekommen deshalb eine dokumentierte Verschiebung um +25 mm X.
Der Builder prüft danach reale Polygone, Höhen und Ausschlussbereiche und
weist unpassende Teile ab. Core-Begleiter behalten ihren normalen Packrahmen.

Belege: [maschinenlesbare GUI-/G-Code-Prüfung](bambu-mixed-gui-verification.json),
[echte Slicer-Vorschau](../screenshots/bambu-mixed-sliced-macos.png).
Dateien liegen lokal unter `benchmarks/mixed-filament-native/`:
`dragon-profile-cube-printable.3mf`, `dragon-profile-cube-gui-roundtrip.3mf`,
`dragon-mixed-gui-verification.gcode`. Das G-Code-File ist ein Prüfbeleg,
keine pauschale Druckfreigabe für andere Figuren oder Spulen.


Stand: 16.10.2026. Vom Nutzer ausdrücklich bereitgestellte Datei `Dragon_Head_and_Hands_FINAL.3mf` ausschließlich lesend geprüft. Original nicht verändert. Keine privaten Zusatzbilder geöffnet, kopiert oder angezeigt; kein Upload, Druck- oder kostenpflichtiger API-Auftrag.

## Verifizierte Metadaten

| Merkmal | Befund |
|---|---|
| Druckermodell | Bambu Lab H2D |
| Düsen | 2 × 0,4 mm |
| Filamentslots | 11 insgesamt: 3 physische, 8 Mischslots |
| Basis 1 | Generic PLA, `#08B690` |
| Basis 2 | Bambu Lab PLA, `#F7E6DE` |
| Basis 3 | Bambu Lab PLA, `#A0EC5E` |
| Mischslots 4–11 | Basis 1 und 2: 85/15, 75/25, 65/35, 55/45, 45/55, 35/65, 25/75, 15/85 |
| Native Z-Gradienten | Alle deaktiviert |
| Großes Originalmodell | 314.282.276 Byte XML, 3.099.242 Dreiecke |
| Weiteres Originalmodell | 139.936.413 Byte XML, 1.393.844 Dreiecke |

Die vorherige pauschale Grenze von 256 MB je eingelesener Datei war für eine reine Vorlagen-Metadatenprüfung ungeeignet. Der Import liest jetzt kleine Konfigurationsdaten begrenzt und zählt Modelldreiecke mit einem stromweise arbeitenden XML-Parser. Laufzeit am vorhandenen Original: **8,35 Sekunden**. Private Auxiliary-Dateien werden nur anhand des ZIP-Verzeichnisses auf sichere Pfade geprüft; ihre Inhalte werden nicht gelesen.

Sicherheitsgrenzen: maximal 4096 ZIP-Einträge, 4 GB deklarierte Gesamtgröße, 2 GB je gestreamtem Modell, 8 MB je relevanter Konfiguration, 120 Sekunden für Modellstatistik. Doppelte/unsichere Pfade, Symlinks, Verschlüsselung und XML-DTD/Entity-Deklarationen werden abgelehnt. Es erfolgt keine Archivextraktion.

## Kleine lokale Profilvorlage

`data/native-templates/h2d-dragon-profiles-only.3mf`, **14.494 Byte**: vollständige vorhandene Projekteinstellungen mit den echten Drucker-/Filamentprofilwerten, leere neue Modellstruktur. Keine Originalgeometrie, keine ursprünglichen Objektzuordnungen, keine privaten Auxiliary-Inhalte. Drucker-/Filament-G-Codes werden als lokale Profilkonfiguration erhalten; die UI-Vorschau gibt diese nicht aus. Sie werden durch die Importprüfung nicht ausgeführt.

Das Original dient damit als lokale Profilquelle. Neue Exporte verwenden ausschließlich eigene neue Geometrie und neue Objektzuordnungen.

## Echter neuer Würfel mit diesen Profilen

Datei: `benchmarks/mixed-filament-native/dragon-profile-cube.3mf`; Prüfbericht `dragon-profile-cube-result.json` daneben.

- Neues Würfelteil, zwölf Dreiecke; alle Flächen explizit dem vorhandenen Mischslot 4 (85/15) zugeordnet.
- Die installierte Bambu-CLI konvertierte zunächst neue Geometrie ohne Mischslots ins native Format. Anschließend wurden echte Vorlagenkonfiguration und native Flächenbemalung übertragen.
- Geordnete Dreieckskoordinaten: **0 mm Abweichung**.
- Unabhängige Weltkoordinatenprüfung: **0 mm Abweichung**.
- Vorhandene Ausgabe- oder Originaldateien werden nicht überschrieben.

**Grenze:** Dies bestätigt die native Geometriekonvertierung und das Schreiben der echten Profile/Bemalung. Die finale Mischdatei ist noch nicht durch die Bambu-GUI gespeichert/gesliced worden. Der Standard-CLI-Import eines bereits gemischten Projekts wird von der installierten Version mit `mixed filament is not supported` abgelehnt. Deshalb bleiben `native_roundtrip_verified: false`, `slicing_verified: false`, `gui_verification_required: true`. Kein physisches Farbergebnis zugesichert.

## Vorhandene Rezepte und gewünschte 5%-Bibliothek

Die Vorlage enthält acht echte Mischrezepte in 10%-Abständen, keine vollständige 17-Rezept-Bibliothek in 5%-Abständen. Diese acht Rezepte sind ohne erfundene Profile verwendbar; eine Abweichung von der gewünschten Mischstufe muss sichtbar bleiben.

Das konkrete Projekt enthält **108 Arrays mit 11 Einträgen**, **45 Arrays mit 22 Einträgen** (Filament-/Düsenkombinationen) und eine Spülmatrix mit **242 Einträgen** (`2 × 11²`). Weitere Profilgruppen besitzen 13 Einträge. Deshalb wäre es fehlerhaft, nur `filament_*`-Felder oder nur Arrays der Länge 11 zu duplizieren. Eine Erweiterung auf 17 Mischrezepte muss sämtliche nativen Düsen-, Profil- und Spülstrukturen konsistent erweitern und anschließend in der GUI geprüft werden. Diese Erweiterung wird hier ausdrücklich nicht als abgeschlossen ausgegeben.

## Automatisierte Prüfung

28 Tests im Modul bestanden, darunter Schutz vor Überschreiben, Ratio-/Hardware-/Slotprüfung, Teilgrenzen, Native-Dreiecksbemalung, sichere Vorlagenpfade, Verweigerung von DTDs sowie ein expliziter Test, dass private Auxiliary-Bilder beim Import und Erzeugen der kleinen Profilvorlage nicht geöffnet werden.

## Nachprüfung: druckbare Plattenzuordnung

Die anschließende echte GUI-Prüfung bestätigte das native Projekt und das 85/15-Rezept, zeigte jedoch zunächst eine leere Slice-Vorschau. Die Geometrie allein war korrekt, die Plattenzuordnung nicht: Der CLI-Konverter hatte `build/item printable="0"` ausgegeben und kein `plate/model_instance` zugeordnet. Außerdem lag der frühere Würfel bei X=24–36 mm zwar auf dem gesamten H2D-Bett, aber 1 mm außerhalb des rechten Düsenbereichs.

Die echten Vorlagenbereiche sind links X=0–325 mm, rechts X=25–350 mm, jeweils Y=0–320 mm. Für die hier gewählte Zwei-Düsen-Strategie gilt der gemeinsame Bereich **X=25–325, Y=0–320, Z=0–320 mm**. Gesamtbettgröße allein reicht daher nicht zur Freigabe.

Der Builder prüft nun vor dem Export Weltkoordinaten, beide Düsenpolygone, Bauhöhe und Bett-Ausschlussbereiche. Erst danach setzt er die konkreten nativen Builditems auf druckbar und schreibt je Objekt `model_instance` mit `object_id`, `instance_id=0`, `identify_id`. Die Form folgt dem offiziellen `bbs_3mf.cpp`-Serializer. Unsichtbare/unnötige Namespace-Deklarationen im nativen Hauptmodell werden dabei **bytegetreu erhalten**: eine vollständige ElementTree-Neuserialisierung könnte den nativen Bambu-Marker entfernen und einen Geometrieimportdialog auslösen.

Neue getrennte Prüfdatei: `benchmarks/mixed-filament-native/dragon-profile-cube-printable.3mf`, Würfel bei X/Y=44–56 mm, Z=0–12 mm, Metadaten für eine druckbare Instanz, Koordinatenfehler 0 mm. Die GUI-Slice-Prüfung dieser korrigierten Datei ist noch separat zu bestätigen; es wird keine abgeschlossene Druckabnahme behauptet.

`native_bed_bounds(settings)` liefert den echten gemeinsamen Ursprung und die verfügbaren Ausdehnungen. Ein im Pack-Koordinatensystem ab X=0 geplantes 300-mm-Feld kann für den nativen Export um **+25 mm X** übersetzt werden. Es wird nicht skaliert; die Core-Begleitdatei behält ihren dokumentierten Packrahmen. Jede übersetzte native Platzierung wird erneut geprüft.

35 Modultests bestanden, zusätzlich zu den bisherigen Tests jetzt inklusive außerhalb liegender Düsenbereiche, negativer/zu großer Höhe, Bett-Ausschlussfläche, nativer Platteninstanz und bytegetreuem Erhalt ungenutzter Bambu-Namespaces.
