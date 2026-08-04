#!/usr/bin/env python3
"""Opt-in build123d source for the PETG 6806 adapter and fit coupons.

Running the file without an explicit generation flag writes nothing.  Coupon
and final-part geometry share the same annular-ring factory and the dimensions
from mechanical/cad_drafts/petg_6806_adapter_v076.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build123d import Align, Cylinder, Location, export_step, export_stl


ROOT = Path(__file__).resolve().parent
SPEC_PATH = ROOT / "cad_drafts" / "petg_6806_adapter_v076.json"
COUPON_DIR = ROOT / "test_coupons_v06"
PETG_DIR = ROOT / "stl_petg_v06"
STEP_DIR = ROOT / "build123d_v076" / "draft_6806_adapter"


def load_spec() -> dict:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def adapter_ring(bore_diameter_mm: float, outer_diameter_mm: float, height_mm: float):
    """Build the shared rigid PETG annulus used by final parts and coupons."""
    if not 0 < bore_diameter_mm < outer_diameter_mm:
        raise ValueError("The bore must be positive and smaller than the outer diameter")
    if height_mm <= 0:
        raise ValueError("The ring height must be positive")
    outer = Cylinder(
        outer_diameter_mm / 2,
        height_mm,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    inner = Cylinder(
        bore_diameter_mm / 2,
        height_mm + 2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).located(Location((0, 0, -1)))
    return (outer - inner).clean()


def dimension(spec: dict, key: str) -> float:
    for item in spec["finalPart"]["dimensions"]:
        if item["key"] == key:
            return float(item["value"])
    raise KeyError(key)


def export_ring(solid, stem: str, stl_directory: Path) -> None:
    stl_directory.mkdir(parents=True, exist_ok=True)
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    if not solid.is_valid:
        raise RuntimeError(f"Invalid B-Rep: {stem}")
    export_step(solid, STEP_DIR / f"{stem}.step")
    export_stl(solid, stl_directory / f"{stem}.stl", tolerance=0.04, angular_tolerance=0.08)


def generate_coupons(spec: dict) -> None:
    for coupon_set in spec["couponSets"]:
        common = coupon_set["common"]
        for variant in coupon_set["variants"]:
            bore = float(variant.get("boreDiameterMm", common.get("boreDiameterMm")))
            outer = float(variant.get("outerDiameterMm", common.get("outerDiameterMm")))
            height = float(common["heightMm"])
            prefix = "pole_fit" if coupon_set["id"] == "pole" else "bearing_fit"
            stem = f"PETG_6806_{prefix}_{variant['code']}"
            export_ring(adapter_ring(bore, outer, height), stem, COUPON_DIR)


def generate_final(spec: dict) -> None:
    if spec["finalPart"]["release"] != "approved-after-coupons":
        raise RuntimeError("Final adapter is blocked until coupon results approve both fits")
    solid = adapter_ring(
        dimension(spec, "pole-bore-diameter"),
        dimension(spec, "bearing-seat-diameter"),
        dimension(spec, "axial-width"),
    )
    export_ring(solid, "PETG_6806_pole_adapter", PETG_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-coupons", action="store_true")
    parser.add_argument("--generate-final", action="store_true")
    args = parser.parse_args()
    spec = load_spec()
    if not args.generate_coupons and not args.generate_final:
        print("Source-only draft: pass --generate-coupons after owner approval; no files were written.")
        return
    if args.generate_coupons:
        generate_coupons(spec)
    if args.generate_final:
        generate_final(spec)


if __name__ == "__main__":
    main()
