# Organische Farbschnitte: Implementierung und Grenzen

## Was "entlang der Farbe" hier bedeutet

Farben stammen aus der Albedo-Textur, Vertexfarben oder Materialgrundfarben.
Normal-, Glanz- und Rauheitskarten erzeugen keine Geometrie. Die Flaechen
werden in CIELAB einer Palette zugeordnet. Bei fotografisch eingebrannten
Schatten kann eine Schattenkante faelschlich als Farbregion erscheinen.
Saubere, flach beleuchtete Referenz-/Albedobilder sind deshalb relevant.

Die Grenze ist **auf dem Mesh liegend und nicht notwendigerweise eben**.
Konforme lokale Unterteilung verfolgt den abgetasteten Farbwechsel. Es werden
nicht einfach Modellhaelften mit horizontalen Ebenen abgeschnitten.

`boundary_tolerance_mm` ist die angestrebte lokale Abtastgroesse, keine
mathematisch bewiesene maximale Konturabweichung. Sieben Proben pro Dreieck und
eine grobe Flaechenabtastung koennen winzige Features zwischen Proben uebersehen.
Die Genauigkeit kann nur durch weitere Verfeinerung und Sichtpruefung verbessert
werden, nicht durch eine behauptete unbegrenzte Praezision.

## A. Oberflaechen-Einsaetze (Standard)

1. Benachbarte nicht-grundfarbige Regionen werden zu einer gemeinsamen Tasche
   zusammengefasst. Dies verhindert doppelte, sich durchdringende Taschenwaende
   direkt nebeneinanderliegender Farben.
2. Der mittlere Flaechennormalenvektor liefert einen Kandidaten fuer die
   Auszugsrichtung. Pro Tasche kann ein Vektor ueberschrieben werden.
3. Die Projektion in die Ebene senkrecht zur Auszugsrichtung wird auf Faltungen
   und Mehrdeutigkeit geprueft. Ein global umlaufender Bereich eignet sich
   haeufig nicht fuer einen einschiebbaren Einsatz.
4. Die originale gekruemmte Aussenflaeche bleibt erhalten. Ihr versetztes
   Gegenstueck bildet den Taschenboden; Seitenwaende schliessen das Volumen.
   Randspalt und Stecktoleranzen sind getrennte Parameter.
5. Geeignete Connector-Punkte werden innerhalb eines erodierten Umrisses
   gesucht. Weder Umriss noch Nachbarflaechen sollen durchbrochen werden.
6. Stifte werden an das Einsatzvolumen angefuegt, geometrisch korrespondierende
   Buchsen in den Grundkoerper gebaut. Es sind keine nur optisch aufgelegten Zylinder.
7. Geschlossene Volumen, Orientierung, Plausibilitaet und stichprobenartiger
   Auszug werden geprueft. Fehler fuehren zum Abbruch, nicht zu einem scheinbar
   erfolgreichen STL-Export.

Wenn der nominelle Stift nicht passt, darf die optionale Einstellung
`adaptive_small_pins` einen 1,6-mm-Stift mit kleinerem Randabstand versuchen.
Das wird ausdruecklich gemeldet und ist nur fuer leichte Farbeinsaetze
gedacht, nicht als Tragverbindung. Auch dieses Mass braucht einen eigenen
Passungstest. Passt selbst dieser Stift nicht, wird keine Befestigung behauptet.

Kleine Flecken koennen nach `min_region_area_mm2` mit einem Nachbarn verschmolzen
werden. Dies wird berichtet. Bleibt ein Fleck als Teil erhalten, aber passt
kein Stift hinein, erscheint eine ausdrueckliche Warnung. Die Software behauptet
dann keine eigenstaendige mechanische Befestigung.

## B. Ganze Farbkoerper (Expertenoption)

Diese Strategie trennt eine vollstaendige Farbregion vom Rest. Die originale
Oberflaechen-Grenzschleife bildet den Rand einer gemeinsamen inneren Kappe.
Die Kappe kann nichtplanar sein; die Bestfit-Ebene dient nur der Triangulierung,
nicht dem Flachschneiden der sichtbaren Kontur.

Beispiel: Ein umlaufendes Farbband wird zum mittleren separaten Koerper mit
zwei Gegenflaechen. Oberer und unterer Rest bleiben getrennte Koerper. Tests
enthalten Halbkugel, umlaufendes Band und wellige nichtplanare Kontur.

Grenzen: komplex verschachtelte Schleifen, sich faltende Projektionen und
Kappen ausserhalb des Quellvolumens werden verweigert. Mehrere Kappen koennen
unterschiedliche Montagerichtungen verlangen; die Software meldet dies zur
Pruefung. Es gibt keinen universellen automatischen anatomischen Cut-Planer.
Die Einsatzparameter Tiefe/Randspalt gelten primaer fuer Strategie A; Strategie B
verwendet gemeinsame Gegenflaechen mit Connector-Spiel.

## Verbinder und Toleranzen

- Rund: polygonal angenaeherter Kreis, leicht verjuengte Spitze.
- Keyed: angefaste quadratische Kontur gegen Verdrehung.
- `pin_clearance_mm`: **radial**, also halber Durchmesserunterschied.
- Buchse ist tiefer als die Stiftspitze, um Bodenkollision zu vermeiden.
- Kein einrastender Schnapphaken, keine garantierte Presspassung.

Testpaare unter Konstruktion > Passungs-Testteile herunterladen oder
`python scripts/calibration.py`. Testen mit echtem Filament und vergleichbarer
Ausrichtung. Gerade bei PLA koennen zu stramme lange Stifte abbrechen.
Die Bibliothek enthaelt derzeit keine Magnete, Heat-Set-Inserts, Gewindestangen
oder tragenden Verriegelungsmechanismen.

## Strukturteilung und Druckplatten

Organische Farbtrennung kommt zuerst. Erst wenn ein fertiger Koerper den
Bauraum ueberschreitet, werden zusaetzliche ebene Strukturschnitte erzeugt.
Sie sind nicht als Ersatz fuer organische Farbgrenzen gedacht.
Schnittpositionen werden in mehreren zentralen Kandidaten anhand kleinerer
Querschnittsflaechen ausgesucht. Primaer wird die Oberflaeche im Halbraum
geclippt und der Schnitt mit einer konturgebundenen Delaunay-Triangulierung
geschlossen; Loecher bleiben erhalten. VTK ist ein zweiter Kandidat bei
problematischen Kappen. Diese Ebenenschnitte laufen in einem
wiederverwendbaren isolierten Prozess mit Zeitlimit (Default 10 Sekunden je
Versuch). Ein haengender Schnittprozess wird ersetzt und der naechste
Kandidat geprueft. Dies wurde nach einem tatsaechlichen haengenden
Grossformat-Schnitt ergaenzt. Verbinder werden automatisch dimensioniert.
Nach rekursivem Teilen koennen Connector-Metadaten noch den Elternkoerper
beschreiben; Montagefolge und Zugangsrichtungen brauchen dann Sichtpruefung.

Ausrichtung prueft 24 rechtwinklige Orientierungen und passende
Einsatzrichtungen. Supportbedarf und Kontakt werden heuristisch bewertet.
Packing nutzt konservative XY-Rechtecke, Abstand und Rand. Es ist kein
mathematisch globales Optimum und keine Simulation des Slicer-Toolpaths.
Reale Supportkonturen, Brims, Purge-Tower, Bettsperrflaechen und Duesenoffsets
muessen in Bambu Studio bestaetigt werden.

Spaetere Filamentzuordnung kann eine Platte in weitere Platten aufteilen,
wenn unterschiedliche Spulen eingesetzt werden. Es zaehlen Filament-IDs,
nicht nur identische Bildschirmfarben. Koerper und vorhandene
Platzierungskoordinaten bleiben unveraendert. Die Farbfreigabe bindet diese
spulenabhaengige Aufteilung.

## Pruefungen, die keine Zertifizierung ersetzen

Geschlossene Kanten, konsistente Orientierung, endliches positives Volumen,
Komponenten, Plattengrenzen, paarweise konservative Bounding-Rechtecke,
Export-Roundtrip sowie bis zu 1800 Flaechenpunkte an acht Auszugspositionen.
Dies schliesst nicht jede Selbstueberschneidung oder Kollision zwischen
aufeinanderfolgenden Proben aus. Schwerpunkt/Standpolygon sind nur Hinweise
unter vereinfachter Materialverteilung. Es gibt keine FEA oder Kippsicherheit.
