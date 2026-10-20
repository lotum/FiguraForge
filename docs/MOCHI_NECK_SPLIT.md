# Mochi · organischer Halsschnitt · 18.10.2026

**50 cm Gesamthöhe**, Kopf und Rumpf getrennt, gleiche bemalte Figur. Acht physische Teile auf drei nativen H2D-Platten. Die geprüfte 47-cm-Variante bleibt als zusätzliche Alternative mit mehr Reserve erhalten. Alle bisherigen Dateien und Richards Original bleiben unverändert.

- [**50 cm · ein natives Projekt mit drei Platten**](../benchmarks/mochi-neck-split-20261018/production-500/Mochi-500mm-Hals-geteilt-3-Platten.3mf)
- [47 cm · mehr Reserve im gemeinsamen Düsenbereich](../benchmarks/mochi-neck-split-20261018/production-470-final/Mochi-470mm-Hals-geteilt-3-Platten.3mf)
- [**Hals-Passungsprobe · zwei kleine Prüfplatten**](../benchmarks/mochi-neck-split-20261018/production-470-final/fit-probe-two-plates/Mochi-Hals-Passungsprobe.3mf)
- [Drehbare Geometrie-/Hals-/Explosionsansicht · 50 cm](http://127.0.0.1:8013/Mochi-Hals-Vorschau.html)

Die interaktive und statische Geometrieansicht verwenden **Bauteil-Kennfarben**: Kopf hellblau, Rumpf braun, Verbinder lime, kleine Gesichtsteile schwarz. Das sind keine neuen Filamentfarben. Die native 3MF erhält Richards originale Braun-/Beige-Bemalung einschließlich feiner Unterdreiecke.

## Warum ein separater Verbinder

| Möglichkeit | Auswirkung | Entscheidung |
|---|---|---|
| Zapfen am Rumpf | Steht über den Hals hinaus und zählt zur Bauraumhöhe; beim 50-cm-Modell ist der Rumpf bereits etwa 316 mm hoch | Keine zusätzliche Bauhöhe am Rumpf |
| Zapfen am Kopf | Hebt den Kopf beim aufrechten Druck um die Zapfenlänge an; kleiner Standfuß und zusätzliche Stützen unter der Halsfläche | Kopf erhält eine breite innere Auflage statt eines langen herausstehenden Zapfens |
| Separater Schlüssel, zwei Aufnahmen | Beide Hauptteile ohne zusätzliche Zapfenhöhe druckbar; Schlüssel lässt sich flach und massiv drucken | **Umgesetzt**, asymmetrisch und auswechselbar |

Die Auflage und die geschwungene Halsfläche tragen den Kopf. Der Schlüssel führt und verhindert Verdrehen. Dies ist eine abnehmbare Schiebepassung, keine verrastete Verbindung oder behauptete Zug-/Sturzsicherung. Reale Haltekraft und Passung sind noch nicht gemessen.

## Geometrische Halslinie

Die Trennung verwendet **keine Farbgrenze**. Die Querprofile der vorhandenen Geometrie zeigen eine Einschnürung unter dem Kopf. Aus radialen Profilen um den Hals werden lokale Taillenminima gewonnen und zu einer glatten, gekrümmten Schnittfläche zusammengefasst. Die äußere Kurve folgt dieser Einschnürung; innen geht sie in eine ebene Auflage über.

Reproduzierbare Parameter: analysierte Quelle auf 180-mm-Referenzmaß; Halszentrum XY(0,−27), Höhenprofile 104–116 mm in 0,5-mm-Schritten und 64 Winkelrichtungen. Quadratischer Außenverlauf aus `neck-valley.json`; innere Auflage bei Z108. Die spätere Vergrößerung skaliert die Figur, die Steckmaße werden **separat in echten Millimetern** konstruiert. Dies ist eine geprüfte Konstruktion für diese Quelle, kein allgemeiner autonomer Anatomieerkenner.

Beide Schnittseiten erhalten dieselbe äußere Kontur und komplementäre innere Kontaktflächen. Der senkrechte Montageweg enthält keine Hinterschneidung. 609 geschnittene Quellflächen haben reine Druckfarbe; Dreiecke mit komplexer nativer Pinselbemalung werden an der Schnittstelle ausdrücklich abgelehnt statt still neu eingefärbt. Alle 1.034 komplex bemalten Quellflächen des vorliegenden Modells bleiben vollständig erhalten.

Die verbliebene äußere Oberfläche ist flächengleich zur Quelle (numerische Abweichung um 1e−11 mm² im 180-mm-Bezugsmaß). Der Volumenunterschied der Hauptteile entspricht ausschließlich den konstruierten Aufnahmehohlräumen. Neue Auflage-/Aufnahmeflächen liegen innerhalb des Originalvolumens. Originalfell, Gesicht und Außenkontur werden nicht remesht oder ummodelliert.

## Verbindung und Druckausrichtung

- Asymmetrischer, gefaster Schlüssel: **20 × 28 × 36 mm**. Eine deutlich größere Eckfase verhindert falsche Ausrichtung. Beidseitig gefaste Einführungen.
- Zwei Aufnahmen: nominal 18 mm Eingriff pro Seite, jeweils 0,6 mm axialer Platz; 0,10 mm seitlicher Konstruktionsabstand. Diesen Wert zuerst real testen; die kleine Nasenprobe ersetzt keine Prüfung dieses größeren Schlüssels.
- Die Kopfaufnahme hat ein berechnetes pyramidenförmiges Dach, mindestens 45° über der Druckebene. Die Dachhöhe beträgt rund 16,16 mm. Damit gibt es innen keine breite horizontale Decke, die frei überbrückt werden müsste.
- Der Kopf liegt mit einer breiten, innenliegenden Halsfläche auf der Platte. Kinn, Fell und äußere Halsauskragungen benötigen weiterhin automatische Baumstützen; „stützenfrei“ wird nicht behauptet.
- Der Schlüssel wird auf einer langen Fläche gedruckt, **100 % Füllung, vier Wände, ohne Stützen oder Raft**. Diese expliziten Objektwerte bleiben auch nach nativem Speichern erhalten.
- Der Rumpf steht auf den Füßen und ist nur für die Plattenbelegung um 17° um die senkrechte Achse gedreht. Die Drehung ist in die neue Druckgeometrie eingerechnet. Das verhindert, dass Bambu eine viel zu große konservative, nochmals gedrehte Boundingbox anzeigt. Die zusammengesetzte Pose bleibt gleich.

## Drei Hauptplatten

| Platte | Inhalt | Material / Profil |
|---|---|---|
| 1 | Rumpf, Beine, Schwanz, Arme und Halsaufnahme | Braun 29 + Beige 31; 0,16 mm; Lightning 5 %, 2 Wände; automatische Baumstützen |
| 2 | Ganzer Kopf einschließlich Ohren und Aufnahme | Gleiche Braun-/Beige-Bemalung; 0,16 mm; Lightning 5 %, 2 Wände; automatische Baumstützen |
| 3 | Schwarze Nase, vier Augen-Klebeteile und massiver Halsverbinder | Schwarz 30; 0,12 mm. Nase/Augen mit Raft und Stützen; Schlüssel mit eigenen massiven Einstellungen und ohne Raft/Stützen |

Kein Mixed Filament. Bestandsspulen wie bisher: ELEGOO PLA Matte Earth Brown (#805947), Bambu PLA Basic Beige (#F7E6DE), eSUN ePLA-Lite Black (#272729). Braun linke Düse, Beige rechte Düse, Schwarz auf der schwarzen Platte rechte Düse. Tatsächliche AMS-Fächer beim Druck auswählen; Slotnummern sind keine zugesagte AMS-Fachbelegung.

„No sparse layers“ am Spülturm bleibt bei diesen Großprojekten ausgeschaltet. Turm und Druckausrichtung so belassen, wie sie gespeichert sind; automatisches Neu-Anordnen verändert die geprüfte Belegung.

## Größe und tatsächliche Slicerprognose

| Gesamtfigur | Rumpf ungefähr | Kopf ungefähr | Gesamtprognose inkl. schwarzer Teile und Slicerzusätzen |
|---|---|---|---|
| 470 mm | 280,6 × 298,1 × 297,2 mm, auf Platte gedreht | 231,8 × 194,1 × 188,0 mm | 56 h 39 min / 974,02 g |
| 500 mm | 298,5 × 317,2 × 316,1 mm, auf Platte gedreht | 246,6 × 206,4 × 200,0 mm | 63 h 31 min / 1.118,65 g |

50 cm ist die hier praktisch geprüfte große Ausführung, keine Aussage über das mathematische Optimum aller denkbaren Orientierungen. Der 50-cm-Rumpf nutzt den gemeinsamen H2D-Düsenbereich eng aus: kleinste geprüfte Extrusionsreserve zur gemeinsamen X-Grenze etwa 0,52 mm, zur Y-Grenze etwa 1,21 mm. Die 47-cm-Variante bietet deutlich mehr Reserve. Keine Maschinen-/Düsenhöhen künstlich erhöht.

Die Nasengeometrie und ihr bisheriger Anschluss sind wie die Figur mitvergrößert: ihr ursprünglicher 0,05-mm-Abstand wird etwa 0,131 mm bei 47 cm bzw. 0,139 mm bei 50 cm. Diese größere Nasenpassung ist physisch ungeprüft; gegebenenfalls Klebung oder eine separat kalibrierte Nasenrevision. Die vier Augenteile bleiben bewusst Klebeeinsätze. Der **neue Halsverbinder** hat in beiden Gesamtgrößen dieselben tatsächlichen Steckmaße und 0,10 mm Abstand.

## Erst die Halsprobe

Die separate Probe enthält zwei Platten:

1. Zwei Halsaufnahmen in **demselben braunen Filament**, 0,16-mm-Schichten. Eine bildet die Kopfaufnahme einschließlich selbsttragendem Dach nach, die andere die Rumpfaufnahme.
2. Derselbe massive schwarze Schlüssel, **0,12-mm-Schichten** wie am großen Modell.

Beide Platten wurden tatsächlich ohne Stützen geslicet und auf Extrusionswege geprüft. Gesamtprognose etwa **1 h 58 min / 57,35 g**. Die Probe testet Schlüssel, Aufnahmen, Dach, Materialpaar und Schichthöhen; sie ist ausdrücklich kein physischer Test der vollständigen organischen Außenfuge. Kopf- und Schlüssel-Schichthöhen wurden auf getrennte Platten gelegt, weil Bambu unterschiedliche Schichthöhen bei gemeinsamem Spülturm ablehnt.

Nach vollständigem Abkühlen Brim entfernen. Der Schlüssel soll ohne Gewalt vollständig einsteckbar sein, und die Aufnahmen sollen zusammenkommen, bevor der Schlüssel oben/unten anstößt. Erst nach dieser Rückmeldung die große Halsverbindung real freigeben. Der Agent startet weder Probe noch Großdruck.

## Montage

1. Rumpf und Kopf von Stützen/Brim befreien. Die sichtbare äußere Halskontur erhalten; Grate nur an den verdeckten Auflagen und Aufnahmeöffnungen vorsichtig entfernen.
2. Schlüssel mit der großen Eckfase zur passenden Ecke in die Rumpfaufnahme einsetzen.
3. Kopf senkrecht absenken. Die geschwungene Kontur bestimmt die Lage; die Auflageflächen sollen schließen. Bei Widerstand die Ursache prüfen statt zu pressen.
4. Nase einsetzen bzw. bei zu loser Passung kleben, vier Augen-Klebeteile zuordnen und befestigen. Größen nicht mit den alten 180-/320-mm-Gesichtsteilen verwechseln.

## Verifikation und Grenzen

[Maschinenlesbarer Nachweis](mochi-neck-split-verification.json) bindet die konkreten Projektdateien an tatsächliche Slices und G-Code-Hashes. Beide Gesamtgrößen: drei echte Slices, vollständige unabhängige Extrusions-Footprints einschließlich G17-I/J-Bögen, gemeinsame H2D-XY-Grenzen eingehalten. Alle acht Teile sind geschlossene Einzelkörper. Kopf-/Schlüssel-Auszug wurde über 45 mm an 16 Positionen geprüft. Neue Innenflächen und Bohrungen wurden gegen das Originalvolumen geprüft. Die Auflage des gedruckten Kopfes hat im Modell einer homogenen Dichte einen positiven Schwerpunktabstand zum Standpolygon; reale Füllung, Stützen und Haftung bleiben physische Einflüsse.

Zwei tatsächliche native Speicher-/Ladedurchläufe pro Hauptprojekt erhalten Geometrie und alle nativen Bemalungscodes. Globale Ressourcenkennungen sind für alle externen Meshdateien eindeutig, auch bei drei Platten. **514 Python-Tests in 53,05 s** und beide Frontend-Harness bestanden. [JUnit](test-results-mochi-neck-split.xml).

Keine manuelle GUI-Abnahme der neuen Datei behauptet. Diskrete Pfad-/Oberflächenprüfung ist keine vollständige dynamische Düsen-/Kollisions- oder Statikzertifizierung. Die reale Halsfuge, Steckkraft, Haftung und Montage sind noch nicht gedruckt und geprüft. Keine kostenpflichtigen API-Aufträge, keine Originale überschrieben, kein Druckstart.

[Erneute vollständige Rekonstruktion](mochi-neck-reproduction.json) aus derselben Quelldatei erzeugt identische Vertex-/Face-Arrays und native Bemalungslisten für Rumpf, Kopf und Schlüssel.

Werkzeuge: `prepare_mochi_neck.py`, `mochi_neck.py`, `build_mochi_neck.py`, `build_mochi_neck_fit.py`, `verify_mochi_neck.py`, `review_mochi_neck.py`. Der Konstruktor lehnt ein aus einem anderen Zielmaß gecachtes Gelenk ab, damit echte Steckmaße beim Vergrößern nicht versehentlich mitwachsen.
