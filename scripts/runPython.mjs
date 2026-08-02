import { spawnSync } from 'node:child_process';
import process from 'node:process';

const scriptArgs = process.argv.slice(2);
if (scriptArgs.length === 0) {
  console.error('Использование: node scripts/runPython.mjs <script.py> [аргументы]');
  process.exit(2);
}

const candidates = [];
for (const value of [process.env.FLAGPOLE_PYTHON, process.env.PYTHON]) {
  if (value?.trim()) candidates.push([value.trim(), []]);
}
if (process.platform === 'win32') {
  candidates.push(['py', ['-3']], ['python', []], ['python3', []]);
} else {
  candidates.push(['python3', []], ['python', []]);
}

const seen = new Set();
for (const [command, prefix] of candidates) {
  const key = `${command}\0${prefix.join('\0')}`;
  if (seen.has(key)) continue;
  seen.add(key);
  const result = spawnSync(command, [...prefix, ...scriptArgs], { stdio: 'inherit' });
  if (result.error?.code === 'ENOENT') continue;
  if (result.error) {
    console.error(`Не удалось запустить ${command}: ${result.error.message}`);
    process.exit(1);
  }
  if (result.signal) {
    console.error(`${command} завершён сигналом ${result.signal}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

console.error('Не найден Python 3. Установите Python или задайте FLAGPOLE_PYTHON.');
process.exit(1);
