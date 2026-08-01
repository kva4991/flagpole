# Crucian rotating flagpole finial v0.7.2

Crucian is an experimental rotating flagpole-finial project combining printable PETG/TPU mechanics, a 12 V illuminated ichthys flag, ESP32-C3 firmware, BLE control, a local Android application, and an offline component/3D catalog.

The current engineering handoff is **v0.7.2**. The current rigid parts target the owner's already purchased orange PETG; ASA remains a possible future outdoor upgrade when the budget permits. The flag-power cable now follows a serviceable external groove below the spoke and enters the electronics pod through one sealed TPU95 grommet. This is not a production-ready or safety-certified product, and physical fits and hardware behavior still require validation.

## Start here

- [Russian project overview](README.ru.md)
- [Fast start for a new development session](docs/agent-fast-start.ru.md)
- [Current implementation status](docs/current-implementation-status.ru.md)
- [v0.7.2 update report](UPDATE_REPORT_V072_RU.md)
- [v0.7.0 cumulative update report](UPDATE_REPORT_V070_RU.md)
- [Project identity settings](docs/PROJECT_IDENTITY_RU.md)
- [Documentation workflow](docs/DOCUMENTATION_WORKFLOW_RU.md)
- [Architecture decisions](docs/architecture/decisions/README.ru.md)
- [Required physical measurements](MEASUREMENTS_REQUIRED_RU.md)
- [Local component, material, drawing, and 3D catalog](catalog/catalog.html)

## Repository areas

- `mechanical/` — model generators, printable STL files, GLB assemblies, previews, and validation data;
- `electronics/` — wiring documentation and ESP32-C3 firmware;
- `android/` — the local BLE control application prototype;
- `catalog/` — a generated offline component catalog whose source is `components.json`;
- `docs/` — current status, focused design documents, audit reports, and immutable ADR history;
- `scripts/`, `tools/quality/`, and `tests/` — deterministic documentation and repository checks.

## Project materials and drawings page

The generated local page at [`catalog/catalog.html`](catalog/catalog.html) collects the project's components, consumables, construction materials, drawings, and rotatable GLB models. From the repository root on Windows, start its local-only server and open the page with:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\open-component-catalog.ps1
```

The server binds only to `127.0.0.1`. The catalog data is edited in `catalog/components.json` and `catalog/drawings.json`; do not edit the generated HTML by hand.

## Local documentation checks

Node.js is sufficient; the quality scripts have no third-party runtime dependencies.

```powershell
npm.cmd run quality:docs:all
npm.cmd run catalog:check
npm.cmd test
npm.cmd run review:impact
npm.cmd run checksums:check
```

These checks validate repository contracts only. They do not prove printable fit, electrical safety, BLE behavior on hardware, Android interoperability, weather resistance, or a verified IP rating.

## License

No project license has been selected. Public visibility alone does not grant permission to copy, modify, redistribute, or commercially use the code, documentation, or mechanical models.
