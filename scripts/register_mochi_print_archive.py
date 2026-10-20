"""Add a NEW immutable Bambu print archive to FiguraForge; no mesh regeneration."""
from pathlib import Path
import argparse,hashlib,json,shutil,zipfile
from figuraforge.db import Store
from figuraforge.models import Settings


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source-root',type=Path,required=True);p.add_argument('--editions',type=Path);args=p.parse_args();root=args.source_root
    source=root/'Mochi-Richards-Anpassungen-180mm-ORIGINAL.3mf';digest=hashlib.sha256(source.read_bytes()).hexdigest();store=Store(Path('data'))
    current=next((r for r in store.list_projects() if r.get('artifacts',{}).get('saved_prints',{}).get('source_sha256')==digest),None)
    if current is None:
        current=store.create_project('Mochi · Richards Druckstand · 180 mm',Settings(mesh_provider='local',height_mm=180).model_dump())
    dest=store.project_dir(current['id'])/'saved-prints';dest.mkdir(exist_ok=True)
    def put(src):
        target=dest/src.name
        if target.exists():
            if hashlib.sha256(target.read_bytes()).digest()!=hashlib.sha256(src.read_bytes()).digest():raise ValueError('Archived file is immutable')
        else:shutil.copyfile(src,target)
        return 'saved-prints/'+target.name
    entries=[{'path':put(root/'fallback-korrigiert/Mochi-Richards-180mm-korrigierte-Details.3mf'),'label':'180 mm · deine Farben + korrekte schwarze Details','primary':True,'note':'Körperplatte und Druckeinstellungen erhalten; nur die fehlerhafte Nasengeometrie auf Platte 2 ersetzt.'},
        {'path':put(root/'fallback-korrigiert/Details-180mm.3mf'),'label':'180 mm · nur Nase und Augen','note':'Für den bereits gedruckten Körper. Fünf schwarze Teile, kein zusätzlicher Körper.'},
        {'path':put(source),'label':'Unveränderte Originaldatei sichern','note':'Original einschließlich deiner Änderungen. ACHTUNG: Platte 2 enthält die fehlerhafte Nasengeometrie; nur Platte 1 verwenden.'}]
    if args.editions:
        for height,mode,label in [(320,'zwei-Duesen','320 mm · zwei Düsen'),(325,'rechte-Duese','325 mm · rechte Düse / AMS-Farbwechsel')]:
            proofs=[json.loads((args.editions/f'slice-{height}-plate-{i}.json').read_text()) for i in (1,2)]
            if not all(p['passed'] for p in proofs):raise ValueError('Edition not sliced successfully')
            for i in (1,2):
                pathcheck=json.loads((args.editions/f'paths-{height}-plate-{i}.json').read_text())['checks'][0]
                if not pathcheck['passed'] or pathcheck['gcode_sha256']!=proofs[i-1]['gcode_sha256']:raise ValueError('Edition footprint proof missing or stale')
            entries.append({'path':put(args.editions/f'Mochi-{height}mm-{mode}-2-Platten.3mf'),'label':label,'note':'Neue Datei; schwarze Teile passend mitvergrößert auf Platte 2. Großversion ohne „No sparse layers“. Beide Platten lokal geslicet.'})
    archive={'source_sha256':digest,'height_mm':180,'parts':6,'plates':2,'preview':put(root/'Richards-Koerper-Vorschau.png'),'files':entries,'body_printed':True,'black_printed':False,'note':'Dein angepasster braun-beiger Körper ist gedruckt und als gut bestätigt. Schwarze Nase/Augen noch nicht gedruckt. Originaldatei bleibt erhalten; korrigierte und große Versionen sind zusätzliche Dateien.'}
    store.mutate(current['id'],lambda p:p['artifacts'].update(saved_prints=archive),require_idle=True)
    store.event(current['id'],'saved-print','Richards Bambu-Druckstand gesichert; Farbkorrekturen und Original erhalten. Korrekte schwarze Details separat hinterlegt; keine Neuberechnung oder Cloudaufrufe.')
    report={'project_id':current['id'],'title':current['title'],'archive':archive};(root/'figuraforge-archive.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({'project_id':current['id'],'files':len(entries)}))

if __name__=='__main__':main()
