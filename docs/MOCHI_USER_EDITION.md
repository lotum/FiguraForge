# Mochi · Richards Druckstand und Großversion · 18.10.2026

Der Nutzer hat die 180-mm-Körperplatte bereits braun/beige gedruckt und ist sehr zufrieden. Er hat Flächenfarben geringfügig nachgemalt und „No sparse layers“ am Spülturm aktiviert. Schwarze Nase und Augen wurden zum Zeitpunkt der Rückmeldung noch nicht gedruckt.

## Unveränderter Ausgangsstand

Original: `benchmarks/mochi-solid-production/Mochi-Braun-Beige-H2D-2-Platten.3mf`.
Aktuelle Nutzerfassung SHA256: `4197d3b9bbd3dff88fe65bacc47bc0448c0d76530c56b66d221760318df73508`.
Zusätzliche unveränderte Kopie: `benchmarks/mochi-user-edition-20261018/Mochi-Richards-Anpassungen-180mm-ORIGINAL.3mf`.

Die Körperplatte enthält 296.494 Dreiecke mit 784 unterschiedlichen codierten Flächenbemalungen einschließlich bemalter Unterdreiecke. Die neuen Dateien kopieren diese Farbcodes vollständig; keine erneute Palette-Klassifikation und keine neue KI-/Mesh-Erzeugung. Schwarze Gegenstücke werden passend mit skaliert. Uniforme Skalierung vergrößert auch das 0,05-mm-Nasenspiel auf etwa 0,089 mm bei 320 mm bzw. 0,090 mm bei 325 mm; reale Großpassung bleibt ungeprüft.

## Schwarzer Körper statt Nase: Ursache und Korrektur

In der vom Nutzer gespeicherten Datei enthält „nose“ 296.494 Körperdreiecke anstelle der 7.058 Nasendreiecke. Der alte Zusammenführer hatte nur die Objektkennungen im Wurzeldokument neu nummeriert. Externe Geometriedokumente enthielten weiterhin kollidierende Ressourcenkennungen. CLI-Sliceprüfungen bestanden zwar, beim anschließenden nativen Speichern konnte die Nasengeometrie durch den Körper ersetzt werden. Damit war die frühere reine CLI-Abnahme für diesen Fall unzureichend.

`native_plates.merge_two_native_plates` vergibt jetzt global eindeutige Ressourcenkennungen für Wurzel- **und** Geometriedokumente und aktualisiert Komponenten-, Bauteil- und Plattenverweise. Die Nasengeometrie wird aus der erhaltenen richtigen Einzelplatte übernommen, nicht aus der kaputten Nutzer-Nase. Vier Augenteile bleiben erhalten. Regression prüft dateiweite Kennungseindeutigkeit.

Zwei aufeinanderfolgende native Import-/Speicherdurchläufe mit Bambu 02.07.01.62 erhalten alle sechs richtigen Geometrien und Farbcodes, maximale Koordinatenrundung unter 4,1e-7 mm. Das ist ein tatsächlicher Test des nativen Parsers und Exporters; keine separat behauptete manuelle GUI-Abnahme.

- [Korrigiertes 180-mm-Projekt mit Richards Körperplatte](../benchmarks/mochi-user-edition-20261018/fallback-korrigiert/Mochi-Richards-180mm-korrigierte-Details.3mf)
- [Nur richtige schwarze Nase und vier Augen für 180 mm](../benchmarks/mochi-user-edition-20261018/fallback-korrigiert/Details-180mm.3mf)

Die Originaldatei wird ausdrücklich erhalten. Ihre Platte 1 ist der gute Körper-Fallback; die beschädigte Platte 2 nicht drucken.

## FiguraForge

Neues Projekt **„Mochi · Richards Druckstand · 180 mm“**, ID `dd9d3c92b8cd4b478aaa375db11acc99`.
Es enthält die unveränderte Originaldatei, ein zusätzliches korrigiertes Projekt, korrekte schwarze Einzelteile und die geprüften Großversionen. Die Vorschau stammt aus dem gespeicherten Bambu-Thumbnail. Archivansicht zeigt Downloads und den tatsächlichen Druckstatus, ohne neue Geometrie-/API-Aufträge anzubieten. Dieses native Archiv ist keine verlustfreie Übernahme der Bambu-Pinselbemalung in FiguraForges eigenen Flächeneditor; die Bemalung bleibt vollständig in den 3MF-Dateien bearbeitbar.

## Bauraum und Spülturm

Bambu nennt 325 mm Höhe im [H2D-Datenblatt](https://eu.store.bambulab.com/de/products/h2d?variant=54207138693468). Das installierte offizielle Maschinenprofil `fdm_bbl_3dp_002_common.json` begrenzt die **linke Düse auf 320 mm**, die rechte auf 325 mm (`extruder_printable_height=[320,325]`). Daher zwei ausdrücklich getrennte Varianten:

| Variante | Körperabmessungen ungefähr | Voraussetzung |
|---|---|---|
| 320 mm, zwei Düsen | 158,6 × 243,0 × 320,0 mm | Braun links, Beige rechts; gemeinsamer Bauraum X25–325 / Y0–320 |
| 325 mm, rechte Düse | 161,1 × 246,8 × 325,0 mm | Beide Farben im AMS der rechten Düse, echte Farbwechsel; kein Zweidüsenbetrieb am Körper |

Beide Varianten verwenden dieselben bemalten Körperdreiecke und dieselben sechs physischen Teile, schwarze Details auf Platte 2. Geometrie wird nur uniform skaliert und auf die Platte gesetzt. 325 mm ist die Profilgrenze, keine zusätzliche Sicherheitsreserve. Keine Maschinenhöhen künstlich erhöht.

Der experimentelle Spülturm ohne dünne Stützschichten wurde bei großer Höhe vom echten Slicer mit Konfliktmeldung abgelehnt. Für Großversionen ist er ausgeschaltet. Außerdem werden Turmposition und Breite angepasst: X250 / Y245 / 40 mm. Der tatsächliche Turm inklusive Rand/Rippen ist breiter als der eingestellte Nennwert; ein erster Ansatz bei X275/Y265 lag mit Druckbahnen bis X341/Y327 außerhalb des Bauraums. Diese Fehlversuche werden nicht als druckbereit angeboten. Die 180-mm-Originaleinstellungen bleiben erhalten.

## Werkzeuge und Grenzen

`scripts/prepare_mochi_user_edition.py` schreibt ausschließlich neue Archive. `scripts/register_mochi_print_archive.py` ergänzt einen neuen lokalen Projektstand mit unveränderlichen Dateikopien. Keine bestehenden Projektstände, Originale oder Mixed-Dateien gelöscht/überschrieben. Keine bezahlten API-Aufträge, keine Druckersends.

Die maschinenlesbaren Abschlussnachweise ergänzen diese Anleitung. Physischer Großdruck, Stützenentfernung und Großpassung sind noch nicht abgenommen.


## Abschließender Prüfnachweis

[Datei-/G-Code-Hashes, Plattenprüfungen, Farb-/Geometrieerhalt und Laufzeiten](mochi-user-edition-verification.json). **511 Python-Tests in 40,47 s**, beide Frontend-Harness bestanden; [JUnit](test-results-mochi-user-edition-final.xml). Regression schützt zusätzlich die Skalierung ohne Verlust bemalter Unterdreiecke und ohne Änderung der Quelldatei.

| Datei mit zwei Platten | Tatsächlich geprüft | Prognose gesamt einschließlich schwarzer Teile |
|---|---|---|
| [320 mm / zwei Düsen](../benchmarks/mochi-user-edition-20261018/editions-verified/Mochi-320mm-zwei-Duesen-2-Platten.3mf) | Beide tatsächlichen Slices; 5.556.683 Extrusionssegmente ohne Owner-Konflikte, gemeinsame H2D-XY-Grenzen eingehalten | 32 h 13 min / 531,00 g |
| [325 mm / rechte Düse](../benchmarks/mochi-user-edition-20261018/editions-verified/Mochi-325mm-rechte-Duese-2-Platten.3mf) | Beide tatsächlichen Slices; 5.746.669 Extrusionssegmente ohne Owner-Konflikte, gemeinsame H2D-XY-Grenzen eingehalten | 74 h 03 min / 1.172,56 g |

Die 325-mm-Körperplatte benötigt laut Slicer 1.543 echte Farbwechsel. Deshalb klare Empfehlung für 320 mm mit beiden Düsen: nur 5 mm kleiner, deutlich weniger Zeit und Spülmaterial. Die 325-mm-Datei bleibt als ausdrücklich gewünschte maximale Höhenoption erhalten; Braun und Beige müssen beide im zur rechten Düse gehörenden AMS verfügbar sein. Beim Drucken tatsächliche AMS-Fachzuordnung prüfen.

[FiguraForge-Projekt direkt öffnen](http://127.0.0.1:8000/?project=dd9d3c92b8cd4b478aaa375db11acc99). Server läuft lokal auf Port 8000; alter Vorschauport 8011 bleibt unberührt.
