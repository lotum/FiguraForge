# Pip – tatsächlicher Durchlauf

Stand: 16. Oktober 2026. Projekt `876726734385498d945775650737df38`, Zielhöhe 180 mm.
Der Bericht unterscheidet Originalreferenzen, generierte Vorschläge, menschliche
Freigabe, tatsächlich gestarteten Auftrag und noch offene Druckabnahme.

## Aktueller verifizierter Stand

- **Genau ein** autorisierter bezahlter Meshy-Auftrag, tatsächlich 30 Credits. Keine weiteren Cloud-Reparaturen oder Bildaufrufe.
- Hauptprojekt verwendet eine neue, lokale, an vier mechanischen Ebenen vorgeteilte Quellkopie: **161.060 Dreiecke**, Zielhöhe180mm, geschlossenes Volumen; Originaldateien und ältere Arbeitsstände erhalten. Inspectbudget bewusst170.000 statt erneuter Verkleinerung der vorbereiteten Schnittdreiecke.
- Produktionskernel `services/pip_pipeline.py`: **zehn geschlossene Teile, 16 Stifte, neun stichprobengeprüfte Montageschritte**, alle paarweisen Überschneidungsproben bestanden. Radialspiel0,05mm; noch kein physischer Pip-Passungsnachweis.
- Aktueller anatomischer Farbplan `c5169cc25f9a419c22dcd33535801fcdf732a5e9baf1c1444650baa40250a0ea` wurde normal über Proposal/PUT gespeichert. Er bereinigt Schnauzen-/Bodenhighlights und korrigiert danach genau zwei mikroskopische Seam-Eigentümer. Mesh und Einstellungen identisch. Segmentjob`ad96e0a07bd94f2c87383a56fc2ac770` ist erfolgreich abgeschlossen; native Materialprüfung gegen die echten Mainteile bestanden. Die früheren Baselines weiter unten sind historisch.
- **Finaler normaler Mainexport `6d0006dece3e44bda76bcd1e9ff9a810` erfolgreich; exakt dessen zehn Native-3MF erneut gesliced, zehnmal CLIexit0/Result0.** Alle zehn aktuellen GCodes bestehen die unabhängige Druckpfadprüfung einschließlich Bögen; native/GCode-SHA256 gegen die echten Dateien verifiziert. Prognose35h27min und505,01g. Root hat das frisch berechnete Modell ohne Licht gesichtet: unerwünschte Beigeflecken weg, Hauptcreme erhalten. Physischer Pip-Druck bleibt offen.

Die folgenden Eingabe-/Reparaturabschnitte dokumentieren den Weg und bewahren verworfene Versuche nachvollziehbar. Der jeweils jüngste Abschnitt hat Vorrang.

## Eingaben und visuelle Prüfung

Die lokale Suche beschränkte sich auf `data/`, `benchmarks/` und `examples/`
im FiguraForge-Projekt. 55 vorhandene GLB-/Meshdateien wurden über ihre Pfade und
Projektzugehörigkeit geprüft: Buddy, Mochi, Demo und Testexporte; kein vorhandenes
Pip-Mesh gefunden. Keine weiteren privaten Ordner durchsucht.

Alle drei Originalausschnitte und alle vier erzeugten Ansichten wurden einzeln
visuell gelesen. Der Gecko ist als Pip wiedererkennbar: grüne Haut, gelbcremefarbener
Bauch/Unterkiefer, große braune Iris und dunkle Pupille, helle Augenumrandung,
orangebraune Rücken-/Schwanzflecken, vier Gliedmaßen und ein Schwanz. Kleine
Zehen sind teilweise verdeckt; eine exakte Zehenzahl oder Druckstabilität lässt
sich aus den Bildern nicht zertifizieren.

| Eingabe | Feststellung → Verwendung |
|---|---|
| Original `front.png`, 425 × 887 | Vollständige sitzende Figur und Bodenauflagen sichtbar → primäre 3D-Eingabe |
| Original `right.png`, 495 × 887 | Seitliche Silhouette, geschwungener Schwanz und Rückenflecken sichtbar; Schnauze zeigt im Bild nach rechts → ergänzende Originalseitenansicht |
| Original `back.png`, 340 × 887 | Rücken, viergliedrige Haltung und Schwanzverlauf plausibel zur Front → ergänzende Rückansicht |
| Generierte Front | Identität ähnlich, Kopf/Augen und Zehenformen teilweise stärker stilisiert → als Vergleich erhalten |
| Generierte `left` **und** `right` | Beide zeigen die Schnauze nach rechts; eine Ansicht ist schräger, aber kein echtes Gegenprofil → nicht als verifiziertes Vieransichten-Set an Meshy weitergegeben |
| Generierte Rückansicht | Ähnliche Grundhaltung; kein Beleg, dass alle Hautflecken und Zehen über Ansichten identisch sind → kein ungeprüfter Austausch der Originale |

Das fehlende zweite Originalprofil wird weder gespiegelt noch künstlich als
beobachtete Geometrie ausgegeben. Alle Originale und alten generierten Dateien bleiben erhalten.

Originalpfade:

- [Front](../data/character-inputs/journey/pip/front.png)
- [Seitliches Profil](../data/character-inputs/journey/pip/right.png)
- [Rückansicht](../data/character-inputs/journey/pip/back.png)

[Lokaler visueller Vergleich](../benchmarks/pip-input-review/73f749491cc4440f880c1ba94c42ae1d/index.html)
zeigt Originale und generierte Ansichten nebeneinander.
[Manifest mit vollständigen Hashes](../benchmarks/pip-input-review/73f749491cc4440f880c1ba94c42ae1d/mesh-input-manifest.json).
Die vorbereiteten Kopien stimmen bytegenau mit den Originalausschnitten überein.

## Konkretes Briefing

Originale sitzende Gecko-Pose mit aufgestützten Vordergliedmaßen, angewinkelten
Hintergliedmaßen und geschwungenem Schwanz erhalten. Genau vier Gliedmaßen und
ein Schwanz, keine Accessoires. Originale Farbmerkmale bewahren; keine gespiegelten
Markierungen oder zusätzlichen Flecken erfinden. 180 mm ist die Zielhöhe der
lokalen Arbeitskopie. Augen, Finger/Zehen und Schwanzwurzel müssen am tatsächlichen
Mesh geprüft werden. Haut-/Lichtschattierungen sind keine zusätzlichen Druckfarben.

## Menschliche Freigabe und genau ein bezahlter Auftrag

Richard wurde der konkrete Auftrag mit drei Originalansichten, Meshy 7.1,
Textur, Ziel 150.000 Dreiecke und erwarteten 30 Credits vorgelegt.
Die ausdrückliche Antwort lautete: **„Ja, diesen einen Auftrag freigeben“**.
Diese Freigabe wurde vom koordinierenden Root-Agenten übermittelt. Die
Poseversionsfreigabe wurde deshalb als menschlich autorisierte Verwendung
genau dieses Satzes eingetragen, nicht als selbst erfundene Agentenfreigabe.

Vor Projektänderung wurde der komplette alte Projektstand gesichert. Danach:

1. Modell auf `meshy-7.1`, Ziel 150.000 Dreiecke und 180 mm gesetzt.
2. Drei Originalansichten als neuen manuellen Pose-Kandidaten importiert.
3. Menschlich autorisierte Poseversion gebunden und Projekt-Auditereignis gespeichert.
4. Genau einen Rekonstruktionsjob über die bestehende lokale App gestartet.

| Merkmal | Tatsächlicher Wert |
|---|---|
| Lokaler Job | `a1554d26a44f4bbd93db24e32dfc0d4f` |
| Meshy-Task | `01a144c6-087b-7253-9db5-7b0868fe87ed` |
| Freigegebener Posehash | `b721e9960062d405150274ce90ebc51844dd2d76af46b021a107084e2d3be5c4` |
| Eingabereihenfolge | Originalfront, Originalseitenansicht, Originalrückansicht |
| Modell / Ziel | Meshy 7.1, Dreiecke, 150.000 Zielpolygone |
| Textur | 2K-Standard, PBR über vorhandenen Adapter |
| Erwartete Kosten | 30 Credits; Eurobetrag mangels belegtem Accountpreis nicht erfunden |
| Wiederholungen | Keine zweite Task-Erstellung, kein zusätzlicher Remesh- oder Bildauftrag |
| Sichtbarkeit | Kein Publish-Aufruf und keine neue Veröffentlichung; keine unbelegte Garantie über interne Providerdatenverwendung |

Die aktuelle offizielle [API-Preistabelle](https://docs.meshy.ai/en/api/pricing)
nennt für Meshy 7.1 Multi-Image mit 2K-Textur 30 Credits.
Die [API-Dokumentation](https://docs.meshy.ai/en/api/multi-image-to-3d)
beschreibt die erste Ansicht als Hauptreferenz und das Polygonziel als ungefähr,
nicht als garantierte Obergrenze. Die lokale Begrenzung bleibt deshalb nötig.

[Autorisierungsnachweis](../benchmarks/pip-input-review/73f749491cc4440f880c1ba94c42ae1d/human-authorization.json),
[Projekt vorher](../benchmarks/pip-input-review/73f749491cc4440f880c1ba94c42ae1d/project-before-authorized-generation.json),
[Job und Checkpoint](../benchmarks/pip-input-review/73f749491cc4440f880c1ba94c42ae1d/job-latest.json).
Der Submit-Helfer schreibt vor dem möglichen kostenpflichtigen Start eine
exklusive Intent-Datei und verweigert eine erneute Ausführung. Bei verlorenem
HTTP-Ergebnis wird erst der gespeicherte Job geprüft, nie automatisch erneut bezahlt.

## Aktueller Verifikationsstand

Der einzige bezahlte Auftrag ist abgeschlossen. Das heruntergeladene Original
hat echte Topologiefehler und wurde unverändert erhalten. Eine konservativ
reparierte Kopie hat die unabhängige Geometrie-/Texturprüfung bestanden und ist
als neuer lokaler Import im Hauptprojekt angebunden. Die App prüft diese Kopie
mit Job `bbf0aefdb2a0432daa3499d0e1a6882f`; keine neue Cloudverarbeitung.
Noch keine menschliche Meshfreigabe, keine konstruierten Pip-Teile und kein
verifizierter druckbarer Pip-Export.

Rest bis zur Abnahme: App-Geometriebericht und Konstruktionseignung abschließen,
Material- und Bauteilplan bestimmen, sichere Montage und Passung konstruieren,
reale Filamente und Vorlagen zuordnen, native H2D-Ausgabe und Support-/Plattenvorschau
prüfen. Physischer Halt bleibt von Richards Kalibrierung und Druckfeedback
abhängig. Kein weiterer kostenpflichtiger Auftrag ist autorisiert.

## Tatsächlicher Download und konservative lokale Reparatur

Der einzige Meshy-Auftrag ist erfolgreich beendet und meldet **30 verbrauchte Credits**.
Die Originaldatei liegt unter
`data/projects/876726734385498d945775650737df38/runs/a1554d26a44f4bbd93db24e32dfc0d4f/generated.glb`,
SHA256 `4f4597c84023277689f4aca32681ae326b94101eb749e270ac3674222864851b`.
Es wurden 154.225 statt exakt 150.000 Dreiecke geliefert. Der Import prüft korrekt:
113 offene Kanten, 55 Non-Manifold-Kanten, 56 Komponenten, inkonsistente Orientierung.
Der Jobabschluss bedeutet daher abgeschlossenen Import/Geometriecheck, nicht
Konstruktionsbereitschaft oder Meshfreigabe.

Die Reparatur untersucht die reale Topologie: eine dominante zusammenhängende
Außenfläche und 55 kleine Artefaktkomponenten. Insgesamt werden 75 Artefaktdreiecke
entfernt (0,00765 % der Oberfläche), die Orientierung der großen Fläche korrigiert
und vier kleine Grenzschleifen geschlossen. Zwei dreieckige Lücken erhalten je ein
Dreieck; zwei viereckige Lücken erhalten einen lokalen Mittelpunktsfächer. Dabei
kommen zehn Dreiecke und zwei Eckpunkte hinzu. Die behaltenen Außenflächen und
UV-Ecken bleiben erhalten. Kein Voxelremeshing und keine neue Cloudverarbeitung.

Das Topologieergebnis hat 154.160 Dreiecke, einen geschlossenen konsistenten Körper,
0 offene und 0 Non-Manifold-Kanten. Ein erster lokaler Reexport wurde ausdrücklich
verworfen, weil JPEG erneut komprimiert wurde. Der zweite erzwingt verlustfreies
PNG; der unabhängige Textur-/Geometrievergleich ist bestanden. Noch keine
Meshfreigabe eingetragen.


## Unabhängige Prüfung und übernommener lokaler Mesh-Draft

Prüfkopie: `benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/pip-repaired.glb`,
SHA256 `09fdd4a6ba1ee37269b7297528c3ac88f0243274446bc0f22e45bc54adeeafde`.
Der alte Versuch unter `d6118081c2fd4bf6b94c9850214e2628` wurde **nicht** übernommen.

| Merkmal | Unabhängig gemessen |
|---|---|
| Dreiecke / Komponenten | 154.160 / 1 |
| Geschlossen / Orientierung | Ja / konsistent |
| Offene / Non-Manifold-Kanten | 0 / 0 |
| Abmessungen X/Y/Z | 102,8621 × 205,9634 × 180 mm, unverändert |
| Volumenänderung | −1,5356 mm³ bei ursprünglich 555.796,4619 mm³ |
| Oberflächenabstand, 10.000 Stichproben je Richtung | p99 0,0000043 mm; größter beobachteter Abstand 0,0000073 mm |
| Albedo-Farbabstand ΔE2000 | p95 0,0000292; p99 0,0000748 |
| Texturbild | Dekodierte RGB-Pixel aller 2048 × 2048 Pixel exakt identisch |

Die Stichproben sind kein vollständiger Hausdorff- oder Selbstüberschneidungsbeweis.
[Messdaten](../benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/independent-quality.json)
und [Reparaturprovenienz](../benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/repair-report.json).

Die [vier tatsächlich angesehenen Ansichten](../benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/four-views.png)
zeigen plausible Front, Seite, Rücken und schräge Front: großer Kopf mit zwei
Augen, vier Gliedmaßen und ein geschwungener Schwanz; keine sichtbaren lokalen
Reparaturartefakte. Die Vorderzehen sind klein und bodennah. Die feinen Zehen
und die Schwanzspitze brauchen eine mechanische Mindeststärken-/Supportprüfung;
geschlossene Topologie allein belegt deren Haltbarkeit nicht.

Der explizite Import bewahrt alle alten Dateien und umgeht das im Befundlog
dokumentierte Zurückspringen auf `original_source`. Aktuelle Projektquelle:
`imports/1c657bdbfc0840c8b3b2a6fa08c7a151.glb` mit demselben reparierten Hash.
Vor Import ist ein weiterer Projektsnapshot im Reparaturordner gespeichert.

## App-Prüfung der reparierten Quelle

Der lokale Inspect-Job `bbf0aefdb2a0432daa3499d0e1a6882f` ist abgeschlossen.
Aktueller Meshhash:
`ecdea421686c733ab24206c32d2b12d1fc00eb6cd2682a0fef53a96827951b8f`.
Die App bestätigt dieselbe gültige Topologie. Die voraussichtliche
Farbgrenzenverfeinerung bleibt mit **284.794 Dreiecken unter 350.000**;
ermittelt in 11,01 Sekunden auf diesem Mac.

Die separate Montagevorprüfung fällt trotzdem durch: **231 Farbtaschen,
36 ohne zulässige Steckrichtung**. Das Feld `construction_readiness.ready=true`
bestätigt hier lediglich die Flächenbudget-Vorbereitung; `assembly.passed=false`
verhindert die Aussage, dass der automatische Vorschlag montierbar sei.

Ein lokaler Entwurf sieht Hautflecken als zweifarbig bedruckte Oberfläche
(Grün/Braun) vor. Bauch und Augenteile müssen eigene Geometrieentscheidungen
bekommen. Die erste unveränderte Cremefarbmaske enthält 39 verzweigte
Randknoten; ein direkter Ganzteilversuch wird korrekt mit „Boundary has a branching
vertex“ abgewiesen. Der Farblabelvorschlag ist damit noch kein druckbarer Bauteilplan.
Farbmasken, Normalkegel und Teilbarkeit werden als lokale Experimente im
Reparaturordner gespeichert; keine Änderungen an Originalgeometrie und keine
unbelegten Freigaben.

## Historischer lokaler Augen-Prototyp (0,10mm-Spiel, noch ohne Gesamtmontage)

Unter `benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/eye-assembly-e9506e3f866042d59490b147dbd3d7e9`
liegen fünf gültige Volumen: vorläufiger Kern, zwei Iris-/Augenrahmen und zwei
Pupillen mit hellen Reflexen. Vier Steckteile und sechs Stifte: je Auge zwei
Ø2,4 × 2,5-mm-Stifte und je Pupille ein Ø1,8 × 1,5-mm-Stift, jeweils 0,10 mm
radiales Spiel. Die gesonderten Stichproben-Auszüge über 15 bzw. 8 mm sind bestanden.
Diese kleinen Pinmaße brauchen eigene physische Kalibrierung.

Die linke Augengrenze folgt einem geometrischen Min-Cut auf einer geglätteten
**Analyse**kopie; die Originalaußenfläche bleibt unverändert. Beim rechten Auge
war die erste Kontur nicht projizierbar. Ein um vier Flächennachbarschaften
verkleinerter Bereich und 13 kleine ergänzte Quellflächen ergeben eine einzige
geschlossene, gültige Augengeometrie mit bestandenem Auszug. Die konkrete
Konturverschiebung ist im Report offengelegt und muss bei der Farbzuordnung
beachtet werden.

[Montage und Explosion, tatsächlich visuell geprüft](../benchmarks/pip-repair/c173bc465e93435ba71a79c161bd9fba/eye-assembly-e9506e3f866042d59490b147dbd3d7e9/eye-assembly-review.png)
zeigt erhaltene Iris, Pupille und Reflexe. Graue Flächen in der Explosion sind
neue verdeckte Schnitt-/Steckflächen. Die Montageansicht zeigt die ursprüngliche
Albedo; noch keine errechnete Filamentrezeptfarbe.

**Weiter offen:** Cremefarbene Unterkiefer-, Hals-/Bauch- und Schwanzunterseiten
müssen in geometrisch sinnvolle Teilbereiche zerlegt werden. Gleiches Creme
bedeutet ausdrücklich nicht ein einziges umlaufendes Teil. Ein Front-Inlaytest
mit 18 kleinen Maskenkorrekturen behebt Randverzweigungen, wird aber wegen einer
sich selbst überschneidenden projizierten Kontur abgewiesen. Die Vorfilterung
kleiner Farbinseln muss vor einer expliziten Maskenprüfung erfolgen; andernfalls
kann der Konstruktor einen schon geprüften Normalkegel durch nachträgliches
Auffüllen kleiner Inseln wieder verändern. Eine lokale Glättungsprobe löst das
Problem nicht und wurde nicht übernommen. Keine kaputte Teilgeometrie exportiert,
keine native Druckfertigkeit und keine Freigabe behauptet.


## Aktuelle Anatomie und echte Spulen

Die vorbereitete Quellkopie liegt unter
`benchmarks/pip-partitioned-source/e02a3fe60255492fb2f367b10003111c/pip-partitioned-source.glb`.
SHA256 `b5486af116bf337a3ea905ce2be19a0495020094833b637a67ed20309eb6ea1c`;
aktueller Hauptprojekt-Meshhash `6b50653c44351800405a94665290e745a712664a400e933106409fe44c6ce644`.
Normal importiert als `imports/ff731dcbab1e42cca79a911bd6dea9a9.glb`,
Inspectjob `a0c20b42dbdf4d19b983218ff3be29b3` erfolgreich. Der lokale Vorbereitungsbericht belegt
p99Oberflächenabstand0,00000055mm / Maximum0,00000564mm und identische dekodierte Texturpixel;
keine Voxel-Remesh-Übernahme. Während der Konstruktion werden Ebenenknoten numerisch um
höchstens0,0000205mm eingerastet; dies ist im Kernelbericht offengelegt, kein verschwiegenes Remesh.

| Teil / Baugruppe | Technik / reale Spulen | Montage |
|---|---|---|
| Rumpffront | Solid Apple Green52 und Beige31 | ZweiØ3×3mm-Rumpfstifte, zusätzlich zweiØ3×3mm-Halsstifte |
| Hinterer Rumpf mit Gliedmaßen und Schwanz | Solid Apple Green52; nur braune Flecken mit Green52/EarthBrown29 Mixed | Zuerst Rumpffront einstecken |
| Unterkiefer als geometrisches Ganzteil | Solid Green52/Beige31 | ZweiØ3×3mm-Stifte; zuerst am oberen Kopf montieren |
| Oberer Kopf | Solid Green52; braune Flecken Green52/EarthBrown29 Mixed | Gesamte vormontierte Kopfgruppe senkrecht auf Halsstifte |
| Boden und Schwanzunterseite | Je ein Beige31-Inlay | Je zweiØ2,4×2,5mm-Stifte; räumlich getrennte Taschen |
| Zwei Iris-/Augenrahmen | Solid EarthBrown29/Beige31 | Je zweiØ2,4×2,5mm-Stifte |
| Zwei Pupillen mit Reflex | Solid Black30/Beige31 | Je einØ1,8×1,5mm-Stift; zuletzt einsetzen |

Beide ganzen Augen werden jetzt **ohne Konturerosion** getrennt. Nur innere Kappenanker liegen0,15mm
tiefer; die äußeren Originalrandpunkte bleiben erhalten. Rechts ergänzt eine lokale Fläche0,00623mm²
die Kontur und beseitigt genau eine Projektionskreuzung. Der auf dem Kopf verbleibende helle Augenrand
sinkt von rund185 auf3,63mm². Links bleibt beim gesonderten Pupillenteil eine Erosionsrunde erforderlich;
rechts keine. Der gesamte aktuelle Kernellauf ist
`production-qa-63a2051cd59b476ebc9934fc0ff91a9c`: zehn Volumen, 16Stifte, alle kombinierten Proben bestanden.
Das ist kein kontinuierlicher Kollisionsbeweis und keine allgemeine Anatomieerkennung.

[Quelle gegen tatsächliche Spulenfarben, Front/Rücken/Unterseite](../benchmarks/pip-partitioned-source/e02a3fe60255492fb2f367b10003111c/production-qa-63a2051cd59b476ebc9934fc0ff91a9c/source-versus-print-colors.png)
und [Montage/Explosion](../benchmarks/pip-partitioned-source/e02a3fe60255492fb2f367b10003111c/production-qa-63a2051cd59b476ebc9934fc0ff91a9c/exact-assembly-explosion.png)
wurden tatsächlich visuell gelesen. Rücken-/Schwanzflecken bleiben sichtbar, Grundgrün ist über die
Montagegrenzen vereinheitlicht. Die Einzelteilgrenzen folgen mechanisch brauchbaren Baugruppen;
nicht jeder Quellfarbpatch wird als winziges Steckteil interpretiert.

**Bewusster Bestandskompromiss:** Apple Green52/53/54 `#C2E189` ist deutlich heller und weniger gesättigt
als das Quellgrün `#92AB2A`. Root hat den erlaubten eigenen PLA-Bestand nachgerechnet: Apple Green
ist mit ΔE2000≈15,58 der nächste Kandidat; Wood33 folgt erst mit≈19,96. Das bedeutet nicht farbgleich.
Auch Beige31 `#F7E6DE` ist heller/weißer als das Quell-Creme. Inventar-HEX wurden nicht physisch gemessen;
Mixed-Vorschau ist ein unkalibriertes optisches Modell. Rund1438,5mm² cremefarbene Rest-Unterseiten
am hinteren Rumpf werden bewusst grün vereinfacht, damit kein drittes Filament oder unmontierbare
Kleinstteile entstehen. Am oberen Kopf verbleiben78,4mm² Creme und3,63mm² heller Augenrand;
keine Behauptung vollständig identischer Farbgrenzen. Die Unterseitenansicht macht den Kompromiss sichtbar.

## Native Profile und tatsächliche Prüfgrenzen

`scripts/build_pip_native_template.py` lädt aufgelöste offizielle lokale H2D-Maschinen-/Prozessprofile
und21 Filamentprofile in einen frischen STL-Würfel. Die Bambu-CLI erzeugt selbst alle dimensionalen
Temperatur-/Spülmatrizen; keine handerfundene Vektorverlängerung. Vier physische Spulen plus17 virtuelle
Green/Brown-Rezepte, 19 nutzbare Stufen einschließlich reiner Basisfarben. Native Slotprüfung und
Zweispulen-Gate bleiben aktiviert. ELEGOO/eSUN verwenden bewusst benannte GenericPLA-Profile,
keine erfundene herstellerspezifische physische Kalibrierung.

Die ersten zehn Slices mit Vorlage`f727...` scheiterten korrekt mit „No valid nozzle found“.
Frische offizielle Profile enthalten keine aktive Düsen-Hardwareinventarisierung: die nativen Felder
`extruder_nozzle_stats`/`extruder_ams_count` waren leer. Die funktionierende H2D-Vorlage liefert die
unverändert übernommenen zwei Hardwareeinträge. Eine weitere Einzelprobe scheiterte mit unbedruckbarem
GCode, weil der offizielle Prozessdefault den Reinigungsturm beiX15 außerhalb der gemeinsamen H2D-Fläche
abX25 platzierte. Pip setzt den Turm beiX235/Y250 auf isolierten Teilplatten; die nachfolgende
Einzelprobe`slice-80df2a531bdd4fe59be8a84198c53835` besteht tatsächlich mitCLIexit0.
Alle Geometrieprüfungen bleiben aktiviert; nur die experimentelle MakerWorld-Publikations-Normprüfung ist aus.

Die korrigierte Vorlage`profiles-09e40af472844adfad28d3f87c041a9b/pip-real-materials-profile-only.3mf`
ist normal im Projekt hinterlegt, SHA256`8c64bf3ba64f713d2e1b381b43e07e11898e226c293d46d7176a9bfc4783879d`.
Gesamtserie und unabhängige Druckpfadprüfung sind nachfolgend belegt; die Mainexport-Parität und Root-GUI-Prüfung bleiben getrennte Nachweise. CLI-Erfolg allein kann bekannte Pfadkonflikte übersehen und bedeutet keine Druckfreigabe.

Der normale Hauptprojekt-Segmentjob`f68ad33...` erzeugte gültige Teile, scheiterte danach an automatischer
Farbplattenzuordnung: `colors_per_plate` stand noch auf1, obwohl der Farbplan2 reale Spulen benötigt.
Root korrigiert das regulär über Einstellungen und Vorabprüfung; keine Artefakte werden von Hand als
freigegeben oder erfolgreich umgeschrieben.

## Abnahmegrenzen

Die zehn korrigierten Nativplatten bestehen Slice- und unabhängige Footprintprüfung. Im normalen Hauptprojekt bleiben UI-/Exportparität und reale Pip-Passung, kleine Stifte und Farbwirkung getrennt nachzuweisen. Es wurde kein Druck gestartet.


### Zehn reale korrigierte Slices

`benchmarks/pip-native-slicer/corrected/slice-12a565d4fcf5474f9d4cc8a3cc23c3de/verification.json`
belegt zehn vollständig abgeschlossene Slices, jeweilsCLIexit0 und Result0. Korrigierter Export:
`production-qa-63a2051cd59b476ebc9934fc0ff91a9c/native-qa-aa52b4fe76f640639d034f7e1267b576/export`.
Alle zehn Platten verwenden die tatsächlichen vier Bestandsprofile, je Teil höchstens zwei physische Spulen;
keine Filamentwechsel im AMS laut Slicerstatistik, die Farbpaare werden auf dem H2D verarbeitet.
Die native Zweispulen-Grenze ist vor dem Export unabhängig geprüft.

Slicer-Schätzung über alle zehn getrennten Drucke: rund35,75Stunden und508,4g einschließlich Stützen,
Raft und Reinigungsturm; rund300,0g sind als Hauptverbrauch ausgewiesen. Das ist eine Slicerprognose,
keine gemessene Druckzeit oder Materialrechnung. Die konservativen isolierten Platten und Stützen sind
bewusst noch keine auf minimalen Abfall optimierte Produktionsserie.

Der unabhängige Checker weist `Arc extrusion unsupported` zurück, statt einen falschen PASS auszugeben:
die offiziellen Prozessprofile erzeugenG2/G3. Der zuständige Agent hat begrenzte G17-I/J-Bogenprüfung ergänzt und20 gezielte Tests ausgeführt. Alle zehn tatsächlichen Pip-GCodes bestehen den Recheck. Prozess-Arc-Fitting wurde nicht zur Umgehung dieser Prüfung deaktiviert.

Die normale Hauptprojektintegration verwendet noch einen erneuten Konstruktionlauf nach dem regulären
Settingsfix. Für eine identische Übertragung dieser Plattenprüfung muss sie dieselben Packparameter
8mmRand, 8mmAbstand und300×320×320mm verwenden; Root ist darauf hingewiesen. Keine stillschweigende
Gleichsetzung anders platzierter Mainplatten mit dem verifizierten Benchmark.


### Buchsenteil korrekt bezeichnet

`head-upper` hat jetzt die ausdrückliche Rolle`socket-body`: der obere Kopf trägt selbst keine Stifte,
sondern empfängt zwei Kieferstifte sowie je zwei Irisstifte. Die Halsbuchsen liegen im geometrisch
abgetrennten Kiefer; deshalb wird die gesamte Kopfgruppe erst nach Kiefer/Oberkopf-Montage auf den
Rumpf gesetzt. Kein fehlender Halt wird pauschal weggefiltert. Ein gezielter Receiver-Test sichert die
Rolle, unveränderte Geometrie und den beschreibenden Hinweis. Root ergänzt das Frontend-Label und
berechnet den normalen Mainstand für korrekte Metadaten erneut; die digitale Geometrie bleibt identisch.
Die konkrete Fügestellenliste und deutsche Reihenfolge stehen nun auch im Konstruktionsreport und Manifest.


### Unabhängige Druckpfadprüfung abgeschlossen

[Verifizierter Footprintbericht](pip-gcode-footprint-verification.json): zehn tatsächliche GCodes,
5.671.524 Extrusionssegmente einschließlich843.410 Druckbögen und4.029.786 konservativ approximierender
Sehnen. Maximale geometrische Fehlergrenze unter0,005mm; zusätzliche Endpunkt-Radiusrundung bis0,002064mm
ist in der Footprintaufweitung berücksichtigt. Alle zehn Owner-/Reinigungsturm-Bounds sind auf den
isolierten Platten getrennt, keine gescreenten Konflikte. Die zehn Report-SHA256 wurden zusätzlich
gegen die echten GCode-Dateien geprüft. Das ist keine Zertifizierung kompletter Düsenräume, Dynamik,
Haftung, eigener Supportkontakte oder physischer Farben/Passungen.

Eine zusätzliche strikte Prüfung ohne Flächenschwelle belegt **null** Quellflächen mit positiver
Außenfläche auf mehreren Teilen. Nach numerischer Schnittkantenbehandlung bleiben neun winzige
Quellflächen von insgesamt0,0001007mm² ohne direktes Außenmatch; begrenztes Füllen über Quellnachbarschaft
ist im Report offengelegt. Obergrenzen im produktiven Kernel:20Faces und0,001mm², keine flächige Umdeutung.
Beleg:`production-qa-63a2051cd59b476ebc9934fc0ff91a9c/strict-source-ownership-proof.json`.

## Nächste Schritte

Root berechnet den normalen Mainstand mit der expliziten Buchsenteil-Rolle erneut und vergleicht dessen
native Geometrie, Platzierungen, reale Profile und Prozesswerte mit diesen zehn geprüften Platten.
GUI-Prüfung und physische kleine Passungs-/Farbprobe folgen getrennt. Keine weiteren Cloudaufträge,
keine Druckauslösung und keine von diesem Agenten erfundenen menschlichen Freigaben.

## Nachprüfung: helle Schnauzen- und Bodenflecken

Root sah im normalen Mainmodell drei kleine helle Flecken oberhalb der Kieferfuge;
sie blieben bei ausgeschalteter Beleuchtung sichtbar. Die Prüfung aller zehn Teile
gegen die geschlossene Quelle ergab keinen Stiftdurchbruch (Kiefer maximale
Abweichung außen0,00000555mm). Die helle Farbe war tatsächlich Beige31 und stammte
von fehlklassifizierten goldgelben Texturhighlights: die zwei größten Schnauzeninseln
sind original#D4B547 und#CEAF40, keine weißen Charaktermarkierungen.

Die Materialbereinigung bleibt modellgebunden auf Kiefer und Rumpffront begrenzt:

| Bereich | Creme erhalten | Isolierte Inseln nach Grundgrün | Gemittelte Quellfarbe der Inseln |
|---|---:|---:|---|
| Kiefer |2526,18mm²|25 /37,4043mm²|#D0B345|
| Rumpffront |4618,23mm²|127 /70,8617mm²|#C4BC4C|

Augen-/Pupillenreflexe werden nicht bereinigt. Keine Änderung an Quellhaut,
Bauteilgeometrie, Steckern, Platzierungen oder UVs. Zwei Regressionfälle sichern
Geometrie-/Eingabenerhalt und den Schutz der Augenreflexe; alle17 Pip-Tests bestehen.
Der Vergleich wurde tatsächlich visuell gelesen:
`benchmarks/pip-optical-diagnosis/corrected-b6641b6a2b624c8e894ba2afb244c36b/source-before-after-cleanup.png`.
Die Flecken verschwinden; der gewollte helle Bauch und das Kinn bleiben erhalten.
Bestands-Apple-Green/Beige bleiben sichtbar heller als die Quell-Albedo und unkalibriert.
Der vorherige Zehnplatten-Slice-/GCode-Nachweis gilt ausdrücklich für den vorherigen
Farbplan; der frische normale Mainlauf und Export folgen separat.

Der bereinigte Plan ist über die normalen Proposal-/PUT-Routen als
`7ae34b76b6fc3ca395450f5cc6600eabe58e4da5e4e8b85250e870ff9c397fdf`
gespeichert. Snapshot, Proposal und unveränderte Einstellungen liegen unter
`benchmarks/pip-optical-diagnosis/main-cleanup-eb67a6b92e6b489391a5c9244c07b355/`.
Der reguläre Segmentjob`2eb50a06f07d43c7bbbd751772a4105a` ist erfolgreich abgeschlossen.
Exakter Vergleich gegen den zuvor geprüften Mainjob`69f2bee7106e45b59595e8a9c1fb9637`:
alle zehn Vertex-/Dreiecksarrays, Stecker, Rollen und Platten identisch. Ausschließlich
1084 Quell-Farbzuordnungen ändern sich:462 Front-Beige→Grün,622 Kiefer-Beige→Grün.
Nachweis:`geometry-parity.json` und`plan-difference-proof.json` im Snapshotordner.

## Nachprüfung: erster normaler Mainexport blockiert zu Recht

Der erste neue Mainexportjob`0baecf6dfb8e4f4f9769e6c1115a1a0d` scheiterte am
unveränderten Zweispulen-Gate: hinterer Rumpf vermeintlich drei reale Filamente.
Die Untersuchung verwendete dessen echte `worker-request.json`, Quellimport,
gespeicherte Mainteile und hochgeladene Vorlage, nicht lediglich den älteren Benchmark.
Genau Rear-Dreieck48095 erbte über Quellfläche154691 falsches Front-Beige auf
0,0000553825mm². Die direkte Außenflächenzuordnung belegte dagegen ausschließlich
Rear als authentischen Eigentümer dieser Quelle.

Ursache war die anschließende mikroskopische Seam-Lückenergänzung: Eine vorgefilterte
matched/unmatched Kante konnte durch bereits verarbeitete Nachbarkanten veralten.
Der bisherige Zweig überschreibt dann einen ursprünglich belegten Eigentümer.
Die Korrektur befüllt ausschließlich noch fehlende Enden; sie verändert weder
Geometrie noch Toleranzen noch das physische Zweispulenlimit. Zwei konkrete
Ketten-/Kantenreihenfolge-Regressionen reproduzieren den Fehler; alle19 Pip-Tests bestehen.

Der korrigierte Plan wurde bereits vor einem weiteren Mainexport gegen exakt jene
Mainteile und native Vorlage durch `prepare_native_materials` geprüft:
Front/Kiefer Slot1+3, Boden/Schwanz3, Iris2+3, Pupille3+4, Rücken/Kopf1+2.
Alle zehn Teile bestehen das Zweispulen-Gate. Nachweis:
`benchmarks/pip-optical-diagnosis/corrected-8f495b23b45e4bffbcfb5b31eee58a03/main-native-material-preflight.json`.
Dieser Material-Preflight ist noch kein Slice-/GCode-Nachweis; frische normale
Plan-/Konstruktions-/Export- und Zehnplatten-Slice-Prüfungen folgen getrennt.

Der Provenienzfix wurde anschließend regulär übernommen: finaler Plan
`c5169cc25f9a419c22dcd33535801fcdf732a5e9baf1c1444650baa40250a0ea`,
Segmentjob`ad96e0a07bd94f2c87383a56fc2ac770` erfolgreich. Die Korrektur betrifft
zusätzlich genau Quellfläche154691 (Front-Beige→Rear-Grün) und154653 (Rear→Front),
keine weitere großflächige Farbänderung. Alle zehn finalen Mainteile sind in
Vertices, Dreiecken, Steckern und Platten exakt identisch zur früheren Maingeometrie.
Das native Materialgate wurde nochmals mit diesen frisch gespeicherten Mainteilen,
dem finalen Plan und der tatsächlich hochgeladenen Vorlage bestanden: maximal zwei
reale Spulen pro Teil. Nachweise im neuen Snapshotordner
`benchmarks/pip-optical-diagnosis/main-cleanup-3e0e4703c8e64bbe8ab1d449e4214712/`:
`final-main-geometry-parity.json` und`final-main-native-material-preflight.json`.

## Finaler normaler Mainexport und aktuelle zehn Slices

Root hat den frischen Mainstand in der normalen Weboberfläche ohne Licht visuell
geprüft: die unerwünschten Beigeflecken verschwinden, Bauch/Kinncreme bleiben erhalten,
zehn Teile und zehn Platten sichtbar. Anschließend normaler UI-Export:
`6d0006dece3e44bda76bcd1e9ff9a810`, erfolgreich. Aktuelle Nativdateien:
`data/projects/876726734385498d945775650737df38/runs/6d0006dece3e44bda76bcd1e9ff9a810/export/plate-01-native.3mf`
bis`plate-10-native.3mf`.

**Genau diese zehn Dateien** wurden frisch mit der offiziellen lokalen Bambu-CLI
gesliced. Zehnmal Prozess-Exit0 und Resultcode0, zehn aktuelle GCodes vorhanden.
Geometrie-/GCode-Validität aktiv; lediglich die experimentelle Mixed-Filament-
MakerWorld-Veröffentlichungsprüfung ist wie zuvor mit`--normative-check=0` deaktiviert.
Keine Kommunikation mit einem Drucker.

Der unabhängige Footprintchecker prüfte danach alle zehn aktuellen GCodes:
5.668.791 Extrusionssegmente, darunter843.778 Druckbögen mit4.031.497 konservativen
Sehnen. Alle zehn bestanden, keine unsupported Bögen, alle Objekt-/Tower-XY-Bounds
je Platte disjunkt. Maximaler Bogenfehlerbound0,004999996mm einschließlich
Radiusrundung; Footprints entsprechend aufgeweitet. Aktuelle native SHA256 und
GCode-SHA256 wurden nochmals direkt gegen Dateien und die Checkerwerte verifiziert.
Dies bleibt ein begrenzter planarer Extrusions-/Eigentümercheck, kein vollständiger
physischer Düsen-, Dynamik-, Haftungs- oder Festigkeitsnachweis.

| Aktuelle Slicerprognose | Wert |
|---|---:|
| Alle zehn Platten |35,4508h (ca.35h27min)|
| Gesamtes Filament |505,011g|
| Hauptmodell |299,875g|
| Zusätzliche Stützen/Raft/Purge/Tower |205,136g|

Natives XML wurde zusätzlich gegen den vorher geprüften Benchmark gelesen:
alle zehn Welt-Vertex-/Dreiecksgeometrien **exakt identisch**, sämtliche vollständigen
Projektsettings identisch. Das native Farbpainting ändert sich nur auf Front462 und
Kiefer636 Dreiecken (einschließlich interner Ersatzfarbzuordnung); die übrigen acht
Platten bleiben im Painting identisch. Der aktuelle Slice-/GCode-Nachweis ersetzt
keine historisch gespeicherten Dateien.

Aktuelle kompakte Projektbelege:

- `docs/pip-main-native-slice-verification.json`
- `docs/pip-main-gcode-footprint-verification.json`
- `benchmarks/pip-main-native-slicer/slice-a6d2ffe20f484edc87c428230c6180dc/native-geometry-and-paint-difference.json`

## Nächste Schritte – aktueller Stand

Root führt die verbleibende native Bambu-GUI-Prüfung am aktuellen Mainexport zusammen.
Anschließend zuerst eine kleine physische Pip-Passungs-/Farbprobe statt ungeprüft alle
505g zu drucken. Dieser Agent hat keinen Druck gestartet, keine weitere kostenpflichtige
API aufgerufen und keine menschliche Freigabe erfunden.

## Abschließende Sichtprüfung des aktuellen Mainexports

Der aktuelle Mainstand wurde zusätzlich in FiguraForge von vorn, seitlich, von hinten und explodiert betrachtet. Unbeleuchtete Ansicht zeigt tatsächliche Druckfarben: die isolierten falschen Beigeflecken sind entfernt; Rückenflecken bleiben erhalten. Vollständige Augen- und Kieferbauteile sowie geschlossene Schnittflächen sind sichtbar. Screenshots: `screenshots/pip-main-final-colors.png`, `pip-main-final-side.png`, `pip-main-final-rear.png`, `pip-main-final-exploded.png`. Das verfügbare Apple-Green ist sichtbar heller als das Referenzgrün; dies ist keine kalibrierte Farbgleichheit oder physische Montageabnahme.
