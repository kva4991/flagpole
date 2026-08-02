# Crucian rotating flagpole finial v0.7.4

Crucian is an experimental rotating flagpole-finial project combining printable PETG/TPU mechanics, a 12 V illuminated fish flag, ESP32-C3 firmware, BLE control, a local Android application, and an offline component, drawing, and 3D catalog.

The current cumulative engineering handoff is **v0.7.4**. The mechanics are again generated parametrically rather than copied from transitional meshes. This revision adds captive M4/M3 nuts to every current screw joint, moves the flag-power wires to the owner-marked point through a replaceable guide angled about 35° downward, ties the upper flag strap to the lower finial edge, shortens the VEML7700 light tunnel to 15 mm with a dedicated glue land, adapts the AHT20+BMP280 pocket to a 20 mm adhesive membrane with a 10 mm active centre and seven ventilation holes, and adds a removable two-level electronics carrier.

Rigid parts target the already purchased orange PETG. TPU 95A is used for retained functional soft parts and TPU 85A for static seals. ASA remains a possible future reprint. This is not a production-ready or safety-certified product: purchased-part fits, outdoor durability, sealing, thermal behaviour, wiring, BLE, and structural strength still require physical validation.

## Start here

- [Russian project overview](README.ru.md)
- [Fast start for a new development session](docs/agent-fast-start.ru.md)
- [Current implementation status](docs/current-implementation-status.ru.md)
- [v0.7.4 cumulative update report](UPDATE_REPORT_V074_RU.md)
- [v0.7.4 drawing audit](docs/DRAWING_AUDIT_V074_RU.md)
- [Project identity settings](docs/PROJECT_IDENTITY_RU.md)
- [Required physical measurements](MEASUREMENTS_REQUIRED_RU.md)
- [Architecture decisions](docs/architecture/decisions/README.ru.md)
- [Local component, drawing, and 3D catalog](catalog/catalog.html)

## Repository areas

- `mechanical/` — current parametric model generator, 40 validated STL files, seven current GLB files, drawings, previews, and validation data;
- `electronics/` — current wiring drawings and ESP32-C3 firmware;
- `android/` — local BLE control application prototype;
- `catalog/` — generated offline catalog whose sources are `components.json` and `drawings.json`;
- `docs/` — current status, design rationale, audits, and immutable ADR history;
- `scripts/`, `tools/quality/`, and `tests/` — reproducibility and repository checks.

Stable filenames containing `v0_6` are retained for compatibility, but their current generated content is version 0.7.4.

## Regeneration and checks

```powershell
python mechanical/generate_models_v06.py
python mechanical/validate_models_v06.py
python mechanical/render_previews_v06.py
python mechanical/render_part_id_drawings_v06.py
python mechanical/render_flag_power_route_v06.py
python mechanical/generate_reference_diagrams_v06.py
python mechanical/generate_detail_diagrams_v074.py
python mechanical/generate_hermeticity_diagram_v074.py
python electronics/generate_electronics_diagrams_v074.py
npm.cmd run catalog:generate
npm.cmd run quality:gate
```

The checks validate repository consistency and STL topology. They do not establish a verified IP rating, safe load, fit, temperature, lifetime, or correct operation on real hardware.

## License

No project license has been selected. Public visibility alone does not grant permission to copy, modify, redistribute, or commercially use the project.
