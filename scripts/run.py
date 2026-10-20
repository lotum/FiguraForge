"""Start a local, single-process checkout. No inference server/GPU is required."""
from pathlib import Path
import argparse,os,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from figuraforge.config import load_env

def main():
    parser=argparse.ArgumentParser(description='FiguraForge local web application')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--host',default='127.0.0.1')
    args=parser.parse_args();load_env(ROOT/'.env')
    if not 1<=args.port<=65535: parser.error('Port must be between 1 and 65535')
    if args.host not in ('127.0.0.1','::1','localhost') and not os.getenv('FORGE_API_TOKEN'):
        parser.error('Set FORGE_API_TOKEN before exposing the service beyond localhost')
    print(f'FiguraForge: http://{args.host}:{args.port} (Ctrl+C stops the server)',flush=True)
    import uvicorn
    # SQLite job ownership and in-process worker locks require exactly one process.
    uvicorn.run('figuraforge.app:app',host=args.host,port=args.port,workers=1)
if __name__=='__main__': main()
