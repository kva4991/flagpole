/*
 * Компактная карта влияния для механики, электроники, прошивки, Android и
 * документации Crucian. Она советует проверки, но не запускает стенд. §impact
 */
const rules = [
  {
    area: 'Документация и решения',
    pattern: /^(?:AGENTS\.md|README(?:\.ru|_RU)?\.md|docs\/|[^/]+_RU\.md$|.*\.txt$|PROJECT_MANIFEST[^/]*\.json$)/,
    risk: 'low',
    checks: ['npm.cmd run quality:docs:all'],
  },
  {
    area: 'Параметрическая механика и печатные модели',
    pattern: /^(?:mechanical\/|fish_template_|FISH_TEMPLATE_)/,
    risk: 'critical',
    checks: ['python mechanical/generate_models_v05.py', 'проверка STL и тестовых купонов'],
  },
  {
    area: 'Электроника и схемы',
    pattern: /^electronics\/(?!firmware\/)/,
    risk: 'high',
    checks: ['ручная сверка схемы, BOM и конкретных модулей'],
  },
  {
    area: 'Прошивка ESP32-C3',
    pattern: /^electronics\/firmware\//,
    risk: 'critical',
    checks: ['PlatformIO build', 'стендовые BLE/PWM/deep-sleep проверки'],
  },
  {
    area: 'Android-приложение',
    pattern: /^android\//,
    risk: 'high',
    checks: ['Gradle assembleDebug', 'BLE-проверка на реальном Android'],
  },
  {
    area: 'Каталог компонентов',
    pattern: /^(?:catalog\/|scripts\/generateComponentCatalog\.mjs$)/,
    risk: 'medium',
    checks: ['npm.cmd run catalog:check'],
  },
  {
    area: 'Локальный quality-контур',
    pattern: /^(?:package\.json|scripts\/|tools\/|tests\/|\.gitignore|\.gitattributes|CHECKSUMS_SHA256\.txt)/,
    risk: 'medium',
    checks: ['npm.cmd test', 'npm.cmd run checksums:check'],
  },
];

const riskOrder = ['low', 'medium', 'high', 'critical'];

export function inspectPaths(paths) {
  const normalized = [...new Set(paths.map((path) => String(path).replaceAll('\\', '/').replace(/^\.\//, '')).filter(Boolean))].sort();
  const areas = new Map();
  const checks = new Set();
  const unknown = [];
  let risk = 'low';
  for (const path of normalized) {
    const matches = rules.filter((rule) => rule.pattern.test(path));
    if (!matches.length) unknown.push(path);
    for (const rule of matches) {
      areas.set(rule.area, (areas.get(rule.area) || 0) + 1);
      for (const check of rule.checks) checks.add(check);
      if (riskOrder.indexOf(rule.risk) > riskOrder.indexOf(risk)) risk = rule.risk;
    }
  }
  if (unknown.length && riskOrder.indexOf(risk) < riskOrder.indexOf('high')) risk = 'high';
  return {
    paths: normalized,
    areas: [...areas.entries()].map(([name, count]) => ({ name, count })),
    checks: [...checks],
    unknown,
    risk,
  };
}

export function formatImpact(report) {
  const lines = [`Изменённых путей: ${report.paths.length}.`, `Максимальный риск: ${report.risk}.`];
  if (report.areas.length) {
    lines.push('Затронутые области:');
    for (const area of report.areas) lines.push(`  - ${area.name}: ${area.count}`);
  }
  if (report.checks.length) {
    lines.push('Рекомендуемые проверки:');
    for (const check of report.checks) lines.push(`  - ${check}`);
  }
  if (report.unknown.length) {
    lines.push('Неизвестные карте пути:');
    for (const path of report.unknown) lines.push(`  - ${path}`);
  }
  return lines.join('\n');
}
