from __future__ import annotations
import ipaddress
import json
import os
import socket
import threading
from pathlib import Path
from urllib.parse import urlsplit
from cryptography.fernet import Fernet

ENV_KEYS={'openai':'OPENAI_API_KEY','gemini':'GEMINI_API_KEY','meshy':'MESHY_API_KEY','tripo':'TRIPO_API_KEY','local':'LOCAL_API_KEY'}


class Vault:
    """Local at-rest encryption. Owner protection, not a multi-tenant KMS."""
    def __init__(self,directory:Path):
        directory.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()
        self.file=directory/'secrets.enc'; keyfile=directory/'vault.key'
        master=os.getenv('FORGE_VAULT_KEY')
        if master: key=master.encode()
        else:
            if not keyfile.exists():
                fd=os.open(keyfile,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'wb') as f:f.write(Fernet.generate_key())
            key=keyfile.read_bytes()
        self.cipher=Fernet(key)
    def _all(self):
        with self.lock:
            return json.loads(self.cipher.decrypt(self.file.read_bytes())) if self.file.exists() else {}
    def get(self,provider): return os.getenv(ENV_KEYS.get(provider,'')) or self._all().get(provider)
    def _write(self,data):
        temp=self.file.with_suffix('.tmp'); fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
        with os.fdopen(fd,'wb') as f: f.write(self.cipher.encrypt(json.dumps(data).encode()))
        temp.replace(self.file)
    def set(self,provider,value):
        with self.lock:
            data=self._all(); data[provider]=value; self._write(data)
    def delete(self,provider):
        with self.lock:
            data=self._all(); data.pop(provider,None); self._write(data)
    def status(self): return {k:bool(self.get(k)) for k in ENV_KEYS}


def safe_asset_path(root:Path,relative:str) -> Path:
    candidate=(root/relative).resolve()
    if not candidate.is_relative_to(root.resolve()): raise ValueError('Path traversal rejected')
    if not candidate.is_file(): raise FileNotFoundError('Asset not found')
    return candidate


def validate_public_url(url:str,allowed_domains=None,resolve=True):
    u=urlsplit(url)
    if u.scheme!='https' or not u.hostname or u.username or u.password or (u.port not in (None,443)):
        raise ValueError('Only public HTTPS asset URLs are accepted')
    host=u.hostname.lower()
    if host=='localhost' or host.endswith('.localhost') or host.endswith('.local'):
        raise ValueError('Private asset URL rejected')
    if allowed_domains and not any(host==d or host.endswith('.'+d) for d in allowed_domains):
        raise ValueError('Asset host not on the provider CDN allowlist; configure an approved domain server-side')
    try:
        ip=ipaddress.ip_address(host)
        if not ip.is_global: raise ValueError('Private/reserved asset IP rejected')
    except ValueError as e:
        if 'IP rejected' in str(e): raise
    if resolve:
        addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
        if not addresses or any(not ipaddress.ip_address(row[4][0]).is_global for row in addresses):
            raise ValueError('Asset resolves to a private/reserved address')
    return url
