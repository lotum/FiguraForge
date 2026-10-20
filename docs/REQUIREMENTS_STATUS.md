# Anforderungsstand und gezielte Weiterentwicklung

## Mochi · geometrischer Halsschnitt und loser Schlüssel · 18.10.2026

Geschwungene Trennung an der geometrischen Einschnürung, breite Kopfauflage, separater asymmetrischer 20×28×36-mm-Schlüssel. Acht geschlossene Teile auf drei nativen H2D-Platten; Richards ursprüngliche Bemalung einschließlich aller 1.034 komplex bemalten Dreiecke erhalten. 500 und 470 mm tatsächlich geslicet und mit vollständigen Extrusions-Footprints geprüft. Zweimaliges natives Speichern erhält alle acht Teile/Farbcodes. 514 Python-Tests und beide Frontend-Harness bestanden. Reale Hals-Passung noch offen; zusätzliche kleine Probe mit gleichen Materialien/Schichthöhen vorhanden. [Dateien, Montage, Größen und Grenzen](MOCHI_NECK_SPLIT.md), [Nachweis](mochi-neck-split-verification.json). Kein Druckstart, Originale erhalten.

## Mochi · nativer Speicherfehler korrigiert · 18.10.2026

Richards gedruckte 180-mm-Körperplatte und Farbkorrekturen unverändert gesichert; eigenes FiguraForge-Archivprojekt. Schwarzer Körper anstelle der Nase auf Platte 2: kollidierende Ressourcenkennungen im nativen Mehrdateiformat behoben, zwei tatsächliche native Speicher-/Ladedurchläufe erhalten alle sechs richtigen Teile. Neue 320-mm-Zweidüsen- und 325-mm-Rechtsdüsen-Dateien erfolgreich geslicet; alte Datei bleibt erhalten, ihre beschädigte zweite Platte nicht verwenden. [Dateien, Bauraum, Nachweise und Grenzen](MOCHI_USER_EDITION.md).

## Mochi: zusätzliche reine Braun/Beige-Variante

Gleiche sechs fertigen Mochi-Teile, Körper nur Braun/Beige ohne Mixed, fünf schwarze Details auf Platte 2 **derselben nativen 3MF-Datei**. 510 Python-Tests bestanden. Beide Platten tatsächlich gesliced und 3.030.926 vollständige Extrusions-Footprints geprüft; bestehende Mixed-Dateien und Geometrien per SHA unverändert. Prognose gesamt ca. 13 h 30 min / 196,55 g. [Datei, Importanleitung und Grenzen](MOCHI_SOLID_TWO_PLATES.md), [Nachweis](mochi-solid-two-plates-verification.json). GUI-/physische Abnahme der neuen Variante offen; kein Druckstart.

## Neueste Mochi-Variante · nur schwarze Details separat

[Eigene Importvariante](MOCHI_UNIFIED_PRINT.md): Kopf/Ohren/Schwanz/Rumpf/Beine als ein Körper, schwarze Nase+vier Augenteile separat. Kopf299.998Quellflächen mit echter Originalprojektion; übrige Körperform erhalten. Genau20 tatsächliche Farbwerte aus vorhandenen Beige31/EarthBrown29, Schwarz30 separat. Zwei reale native Slices plus vollständigeDruckpfade bestanden, Lightning5%/2Wände, ca.33h/330g. 507Python-Tests und beideFrontend-Harness bestanden. Eigenständige lokale Datei-/Vorschauausgabe; bisheriges Neunteileprojekt erhalten. Bambu-GUI/physischeFarben/Passung bleiben offen. Buddy-Lightning-Präferenz aufgenommen, neueBuddy-Berechnung nicht Teil dieses Mochi-Auftrags.


## Aktuellster Stand vom 16.10.2026

| Punkt | Verifiziert / verbleibend |
|---|---|
| Farbplan / Geometriegruppen | Eigener Schritt, sichtbare Legende und Infos, breiter Editor, Flächenpinsel; getrennte Geometrie- und Farbmodi erlauben Mixed auf Einzelteilen; mehrfarbige Ganzteile/Einsätze als getrennte Konstruktionslogik getestet |
| Farbvarianten | Neun lokale editierbare Vorschläge; Schattenvereinheitlichung heuristisch, dunkle Details geschützt, unkalibriert |
| Native Mixed-Vorlage | 19 Farbstufen aus zwei Spulen in echter H2D-GUI gesliced; Preview/Export-Rezeptparität getestet. Die grün/beige Dragon-Testfarben sind keine Mochi-Farbfreigabe. Echte Dragon-H2D-Profile geprüft; nativer Würfel-/Paketexport mit Slot 4 sowie echter GUI-Save-/Slicing-Test bestanden; physischer Druck offen |
| UV-Vorschau | Originaltextur und weiche Normalen, kein unnötiges Remeshing für Darstellungsfehler |
| Zu grosse Meshy-Netze | Ziel schon im Request; automatische lokale Blender-Arbeitskopien Buddy und Mochi je 150.000 Faces, Originale erhalten |
| Farbgrenzenbudget | Exakte Vorplanung unter 350.000; Automatik zur Zielhoehe, feste Praezision wird nicht heimlich reduziert |
| Bedienung | Zusaetzliche Pruef-/Freigabecheckboxen entfernt, Hauptaktion bindet verwendete Version, Hinweise unter Buttons, Fehler sofort sichtbar |
| Detailregler | Begrenztes Ziel mit Reserve, Bewertung und erneute lokale Arbeitskopie |
| KI-Vorausfuellen | Freies Briefing pro Schritt, editierbare Einstellungs- und Farbregionsvorschläge, keine automatische Generierung; Live-Abnahme gesondert |
| Produktionsprotokoll | Deutsche Schrittbezeichnungen, aktueller Fehler im Formular, alte Fehler als historisch markiert |
| Budget | Optionales Limit statt willkuerlichem 100-EUR-Standard |
| Mochi V2 | 9 geschlossene Teile / 7 Stifte / 4 Klebeaugenteile / 5 native Platten. Aktueller normaler Export `fe198e03f321491d99af56a50994001c` gegen den gesliceten Prüfstand abgeglichen: Weltvertices, Flächenfarben und vollständige Projekteinstellungen identisch; Datei-SHAs separat belegt. [Aktuelle Parität](mochi-v2-current-native-parity.json). Physischer Gesamtdruck, Farben und Montage offen. |
| Pip | 10 geschlossene Teile / 16 Stifte / 10 isolierte Platten. Aktueller Mainexport `6d0006dece3e44bda76bcd1e9ff9a810`: alle zehn aktuellen Slices und Pfadprüfungen bestanden. 5.668.791 Extrusionssegmente / 843.778 Druckbögen; Objekt-/Turm-Footprints getrennt. [Slice](pip-main-native-slice-verification.json) / [Pfade](pip-main-gcode-footprint-verification.json). Prognose 35 h 27 min / 505,01 g; physische Montage und Farbwirkung offen. |
| Buddy | Aktueller Plan `f3428…` regulär gespeichert, alle Spulen-IDs erhalten. Main-Konstruktion `8ae358614600412b95e801d4c80f28cf` erfolgreich: 37 geschlossene Teile / 34 Platten / 68 Passungsschlüssel / 32 Schnittstellen, 0,05 mm. Alle 34 finalen Platten gesliced, vollständig auf Extrusions-Footprints geprüft und gegen den tatsächlichen Mainexport `37f366df…` abgeglichen. [Parität](buddy-main-native-parity.json) / [GCode-Kette](buddy-main-gcode-footprint-verification.json). Prognose 1.042,93 h / 25,328 kg. Großmontage/Statik/Farbwirkung physisch offen; keine Druckfreigabe. |
| Physische Passung | Reale Nasenvergleichsprobe: 0,05 mm radial akzeptiert, 0,10/0,15/0,20 zu lose. Keine automatische Abnahme anderer Formen/Größen. Neue optionale Pip-/Buddy-Vierpaarplatte mit korrigiertem Kern nativ erzeugt/gesliced; Nutzertest offen. |
| Materialsegmentierung | Modellgebundene Korrekturen: Buddy-Lederlichter vereinheitlicht (1.053 Gold→Braun), fünf künstlich braune Emblemflächen zurück zu Gold; tatsächliches Ring-/Facettenrelief liefert natürliche Schattierung. [A/B und Quell-/Hashbelege](../benchmarks/buddy-material-islands-review/REPORT.md). Allgemeine Trennung von Beleuchtung und Materialfarben weiterhin offen; keine physikalische Entlichtung behauptet. |
| 3MF/H2D | Demo-Import, native Mixed-Testkörper sowie konkrete Mochi-/Pip-Platten tatsächlich gesliced. Reine Solid-H2D-Vorlagen brauchen keine Fake-Mischslots; echte Mixed-Pläne ohne passende Rezeptslots werden blockiert. CLI-Exit0 allein ist keine Pfadfreigabe: unabhängige geometrische Extrusions-Footprintprüfung ergänzt die aktuellen Mochi-/Pip-Platten. Physischer Druck dieser Gesamtfiguren offen. |
| Anbieter-Privatsphaere | Code publiziert nicht; konkrete Kontosichtbarkeit und Trainingsausnahme nicht belegt, Quellenkonflikt dokumentiert |

**Aktueller Integrationslauf: 498 Python-Tests in 39,42 Sekunden und beide Node-Frontend-Prüfprogramme bestanden.** [JUnit](test-results-current-mac-final.xml). Enthalten: Buddy-Vorausfüllung, 68 Passungsschlüssel und veraltete KI-Vorschläge. Alle 34 Buddy-Platten haben Slice- und Vollpfad-PASS; der endgültige Mainexport besteht den vollständigen XML-/Paint-/Settings-Abgleich. Bambu-Desktopprüfung wegen gesperrtem Mac separat offen. Details und Grenzen: [Testbericht](TEST_REPORT.md).
Farbwirkung bleibt unkalibriert: Pips Bestandsgrün ist blasser als die Referenz, Buddys Wood-Filament matter. Keine physische Gesamtmontage oder automatische Druckfreigabe; kein Agenten-Druckstart.

Die folgenden Abschnitte erhalten den historischen Stand und werden durch
diesen Nachtrag praezisiert.


Dieser Stand ist eine lauffaehige Engineering-Version, kein Versprechen,
jedes beliebige texturierte Mesh autonom perfekt fertigen zu koennen.

## Verifizierung auf Richards Mac am 16. Oktober 2026

Nachtrag echte Anbieter: OpenAI-Bildgenerierung und ein vom Nutzer gestarteter
Meshy-Mehransichtenauftrag haben Ergebnisse geliefert. Buddy ist als unveraendertes
texturiertes Mesh mit 768.288 Dreiecken lokal geladen und geometrisch als
geschlossener Einzelkoerper geprueft. Importgrenze jetzt begrenzt auf 1 Mio.
Dreiecke. Poseherkunft und separate generierte Testbilder sind in der Oberflaeche
sichtbar. Meshfreigabe, Farbtrennung, Steckmontage und Bambu-Export dieses
Characters stehen noch aus; die bisherige Druckabnahme unten betrifft die Demo.
Aktueller Testnachweis und Screenshots stehen in [TEST_REPORT.md](TEST_REPORT.md).

Installation und Web-Demo sind ausgefuehrt. 75 Tests bestehen; der geometrische
Bambu-Studio-Roundtrip besteht fuer 3 Platten bei 180 mm und 17 Platten bei
1000 mm. Ein dabei belegter Praezisionsfehler beim Import kleiner Einsaetze
ist durch lokale Meshkoordinaten im Export behoben.
Belege und genaue Grenzen stehen in [TEST_REPORT.md](TEST_REPORT.md).
Die Anforderungen an vollstaendige Steckmontage sind weiterhin **teilweise offen**:
bei 180 mm besitzen zwei Augen-Einsaetze keinen sicheren Stift. Die Oberflaeche
benennt die betroffenen Teile jetzt sichtbar. Im 1000-mm-Demolauf haben alle
Farbeinsaetze Verbinder; physische Passung und Montage sind weiterhin ungeprueft.

| Urspruengliche Anforderung | Ausgelieferter Stand |
|---|---|
| Mehrere Referenzbilder, neue Pose | Upload, freie Prompts, gesonderte Ansichten, austauschbare API-Adapter |
| Identitaet pruefen und iterieren | Optionaler multimodaler Review mit begrenzten neuen Kandidaten; menschliche Freigabe |
| Fremdes 3D-Modell statt Eigenentwicklung | Meshy-/Tripo-REST-Adapter; offener lokaler Gateway-Vertrag |
| Direkter eigener Hunyuan/TRELLIS-Betrieb | Vertrag vorhanden; GPU-Worker/Modellgewichte nicht enthalten |
| Organische Farbgrenzen | Texturabtastung, konforme Verfeinerung, gekruemmte Taschen und Einsaetze |
| Ganze farbige Abschnitte | Expertenstrategie mit nichtplanaren gemeinsamen Kappen |
| Steckverbindungen | Runde / verdrehsichere Stifte; passende Buchsen; Kalibrierkoerper |
| Jede beliebige Verbindungstechnik | Noch nicht: Schnapphaken, Magnete, Heat-Set, innere Tragwerke |
| Ein Meter / mehrere Plates | Reale 1000-mm-API-Ausgabe, 22 Teile / 17 Platten; zusaetzliche Strukturteilungen |
| H2D, moeglichst wenig Farbwechsel | Konservative Profile, farbreine oder maximal zweispulige Platten |
| Filamentbestand und Alternativen | Eigene Spulen, erlaubte Marken/Eintraege, Katalogimport, CIEDE2000 und Vorschau |
| Physisch praezise Farben | Messwerte importierbar; keine eigene Messung, kein kalibrierter Druck-Proof |
| Live-Filamentangebote | Katalogsynchronisation vorhanden; keine verifizierten Shoppreise/Lagerbestaende |
| Mixed Filament | Vorhandene native H2D-Mischrezepte prüfen und pro Fläche zuordnen; experimenteller Export, finale GUI-/Slicing-Abnahme offen |
| Pose / Mesh / Farbe freigeben | Hash-gebundene Freigaben und Invalidierung bei relevanten Aenderungen |
| Eigene Weboberflaeche | Ausgeliefert, mit echtem 3D-Viewer und Software-Fallback |
| Bambu-kompatibles 3MF | Core-3MF; geometrischer Bambu-Studio-Import/Export auf dem Mac bestanden, Profil/Slicing noch offen |
| Komplettes natives Bambu-Projekt | Nicht implementiert; keine erfundenen Druck-/AMS-Profile |
| Rigging | Erweiterungspunkt; kein funktionierender Rigging-Worker in dieser Version |
| Autonome Ausfuehrung ueber Nacht | Persistente Auftraege, Budget, API-Task-Recovery, abbrechbare native Worker; Freigaben bleiben Haltepunkte |

## Wichtigste naechste reale Abnahmen

1. Erledigt am 16.10.2026: auf dem Zielrechner frisch installiert, Demo-GLB im Browser geladen, konstruiert und exportiert.
2. Drei geometrisch unterschiedliche echte Modelle statt ausschliesslich der
   prozeduralen Fixtures testen: menschliche Buste, Figur mit Haaren/Fingern,
   Figur mit mehreren angrenzenden Farben und einer umlaufenden Farbregion.
3. Die beiden Steckstiftdurchmesser 3,0 und 1,6 mm in vorgesehenem Filament,
   Druckprofil und Orientierung kalibrieren. Kleine Augen ohne Stift benoetigen
   eine geaenderte Teil-/Toleranzstrategie; sie sind nicht stillschweigend geloest.
4. Meshy/OpenAI/Google mit echten Konten abnehmen. Tripo-Ausgabe auf Meshopt und
   Face-Zahl pruefen; erforderliche Dekompression/Remeshing noch ergaenzen.
5. Geometrischer CLI-Import/Export aller 20 Demo-Platten in Bambu Studio ist
   erledigt: Koordinaten, Dreiecke, Volumen, Geschlossenheit und Teilezahl stimmen.
   Offen bleiben die H2D-Profilwahl, reale Filament-/Duesenzuordnung und Slicing
   in der GUI. Erst nach Passungstest drucken.

Die naechste grosse algorithmische Verbesserung waere ein kombinierter
Fertigungsplaner: grosse Farbregionen als Steckteile, zu kleine Details als
verbundene Mehrfarb-Geometrie im gleichen Druck. Diese automatische
Mischstrategie ist inzwischen im separaten Farbplan vorhanden; native H2D-GUI-/Slicing-Abnahme bleibt offen.
