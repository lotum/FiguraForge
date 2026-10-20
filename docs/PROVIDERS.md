# Provider-Vertraege und Anschluss eigener Modelle

Pruefstand 16.10.2026: OpenAI Images und Meshy haben echte Ergebnisse geliefert.
Der freigegebene Meshy-Remesh kostete 5 Credits; seine offene Topologie wurde
abgelehnt. Die uebernommene Reduktion erfolgt lokal mit Blender. Andere Adapter
und Astra-Vorschlaege sind mockgetestet, nicht mit bezahlten Live-Aufrufen
abgenommen. Siehe [Testbericht](TEST_REPORT.md) und [Privatsphaere](PRIVACY_PROVIDERS.md).

Meshy: `should_remesh=true`, `topology=triangle`, `target_polycount=150000`
(Standard, begrenzt durch Arbeits-/Refinementbudget). Nach Download lokale
Qualitaetspruefung; Zielzahl ist keine harte Anbieterzusage. Remesh vorhandener
Modelle ueber `/openapi/v1/remesh`, kein erneuter Bild-zu-3D-Auftrag.

Astra: Responses API, `store=false`, strukturiertes JSON mit erlaubten Feldern,
Pydantic-Grenzen und versionierter Vorschlagsbasis. Kein Ausgabenlimit,
Providerwechsel oder Freigabe darf vom Vorschlag erhoeht/erteilt werden.

## Vorhandene Adapter

| Adapter | Authentifizierung | Aufrufe | Implementierter Umfang |
|---|---|---|---|
| OpenAI Images | OPENAI_API_KEY | POST /v1/images/edits bzw. /generations | Referenzbilder, Prompt, Modell, Groesse, Qualitaet; PNG-Antwort |
| Gemini | GEMINI_API_KEY | POST /v1beta/interactions | Text plus Base64-Bilder, PNG, 2:3, 2K; finale model_output-Bildbloecke |
| Gemini Legacy | GEMINI_API_KEY | POST /v1beta/models/{model}:generateContent | InlineData-Eingaben, IMAGE/TEXT-Ausgabe |
| Meshy | MESHY_API_KEY | POST/GET /openapi/v1/multi-image-to-3d | 1-4 Ansichten, PBR, GLB, Remote-ID und Polling |
| Tripo | TRIPO_API_KEY | POST /v2/openapi/upload und /task, GET /task/{id} | H3 Image/Multiview, vier Ansichtspositionen, PBR-Modell |
| LocalGateway | LOCAL_API_KEY optional | POST /jobs, GET /jobs/{id} | Eigener unten definierter Vertrag; keine mitgelieferten Modellgewichte |
| OpenAI Review | OPENAI_API_KEY | POST /v1/responses | JSON-Bewertung von Identitaet/Pose/Konsistenz und Korrekturhinweis |

### OpenAI

Default ist `gpt-image-2.5-sunburst`, Qualitaet `max`; beide sind editierbar.
`input_fidelity=high` wird nur fuer die passenden Modelle 1/1.5 gesendet, nicht
blind an neuere Modelle. Bei einem Modell ohne `max` wird auf `high` gewechselt.
Es wird die Images-API genutzt, nicht eine angebliche Steuerung des ChatGPT-UI.

### Google

Default im Interactions-Modus ist `gemini-nano-banana-2.1`. Fuer aeltere Modelle
steht ein separater generateContent-Modus zur Verfuegung. Aktuell werden 2K
und 2:3 angefordert; ein OpenAI-Bildgroessenstring steuert diese Google-Werte
nicht. Der Parser verwendet finale generierte Bilder, keine internen
Thinking-/Zwischenbilder. Unterschiedliche API-Antwortformen sind mockgetestet.

### Meshy

Es werden bewusst dokumentierte, einfache Grundparameter gesendet. Der
Modellname ist editierbar; `latest` folgt dem Anbieter und ist daher kein
reproduzierbar eingefrorener Gewichtsstand. Fuer reproduzierbare Auftraege
konkrete Modellnamen verwenden. Der Adapter fordert GLB mit Texturen an;
die aktuell dokumentierten zusaetzlichen Ultra-/8K-Optionen sind noch keine
UI-Auswahl. Automatische Textur-Nachbeleuchtung wird dem Anbieter ueberlassen.

### Tripo: bekannte wichtige Grenze

Die offizielle H3-Dokumentation nennt meshopt als Standardkompression. Der
Geometrieimport dieses Releases akzeptiert **keine erforderliche meshopt-,
Draco- oder BasisU-Dekompression**. Ein solches Ergebnis wird abgelehnt statt
unsauber eingelesen. Eine providerseitige entkomprimierte Ausgabe oder ein
bewusst eingerichteter Konverter kann deshalb erforderlich sein. Dies ist
ein noch offener Integrationspunkt und kein bereits geloester Live-Workflow.
Der task_id bleibt gespeichert, um den bezahlten Auftrag nicht erneut zu bestellen.

## Lokaler Inferenzserver: expliziter Vertrag

`FORGE_LOCAL_GATEWAY` wird nur durch den Betreiber gesetzt, zum Beispiel
`http://127.0.0.1:9100`. Das ist **nicht** automatisch die API eines beliebigen
Hunyuan-/TRELLIS-Web-UIs. Ein Worker muss den folgenden Vertrag implementieren.

POST `/jobs`, Bearer-Token falls konfiguriert:

```json
{
  "model": "my-pinned-model-version",
  "images": ["data:image/png;base64,..."],
  "output_format": "glb",
  "texture": true
}
```

Antwort:

```json
{"id": "worker-job-123"}
```

GET `/jobs/worker-job-123`:

```json
{"id": "worker-job-123", "status": "running"}
```

Erfolg, Variante A:

```json
{"status": "succeeded", "model": "my-pinned-model-version", "glb_base64": "..."}
```

Erfolg, Variante B:

```json
{"status": "succeeded", "model": "my-pinned-model-version", "asset_path": "/assets/worker-job-123.glb"}
```

`asset_path` ist same-origin, keine fremde URL oder lokale Dateipfad-Abkuerzung.
Fehler: `{"status":"failed"}`. Ergebnis maximal 100 MB, selbstenthaltenes GLB
mit eingebetteter Albedo, ohne erforderliche Kompressionsdecoder.
Der lokale Worker ist vertrauenswuerdige Betreiberinfrastruktur. Bei Docker
zeigt localhost auf den Container; Netzwerkadresse bewusst konfigurieren.

## Neuer Provider

Klasse nach dem Muster in `providers/` implementieren. Bildadapter:
`generate(prompt, refs, output, model, quality, size)`. 3D-Adapter:
`submit(...) -> task_id`, `poll(task_id, output) -> provenance`.
Zusaetzlich Auswahl in Settings, Runner und UI registrieren. Fuer einen neuen
3D-Anbieter mit eigenem Gateway ist keine Aenderung am Geometriekern notwendig.

Pflichten: keine automatischen kostenpflichtigen Wiederholungen, Remote-ID
persistieren, konkrete Modellversion protokollieren, keine Schluessel loggen,
Download-Hosts begrenzen und aktuelle Vertrags-Tests ergaenzen.

## Live-Abnahme mit eigenem Konto

Zuerst ein unkritisches eigenes Referenzbild, ein Bild und ein kleiner 3D-Task.
Anbieter-Dashboard auf tatsaechliche Kosten, Modellnamen und fertiges Asset
pruefen. Erst danach vier Ansichten und automatische Korrekturrunden aktivieren.
Den generierten GLB-Header auf Kompression und die Textur auf Schatten prüfen.
Eine 3D-Ausgabe mit gutem Rendering ist noch kein druckfaehiges Volumen.

## Primaerquellen

- https://developers.openai.com/api/reference/cli/resources/images/methods/edit
- https://ai.google.dev/gemini-api/docs/image-generation
- https://docs.meshy.ai/en/api/multi-image-to-3d
- https://docs.tripo3d.ai/model-generation/multiview-to-model-v3-0-v3-1.html
