#!/usr/bin/env python3
"""Opt-in build123d source for the lower-pole TPU 85A cable strain relief.

The default invocation writes nothing. Dimensions are read from the source-only
draft JSON. Coupon generation remains opt-in, and final-part generation remains
blocked until the owner records the real lower-segment and cable measurements.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Align, Cylinder, Location, export_step, export_stl


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "cad_drafts" / "tpu85_lower_pole_strain_relief_v076.json"
COUPON_DIR = ROOT / "test_coupons_v06"
TPU85_DIR = ROOT / "stl_tpu85_v06"
STEP_DIR = ROOT / "build123d_v076" / "draft_lower_pole_strain_relief"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def annular_coupon(bore_diameter_mm: float, outer_diameter_mm: float, height_mm: float):
    """Build a simple ring for independent seat or cable-grip fitting."""
    if not 0 < bore_diameter_mm < outer_diameter_mm:
        raise ValueError("The bore must be positive and smaller than the outer diameter")
    outer = Cylinder(outer_diameter_mm / 2, height_mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(bore_diameter_mm / 2, height_mm + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, -1)))
    return (outer - inner).clean()


def paired_wire_coupon(wire_diameter_mm: float, outer_diameter_mm: float, height_mm: float, center_spacing_mm: float = 2.0):
    """Build a two-channel coupon for two separate round power wires."""
    body = Cylinder(outer_diameter_mm / 2, height_mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
    holes = None
    for x in (-center_spacing_mm / 2, center_spacing_mm / 2):
        hole = Cylinder(wire_diameter_mm / 2, height_mm + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((x, 0, -1)))
        holes = hole if holes is None else holes + hole
    return (body - holes).clean()


def ribbed_seat(core_diameter_mm: float, rib_diameter_mm: float, height_mm: float, rib_count: int = 6):
    """Build a compliant seat with six shallow, approximately rounded ribs."""
    if not 0 < core_diameter_mm < rib_diameter_mm:
        raise ValueError("The rib diameter must exceed the seat core diameter")
    if rib_count < 1 or height_mm < 4:
        raise ValueError("The ribbed seat dimensions are invalid")
    body = Cylinder(core_diameter_mm / 2, height_mm, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rib_width = 1.2
    margin = 1.2
    pitch = (height_mm - 2 * margin - rib_width) / max(1, rib_count - 1)
    shoulder_diameter = core_diameter_mm + (rib_diameter_mm - core_diameter_mm) * 0.58
    for index in range(rib_count):
        z = margin + index * pitch
        lower = Cylinder(shoulder_diameter / 2, 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, z)))
        crest = Cylinder(rib_diameter_mm / 2, 0.6, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, z + 0.3)))
        upper = Cylinder(shoulder_diameter / 2, 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, z + 0.9)))
        body += lower + crest + upper
    return body.clean()


def dimension(spec: dict, key: str) -> float:
    for item in spec["finalPart"]["dimensions"]:
        if item["key"] == key:
            return float(item["value"])
    raise KeyError(key)


def strain_relief(spec: dict):
    """Build the closed internal cup and compliant tapered boot from one body."""
    seat_core_od = dimension(spec, "seat-core-diameter")
    rib_od = dimension(spec, "retention-rib-outer-diameter")
    seat_length = dimension(spec, "seat-length")
    rib_count = int(dimension(spec, "retention-rib-count"))
    tail_length = dimension(spec, "flex-tail-length")
    wire_diameter = dimension(spec, "wire-channel-diameter")
    total_length = seat_length + tail_length

    seat = ribbed_seat(seat_core_od, rib_od, seat_length, rib_count)
    # A stepped taper approximates the smooth boot while keeping the source
    # explicit and printable; shallow circumferential valleys provide flex zones.
    boot = Cylinder(7.0, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, seat_length)))
    boot += Cylinder(6.2, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, seat_length + 8.0)))
    boot += Cylinder(5.4, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, seat_length + 16.0)))
    boot += Cylinder(4.7, max(1.0, tail_length - 24.0), align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, seat_length + 24.0)))
    body = (seat + boot).clean()
    bores = None
    for x in (-wire_diameter / 2, wire_diameter / 2):
        bore = Cylinder(wire_diameter / 2, total_length + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((x, 0, -1)))
        bores = bore if bores is None else bores + bore
    return (body - bores).clean()


def export_pair(body, stl_path: Path, step_path: Path) -> None:
    stl_path.parent.mkdir(parents=True, exist_ok=True)
    step_path.parent.mkdir(parents=True, exist_ok=True)
    export_stl(body, str(stl_path))
    export_step(body, str(step_path))


def generate_coupons(spec: dict) -> None:
    names = {
        "S1": "TPU85_lower_pole_seat_S1",
        "S2": "TPU85_lower_pole_seat_S2",
        "S3": "TPU85_lower_pole_seat_S3",
        "C1": "TPU85_lower_pole_cable_C1",
        "C2": "TPU85_lower_pole_cable_C2",
        "C3": "TPU85_lower_pole_cable_C3",
    }
    for coupon_set in spec["couponSets"]:
        for variant in coupon_set["variants"]:
            bore = float(variant.get("boreDiameterMm", coupon_set["common"]["boreDiameterMm"]))
            outer = float(variant.get("outerDiameterMm", coupon_set["common"]["outerDiameterMm"]))
            height = float(coupon_set["common"]["heightMm"])
            if coupon_set["id"] == "cable-grip":
                body = paired_wire_coupon(bore, outer, height)
            else:
                seat = ribbed_seat(float(coupon_set["common"]["coreDiameterMm"]), outer, height, int(coupon_set["common"]["ribCount"]))
                hole = Cylinder(bore / 2, height + 2, align=(Align.CENTER, Align.CENTER, Align.MIN)).located(Location((0, 0, -1)))
                body = (seat - hole).clean()
            stem = names[variant["code"]]
            export_pair(body, COUPON_DIR / f"{stem}.stl", STEP_DIR / f"{stem}.step")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-coupons", action="store_true")
    parser.add_argument("--generate-final", action="store_true")
    args = parser.parse_args()
    spec = load_spec()

    if args.generate_coupons:
        generate_coupons(spec)
    if args.generate_final:
        if spec["finalPart"]["release"] != "approved-after-coupons-and-measurement":
            raise SystemExit("Final generation is blocked until measurements and coupon results are recorded")
        export_pair(
            strain_relief(spec),
            TPU85_DIR / "lower_pole_cable_strain_relief_upright.stl",
            STEP_DIR / "TPU85_lower_pole_cable_strain_relief.step",
        )
    if not args.generate_coupons and not args.generate_final:
        print("Source-only draft: no files generated. Use an explicit flag after measurements are recorded.")


if __name__ == "__main__":
    main()
