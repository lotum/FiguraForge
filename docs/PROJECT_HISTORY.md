# FiguraForge

## Mochi · 50 cm mit organischem Halsschnitt · 18.10.2026

Geschwungene Trennung an der geometrischen Einschnürung, breite Kopfauflage, separater asymmetrischer 20×28×36-mm-Schlüssel. Acht geschlossene Teile auf drei nativen H2D-Platten; Richards ursprüngliche Bemalung einschließlich aller 1.034 komplex bemalten Dreiecke erhalten. 500 und 470 mm tatsächlich geslicet und mit vollständigen Extrusions-Footprints geprüft. Zweimaliges natives Speichern erhält alle acht Teile/Farbcodes. 514 Python-Tests und beide Frontend-Harness bestanden. Reale Hals-Passung noch offen; zusätzliche kleine Probe mit gleichen Materialien/Schichthöhen vorhanden. [Dateien, Montage, Größen und Grenzen](docs/MOCHI_NECK_SPLIT.md), [Nachweis](docs/mochi-neck-split-verification.json). Kein Druckstart, Originale erhalten.

## Mochi · gespeicherte Nutzerfassung und Großversion · 18.10.2026

Richards gedruckte 180-mm-Körperplatte und Farbkorrekturen unverändert gesichert; eigenes FiguraForge-Archivprojekt. Schwarzer Körper anstelle der Nase auf Platte 2: kollidierende Ressourcenkennungen im nativen Mehrdateiformat behoben, zwei tatsächliche native Speicher-/Ladedurchläufe erhalten alle sechs richtigen Teile. Neue 320-mm-Zweidüsen- und 325-mm-Rechtsdüsen-Dateien erfolgreich geslicet; alte Datei bleibt erhalten, ihre beschädigte zweite Platte nicht verwenden. [Dateien, Bauraum, Nachweise und Grenzen](docs/MOCHI_USER_EDITION.md).

## Mochi · reine Farben in einem Zwei-Platten-Projekt

Gleiche sechs fertigen Mochi-Teile, Körper nur Braun/Beige ohne Mixed, fünf schwarze Details auf Platte 2 **derselben nativen 3MF-Datei**. 510 Python-Tests bestanden. Beide Platten tatsächlich gesliced und 3.030.926 vollständige Extrusions-Footprints geprüft; bestehende Mixed-Dateien und Geometrien per SHA unverändert. Prognose gesamt ca. 13 h 30 min / 196,55 g. [Datei, Importanleitung und Grenzen](docs/MOCHI_SOLID_TWO_PLATES.md), [Nachweis](docs/mochi-solid-two-plates-verification.json). GUI-/physische Abnahme der neuen Variante offen; kein Druckstart.

## Neue Mochi-Einteilvariante · 16.10.2026

Ein Körper einschließlich Kopf/Ohren/Schwanz, nur schwarze Stecknase und vier Klebe-Augenteile separat. Ganzer Kopf lokal feiner; genau20 tatsächlich verwendete Farbwerte aus vorhandenen Spulen29/31. Beide nativen H2D-Platten gesliced und vollständig auf Druckpfade geprüft. Prognose **32 h56 min /329,73g**, Lightning5%, zweiWände. **507 Python-Tests und beide Frontend-Harness bestanden.** [Importdateien, Anleitung und Grenzen](docs/MOCHI_UNIFIED_PRINT.md). Alte Projekte bleiben erhalten; native GUI- und physische Abnahme offen.

## Charakterbilder -> organische Farbteile -> Druckpaket

**Version 0.1.0 / Engineering Preview / 16. Oktober 2026**

**Auf diesem Mac digital verifiziert, keine physische Gesamtabnahme.**
Aktueller Integrationslauf: **498 Python-Tests in 39,42 Sekunden** und beide Node-Frontend-Prüfprogramme bestanden.
[JUnit-Nachweis](docs/test-results-current-mac-final.xml). Alle 34 Buddy-Platten bestehen tatsächliches Slicing, vollständige unabhängige Druckpfadprüfung und den Abgleich mit dem endgültigen Mainexport `37f366df…`. Lokale
Arbeitskopien erhalten die Originale; Bild-/3D-Anbieter bleiben austauschbar.
Aktueller Stand der echten Characters:

| Figur | Tatsächlich geprüft | Noch offen |
|---|---|---|
| Mochi V2 | 9 geschlossene Teile, 7 Stifte, 4 Klebeaugenteile, 5 native Platten. Aktueller regulärer Export `fe198e…` stimmt in Weltgeometrie, Flächenfarben und vollständigen Projekteinstellungen mit dem gesliceten Prüfstand überein; [Datei-/Paritätsnachweis](docs/mochi-v2-current-native-parity.json). | Reale Mixed-Farbwirkung, Gesamtdruck, Kleben und neue Steckpassungen. |
| Pip | 10 geschlossene Teile, 16 Stifte, 10 isolierte Platten. Aktueller normaler Mainexport `6d0006…`: alle zehn Dateien tatsächlich gesliced und unabhängig auf Extrusions-Footprints geprüft. [Slice](docs/pip-main-native-slice-verification.json) / [Pfadnachweis](docs/pip-main-gcode-footprint-verification.json). | Reale Montage, Stützentfernung und Farben; Prognose 35 h 27 min / 505,01 g für den Gesamtdruck. |
| Buddy | Regulärer Main-Konstruktionslauf `8ae358…` erfolgreich: 37 geschlossene Teile / 34 Platten / 68 Passungsschlüssel an 32 Schnittstellen, 0,05 mm Spiel. Alle 34 ausgewählten finalen Referenzplatten haben Slice-PASS. Lederlichter vereinheitlicht, Emblem einfarbig Gold mit natürlicher Meshschattierung; bestehende Spulen-IDs erhalten. | 34/34 vollständige Druckpfadprüfungen und 34/34 tatsächliche Main-XML-/Paint-/Settings-Abgleiche bestanden. Prognose 1.042,93 h / 25,328 kg (ca. 43,46 Tage). Physische Großmontage, Statik und Farben offen; keine Druckfreigabe. |

Buddy verändert ausschließlich 1.058 Materialzuordnungen: 1.053 Lederlicht-Flächen Gold→Braun und fünf Emblemflächen Braun→Gold. Mesh und Anatomiemasken bleiben gleich. [Beleuchteter Emblemvergleich](benchmarks/buddy-material-islands-review/emblem-source-brown-gold-lit.png), [Leder-A/B und Prüfbericht](benchmarks/buddy-material-islands-review/REPORT.md). Keine zusätzliche Druckfarbe für natürliche Schattierung.

Die echte Mochi-Nasenprobe ergab 0,05 mm radial als brauchbaren Ausgangswert.
Für weitere tatsächliche Pip-/Buddy-Anschlussgrößen liegt eine neue optionale
[vierpaarige Passungsplatte](docs/PIP_BUDDY_FIT_PLATE.md) mit Beige-Profil und
lokalem G-Code vor. Der Agent hat keinen Druckauftrag gesendet.
[Testbericht und Prüfgrenzen](docs/TEST_REPORT.md).

Alle Farbvorhersagen bleiben unkalibriert. Pips vorhandenes Grün ist blasser als
die Referenz; Buddys gewähltes Wood-Filament wirkt matter. Diese sichtbaren
Bestandskompromisse sind keine gemessene Farbfreigabe. Die Großmontage ist
physisch offen; kein Druck wurde durch den Agenten gestartet.

Eine lokal laufende Webanwendung mit echtem Geometriekern. Sie erzeugt aus einem
texturierten GLB separate, geschlossene Farbeinsaetze mit passenden Taschen und
Steckstiften. Bild- und 3D-Generierung sind austauschbare externe Dienste.

**Sofort ohne API-Schluessel ausprobierbar:** Die originale texturierte
Testfigur `examples/teddy-source.glb` ist enthalten. Es gibt keine kostenpflichtigen
Demo-Aufrufe und keine externe JavaScript-CDN-Abhaengigkeit.

![Tatsaechliche Anwendung mit berechneten Einzelteilen](screenshots/exploded.png)

## Farbplanung und Bedienung (16. Oktober 2026)

Der Ablauf hat sechs Schritte: **Pose → Mesh → Farbplan → Konstruktion →
Filamente → Druckpaket**. Der Farbplan zeigt Grundkörper, separate Teile und
Mixed-Flächen vor dem Schneiden. Auf der Oberfläche markierte mehrfarbige
Regionen können eine gemeinsame Bauteilgruppe bilden, etwa ein ganzes Ohr.
Je Teil bleibt das gewählte Düsen-/Basisfilamentlimit verbindlich.

**Mit KI vorbereiten** nimmt in jedem Schritt ein eigenes Briefing entgegen.
Ein Vorschlag wird erst nach Prüfung übernommen; Generierung und Konstruktion
starten separat. Im Farbplan kann die KI bestehende Regionen umstellen; eine
Farbregion kann mehrere anatomische Stellen enthalten. Neue anatomische
Schnittgrenzen lassen sich manuell malen. Kein unbelegtes Versprechen einer
vollständigen semantischen 3D-Erkennung.

**Farbvarianten vergleichen** erstellt lokal neun bearbeitbare Vorschläge:
Grundfarben / ausgewogen / mehr Farbdetails, jeweils heller / original / dunkler.
Ähnliche Farbtöne lassen sich vereinheitlichen, schwarze Details bleiben geschützt.
Das ist eine Schatten-Hypothese, keine physikalische Entlichtung und keine
kalibrierte Druckfarbvorhersage. Angepasste Zielfarben brauchen danach passende
reale Filamente.

Native Mixed-Flächen zeigen bis zu 19 berechnete Rezeptfarben aus zwei echten Basisfilamenten. Separate Bauteile können ebenfalls Mixed verwenden. Prozentanteile und rechnerische Teilschichtdicken sind sichtbar; die unkalibrierte Vorschau und der Export verwenden dieselbe Zuordnung. Sie verwenden vorhandene H2D-Rezeptslots aus einer importierten
3MF-Vorlage. Der Export übernimmt keine erfundenen Temperaturen und fällt nicht
still auf einfarbige Core-Dateien zurück. Native Dateien bleiben experimentell,
bis die konkrete Platte und der Testdruck geprüft sind. Ein nativer 85/15-Würfel und eine 19-Farbstufen-Platte haben H2D-GUI-Slicing bestanden. Die grün/beige Testprofile sind ausdrücklich keine passende Mochi-Materialzuordnung. [Format und Grenzen](docs/MIXED_FILAMENT.md).
Die Oberfläche orientiert sich am öffentlichen Lotum-Auftritt; der
[UI-Audit](docs/UI_AUDIT.md) prüft 20 Prinzipien.

## Start

Python 3.12 oder 3.13 installieren. Zusaetzlich zum urspruenglichen Linux-Test
wurde Python 3.13.13 auf macOS/Apple Silicon frisch installiert und getestet.
`start.sh` sucht eine unterstuetzte Version statt Apples Python 3.9 zu verwenden.
Fuer die erste Installation wird Internetzugang benoetigt;
VTK ist ein groesseres binaeres Python-Paket. Node.js, NVIDIA-GPU und Blender
sind fuer Web-App, Geometrie und Demo nicht erforderlich. Fuer die automatische
Reduktion dichter GLBs wird Blender benoetigt; auf diesem Mac ist Blender 5.1.1
installiert. Optionaler Pfad: `FORGE_BLENDER_PATH`. Originale bleiben erhalten.

### macOS / Linux

Im entpackten Projektordner ein Terminal oeffnen:

```sh
bash start.sh
```

Dann **http://127.0.0.1:8000** im Browser oeffnen. Das Terminal offen lassen;
`Ctrl+C` beendet den Server. Alternativer Port: `bash start.sh --port 8001`.

### Windows / PowerShell

```powershell
.\start.ps1
```

Alternativ ohne Startskript:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -c requirements-tested.txt -e .
.venv\Scripts\python.exe scripts/run.py
```

### Docker

`.env.example` nach `.env` kopieren und ein langes zufaelliges
`FORGE_API_TOKEN` eintragen. Danach:

```sh
docker compose up --build
```

Im Browser dieses Token eingeben. Docker-Konfiguration ist enthalten, wurde
in der Bereitstellungsumgebung jedoch nicht gebaut. Der Port ist standardmaessig
nur an localhost gebunden. Genau **einen** API-Prozess betreiben.

## Der erste vollstaendige Durchlauf

1. **Testfigur laden**. Das GLB wird eingelesen, auf die Zielhoehe skaliert und
   geometrisch geprueft. Alternativ unter Mesh ein eigenes GLB importieren.
2. Unter **3D-Modell** Vorschau, Form, Faces und Warnungen pruefen.
3. Unter **Farbteile** mit `Oberflaechen-Einsaetze / Standard` beginnen.
   **Farbteile & Steckverbindungen bauen** berechnet Konturen, Einsaetze,
   Taschen, Stifte, Bauraumaufteilung und Druckplatten.
4. **Explodiert** und **Druckplatten** ansehen. **Passungs-Testteile
   herunterladen** erzeugt zehn Testkoerper mit fuenf radialen Toleranzen.
5. Unter **Filamente** echte Filamente hinzufuegen oder importieren. Die initialen
   DEMO-Eintraege sind keine kaufbaren Produkte. Filamente zuordnen,
   Vorschlaege pruefen, **Zuordnung speichern & Vorschau aktualisieren**.
6. Unter **Druckpaket** exportieren. Der jeweilige Hauptbutton verwendet die
   gezeigte Pose-, Mesh- bzw. Farbversion; keine vorgeschalteten Pruefcheckboxen.
   Die verwendete Version wird weiterhin mit Hash protokolliert. Jede `plate-XX.3mf` in Bambu Studio als
   Geometrie importieren; echtes Druckerprofil, Filament, Support und Brim
   kontrollieren. Es ist kein geslicter Druckauftrag.

Bei geaenderten Bildern, Abmessungen oder Konstruktionsvorgaben werden betroffene
Freigaben verworfen. Bereits freigegebene Dateien werden nicht heimlich
ueberschrieben. Aeltere Berechnungen bleiben im Projektverzeichnis erhalten.

## Was implementiert ist

| Bereich | Funktion |
|---|---|
| Weboberflaeche | Projekte, Uploads, 3D-Vorschau, Explosionsansicht, Teileauswahl, Plattenansicht, Protokoll und Freigaben |
| Bildgenerierung | OpenAI Images; Google Gemini Interactions und generateContent; frei editierbare Modellnamen |
| Konsistenz | Vorderansicht zuerst; weitere Kamerawinkel mit ihr als Referenz; optionaler KI-Review mit begrenzten Korrekturrunden |
| 3D-Generierung | Meshy Multi-Image, Tripo H3 sowie eigener lokaler Gateway-Vertrag |
| Geometrieimport | Selbstenthaltenes GLB mit Albedo/Vertexfarben, PLY, STL; Zielhoehe in mm; UV-Nahterhaltung |
| Farberkennung | CIELAB-Palette, Texturabtastung, zusammenhaengende Regionen, konforme Verfeinerung an Farbwechseln |
| Organische Einsaetze | Gekruemmte Aussenflaechen, gemeinsame Tasche fuer benachbarte Farben, Randspalt und versetzter Taschenboden |
| Ganze Farbkoerper | Zweite Expertenstrategie mit nichtplanaren gemeinsamen Grenzflaechen; auch umlaufende Farbbereiche |
| Verbinder | Runde oder verdrehsichere Stifte, passende Buchsen, radiales Spiel, Testkoerper |
| Grosse Modelle | Automatische weitere Strukturteilungen nur bei Bauraumueberschreitung; farbgetrennte Plattenplanung |
| Farbauswahl | Bestand/erlaubte Spulen, bevorzugte Marken, CIEDE2000, Spoolman/SpoolmanDB-JSON, Bildschirmvorschau |
| Ausgabe | Farbige Core-3MF-Baugruppe, 3MF je Platte und Teil, GLB, Montagehinweise, Geometriebericht, SHA256 |
| Betrieb | SQLite-Projekte, Datei-Artefakte, API-Key-Tresor, abbrechbare native Geometrie-Worker, Remote-Task-Wiederaufnahme und Budgetreservierung |

## Was nicht als fertig oder garantiert gilt

- **Kein universeller vollautonomer Figuren-Konstrukteur:** Die beiden
  Schnittstrategien haben geometrische Voraussetzungen. Gefaltete Projektionen,
  unbrauchbare Netze oder zu tiefe Taschen werden mit Fehlern gestoppt. Eine
  anatomisch-semantische KI-Segmentierung beliebiger Koerper ist nicht eingebaut.
- **OpenAI Images und Meshy wurden mit echten Ergebnissen geprueft.** Weitere
  Anbieter sowie Astra-Einstellungsvorschlaege sind mit simulierten Antworten
  getestet; ein echter Astra-Aufruf wurde nicht ungefragt bezahlt.
- **Kein natives komplettes Bambu-Multiplattenprojekt:** Exportiert werden
  standardkonforme Core-3MF-Dateien je Platte. Bambu-Profile, AMS-Zuordnung,
  Purge-Tower und Support werden nicht erfunden. Der geometrische Import/Export
  wurde mit Bambu Studio 2.7.1.62 auf diesem Mac getestet. H2D-Profil, Slicing,
  Material-/Duesenzuordnung und physischer Druck sind noch nicht abgenommen.
- **Keine physische Druckabnahme:** Wasserdichtheit und diskrete Montagewegtests
  sind keine Garantie fuer Passung, Haltbarkeit, Standfestigkeit oder jede
  Selbstueberschneidung. Kleine Farbflecken koennen fuer einen Steckstift zu klein sein.
- **Rigging, innere Tragwerke,
  selbstverriegelnde Schnapphaken und Live-Shop-Verfuegbarkeit sind nicht
  implementiert.** Schnittstellen/Erweiterungspunkte sind dokumentiert.
- Ein lokaler Hunyuan/TRELLIS-Inferenzserver und Modellgewichte sind **nicht**
  Bestandteil dieses Pakets. Der Geometriekern braucht diese nicht.

## Eigene Bilder und Cloud-Dienste

Unter **API & Einstellungen** die gewuenschten Schluessel hinterlegen oder in
`.env` setzen. Niemals Schluessel in Git, Screenshots oder Prompts aufnehmen.
Bilder werden nur nach expliziter Cloud-Zustimmung an den ausgewaehlten Anbieter
uebermittelt. Es findet kein stiller Wechsel zu einem anderen Anbieter statt.

Unter Pose Modell, Prompt und Identitaetsmerkmale eingeben. Vier Ansichten
werden separat erzeugt. Ein optionaler Review-Modellname aktiviert die visuelle
Kontrolle; dieser benoetigt zusaetzlich einen OpenAI-Key. Freigaben bleiben menschlich.
Der generative Teil darf die Referenzen interpretieren, er misst keine reale Geometrie.

Bereits vorhandene Ansichten lassen sich unter **Pose -> Vorhandene Ansichten
importieren** direkt als Kandidat uebernehmen. Vorne ist Pflicht; Links, Hinten
und Rechts sind optional. Je Datei nur eine Figur und Kameraansicht verwenden,
keine gesamten Turnaround-Boegen. Der Import erzeugt keine Bilder, kostet keine
Provider-Credits und ersetzt keine Posefreigabe. Transparente PNG-Hintergruende
werden weiss unterlegt; Originaldateien bleiben erhalten.

API-Key aus der macOS-Zwischenablage hinterlegen (laufender lokaler Server):

```sh
# Zuerst den jeweiligen Anbieter-Key kopieren, dann genau einen Befehl ausfuehren:
.venv/bin/python scripts/key_from_clipboard.py openai
.venv/bin/python scripts/key_from_clipboard.py gemini
.venv/bin/python scripts/key_from_clipboard.py meshy
.venv/bin/python scripts/key_from_clipboard.py tripo
```

Der Helfer schreibt ausschliesslich in den lokalen verschluesselten Tresor,
zeigt den Key nicht an und startet keine Generierung. Bereits konfigurierte
Keys ersetzt der Helfer nur mit ausdruecklichem `--replace`, beispielsweise
`.venv/bin/python scripts/key_from_clipboard.py openai --replace`.
Fuer importierte Originalansichten ist kein Bildgenerierungs-Key erforderlich;
eine neue Cloud-3D-Rekonstruktion braucht einen separat ausgewaehlten 3D-Anbieter.
Auf schmalen Fenstern steht die Projektauswahl oberhalb des Projekttitels.

Ein **optionales Ausgabenlimit** kann gesetzt werden; neue Projekte haben kein
erfundenes 100-EUR-Limit. Die Planwerte pro Aufruf sind Schaetzungen, keine
Anbieterrechnung oder harte providerseitige Kostengrenze. Bezahlte POST-Anfragen werden bei einem
unklaren Timeout nicht automatisch erneut abgeschickt.

## Detailgrad und KI-Unterstuetzung

Im Schritt **3D-Modell** begrenzt der Detailregler die gewuenschte Arbeitskopie.
Standard: etwa 150.000 Dreiecke mit Reserve fuer das 350.000-Dreiecke-Budget
an Farbgrenzen. Meshy bekommt dieses Ziel bereits bei der Generierung; es ist
anbieterbedingt kein exaktes Ausgabelimit. Dichtere GLBs werden lokal reduziert
und gegen das Original auf Form, Albedo und geschlossene Topologie geprueft.
**Arbeitskopie aktualisieren / skalieren** berechnet vorhandene Dateien lokal neu.

Die automatische Farbgrenzen-Praezision skaliert zur Druckhoehe und zeigt den
effektiven Millimeterwert. Feste Praezision wird nicht heimlich verschlechtert.
Die Montage-Vorpruefung ist von der Dreiecksplanung getrennt: ein geschlossenes,
kleines Netz kann weiterhin nicht montierbare Farbregionen enthalten.

**KI: Einstellungen vorschlagen** erstellt je Schritt einen pruefbaren Vorschlag
mit Begruendungen; Referenzen, aktuelle Vorschau und erlaubte Formularfelder
gehen an das konfigurierte OpenAI-Modell (Standard `gpt-6-astra`). Erst der
separate Uebernehmen-Button aendert Vorgaben. Dieser optionale Aufruf kostet;
er startet keine Bild-/3D-Erzeugung und erteilt keine Freigabe.

Meshy-Sichtbarkeit und Training sind nicht allein durch den API-Key belegt.
[Privatsphaere und Quellenstand](docs/PRIVACY_PROVIDERS.md).

## Tests und reproduzierbare Benchmarks

```sh
.venv/bin/python -m pip install -c requirements-tested.txt -e '.[dev]'
.venv/bin/python -m pytest
.venv/bin/python scripts/benchmark.py --height 180
.venv/bin/python scripts/benchmark_api.py --height 1000
.venv/bin/python scripts/calibration.py --shape round
```

Windows: `.venv\Scripts\python.exe` statt `.venv/bin/python`.
Die Befehle erzeugen echte Meshes und 3MF-Dateien. Es werden keine API-Credits
verbraucht. Der 1000-mm-Benchmark verwendet explizit eine groebere
Farbgrenzenabtastung von 2 mm, nicht die 0,65 mm der kleinen Figur.

Die ausgefuehrten Ergebnisse und Grenzen stehen in
[TEST_REPORT.md](docs/TEST_REPORT.md). Weitere Dokumentation:
[Bedienung](docs/WORKFLOW.md), [Architektur](docs/ARCHITECTURE.md),
[Provider](docs/PROVIDERS.md), [Geometrie](docs/GEOMETRY.md),
[Sicherheit](docs/SECURITY.md), [Recherche](docs/RESEARCH.md),
[Anforderungsstand](docs/REQUIREMENTS_STATUS.md).

## Daten, Sicherung und Updates

`data/` enthaelt Projekte, Quelldateien, Job-Artefakte, Spulen und den lokalen
Schluesseltresor. Fuer eine konsistente Sicherung den Server zuerst beenden und
**den gesamten Ordner** sichern, einschliesslich `vault.key`. Ein extern gesetzter
`FORGE_VAULT_KEY` muss separat gesichert werden. Ohne passenden Schluessel sind
gespeicherte API-Keys nicht wieder lesbar.

Die getesteten direkten Versionen stehen in `requirements-tested.txt`.
Zum erneuten Installieren bewusst
`.venv/bin/python -m pip install -c requirements-tested.txt -e .` ausfuehren.
Neuere Versionen ohne diese Constraints erst mit der Testsuite pruefen. Startskripte installieren nur
beim ersten erfolgreichen Start. Ein komplettes Vorher-Backup ist sinnvoll.

Eigener Anwendungscode: MIT. Demo-GLB: CC0. Abhaengigkeiten und untersuchte
Fremdprojekte behalten ihre eigenen Bedingungen; siehe
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Finaler Buddy-Nachweis: [native Main-Parität](docs/buddy-main-native-parity.json), [vollständige Slice-/GCode-Kette](docs/buddy-main-gcode-footprint-verification.json). Die Bambu-Desktopprüfung bleibt wegen gesperrtem Mac separat offen.
