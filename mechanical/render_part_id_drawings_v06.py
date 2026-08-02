#!/usr/bin/env python3
"""Render current v0.7.3 technical views with stable printable-part identifiers."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
import trimesh

ROOT=Path(__file__).resolve().parent
REGISTRY=json.loads((ROOT/'part_id_registry_v06.json').read_text(encoding='utf-8'))
PART_IDS={item['name']:item['id'] for group in REGISTRY['groups'].values() for item in group}
ALIASES={
    'rotor_A':'rotor_half_A','rotor_B':'rotor_half_B','collar_A':'stationary_collar_A','collar_B':'stationary_collar_B',
    'lid':'service_lid','photo_retainer':'photo_window_retainer','env_pocket':'environment_sensor_pocket',
    'spoke_liner_A_split_face_down':'spoke_liner_A','spoke_liner_B_split_face_down':'spoke_liner_B',
    'flag_cable_grommet_A_split_face_down':'flag_cable_grommet_A','flag_cable_grommet_B_split_face_down':'flag_cable_grommet_B',
    'M125_bundle_grommet_A_split_face_down':'M125_bundle_grommet_A','M125_bundle_grommet_B_split_face_down':'M125_bundle_grommet_B',
    'M125_pole_sleeve_upright':'M125_pole_sleeve','pole_collar_liner_A_split_face_down':'pole_collar_liner_A',
    'pole_collar_liner_B_split_face_down':'pole_collar_liner_B','lid_gasket_flat':'lid_gasket',
    'photo_window_gasket_flat':'photo_window_gasket','environment_pocket_gasket_flat':'environment_pocket_gasket',
    'environment_membrane_gasket_flat':'environment_membrane_gasket',
    'flag_side_wire_guide_slit_up':'flag_side_wire_guide',
}

def canonical(name):
    name=ALIASES.get(name,name)
    for prefix in ('PETG_','TPU95_','TPU85_'):
        if name.startswith(prefix):
            name=name[len(prefix):]
    return ALIASES.get(name,name)

def color(name):
    value=canonical(name)
    if value.startswith(('rotor_','stationary_')) or value in ('service_lid','photo_tunnel','photo_window_retainer','environment_sensor_pocket'):
        return np.array([0.86,0.45,0.17])
    if value.startswith(('spoke_liner','flag_cable_grommet','M125_bundle_grommet','M125_pole_sleeve','pole_collar_liner','flag_side_wire_guide')):
        return np.array([0.38,0.42,0.46])
    if value.startswith(('lid_gasket','photo_window_gasket','environment_')):
        return np.array([0.52,0.56,0.60])
    return np.array([0.5,0.5,0.5])

def transformed_items(scene):
    result=[]
    for node in scene.graph.nodes_geometry:
        transform, geometry_name=scene.graph[node]
        mesh=scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        result.append((geometry_name,mesh))
    return result

def add_mesh(ax,mesh,name):
    faces=mesh.faces
    indices=np.linspace(0,len(faces)-1,min(len(faces),1600),dtype=int)
    triangles=mesh.vertices[faces[indices]]
    normals=mesh.face_normals[indices]
    light=np.array([-0.35,-0.55,0.75]); light/=np.linalg.norm(light)
    intensity=0.8+0.2*np.clip(normals@light,0,1)
    faces_color=np.clip(color(name)[None,:]*intensity[:,None],0,1)
    collection=Poly3DCollection(triangles,linewidths=0,zsort='average')
    collection.set_facecolors(np.column_stack([faces_color,np.ones(len(faces_color))]))
    collection.set_edgecolor('none')
    ax.add_collection3d(collection)

def equal_axes(ax,items):
    low=np.min([mesh.bounds[0] for _,mesh in items],axis=0)
    high=np.max([mesh.bounds[1] for _,mesh in items],axis=0)
    center=(low+high)/2
    span=max(high-low)*1.06
    ax.set_xlim(center[0]-span/2,center[0]+span/2)
    ax.set_ylim(center[1]-span/2,center[1]+span/2)
    ax.set_zlim(center[2]-span/2,center[2]+span/2)
    ax.set_box_aspect((1,1,1))

def project(ax,figure,point):
    x2,y2,_=proj3d.proj_transform(*point,ax.get_proj())
    pixel=ax.transData.transform((x2,y2))
    return figure.transFigure.inverted().transform(pixel)

def render(glb,output,title,elevation,azimuth):
    scene=trimesh.load(ROOT/glb,force='scene')
    items=transformed_items(scene)
    figure=plt.figure(figsize=(10,7),dpi=110,facecolor='#f2f4f5')
    ax=figure.add_subplot(111,projection='3d'); ax.set_facecolor('#f2f4f5'); ax.set_proj_type('ortho')
    for name,mesh in items:
        add_mesh(ax,mesh,name)
    equal_axes(ax,items)
    ax.view_init(elev=elevation,azim=azimuth)
    ax.set_axis_off(); ax.set_title(title,fontsize=14,pad=12)
    figure.canvas.draw()
    occupied=[]
    for name,mesh in items:
        identifier=PART_IDS.get(canonical(name))
        if not identifier:
            continue
        point=(mesh.bounds[0]+mesh.bounds[1])/2
        fx,fy=project(ax,figure,point)
        fx+=0.012; fy+=0.008
        for ox,oy in occupied:
            if abs(fx-ox)<0.045 and abs(fy-oy)<0.03:
                fy+=0.03
        occupied.append((fx,fy))
        figure.text(fx,fy,identifier,fontsize=8,color='black',ha='left',va='center',
                    bbox=dict(boxstyle='round,pad=0.22',facecolor='white',edgecolor='#444',alpha=0.95))
    figure.savefig(ROOT/output,bbox_inches='tight',facecolor='#f2f4f5')
    plt.close(figure)

if __name__=='__main__':
    render('flagpole_finial_v0_6_exploded.glb','preview_v06_exploded_PETG_TPU_ids.png','Разнесённый вид v0.7.3 с ID деталей',25,-57)
    render('flagpole_finial_v0_6_print_layout_PETG.glb','preview_v06_print_PETG_ids.png','Раскладка деталей PETG v0.7.3 с ID',58,-50)
    render('flagpole_finial_v0_6_print_layout_TPU95.glb','preview_v06_print_TPU95_ids.png','Раскладка деталей TPU 95A v0.7.3 с ID',58,-50)
    render('flagpole_finial_v0_6_print_layout_TPU85.glb','preview_v06_print_TPU85_ids.png','Раскладка деталей TPU 85A v0.7.3 с ID',58,-50)
