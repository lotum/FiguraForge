# UI-Audit und Lotum-Ausrichtung

Stand: 16. Oktober 2026. Geltungsbereich: bestehende lokale FiguraForge-Web-App.
Der Audit umfasst alle in `frontend/index.html` und `frontend/app.js` gefundenen
Elementgruppen, einschließlich Dialogen, Fehlern, leeren Ansichten und langen Listen.
Die Matrizen sind eine Codeprüfung mit konkreten Korrekturen, keine behauptete
vollständige Barrierefreiheitszertifizierung. Browsernachweise dokumentiert der Testbericht.

## Beobachtetes Lotum-Design

Öffentliche Quelle: [Lotum](https://lotum.com/de), tatsächlich abgerufene
[Produktions-CSS](https://lotum.com/_nuxt/style.Csz1ykGo.css).
Die Homepage liefert eine Nuxt-App; der reine Textabruf enthält daher wenig Layout.
Die Produktions-CSS wurde unabhängig davon erfolgreich direkt abgerufen.

| Beobachtung im Original | Übertragung auf FiguraForge |
|---|---|
| Lime `#cfff00`, häufige Flächen und Buttons | Primäre Aktion und Markenakzent; schwarzer Text |
| Blau `#00b2ff` | Auswahlflächen und visuelle Orientierung; dunkleres Blau für kleine Schrift/Fokus |
| Weiß und Schwarz, kühle Grautöne `#4a5464`, `#728197` | Helle Werkbank, dunkle Projektleiste, deutlich lesbare Hinweise |
| Museo Sans Cyrl 300 für Fließtext, 900 für Überschriften/Buttons; 500/700 für Zwischenstufen | System-Sans ohne Download; kräftige Überschriften und Buttons. Keine Behauptung, die Originalschrift werde verwendet |
| Große Headlines, klare Akzente und großzügige Abstände | Größere Schrittüberschrift, größere Controls, klarer Aktionsrang; bestehende Dreispaltenaufteilung bleibt |

Keine privaten Lotum-Design-Dateien und keine vollständige interne Designsystem-Spezifikation
wurden gelesen. Die öffentlich ausgelieferte Schrift wird wegen ungeklärter Weitergaberechte
nicht in das Projekt kopiert. Das Ergebnis ist eine am öffentlichen Lotum-Auftritt
orientierte Oberfläche, keine vorgetäuschte vollständige Designsystem-Implementierung.

## Zwanzig überprüfbare Prinzipien

Die Prinzipien sind eine auf dieses Produkt zugeschnittene Audit-Systematik,
keine angebliche universelle Rangliste. Die Regeln überschneiden sich bewusst:
Lesbarkeit, Hierarchie und Zugänglichkeit müssen dieselben Elemente aus verschiedenen
Perspektiven prüfen.

| Nr. und Prinzip | Konkretes Prüfkriterium | Befund → Korrektur / verbleibende Prüfung |
|---|---|---|
| 1 · Arbeitsziel zuerst | Aktueller Schritt und nächste fachliche Aktion sofort erkennbar | Testfigur konkurrierte mit Produktionsaufgabe → Testfigur zur Nebenaktion; Hauptaktion im jeweiligen Schritt |
| 2 · Sachlogik vor Technik | Farbe planen, danach Geometrie/Passung bauen | Farbanalyse und Steckverbinder waren vermischt → eigener Farbplanungsschritt; keine automatische Gleichsetzung von Farbregion und Einzelteil |
| 3 · Eine klare Hauptaktion | Pro Schritt eine hervorgehobene fachliche Aktion | Viele gleich gewichtete Outline-Buttons → Lime ausschließlich für primäre Aktion, Import/Speichern/KI als sekundäre Handlungen |
| 4 · Lesbare Grundschrift | Controls 14–15 px, Hinweise in der Regel 13 px | Bestehende Labels/Inputs 10/11 px → Labels 14 px, Inputs 15 px, Hauptbuttons 14 px; keine nur per Vergrößerung lesbare Werkbank |
| 5 · Ausreichender Kontrast | Normaltext mindestens 4,5:1; Status nicht nur farbig | Blasse Olivtöne → Slate auf Weiß und klar bezeichnete Zustände; gemessene Tokenkontraste dokumentiert |
| 6 · Großzügige Klickziele | Hauptcontrols mindestens 42 px hoch; kleine Iconziele mindestens 30–38 px | Viele 20–30-px-Controls → gemeinsame Mindesthöhen und größere Bild-Entfernen-Schaltfläche |
| 7 · Zusammengehöriges gruppieren | Eingabe, Ausgabe und Aktion räumlich zusammen | Lange Formulare ohne klare Handlungsebene → Gruppen, Trennlinien und ausgewählte Region im Planeditor |
| 8 · Details nach Bedarf | Modellkennung, technische Limits und Diagnose nicht vor Alltagsaktion | Technische Felder belegten den ganzen Inspector → erweiterte Bereiche; sichtbare kurze Zusammenfassung statt vollständiger Erklärtexte |
| 9 · Zustand sichtbar machen | Wartend, läuft, fertig, Fehler unterscheiden | Produktionsprotokoll war klein und abgeschnitten → 13-px-Status, mehrzeiliger Text, größerer Verlauf und sichtbare Fortschrittsleiste |
| 10 · Aktion und Wirkung benennen | Nutzer erkennt Eingabe, Ausgabe und Folgewirkung | „Reconstruct“/generisches Speichern unklar → deutsche Vorgangsnamen; kurze Eingabe→Ausgabe-Zeile |
| 11 · Nutzer behält Kontrolle | Kein bezahlter Auftrag oder Geometriebau durch reine Navigation | Freigabecheckboxen irritierten → ausdrückliche Hauptaktion, Hinweise unter Aktion; KI-Vorschläge zuerst prüfen und dann übernehmen |
| 12 · Vorhersehbare Fehler | Fehler direkt am Arbeitsbereich und mit nächster Handlung | Protokoll allein verbarg aktuelle Fehler → persistente Inline-Meldung; Farbe plus Text, kein stummes Scheitern |
| 13 · Unterscheiden statt nur färben | Einfarbig, Mixed Filament, separates Teil textlich benennen | Farbflächen allein sagen nichts über Fertigung → Strategieauswahl und Legende im Farbplan |
| 14 · Direkte Manipulation | Region wählen/bearbeiten und Wirkung im großen Modell sehen | Große Vorschau wurde kaum zur Arbeit genutzt → Planeditor und Pinselwerkzeuge verwenden dieselbe Hauptfläche |
| 15 · Konsistenz | Dieselbe Farbe, Beschriftung und Interaktion bedeutet überall dasselbe | Grün konnte Branding, Erfolg und Aktion zugleich meinen → Lime Aktion, Blau Auswahl, benannter Status für Erfolg/Fehler |
| 16 · Wiedererkennen vor Erinnern | Aktuelle Wahl, Maße und ausgewählte Region bleiben sichtbar | Kleine unbenannte Werte und Rollen-Codes → verständliche Teile-/Strategienamen; Messwerte tabellarisch und mit Einheiten |
| 17 · Responsive ohne Schrumpfen | Lesbare Schrift auch am Laptop; kleine Fenster stapeln Inhalte | Mediaqueries verkleinerten Navigation/Controls erneut → breiter Editor, Sidebar bis 1450 px bei Bedarf ausblenden, bis 1100 px stapeln |
| 18 · Tastatur und Fokus | Sichtbarer Fokus, echte Buttons, zugängliche Labels | Fehlende universelle Fokusanzeige → 3-px-Fokus; interaktive Teilezeilen benötigen echte Buttons/Key-Handler; Canvas-Ersatzbedienung separat prüfen |
| 19 · Ruhige Rückmeldung | Fortschritt sichtbar, Bewegung reduzierbar, Ton optional | Dauerbewegung ohne Reduced-Motion-Regel → reduzierte Animation; KI-Fertigmeldung sichtbar, Signalton nur als ergänzende abschaltbare Rückmeldung |
| 20 · Ehrliche Qualität und Rückweg | Geprüftes von Vorschlag unterscheiden, Originale erhalten | „Geschlossen“ darf keine Druckfreigabe bedeuten → Geometriecheck, Plan, Konstruktion und Slicerprüfung trennen; Arbeitskopie erhält Originalquelle |

## Vollständige Elementgruppen-Prüfung

Die Zeilen decken jede bestehende Elementgruppe genau einmal ab. Einzelne Prinzipien
werden mehrfach angewendet. „CSS umgesetzt“ bedeutet ausschließlich die visuelle
Korrektur; Änderungen an Verhalten und Texten stehen ausdrücklich separat.

| Elementgruppe / Selektor | Relevante Prinzipien | Problem → konkrete Maßnahme | Prüfstatus |
|---|---|---|---|
| Marke/Topbar `.brand`, `.topbar`, `.topcenter`, `.version` | 1 Arbeitsziel, 4 Schrift, 5 Kontrast, 15 Konsistenz | Zu kleine technische Kennzeichnungen → lesbarer, neutraler Header; unnötige Metadaten dürfen entfallen | CSS umgesetzt; Textprüfung in Gesamtintegration |
| Globale Aktionen `.topactions` | 3 Hauptaktion, 6 Klickziel, 15 Konsistenz | Kleine gleichförmige Schaltflächen → 42-px-Targets; Material/API bleiben globale Nebenaktionen | CSS umgesetzt |
| Projekte `.sidebar`, `.projectitem`, `.compact-projects` | 7 Gruppierung, 16 Erkennen, 17 Responsive | Projektname/Datum klein → 14/12 px, klarer Auswahlrand, kompakte Projektauswahl bei schmalen Fenstern | CSS umgesetzt |
| Druckerziel `.sideblock`, `.minirow` | 2 Sachlogik, 4 Schrift, 16 Erkennen | Statische Düsenangabe darf aktiver Konfiguration nicht widersprechen → sichtbare dynamische Zusammenfassung nötig | CSS umgesetzt; dynamische Werte in Integration prüfen |
| Lokale Engine/API-Link `.sidebottom` | 8 Details, 10 Benennung | Technische Angaben konkurrieren mit Aufgabe → leise Nebeninformation, Link zugänglich | CSS umgesetzt |
| Projektkopf/Testfigur `.projectheader`, `#demo-load` | 1 Arbeitsziel, 3 Hauptaktion | Demo stand prominent neben jedem echten Projekt → Nebenaktion bzw. Menü beim Projektanlegen | CSS abgestuft; Platzierung durch Integration |
| Schrittleiste `.pipeline` | 2 Sachlogik, 9 Zustand, 17 Responsive | Zu kleine Schritte, gemischte Farb-/Konstruktionslogik → sechs klar benannte Schritte, Auswahl mit Unterstrich | CSS umgesetzt; neue Schritte durch Integration |
| Canvas/Ansichtmodi `.canvas-panel`, `.segmented`, `.viewer-tools` | 6 Klickziel, 14 Manipulation, 18 Tastatur | Mikroschalter und wenig nutzbare Fläche → größere Viewer-Controls, Modellfläche bleibt zentral | CSS umgesetzt; Tastaturalternativen offen |
| Leeransicht/Posebilder `#viewer-empty`, `.current-pose-preview` | 1 Arbeitsziel, 10 Wirkung, 17 Responsive | Demo dominierte und Ursprung unklar → klare Eingabe/Ausgabe, Bilder groß im Hauptbereich | CSS umgesetzt; Texte durch Integration |
| Viewerstatus/Abstandsregler `.viewer-bottom` | 4 Schrift, 9 Zustand, 16 Erkennen | Hinweise kaum lesbar → mindestens 11–13 px, Controls mit Labels | CSS umgesetzt |
| Kennzahlen `.metrics` | 5 Kontrast, 16 Erkennen, 20 Ehrliche Qualität | Kleine Labels, „geschlossen“ verwechselbar mit druckbereit → lesbare Zahlen; genaue technische Bedeutung beibehalten | CSS umgesetzt; Benennung prüfen |
| Produktionsprotokoll/Abbruch `#events`, `#job-status`, `#progress-bar` | 9 Zustand, 10 Benennung, 12 Fehler | Englische/abgeschnittene Jobs → deutsche Vorgänge, mehrzeiliger Status, größere Schrift, Fehler separat | CSS umgesetzt; Laufzeitnachweis durch Integration |
| Inspector/Schrittkopf `.inspector`, `.inspector-title` | 4 Schrift, 7 Gruppierung, 17 Responsive | Enger 318-px-Bereich erzeugte lange Scrollstrecke → 390 px, 360 px auf Laptop, 410 px breit | CSS umgesetzt; reale Viewports prüfen |
| Standardfelder `.field`, `label`, `.twocol`, `.formgrid` | 4 Schrift, 6 Klickziel, 7 Gruppierung | Technisches Formular zu dicht → 43-px-Felder, 14/15-px-Text, sinnvolle Zweispaltengruppen | CSS umgesetzt; Reihenfolge durch Integration |
| Import/Referenzen `.filebutton`, `.reference-grid`, `.pose-grid` | 6 Klickziel, 10 Wirkung, 11 Kontrolle | Kleine Entfernen-Aktion, Eingabe/Ausgabe unscharf → größere Targets; eindeutige Original-/Ergebnisbeschreibung | CSS umgesetzt; Rückgängig-/Entfernen-Fluss prüfen |
| Geometrie/Detailregler `#mesh-face-value`, `.report-grid` | 9 Zustand, 16 Erkennen, 20 Qualität | Starre Zahl ohne Einordnung → lesbarer Wert, größenbezogene Bewertung; Vereinfachung keine Detailgarantie | CSS umgesetzt; fachliche Bewertung vorhanden |
| Farbplanung `.plan-editor`, `.brush-toolbar`, `.region-list`, `.strategy-options` | 2 Sachlogik, 13 Strategie, 14 Manipulation | Eine Farberkennung konnte nicht zwischen Verlauf und Bauteil entscheiden → wählbare Regionen und separate Fertigungsstrategie | CSS vorbereitet; Verhalten durch Integration |
| Konstruktionsvorgaben/Kalibrierung | 2 Sachlogik, 8 Details, 20 Qualität | Palette, Verbinder, Drucker und Präzision gleichzeitig → Alltagswerte zuerst, Details aufklappen, Kalibrierung Nebenaktion | CSS umgesetzt; Reihenfolge durch Integration |
| Bauteilzeilen `.partrow`, `.partdesc`, `.partid` | 6 Klickziel, 16 Erkennen, 18 Tastatur | Klickbare Divs/kleine Codes → größere Zeilen, verständliche Namen; semantische Buttons notwendig | CSS umgesetzt; Semantik durch Integration |
| Filamentzuordnung `.colorrow`, `.swatch` | 5 Kontrast, 13 Strategie, 16 Erkennen | Minischrift und Farbe ohne Bedeutung → 14-px-Namen, Bestandskennzeichnung und Auswahl lesbar | CSS umgesetzt |
| Export/Downloads `.downloads` | 3 Hauptaktion, 10 Wirkung, 20 Qualität | Viele ähnliche Dateien → ZIP priorisieren, Einzeldateien sekundär; Slicingstatus ausdrücklich benennen | CSS umgesetzt; Priorisierung durch Integration |
| Hinweise/Fehler `.notice`, `.action-note`, `.tiny` | 5 Kontrast, 8 Details, 12 Fehler | Lange grüne Kleinschrift → kompakte 13-px-Hinweise; Warnung/Fehler sprachlich unterschieden | CSS umgesetzt; Textkürzung durch Integration |
| KI-Hilfe `.suggestion`, `.suggested-change`, `#suggest-settings` | 9 Zustand, 11 Kontrolle, 19 Rückmeldung | Formularblock ganz unten, technische Schlüssel statt Begriffe → zugängliche Nebenaktion, Vorschlag vor Übernahme, klare Fertigmeldung | CSS umgesetzt; Platzierung/Bezeichnungen durch Integration |
| Erweiterte Bereiche/Diagnose `details`, `summary`, `pre`, `code` | 8 Details, 18 Tastatur | Kleines Summary und zu viele Fachwerte offen → größere Summary-Targets, Details bewusst sekundär | CSS umgesetzt |
| Projekt-/Login-Dialoge `dialog`, `.dialog-actions` | 6 Klickziel, 7 Gruppierung, 18 Tastatur | Kleine Dialogfelder → gut lesbare Modal-Controls; Fokus und Escape prüfen | CSS umgesetzt; Dialoglaufzeitprüfung offen |
| API-Schlüssel `.keyrow` | 4 Schrift, 11 Kontrolle, 20 Qualität | Veraltete Testaussage und enge Eingabe → lesbare Felder; keine Schlüsselanzeige im Klartext | CSS umgesetzt; Text durch Integration prüfen |
| Filamentbibliothek `.inventory-toolbar`, `.inventory-item` | 6 Klickziel, 16 Erkennen, 17 Responsive | Enge vier Spalten → großzügigere Ziele, responsive Zweispalten; Vorrat/Erlaubt sind tatsächliche Daten, keine Prozessfreigaben | CSS umgesetzt |
| Toast/Fallback `#toast`, `#webgl-error` | 9 Zustand, 12 Fehler, 19 Rückmeldung | Kurzlebige Meldung reicht bei Fehler nicht → persistenter Inline-Fehler zusätzlich zum Toast; sichtbarer Fallback | CSS umgesetzt; ARIA/Timing durch Integration prüfen |

## Technische Sichtprüfung der Gestaltung

Berechnete WCAG-Kontraste der tatsächlich eingeführten Tokens:

| Kombination | Kontrast |
|---|---:|
| `#16191f` auf Lotum-Lime `#cfff00` | 15,05:1 |
| Hinweis `#536072` auf Weiß | 6,39:1 |
| Hinweis `#536072` auf Werkbank `#f4f6f8` | 5,90:1 |
| Status `#374e67` auf `#eef4fb` | 7,75:1 |
| Link `#006b9d` auf Weiß | 5,85:1 |

Diese Tokenprüfung ersetzt keinen Screenshot- oder vollständigen Kontrastaudit
aller überlagerten Canvas-Texte. Decorative Marken-/Eyebrowtexte können 10–12 px
betragen; funktionale Formularwerte sind 15 px. Schrift wird bei kleineren
Viewports nicht wieder auf 8–10 px abgesenkt. Das bestehende Canvas-Raster
und die Figurenfarben sind keine UI-Kontrastbelege.

## Quellen und Skill-Recherche

- Vorhandenen Skill `find-skills` für die Recherche gelesen. Keine Installation vorgenommen.
- [Vercel Web Design Guidelines](https://skills.sh/vercel-labs/agent-skills/web-design-guidelines):
  offizielles Vercel-Paket, zum Abrufzeitpunkt 743,5 Tsd. Installationen,
  Quellrepository 32,5 Tsd. Sterne. Für eine spätere Installation geeignet;
  für diesen Audit wurden die [öffentlichen Regeln](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md)
  direkt gelesen. Diese Regeln wurden auf das deutsche Fachprodukt übertragen;
  keine englische Title-Case-Vorgabe in deutsche Texte übernommen.
- [WCAG 2.2 – Textkontrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html):
  Kontrastgrenze für normalen Text.
- [WCAG 2.2 – Zielgrößen](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html):
  Mindestzielgrößen und Abstände. Die größeren 42–44-px-Controls sind unsere bewusste Komfortentscheidung.
- [WCAG 2.2 – Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html):
  Umbruch bei schmalen Ansichten.
- [Nielsen Norman Group – Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/):
  Ausgangspunkt für Zustandsklarheit, fachliche Sprache, Kontrolle und Fehlerbehandlung.

## Noch nicht als abgeschlossen behauptet

1. Vollständige Bedienung von 3D-Auswahl/Brush ohne Maus: semantische Regionliste
   und Tastaturaktion prüfen; ohne Alternative keine vollständige Barrierefreiheit zusagen.
2. Farbblindheitsprüfung der neuen Strategielegende: Text/Icons zusätzlich zu Farben;
   ausgewählte reale Pläne im Browser kontrollieren.
3. Interaktions- und Scrollprüfung auf Richards tatsächlicher Fenstergröße:
   bestehende Screenshots beweisen die neue Oberfläche erst nach Reload und Aufnahme.
4. Umlaute, übersetzte technische Schlüssel und reale verständliche Fehlermeldungen:
   in der Integration aller sechs Schritte prüfen, keine vollständige Lokalisierung behaupten.

## Nachtrag: konkrete KI-Aufträge und Variantenvergleich

Die KI-Hilfe hat jetzt in jedem der sechs Schritte ein Textfeld „Dein Auftrag
für diesen Schritt“ und ein passendes Beispiel. Der Entwurf wird im lokalen
Browser getrennt nach Projekt-ID und Schritt gespeichert. Beim bewussten
KI-Aufruf wird der Text als `advice_prompt` an den lokalen Server gesendet;
der Server hält den Text im Jobrequest fest. Ein Projekt auf einem anderen
Browser übernimmt den lokalen Entwurf nicht automatisch.

Die KI-Vorschau zeigt verständliche Feldnamen, bisherigen Wert, editierbaren
Vorschlag und Begründung. Regionale Planvorschläge enthalten wählbare Druckweise,
Filament und bei Einzelteilen Schnittart/Bauteilgruppe. Auch die zwei
Basisfilamente sind vor dem ausdrücklichen Übernehmen editierbar. Das Übernehmen
löst keine Bild-, Mesh- oder Teilegenerierung aus. Noch nicht gespeicherte
manuelle Planänderungen werden als vollständiger Referenzentwurf an den lokalen
Server übergeben. Vor dem KI-Aufruf wird keine Planfreigabe oder Speicherung als
gültiger Produktionsplan erzwungen; auch eine noch unvollständige Mixed-Auswahl
kann beraten werden. Der Server sichert diesen Referenzentwurf getrennt und
übernimmt den Kandidaten erst nach der ausdrücklichen Übernahmeaktion.

Die Werkzeuge „Wählen“, „Malen“ und „Zurück“ stehen horizontal. Die kompakte
Regionliste bleibt in einem begrenzten Bereich; die aktuell gewählte Region
hat größere lesbare Felder. Schnittart und Bauteilgruppe erscheinen nur bei
„Getrenntes Bauteil“; Mixed Filament zeigt keine bedeutungslose Vollfarbenwahl.
Der frühere falsche Shift-Hinweis ist korrigiert: Ziehen dreht, Shift + Ziehen
verschiebt; zum Drehen aus dem Malmodus zuerst „Wählen“ nutzen. Ohne WebGL ist
Malen deaktiviert, die Regionliste bleibt bedienbar.

„Farbvarianten vergleichen · 3 × 3“ öffnet einen großen Dialog mit neun lokalen
Vorschauen. Jede Vorschau nutzt denselben Kamerazustand des aktuellen Modells;
das bestehende Modell wird für die Aufnahme nur vorübergehend eingefärbt und
danach wiederhergestellt. Alle neun Bilder werden aus dem tatsächlichen lokalen
Canvas aufgenommen. Eine Variantenwahl ersetzt nur den bearbeitbaren Entwurf,
behält Rückgängig bei und benötigt weiterhin „Plan speichern“. Es werden keine
neuen Bilder über Cloudanbieter erzeugt. Helligkeit und Zusammenfassen ähnlicher
Farben sind als Heuristik bezeichnet; keine physikalische Entfernung von
Beleuchtung oder kalibrierte Vorhersage von Filamentfarben wird zugesagt.

Codeprüfung: `node --check` für `app.js` und `color-plan.js` bestanden. Ein
isolierter Node-Harness prüfte die getrennte Speicherung der Promptentwürfe
und Zahl-/Boolean-/Array-Konvertierung editierter Vorschläge. Visuelle Abnahme
und tatsächliche Backend-Übernahme werden im aktuellen Testbericht gesondert
dokumentiert; diese Codeprüfung allein behauptet keine Browserabnahme.

### Ergänzende Zustandsprüfung

Die KI-Hilfe steht im Farbplanungsschritt vor dem manuellen Editor, damit eine
Vorbereitung ohne manuelles Ausfüllen erreichbar bleibt. Der Drei-Zeilen-Prompt
ist nicht hinter einem weiteren Aufklapper verborgen.

Eine vollständige Rückgängig-Stufe enthält jetzt den gesamten Plan einschließlich
Basisfilamenten, Düsenanzahl und Variantenhinweis. Bei erneutem Inspectoraufbau
bleiben Änderungen und der Dirty-Zustand des lokalen Entwurfs erhalten. Verspätete
Ladeantworten eines bereits geschlossenen Editors werden verworfen. Asynchrone
Vorschauladevorgänge prüfen Projekt, Schritt und Aufrufticket vor Änderungen am
Viewer und Status, damit ein schneller Schrittwechsel keine alte Vorschau zurücksetzt.
Ein isolierter Node-Harness prüfte komplettes Varianten-Undo, erhaltene Entwürfe
beim Neuaufbau und den Abbruch verspäteten Renderns nach `destroy()`.

## Nachtrag: verständliche Druckweisen und breite Arbeitsfläche

Die Druckweisen-Legende steht dauerhaft direkt auf der großen Vorschau, solange
„Druckweisen“ aktiv ist. Grau bezeichnet den Grundkörper, Blau ein separates
Bauteil und Gelbgrün Mixed Filament. Die Legende benennt den schichtweisen Wechsel
zweier Basisfilamente und stellt klar, dass dabei kein Kunststoff physisch gemischt
wird. Bei „Zielfarben“ wird die Strategiefarben-Legende ausgeblendet. Viewer und
Legende verwenden dieselben zentralen Frontend-Farbtokens in `plan-guidance.js`.

Für Ansicht, Druckweise, Schnittart, Bauteilgruppe, Basispaar und Varianten gibt es
kurze aufrufbare Erklärungen. Native `details`/`summary` stellen Maus- und
Tastaturbedienung bereit; die Informationsschalter haben eindeutige zugängliche
Namen. Die Erläuterungen bleiben geschlossen, bis sie gebraucht werden. Es wurden
keine Freigabecheckboxen hinzugefügt.

Die rechte Arbeitsfläche skaliert nun proportional zur Fensterbreite, mindestens
480 px und auf großen Bildschirmen bis 1.000 px. Dadurch bleibt der Planeditor auf
Ultrawide-Fenstern keine schmale Seitenspalte neben großer ungenutzter Fläche.
Ab ausreichend breitem Inspector stehen Regionliste und ausgewähltes Formular
nebeneinander. Bei kleinen Fenstern werden Vorschau und Arbeitsfläche gestapelt.
Die Hauptvorschau ist auf großen Fenstern höher, damit die Figur eine brauchbare
Porträtfläche erhält. Die Aufteilung Projekte / Vorschau / Bearbeitung bleibt erhalten.

Für den Variantenvergleich wird die Kamera einmal auf die oberen etwa 65 % der
Figur gerichtet. Alle neun Bilder nutzen exakt denselben Ausschnitt; der Fokus
wird geometrisch aus den oberen Modellpunkten ermittelt. Das ist keine anatomische
Erkennung. Füße und ein niedrig sitzender Schwanz treten damit zugunsten von Kopf,
Brust und Farbwirkung zurück. Nach Schließen oder Auswahl kehrt die Vorschau zur
ursprünglichen Kamera zurück. Bei Editorwechsel erfolgt die Wiederherstellung vor
dem Abbau, damit eine verspätete Variantenaufnahme die neue Ansicht nicht verändert.

Zusätzlicher Node-Harness: engerer Ausschnitt und exakte Kamerawiederherstellung,
übereinstimmende Farbpalette, sichtbare Legende nur im Druckweisenmodus sowie
Hilfen und ausgewogene Label-Tags im gerenderten Planeditor bestanden.
`node --check` für alle vier betroffenen JavaScript-Module bestanden. Eine echte
Browserabnahme dieser Änderungen muss nach Reload getrennt dokumentiert werden.

## Nachtrag: berechnete Mischvorschau

Die Ansicht „Zielfarben (berechnet)“ fordert das lokale Matching auf Mischrezepte
an. Der Request enthält den erwarteten gespeicherten Planhash und den vollständigen
aktuellen Entwurf. Es entstehen keine API-Anbieterkosten und keine Planfreigaben.
Ohne zwei unterschiedliche Basisfilamente bleibt die Darstellung neutral Grau;
auch während einer noch ausstehenden Berechnung werden keine unberechneten
Zielfarben als fertige Mischwirkung ausgegeben.

Die Anzeige umfasst das verwendete Basispaar, eine Palette der berechneten
Anteile, rechnerische Teilschichtdicken und die Basisschichthöhe (derzeit 0,2 mm).
Für den ausgewählten Bereich werden Anteilsspanne und Zahl der verwendeten
Rezepte gezeigt. Die gemeldete Abdeckung der nativen Vorlage und Warnungen sind
separat sichtbar. Bildschirmfarben und Dicken bleiben rechnerische Schätzungen,
keine physische Farbmessung, kein Nachweis druckbarer Teilschichthöhen und keine
Slicing-Abnahme. Die Neuner-Matrix ist ausdrücklich als Zielfarbvorschlag
gekennzeichnet; die berechnete Rezeptwirkung wird für den gewählten Plan geladen.

Die Kamerapose bleibt beim Austausch der Geometrievorschau erhalten. Requests
werden 350 ms entprellt und pro Editor serialisiert; Antworten für inzwischen
veränderte Entwürfe oder abgebaute Editoren werden verworfen. Ein Cache hält
höchstens zwei Berechnungsergebnisse. Das verhindert wiederholte Vollberechnungen
bei reinem Regionswechsel und parallele Anfragen bei schnellem Malen.

Isolierter Node-Harness bestanden: kein Request ohne Basispaar; Hash-/Entwurfsbindung;
Darstellung von 10–50 % Anteil und 0,02/0,18 mm Teilschichtdicken; vollständiger
Erhalt der Kamera; Verwerfen einer veralteten Antwort. Dieser simulierte Test
ersetzt den echten lokalen API-/Browserdurchlauf nicht.

## Nachtrag: Geometrie und Farbtechnik unabhängig

Ein getrenntes Bauteil darf zugleich Mixed Filament nutzen, etwa ein abgetrenntes
Ohr mit einem Verlauf. Der Planeditor führt dafür „Farbtechnik“ zusätzlich zur
Geometrieentscheidung: „Ein Filament“ oder „Mixed Filament“. Bei einem getrennten
Bauteil bleiben Schnittart und Gruppennummer dabei sichtbar; eine Auswahl der
Mixed-Farbtechnik entfernt diese Geometrieentscheidung nicht.

Die Regionliste benennt beide Eigenschaften, beispielsweise „Getrenntes Bauteil ·
Mixed Filament“. Die Druckweisen-Vorschau priorisiert Gelbgrün für die Mixed-Technik;
die sichtbare Legende erklärt, dass Mixed auch auf separaten Bauteilen möglich ist.
Der Gruppenzähler zählt die beiden Basisfilamente auch bei solchen Einzelteilen.
Pinselaktionen erhalten die gewählte Farbtechnik. Ältere Pläne mit der Strategie
`mixed` bleiben kompatibel; beim Wechsel dieser Region zu einem getrennten Bauteil
bleibt die Mischtechnik erhalten. KI-Vorschläge lassen Geometrie und Farbtechnik
vor der Übernahme getrennt bearbeiten.

Node-Harness bestanden: Erkennung beider Mixed-Formen; gelbgrüne Darstellung eines
Mixed-Einzelteils; Regionbeschriftung und Zwei-Basisfilament-Zähler; gleichzeitige
Schnitt-/Gruppen- und Mixed-Einstellungen; verlustfreier Wechsel einer Legacy-
Mixed-Region zum Einzelteil. Diese Frontendprüfung ist keine Abnahme der realen
Konstruktion oder des nativen Exports eines gemischten Einzelteils.

### Responsive Nachkorrektur für 860–1.100 px

Bis einschließlich 1.100 px Fensterbreite stehen Vorschau und Editor jetzt
untereinander. Die Projektleiste weicht der kompakten Projektauswahl. Damit
entsteht neben dem mindestens 480 px breiten Editor keine unbrauchbar schmale
350-px-Vorschau mehr. Oberhalb dieser Grenze bleibt die breite Desktopaufteilung.

Die sichtbare Druckweisen-Legende erhält in schmalen Fenstern einen reservierten
Bereich unter dem eigentlichen Canvas. Die Figur wird nicht mehr hinter der
Legende gezeichnet. Bei „Zielfarben (berechnet)“ verschwindet die Strategiefarben-
Legende einschließlich des dafür reservierten Platzes. Auf sehr kleinen Geräten
ist der Legendenbereich höher, damit der Mixed-Hinweis umbrechen kann.

Geprüft wurden CSS-Klammerbilanz und die Reihenfolge der wirksamen Mediaqueries.
Ein realer 860-px-Screenshot dieser Nachkorrektur ist durch diese Codeprüfung
noch nicht belegt und bleibt Teil der getrennten Browserabnahme.

## Nachprüfung im mittleren Fenster und im laufenden Workflow

Bei 1264 px fiel die lange Projektliste durch Flex-Schrumpfung über sich selbst; Projektzeilen behalten jetzt ihre Inhaltshöhe. Von 1101 bis 1450 px erhalten Modell und Editor je eine nutzbare Spalte, die Projektwahl steht kompakt oben. Alle sechs Schritte sind in zwei Reihen sichtbar. Der Lichtschalter lässt die zugewiesenen Farben ohne zusätzliche Vorschau-Beleuchtung beurteilen; kein Material wird dadurch geändert. Netzwerkunterbrechungen halten die Statusabfrage nicht mehr dauerhaft an. Ein unveränderter Farbplan verwirft keine Konstruktion; abhängige Schritte speichern bearbeitete Entwürfe vor dem Wechsel. Node-Workflowregressionen und aktueller Browsernachweis im Testbericht.
