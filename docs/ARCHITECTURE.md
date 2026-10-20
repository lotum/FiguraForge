# Architektur und Entwicklungsuebergabe

Stand: 0.1.0, 15.10.2026. Ausfuehrbare lokale Einzelbenutzer-Anwendung, keine
verteilte SaaS-Infrastruktur.

## Aufbau

```
Browser: HTML/CSS/ES-Module
  -> FastAPI / JSON / Uploads
       -> SQLite (Projekt, Freigaben, Jobs, Budget, Filamente)
       -> Datei-Artefakte in unveraenderlichen runs/<job-id>/
       -> ThreadPool: zwei ausfuehrende Threads
            -> austauschbare Bild-/3D-Provider
            -> serialisierte Einweg-Geometrieprozesse + isolierter Plane-Clip-Prozess
            -> 3MF/GLB/ZIP-Exporter
```

Die urspruenglich erwogenen React/Next.js, Redis, Celery und LangGraph sind
fuer diese lokale Ausbaustufe absichtlich nicht erforderlich. Der Browser
laedt ausschliesslich eigene statische Dateien. GPU-Vorschau: WebGL; ohne
WebGL existiert ein tatsaechlicher Software-3D-Renderer mit Picking. Backend:
FastAPI, Pydantic, NumPy, SciPy, Trimesh, VTK und Shapely.

Eine kuenftige verteilte Version kann den Runner ersetzen. Die vorhandene
SQLite-Sperre ist **kein** verteilter Scheduler. Mehrere Uvicorn-Prozesse sind
nicht unterstuetzt; der Startwrapper setzt workers=1.

## Zustandsmodell

`pose -> mesh -> segments -> colors -> export`

Menschliche Freigaben gibt es fuer Pose, Mesh und Farben. Jede Freigabe bindet
an einen SHA256-Hash des konkreten Artefakts. Ein Settings-Patch verwirft nur
betroffene Stufen und deren Nachfolger. Budget- und Reviewer-Einstellungen
veraendern bestehende Geometrie nicht.

- Geaenderte Pose oder Referenzen: Pose/Mesh/Konstruktion/Farben/Export verfallen.
- Neue Hoehe oder Orientierung: Mesh und Nachfolger verfallen; Quellbytes bleiben.
- Geaenderter Schnitt: Konstruktion und Nachfolger verfallen.
- Neue Filamente: Farben/Export verfallen; Mesh und konstruierte Koerper bleiben.
- Ein manuell importiertes Mesh darf die Pose-Stufe bewusst ueberspringen. Dies
  wird als Herkunftsmerkmal gespeichert.

Bearbeitung und Job-Start werden innerhalb der Datenbank gesperrt; ein aktiver
Job pro Projekt. UI und API verweigern veraltete Freigaben. Run-Verzeichnisse
sind versioniert, aber es gibt noch keinen interaktiven Versions-Rollback.

## Schichten und Erweiterungspunkte

| Ordner | Verantwortlichkeit |
|---|---|
| `backend/figuraforge/providers/` | REST-Vertraege, Auftrags-IDs, Polling, sichere Downloads |
| `geometry/io.py` | GLB/PLY/STL, Einheiten, Texturen, Orientierung |
| `geometry/refine.py` | Konforme Grenzabtastung ohne T-Knoten |
| `geometry/construct.py` | Organische Farbeinsaetze und gemeinsame Taschen |
| `geometry/surface_parts.py` | Ganze Farbkoerper an nichtplanaren Oberflaechenkonturen |
| `geometry/connectors.py` | Stift-/Buchsengeometrie ohne proprietaere CAD-Abhaengigkeit |
| `geometry/split.py` | Zusaetzliche Strukturteilung zu grosser Bauteile |
| `geometry/packing.py` | Heuristische Ausrichtung und Plattenbelegung |
| `services/workflow.py` | Hash-Freigaben, Farb-Snapshots, spulenabhaengige Platten |
| `services/export.py` | Core-3MF, GLB, Manifest, Montage, Pruefsummen |
| `services/jobs.py` | Ausfuehrung, Budget, Abbruch, Recovery |
| `services/native_jobs.py`, `geometry_task.py` | Einwegprozesse, Deadline, nativer Crash-/Abbruchschutz |
| `frontend/` | Produkt-Workflow und echte 3D-Interaktion |

Providerobjekte besitzen keinen Zugriff auf die gesamte Datenbank. Der Runner
uebergibt explizite Referenzen und Zielpfade. Erzeugte Prompttexte duerfen keine
Dateipfade oder beliebige Werkzeuge ausfuehren. Geometrieentscheidungen werden
nicht an ein unbeschraenktes Shell-Agentensystem delegiert.

## Auftrag und Recovery

Status: queued, running, succeeded, failed, cancelled, interrupted.
Remote-ID wird unmittelbar nach Annahme eines 3D-Auftrags persistiert. Nach
Neustart werden laufende Auftraege als interrupted markiert. Wiederaufnahme
fragt genau denselben Provider-Task ab; Pose-Hash und Provider muessen stimmen.
Ein unklar beantworteter kostenpflichtiger POST wird nicht blind wiederholt.
Bildgeneratoren liefern in diesem Adapter synchron; fuer einen verlorenen
Bild-POST gibt es keine erfundene Remote-Wiederaufnahme.

Importpruefung, Konstruktion und Export laufen in separaten Prozessen. Der
Webserver pollt Fortschritt und Abbruch und kann einen haengenden oder
abgestuerzten nativen Worker beenden. FORGE_GEOMETRY_TIMEOUT_SECONDS setzt
das Zeitlimit pro Operation (Default: 1800 Sekunden). Struktur-Clip-Versuche
haben zusaetzlich ein eigenes kurzes Limit. Prozessgruppen-Abbruch wurde
unter Linux getestet; Windows/macOS muessen separat abgenommen werden.
Das ist keine Netzwerk- oder Speicher-Sandbox. Ein bereits gestarteter
Cloud-Task kann beim Anbieter weiterlaufen und Kosten verursachen.

## Speicherung und API

SQLite-Tabellen: projects, jobs, events, filaments. Projektinhalt ist versioniertes
JSON mit Referenzen, Settings, Artefakten, Freigaben und Schaetzkosten-Ledger.
NPZ-Geometrien werden mit `allow_pickle=False` gelesen. Alle Kernkoordinaten
sind Millimeter/Z-up. GLB-Ausgabe wird auf Meter/Y-up transformiert.

Die aktuelle API ist maschinenlesbar unter `/openapi.json`; `/docs` zeigt eine
lokale Endpoint-Liste. Es gibt keine abhaengige Swagger-CDN.

## Naechste fachlich sinnvolle Erweiterungen

1. Eine kleine reale Figuren-Testmenge mit scharfen Farbgrenzen, Gradient,
   umlaufendem Band, Haaren, Gesicht und duennen Fingern als Regressionen pflegen.
2. Reale Passungsdaten pro Material/Duese/Orientierung speichern und statt
   universeller Defaultwerte nutzen.
3. Experten-Schnittkurven im 3D-Viewer editierbar machen; heute koennen Palette,
   Parameter und Auszugsrichtungen editiert werden, nicht einzelne Kurvenpunkte.
4. Separaten Blender-Worker fuer kontrollierte Reparatur/Rigging oder einen
   geprueften PartPin-Adapter ergaenzen. Lizenzen und Laufzeit getrennt betrachten.
5. Native Bambu-3MF-Projektintegration anhand echter, versionierter H2D-Projekte
   testen; keine unbekannten proprietaeren XML-Felder erfinden.
6. Authentifizierte Mehrbenutzer-Version erst mit isolierten Jobs, Quoten,
   speicherbegrenzten Parsern und mandantenfaehiger Geheimnisverwaltung bauen.
