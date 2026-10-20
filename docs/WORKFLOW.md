# Bedienung, Farbmanagement und Problembehandlung

## Gezeigte Version verwenden

Pose prueft die beabsichtigte Figur. Mesh prueft die rekonstruierte Form.
Farben prueft die fertigen Teile, Materialwahl und die dann gueltigen Platten.
Eine geaenderte Hoehe ist ein neuer Geometrieauftrag: zuerst neu einlesen,
dann die neue Meshversion beim Bauen verwenden. Die Hauptaktionen
protokollieren die verwendeten Pose-, Mesh- und Farbversionen; separate
Freigabecheckboxen entfallen. Hinweise stehen unter den Buttons. Gewaehlte API-Kosten sind kein Qualitaetsmassstab.

Bildgenerator und 3D-Provider lassen sich getrennt einstellen. Einzelne
Modellnamen sind editierbar; nicht jedes Modell unterstuetzt dieselben Parameter.
Weitere Anbieter werden als neue Providerklasse oder ueber den dokumentierten
lokalen Gateway eingebunden, nicht ueber unkontrollierte URLs im Browser.

## 180-mm-Figur

Mit der Demo beginnen, drei Palettefarben und Standard-Einsaetze verwenden.
Der mitgelieferte Benchmark ergibt sechs Koerper und drei farbgetrennte Platten.
Gesicht und welliger Bauch sind organisch gekruemmt. Bei kleinen Augenfeldern
kann kein sicherer Stift passen; dazu steht eine Warnung im Geometrie-/Montagebericht.
Farbflecken ohne Stift benoetigen eine bewusst gepruefte andere Befestigung oder
eine geaenderte Segmentierung; es wird keine Klebeloesung stillschweigend unterstellt.

## Ein Meter

Zielhoehe 1000 mm setzen, Mesh neu pruefen, Parameter passend skalieren.
Der reproduzierbare Grossbenchmark nutzt 5 mm Einsatzbodenversatz, 2,5 mm
Stiftradius, 7 mm Stiftlaenge und 2 mm Farbgrenzenabtastung. Diese Werte sind
Testparameter, keine belastbar kalibrierten Fertigungsprofile.

Die Ausgabe besteht aus geschlossenen Volumen. Ein geschlossener Volumenkoerper
bedeutet nicht 100 % Infill: Wandlinien und Fuellung bestimmt spaeter der Slicer.
Eine automatisch konstruierte innere Tragstruktur ist noch nicht enthalten.

## Filamente

Der erste Start enthaelt nur vier deutlich als DEMO bezeichnete Farben. Unter
Filamente ist ein Community-Katalog abrufbar; Import aus JSON funktioniert
auch ohne Internet. Formate: FiguraForge, kompiliertes SpoolmanDB und
Spoolman-Bestandsantwort. Im Katalog nach Elegoo oder Bambu Lab suchen und
passende Eintraege als vorhanden/erlaubt markieren. Keine Preise oder aktuelle
Shop-Verfuegbarkeit werden suggeriert.

Eigene Datei:

```json
[
  {
    "id": "meine-spule-001",
    "brand": "Eigener Bestand",
    "name": "PLA Braun - eigene Eingabe",
    "material": "PLA",
    "hex": "#8B5E3C",
    "owned": true,
    "allowed": true,
    "measured": false,
    "finish": "matte"
  }
]
```

Das Beispiel ist kein gemessener Produktfarbwert. Fuer echte Messwerte kann
`lab_d65: [L, a, b]` und `measured: true` eingetragen werden. CIEDE2000 vergleicht
die Zielfarbe mit dem Messwert, falls vorhanden, andernfalls mit Katalog-RGB.
D65-Werte nicht mit einem anderen Weisspunkt mischen. Glanz, Transparenz,
Druckrichtung, Schichtstaerke und Beleuchtung sind im Bildschirmvergleich nicht
physikalisch modelliert. Ein numerischer Farbabstand ist kein garantierter
subjektiver Qualitaetsscore.

Nach Katalogwechsel **Neue Farbvorschlaege berechnen** benutzen. Gesperrte
Spulen bzw. nicht vorhandene Spulen bei Bestandsfilter duerfen nicht neu
zugeordnet werden. Gespeicherte Zuordnungen enthalten einen Snapshot ihrer
Eigenschaften; ein spaeter editierter Katalog aendert keine bereits
freigegebene Baugruppe unbemerkt.

## Fehler und sinnvolle Reaktionen

| Meldung / Symptom | Reaktion |
|---|---|
| Mesh nicht geschlossen | In Blender reparieren und als selbstenthaltenes GLB erneut importieren. Der Kern erfindet keine grossen fehlenden Oberflaechen. |
| Projektion faltet sich / Undercut | Anderen Auszugsvektor versuchen, Region anders segmentieren oder ganze Farbkoerper waehlen. |
| Tasche liegt ausserhalb des Koerpers | Einsatz weniger tief; duenne Gliedmassen als ganze Teile behandeln. |
| Kein Platz fuer Steckstift | Figur vergroessern, Farbfleck vergroessern oder Befestigung bewusst anders planen. |
| Face-Limit erreicht | Grobere Abtastung oder gezielter bereinigtes Quellmesh; nicht jede Textur verlangt submillimetergenaue Teilung. |
| GLB verlangt Draco / meshopt / BasisU | In einem geeigneten Import-/Exportwerkzeug entkomprimieren und eingebettet erneut als GLB speichern. Nicht einfach die Extension-Angabe entfernen. |
| API-Timeout beim Absenden | Provider-Dashboard pruefen. Derselbe Auftrag koennte bereits bezahlt gestartet sein. Nicht sofort mehrfach neu starten. |
| Remote-Task kann fortgesetzt werden | Vorhandenen Task erneut abrufen; Pose und Provider nicht aendern. |
| Farbfeld liefert viele Schattenregionen | Albedo/Referenz besser beleuchten, Palette reduzieren oder explizite Palette vorgeben. |
| Katalogabruf scheitert | JSON manuell herunterladen und in der Weboberflaeche importieren. |
| Mac/Windows meldet kein vtk-Paket | Python 3.12/3.13, 64-bit verwenden; keine beliebig neue Python-Vorabversion. |

## Mixed Filament und Rigging

Mixed Filament ist keine physische Verschmelzung im H2D-Hotend. Eine native
Bambu-Umsetzung mit Schichtrezepten ist in dieser Version bewusst **nicht**
emittiert: ohne echte Profile und Kalibrierung waeren solche Werte spekulativ.
Die aktuelle Produktionsstrategie bleibt separate, einfarbige Koerper oder
hoechstens zwei reale Spulen je Platte. Rigging ist als spaeterer Prozess
vorgesehen; die Version erzeugt oder deformiert noch kein Character-Rig.
