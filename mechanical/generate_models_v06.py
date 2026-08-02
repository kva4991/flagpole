#!/usr/bin/env python3
"""Generate the current v0.7.4 flagpole-finial PETG + TPU95A + TPU85A models.

Design status
-------------
This is a fully parametric, printable concept updated for:
- orange PETG structural parts with captive M4/M3 nut pockets;
- white TPU 95A functional liners, cable entry seals and an angled wire guide;
- TPU 85A static lid, window and climate-pocket seals;
- two 6804-2RS bearings around a provisional 20 mm pole;
- carbon spoke between the two bearings;
- preferred M125-0205 miniature slip ring inside a provisional hollow pole;
- a removable two-level electronics carrier with vertical ESP32/MOSF mounting;
- a 15 mm VEML7700 light tunnel with a dedicated adhesive land and glue groove;
- a removable AHT20+BMP280 pocket for a 20 mm self-adhesive membrane whose
  functional central area is 10 mm;
- a raised, open twin-wire rail ending at an angled TPU95 guide approximately
  35 degrees downward toward the flag.

Exact pole OD/ID, carbon rod OD, bearing fit, nuts, wires, membranes and purchased
module dimensions remain provisional until measured. STL units are millimetres.
GLB units are metres. Stable v0_6 file names are retained for compatibility.
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

CURRENT_VERSION = "0.7.4"
ROOT = Path(__file__).resolve().parent
PETG_DIR = ROOT / "stl_petg_v06"
TPU95_DIR = ROOT / "stl_tpu95_v06"
TPU85_DIR = ROOT / "stl_tpu85_v06"
COUPON_DIR = ROOT / "test_coupons_v06"
for d in (PETG_DIR, TPU95_DIR, TPU85_DIR, COUPON_DIR):
    d.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Params:
    # Flag reference and loop datum
    flag_width: float = 300.0
    flag_height: float = 250.0
    flag_top_z: float = 27.0
    finial_lower_edge_z: float = -8.0
    flag_loop_visible_height: float = 20.0
    flag_loop_clearance_below_finial: float = 10.0

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
    body_radius: float = 22.6
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
    arm_half_width: float = 15.0
    arm_corner_radius: float = 4.0
    clamp_gap_total: float = 0.70
    clamp_gap_x_min: float = 24.0

    # Flag-power cable. Two separate Ø2 mm wires remain outside the dry box.
    # The raised rail ends at the owner-marked flag-side location. The removable
    # guide then points approximately 35° downward toward the connector/flag.
    flag_cable_inner_diameter: float = 4.4
    flag_cable_grommet_body_diameter: float = 9.4
    flag_cable_grommet_flange_diameter: float = 12.0
    flag_cable_center_z: float = 18.0
    flag_cable_x_min: float = -18.0
    flag_cable_x_max: float = -8.0
    external_cable_groove_radius: float = 0.0  # historical name; v0.7.4 uses a raised rail
    external_cable_route_points: Tuple[Tuple[float, float, float], ...] = (
        (58.0, -16.2, 15.0),
        (49.0, -16.5, 12.2),
        (38.0, -17.0, 10.8),
        (28.0, -19.0, 7.0),
        (21.0, -22.7, 2.0),
        (5.0, -23.8, -2.0),
        (-10.0, -20.5, 1.5),
        (-15.0, -9.0, 11.0),
        (-13.0, 0.0, 18.0),
    )
    wire_diameter: float = 2.0
    twin_wire_clear_width: float = 4.2
    wire_rail_height: float = 2.5
    wire_rail_width: float = 1.6
    wire_rail_base_thickness: float = 1.0
    wire_rail_base_radius: float = 2.8
    wire_rail_wall_radius: float = 1.25
    wire_rail_wall_offset: float = 3.35
    flag_side_guide_start: Tuple[float, float, float] = (58.0, -16.2, 15.0)
    flag_side_guide_end: Tuple[float, float, float] = (72.0, -16.2, 5.2)
    flag_side_guide_body_radius: float = 5.2
    flag_side_guide_channel_diameter: float = 2.15
    flag_side_guide_channel_offset: float = 1.10
    flag_side_guide_slit_radius: float = 0.90
    flag_side_guide_seat_length: float = 6.0
    flag_side_guide_seat_wall: float = 1.45
    flag_side_guide_seat_clearance: float = 0.25
    connector_reference_length: float = 22.0
    connector_reference_diameter: float = 10.0

    # Electronics pod opposite the flag
    pod_x_min: float = -72.0
    pod_x_max: float = -10.0
    pod_y_half: float = 20.0
    pod_z_min: float = 12.0
    pod_z_max: float = 50.0
    pod_inner_x_min: float = -66.0
    pod_inner_x_max: float = -16.0
    pod_inner_y_half: float = 14.0
    pod_inner_z_min: float = 17.0
    pod_inner_z_max: float = 54.0

    # Removable two-level electronics carrier. Module dimensions are nominal;
    # adjustable frames and TPU ties are used until the purchased boards are measured.
    carrier_x_min: float = -65.0
    carrier_x_max: float = -17.0
    carrier_y_half: float = 12.2
    carrier_z_min: float = 17.6
    carrier_z_max: float = 42.0
    carrier_base_thickness: float = 1.8
    carrier_frame_thickness: float = 2.0
    carrier_cradle_nut_y: float = 11.0
    buck_size: Tuple[float, float, float] = (28.0, 22.0, 9.0)
    buck_center: Tuple[float, float, float] = (-52.0, 0.0, 24.3)
    esp_size_vertical: Tuple[float, float, float] = (23.0, 3.2, 18.0)
    esp_center_vertical: Tuple[float, float, float] = (-29.0, 10.3, 31.0)
    mosfet_size_vertical: Tuple[float, float, float] = (25.0, 3.2, 16.0)
    mosfet_center_vertical: Tuple[float, float, float] = (-49.0, -10.3, 35.0)
    veml_cradle_center: Tuple[float, float, float] = (-50.0, 0.0, 42.0)
    veml_board_center_z: float = 45.4

    # Removable AHT20+BMP280 pocket mounted below the electronics pod.
    # Seven small ventilation pilots remain covered by a drill skin until fit-check.
    env_pocket_center_x: float = -42.0
    env_pocket_outer_x_half: float = 17.0
    env_pocket_outer_y_half: float = 15.0
    env_pocket_body_z_min: float = 0.0
    env_pocket_body_z_max: float = 17.5
    env_pocket_inner_x_half: float = 13.5
    env_pocket_inner_y_half: float = 11.5
    env_pocket_inner_z_min: float = 3.8
    env_pocket_flange_thickness: float = 2.0
    env_pocket_mount_x: float = -42.0
    env_pocket_mount_y: float = 17.0
    env_pocket_screw_diameter: float = 3.4
    env_pocket_board_size: float = 15.0
    env_pocket_drill_skin: float = 0.8
    env_membrane_recess_depth: float = 0.65
    env_pocket_gasket_thickness: float = 1.6
    env_membrane_disc_diameter: float = 20.0
    env_membrane_active_diameter: float = 10.0
    env_membrane_recess_diameter: float = 20.4
    env_membrane_guard_diameter: float = 23.0
    env_membrane_guard_height: float = 2.5
    env_vent_hole_diameter: float = 2.0
    env_vent_hole_radius: float = 3.2
    env_vent_hole_count: int = 7
    env_potting_well_diameter: float = 8.0
    env_board_support_z: float = 6.2

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
    gasket_thickness: float = 2.00
    gasket_groove_depth: float = 1.50
    gasket_center_x: float = -41.0

    # Photo-sensor tunnel, separate PETG insert. Reduced from 18 to 15 mm.
    photo_tunnel_body_diameter: float = 11.0
    photo_tunnel_flange_diameter: float = 16.0
    photo_tunnel_flange_thickness: float = 2.2
    photo_tunnel_height: float = 15.0
    photo_tunnel_mount_hole_diameter: float = 11.4
    photo_tunnel_center_x: float = -50.0
    photo_window_diameter: float = 8.0
    photo_window_seat_diameter: float = 8.3
    photo_window_nominal_thickness: float = 1.0
    photo_window_retainer_outer_diameter: float = 9.8
    photo_window_retainer_inner_diameter: float = 4.4
    photo_window_retainer_thickness: float = 1.2
    photo_window_gasket_thickness: float = 0.8
    photo_glue_groove_inner_diameter: float = 12.2
    photo_glue_groove_outer_diameter: float = 14.2
    photo_glue_groove_depth: float = 0.45
    veml_board_size: float = 16.5
    veml_board_clear_size: float = 17.1
    veml_board_hole_spacing_x: float = 11.0
    veml_board_hole_y_offset: float = 0.0
    veml_board_pin_bottom_diameter: float = 1.8
    veml_board_pin_top_diameter: float = 1.35
    veml_board_pin_height: float = 2.2

    # Fasteners
    body_bolt_clearance_diameter: float = 4.5
    body_bolt_boss_diameter: float = 14.4
    body_bolt_boss_half_length: float = 15.6
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
    m4_nut_across_flats: float = 7.0
    m4_nut_pocket_across_flats: float = 7.30
    m4_nut_snap_entry_across_flats: float = 6.85
    m4_nut_thickness: float = 3.2
    m3_nut_across_flats: float = 5.5
    m3_nut_pocket_across_flats: float = 5.80
    m3_nut_snap_entry_across_flats: float = 5.35
    m3_nut_thickness: float = 2.4

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
    rotor_voxel: float = 0.55
    part_voxel: float = 0.42
    tpu_voxel: float = 0.34
    coupon_voxel: float = 0.34


P = Params()


def unit_vector(value: Iterable[float]) -> np.ndarray:
    vector = np.asarray(tuple(value), dtype=float)
    length = float(np.linalg.norm(vector))
    if length <= 1e-9:
        raise ValueError("zero-length vector")
    return vector / length


def guide_axis() -> np.ndarray:
    return unit_vector(np.asarray(P.flag_side_guide_end) - np.asarray(P.flag_side_guide_start))


def guide_outward() -> np.ndarray:
    return np.array([0.0, -1.0, 0.0], dtype=float)


def guide_side() -> np.ndarray:
    return unit_vector(np.cross(guide_outward(), guide_axis()))


def flag_loop_top_offsets() -> Tuple[float, float, float, float]:
    top = P.flag_top_z - (P.finial_lower_edge_z - P.flag_loop_clearance_below_finial)
    bottom = P.flag_height - P.flag_loop_visible_height
    top_center = top + P.flag_loop_visible_height / 2
    bottom_center = bottom + P.flag_loop_visible_height / 2
    centers = np.linspace(top_center, bottom_center, 4)
    return tuple(float(center - P.flag_loop_visible_height / 2) for center in centers)



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


def sd_capsule_3d(x, y, z, start, end, radius: float):
    """Signed distance to a rounded cable channel between arbitrary points."""
    ax, ay, az = start
    bx, by, bz = end
    vx, vy, vz = bx-ax, by-ay, bz-az
    wx, wy, wz = x-ax, y-ay, z-az
    vv = vx*vx + vy*vy + vz*vz
    if vv <= 1e-12:
        return np.sqrt(wx*wx + wy*wy + wz*wz) - radius
    t = np.clip((wx*vx + wy*vy + wz*vz) / vv, 0.0, 1.0)
    dx = wx - t*vx
    dy = wy - t*vy
    dz = wz - t*vz
    return np.sqrt(dx*dx + dy*dy + dz*dz) - radius


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


def sd_hex_prism_y(x, y, z, across_flats: float, y_min: float, y_max: float,
                   cx: float = 0.0, cz: float = 0.0):
    """Hexagonal prism with the screw/nut axis along Y.

    across_flats is the distance between opposite flats. The returned field is
    suitable for subtracting captive nut pockets.
    """
    px = x - cx
    pz = z - cz
    apothem = across_flats * 0.5
    planes = []
    for angle in (0.0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3):
        planes.append(px*math.cos(angle) + pz*math.sin(angle) - apothem)
    radial = planes[0]
    for plane in planes[1:]:
        radial = np.maximum(radial, plane)
    yc = (y_min+y_max)*0.5
    yh = (y_max-y_min)*0.5
    return np.maximum(radial, np.abs(y-yc)-yh)


def sd_hex_prism_z(x, y, z, across_flats: float, z_min: float, z_max: float,
                   cx: float = 0.0, cy: float = 0.0):
    """Hexagonal prism with the screw/nut axis along Z."""
    px = x - cx
    py = y - cy
    apothem = across_flats * 0.5
    planes = []
    for angle in (0.0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3):
        planes.append(px*math.cos(angle) + py*math.sin(angle) - apothem)
    radial = planes[0]
    for plane in planes[1:]:
        radial = np.maximum(radial, plane)
    zc = (z_min+z_max)*0.5
    zh = (z_max-z_min)*0.5
    return np.maximum(radial, np.abs(z-zc)-zh)


# ---------------------------------------------------------------------------
# Main PETG rotor
# ---------------------------------------------------------------------------

def route_segment_frames():
    """Return tangent/outward/side frames for the raised external rail."""
    frames=[]
    points=[np.asarray(point,dtype=float) for point in P.external_cable_route_points]
    for start,end in zip(points[:-1],points[1:]):
        tangent=unit_vector(end-start)
        mid=(start+end)*0.5
        if mid[0] > 24.0:
            outward=np.array([0.0,-1.0,0.0])
        elif mid[0] > -4.0:
            outward=np.array([mid[0],mid[1],0.0],dtype=float)
            if np.linalg.norm(outward)<1e-6:
                outward=np.array([0.0,-1.0,0.0])
            else:
                outward=unit_vector(outward)
                if outward[1] > 0:
                    outward=-outward
        else:
            outward=np.array([0.0,-1.0,0.0])
        side=unit_vector(np.cross(outward,tangent))
        frames.append((start,end,tangent,outward,side))
    return frames


def external_wire_rail_sdf(x,y,z):
    """Raised open PETG rail with 4.2 mm clear width and 2.5 mm side borders."""
    fields=[]
    for start,end,_,_,side in route_segment_frames():
        fields.append(sd_capsule_3d(x,y,z,start,end,P.wire_rail_base_radius))
        for sign in (-1.0,1.0):
            shift=side*(P.wire_rail_wall_offset*sign)
            fields.append(sd_capsule_3d(
                x,y,z,start+shift,end+shift,P.wire_rail_wall_radius))
    return union(*fields)


def flag_side_guide_seat_fields(x,y,z):
    axis=guide_axis()
    start=np.asarray(P.flag_side_guide_start,dtype=float)-axis*0.8
    end=np.asarray(P.flag_side_guide_start,dtype=float)+axis*P.flag_side_guide_seat_length
    outer_radius=(P.flag_side_guide_body_radius + P.flag_side_guide_seat_clearance +
                  P.flag_side_guide_seat_wall)
    inner_radius=P.flag_side_guide_body_radius+P.flag_side_guide_seat_clearance
    return (
        sd_capsule_3d(x,y,z,start,end,outer_radius),
        sd_capsule_3d(x,y,z,start-axis*0.4,end+axis*0.8,inner_radius),
    )


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
    for sx,sy in P.lid_screw_positions:
        bosses.append(sd_cylinder_z(x-sx,y-sy,z,4.3,43.0,53.5))
    for sy in (-P.env_pocket_mount_y, P.env_pocket_mount_y):
        bosses.append(sd_cylinder_z(x-P.env_pocket_mount_x,y-sy,z,4.6,10.8,19.0))

    guide_seat_outer,guide_seat_inner=flag_side_guide_seat_fields(x,y,z)
    solid = union(body,tower,skirt,arm,pod,external_wire_rail_sdf(x,y,z),
                  guide_seat_outer,*bosses)

    lower_min = P.lower_bearing_center_z - P.lower_bearing_seat_width/2
    lower_max = P.lower_bearing_center_z + P.lower_bearing_seat_width/2
    upper_min = P.upper_bearing_center_z - P.upper_bearing_seat_width/2
    upper_max = P.upper_bearing_center_z + P.upper_bearing_seat_width/2

    holes = [
        sd_cylinder_z(x,y,z,P.skirt_inner_radius,P.skirt_z_min-1,6.0),
        sd_cylinder_z(x,y,z,10.60,5.5,P.pole_top_z+0.5),
        sd_cylinder_z(x,y,z,P.bearing_seat_diameter/2,lower_min,lower_max),
        sd_cylinder_z(x,y,z,P.bearing_seat_diameter/2,upper_min,upper_max),
        sd_cylinder_z(x,y,z,P.spacer_cavity_diameter/2,lower_max,upper_min),
        sd_cylinder_z(x,y,z,P.tower_cavity_radius,51.5,P.tower_z_max-2.0),
        sd_cylinder_x(x,y,z,P.spoke_liner_outer_diameter/2 + 0.18,
                      P.spoke_insert_x_min,P.spoke_insert_x_max,cz=P.spoke_center_z),
        sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2 + 0.18,
                      P.spoke_insert_x_min,P.spoke_insert_x_min+3.2,cz=P.spoke_center_z),
        sd_cylinder_x(x,y,z,P.spoke_liner_flange_diameter/2 + 0.18,
                      P.spoke_insert_x_max-3.2,P.spoke_insert_x_max,cz=P.spoke_center_z),
        sd_box(x,y,z,P.clamp_gap_x_min,P.arm_x_max+1,
               -P.clamp_gap_total/2,P.clamp_gap_total/2,
               P.arm_z_min-0.5,P.arm_z_max+0.5),
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_body_diameter/2+0.18,
                      P.flag_cable_x_min+2.7,P.flag_cable_x_max-3.0,
                      cz=P.flag_cable_center_z),
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2+0.18,
                      P.flag_cable_x_min,P.flag_cable_x_min+3.0,
                      cz=P.flag_cable_center_z),
        sd_cylinder_x(x,y,z,P.flag_cable_grommet_flange_diameter/2+0.18,
                      P.flag_cable_x_max-3.0,P.flag_cable_x_max+0.5,
                      cz=P.flag_cable_center_z),
        sd_rounded_box(
            x,y,z,
            center=((P.pod_inner_x_min+P.pod_inner_x_max)/2,0,
                    (P.pod_inner_z_min+P.pod_inner_z_max)/2),
            half_size=((P.pod_inner_x_max-P.pod_inner_x_min)/2,
                       P.pod_inner_y_half,
                       (P.pod_inner_z_max-P.pod_inner_z_min)/2),
            radius=3.0,
        ),
        sd_cylinder_x(x,y,z,P.bundle_grommet_body_diameter/2+0.16,
                      P.bundle_grommet_x_min+2.0,P.bundle_grommet_x_max-2.0,
                      cz=P.bundle_grommet_center_z),
        sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2+0.16,
                      P.bundle_grommet_x_min,P.bundle_grommet_x_min+2.2,
                      cz=P.bundle_grommet_center_z),
        sd_cylinder_x(x,y,z,P.bundle_grommet_flange_diameter/2+0.16,
                      P.bundle_grommet_x_max-2.2,P.bundle_grommet_x_max,
                      cz=P.bundle_grommet_center_z),
        sd_cylinder_x(x,y,z,1.5,16.0,24.0,cz=-3.0),
        guide_seat_inner,
    ]

    for x0 in (30.0,53.0):
        holes.append(sd_box(x,y,z,x0-2.6,x0+2.6,3.25,6.20,
                            P.spoke_center_z-1.35,P.spoke_center_z+1.35))
        holes.append(sd_box(x,y,z,x0-2.6,x0+2.6,-6.20,-3.25,
                            P.spoke_center_z-1.35,P.spoke_center_z+1.35))
    for bx,bz in P.body_bolt_positions + P.clamp_bolt_positions:
        holes.append(sd_cylinder_y(x,y,z,P.body_bolt_clearance_diameter/2,
                                   -17.5,17.5,cx=bx,cz=bz))
    for sx,sy in P.lid_screw_positions:
        holes.append(sd_cylinder_z(x-sx,y-sy,z,P.lid_screw_diameter/2,42.0,55.5))
        holes.append(sd_hex_prism_z(
            x,y,z,P.m3_nut_pocket_across_flats,43.5,46.2,cx=sx,cy=sy))
        if sy > 0:
            holes.append(sd_box(x,y,z,sx-3.4,sx+3.4,13.8,sy+0.3,43.4,46.3))
        else:
            holes.append(sd_box(x,y,z,sx-3.4,sx+3.4,sy-0.3,-13.8,43.4,46.3))

    for sy in (-P.env_pocket_mount_y, P.env_pocket_mount_y):
        holes.append(sd_cylinder_z(
            x-P.env_pocket_mount_x,y-sy,z,P.env_pocket_screw_diameter/2,9.5,19.5))
        holes.append(sd_hex_prism_z(
            x,y,z,P.m3_nut_pocket_across_flats,13.2,16.5,
            cx=P.env_pocket_mount_x,cy=sy))
        holes.append(sd_hex_prism_z(
            x,y,z,P.m3_nut_snap_entry_across_flats,16.3,17.5,
            cx=P.env_pocket_mount_x,cy=sy))

    holes.append(sd_cylinder_z(
        x-(P.env_pocket_center_x+6.0),y-7.0,z,2.0,13.0,17.5))

    base=subtract(solid,*holes)
    anchor_post_a=sd_rounded_box(
        x,y,z,center=(-24.0,-6.5,20.0),half_size=(2.3,1.8,3.0),radius=0.8)
    anchor_post_b=sd_rounded_box(
        x,y,z,center=(-24.0,6.5,20.0),half_size=(2.3,1.8,3.0),radius=0.8)
    anchor_bridge=sd_rounded_box(
        x,y,z,center=(-24.0,0.0,22.2),half_size=(2.3,7.0,1.0),radius=0.8)
    return union(base,anchor_post_a,anchor_post_b,anchor_bridge)


def rotor_half_a_sdf(x,y,z):
    return np.maximum(rotor_full_sdf(x,y,z),-y)


def rotor_half_b_sdf(x,y,z):
    """Negative-Y rotor half with captive M4 nut pockets for every through-bolt."""
    base=np.maximum(rotor_full_sdf(x,y,z),y)
    pockets=[]
    for bx,bz in P.body_bolt_positions + P.clamp_bolt_positions:
        pockets.append(sd_hex_prism_y(
            x,y,z,P.m4_nut_pocket_across_flats,-15.7,-11.9,cx=bx,cz=bz))
        pockets.append(sd_hex_prism_y(
            x,y,z,P.m4_nut_snap_entry_across_flats,-16.0,-15.0,cx=bx,cz=bz))
    return subtract(base,*pockets)


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
    """15 mm optical tunnel with an explicit adhesive land and glue reservoir."""
    outer = union(
        sd_cylinder_z(x,y,z,P.photo_tunnel_body_diameter/2,0,P.photo_tunnel_height),
        sd_cylinder_z(x,y,z,P.photo_tunnel_flange_diameter/2,0,P.photo_tunnel_flange_thickness),
        sd_cylinder_z(x,y,z,P.photo_window_retainer_outer_diameter/2,
                      P.photo_tunnel_height-2.0,P.photo_tunnel_height+0.6),
    )
    holes = [
        sd_cylinder_z(x,y,z,2.55,-1,6.5),
        sd_cylinder_z(x,y,z,1.95,6.5,7.7),
        sd_cylinder_z(x,y,z,2.55,7.7,13.8),
        sd_cylinder_z(x,y,z,1.75,13.8,15.1),
        sd_cylinder_z(x,y,z,2.55,15.1,P.photo_tunnel_height+1),
        sd_cylinder_z(x,y,z,P.photo_window_seat_diameter/2,
                      P.photo_tunnel_height-P.photo_window_nominal_thickness-0.25,
                      P.photo_tunnel_height+1.0),
    ]
    # Shallow annular reservoir on the upper face of the inner flange. The
    # remaining annular surfaces are the adhesive lands; the optical channel is isolated.
    groove_outer=sd_cylinder_z(
        x,y,z,P.photo_glue_groove_outer_diameter/2,
        P.photo_tunnel_flange_thickness-P.photo_glue_groove_depth,
        P.photo_tunnel_flange_thickness+0.1)
    groove_inner=sd_cylinder_z(
        x,y,z,P.photo_glue_groove_inner_diameter/2,
        P.photo_tunnel_flange_thickness-P.photo_glue_groove_depth-0.1,
        P.photo_tunnel_flange_thickness+0.2)
    holes.append(rounded_ring(groove_outer,groove_inner))
    return subtract(outer,*holes)


def photo_window_retainer_sdf(x,y,z):
    outer=sd_cylinder_z(x,y,z,P.photo_window_retainer_outer_diameter/2,
                        0,P.photo_window_retainer_thickness)
    inner=sd_cylinder_z(x,y,z,P.photo_window_retainer_inner_diameter/2,
                        -1,P.photo_window_retainer_thickness+1)
    return subtract(outer,inner)


def photo_window_gasket_sdf(x,y,z):
    outer=sd_cylinder_z(x,y,z,P.photo_window_diameter/2,
                        0,P.photo_window_gasket_thickness)
    inner=sd_cylinder_z(x,y,z,P.photo_window_retainer_inner_diameter/2,
                        -1,P.photo_window_gasket_thickness+1)
    return subtract(outer,inner)


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


def stationary_collar_half_a_sdf(x,y,z):
    return np.maximum(stationary_collar_full_sdf(x,y,z),-y)


def stationary_collar_half_b_sdf(x,y,z):
    base=np.maximum(stationary_collar_full_sdf(x,y,z),y)
    pockets=[]
    for cx in (-11.0,11.0):
        pockets.append(sd_hex_prism_y(
            x,y,z,P.m3_nut_pocket_across_flats,-17.0,-13.8,cx=cx,cz=4.0))
        pockets.append(sd_hex_prism_y(
            x,y,z,P.m3_nut_snap_entry_across_flats,-17.4,-16.5,cx=cx,cz=4.0))
    return subtract(base,*pockets)


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
    # The two flanges are enough to capture the split grommet between the
    # rotor halves; no remote snap keys are required at the pod wall.
    solid=union(body,fa,fb)
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
# Removable environment-sensor pocket (PETG + TPU85)
# ---------------------------------------------------------------------------

def environment_sensor_pocket_sdf(x,y,z):
    """Removable pocket for a Ø20 mm self-adhesive membrane with Ø10 active area."""
    cx=P.env_pocket_center_x
    outer=sd_rounded_box(
        x,y,z,
        center=(cx,0,(P.env_pocket_body_z_min+P.env_pocket_body_z_max)/2),
        half_size=(P.env_pocket_outer_x_half,P.env_pocket_outer_y_half,
                   (P.env_pocket_body_z_max-P.env_pocket_body_z_min)/2),
        radius=3.0,
    )
    ears=[
        sd_cylinder_z(x-P.env_pocket_mount_x,y-sy,z,4.6,
                      P.env_pocket_body_z_max-P.env_pocket_flange_thickness,
                      P.env_pocket_body_z_max)
        for sy in (-P.env_pocket_mount_y,P.env_pocket_mount_y)
    ]
    guard_outer=sd_cylinder_z(
        x-cx,y,z,P.env_membrane_guard_diameter/2,
        -P.env_membrane_guard_height,0.35)
    guard_inner=sd_cylinder_z(
        x-cx,y,z,P.env_membrane_recess_diameter/2+0.55,
        -P.env_membrane_guard_height-0.2,0.5)
    guard=rounded_ring(guard_outer,guard_inner)
    solid=union(outer,*ears,guard)

    inner=sd_rounded_box(
        x,y,z,
        center=(cx,0,(P.env_pocket_inner_z_min+P.env_pocket_body_z_max+1.0)/2),
        half_size=(P.env_pocket_inner_x_half,P.env_pocket_inner_y_half,
                   (P.env_pocket_body_z_max+1.0-P.env_pocket_inner_z_min)/2),
        radius=2.0,
    )
    holes=[inner]
    holes.append(sd_cylinder_z(
        x-cx,y,z,P.env_membrane_recess_diameter/2,
        -0.05,P.env_membrane_recess_depth))

    vent_positions=[(0.0,0.0)]
    for index in range(6):
        angle=2*math.pi*index/6
        vent_positions.append((
            P.env_vent_hole_radius*math.cos(angle),
            P.env_vent_hole_radius*math.sin(angle)))
    for dx,dy in vent_positions:
        holes.append(sd_cylinder_z(
            x-(cx+dx),y-dy,z,P.env_vent_hole_diameter/2,
            P.env_membrane_recess_depth+P.env_pocket_drill_skin,
            P.env_pocket_inner_z_min+0.6))

    # Four wide drainage notches divide the guard into connected quarter arcs.
    holes.extend([
        sd_box(x,y,z,cx-1.6,cx+1.6,-13.0,13.0,-3.0,0.45),
        sd_box(x,y,z,cx-13.0,cx+13.0,-1.6,1.6,-3.0,0.45),
    ])

    for sy in (-P.env_pocket_mount_y,P.env_pocket_mount_y):
        holes.append(sd_cylinder_z(
            x-P.env_pocket_mount_x,y-sy,z,P.env_pocket_screw_diameter/2,
            P.env_pocket_body_z_max-P.env_pocket_flange_thickness-1,
            P.env_pocket_body_z_max+1))
    holes.append(sd_cylinder_z(
        x-(cx+6.0),y-7.0,z,2.0,
        P.env_pocket_body_z_max-P.env_pocket_flange_thickness,
        P.env_pocket_body_z_max-P.env_pocket_drill_skin))

    base=subtract(solid,*holes)
    # Offset baffle prevents direct dynamic pressure and splash from reaching BMP280.
    baffle=sd_rounded_box(
        x,y,z,center=(cx+3.8,0.0,6.7),half_size=(0.8,8.0,2.8),radius=0.5)
    supports=[]
    support_offset=P.env_pocket_board_size/2-1.2
    for dx in (-support_offset,support_offset):
        for dy in (-support_offset,support_offset):
            supports.append(sd_cylinder_z(
                x-(cx+3.0+dx),y-dy,z,1.05,P.env_pocket_inner_z_min,P.env_board_support_z))
    # Three low guide walls; the cable side remains open.
    guides=[
        sd_rounded_box(x,y,z,center=(cx+3.0,-8.5,7.3),half_size=(8.8,0.7,1.3),radius=0.4),
        sd_rounded_box(x,y,z,center=(cx-5.5,0.0,7.3),half_size=(0.7,7.8,1.3),radius=0.4),
        sd_rounded_box(x,y,z,center=(cx+11.5,0.0,7.3),half_size=(0.7,7.8,1.3),radius=0.4),
    ]
    return union(base,baffle,*supports,*guides)


def environment_pocket_gasket_sdf(x,y,z):
    """TPU85 seal between the removable climate pocket and dry pod floor."""
    cx=P.env_pocket_center_x
    t=P.env_pocket_gasket_thickness
    outer=sd_rounded_box(
        x,y,z,center=(cx,0,t/2),half_size=(16.10,14.20,t/2),radius=2.6)
    inner=sd_rounded_box(
        x,y,z,center=(cx,0,t/2),half_size=(14.15,12.25,t),radius=1.8)
    ring=rounded_ring(outer,inner)
    ears=[]; holes=[]
    for sy in (-P.env_pocket_mount_y,P.env_pocket_mount_y):
        ears.append(sd_cylinder_z(x-P.env_pocket_mount_x,y-sy,z,4.2,0,t))
        holes.append(sd_cylinder_z(x-P.env_pocket_mount_x,y-sy,z,
                                   P.env_pocket_screw_diameter/2+0.18,-1,t+1))
    return subtract(union(ring,*ears),*holes)


# ---------------------------------------------------------------------------
# Angled flag-side guide and electronics carrier
# ---------------------------------------------------------------------------

def flag_side_wire_guide_sdf(x,y,z):
    axis=guide_axis(); side=guide_side(); outward=guide_outward()
    start=np.asarray(P.flag_side_guide_start,dtype=float)
    end=np.asarray(P.flag_side_guide_end,dtype=float)
    body=sd_capsule_3d(x,y,z,start,end,P.flag_side_guide_body_radius)
    shoulder=sd_capsule_3d(
        x,y,z,start-axis*0.6,start+axis*1.5,P.flag_side_guide_body_radius+0.35)
    holes=[]
    channel_radius=P.flag_side_guide_channel_diameter/2
    for sign in (-1.0,1.0):
        offset=side*(P.flag_side_guide_channel_offset*sign)
        holes.append(sd_capsule_3d(
            x,y,z,start+offset-axis*0.8,end+offset+axis*0.8,channel_radius))
        # A chain of overlapping outward capsules joins each channel to the
        # weather-facing surface. This produces a real service slit while
        # retaining one continuous TPU body behind both wire channels.
        for outward_distance in np.linspace(0.7, P.flag_side_guide_body_radius + 0.6, 7):
            slit_offset=offset+outward*outward_distance
            holes.append(sd_capsule_3d(
                x,y,z,start+slit_offset-axis*0.3,end+slit_offset+axis*0.3,
                P.flag_side_guide_slit_radius))
    return subtract(union(body,shoulder),*holes)


def electronics_carrier_sdf(x,y,z):
    """One-piece two-level carrier for flat DC-DC and vertical ESP/MOSF modules."""
    t=P.carrier_frame_thickness
    base=sd_rounded_box(
        x,y,z,center=(-47.0,0.0,P.carrier_z_min+P.carrier_base_thickness/2),
        half_size=(18.0,P.carrier_y_half,P.carrier_base_thickness/2),radius=1.2)
    rear=sd_rounded_box(
        x,y,z,center=(P.carrier_x_min+1.0,0.0,30.0),
        half_size=(1.0,P.carrier_y_half,12.0),radius=0.8)
    # DC-DC edge stops around the lower tray.
    stops=[]
    bx,by,bz=P.buck_center
    sx,sy,_=P.buck_size
    for dx in (-sx/2+0.5,sx/2-0.5):
        for dy in (-sy/2+0.2,sy/2-0.2):
            stops.append(sd_rounded_box(
                x,y,z,center=(bx+dx,by+dy,P.carrier_z_min+3.1),
                half_size=(0.9,0.9,2.3),radius=0.45))

    # Vertical frame on positive-Y side for ESP32-C3.
    esp_x0=P.esp_center_vertical[0]-P.esp_size_vertical[0]/2-1.0
    esp_x1=P.esp_center_vertical[0]+P.esp_size_vertical[0]/2+1.0
    # Extend frame legs to the tray so the printed carrier is one connected
    # component even before boards or cable ties are installed.
    esp_z0=P.carrier_z_min+P.carrier_base_thickness-0.4
    esp_z1=P.esp_center_vertical[2]+P.esp_size_vertical[2]/2+1.0
    frames=[
        sd_rounded_box(x,y,z,center=(esp_x0,P.carrier_y_half-1.1,(esp_z0+esp_z1)/2),half_size=(1.0,1.1,(esp_z1-esp_z0)/2),radius=0.5),
        sd_rounded_box(x,y,z,center=(esp_x1,P.carrier_y_half-1.1,(esp_z0+esp_z1)/2),half_size=(1.0,1.1,(esp_z1-esp_z0)/2),radius=0.5),
        sd_rounded_box(x,y,z,center=((esp_x0+esp_x1)/2,P.carrier_y_half-1.1,esp_z0),half_size=((esp_x1-esp_x0)/2,1.1,1.0),radius=0.5),
        sd_rounded_box(x,y,z,center=((esp_x0+esp_x1)/2,P.carrier_y_half-1.1,esp_z1),half_size=((esp_x1-esp_x0)/2,1.1,1.0),radius=0.5),
    ]

    # Vertical frame on negative-Y side for the MOSFET module.
    mos_x0=P.mosfet_center_vertical[0]-P.mosfet_size_vertical[0]/2-1.0
    mos_x1=P.mosfet_center_vertical[0]+P.mosfet_size_vertical[0]/2+1.0
    mos_z0=P.carrier_z_min+P.carrier_base_thickness-0.4
    mos_z1=P.mosfet_center_vertical[2]+P.mosfet_size_vertical[2]/2+1.0
    frames.extend([
        sd_rounded_box(x,y,z,center=(mos_x0,-P.carrier_y_half+1.1,(mos_z0+mos_z1)/2),half_size=(1.0,1.1,(mos_z1-mos_z0)/2),radius=0.5),
        sd_rounded_box(x,y,z,center=(mos_x1,-P.carrier_y_half+1.1,(mos_z0+mos_z1)/2),half_size=(1.0,1.1,(mos_z1-mos_z0)/2),radius=0.5),
        sd_rounded_box(x,y,z,center=((mos_x0+mos_x1)/2,-P.carrier_y_half+1.1,mos_z0),half_size=((mos_x1-mos_x0)/2,1.1,1.0),radius=0.5),
        sd_rounded_box(x,y,z,center=((mos_x0+mos_x1)/2,-P.carrier_y_half+1.1,mos_z1),half_size=((mos_x1-mos_x0)/2,1.1,1.0),radius=0.5),
    ])

    # Two top arms and bosses carry the removable VEML7700 cradle.
    arms=[]; bosses=[]
    for sy_nut in (-P.carrier_cradle_nut_y,P.carrier_cradle_nut_y):
        arms.append(sd_rounded_box(
            x,y,z,center=(-56.5,sy_nut,40.5),half_size=(7.5,1.4,1.2),radius=0.6))
        bosses.append(sd_cylinder_z(x+50.0,y-sy_nut,z,4.2,38.8,42.0))
    solid=union(base,rear,*stops,*frames,*arms,*bosses)
    holes=[]
    for sy_nut in (-P.carrier_cradle_nut_y,P.carrier_cradle_nut_y):
        holes.append(sd_cylinder_z(x+50.0,y-sy_nut,z,1.75,38.0,43.0))
        holes.append(sd_hex_prism_z(
            x,y,z,P.m3_nut_pocket_across_flats,39.0,41.6,cx=-50.0,cy=sy_nut))
        holes.append(sd_hex_prism_z(
            x,y,z,P.m3_nut_snap_entry_across_flats,38.5,39.5,cx=-50.0,cy=sy_nut))
    # Wide tie slots in the tray, plus service opening around the cable anchor.
    holes.extend([
        sd_box(x,y,z,-61.0,-57.0,-8.0,8.0,17.0,20.5),
        sd_box(x,y,z,-47.0,-43.0,-8.0,8.0,17.0,20.5),
        sd_box(x,y,z,-34.5,-30.5,-8.0,8.0,17.0,20.5),
    ])
    return subtract(solid,*holes)


def veml_cradle_sdf(x,y,z):
    """Removable provisional VEML7700 cradle secured to two captive M3 nuts."""
    base=sd_rounded_box(x,y,z,center=(0,0,0.9),half_size=(12.5,14.0,0.9),radius=1.6)
    pads=[]
    corner=P.veml_board_clear_size/2-1.4
    for dx in (-corner,corner):
        for dy in (-corner,corner):
            pads.append(sd_cylinder_z(x-dx,y-dy,z,1.5,1.8,2.5))
    pins=[]
    for dx in (-P.veml_board_hole_spacing_x/2,P.veml_board_hole_spacing_x/2):
        pins.append(sd_frustum_z(
            x-dx,y-P.veml_board_hole_y_offset,z,
            P.veml_board_pin_bottom_diameter/2,
            P.veml_board_pin_top_diameter/2,
            1.8,1.8+P.veml_board_pin_height))
    solid=union(base,*pads,*pins)
    holes=[
        sd_cylinder_z(x,y,z,3.0,-1,5),
        sd_cylinder_z(x,y-P.carrier_cradle_nut_y,z,1.75,-1,4),
        sd_cylinder_z(x,y+P.carrier_cradle_nut_y,z,1.75,-1,4),
        # Open cable side at +X.
        sd_box(x,y,z,8.2,13.5,-5.0,5.0,1.4,4.5),
    ]
    return subtract(solid,*holes)


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


def nut_trap_coupon_sdf(x,y,z):
    solid=sd_box(x,y,z,-18,18,-10,10,0,8)
    holes=[
        sd_cylinder_z(x+9,y,z,P.body_bolt_clearance_diameter/2,-1,9),
        sd_hex_prism_z(x,y,z,P.m4_nut_pocket_across_flats,3.8,7.2,cx=-9,cy=0),
        sd_hex_prism_z(x,y,z,P.m4_nut_snap_entry_across_flats,7.0,8.5,cx=-9,cy=0),
        sd_cylinder_z(x-9,y,z,P.body_bolt_clearance_diameter/2,-1,9),
    ]
    return subtract(solid,*holes)


def drill_skin_coupon_sdf(x,y,z):
    solid=sd_box(x,y,z,-22,22,-10,10,0,5)
    holes=[]
    for index,skin in enumerate((0.6,0.8,1.0)):
        px=-14+index*14
        holes.append(sd_cylinder_z(x-px,y,z,2.0,skin,5.5))
    return subtract(solid,*holes)


def twin_wire_rail_coupon_sdf(x,y,z):
    """PETG coupon for the 4.2 mm clear twin-wire rail and 2.5 mm side walls."""
    base=sd_rounded_box(x,y,z,center=(0,0,P.wire_rail_base_thickness/2),
                         half_size=(28.0,10.0,P.wire_rail_base_thickness/2),radius=1.4)
    rail_offset=P.twin_wire_clear_width/2+P.wire_rail_width/2
    rail_a=sd_rounded_box(x,y,z,
        center=(0,rail_offset,P.wire_rail_base_thickness+P.wire_rail_height/2),
        half_size=(27.0,P.wire_rail_width/2,P.wire_rail_height/2),radius=0.45)
    rail_b=sd_rounded_box(x,y,z,
        center=(0,-rail_offset,P.wire_rail_base_thickness+P.wire_rail_height/2),
        half_size=(27.0,P.wire_rail_width/2,P.wire_rail_height/2),radius=0.45)
    return union(base,rail_a,rail_b)



def m3_nut_trap_coupon_sdf(x,y,z):
    solid=sd_box(x,y,z,-18,18,-10,10,0,7)
    holes=[
        sd_cylinder_z(x+9,y,z,P.lid_screw_diameter/2,-1,8),
        sd_hex_prism_z(x,y,z,P.m3_nut_pocket_across_flats,3.1,5.8,cx=-9,cy=0),
        sd_hex_prism_z(x,y,z,P.m3_nut_snap_entry_across_flats,5.6,7.4,cx=-9,cy=0),
        sd_cylinder_z(x-9,y,z,P.lid_screw_diameter/2,-1,8),
    ]
    return subtract(solid,*holes)


def photo_tunnel_comparison_coupon_sdf(x,y,z):
    base=sd_rounded_box(x,y,z,center=(0,0,1.0),half_size=(25,12,1.0),radius=1.5)
    short=sd_cylinder_z(x+12,y,z,P.photo_tunnel_body_diameter/2,2,17)
    long=sd_cylinder_z(x-12,y,z,P.photo_tunnel_body_diameter/2,2,20)
    holes=[
        sd_cylinder_z(x+12,y,z,2.1,1,18),
        sd_cylinder_z(x-12,y,z,2.1,1,21),
    ]
    return subtract(union(base,short,long),*holes)


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


def center_xy_on_bed(mesh: trimesh.Trimesh)->trimesh.Trimesh:
    out=mesh.copy()
    center=(out.bounds[0]+out.bounds[1])*0.5
    out.apply_translation([-float(center[0]),-float(center[1]),-float(out.bounds[0,2])])
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
    scene.metadata.update({'title':title,'units':'metres in GLB; source mm','version':f'{CURRENT_VERSION} PETG+TPU95+TPU85 provisional'})
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


def cylinder_between(start, end, radius: float, sections: int = 32)->trimesh.Trimesh:
    a=np.array(start,dtype=float); b=np.array(end,dtype=float)
    delta=b-a; length=float(np.linalg.norm(delta))
    if length <= 1e-9:
        return trimesh.creation.icosphere(subdivisions=2,radius=radius)
    tube=trimesh.creation.cylinder(radius=radius,height=length,sections=sections)
    tube.apply_transform(trimesh.geometry.align_vectors([0,0,1],delta/length))
    tube.apply_translation((a+b)/2)
    return tube


def wire_reference_for_polyline(points, offset_sign: float)->trimesh.Trimesh:
    parts=[]
    points=[np.asarray(point,dtype=float) for point in points]
    for start,end in zip(points[:-1],points[1:]):
        tangent=unit_vector(end-start)
        mid=(start+end)/2
        if mid[0] > 24:
            outward=np.array([0.0,-1.0,0.0])
        elif mid[0] > -4:
            outward=unit_vector([mid[0],mid[1],0.0])
            if outward[1]>0: outward=-outward
        else:
            outward=np.array([0.0,-1.0,0.0])
        side=unit_vector(np.cross(outward,tangent))
        shift=side*(P.wire_diameter/2*offset_sign)
        parts.append(cylinder_between(start+shift,end+shift,P.wire_diameter/2,24))
    return trimesh.util.concatenate(parts)


def external_flag_cable_reference()->trimesh.Trimesh:
    route=list(P.external_cable_route_points)
    route.extend([(-18.0,0.0,P.flag_cable_center_z),(-28.0,-5.0,22.0)])
    guide=[P.flag_side_guide_end,P.flag_side_guide_start]
    wires=[]
    for sign in (-1.0,1.0):
        wires.append(wire_reference_for_polyline(route,sign))
        axis=guide_axis(); side=guide_side()
        shift=side*(P.wire_diameter/2*sign)
        wires.append(cylinder_between(
            np.asarray(P.flag_side_guide_end)+shift,
            np.asarray(P.flag_side_guide_start)+shift,
            P.wire_diameter/2,24))
    mesh=trimesh.util.concatenate(wires)
    mesh.metadata['name']='REF_flag_power_cable_external_route'
    return mesh


def waterproof_connector_reference()->trimesh.Trimesh:
    axis=guide_axis(); start=np.asarray(P.flag_side_guide_end)+axis*2.0
    end=start+axis*P.connector_reference_length
    body=cylinder_between(start,end,P.connector_reference_diameter/2,48)
    relief=cylinder_between(
        np.asarray(P.flag_side_guide_end)-axis*1.0,start+axis*5.0,3.3,40)
    mesh=trimesh.util.concatenate([body,relief])
    mesh.metadata['name']='REF_waterproof_2pin_connector_provisional'
    return mesh


def hex_nut_reference(axis: str, center, across_flats: float, thickness: float)->trimesh.Trimesh:
    radius=across_flats/math.sqrt(3.0)
    nut=trimesh.creation.cylinder(radius=radius,height=thickness,sections=6)
    if axis=='y':
        nut.apply_transform(trimesh.geometry.align_vectors([0,0,1],[0,1,0]))
    elif axis!='z':
        raise ValueError(axis)
    nut.apply_translation(center)
    return nut


def cloth_loop_reference(z_center: float, loop_index: int)->trimesh.Trimesh:
    """Create a non-printable orange fabric-loop reference around the pole.

    The loop is shown as a segmented 20 mm-high textile band. It is only an
    assembly reference; the sewing pattern is defined in the root SVG files.
    """
    pole_path_radius=P.pole_outer_diameter/2+3.0
    flag_edge_x=P.arm_x_max
    side_y=8.0
    points=[np.array([flag_edge_x,-side_y],dtype=float)]
    for angle_deg in (-45,-90,-135,-180,-225,-270,-315):
        a=np.deg2rad(angle_deg)
        points.append(np.array([pole_path_radius*np.cos(a),pole_path_radius*np.sin(a)],dtype=float))
    points.append(np.array([flag_edge_x,side_y],dtype=float))
    parts=[]
    for a,b in zip(points[:-1],points[1:]):
        delta=b-a
        length=float(np.linalg.norm(delta))
        if length<1e-6:
            continue
        bar=trimesh.creation.box(extents=[length,1.2,20.0])
        angle=float(np.arctan2(delta[1],delta[0]))
        transform=trimesh.transformations.rotation_matrix(angle,[0,0,1])
        bar.apply_transform(transform)
        mid=(a+b)/2
        bar.apply_translation([mid[0],mid[1],z_center])
        parts.append(bar)
    loop=trimesh.util.concatenate(parts)
    loop.metadata['name']=f'REF_flag_attachment_loop_{loop_index}'
    return loop


def create_references()->Dict[str,trimesh.Trimesh]:
    refs={}
    pole=annulus(P.pole_inner_diameter_provisional/2,P.pole_outer_diameter/2,
                 320.0,P.pole_top_z-160.0)
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
    refs['REF_flag_power_cable_external_route']=colored_copy(
        external_flag_cable_reference(),[35,38,42,255])
    refs['REF_waterproof_2pin_connector_provisional']=colored_copy(
        waterproof_connector_reference(),[55,62,68,255])

    m125=trimesh.creation.cylinder(radius=P.m125_body_diameter/2,
                                   height=P.m125_body_length,sections=64)
    body_top=P.pole_top_z-1.5
    m125.apply_translation([0,0,body_top-P.m125_body_length/2])
    refs['REF_M125_body']=colored_copy(m125,[80,80,86,255])
    stem=trimesh.creation.cylinder(radius=P.m125_stem_diameter/2,
                                   height=P.m125_stem_length,sections=48)
    stem.apply_translation([0,0,body_top+P.m125_stem_length/2])
    refs['REF_M125_rotor_stem']=colored_copy(stem,[95,95,102,255])

    # Electronics placeholders match the v0.7.4 carrier arrangement.
    esp=trimesh.creation.box(extents=P.esp_size_vertical); esp.apply_translation(P.esp_center_vertical)
    refs['REF_ESP32_C3_SuperMini_vertical']=colored_copy(esp,[180,45,45,255])
    buck=trimesh.creation.box(extents=P.buck_size); buck.apply_translation(P.buck_center)
    refs['REF_buck_12_to_5_flat']=colored_copy(buck,[42,115,73,255])
    mos=trimesh.creation.box(extents=P.mosfet_size_vertical); mos.apply_translation(P.mosfet_center_vertical)
    refs['REF_PC817_LR7843_vertical']=colored_copy(mos,[60,82,160,255])
    veml=trimesh.creation.box(extents=[P.veml_board_size,P.veml_board_size,2.0])
    veml.apply_translation([P.photo_tunnel_center_x,0,P.veml_board_center_z])
    refs['REF_VEML7700_board_provisional']=colored_copy(veml,[58,130,80,230])
    env=trimesh.creation.box(extents=[P.env_pocket_board_size,P.env_pocket_board_size,2.0])
    env.apply_translation([P.env_pocket_center_x+3.0,0,P.env_board_support_z+1.0])
    refs['REF_AHT20_BMP280_board_provisional']=colored_copy(env,[118,78,170,230])

    # Adhesive membrane: full Ø20 disc with distinct functional Ø10 centre.
    membrane=trimesh.creation.cylinder(radius=P.env_membrane_disc_diameter/2,height=0.20,sections=64)
    membrane.apply_translation([P.env_pocket_center_x,0,-0.10])
    refs['REF_environment_membrane_OD20_adhesive']=colored_copy(membrane,[195,210,218,190])
    active=trimesh.creation.cylinder(radius=P.env_membrane_active_diameter/2,height=0.24,sections=64)
    active.apply_translation([P.env_pocket_center_x,0,-0.12])
    refs['REF_environment_membrane_active_OD10']=colored_copy(active,[132,181,203,190])

    flag=trimesh.creation.box(extents=[P.flag_width,0.8,P.flag_height])
    flag.apply_translation([P.arm_x_max+P.flag_width/2,2,P.flag_top_z-P.flag_height/2])
    refs['REF_flag_300x250']=colored_copy(flag,[220,115,60,90])
    for index,top_offset in enumerate(flag_loop_top_offsets(),start=1):
        center_offset=top_offset+P.flag_loop_visible_height/2
        zc=P.flag_top_z-center_offset
        refs[f'REF_flag_attachment_loop_{index}']=colored_copy(
            cloth_loop_reference(zc,index),[242,112,24,210])

    # Captive nuts are explicit reference objects in every current 3D assembly.
    metal=[155,160,164,255]
    for index,(bx,bz) in enumerate(P.body_bolt_positions+P.clamp_bolt_positions,start=1):
        refs[f'REF_M4_captive_nut_{index:02d}']=colored_copy(
            hex_nut_reference('y',(bx,-13.8,bz),P.m4_nut_across_flats,P.m4_nut_thickness),metal)
    for index,(sx,sy) in enumerate(P.lid_screw_positions,start=1):
        refs[f'REF_M3_lid_captive_nut_{index:02d}']=colored_copy(
            hex_nut_reference('z',(sx,sy,44.85),P.m3_nut_across_flats,P.m3_nut_thickness),metal)
    for index,sy in enumerate((-P.env_pocket_mount_y,P.env_pocket_mount_y),start=1):
        refs[f'REF_M3_sensor_pocket_captive_nut_{index:02d}']=colored_copy(
            hex_nut_reference('z',(P.env_pocket_mount_x,sy,14.8),P.m3_nut_across_flats,P.m3_nut_thickness),metal)
    for index,cx in enumerate((-11.0,11.0),start=1):
        refs[f'REF_M3_collar_captive_nut_{index:02d}']=colored_copy(
            hex_nut_reference('y',(cx,-15.4,54.0),P.m3_nut_across_flats,P.m3_nut_thickness),metal)
    for index,sy in enumerate((-P.carrier_cradle_nut_y,P.carrier_cradle_nut_y),start=1):
        refs[f'REF_M3_cradle_captive_nut_{index:02d}']=colored_copy(
            hex_nut_reference('z',(-50.0,sy,40.3),P.m3_nut_across_flats,P.m3_nut_thickness),metal)
    return refs




def main():
    rotor_bounds=((-80,82),(-31,27),(-11,79))
    lid_bounds=((-77,-5),(-24,24),(45,57))
    photo_bounds=((-9,9),(-9,9),(-1,22))
    photo_retainer_bounds=((-9,9),(-9,9),(-1,4))
    collar_bounds=((-18,18),(-18,18),(-3,16))
    spoke_bounds=((13,68),(-7,7),(21,33))
    flag_grommet_bounds=((-20,-6),(-8,8),(10,26))
    guide_bounds=((50,78),(-24,-8),(-2,24))
    bundle_grommet_bounds=((-24,-9),(-7,7),(40,54))
    gasket_bounds=((-74,-8),(-22,22),(-1,4))
    sleeve_bounds=((-11,11),(-11,11),(-1,19))
    pole_liner_bounds=((-14,14),(-14,14),(-1,11))
    env_pocket_bounds=((-61,-23),(-24,24),(-4,19))
    env_gasket_bounds=((-62,-22),(-23,23),(-1,4))
    carrier_bounds=((-72,-12),(-18,18),(14,47))
    cradle_bounds=((-15,15),(-17,17),(-1,6))

    # Remove stale generated STL files before rebuilding the cumulative set.
    for folder in (PETG_DIR,TPU95_DIR,TPU85_DIR,COUPON_DIR):
        for old in folder.glob('*.stl'):
            old.unlink()

    print(f'Generating fully parametric v{CURRENT_VERSION} rotor halves...')
    rotor_a=make_mesh_from_sdf(rotor_half_a_sdf,rotor_bounds,P.rotor_voxel,'PETG_rotor_half_A')
    rotor_b=make_mesh_from_sdf(rotor_half_b_sdf,rotor_bounds,P.rotor_voxel,'PETG_rotor_half_B')
    print('Generating PETG lid, 15 mm tunnel, climate pocket and electronics fixtures...')
    lid=make_mesh_from_sdf(lid_sdf,lid_bounds,P.part_voxel,'PETG_service_lid')
    photo=make_mesh_from_sdf(photo_tunnel_sdf,photo_bounds,P.part_voxel,'PETG_photo_tunnel')
    photo_retainer=make_mesh_from_sdf(photo_window_retainer_sdf,photo_retainer_bounds,P.part_voxel,'PETG_photo_window_retainer')
    env_pocket=make_mesh_from_sdf(environment_sensor_pocket_sdf,env_pocket_bounds,P.part_voxel,'PETG_environment_sensor_pocket')
    carrier=make_mesh_from_sdf(electronics_carrier_sdf,carrier_bounds,P.part_voxel,'PETG_electronics_carrier')
    veml_cradle=make_mesh_from_sdf(veml_cradle_sdf,cradle_bounds,P.part_voxel,'PETG_VEML7700_cradle')
    collar_a=make_mesh_from_sdf(stationary_collar_half_a_sdf,collar_bounds,P.part_voxel,'PETG_stationary_collar_A')
    collar_b=make_mesh_from_sdf(stationary_collar_half_b_sdf,collar_bounds,P.part_voxel,'PETG_stationary_collar_B')

    print('Generating TPU95 functional retained parts...')
    spoke_a=make_mesh_from_sdf(split_positive_y(spoke_liner_full_sdf),spoke_bounds,P.tpu_voxel,'TPU95_spoke_liner_A')
    spoke_b=make_mesh_from_sdf(split_negative_y(spoke_liner_full_sdf),spoke_bounds,P.tpu_voxel,'TPU95_spoke_liner_B')
    cable_a=make_mesh_from_sdf(split_positive_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,P.tpu_voxel,'TPU95_flag_cable_grommet_A')
    cable_b=make_mesh_from_sdf(split_negative_y(flag_cable_grommet_full_sdf),flag_grommet_bounds,P.tpu_voxel,'TPU95_flag_cable_grommet_B')
    flag_side_guide=make_mesh_from_sdf(flag_side_wire_guide_sdf,guide_bounds,P.tpu_voxel,'TPU95_flag_side_wire_guide')
    bundle_a=make_mesh_from_sdf(split_positive_y(bundle_grommet_full_sdf),bundle_grommet_bounds,P.tpu_voxel,'TPU95_M125_bundle_grommet_A')
    bundle_b=make_mesh_from_sdf(split_negative_y(bundle_grommet_full_sdf),bundle_grommet_bounds,P.tpu_voxel,'TPU95_M125_bundle_grommet_B')
    sleeve=make_mesh_from_sdf(m125_sleeve_sdf_factory(P.m125_sleeve_outer_diameter),sleeve_bounds,P.tpu_voxel,'TPU95_M125_pole_sleeve_OD15_8')
    pole_liner_a=make_mesh_from_sdf(split_positive_y(pole_liner_full_sdf),pole_liner_bounds,P.tpu_voxel,'TPU95_pole_collar_liner_A')
    pole_liner_b=make_mesh_from_sdf(split_negative_y(pole_liner_full_sdf),pole_liner_bounds,P.tpu_voxel,'TPU95_pole_collar_liner_B')

    print('Generating TPU85 static sealing parts...')
    lid_gasket=make_mesh_from_sdf(lid_gasket_sdf,gasket_bounds,P.tpu_voxel,'TPU85_lid_gasket')
    photo_gasket=make_mesh_from_sdf(photo_window_gasket_sdf,photo_retainer_bounds,P.tpu_voxel,'TPU85_photo_window_gasket')
    env_pocket_gasket=make_mesh_from_sdf(environment_pocket_gasket_sdf,env_gasket_bounds,P.tpu_voxel,'TPU85_environment_pocket_gasket')

    petg_print={}
    for name,m,tr in [
        ('rotor_half_A_print_flat',rotor_a,rot_x(90)),
        ('rotor_half_B_print_flat',rotor_b,rot_x(-90)),
        ('stationary_collar_A_print_flat',collar_a,rot_x(90)),
        ('stationary_collar_B_print_flat',collar_b,rot_x(-90)),
        ('service_lid_top_face_down',lid,rot_x(180)),
        ('photo_tunnel_upright',photo,np.eye(4)),
        ('photo_window_retainer_flat',photo_retainer,np.eye(4)),
        ('environment_sensor_pocket_open_side_up',env_pocket,np.eye(4)),
        ('electronics_carrier_open_side_up',carrier,np.eye(4)),
        ('VEML7700_cradle_flat',veml_cradle,np.eye(4)),
    ]:
        o=m.copy(); o.apply_transform(tr); petg_print[name]=put_on_bed(o)

    tpu95_print={}
    for name,m,tr in [
        ('spoke_liner_A_split_face_down',spoke_a,rot_x(90)),
        ('spoke_liner_B_split_face_down',spoke_b,rot_x(-90)),
        ('flag_cable_grommet_A_split_face_down',cable_a,rot_x(90)),
        ('flag_cable_grommet_B_split_face_down',cable_b,rot_x(-90)),
        ('M125_bundle_grommet_A_split_face_down',bundle_a,rot_x(90)),
        ('M125_bundle_grommet_B_split_face_down',bundle_b,rot_x(-90)),
        ('M125_pole_sleeve_upright',sleeve,np.eye(4)),
        ('pole_collar_liner_A_split_face_down',pole_liner_a,rot_x(90)),
        ('pole_collar_liner_B_split_face_down',pole_liner_b,rot_x(-90)),
    ]:
        o=m.copy(); o.apply_transform(tr); tpu95_print[name]=put_on_bed(o)
    tpu95_print['flag_side_wire_guide_slit_up']=center_xy_on_bed(flag_side_guide)

    tpu85_print={
        'lid_gasket_flat':put_on_bed(lid_gasket),
        'photo_window_gasket_flat':put_on_bed(photo_gasket),
        'environment_pocket_gasket_flat':put_on_bed(env_pocket_gasket),
    }

    exported=[]
    for name,m in petg_print.items(): exported.append(export_stl(m,PETG_DIR/f'{name}.stl'))
    for name,m in tpu95_print.items(): exported.append(export_stl(m,TPU95_DIR/f'{name}.stl'))
    for name,m in tpu85_print.items(): exported.append(export_stl(m,TPU85_DIR/f'{name}.stl'))

    coupon_meshes={}
    for d in (32.20,32.35,32.50):
        sdf=bearing_coupon_sdf_factory(d); b=((-23,23),(-23,23),(-2,12))
        ca=make_mesh_from_sdf(split_positive_y(sdf),b,P.coupon_voxel,f'Bearing_coupon_{d:.2f}_A')
        cb=make_mesh_from_sdf(split_negative_y(sdf),b,P.coupon_voxel,f'Bearing_coupon_{d:.2f}_B')
        ca.apply_transform(rot_x(90)); ca=put_on_bed(ca)
        cb.apply_transform(rot_x(-90)); cb=put_on_bed(cb)
        coupon_meshes[f'bearing_seat_{d:.2f}_half_A']=ca
        coupon_meshes[f'bearing_seat_{d:.2f}_half_B']=cb
    coupon_meshes['PETG_lid_gasket_groove_coupon']=put_on_bed(make_mesh_from_sdf(lid_gasket_coupon_petg_sdf,((-24,24),(-16,16),(-1,7)),P.coupon_voxel,'PETG_lid_gasket_coupon'))
    coupon_meshes['TPU85_lid_gasket_coupon']=put_on_bed(make_mesh_from_sdf(lid_gasket_coupon_tpu_sdf,((-21,21),(-13,13),(-1,4)),P.tpu_voxel,'TPU85_lid_gasket_coupon'))
    for d in (15.60,15.80,16.00):
        sm=make_mesh_from_sdf(m125_sleeve_sdf_factory(d),sleeve_bounds,P.tpu_voxel,f'TPU95_M125_sleeve_OD{d:.2f}')
        coupon_meshes[f'TPU95_M125_sleeve_OD_{d:.2f}']=put_on_bed(sm)
    coupon_meshes['PETG_M4_captive_nut_trap_coupon']=put_on_bed(make_mesh_from_sdf(nut_trap_coupon_sdf,((-20,20),(-12,12),(-1,10)),P.coupon_voxel,'PETG_M4_nut_trap_coupon'))
    coupon_meshes['PETG_M3_captive_nut_trap_coupon']=put_on_bed(make_mesh_from_sdf(m3_nut_trap_coupon_sdf,((-20,20),(-12,12),(-1,9)),P.coupon_voxel,'PETG_M3_nut_trap_coupon'))
    coupon_meshes['PETG_drill_skin_0.6_0.8_1.0_coupon']=put_on_bed(make_mesh_from_sdf(drill_skin_coupon_sdf,((-24,24),(-12,12),(-1,7)),P.coupon_voxel,'PETG_drill_skin_coupon'))
    coupon_meshes['PETG_twin_wire_rail_4.2x2.5_coupon']=put_on_bed(make_mesh_from_sdf(twin_wire_rail_coupon_sdf,((-31,31),(-13,13),(-1,6)),P.coupon_voxel,'PETG_twin_wire_rail_coupon'))
    coupon_meshes['PETG_VEML7700_cradle_coupon']=center_xy_on_bed(veml_cradle.copy())
    coupon_meshes['PETG_photo_tunnel_15_18_comparison_coupon']=put_on_bed(make_mesh_from_sdf(photo_tunnel_comparison_coupon_sdf,((-28,28),(-15,15),(-1,23)),P.coupon_voxel,'PETG_photo_tunnel_15_18_coupon'))
    for name,m in coupon_meshes.items(): exported.append(export_stl(m,COUPON_DIR/f'{name}.stl'))

    ORANGE_A=[235,116,40,255]; ORANGE_B=[246,145,67,255]
    WHITE95=[145,154,160,255]; WHITE85=[188,196,202,255]
    PETG_DARK=[220,94,28,255]
    photo_global=[P.photo_tunnel_center_x,0,48.0]
    photo_top=photo_global[2]+P.photo_tunnel_height
    cradle_global=P.veml_cradle_center
    assembly={
        'PETG_rotor_half_A':colored_copy(rotor_a,ORANGE_A),
        'PETG_rotor_half_B':colored_copy(rotor_b,ORANGE_B),
        'PETG_service_lid':colored_copy(lid,PETG_DARK),
        'PETG_photo_tunnel':colored_copy(translate(photo,photo_global),ORANGE_A),
        'PETG_photo_window_retainer':colored_copy(translate(photo_retainer,[P.photo_tunnel_center_x,0,photo_top]),PETG_DARK),
        'PETG_environment_sensor_pocket':colored_copy(env_pocket,ORANGE_B),
        'PETG_electronics_carrier':colored_copy(carrier,PETG_DARK),
        'PETG_VEML7700_cradle':colored_copy(translate(veml_cradle,cradle_global),ORANGE_A),
        'PETG_stationary_collar_A':colored_copy(translate(collar_a,[0,0,50]),ORANGE_A),
        'PETG_stationary_collar_B':colored_copy(translate(collar_b,[0,0,50]),ORANGE_B),
        'TPU95_spoke_liner_A':colored_copy(spoke_a,WHITE95),
        'TPU95_spoke_liner_B':colored_copy(spoke_b,WHITE95),
        'TPU95_flag_cable_grommet_A':colored_copy(cable_a,WHITE95),
        'TPU95_flag_cable_grommet_B':colored_copy(cable_b,WHITE95),
        'TPU95_flag_side_wire_guide':colored_copy(flag_side_guide,WHITE95),
        'TPU95_M125_bundle_grommet_A':colored_copy(bundle_a,WHITE95),
        'TPU95_M125_bundle_grommet_B':colored_copy(bundle_b,WHITE95),
        'TPU95_M125_pole_sleeve':colored_copy(translate(sleeve,[0,0,42]),WHITE95),
        'TPU95_pole_collar_liner_A':colored_copy(translate(pole_liner_a,[0,0,50]),WHITE95),
        'TPU95_pole_collar_liner_B':colored_copy(translate(pole_liner_b,[0,0,50]),WHITE95),
        'TPU85_lid_gasket':colored_copy(translate(lid_gasket,[0,0,49.50]),WHITE85),
        'TPU85_photo_window_gasket':colored_copy(translate(photo_gasket,[P.photo_tunnel_center_x,0,photo_top-P.photo_window_nominal_thickness]),WHITE85),
        'TPU85_environment_pocket_gasket':colored_copy(translate(env_pocket_gasket,[0,0,15.90]),WHITE85),
    }
    assembly.update(create_references())
    assembly_path=ROOT/'flagpole_finial_v0_6_assembly.glb'
    assembly_path.write_bytes(to_glb_scene(assembly,f'Flagpole finial v{CURRENT_VERSION} assembly').export(file_type='glb'))

    route_names={
        'PETG_rotor_half_A','PETG_rotor_half_B','PETG_service_lid','PETG_electronics_carrier',
        'TPU95_flag_cable_grommet_A','TPU95_flag_cable_grommet_B','TPU95_flag_side_wire_guide',
        'REF_flag_power_cable_external_route','REF_waterproof_2pin_connector_provisional',
        'REF_ESP32_C3_SuperMini_vertical','REF_buck_12_to_5_flat','REF_PC817_LR7843_vertical'}
    route_scene={name:mesh for name,mesh in assembly.items() if name in route_names}
    short_spoke=cylinder_between([P.spoke_insert_x_min,0,P.spoke_center_z],[105.0,0,P.spoke_center_z],P.spoke_diameter/2,48)
    route_scene['REF_carbon_spoke_short']=colored_copy(short_spoke,[28,32,36,255])
    route_path=ROOT/'flagpole_finial_v0_6_flag_power_route.glb'
    route_path.write_bytes(to_glb_scene(route_scene,f'Flag power route v{CURRENT_VERSION}').export(file_type='glb'))

    electronics_names={
        'PETG_electronics_carrier','PETG_VEML7700_cradle','PETG_service_lid',
        'REF_ESP32_C3_SuperMini_vertical','REF_buck_12_to_5_flat','REF_PC817_LR7843_vertical',
        'REF_VEML7700_board_provisional','TPU85_lid_gasket'}
    electronics_scene={name:mesh for name,mesh in assembly.items() if name in electronics_names or name.startswith('REF_M3_cradle_')}
    electronics_scene['PETG_rotor_half_A_retracted']=translate(assembly['PETG_rotor_half_A'],[0,30,0])
    electronics_scene['PETG_rotor_half_B_retracted']=translate(assembly['PETG_rotor_half_B'],[0,-30,0])
    electronics_scene['PETG_service_lid_raised']=translate(assembly['PETG_service_lid'],[0,0,22])
    electronics_path=ROOT/'flagpole_finial_v0_6_electronics_layout.glb'
    electronics_path.write_bytes(to_glb_scene(electronics_scene,f'Electronics layout v{CURRENT_VERSION}').export(file_type='glb'))

    exploded={}
    explode_offsets={
        'PETG_rotor_half_A':[0,35,0], 'PETG_rotor_half_B':[0,-35,0],
        'PETG_service_lid':[0,0,28], 'PETG_photo_tunnel':[0,0,42],
        'PETG_photo_window_retainer':[0,0,55], 'PETG_environment_sensor_pocket':[0,0,-28],
        'PETG_electronics_carrier':[-4,0,8], 'PETG_VEML7700_cradle':[0,0,25],
        'PETG_stationary_collar_A':[0,25,0], 'PETG_stationary_collar_B':[0,-25,0],
        'TPU95_spoke_liner_A':[10,22,0], 'TPU95_spoke_liner_B':[10,-22,0],
        'TPU95_flag_cable_grommet_A':[16,18,0], 'TPU95_flag_cable_grommet_B':[16,-18,0],
        'TPU95_flag_side_wire_guide':[18,-12,-6],
        'TPU85_lid_gasket':[0,0,18], 'TPU85_environment_pocket_gasket':[0,0,-14],
    }
    for name,m in assembly.items():
        if name.startswith('REF_'): continue
        exploded[name]=translate(m,explode_offsets.get(name,[0,0,0]))
    exploded_path=ROOT/'flagpole_finial_v0_6_exploded.glb'
    exploded_path.write_bytes(to_glb_scene(exploded,f'Flagpole finial v{CURRENT_VERSION} exploded').export(file_type='glb'))

    def build_layout(parts, positions, title, path, colors):
        scene={}
        for index,(name,key,pos) in enumerate(positions):
            scene[name]=colored_copy(translate(parts[key],pos),colors[index%len(colors)])
        path.write_bytes(to_glb_scene(scene,title).export(file_type='glb'))
        return path

    petg_positions=[
        ('rotor_A','rotor_half_A_print_flat',[0,0,0]),
        ('rotor_B','rotor_half_B_print_flat',[0,100,0]),
        ('lid','service_lid_top_face_down',[-92,0,0]),
        ('collar_A','stationary_collar_A_print_flat',[-92,60,0]),
        ('collar_B','stationary_collar_B_print_flat',[-92,95,0]),
        ('photo_tunnel','photo_tunnel_upright',[-128,65,0]),
        ('photo_retainer','photo_window_retainer_flat',[-128,92,0]),
        ('env_pocket','environment_sensor_pocket_open_side_up',[-148,5,0]),
        ('electronics_carrier','electronics_carrier_open_side_up',[-155,65,0]),
        ('veml_cradle','VEML7700_cradle_flat',[-122,125,0]),
    ]
    petg_layout_path=build_layout(petg_print,petg_positions,f'PETG print layout v{CURRENT_VERSION}',ROOT/'flagpole_finial_v0_6_print_layout_PETG.glb',[ORANGE_A,ORANGE_B])
    tpu95_positions=[(name,name,[(idx%4)*75,(idx//4)*45,0]) for idx,name in enumerate(tpu95_print)]
    tpu95_layout_path=build_layout(tpu95_print,tpu95_positions,f'TPU95 print layout v{CURRENT_VERSION}',ROOT/'flagpole_finial_v0_6_print_layout_TPU95.glb',[WHITE95])
    tpu85_positions=[(name,name,[(idx%4)*75,(idx//4)*45,0]) for idx,name in enumerate(tpu85_print)]
    tpu85_layout_path=build_layout(tpu85_print,tpu85_positions,f'TPU85 print layout v{CURRENT_VERSION}',ROOT/'flagpole_finial_v0_6_print_layout_TPU85.glb',[WHITE85])

    meshes={
        'rotor_half_A':rotor_a,'rotor_half_B':rotor_b,'service_lid':lid,
        'photo_tunnel':photo,'photo_retainer':photo_retainer,'environment_sensor_pocket':env_pocket,
        'electronics_carrier':carrier,'VEML7700_cradle':veml_cradle,
        'stationary_collar_A':collar_a,'stationary_collar_B':collar_b,
        'spoke_liner_A':spoke_a,'spoke_liner_B':spoke_b,
        'flag_cable_grommet_A':cable_a,'flag_cable_grommet_B':cable_b,'flag_side_wire_guide':flag_side_guide,
        'bundle_grommet_A':bundle_a,'bundle_grommet_B':bundle_b,
        'lid_gasket':lid_gasket,'photo_gasket':photo_gasket,
        'environment_pocket_gasket':env_pocket_gasket,
        'm125_sleeve':sleeve,'pole_liner_A':pole_liner_a,'pole_liner_B':pole_liner_b,
    }
    generated_glb=[assembly_path,route_path,electronics_path,exploded_path,petg_layout_path,tpu95_layout_path,tpu85_layout_path]
    diagnostics={
        'version':f'{CURRENT_VERSION} PETG+TPU95+TPU85 provisional',
        'design_status':'Print coupons first; all purchased-part fits remain measurement-driven',
        'parameters_mm':asdict(P),
        'derived_mm':{
            'bearing_center_spacing':P.upper_bearing_center_z-P.lower_bearing_center_z,
            'spoke_engagement_length':P.spoke_insert_x_max-P.spoke_insert_x_min,
            'lid_gasket_nominal_compression':P.gasket_thickness-P.gasket_groove_depth,
            'm4_nut_pocket_clearance_across_flats':P.m4_nut_pocket_across_flats-P.m4_nut_across_flats,
            'm3_nut_pocket_clearance_across_flats':P.m3_nut_pocket_across_flats-P.m3_nut_across_flats,
            'flag_side_guide_angle_down_deg':round(math.degrees(math.atan2(-guide_axis()[2],guide_axis()[0])),2),
            'flag_loop_top_offsets':flag_loop_top_offsets(),
            'environment_membrane_open_area_mm2':P.env_vent_hole_count*math.pi*(P.env_vent_hole_diameter/2)**2,
            'photo_tunnel_field_half_angle_deg':round(math.degrees(math.atan((P.photo_window_retainer_inner_diameter/2)/P.photo_tunnel_height)),2),
        },
        'meshes':{name:mesh_diagnostics(m) for name,m in meshes.items()},
        'files':[str(p.relative_to(ROOT)) for p in exported]+[p.name for p in generated_glb],
    }
    (ROOT/'model_parameters_and_diagnostics_v06.json').write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'project_manifest_v06.json').write_text(json.dumps({
        'version':CURRENT_VERSION,
        'printer':'Bambu Lab X1 Carbon, 0.4 mm nozzle',
        'materials':{
            'structural_current':'orange PETG','structural_future_option':'ASA after reprinting fit coupons',
            'functional_soft':'TPU 95A','seals':'TPU 85A'},
        'generated_files':diagnostics['files'],
    },ensure_ascii=False,indent=2),encoding='utf-8')

    print(f'Generated v{CURRENT_VERSION} files (stable v0_6 paths retained):')
    for p in exported+generated_glb: print(' -',p.relative_to(ROOT))
    print(json.dumps(diagnostics['derived_mm'],ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
