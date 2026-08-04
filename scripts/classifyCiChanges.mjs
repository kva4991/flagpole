import fs from 'node:fs';
import process from 'node:process';

export function classify(paths) {
  const normalized = paths.map((path) => path.replaceAll('\\', '/')).filter(Boolean);
  const all = normalized.includes('__all__');
  const matches = (patterns) => all || normalized.some((path) => patterns.some((pattern) => pattern.test(path)));

  return {
    mechanical: matches([
      /^mechanical\//,
      /^catalog\//,
      /^electronics\/(electronics_|generate_electronics)/,
      /^scripts\/(build|runPython|generateComponentCatalog|checkChecksums)\.mjs$/,
      /^tests\/(mechanical|catalog|printLayout|cadWorkflow)/,
      /^package(?:-lock)?\.json$/,
      /^project_identity\.json$/,
      /^\.gitattributes$/,
      /^\.github\/workflows\/validate\.yml$/,
    ]),
    android: matches([
      /^android\//,
      /^project_identity\.json$/,
      /^scripts\/generateProjectIdentity\.mjs$/,
      /^\.github\/workflows\/validate\.yml$/,
    ]),
    firmware: matches([
      /^electronics\/firmware\//,
      /^project_identity\.json$/,
      /^scripts\/generateProjectIdentity\.mjs$/,
      /^tools\/toolchain\.json$/,
      /^\.github\/workflows\/validate\.yml$/,
    ]),
  };
}

if (process.argv[1]?.endsWith('classifyCiChanges.mjs')) {
  const inputPath = process.argv[2];
  if (!inputPath) {
    console.error('Использование: node scripts/classifyCiChanges.mjs <changed-files.txt>');
    process.exit(2);
  }
  const result = classify(fs.readFileSync(inputPath, 'utf8').split(/\r?\n/));
  for (const [name, enabled] of Object.entries(result)) console.log(`${name}=${enabled}`);
}
