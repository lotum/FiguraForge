# Passungsrückmeldung – PLA, H2D, vier Nasenproben

## Ergebnis vom 16. Oktober 2026

Richard hat die vorbereitete Vergleichsplatte gedruckt und die vier Paare geprüft.
Die Reihenfolge entspricht A005/B010/C015/D020, also von links nach rechts dem
steigenden radialen Spiel. Der Stift hat nominal 3 mm Breite, Länge 3 mm und eine
abgeflachte Vierkantkontur gegen Verdrehen. Radiales Spiel ist die Zugabe je Seite der Tasche.

| Nutzerbezeichnung | Radiales Spiel | Breitendifferenz | Tatsächliches Nutzerfeedback |
|---|---:|---:|---|
| 1 / A005 | 0,05 mm | 0,10 mm | Gerade steckfest: lässt sich eindrücken, hält, ganz leichtes Restwackeln. Für größere Steckteile akzeptiert. Ein minimal engerer Sitz wäre denkbar, wurde nicht getestet. |
| 2 / B010 | 0,10 mm | 0,20 mm | Ein kleines bisschen zu lose; fällt heraus. |
| 3 / C015 | 0,15 mm | 0,30 mm | Zu lose. |
| 4 / D020 | 0,20 mm | 0,40 mm | Zu lose. |

**Verwendeter Ausgangswert für Buddy, Mochi und Pip: 0,05 mm radial.**
Keine automatische Verschärfung auf 0,04 mm; das würde einen neuen Test brauchen.
Die drei Projektstände vor der Änderung wurden in einem neuen lokalen Benchmark-
Ordner gesichert; alte Geometrie-/Exportdateien bleiben erhalten. Geänderte
Passungen invalidieren die bisherigen Konstruktionen und Material-/Exportfreigaben,
nicht die unveränderte Pose- oder Meshversion. Neue Konstruktionen werden erneut
geometrisch geprüft.

## Testbedingungen und Grenzen

Vorbereitete Bambu-Datei: `Nasenvergleich-H2D-0.12-PLA-Beige-GUI-geprueft.3mf`.
Slicerprofil: H2D, 0,4-mm-Düse, 0,12-mm-Schichten, drei Raftlagen und Stützen,
geplanter einzelner PLA-Slot 2 / Beige. Richard hatte PLA und 0,4-mm-Düse genannt;
eine unabhängige Bestätigung der tatsächlich am Gerät geladenen Marke/Spule und
unveränderter Maschinenkompensation liegt nicht vor.

Das ist eine qualitative Passungsprüfung dieser konkreten Verbindung, keine
Messschiebermessung oder allgemeine Materialkalibrierung. Leichtes Rotationsspiel
bleibt dokumentiert. Größere Stifte, andere Orientierung, andere Schichthöhe,
anderes PLA, PETG/TPU oder Klebeeinsätze können abweichend reagieren. Deshalb bleibt
der Wert pro Projekt sichtbar einstellbar; allgemeine Softwaredefaults für
unbekannte Materialien werden nicht heimlich als physisch kalibriert ausgegeben.

Der vorherige einzelne 0,20-mm-Test war zusätzlich durch schrägen, ungestützten
Druck beeinträchtigt. Die neue Viererprobe hatte bewusst gleiche Stiftrichtung
und geprüfte Stützen. [Digitaler Stützennachweis](nose-fit-comparison-verification.json).

## Nächster technischer Nachweis

Neue Figurenteile werden mit 0,05 mm konstruiert, auf geschlossene Volumen,
Kollisionen und druckbare Platzierung geprüft. Die physische Montage aller
Figurenteile und die Farbwirkung der Mixed-Rezepte stehen weiterhin aus.
