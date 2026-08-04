import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";

const root = path.resolve(import.meta.dirname, "..");
const read = (relativePath) => fs.readFileSync(path.join(root, relativePath), "utf8");

test("Windows toolchain manifest covers Android and both ESP32 projects", () => {
  const manifest = JSON.parse(read("tools/toolchain.json"));
  assert.equal(manifest.schemaVersion, 1);
  assert.equal(manifest.gradleWrapperVersion, "8.10.2");
  assert.deepEqual(manifest.androidSdk.packages, [
    "platform-tools",
    "platforms;android-35",
    "build-tools;35.0.0",
  ]);
  assert.deepEqual(manifest.platformio.projects, [
    "electronics/firmware/esp32_c3_crucian_v06",
    "electronics/firmware/esp32_c3_flag_light",
  ]);
  for (const project of manifest.platformio.projects) {
    assert.ok(fs.existsSync(path.join(root, project, "platformio.ini")), project);
  }
});

test("Windows setup uses isolated official PlatformIO installer and repository Gradle Wrapper", () => {
  const setup = read("tools/windows/setup.ps1");
  const manifest = JSON.parse(read("tools/toolchain.json"));
  assert.match(manifest.platformio.installerUrl, /^https:\/\/raw\.githubusercontent\.com\/platformio\/platformio-core-installer\//);
  assert.match(setup, /\.platformio\\penv\\Scripts\\pio\.exe/);
  assert.match(setup, /gradlew\.bat/);
  assert.match(setup, /Sync-ExecutionWorktree/);
  assert.match(setup, /robocopy.+\/PURGE/);
  assert.match(setup, /\/XF \.git \*\.log \*\.tmp/);
  assert.match(setup, /crucian-control-debug\.apk/);
  assert.match(setup, /crucian-v06-firmware\.bin/);
  assert.match(setup, /Install-MechanicalPythonEnvironment/);
  assert.match(setup, /mechanical\\requirements\.txt/);
  assert.match(setup, /\.mechanical-venv/);
  assert.match(setup, /git lfs install --skip-repo/);
  assert.match(setup, /setup-cad\.ps1/);
  assert.doesNotMatch(setup, /pip install.+platformio/i);
});

test("Windows CAD setup pins build123d/OCP and installs desktop CAD normally", () => {
  const manifest = JSON.parse(read("tools/toolchain.json"));
  const setupCad = read("tools/windows/setup-cad.ps1");
  const check = read("tools/windows/check.ps1");

  assert.equal(manifest.cad.build123dVersion, "0.11.1");
  assert.equal(manifest.cad.ocpPackage, "cadquery-ocp-novtk==7.9.3.1.1");
  assert.equal(manifest.cad.glbPackage, "trimesh==5.0.0");
  assert.equal(manifest.cad.venvDirectory, ".venv-build123d");
  assert.deepEqual(manifest.cad.windowsPackages.map(({ wingetId }) => wingetId), [
    "FreeCAD.FreeCAD",
    "OpenSCAD.OpenSCAD",
  ]);
  assert.match(setupCad, /winget install/);
  assert.match(setupCad, /import build123d, OCP/);
  assert.match(check, /build123d\/OCP environment/);
  assert.match(check, /freecadcmd\.exe/i);
  assert.match(check, /openscad\.exe/i);
});

test("agent guidance requires Python execution from the protected Windows copy", () => {
  const agents = read("AGENTS.md");
  const fastStart = read("docs/agent-fast-start.ru.md");
  const toolsReadme = read("tools/README.ru.md");

  for (const document of [agents, fastStart, toolsReadme]) {
    assert.match(document, /pesochnica\\flagpole\\worktree/);
    assert.match(document, /spawnSync py EPERM/);
  }
  assert.match(agents, /Пробный Python-запуск из исходного Git-worktree запрещён/);
  assert.match(fastStart, /не запускать Python.+из исходного Git-worktree/s);
  assert.match(toolsReadme, /не запускать Python.+из исходного Git-worktree/s);
});

test("Android Kotlin 2 project applies matching Compose compiler plugin and wrapper", () => {
  const rootBuild = read("android/crucian-control/build.gradle.kts");
  const appBuild = read("android/crucian-control/app/build.gradle.kts");
  assert.match(rootBuild, /org\.jetbrains\.kotlin\.plugin\.compose"\) version "2\.0\.21"/);
  assert.match(appBuild, /id\("org\.jetbrains\.kotlin\.plugin\.compose"\)/);
  assert.doesNotMatch(appBuild, /kotlinCompilerExtensionVersion/);
  assert.ok(fs.existsSync(path.join(root, "android/crucian-control/gradlew.bat")));
  assert.ok(fs.existsSync(path.join(root, "android/crucian-control/gradle/wrapper/gradle-wrapper.jar")));
});

test("GitHub Actions builds Android and both PlatformIO projects", () => {
  const workflow = read(".github/workflows/validate.yml");
  assert.match(workflow, /\.\/gradlew :app:assembleDebug/);
  assert.match(workflow, /platformio==6\.1\.19/);
  assert.match(workflow, /esp32_c3_crucian_v06/);
  assert.match(workflow, /esp32_c3_flag_light/);
  assert.match(workflow, /actions\/checkout@v7/);
  assert.match(workflow, /actions\/upload-artifact@v7/);
  assert.match(workflow, /mechanical\/requirements\.txt/);
  assert.match(workflow, /npm run build:ci/);
  assert.match(workflow, /git lfs pull --include="\*\.glb,\*\.stl"/);
  assert.match(workflow, /needs\.quality\.outputs\.mechanical/);
});

test("checksum manifest normalizes text line endings across Windows and Linux", () => {
  const checker = read("scripts/checkChecksums.mjs");
  assert.match(checker, /replaceAll\('\\r\\n', '\\n'\)\.replaceAll\('\\r', '\\n'\)/);
  assert.match(checker, /textExtensions/);
  assert.match(checker, /textBasenames/);
  assert.match(checker, /'\.cache'/);
  assert.match(checker, /'__pycache__'/);
  assert.match(checker, /if \(ignoredDirectories\.has\(entry\.name\)\) continue/);
});

test("component catalog launcher supports an explicit Firefox browser", () => {
  const launcher = read("tools/windows/open-component-catalog.ps1");
  assert.match(launcher, /\[ValidateSet\('Default', 'Firefox'\)\]/);
  assert.match(launcher, /Get-Command firefox\.exe/);
  assert.match(launcher, /Mozilla Firefox\\firefox\.exe/);
  assert.match(launcher, /Start-Process -FilePath \$firefoxPath -ArgumentList \$url/);
  assert.match(launcher, /\[switch\]\$NoBrowser/);
});
