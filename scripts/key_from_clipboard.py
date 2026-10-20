"""Store a copied provider key in the running local FiguraForge vault (macOS)."""
import argparse
import getpass
import subprocess

import httpx


def store_key(provider, port=8000, *, clipboard=None, client=None, replace=False):
    if provider not in ('openai', 'gemini', 'meshy', 'tripo') or not 1 <= port <= 65535:
        raise ValueError('Ungueltiger Anbieter oder Port.')
    key = (clipboard if clipboard is not None else subprocess.run(
        ['pbpaste'], capture_output=True, text=True, check=True).stdout).strip()
    if not 8 <= len(key) <= 1000 or any(c.isspace() for c in key):
        raise ValueError('Bitte nur den API-Key in die Zwischenablage kopieren.')
    # Never honor proxy environment variables or redirects for credential writes.
    own_client = client is None
    client = client or httpx.Client(base_url=f'http://127.0.0.1:{port}',
                                    timeout=10, trust_env=False, follow_redirects=False)
    try:
        status = client.get('/api/config')
        if status.status_code == 401:
            token = getpass.getpass('Lokales FiguraForge-Zugriffstoken (nicht der Anbieter-Key): ')
            client.headers['Authorization'] = 'Bearer ' + token
            status = client.get('/api/config')
        if status.status_code != 200:
            raise ValueError(f'Lokaler Server nicht bereit (HTTP {status.status_code}).')
        if status.json().get('providers', {}).get(provider) and not replace:
            # Preserve an existing key unless the operator explicitly replaces it.
            raise ValueError('Anbieter bereits konfiguriert. Zum Ersetzen bitte API & Einstellungen verwenden.')
        response = client.post('/api/secrets', json={'provider': provider, 'key': key})
        if response.status_code != 200 or response.json().get(provider) is not True:
            raise ValueError(f'Speichern fehlgeschlagen (HTTP {response.status_code}).')
    finally:
        if own_client:
            client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('provider', choices=['openai', 'gemini', 'meshy', 'tripo'])
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--replace', action='store_true', help='Vorhandenen Anbieter-Key ausdruecklich ersetzen')
    args = parser.parse_args()
    try:
        store_key(args.provider, args.port, replace=args.replace)
    except (ValueError, httpx.HTTPError, OSError, subprocess.SubprocessError):
        # Response bodies and exception strings can contain secret input: omit both.
        print('Nicht gespeichert: Server/Port und Zwischenablage pruefen. '
              'Vorhandene Keys nur mit --replace oder in API & Einstellungen ersetzen.')
        return 1
    print(f'{args.provider}: im lokalen Tresor gespeichert. Kein Anbieter-Aufruf ausgefuehrt.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
