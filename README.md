# FiguraForge

Lokale Webanwendung für druckbare, farbige Figuren: Referenzen → Pose → 3D-Mesh → Farbplan → organische Teile und Verbinder → H2D-Druckpaket.

**Engineering Preview.** Enthält die bestehende Anwendung, Geometriekern, Anbieteradapter, Tests und dokumentierte digitale Prüfungen. Persönliche Datenbank, API-Schlüssel, Referenzuploads und lokale Git-Historie sind nicht enthalten. Neue Installation startet mit leerem Workspace; die prozedurale Testfigur funktioniert ohne API-Key.

## Sofort starten

```sh
git clone https://github.com/lotum/FiguraForge.git
cd FiguraForge
bash start.sh
```

Dann http://127.0.0.1:8000 öffnen. Python 3.12 oder 3.13 empfohlen. Für optionale Cloud-Aufträge eigene Schlüssel unter **API & Einstellungen** eintragen; diese Aufträge können kostenpflichtig sein.

## Figuren und 3MF-Dateien

[Downloadpakete im GitHub-Release](https://github.com/lotum/FiguraForge/releases/tag/share-2026-10-20).

- **FiguraForge-3MF-Druckfassungen.zip**: geprüfte native Druckfassungen für Mochi, Pip und Buddy, Größenvarianten und Passungsproben. Mit Dateiliste, SHA256 und Hinweisen.
- **FiguraForge-3MF-Vollarchiv-*.zip**: vollständiges lokales 3MF-Archiv, identische Dateien nur einmal gespeichert. Enthält auch fehlgeschlagene und überholte Versuche: **kein Druckpaket**. `MANIFEST.json` ordnet alle ursprünglichen Pfade den Dateien zu.
- Die 3MF-Dateien sind Bambu-Studio-Projekte/Geometrien; die ZIPs starten keinen Druck.
- Buddy ist ein großer Entwicklungsstand mit ca. 25,3 kg prognostiziertem Materialverbrauch: **keine Druckempfehlung**. Mochis kleiner Körper wurde vom Nutzer gedruckt; der neue Halsverbinder ist physisch noch nicht geprüft.
- Bestehende öffentliche digitale Prüfberichte sind historische Nachweise. Ihre lokalen `data/`-/`benchmarks/`-Pfade sind ohne zusätzliche Arbeitsdaten nicht reproduzierbar.

## Tests

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -c requirements-tested.txt -e '.[dev]'
.venv/bin/python -m pytest
node tests/frontend_color_plan_regressions.mjs
node tests/frontend_workflow_regressions.mjs
```

Weitere Bedienung und technische Grenzen: [Projektübersicht](docs/PROJECT_HISTORY.md), [Architektur](docs/ARCHITECTURE.md), [Sicherheit](docs/SECURITY.md), [Testbericht](docs/TEST_REPORT.md).

Anwendungscode: MIT. Charaktere, Providerergebnisse und Fremdprofile haben eigene Rechte; die MIT-Lizenz des Codes erteilt keine Charakterrechte. Siehe [Drittanbieterhinweise](THIRD_PARTY_NOTICES.md).
