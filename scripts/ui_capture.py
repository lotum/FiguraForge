"""Offline browser harness: execute shipped UI against the real localhost API.

The managed test browser restricts navigation; a narrowly scoped Python bridge
serves only our local app requests. No external navigation or remote content.
"""
from pathlib import Path
import re,json,base64
import httpx
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
BASE='http://127.0.0.1:8765'

def capture():
    html=(ROOT/'frontend/index.html').read_text()
    html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html)
    html=re.sub(r'<script[^>]*src=[^>]+></script>','',html)
    html=html.replace('</head>','<style>'+(ROOT/'frontend/style.css').read_text()+'</style></head>')
    js=(ROOT/'frontend/viewer.js').read_text().replace('export class Viewer','class Viewer')
    js+='\n'+(ROOT/'frontend/app.js').read_text().replace("import {Viewer} from './viewer.js';",'')
    out=ROOT/'screenshots';out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--enable-unsafe-swiftshader'])
        page=b.new_page(viewport={'width':1512,'height':982},device_scale_factor=1)
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        def local_fetch(source,path,options):
            if not str(path).startswith(('/api/','/session')): raise ValueError('Offline harness only allows local app API calls')
            headers=options.get('headers') or {}
            r=httpx.request(options.get('method','GET'),BASE+path,content=options.get('body'),headers=headers,timeout=30)
            return {'status':r.status_code,'statusText':r.reason_phrase,'body':r.text,'headers':dict(r.headers)}
        page.expose_binding('__localFetch',local_fetch)
        page.set_content(html,wait_until='domcontentloaded')
        page.add_script_tag(content="""
        Object.defineProperty(window,'localStorage',{value:{_data:{},getItem(k){return this._data[k]??null},setItem(k,v){this._data[k]=v}}});
        window.fetch=async(path,options={})=>{const r=await window.__localFetch(String(path),options);return new Response(r.body,{status:r.status,headers:r.headers})};
        """)
        page.add_script_tag(content=js)
        page.wait_for_function("document.querySelector('#metric-parts').textContent !== '-'")
        page.wait_for_timeout(1800)
        page.locator('[data-stage="segments"]').click();page.wait_for_timeout(300)
        page.screenshot(path=str(out/'construction.png'),full_page=True)
        page.locator('[data-mode="explode"]').click();page.wait_for_timeout(300)
        page.screenshot(path=str(out/'exploded.png'),full_page=True)
        page.locator('[data-mode="plates"]').click();page.wait_for_timeout(300)
        page.screenshot(path=str(out/'plates.png'),full_page=True)
        page.locator('[data-stage="colors"]').click();page.locator('[data-mode="assembly"]').click();page.wait_for_timeout(300)
        page.screenshot(path=str(out/'colors.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(300)
        page.screenshot(path=str(out/'mobile.png'),full_page=True)
        print(json.dumps({'browser_errors':errors,'parts':page.locator('#metric-parts').inner_text(),'screenshots':5},indent=2))
        (out/'ui-test.json').write_text(json.dumps({'browser_errors':errors,'mode':'offline UI bridge to real local HTTP API','screenshots':5},indent=2))
        b.close()
if __name__=='__main__':capture()
