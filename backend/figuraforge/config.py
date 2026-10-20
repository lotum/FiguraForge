from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
# In a source checkout: ROOT is backend's parent (project root).
ROOT=ROOT.parent if ROOT.name=='backend' else ROOT


def load_env(path:Path):
    """Minimal local .env loader; does not override actual environment variables."""
    if not path.exists(): return
    for raw in path.read_text(encoding='utf-8').splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        key,value=line.split('=',1)
        if key.strip().replace('_','').isalnum(): os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))


@dataclass
class Config:
    root:Path=ROOT
    data_dir:Path|None=None
    api_token:str|None=None
    max_upload_mb:int=64
    def __post_init__(self):
        load_env(self.root/'.env')
        self.data_dir=Path(self.data_dir or os.getenv('FORGE_DATA_DIR',str(self.root/'data'))).resolve()
        self.data_dir.mkdir(parents=True,exist_ok=True)
        try: self.data_dir.chmod(0o700)
        except OSError: pass
        self.api_token=self.api_token or os.getenv('FORGE_API_TOKEN') or None

    @property
    def frontend(self): return self.root/'frontend'
    @property
    def assets(self): return self.root/'assets'
