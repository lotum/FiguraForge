# Testbericht - FiguraForge 0.1.0 mit Mac-Korrekturen

## Mochi · Halskonstruktion 500/470 mm · 18.10.2026

Geschwungene Trennung an der geometrischen Einschnürung, breite Kopfauflage, separater asymmetrischer 20×28×36-mm-Schlüssel. Acht geschlossene Teile auf drei nativen H2D-Platten; Richards ursprüngliche Bemalung einschließlich aller 1.034 komplex bemalten Dreiecke erhalten. 500 und 470 mm tatsächlich geslicet und mit vollständigen Extrusions-Footprints geprüft. Zweimaliges natives Speichern erhält alle acht Teile/Farbcodes. 514 Python-Tests und beide Frontend-Harness bestanden. Reale Hals-Passung noch offen; zusätzliche kleine Probe mit gleichen Materialien/Schichthöhen vorhanden. [Dateien, Montage, Größen und Grenzen](MOCHI_NECK_SPLIT.md), [Nachweis](mochi-neck-split-verification.json). Kein Druckstart, Originale erhalten.

## Mochi · neue Nutzerfassung und Großformatprüfung · 18.10.2026

Richards gedruckte 180-mm-Körperplatte und Farbkorrekturen unverändert gesichert; eigenes FiguraForge-Archivprojekt. Schwarzer Körper anstelle der Nase auf Platte 2: kollidierende Ressourcenkennungen im nativen Mehrdateiformat behoben, zwei tatsächliche native Speicher-/Ladedurchläufe erhalten alle sechs richtigen Teile. Neue 320-mm-Zweidüsen- und 325-mm-Rechtsdüsen-Dateien erfolgreich geslicet; alte Datei bleibt erhalten, ihre beschädigte zweite Platte nicht verwenden. [Dateien, Bauraum, Nachweise und Grenzen](MOCHI_USER_EDITION.md).

## Neuester Zweifarbenlauf · 17.10.2026

Gleiche sechs fertigen Mochi-Teile, Körper nur Braun/Beige ohne Mixed, fünf schwarze Details auf Platte 2 **derselben nativen 3MF-Datei**. 510 Python-Tests bestanden. Beide Platten tatsächlich gesliced und 3.030.926 vollständige Extrusions-Footprints geprüft; bestehende Mixed-Dateien und Geometrien per SHA unverändert. Prognose gesamt ca. 13 h 30 min / 196,55 g. [Datei, Importanleitung und Grenzen](MOCHI_SOLID_TWO_PLATES.md), [Nachweis](mochi-solid-two-plates-verification.json). GUI-/physische Abnahme der neuen Variante offen; kein Druckstart.

## Neuester Mochi-Einteillauf

**507 Python-Tests bestanden, 0Fehler, 55,38Sekunden**, [aktuellesJUnit](test-results-mochi-unified-final.xml); beideFrontend-Harness grün. Sechs geschlossene Teile / zwei native Platten, nur Schwarz separat. Alle20 Farbwerte auf dem ganzen Körper tatsächlich verwendet. Beide tatsächlichen Slices und4.272.941 vollständige Extrusions-Footprints bestanden, aktuelle Datei-/GCode-SHAs gebunden. GemeinsameH2D-Fläche geprüft, Lightning5%/2Wände/Rezeptdaten nachSlice erhalten. Prognose **32,9439h/329,73g**. [Anleitung](MOCHI_UNIFIED_PRINT.md), [Kopfprüfung](mochi-unified-head-verification.json), [Printnachweis](mochi-unified-print-verification.json). Native GUI-/physischeAbnahme bleibt offen; kein Druckstart. Folgende Abschnitte erhalten den früheren Drei-Figuren-Stand.


## Aktueller Integrationslauf

**498 Python-Tests bestanden, 0 Fehler, 39,42 Sekunden**. [JUnit-Protokoll dieses eingefrorenen Codezustands](test-results-current-mac-final.xml). Frühere Protokolle bleiben erhalten. Beide Node-Harness bestehen: `frontend_color_plan_regressions.mjs` und `frontend_workflow_regressions.mjs`, einschließlich initial gesperrter Bedienung beim Laden, Demo-Rennbedingung, veralteter Pollingantworten, Buddy-Standardvorausfüllung, 68 Passungsschlüsseln und abgelaufenen KI-Vorschlägen. Die getrennten tatsächlichen Buddy-Slice-/Vollpfad-/Main-Paritätsprüfungen sind ebenfalls abgeschlossen; Softwaretests ersetzen keine physische Gesamtabnahme.

Der aktuelle Lauf umfasst echte Solid-only-Vorlagen-/API-Grenzen, obligatorische Mixed-Rezeptprüfung, H2D-Hardwareguard, explizite Turmprozessabweichungen, Buddy-Source-/1000-mm-/Y-up-/Worker-/Exportdispatch und den G17-Kreisbogenprüfer. Eine neue Exportregression bestätigt Pips geordnete `assembly_instructions_de` in `MONTAGE.md`, Native-3MF-Vorrang und den Hinweis auf fehlende physische Gesamtabnahme. Unit-/Integrationstests ersetzen keine neue tatsächliche Character-Sliceprüfung; die realen Mochi-/Pip-G-Code-Nachweise stehen getrennt im Bericht.

## Aktuelle Zuordnung der Character-Nachweise

| Figur | Aktueller Stand und Beleg | Ausstehend |
|---|---|---|
| Mochi V2 | Normaler Mainexport `fe198e03f321491d99af56a50994001c`, 9 Teile / 7 Stifte / 5 native Platten. Alle fünf tatsächlichen Dateien mit Weltgeometrie, Flächenfarbcodes, vollständigen Projekteinstellungen und Datei-SHAs gegen den bereits gesliceten Stand geprüft. [Aktueller Nachweis](mochi-v2-current-native-parity.json). | Reale Farben, Gesamtdruck, Klebe-/Steckmontage. |
| Pip | Aktueller normaler Mainexport `6d0006dece3e44bda76bcd1e9ff9a810`, 10 Teile / 16 Stifte / 10 Platten. Alle zehn tatsächlichen Dateien nach Farb-/Source-Ownership-Korrektur neu gesliced und unabhängig geprüft. [Aktuelle Slices](pip-main-native-slice-verification.json), [aktuelle Extrusions-Footprints](pip-main-gcode-footprint-verification.json). | Physische Montage, Stützentfernung und Farbwirkung. Frühere Pip-Berichte bleiben historische Belege. |
| Buddy | Regulärer Mainlauf `8ae358614600412b95e801d4c80f28cf` erfolgreich: 37 geschlossene Teile / 34 Platten / 68 Passungsschlüssel / 32 Schnittstellen, 0,05 mm. Finaler Plan `f3428…` mit 1.058 gezielten Materialkorrekturen, alle Spulen-IDs erhalten. Alle 34 ausgewählten finalen Referenzplatten haben Slice-PASS. | 34/34 volle Extrusions-Pfadprüfungen und 34/34 tatsächliche Main-XML-/Paint-/Settings-Abgleiche bestanden. Bambu-Desktopprüfung wegen gesperrtem Mac separat offen; Großmontage, Statik und Farben offen. |

Alle Materialfarben und Mixed-Vorschauen sind unkalibrierte Annäherungen. Pips vorhandenes Grün ist blasser als die Referenz, Buddys Wood-Filament matter. Diese bewussten Bestandskompromisse sind keine gemessene Farbfreigabe. Kein Druckauftrag wurde durch den Agenten gestartet.

## Buddy: regulärer Mainlauf und letzte Materialkorrekturen

Der normale UI-Auftrag `8ae358614600412b95e801d4c80f28cf` ist erfolgreich abgeschlossen: 37 geschlossene Teile, 34 Platten, 68 Passungsschlüssel an 32 Schnittstellen und 0,05 mm radiales Spiel. Der regulär gespeicherte Plan `f3428…` erhält alle zuvor gewählten realen Spulen-IDs. Der endgültige normale Mainexport `37f366df5b7241c6b98ca1507b02788c` besteht für alle 34 tatsächlichen nativen Platten den vollständigen XML-/Weltgeometrie-/Flächenfarb-/Settings-/Extruderabgleich. Root hat den tatsächlichen ZIP-SHA256 unabhängig bestätigt. [Main-Parität](buddy-main-native-parity.json).

**Alle 34 final ausgewählten Platten haben tatsächliches Slice-PASS und vollständiges unabhängiges Extrusions-Footprint-PASS.** Die [zusammengeführte Nachweiskette](buddy-main-gcode-footprint-verification.json) bindet tatsächliche GCode-Hashes an die finale Main-Parität und den Paket-SHA256. CLI-Exit0 allein wird ausdrücklich nicht als Pfadfreigabe verwendet. Aktuelle Slicerprognose: **1.042,93 Stunden / 25,328 kg**, entsprechend etwa **43,46 Tagen** serieller Druckzeit. Das ist ein rechnerischer Bedarf einschließlich Slicerzusätzen, keine Laufzeitgarantie und keine Statik-, Last- oder Montagefreigabe. Kein Druckstart.

Quellgebundener Materialvergleich gegen den erhaltenen vorherigen Plan: **genau 1.058 geänderte Flächen**, davon 1.053 Gold→Braun auf Lederlichtern und fünf Braun→Gold im Emblem. Geometrie und anatomische Masken sind unverändert. Große echte Fellbereiche, Sondermaterialgrenzen, Brauen, Augen und Nase bleiben geschützt. Das Emblem verwendet eine Goldfarbe: Ring, Aufhängung und Facetten sind echte Meshgeometrie und liefern natürliche Schattierung. Der zusätzliche Kontrast der Originalalbedo wird nicht versprochen; physische Farbwirkung ist ungeprüft.

[Leder-/Front-/Emblem-A/B und Bericht](../benchmarks/buddy-material-islands-review/REPORT.md), [beleuchteter Vergleich](../benchmarks/buddy-material-islands-review/emblem-source-brown-gold-lit.png), [exakte 1.058-Flächen-/Quell-/Code-Fingerabdrücke](../benchmarks/buddy-material-islands-review/gold-emblem-implementation-verification.json). Die 34 gezielten Tests dieses Materialschritts sind im separaten Beleg dokumentiert und im späteren vollständigen Integrationslauf ergänzt.

## Pip: aktueller normaler Export digital geprüft

Die zehn nativen Dateien aus `runs/6d0006dece3e44bda76bcd1e9ff9a810/export` haben tatsächlich CLI-Exit 0 / Result 0 erreicht. Native- und G-Code-SHAs wurden den konkreten Dateien zugeordnet. Die unabhängige Prüfung liest 5.668.791 Extrusionssegmente einschließlich 843.778 Druckbögen; keine nicht unterstützten Druckbögen, alle Objekt-/Turm-XY-Footprints einschließlich Linienbreiten und Bogenfehler getrennt. Der ältere Nachweis mit 5.671.524 Segmenten gehört ausdrücklich zum vorherigen Farbplan.

Slicer-Gesamtprognose: **35 h 27 min / 505,01 g**. Davon weist der Slicer 299,88 g als Hauptverbrauch und 205,14 g als zusätzlichen Bedarf aus. Das ist kein gemessener realer Verbrauch und keine physische Gesamtabnahme. Die aktiven Slicer-/Geometrieprüfungen wurden nicht ausgeschaltet; allein die MakerWorld-Publikationsprüfung ist deaktiviert. Kein Druckersenden und kein Druckstart.

Die Material-Snapshots aller drei Hauptprojekte wurden unabhängig mit dem tatsächlichen Bestand abgeglichen. Für Pip sind zusätzlich die aktuellen zehn nativen Dateien und G-Codes per SHA geprüft. Diese Material- und Dateibindung ist keine physische Farb- oder Gesamtmontagefreigabe.

## Neue physische Rückmeldung: 0,05 mm radial bestätigt

Die vier Nasenproben sind gedruckt. Richard meldet: 0,20/0,15/0,10 mm zu lose,
0,05 mm gerade steckfest mit leichtem Restwackeln, für größere Steckteile akzeptiert.
Buddy, Mochi und Pip verwenden nun **0,05 mm radial**; vorherige Projektstände
sind separat gesichert, neue Konstruktionen werden erneut berechnet.
[Zuordnung, Bedingungen und Grenzen](FIT_CALIBRATION.md). Dies ist keine physische
Freigabe aller Figurenteile oder aller Materialien. Kein Druck durch den Agenten.

## Neue optionale Pip-/Buddy-Passungsplatte

**Neue Version nach Taperkorrektur:** Buddy erreichte den Nennradius vorher erst 2 mm hinter der echten Wurzel. Kern und Querschnittsregression sind korrigiert; die neue native Datei ist an den korrigierten Kernel gebunden. Die zurückgezogene erste Version bleibt erhalten.

Vier neue beschriftete Paare mit 0,05 mm radial: Buddy keyed 12 × 10 und 4 × 6 mm, Pip rund Ø 1,8 × 1,5 und Ø 2,4 × 2,5 mm. Acht geschlossene zusammenhängende Körper, Stifte aufrecht, Taschen offen nach oben, keine innere Stütze. Echte native H2D-Datei plus CLI-G-Code: 0,12-mm-Layer, Beige 31, 54:46 min / 12,51 g, ausschließlich Slot 2. Unabhängige Prüfung von 34.306 Extrusionssegmenten ohne Owner-Footprintüberlappung; vier gezielte Geometrie-/Profilregressionen bestanden. [Dateien und Testanleitung](PIP_BUDDY_FIT_PLATE.md), [Hash-/Slicenachweis](pip-buddy-fit-plate-verification.json).

Kein Druck gesendet, physische Rückmeldung offen. Unterschiedliche Formen und Größen werden aus der Mochi-Nasenprobe nicht als automatisch passend abgeleitet.

## Mochi V2 im regulären UI-Ablauf verifiziert

Neue augengeschützte Arbeitskopie mit weiterhin 150.000 Dreiecken, versionierter
Übernahme und erhaltenen Originalen. Tatsächlich im normalen UI gebaut/exportiert:
9 geschlossene Teile, 7 Stifte, 4 explizite Klebeaugenteile, 5 Platten, 0,05 mm radiales
Spiel. Von vorn und gedreht am Modell angesehen. Aktueller UI-Export
`runs/fe198e03f321491d99af56a50994001c/export` stimmt für alle fünf nativen
Platten in Weltvertices, Dreiecksfarben und vollständigen Projekteinstellungen
mit dem bereits gesliceten Prüfstand überein. [Aktuelle Datei-SHAs und Parität](mochi-v2-current-native-parity.json).
Der frühere UI-Export `runs/1193d7be224742cd92134900f1124ece/export` und dessen
[ursprünglicher Paritätsnachweis](mochi-v2-main-native-parity.json) bleiben als Basisbeleg erhalten;
[ausführlicher Bericht](MOCHI_DETAIL_V2_RUN_REPORT.md).

Alle fünf Platten wurden mit dem installierten Bambu-Slicer tatsächlich in G-Code
umgewandelt. Gesamtprognose: 31:59:57 h / 337,33 g inklusive Spülen/Stützen. **CLI-Exit 0
ist keine Pfadkonfliktfreigabe:** Die in der GUI nachweislich konfliktbehaftete
alte v1-Platte ergibt in einer Negativkontrolle ebenfalls Exit 0. Die eigene
Pfadprüfung ist abgeschlossen: 2.766.148 tatsächliche Extrusionssegmente aller fünf Platten, Linienbreiten-erweiterte Owner-XY-Bounds einschließlich Stützen und Spültürmen disjunkt. Die bekannte problematische GUI-v1-Datei wird in der unabhängigen Negativkontrolle erkannt. Das ist keine vollständige Düsen-/Dynamik-/physische Zertifizierung. [Nachweis](mochi-v2-extrusion-footprint-verification.json). Die negative CLI-Bbox-Z-Anzeige gedrehter Teile ist eine
AABB-Rechnung; unabhängige rekursive native XML-Prüfung zeigt alle echten
Weltvertices auf/über dem Bett und unverändert nach dem Slice. Keine
Abschneidung aus diesen Bbox-Zahlen ableiten. Physische Gesamtmontage und
Mixed-Farbwirkung bleiben offen; kein Druck durch den Agenten.

Zusätzliche UI-Korrekturen: quellgebundene Geometrien ohne generische
Refinement-Prognose rendern wieder; verspätete Pollingantworten können einen
gerade gestarteten Auftrag oder eine neuere Revision nicht mehr verdrängen.
Node-Workflowregressionen bestehen einschließlich beider Status-Rennbedingungen.

## Neuer GUI-Befund: Stützpfade zwischen Mochi-Teilen kollidieren

Der normale native Mochi-V1-Export mit 0,05 mm Spiel wurde tatsächlich in Bambu
Studio gesliced: 8.545 Mixed-Unterschichten, 179,60 mm, 237 g, geschätzt 25:15 h.
Braun und Beige werden den zwei Düsen zugeordnet. **Nicht druckfreigegeben:**
Bambu meldet einen ernsten G-Code-Pfadkonflikt bei Layer 3310 zwischen Schwanz
und Körper. Geschlossene Einzelteile und reine Mesh-Abstände reichen für den
Abstand der automatisch erzeugten Baumstützen nicht aus. Der neue V2-Entwurf
trennt deshalb Körper, beide Ohren und Schwanz auf eigene Platten; die schwarzen
Details liegen auf einer weiteren Platte. Die erneute GUI-Abnahme läuft.
Screenshot und fehlerhafter G-Code sind separat als Benchmark erhalten; kein
Druckstart. Dieser Befund schränkt die frühere Zwei-Platten-Konstruktion unten ein.

## Aktuellster Nachtrag: regulärer Character-Workflow und Passungsvergleich

**381 Python-Tests bestanden in 24,63 Sekunden**, [JUnit](junit-current.xml),
zusätzlich Node-Frontendregressionen bestanden. Prozess-/Material-/Worker-Integritätsprüfungen sind in diesem Lauf enthalten.

- **Nasenvergleich:** vier neue Paare mit 0,05/0,10/0,15/0,20 mm radialem Spiel,
  senkrechten Stiften und Taschen. Tatsächliche Bambu-GUI-Abnahme der endgültig
  gespeicherten Datei: 55 Schichten, 4,95 g, 36:34 min, ausschließlich Slot 2 Beige.
  Raft 3 und Stützen bleiben beim GUI-Import erhalten. G-Code-Nachweis: pro Nase
  524 Stützextrusionsbewegungen innerhalb der Nasen-XY-Grenze vor dem ersten
  Modellmaterial bei Z 1,02 mm. Richard hat den Druck selbst gestartet und die Passungen zurückgemeldet; kein Druckauftrag
  durch den Agenten. [Sliceransicht](../screenshots/nose-fit-four-clearances-supported-macos.png).
- **Mochi:** lokaler anatomischer Vorschlag im normalen Farbplan verfügbar, nach
  Prüfung speicherbar; freier Plan weiterhin verfügbar. Normaler UI-Konstruktionslauf
  erfolgreich: 9 geschlossene Teile / 7 Stifte / 2 nach realen Spulen gruppierte
  Platten. Unveränderliche Konstruktionsreferenz bleibt von der Farbkorrekturreferenz
  getrennt. Die Profilvorlage verwendet tatsächliche Brown/Beige/Black-Spulenfarben,
  offizielle lokale Generic-PLA-/Bambu-PLA-Profile als unkalibrierte Startprofile.
  Nase/kleine Augen separat schwarz; Körper/Ohren/Schwanz Beige+Braun mit berechneten
  Flächenrezepten. Neue verdeckte Nasentaschenflächen übernehmen kein falsches Schwarz.
  [Ausführlicher Laufbericht](MOCHI_RUN_REPORT.md).
- **Filamentschritt:** anatomische Mixed-Teile behalten beide geplanten Basisfilamente;
  Einzelzuordnung kann den Verlauf nicht unbemerkt ersetzen. Drei echte Spulen werden
  auf getrennte Platten verteilt. Die Vorschau behält lokale Flächenfarben.
- **Pip:** genau ein freigegebener Meshy-Auftrag, tatsächlich 30 Credits. Provider-Mesh
  war topologisch ungültig; neue lokale Reparaturkopie ist geschlossen und behält
  identische dekodierte Texturpixel. Import/Inspect im Hauptprojekt bestanden.
  Anatomische Konstruktion und Materialabnahme laufen noch. [Pip-Bericht](PIP_RUN_REPORT.md).
- **Buddy:** anatomische Schnitte und Bauraumteilung in Bearbeitung. Geometrisch gültige
  Zwischenteile sind ausdrücklich noch keine bestandene Material-/Slicerabnahme.
  [Buddy-Bericht](BUDDY_RUN_REPORT.md).

Zusätzliche UI-Nachprüfung: `node tests/frontend_workflow_regressions.mjs`
besteht. Strukturkacheln explodieren auseinander; Statusabfragen verbinden sich
nach Unterbrechungen erneut; späte Antworten überschreiben keinen Projektwechsel.
Ein unveränderter validierter Farbplan behält bestehende Konstruktionen, auch
bei erneutem Speichern. Vor abhängigen Schritten werden geänderte Entwürfe
validiert und gespeichert; Rücknavigation erhält unfertige Entwürfe.
Der neue Lichtschalter zeigt dieselben tatsächlichen Flächenfarben ohne
zusätzliche Beleuchtung ([Browsernachweis](../screenshots/mochi-unlit-material-ui-macos.png)).
Das beseitigt keine in der Originaltextur eingebrannten Schatten. Der gesonderte
[Materialbasis-Prototyp](MOCHI_MATERIAL_BASIS_PROTOTYPE.md) blieb nach A/B-Prüfung
bewusst außerhalb des aktuellen Plans. Ein [wärmeres Bestandspaar](MOCHI_FILAMENT_COMPARISON.md)
ist als lokale Alternative verglichen, nicht automatisch übernommen.

Die folgenden Abschnitte sind historische Prüfnachweise; neuere Aussagen in diesem
Nachtrag gehen vor. Konkretes finales Mochi-GUI-Slicing, echte Farbwirkung und physische
Passung aller Figuren bleiben offen. Orange lässt sich aus den ausgewählten
Beige-/Braun-Basisfilamenten nicht durch zusätzliche Rezeptstufen erzeugen.

## Verifizierter Nachtrag: Mischrezepte, anatomische Schnitte und Bambu-Druckbarkeit

**313 Tests bestanden**, 0 Fehler, Warnungen als Fehler, 29,19 Sekunden.
[JUnit](junit-color-mode-final.xml). Keine kostenpflichtigen Aufrufe für diese Prüfungen.

| Befund → Korrektur | Tatsächlich geprüft |
|---|---|
| Core-3MF-Objekte waren als `printable="true"` gespeichert. Bambu interpretiert dies numerisch als 0 → Export schreibt `printable="1"`, Validator stoppt falsche Werte. | Vier Regressionstests; echte Nasenprobe in Bambu-GUI gesliced: 91 Schichten, 1,41 g, 14:28 min. Nutzer startet selbst den Passungsdruck; Ergebnis offen. |
| Mixed war mit einer festen Regionsfarbe und Geometrieentscheidung vermischt → `strategy=body/part` und `color_mode=solid/mixed` getrennt. | Altpläne verlustfrei migriert; getrenntes Teil plus Mixed in API, Vorschau, KI-Übernahme und nativem Mapper getestet. |
| Zu wenige angezeigte Farben → per Originaldreieck ein Mischrezept aus derselben Basisfilament-Paarung berechnet. | 17 Rezepte von 10/90 bis 90/10 in 5%-Schritten, plus reine Endpunkte = 19 Farben. Anteil und rechnerische Teilschichtdicken sichtbar. Referenzplan bleibt über Speichervorgänge unverändert; Farbkorrekturen beeinflussen die Vorschau. |
| Export hätte andere Rezepte als die Vorschau wählen können → exakte Quellflächen-Rezeptzuordnung, vorhandene virtuelle Slots gezielt belegt. | Native Zuordnung stimmt mit Vorschau überein; fehlende Slotkapazität stoppt ausdrücklich statt die Palette zu vergröbern. Temperaturen, physische Profile und Purge-Matrix bleiben erhalten. |
| Fremde Dragon-Farben könnten als Mochi-Farben missverstanden werden → technische Abnahme und Character-Materialabnahme getrennt. | 19-Streifen-Test mit Grün/Beige in echter H2D-GUI gesliced: 163 Teilschichten bei 2 mm, 5,01 g, 33:34 min, Düsenbelegung ausschließlich Slots 1 und 2. Glow-Slot 3 existiert unbenutzt. **Kein Mochi-Farbprofil und keine physische Farbkalibrierung.** CLI lehnt Mixed mit Exit 231 ab; das GUI-Ergebnis ersetzt diese CLI-Grenze nicht. |
| Ohr-/Schwanzschnitte lagen mitten im Anhang → geometrischer Min-Cut an konkaven anatomischen Wurzeln auf geglätteter Analysegeometrie, äußeres Originalnetz unverändert. | Neue modellgebundene Mochi-Probe: 9 geschlossene Teile, 7 Stifte, 4 Klebe-Augeneinsätze, 10 gemeinsame diskrete Pfadprüfungen bestanden. Max. Stichproben-Eindringung 0,0022 mm. Nase vollständig einschließlich altem dunklem Restdreieck. |
| Schmale Spalte, fehlende Legende, kleine Varianten → breiter Desktopeditor, gestapelt bis 1100 px, Legende und Info-Aufklapper, Nahansicht der neun Varianten. | Desktop-Browser ausgeführt; neun Nahansichten visuell geprüft. Keine Browserfehler im geprüften Ablauf. Varianten sind zunächst Zielfarbentwürfe; berechnete Mixed-Vorschau folgt nach Auswahl. |

Belege: [Core-Slicing](../screenshots/bambu-core-printable-sliced-macos.png),
[19-Rezept-Slicing](../screenshots/bambu-19-recipes-sliced-macos.png),
[19-Rezept-G-Code-Nachweis](bambu-19-recipes-gui-verification.json),
[Mixed-Vorschau](../screenshots/mixed-computed-preview-macos.png),
[Varianten-Nahansichten](../screenshots/color-variants-closeup-macos.png),
[anatomische Messdaten](mochi-anatomical-verification.json).

Die neue anatomische Probe ist reproduzierbar mit
`PYTHONPATH=backend .venv/bin/python scripts/verify_mochi_construction.py --project 1b0e2fdd463d4f15ac64f1c7b3e8acc7`.
Sie prüft Quellhash, Maßstab und Planbindung und verändert keine Projektfreigaben.
Nase: Ø3 mm/Länge 3 mm; Ohren und Schwanz: jeweils zwei Ø2,4-mm-Stifte/Länge 2,5 mm.
Radiales Spiel 0,2 mm. 13 Core-Dateien bestehen XML-/Geometrie-Roundtrip und numerische Druckbarkeitsprüfung.
Summiertes Teilevolumen 476.150,9859 mm³ gegenüber Quelle 476.224,4366 mm³;
Differenz 73,4506 mm³ durch Passungsfreiräume.

**Verbleibend:** Anatomische Grenzen sind noch ein explizit modellgebundener Versuch,
keine allgemeine anatomische Erkennung im normalen Konstruktionsbutton.
Core-Proben haben vereinfachte Anzeigefarben; die Kombination dieser Anatomie mit
regionalem nativem Mochi-Mixed-Export ist nicht als fertig abgenommen.
Für Mochi sind im aktuellen Farbplan Bambu PLA Basic Beige und ELEGOO PLA Matte
Earth Brown gewählt. Die Dragon-Vorlage enthält stattdessen Grün/Beige/Glow:
passende echte Materialprofile fehlen noch. Zwei Filamente erzeugen nur Farben
zwischen diesen Ausgangsfarben; 19 Stufen können fehlendes Orange nicht ersetzen.
Keine Änderung fremder Profile allein durch Umbenennen oder Umfärben.
Physische Passung und reale Mixed-Farbwirkung bleiben bis zum Nutzerfeedback offen.

### Erster physischer Nasentest: Nutzerfeedback

Richard meldet zur bisherigen 0,20-mm-Radialspiel-Probe: sichtbare Fuge leicht,
vorläufig akzeptabel; Teil fällt wieder heraus und hat insbesondere Drehspiel.
Er beobachtet eine schräg gedruckte Nasenspitze ohne Stütze sowie eine schlecht
gedruckte Seite des abgerundeten verdrehsicheren Stifts. Damit ist der Befund
keine isolierte Toleranzmessung. **Passung/Retention nicht abgenommen.**
Die neue Vergleichsprobe mit 0,05/0,10/0,15/0,20 mm radialem Spiel, überprüfter
Stift-/Taschenausrichtung und erforderlichen Stützen ist digital geprüft (siehe aktueller Nachtrag).
Kein automatischer Rückschluss auf alle Teile oder andere Materialien.

Frontend-Nachprüfung: `node tests/frontend_color_plan_regressions.mjs` besteht. Sie vergleicht die Legacy-Normalisierung mit dem echten Pydantic-Modell, erkennt echte Entwurfsänderungen und invalidiert die Mixed-Vorschau bei relevanten Profil-/Schichthöhen-/Bestandsänderungen. Damit bleiben alte Vorschläge anwendbar und geänderte Spulenfarben erzeugen keine veraltete Vorschau.

Die folgenden Abschnitte dokumentieren ältere Zwischenstände.


## Neuester Konstruktionsnachtrag: neun echte Mochi-Teile

**259 Tests bestanden, 0 fehlgeschlagen**, 18,93 Sekunden; Warnungen als Fehler.
[JUnit](junit-construction-recheck.xml). Das modellgebundene lokale Experiment
ist mit [verify_mochi_construction.py](../scripts/verify_mochi_construction.py)
reproduziert: Quell-GLB-SHA256 und 180-mm-Maßstab werden geprüft; keine
Projektmutation, erfundenen Freigaben oder Provideraufrufe.

**9 Teile auf 3 geometrisch geprüften Platten:** Körper, Schwanz, Nase,
beide Ohren und vier dunkle Augeneinsätze. Jedes Teil ist genau ein geschlossener
Körper ohne offene oder Non-Manifold-Kanten. Nase: ein Stift Ø3 mm; Schwanz:
zwei Stifte Ø3 mm; Ohren: je ein Stift Ø2,4 mm. Radiales Spiel jeweils 0,2 mm.
Die vier kleinen Augeneinsätze haben ausdrücklich **keine sicheren Stifte**:
Klebeteile, Fuge 0 mm, physische Klebefuge/Retention nicht geprüft.
Zehn gemeinsame diskrete Abzugsprüfungen gegen relevante andere Teile bestanden,
maximal gemessene Eindringung jeweils 0 mm. Keine kontinuierliche Kollisionsgarantie.

Nase und Augeneinsätze folgen organischen Originalfarbgrenzen; die sichtbaren
Originaldreiecke der dunklen Augenbereiche bleiben erhalten. Schwanz und ganze
mehrfarbige Ohren werden geometrisch getrennt. Sieben winzige Fellfragmente,
die Ohr-Ebenenschnitte zunächst ablösten, werden vollständig wieder mit dem Kopf
verbunden. Volumen und äußere Fläche bleiben bei dieser Zuordnung erhalten;
kein Außenfragment wird gelöscht. Der neue Helfer wird zusätzlich an einem
analytischen Kammkörper in beiden Schnittrichtungen geprüft.

Summiertes Teilevolumen 476.160,6915 mm³ gegenüber 476.224,4366 mm³ Quelle;
63,7451 mm³ Differenz durch Steckpassungsfreiräume. 3MF-XML-/Geometrie-Roundtrip
für Baugruppe und drei Platten bestanden.
[Messdaten, Grenzen und Dateihashes](mochi-construction-verification.json).

**Korrigierte Ursachen:**
- Automatische Steckrichtung prüft bei ungeeignetem gewichteten Mittel auch
  einen per linearem Programm gefundenen Kandidaten. Jede Originalnormale muss
  weiterhin die unveränderte Mindestmarge 0,06 bestehen. Explizite Benutzerrichtungen
  werden nicht still ersetzt.
- Nicht sternförmige Kappen verwendeten äußere Meshdiagonalen erneut. Innenkanten
  erhalten jetzt echte nach innen versetzte Punkte; sichtbare Konturen bleiben
  exakt. Quelleninneres, geschlossene Körper, Volumen und Montagepfad bleiben Gates.
- VTK-Pseudonormalen lieferten am rechten Ohr negative Abstände trotz belegter
  räumlicher Trennung. Distanzbetrag und Innen-/Außensignum werden jetzt getrennt
  bestimmt: [VTK SelectEnclosedPoints](https://vtk.org/doc/nightly/html/classvtkSelectEnclosedPoints.html)
  prüft Einschluss durch eine geschlossene Oberfläche. Loch-/Material- und
  absichtlich falsche Pseudonormalen sind Regressionstests. Nicht zertifizierte
  überlappende/verschachtelte Mehrfachschalen werden abgelehnt; mehrere
  positive Körper sind nur bei nachweislich disjunkten Begrenzungsboxen
  zugelassen. Getrennte Restkörper einer umlaufenden Farbregion bleiben unterstützt.

**Konkrete physische Probe vorbereitet:** Ein 18 × 11,06 × 17 mm großer
Block enthält die echte Nasentasche; die echte Nase samt Steckstift wird separat
auf dieselbe Platte gepackt. Beide Körper und der 10-mm-Abzug sind geprüft.
Die Probe ist um +25 mm in X ins gemeinsame H2D-Bett versetzt; beide
transformierten Objektgrenzen liegen innerhalb des geprüften gemeinsamen
Düsenraums. Die Core-Datei enthält trotzdem kein erfundenes Maschinenprofil.
Damit kann die Passung ohne Druck der ganzen Figur getestet werden.

**Grenzen:** Das ist ein modellgebundener Konstruktionsentwurf, noch keine
allgemeine automatische anatomische Aufteilung im normalen UI-Konstruktionsjob.
Die zusätzliche Browservorschau zeigt die neun Teile zusammengebaut/explodiert,
einen unkalibrierten Orange-/Creme-Farbentwurf (ähnliche Brauntöne vereinheitlicht)
und die Downloadlinks. Sie exportiert keine regionalen Druckfarben; die Core-3MFs
haben vereinfachte Anzeigefarben pro Teil. Native H2D-Filament-/Rezeptzuordnung und
vollständige Übergabe dieses Entwurfs in den regulären Farbplan bleiben offen.
Menschliche Mesh-/Farbfreigaben wurden nicht nachgetragen. Brust und Wangen
bestehen an ihren rohen Fell-/Farbkonturen als separate Ganzteile weiterhin nicht;
im gezeigten Entwurf bleiben diese Regionen am zweifarbigen Grundkörper.
Eine neue Bambu-GUI-Prüfung der Mochi-Datei konnte wegen eines
ScreenCaptureKit-Aufnahmefehlers nicht beendet werden; der bereits belegte
native Mixed-Würfeltest bleibt davon getrennt.


## Neuester Nachtrag: druckbare native Platten und echter Mixed-Slicer-Test

**243 Tests bestanden, 0 fehlgeschlagen, Warnungen als Fehler**, 18,96 Sekunden.
[JUnit](junit-native-printability.xml). Die native GUI-Prüfung ist inzwischen
für den 85/15-Würfel bestanden; der frühere Abschnitt „GUI-Abnahme offen“ ist
historisch. Details, Fehlerursachen und Belege:
[H2D-Mixed-Abnahme](DRAGON_TEMPLATE_VERIFICATION.md).

Der vorherige reine Geometrie-Roundtrip hatte eine falsche Printable-Markierung
und eine fehlende native Platteninstanz nicht erkannt. Genau deshalb wurde die
GUI-Slicing-Abnahme durchgeführt. Der Builder prüft jetzt Druckbett und beide
Düsenräume vor der Markierung. Der finale Export-Worker übersetzt den
300-mm-Packrahmen korrekt ins H2D-Bettkoordinatensystem.
Ein erneuter vollständiger Worker-/ZIP-Test besteht lokal unter
`benchmarks/native-bundle-check/b0299228efb54ffba84c993a3a5379f7/`.

Ein frisches Projekt **Mochi · neuer Farb- und Montageplan** wurde ohne bezahlte
Aufrufe angelegt und im Browser geöffnet. Verifizierte Eingangsdateien wurden
hashgleich kopiert; alte Schnitte, Vorschläge und Freigaben wurden nicht übernommen.
Der lokale Farbplan hat vier Bereiche. Ein fertiger montierbarer Character und
physische Passungs-/Farbtests stehen weiterhin aus.


## Aktueller Nachtrag: Farbplan, Promptsteuerung und native Profile (16.10.2026)

**236 Tests bestanden, 0 fehlgeschlagen; Warnungen als Fehler**, 26,02 Sekunden.
[JUnit](junit-color-planning.xml). JavaScript-Syntaxprüfung aller drei Module und
`git diff --check` bestanden. Dieser Nachtrag präzisiert die historischen Berichte.
Keine bezahlten Provideraufrufe für diese Prüfung.

| Problem → Änderung | Tatsächlich geprüft / Grenze |
|---|---|
| Farbe und Montage waren ein Schritt → separater Farbplan | API-Vorschläge, immutable Planversionen, Meshbindung, gleichzeitige Zugriffe, Flächenzuordnungen durch Verfeinerung getestet |
| Farbgrenze bedeutete automatisch Einzelteil → geometrische Bauteilgruppen | Ein Teil kann mehrere Farben enthalten; Misch-/Vollfarben zählen nach physischen Basisfilamenten, maximal zwei pro H2D-Teil. Hybrider Ganzteil-/Einsatz-Test mit realen Volumen und Kollisionskontrolle |
| Formulararbeit → freies KI-Briefing pro Schritt | Strukturierte Mockantworten für Pose, Settings, Planregionen und konkrete Teile-/Spulenzuordnungen; bearbeitbare Übernahme, veraltete/manipulierte Referenzen und gesperrte IDs getestet. Kein bezahlter Astra-Live-Test |
| Unvollständiger Mixed-Plan blockierte sogar KI-Hilfe → Referenzdraft | Ungespeicherte Pinselzuordnung mit fehlendem Basispaar wird lokal unveränderlich referenziert. KI sieht Regionen ohne Facearray. Vollprüfung erst nach Antwort; Originalplan und Freigaben bis Übernahme unverändert |
| Schattierungen als zusätzliche Farben → neun lokale Varianten | 3×3: hell/original/dunkel; Grundfarben/ausgewogen/mehr Details mit Sättigungsvariation. Ähnliche automatisch vorgeschlagene Farbtöne vereinheitlichen, sehr dunkle neutrale Details und manuelle Markierungen schützen. Heuristik, keine physikalische Entlichtung |
| Grobe Augenansicht → echte UV-Textur und interpolierte Normalen | Pixel/UV/Faktor und unveränderte Geometrie automatisch geprüft; echter Mochi im Browser betrachtet. Detailanalyse separat: [Messung](MESH_DETAIL_ANALYSIS.md) |
| Kleine Schrift/zu viele gleichrangige Controls → Lotum-orientierte UI | 20 Prinzipien und Elementgruppen im [Audit](UI_AUDIT.md); größere Schrift/Controls, Details aufgeklappt nur bei Bedarf, Prompt vor manuellem Farbplan, Demo zurückgenommen |
| Native Mischdaten fehlten → echte H2D-Vorlage und native Flächenbemalung | Vom Nutzer bereitgestellte Dragon-Datei read-only geprüft; drei physische Slots/acht Mischrezepte. Kleine Profilkopie ohne Originalgeometrie/Auxiliary-Inhalte. [Vorlagenprüfung](DRAGON_TEMPLATE_VERIFICATION.md) |
| Mischfarben könnten still einfarbig exportiert werden → expliziter nativer Export | Fehlende Vorlage/Filamente/Rezepte blockieren. Nativer Begleiter pro Platte im ZIP mit SHA256 und klar gekennzeichneten einfarbigen Core-/GLB-Begleitern. Vollständiger lokaler Worker-Test mit echtem Profil: zwölf Würfelflächen auf Mischslot 4, 0 mm Geometrie-/Weltlageabweichung |

### Tatsächlicher Browsercheck

Lokale App auf Port 8000: bestehendes Mochi-Projekt, echte UV-Meshvorschau,
Farbplan mit vier vorgeschlagenen Regionen, Promptentwurf über Schrittwechsel
wiedergefunden, neun Vorschaubilder erzeugt. Die neun PNG-Daten unterscheiden
sich, Kamera bleibt gleich. Variante gewählt und zurückgenommen; der
Serverplanhash blieb bis zum ausdrücklichen Speichern unverändert.
Der echte Plan wurde nicht durch einen ungeprüften KI-Vorschlag freigegeben.

Belege: [Farbmatrix](../screenshots/color-variants-macos.png),
[Prompt und Farbplan](../screenshots/prompt-color-plan-macos.png),
[UV-Texturansicht](../screenshots/uv-texture-macos.png).
Eine Fehlermeldung im Browserprotokoll stammt vom kontrollierten Serverneustart;
keine danach beobachteten JavaScript-Laufzeitfehler im geprüften Ablauf.

### Native Exportabnahme und verbleibende Grenzen

Der vollständige Worker-Test liegt lokal unter
`benchmarks/native-bundle-check/3774e3222a4d41c48243a9fc54f0f362/`:
Paket, Manifest, Materialbericht und native Plattendatei. Alle zwölf Flächen
werden dem vorhandenen Rezeptslot 4 zugeordnet, die zwei physischen Komponenten
werden korrekt aufgelöst. Dies bestätigt das Schreiben und geometrische
Konvertieren mit echten Profilwerten, **keine finale Mixed-Slicing-Abnahme**.
Die installierte Standard-CLI lehnt bereits gemischte Projekte ab. Ein GUI-
Projektwechsel traf auf ein anderes ungespeichertes Bambu-Projekt und wurde
abgebrochen; das bestehende Projekt wurde nicht überschrieben/verworfen.
Der finale native Import/Save/Slice muss in einem freien Bambu-Prüffenster
geprüft werden. Bis dahin bleiben native Dateien ausdrücklich experimentell.

Die Dragon-Farben sind Grün/Creme, nicht Mochis Orange/Braun. Die native
Zuordnung verlangt zu Farbplan und realen Spulen passende Profile; die
Dragon-Vorlage wird nicht still umgefärbt. Eine komplette 5%-Bibliothek fehlt
weiterhin: acht vorhandene Rezepte werden verwendet, keine unvollständigen
Filament-/Düsen-/Spülmatrizen erzeugt.

Anatomische Erkennung beliebiger 3D-Oberflächen, regional gewichtetes echtes
Remeshing, vollständig montierbare reale Characters und physische Passungen
sind weiter offen. Farbregionen können mehrere Körperstellen umfassen; manuelle
Pinselbereiche und KI-Vorauswahl ersetzen keine geometrische Montageprüfung.
Die historischen Demo-Geometrieprüfungen bleiben gültig; ein neuer realer
Character wurde durch diesen Nachtrag nicht als komplett montierbar erklärt.

## Historischer Nachtrag: Arbeitskopien, Bedienung und echte Characters (16.10.2026)

**107 Tests bestanden**, Warnungen als Fehler; Node-Syntaxpruefung bestanden.
[JUnit](junit-workflow-final.xml). Die historischen Abschnitte unten beschreiben
fruehere Staende; dieser Nachtrag hat Vorrang.

### Ursachen und Korrekturen

- Alte Meshy-Auftraege hatten kein Polygonziel: Mochi lieferte 2.630.056 Faces.
  Jetzt wird `should_remesh=true`, Triangle-Topologie und standardmaessig
  `target_polycount=150000` bereits beim Auftrag gesetzt. Kein bezahlter neuer
  Auftrag nur fuer diese Vertragspruefung; HTTP-Mocktest belegt die Parameter.
- Importcap und Farbgrenzenbudget sind unterschiedliche Grenzen. Weniger
  Eingangsfaces allein verhindern keine starke spaetere Verfeinerung.
  Dichtere GLBs bis 4 Mio. Dreiecke werden zuerst mit Blender in einer separaten
  Datei reduziert; anschliessend werden Form, Albedo und Topologie verglichen.
  Der normale Kernimport bleibt auf 1 Mio. begrenzt. Kein blindes Voxel-Remesh,
  keine automatische Versiegelung grosser Loecher, kein ueberschriebenes Original.
- GLB-UV-Nahtvertices vor Collapse verschweissen: Ohne diesen Schritt oeffnete
  der erste lokale Versuch Naehte. Die korrigierte Arbeitskopie bleibt geschlossen.
- Verfeinerungsbudget zaehlt tatsaechliche Nachbardreieck-Teilungen statt eines
  zu groben Schaetzfaktors. Automatik skaliert zur Druckhoehe, plant innerhalb
  des Budgets und zeigt effektive Millimeter. Feste Werte bleiben verbindlich.
- UI aktualisiert Fehler auch bei unveraenderter Projektrevision: Jobstatus und
  Fehler gehen in die Renderentscheidung ein. Aktueller Fehler direkt im Formular,
  fruehere Fehler klar als historisch markiert. Keine Pruefcheckboxen oder
  zusaetzlichen Freigabebuttons. Hauptaktionen binden die gezeigte Version per Hash.
- Face-Regler mit Reserve und Bewertung, Input/Output-Texte, passende zentrale
  Vorschau, deutsche Prozessnamen und kleine Hinweise unter Aktionen.
  Leere Explosions-/Plattenansichten sind bis zur Konstruktion deaktiviert.
- Kein pauschales 100-EUR-Produktversprechen: Ausgabenlimit optional, Planwerte
  bleiben als Schaetzungen erhalten. Vor der lokalen Migration liegt ein Snapshot.
- Astra-Vorschlag je Schritt: strict JSON, erlaubte Settings und Wertevalidierung,
  Begruendungen und explizites Uebernehmen, veraltete Basis wird abgelehnt.
  Keine automatische Bild-/Mesh-Generierung, Freigabe oder Budgeterhoehung.
  API-Vertrag und UI mit simuliertem Anbieter getestet; **kein bezahlter Astra-Test**.

### Messwerte an den echten Eingaben

| Merkmal | Buddy | Mochi |
|---|---:|---:|
| Druckhoehe | 1000 mm | 180 mm |
| Originaldreiecke | 768.288 | 2.630.056 |
| Aktuelle Arbeitskopie | 150.000 | 150.000 |
| Offene / Non-Manifold-Kanten | 0 / 0 | 0 / 0 |
| Geschlossene Koerper | 1 | 1 |
| Geplante verfeinerte Dreiecke | 278.942 / 350.000 | 333.512 / 350.000 |
| Effektive Farbgrenzen-Abtastung | 5,06 mm | 0,65 mm |
| Montage-Vorpruefung: unzulaessige Steckrichtungen | 16 von 935 Taschen | 20 von 26 Taschen |

[Maschinenlesbare Qualitaet und Vorpruefung](character-preparation-verified.json).
Die Abtastung ist keine garantierte Konturabweichung; kleine Details unter der
groben Flaechenabtastung koennen fehlen. Automatik ist als solche sichtbar.

Buddy-Reduktion: 12.000 flaechengewichtete Distanzstichproben in beide Richtungen,
p99 0,162 mm, Maximum 0,250 mm; Albedo p95 Delta E 2000 = 1,159.
[Messdaten](buddy-reduction-quality.json). Keine vollstaendige Hausdorff- oder
Selbstschnittzertifizierung. Laufzeit fuer die Blender-Reduktion allein rund
10 Sekunden, Max-RSS 1,27 GiB. Vorbereitung mit Vergleich zuletzt 11,37 s
(Buddy) / 37,86 s (Mochi); Farbgrenzenplanung zusaetzlich etwa 30–45 s.
Zwei Threads fuer native Rechenbibliotheken und Blender, Geometrie serialisiert.
Das sind Einzelmessungen auf diesem Mac, keine zugesicherte Laufzeit.

Der freigegebene Meshy-Remesh des vorhandenen Buddy kostete **5 Credits**, dauerte
113,55 s und lieferte 153.639 Faces, aber 271 offene/133 Non-Manifold-Kanten und
130 Komponenten. Diese Datei wurde **nicht** uebernommen. Die gueltige Kopie
stammt aus lokaler Blender-Reduktion des erhaltenen Originals.

**Der echte Character-Druckablauf ist noch nicht bestanden.** Der vollstaendige
Buddy-Konstruktionsversuch scheitert nach erfolgreicher Budgetplanung an
Hinterschneidungen (51,25 s). Die zweite Schnittstrategie scheitert an einer
verzweigten Farbgrenze. [Ergebnisse](buddy-construction-results.json).
Ein weiterer separater lokaler Versuch mit expliziter fuenffarbiger
Materialpalette und 100 mm2 Insel-Mindestflaeche braucht nur 222.404 verfeinerte
Dreiecke, scheitert aber ebenfalls an einer verzweigten Grenze. Auch dieses
Ergebnis wurde nicht uebernommen; Projektvorgaben blieben dabei unveraendert.
Die Texturklassifizierung erzeugt zahlreiche Schatten-/Fellregionen, keine
semantischen Materialteile. Naechste notwendige Geometriearbeit ist robuste
Materialregionen-Bereinigung und montierbare Unterteilung umlaufender Bereiche;
bloss ein weiteres hoeheres Face-Limit waere keine Loesung.
Daher kein Character-3MF als druckfertig ausgegeben. Die weiter unten belegte
Bambu-Geometrieabnahme betrifft die **Demo**, nicht Buddy oder Mochi.

### Erneuter Browser-Durchlauf der vereinfachten Bedienung

Isolierter lokaler Datenspeicher und simulierter OpenAI-Anbieter: Vorschlag
anzeigen (Formular unveraendert), explizit uebernehmen, verzoegerten Fehler
anzeigen, Reglerbewertung aktualisieren. Anschliessend echte lokale Demo:
Import -> Hauptaktion Farbteile bauen -> Explodiert -> drei belegte Platten ->
Filamente speichern -> Hauptaktion Export. Keine vorgeschalteten Checkboxen
oder separaten Freigabebuttons. Sechs Teile, fuenf Verbinder; zwei kleine
Augeneinsaetze weiterhin ohne sichere Halterung, prominent sichtbar.
ZIP-Pruefsummen bestanden, keine Browserwarnungen/-fehler beobachtet.
[UI-Nachweis](ui-workflow-verified.json),
[Plattenansicht](../screenshots/workflow-plates-verified.png),
[Exportansicht](../screenshots/workflow-export-verified.png),
[verzoegerter Fehler](../screenshots/workflow-error-verified.png).
Die drei neu erzeugten Platten wurden erneut mit Bambu Studio 2.7.1.62
importiert/exportiert; unabhaengiger Geometrievergleich fuer alle bestanden.
[Neuer Bambu-Nachweis](bambu-workflow-verified.json). Kein Slicing oder Druckstart.

### Ressourcen und Vertraulichkeit

M2 Max, 12 Kerne, 96 GiB RAM. Gemessene Momentaufnahme: etwa 1,4–3 GiB physisch
unbenutzt, rund 15 GiB komprimiert, 4,46 GiB Swap belegt. Die 56 % aus
`memory_pressure` sind nicht gleich 54 GiB unbenutztem RAM. Ein llama-server
belegte rund 23,8 GiB RSS; Zuordnung zur Diktierfunktion nicht verifiziert.
Kein fremder Prozess beendet. Fixe 0,65-mm-Planung am 1-m-Buddy erreichte knapp
4 Mio. Dreiecke nach 134 s bei rund 6,94 GiB Max-RSS und wurde verworfen.
Die begrenzte Automatik vermeidet diesen Lauf. Vollstaendige Konstruktion kann
mehr Speicher und Zeit brauchen; aktuell geometrisch blockiert.

[Meshy-Privatsphaere und widerspruechliche Training-Angaben](PRIVACY_PROVIDERS.md).
Keine weiteren bezahlten Tests fuer UI-/Limitkorrekturen gestartet.


## Aktueller verifizierter Stand: 16. Oktober 2026

**Echter Meshy-Durchlauf und Vorschau:** Der Nutzer startete nach Posefreigabe
selbst einen Meshy-Auftrag mit den drei importierten Originalansichten.
Das heruntergeladene GLB enthielt 768.288 Dreiecke und wurde zunaechst allein
wegen der bisherigen Importgrenze von 500.000 Dreiecken abgelehnt. Die begrenzte
Importkapazitaet wurde auf 1.000.000 erhoeht; der vorhandene isolierte Worker
und dessen Zeitlimit bleiben aktiv. Kein Remeshing und kein neuer Cloud-Auftrag.
Lokales `inspect` des unveraenderten Downloads erfolgreich: 384.066 Vertices,
768.288 Dreiecke, ein geschlossener konsistent orientierter Koerper,
0 offene/Non-Manifold-Kanten. Selbstschnitte nicht vollstaendig zertifiziert.
Aktuell vom Nutzer gespeicherte Hoehe 1.000 mm, Ausdehnung
499,5048 x 1.239,7324 x 1.000 mm; noch keine Meshfreigabe oder Character-Konstruktion.
Beleg: [Buddy-Mesh-Import](buddy-mesh-import.json).

Die zentrale Vorschau zeigt im Pose-Schritt nun die aktuellen Posebilder und
im Mesh-Schritt das aktuelle 3D-Modell. Importierte Originalansichten sind
ausdruecklich gekennzeichnet. Die zwei OpenAI-Einzelergebnisse erscheinen separat
als Testbilder und werden nicht implizit zum freigegebenen Kandidaten gemischt.
Im Browser zwischen Pose und Mesh gewechselt, beide Darstellungen geprueft;
[Pose-Screenshot](../screenshots/buddy-pose-preview.png),
[Mesh-Screenshot](../screenshots/buddy-mesh-verified.png).
JavaScript-Syntaxpruefung bestanden. Gesamtsuite vor dem zusaetzlichen Import-
Grenztest: 88 bestanden, 67,11 s (parallel zum echten Mesh-Import),
[JUnit Pose-Vorschau](junit-pose-preview.xml). Danach Geometriesuite einschliesslich
neuem Test der weiter wirksamen Obergrenze: 30 bestanden, -W error, 4,66 s.

**Gezielter Wiederholungsversuch, vom Nutzer freigegeben:** Auftrag
`a0afab142b1641a78fd25e71cdd753b8` erzeugte nur die zuvor fehlgeschlagene linke
Buddy-Ansicht unter Wiederverwendung der bereits erzeugten Front. OpenAI lieferte
HTTP 200, Request-ID `req_a6ed5b8b661f42a19ce69b7375bc4f0a`, 3.233 Input- und
5.488 Output-Tokens. Das neue PNG wurde visuell angesehen; vollstaendige Figur
und charakteristische Ausruestung vorhanden. Bild und `diagnostic.json` liegen
lokal im zugehoerigen ignorierten Auftragsordner. Kein vollstaendiger neuer
Vieransichten-Kandidat, keine Posefreigabe. Frueherer HTTP 400 nicht reproduziert;
dessen exakte Ursache weiterhin unbekannt.

**Dauerhafte Speicherung erweitert:** Der normale Runner sichert abgewiesene
POST-Antworten jetzt verschluesselt in `runs/<job>/provider-errors/*.enc` und
vermerkt den Pfad im Job-Checkpoint. Keine Request-Header werden gespeichert.
Erfolgreiche Pose-Ansichten werden sofort einzeln im Checkpoint gespeichert,
damit ein spaeterer Fehler ihren Pfad und ihre Nutzungsdaten nicht mehr verbirgt.
Regressionstest simuliert Erfolg vorne und Fehler bei der naechsten Ansicht,
prueft Bild-Erhalt, verschluesselte Fehlerdetails und fehlende implizite Freigabe.
Gesamtsuite **88 bestanden, -W error, 15,33 Sekunden**; JUnit-Datei unten aktualisiert.

**Nachtrag echter Bildaufruf:** Nach dem Key-Wechsel hat der bereits vom Nutzer
gestartete Buddy-Pose-Auftrag `9d1388d74f7d4616919aff7242e483fd` erfolgreich
`pose-0-front.png` geliefert: PNG, RGB, 1024 x 1536 Pixel, 1.693.172 Bytes;
vollstaendig mit Pillow dekodiert und visuell angesehen. Bei der Pruefung lief
bereits die linke Ansicht. Damit ist echte Bildgenerierung mit dem aktuellen
Key belegt; der Gesamtauftrag und die Abrechnungssumme sind damit noch nicht
verifiziert. Kein zusaetzlicher Testaufruf wurde gestartet.

**Abschluss dieses Auftrags:** Die linke Ansicht wurde anschliessend mit HTTP 400
abgelehnt. Nur die neue Frontansicht ist erzeugt worden; der vollstaendige
Pose-Kandidat wurde deshalb nicht ersetzt. Die Oberflaeche zeigt weiter die
manuell importierten Originalansichten. Die exakte 400-Ursache ist wegen der
bisher pauschalen Fehlerbehandlung nicht rekonstruierbar. Neue Fehler enthalten
jetzt verfuegbare strukturierte `code`, `param`, `type` und `x-request-id`-Werte;
freie Anbietertexte und Antwortkoerper werden zum Schutz von Eingaben nicht
gespeichert. Kein erneuter kostenpflichtiger Versuch. Gesamtsuite nach dieser
Erweiterung und explizitem Key-Ersetzen: **87 bestanden, -W error, 15,02 Sekunden**.
Die Prozesshinweise aller drei Journey-Projekte wurden aus den Prompt-Feldern
in die Pose-Pruefhinweise verschoben. Vorheriger Stand lokal unter
`data/character-inputs/journey/prompt-cleanup-before-*.json` gesichert;
Originalbilder erhalten, Pose-Hashes neu gebunden, Buddy-Freigabe zur erneuten
menschlichen Pruefung zurueckgesetzt. Server mit neuer Fehlerdiagnose gestartet.

**Ergaenzung Provider-Diagnose:** Ein nicht generierender OpenAI-Modellabruf
mit dem gespeicherten Key lieferte HTTP 200; das konfigurierte Bildmodell war
aufgelistet. Das belegt Authentifizierung, nicht Bildgenerierungs-Kontingent.
Zwei anschliessend vom Nutzer gestartete Pose-Auftraege scheiterten mit HTTP 429.
Der alte Adapter verwarf den detaillierten Fehlercode; die genaue Ursache
dieser beiden Fehler ist daher nicht mehr bestimmbar. Der Adapter unterscheidet
jetzt bekannte Guthaben-/Kontingentfehler von Anfragelimits und meldet unbekannte
429-Ursachen ausdruecklich als unbestimmt. Keine automatischen POST-Wiederholungen,
keine Ausgabe beliebiger Anbieter-Fehlertexte oder Schluessel. Gesamtsuite:
**85 bestanden, -W error, 15,40 Sekunden**, siehe
[JUnit Provider-Diagnose](junit-provider-diagnostics.xml). Der lokale Server wurde
mit der Korrektur neu gestartet. Kein weiterer Generierungsaufruf zur Diagnose.

**Ergaenzung Character-Eingaben:** Nach der unten dokumentierten Mac-Abnahme
wurden vorhandene Character-Ansichten, transparente PNGs und der lokale
Zwischenablage-Key-Helfer ergaenzt. Die anschliessende gesamte Testsuite besteht
mit **82 Tests, 0 Fehlern, -W error**, 16,20 Sekunden:
[JUnit Character-Eingaben](junit-character-inputs.xml).
Die zusaetzlichen Tests pruefen Posefreigabesperren, atomaren Import bei
ungueltigen Bildern, Erhalt alter Kandidaten, weisse PNG-Transparenz und
Schluesselablage im echten isolierten verschluesselten Testtresor.
Der Key-Helfer wurde nur mit Testschluesseln und simulierten bzw. lokalen
Testclient-Anfragen getestet, nicht mit einem echten Anbieter-Aufruf.

Dieser Abschnitt berichtet die tatsaechlich auf Richards Mac ausgefuehrten
Pruefungen. Der urspruengliche Linux-Bericht bleibt unten als historische
Auslieferungsdokumentation erhalten; dessen offene Mac-/Bambu-Pruefung ist
durch die hier konkret genannten Pruefungen teilweise abgeschlossen.

**75 Tests bestanden, 0 Fehler, Warnungen als Fehler, 14,90 Sekunden.**
[JUnit-Protokoll](junit-macos-final.xml). Frische isolierte Installation mit
Python 3.13.13, macOS 26.7.1, Apple Silicon/arm64; Paketstand:
[dependency-versions-macos.txt](dependency-versions-macos.txt).
`pip check` besteht. `bash start.sh` startet den Server auf 127.0.0.1:8000.
Es wurden keine kostenpflichtigen Provider-Aufrufe ausgefuehrt.

### Belegte Fehler und Korrekturen

| Problem | Korrektur und Nachweis |
|---|---|
| Apples Python 3.9 wird vor installiertem Homebrew-Python gefunden | Startdatei sucht explizit eine Version >=3.11; bestehende .venv bleibt erhalten |
| uv-Umgebung hat kein pip | Startdatei stellt pip bei Bedarf mit ensurepip bereit; echter Startbefehl auf diesem Mac getestet |
| Starlette 0.50 nutzt einen in AnyIO 4.15 veralteten Alias; Tests stoppen bereits beim Import unter -W error | AnyIO 4.11.0 in getesteten Constraints festgelegt; Warnungen bleiben Fehler |
| lxml war nicht als Testabhaengigkeit deklariert; unabhaengiger 3MF-Importtest scheiterte | lxml zu dev-Abhaengigkeiten und getesteten Constraints hinzugefuegt |
| Bambu liest Meshkoordinaten mit Float32; acht sehr schmale Dreiecke eines weit vom Ursprung liegenden Farbeinsatzes kollabierten im urspruenglichen Export | Jedes Objekt bekommt lokale Koordinaten, die Build-Transformation stellt die Weltlage wieder her. Kein Remeshing; neuer Regressionstest mit ferner duennwandiger Geometrie und Rotation sowie echter Bambu-Roundtrip |
| Fehlende Halterung kleiner Augen nur hinter aufklappbaren Warnungen erkennbar | Betroffene Einsaetze werden in Konstruktion, Farben und Export direkt als unvollstaendige Steckmontage benannt; im Browser sichtbar geprueft |
| Demo-Materialwarnung wurde wegen Vergleich von Demo mit DEMO nicht erzeugt | Vergleich unabhaengig von Grossschreibung; im End-to-End-Test und Browser geprueft |

### Lokale Geometrie- und API-Durchlaeufe

| Merkmal | 180 mm | 1000 mm |
|---|---:|---:|
| Einzelteile / Platten | 6 / 3 | 22 / 17 |
| Alle Teile geschlossene positive Einzelvolumen | Ja | Ja |
| Montageweg-Stichproben und Bauraumpruefung | Bestanden | Bestanden |
| 3MF-XML-/Geometrie-Roundtrip | Bestanden | Bestanden |
| API-Durchlauf inkl. Export | 83,749 s | 56,350 s |
| Farbgrenzenabtastung | 0,65 mm | 2 mm |
| Farbeinsaetze ohne sicheren Stift | 2 | 0 |

Die Laufzeiten sind Einzelmessungen (einschliesslich erstmaliger Modulinitialisierung
und teilweise paralleler Testarbeit), kein Leistungsvergleich der Figurengroessen.
Belege: [180-mm-API-Lauf](benchmark-macos-api-180.json),
[1000-mm-API-Lauf](benchmark-macos-api-1000.json).
Der 180-mm-API-Benchmark enthaelt noch den urspruenglichen Export; seine
Geometrie wurde anschliessend mit der Exportkorrektur erneut ausgegeben und
zusaetzlich durch den aktuellen Browser-Workflow neu exportiert.
Der 1000-mm-Lauf verwendet bereits die Exportkorrektur.

### Bambu Studio 02.07.01.62 auf dem Zielrechner

Alle **3 kleinen und 17 grossen Platten** wurden durch die installierte
Bambu-Studio-Kommandozeile importiert und in separate native 3MF-Pruefdateien
exportiert. Der unabhaengige trimesh-Vergleich umfasst Teilezahl, Dreieckszahl,
geschlossene positive Volumen, transformierte Bauteilgrenzen, Volumendifferenz,
Eckpunkte und Nullflaechen-Dreiecke. Alle Pruefungen bestehen.
Die kleinen Platten stammen aus dem tatsaechlichen Browser-Download.
Belege: [180-mm-Bambu-Pruefung](bambu-macos.json),
[1000-mm-Bambu-Pruefung](bambu-macos-1000.json).

Dies ist eine **geometrische Importabnahme**, keine H2D-Slicing- oder Druckfreigabe.
Die CLI erzeugt kein abgenommenes Maschinenprofil. Reale Filamente,
Duesenzuordnung, Support, Brim, Sperrflaechen und die Druckbarkeit im gewaehlten
H2D-Profil muessen vor einem Druck in Bambu Studio kontrolliert werden.
Das bereits geoeffnete fremde Bambu-Projekt wurde nicht veraendert.

Reproduktion, nach Erzeugen eines API-Druckpakets und Entpacken in einen
eigenen Pruefordner mit plate-XX.3mf:

```sh
.venv/bin/python -m pytest -q -W error
.venv/bin/python scripts/benchmark_api.py --height 180 --output benchmarks/recheck-180
.venv/bin/python scripts/benchmark_api.py --height 1000 --output benchmarks/recheck-1000
.venv/bin/python scripts/verify_bambu.py /absoluter/pfad/zum/pruefordner --report benchmarks/recheck-bambu.json
```

### Tatsaechlicher Browser-Demoablauf

Direkte Navigation zur lokalen Web-App im Codex-Browser, ohne Offline-Bridge:
Testfigur laden -> Meshhinweise pruefen -> Mesh freigeben -> organisch
konstruieren -> Explosionsansicht und Druckplatten -> Filamente speichern ->
Farbhinweise pruefen -> Farben freigeben -> Druckpaket exportieren -> ZIP
herunterladen. Der Browser-Download stimmt bytegenau mit dem Serverartefakt
ueberein; alle enthaltenen SHA256-Pruefsummen bestehen.
Keine beobachteten JavaScript-Fehler oder -Warnungen im abschliessenden
Browserprotokoll. [UI-Protokoll](ui-macos.json),
[Screenshot der Exportansicht](../screenshots/macos-verified.png).
Der PNG-Downloadknopf wurde wegen eines Browserwerkzeug-Timeouts nicht
abschliessend abgenommen; der Screenshot wurde direkt aus dem Browser gesichert.
Der Demo-GLB-Import benoetigt keine Poseerzeugung; Pose-Freigabesperren und
Provider-Austauschbarkeit sind weiterhin durch die automatischen Tests abgedeckt.
Bezahlte Live-Provider sind nicht abgenommen.

### Noch offen und naechste Abnahme

1. **Kleine Augen bei 180 mm:** Zwei Teile sind geschlossen, haben aber keinen
   sicheren Haltestift. Naechste algorithmische Arbeit: eine ausdrueckliche
   Mischstrategie fuer zu kleine Details entwickeln und an unterschiedlichen
   Netzen testen. Bis dahin keine vollstaendige Steckmontage zusagen.
2. **Physische Passung:** Richard druckt zuerst Kalibrierpaare fuer 3,0 und
   1,6 mm Stiftdurchmesser im tatsaechlichen Material und Profil. Ohne Messung
   bleiben Spiel, Halt und Belastbarkeit ungeprueft.
3. **H2D-Slicing:** Mit den echten Spulen und Duesen pro Platte in Bambu Studio
   slicen und die Vorschau kontrollieren. Die digitale Geometrieabnahme ersetzt
   diesen Schritt nicht.
4. **Modellvielfalt:** Als naechste Eingaben drei echte, geometrisch verschiedene
   GLBs pruefen (Bueste, Haare/Finger, umlaufende Farbbereiche). Der aktuelle
   Demoerfolg ist keine Abnahme beliebiger KI-Netze.

## Historischer Auslieferungsbericht vom 15. Oktober 2026 (Linux)

Stand: 15. Oktober 2026. Die folgenden Tests wurden ausgefuehrt; sie sind keine
Liste erst geplanter Tests. Quellcode, Tests, Fixture und Startskripte werden
mitgeliefert. Die letzte Testsuite wurde mit `pytest -q -W error` ausgefuehrt.

## Ergebnis

**74 Tests bestanden, 0 fehlgeschlagen; Warnungen wurden als Fehler behandelt.**
Maschinenlesbare Einzeltests: [junit.xml](junit.xml).
Die letzte protokollierte Laufzeit betrug 23,65 Sekunden; Zeiten sind nur
Messwerte dieser Umgebung, keine Zusage fuer andere Rechner.

| Pruefung | Ergebnis |
|---|---|
| CIEDE2000 | Referenzwerte, Katalogfilter, Filament-Prioritaeten |
| GLB-Import | UV-/Albedowerte, Zielhoehe, externe Ressourcen blockiert |
| Farbverfeinerung | Konforme Topologie ohne T-Knoten, Volumenerhaltung |
| Organische Einsaetze | Benachbarte Farben mit gemeinsamer gekruemmter Tasche |
| Ganze Farbkoerper | Halbkugel, umlaufendes Band, wellige nichtplanare Grenze |
| Verbinder | Runde und verdrehsichere echte Stift-/Buchsengeometrie; kleine Ersatzstifte werden gemeldet |
| Strukturkappen | Box, Kugel, Hohlring und Torus in drei Richtungen; Volumenerhaltung und Loecher |
| Druckplanung | Transformierte Bauraumgrenzen, konservative XY-Abstaende, echte Spulen statt RGB allein |
| Export | XML-/Mesh-Roundtrip fuer 3MF, Farbe, Einheiten, Transformationen und ZIP-Pruefsummen |
| Workflow | Alte Freigaben blockiert, Budget, gleichzeitige Schreib-/Job-Zugriffe |
| Sicherheit | Pfadausbruch/Symlinks, Cross-Origin-Schreiben, URL-Pruefung, Secret-Tresor |
| Native Prozesse | Abbruch, Deadline, Absturz und Fehlerfortleitung ohne falschen Erfolg |
| Provider | Simulierte HTTP-Vertraege fuer Bild- und 3D-APIs; keine bezahlten Live-Aufrufe |
| End-to-End | Reale FastAPI-App: Demoimport -> Meshfreigabe -> Geometrie -> Farbfreigabe -> ZIP |

## Reale Geometrie-Benchmarks

Die originale, mitgelieferte GLB-Testfigur hat eine echte Albedo-Textur und
ist kein nur im Browser eingefaerbtes Platzhaltermodell. Sie ist ein
prozedural erstellter Testbaer, keine aus Benutzerfotos rekonstruierte Figur.

| Merkmal | 180-mm-Geometriebenchmark | 1000-mm-Web-API-Benchmark |
|---|---|---|
| Ergebnis | 6 Einzelteile, 3 Platten | 22 Einzelteile, 17 Platten |
| Geschlossene positive Volumen | Alle | Alle |
| Ein zusammenhaengender Koerper je Teil | Alle | Alle |
| Plattengrenzen / konservative Ueberlappung | Bestanden | Bestanden |
| 3MF-Roundtrip | Bestanden | Bestanden |
| Kostenpflichtige API-Aufrufe | 0 | 0 |
| Lokale Farbgrenzenabtastung | 0,65 mm | 2,0 mm |
| Grobe Flaechenabtastung | 4 mm | 8 mm |
| Fertig einschliesslich Export | 12,61 Sekunden | 87,90 Sekunden |

Der grosse Benchmark verwendet den **tatsaechlichen App-Workflow mit separaten
Geometrieprozessen, Freigaben, Filament-Snapshots und Download-Endpunkt**.
Er ist nicht lediglich ein einzelner erfolgreicher Algorithmusaufruf.
Ein frueherer direkter Benchmark mit anderer struktureller Verbinderwahl
hatte 16 Platten; die mitgelieferte aktuelle API-Ausgabe hat 17.

[180-mm-Messdaten](benchmark-180mm.json) / [1000-mm-API-Messdaten](benchmark-api-1000mm.json).

Reproduktion:

```sh
python -m pytest -q -W error
python scripts/benchmark.py --height 180
python scripts/benchmark_api.py --height 1000
python scripts/calibration.py --shape round
```

Die Grossformatfigur ist ein **digitales Testobjekt**, keine Empfehlung, sofort
alle 17 Platten zu drucken. Zuerst Passung, Material, Support, Montagefolge und
Tragfaehigkeit ueberpruefen. Die 180-mm-Figur enthaelt zwei kleine Augen-Einsaetze,
fuer die auch der verkleinerte Stift nicht sicher hineinpasst; diese werden
explizit als ohne garantierte Halterung gemeldet. Die 1-m-Farbteile bieten mehr
Platz fuer Verbinder. Kleine Farben koennen eine andere Fertigungsstrategie
oder eine vergroesserte Figur erfordern.

## Passungs-Testkoerper

Zehn geschlossene Teile auf einer Platte: fuenf Stift-/Buchsenpaare fuer
0,10 / 0,15 / 0,20 / 0,25 / 0,30 mm **radiales** Spiel. Sowohl runde als auch
verdrehsichere Varianten sind geometrisch getestet. Die Beispieldatei verwendet
runde Stifte mit 3 mm Nenndurchmesser. Fuer automatisch verkleinerte 1,6-mm-Stifte
separat `python scripts/calibration.py --radius 0.8` verwenden.
Es wurde kein physisches Paar gedruckt oder als passend vermessen.

## Weboberflaeche

Die ausgelieferten HTML-/CSS-/JS-Dateien wurden in Chromium ausgefuehrt.
Fuenf Screenshots: Konstruktion, Explosionsdarstellung, Platten, Farben, Mobil.
JavaScript-Laufzeitfehler: **keine**. Node-Syntaxpruefung beider JS-Module bestanden.

Die verwaltete Browserumgebung beschraenkte normale lokale Navigation und
WebGL. Der Test nutzte deshalb den dokumentierten Offline-Harness mit einer
auf die reale lokale App-API beschraenkten Bridge und den implementierten
Software-3D-Renderer. Das ist **kein** umfassender echter Browser-Navigationstest
und keine Abnahme der GPU-Pipeline. Der Fallback zeigt und manipuliert reale
Meshdreiecke, kein vorgerendertes Bild.

## Entpacktes Release getestet

Das erzeugte Quellcode-ZIP wurde in einen neuen Ordner entpackt. Von dort
startete `scripts/run.py` erfolgreich. Index, JavaScript, CSS, API-Schema und
API-Dokumentation antworteten; eine neue Testfigur wurde durch den separaten
Import-Worker eingelesen. [Messprotokoll](release-smoke.json). Die vorhandenen
Python-Pakete wurden wiederverwendet; dies ist kein frischer pip-Installationstest.

## Laufzeitumgebung und Grenzen

Linux x86_64, Python 3.13.5. Exakte Versionen:
[dependency-versions.json](dependency-versions.json), `requirements-tested.txt`.
Vorhandene Pakete wurden verwendet. Eine frische Paketinstallation war wegen
fehlendem Paketnetzwerk hier nicht moeglich; Docker, macOS/Apple Silicon und
Windows wurden nicht praktisch installiert oder gestartet.

Nicht abgenommen: bezahlte Providerkonten, aktueller Accountzugriff auf einzelne
KI-Modelle, echte Personen-Identitaet, Drucker-/Filamentkalibrierung, Bambu Studio,
Slicing, FEA, vollstaendige Selbstschnitt-/Montagekollisionsfreiheit und
beliebige ungepruefte KI-Meshes. Der Bericht erteilt keine Druckfreigabe.

## Zusätzliche unabhängige Pip-Kreisbogenprüfung

Die zehn tatsächlich gesliceten Pip-Platten wurden vollständig mit G17-I/J-Kreisbogenunterstützung erneut geprüft:5.671.524 Extrusionssegmente,843.410 druckende Bögen,4.029.786 Sehnen. Alle zehn Owner-Footprintgruppen einschließlich Spülturm sind räumlich getrennt. Maximaler konservativer Bogenfehler0,004999997 mm, im Linienbreiten-Footprint zusätzlich berücksichtigt; finale Wiederholung mit aktueller Prüfer-SHA unter paralleler Last100,32 s.25 gezielte Regressionen bestanden (0,43 s). Helical-/R-/G18-/G19-Druckbögen werden nicht stillschweigend angenähert. [Vertrag und Grenzen](GCODE_PATH_SCREENING.md), [tatsächliche G-Code-/Hashnachweise](pip-gcode-footprint-verification.json). Keine physische Druck-/Montage- oder Düsendynamikfreigabe.
