#!/usr/bin/env python3
"""Render an annotated service view of the flag-power cable route."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits.mplot3d import proj3d
import trimesh

ROOT=Path(__file__).resolve().parent
COLORS={
    'PETG_rotor_half_A':'#dd762b','PETG_rotor_half_B':'#ef9041','PETG_service_lid':'#cc551b',
    'TPU95_flag_cable_grommet_A':'#727d84','TPU95_flag_cable_grommet_B':'#727d84',
    'TPU95_flag_side_wire_guide':'#8f989f',
    'REF_flag_power_cable_external_route':'#15191c','REF_waterproof_2pin_connector_provisional':'#4b5359',
    'REF_carbon_spoke_short':'#252b2f','REF_ESP32_C3_SuperMini':'#355c9a',
    'REF_buck_12_to_5':'#2f8f6b','REF_PC817_LR7843_module':'#b24a36',
}

def transformed(scene):
    result=[]
    for node in scene.graph.nodes_geometry:
        transform,name=scene.graph[node]
        mesh=scene.geometry[name].copy()
        mesh.apply_transform(transform)
        mesh.apply_scale(1000.0)  # GLB metres -> millimetres
        result.append((name,mesh))
    return result

def add_mesh(ax,name,mesh):
    faces=mesh.faces
    indices=np.linspace(0,len(faces)-1,min(len(faces),24000),dtype=int)
    triangles=mesh.vertices[faces[indices]]
    normals=mesh.face_normals[indices]
    light=np.array([-0.25,-0.45,0.86]); light/=np.linalg.norm(light)
    intensity=0.72+0.28*np.clip(normals@light,0,1)
    base=np.array(matplotlib.colors.to_rgb(COLORS.get(name,'#888888')))
    face_colors=np.clip(base[None,:]*intensity[:,None],0,1)
    collection=Poly3DCollection(triangles,linewidths=0,zsort='average')
    collection.set_facecolors(np.column_stack([face_colors,np.ones(len(face_colors))]))
    collection.set_edgecolor('none')
    ax.add_collection3d(collection)

def equal_axes(ax,items):
    low=np.min([mesh.bounds[0] for _,mesh in items],axis=0)
    high=np.max([mesh.bounds[1] for _,mesh in items],axis=0)
    center=(low+high)/2
    span=max(high-low)*1.12
    ax.set_xlim(center[0]-span/2,center[0]+span/2)
    ax.set_ylim(center[1]-span/2,center[1]+span/2)
    ax.set_zlim(center[2]-span/2,center[2]+span/2)
    ax.set_box_aspect((1,1,1))

def project(ax,fig,point):
    x,y,_=proj3d.proj_transform(*point,ax.get_proj())
    pixel=ax.transData.transform((x,y))
    return fig.transFigure.inverted().transform(pixel)

def render():
    scene=trimesh.load(ROOT/'flagpole_finial_v0_6_flag_power_route.glb',force='scene')
    items=transformed(scene)
    fig=plt.figure(figsize=(12,8),dpi=130,facecolor='#eef1f3')
    ax=fig.add_subplot(111,projection='3d'); ax.set_facecolor('#eef1f3'); ax.set_proj_type('ortho')
    for name,mesh in items:
        add_mesh(ax,name,mesh)
    equal_axes(ax,items)
    ax.view_init(elev=18,azim=-48)
    ax.set_axis_off()
    ax.set_title('Маршрут питания флага v0.7.3: два провода → защитные борта → электроника',fontsize=17,pad=20)
    fig.canvas.draw()

    callouts=[
        ((81,-12.5,10),'1. Герметичный 2-pin разъём\nпод спицей, рядом с флагом',(0.77,0.66)),
        ((69,-12.0,10),'2. PETG-кольцо и сменная\nнаправляющая #tpu95-10',(0.72,0.46)),
        ((22,-22.8,0.9),'3. Два провода Ø2 мм идут ниже гайки\nмежду бортами: 4,2 × 2,5 мм',(0.34,0.24)),
        ((-13,0,18),'4. #tpu95-3 / #tpu95-4\nна краю полукруга у бокса',(0.20,0.53)),
        ((-28,-5,22),'5. Внутри — короткая сервисная петля\nи разгрузка до клемм электроники',(0.18,0.76)),
    ]
    for point,text,text_pos in callouts:
        px,py=project(ax,fig,point)
        ax.annotate('',xy=(px,py),xytext=text_pos,xycoords=fig.transFigure,textcoords=fig.transFigure,
                    arrowprops=dict(arrowstyle='->',color='#263238',lw=1.4))
        fig.text(text_pos[0],text_pos[1],text,ha='left',va='center',fontsize=10.5,color='#172126',
                 bbox=dict(boxstyle='round,pad=0.35',facecolor='white',edgecolor='#6d7b82',alpha=0.96))

    fig.text(0.5,0.045,
             'Два провода не проходят через силовую втулку спицы и не пересекают подшипниковые посадки. '
             'Между защитными бортами они фиксируются съёмно: редкими точками нейтрального RTV или короткими TPU-ремешками.',
             ha='center',va='center',fontsize=10,color='#46565e')
    fig.savefig(ROOT/'preview_v06_flag_power_route.png',bbox_inches='tight',facecolor='#eef1f3')
    plt.close(fig)

if __name__=='__main__':
    render()
