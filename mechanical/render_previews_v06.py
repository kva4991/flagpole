#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.colors import to_rgb
import trimesh

ROOT=Path(__file__).resolve().parent

DEFAULT_COLORS=['#ed7428','#f59443','#9ca6ad','#d95b17','#8a949c','#2d3339','#3e8b66','#455f9c']

def transformed_meshes(scene):
    dumped=scene.dump(concatenate=False)
    return [m for m in dumped if isinstance(m,trimesh.Trimesh) and len(m.faces)]

def mesh_color(mesh,index):
    try:
        c=np.array(mesh.visual.main_color,dtype=float)[:3]/255.0
        if np.all(c>0.90): return np.array(to_rgb('#9ca6ad'))
        return c
    except Exception:
        return np.array(to_rgb(DEFAULT_COLORS[index%len(DEFAULT_COLORS)]))

def add_mesh(ax,mesh,index,max_faces=3000):
    faces=mesh.faces
    if len(faces)>max_faces:
        # deterministic sample across the full face array
        idx=np.linspace(0,len(faces)-1,max_faces,dtype=int)
        tri=mesh.vertices[faces[idx]]
        normals=mesh.face_normals[idx]
    else:
        tri=mesh.triangles
        normals=mesh.face_normals
    light=np.array([-0.35,-0.55,0.75]); light/=np.linalg.norm(light)
    diffuse=np.clip(normals@light,0,1)
    intensity=0.45+0.55*diffuse
    base=mesh_color(mesh,index)
    fc=np.clip(base[None,:]*intensity[:,None],0,1)
    coll=Poly3DCollection(tri,linewidths=0,zsort='average')
    coll.set_facecolors(np.column_stack([fc,np.ones(len(fc))]))
    coll.set_edgecolor('none')
    ax.add_collection3d(coll)

def equal_axes(ax,meshes,pad=.08):
    lo=np.min([m.bounds[0] for m in meshes],axis=0)
    hi=np.max([m.bounds[1] for m in meshes],axis=0)
    c=(lo+hi)/2
    span=max(hi-lo)*(1+pad)
    ax.set_xlim(c[0]-span/2,c[0]+span/2)
    ax.set_ylim(c[1]-span/2,c[1]+span/2)
    ax.set_zlim(c[2]-span/2,c[2]+span/2)
    ax.set_box_aspect((1,1,1))

def render(glb,out,title,elev,azim):
    scene=trimesh.load(ROOT/glb,force='scene')
    meshes=transformed_meshes(scene)
    fig=plt.figure(figsize=(12,8),dpi=120,facecolor='#f2f4f5')
    ax=fig.add_subplot(111,projection='3d'); ax.set_facecolor('#f2f4f5')
    ax.set_proj_type('ortho')
    for i,m in enumerate(meshes): add_mesh(ax,m,i)
    equal_axes(ax,meshes)
    ax.view_init(elev=elev,azim=azim)
    ax.set_axis_off()
    ax.set_title(title,fontsize=15,pad=15)
    fig.tight_layout()
    fig.savefig(ROOT/out,bbox_inches='tight',facecolor='#f2f4f5')
    plt.close(fig)

if __name__=='__main__':
    render('flagpole_finial_v0_6_assembly.glb','preview_v06_assembly.png','Общий вид сборки v0.6',23,-55)
    render('flagpole_finial_v0_6_exploded.glb','preview_v06_exploded_PETG_TPU.png','Разнесённый вид v0.6: PETG, TPU 95A и TPU 85A',25,-57)
    render('flagpole_finial_v0_6_print_layout_PETG.glb','preview_v06_print_PETG.png','Раскладка деталей PETG v0.6',58,-50)
    render('flagpole_finial_v0_6_print_layout_TPU95.glb','preview_v06_print_TPU95.png','Раскладка деталей TPU 95A v0.6',58,-50)
    render('flagpole_finial_v0_6_print_layout_TPU85.glb','preview_v06_print_TPU85.png','Раскладка деталей TPU 85A v0.6',58,-50)
