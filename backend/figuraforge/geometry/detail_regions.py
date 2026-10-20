"""Validated, bounded detail masks for a future region-aware simplifier.

Weights preserve more *existing* geometry in selected areas. They do not create
new detail, change topology or perform decimation. Coordinates use the loaded
surface's millimetre coordinate system; face IDs must remain tied to its hash.
"""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class DetailRegion:
    center: tuple[float, float, float]
    radius_mm: float
    importance: float = 4.0

    def __post_init__(self):
        c=np.asarray(self.center,dtype=float)
        if c.shape!=(3,) or not np.isfinite(c).all():
            raise ValueError('Detail center must contain three finite coordinates')
        if not np.isfinite(self.radius_mm) or self.radius_mm<=0:
            raise ValueError('Detail radius must be finite and positive')
        if not np.isfinite(self.importance) or not 1<=self.importance<=100:
            raise ValueError('Detail importance must be between 1 and 100')


def vertex_importance(vertices, regions):
    """Smooth brush weights; overlapping strokes use maximum, not addition."""
    points=np.asarray(vertices,dtype=float)
    if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():
        raise ValueError('Vertices must be a finite N by 3 array')
    weights=np.ones(len(points))
    for region in regions:
        t=np.clip(1-np.linalg.norm(points-region.center,axis=1)/region.radius_mm,0,1)
        influence=t*t*(3-2*t)
        weights=np.maximum(weights,1+(region.importance-1)*influence)
    return weights


def allocate_face_budget(face_counts, importance, total_budget):
    """Allocate integer retained-face targets for disjoint surface regions.

    Water filling caps each region at its original count, so protecting a tiny
    eye cannot consume impossible triangles. Every nonempty region retains at
    least one face. These targets are *planning*, not a topological guarantee:
    a real simplifier must verify its actual total and refuse an overshoot.
    """
    raw=np.asarray(face_counts)
    weights=np.asarray(importance,dtype=float)
    if raw.ndim!=1 or (raw.size and not np.issubdtype(raw.dtype,np.integer)) or (raw<0).any():
        raise ValueError('Face counts must be a one-dimensional integer array')
    counts=raw.astype(np.int64)
    if weights.shape!=counts.shape or not np.isfinite(weights).all() or (weights<=0).any():
        raise ValueError('Importance must contain one finite positive weight per region')
    if isinstance(total_budget,bool) or not isinstance(total_budget,(int,np.integer)) or total_budget<0:
        raise ValueError('Total budget must be a nonnegative integer')
    target=min(int(total_budget),int(counts.sum()))
    allocation=(counts>0).astype(np.int64)
    if int(allocation.sum())>target:
        raise ValueError('Budget cannot retain at least one face in every nonempty region')
    remaining=target-int(allocation.sum())
    while remaining:
        capacity=counts-allocation;active=capacity>0
        score=counts[active].astype(float)*weights[active]
        score/=score.max()
        desired=remaining*score/score.sum()
        quota=np.minimum(capacity[active],np.floor(desired).astype(np.int64))
        indices=np.flatnonzero(active)
        allocation[indices]+=quota
        remaining-=int(quota.sum())
        if not remaining:break
        if quota.sum()==0:
            # Largest remainders; original index breaks ties deterministically.
            order=np.argsort(-desired,kind='stable')
            take=indices[order[:remaining]]
            allocation[take]+=1
            remaining-=len(take)
    return allocation
