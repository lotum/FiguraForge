from __future__ import annotations
import contextlib
import hashlib
import json
import sqlite3
import time
import uuid
from pathlib import Path


def uid(): return uuid.uuid4().hex

def digest(obj): return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def now(): return time.time()


class Conflict(ValueError): pass
class NotFound(ValueError): pass


class Store:
    def __init__(self,directory:Path):
        self.directory=directory; self.path=directory/'forge.sqlite3'
        with self.connection() as c:
            c.executescript('''
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, project_id TEXT, status TEXT, created REAL, data TEXT);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, at REAL, kind TEXT, message TEXT);
            CREATE TABLE IF NOT EXISTS filaments(id TEXT PRIMARY KEY,data TEXT);
            ''')
    @contextlib.contextmanager
    def connection(self):
        c=sqlite3.connect(self.path,timeout=30)
        c.row_factory=sqlite3.Row
        try: yield c; c.commit()
        except BaseException: c.rollback(); raise
        finally: c.close()

    def create_project(self,title,settings):
        p={'id':uid(),'title':title,'created':now(),'updated':now(),'revision':0,'settings':settings,
           'references':[],'artifacts':{},'approvals':{},'ledger':[]}
        with self.connection() as c: c.execute('INSERT INTO projects VALUES(?,?)',(p['id'],json.dumps(p)))
        (self.directory/'projects'/p['id']).mkdir(parents=True)
        self.event(p['id'],'created','Projekt erstellt')
        return p

    def list_projects(self):
        with self.connection() as c: rows=c.execute('SELECT data FROM projects').fetchall()
        return sorted([json.loads(r['data']) for r in rows],key=lambda p:-p['updated'])

    def get(self,project_id):
        with self.connection() as c: row=c.execute('SELECT data FROM projects WHERE id=?',(project_id,)).fetchone()
        if row is None: raise NotFound('Project not found')
        return json.loads(row['data'])

    def mutate(self,project_id,fn,expected_revision=None,require_idle=False):
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT data FROM projects WHERE id=?',(project_id,)).fetchone()
            if row is None: raise NotFound('Project not found')
            if require_idle and c.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')",(project_id,)).fetchone():
                raise Conflict('A project job became active; editing was rejected')
            p=json.loads(row['data'])
            if expected_revision is not None and p['revision']!=expected_revision: raise Conflict('Project changed; stale operation rejected')
            fn(p); p['revision']+=1; p['updated']=now()
            c.execute('UPDATE projects SET data=? WHERE id=?',(json.dumps(p,allow_nan=False),project_id))
        return p

    def project_dir(self,project_id):
        self.get(project_id)
        return self.directory/'projects'/project_id

    def event(self,project_id,kind,message):
        with self.connection() as c: c.execute('INSERT INTO events(project_id,at,kind,message) VALUES(?,?,?,?)',(project_id,now(),kind,str(message)[:1000]))

    def events(self,project_id):
        with self.connection() as c: rows=c.execute('SELECT * FROM events WHERE project_id=? ORDER BY id DESC LIMIT 200',(project_id,)).fetchall()
        return [dict(r) for r in rows][::-1]

    def active_job(self,project_id):
        with self.connection() as c: row=c.execute("SELECT data FROM jobs WHERE project_id=? AND status IN ('queued','running') LIMIT 1",(project_id,)).fetchone()
        return None if row is None else json.loads(row['data'])

    def new_job(self,project_id,operation,request):
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("SELECT 1 FROM jobs WHERE project_id=? AND status IN ('queued','running')",(project_id,)).fetchone():
                raise Conflict('A job is already active for this project')
            p=self.get(project_id)
            j={'id':uid(),'project_id':project_id,'operation':operation,'status':'queued','created':now(),
               'updated':now(),'message':'In Warteschlange','error':None,'request':request,
               'base_revision':p['revision'],'checkpoint':{},'cancel_requested':False}
            c.execute('INSERT INTO jobs VALUES(?,?,?,?,?)',(j['id'],project_id,j['status'],j['created'],json.dumps(j)))
        return j

    def job(self,ident):
        with self.connection() as c: r=c.execute('SELECT data FROM jobs WHERE id=?',(ident,)).fetchone()
        if not r: raise NotFound('Job not found')
        return json.loads(r['data'])

    def update_job(self,ident,**updates):
        with self.connection() as c:
            c.execute('BEGIN IMMEDIATE')
            row=c.execute('SELECT data FROM jobs WHERE id=?',(ident,)).fetchone()
            if not row: raise NotFound('Job not found')
            j=json.loads(row['data']); j.update(updates); j['updated']=now()
            c.execute('UPDATE jobs SET status=?,data=? WHERE id=?',(j['status'],json.dumps(j),ident))
        return j

    def jobs(self,project_id):
        with self.connection() as c: rows=c.execute('SELECT data FROM jobs WHERE project_id=? ORDER BY created DESC LIMIT 50',(project_id,)).fetchall()
        return [json.loads(r['data']) for r in rows]

    def recover(self):
        with self.connection() as c: rows=c.execute("SELECT data FROM jobs WHERE status IN ('queued','running')").fetchall()
        for r in rows:
            j=json.loads(r['data'])
            self.update_job(j['id'],status='interrupted',message='Server neu gestartet. Kein kostenpflichtiger Auftrag automatisch wiederholt.',
                            error='Interrupted: review the saved provider task ID before starting again.')

    def reserve(self,project_id,job_id,amount,operation,override=False):
        def apply(p):
            spent=sum(x['estimate_eur'] for x in p['ledger'])
            limit=p['settings'].get('budget_eur')
            if limit is not None and spent+amount>limit and not override:
                raise Conflict('Gesetztes Ausgabenlimit erreicht (Planwerte). Limit in den erweiterten Kosteneinstellungen pruefen.')
            p['ledger'].append({'id':uid(),'job_id':job_id,'operation':operation,'estimate_eur':amount,'at':now(),
                                'billing_status':'estimate/reservation, not provider invoice'})
        return self.mutate(project_id,apply)

    def filaments(self):
        with self.connection() as c: rows=c.execute('SELECT data FROM filaments').fetchall()
        return [json.loads(r['data']) for r in rows]

    def save_filaments(self,items):
        with self.connection() as c:
            for item in items: c.execute('INSERT OR REPLACE INTO filaments VALUES(?,?)',(item['id'],json.dumps(item,allow_nan=False)))

    def delete_filament(self,ident):
        with self.connection() as c: c.execute('DELETE FROM filaments WHERE id=?',(ident,))
