from __future__ import annotations
import numpy as np
from scipy.spatial.distance import cdist


def hex_rgb(value: str) -> np.ndarray:
    s = value.removeprefix('#')
    if len(s) != 6:
        raise ValueError('Expected #RRGGBB')
    return np.array([int(s[i:i+2], 16) for i in (0,2,4)]) / 255.


def rgb_hex(rgb) -> str:
    return '#' + ''.join(f'{v:02X}' for v in np.rint(np.clip(rgb,0,1)*255).astype(int))


def srgb_to_lab(rgb) -> np.ndarray:
    """sRGB, D65, CIE 1931 2-degree standard observer."""
    rgb = np.asarray(rgb, dtype=float)
    lin = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    xyz = lin @ np.array([[.4124564,.3575761,.1804375],
                          [.2126729,.7151522,.0721750],
                          [.0193339,.1191920,.9503041]]).T
    xyz /= np.array([.95047, 1, 1.08883])
    d = 6/29
    f = np.where(xyz > d**3, np.cbrt(xyz), xyz/(3*d*d)+4/29)
    return np.stack([116*f[...,1]-16,500*(f[...,0]-f[...,1]),200*(f[...,1]-f[...,2])],axis=-1)


def delta_e_2000(lab1, lab2):
    """CIEDE2000 with kL=kC=kH=1; broadcast-compatible implementation."""
    a, b = np.broadcast_arrays(np.asarray(lab1, float), np.asarray(lab2, float))
    L1,a1,b1 = np.moveaxis(a,-1,0); L2,a2,b2 = np.moveaxis(b,-1,0)
    C1=np.hypot(a1,b1); C2=np.hypot(a2,b2); Cbar=(C1+C2)/2
    G=.5*(1-np.sqrt(Cbar**7/(Cbar**7+25**7)))
    ap1=(1+G)*a1; ap2=(1+G)*a2
    Cp1=np.hypot(ap1,b1); Cp2=np.hypot(ap2,b2)
    hp1=np.mod(np.degrees(np.arctan2(b1,ap1)),360)
    hp2=np.mod(np.degrees(np.arctan2(b2,ap2)),360)
    dLp=L2-L1; dCp=Cp2-Cp1
    dh=hp2-hp1
    dh=np.where(dh>180,dh-360,np.where(dh < -180, dh+360, dh))
    dh=np.where(Cp1*Cp2==0,0,dh)
    dHp=2*np.sqrt(Cp1*Cp2)*np.sin(np.radians(dh/2))
    Lp=(L1+L2)/2; Cp=(Cp1+Cp2)/2
    hp=np.where(np.abs(hp1-hp2)<=180,(hp1+hp2)/2,
                np.where(hp1+hp2<360,(hp1+hp2+360)/2,(hp1+hp2-360)/2))
    hp=np.where(Cp1*Cp2==0,hp1+hp2,hp)
    T=1-.17*np.cos(np.radians(hp-30))+.24*np.cos(np.radians(2*hp))+.32*np.cos(np.radians(3*hp+6))-.20*np.cos(np.radians(4*hp-63))
    Sl=1+.015*(Lp-50)**2/np.sqrt(20+(Lp-50)**2)
    Sc=1+.045*Cp; Sh=1+.015*Cp*T
    Rt=-2*np.sqrt(Cp**7/(Cp**7+25**7))*np.sin(np.radians(60*np.exp(-((hp-275)/25)**2)))
    x=dLp/Sl; y=dCp/Sc; z=dHp/Sh
    return np.sqrt(np.maximum(x*x+y*y+z*z+Rt*y*z,0))


def choose_palette(rgb: np.ndarray, count: int = 4, weights=None) -> list[str]:
    """Deterministic weighted k-means; not an AI semantic/material classifier."""
    if not 1 <= count <= 16:
        raise ValueError('Palette size must be 1..16')
    rgb=np.asarray(rgb)
    if len(rgb)>40000:
        idx=np.linspace(0,len(rgb)-1,40000,dtype=int)
        rgb=rgb[idx]; weights=None if weights is None else np.asarray(weights)[idx]
    lab=srgb_to_lab(rgb)
    weights=np.ones(len(lab)) if weights is None else np.maximum(weights,1e-12)
    first=np.argmin(np.linalg.norm(lab-np.average(lab,axis=0,weights=weights),axis=1))
    centers=[lab[first]]
    for _ in range(1,count):
        dist=cdist(lab,centers).min(axis=1)
        if dist.max()<2:
            break
        centers.append(lab[np.argmax(dist)])
    centers=np.array(centers)
    for _ in range(30):
        labels=cdist(lab,centers).argmin(axis=1)
        new=np.array([np.average(lab[labels==i],axis=0,weights=weights[labels==i])
                      if (labels==i).any() else centers[i] for i in range(len(centers))])
        if np.max(np.abs(new-centers)) < .02:
            centers=new; break
        centers=new
    labels=cdist(lab,centers).argmin(axis=1)
    order=sorted(range(len(centers)),key=lambda i: -weights[labels==i].sum())
    colors=[]
    for i in order:
        idx=np.flatnonzero(labels==i)
        if not len(idx): continue
        # Representative observed color avoids an invented average between materials.
        sample=idx[np.argmin(np.linalg.norm(lab[idx]-centers[i],axis=1))]
        value=rgb_hex(rgb[sample])
        if value not in colors: colors.append(value)
    return colors


def classify(rgb: np.ndarray, palette: list[str]) -> np.ndarray:
    return cdist(srgb_to_lab(rgb),srgb_to_lab([hex_rgb(v) for v in palette])).argmin(axis=1)
