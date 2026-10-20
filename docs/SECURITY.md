# Sicherheits- und Betriebsgrenzen

## Voreinstellung: lokal, ein Benutzer

Der Startwrapper bindet 127.0.0.1. Die API verweigert Zugriffe auf einen
nichtlokalen Host ohne FORGE_API_TOKEN. Diese Hostpruefung ersetzt keine Firewall;
beim Verlassen von localhost immer Token, HTTPS-Reverse-Proxy und
Zugriffsbeschraenkung verwenden. Nicht einfach Port 8000 im Internet freigeben.

Die Implementierung ist keine mandantenfaehige Plattform. Wer das
Workspace-Token kennt, darf alle Workspace-Projekte und Cloud-Keys verwenden.
Es gibt keine Benutzerrollen, OIDC-Anbindung oder tenantbezogene Quoten.

## API-Keys

Fernet-verschluesselte Datei `secrets.enc`, lokale Masterdatei `vault.key`.
Dateirechte werden auf 0600 gesetzt; Datenordner 0700, soweit das Betriebssystem
dies unterstuetzt. Die Web-API liefert nur konfiguriert/nicht konfiguriert,
nie gespeicherte Klartextkeys. Updates sind innerhalb des Prozesses atomar.

Ein Angreifer mit Dateizugriff auf Tresor UND Masterdatei kann entschluesseln.
Das ist Schutz gegen versehentliches Mitlesen einzelner Dateien, kein KMS.
Optional FORGE_VAULT_KEY aus getrenntem Secret-Management setzen.
Environment-Keys haben Vorrang; Loeschen eines UI-Keys entfernt keinen
extern gesetzten Environment-Key. Keine echten Secrets in ein Repository committen.

## Uploads und externe Ressourcen

- Bilder: begrenzte Dateigroesse und Pixelzahl, EXIF-Orientierung anwenden,
  Metadaten beim PNG-Speichern entfernen und grosse Referenzen verkleinern.
- GLB: Formatkennung, Laenge und externe Ressourcen pruefen. Keine externen
  GLTF-URIs, keine Dateipfade aus einem Modell nachladen.
- Downloads: HTTPS, Host-Allowlist, keine privaten/reservierten Zieladressen,
  begrenzte Redirects und Datenmenge; API-Schluessel werden nicht an CDN-URLs angehaengt.
- Projektdateizugriff: Pfad muss im Projektordner liegen, Typ-Allowlist.
- Keine freie Shell-Ausfuehrung aus Prompt- oder Meshinhalten.
- JSON-/NPZ-Artefakte statt unsicherer Pickle-Dateien.

Bekannte Grenze: DNS wird geprueft, aber die IP ist nicht ueber den gesamten
TLS-Verbindungsaufbau kryptographisch gepinnt. Fuer oeffentlichen Betrieb ist
eine strikte Netzwerk-Egress-Regel erforderlich. Mesh-Importpruefung, Konstruktion und Export laufen in abbrechbaren
Einwegprozessen mit Deadline, jedoch nicht in speicher- oder
netzwerkbeschraenkten Sandbox-Containern. Bildparser laufen im API-Prozess. Es gibt
Uploadgroessen- und Face-Limits, aber keinen Beweis gegen jede Dekompressionsbombe.
Unvertrauenswuerdige Massenuploads sind kein unterstuetztes Einsatzszenario.

## Browser

Same-Origin-Pruefung fuer schreibende API-Aufrufe, Strict-SameSite/HttpOnly
Sessioncookie, CSP nur fuer eigene Scripts, keine externen CDNs. Inline-Stile
sind fuer die Vorschau/Farbfelder erlaubt. HTML-Texte werden escaped.
Die CSP und ein lokales Token sind keine vollständige Mehrbenutzer-Haertung.

## Kosten und Abbruch

Budget ist eine konservative manuelle Schaetzung, keine aktuelle Preisdatenbank.
Reservierungen werden auch bei mehrdeutigen Fehlern nicht automatisch
zurueckgesetzt. Keine wiederholten bezahlten POSTs nach Timeout.
Bereits uebertragene Cloud-Referenzen werden durch einen lokalen Abbruch nicht
beim Anbieter geloescht. Datenaufbewahrung und Loeschung dort separat regeln.

## Vor einem produktiven Cloud-Deployment

TLS, Identitaetsprovider, echte Rollen, isolierte Worker, Daten- und
Laufzeitquoten, Netzwerk-Egress, Secret-Management, Audit, Backup/Restore,
Abhaengigkeits-Scanning, Bild-/Mesh-Sandbox und geloescht-markierte Artefakte
mit geplanter Bereinigung ergaenzen. Docker/CI-Dateien sind Startpunkte und
wurden hier nicht als Internet-Deployment abgenommen.
