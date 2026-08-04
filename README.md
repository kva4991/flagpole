# Super_pommels_and_flag rotating flagpole finial v0.7.6

Super_pommels_and_flag is an experimental rotating flagpole-finial project combining printable PETG/TPU mechanics, a 12 V illuminated fish flag, ESP32-C3 firmware, BLE control, a local Android application, and an offline component, drawing, and 3D catalog.

The current cumulative engineering handoff is **v0.7.6**. All 23 canonical printable parts are generated as native build123d/OCP B-Reps rather than copied from transitional meshes. This revision adds captive M4/M3 nuts to every current screw joint, uses a closed twin-bore flag-power guide angled about 35° downward on the lower rounding of `#petg-2`, shortens the VEML7700 light tunnel to 15 mm with a dedicated glue land, adapts the AHT20+BMP280 pocket to a 20 mm adhesive membrane with a 10 mm active centre and seven ventilation holes, and adds a removable two-level electronics carrier.

Rigid parts target the already purchased orange PETG. TPU 95A is used for retained functional soft parts and TPU 85A for static seals. ASA remains a possible future reprint. This is not a production-ready or safety-certified product: purchased-part fits, outdoor durability, sealing, thermal behaviour, wiring, BLE, and structural strength still require physical validation.

## Start here

- [Russian project overview](README.ru.md)
- [Fast start for a new development session](docs/agent-fast-start.ru.md)
- [Current implementation status](docs/current-implementation-status.ru.md)
- [v0.7.6 cumulative update report](UPDATE_REPORT_V076_RU.md)
- [v0.7.6 drawing audit](docs/DRAWING_AUDIT_V074_RU.md)
- [Project identity settings](docs/PROJECT_IDENTITY_RU.md)
- [Required physical measurements](MEASUREMENTS_REQUIRED_RU.md)
- [Architecture decisions](docs/architecture/decisions/README.ru.md)
- [Licensing map](LICENSE.md)
- [Local component, drawing, and 3D catalog](catalog/catalog.html)

## Repository areas

- `mechanical/` — current parametric model generator, 40 validated STL files, seven current GLB files, drawings, previews, and validation data;
- `electronics/` — current wiring drawings and ESP32-C3 firmware;
- `android/` — local BLE control application prototype;
- `catalog/` — generated offline catalog whose sources include `components.json`, the single physical-measurement registry `physical-components.json`, and `drawings.json`;
- `docs/` — current status, design rationale, audits, and immutable ADR history;
- `scripts/`, `tools/quality/`, and `tests/` — reproducibility and repository checks.

Stable filenames containing `v0_6` are retained for compatibility, but their current generated content is version 0.7.6.

The canonical printable source is `mechanical/generate_build123d_canonical_v076.py` and the native STEP/report output is stored in `mechanical/build123d_v076/`. Legacy reference drawings and non-print interactive scenes keep their existing generators and are regenerated only when the owner explicitly requests them.

## Local component, drawing, and 3D catalog

Run from the repository root on Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\open-component-catalog.ps1
```

The script binds a local server to `127.0.0.1`, opens `catalog/catalog.html`, and enables interactive GLB viewing. Stop it with `Ctrl+C`.

To open the catalog explicitly in Firefox:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\open-component-catalog.ps1 -Browser Firefox
```

## Regeneration and checks

Run the complete model, drawing, catalog and validation pipeline from the synchronized antivirus-safe worktree:

```powershell
.\build.cmd all
```

The `generate`, `validate`, and `catalog` modes are also available. Large `*.stl` and `*.glb` files use Git LFS; PNG remains in regular Git. GitHub Actions downloads LFS only for the conditional mechanical job.

The checks validate repository consistency and STL topology. They do not establish a verified IP rating, safe load, fit, temperature, lifetime, or correct operation on real hardware.

## License

Project-authored hardware design source, including CAD, drawings and generated
STL/GLB, is licensed under `CERN-OHL-S-2.0`. Project-authored Android, firmware
and repository tooling use the MIT License. Third-party material keeps its own
terms and is not relicensed. See the complete [licensing map](LICENSE.md).
