#!/usr/bin/env python3
"""Generate the canonical 23-part PETG/TPU build123d line for v0.7.6.

Scope is deliberately narrow: printable solids, their STEP/STL files and the
exploded model #204.  Reference drawings and non-print assembly/electronics
scenes remain on the legacy generators and are never regenerated here.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path

import build123d
from build123d import (
    Align, Box, Cone, Cylinder, Location, RectangleRounded, RegularPolygon,
    export_step, export_stl, extrude,
)
import trimesh


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build123d_v076"
PETG_DIR = ROOT / "stl_petg_v06"
TPU95_DIR = ROOT / "stl_tpu95_v06"
TPU85_DIR = ROOT / "stl_tpu85_v06"
for directory in (OUT, PETG_DIR, TPU95_DIR, TPU85_DIR):
    directory.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class P:
    bearing_seat_d: float = 32.36
    pole_d: float = 20.0
    spoke_d: float = 5.0
    m4_clear: float = 4.5
    m4_hex: float = 7.30
    m3_clear: float = 3.5
    m3_hex: float = 5.80
    # The guide socket belongs to rotor half B and starts on the lower
    # pole-hugging skirt, not below or outside the printed body.
    guide_start: tuple[float, float, float] = (15.2, -17.2, 4.8)
    guide_end: tuple[float, float, float] = (29.2, -17.2, -5.0)
    # Electronics enclosure.  Keep the sealing plane completely outside the
    # rotor tower; only the lower structural neck is allowed to reach inward.
    box_cx: float = -60.0
    box_outer_x: float = 72.0
    box_outer_y: float = 42.0
    box_inner_x: float = 64.0
    box_inner_y: float = 34.0
    box_top_z: float = 50.0
    lid_outer_x: float = 74.0
    lid_outer_y: float = 44.0
    lid_bottom_z: float = 51.2
    lid_groove_depth: float = 0.3
    gasket_free_height: float = 2.0
    gasket_working_height: float = 1.5


PARAM = P()
LID_POINTS = ((-91, -16), (-91, 16), (-29, -16), (-29, 16))
DRY_OPENING_X = 54.0
DRY_OPENING_Y = 31.6
DRY_OPENING_RADIUS = 8.8


def loc(shape, xyz=(0.0, 0.0, 0.0), rot=(0.0, 0.0, 0.0)):
    return shape.located(Location(xyz, rot))


def box(x, y, z, center):
    return loc(Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.CENTER)), center)


def rounded(x, y, z, radius, center):
    profile = RectangleRounded(x, y, radius)
    return loc(extrude(profile, amount=z), (center[0], center[1], center[2] - z / 2))


def cyl_z(radius, height, center):
    return loc(Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.CENTER)), center)


def cyl_x(radius, length, center):
    return loc(Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.CENTER)), center, (0, 90, 0))


def cyl_y(radius, length, center):
    return loc(Cylinder(radius, length, align=(Align.CENTER, Align.CENTER, Align.CENTER)), center, (90, 0, 0))


def hex_z(across_flats, height, center):
    profile = RegularPolygon(across_flats / math.sqrt(3), 6)
    return loc(extrude(profile, amount=height), (center[0], center[1], center[2] - height / 2))


def hex_y(across_flats, length, center):
    return loc(hex_z(across_flats, length, (0, 0, 0)), center, (90, 0, 0))


def top_loaded_m3_well(solid, x, y, top_z, pocket_bottom_z):
    """Cut a top-open M3 nut well with a short blind screw-tail relief."""
    pocket_height = top_z - pocket_bottom_z + 0.2
    solid -= hex_z(PARAM.m3_hex, pocket_height, (x, y, pocket_bottom_z + pocket_height / 2))
    tail_bottom = pocket_bottom_z - 1.5
    solid -= cyl_z(PARAM.m3_clear / 2, 1.7, (x, y, tail_bottom + 0.85))
    return solid


def half(shape, positive_y: bool):
    clip = Box(260, 140, 220, align=(Align.CENTER, Align.MIN if positive_y else Align.MAX, Align.MIN))
    clip = loc(clip, (0, 0, -30))
    return (shape & clip).clean()


def annulus(od, id_, height, center=(0, 0, 0)):
    return cyl_z(od / 2, height, center) - cyl_z(id_ / 2, height + 2, center)


def rotor_full():
    body = cyl_z(22.6, 56, (0, 0, 28))
    skirt = cyl_z(23.0, 18, (0, 0, 1))
    tower = loc(Cone(22.6, 16.0, 22, align=(Align.CENTER, Align.CENTER, Align.MIN)), (0, 0, 52))
    arm = rounded(64, 30, 34, 4, (40, 0, 31))
    pod = rounded(PARAM.box_outer_x, PARAM.box_outer_y, 40, 4, (PARAM.box_cx, 0, 30))
    # The neck joins the enclosure to the rotor below the sealing plane.  It
    # must not protrude under the lid or distort its rectangular mating rim.
    pod_neck = rounded(12, 30, 30, 3, (-22.5, 0, 28))
    solid = body + skirt + tower + arm + pod + pod_neck

    for x, z in ((-22, 10), (22, 10), (-22, 44), (22, 44), (-68, 22), (-68, 40), (50, 19), (50, 35)):
        solid += cyl_y(7.2, 31.2, (x, 0, z))
    holes = [
        cyl_z(16.8, 15, (0, 0, -1.5)),
        cyl_z(10.6, 54, (0, 0, 32)),
        cyl_z(PARAM.bearing_seat_d / 2, 7.3, (0, 0, 10)),
        cyl_z(PARAM.bearing_seat_d / 2, 7.8, (0, 0, 44)),
        cyl_z(12.4, 27, (0, 0, 27)),
        cyl_z(15.0, 21, (0, 0, 62)),
        # Continuous spoke bore: starts inside the rotor and opens through
        # the flag-side end face of both clamshell halves.
        cyl_x(3.93, 59, (44.5, 0, 27)),
        cyl_x(4.68, 3.2, (16.6, 0, 27)),
        cyl_x(4.68, 4.5, (70.75, 0, 27)),
        box(48, 0.7, 35, (48, 0, 31)),
        cyl_x(4.88, 10.5, (-13, 0, 18)),
        # Open-top rectangular cavity leaves a uniform 4 mm mating rim.
        rounded(PARAM.box_inner_x, PARAM.box_inner_y, 37, 3, (PARAM.box_cx, 0, 33.5)),
        cyl_x(4.26, 11, (-16.5, 0, 47)),
    ]
    for hole in holes:
        solid -= hole
    for x, z in ((-22, 10), (22, 10), (-22, 44), (22, 44), (-68, 22), (-68, 40), (50, 19), (50, 35)):
        solid -= cyl_y(PARAM.m4_clear / 2, 40, (x, 0, z))

    # Continuous inner sealing shelf. The TPU85 gasket sits on this land and
    # encloses only the dry electronics opening; all four lid screws remain in
    # the outer wet zone. A small overlap with the existing cavity wall makes
    # the shelf a fused part of the enclosure rather than a tangent surface.
    sealing_shelf = (
        rounded(67.0, 38.4, 2.5, 5.0, (PARAM.box_cx, 0, 48.75)) -
        rounded(DRY_OPENING_X, DRY_OPENING_Y, 3.5, DRY_OPENING_RADIUS, (PARAM.box_cx, 0, 48.75))
    )
    solid += sealing_shelf

    # Add the service-lid pillars after hollowing the enclosure. Each pillar
    # remains a full internal column instead of being cut into a thin crescent
    # by the electronics cavity. A 10 mm OD and 18 mm height leave more PETG
    # around the M3 nut and transfer tightening load deeper into the enclosure.
    for x, y in LID_POINTS:
        solid += cyl_z(5.0, 18.0, (x, y, 42.2))

    # Restore the #petg-8 pillars after the cavity subtraction as well, keeping
    # their later nut and screw-tail cuts blind to the electronics bay.
    for y in (-18, 18):
        solid += cyl_z(4.6, 10.0, (-61, y, 14.0))

    # Open raised rail: floor and two walls remain drainable from below.
    solid += rounded(50, 7.0, 1.2, 0.8, (-15, -22.2, 5.0))
    solid += rounded(50, 1.4, 3.7, 0.6, (-15, -25.0, 6.3))
    solid += rounded(50, 1.4, 3.7, 0.6, (-15, -19.4, 6.3))

    # Socket on the lower pole-hugging rounding for the closed TPU guide.
    start, end = PARAM.guide_start, PARAM.guide_end
    mid = tuple((a + b) / 2 for a, b in zip(start, end))
    length = math.dist(start, end)
    angle = math.degrees(math.atan2(end[0] - start[0], end[2] - start[2]))
    socket_outer_length = 7.0
    socket_outer = loc(Cylinder(6.9, socket_outer_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)), start, (0, angle, 0))
    # Blind 5 mm socket: its inner end stops 2 mm before the back of the added
    # boss, so #petg-2_ввод_флага cannot form a through-hole into the rotor.
    axis = tuple((b - a) / length for a, b in zip(start, end))
    socket_depth = 5.0
    cavity_offset = (socket_outer_length - socket_depth) / 2
    cavity_center = tuple(a + u * cavity_offset for a, u in zip(start, axis))
    socket_inner = loc(Cylinder(5.45, socket_depth, align=(Align.CENTER, Align.CENTER, Align.CENTER)), cavity_center, (0, angle, 0))
    solid += socket_outer
    solid -= socket_inner
    return solid.clean()


def rotor_half(positive_y):
    result = half(rotor_full(), positive_y)
    # Six body nuts and two spoke-clamp nuts live in B; screw heads remain on A.
    if not positive_y:
        for index, (x, z) in enumerate(((-22, 10), (22, 10), (-22, 44), (22, 44), (-68, 22), (-68, 40), (50, 19), (50, 35)), 1):
            result -= hex_y(PARAM.m4_hex, 3.5, (x, -12.4, z))
            result -= box(6.9, 7.5, 3.1, (x, -16.2, z))
    # Lid nuts drop into blind wells from the service side after the lid is
    # removed. No loading slot opens through the enclosure's outside wall.
    lid_points = tuple((x, y) for x, y in LID_POINTS if (y > 0) == positive_y)
    for x, y in lid_points:
        result = top_loaded_m3_well(result, x, y, 51.2, 47.0)
    # Climate-pocket nuts also drop from the mating/service side into blind
    # wells. Their screw-tail relief stops above the enclosure interior.
    y = 18 if positive_y else -18
    result = top_loaded_m3_well(result, -61, y, 19.0, 14.8)
    return result.clean()


def service_lid_groove():
    cx = PARAM.box_cx
    groove_z = PARAM.lid_bottom_z + PARAM.lid_groove_depth / 2
    # Strongly rounded corners route the seal inward around the four wet screw
    # wells while leaving a wider central opening for the electronics carrier.
    return (rounded(60.0, 36.8, PARAM.lid_groove_depth, 10.0, (cx, 0, groove_z)) -
            rounded(55.6, 32.4, PARAM.lid_groove_depth + 1, 9.2, (cx, 0, groove_z)))


def service_lid():
    cx = PARAM.box_cx
    plate_h = 3.6
    plate = rounded(PARAM.lid_outer_x, PARAM.lid_outer_y, plate_h, 4, (cx, 0, PARAM.lid_bottom_z + plate_h / 2))
    # A shallow skirt locates the lid inside the new dry opening. Its 0.4 mm
    # clearance per side prevents it from becoming the sealing surface.
    skirt = (rounded(53.2, 30.8, 1.4, 8.4, (cx, 0, 50.5)) -
             rounded(49.2, 26.8, 3.0, 7.6, (cx, 0, 50.5)))
    solid = plate + skirt
    # The 0.3 mm recess leaves 1.5 mm for a 2.0 mm TPU85 gasket: 25% squeeze.
    solid -= service_lid_groove()
    # Wide lower-ring recess makes the light tunnel easy to locate and glue.
    solid -= cyl_z(8.25, 2.5, (-69, 0, 51.1))
    solid -= cyl_z(5.7, 10, (-69, 0, 52))
    for x, y in LID_POINTS:
        solid -= cyl_z(PARAM.m3_clear / 2, 12, (x, y, 51))
    return solid.clean()


def photo_tunnel():
    solid = cyl_z(5.5, 15, (0, 0, 7.5)) + cyl_z(8, 2.2, (0, 0, 1.1))
    solid -= cyl_z(2.55, 6.6, (0, 0, 2.8))
    solid -= cyl_z(1.95, 1.4, (0, 0, 7.1))
    solid -= cyl_z(2.55, 6.3, (0, 0, 10.8))
    solid -= cyl_z(4.15, 1.25, (0, 0, 14.38))
    # The glue reservoir opens onto the bonding face; it is not a sealed void.
    solid -= annulus(14.2, 12.2, 0.65, (0, 0, 0.25))
    return solid.clean()


def photo_retainer():
    return annulus(9.8, 4.4, 1.2, (0, 0, 0.6)).clean()


def collar_full():
    solid = cyl_z(14.5, 14, (0, 0, 7))
    solid -= cyl_z(10.95, 8.5, (0, 0, 4.25))
    solid -= cyl_z(12.2, 2.7, (0, 0, 8.2))
    solid -= cyl_z(6.65, 7, (0, 0, 11))
    for x in (-11, 11):
        solid -= cyl_y(1.8, 38, (x, 0, 4))
    return solid.clean()


def collar_half(positive_y):
    solid = half(collar_full(), positive_y)
    if not positive_y:
        for x in (-11, 11):
            solid -= hex_y(PARAM.m3_hex, 2.7, (x, -11.5, 4))
            solid -= box(5.5, 5.0, 2.2, (x, -14.0, 4))
    return solid.clean()


def environment_pocket():
    cx = -61
    outer = rounded(34, 30, 17.5, 3, (cx, 0, 8.75))
    for y in (-18, 18):
        outer += cyl_z(4.6, 2, (cx, y, 16.5))
    inner = rounded(27, 23, 14.7, 2, (cx, 0, 11.15))
    solid = outer - inner
    # Membrane is bonded from inside; only the active Ø10 zone is perforated.
    solid -= cyl_z(10.2, 0.65, (cx, 0, 0.325))
    for index in range(7):
        if index == 0:
            dx = dy = 0
        else:
            a = 2 * math.pi * (index - 1) / 6
            dx, dy = 3.2 * math.cos(a), 3.2 * math.sin(a)
        solid -= cyl_z(1.0, 2.0, (cx + dx, dy, 2.8))
    # Shallow drip lip only: the membrane is bonded from inside, therefore a
    # tall external skirt adds print risk and catches water without helping
    # retention. Four gaps leave every orientation drainable.
    guard = annulus(22.0, 20.8, 1.0, (cx, 0, -0.5))
    guard -= box(3.2, 26, 2, (cx, 0, -0.5))
    guard -= box(26, 3.2, 2, (cx, 0, -0.5))
    solid += guard
    solid += rounded(1.6, 16, 6.0, 0.5, (cx + 3.8, 0, 6.5))
    for dx in (-6.3, 6.3):
        for dy in (-6.3, 6.3):
            solid += cyl_z(1.05, 2.4, (cx + 3 + dx, dy, 5.0))
    for y in (-18, 18):
        solid -= cyl_z(PARAM.m3_clear / 2, 5, (cx, y, 16.5))
    # Closed drill skin for the cable: mark with a shallow annulus, do not pierce.
    solid -= annulus(8.0, 6.6, 0.35, (cx + 6, -7, 17.325))
    return solid.clean()


def electronics_carrier():
    solid = rounded(36, 24.4, 1.8, 1.2, (-66, 0, 18.5))
    solid += rounded(2, 24.4, 24, 0.8, (-83, 0, 30))
    for x, y in ((-84, -10), (-84, 10), (-58, -10), (-58, 10)):
        solid += rounded(1.8, 1.8, 4.6, 0.45, (x, y, 21.7))
    # Vertical ESP and MOSF frames connected to the tray.
    for y, x0, x1, z1 in ((11.1, -60.5, -35.5, 41), (-11.1, -81.5, -54.5, 44)):
        solid += rounded(2, 2.2, z1 - 18, 0.5, (x0, y, (z1 + 18) / 2))
        solid += rounded(2, 2.2, z1 - 18, 0.5, (x1, y, (z1 + 18) / 2))
        solid += rounded(x1 - x0 + 2, 2.2, 2, 0.5, ((x0 + x1) / 2, y, z1))
    for y in (-11, 11):
        solid += rounded(15, 2.8, 2.4, 0.6, (-75.5, y, 40.5))
        solid += cyl_z(4.2, 3.2, (-69, y, 40.4))
        solid -= cyl_z(PARAM.m3_clear / 2, 7, (-69, y, 40.4))
        solid -= hex_z(PARAM.m3_hex, 2.7, (-69, y, 40.1))
        solid -= box(6.0, 5.0, 2.2, (-69, y + (3.8 if y > 0 else -3.8), 40.1))
    for x in (-78, -64, -51.5):
        solid -= box(4, 16, 4, (x, 0, 18.5))
    return solid.clean()


def veml_cradle():
    solid = rounded(25, 28, 1.8, 1.6, (0, 0, 0.9))
    for x in (-7.15, 7.15):
        for y in (-7.15, 7.15):
            solid += cyl_z(1.5, 0.7, (x, y, 2.15))
    for x in (-5.5, 5.5):
        solid += loc(Cone(0.9, 0.675, 2.2, align=(Align.CENTER, Align.CENTER, Align.MIN)), (x, 0, 1.8))
    # The board is clamped between the lid and four corner pads.  Keep the
    # centre closed: an opening here is neither an optical path nor required
    # by the flat back of the selected VEML7700 module.
    for y in (-11, 11):
        solid -= cyl_z(PARAM.m3_clear / 2, 5, (0, y, 1.5))
    solid -= box(5.3, 10, 3.1, (10.85, 0, 2.95))
    return solid.clean()


def flanged_tube_x(body_d, flange_d, id_, x0, x1, z, split_positive=None):
    length = x1 - x0
    solid = cyl_x(body_d / 2, length - 4, ((x0 + x1) / 2, 0, z))
    solid += cyl_x(flange_d / 2, 2.2, (x0 + 1.1, 0, z))
    solid += cyl_x(flange_d / 2, 2.2, (x1 - 1.1, 0, z))
    solid -= cyl_x(id_ / 2, length + 2, ((x0 + x1) / 2, 0, z))
    return half(solid, split_positive).clean() if split_positive is not None else solid.clean()


def pole_liner(positive):
    solid = annulus(21.65, 20.10, 8, (0, 0, 4)) + annulus(24, 20.10, 2.2, (0, 0, 7.7))
    return half(solid, positive).clean()


def m125_sleeve():
    solid = annulus(15.8, 12.7, 16, (0, 0, 8)) + annulus(19, 12.7, 2, (0, 0, 15))
    solid -= box(3, 1.3, 20, (7.6, 0, 8))
    return solid.clean()


def closed_wire_guide():
    start, end = PARAM.guide_start, PARAM.guide_end
    mid = tuple((a + b) / 2 for a, b in zip(start, end))
    length = math.dist(start, end)
    angle = math.degrees(math.atan2(end[0] - start[0], end[2] - start[2]))
    solid = loc(Cylinder(5.2, length, align=(Align.CENTER, Align.CENTER, Align.CENTER)), mid, (0, angle, 0))
    solid += loc(Cylinder(5.55, 2.1, align=(Align.CENTER, Align.CENTER, Align.CENTER)), start, (0, angle, 0))
    # Two completely closed through channels. No slit to the outer surface.
    for y_offset in (-1.1, 1.1):
        channel_mid = (mid[0], mid[1] + y_offset, mid[2])
        solid -= loc(Cylinder(1.075, length + 3, align=(Align.CENTER, Align.CENTER, Align.CENTER)), channel_mid, (0, angle, 0))
    return solid.clean()


def rounded_ring(outer_x, outer_y, inner_x, inner_y, height, radius, center_x):
    return (rounded(outer_x, outer_y, height, radius, (center_x, 0, height / 2)) -
            rounded(inner_x, inner_y, height + 2, max(0.4, radius - 0.8), (center_x, 0, height / 2))).clean()


PARTS = {
    "PETG_rotor_half_A": ("petg-1_rotor_half_A", lambda: rotor_half(True), PETG_DIR / "rotor_half_A_print_flat.stl", (235, 116, 40, 255), (0, 35, 0)),
    "PETG_rotor_half_B": ("petg-2_rotor_half_B", lambda: rotor_half(False), PETG_DIR / "rotor_half_B_print_flat.stl", (246, 145, 67, 255), (0, -35, 0)),
    "PETG_stationary_collar_A": ("petg-3_stationary_collar_A", lambda: collar_half(True), PETG_DIR / "stationary_collar_A_print_flat.stl", (235, 116, 40, 255), (0, 25, 50)),
    "PETG_stationary_collar_B": ("petg-4_stationary_collar_B", lambda: collar_half(False), PETG_DIR / "stationary_collar_B_print_flat.stl", (246, 145, 67, 255), (0, -25, 50)),
    "PETG_service_lid": ("petg-5_service_lid", service_lid, PETG_DIR / "service_lid_top_face_down.stl", (220, 94, 28, 255), (0, 0, 28)),
    "PETG_photo_tunnel": ("petg-6_photo_tunnel", photo_tunnel, PETG_DIR / "photo_tunnel_upright.stl", (235, 116, 40, 255), (-69, 0, 90)),
    "PETG_photo_window_retainer": ("petg-7_photo_window_retainer", photo_retainer, PETG_DIR / "photo_window_retainer_flat.stl", (220, 94, 28, 255), (-69, 0, 118)),
    "PETG_environment_sensor_pocket": ("petg-8_environment_sensor_pocket", environment_pocket, PETG_DIR / "environment_sensor_pocket_open_side_up.stl", (246, 145, 67, 255), (0, 0, -28)),
    "PETG_electronics_carrier": ("petg-9_electronics_carrier", electronics_carrier, PETG_DIR / "electronics_carrier_open_side_up.stl", (220, 94, 28, 255), (-4, 0, 8)),
    "PETG_VEML7700_cradle": ("petg-10_VEML7700_cradle", veml_cradle, PETG_DIR / "VEML7700_cradle_flat.stl", (235, 116, 40, 255), (-69, 0, 67)),
    "TPU95_spoke_liner_A": ("tpu95-1_spoke_liner_A", lambda: flanged_tube_x(7.5, 9, 5.2, 15, 73, 27, True), TPU95_DIR / "spoke_liner_A_split_face_down.stl", (145, 154, 160, 255), (10, 22, 0)),
    "TPU95_spoke_liner_B": ("tpu95-2_spoke_liner_B", lambda: flanged_tube_x(7.5, 9, 5.2, 15, 73, 27, False), TPU95_DIR / "spoke_liner_B_split_face_down.stl", (145, 154, 160, 255), (10, -22, 0)),
    "TPU95_flag_cable_grommet_A": ("tpu95-3_flag_cable_grommet_A", lambda: flanged_tube_x(9.4, 12, 4.4, -18, -8, 18, True), TPU95_DIR / "flag_cable_grommet_A_split_face_down.stl", (145, 154, 160, 255), (16, 18, 0)),
    "TPU95_flag_cable_grommet_B": ("tpu95-4_flag_cable_grommet_B", lambda: flanged_tube_x(9.4, 12, 4.4, -18, -8, 18, False), TPU95_DIR / "flag_cable_grommet_B_split_face_down.stl", (145, 154, 160, 255), (16, -18, 0)),
    "TPU95_M125_bundle_grommet_A": ("tpu95-5_M125_bundle_grommet_A", lambda: flanged_tube_x(8.2, 10.6, 4.6, -22, -11, 47, True), TPU95_DIR / "M125_bundle_grommet_A_split_face_down.stl", (145, 154, 160, 255), (0, 0, 0)),
    "TPU95_M125_bundle_grommet_B": ("tpu95-6_M125_bundle_grommet_B", lambda: flanged_tube_x(8.2, 10.6, 4.6, -22, -11, 47, False), TPU95_DIR / "M125_bundle_grommet_B_split_face_down.stl", (145, 154, 160, 255), (0, 0, 0)),
    "TPU95_M125_pole_sleeve": ("tpu95-7_M125_pole_sleeve", m125_sleeve, TPU95_DIR / "M125_pole_sleeve_upright.stl", (145, 154, 160, 255), (0, 0, 42)),
    "TPU95_pole_collar_liner_A": ("tpu95-8_pole_collar_liner_A", lambda: pole_liner(True), TPU95_DIR / "pole_collar_liner_A_split_face_down.stl", (145, 154, 160, 255), (0, 25, 50)),
    "TPU95_pole_collar_liner_B": ("tpu95-9_pole_collar_liner_B", lambda: pole_liner(False), TPU95_DIR / "pole_collar_liner_B_split_face_down.stl", (145, 154, 160, 255), (0, -25, 50)),
    "TPU95_flag_side_wire_guide": ("tpu95-10_flag_side_wire_guide_closed", closed_wire_guide, TPU95_DIR / "flag_side_wire_guide_closed.stl", (145, 154, 160, 255), (18, -12, -6)),
    "TPU85_lid_gasket": ("tpu85-1_lid_gasket", lambda: rounded_ring(60.0, 36.8, 55.6, 32.4, 2, 10.0, PARAM.box_cx), TPU85_DIR / "lid_gasket_flat.stl", (188, 196, 202, 255), (0, 0, 18)),
    "TPU85_photo_window_gasket": ("tpu85-2_photo_window_gasket", lambda: annulus(8, 4.4, 0.8, (0, 0, 0.4)), TPU85_DIR / "photo_window_gasket_flat.stl", (188, 196, 202, 255), (-69, 0, 104)),
    "TPU85_environment_pocket_gasket": ("tpu85-3_environment_pocket_gasket", lambda: rounded_ring(32.2, 28.4, 28.3, 24.5, 1.6, 2.6, -61), TPU85_DIR / "environment_pocket_gasket_flat.stl", (188, 196, 202, 255), (0, 0, -14)),
}

PRINT_ROTATION_X = {
    "PETG_rotor_half_A": 90,
    "PETG_rotor_half_B": -90,
    "PETG_stationary_collar_A": 90,
    "PETG_stationary_collar_B": -90,
    "PETG_service_lid": 180,
    "TPU95_spoke_liner_A": 90,
    "TPU95_spoke_liner_B": -90,
    "TPU95_flag_cable_grommet_A": 90,
    "TPU95_flag_cable_grommet_B": -90,
    "TPU95_M125_bundle_grommet_A": 90,
    "TPU95_M125_bundle_grommet_B": -90,
    "TPU95_pole_collar_liner_A": 90,
    "TPU95_pole_collar_liner_B": -90,
}


def main():
    # CAD-level closure checks.  They do not replace a printed water test, but
    # they prevent a lid that intersects the rotor or misses its mating rim.
    assembled_lid = service_lid()
    assembled_rotor = rotor_full()
    lid_collision_mm3 = float((assembled_lid & assembled_rotor).volume)
    gasket_screw_overlap_mm3 = sum(
        float((service_lid_groove() & cyl_z(PARAM.m3_clear / 2, 12, (x, y, 51))).volume)
        for x, y in LID_POINTS
    )
    carrier_box = electronics_carrier().bounding_box().size
    carrier_opening_clearance_x_mm = (DRY_OPENING_X - carrier_box.X) / 2
    carrier_opening_clearance_y_mm = (DRY_OPENING_Y - carrier_box.Y) / 2
    carrier_passage = rounded(DRY_OPENING_X, DRY_OPENING_Y, 100, DRY_OPENING_RADIUS, (PARAM.box_cx, 0, 30))
    carrier_outside_opening_mm3 = float((electronics_carrier() - carrier_passage).volume)
    tower_lid_clearance_mm = (-PARAM.pole_d / 2 - 12.6) - (PARAM.box_cx + PARAM.lid_outer_x / 2)
    gasket_compression_percent = round(
        100 * (PARAM.gasket_free_height - PARAM.gasket_working_height) / PARAM.gasket_free_height,
        1,
    )
    if lid_collision_mm3 > 0.05:
        raise RuntimeError(f"Service lid intersects rotor by {lid_collision_mm3:.3f} mm3")
    if gasket_screw_overlap_mm3 > 0.01:
        raise RuntimeError(f"Lid screw holes intersect the gasket groove by {gasket_screw_overlap_mm3:.3f} mm3")
    if min(carrier_opening_clearance_x_mm, carrier_opening_clearance_y_mm) < 0.4:
        raise RuntimeError(
            "Electronics carrier does not have 0.4 mm per-side clearance through the dry opening: "
            f"X={carrier_opening_clearance_x_mm:.3f}, Y={carrier_opening_clearance_y_mm:.3f} mm"
        )
    if carrier_outside_opening_mm3 > 0.05:
        raise RuntimeError(f"Electronics carrier crosses the rounded dry opening by {carrier_outside_opening_mm3:.3f} mm3")
    if tower_lid_clearance_mm < 0.35:
        raise RuntimeError(f"Service lid/tower clearance is only {tower_lid_clearance_mm:.3f} mm")
    if not 20 <= gasket_compression_percent <= 30:
        raise RuntimeError(f"TPU85 gasket compression is {gasket_compression_percent}%")

    scene = trimesh.Scene(metadata={"title": "Super_pommels_and_flag v0.7.6 canonical build123d exploded"})
    rendered_parts = {}
    printable_parts = {}
    diagnostics = []
    for node, (stem, factory, canonical_stl, color, offset) in PARTS.items():
        solid = factory()
        if not solid.is_valid:
            raise RuntimeError(f"Invalid B-Rep: {node}")
        step_path = OUT / f"{stem}.step"
        native_stl = OUT / f"{stem}.stl"
        export_step(solid, step_path)
        export_stl(solid, native_stl, tolerance=0.08, angular_tolerance=0.12)
        mesh = trimesh.load_mesh(native_stl, force="mesh")
        if not mesh.is_watertight or len(mesh.split(only_watertight=False)) != 1:
            raise RuntimeError(f"Invalid STL topology: {node}")
        print_mesh = mesh.copy()
        angle_x = PRINT_ROTATION_X.get(node, 0)
        if angle_x:
            print_mesh.apply_transform(trimesh.transformations.rotation_matrix(math.radians(angle_x), (1, 0, 0)))
        print_mesh.apply_translation((0, 0, -print_mesh.bounds[0, 2]))
        canonical_stl.write_bytes(print_mesh.export(file_type="stl"))
        printable_parts[node] = print_mesh
        mesh.visual.face_colors = color
        mesh.apply_translation(offset)
        mesh.apply_scale(0.001)
        scene.add_geometry(mesh, node_name=node, geom_name=node)
        rendered_parts[node] = mesh.copy()
        diagnostics.append({
            "node": node,
            "step": step_path.relative_to(ROOT).as_posix(),
            "stl": canonical_stl.relative_to(ROOT).as_posix(),
            "volumeMm3": round(float(solid.volume), 3),
            "watertight": True,
            "connectedBodies": 1,
        })

    if len(scene.graph.nodes_geometry) != 23:
        raise RuntimeError(f"Expected 23 nodes, got {len(scene.graph.nodes_geometry)}")
    glb_path = ROOT / "flagpole_finial_v0_6_exploded.glb"
    glb_path.write_bytes(scene.export(file_type="glb"))

    # Optional lightweight hardware overlay for the fullscreen catalog viewer.
    # It is a separate GLB and can never enter a printable STL.
    hardware_scene = trimesh.Scene(metadata={"title": "Canonical build123d exploded with simplified fasteners"})
    for node, mesh in rendered_parts.items():
        hardware_scene.add_geometry(mesh.copy(), node_name=node, geom_name=node)

    def fastener(axis, radius, length, center_mm, color):
        shank = trimesh.creation.cylinder(radius=radius, height=length, sections=20)
        head = trimesh.creation.cylinder(radius=radius * 1.8, height=max(1.8, radius), sections=6)
        head.apply_translation((0, 0, length / 2 + max(1.8, radius) / 2))
        mesh = trimesh.util.concatenate((shank, head))
        if axis == "y":
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi / 2, (1, 0, 0)))
        mesh.apply_translation(center_mm)
        mesh.visual.face_colors = color
        mesh.apply_scale(0.001)
        return mesh

    fastener_index = 0
    for x, z in ((-22, 10), (22, 10), (-22, 44), (22, 44), (-68, 22), (-68, 40), (50, 19), (50, 35)):
        fastener_index += 1
        mesh = fastener("y", 2.0, 54, (x, 0, z), (92, 98, 104, 255))
        name = f"REF_FASTENER_M4_{fastener_index:02d}"
        hardware_scene.add_geometry(mesh, node_name=name, geom_name=name)
    for x, y in LID_POINTS:
        fastener_index += 1
        mesh = fastener("z", 1.5, 16, (x, y, 57), (116, 122, 128, 255))
        name = f"REF_FASTENER_M3_{fastener_index:02d}"
        hardware_scene.add_geometry(mesh, node_name=name, geom_name=name)
    for x in (-11, 11):
        fastener_index += 1
        mesh = fastener("y", 1.5, 36, (x, 0, 54), (116, 122, 128, 255))
        name = f"REF_FASTENER_M3_{fastener_index:02d}"
        hardware_scene.add_geometry(mesh, node_name=name, geom_name=name)
    # Environmental-sensor pocket and the removable electronics carrier.
    # These are deliberately schematic fasteners: they document access and
    # direction without bloating the catalog model or entering printable STL.
    for x, y, z in ((-61, -18, 10), (-61, 18, 10), (-69, -11, 45), (-69, 11, 45)):
        fastener_index += 1
        mesh = fastener("z", 1.5, 14, (x, y, z), (116, 122, 128, 255))
        name = f"REF_FASTENER_M3_{fastener_index:02d}"
        hardware_scene.add_geometry(mesh, node_name=name, geom_name=name)
    hardware_glb = ROOT / "flagpole_finial_v0_6_exploded_with_fasteners.glb"
    hardware_glb.write_bytes(hardware_scene.export(file_type="glb"))

    def build_print_layout(prefix, output_name, gap, colors):
        entries = [(name, mesh.copy()) for name, mesh in printable_parts.items() if name.startswith(prefix)]
        entries.sort(key=lambda item: max(item[1].extents[:2]), reverse=True)
        # A 4 mm bed margin lets the 74 mm lid occupy the strip beside a
        # 168 mm rotor half.  Rotation about Z is unnecessary and print-safe
        # spacing remains the caller-provided 5/6 mm.
        bed_margin = 4.0
        bed_limit = 256.0 - bed_margin
        x = y = bed_margin
        row_height = 0.0
        layout = trimesh.Scene(metadata={"title": f"{prefix} canonical build123d print layout"})
        for index, (name, mesh) in enumerate(entries):
            width, depth = mesh.extents[:2]
            if x + width > bed_limit + 1e-6:
                x = bed_margin
                y += row_height + gap
                row_height = 0.0
            if y + depth > bed_limit + 1e-6:
                raise RuntimeError(f"{prefix} print layout exceeds 256 mm bed at {name}")
            mesh.apply_translation((x - mesh.bounds[0, 0], y - mesh.bounds[0, 1], 0))
            mesh.visual.face_colors = colors[index % len(colors)]
            mesh.apply_scale(0.001)
            layout.add_geometry(mesh, node_name=name, geom_name=name)
            x += width + gap
            row_height = max(row_height, depth)
        path = ROOT / output_name
        path.write_bytes(layout.export(file_type="glb"))
        return path, len(entries)

    petg_layout, petg_count = build_print_layout("PETG_", "flagpole_finial_v0_6_print_layout_PETG.glb", 6.0, ((235, 116, 40, 255), (246, 145, 67, 255)))
    tpu95_layout, tpu95_count = build_print_layout("TPU95_", "flagpole_finial_v0_6_print_layout_TPU95.glb", 5.0, ((145, 154, 160, 255),))
    tpu85_layout, tpu85_count = build_print_layout("TPU85_", "flagpole_finial_v0_6_print_layout_TPU85.glb", 5.0, ((188, 196, 202, 255),))
    report = {
        "schemaVersion": 2,
        "version": "0.7.6",
        "status": "canonical-build123d",
        "build123dVersion": build123d.__version__,
        "geometryNodes": 23,
        "nativeBuild123dNodes": 23,
        "legacyMeshNodes": 0,
        "wireGuide": "closed twin through-channels; no service slit",
        "guideStartMm": list(PARAM.guide_start),
        "guideEndMm": list(PARAM.guide_end),
        "guideAngleDownDeg": round(math.degrees(math.atan2(PARAM.guide_start[2] - PARAM.guide_end[2], PARAM.guide_end[0] - PARAM.guide_start[0])), 3),
        "spokeBore": "continuous split bore opens through flag-side end face in both rotor halves",
        "environmentDripLipMm": {"outerDiameter": 22.0, "innerDiameter": 20.8, "height": 1.0, "drainGaps": 4},
        "vemlCradleCentre": "solid support; no unjustified central through-hole",
        "electronicsEnclosure": {
            "centreXmm": PARAM.box_cx,
            "outerMm": [PARAM.box_outer_x, PARAM.box_outer_y, PARAM.box_top_z - 10.0],
            "innerMm": [PARAM.box_inner_x, PARAM.box_inner_y, 36.0],
            "lidOuterMm": [PARAM.lid_outer_x, PARAM.lid_outer_y, 3.6],
            "towerToLidClearanceMm": round(tower_lid_clearance_mm, 3),
            "lidCollisionVolumeMm3": round(lid_collision_mm3, 6),
            "gasketScrewOverlapVolumeMm3": round(gasket_screw_overlap_mm3, 6),
            "locatingSkirtClearancePerSideMm": 0.4,
            "dryOpeningMm": [DRY_OPENING_X, DRY_OPENING_Y],
            "carrierOpeningClearancePerSideMm": [round(carrier_opening_clearance_x_mm, 3), round(carrier_opening_clearance_y_mm, 3)],
            "carrierOutsideOpeningVolumeMm3": round(carrier_outside_opening_mm3, 6),
            "gasketFreeHeightMm": PARAM.gasket_free_height,
            "gasketWorkingHeightMm": PARAM.gasket_working_height,
            "gasketCompressionPercent": gasket_compression_percent,
            "seal": "continuous inner shelf and lid groove; all four screw holes stay outside the dry gasket contour",
        },
        "legacyReferenceGeneratorsRun": False,
        "outputGlb": glb_path.relative_to(ROOT).as_posix(),
        "outputSha256": sha256(glb_path.read_bytes()).hexdigest(),
        "hardwareOverlayGlb": hardware_glb.relative_to(ROOT).as_posix(),
        "hardwareOverlaySha256": sha256(hardware_glb.read_bytes()).hexdigest(),
        "simplifiedFastenerNodes": fastener_index,
        "printLayouts": {
            petg_layout.name: petg_count,
            tpu95_layout.name: tpu95_count,
            tpu85_layout.name: tpu85_count,
        },
        "parts": diagnostics,
        "limitations": ["Physical fits, nut retention, sealing and printed strength remain unverified."],
    }
    (OUT / "BUILD123D_CANONICAL_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Generated 23 native build123d parts and canonical exploded #204.")


if __name__ == "__main__":
    main()
