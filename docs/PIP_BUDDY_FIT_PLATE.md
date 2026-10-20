# Optionaler Pip-/Buddy-Passungstest

**Aktuelle Version nach belegter Kernkorrektur:** Buddy `_primitive` erreicht die volle Kontur nun genau an der echten Wurzel und bleibt über2 mm Boolean-Überlappung konstant. Reale Querschnittstests bestätigen0,05 mm Wurzelspiel. Die neue unten genannte Datei ist mit dem korrigierten Kernhash gebunden und neu gesliced. Die alte Version `fit-b5dedbd6f3304ac5b6b001de7240199e` bleibt unverändert erhalten und ist als damals nicht repräsentativer Buddy-Vergleich zurückgezogen.

Die akzeptierte Mochi-Nasenprobe0,05 mm radial ist ein Ausgangspunkt, keine physische Abnahme anderer Größen/Formen. Neue kleine Vergleichsplatte: vier Paare, acht tatsächlich mit A–D beschriftete, jeweils geschlossene zusammenhängende Körper. Keine vorhandene Datei überschrieben.

| Paar | Tatsächlicher Anschluss | Profil | Nennmaß | Länge |
|---|---|---|---:|---:|
| A | Buddy großer Halsbandanschluss | keyed | 12 mm Schlüsselbreite | 10 mm |
| B | Buddy Halsband-Teilfuge | keyed | 4 mm Schlüsselbreite | 6 mm |
| C | Pip Pupille | rund | Ø1,8 mm | 1,5 mm |
| D | Pip Iris | rund | Ø2,4 mm | 2,5 mm |

Die Geometrie verwendet direkt `Connector.profile()` und dieselbe vollständige85%-Spitzenverjüngung des Konstruktionskerns. Alle0,05 mm nominal radiales Spiel,0,35 mm axiales Spitzenspiel. Keyed ist ein angefastes Quadrat: Nennmaß ist die Schlüsselbreite, kein Kreisdurchmesser. Der Test ersetzt keine Belastungsprüfung des großen Buddy und prüft nicht dessen längere16-mm-Strukturstifte.

## Dateien und echte Prüfungen

Ordner `benchmarks/connector-fit-pip-buddy/fit-ce7f19c742784154aef094d803f90fbd/`:

- Native Datei `Pip-Buddy-Passung-Beige-H2D.3mf`, beige2.
- `PASSUNG.md`: konkrete Bedien-/Bewertungsanleitung.
- `fit-plate-top.png`: quellgeometrische Draufsicht; Helligkeit dient nur der Tiefenzeichnung.
- `verification.json` und `path-screening.json`: Geometry/Native/G-Code-Nachweise.

Tatsächlicher Bambu-Slice mit H2D0,4/0,4 mm,0,12-mm-Layer,0,20-mm-Erstschicht, bestehendem Bambu-PLA-Basic-Beige-Profil: Exit0, leeres Warnfeld,54m46s,12,51 g, ausschließlich physischer Slot2/GFA00. Alle Stifte stehen aufrecht, Taschen öffnen nach oben und besitzen2 mm geschlossenen Boden. Es gibt keine abwärts gerichteten/überbrückten Flächen über dem Bett; Supports, Raft und Brim sind ausdrücklich aus.

Unabhängig34.306 tatsächliche Extrusionssegmente geprüft: Linienbreiten-erweiterte XY-Footprints aller acht Owner getrennt; keine Crossobject-Footprintkollision. Vier gezielte Couponregressionen bestanden einschließlich Profilidentität, Volumenbilanz und stützfreier Taschen. Getrackter Nachweis mit Hashes `docs/pip-buddy-fit-plate-verification.json`.

Die CLI-Bildminiatur erscheint grün, obwohl Projektprofil, sämtliche Objektdefaults und tatsächlich geslicete Extrusion ausschließlich Slot2 Beige belegen. Die Miniatur ist daher kein Materialnachweis; diese Abweichung wird ausdrücklich offengelegt. Unbenutzte Profile bleiben in der Vorlagensammlung erhalten, benötigen aber keine weiteren geladenen Spulen für diese Platte.

## Optionaler nächster Nutzertest

1. Native Datei in Bambu Studio öffnen, H2D und tatsächliches Beige31 auf Slot2 prüfen. Ausrichtung und0,12-mm-Layer beibehalten. Kein Drehen der Taschenöffnung zur Platte.
2. Optional selbst slicen/drucken; der Agent sendet keinen Auftrag. Innerhalb der Taschen werden keine Stützen benötigt.
3. Nach Abkühlen jeweils gleiche Buchstaben paaren und Sitz/Einsteckkraft/Restspiel melden. Kein gewaltsames Stecken.
4. Erst daraus die betroffenen Pip-/Buddy-Anschlüsse physisch beurteilen. Bis dahin bleiben die digital geprüften Produktionsentwürfe erhalten; Gesamtdruck, Haltbarkeit und reale Materialunterschiede sind nicht freigegeben.
