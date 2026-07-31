#!/usr/bin/env python3
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import trimesh

from generate_models_v05 import (
    P, rotor_full_sdf, lid_sdf, photo_tunnel_sdf, stationary_collar_full_sdf,
    spoke_liner_full_sdf, flag_cable_grommet_full_sdf, bundle_grommet_full_sdf,
    lid_gasket_sdf, m125_sleeve_sdf_factory, pole_liner_full_sdf,
    split_positive_y, split_negative_y, make_mesh_from_sdf,
    rot_x, put_on_bed, create_references,
)

ROOT=Path(__file__).resolve().parent
ORANGE='#ed7428'
ORANGE2='#f59443'
ORANGE_DARK='#d95b17'
WHITE='#f5f5ef'
GREY='#8a949c'
DARK='#2d3339'
GREEN='#3e8b66'
BLUE='#455f9c'


def lowres_parts():
    rotor_bounds=((-76,76),(-24,24),(-10,77))
    lid_bounds=((-77,-5),(-24,24),(45,57))
    photo_bounds=((-9,9),(-9,9),(-1,29))
    collar_bounds=((-18,18),(-18,18),(-3,16))
    spoke_bounds=((13,68),(-7,7),(21,33))
    flag_grommet_bounds=((53,74),(-8,8),(33,48))
    bundle_grommet_bounds=((-24,-9),(-7,7),(40,54))
    gasket_bounds=((-74,-8),(-22,22),(-1,4))
    sleeve_bounds=((-11,11),(-11,11),(-1,19))
    pole_liner_bounds=((-14,14),(-14,14),(-1,11))
    return {
        'rotor_a':make_mesh_from_sdf(split_positive_y(rotor_full_sdf),rotor_bounds,1.65,'ra'),
        'rotor_b':make_mesh_from_sdf(split_negative_y(rotor_full_sdf),rotor_bounds,1.65,'rb'),
        'lid':make_mesh_from_sdf(lid_sdf,lid_bounds,1.15,'lid'),
        'photo':make_mesh_from_sdf(photo_tunnel_sdf,photo_bounds,0.85,'photo'),
        'collar_a':make_mesh_from_sdf(split_positive_y(stationary_collar_full_sdf),collar_bounds,0.95,'ca'),
        'collar_b':make_mesh_from_sdf(split_negative_y(stationary_collar_full_sdf),collar_bounds,0.95,'cb'),
        'spoke_a':make_mesh_from_sdf(split_positive_y(spoke_liner_full_sdf),spoke_bounds,0.75,'sa'),
        'spoke_b':make_mesh_from_sdf(split_negative_y(spoke_liner_full_sdf),spoke_bounds,0.75,'sb'),
        'cable_a':make_mesh_from_sdf(split_positive_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,0.70,'ga'),
        'cable_b':make_mesh_from_sdf(split_negative_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,0.70,'gb'),
        'bundle_a':make_mesh_from_sdf(split_positive_y(bundle_grommet_full_sdf),bundle_grommet_bounds,0.65,'ba'),
        'bundle_b':make_mesh_from_sdf(split_negative_y(bundle_grommet_full_sdf),bundle_grommet_bounds,0.65,'bb'),
        'gasket':make_mesh_from_sdf(lid_gasket_sdf,gasket_bounds,0.75,'gasket'),
        'sleeve':make_mesh_from_sdf(m125_sleeve_sdf_factory(P.m125_sleeve_outer_diameter),sleeve_bounds,0.65,'sleeve'),
        'pole_liner_a':make_mesh_from_sdf(split_positive_y(pole_liner_full_sdf),pole_liner_bounds,0.65,'pla'),
        'pole_liner_b':make_mesh_from_sdf(split_negative_y(pole_liner_full_sdf),pole_liner_bounds,0.65,'plb'),
    }


def add_mesh_lit(ax,mesh,color,alpha=1.0):
    tri=mesh.triangles
    normals=mesh.face_normals
    light=np.array([-0.35,-0.55,0.75],dtype=float); light/=np.linalg.norm(light)
    diffuse=np.clip(normals@light,0,1)
    intensity=0.48+0.52*diffuse
    base=np.array(to_rgb(color),dtype=float)
    fc=np.clip(base[None,:]*intensity[:,None],0,1)
    rgba=np.column_stack([fc,np.full(len(fc),alpha)])
    coll=Poly3DCollection(tri,linewidths=0,zsort='average')
    coll.set_facecolors(rgba); coll.set_edgecolor('none')
    ax.add_collection3d(coll)


def equal_axes(ax,meshes,pad=0.06):
    lo=np.min([m.bounds[0] for m in meshes],axis=0)
    hi=np.max([m.bounds[1] for m in meshes],axis=0)
    c=(lo+hi)/2; span=max(hi-lo)*(1+pad)
    ax.set_xlim(c[0]-span/2,c[0]+span/2)
    ax.set_ylim(c[1]-span/2,c[1]+span/2)
    ax.set_zlim(c[2]-span/2,c[2]+span/2)
    ax.set_box_aspect((1,1,1))


def translated(m,xyz):
    o=m.copy(); o.apply_translation(xyz); return o


def assembly_preview(parts):
    fig=plt.figure(figsize=(13,9),dpi=170)
    ax=fig.add_subplot(111,projection='3d'); ax.set_proj_type('ortho')
    meshes=[]
    # One half is slightly transparent so internal white TPU inserts are visible.
    add_mesh_lit(ax,parts['rotor_a'],ORANGE,0.92); meshes.append(parts['rotor_a'])
    add_mesh_lit(ax,parts['rotor_b'],ORANGE2,0.38); meshes.append(parts['rotor_b'])
    add_mesh_lit(ax,parts['lid'],ORANGE_DARK,0.95); meshes.append(parts['lid'])
    photo=translated(parts['photo'],[P.photo_tunnel_center_x,0,P.lid_z_max])
    add_mesh_lit(ax,photo,ORANGE); meshes.append(photo)
    # TPU components in assembly coordinates.
    for key in ('spoke_a','spoke_b','cable_a','cable_b','bundle_a','bundle_b'):
        add_mesh_lit(ax,parts[key],WHITE,1.0); meshes.append(parts[key])
    gasket=translated(parts['gasket'],[0,0,49.65])
    add_mesh_lit(ax,gasket,WHITE); meshes.append(gasket)
    sleeve=translated(parts['sleeve'],[0,0,42])
    add_mesh_lit(ax,sleeve,WHITE); meshes.append(sleeve)
    for key in ('collar_a','collar_b'):
        m=translated(parts[key],[0,0,50]); add_mesh_lit(ax,m,ORANGE if key.endswith('a') else ORANGE2); meshes.append(m)
    for key in ('pole_liner_a','pole_liner_b'):
        m=translated(parts[key],[0,0,50]); add_mesh_lit(ax,m,WHITE); meshes.append(m)
    refs=create_references()
    for name,m in refs.items():
        if name=='REF_flag_300x250':
            continue
        if 'carbon' in name:
            # Short display rod so the finial remains readable in the preview.
            m=trimesh.creation.cylinder(radius=P.spoke_diameter/2,height=135,sections=32)
            m.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]))
            m.apply_translation([P.spoke_insert_x_min+67.5,0,P.spoke_center_z])
            c='#1f2428'; a=1
        elif 'hollow_pole' in name:
            m=trimesh.creation.annulus(r_min=P.pole_inner_diameter_provisional/2,r_max=P.pole_outer_diameter/2,height=85,sections=48)
            m.apply_translation([0,0,15.5])
            c=GREY; a=0.38
        elif 'bearing' in name: c=DARK; a=1
        elif 'spacer' in name or 'M125' in name: c='#a8adb2'; a=1
        elif 'buck' in name: c=GREEN; a=1
        elif 'ESP' in name: c='#b63232'; a=1
        else: c=BLUE; a=1
        add_mesh_lit(ax,m,c,a); meshes.append(m)
    equal_axes(ax,meshes,0.10)
    ax.view_init(elev=22,azim=-55); ax.set_axis_off()
    ax.set_title('Навершие v0.5: оранжевый PETG + удерживаемые белые TPU-вставки',fontsize=15,pad=16)
    fig.tight_layout(); fig.savefig(ROOT/'preview_v05_assembly.png',bbox_inches='tight'); plt.close(fig)


def exploded_preview(parts):
    fig=plt.figure(figsize=(14,10),dpi=170)
    ax=fig.add_subplot(111,projection='3d'); ax.set_proj_type('ortho')
    meshes=[]
    a=translated(parts['rotor_a'],[0,31,0]); b=translated(parts['rotor_b'],[0,-31,0])
    add_mesh_lit(ax,a,ORANGE); add_mesh_lit(ax,b,ORANGE2); meshes += [a,b]
    lid=translated(parts['lid'],[0,0,28]); add_mesh_lit(ax,lid,ORANGE_DARK); meshes.append(lid)
    photo=translated(parts['photo'],[P.photo_tunnel_center_x,0,P.lid_z_max+42]); add_mesh_lit(ax,photo,ORANGE); meshes.append(photo)
    gasket=translated(parts['gasket'],[0,0,68]); add_mesh_lit(ax,gasket,WHITE); meshes.append(gasket)
    # TPU halves follow their PETG half to show where they snap in.
    for key,dy in [('spoke_a',19),('cable_a',19),('bundle_a',19)]:
        m=translated(parts[key],[0,dy,0]); add_mesh_lit(ax,m,WHITE); meshes.append(m)
    for key,dy in [('spoke_b',-19),('cable_b',-19),('bundle_b',-19)]:
        m=translated(parts[key],[0,dy,0]); add_mesh_lit(ax,m,WHITE); meshes.append(m)
    ca=translated(parts['collar_a'],[0,25,50]); cb=translated(parts['collar_b'],[0,-25,50])
    add_mesh_lit(ax,ca,ORANGE); add_mesh_lit(ax,cb,ORANGE2); meshes += [ca,cb]
    pla=translated(parts['pole_liner_a'],[0,16,50]); plb=translated(parts['pole_liner_b'],[0,-16,50])
    add_mesh_lit(ax,pla,WHITE); add_mesh_lit(ax,plb,WHITE); meshes += [pla,plb]
    sl=translated(parts['sleeve'],[0,0,28]); add_mesh_lit(ax,sl,WHITE); meshes.append(sl)
    equal_axes(ax,meshes,0.10)
    ax.view_init(elev=24,azim=-57); ax.set_axis_off()
    ax.set_title('Разнесённый вид: TPU удерживается фланцами, ключами и пазами',fontsize=15,pad=16)
    fig.tight_layout(); fig.savefig(ROOT/'preview_v05_exploded_PETG_TPU.png',bbox_inches='tight'); plt.close(fig)


def print_layout_preview(parts,material):
    fig=plt.figure(figsize=(14,9),dpi=170)
    ax=fig.add_subplot(111,projection='3d'); ax.set_proj_type('ortho')
    meshes=[]
    if material=='PETG':
        items=[]
        for key,tr,pos,c in [
            ('rotor_a',rot_x(90),[0,0,0],ORANGE),
            ('rotor_b',rot_x(-90),[0,95,0],ORANGE2),
            ('lid',rot_x(180),[-95,0,0],ORANGE_DARK),
            ('collar_a',rot_x(90),[-95,62,0],ORANGE),
            ('collar_b',rot_x(-90),[-95,98,0],ORANGE2),
            ('photo',np.eye(4),[-130,65,0],ORANGE),
        ]:
            m=parts[key].copy(); m.apply_transform(tr); m=put_on_bed(m); m.apply_translation(pos)
            add_mesh_lit(ax,m,c); meshes.append(m)
        title='Ориентация деталей из PETG: плоскости разъёма на столе, крышка верхом вниз'
        out='preview_v05_print_PETG.png'
    else:
        keys=['spoke_a','spoke_b','cable_a','cable_b','bundle_a','bundle_b','gasket','sleeve','pole_liner_a','pole_liner_b']
        for i,key in enumerate(keys):
            m=parts[key].copy()
            if key.endswith('_a'): m.apply_transform(rot_x(90))
            elif key.endswith('_b'): m.apply_transform(rot_x(-90))
            m=put_on_bed(m); m.apply_translation([(i%4)*76,(i//4)*47,0])
            add_mesh_lit(ax,m,WHITE); meshes.append(m)
        title='Ориентация TPU 95A: прокладки плоско, втулка M125 вертикально'
        out='preview_v05_print_TPU.png'
    equal_axes(ax,meshes,0.05); ax.view_init(elev=58,azim=-50); ax.set_axis_off(); ax.set_title(title,fontsize=14,pad=16)
    fig.tight_layout(); fig.savefig(ROOT/out,bbox_inches='tight'); plt.close(fig)


def retention_diagram():
    fig,axs=plt.subplots(2,2,figsize=(14,10),dpi=180)
    fig.suptitle('Как белые TPU 95A-вставки удерживаются и почему не выпадают',fontsize=16,y=0.98)

    ax=axs[0,0]; ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(FancyBboxPatch((0,0),10,4,boxstyle='round,pad=0.2,rounding_size=0.6',fc=ORANGE,ec='#813610'))
    ax.add_patch(Rectangle((1.0,1.25),8.0,1.5,fc='white',ec='#555'))
    ax.add_patch(Rectangle((1.0,1.0),0.7,2.0,fc='white',ec='#555'))
    ax.add_patch(Rectangle((8.3,1.0),0.7,2.0,fc='white',ec='#555'))
    ax.add_patch(Rectangle((4.0,2.55),1.0,0.7,fc='white',ec='#555'))
    ax.text(5,-0.7,'Вкладыш углепластиковой спицы',ha='center',fontsize=12,fontweight='bold')
    ax.text(5,-1.35,'Фланцы блокируют сдвиг вдоль спицы;\nгибкие ключи входят в карманы каждой PETG-половины.',ha='center',fontsize=10)
    ax.set_xlim(-0.5,10.5); ax.set_ylim(-2.0,4.8)

    ax=axs[0,1]; ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((0,0),10,4,fc=ORANGE,ec='#813610'))
    ax.add_patch(Rectangle((2,1.2),6,1.6,fc='white',ec='#555'))
    ax.add_patch(Rectangle((1.2,0.8),1.0,2.4,fc='white',ec='#555'))
    ax.add_patch(Rectangle((7.8,0.8),1.0,2.4,fc='white',ec='#555'))
    ax.add_patch(Rectangle((2.2,1.75),5.6,0.5,fc='#222',ec='none'))
    ax.text(5,-0.7,'Разгрузочная втулка кабеля к флагу',ha='center',fontsize=12,fontweight='bold')
    ax.text(5,-1.35,'Два фланца заперты в ступенчатом канале.\nПосле стяжки корпуса втулка не может выйти наружу.',ha='center',fontsize=10)
    ax.set_xlim(-0.5,10.5); ax.set_ylim(-2.0,4.8)

    ax=axs[1,0]; ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(FancyBboxPatch((0,0),10,4,boxstyle='round,pad=0.2,rounding_size=0.5',fc=ORANGE_DARK,ec='#813610'))
    ax.add_patch(FancyBboxPatch((1,0.8),8,2.4,boxstyle='round,pad=0.1,rounding_size=0.4',fc='white',ec='#555'))
    ax.add_patch(FancyBboxPatch((1.7,1.35),6.6,1.3,boxstyle='round,pad=0.05,rounding_size=0.3',fc=ORANGE_DARK,ec='none'))
    for px,py in [(5,3.15),(5,0.85),(8.9,2),(1.1,2)]:
        ax.add_patch(Rectangle((px-0.35,py-0.25),0.7,0.5,fc='white',ec='#555'))
    ax.text(5,-0.7,'Прокладка сервисной крышки',ha='center',fontsize=12,fontweight='bold')
    ax.text(5,-1.35,'Лежит в пазу и имеет четыре фиксирующие лапки.\nДопустимы 4 маленькие точки нейтрального RTV на стороне крышки.',ha='center',fontsize=10)
    ax.set_xlim(-0.5,10.5); ax.set_ylim(-2.0,4.8)

    ax=axs[1,1]; ax.set_aspect('equal'); ax.axis('off')
    ax.add_patch(Rectangle((3.4,0),3.2,4,fc=GREY,ec='#4b545b'))
    ax.add_patch(Rectangle((3.9,0.4),2.2,3.2,fc='white',ec='#555'))
    ax.add_patch(Rectangle((3.4,3.3),3.2,0.7,fc='white',ec='#555'))
    ax.add_patch(Rectangle((2.8,3.6),4.4,1.2,fc=ORANGE,ec='#813610'))
    ax.add_patch(Rectangle((4.5,0.5),1.0,3.1,fc=DARK,ec='black'))
    ax.text(5,-0.7,'Втулка M125 внутри полого древка',ha='center',fontsize=12,fontweight='bold')
    ax.text(5,-1.35,'Верхний TPU-фланец зажат между торцом древка\nи неподвижным PETG-воротником: втулка не проваливается.',ha='center',fontsize=10)
    ax.set_xlim(0,10); ax.set_ylim(-2.0,5.2)

    fig.tight_layout(rect=[0,0,1,0.95]); fig.savefig(ROOT/'preview_v05_TPU_retention.png',bbox_inches='tight'); plt.close(fig)


def longitudinal_section():
    fig,ax=plt.subplots(figsize=(15,9),dpi=180)
    x=np.linspace(-78,92,1000,dtype=np.float32)[:,None]
    z=np.linspace(-12,82,800,dtype=np.float32)[None,:]
    y=np.full((1,1),0.9,dtype=np.float32)
    field=rotor_full_sdf(x,y,z)
    ax.contourf(x[:,0],z[0,:],field.T,levels=[-100,0],colors=[ORANGE])
    ax.contour(x[:,0],z[0,:],field.T,levels=[0],colors=['#813610'],linewidths=0.8)
    # Hollow pole
    ax.add_patch(Rectangle((-10,-10),20,P.pole_top_z+10,fc=GREY,ec='#4b545b',alpha=0.75))
    ax.add_patch(Rectangle((-P.pole_inner_diameter_provisional/2,-10),P.pole_inner_diameter_provisional,P.pole_top_z+10,fc='white',ec='none'))
    # Bearings
    for zc in (P.lower_bearing_center_z,P.upper_bearing_center_z):
        ax.add_patch(Rectangle((-16,zc-3.5),32,7,fc=DARK,ec='black'))
        ax.add_patch(Rectangle((-10,zc-3.5),20,7,fc=GREY,ec='none'))
    # TPU sleeve and M125
    ax.add_patch(Rectangle((-P.m125_sleeve_outer_diameter/2,42),P.m125_sleeve_outer_diameter,16,fc='white',ec='#666'))
    ax.add_patch(Rectangle((-P.m125_body_diameter/2,43),P.m125_body_diameter,13.5,fc='#555b62',ec='black'))
    # Carbon spoke and TPU liner
    ax.add_patch(Rectangle((P.spoke_insert_x_min,P.spoke_center_z-P.spoke_liner_outer_diameter/2),
                           P.spoke_insert_x_max-P.spoke_insert_x_min,P.spoke_liner_outer_diameter,
                           fc='white',ec='#666'))
    ax.add_patch(Rectangle((P.spoke_insert_x_min,P.spoke_center_z-P.spoke_diameter/2),
                           88-P.spoke_insert_x_min,P.spoke_diameter,fc='#22272b',ec='black'))
    # Lid gasket and lid note
    ax.annotate('электроника размещена\nс противоположной стороны флага',xy=(-44,31),xytext=(-72,72),
                arrowprops=dict(arrowstyle='->'),fontsize=11,ha='center')
    ax.annotate('TPU 95A вокруг спицы:\nравномерный зажим без точечного смятия',xy=(34,27),xytext=(48,64),
                arrowprops=dict(arrowstyle='->'),fontsize=10,ha='center')
    ax.annotate('M125 в белой TPU-втулке\nвнутри полого древка',xy=(0,51),xytext=(20,75),
                arrowprops=dict(arrowstyle='->'),fontsize=10,ha='left')
    ax.annotate('двойной подшипниковый узел',xy=(16,44),xytext=(42,46),
                arrowprops=dict(arrowstyle='->'),fontsize=10)
    ax.text(-74,9,'сервисная камера\nс отдельной крышкой\nи TPU-прокладкой',fontsize=10,va='center')
    ax.set_aspect('equal'); ax.set_xlim(-80,94); ax.set_ylim(-12,83); ax.axis('off')
    ax.set_title('Продольная схема v0.5: PETG несёт нагрузку, TPU только уплотняет и распределяет прижим',fontsize=15,pad=14)
    fig.tight_layout(); fig.savefig(ROOT/'preview_v05_longitudinal_section.png',bbox_inches='tight'); plt.close(fig)


if __name__=='__main__':
    parts=lowres_parts()
    assembly_preview(parts)
    exploded_preview(parts)
    print_layout_preview(parts,'PETG')
    print_layout_preview(parts,'TPU')
    retention_diagram()
    longitudinal_section()
