"""Run from Blender's Scripting workspace.

Imports the current v0.7.4 assembly (stable v0_6 filename retained for
compatibility) and saves a native .blend next to it.
"""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parent
source = root / "flagpole_finial_v0_6_assembly.glb"
target = root / "flagpole_finial_v0_7_3.blend"

if not source.exists():
    raise FileNotFoundError(f"Current assembly not found: {source}")

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print(f"Saved: {target}")
