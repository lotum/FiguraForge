# Mochi: Detailverteilung und grobe Augen

Stand: 16. Oktober 2026. Lokale Analyse, keine Cloud-Aufrufe und keine Änderung
an den Projektmodellen. Der Nutzerscreenshot wurde mit dem bestehenden Original
und der aktuellen Arbeitskopie verglichen.

## Ergebnis und Korrekturen

**Die groben Augen sind nicht einfach ein Beleg für zu wenige geometrische Faces.**
Die Vorschau verwirft Texturdetails innerhalb jedes Dreiecks: `mesh_preview` in
`backend/figuraforge/geometry/preview.py` wiederholt eine einzige Albedo-Farbe und
eine Flächennormale dreimal. Der Viewer interpoliert daher innerhalb des Dreiecks
keine unterschiedlichen Farben und keine glatte Oberflächennormale. Das ist an
schwarz-weißen Augen deutlich auffälliger als auf orangefarbenem Fell.

Lösung: Die Modellansicht sollte die erhaltene Originaltextur oder ausreichend
feine, unabhängig budgetierte Vorschau-Geometrie und glatte Normalen verwenden.
Eine reine Änderung der Normalen behebt die blockigen Augenfarben nicht. Ein
Farbwert pro Eckpunkt ist eine Verbesserung, kann aber Texturmerkmale zwischen
den Eckpunkten weiterhin verlieren. Die technische Farbteil-/Regionsansicht darf
weiter bewusst diskrete Farben zeigen; die Modellansicht soll deren Fehler nicht
mit geometrischen Fehlern verwechseln lassen.

**Regionale Form- und Albedoprüfung statt nur globaler QA:** Die automatische
Reduktion verändert tatsächlich die Auflösung der Augen, aber die lokal gemessenen
Formabweichungen sind bei 180 mm Figurenhöhe deutlich kleiner als die Dreiecke.
Die folgenden Kugelbereiche sind geometrisch definierte Proben um die sichtbaren
Augen und Stirn, keine menschlich bestätigten anatomischen Masken.

| Bereich | Faces Original → 150k | Median Kantenlänge Original → 150k | Formabweichung p99 / Maximum Stichprobe |
|---|---:|---:|---:|
| Linkes Auge, Radius 5 mm | 2.303 → 126 | 0,231 → 1,432 mm | 0,065 / 0,075 mm |
| Rechtes Auge, Radius 5 mm | 2.149 → 122 | 0,252 → 1,288 mm | 0,076 / 0,085 mm |
| Stirnfell, Radius 8 mm | 2.170 → 142 | 0,378 → 1,716 mm | 0,056 / 0,062 mm |

Je Bereich wurden 1.000 flächengewichtete Originalpunkte gegen die Arbeitskopie
verglichen. Die Modelle bleiben auf 180 mm skaliert. Bei anderer Druckhöhe
skalieren diese geometrischen Abstände entsprechend. Das ist keine vollständige
Hausdorff-Prüfung und keine Druckfreigabe.

**Die konstante Vorschaufarbe ist im Augenbereich besonders schädlich:** Auf
exakt derselben Arbeitskopie wurden 2.000 Punkte je Bereich mit der tatsächlich
interpolierten UV-Textur und der konstanten Dreiecksmittelfarbe verglichen.

| Bereich | Vorschau-Albedofehler p95 ΔE2000 | Anteil mit ΔE2000 > 10 |
|---|---:|---:|
| Linkes Auge | 39,32 | 20,80 % |
| Rechtes Auge | 47,57 | 22,45 % |
| Stirnfell | 7,65 | 3,55 % |

Dagegen beträgt der lokale Albedofehler Original → Arbeitskopie im Augenbereich
p95 ΔE2000 4,67 bzw. 5,80. Die Vorschau verstärkt den sichtbaren Fehler daher
stark. Die Messung belegt nicht, dass das ursprüngliche generierte Auge perfekt
ist; die verbleibende Originalqualität muss mit Textur und Referenz betrachtet
werden.

Messdaten: [mesh-detail-regions-evidence.json](mesh-detail-regions-evidence.json).
Diese Datei enthält keine API-Schlüssel, signierten Downloadlinks oder Chatdaten.

## Regionales Detailbudget

Eine gleichmäßige Dreiecksverteilung ist für einen Charakter nicht das beste
Ziel. Kontrastreiche Gesichtszüge und Silhouette benötigen Schutz. Eine rein
krümmungsbasierte Vereinfachung kann viel Budget für Fellrauschen verbrauchen,
während ein geometrisch relativ glattes, aber farblich wichtiges Auge vereinfacht
wird.

Empfohlener Ablauf:

1. Die Originaloberfläche bleibt erhalten. Die Arbeitskopie wird bei geänderten
   Schutzmasken erneut aus dem Original erzeugt.
2. In der 3D-Ansicht Gesicht/Ohren oder andere wichtige Bereiche per Pinsel
   markieren. Pinselradius in Millimetern und weicher Übergang; Löschpinsel.
   Masken an den Original-Meshhash binden, damit geänderte Face-IDs keine falschen
   Bereiche markieren.
3. Geschützte Bereiche bekommen höhere Erhaltungsgewichte; Fellbereiche niedrigere.
   Nicht mehrere separat ausgeschnittene offene Netze unabhängig reduzieren:
   Gemeinsame Grenzvertices müssen übereinstimmen, sonst entstehen Nahtspalten.
4. Ein einziges globales Arbeitskopiebudget und die vorhandene Reserve für die
   Farbgrenzenverfeinerung bleiben verbindlich. Masken ändern die Verteilung,
   erhöhen das Maximum nicht. Bei zu vielen geschützten Details erhält der Nutzer
   eine konkrete Konfliktmeldung statt eines stillen Überschreitens.
5. Geschlossenheit, Komponenten, Farben und Formabweichung global **und je
   Schutzbereich** gegen das Original prüfen. UV-Koordinaten erhalten. Erst die
   verifizierte Arbeitskopie anbieten.

Blender unterstützt im Collapse-Modus Vertex Groups als Einfluss auf die
Reduktion: [Blender-Handbuch, Decimate Modifier](https://docs.blender.org/manual/en/2.80/modeling/modifiers/generate/decimate.html).
Die konkrete Schutzrichtung und Stärke der Gewichte muss in der installierten
Blender-Version an einer Kontrollgeometrie geprüft werden, bevor eine automatische
Integration als verlässlich gilt. Ein Vertex-Group-Regler allein garantiert keine
strenge lokale Fehlergrenze.

## Implementierter, isolierter Baustein

`backend/figuraforge/geometry/detail_regions.py` enthält validierte kugelförmige
Pinselmasken mit glattem Abfall sowie eine deterministische Verteilung eines
begrenzten ganzzahligen Facebudgets. Überlappende Pinsel addieren ihre Gewichte
nicht unbegrenzt. Kleine Regionen erhalten nie mehr Faces als das Original;
übriges Budget wird umverteilt. Jede nichtleere Region behält mindestens ein
Face oder die unzureichende Budgetvorgabe wird abgelehnt.

**Dieser Baustein führt noch kein Remesh aus und ist noch keine fertige
Pinseloberfläche.** Für eine tatsächliche Simplifizierung gelten zusätzlich
Topologie- und Texturprüfungen. Die unabhängigen Tests prüfen den Budgeterhalt
über viele Größenverteilungen, Schutzwirkung, Kapazitätsgrenzen und ungültige
Eingaben: `tests/test_detail_regions.py`, 11 bestanden.

Blindes Subdivide wäre keine Lösung: Es fügt auf denselben Flächen neue Dreiecke
ein, stellt aber verlorene Augenform oder verlorene Texturdetails nicht wieder her.
Glättung verändert dagegen die Form und darf nicht pauschal Wangen, Lider und
Fellmerkmale entfernen. Wenn das Original unzureichend ist, braucht es eine
gezielte geometrische Korrektur mit Referenzvergleich, keinen bloßen Facezähler.
