import fs from 'node:fs';
import path from 'node:path';

export const MEDIA_DESCRIPTION_DIRECTORY = path.join('catalog', 'media-descriptions');

const REQUIRED_HEADINGS = [
  '## 0. Критический контракт',
  '## 1. Назначение и границы',
  '## 2. Источник истины и связанные файлы',
  '## 3. Что показано',
  '## 4. Почему изображено именно так',
  '## 5. Разбор элементов и ID',
  '## 6. Сборочная, эксплуатационная и сервисная логика',
  '## 7. Предварительные параметры и неподтверждённые допущения',
  '## 8. Что обновлять одновременно',
  '## 9. Проверка после изменения',
];

const REQUIRED_CONTRACT_HEADINGS = [
  '### Критические элементы — нельзя потерять',
  '### Запрещено',
  '### Проверить после генерации',
];

function sectionBulletCount(body, heading) {
  const start = body.indexOf(heading);
  if (start < 0) return 0;
  const tail = body.slice(start + heading.length);
  const nextHeading = tail.search(/^#{2,3} /m);
  const section = nextHeading < 0 ? tail : tail.slice(0, nextHeading);
  return (section.match(/^- .+/gm) ?? []).length;
}

function unquote(value) {
  const trimmed = value.trim();
  if (!trimmed) return '';
  if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
    return JSON.parse(trimmed);
  }
  return trimmed;
}

export function parseMediaDescription(text, relativePath = '<memory>') {
  const normalized = text.replaceAll('\r\n', '\n');
  if (!normalized.startsWith('---\n')) {
    throw new Error(`${relativePath}: отсутствует начальный блок метаданных ---`);
  }
  const end = normalized.indexOf('\n---\n', 4);
  if (end < 0) throw new Error(`${relativePath}: не закрыт блок метаданных ---`);
  const headerText = normalized.slice(4, end);
  const body = normalized.slice(end + 5).trim();
  const metadata = {};
  for (const [index, line] of headerText.split('\n').entries()) {
    if (!line.trim()) continue;
    const separator = line.indexOf(':');
    if (separator < 1) throw new Error(`${relativePath}:${index + 2}: ожидается поле key: value`);
    const key = line.slice(0, separator).trim();
    if (Object.hasOwn(metadata, key)) throw new Error(`${relativePath}: повтор поля ${key}`);
    metadata[key] = unquote(line.slice(separator + 1));
  }
  return { metadata, body, text: normalized };
}

function mediaRecords(media) {
  return [
    ...(media.drawings ?? []).map(item => ({ ...item, catalogSection: 'drawings' })),
    ...(media.models ?? []).map(item => ({ ...item, catalogSection: 'models' })),
    ...(media.experimentalModels ?? []).map(item => ({ ...item, catalogSection: 'experimentalModels' })),
    ...(media.printSessions ?? []).map(item => ({ ...item, catalogSection: 'printSessions' })),
  ];
}

function validateRelativePath(relativePath, expectedId, failures) {
  if (typeof relativePath !== 'string' || !relativePath.trim() || path.isAbsolute(relativePath)) {
    failures.push(`#${expectedId}: descriptionFile должен быть безопасным относительным путём`);
    return;
  }
  const normalized = relativePath.split('\\').join('/');
  if (normalized.split('/').includes('..')) failures.push(`#${expectedId}: descriptionFile не должен содержать ..`);
  if (normalized !== `${MEDIA_DESCRIPTION_DIRECTORY.split(path.sep).join('/')}/${expectedId}.md`) {
    failures.push(`#${expectedId}: ожидается descriptionFile catalog/media-descriptions/${expectedId}.md, найден ${relativePath}`);
  }
}

export function loadAndValidateMediaDescriptions(root, media, { throwOnFailure = true } = {}) {
  const failures = [];
  const records = mediaRecords(media);
  const descriptions = new Map();
  const recordIds = new Set(records.map(item => item.id));
  const directory = path.join(root, MEDIA_DESCRIPTION_DIRECTORY);

  if (!fs.existsSync(directory)) {
    failures.push(`Не найдена папка ${MEDIA_DESCRIPTION_DIRECTORY}`);
  }

  for (const item of records) {
    validateRelativePath(item.descriptionFile, item.id, failures);
    if (Object.hasOwn(item, 'description')) failures.push(`#${item.id}: поле description запрещено; текст хранится только в ${item.descriptionFile}`);
    if (!item.descriptionFile) continue;
    const absolutePath = path.join(root, item.descriptionFile);
    if (!fs.existsSync(absolutePath)) {
      failures.push(`#${item.id}: файл описания не найден: ${item.descriptionFile}`);
      continue;
    }
    let parsed;
    try {
      parsed = parseMediaDescription(fs.readFileSync(absolutePath, 'utf8'), item.descriptionFile);
    } catch (error) {
      failures.push(error.message);
      continue;
    }
    const { metadata, body } = parsed;
    const expected = {
      id: item.id,
      catalogSection: item.catalogSection,
      mediaType: item.kind,
      version: item.version,
      status: item.status,
      mediaFile: item.file,
      title: item.title,
    };
    for (const [key, value] of Object.entries(expected)) {
      if (metadata[key] !== value) failures.push(`${item.descriptionFile}: ${key} должен быть ${JSON.stringify(value)}, найден ${JSON.stringify(metadata[key])}`);
    }
    if (typeof metadata.summary !== 'string' || metadata.summary.length < 80 || metadata.summary.length > 500) {
      failures.push(`${item.descriptionFile}: summary должен содержать 80…500 символов`);
    }
    if (typeof metadata.sourceOfTruth !== 'string' || !metadata.sourceOfTruth.trim()) {
      failures.push(`${item.descriptionFile}: sourceOfTruth обязателен`);
    } else {
      const normalizedSource = metadata.sourceOfTruth.split('\\').join('/');
      if (path.isAbsolute(metadata.sourceOfTruth) || normalizedSource.split('/').includes('..')) {
        failures.push(`${item.descriptionFile}: sourceOfTruth должен быть безопасным относительным путём`);
      } else if (!fs.existsSync(path.join(root, metadata.sourceOfTruth))) {
        failures.push(`${item.descriptionFile}: sourceOfTruth не найден: ${metadata.sourceOfTruth}`);
      }
    }
    if (!fs.existsSync(path.join(root, item.file))) {
      failures.push(`#${item.id}: основной медиафайл не найден: ${item.file}`);
    }
    if (!body.startsWith(`# #${item.id} — `)) failures.push(`${item.descriptionFile}: заголовок должен начинаться с «# #${item.id} — »`);
    if (body.replace(/\s/g, '').length < 2500) failures.push(`${item.descriptionFile}: подробное описание слишком короткое; нужно не менее 2500 непробельных символов`);
    for (const heading of REQUIRED_HEADINGS) {
      if (!body.includes(heading)) failures.push(`${item.descriptionFile}: отсутствует обязательный раздел «${heading}»`);
    }
    for (const heading of REQUIRED_CONTRACT_HEADINGS) {
      if (!body.includes(heading)) {
        failures.push(`${item.descriptionFile}: отсутствует обязательный подраздел «${heading}»`);
      } else if (sectionBulletCount(body, heading) < 2) {
        failures.push(`${item.descriptionFile}: подраздел «${heading}» должен содержать минимум два конкретных пункта`);
      }
    }
    if (!body.includes(`\`${item.file}\``)) failures.push(`${item.descriptionFile}: тело должно явно ссылаться на основной файл ${item.file}`);
    if (!body.includes('§mediarationale1')) failures.push(`${item.descriptionFile}: отсутствует стабильная ссылка §mediarationale1`);
    const visibleIds = [...(item.callouts ?? []), ...(item.hotspots ?? [])]
      .map(entry => entry.id)
      .filter(Boolean)
      .map(value => `#${String(value).replace(/^#+/, '')}`);
    for (const visibleId of new Set(visibleIds)) {
      if (!body.includes(visibleId)) failures.push(`${item.descriptionFile}: не объяснён отображаемый ID ${visibleId}`);
    }
    descriptions.set(item.id, { ...parsed, item, absolutePath, relativePath: item.descriptionFile });
  }

  if (fs.existsSync(directory)) {
    const files = fs.readdirSync(directory, { withFileTypes: true })
      .filter(entry => entry.isFile() && /^\d{3}\.md$/.test(entry.name))
      .map(entry => entry.name.slice(0, -3));
    for (const id of files) {
      if (!recordIds.has(id)) failures.push(`catalog/media-descriptions/${id}.md не имеет карточки в catalog/drawings.json`);
    }
    for (const id of recordIds) {
      if (!files.includes(id)) failures.push(`#${id}: отсутствует catalog/media-descriptions/${id}.md`);
    }
  }

  if (descriptions.size !== records.length) {
    failures.push(`Загружено ${descriptions.size} описаний для ${records.length} медиа-карточек`);
  }

  const summaries = new Map();
  const bodies = new Map();
  for (const [id, description] of descriptions) {
    const summaryKey = description.metadata.summary.trim();
    if (summaries.has(summaryKey)) failures.push(`#${id}: summary дословно повторяет #${summaries.get(summaryKey)}`);
    else summaries.set(summaryKey, id);
    const bodyKey = description.body.replaceAll(/\s+/g, ' ').trim();
    if (bodies.has(bodyKey)) failures.push(`#${id}: полное описание дословно повторяет #${bodies.get(bodyKey)}`);
    else bodies.set(bodyKey, id);
  }

  if (failures.length && throwOnFailure) {
    throw new Error(`Ошибки подробных медиа-описаний:\n- ${failures.join('\n- ')}`);
  }
  return { descriptions, failures, records, requiredHeadings: REQUIRED_HEADINGS, requiredContractHeadings: REQUIRED_CONTRACT_HEADINGS };
}
