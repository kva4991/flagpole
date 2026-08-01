/* Показывает blast radius Git-изменений без запуска сборок и стенда. §impact */
import { spawnSync } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { formatImpact, inspectPaths } from '../tools/quality/changeImpact.mjs';

const repoRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function git(args) {
  const result = spawnSync('git', args, { cwd: repoRoot, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr.trim() || `git ${args.join(' ')} failed`);
  return result.stdout.split(/\r?\n/).filter(Boolean);
}

function collectPaths(args) {
  const gitIndex = args.indexOf('--git');
  if (gitIndex < 0) return args.filter((arg) => !arg.startsWith('--'));
  const base = args[gitIndex + 1] || 'origin/main';
  return [
    ...git(['diff', '--name-only', `${base}...HEAD`]),
    ...git(['diff', '--name-only']),
    ...git(['diff', '--name-only', '--cached']),
    ...git(['ls-files', '--others', '--exclude-standard']),
  ];
}

const report = inspectPaths(collectPaths(process.argv.slice(2)));
console.log(formatImpact(report));
if (report.unknown.length) process.exitCode = 1;
