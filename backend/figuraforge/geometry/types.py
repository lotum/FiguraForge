from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import numpy as np
import trimesh


class GeometryError(ValueError):
    """A failed geometric precondition; never silently export a broken part."""


@dataclass
class Surface:
    mesh: trimesh.Trimesh
    corner_uv: np.ndarray
    corner_rgb: np.ndarray
    material_ids: np.ndarray
    textures: list[Any] = field(default_factory=list)
    factors: list[np.ndarray] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    face_tags: np.ndarray | None = None

    def sample(self, bary: np.ndarray | None = None) -> np.ndarray:
        """Sample sRGB albedo. Normal/roughness maps are deliberately excluded."""
        if bary is None:
            bary = np.array([1/3, 1/3, 1/3])
        bary = np.asarray(bary, dtype=float)
        uv = np.einsum('fvc,v->fc', self.corner_uv, bary)
        result = np.einsum('fvc,v->fc', self.corner_rgb, bary).copy()
        for mat_id, image in enumerate(self.textures):
            if image is None:
                continue
            mask = self.material_ids == mat_id
            if not mask.any():
                continue
            # Keep large textures as uint8; promote only the sampled texels, not the entire 8K image.
            a = np.asarray(image if image.mode == 'RGB' else image.convert('RGB'))
            coords = uv[mask].copy()
            # GLB sampler support: repeat outside [0, 1], retain exact boundary.
            coords = np.where((coords < 0) | (coords > 1), coords % 1, coords)
            x = coords[:, 0] * (a.shape[1] - 1)
            y = (1 - coords[:, 1]) * (a.shape[0] - 1)
            x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
            x1, y1 = np.minimum(x0+1, a.shape[1]-1), np.minimum(y0+1, a.shape[0]-1)
            wx, wy = (x-x0)[:, None], (y-y0)[:, None]
            rgb = ((1-wx)*(1-wy)*a[y0,x0] + wx*(1-wy)*a[y0,x1]
                   + (1-wx)*wy*a[y1,x0] + wx*wy*a[y1,x1]) / 255
            factor = self.factors[mat_id][:3] if mat_id < len(self.factors) else np.ones(3)
            # glTF baseColorFactor is linear, unlike the texture's sRGB.
            lin = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
            lin *= factor
            result[mask] = np.where(lin <= .0031308, 12.92*lin,
                                    1.055*np.maximum(lin, 0)**(1/2.4)-.055)
        return np.clip(result, 0, 1)


@dataclass
class Part:
    id: str
    name: str
    mesh: trimesh.Trimesh
    color: str
    color_index: int = 0
    role: str = 'inlay'
    assembly_direction: list[float] | None = None
    connectors: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    filament_id: str | None = None

    def summary(self) -> dict:
        return {
            'id': self.id, 'name': self.name, 'color': self.color,
            'color_index': self.color_index, 'role': self.role,
            'dimensions_mm': np.round(self.mesh.extents, 3).tolist(),
            'bounds_mm': np.round(self.mesh.bounds, 3).tolist(),
            'volume_mm3': round(abs(float(self.mesh.volume)), 3),
            'faces': len(self.mesh.faces), 'watertight': bool(self.mesh.is_watertight),
            'winding_consistent': bool(self.mesh.is_winding_consistent),
            'assembly_direction': self.assembly_direction,
            'connectors': self.connectors, 'warnings': self.warnings,
            'filament_id': self.filament_id,
        }

    def save(self, directory: Path) -> dict:
        directory.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(directory / f'{self.id}.npz',
                            vertices=np.asarray(self.mesh.vertices), faces=np.asarray(self.mesh.faces))
        return self.summary()


def load_part(directory: Path, item: dict) -> Part:
    with np.load(directory / f"{item['id']}.npz", allow_pickle=False) as a:
        mesh = trimesh.Trimesh(a['vertices'], a['faces'], process=False)
    return Part(id=item['id'], name=item['name'], mesh=mesh, color=item['color'],
                color_index=item.get('color_index', 0), role=item.get('role', 'inlay'),
                assembly_direction=item.get('assembly_direction'),
                connectors=item.get('connectors', []), warnings=item.get('warnings', []),
                filament_id=item.get('filament_id'))
