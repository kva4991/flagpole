import { spawnSync } from 'node:child_process';
import process from 'node:process';

const mode = (process.argv[2] ?? 'all').toLowerCase();
const supportedModes = new Set(['all', 'generate', 'validate', 'catalog', 'ci', 'legacy-references']);

if (!supportedModes.has(mode)) {
  console.error(`Неизвестный режим: ${mode}. Допустимо: ${[...supportedModes].join(', ')}.`);
  process.exit(2);
}

const node = process.execPath;

function run(title, command, args) {
  console.log(`\n=== ${title} ===`);
  const result = spawnSync(command, args, { stdio: 'inherit', env: process.env });
  if (result.error) {
    console.error(`Не удалось запустить ${command}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.signal) {
    console.error(`${title}: процесс завершён сигналом ${result.signal}.`);
    process.exit(1);
  }
  if (result.status !== 0) process.exit(result.status ?? 1);
}

function npmRun(script) {
  if (process.platform === 'win32') {
    run(`npm run ${script}`, process.env.ComSpec ?? 'cmd.exe', ['/d', '/s', '/c', `npm.cmd run ${script}`]);
  } else {
    run(`npm run ${script}`, 'npm', ['run', script]);
  }
}

function python(script, ...args) {
  run(script, node, ['scripts/runPython.mjs', script, ...args]);
}

function cadPython(script, ...args) {
  const cad = process.env.FLAGPOLE_CAD_PYTHON;
  if (!cad) {
    console.error('FLAGPOLE_CAD_PYTHON не задан. Запустите tools/windows/setup-cad.ps1 -Install.');
    process.exit(1);
  }
  run(script, cad, [script, ...args]);
}

function generateProject() {
  npmRun('identity:generate');
  cadPython('mechanical/generate_build123d_canonical_v076.py');
  python('mechanical/render_build123d_exploded_preview_v076.py');
  npmRun('catalog:generate');
}

function generateLegacyReferencesOnExplicitRequest() {
  python('mechanical/generate_models_v06.py');
  python('mechanical/render_previews_v06.py');
  python('mechanical/render_flag_power_route_v06.py');
  python('mechanical/generate_reference_diagrams_v06.py');
  python('mechanical/generate_detail_diagrams_v075.py');
  python('mechanical/generate_hermeticity_diagram_v075.py');
  python('electronics/generate_electronics_diagrams_v075.py');
  npmRun('catalog:generate');
}

function validateProject() {
  python('mechanical/validate_models_v06.py');
  npmRun('quality:gate');
}

if (mode === 'legacy-references') {
  generateLegacyReferencesOnExplicitRequest();
} else if (mode === 'catalog') {
  npmRun('catalog:generate');
  npmRun('checksums:update');
  npmRun('catalog:check');
  npmRun('checksums:check');
} else if (mode === 'generate') {
  generateProject();
  npmRun('checksums:update');
} else if (mode === 'validate') {
  validateProject();
} else if (mode === 'ci') {
  generateProject();
  validateProject();
  run('Проверка воспроизводимости Git', 'git', ['diff', '--exit-code']);
} else {
  generateProject();
  npmRun('checksums:update');
  validateProject();
}

console.log(`\nСборочный режим ${mode} завершён успешно.`);
