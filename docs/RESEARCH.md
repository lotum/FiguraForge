# Pruefung vorhandener Bausteine

Stand: 15.10.2026. Quellen sind Projekt-Repositories und offizielle
Anbieterdokumentation. Dies ist keine Behauptung, alle aufgefuehrten
Fremdprojekte lokal ausgefuehrt oder miteinander gebenchmarkt zu haben.

## Repositories

| Projekt | Belegter Ansatz | Einordnung fuer dieses Release |
|---|---|---|
| PartPin | Auf dem Mesh gezeichnete Konturen, Oberflaechen-Walking, gemeinsame Kappen, Stifte/Buchsen, Headless-Testaufruf | README und Repository gelesen; GPL-3.0-or-later. Nicht kopiert, eingebettet oder lokal ausgefuehrt. |
| DitherForge | Textur-/Farbabtastung, mehrfarbige 3MF, Farbgrenzen und Voxelverfahren, Filamentpalette | README gelesen. Kein Beleg fuer universelle automatisch montierbare Farbeinsaetze; nicht als eigener Code ausgegeben. |
| SpoolmanDB | Community-Datenschema und kompilierter JSON-Katalog fuer reale Filamente | Importer und fester Abruf-Endpunkt implementiert. Der reale Katalog wird nicht mit fingierten Daten gebuendelt. |
| SnapSplit / PrintSplit | Fruehere Recherchekandidaten fuer Schnitte und Verbinder | Keine aktive Laufzeitabhaengigkeit dieses Releases; deren Headless-Robustheit nicht hier bestaetigt. |
| Hunyuan3D / TRELLIS | Externe Bild-zu-3D-Modellfamilien | Eigener Gateway-Vertrag, keine Gewichte oder eigenentwickelte Generierung. Lizenz pro konkretem Modell separat pruefen. |

Links:

- https://github.com/matthewslade/PartPin
- https://github.com/rtwfroody/ditherforge
- https://github.com/Donkie/SpoolmanDB
- https://github.com/Betakontext/snapsplit
- https://github.com/wenyen-hsu/printsplit
- https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- https://github.com/microsoft/TRELLIS.2

## Architekturentscheidung

Keine proprietaere 3D-Generierung nachbauen. Die entscheidende eigene Arbeit
ist Texturregion -> gekruemmter geschlossener Koerper -> montagefaehige
Gegenflaeche. Dafuer wurde ein eigener kleiner Topologie-/Geometriekern
implementiert, statt interaktive Blender-Operatoren ungeprueft zu automatisieren.
Dies reduziert die notwendige lokale Installation; Blender bleibt ein
moegliches Reparatur- und spaeteres Riggingwerkzeug.

Bambu Studio ist nicht als Bibliothek eingebettet. Standard-Core-3MF wird
direkt geschrieben und erneut eingelesen. Komplette proprietaere
Projektmetadaten werden nicht aus unbelegten Annahmen konstruiert.

## Primaerquellen fuer Integration

| Thema | Quelle | Konsequenz |
|---|---|---|
| Bildbearbeitung | https://developers.openai.com/api/reference/cli/resources/images/methods/edit | Images-Adapter, bedingte Fidelity-/Qualitaetsparameter |
| Nano Banana | https://ai.google.dev/gemini-api/docs/image-generation | Interactions plus separater Legacy-Adapter |
| Meshy Multiview | https://docs.meshy.ai/en/api/multi-image-to-3d | 1-4 Ansichten, GLB-Ausgabe, persistierte Task-ID |
| Tripo H3 | https://docs.tripo3d.ai/model-generation/multiview-to-model-v3-0-v3-1.html | Ansichtsreihenfolge und Kompressionsrisiko beachten |
| H2D-Bauraum | https://bambulab.com/en/h2d/tech-specs | Unterschiedliche konservative Single-/Dual-Planungsprofile |
| Bambu Mixed Filament | https://wiki.bambulab.com/en/bambu-studio/color-mixing | Als optionales zukuenftiges Profilmodul dokumentiert, nicht als Hotend-Mischung missverstanden |
| Blender 3D Print Toolbox | https://extensions.blender.org/add-ons/print3d-toolbox/ | Geeignet fuer externe Kontrolle; nicht als ausgefuehrte Integration behauptet |
| 3MF | https://github.com/3MFConsortium/spec_core | Standardformat statt selbst erfundener STL-Farbkonvention |

## Noch notwendige externe Benchmarks

Derselbe reale Charakter durch mindestens zwei bezahlte 3D-Provider, mit
identischen vier Ansichten und sichtbarer Albedo. Danach Vergleich von
Identitaet, Details, verdeckten Flaechen, geschlossenen Volumen, Farbgrenzen und
Einsatzmontage. In diesem Release wurde **kein** Anbieter zum nachweislich
besten 3D-Generator erklaert. Die Architektur laesst einen Wechsel zu.
