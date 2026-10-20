"""Analysis-only anatomical seed cuts; output refers to untouched source faces.

This is a geometric proposal, never automatic semantic recognition or approval.
"""
from __future__ import annotations
import numpy as np
import trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import maximum_flow,breadth_first_order,dijkstra
from .types import GeometryError


def analysis_copy(mesh,iterations=30):
    if not isinstance(iterations,int) or not 0<=iterations<=200:raise GeometryError('Analysis smoothing requires 0..200 iterations')
    result=mesh.copy()
    if iterations:trimesh.smoothing.filter_taubin(result,lamb=.5,nu=.53,iterations=iterations)
    return result


def seed_geodesic_faces(mesh,seed_faces,distance_mm):
    seeds=np.asarray(seed_faces)
    if seeds.ndim!=1 or not np.issubdtype(seeds.dtype,np.integer) or not np.isfinite(distance_mm) or distance_mm<0:raise GeometryError('Integer seeds and nonnegative finite distance required')
    seeds=np.unique(seeds)
    if not len(seeds) or seeds.min()<0 or seeds.max()>=len(mesh.faces):raise GeometryError('Valid source face seeds required')
    edges=mesh.face_adjacency;centers=mesh.triangles_center
    weights=np.linalg.norm(centers[edges[:,0]]-centers[edges[:,1]],axis=1)
    graph=coo_matrix((np.r_[weights,weights],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(mesh.faces),)*2).tocsr()
    distances=dijkstra(graph,directed=False,indices=seeds,min_only=True,limit=distance_mm)
    return np.flatnonzero(distances<=distance_mm)


def anatomical_seed_cut(mesh,appendage_faces,core_faces,*,smoothing_iterations=30,concavity_scale=.08):
    """Minimum perimeter weighted toward concave creases on a smoothed copy.

    Seeds are human/domain hypotheses. No source positions, normals, colors or
    connectivity are modified. A returned set still needs contour, volume,
    collision and connector validation on the original mesh.
    """
    count=len(mesh.faces);source=np.asarray(appendage_faces);sink=np.asarray(core_faces)
    if source.ndim!=1 or sink.ndim!=1 or not np.issubdtype(source.dtype,np.integer) or not np.issubdtype(sink.dtype,np.integer):raise GeometryError('Integer face seed arrays required')
    source=np.unique(source);sink=np.unique(sink)
    if not len(source) or not len(sink) or min(source.min(),sink.min())<0 or max(source.max(),sink.max())>=count:
        raise GeometryError('Nonempty valid appendage and core seeds are required')
    if np.intersect1d(source,sink).size:raise GeometryError('Appendage and core seeds must be disjoint')
    if not np.isfinite(concavity_scale) or concavity_scale<=0:raise GeometryError('Concavity scale must be finite and positive')
    analysis=analysis_copy(mesh,smoothing_iterations);adj=analysis.face_adjacency
    edge_vertices=analysis.face_adjacency_edges
    length=np.linalg.norm(analysis.vertices[edge_vertices[:,0]]-analysis.vertices[edge_vertices[:,1]],axis=1)
    crease=np.where(analysis.face_adjacency_convex,0,analysis.face_adjacency_angles)
    weights=length*(.08+.92*np.exp(-crease/concavity_scale))
    capacity=np.maximum(1,np.rint(weights*1000)).astype(np.int64)
    infinite=int(capacity.sum()+1)
    if infinite>2**30:raise GeometryError('Anatomical cut graph exceeds bounded capacity budget')
    row=np.r_[adj[:,0],adj[:,1],np.full(len(source),count),sink]
    col=np.r_[adj[:,1],adj[:,0],source,np.full(len(sink),count+1)]
    values=np.r_[capacity,capacity,np.full(len(source),infinite),np.full(len(sink),infinite)]
    graph=coo_matrix((values,(row,col)),shape=(count+2,count+2)).tocsr()
    flow=maximum_flow(graph,count,count+1,method='dinic')
    residual=graph-flow.flow
    reachable=breadth_first_order((residual>0).tocsr(),count,directed=True,return_predecessors=False)
    selected=np.zeros(count,bool);selected[reachable[reachable<count]]=True
    if not selected[source].all() or selected[sink].any():raise GeometryError('Anatomical cut violated hard seeds')
    boundary=selected[adj[:,0]]!=selected[adj[:,1]]
    return np.flatnonzero(selected),{'method':'seeded face graph minimum cut on analysis-only Taubin copy',
        'source_faces':count,'selected_faces':int(selected.sum()),'appendage_seeds':len(source),'core_seeds':len(sink),
        'smoothing_iterations':smoothing_iterations,'concavity_scale':concavity_scale,
        'cut_edges':int(boundary.sum()),'source_cut_length_mm':float(np.linalg.norm(mesh.vertices[edge_vertices[boundary,0]]-mesh.vertices[edge_vertices[boundary,1]],axis=1).sum()),
        'weighted_cut_cost_mm':float(flow.flow_value)/1000,'original_geometry_modified':False,
        'limitation':'Seeded geometric proposal. Not autonomous anatomical recognition; source contours, solids, assembly and physical fit require separate validation.'}
