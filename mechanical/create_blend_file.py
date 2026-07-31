"""Run from Blender's Scripting workspace.
Imports the v0.5 GLB assembly and saves a native .blend next to it.
"""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parent
source = root / "flagpole_finial_v0_5_assembly.glb"
target = root / "flagpole_finial_v0_5.blend"

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
bpy.ops.wm.save_as_mainfile(filepath=str(target))
print(f"Saved: {target}")
