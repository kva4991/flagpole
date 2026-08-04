#!/usr/bin/env python3
"""Render only the canonical build123d exploded poster used by #204/#112."""
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageDraw
import trimesh


ROOT = Path(__file__).resolve().parent
JOBS = (
    ("flagpole_finial_v0_6_exploded.glb", "preview_v06_exploded_PETG_TPU.png"),
    ("flagpole_finial_v0_6_print_layout_PETG.glb", "preview_v06_print_PETG.png"),
    ("flagpole_finial_v0_6_print_layout_TPU95.glb", "preview_v06_print_TPU95.png"),
    ("flagpole_finial_v0_6_print_layout_TPU85.glb", "preview_v06_print_TPU85.png"),
)


def rotation_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(((1, 0, 0), (0, c, -s), (0, s, c)), dtype=float)


def rotation_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return np.array(((c, -s, 0), (s, c, 0), (0, 0, 1)), dtype=float)


for source_name, target_name in JOBS:
    scene = trimesh.load(ROOT / source_name, force="scene")
    mesh = scene.to_geometry()
    rotation = rotation_x(math.radians(63)) @ rotation_z(math.radians(-38))
    vertices = mesh.vertices @ rotation.T
    width, height, supersample = 1006, 940, 2
    canvas = Image.new("RGB", (width * supersample, height * supersample), (248, 250, 251))
    draw = ImageDraw.Draw(canvas)
    xy = vertices[:, :2]
    mins, maxs = xy.min(axis=0), xy.max(axis=0)
    span = np.maximum(maxs - mins, 1e-9)
    scale = min((width * 0.88) / span[0], (height * 0.84) / span[1]) * supersample
    projected = (xy - (mins + maxs) / 2) * scale
    projected[:, 0] += width * supersample / 2
    projected[:, 1] = height * supersample / 2 - projected[:, 1]
    light = np.array((-0.35, -0.45, 0.82), dtype=float)
    light /= np.linalg.norm(light)
    normals = mesh.face_normals @ rotation.T
    depth = vertices[mesh.faces, 2].mean(axis=1)
    base_colors = mesh.visual.face_colors[:, :3] if hasattr(mesh.visual, "face_colors") else np.tile((230, 116, 40), (len(mesh.faces), 1))
    for face_index in np.argsort(depth):
        face = mesh.faces[face_index]
        polygon = [tuple(projected[index]) for index in face]
        shade = 0.58 + 0.42 * max(0.0, float(np.dot(normals[face_index], light)))
        rgb = tuple(int(max(0, min(255, value * shade))) for value in base_colors[face_index])
        draw.polygon(polygon, fill=rgb)
    canvas.resize((width, height), Image.Resampling.LANCZOS).save(ROOT / target_name, optimize=True)
    print(f"Rendered {target_name} from canonical build123d geometry.")
