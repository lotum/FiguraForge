from pathlib import Path
import argparse,sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from figuraforge.services.calibration import create_calibration
if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Generate physical pin/socket fit test pieces')
    parser.add_argument('--shape',choices=['round','keyed'],default='round')
    parser.add_argument('--radius',type=float,default=1.5)
    parser.add_argument('--length',type=float,default=4)
    parser.add_argument('--output',type=Path,default=ROOT/'benchmarks'/'calibration')
    args=parser.parse_args()
    if not .8<=args.radius<=12 or not 1<=args.length<=30: parser.error('Invalid radius or length')
    result=create_calibration(args.output,args.shape,args.radius,args.length)
    print(json.dumps({'file':str(args.output/result['bundle']),'parts':result['parts'],'plates':result['plates']},indent=2))
