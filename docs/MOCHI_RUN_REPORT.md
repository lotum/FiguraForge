# Mochi: modellgebundener Produktionsentwurf

Verifiziert am 16.10.2026. Status: lokal konstruierter und farbig geprüfter Entwurf; die endgültigen Mischprojekte brauchen noch die GUI-Slicerprüfung und einen physischen Passungs-/Farbtest. Kein Druck gestartet, kein Cloudauftrag, keine Freigabe erzeugt. Originale unverändert.

## Quelle und Reproduktion

- Projekt `1b0e2fdd463d4f15ac64f1c7b3e8acc7`, 180 mm, Y-up.
- Arbeitskopie SHA-256 `c8b50eee6cce4bf76ca8ef17050c44694e6db0ee7d18bdd47cf48507fc065643`; Meshhash `56c3e3b339a0710a9eab9392cc657b5f4c1d7b6c7d9e37866074fd32ee089d17`.
- `services/mochi_pipeline.py`: Vorschlag/Konstruktion ohne Datei-, Datenbank-, Freigabe- oder Netzwerkeffekte. Geometriesignatur, Meshhash, Original-Farbmasken und Maßstab verhindern die versehentliche Anwendung auf andere Figuren. Konstruktion braucht die unveränderte 150k-Arbeitskopie vor Farbgrenzen-Verfeinerung.
- Reproduktion: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend .venv/bin/python scripts/build_mochi_production.py --project 1b0e2fdd463d4f15ac64f1c7b3e8acc7`. Jeder Lauf erzeugt einen neuen Ordner.
- Aktueller Lauf: `benchmarks/mochi-production/draft-9372a14613a141a888aac191637a22e4`, 42,1 Sekunden einschließlich Konstruktion, berechneter Farb-/Teilevorschau und Core-3MF-Roundtrip. Die nativen Dateien wurden anschließend separat erzeugt.
- Profilvorlage neu erzeugen: `PYTHONPATH=backend .venv/bin/python scripts/build_mochi_native_template.py` (neuer Laufordner, keine Quelle überschrieben); anschließend optional `scripts/build_mochi_production.py --project … --native-template PFAD`.
- Reproduzierbare native Profilherstellung und Export/Prüfung: `benchmarks/mochi-native-template-20261016/{build.py,export_mochi.py,check_mochi.py}`. Benchdateien sind lokale, ignorierte Prüfdaten.

## Konstruktion und Farbe

9 geschlossene, jeweils zusammenhängende Teile: Körper, ganze schwarze Nase, beide ganzen Ohren, Schwanz, vier schwarze Augeneinsätze. Die Ohren enthalten jeweils ihre ursprünglichen hellen und dunklen Flächen; die Geometrie wird nicht entlang jeder Farbe zerlegt. 7 Stifte und 10 gemeinsame Montagepfadprüfungen bestanden. Source-Volumen 476224,437 mm³; Teilevolumen 476150,986 mm³; Differenz 73,451 mm³ als überprüftes Verbindungsspiel.

| Teilgruppe | Material und Farbe | Montage / Druck |
|---|---|---|
| Körper, Ohren, Schwanz | bestätigtes Bestandspaar Beige31 `#F7E6DE` + ELEGOO Matte EarthBrown29 `#805947`; 17 virtuelle Mischrezepte plus beide reinen Farben | Platte 1, zwei reale Spulen; ganze Anhänge mit Stiften |
| Nase | eSUN ePLA-Lite Black30 `#272729` | Platte 2, ein Nasenstift R1,5/L3 mm |
| Vier Augeneinsätze | dieselbe schwarze Spule30 | Platte 2, ausschließlich Klebeteile, keine behauptete Steckverbindung |

Ohren/Schwanz: R1,2/L2,5-mm-Stifte. Aktuelles radiales Spiel 0,2 mm. Das anatomische Preset ersetzt die allgemeinen Stiftgrößen-/Inlaytiefe-Einstellungen durch diese dokumentierten Werte; anderes radiales Spiel wird unterstützt. Die Augen behalten den geprüften 1-mm-Tiefen-/0-mm-Seam-Entwurf; tatsächliches Klebespiel und ausreichende Haftung sind noch offen.

Farben werden für jede ursprüngliche Außenfläche aus lokaler Albedo berechnet, mit 19 theoretischen Rezeptfarben und exakter Rezeptzuordnung in der nativen Datei. Neue Innenflächen erhalten das dominante tatsächliche Material desselben Teils; die Vorschau zeigt sie neutralgrau. Lineare Lichtmischung ist eine unkalibrierte optische Näherung, keine Messung des gedruckten PLA. Median ΔE2000 15,1622; P95 17,2895. Das vorhandene warme Braun/Beige-Paar erhält die Muster, erreicht das Orange der Originalreferenz aber nicht. Eine rechnerisch besser passende rot/grüne Kombination wurde wegen ungesicherter physischer Mischwirkung und ungeeigneter Basiswirkung nicht automatisch gewählt.

## Native Materialien und Dateien

Neue Profilvorlage: `benchmarks/mochi-native-template-20261016/mochi-real-materials-profile-only.3mf`. Slot1 = Brown29, Slot2 = Beige31, Slot3 = Black30; Slots4–20 = echte native virtuelle Mischrezepte desselben 1/2-Paars. Kein Glow- oder Sea-Green-Profil. Keine Originalgeometrie oder privaten Vorschaubilder enthalten.

Die offizielle Bambu-CLI hat aus den installierten Profilen `Generic PLA @BBL H2D` und `Bambu PLA Basic @BBL H2D` die vollständigen 20-Slot-Arrays aufgebaut. Vererbte Basen und Dual-Includes stammen ausschließlich aus den installierten Bambu-JSON-Dateien; SHA-256 und daraus erzeugte Profile stehen in `profile-provenance.json`. Anschließend wurden nur die bereits vorhandenen nativen Mixed-Projektfelder wieder eingesetzt und vorhandene virtuelle Slots mit exakten Rezepten belegt. Keine unbekannten Arraydimensionen erfunden.

EarthBrown/eSUN verwenden ausdrücklich **unkalibrierte Generic-PLA-Startprofile**, keine Herstellerspezialprofile. Beige verwendet Bambu PLA Basic. Offizielle Werte: 220 °C, Fluss .98; Generic max. 12 mm³/s, Bambu Basic 25/40 mm³/s je Düse. Beide .4-mm-Düsen unverändert.

Endgültige Projektdateien im aktuellen Lauf unter `native-export/`:

- `plate-01-H2D-regional-native.3mf`: Körper, Ohren, Schwanz. Weltgeometriefehler maximal 0,000005811 mm. 0,2-mm-Layer, Tree-Support, nur vom Bett, Schwelle20°, Top-Abstand0,2, Auto-Brim5 mm.
- `plate-02-H2D-regional-native.3mf`: Nase und vier Augeneinsätze. Weltgeometriefehler maximal 0,000000226 mm. Zusätzlich Raft3 und Outer-Brim5 mm für die gekrümmten Auflageflächen.

Beide Dateien bewahren native Namespaces, druckbare Builditems, Platten-/Modellzuordnung, Profile und explizite Prozess-Abweichungen. Auf H2D-Koordinaten +25 mm X versetzt, ohne Skalierung. Originalfigur bleibt im unveränderten Montagekoordinatensystem.

Die installierte CLI lehnt Mixed-Projekte grundsätzlich mit Exit231 ab. Deshalb **keine abschließende Slicerabnahme dieser zwei Dateien**. Frühere GUI-Abnahme der 19-Farb-Teststreifen belegt die native Rezepttechnik, nicht die Druckbarkeit von Mochi.

## Konkrete Fehler, UX-Folge und Prüfung

| Fehler / Risiko | Folge | Änderung / Beleg | Offen |
|---|---|---|---|
| Anatomie war nur in einem Prüfskript vorhanden | Normaler Workflow konnte die geprüften Teile nicht reproduzieren | modellgebundener Service, Vorschlag und kanonischer 9-Regionen-Plan; API/UI-Adoption durch Hauptagent | Nutzerabnahme des Entwurfs |
| Bauteil-Durchschnittsfarbe statt lokaler Rezepte | Schwanz-/Fellmuster wirkten falsch; Vorschau entsprach nicht dem Export | berechnete per-face-Rezepte, geglättete ursprüngliche Außennormalen, neutrale neue Innenflächen; keine Geometrieglättung | kalibrierte reale Mischfarben |
| 22 neue Nasentaschen-Dreiecke lagen innerhalb der alten .03-mm-Oberflächentoleranz | fälschlich dritte schwarze Spule am Körper, Export korrekt blockiert | nur für quellidentisches Mochi-Preset .0001-mm-Grenze; 0,359 mm² falsche Zuordnung beseitigt, Körper nun ausschließlich Basis1/2; `nasal-pocket-material-regression.json` | generische Figuren brauchen eigene Herkunftsprüfung |
| Packen nach Anzeigefarbe | virtuelle Rezeptfarben verursachten unnötige Platten/Spulen | Materialgruppen: Mischteile zusammen, Schwarzteile separat; 2 Platten | abschließende Stütz-/Sliceansicht |
| Alte grüne/Glow-Profilvorlage | falsche tatsächliche Materialparameter trotz umgefärbter Anzeige | echte offizielle PLA-Profile über CLI geladen, inventarbezogene Namen/Farben, kein Farbtausch als Profilersatz | Generic-Profile physisch kalibrieren |
| Endgültiges Mixed-Projekt nicht CLI-slicebar | keine belastbare automatische Gesamtzeit | CLI231 explizit berichtet, GUI-Prüfung ausstehend | GUI-Slicing beider finaler Platten |

9 gezielte Service-/Vorschau-/Prozess-/Workerregressionen bestanden (`tests/test_mochi_pipeline.py`, 1,38 s), einschließlich des Hauptagenten-Tests zur Dispatch-Reihenfolge. Die tatsächlichen 9 Teile/7 Pins/10 Pfade sowie native Materialzuordnung wurden zusätzlich am 180-mm-Quellmodell ausgeführt; kleine Unit-Testkörper sind kein Ersatz dafür.

## Separate Schwarz-Diagnose und Sichtprüfung

Eine **separate Diagnosekopie** der schwarzen Platte deaktiviert nur die unbenutzten Mixed-Optionen, damit die CLI dieselbe Geometrie mit demselben schwarzen Profil slicen kann. CLI Exit0, 33 Schichten, 0,45 g, 9m27; nur Slot3/GFL99 `#272729` für Modell und Stützen. Nase: 1712 Support-Extrusionsbewegungen, davon745 vor der ersten Modellschicht; alle vier Augen ebenfalls mit Supportbewegungen vor ihrem Modellbeginn. `black-diagnostic-support-verification.json` enthält die Einzelwerte. Die Diagnosekopie beweist keine Mixed-GUI-Abnahme und wird nicht als fertiges Druckprojekt ausgegeben.

Bambu meldet mit den unveränderten offiziellen Generic-PLA-Werten `bed_temperature_too_high_than_filament` (Textured PEI55 °C, temperature_vitrification45 °C). Der Hinweis bleibt dokumentiert; ohne tatsächliche Materialkalibrierung wurde keine Temperatur erfunden oder Warnung versteckt.

Vier lokale Blender-Ansichten wurden gerendert und Vorder-/Rück-/Seitenansichten geprüft: `appearance-{front,right,back,left}.png`. Nase vollständig schwarz; beide ganzen Ohren, Gesicht, Brust- und Schwanzmuster sind erhalten. Die ursprünglichen Augenflächen sind im Vergleich zum Fell sichtbar facettiert. Es wurde keine unbelegte lokale Remesh-Verbesserung behauptet oder bestehende Gesichtsgeometrie automatisch ersetzt. Reale Farbtreue, Augen-Klebbarkeit, Nasen-Passung, Stützentfernung und finale GUI-Slices bleiben physisch bzw. im Slicer abzunehmen.

Z-Kontrollnachtrag: negative CLI-Statistikwerte der schwarzen Teile sind transformierte lokale Boundingbox-Ecken. Beispiel Nase: konservative Box-MinZ -1,186845625 mm entspricht exakt dem CLI-Bericht, während alle tatsächlichen Welt-Vertices bei Z ≥ -3,5e-9 mm liegen. Keine reale Geometrie liegt unter dem Bett; `bed-z-contact-verification.json` enthält beide unabhängigen Berechnungen.

`configure_mochi_plate(config, plate)` liefert die oben beschriebenen expliziten Prozesssettings für den normalen Export. Die Funktion bewahrt echte Profile, erzwingt getrennte Materialgruppen und markiert Prozessabweichungen für den GUI-Import. Die Interpretation negativer AABB-Ecken darf diese tatsächliche Auflageprüfung nicht ersetzen.

## Nachtrag regulärer UI-Lauf

Der Hauptagent hat den lokalen anatomischen Vorschlag im normalen Farbplan geprüft und gespeichert, die Konstruktion und den Export über die regulären Hauptaktionen ausgeführt. Dies ist eine Agentenprüfung im vom Nutzer beauftragten Gesamtdurchlauf, keine erfundene menschliche Material-/Druckabnahme. Run `runs/2f55cdd9d9f146c5854df116292c94d4/export`: neun Teilegeometrien stimmen exakt mit dem Benchmark überein; sämtliche 155.136 nativen Flächenfarben sowie reale Profile, 17 virtuelle Mischrezepte und Prozessparameter stimmen überein. Der Export enthält zwei native Platten; Core-Dateien sind lediglich Geometriebegleiter. GUI-Slicing der konkreten finalen Platten steht noch aus.

## Abgleich mit dem normalen Hauptprojekt-Workflow

Der normale UI-Konstruktionslauf `49021b4df99a4e5fa542c2e5c3eeea90` und Exportlauf `2f55cdd9d9f146c5854df116292c94d4` wurden unabhängig mit dem obigen Offline-Entwurf verglichen. Alle neun Vertex-/Facearrays sind exakt gleich. Die native `paint_color`-Folge stimmt für alle 155136 exportierten Dreiecke pro Teil exakt überein, ebenso echte Materialprofile, Rezeptverhältnisse und die relevanten Prozesssettings beider Platten. Der UI-Lauf verwendet seinen eigenen Plattenrand; unterschiedliche XY-Platzierungen sind daher beabsichtigt.

Die **tatsächliche normale Teilevorschau** wurde zusätzlich direkt gegen die nativen Slotfarben geprüft: alle 150000 ursprünglichen Außenflächen stimmen im RGB-Wert bis auf Float32-Rundung (<1e-6) überein. Neue graue Innenflächen sind ausdrücklich von diesem Farbvergleich ausgenommen. Beleg: `benchmarks/mochi-native-template-20261016/ui-parity/comparison.json`; reproduzierbar mit dem danebenliegenden `compare_ui.py`. Dieser Vergleich bestätigt Vorschau-/Export-Parität und ersetzt keine GUI-Slice- oder physische Abnahme.

Review der normalen Integration: Anatomie-Dispatch erfolgt vor der Farbgrenzen-Verfeinerung; immutable Konstruktions- und Farbreferenzen bleiben getrennt. Inventar-Snapshots binden beide Basisspulen. Gefundene Datei-Hash-Lücken in Segment/Export (Mesh-/Vorlagenbytes und gespeichertes Plandokument) wurden dem Hauptagenten gemeldet und dort mit fünf gezielten Regressionstests geschlossen. Ein kleiner Metadatenbefund bleibt separat gemeldet: bei nachträglicher Aufteilung einer Materialplatte muss `physical_spool_count` an die tatsächlichen `material_ids` angepasst werden.

Zusätzlicher lokaler Vergleich des alternativen vorhandenen PLA+ Brown28 mit Beige31: siehe `docs/MOCHI_FILAMENT_COMPARISON.md`. Warmerer Look und flächengewichtetes ΔE −6,56 %, aber schlechteres Körper-P95; aktueller Benutzerplan und bestehende native Dateien unverändert. Eine separate unkalibrierte Generic-PLA-Profilvorlage für diese Alternative wurde vorbereitet.

## Sicherheitsnachtrag: kompakte v1-Platte überholt

Der reale GUI-Slice der kompakten v1-Mixed-Platte meldete einen G-Code-Pfadkonflikt bei Schicht3310 zwischen Baumstützen von Schwanz und Körper. Getrennte Modellboundingboxen garantieren keine getrennten Stützen. Die frühere Zweiplatten-Anordnung ist deshalb keine Druckempfehlung. Der separate Detail-v2-Entwurf verwendet fünf Platten; alle fünf wurden mit aktiven Bambu-G-Code-Prüfungen erfolgreich gesliced. `docs/MOCHI_DETAIL_V2_RUN_REPORT.md` dokumentiert Quelle, Layout, tatsächliche Zeiten und physische Restprüfung. Die frühere CLI231-Beschränkung ist mit korrekter offizieller Syntax `--normative-check=0` für reine MakerWorld-Normative-Prüfungen gelöst; G-Code-Prüfungen bleiben an.

CLI-Negativkontrolle: Die alte in der GUI konfliktbehaftete v1-Platte wird von der CLI ebenfalls mit Exit0/leerem Warnfeld exportiert. Daher dürfen aktivierte CLI-G-Code-Prüfungen nicht als vollständige Pfadkonfliktfreigabe bezeichnet werden. Die fünf konservativ getrennten v2-Platten sind tatsächlich gesliced; weitere Extrusions-/Stützprüfung bleibt getrennt.
