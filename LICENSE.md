# Licensing

Copyright (c) 2026 kva4991 and contributors.

Super_pommels_and_flag is a mixed hardware and software project. The licences
below apply only to material for which the project authors own the necessary
rights. A file that contains its own copyright or licence notice keeps that
notice.

## Open hardware — CERN-OHL-S-2.0

The project-authored hardware design source is licensed under the CERN Open
Hardware Licence Version 2 — Strongly Reciprocal, version 2 only
(`CERN-OHL-S-2.0`). This includes:

- `mechanical/`, including parametric CAD source, manufacturing scripts,
  drawings, STL/GLB exports, print layouts and validation data;
- project-authored electronics schematics, wiring drawings and hardware design
  documentation under `electronics/`, except firmware source;
- flag patterns, mechanical/electrical BOM data, project-authored catalog data,
  design rationale and assembly documentation;
- generated previews and other project-authored representations of the covered
  hardware design.

The complete unmodified licence text is in
[`LICENSES/CERN-OHL-S-2.0.txt`](LICENSES/CERN-OHL-S-2.0.txt).

This source describes Open Hardware and is licensed under CERN-OHL-S v2. You
may redistribute and modify this source and make products using it under the
terms of CERN-OHL-S v2.

Source Location: https://github.com/kva4991/flagpole

The covered source and resulting products are distributed without any express
or implied warranty, including merchantability, satisfactory quality and
fitness for a particular purpose. See the licence text for the applicable
conditions.

## Software — MIT

Unless a file carries another notice, the following project-authored software
is licensed under the MIT License:

- `android/`;
- `electronics/firmware/`;
- `.github/`, `scripts/`, `tests/` and `tools/`;
- `build.cmd`, `package.json` and other repository automation intended to run
  as software rather than describe or manufacture the hardware.

The complete MIT text is in [`LICENSES/MIT.txt`](LICENSES/MIT.txt).

Third-party files bundled with the Android/Gradle toolchain keep their original
licences. For example, Gradle Wrapper launcher files carry Apache-2.0 notices.

## Documentation and catalog media

Project-authored hardware documentation and catalog metadata form part of the
open hardware source and use `CERN-OHL-S-2.0`. Documentation belonging solely
to MIT-licensed software may be used under MIT together with that software.

Photos, product-listing images, datasheet excerpts, fonts, libraries and other
third-party materials are **not relicensed** by this repository. Their original
terms and attribution continue to apply. Catalog image provenance is recorded
in [`catalog/images/SOURCES.md`](catalog/images/SOURCES.md); an absent or
unknown external licence must not be interpreted as permission to reuse an
image.

## Contributions and modifications

By contributing material, a contributor must have the right to provide it
under the licence assigned to the corresponding project area. Hardware design
changes must be recorded in [`CHANGES.txt`](CHANGES.txt) or in an equivalent
dated change notice and must satisfy CERN-OHL-S-2.0.

Suggested SPDX identifiers:

```text
SPDX-License-Identifier: CERN-OHL-S-2.0
SPDX-License-Identifier: MIT
```

Use only the identifier that applies to the file. Do not replace or remove a
third-party file's existing notice.
