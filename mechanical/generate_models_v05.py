#!/usr/bin/env python3
"""Generate flagpole finial v0.5 PETG + TPU concept models.

Design status
-------------
This is a parametric, printable concept updated for:
- orange PETG structural parts;
- white TPU 95A retained gaskets/liners;
- two 6804-2RS bearings around a provisional 20 mm pole;
- carbon spoke between the two bearings;
- M125/M125U miniature slip ring located inside a provisional hollow pole;
- electronics pod on the side opposite the flag;
- service lid with a captured TPU gasket;
- separate TPU cable grommets and carbon-rod liner.

Exact pole OD/ID, carbon rod OD, bearing fit and purchased module dimensions remain
provisional until measured. STL units are millimetres. GLB units are metres.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple
import json
import math

import numpy as np
from skimage import measure
import trimesh

ROOT = Path(__file__).resolve().parent
PETG_DIR = ROOT / "stl_petg"
TPU_DIR = ROOT / "stl_tpu"
COUPON_DIR = ROOT / "test_coupons"
for d in (PETG_DIR, TPU_DIR, COUPON_DIR):
    d.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Params:
    # Flag reference
    flag_width: float = 300.0
    flag_height: float = 250.0

    # Pole and miniature slip ring (provisional until measured)
    pole_outer_diameter: float = 20.0
    pole_inner_diameter_provisional: float = 16.0
    pole_top_z: float = 58.0
    m125_body_diameter: float = 12.5
    m125_body_length: float = 13.5
    m125_stem_diameter: float = 5.0
    m125_stem_length: float = 3.0

    # Bearings: 6804-2RS, 20 x 32 x 7 mm
    bearing_id: float = 20.0
    bearing_od: float = 32.0
    bearing_width: float = 7.0
    bearing_seat_diameter: float = 32.36
    lower_bearing_center_z: float = 10.0
    upper_bearing_center_z: float = 44.0
    lower_bearing_seat_width: float = 7.30
    upper_bearing_seat_width: float = 7.80

    # Stationary inner-race spacer reference
    inner_spacer_id: float = 20.30
    inner_spacer_od: float = 24.0
    inner_spacer_length: float = 27.0
    spacer_cavity_diameter: float = 24.80

    # Carbon rod and retained TPU liner
    spoke_diameter: float = 5.0
    spoke_liner_inner_diameter: float = 5.20
    spoke_liner_outer_diameter: float = 7.50
    spoke_liner_flange_diameter: float = 9.00
    spoke_insert_x_min: float = 15.0
    spoke_insert_x_max: float = 66.0
    spoke_center_z: float = 27.0
    spoke_visible_length: float = 310.0

    # Main PETG rotor envelope
    body_radius: float = 21.5
    body_z_min: float = 0.0
    body_z_max: float = 56.0
    tower_z_min: float = 52.0
    tower_z_max: float = 74.0
    tower_top_radius: float = 16.0
    tower_cavity_radius: float = 15.0
    skirt_radius: float = 23.0
    skirt_z_min: float = -8.0
    skirt_z_max: float = 10.0
    skirt_inner_radius: float = 16.8

    # Spoke arm
    arm_x_min: float = 8.0
    arm_x_max: float = 72.0
    arm_z_min: float = 14.0
    arm_z_max: float = 48.0
    arm_half_width: float = 12.5
    arm_corner_radius: float = 4.0
    clamp_gap_total: float = 0.70
    clamp_gap_x_min: float = 24.0

    # Cable exit to the flag; TPU split grommet is captured by two flanges
    flag_cable_inner_diameter: float = 4.4
    flag_cable_grommet_body_diameter: float = 9.4
    flag_cable_grommet_flange_diameter: float = 12.0
    flag_cable_center_z: float = 40.5
    flag_cable_x_min: float = 55.0
    flag_cable_x_max: float = 72.0

    # Electronics pod opposite the flag
    pod_x_min: float = -72.0
    pod_x_max: float = -10.0
    pod_y_half: float = 19.0
    pod_z_min: float = 12.0
    pod_z_max: float = 50.0
    pod_inner_x_min: float = -66.0
    pod_inner_x_max: float = -16.0
    pod_inner_y_half: float = 14.5
    pod_inner_z_min: float = 17.0
    pod_inner_z_max: float = 54.0

    # Service lid and TPU gasket
    lid_x_min: float = -74.0
    lid_x_max: float = -8.0
    lid_y_half: float = 21.0
    lid_z_min: float = 47.0
    lid_z_max: float = 54.5
    gasket_outer_x_half: float = 29.0
    gasket_outer_y_half: float = 17.0
    gasket_inner_x_half: float = 26.1
    gasket_inner_y_half: float = 14.1
    gasket_thickness: float = 1.80
    gasket_groove_depth: float = 1.45
    gasket_center_x: float = -41.0

    # Photo-sensor vertical tunnel, separate PETG insert
    photo_tunnel_body_diameter: float = 10.0
    photo_tunnel_flange_diameter: float = 15.0
    photo_tunnel_height: float = 26.0
    photo_tunnel_mount_hole_diameter: float = 10.6
    photo_tunnel_center_x: float = -50.0

    # Fasteners
    body_bolt_clearance_diameter: float = 4.5
    body_bolt_boss_diameter: float = 13.0
    body_bolt_boss_half_length: float = 14.0
    body_bolt_positions: Tuple[Tuple[float, float], ...] = (
        (-22.0, 10.0),
        (22.0, 10.0),
        (-22.0, 44.0),
        (22.0, 44.0),
        (-68.0, 22.0),
        (-68.0, 40.0),
    )
    clamp_bolt_positions: Tuple[Tuple[float, float], ...] = (
        (50.0, 19.0),
        (50.0, 35.0),
    )
    lid_screw_diameter: float = 3.5
    lid_screw_positions: Tuple[Tuple[float, float], ...] = (
        (-69.0, -16.5),
        (-69.0, 16.5),
        (-13.0, -16.5),
        (-13.0, 16.5),
    )

    # Stationary split collar and retained TPU pole liner
    collar_outer_diameter: float = 29.0
    collar_tpu_cavity_diameter: float = 21.9
    collar_height: float = 14.0
    collar_lower_height: float = 8.0
    collar_m125_hole_diameter: float = 13.3
    collar_bolt_diameter: float = 3.6
    pole_liner_inner_diameter: float = 20.10
    pole_liner_outer_diameter: float = 21.65
    pole_liner_flange_diameter: float = 24.0
    pole_liner_length: float = 8.0

    # M125 sleeve inside hollow pole. Three OD coupons are generated.
    m125_sleeve_inner_diameter: float = 12.70
    m125_sleeve_outer_diameter: float = 15.80
    m125_sleeve_length: float = 16.0
    m125_sleeve_flange_diameter: float = 19.0

    # TPU bundle grommet between central slip-ring cavity and electronics pod
    bundle_grommet_inner_diameter: float = 4.6
    bundle_grommet_body_diameter: float = 8.2
    bundle_grommet_flange_diameter: float = 10.6
    bundle_grommet_x_min: float = -22.0
    bundle_grommet_x_max: float = -11.0
    bundle_grommet_center_z: float = 47.0

    # Meshing
    rotor_voxel: float = 0.36
    part_voxel: float = 0.28
    tpu_voxel: float = 0.22
    coupon_voxel: float = 0.28


P = Params()


# ---------------------------------------------------------------------------
# Signed-distance primitives
# ---------------------------------------------------------------------------

def sd_cylinder_z(x, y, z, radius: float, z_min: float, z_max: float):
    radial = np.sqrt(x*x + y*y) - radius
    zc = (z_min + z_max) * 0.5
    zh = (z_max - z_min) * 0.5
    return np.maximum(radial, np.abs(z-zc)-zh)


def sd_frustum_z(x, y, z, radius_bottom: float, radius_top: float,
                 z_min: float, z_max: float):
    t = np.clip((z-z_min)/(z_max-z_min), 0.0, 1.0)
    radius = radius_bottom + (radius_top-radius_bottom)*t
    radial = np.sqrt(x*x + y*y) - radius
    axial = np.maximum(z_min-z, z-z_max)
    return np.maximum(radial, axial)


def sd_cylinder_x(x, y, z, radius: float, x_min: float, x_max: float,
                  cy: float = 0.0, cz: float = 0.0):
    radial = np.sqrt((y-cy)**2 + (z-cz)**2) - radius
    xc = (x_min+x_max)*0.5
    xh = (x_max-x_min)*0.5
    return np.maximum(radial, np.abs(x-xc)-xh)


def sd_cylinder_y(x, y, z, radius: float, y_min: float, y_max: float,
                  cx: float = 0.0, cz: float = 0.0):
    radial = np.sqrt((x-cx)**2 + (z-cz)**2) - radius
    yc = (y_min+y_max)*0.5
    yh = (y_max-y_min)*0.5
    return np.maximum(radial, np.abs(y-yc)-yh)


def sd_box(x, y, z, x_min, x_max, y_min, y_max, z_min, z_max):
    cx, cy, cz = (x_min+x_max)/2, (y_min+y_max)/2, (z_min+z_max)/2
    hx, hy, hz = (x_max-x_min)/2, (y_max-y_min)/2, (z_max-z_min)/2
    qx = np.abs(x-cx)-hx
    qy = np.abs(y-cy)-hy
    qz = np.abs(z-cz)-hz
    ox, oy, oz = np.maximum(qx,0), np.maximum(qy,0), np.maximum(qz,0)
    return np.sqrt(ox*ox+oy*oy+oz*oz) + np.minimum(np.maximum(qx,np.maximum(qy,qz)),0)


def sd_rounded_box(x, y, z, center, half_size, radius: float):
    cx, cy, cz = center
    hx, hy, hz = half_size
    qx = np.abs(x-cx) - (hx-radius)
    qy = np.abs(y-cy) - (hy-radius)
    qz = np.abs(z-cz) - (hz-radius)
    ox, oy, oz = np.maximum(qx,0), np.maximum(qy,0), np.maximum(qz,0)
    outside = np.sqrt(ox*ox+oy*oy+oz*oz)
    inside = np.minimum(np.maximum(qx,np.maximum(qy,qz)),0)
    return outside + inside - radius


def union(*fields):
    out = fields[0]
    for f in fields[1:]:
        out = np.minimum(out, f)
    return out


def subtract(solid, *holes):
    out = solid
    for h in holes:
        out = np.maximum(out, -h)
    return out


def intersection(*fields):
    out = fields[0]
    for f in fields[1:]:
        out = np.maximum(out, f)
    return out


def rounded_ring(outer, inner):
    return np.maximum(outer, -inner)


# ---------------------------------------------------------------------------
# Main PETG rotor
# ---------------------------------------------------------------------------

def rotor_full_sdf(x, y, z):
    body = sd_cylinder_z(x,y,z,P.body_radius,P.body_z_min,P.body_z_max)
    tower = sd_frustum_z(x,y,z,P.body_radius,P.tower_top_radius,
                         P.tower_z_min,P.tower_z_max)
    skirt = sd_cylinder_z(x,y,z,P.skirt_radius,P.skirt_z_min,P.skirt_z_max)
    arm = sd_rounded_box(
        x,y,z,
        center=((P.arm_x_min+P.arm_x_max)/2,0,(P.arm_z_min+P.arm_z_max)/2),
        half_size=((P.arm_x_max-P.arm_x_min)/2,P.arm_half_width,
                   (P.arm_z_max-P.arm_z_min)/2),
        radius=P.arm_corner_radius,
    )
    pod = sd_rounded_box(
        x,y,z,
        center=((P.pod_x_min+P.pod_x_max)/2,0,(P.pod_z_min+P.pod_z_max)/2),
        half_size=((P.pod_x_max-P.pod_x_min)/2,P.pod_y_half,
                   (P.pod_z_max-P.pod_z_min)/2),
        radius=5.0,
    )

    bosses = []
    for bx,bz in P.body_bolt_positions + P.clamp_bolt_positions:
        bosses.append(sd_cylinder_y(x,y,z,P.body_bolt_boss_diameter/2,
                                    -P.body_bolt_boss_half_length,
                                    P.body_bolt_boss_half_length,
                                    cx=bx,cz=bz))
    # Vertical lid screw towers in the pod walls.
    for sx,sy in P.lid_screw_positions:
        bosses.append(sd_cylinder_z(x-sx,y-sy,z,4.3,43.0,53.5))

    solid = union(body,tower,skirt,arm,pod,*bosses)

    lower_min = P.lower_bearing_center_z - P.lower_bearing_seat_width/2
    lower_max = P.lower_bearing_center_z + P.lower_bearing_seat_width/2
    upper_min = P.upper_bearing_center_z - P.upper_bearing_seat_width/2
    upper_max = P.upper_bearing_center_z + P.upper_bearing_seat_width/2

    holes = [
        # Lower non-contact labyrinth cavity.
        sd_cylinder_z(x,y,z,P.skirt_inner_radius,P.skirt_z_min-1,6.0),
        # Clearance around the pole; no PETG sliding on the pole.
        sd_cylinder_z(x,y,z,10.60,5.5,P.pole_top_z+0.5),
        # Bearing outer-ring seats.
        sd_cylinder_z(x,y,z,P.bearing_seat_diameter/2,lower_min,lower_max),
        sd_cylinder_z(x,y,z,P.bearing_seat_diameter/2,upper_min,upper_max),
        # Spacer cavity between inner rings.
        sd_cylinder_z(x,y,z,P.spacer_cavity_diameter/2,lower_max,upper_min),
        # Stationary collar and M125 cavity inside the rotating tower.
        sd_cylinder_z(x,y,z,P.tower_cavity_radius,51.5,P.tower_z_max-2.0),
        # TPU carbon-rod liner pocket and captured end flanges.
        sd_cylinder_x(x,y,z,P.spoke_liner_outer_diameter/2 + 0.18,
                      P.spoke_insert_x_min,P.spoke_insert_x_max,cz=P.spoke_center_z),
        sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2 + 0.18,
                      P.spoke_insert_x_min,P.spoke_insert_x_min+3.2,cz=P.spoke_center_z),
        sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2 + 0.18,
                      P.spoke_insert_x_max-3.2,P.spoke_insert_x_max,cz=P.spoke_center_z),
        # Clamp travel in arm only; main body keeps rigid PETG-to-PETG stops.
        sd_box(x,y,z,P.clamp_gap_x_min,P.arm_x_max+1,
               -P.clamp_gap_total/2,P.clamp_gap_total/2,
               P.arm_z_min-0.5,P.arm_z_max+0.5),
        # Captured flag-cable grommet pocket.
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_body_diameter/2+0.18,
                      P.flag_cable_x_min+2.7,P.flag_cable_x_max-3.0,
                      cz=P.flag_cable_center_z),
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2+0.18,
                      P.flag_cable_x_min,P.flag_cable_x_min+3.0,
                      cz=P.flag_cable_center_z),
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2+0.18,
                      P.flag_cable_x_max-3.0,P.flag_cable_x_max+0.5,
                      cz=P.flag_cable_center_z),
        # Electronics cavity, intentionally open at top.
        sd_rounded_box(
            x,y,z,
            center=((P.pod_inner_x_min+P.pod_inner_x_max)/2,0,
                    (P.pod_inner_z_min+P.pod_inner_z_max)/2),
            half_size=((P.pod_inner_x_max-P.pod_inner_x_min)/2,
                       P.pod_inner_y_half,
                       (P.pod_inner_z_max-P.pod_inner_z_min)/2),
            radius=3.0,
        ),
        # Captured TPU bundle grommet from M125 cavity to electronics pod.
        sd_cylinder_x(x,y,z,P.bundle_grommet_body_diameter/2+0.16,
                      P.bundle_grommet_x_min+2.0,P.bundle_grommet_x_max-2.0,
                      cz=P.bundle_grommet_center_z),
        sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2+0.16,
                      P.bundle_grommet_x_min,P.bundle_grommet_x_min+2.2,
                      cz=P.bundle_grommet_center_z),
        sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2+0.16,
                      P.bundle_grommet_x_max-2.2,P.bundle_grommet_x_max,
                      cz=P.bundle_grommet_center_z),
        # Drainage opening in the lower rotating skirt.
        sd_cylinder_x(x,y,z,1.5,16.0,24.0,cz=-3.0),
    ]

    # TPU liner snap-key pockets. The keys hold each half in its PETG half during service.
    for x0 in (30.0,53.0):
        holes.append(sd_box(x,y,z,x0-2.6,x0+2.6,3.25,6.20,
                            P.spoke_center_z-1.35,P.spoke_center_z+1.35))
        holes.append(sd_box(x,y,z,x0-2.6,x0+2.6,-6.20,-3.25,
                            P.spoke_center_z-1.35,P.spoke_center_z+1.35))
    # Cable grommet snap pockets.
    for x0 in (61.0,67.0):
        holes.append(sd_box(x,y,z,x0-1.9,x0+1.9,4.1,6.6,
                            P.flag_cable_center_z-1.2,P.flag_cable_center_z+1.2))
        holes.append(sd_box(x,y,z,x0-1.9,x0+1.9,-6.6,-4.1,
                            P.flag_cable_center_z-1.2,P.flag_cable_center_z+1.2))

    # Through-bolts.
    for bx,bz in P.body_bolt_positions + P.clamp_bolt_positions:
        holes.append(sd_cylinder_y(x,y,z,P.body_bolt_clearance_diameter/2,
                                   -17.5,17.5,cx=bx,cz=bz))
    # Lid screw holes.
    for sx,sy in P.lid_screw_positions:
        holes.append(sd_cylinder_z(x-sx,y-sy,z,P.lid_screw_diameter/2,42.0,55.5))

    return subtract(solid,*holes)


# ---------------------------------------------------------------------------
# PETG service lid and photo tunnel
# ---------------------------------------------------------------------------

def lid_sdf(x,y,z):
    cx = P.gasket_center_x
    # Top plate.
    plate = sd_rounded_box(
        x,y,z,
        center=(cx,0,(51.0+P.lid_z_max)/2),
        half_size=((P.lid_x_max-P.lid_x_min)/2,P.lid_y_half,
                   (P.lid_z_max-51.0)/2),
        radius=4.0,
    )
    # Downward rain lip around the pod wall.
    lip_outer = sd_rounded_box(x,y,z,center=(cx,0,49.0),
                               half_size=(32.5,20.5,3.0),radius=4.0)
    lip_inner = sd_rounded_box(x,y,z,center=(cx,0,48.8),
                               half_size=(29.6,17.6,3.8),radius=3.0)
    lip = rounded_ring(lip_outer,lip_inner)
    solid = union(plate,lip)

    groove_outer = sd_rounded_box(
        x,y,z,center=(cx,0,51.0+P.gasket_groove_depth/2),
        half_size=(P.gasket_outer_x_half+0.20,P.gasket_outer_y_half+0.20,
                   P.gasket_groove_depth/2),radius=3.0)
    groove_inner = sd_rounded_box(
        x,y,z,center=(cx,0,51.0+P.gasket_groove_depth/2),
        half_size=(P.gasket_inner_x_half-0.20,P.gasket_inner_y_half-0.20,
                   P.gasket_groove_depth),radius=2.5)
    groove = rounded_ring(groove_outer,groove_inner)

    holes = [groove,
             sd_cylinder_z(x-P.photo_tunnel_center_x,y,z,
                           P.photo_tunnel_mount_hole_diameter/2,48.0,56.0)]
    # Retention-tab pockets extend from the groove. TPU tabs can be secured with a
    # small spot of neutral RTV but cannot slide into the sealed opening.
    holes += [
        sd_box(x,y,z,cx-3,cx+3,P.gasket_outer_y_half-0.3,
               P.gasket_outer_y_half+3.0,50.9,52.6),
        sd_box(x,y,z,cx-3,cx+3,-P.gasket_outer_y_half-3.0,
               -P.gasket_outer_y_half+0.3,50.9,52.6),
        sd_box(x,y,z,cx+P.gasket_outer_x_half-0.3,
               cx+P.gasket_outer_x_half+3.0,-3,3,50.9,52.6),
        sd_box(x,y,z,cx-P.gasket_outer_x_half-3.0,
               cx-P.gasket_outer_x_half+0.3,-3,3,50.9,52.6),
    ]
    for sx,sy in P.lid_screw_positions:
        holes.append(sd_cylinder_z(x-sx,y-sy,z,P.lid_screw_diameter/2,46.0,56.0))
    return subtract(solid,*holes)


def photo_tunnel_sdf(x,y,z):
    outer = union(
        sd_cylinder_z(x,y,z,P.photo_tunnel_body_diameter/2,0,P.photo_tunnel_height),
        sd_cylinder_z(x,y,z,P.photo_tunnel_flange_diameter/2,0,2.2),
    )
    # Narrow field of view through two baffles. Local z=0 is at the lid surface.
    holes = [
        sd_cylinder_z(x,y,z,2.55,-1,8.0),
        sd_cylinder_z(x,y,z,1.95,8.0,9.2),
        sd_cylinder_z(x,y,z,2.55,9.2,17.0),
        sd_cylinder_z(x,y,z,1.75,17.0,18.2),
        sd_cylinder_z(x,y,z,2.55,18.2,P.photo_tunnel_height+1),
    ]
    return subtract(outer,*holes)


# ---------------------------------------------------------------------------
# PETG stationary split collar around pole top
# ---------------------------------------------------------------------------

def stationary_collar_full_sdf(x,y,z):
    outer = sd_cylinder_z(x,y,z,P.collar_outer_diameter/2,0,P.collar_height)
    bosses = [
        sd_cylinder_y(x,y,z,5.6,-17,17,cx=-11.0,cz=4.0),
        sd_cylinder_y(x,y,z,5.6,-17,17,cx=11.0,cz=4.0),
    ]
    solid = union(outer,*bosses)
    holes = [
        # Cavity for retained TPU liner around the outside of the pole.
        sd_cylinder_z(x,y,z,P.collar_tpu_cavity_diameter/2,-1,P.collar_lower_height+0.4),
        # Flange recess for TPU pole liner.
        sd_cylinder_z(x,y,z,P.pole_liner_flange_diameter/2+0.2,
                      P.collar_lower_height-1.1,P.collar_lower_height+1.6),
        # Central M125 passage through the top bridge.
        sd_cylinder_z(x,y,z,P.collar_m125_hole_diameter/2,
                      P.collar_lower_height-0.4,P.collar_height+1),
        sd_cylinder_y(x,y,z,P.collar_bolt_diameter/2,-18,18,cx=-11.0,cz=4.0),
        sd_cylinder_y(x,y,z,P.collar_bolt_diameter/2,-18,18,cx=11.0,cz=4.0),
    ]
    return subtract(solid,*holes)


# ---------------------------------------------------------------------------
# TPU retained parts
# ---------------------------------------------------------------------------

def spoke_liner_full_sdf(x,y,z):
    outer = sd_cylinder_x(x,y,z,P.spoke_liner_outer_diameter/2,
                          P.spoke_insert_x_min,P.spoke_insert_x_max,
                          cz=P.spoke_center_z)
    flange_a = sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2,
                             P.spoke_insert_x_min,P.spoke_insert_x_min+3.0,
                             cz=P.spoke_center_z)
    flange_b = sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2,
                             P.spoke_insert_x_max-3.0,P.spoke_insert_x_max,
                             cz=P.spoke_center_z)
    keys=[]
    for x0 in (30.0,53.0):
        keys.append(sd_box(x,y,z,x0-2.4,x0+2.4,3.45,5.85,
                           P.spoke_center_z-1.15,P.spoke_center_z+1.15))
        keys.append(sd_box(x,y,z,x0-2.4,x0+2.4,-5.85,-3.45,
                           P.spoke_center_z-1.15,P.spoke_center_z+1.15))
    solid=union(outer,flange_a,flange_b,*keys)
    inner=sd_cylinder_x(x,y,z,P.spoke_liner_inner_diameter/2,
                        P.spoke_insert_x_min-1,P.spoke_insert_x_max+1,
                        cz=P.spoke_center_z)
    return subtract(solid,inner)


def flag_cable_grommet_full_sdf(x,y,z):
    body=sd_cylinder_x(x,y,z,P.flag_cable_grommet_body_diameter/2,
                       P.flag_cable_x_min+2.8,P.flag_cable_x_max-3.0,
                       cz=P.flag_cable_center_z)
    fa=sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2,
                     P.flag_cable_x_min,P.flag_cable_x_min+3.0,
                     cz=P.flag_cable_center_z)
    fb=sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2,
                     P.flag_cable_x_max-3.0,P.flag_cable_x_max,
                     cz=P.flag_cable_center_z)
    keys=[]
    for x0 in (61.0,67.0):
        keys.append(sd_box(x,y,z,x0-1.7,x0+1.7,4.25,6.2,
                           P.flag_cable_center_z-1.0,P.flag_cable_center_z+1.0))
        keys.append(sd_box(x,y,z,x0-1.7,x0+1.7,-6.2,-4.25,
                           P.flag_cable_center_z-1.0,P.flag_cable_center_z+1.0))
    solid=union(body,fa,fb,*keys)
    inner=sd_cylinder_x(x,y,z,P.flag_cable_inner_diameter/2,
                        P.flag_cable_x_min-1,P.flag_cable_x_max+1,
                        cz=P.flag_cable_center_z)
    return subtract(solid,inner)


def bundle_grommet_full_sdf(x,y,z):
    body=sd_cylinder_x(x,y,z,P.bundle_grommet_body_diameter/2,
                       P.bundle_grommet_x_min+2.0,P.bundle_grommet_x_max-2.0,
                       cz=P.bundle_grommet_center_z)
    fa=sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2,
                     P.bundle_grommet_x_min,P.bundle_grommet_x_min+2.2,
                     cz=P.bundle_grommet_center_z)
    fb=sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2,
                     P.bundle_grommet_x_max-2.2,P.bundle_grommet_x_max,
                     cz=P.bundle_grommet_center_z)
    solid=union(body,fa,fb)
    inner=sd_cylinder_x(x,y,z,P.bundle_grommet_inner_diameter/2,
                        P.bundle_grommet_x_min-1,P.bundle_grommet_x_max+1,
                        cz=P.bundle_grommet_center_z)
    return subtract(solid,inner)


def lid_gasket_sdf(x,y,z):
    cx=P.gasket_center_x
    outer=sd_rounded_box(x,y,z,center=(cx,0,P.gasket_thickness/2),
                         half_size=(P.gasket_outer_x_half,P.gasket_outer_y_half,
                                    P.gasket_thickness/2),radius=3.0)
    inner=sd_rounded_box(x,y,z,center=(cx,0,P.gasket_thickness/2),
                         half_size=(P.gasket_inner_x_half,P.gasket_inner_y_half,
                                    P.gasket_thickness),radius=2.5)
    ring=rounded_ring(outer,inner)
    tabs=[
        sd_box(x,y,z,cx-2.8,cx+2.8,P.gasket_outer_y_half-1.2,
               P.gasket_outer_y_half+2.7,0,P.gasket_thickness),
        sd_box(x,y,z,cx-2.8,cx+2.8,-P.gasket_outer_y_half-2.7,
               -P.gasket_outer_y_half+1.2,0,P.gasket_thickness),
        sd_box(x,y,z,cx+P.gasket_outer_x_half-1.2,
               cx+P.gasket_outer_x_half+2.7,-2.8,2.8,0,P.gasket_thickness),
        sd_box(x,y,z,cx-P.gasket_outer_x_half-2.7,
               cx-P.gasket_outer_x_half+1.2,-2.8,2.8,0,P.gasket_thickness),
    ]
    return union(ring,*tabs)


def m125_sleeve_sdf_factory(outer_diameter: float):
    def sdf(x,y,z):
        body=sd_cylinder_z(x,y,z,outer_diameter/2,0,P.m125_sleeve_length)
        flange=sd_cylinder_z(x,y,z,P.m125_sleeve_flange_diameter/2,
                             P.m125_sleeve_length-2.0,P.m125_sleeve_length+1.0)
        solid=union(body,flange)
        inner=sd_cylinder_z(x,y,z,P.m125_sleeve_inner_diameter/2,-1,
                            P.m125_sleeve_length+2)
        # Axial slit allows the TPU sleeve to flex and fit the real M125 body.
        slit=sd_box(x,y,z,outer_diameter/2-0.8,outer_diameter/2+2.0,
                    -0.65,0.65,-1,P.m125_sleeve_length+2)
        return subtract(solid,inner,slit)
    return sdf


def pole_liner_full_sdf(x,y,z):
    body=sd_cylinder_z(x,y,z,P.pole_liner_outer_diameter/2,0,P.pole_liner_length)
    flange=sd_cylinder_z(x,y,z,P.pole_liner_flange_diameter/2,
                         P.pole_liner_length-1.4,P.pole_liner_length+0.8)
    solid=union(body,flange)
    inner=sd_cylinder_z(x,y,z,P.pole_liner_inner_diameter/2,-1,
                        P.pole_liner_length+2)
    return subtract(solid,inner)


# ---------------------------------------------------------------------------
# Coupons
# ---------------------------------------------------------------------------

def bearing_coupon_sdf_factory(seat_diameter: float):
    def sdf(x,y,z):
        solid=sd_cylinder_z(x,y,z,21.0,0,10.0)
        holes=[
            sd_cylinder_z(x,y,z,seat_diameter/2,1.25,8.75),
            sd_cylinder_z(x,y,z,10.6,-1,11),
            sd_cylinder_y(x,y,z,P.body_bolt_clearance_diameter/2,
                          -17,17,cx=-15.5,cz=5.0),
            sd_cylinder_y(x,y,z,P.body_bolt_clearance_diameter/2,
                          -17,17,cx=15.5,cz=5.0),
        ]
        return subtract(solid,*holes)
    return sdf


def lid_gasket_coupon_petg_sdf(x,y,z):
    solid=sd_rounded_box(x,y,z,center=(0,0,2.5),half_size=(22,14,2.5),radius=3.0)
    groove_outer=sd_rounded_box(x,y,z,center=(0,0,0.75),half_size=(18,10,0.75),radius=2.5)
    groove_inner=sd_rounded_box(x,y,z,center=(0,0,0.75),half_size=(15.1,7.1,1.2),radius=2.0)
    groove=rounded_ring(groove_outer,groove_inner)
    return subtract(solid,groove)


def lid_gasket_coupon_tpu_sdf(x,y,z):
    outer=sd_rounded_box(x,y,z,center=(0,0,0.9),half_size=(18,10,0.9),radius=2.5)
    inner=sd_rounded_box(x,y,z,center=(0,0,0.9),half_size=(15.1,7.1,1.4),radius=2.0)
    return rounded_ring(outer,inner)


# ---------------------------------------------------------------------------
# Mesh generation and transforms
# ---------------------------------------------------------------------------

def split_positive_y(full_sdf: Callable):
    return lambda x,y,z: np.maximum(full_sdf(x,y,z),-y)


def split_negative_y(full_sdf: Callable):
    return lambda x,y,z: np.maximum(full_sdf(x,y,z),y)


def make_mesh_from_sdf(sdf: Callable,
                       bounds: Tuple[Tuple[float,float],Tuple[float,float],Tuple[float,float]],
                       voxel: float,name: str) -> trimesh.Trimesh:
    axes=[np.arange(lo,hi+voxel*0.5,voxel,dtype=np.float32) for lo,hi in bounds]
    x=axes[0][:,None,None]
    y=axes[1][None,:,None]
    z=axes[2][None,None,:]
    vol=np.asarray(sdf(x,y,z),dtype=np.float32)
    if not (float(vol.min())<0<float(vol.max())):
        raise RuntimeError(f"SDF for {name} does not cross zero")
    verts,faces,_,_=measure.marching_cubes(vol,level=0.0,
                                           spacing=(voxel,voxel,voxel),
                                           allow_degenerate=False)
    origin=np.array([bounds[0][0],bounds[1][0],bounds[2][0]],dtype=np.float64)
    verts += origin
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=True)
    # Marching cubes on an exact split plane can leave zero-area triangles.
    # Remove them and discard only numerically tiny disconnected fragments.
    try:
        mesh.update_faces(mesh.nondegenerate_faces(height=1e-7))
    except Exception:
        pass
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()
    components=mesh.split(only_watertight=False)
    if len(components)>1:
        components=sorted(components,key=lambda c: c.area,reverse=True)
        main=components[0]
        tiny_area=sum(c.area for c in components[1:])
        if tiny_area < max(main.area*1e-5,1e-3):
            mesh=main.copy()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()
    mesh.metadata['name']=name
    mesh.units='mm'
    return mesh


def put_on_bed(mesh: trimesh.Trimesh)->trimesh.Trimesh:
    out=mesh.copy()
    out.apply_translation([0,0,-float(out.bounds[0,2])])
    return out


def rot_x(deg: float):
    return trimesh.transformations.rotation_matrix(math.radians(deg),[1,0,0])


def rot_y(deg: float):
    return trimesh.transformations.rotation_matrix(math.radians(deg),[0,1,0])


def export_stl(mesh: trimesh.Trimesh,path: Path)->Path:
    mesh.export(path)
    return path


def colored_copy(mesh: trimesh.Trimesh,rgba)->trimesh.Trimesh:
    out=mesh.copy()
    out.visual.vertex_colors=np.tile(np.array(rgba,dtype=np.uint8),(len(out.vertices),1))
    return out


def annulus(r_min,r_max,height,z):
    m=trimesh.creation.annulus(r_min=r_min,r_max=r_max,height=height,sections=96)
    m.apply_translation([0,0,z])
    return m


def translate(mesh,xyz):
    out=mesh.copy(); out.apply_translation(xyz); return out


def to_glb_scene(objects_mm: Dict[str,trimesh.Trimesh],title: str)->trimesh.Scene:
    scene=trimesh.Scene()
    for name,m in objects_mm.items():
        mm=m.copy(); mm.apply_scale(0.001); mm.metadata['name']=name
        scene.add_geometry(mm,node_name=name,geom_name=name)
    scene.metadata.update({'title':title,'units':'metres in GLB; source mm','version':'0.5 PETG+TPU provisional'})
    return scene


def mesh_diagnostics(mesh: trimesh.Trimesh):
    return {
        'watertight': bool(mesh.is_watertight),
        'winding_consistent': bool(mesh.is_winding_consistent),
        'euler_number': int(mesh.euler_number),
        'volume_mm3': float(mesh.volume),
        'faces': int(len(mesh.faces)),
        'vertices': int(len(mesh.vertices)),
        'bounds_mm': mesh.bounds.tolist(),
        'components': int(len(mesh.split(only_watertight=False))),
    }


def create_references()->Dict[str,trimesh.Trimesh]:
    refs={}
    # Hollow pole, top at P.pole_top_z.
    pole=annulus(P.pole_inner_diameter_provisional/2,P.pole_outer_diameter/2,
                 120.0,P.pole_top_z-60.0)
    refs['REF_hollow_pole_OD20_ID16_provisional']=colored_copy(pole,[110,120,130,150])
    for label,zc in [('lower',P.lower_bearing_center_z),('upper',P.upper_bearing_center_z)]:
        b=annulus(P.bearing_id/2,P.bearing_od/2,P.bearing_width,zc)
        refs[f'REF_6804_2RS_{label}']=colored_copy(b,[42,47,52,255])
    sp=annulus(P.inner_spacer_id/2,P.inner_spacer_od/2,P.inner_spacer_length,
               (P.lower_bearing_center_z+P.upper_bearing_center_z)/2)
    refs['REF_inner_race_spacer']=colored_copy(sp,[180,185,190,255])
    rod_len=P.spoke_visible_length+(P.spoke_insert_x_max-P.spoke_insert_x_min)
    rod=trimesh.creation.cylinder(radius=P.spoke_diameter/2,height=rod_len,sections=64)
    rod.apply_transform(trimesh.geometry.align_vectors([0,0,1],[1,0,0]))
    rod.apply_translation([P.spoke_insert_x_min+rod_len/2,0,P.spoke_center_z])
    refs['REF_carbon_spoke_OD5']=colored_copy(rod,[28,32,36,255])
    # M125 body in pole.
    m125=trimesh.creation.cylinder(radius=P.m125_body_diameter/2,
                                   height=P.m125_body_length,sections=64)
    body_top=P.pole_top_z-1.5
    m125.apply_translation([0,0,body_top-P.m125_body_length/2])
    refs['REF_M125_body']=colored_copy(m125,[80,80,86,255])
    stem=trimesh.creation.cylinder(radius=P.m125_stem_diameter/2,
                                   height=P.m125_stem_length,sections=48)
    stem.apply_translation([0,0,body_top+P.m125_stem_length/2])
    refs['REF_M125_rotor_stem']=colored_copy(stem,[95,95,102,255])
    # Electronics placeholders inside pod.
    esp=trimesh.creation.box(extents=[23,18,4]); esp.apply_translation([-30,-6,25])
    refs['REF_ESP32_C3_SuperMini']=colored_copy(esp,[180,45,45,255])
    buck=trimesh.creation.box(extents=[28,22,9]); buck.apply_translation([-52,4,27])
    refs['REF_buck_12_to_5']=colored_copy(buck,[42,115,73,255])
    mos=trimesh.creation.box(extents=[25,16,8]); mos.apply_translation([-48,-3,41])
    refs['REF_PC817_LR7843_module']=colored_copy(mos,[60,82,160,255])
    # Flag reference.
    flag=trimesh.creation.box(extents=[P.flag_width,0.8,P.flag_height])
    flag.apply_translation([P.arm_x_max+P.flag_width/2,2,P.spoke_center_z-P.flag_height/2])
    refs['REF_flag_300x250']=colored_copy(flag,[220,115,60,90])
    return refs


def main():
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

    print('Generating PETG rotor halves...')
    rotor_a=make_mesh_from_sdf(split_positive_y(rotor_full_sdf),rotor_bounds,P.rotor_voxel,'PETG_rotor_half_A')
    rotor_b=make_mesh_from_sdf(split_negative_y(rotor_full_sdf),rotor_bounds,P.rotor_voxel,'PETG_rotor_half_B')
    print('Generating PETG lid, photo tunnel and stationary collar...')
    lid=make_mesh_from_sdf(lid_sdf,lid_bounds,P.part_voxel,'PETG_service_lid')
    photo=make_mesh_from_sdf(photo_tunnel_sdf,photo_bounds,P.part_voxel,'PETG_photo_tunnel')
    collar_a=make_mesh_from_sdf(split_positive_y(stationary_collar_full_sdf),collar_bounds,P.part_voxel,'PETG_stationary_collar_A')
    collar_b=make_mesh_from_sdf(split_negative_y(stationary_collar_full_sdf),collar_bounds,P.part_voxel,'PETG_stationary_collar_B')

    print('Generating TPU retained parts...')
    spoke_a=make_mesh_from_sdf(split_positive_y(spoke_liner_full_sdf),spoke_bounds,P.tpu_voxel,'TPU_spoke_liner_A')
    spoke_b=make_mesh_from_sdf(split_negative_y(spoke_liner_full_sdf),spoke_bounds,P.tpu_voxel,'TPU_spoke_liner_B')
    cable_a=make_mesh_from_sdf(split_positive_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,P.tpu_voxel,'TPU_flag_cable_grommet_A')
    cable_b=make_mesh_from_sdf(split_negative_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,P.tpu_voxel,'TPU_flag_cable_grommet_B')
    bundle_a=make_mesh_from_sdf(split_positive_y(bundle_grommet_full_sdf),bundle_grommet_bounds,P.tpu_voxel,'TPU_M125_bundle_grommet_A')
    bundle_b=make_mesh_from_sdf(split_negative_y(bundle_grommet_full_sdf),bundle_grommet_bounds,P.tpu_voxel,'TPU_M125_bundle_grommet_B')
    gasket=make_mesh_from_sdf(lid_gasket_sdf,gasket_bounds,P.tpu_voxel,'TPU_lid_gasket')
    sleeve=make_mesh_from_sdf(m125_sleeve_sdf_factory(P.m125_sleeve_outer_diameter),sleeve_bounds,P.tpu_voxel,'TPU_M125_pole_sleeve_OD15_8')
    pole_liner_a=make_mesh_from_sdf(split_positive_y(pole_liner_full_sdf),pole_liner_bounds,P.tpu_voxel,'TPU_pole_collar_liner_A')
    pole_liner_b=make_mesh_from_sdf(split_negative_y(pole_liner_full_sdf),pole_liner_bounds,P.tpu_voxel,'TPU_pole_collar_liner_B')

    # Print orientation.
    petg_print={}
    for name,m,tr in [
        ('rotor_half_A_print_flat',rotor_a,rot_x(90)),
        ('rotor_half_B_print_flat',rotor_b,rot_x(-90)),
        ('stationary_collar_A_print_flat',collar_a,rot_x(90)),
        ('stationary_collar_B_print_flat',collar_b,rot_x(-90)),
        ('service_lid_top_face_down',lid,rot_x(180)),
        ('photo_tunnel_upright',photo,np.eye(4)),
    ]:
        o=m.copy(); o.apply_transform(tr); petg_print[name]=put_on_bed(o)
    tpu_print={}
    for name,m,tr in [
        ('spoke_liner_A_split_face_down',spoke_a,rot_x(90)),
        ('spoke_liner_B_split_face_down',spoke_b,rot_x(-90)),
        ('flag_cable_grommet_A_split_face_down',cable_a,rot_x(90)),
        ('flag_cable_grommet_B_split_face_down',cable_b,rot_x(-90)),
        ('M125_bundle_grommet_A_split_face_down',bundle_a,rot_x(90)),
        ('M125_bundle_grommet_B_split_face_down',bundle_b,rot_x(-90)),
        ('lid_gasket_flat',gasket,np.eye(4)),
        ('M125_pole_sleeve_upright',sleeve,np.eye(4)),
        ('pole_collar_liner_A_split_face_down',pole_liner_a,rot_x(90)),
        ('pole_collar_liner_B_split_face_down',pole_liner_b,rot_x(-90)),
    ]:
        o=m.copy(); o.apply_transform(tr); tpu_print[name]=put_on_bed(o)

    exported=[]
    for name,m in petg_print.items():
        exported.append(export_stl(m,PETG_DIR/f'{name}.stl'))
    for name,m in tpu_print.items():
        exported.append(export_stl(m,TPU_DIR/f'{name}.stl'))

    # Bearing fit coupons, three diameters.
    coupon_meshes={}
    for d in (32.20,32.35,32.50):
        sdf=bearing_coupon_sdf_factory(d)
        b=(( -23,23),(-23,23),(-2,12))
        ca=make_mesh_from_sdf(split_positive_y(sdf),b,P.coupon_voxel,f'Bearing_coupon_{d:.2f}_A')
        cb=make_mesh_from_sdf(split_negative_y(sdf),b,P.coupon_voxel,f'Bearing_coupon_{d:.2f}_B')
        ca.apply_transform(rot_x(90)); ca=put_on_bed(ca)
        cb.apply_transform(rot_x(-90)); cb=put_on_bed(cb)
        coupon_meshes[f'bearing_seat_{d:.2f}_half_A']=ca
        coupon_meshes[f'bearing_seat_{d:.2f}_half_B']=cb
    # Lid gasket compression coupon.
    cg_petg=make_mesh_from_sdf(lid_gasket_coupon_petg_sdf,((-24,24),(-16,16),(-1,7)),P.coupon_voxel,'PETG_lid_gasket_coupon')
    cg_tpu=make_mesh_from_sdf(lid_gasket_coupon_tpu_sdf,((-21,21),(-13,13),(-1,4)),P.tpu_voxel,'TPU_lid_gasket_coupon')
    coupon_meshes['PETG_lid_gasket_groove_coupon']=put_on_bed(cg_petg)
    coupon_meshes['TPU_lid_gasket_coupon']=put_on_bed(cg_tpu)
    # M125 sleeve OD variants.
    for d in (15.60,15.80,16.00):
        sm=make_mesh_from_sdf(m125_sleeve_sdf_factory(d),sleeve_bounds,P.tpu_voxel,f'TPU_M125_sleeve_OD{d:.2f}')
        coupon_meshes[f'TPU_M125_sleeve_OD_{d:.2f}']=put_on_bed(sm)
    for name,m in coupon_meshes.items():
        exported.append(export_stl(m,COUPON_DIR/f'{name}.stl'))

    # Assembly scene. Translate collar and TPU pole parts into their global positions.
    ORANGE_A=[235,116,40,255]
    ORANGE_B=[246,145,67,255]
    WHITE=[245,245,240,255]
    PETG_DARK=[220,94,28,255]
    assembly={
        'PETG_rotor_half_A': colored_copy(rotor_a,ORANGE_A),
        'PETG_rotor_half_B': colored_copy(rotor_b,ORANGE_B),
        'PETG_service_lid': colored_copy(lid,PETG_DARK),
        'PETG_photo_tunnel': colored_copy(translate(photo,[P.photo_tunnel_center_x,0,P.lid_z_max]),ORANGE_A),
        'PETG_stationary_collar_A': colored_copy(translate(collar_a,[0,0,50]),ORANGE_A),
        'PETG_stationary_collar_B': colored_copy(translate(collar_b,[0,0,50]),ORANGE_B),
        'TPU_spoke_liner_A': colored_copy(spoke_a,WHITE),
        'TPU_spoke_liner_B': colored_copy(spoke_b,WHITE),
        'TPU_flag_cable_grommet_A': colored_copy(cable_a,WHITE),
        'TPU_flag_cable_grommet_B': colored_copy(cable_b,WHITE),
        'TPU_M125_bundle_grommet_A': colored_copy(bundle_a,WHITE),
        'TPU_M125_bundle_grommet_B': colored_copy(bundle_b,WHITE),
        'TPU_lid_gasket': colored_copy(translate(gasket,[0,0,49.65]),WHITE),
        'TPU_M125_pole_sleeve': colored_copy(translate(sleeve,[0,0,42]),WHITE),
        'TPU_pole_collar_liner_A': colored_copy(translate(pole_liner_a,[0,0,50]),WHITE),
        'TPU_pole_collar_liner_B': colored_copy(translate(pole_liner_b,[0,0,50]),WHITE),
    }
    assembly.update(create_references())
    assembly_path=ROOT/'flagpole_finial_v0_5_assembly.glb'
    assembly_path.write_bytes(to_glb_scene(assembly,'Flagpole finial v0.5 PETG + TPU assembly').export(file_type='glb'))

    # Print layout scenes.
    layout_petg={}
    positions=[
        ('rotor_A',petg_print['rotor_half_A_print_flat'],[0,0,0]),
        ('rotor_B',petg_print['rotor_half_B_print_flat'],[0,95,0]),
        ('lid',petg_print['service_lid_top_face_down'],[-90,0,0]),
        ('collar_A',petg_print['stationary_collar_A_print_flat'],[-90,60,0]),
        ('collar_B',petg_print['stationary_collar_B_print_flat'],[-90,95,0]),
        ('photo_tunnel',petg_print['photo_tunnel_upright'],[-125,65,0]),
    ]
    for i,(name,m,pos) in enumerate(positions):
        mm=translate(m,pos); layout_petg[name]=colored_copy(mm,ORANGE_A if i%2==0 else ORANGE_B)
    petg_layout_path=ROOT/'flagpole_finial_v0_5_print_layout_PETG.glb'
    petg_layout_path.write_bytes(to_glb_scene(layout_petg,'PETG print layout v0.5').export(file_type='glb'))

    layout_tpu={}
    x0=0; y0=0
    for idx,(name,m) in enumerate(tpu_print.items()):
        row=idx//4; col=idx%4
        mm=translate(m,[col*75,row*45,0])
        layout_tpu[name]=colored_copy(mm,WHITE)
    tpu_layout_path=ROOT/'flagpole_finial_v0_5_print_layout_TPU.glb'
    tpu_layout_path.write_bytes(to_glb_scene(layout_tpu,'TPU 95A print layout v0.5').export(file_type='glb'))

    meshes={
        'rotor_half_A':rotor_a,'rotor_half_B':rotor_b,'service_lid':lid,
        'photo_tunnel':photo,'stationary_collar_A':collar_a,'stationary_collar_B':collar_b,
        'spoke_liner_A':spoke_a,'spoke_liner_B':spoke_b,
        'flag_cable_grommet_A':cable_a,'flag_cable_grommet_B':cable_b,
        'bundle_grommet_A':bundle_a,'bundle_grommet_B':bundle_b,
        'lid_gasket':gasket,'m125_sleeve':sleeve,
        'pole_liner_A':pole_liner_a,'pole_liner_B':pole_liner_b,
    }
    diagnostics={
        'version':'0.5 PETG+TPU provisional',
        'design_status':'Print coupons first; pole OD/ID, carbon rod and purchased modules not yet measured',
        'parameters_mm':asdict(P),
        'derived_mm':{
            'bearing_center_spacing':P.upper_bearing_center_z-P.lower_bearing_center_z,
            'spoke_to_lower_bearing':P.spoke_center_z-P.lower_bearing_center_z,
            'spoke_to_upper_bearing':P.upper_bearing_center_z-P.spoke_center_z,
            'spoke_engagement_length':P.spoke_insert_x_max-P.spoke_insert_x_min,
            'lid_gasket_nominal_compression':P.gasket_thickness-P.gasket_groove_depth,
            'lid_gasket_compression_percent':100*(P.gasket_thickness-P.gasket_groove_depth)/P.gasket_thickness,
            'm125_sleeve_radial_wall':(P.m125_sleeve_outer_diameter-P.m125_sleeve_inner_diameter)/2,
            'pole_liner_radial_wall':(P.pole_liner_outer_diameter-P.pole_liner_inner_diameter)/2,
        },
        'meshes':{name:mesh_diagnostics(m) for name,m in meshes.items()},
        'files':[str(p.relative_to(ROOT)) for p in exported]+[
            assembly_path.name,petg_layout_path.name,tpu_layout_path.name],
    }
    (ROOT/'model_parameters_and_diagnostics.json').write_text(
        json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'project_manifest.json').write_text(json.dumps({
        'version':'0.5','materials':{'structural':'orange PETG','gaskets':'white TPU 95A'},
        'generated_files':diagnostics['files']
    },ensure_ascii=False,indent=2),encoding='utf-8')

    print('Generated files:')
    for p in exported+[assembly_path,petg_layout_path,tpu_layout_path]:
        print(' -',p.relative_to(ROOT))
    print(json.dumps(diagnostics['derived_mm'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
