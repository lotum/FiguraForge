# Bambu Mixed Filament: geprüfter Vertrag und offene Abnahme

## GUI-Abnahme: 19 Rezeptfarben aus zwei Basisfilamenten bestanden

Am 16.10.2026 wurde zusätzlich der vollständige 19-Farben-Prüfstreifen in Bambu Studio 02.07.01.62 geöffnet und tatsächlich gesliced: **zwei reine Basisfarben plus 17 native Mischrezepte in 5%-Abständen zwischen 10/90 und 90/10**. Die Vorlage mit den zusätzlichen virtuellen Slots wurde von Bambu Studio selbst angelegt; FiguraForge hat keine zusätzlichen physischen Filamente, Temperaturen oder unbekannten Profilarrays erfunden.

| Merkmal | Tatsächlicher GUI-Befund |
|---|---|
| Verwendete Basisfilamente | Grün `#08B690` und Beige `#F7E6DE` |
| Düsen-/Filamentzuordnung | Links Slot 1, rechts Slot 2 |
| Rezeptfarben | 19 insgesamt, davon 17 virtuelle Mischungen |
| Prüfstreifenhöhe | 2 mm |
| Angezeigte Unterlagen-/Schichtschritte | 163 |
| Materialschätzung | 5,01 g |
| Gesamtdruckzeitschätzung | 33 min 34 s |
| Physischer Druck / gemessene Farbwirkung | Nicht geprüft |

Beleg: [echte 19-Rezepte-Sliceransicht](../screenshots/bambu-19-recipes-sliced-macos.png). Native Datei und reproduzierbarer Aufbau: `benchmarks/native-19-recipe-stripes-20261016/h2d-native-19-colors-two-spools.3mf`, `build.py`, `result.json`; die getrennte Auswertung steht in `REPORT.md` daneben.

Der separat über die GUI exportierte G-Code ist ebenfalls geprüft: zehn 0,2-mm-Basisschichten, echte `LAYER_HEIGHT`-Abschnitte von 0,02 bis 0,18 mm in 0,01-mm-Schritten (je 18 Kommentare; einschließlich beider Rezeptanteile) sowie ausschließlich reale Werkzeugwahlen T0/T1. Kommentarzahlen sind keine gedruckten Messwerte. [Maschinenlesbarer Nachweis](bambu-19-recipes-gui-verification.json).

**Aktualisierte CLI-Prüfung:** Die frühere Ablehnung mit Exit231 ist durch die korrekte offizielle Syntax `--normative-check=0` für die MakerWorld-Normative-Prüfung geklärt. Native Mixed-Characterprojekte wurden inzwischen tatsächlich gesliced. Die G-Code-Prüfungen bleiben aktiviert; trotzdem ist CLI-Exit0 keine vollständige Pfadkonfliktfreigabe (belegte Negativkontrolle der alten Mochi-Platte). Eine unabhängige Extrusions-Footprintprüfung ergänzt die fünf neuen Mochi-Platten, siehe `docs/mochi-v2-extrusion-footprint-verification.json`. Ohne tatsächlichen Testdruck sind Farbgenauigkeit, Schichtverbund und Druckergebnisse weiterhin offen.

Die folgende ältere Prüfung des 85/15-Würfels bleibt als zusätzlicher Import-/Save-/G-Code-Nachweis erhalten. Historische Abschnitte über eine fehlende GUI-Abnahme werden durch die beiden dokumentierten GUI-Prüfungen für genau diese Testdateien ergänzt; sie sind keine Freigabe beliebiger Character-Exporte.


## GUI-Abnahme am 16. Oktober 2026: Mixed-Würfel bestanden

Nach Richards ausdrücklicher Freigabe zum Verwerfen der ungespeicherten
Bambu-Änderungen wurde der native Export in Bambu Studio 02.07.01.62 geöffnet,
als neue Datei gespeichert und tatsächlich gesliced. Die älteren Abschnitte
zur noch fehlenden GUI-Abnahme beschreiben den Stand vor dieser Prüfung.

**Import, nativer Save-Roundtrip und Slicing für den 85/15-Testwürfel bestanden.**
Die acht Mischrezepte bleiben nach dem GUI-Speichern erhalten. Der exportierte
G-Code enthält 59 Unterschichten mit 0,17 mm und 59 mit 0,03 mm: zusammen
0,20 mm mit 85/15-Aufteilung. Gedruckt wurde nicht; physische Farbwirkung und
Montage sind damit nicht abgenommen.

Die GUI-Prüfung fand zwei zuvor vom Geometrievergleich nicht erfasste Fehler:

- CLI-Konvertierung lieferte `printable="0"` → der Builder setzt die Markierung
  erst nach erfolgreicher Prüfung gegen den echten gemeinsamen Düsenraum und
  ergänzt die native Platten-Instanzzuordnung.
- Ein allgemeiner XML-Neuaufbau entfernte das ungenutzte Bambu-Namespace und
  wurde von der GUI als fremdes 3MF interpretiert → das Hauptmodell bleibt
  bytegetreu bis auf gezielt ersetzte Printable-Attribute.

Die echte H2D-Vorlage besitzt einen gemeinsamen Düsenraum **X 25–325,
Y 0–320, Z 0–320 mm**. FiguraForges normaler 300-mm-Packrahmen beginnt bei X=0;
native Platten bekommen deshalb eine dokumentierte Verschiebung um +25 mm X.
Der Builder prüft danach reale Polygone, Höhen und Ausschlussbereiche und
weist unpassende Teile ab. Core-Begleiter behalten ihren normalen Packrahmen.

Belege: [maschinenlesbare GUI-/G-Code-Prüfung](bambu-mixed-gui-verification.json),
[echte Slicer-Vorschau](../screenshots/bambu-mixed-sliced-macos.png).
Dateien liegen lokal unter `benchmarks/mixed-filament-native/`:
`dragon-profile-cube-printable.3mf`, `dragon-profile-cube-gui-roundtrip.3mf`,
`dragon-mixed-gui-verification.gcode`. Das G-Code-File ist ein Prüfbeleg,
keine pauschale Druckfreigabe für andere Figuren oder Spulen.


Stand: 16.10.2026. Kein Druckauftrag, kein Upload, kein kostenpflichtiger API-Aufruf.

## Fachliche Trennung

Ein montierbares Bauteil darf mehrere Farbregionen enthalten: etwa ein braun/beiges Ohr. Die gewünschte Beschränkung auf zwei Basisfilamente gilt **pro Bauteil**, nicht für die gesamte Figur. Mischrezepte verweisen auf physische Filamentslots; ein Mischslot ist keine zusätzliche Rolle. Zwei Düsen bedeuten technisch nicht automatisch nur zwei AMS-Farben: das Zwei-Farben-Limit ist hier die gewählte Produktvorgabe für H2D-Bauteile.

Die native Funktion druckt Unterlagen unterschiedlicher Filamente. Sie mischt keine Pigmente in einer Düse. Farbergebnis, Detailverlust und Sichtbarkeit der Streifen hängen von Filamenten, Schichthöhe und Blickrichtung ab. Ein rechnerischer RGB-Mittelwert ist keine farbverbindliche Vorhersage.

Ein nativer **Z-Gradient** folgt der Druckhöhe. Er bildet einen beliebigen Verlauf um einen liegenden Schwanz nicht automatisch ab. Dafür braucht es örtlich zugewiesene Mischrezepte auf dem gleichen Bauteil, gespeichert als native Dreiecksbemalung. Bauteilorientierung muss vor der endgültigen Verlaufsprüfung feststehen.

## Verifizierte native Felder

Offizieller Quellcode: [PrintConfig.cpp](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/PrintConfig.cpp), [FilamentMixer.cpp](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/FilamentMixer.cpp), [MixedFilamentDialog.cpp](https://github.com/bambulab/BambuStudio/blob/master/src/slic3r/GUI/MixedFilamentDialog.cpp), [Model.cpp](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Model.cpp), [3MF-Serializer](https://github.com/bambulab/BambuStudio/blob/master/src/libslic3r/Format/bbs_3mf.cpp). Die verlinkten master-Dateien sind beweglich; Feldnamen und konkrete lokale Prüfgrenzen unten dokumentieren den gelesenen Stand.

| Pfad/Feld | Bedeutung |
|---|---|
| `Metadata/project_settings.config` | Native JSON-Projekteinstellungen und Filamentslots |
| `Metadata/model_settings.config` | Native Objekt-/Bauteilzuordnung; `metadata key="extruder" value="N"` bezeichnet den 1-basierten Slot |
| `enable_mixed_color_sublayer` | Globaler Schalter; im gespeicherten JSON `"1"` |
| `filament_is_mixed` | Slot-Array aus `"0"`/`"1"` |
| `filament_mixed_components` | Slot-Array; z. B. `"1,2"`, **1-basiert**, Referenzen auf physische Slots |
| `filament_mixed_sublayer_ratios` | Slot-Array; z. B. `"0.35,0.65"` |
| `filament_mixed_gradient` | Optionaler nativer Druck-Z-Verlauf; hier bewusst deaktiviert |
| `filament_mixed_gradient_range` / `_curve` / `_per_part` | Native Z-Verlaufsparameter; bestehende leere/deaktivierte Werte bleiben erhalten |
| `filament_colour` | UI-Vorschaufarben; keine Kalibrierung |
| `3D/Objects/*.model` | Native Dreiecksgeometrie; jedes `triangle` kann `paint_color` tragen |

`paint_color` ist **kein normaler Slotindex**: Bambu `Model.cpp` codiert vollständig bemalte Dreiecke mit `4` für Slot 1, `8` für Slot 2, `0C` für Slot 3, `1C` für Slot 4 usw. Bis Slot 32 ist die offizielle Tabelle im Modul übernommen. Es werden keine subtriangulierten, unbekannten Bitfolgen erzeugt.

## 5%-Stufen

Die gelesene offizielle UI setzt `MIN_COMPONENT_RATIO=10`; native Gradientensampler begrenzen ebenfalls auf 10–90%. Deshalb erzeugt `recipe_library((1,2),5)` **17 Mischrezepte**: 10/90, 15/85, …, 90/10. Reine 0/100 und 100/0 verwenden die beiden ursprünglichen Filamente. 5/95 und 95/5 werden nicht als UI-kompatibel zugesichert. Diese Bibliothek benötigt keine KI.

Alle 17 Mischslots plus zwei physische Slots ergeben 19 Slots; das konservative Gesamtlimit dieses Vertrags ist 32. Zusätzliche Paare für andere Bauteile teilen Slots soweit möglich und müssen innerhalb dieses Limits bleiben.

## Implementierung

`backend/figuraforge/services/mixed_filament.py` bietet:

- `MixRecipe`, `recipe_library`: deterministische Rezepte.
- `validate_native_settings`: vollständige Slotarrays, endliche normierte Verhältnisse, physische Komponenten, maximal zwei Komponenten; verschachtelte virtuelle Rezepte werden abgelehnt.
- `validate_part_filament_limits(settings, {part_id: [slot,...]})`: expandiert Mischslots und begrenzt jedes Bauteil separat auf zwei physische Filamente.
- `read_native_template(path)`: begrenzter ZIP-Metadatenleser, keine Extraktion. Reines Core-3MF ohne native Objektzuordnung wird abgelehnt.
- `apply_recipes_to_template(settings, {mixed_slot: MixRecipe(...)})`: ändert ausschließlich existierende Mischslots in einer Kopie. Vorhandene Maschinen-/Filamentprofile bleiben erhalten; keine erfundenen Temperaturen oder G-Codes.
- `attach_native_painting(source, output, settings, paintings)`: schreibt eine **neue** native Datei und konkrete Flächenzuordnungen. Vorhandene unselektierte Bemalung bleibt erhalten. Quelle und Ausgabe müssen verschieden sein, Ausgabe darf noch nicht existieren.
- `verify_native_roundtrip`: vergleicht tatsächliche native Einstellungen nach einem echten Bambu-Speichern; die Funktion selbst startet keinen Slicer und bestätigt keine Druckfähigkeit.

Ein Malauftrag lautet:

```python
paintings = [{
    'model_path': '3D/Objects/object_1.model',
    'object_id': '1',
    'expected_triangle_count': 1200,
    'face_slots': {0: 3, 17: 4},  # Dreiecke 0-basiert, Filamentslots 1-basiert
}]
```

Die Flächen müssen auf genau diese Exporttopologie abgebildet werden. Ein nachträgliches Remesh macht ein solches Mapping ungültig; gleiche Dreieckszahl allein beweist keine gleiche Topologie. Der Aufrufer muss den Plan zusätzlich an den Geometriehash binden. Ein nächstgelegenes Dreieck oder eine Farb-ID darf nicht als nativer Dreiecksindex missverstanden werden.

Die Integration braucht eine vom passenden Studio erzeugte H2D-Vorlage mit den benötigten physischen und virtuellen Slots. Neue Slots dürfen nicht allein durch Anhängen von Farben erzeugt werden: alle Filamentprofil-Arrays und Düsen-/AMS-Zuordnungen müssen konsistent sein. Dieses Modul erweitert daher keine unbekannten Profilarrays. Es schaltet einen vorhandenen generischen Core-3MF-Export nicht automatisch in einen nativen Misch-Export um.

## Tatsächlich durchgeführte Prüfung

Installiertes Bambu Studio: **02.07.01.62**.

28 lokale Tests bestanden: Rezeptgrenzen, Eingabe-Unveränderlichkeit, ungültige/virtuelle Slotreferenzen, NaN, Ratio-Summen, Arraylängen, Teilgruppengrenzen, echte XML-`paint_color`-Attribute und Schutz vor Überschreiben.

Zusätzlich wurde eine synthetische Vorlage aus einem früher lokal erzeugten Bambu-Roundtrip abgeleitet; keine originale Benutzerdatei wurde verändert. Die Datei ist **keine geprüfte H2D-Vorlage**. Zwei physische Slots, ein 35/65-Mischslot und drei gezielt bemalte Dreiecke wurden geschrieben:

- `benchmarks/mixed-filament-native/painted-input-v2.3mf`
- `benchmarks/mixed-filament-native/roundtrip-v2.log`

Der echte Standard-CLI-Aufruf `--export-3mf ... --arrange 0 --orient 0 ...` bricht ab:

```text
normative_check: mixed filament is not supported
```

Exitstatus 231. Auch `--normative-check=false` beseitigt diese Ablehnung nicht. Die Standard-CLI-Prüfung ist damit **blockiert**, nicht bestanden. Dies beweist nicht, dass die GUI das Feature nicht unterstützt; CLI und GUI haben unterschiedliche Einschränkungen.

**Nicht abgenommen:** Öffnen/Speichern dieser Vorlage in der Bambu-GUI, native Farbauswahl nach dem Import, H2D-Zuordnungen, gemischte Unterlagen im G-Code, Farbwirkung eines Testdrucks. Es existiert bislang keine ehrlich als H2D-Mixed-Roundtrip-abgenommen bezeichnete Projektvorlage. Solange diese Abnahme fehlt, muss ein Export mit solchen Regionen als blockiert/experimentell gekennzeichnet bleiben; ein Core-3MF-Farbwert darf nicht als funktionierendes Mischrezept ausgegeben werden.

Die angegebene [Bambu-Wikiseite](https://wiki.bambulab.com/en/bambu-studio/color-mixing) lieferte dem Webabruf HTTP 402; deshalb wurden die technischen Feldnamen und Grenzen zusätzlich im offiziellen Quellcode geprüft.


## Sichere Vorlagenprüfung und experimenteller Geometrieaufbau

`inspect_template(path, require_mixed=False)` verlangt `printer_model = "Bambu Lab H2D"`, genau zwei positive, endliche Düsendurchmesser und mindestens eine echte physische Spule. Eine reine Solid-Vorlage braucht keinen erfundenen Mischslot und ist für Upload und nativen Builder zulässig. `require_mixed=True` verlangt zusätzlich mindestens zwei physische und einen vorhandenen gültigen Mischslot. Tatsächlich gemischte Pläne stoppen beim Materialmapping weiterhin, wenn keine passende Rezeptbibliothek existiert. Die Ergebnisfelder `physical_only` und `mixed_supported` unterscheiden beide Fähigkeiten. Leere explizite H2D-Hardwarelisten werden weiterhin abgewiesen. Die Vorschau gibt ausschließlich eine Einstellungs-Allowlist, Basisfilament-Material/Hersteller/Farbe und Modellpfade mit Objekt-IDs/Dreieckszahlen zurück. G-Codes, beliebige Profilfelder, Kontodaten und Dateipfade aus Einstellungen werden nicht als Vorschau zurückgegeben. Ungültige ZIP-Pfade, Backslashes, Laufwerkspfade, Symlinks, verschlüsselte und doppelte Einträge werden abgelehnt. Die Vorlagenprüfung nutzt jetzt Streaming: 4096 Einträge, 4 GB deklarierte Gesamtgröße, 8 MB je relevanter Konfiguration und 2 GB je gestreamtem Modell; Auxiliary-Inhalte werden nicht gelesen. Der separate Writer für neue, kleine Geometrie behält konservative Speicherlimits. Die Prüfung liest Archive, ohne sie zu extrahieren.

`build_native_from_parts(template_path, output, parts, placements, settings, face_slots)` nutzt den bestehenden Core-3MF-Schreiber für **neue** Geometrie, konvertiert diese über die installierte Bambu-CLI ohne Mischslots ins native Format und überträgt danach die vollständigen bereits vorhandenen H2D-Projekteinstellungen samt Flächenbemalung. `face_slots` muss für jedes Teil alle Dreiecke explizit auf einen Slot abbilden. Die Funktion prüft:

- native Objektzuordnung anhand eindeutiger Teil-IDs;
- identische Dreiecksreihenfolge und geordnete Dreieckskoordinaten bis 0,001 mm nach Zentrierung;
- alle Weltkoordinaten der importierten Geometrie bis 0,001 mm über unabhängige bidirektionale Punktabstände;
- höchstens zwei physische Filamente je Teil nach Auflösen virtueller Mischslots.

Abweichungen, fehlende Teile und unvollständige Flächenzuordnungen brechen vor dem finalen Export ab. CLI-Aufruf ohne Shell, mit 90 Sekunden Zeitlimit; kein Slicing, keine Druckerkommunikation. Der neue Arbeitsordner enthält Zwischengeometrie und ein lokales Konvertierungsprotokoll. Eine vorhandene Ausgabedatei wird nicht überschrieben.

Echter lokaler Integrationstest: ein neuer Würfel mit zwölf Dreiecken und allen Flächen auf Mischslot 3 wurde über die CLI konvertiert und anschließend bemalt. Geometrie- und Weltkoordinatenfehler jeweils **0 mm**. Datei: `benchmarks/mixed-filament-native/built-parts-on-bed.3mf`. Die für diesen Vertragsprüfversuch verwendete Vorlage war synthetisch mit H2D-Metadaten versehen; sie bestätigt ausdrücklich keine gültige Benutzer-/Maschinenkonfiguration. Ein Würfel unterhalb der Platte wurde vom Slicer angehoben und vom Prüfer deshalb korrekt abgelehnt.

**Diese Konvertierung prüft ausschließlich die Geometrie vor dem Hinzufügen der Mischmetadaten.** Das endgültige gemischte Ergebnis ist weiterhin `experimental: true`, `native_roundtrip_verified: false`, `slicing_verified: false` und verlangt die GUI-Abnahme mit einer echten H2D-Vorlage.

Ein bestehender Mischslot wird nicht blind siebzehnmal geklont: unter anderem Temperatur- und Retraktionsarrays tragen ebenfalls Filamentdaten und heißen nicht alle `filament_*`. Eine vollständige 17-Rezept-Bibliothek braucht deshalb eine entsprechend angelegte native Vorlage oder einen zusätzlich verifizierten nativen Slot-Erweiterungspfad. Vorhandene Rezepte lassen sich bereits prüfen und ohne erfundene Profile verwenden.


Die inzwischen vom Nutzer bereitgestellte echte H2D-Vorlage wurde separat geprüft; aktuelle Befunde, kleine Profilkopie und echter Würfeltest mit diesen Profilen stehen in [DRAGON_TEMPLATE_VERIFICATION.md](DRAGON_TEMPLATE_VERIFICATION.md). Die ursprüngliche synthetische Vorlage ist keine Voraussetzung mehr. Die finale Misch-GUI-Abnahme bleibt offen.


## Welche native Vorlage Mochi tatsächlich braucht

Der 19-Rezeptnachweis verwendet Grün und Beige. Das ist eine Funktionsprobe und noch keine passende Mochi-Farbkonfiguration. Im aktuell gespeicherten Projekt „Mochi · neuer Farb- und Montageplan“ sind Bambu PLA Basic Beige (`#F7E6DE`, Inventar 31) und ELEGOO PLA Matte Earth Brown (`#805947`, Inventar 29) ausgewählt. Die passende native Bambu-Vorlage dafür fehlt noch. Die vorhandenen Zielfarben sind Orangebraun `#AF440A`, Dunkelbraun `#852F06`, helles Creme `#EFB27C` und fast Schwarz `#090505`.

Für den vorgesehenen Aufbau braucht die spätere native Vorlage:

1. Zwei konkrete, temperatur-/flusskompatible Orange-/Braun- und Creme-/Beige-Spulen samt echten Druckprofilen; daraus entstehen die virtuellen Verlaufsfarben auf Grundkörper, Schwanz und gegebenenfalls getrennten Ohren.
2. Ein zusätzliches echtes schwarzes Profil für separat konstruierte Nase/Augenteile. Damit bleibt jedes Bauteil innerhalb seiner gewählten Zwei-Basisfilament-Grenze, obwohl die gesamte Figur mehr Farben besitzt.
3. Die 17 nativen Mischslots müssen genau dieses Braun-/Beige-Paar referenzieren. Ein grünes Profil nur durch Ändern seines HEX-Werts als braunes Material auszugeben wäre unzureichend.

Die aktuelle Auswahl ist **Beige 31 plus Earth Brown 29**. Das zusätzliche schwarze Profil ist noch konkret zuzuordnen; vorhandener Kandidat ist eSUN ePLA-Lite Black `#272729` (Inventar 30). Das zuvor nur als möglicher Kandidat betrachtete ELEGOO PLA+ Brown (Inventar 28) ist nicht das ausgewählte Basisfilament.

Die Bestands-HEX-Werte sind ungemessen. Ein Earth-Brown-/Beige-Verlauf kann nicht beliebige Orangebraun-Zielfarben rekonstruieren; `#AF440A` und `#852F06` liegen nicht automatisch auf seiner Farbmischlinie. Ob die gedämpfte Palette genügt oder ein anderes reales Basispaar gewählt werden soll, bleibt eine bewusste Farbentscheidung. Weder Spulen noch Herstellerpresets wurden hierfür verändert. Die native Vorlage muss die tatsächlichen Profile für Earth Brown 29 und Beige 31 verwenden; ein grünes Testprofil nur über seinen HEX-Wert umzufärben wäre unzureichend.

Die explizite Prozess-Allowlist umfasst zusätzlich `wipe_tower_x`, `wipe_tower_y` und `prime_tower_width`. Damit bleiben bewusste Turmplatzierungs-/Breitenänderungen beim GUI-Presetimport als Prozessdifferenzen erhalten; thermische Materialparameter und G-Code werden dadurch nicht in die Prozessgruppe übernommen. Der Test des Hilfsvertrags bestätigt keine reale Turmreserve oder Pfadfreigabe einer noch nicht gesliceten Platte.
