# Crucian rotating flagpole finial

Crucian is an experimental rotating flagpole-finial project combining printable ASA/PETG/TPU mechanics, a 12 V illuminated ichthys flag, ESP32-C3 firmware, BLE control, and a local Android application.

The current engineering handoff is **v0.6.1**. It is not a production-ready or safety-certified product. Mechanical fits still depend on physical measurements, and the BLE, power, thermal, weather, and Android paths require real-hardware validation.

## Start here

- [Russian project overview](README.ru.md)
- [Fast start for a new development session](docs/agent-fast-start.ru.md)
- [Current implementation status](docs/current-implementation-status.ru.md)
- [v0.6.1 technical audit](docs/AUDIT_V061_RU.md)
- [Documentation workflow](docs/DOCUMENTATION_WORKFLOW_RU.md)
- [Architecture decisions](docs/architecture/decisions/README.ru.md)
- [Required physical measurements](MEASUREMENTS_REQUIRED_RU.md)

## Repository areas

- `mechanical/` — model generators, printable STL files, GLB assemblies, previews, and validation data;
- `electronics/` — wiring documentation and ESP32-C3 firmware;
- `android/` — the local BLE control application prototype;
- `catalog/` — a generated offline component catalog whose source is `components.json`;
- `docs/` — current status, focused design documents, audit reports, and immutable ADR history;
- `scripts/`, `tools/quality/`, and `tests/` — deterministic documentation and repository checks.

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
