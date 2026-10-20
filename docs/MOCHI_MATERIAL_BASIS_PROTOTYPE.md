# Mochi: kontrollierter Materialbasis-Prototyp

16.10.2026. Ausschließlich lokaler A/B-Versuch; Hauptplan, Services, Originalmesh und aktuelle native Dateien wurden nicht geändert. Standard bleibt die bereits verifizierte exakte Originalalbedo-/Rezeptzuordnung.

## Verfahren und Belege

Dieselbe Originalgeometrie und dasselbe bestätigte Bestandspaar Beige31/EarthBrown29. Die ursprünglichen vier Quellklassen werden ausdrücklich verwendet, keine angebliche physikalische Entlichtung:

- Orange0 und dunkles Orange1 außerhalb des Schwanzes → gemeinsame Quell-Grundfarbe `#AF440A`.
- Creme2 außerhalb des Schwanzes → gemeinsame Quell-Grundfarbe `#EFB27C`.
- Schwanz: sämtliche lokalen Original-Albedofarben unverändert; Ringmuster und vorhandene Verläufe bleiben erhalten.
- Ganze schwarze Nase und vier schwarze Augenteile unverändert.

Beide Varianten verwenden dieselbe 19-Rezept-Methode und dieselbe immutable Farbreferenz. 13.673 Flächen ändern ihre Rezeptzuordnung. Am Körper sinkt die benutzte Rezeptzahl von19 auf2; alle Schwanz-Rezeptindices sind exakt unverändert. Geometrievertices unverändert. Das ist eine absichtliche Materialfarbvereinheitlichung mit erhaltenen Creme-/Braunmasken, keine Rekonstruktion unbekannter unbeleuchteter Originalmaterialien.

Prüfordner `benchmarks/mochi-material-basis/prototype-063af7de65cd4710a0875e07157f3ede/`:

- `material-basis-ab.png`: identische Vorder-/Seitenansichten und Beleuchtung, links aktuelle Albedo, rechts Prototyp.
- `material-basis-unlit-ab.png`: dieselbe reine Druckfarbbelegung ohne Beleuchtung/Geometrieschatten.
- `report.json`, beide GLB-Varianten und Einzelrender.
- Reproduktion: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python scripts/prototype_mochi_material_basis.py` erzeugt einen neuen Ordner. Die lokalen `render.py`/`render_unlit.py` halten identische Kameras und Beleuchtung fest.

## Ergebnis

Die Materialbasis macht Cremebrust, Wangen, Stirn und Ohrinnenflächen gleichmäßiger und schärfer abgegrenzt. Sie entfernt dort bewusst auch kleine lokale Farbvariationen der Textur. Das kann für einen klaren Figurenlook erwünscht sein; es verändert den Charakter der weichen ursprünglichen Farbübergänge. Schwanzringe/Verläufe bleiben erhalten.

**Das dunkle Bauch-/Unterarmbild wird damit nicht nachweisbar verbessert.** Die unbeleuchtete Kontrollansicht zeigt, dass diese Partien beim aktuellen Bestandspaar bereits weitgehend dieselbe Brown29-Druckfarbe benutzen. Die starke Abdunklung im beleuchteten Bild entsteht hier überwiegend durch Geometrie/Beleuchtung. Dunkle Originaltexturtöne werden zudem häufig schon auf den dunkelsten verfügbaren Basiston geklemmt. Dieser Befund gilt für den geprüften Mochi-/Filamentstand und ist kein allgemeiner Beweis, dass alle importierten Texturen schattenfrei sind.

Daher keine automatische Übernahme und kein Claim „Schatten entfernt“. Eine unbeleuchtete **Druckfarbenansicht** wäre bereits hilfreich: Nutzer könnten zwischen tatsächlicher Druckfarbbelegung und räumlich beleuchteter Vorschau unterscheiden.

## Optionaler Bedienentwurf, noch nicht implementiert

Nur als ausdrücklicher Vergleichsentwurf pro gewähltem Farbbereich:

| Auswahl | Verhalten |
|---|---|
| Texturverlauf erhalten — Standard | lokale originale Albedo, bisherige exakte Rezeptzuordnung |
| Materialbasis vereinheitlichen — Vorschlag | konkrete ausgewählte Quellfarbklassen auf überprüfte Grundfarben abbilden; Vorschau vorher/nachher, Zahl geänderter Flächen/Rezeptfarben anzeigen |

Wichtig: ein geometrischer Körperbereich kann zugleich braune und cremefarbene Oberflächen enthalten. Sein Schalter darf **nicht** pauschal jede Fläche auf eine einzige Farbe setzen. Die vorhandenen Farbmasken müssen separat von Bauteilgruppen erhalten bleiben. Für den geprüften Mochi-Prototyp ist die Klassenabbildung0/1→Orange und2→Creme ausdrücklich definiert; bei unbekannten Modellen wäre eine sichtbare, bearbeitbare Farbmaske nötig. Schwanz ist unabhängig auf „Texturverlauf erhalten“ gesetzt.

Ein späterer persistierter Modus müsste Quellhash, immutable Klassenmasken und die expliziten Grundfarben im Plan binden. Preview und Native-Export müssten denselben transformierten Ziel-Farbstrom verwenden und denselben per-face-Paritätstest bestehen. Erst eine explizite Annahme des Vorschlags dürfte den gespeicherten Plan ersetzen; keine automatische Änderung aus der Vorschau heraus.
