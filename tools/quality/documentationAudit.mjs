/*
 * Локальный аудит документации Crucian: относительные ссылки, зарегистрированные
 * §-теги и упомянутые npm-команды. Сеть намеренно не используется. §docqa01
 */
import { existsSync, readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const inlineLinkPattern = /!?\[[^\]]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+['"][^'"]*['"])?\s*\)/g;
const referenceLinkPattern = /^\s*\[[^\]]+\]:[ \t]+(<[^>]+>|\S+)/gm;
const tagPattern = /§[a-z][a-z0-9]{2,}/g;
const npmRunPattern = /\bnpm(?:\.cmd)?\s+run\s+([A-Za-z0-9:_-]+)/g;

function cleanTarget(rawTarget) {
  const unwrapped = String(rawTarget || '').replace(/^<|>$/g, '');
  try {
    return decodeURIComponent(unwrapped).split('#')[0].split('?')[0];
  } catch {
    return unwrapped.split('#')[0].split('?')[0];
  }
}

function isLocalRelative(target) {
  return Boolean(target)
    && !target.startsWith('#')
    && !target.startsWith('/')
    && !/^[a-z][a-z0-9+.-]*:/i.test(target);
}

export function markdownTargets(source) {
  const targets = [];
  for (const pattern of [inlineLinkPattern, referenceLinkPattern]) {
    pattern.lastIndex = 0;
    for (const match of source.matchAll(pattern)) targets.push(match[1]);
  }
  return targets;
}

export function registeredTags(source) {
  return new Set([...source.matchAll(/`(§[a-z][a-z0-9]+)`/g)].map((match) => match[1]));
}

export function auditDocumentation(paths, options) {
  const repoRoot = options.repoRoot;
  const read = options.read || ((path) => readFileSync(path, 'utf8'));
  const exists = options.exists || existsSync;
  const knownTags = registeredTags(read(resolve(repoRoot, 'docs/dev/tag-map.md')));
  const packageScripts = new Set(Object.keys(JSON.parse(read(resolve(repoRoot, 'package.json'))).scripts || {}));
  const report = {
    checkedFiles: [],
    brokenLinks: [],
    unknownTags: [],
    missingNpmScripts: [],
  };

  for (const relativePath of [...new Set(paths)].sort()) {
    const absolutePath = resolve(repoRoot, relativePath);
    const source = read(absolutePath);
    report.checkedFiles.push(relativePath);

    for (const rawTarget of markdownTargets(source)) {
      const target = cleanTarget(rawTarget);
      if (!isLocalRelative(target)) continue;
      if (!exists(resolve(dirname(absolutePath), target))) {
        report.brokenLinks.push({ file: relativePath, target });
      }
    }

    for (const tag of new Set(source.match(tagPattern) || [])) {
      if (!knownTags.has(tag)) report.unknownTags.push({ file: relativePath, tag });
    }

    for (const match of source.matchAll(npmRunPattern)) {
      if (!packageScripts.has(match[1])) {
        report.missingNpmScripts.push({ file: relativePath, script: match[1] });
      }
    }
  }
  return report;
}

export function formatDocumentationAudit(report) {
  const lines = [`Проверено Markdown-файлов: ${report.checkedFiles.length}.`];
  if (!report.brokenLinks.length && !report.unknownTags.length && !report.missingNpmScripts.length) {
    lines.push('Относительные ссылки, §-теги и npm-команды исправны.');
    return lines.join('\n');
  }
  for (const item of report.brokenLinks) lines.push(`BROKEN_LINK ${item.file}: ${item.target}`);
  for (const item of report.unknownTags) lines.push(`UNKNOWN_TAG ${item.file}: ${item.tag}`);
  for (const item of report.missingNpmScripts) lines.push(`MISSING_NPM_SCRIPT ${item.file}: ${item.script}`);
  return lines.join('\n');
}
