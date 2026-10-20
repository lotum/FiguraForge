"""Register a NEW inspected neck-split native project, preserving every old one."""
from pathlib import Path
import json,hashlib,shutil
from figuraforge.db import Store
from figuraforge.models import Settings


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proof=json.loads(Path('docs/mochi-neck-split-verification.json').read_text());assert all(proof[str(h)]['passed'] for h in (470,500))
    base=Path('benchmarks/mochi-neck-split-20261018');large=base/'production-500';small=base/'production-470-final';file=large/'Mochi-500mm-Hals-geteilt-3-Platten.3mf';digest=sha(file);assert digest==proof['500']['project_sha256']
    store=Store(Path('data'));project=next((p for p in store.list_projects() if p.get('artifacts',{}).get('saved_prints',{}).get('source_sha256')==digest),None)
    if project is None:project=store.create_project('Mochi · organischer Hals · 500 mm',Settings(height_mm=500,mesh_provider='local').model_dump())
    dest=store.project_dir(project['id'])/'saved-prints';dest.mkdir(exist_ok=True)
    def put(source,name=None):
        target=dest/(name or source.name)
        if target.exists():assert sha(target)==sha(source),'Immutable archive file changed'
        else:shutil.copyfile(source,target)
        return 'saved-prints/'+target.name
    files=[{'path':put(file),'label':'500 mm · Kopf + Rumpf + Schwarzteile','primary':True,'note':'Ein natives Projekt, drei Platten. Ca. 63 h 31 min / 1,119 kg. Rumpf belegt den gemeinsamen Düsenbereich eng.'},
        {'path':put(small/'Mochi-470mm-Hals-geteilt-3-Platten.3mf'),'label':'470 mm · Alternative mit mehr Bauraumreserve','note':'Gleiche Verbindung und Bemalung. Drei Platten, ca. 56 h 39 min / 974 g.'},
        {'path':put(small/'fit-probe-two-plates/Mochi-Hals-Passungsprobe.3mf'),'label':'Zuerst Hals-Passungsprobe drucken','note':'Zwei kleine Prüfplatten, ca. 1 h 58 min / 57,35 g. Gleicher Schlüssel, gleiche Aufnahmen, Materialien und Schichthöhen wie an beiden Großversionen.'},
        {'path':put(Path('docs/MOCHI_NECK_SPLIT.md'),'Montage-und-Druckhinweise.md'),'label':'Montage und Druckhinweise','note':'Organische Halsfuge, abnehmbarer Kopf, Steckmaße, Grenzen und Bestandsfilamente.'},
        {'path':put(Path('docs/mochi-neck-split-verification.json')),'label':'Technische Prüfnachweise','note':'Tatsächliche Projekt-/G-Code-Hashes, Werkzeugwege, Geometrie, Quellbemalung und native Speichertests.'}]
    archive={'source_sha256':digest,'height_mm':500,'parts':8,'plates':3,'preview':put(large/'Mochi-Hals-Geometriepruefung.png'),'preview_kind':'comparison','preview_label':'Geometrieprüfung · Bauteil-Kennfarben','preview_description':'Vorn, seitlich und Kopf abgehoben; Kennfarben zeigen die getrennten Bauteile.','preview_note':'Hellblau = Kopf, Braun = Rumpf, Lime = loser Halsverbinder. Keine Filamentvorschau: Die 3MF erhält Richards Braun-/Beige-Bemalung.','files':files,'body_printed':False,'black_printed':False,'note':'Neue Halskonstruktion: geschwungene äußere Halsfuge, breite innere Kopfauflage und separater asymmetrischer Schlüssel. Alle Platten digital geprüft. Reale Passung zuerst mit der Probe testen; frühere Mochi-Projekte bleiben erhalten.','parent_project_id':'dd9d3c92b8cd4b478aaa375db11acc99'}
    store.mutate(project['id'],lambda p:p['artifacts'].update(saved_prints=archive),require_idle=True)
    store.event(project['id'],'neck-archive','Neue organische Halskonstruktion 500/470 mm gesichert; acht Teile, drei Platten, massive separate Schlüssel, reale Passungsprobe offen. Originale unverändert; kein Druckstart.')
    report={'project_id':project['id'],'title':project['title'],'project_file_sha256':digest,'archive':archive,'file_sha256':{row['path']:sha(store.project_dir(project['id'])/row['path']) for row in files}}
    Path('docs/mochi-neck-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'project_id':project['id'],'files':len(files)}))

if __name__=='__main__':main()
