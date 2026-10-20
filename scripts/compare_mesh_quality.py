"""Deterministic sampled geometry/albedo comparison of two local textured meshes."""
from pathlib import Path
import argparse
import json
import sys
import time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from figuraforge.geometry.io import load_surface
from figuraforge.geometry.types import Surface
from figuraforge.geometry.validation import to_vtk,validate_mesh
from figuraforge.geometry.colors import delta_e_2000,srgb_to_lab,choose_palette,classify


from figuraforge.geometry.compare import compare


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('original');parser.add_argument('working');parser.add_argument('--height',type=float,default=1000)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    report=compare(args.original,args.working,args.height)
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
