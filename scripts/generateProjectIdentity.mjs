import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const sourcePath = path.join(root, 'project_identity.json');
const firmwarePath = path.join(root, 'electronics', 'firmware', 'esp32_c3_crucian_v06', 'include', 'project_identity.h');
const androidPath = path.join(root, 'android', 'crucian-control', 'app', 'src', 'main', 'java', 'ru', 'superpommelsandflag', 'crucian', 'ProjectIdentity.kt');
const stringsPath = path.join(root, 'android', 'crucian-control', 'app', 'src', 'main', 'res', 'values', 'strings.xml');

const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const failures = [];
if (source.schemaVersion !== 1) failures.push('schemaVersion должен быть равен 1');
for (const key of ['projectDisplayName', 'bluetoothDeviceName']) {
  if (typeof source[key] !== 'string' || !source[key].trim()) failures.push(`${key} должен быть непустой строкой`);
  if ((source[key] ?? '').length > 24) failures.push(`${key} должен быть короче 25 символов для удобной BLE-рекламы`);
  if (/[^\x20-\x7E]/.test(source[key] ?? '')) failures.push(`${key} пока должен содержать печатные ASCII-символы`);
}
if (failures.length) {
  console.error(`Ошибки project_identity.json:\n- ${failures.join('\n- ')}`);
  process.exit(1);
}

const cppEscape = value => value.replaceAll('\\', '\\\\').replaceAll('"', '\\"');
const xmlEscape = value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&apos;');

const firmware = `#pragma once\n\n// Сгенерировано из project_identity.json. Вручную не редактировать.\nnamespace project_identity {\ninline constexpr char PROJECT_DISPLAY_NAME[] = "${cppEscape(source.projectDisplayName)}";\ninline constexpr char BLE_DEVICE_NAME[] = "${cppEscape(source.bluetoothDeviceName)}";\n}\n`;

const android = `package ru.superpommelsandflag.crucian\n\n/** Сгенерировано из project_identity.json. Вручную не редактировать. */\nobject ProjectIdentity {\n    const val PROJECT_DISPLAY_NAME: String = "${cppEscape(source.projectDisplayName)}"\n    const val BLE_DEVICE_NAME: String = "${cppEscape(source.bluetoothDeviceName)}"\n}\n`;

const strings = `<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <!-- Сгенерировано из project_identity.json. Вручную не редактировать. -->\n    <string name="app_name">${xmlEscape(source.projectDisplayName)}</string>\n</resources>\n`;

const outputs = [[firmwarePath, firmware], [androidPath, android], [stringsPath, strings]];
const checkOnly = process.argv.includes('--check');
let changed = false;
for (const [file, content] of outputs) {
  if (checkOnly) {
    if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== content) {
      console.error(`Устаревший generated-файл: ${path.relative(root, file)}`);
      changed = true;
    }
  } else {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, content, 'utf8');
    console.log(`Generated ${path.relative(root, file)}`);
  }
}
if (checkOnly && changed) process.exit(1);
if (checkOnly && !changed) console.log('Имена проекта и BLE синхронизированы.');
