# Buddy – lokale Produktionsprüfung

Stand: 16.10.2026. Digitale Geometrie-, Slice-, Vollpfad- und Mainexportprüfung abgeschlossen. Keine physische Druck-/Lastfreigabe und keine kostenpflichtigen Aufrufe. Die hier dokumentierten Benchmarkskripte ändern keine Projekte/Freigaben; reguläre API-Integration wird separat protokolliert.

## Verifizierter Arbeitsstand (neuester Überblick)

- Geometrie vollständig reproduziert: **37 geschlossene zusammenhängende Teile**, sourcegebundene anatomische Schnitte, Halsband-Montagefolge und Strukturbaum. Sichtbare Quelle bleibt bis auf dokumentierte Blender-Float32-Genauigkeit erhalten; Originaldatei unverändert.
- Aktuelle Druckplanung: **34 Platten**, gemeinsamer H2D-Raum 300×320×320 mm lokal / X25–325 mm real, mindestens 10 mm Rand und **20 mm Objektabstand** für tatsächliche Tree-Stützen; zwei Spulen maximal, konkreter Towerbereich reserviert. Nasenschlüssel auf eigener Platte senkrecht +Z; gerundete Sichtfläche benötigt ggf. Support.
- Alte 28-/29-/31-Platten-Ausgaben sind dokumentierte Zwischenstände. Nach 8-mm-Randfehler (-102) und echter 5-mm-Supportkollision (-101) wurden die Gates beibehalten und die Packung korrigiert.
- Die bisher geometrisch berührende Halsring-Innenfläche erhält jetzt echte **0,05 mm radiale Schiebefreiheit**: nur die innere Ringbohrung wird erweitert; nominaler Körperzylinder und sichtbare Außenkonturen bleiben erhalten. Der vollständige neue Solid-/Montagefolgenlauf besteht mit 37 Teilen in 142 Sekunden; exakt 35 Teile bleiben bitgleich.
- Fünf tatsächliche Bestandsspulen und offizielle/als Generic gekennzeichnete unkalibrierte H2D-Profile. Über alle 37 Teile **null unterschiedliche Facefarben zwischen Vorschau und nativen Slots**.
- Endgültiger Materialstand: exakt 1.058 bestätigte Quellflächen korrigiert (Lederlichter und einfarbiges Emblem); alle realen Spulen und Quellgeometrie erhalten. Der reguläre Mainplan `f3428f…` ist in sämtlichen Flächen-/Materialfeldern identisch zum geprüften Kandidaten.
- **Alle 34 endgültigen nativen Platten bestehen ihre tatsächlichen CLI-Slices und vollständigen unabhängigen GCode-Footprintprüfungen.** Die tatsächlichen nativen Dateien des regulären Main-ZIP sind in Geometrie, FacePaints, Welttransforms, vollständigen Settings, Extruderdefaults und Packungsbytes exakt zu diesen geslicten Referenzen abgeglichen. Keine physische Druck-/Lastfreigabe; erneute Bambu-GUI-Sichtung bleibt wegen gesperrtem Mac offen.
- Aktuelle Slicer-Schätzung dieser 34 tatsächlichen Varianten: **1.042,93 Druckstunden und 25,328 kg PLA**, mit unveränderten offiziellen 2 Wänden/15 % Infill. Reale Lasten, Stabilität und Materialkalibrierung bleiben offen; vor einem Druck braucht diese Größenordnung eine bewusste Nutzerentscheidung. Keine heimliche Profil-/Infillabsenkung.
- Augen links/rechts und kleine Halskontur collar-neck-1 sind drei ausdrücklich stiftlose Klebe-/gefangene Teile. Die aktuelle deutsche Montagefolge rekonstruiert zuerst die 24 Struktur-Schnittpaare und danach den noch kopflosen Hals in seiner tatsächlich geprüften Reihenfolge.

Die folgenden Abschnitte bewahren die Befunde und verworfenen Versuche chronologisch; frühere Zwischenstände sind keine Behauptung über den aktuellen Druckstand.

## Quelle und Maßstab

Projekt `2c9a7959d13a438fbeb5b8340d8eefd4`, menschlich freigegebenes Mesh `5d60b394adfbf92e46b0b6d3a70fbbeb2b02d3284557297a48aba5cad14f43af`.
Arbeitskopie-SHA256 `1fbf9afb006d912cb612702232d7eb0e194e35407ad0e293b6550b4337bce61c`.
150.000 Dreiecke, ein geschlossenes positives Volumen. Zielhöhe 1.000 mm; Gesamtmaße ca. 500 × 1.240 × 1.000 mm.
Ursprünglicher Referenzplan `64833d22e43f0c5cac360f0ffdae5d9a5b5f0e32b1671dccbf9dabb7eac834fe` wurde nur gelesen. Der neue anatomische Vorschlag ersetzt dessen sechs Farbcluster ausdrücklich durch acht semantische Regionen; spätere reguläre API-Versionen sind eigene Artefakte.

| Befund → Korrektur | Beleg | Offen / Auswirkung |
|---|---|---|
| Automatische sechs Farbtöne erzeugen 2.663 Zusammenhangskomponenten → anatomische Bauteile anhand tatsächlicher Form prüfen; Fellschatten bleiben Farbwirkung. | `benchmarks/buddy-production/review-bf7b18bf10fb4a87b134cf7f0f8d2d81/source-analysis.json` | Viele Mini-Bedienelemente oder Einzelteile wären weder verständlich noch praktisch montierbar. |
| Kopf-/Halsband-/Rucksackfarbgruppen sind keine garantierten Steckteile → separate geometrische Extraktions- und Kappenprüfungen. | Quelle und gespeicherter Farbplan; weitere Versuche folgen unten. | Keine behauptete Montagefähigkeit aus Farbe allein. |
| Gesamtlänge übersteigt einen Meter trotz 1.000-mm-Zielhöhe → Zielhöhe und reale XYZ-Maße getrennt berichten; Strukturteilung für H2D nötig. | Quellenbounds: X ±249,810; Y ±619,893; Z 0–1000 mm. | Höhe allein unterschätzt Plattenzahl, Material und Montageaufwand. |
| Erste Mochi-Nasenprobe mit 0,20 mm radial lose und mit fehlerhafter Druckorientierung → keine ungeprüfte globale Toleranzsenkung. | Reales Nutzerfeedback; neue Viererprobe 0,05–0,20 mm vorbereitet. | Buddy-Toleranzen bleiben vorläufig und verlangen einen physischen Test im verwendeten Material. |

## Sichtprüfung und Konstruktion

Acht lokale orthogonale Blickrichtungen werden aus unveränderten Quellflächen gerendert. Masken und Konstruktionsversuche werden in neuen Benchmarkordnern aufbewahrt. Ergebnisse und verbleibende Grenzen werden nach jedem belegten Schritt ergänzt.

## Konstruktionsbefunde → Maßnahmen

| Befund → Korrektur | Beleg | Offen / technische und UX-Auswirkung |
|---|---|---|
| Einfacher Min-Cut liefert eine anatomische Kontur, aber seine Innenkappe kann außerhalb des Hundes liegen → experimentelle Kappe nur innen anpassen, Außenflächen unverändert lassen; identische strenge Quellabstands-, Solid- und Montageprüfungen. | `review-bf7b18bf10fb4a87b134cf7f0f8d2d81/anatomy-probes.json`, `cap-fit.json` | Keine universelle automatische Reparatur behaupten. Konstruktionsfehler müssen Kontur/Kappe und betroffenes Teil benennen. |
| Jedes Ohr besitzt zwei Kontaktflächen mit verschiedenen Normalen. Der vorhandene Ganzteilpfad gibt dann nur einen Warnhinweis und keinen gemeinsamen Pfadtest aus → für Buddy sämtliche Ohrstifte parallel zur gemeinsamen ±X-Richtung konstruieren und tatsächlich prüfen. | `cap-fit.json`: drei Stifte, aber `path_check=null`; `growth-probe.json`: gemeinsame 40-mm-Auszüge bestehen. | „Steckbar“ darf bei mehreren Kontaktflächen nicht aus einer bestandenen Geschlossenheitsprüfung folgen. Allgemeine API-Integration des gemeinsamen Richtungswegs offen. |
| Winzige echte Hinterschneidungen am ursprünglichen Ohrrand blockieren die Montage → Auswahl am rechten Ohr 2 mm, links 5 mm über geodätischen Abstand erweitern. | `growth-probe.json`: rechts vorher 0,0459 mm, links vorher 0,0343 mm Stichprobenpenetration; akzeptierte Varianten jeweils 0 mm. | Grenztoleranz wurde nicht vergrößert. Die Schnittkontur ist leicht erweitert, die sichtbare Originaloberfläche bleibt unverformt. |
| Ein proximaler Schwanzschnitt schneidet zugleich kleine Hinterbeinfragmente im Halbraum ab → nur Hauptschwanz trennen, Fragmente vollständig am Rumpf behalten. | `tail-plane.json`: Y=275,000137 mm, zwei Fragmente zurückgegeben, Außenfläche und Volumen erhalten; zwei Stifte, 40-mm-Auszug bestanden. | Nicht mit lösbaren Kleinstteilen oder gelöschten Fragmenten exportieren. Der Schwanz braucht eher eine zusätzliche Strukturteilung als einen falschen Schnitt weiter in der Mitte. |
| Die dunkle Nase ist nicht automatisch eine frontal ausziehbare Kontur → mehrere Masken/Kappen geprüft; blockierte Versuche nicht als fertige Nasenteile ausgegeben. | `common-axis.json`, `growth-probe.json`: trotz Erweiterung 2–20 mm Montageblockade. | Nase vorerst Bestandteil des Kopfes. Eigene schwarze Materialfläche/native Zweifilamentzuordnung und bessere Kontur weiterhin nötig. |
| Rucksack, Riemen und Halsband wickeln sich um den Körper → kein einzelnes flaches Inlay aus der gesamten Farbe erzwingen. | `anatomy-probes.json`: Rucksackschleife nicht einfach projizierbar. | Anatomische Ausrüstung muss in Richtungspatches oder eigenständige umlaufende Baugruppen zerlegt werden. Reine Plattenfähigkeit löst die regionale Materialzuordnung nicht. |
| Automatische Strukturteilung kann mehrere lose Beine in einem Mesh bündeln; geerbte Stiftmetadaten beziehen sich anschließend auf alte Elternteile → Buddy teilt nur verbundene Halbraum-Hauptkomponenten, behält Fragmente im Rest und schreibt einen expliziten Montagebaum. | `scripts/verify_buddy_construction.py`, je Lauf `structural-progress.json` | Jeder exportierte Artikel wird auf genau einen geschlossenen Körper geprüft. Strukturpfade gelten für Geschwisterteile im Montagebaum; kein pauschaler globaler simultaner Auszug behauptet. |

Ein erster Strukturierungsdurchlauf stoppte nach vier Schnitten: Beim alleinigen Abtrennen der größten positiven Halbraumkomponente wurden die übrigen Beine zu mehreren Restkörpern. Korrektur im Buddy-Experiment: Beide Vorzeichen und alle drei Achsen ausprobieren, jeweils nur einen verbundenen Körper abtrennen. Ein nicht verbundener Rest wird weiterhin abgelehnt; Fehler werden mit Teil-ID, Quellengeometrie und Versuchsliste aufbewahrt. Das ist eine gezielte Verbesserung gegenüber blindem Bündeln loser Komponenten.

## Erster vollständig exportierter Geometriesatz

`benchmarks/buddy-production/construction-790b6d1f615c4403a1651431f8f66ec0/`

- **24 einzelne geschlossene Körper, 21 H2D-Platten**, alle Platten innerhalb des gemeinsamen X-Bereichs 25–325 mm, Y 0–320 mm, Z 0–320 mm.
- Zwei organische Ohren mit je drei Stiften; proximale Schwanzwurzel mit zwei Stiften. Gemeinsame anatomische Kollisions-/Auszugstests bestanden.
- **20 weitere Strukturteilungen, 38 Strukturstifte**. Sämtliche zugehörigen 40-mm-Geschwister-Auszüge bestanden, maximale Stichprobenpenetration 0 mm. Montagebaum im Bericht; keine vollständige globale Montage-/Tragfähigkeitszertifizierung.
- **46 Core-3MF-Dateien** geometrisch zurückgelesen, geschlossen und mit numerischem `printable="1"`. Volumendifferenz durch vorgesehenes Verbinder-Spiel ca. 22.606 mm³ bei 99.747.968 mm³ ursprünglichem Vollvolumen.
- `review.html`: eigenständige Offline-Datei mit eingebetteter Originaltextur, neuen Geometrieteilen, Explosions- und Plattenansicht. Keine CDN-/Serverabhängigkeit. JavaScript-Syntaxprüfung bestanden; die Quellform wurde tatsächlich aus acht gedrehten Ansichten betrachtet.
- **Noch kein fertiges Farb-Druckpaket**: Core-Teilefarben sind ausdrücklich Platzhalter. Halsband, Rucksack, Nase und Karte brauchen eine geometrisch vollständige regionale Materialzuordnung mit realen Filamenten. H2D-Slicing, Support, Filamentverbrauch und physische Belastbarkeit stehen noch aus. Das bestehende freigegebene Mesh und der gespeicherte Farbplan bleiben unverändert.

## Material- und Konturprüfung nach dem ersten Paket

Einzelne große Halsband-, Rucksack-, Nasen-, Sohlen- und Kartenflächen wurden zusätzlich in sechs Richtungssektoren untersucht (`material-patches.json`, `material-no-clean/material-patches.json`). Ein Teil besteht; andere scheitern korrekt an lokaler Dicke, gefalteter Projektion, Konturverzweigung oder echtem Montageweg. Erfolgreiche Einzelversuche werden nicht als bereits kombinierte vollständige Materialzerlegung ausgegeben.

**Befund → Korrektur:** `clean_small_islands` bearbeitet bei der Vorbereitung auch kleine Grundkörper-Inseln. Bei Richtungspatches können damit nachträglich Flächen mit unzulässigen Normalen zum Inlay kommen. Nur den Flächenfilter abzuschalten lässt punktberührende Konturen übrig. Daher neue isolierte Hilfsfunktion `geometry/patch_masks.py`: ausschließlich 1–3 kompatible Quellnachbarflächen pro Reparatur hinzufügen, ursprüngliche Auswahl und Originalgeometrie erhalten. Verbotene Nachbarn werden respektiert, fehlende Lösung bleibt ein Fehler. Zwei gezielte Tests bestehen. Die Hilfsfunktion ist noch nicht pauschal in die Produktion eingebaut.

Die reale Buddy-Prüfung damit steht unter `material-compatible-repair/material-patches.json`: Verzweigungen lassen sich teils mit wenigen Quadratmillimetern zusätzlichen Quellflächen beheben. Danach bleiben andere, echte Hindernisse sichtbar; **Grenzwerte für Richtung, lokale Dicke oder Montagekollision wurden nicht gelockert**.

Eine gesonderte Material-Abdeckungsanalyse (`part-material-coverage.json`) zeigt: Selbst beim lediglich vorgeschlagenen Zusammenfassen der drei Goldschattierungen liegen auf **10 der 24** bisherigen Geometrieteile drei oder vier Materialklassen. Ein nativer H2D-Zweifilamentexport muss diese Teile weiter zerlegen oder eine ausdrückliche regionale Farbvereinheitlichung prüfen; stilles Ignorieren der dritten Farbe ist ausgeschlossen. Goldschattierungen können Fell/Beleuchtung enthalten; diese vereinfachte Analyse ist **keine Farbfreigabe**.

**UX-Befund → Korrektur:** Strukturkacheln erben im aktuellen Konstruktor die Rolle `body`, der Viewer bewegt aber nur andere Rollen in der Explosionsansicht. Dadurch bleiben die meisten Strukturteile scheinbar zusammen. Buddy-Offline-Review `review-v2.html` korrigiert nur die Darstellungsrolle; ursprüngliche `review.html` bleibt erhalten. Eine entsprechende allgemeine Produktionskorrektur ist separat erforderlich. Teileübersicht mit zurückübertragenen Quellfarben und grauen Innenflächen: `parts-source-review-v2.png`.

**Druckgrenzen:** Die automatisch gepackten Teile haben mehrere Verbindungsrichtungen. Nicht alle Stifte lassen sich gleichzeitig senkrecht drucken; Slicer-Support muss die jeweiligen Funktionsflächen schützen. Geometrisch passender positiver Freiraum belegt keine Haltekraft. Die 12-mm-Schlüssel sind zur Ausrichtung konstruiert; die reale Last-/Klebe-/Reibverbindung und die gesamte Standfestigkeit des ein Meter großen Hundes sind noch nicht geprüft.

## Weitere belegte Korrekturen: vollständige Nase und gerollte Karte

**Nasenbefund → Korrektur:** Die erste angepasste Kappe überschnitt an genau einem originalen sichtbaren Nasenpunkt den Restkörper um 0,143 mm. Eine Prüfung der Distanzänderung bei 0,02-mm-Bewegung bestätigt die Konsistenz des Distanzverfahrens; kein Anlass, die Montageprüfung zu lockern. Den ausschließlich inneren Kappenanker 2 mm weiter in den vorhandenen Körper gelegt, sichtbare Nasenfläche und Kontur beibehalten. Damit zwei Ø12×10-mm-Schlüssel und 40-mm-Auszug mit 0 mm Stichprobenpenetration bestanden. 1 mm blieb blockiert; 5/10/20 mm bestanden ebenfalls. Gewählt wird die kleinste funktionierende 2-mm-Variante (`nose-cap-depth.json`, `nose-distance-diagnostic-v2.json`).

Kombiniert neu gerechnet: `construction-73227146019145d4b612971fe6f7ed3f/`, **25 geschlossene Teile / 22 Platten**, zehn anatomische Schlüssel, 38 strukturelle Schlüssel. Originale des ersten 24-Teile-Experiments bleiben erhalten. Diese Nase ist jetzt Bestandteil des reproduzierbaren Skripts; der vorherige Nasen-Offenpunkt oben ist dadurch geometrisch überholt.

**Kartenbefund → Korrektur:** Die gerollte Karte benötigt eine eigene räumliche, leicht geneigte Auszugsrichtung. Min-Cut um ihre tatsächliche Cremefläche plus 2-mm-Innenanker liefert ein geschlossenes Teil von etwa 116 × 85 × 125 mm, zwei Ø6×6-mm-Schlüssel und einen bestandenen 40-mm-Auszug ohne Stichprobenpenetration (`small-accessories-depth.json`). Der Kompass blieb dagegen mit 2/5/10-mm-Kappenankern kollidierend und wird nicht als fertiges Teil ausgegeben. Die Karte wird vor Ohren/Schwanz in den kombinierten Lauf integriert.

Halsband-Versuche mit Viertelringen und engeren Winkelsektoren dokumentieren weiterhin mehrfach projizierte oder verzweigte Konturen. Die schräge Halsachse wird zusätzlich aus der Originalgeometrie bestimmt; eine feste horizontale Winkelaufteilung ist keine belastbare Annahme für diesen geneigten Hals. Diese Versuche verändern keine Quelldatei und werden nicht als erfolgreiche Produktion ausgegeben.

## Aktuellster kombinierter Stand

`construction-95ad9d66467b4d56b385e8b358ae17a9/`: **26 geschlossene Körper / 23 Platten**, einschließlich Nase, Karte, beiden Ohren und proximalem Schwanz. Zwölf anatomische Schlüssel, 38 Strukturstifte; kombinierte anatomische Montageprüfungen sowie alle Geschwisterprüfungen bestanden. Das bleibt ein geometrischer Zwischenstand mit ausdrücklich offenen regionalen Materialien.

**Halsband-Architektur → neuer Lösungsweg:** Der blaue Ring liegt um eine ca. 27° geneigte Halsachse. PCA-Messung: Achse `[-0,00683, -0,45605, 0,88993]`, Ringzentrum ungefähr `[-2,10, -314,61, 622,03]` mm. Ein umlaufender Ring braucht eine räumliche innere Mantelfläche; unabhängige flache Scheibenkappen sind dafür das falsche Modell. Lokaler Blender-Exact-Boolean mit einer analytischen Ringschale erzeugt tatsächlich einen geschlossenen Ring und einen geschlossenen Restkörper. Vier radiale Segmente mit parallelen Verbindungspins werden geprüft; noch kein bestandener finaler Ring-Montagebericht.

Blender 5.1.1 stürzte im eingeschränkten Toolprozess vor Python bei der Metal-Geräteerkennung ab. Der identische lokale Aufruf außerhalb der Prozess-Sandbox wurde automatisch zugelassen und lief mit zwei Threads. Annularer Schnitt: rund 2,0 s, Restkörper: rund 2,4 s. Keine Remesh-Operation, keine Cloud, keine Druckerkommunikation. Die Quelle bleibt unverändert; Blender-Ausgabekoordinaten besitzen die dokumentierte Float32-Genauigkeit. Direkte Viertelschnitte können an beinahe koplanaren Kanten leere oder nicht geschlossene Ausgaben erzeugen; solche Ergebnisse werden verworfen und nicht exportiert.

## Physische Passungsrückmeldung und echte H2D-Grenzen

Der Nutzer hat inzwischen den vertikal gedruckten Vierervergleich geprüft: 0,20 / 0,15 / 0,10 mm radiales Spiel halten nicht, 0,05 mm hält gerade mit geringem Restwackeln. **Neue Buddy-Versuche verwenden daher 0,05 mm radial**, auch für größere Verbindungen; 0,04 mm wird daraus nicht abgeleitet. Die alten Pakete mit 0,20 mm bleiben unverändert. Größere Stifte und Lastverbindungen benötigen weiter einen realen Belastungstest.

Die importierte H2D-Vorlage hat einen gemeinsamen Düsenbereich X 25–325, Y 0–320, Z 0–320 mm. Das Reproskript verwendet jetzt **300 × 320 × 320 mm mit 8 mm XY-Rand**, verschiebt die Platte um +25 mm X und dokumentiert jedes transformierte Teil einschließlich tatsächlichem maximalem Welt-Z. Diese Grenzen ersetzen die früheren 6-mm-Packversuche. Nach der zusätzlichen Korrektur der tatsächlichen abgefasten Schlüsselkontur im gemeinsamen Verbinder-Code wird vollständig neu gerechnet; alte Ergebnisse gelten nicht als Beleg für den neuen Stand.

## Halsband: geschlossene Geometrie ist noch kein Montagebeleg

Die vier Ringstücke sind jetzt einzeln geschlossene, verbundene Volumenkörper. Eine zuvor lose 5,53-ml-Quellkomponente wird ihrem benachbarten Ringviertel wieder angeschlossen; nichts wird gelöscht (`collar-quarter-retained-0.npz`). Blender-Manifold löst die problematischen Viertelschnitte zuverlässiger als Exact. Die ursprüngliche sichtbare Quellfläche bleibt bis auf dokumentierte Float32-Koordinatengenauigkeit erhalten.

Die übliche projizierte Verbinderwurzel schloss auf diesen gekrümmten Innenflächen nicht. Ein neuer lokaler Boolean-Versuch erzeugt stattdessen acht tatsächlich geschlossene Schlüssel-/Socketpaare mit 0,05 mm Spiel und vier geschlossene Ringteile plus geschlossenen Körper (`collar-key-checks.json`). **Die kombinierte Montageprüfung blockiert korrekt:** Das erste Ringviertel kollidiert beim Auszug mit dem Körper, maximal ca. 3,38 mm. Kein fertiges druckbares Halsband und keine Montagefreigabe wird behauptet. Nächste Korrektur muss den räumlichen Schnitt unterhalb/oberhalb der Ringschale an tatsächliche Hinterschneidungen anpassen, nicht die Kollisionsgrenze erhöhen.

## Augen: statische Prüfung zusätzlich zur Auszugsprüfung

Ein oberflächentreues linkes Augenstück mit vollständig erfasster Creme-/Pupillenfläche bestand den geraden Auszug knapp, scheitert aber bei zusammengesetzter Lage an ca. **0,0303 mm** gemessener Überschneidung. Größere Innenankertiefe ändert diesen Randkonflikt nicht. Quellnahe Maskenerweiterungen mit gefüllten kleinen Inneninseln erzeugen wiederum echte Rand-/Projektions- oder Montagefehler (`eye-left-grow-filled.json`). Die Grenze bleibt unverändert. Diese Einzelversuche werden weder ins Druckpaket aufgenommen noch als gelöste Augenzerlegung bezeichnet.

## Verifizierter Lauf mit 0,05 mm und Augen

**Ursache der Ohr-Überschneidung → belegte Korrektur:** Die zwei problematischen Messpunkte gehörten zur originalen sichtbaren Ohrfläche, nicht zu einem Steckstift (`ear-static-diagnostic.json`). Der innere Kappenanker war zu flach. Ausschließlich diesen Anker um 1 mm nach innen verlegt, sämtliche äußeren Quellpunkte und Konturen identisch belassen. Beide Ohren bestanden damit statisch und über 40 mm Auszug mit 0,05-mm-Steckerspiel (`ear-deeper-005.json`).

`construction-3b289296cf854f12bbeee2512220bf1a/`: **26 geschlossene Teile / 23 Platten**, 12 anatomische und 39 Strukturkeys, 50 Core-3MF zurückgelesen. Tatsächliches maximales Welt-Z **291,0001 mm**, XY-Rand 8 mm; alle anatomischen und Struktur-Geschwisterprüfungen bestanden.

**Augen-Innenkappe → Korrektur:** Der alte Kappentest betrachtete nur Mesh-Vertices. Zusätzlich Kantenmitten und Dreieckszentren geprüft und die innere Kappe mindestens einmal verfeinert, ohne ihre Quellkontur zu verschieben. Beim zuvor kaum verwendeten Verfeinerungspfad musste die Dreiecksorientierung erhalten werden; die falsche Fan-Reihenfolge führte sonst zu inkonsistenter Wicklung. Mittelpunkte werden für die Distanzabfrage gesammelt verarbeitet, statt VTK für jeden Punkt neu auszuführen. Nur im Buddy-Reproskript umgesetzt, keine allgemeine Herstellungsprüfung gelockert. Beide Augen bestehen damit auch den statischen und 40-mm-Montagetest. Die linke Variante liegt mit 0,0299 mm Stichprobenpenetration nahe am 0,03-mm-Gate und benötigt weiter eine physische Klebe-/Montageprobe.

Aktueller geometrischer Entwurf `construction-21e36ac646604fd48e5fefdeceef6204/`: **28 geschlossene Teile / 23 Platten**, inklusive beider Creme-/Pupillen-Augen, Nase, Karte, Ohren und Schwanz. Die Augen haben mit den geprüften Parametern **keine sicheren Stifte**; sie sind ausdrücklich als geschlossene **Klebeteile** markiert. Keine Steckpassung oder Klebespaltfreigabe wird dafür behauptet. Alle kombinierten anatomischen und strukturellen Stichprobentests bestanden. `part_region_ids` wird nach dem letzten Strukturzuschnitt für jede tatsächliche Teil-ID aus den Originalplanflächen bestimmt; innere Kappen werden nicht als neue Materialfarbe gewertet. Der ursprüngliche gespeicherte Farbplan bleibt unverändert.

## Halsband-Montagereihenfolge statt pauschalem Auszug

Ein kompletter Halsring kann vor Montage des Kopfes platziert werden. Diese Reihenfolge wurde konkret geometrisch untersucht. Der erste reine Kopf-/Unterkörper-Schnitt bestand für den Ring, scheiterte aber bei Einführen des Kopfes mit bis zu 7,8 mm an äußeren Halskonturen. Korrektur: zusätzlich am tatsächlichen oberen Bandende schneiden, mittleres Halsstück in seine echten zusammenhängenden Komponenten zerlegen und diese in zulässiger Richtung einzeln montieren. Schiebeflächen sind der analytische innere Ringmantel und die beiden Halsquerschnitte.

Beleg `collar-component-sequence-exact-band.json` (zuletzt mit `blender-collar-sequence-split-inside-band.py` berechnet): **Unterkörper → Ring → innerer Halszylinder und drei äußere Halskomponenten → Kopf**. Alle sieben Körper geschlossen und verbunden; jeder einzelne 80-mm-Auszug gegen die zu diesem Zeitpunkt bereits montierten Körper weist **0,0 mm** Stichprobenpenetration auf. Keine Quellfragmente wurden gelöscht. Die internen Schnittzuordnungen liegen 0,001137 mm innerhalb der analytischen Bandenden, um beinahe koplanare Float32-Artefakte zu vermeiden; das ist keine neue Passungstoleranz. Das ist ein erfolgreicher Montagefolgen-Vorversuch, noch kein fertiges Halsbandpaket: Ring für Bauraum teilen, reale Naht-/Halskeys ergänzen, gemeinsame statische Prüfung und finale kombinierte Konstruktion stehen aus.

## Vollständiger Service-Lauf und Materialprüfung (aktueller Stand)

`service-a2c9928e1a9349d1abdd9e8dde5209cb` reproduziert über `scripts/verify_buddy_service.py` den gekapselten Service: **37 geschlossene, jeweils zusammenhängende Teile / 28 materialbewusste Platten**, rund **172,5 s** lokaler Geometrieberechnung. Quelle/Hash/1.000-mm-Maßstab und sichtbare Originalkonturen sind gebunden. Die Halsband-Montagefolge und Struktur-Geschwisterprüfungen bleiben explizit; keine globale gleichzeitige Ausziehbarkeit oder physische Belastbarkeit wird daraus abgeleitet. Zwei Augen bleiben klar bezeichnete Klebeteile ohne sichere Stifte.

Der Vorschlag nutzt erlaubte reale Bestandseinträge: ELEGOO Earth Brown 29, ELEGOO Wood 33, ELEGOO Navy Blue 60, eSUN Black 30 und Bambu Beige 31. Die Bestands-HEX stammen aus der früheren Inventur und sind ungemessen. Ein grün benannter Eintrag hatte einen irreführend näheren dunkelblauen HEX-Wert: Navy wird deshalb ausdrücklich nach plausibler Spulenbezeichnung gewählt. Alte sechs Farbcluster-IDs werden nicht als neue anatomische Regions-IDs übernommen. Augeniris/Braun wird bewusst mit Schwarz vereinheitlicht; Augen bestehen nur aus Schwarz/Creme. Das bestehende Halsbandgold ist separat vom Fellgold markiert. V1 unterstützt ausschließlich feste Spulenfarben; Mixed wird ausdrücklich blockiert und nicht als editierbare Funktion versprochen.

### Tatsächliches Steckerspiel: bestätigter Fehler und Korrektur

Der erste Boolean-Stift lief von 0,85 R an der Spitze erst nach **L + 2 mm** auf R. An der tatsächlichen Schnittfläche L war er kleiner: R6/L10 ungefähr 5,85 statt 6 mm, dadurch effektiv ca. 0,20 statt 0,05 mm Spiel. Die ältere Behauptung einer tatsächlichen 0,05-mm-Passung dieser Boolean-Stifte war damit falsch. Alte Dateien bleiben als Versuchsstände erhalten.

`buddy_collar._primitive` erreicht jetzt R exakt bei **tip_z + L**, danach folgen 2 mm **konstante** Überlappung innerhalb des Elternkörpers. Ein echter Mesh-Querschnittstest mit R6/L10 und R2/L6 belegt Socket−Pin = 0,05 mm an der Wurzel und die konstante Überlappung; Spitze weiterhin Einführfase. Der oben genannte vollständige Service-Lauf wurde nach diesem Fix neu gerechnet. Reale größere Steckteile sind weiterhin nicht belastungsgeprüft. Der neu angepasste Couponvergleich wird separat protokolliert.

### Platten-/Vorschaufehler korrigiert

Die erste Plattenliste meldete die gesamte Materialbatch-Union, auch wenn eine konkrete Platte nur einen Teil davon enthielt. Jetzt entsteht `physical_filament_ids` aus den wirklich platzierten Teilen; Regression mit zwei großen Einfarbteilen auf zwei Platten bestätigt je eine Spule. Innenflächen der Vorschau übernehmen flächengewichtet die dominierende reale Spule über alle zugehörigen Regionen, entsprechend der nativen Zuordnung. Native Supports: Einspulenplatten explizit auf diese Spule, Zweispulenplatten AUTO anhand des geprüften tatsächlichen Objektdefaults; maximal zwei physische Spulen bleiben geprüft. Temperaturen werden nicht aus Spulenfarben erfunden.

### Native Ausgabe noch gesondert zu belegen

Die vorhandenen Core-3MF sind geometrisch prüfbare Pakete; sie beweisen keine native Farb-/Supportzuordnung. `scripts/build_buddy_native_template.py` baut eine neue Fünfspulen-Vorlage aus installierten offiziellen H2D-Profilen. Für ELEGOO und ePLA-Lite fehlt ein exakt passendes installiertes Herstellerprofil: offizielles Generic PLA wird unverändert als **unkalibrierter Ersatz** gekennzeichnet. Hardwaremetadaten stammen aus einer tatsächlich vorhandenen H2D-Vorlage. `scripts/verify_buddy_native.py` führt danach native Zuordnung, Export, lokales Slicing und unabhängige G-Code-Pfadprüfung pro Platte aus; kein Druckerauftrag. Solange der echte Lauf nicht erfolgreich dokumentiert ist, bleiben natives Slicing/Farbprofil und GUI-Abnahme offen.

Der CLI-Vorlagenbau stockte bei gesperrtem Mac bereits in `Initializing StaticPrintConfigs` (Timeout); dieser Systemzustand ist kein erfolgreicher Test. Nach Entsperren erneut versuchen. Offline-Bildreview ist mit `scripts/render_buddy_review.py` möglich; vollständige Textur bleibt zusätzlich im rotierbaren Review erhalten. Die PNG-Fassung nutzt Flächenabtastung und Backface-Culling und ersetzt keine Slicer-Vorschau.

## Native Smokeprüfung: reale Supportgrenzen und Druckaufwand

Die neue Fünfspulen-Vorlage ist tatsächlich durch Bambu CLI erzeugt: `benchmarks/buddy-native-template/profiles-bdfb896a74b1430ba040e0e2ebc9608b/buddy-real-materials-profile-only.3mf`. Fünf physische Profile, null erfundene Mischslots. Die gemeinsame Templateprüfung wurde anschließend so korrigiert, dass reine feste Farben keine fiktive Mixed-Rezeptur benötigen.

Native Face-Zuordnung gegen die Vorschau: **alle 37 Teile, null abweichende Dreiecke** (`verification-2faed440fe8144b992a9211ff9ed0a4a/preview-native-parity.json`). Dies prüft tatsächliche Slot-/HEX-Zuordnung einschließlich Innenflächen, keine kalibrierte Druckfarbwirkung.

Die erste native Platte mit 8 mm Rand scheiterte korrekt an Bambu-Validitätsprüfung -102: ein tatsächlicher Tree-Supportfuß erreichte **X24,843 mm**, knapp außerhalb des gemeinsamen X≥25-mm-Raums. Modell und Tower waren innerhalb. Buddy-Mindest-/Standardrand und vorgeschlagene Einstellung sind deshalb jetzt **10 mm**. Keine Validitätsprüfung wurde abgeschaltet. Mit 10 mm wurde dieselbe erste Platte **erfolgreich geslicet (return_code0)**: `benchmarks/buddy-native/verification-8297b3e32d1d4a908929f2110ce47e24/plate-01.3mf` und `slice-01/result.json`.

Die ursprünglichen 28 Platten enthielten keinen reservierten Prime-Tower. Die beiden Halsbandhälften belegten zusammen praktisch die ganze Fläche. Aktueller Packer reserviert bei zwei Spulen konservativ **45×80 mm** für einen **35-mm-Tower**, dessen konkrete Weltposition mit H2D-X-Offset gesetzt wird. Das volle Halsband wird deshalb auf zwei Platten verteilt: **29 Platten**. Die echte G-Code-Footprintprüfung bleibt zusätzlich erforderlich; rechteckige Reserve allein ist kein Slicerbeleg.

**Konkreter Aufwand der ersten großen Platte:** vom Slicer prognostizierte **272.266 s = 75,63 h**, etwa **1.891,93 g PLA** einschließlich Tower/Support. Geerbtes Prozessprofil: 0,20-mm-Layer, 15 % Infill, zwei Wände; keine unbemerkte Absenkung zur Schönrechnung. Zwei Wände und geometrisch gültige Keys beweisen keine Großbau-Festigkeit, Kippstabilität oder Tragfähigkeit. Gesamtmaterial/-zeit und eine reale Druckkostenentscheidung folgen erst aus der vollständigen 29-Plattenprüfung; nichts wurde an einen Drucker gesendet.

Die erste unabhängige Pfadprüfung nutzte einen noch geladenen alten Arc-Parser und stoppte an einem nicht druckenden Startup-Helixkommando. Der aktualisierte Parser überspringt ausschließlich solche nicht druckenden Startbewegungen; vorhandener G-Code wird neu geprüft, kein erneutes Slicing allein deswegen. Der zusätzliche prozesslokale Test `-ApplePersistenceIgnoreState YES` wurde von Bambu CLI als ungültige Option abgelehnt und nicht dauerhaft übernommen. Keine globalen macOS-Defaults oder Fensterzustände wurden gelöscht.

## Weitere belegte Druckkorrekturen

Ein erster 29er-Nativlauf scheiterte korrekt mit **-101** an echten Supportpfadkonflikten zwischen `tail-a` und `collar-body-a-b-b-b-a`. Fünf Millimeter Objektabstand genügen für diese Tree-Stützen nicht. Der Buddy-Packer verlangt jetzt ausdrücklich mindestens **20 mm**, Default und vorgeschlagene Einstellung sind identisch; niedrigere Nutzereingaben werden klar abgewiesen. Dadurch entstanden zunächst31Platten. Kein `--no-check`, keine gelöschten Stützen und keine vergrößerte Kollisions-Toleranz.

Eine anschließende konkrete Orientierungskontrolle zeigte Nasenstifte horizontal und keine flächige Bettauflage. Die Nase wird jetzt separat mit **Schlüsselachse +Z** gepackt, analog zur sinnvollen Passungsprobenorientierung. Raft/Tree-Stützen sind aktiv; Supportnarben auf der gerundeten sichtbaren Nasenfläche sind eine reale mögliche Folge und kein angeblich überhangfreies Design. Aktuell32Platten: erste30Platten sind exakt JSON-identisch zur gestarteten31erPrüfung; nur die letzte Farbteilplatte wurde in Karte/Augen und Nase aufgeteilt. Native Prüfbelege werden diesen konkreten Platten zugeordnet, nicht rückwirkend umbenannt.

Die Vorschau hatte zusätzlich künstliche dunkle Nahtbänder, weil gemittelte Teil-Vertexnormalen innere Kappen in die Außenflächenbeleuchtung einbezogen. Jetzt stammen Außenflächen-Normalen aus der unveränderten Originaloberfläche; Kappen/Keys bleiben explizit flach. Ein Regressionstest belegt unveränderte Meshpunkte und Faces. Dies korrigiert **nur Beleuchtung**, fügt keine Gesichtsdetaillierung hinzu und ersetzt keine geometrische Facetten-/Farbgrenzenverbesserung. Kleine Augenfarbränder bleiben durch die Quellface-Auflösung begrenzt.

Die vollständige deutsche Montageanleitung kann als reine Funktion `assembly_instructions(report)` aus einem bestehenden verifizierten Bericht erzeugt werden; kein neuer Geometrieauftrag und keine erfundene Projektfreigabe sind nötig.

## Neuester Pack- und Ringstand: 34 Platten

Auch die gemeinsame kleine Farbteilplatte scheiterte mit realen Tree-Stützen außerhalb des H2D-Gemeinschaftsraums (-102), trotz 10 mm Modellrand. Deshalb erhalten **gerollte Karte, linkes Auge, rechtes Auge und Nase je eine eigene, zentrierte Platte**. Die ersten 30 großen Platten bleiben geometrisch exakt unverändert; die letzte Sammelplatte wird durch vier gut zuordenbare Einzelplatten ersetzt. Insgesamt aktuell **34 Platten**. Nase: Schlüssel +Z; Augen: sichtbare Seite +Z und Stützen auf der angepassten Rückseite; Karte: sichtbare Seite +Z, Schlüssel -Z und Stützen an der verborgenen Wurzel. Raft/Tree-Unterstützung wird tatsächlich geslicet und nicht als überhangfreie Fertigung ausgegeben.

Im Montageaudit fiel zusätzlich eine echte Passungslücke auf: identischer Annuluscutter für Halsring und Restkörper erzeugte **null nominelles radiales Schiebespiel** am großen inneren Halszylinder. Bestandene digitale Berührpfade beweisen dort keine FDM-Schiebepassung. Jetzt bleiben Körpercutter und nominaler Zylinder identisch, während ausschließlich der Ringcutter eine um **0,05 mm** größere innere Bohrung erhält. Ein analytischer Mesh-Test belegt reale radiale Differenz, gleiche äußere Abmessungen, gleiche Höhen und geschlossene Volumen. Der vollständige sourcegebundene Buddy-Lauf wird danach neu durchgeführt; bestehende Druckbelege werden nur bei belegter Geometrie-/Einstellungsparität weiterverwendet. Alte Dateien bleiben erhalten. Großring-Passung und Materialschrumpfung sind weiterhin real zu prüfen.


## Korrekte Verbindungszählung und letzter nativer Randbefund

Die bisherige Summe von 15 in den endgültigen `parts[].connectors` war keine Gesamtzahl: Strukturkinder tragen absichtlich keine Connectorobjekte aus früheren Schnittebenen. Der neue reine `connection_summary(report)` wertet die tatsächlich konstruierten Verbindungen im Montagebaum aus: **68 Schlüssel-/Taschenpaare an 32 Schnittverbindungen**, davon Anatomie 12/5, Halsband/Hals 8/3 und Struktur 48/24. Er benennt 27 tatsächliche Strukturblattteile und die drei expliziten Klebe-/gefangenen Teile. `collar-right` ist trotz leerer männlicher Stiftliste kein Klebeteil: seine Taschen gehören zur Ringschließung. Es werden keine lokalen Stiftpositionen an Kinder erfunden. Beleg: `docs/buddy-assembly-connections-verification.json`; gezielte Tests bestehen. Diese Metadatenkorrektur verändert keine Geometrie.

Der vollständige 34-Platten-CLI-Sweep `verification-b9d9de6a388c4699882d2186299b2b13` isoliert zwei weitere echte -102-Fälle. Platte 18: Support X10,602–189,848 mm überschreitet links den realen gemeinsamen Bettrand X25; die Hülle passt nach reiner X-Zentrierung. Platte 30: Support X20,768–328,756 mm ist 308 mm breit und passt deshalb nicht durch Verschieben in 300 mm gemeinsames X. Eine 90°-Drehung in XY erhält die Support-/Schwerkraftrichtung und nutzt320 mm gemeinsames Y. Die gemessene Hülle wird zentriert; anschließend sind neue tatsächliche Slices und Footprints erforderlich. Kein Stütz- oder Bauraumgate wird abgeschaltet.

Der Towerreserve wurde wegen tatsächlicher 50,2-mm-Rippenbreite von 45×80 auf 55×85 mm erweitert. Die tatsächlichen Toweranker, alle Modellpositionen und native Einstellungen des laufenden Sweeps bleiben dadurch identisch (`tower-reserve-parity.json`); nur die konservative Reservemetadatenfläche wächst. Gezielte Korrekturen18/30 erhalten eigene neue Belegordner; alte Dateien bleiben unverändert.


Nach tatsächlicher Anwendung der XY-Drehung besteht auch Platte 30 sowohl den CLI-Slice als auch den vollständigen unabhängigen Footprinttest (`verification-b80dbbdfbcac456980bbcb3e6eabd0b0`); Platte 18 besteht beide Gates in `verification-5e81a7e9126e4411a789b8bb44887c07`. Ein zunächst vor der Ring-Separierung platzierter Hook hatte keine Wirkung und erzeugte erneut denselben alten GCode; dieser Implementierungsfehler ist korrigiert und durch einen gezielten Split-vor-Rotation-Regressionstest abgedeckt. `benchmarks/buddy-native/final-pack-parity.json` belegt exakt unveränderte native Packinputs für 32 andere Platten.

Vorläufige Summe der34 tatsächlich erfolgreichen Slices, noch vor dem separat visuell bestätigten Lederlicht-Repaint: **1.052,11 Druckstunden und 25,475 kg PLA** laut Bambu-Slicer. Das entspricht etwa 43,8 Tagen reiner geschätzter Druckzeit, ohne Ausfälle, Montage oder parallele Drucker. Beleg `benchmarks/buddy-native/preliminary-34-slice-costs.json`; offizielles Profil mit 2 Wänden/15 % Infill unverändert. Das ist weder eine Preisangabe noch eine physische Stabilitätsfreigabe. Materialbedarf und Tragfähigkeit des 1-m-Modells erfordern eine ausdrückliche spätere Druck-/Kostenentscheidung; keine heimliche Infillabsenkung zur Beschönigung.


## Bestätigte Materialkorrektur und erneute native Prüfung

Nach persönlichem Original-/Vorschlagsvergleich hat Root zwei eng begrenzte Materialkorrekturen akzeptiert: 61 vollständig lederbraun umschlossene Goldlicht-Komponenten (1.053 Quellflächen) werden Braun; fünf bisher braun klassifizierte Emblemflächen werden Gold. Das Emblem bleibt geometrisch einschließlich Ring und Facetten erhalten. Die große tatsächliche Fellfläche bleibt geschützt. Insgesamt ändern sich exakt 1.058 Materialtags, keine Meshvertices, Dreiecke oder anatomischen Konturen.

Der regulär gespeicherte Mainplan `f3428f18596d2c03fe9c2cbf6805c1364bc80d4d8357211166b0d1c3fb059f9f` ist mit dem lokalen finalen Kandidaten in sämtlichen 150.000 Flächenzuordnungen und allen acht physischen Regionsfeldern identisch (`benchmarks/buddy-native/final-main-plan-parity.json`). Alle fünf realen Spulen bleiben erhalten. Der neue Vieransichtenvergleich `verification-d10eb2eabfe1454eb34b19cdad14c456/material-four-views.png` wurde visuell betrachtet; ungemessene Bestands-HEX sind weiter keine physische Farbzusage.

Die neun Lederkorrekturplatten bestehen sämtliche neuen CLI-Slices (`verification-2f28d7e79a074dfdb37aa2bbdd62c6ce`); deren vollständige Footprints laufen weiter. Der zusätzliche Emblemfix lässt die beiden Körperteile `collar-body-a-b-a-a` und `collar-body-a-b-b-a` tatsächlich einspulig Wood33 werden. Neu berechnete tatsächliche Spulenunion ergibt weiterhin 34 Platten; unveränderte Inputs werden anhand der tatsächlichen Teil-IDs, Geometrie, FaceSlot-Hashes, Transform und vollständigen nativen Einstellungen abgeglichen, nicht anhand historischer Plattennummern.

Die zweite genannte einfarbige Emblemplatte besteht Slice und FullFootprints in `verification-014d22255b5842ac940b39333a003220`. Die erste einfarbige Variante hatte erneut einen belegten -102-Randfehler: Support-Mittellinie X25,181 mm bei 0,5 mm Linienbreite bedeutet physisch X24,931 mm, also außerhalb des gemeinsamen X25-Bettrands (GCodezeile 1124). Ausschließlich dieser einfarbige Packfall erhält 1 mm zusätzlichen X-Abstand. Neuer tatsächlicher Slice besteht (`verification-3f3f98a235114fb48368ae684e23aedb`); FullFootprints noch im Lauf. Keine Geometrie- oder Profilabsenkung. Die frühere reine Endpunktdiagnose war dafür unzureichend; Linienbreite und konservative Arcaufweitung bleiben Bestandteil der endgültigen Prüfung.


Der zuletzt neue einfarbige Packfall `collar-body-a-b-a-a` besteht inzwischen auch die vollständige Footprintprüfung. Der alte Gesamtlauf wurde nach eindeutigem Prozessvergleich kontrolliert unterbrochen, um keine überholten Leder-GCodes weiter zu prüfen; fertige Zwischenbelege bleiben erhalten. `scripts/verify_buddy_remaining_paths.py` prüft ausschließlich die 17 noch fehlenden final unveränderten GCodes in einem neuen Ordner. `scripts/collect_buddy_native_verification.py` sammelt tatsächliche Slice-/Pfadbelege mit nativen Datei- und GCode-Hashes, lässt fehlende Belege ausdrücklich offen und verlangt einen neuen Berichtspfad. Die endgültige Main-XML-/Paint-/Settings-Parität ist ein eigener notwendiger Beleg; eine Referenzsammlung allein ist keine Mainfreigabe.


## Regulärer Mainlauf und endgültiger Inputabgleich

Der normale UI-Konstruktionsjob `8ae358614600412b95e801d4c80f28cf` liefert 37 Teile, 34 Platten, 68 Schlüssel und 32 Verbindungen. Der read-only Abgleich mit dem finalen lokalen Kandidaten besteht vollständig:

- Sämtliche 37 NPZ-Meshes: Vertices und Face-Reihenfolge exakt identisch, maximaler Fehler 0,0 mm.
- Sämtliche 37 tatsächlichen nativen FaceSlot-Hashes aus gespeicherten Mainteilen und Mainplan exakt identisch.
- Sämtliche Teil-ID-Sets, Modelltransforms, physischen Spulenunionen und Towerreserven der 34 Platten exakt identisch; zusätzlicher 1 mm X-Abstand des einfarbigen Körperteils enthalten.
- Die hochgeladene, bereinigte Vorlage hat einen anderen Archivhash, aber vollständig identische Druck-/Hardware-/Materialsettings. Die konfigurierten nativen Settings sind für jede der 34 Platten exakt identisch.

Belege: `main-geometry-raw-parity.json`, `main-placement-raw-parity.json`, `main-face-slots-parity.json` und `main-config-settings-parity.json` unter `benchmarks/buddy-native/`. Der tatsächliche finale Main-3MF-XML-/Paint-/Settings-Abgleich nach normalem UI-Export ist weiterhin ein eigener Prüfschritt.

Der vollständige neue Leder-Neusweep besteht inzwischen sämtliche neun tatsächlichen Slices und unabhängigen Vollpfadprüfungen (`verification-2f28d7e79a074dfdb37aa2bbdd62c6ce`). Zusammen mit beiden Einfarb-Emblemplatten und den Randkorrekturen bleibt nur der ressourcenschonende Vollpfadlauf der final unveränderten Restplatten offen. Keine Print-Gates wurden gelockert.


## Abschließender verifizierter Digitalstand

Der letzte ressourcenschonende Restlauf ist abgeschlossen. **34/34 tatsächliche lokale Bambu-CLI-Slices und 34/34 vollständige unabhängige GCode-Footprintprüfungen bestehen.** Sämtliche tatsächlichen nativen Dateien aus dem regulären Main-ZIP wurden zusätzlich strikt gegen die geslicten Referenzen verglichen: 34/34 XML-Meshes, Face-Reihenfolgen, Weltpositionen, FacePaints und vollständige Settings identisch; Objekt- und Part-Extruderdefaults identisch; `printable=1`; archivierte ZIP-Dateibytes identisch.

| Beleg | Inhalt |
|---|---|
| `docs/buddy-main-gcode-footprint-verification.json` | Zusammengeführter 34/34-Slice-/Vollpfadbeleg, echte GCode-/native Dateihashes, Referenzzuordnung und kryptografische Verknüpfung zum tatsächlichen Main-ZIP. `digital_cli_and_xml_gates_passed=true`. |
| `docs/buddy-main-native-parity.json` | Strikter Vergleich sämtlicher 34 tatsächlicher Main-Nativdateien gegen die geslicten Referenzen, einschließlich Paints/Settings/Extruderdefaults und ZIP-Bytes. |
| `docs/buddy-assembly-connections-verification.json` | 68 konstruierte Schlüssel-/Taschenpaare an 32 Verbindungen; 27 tatsächliche Strukturblätter und drei stiftlose Klebe-/gefangene Teile. |
| `benchmarks/buddy-native/final-main-plan-parity.json` | Finaler regulärer Mainplan `f3428f18596d2c03fe9c2cbf6805c1364bc80d4d8357211166b0d1c3fb059f9f` ist in sämtlichen Quellflächen-/Materialfeldern identisch. |

Tatsächlicher finaler Mainexport: `data/projects/2c9a7959d13a438fbeb5b8340d8eefd4/runs/37f366df5b7241c6b98ca1507b02788c/export/print-package.zip`.
SHA256: `3d924cc030ace7b1a2f881645fce6d5331cb7bb3646adc08f3dcaade570e947a`.

Die Summe der tatsächlichen finalen Slicergebnisse bleibt **1.042,9316 Stunden / 25,3277 kg PLA**, einschließlich Stützen/Tower und ohne hypothetische Ersparnisse. Das ist eine Slicer-Schätzung, keine Kosten- oder Durchsatzgarantie. Offizielle 2 Wände/15 % Infill wurden nicht stillschweigend reduziert.

Reale Main-Weboberfläche wurde von Root vorne, seitlich, hinten und explodiert geprüft; aktuelle Bilder liegen unter `screenshots/buddy-main-final-*.png`. Der erneute Zugriff auf die native Bambu-GUI meldet einen gesperrten Mac. Deshalb bleibt **Bambu-GUI-Nachprüfung offen**: nach Entsperren die tatsächlichen `plate-XX-native.3mf` öffnen und die physische Spulenzuordnung prüfen. Die digitalen CLI-/XML-Belege bleiben dadurch gültig; eine persönliche GUI-Sichtung wird nicht behauptet.

**Physisch offen → konkrete nächste Prüfung:** Die bestätigte kleine 0,05-mm-Radialprobe ersetzt keine Last-/Klebefestigkeits-/Kippstabilitätsprüfung des rund 1 m großen Aufbaus. Vor dem Aufwand von etwa 25,3 kg Material und 43,5 Tagen geschätzter reiner Druckzeit zuerst die vorbereiteten Anschlussproben im tatsächlich verwendeten Material drucken und Passung prüfen; die langen Großformat-Strukturschlüssel und die Statik benötigen darüber hinaus eigene reale Prüfungen und den großen Aufbau bis zu einer realen Belastungsprüfung abstützen. Kein Druckauftrag wurde abgeschickt und keine solche Freigabe erfunden.

Reproduzierbare Auditwerkzeuge: `scripts/verify_buddy_native.py`, `scripts/verify_buddy_remaining_paths.py`, `scripts/collect_buddy_native_verification.py` und `scripts/verify_buddy_main_native.py`. Alle vier Skripte bestehen `py_compile`; gezielte Buddytests und die von Root gemeldete vollständige Suite bleiben grün. Originale und verworfene Zwischenexporte wurden beibehalten.
