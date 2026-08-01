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
  assert.match(setup, /crucian-control-debug\.apk/);
  assert.match(setup, /crucian-v06-firmware\.bin/);
  assert.doesNotMatch(setup, /pip install.+platformio/i);
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
});

test("checksum manifest normalizes text line endings across Windows and Linux", () => {
  const checker = read("scripts/checkChecksums.mjs");
  assert.match(checker, /replaceAll\('\\r\\n', '\\n'\)\.replaceAll\('\\r', '\\n'\)/);
  assert.match(checker, /textExtensions/);
  assert.match(checker, /textBasenames/);
  assert.match(checker, /'\.cache'/);
  assert.match(checker, /'__pycache__'/);
});
