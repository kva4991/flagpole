import fs from 'node:fs';
import path from 'node:path';
import { readLfsPointer } from './lfsPointer.mjs';
import { loadAndValidateMediaDescriptions } from './mediaDescriptions.mjs';
import process from 'node:process';

const root = process.cwd();
const componentPath = path.join(root, 'catalog', 'components.json');
const physicalComponentsPath = path.join(root, 'catalog', 'physical-components.json');
const drawingsPath = path.join(root, 'catalog', 'drawings.json');
const identityPath = path.join(root, 'project_identity.json');
const versionPath = path.join(root, 'VERSION.txt');
const partRegistryPath = path.join(root, 'mechanical', 'part_id_registry_v06.json');
const featureRegistryPath = path.join(root, 'mechanical', 'feature_id_registry_v076.json');
const imageDirectory = path.join(root, 'catalog', 'images');
const htmlPath = path.join(root, 'catalog', 'catalog.html');

const displayId = value => `#${String(value).replace(/^#+/, '')}`;

const escape = value => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#39;');

const finiteArray = (value, length) => Array.isArray(value)
  && value.length === length
  && value.every(number => Number.isFinite(number));

function validateAsset(value, place, failures) {
  if (typeof value !== 'string' || !value.trim() || path.isAbsolute(value) || value.split(/[\\/]/).includes('..')) {
    failures.push(`${place} должен быть безопасным путём относительно корня проекта`);
  } else if (!fs.existsSync(path.join(root, value))) {
    failures.push(`${place} не найден: ${value}`);
  }
}

function validateCalloutId(id, allowedIds, place, failures) {
  if (typeof id !== 'string' || !allowedIds.has(id)) {
    failures.push(`${place}.id неизвестен: ${String(id)}`);
  }
}

function validateDrawingCallouts(item, place, allowedIds, failures) {
  if (item.kind === 'print-layout') {
    if (item.calloutMode !== 'exempt') failures.push(`${place}.calloutMode для раскладки должен быть exempt`);
    if (!item.calloutExemptReason?.trim()) failures.push(`${place}.calloutExemptReason обязателен`);
    if ((item.callouts ?? []).length) failures.push(`${place}: раскладка печати не должна содержать callouts`);
    if (item.annotatedPreview) failures.push(`${place}: раскладка печати не должна иметь annotatedPreview`);
    return;
  }
  if (item.kind !== 'drawing') failures.push(`${place}.kind должен быть drawing или print-layout`);
  if (item.calloutMode === 'embedded') {
    if (!Array.isArray(item.partIds) || item.partIds.length === 0) failures.push(`${place}.partIds должен быть непустым массивом`);
    if ((item.callouts ?? []).length) failures.push(`${place}: embedded-вид не должен дублировать callouts`);
    if (item.annotatedPreview) failures.push(`${place}: embedded-вид не должен иметь annotatedPreview`);
    for (const [index, id] of (item.partIds ?? []).entries()) validateCalloutId(id, allowedIds, `${place}.partIds[${index}]`, failures);
    return;
  }
  if (item.calloutMode !== 'overlay') failures.push(`${place}.calloutMode должен быть overlay или embedded`);
  if (item.partIds) failures.push(`${place}: overlay-вид не должен иметь partIds`);
  if (!Array.isArray(item.callouts) || item.callouts.length === 0) failures.push(`${place}.callouts должен быть непустым массивом`);
  validateAsset(item.annotatedPreview, `${place}.annotatedPreview`, failures);
  for (const [index, callout] of (item.callouts ?? []).entries()) {
    const calloutPlace = `${place}.callouts[${index}]`;
    validateCalloutId(callout.id, allowedIds, calloutPlace, failures);
    if (!callout.label?.trim()) failures.push(`${calloutPlace}.label обязателен`);
    if (!finiteArray(callout.target, 2) || callout.target.some(value => value < 0 || value > 1)) failures.push(`${calloutPlace}.target должен быть [x,y] в диапазоне 0…1`);
    if (!finiteArray(callout.labelPosition, 2) || callout.labelPosition.some(value => value < 0 || value > 1)) failures.push(`${calloutPlace}.labelPosition должен быть [x,y] в диапазоне 0…1`);
  }
}

function validateModelCallouts(item, place, allowedIds, failures) {
  if (item.kind === 'print-layout') {
    if (item.calloutMode !== 'exempt') failures.push(`${place}.calloutMode для раскладки должен быть exempt`);
    if (!item.calloutExemptReason?.trim()) failures.push(`${place}.calloutExemptReason обязателен`);
    if ((item.callouts ?? []).length) failures.push(`${place}: раскладка печати не должна содержать hotspots`);
    return;
  }
  if (item.kind !== 'model') failures.push(`${place}.kind должен быть model или print-layout`);
  if (item.calloutMode !== 'hotspots') failures.push(`${place}.calloutMode должен быть hotspots`);
  if (!Array.isArray(item.callouts) || item.callouts.length === 0) failures.push(`${place}.callouts должен быть непустым массивом`);
  for (const [index, callout] of (item.callouts ?? []).entries()) {
    const calloutPlace = `${place}.callouts[${index}]`;
    validateCalloutId(callout.id, allowedIds, calloutPlace, failures);
    if (!callout.label?.trim()) failures.push(`${calloutPlace}.label обязателен`);
    if (!finiteArray(callout.position, 3)) failures.push(`${calloutPlace}.position должен быть массивом из трёх конечных чисел в метрах`);
    if (!finiteArray(callout.normal, 3) || callout.normal.every(value => value === 0)) failures.push(`${calloutPlace}.normal должен быть ненулевым массивом из трёх чисел`);
  }
}

function validate(source, physical, media, cadDrafts, identity, registry, featureRegistry, currentVersion) {
  const failures = [];
  const ids = new Set();
  const categoryIds = new Set();

  if (identity.schemaVersion !== 1) failures.push('schemaVersion project_identity.json должен быть равен 1');
  for (const key of ['projectDisplayName', 'bluetoothDeviceName']) {
    if (typeof identity[key] !== 'string' || !identity[key].trim()) failures.push(`${key} должен быть непустой строкой`);
  }
  if (!/^\d+\.\d+\.\d+$/.test(currentVersion)) failures.push('VERSION.txt должен содержать версию вида X.Y.Z');

  if (source.schemaVersion !== 2) failures.push('schemaVersion components.json должен быть равен 2');
  if (!Array.isArray(source.categories) || source.categories.length === 0) failures.push('categories должен быть непустым массивом');
  for (const [index, category] of (source.categories ?? []).entries()) {
    if (!category.id?.trim() || !category.label?.trim()) failures.push(`categories[${index}] требует id и label`);
    if (categoryIds.has(category.id)) failures.push(`повтор категории: ${category.id}`);
    categoryIds.add(category.id);
  }

  if (!Array.isArray(source.components) || source.components.length === 0) failures.push('components должен быть непустым массивом');
  for (const [index, item] of (source.components ?? []).entries()) {
    const place = `components[${index}]`;
    if (!/^\d{3}$/.test(item.id ?? '')) failures.push(`${place}.id должен состоять ровно из трёх цифр`);
    if (ids.has(item.id)) failures.push(`${place}.id повторяется: ${item.id}`);
    ids.add(item.id);
    if (!categoryIds.has(item.category)) failures.push(`${place}.category неизвестна: ${item.category}`);
    if (!item.name?.trim() || !item.purpose?.trim()) failures.push(`${place} требует name и purpose`);
    if (!Array.isArray(item.aliases) || item.aliases.length === 0) failures.push(`${place}.aliases должен быть непустым массивом`);
    if (!item.image?.trim() || path.basename(item.image) !== item.image) failures.push(`${place}.image должен быть именем локального файла`);
    else if (!fs.existsSync(path.join(imageDirectory, item.image))) failures.push(`${place}.image не найден: ${item.image}`);
    for (const [imageIndex, image] of (item.additionalImages ?? []).entries()) {
      if (!image.file?.trim() || path.basename(image.file) !== image.file || !image.label?.trim()) failures.push(`${place}.additionalImages[${imageIndex}] требует file и label`);
      else if (!fs.existsSync(path.join(imageDirectory, image.file))) failures.push(`${place}.additionalImages[${imageIndex}] не найден: ${image.file}`);
    }
    if (!['confirmed', 'listing', 'reference', 'placeholder'].includes(item.imageStatus)) failures.push(`${place}.imageStatus некорректен`);
    if (!Array.isArray(item.links)) failures.push(`${place}.links должен быть массивом`);
    for (const [linkIndex, link] of (item.links ?? []).entries()) {
      if (!link.label?.trim()) failures.push(`${place}.links[${linkIndex}].label обязателен`);
      try {
        if (new URL(link.url).protocol !== 'https:') throw new Error();
      } catch {
        failures.push(`${place}.links[${linkIndex}].url должен быть корректным HTTPS URL`);
      }
    }
  }
  const componentIds = [...ids].sort();
  componentIds.forEach((id, index) => {
    const expected = String(index + 1).padStart(3, '0');
    if (id !== expected) failures.push(`ID компонентов должны идти без пропусков: ожидался ${expected}, найден ${id}`);
  });

  if (physical.schemaVersion !== 1) failures.push('schemaVersion physical-components.json должен быть равен 1');
  if (physical.tag !== '§physicalcomponents1') failures.push('physical-components.json должен содержать тег §physicalcomponents1');
  if (physical.policy?.singleSourceOfTruth !== true) failures.push('physical-components.json должен закреплять singleSourceOfTruth');
  const allowedMeasurementStatuses = new Set(physical.policy?.statuses ?? []);
  const physicalIds = new Set();
  for (const [index, item] of (physical.components ?? []).entries()) {
    const place = `physical.components[${index}]`;
    if (!componentIds.includes(item.id)) failures.push(`${place}.id не найден в components.json: ${item.id}`);
    if (physicalIds.has(item.id)) failures.push(`${place}.id повторяется: ${item.id}`);
    physicalIds.add(item.id);
    if (item.anchor !== `component-${item.id}`) failures.push(`${place}.anchor должен быть component-${item.id}`);
    if (!Array.isArray(item.measurements) || !Array.isArray(item.needs)) failures.push(`${place} требует массивы measurements и needs`);
    const measurementKeys = new Set();
    for (const [measurementIndex, measurement] of (item.measurements ?? []).entries()) {
      const measurementPlace = `${place}.measurements[${measurementIndex}]`;
      if (!measurement.key?.trim() || !measurement.label?.trim() || !String(measurement.value ?? '').trim()) failures.push(`${measurementPlace} требует key, label и value`);
      if (measurementKeys.has(measurement.key)) failures.push(`${measurementPlace}.key повторяется: ${measurement.key}`);
      measurementKeys.add(measurement.key);
      if (!allowedMeasurementStatuses.has(measurement.status)) failures.push(`${measurementPlace}.status неизвестен: ${measurement.status}`);
      if (!measurement.source?.trim()) failures.push(`${measurementPlace}.source обязателен`);
    }
  }
  if (physicalIds.size !== componentIds.length || componentIds.some(id => !physicalIds.has(id))) failures.push('physical-components.json должен иметь ровно одну запись для каждого ID components.json');

  const registryItems = Object.values(registry.groups ?? {}).flat();
  const registryIds = registryItems.map(item => item.id);
  if (!registryIds.length) failures.push('Реестр печатных деталей пуст');
  if (new Set(registryIds).size !== registryIds.length) failures.push('В реестре печатных деталей повторяются ID');
  const featureIds = (featureRegistry.features ?? []).map(item => item.id);
  const featureIdSet = new Set(featureIds);
  if (featureIdSet.size !== featureIds.length) failures.push('В реестре feature-ID повторяются ID');
  for (const item of featureRegistry.features ?? []) {
    if (!registryIds.includes(item.parent)) failures.push(`feature-ID ${item.id} ссылается на неизвестного родителя ${item.parent}`);
  }
  const allowedCalloutIds = new Set([...componentIds, ...registryIds, ...featureIds]);

  if (media.schemaVersion !== 6) failures.push('schemaVersion drawings.json должен быть равен 6');
  if (media.catalogPolicy?.visibility !== 'current-only') failures.push('catalogPolicy.visibility должен быть current-only');
  if (media.catalogPolicy?.currentVersion !== currentVersion) failures.push('catalogPolicy.currentVersion должен совпадать с VERSION.txt');
  if (media.catalogPolicy?.partIdCallouts !== 'required-for-all-drawings-and-models-except-print-layouts') failures.push('catalogPolicy.partIdCallouts не закрепляет обязательное правило выносок');
  if (media.catalogPolicy?.sourceDrawingsRemainClean !== true) failures.push('catalogPolicy.sourceDrawingsRemainClean должен быть true');
if (media.catalogPolicy?.thumbnailIdentifiers !== 'hidden') failures.push('catalogPolicy.thumbnailIdentifiers должен быть hidden');
if (media.catalogPolicy?.fullscreenIdentifierToggle !== true) failures.push('catalogPolicy.fullscreenIdentifierToggle должен быть true');
if (media.catalogPolicy?.labelPlacement !== 'automatic-near-target') failures.push('catalogPolicy.labelPlacement должен быть automatic-near-target');
  if (media.catalogPolicy?.mediaDescriptions !== 'one-markdown-file-per-media-id') failures.push('catalogPolicy.mediaDescriptions должен быть one-markdown-file-per-media-id');
  if (media.catalogPolicy?.mediaDescriptionDirectory !== 'catalog/media-descriptions') failures.push('catalogPolicy.mediaDescriptionDirectory должен быть catalog/media-descriptions');
  if (media.catalogPolicy?.mediaDescriptionSync !== 'required-same-change') failures.push('catalogPolicy.mediaDescriptionSync должен быть required-same-change');
  if (media.catalogPolicy?.physicalMeasurements !== 'catalog/physical-components.json') failures.push('catalogPolicy.physicalMeasurements должен ссылаться на catalog/physical-components.json');
  if (media.catalogPolicy?.componentPermalinks !== 'catalog/catalog.html#component-<ID>') failures.push('catalogPolicy.componentPermalinks должен закреплять постоянные ссылки карточек');
  if (!Array.isArray(media.catalogPolicy?.cadDraftSources) || media.catalogPolicy.cadDraftSources.length !== cadDrafts.length) failures.push('catalogPolicy.cadDraftSources должен перечислять все CAD-заготовки');
  if (media.catalogPolicy?.experimentalCadIsolation !== 'canonical-build123d-no-separate-tab') failures.push('catalogPolicy.experimentalCadIsolation должен закреплять канонический build123d без отдельной вкладки');

  const canonicalModels = new Map((media.models ?? []).map(item => [item.id, item]));
  for (const group of ['drawings', 'models', 'experimentalModels', 'printSessions']) {
    if (!Array.isArray(media[group])) failures.push(`${group} должен быть массивом`);
    for (const [index, item] of (media[group] ?? []).entries()) {
      const place = `${group}[${index}]`;
      if (!/^\d{3}$/.test(item.id ?? '')) failures.push(`${place}.id должен состоять ровно из трёх цифр`);
      if (ids.has(item.id)) failures.push(`повтор ID: ${item.id}`);
      ids.add(item.id);
      if (!item.title?.trim() || !item.descriptionFile?.trim()) failures.push(`${place} требует title и descriptionFile`);
      if (Object.hasOwn(item, 'description')) failures.push(`${place}.description запрещён: подробный текст хранится только в descriptionFile`);
      const expectedStatus = group === 'experimentalModels' ? 'experimental' : 'current';
      if (item.status !== expectedStatus) failures.push(`${place}.status должен быть ${expectedStatus}`);
      if (item.version !== currentVersion) failures.push(`${place}.version должен быть ${currentVersion}`);
      validateAsset(item.file, `${place}.file`, failures);
      const previewField = group === 'models' || group === 'experimentalModels' ? 'poster' : 'preview';
      validateAsset(item[previewField], `${place}.${previewField}`, failures);
if (group === 'drawings') {
  validateAsset(item.thumbnail, `${place}.thumbnail`, failures);
  if (item.thumbnail === item.annotatedPreview || /(?:catalog[\\/]annotated|_ids\.png$)/i.test(item.thumbnail ?? '')) failures.push(`${place}.thumbnail должен быть чистым изображением без ID`);
}
      if (group === 'drawings') validateDrawingCallouts(item, place, allowedCalloutIds, failures);
      else if (group === 'models' || group === 'experimentalModels') {
        const inherited = item.calloutsFrom ? canonicalModels.get(item.calloutsFrom) : null;
        if (item.calloutsFrom && !inherited) failures.push(`${place}.calloutsFrom ссылается на отсутствующую каноническую модель`);
        validateModelCallouts(inherited ? { ...item, callouts: inherited.callouts } : item, place, allowedCalloutIds, failures);
        if (item.hardwareFile && !fs.existsSync(path.join(root, item.hardwareFile))) failures.push(`${place}.hardwareFile не найден: ${item.hardwareFile}`);
      }
      else {
        if (item.kind !== 'print-layout' || item.calloutMode !== 'exempt' || !item.calloutExemptReason?.trim()) failures.push(`${place} должен быть оформлен как освобождённая раскладка печати`);
        if ((item.callouts ?? []).length || item.partIds || item.annotatedPreview) failures.push(`${place}: очередь печати не должна содержать выноски`);
      }
    }
  }
  for (const [index, draft] of cadDrafts.entries()) {
    const place = `cadDrafts[${index}]`;
    const draftPath = media.catalogPolicy.cadDraftSources[index];
    validateAsset(draftPath, `${place}.registryFile`, failures);
    if (!/^\d{3}$/.test(draft.id ?? '')) failures.push(`${place}.id должен состоять ровно из трёх цифр`);
    if (ids.has(draft.id)) failures.push(`повтор ID: ${draft.id}`);
    ids.add(draft.id);
    if (draft.schemaVersion !== 1 || draft.version !== currentVersion) failures.push(`${place} имеет неверную схему или версию`);
    if (draft.status !== 'source-only-not-generated') failures.push(`${place}.status должен быть source-only-not-generated`);
    const supportedDrafts = new Map([
      ['bearing-adapter', { tag: '§bearingadapter1', material: 'PETG' }],
      ['flexible-cable-strain-relief', { tag: '§lowercablestrain1', material: 'TPU 85A' }],
    ]);
    const draftContract = supportedDrafts.get(draft.draftType);
    if (!draftContract) failures.push(`${place}.draftType не поддерживается`);
    if (draftContract && draft.tag !== draftContract.tag) failures.push(`${place}.tag должен быть ${draftContract.tag}`);
    if (draftContract && draft.material !== draftContract.material) failures.push(`${place}.material должен быть ${draftContract.material}`);
    if (!draft.title?.trim() || !draft.summary?.trim()) failures.push(`${place} требует title и summary`);
    validateAsset(draft.sourceFile, `${place}.sourceFile`, failures);
    validateAsset(draft.documentation, `${place}.documentation`, failures);
    if (!Array.isArray(draft.physicalDependencies) || draft.physicalDependencies.some(item => !componentIds.includes(item.componentId))) failures.push(`${place}.physicalDependencies содержит неизвестный component-ID`);
    if (!Array.isArray(draft.finalPart?.dimensions) || draft.finalPart.dimensions.length < 3) failures.push(`${place}.finalPart.dimensions неполон`);
    if (!/^#[a-z0-9]+-\d+$/.test(draft.finalPart?.partId ?? '')) failures.push(`${place}.finalPart.partId должен быть печатным ID`);
    if (!Array.isArray(draft.couponSets) || draft.couponSets.length < 1) failures.push(`${place}.couponSets должен содержать минимум одну независимую серию`);
    for (const output of draft.plannedOutputs ?? []) {
      if (path.isAbsolute(output) || output.split(/[\\/]/).includes('..')) failures.push(`${place}.plannedOutputs содержит небезопасный путь: ${output}`);
      if (fs.existsSync(path.join(root, output))) failures.push(`${place}: запланированный файл уже существует при статусе source-only-not-generated: ${output}`);
    }
  }
  return failures;
}

const source = JSON.parse(fs.readFileSync(componentPath, 'utf8'));
const physical = JSON.parse(fs.readFileSync(physicalComponentsPath, 'utf8'));
const media = JSON.parse(fs.readFileSync(drawingsPath, 'utf8'));
const cadDrafts = (media.catalogPolicy?.cadDraftSources ?? []).map(file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8')));
const identity = JSON.parse(fs.readFileSync(identityPath, 'utf8'));
const registry = JSON.parse(fs.readFileSync(partRegistryPath, 'utf8'));
const featureRegistry = JSON.parse(fs.readFileSync(featureRegistryPath, 'utf8'));
const currentVersion = fs.readFileSync(versionPath, 'utf8').trim();
const descriptionValidation = loadAndValidateMediaDescriptions(root, media, { throwOnFailure: false });
const mediaDescriptions = descriptionValidation.descriptions;
const failures = [...validate(source, physical, media, cadDrafts, identity, registry, featureRegistry, currentVersion), ...descriptionValidation.failures];
if (failures.length) {
  console.error(`Ошибки каталога:\n- ${failures.join('\n- ')}`);
  process.exit(1);
}

const categoryOrder = new Map(source.categories.map((category, index) => [category.id, index]));
const categoryLabels = new Map(source.categories.map(category => [category.id, category.label]));
const components = [...source.components].sort((a, b) => categoryOrder.get(a.category) - categoryOrder.get(b.category) || a.id.localeCompare(b.id));
const incompleteCount = components.filter(item => item.imageStatus === 'placeholder' || item.missing).length;
const repoUrl = file => `../${file.split(path.sep).join('/')}`;
const formatFileSize = bytes => {
  if (bytes < 1024) return `${bytes} Б`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1).replace('.', ',')} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} МБ`;
};
const fileSize = file => {
  const absolutePath = path.join(root, file);
  const bytes = readLfsPointer(absolutePath)?.size ?? fs.statSync(absolutePath).size;
  return formatFileSize(bytes);
};
const projectName = identity.projectDisplayName;
const componentNames = new Map(source.components.map(item => [item.id, item.name]));
const physicalById = new Map(physical.components.map(item => [item.id, item]));
const partItems = Object.values(registry.groups).flat();
const partNames = new Map(partItems.map(item => [item.id, item.label]));
const nameForId = id => partNames.get(id) ?? componentNames.get(id) ?? id;
const descriptionFor = item => mediaDescriptions.get(item.id);
const descriptionSummary = item => descriptionFor(item)?.metadata.summary ?? '';
const descriptionUrl = item => repoUrl(item.descriptionFile);

function renderLinks(links) {
  if (!links.length) return '<span class="empty">Ссылка пока не подтверждена</span>';
  return `<ul class="links">${links.map(link => `<li><a href="${escape(link.url)}" target="_blank" rel="noopener noreferrer">${escape(link.label)}</a></li>`).join('')}</ul>`;
}

function renderSpecifications(specifications = []) {
  return specifications.length
    ? `<dl class="specifications">${specifications.map(spec => `<div><dt>${escape(spec.label)}</dt><dd>${escape(spec.value)}</dd></div>`).join('')}</dl>`
    : '';
}

const measurementStatusLabels = new Map([
  ['measured', 'измерено'],
  ['calculated', 'рассчитано'],
  ['standard', 'стандарт'],
  ['seller', 'данные продавца'],
  ['seller-image', 'по изображению продавца'],
  ['provisional', 'предварительно'],
]);

function renderPhysicalMeasurements(item) {
  const measurements = item.measurements ?? [];
  const values = measurements.length
    ? `<dl class="physical-measurements">${measurements.map(measurement => `<div><dt>${escape(measurement.label)}</dt><dd><strong>${escape(measurement.value)}${measurement.unit ? ` ${escape(measurement.unit)}` : ''}</strong><span class="measurement-status">${escape(measurementStatusLabels.get(measurement.status) ?? measurement.status)}</span><small>Источник: ${escape(measurement.source)}</small></dd></div>`).join('')}</dl>`
    : '<p class="empty">Подтверждённых размеров пока нет.</p>';
  const needs = item.needs?.length ? `<aside class="physical-needs"><strong>Что измерить:</strong><ul>${item.needs.map(value => `<li>${escape(value)}</li>`).join('')}</ul></aside>` : '';
  return `<section class="physical-data" aria-labelledby="${escape(item.anchor)}-dimensions"><h4 id="${escape(item.anchor)}-dimensions">Физические размеры</h4>${values}${needs}<a class="physical-source" href="physical-components.json" target="_blank" rel="noopener">Единый источник размеров</a></section>`;
}

function renderBadge(status) {
  return status === 'confirmed' ? '<span class="badge ok">фото экземпляра</span>'
    : status === 'listing' ? '<span class="badge info">фото продавца</span>'
      : status === 'reference' ? '<span class="badge info">справочное изображение</span>'
        : '<span class="badge warning">нужно фото</span>';
}

function renderImages(item) {
  const images = [{ file: item.image, label: item.name }, ...(item.additionalImages ?? [])];
  return `<div class="gallery">${images.map(image => `<figure><img class="thumb" src="images/${escape(image.file)}" alt="${escape(image.label)}" loading="lazy"><figcaption>${escape(image.label)}<span class="asset-size">${fileSize(path.join('catalog', 'images', image.file))}</span></figcaption></figure>`).join('')}</div>${renderBadge(item.imageStatus)}`;
}

function renderAssetSizes(entries) {
  const unique = entries.filter((entry, index) => entries.findIndex(candidate => candidate.file === entry.file) === index);
  return `<p class="asset-sizes">${unique.map(entry => `<span><strong>${escape(entry.label)}:</strong> ${fileSize(entry.file)}</span>`).join('<span aria-hidden="true"> · </span>')}</p>`;
}

function visibleIds(item) {
  if (item.calloutMode === 'embedded') return item.partIds;
  return (item.callouts ?? []).map(callout => callout.id);
}

function renderCalloutLegend(item) {
  if (item.kind === 'print-layout') return `<p class="callout-exemption"><strong>Без выносок:</strong> ${escape(item.calloutExemptReason)}</p>`;
  const labels = item.calloutMode === 'embedded'
    ? item.partIds.map(id => ({ id, label: nameForId(id) }))
    : item.callouts.map(callout => ({ id: callout.id, label: callout.label }));
  return `<details class="callout-legend"><summary>Показанные ID: ${labels.length}</summary><ul>${labels.map(({ id, label }) => `<li><code>${escape(displayId(id))}</code> — ${escape(label)}</li>`).join('')}</ul></details>`;
}

function renderModelHotspots(item) {
  if (item.kind === 'print-layout') return '';
  return item.callouts.map((callout, index) => {
    const slot = `hotspot-${item.id}-${index}-${callout.id.replace(/[^a-zA-Z0-9_-]/g, '')}`;
    const position = callout.position.map(value => `${value}m`).join(' ');
    const normal = callout.normal.join(' ');
    const side = index % 2 === 0 ? 1 : -1;
    const tier = (Math.floor(index / 2) % 9) - 4;
    const x = side * (72 + Math.floor(index / 18) * 24);
    const y = tier * 24;
    const length = Math.hypot(x, y).toFixed(1);
    const angle = (Math.atan2(y, x) * 180 / Math.PI).toFixed(1);
    const shift = x < 0 ? '-100%' : '0%';
    const style = `--hx:${x}px;--hy:${y}px;--hlen:${length}px;--ha:${angle}deg;--hshift:${shift}`;
    return `<button class="model-hotspot" type="button" slot="${escape(slot)}" data-position="${escape(position)}" data-normal="${escape(normal)}" style="${escape(style)}" aria-label="${escape(`${displayId(callout.id)}: ${callout.label}`)}"><span class="hotspot-anchor" aria-hidden="true"></span><span class="hotspot-leg" aria-hidden="true"></span><span class="hotspot-card"><span class="hotspot-id">${escape(displayId(callout.id))}</span></span><span class="hotspot-label">${escape(callout.label)}</span></button>`;
  }).join('');
}

let currentCategory = '';
const rows = components.map(item => {
  const categoryRow = item.category !== currentCategory
    ? `<tr class="category-row" data-category-heading="${escape(item.category)}"><th colspan="5">${escape(categoryLabels.get(item.category))}</th></tr>`
    : '';
  currentCategory = item.category;
  const incomplete = item.imageStatus === 'placeholder' || Boolean(item.missing);
  const physicalItem = physicalById.get(item.id);
  const searchText = [item.id, item.name, ...item.aliases, item.purpose, ...(item.specifications ?? []).flatMap(spec => [spec.label, spec.value]), ...(physicalItem.measurements ?? []).flatMap(measurement => [measurement.label, measurement.value, measurement.unit]), item.missing ?? ''].join(' ').toLowerCase();
  return `${categoryRow}<tr id="${escape(physicalItem.anchor)}" class="component-row" data-category="${escape(item.category)}" data-incomplete="${incomplete}" data-search="${escape(searchText)}">
    <td class="id-cell"><code>${escape(displayId(item.id))}</code><a class="component-permalink" href="#${escape(physicalItem.anchor)}">ссылка</a><button class="copy-id" type="button" data-id="${escape(displayId(item.id))}">копировать</button></td>
    <td class="image-cell">${renderImages(item)}</td>
    <td><strong>${escape(item.name)}</strong><ul class="aliases">${item.aliases.map(alias => `<li>${escape(alias)}</li>`).join('')}</ul></td>
    <td><p>${escape(item.purpose)}</p>${renderPhysicalMeasurements(physicalItem)}${renderSpecifications(item.specifications)}${item.missing ? `<aside class="needed"><strong>Нужно уточнить:</strong> ${escape(item.missing)}</aside>` : ''}</td>
    <td>${renderLinks(item.links)}</td>
  </tr>`;
}).join('');

const drawings = media.drawings.map(item => {
  const fullPreview = item.calloutMode === 'overlay' ? item.annotatedPreview : item.preview;
  const thumbnailPreview = item.thumbnail;
  const mainAction = item.calloutMode === 'overlay' ? 'Открыть версию с выносками' : 'Открыть полный документ';
  const sizes = renderAssetSizes([
    { label: 'Миниатюра', file: thumbnailPreview },
    { label: item.calloutMode === 'overlay' ? 'Изображение с ID' : 'Полное изображение', file: fullPreview },
    { label: 'Исходник', file: item.file },
  ]);
  return `<article class="media-card" data-kind="${escape(item.kind)}">
  <a href="${escape(repoUrl(fullPreview))}" target="_blank" rel="noopener"><img src="${escape(repoUrl(thumbnailPreview))}" alt="${escape(`${item.title}; миниатюра без ID`)}" loading="lazy"></a>
  <div><span class="eyebrow">${escape(item.category)} · ${escape(displayId(item.id))}</span><span class="media-status">актуально · v${escape(item.version)}</span><h3>${escape(item.title)}</h3>${sizes}<p>${escape(descriptionSummary(item))}</p>
  <div class="media-actions"><a class="action" href="${escape(repoUrl(fullPreview))}" target="_blank" rel="noopener">${mainAction}</a>${item.calloutMode === 'overlay' ? `<a class="secondary-action" href="${escape(repoUrl(item.file))}" target="_blank" rel="noopener">Исходник без выносок</a>` : ''}<a class="description-link" href="${escape(descriptionUrl(item))}" target="_blank" rel="noopener">Подробное описание ${escape(displayId(item.id))}</a></div>${renderCalloutLegend(item)}</div>
</article>`;
}).join('');

function renderModelCard(item, badge = `актуально · v${item.version}`) {
  const source = item.calloutsFrom ? media.models.find(model => model.id === item.calloutsFrom) : null;
  const renderedItem = source ? { ...item, callouts: source.callouts } : item;
  return `<article class="model-card" data-title="${escape(item.title)}" data-kind="${escape(item.kind)}">
  <div class="viewer-shell">
    <model-viewer data-model data-src="${escape(repoUrl(item.file))}"${item.hardwareFile ? ` data-hardware-src="${escape(repoUrl(item.hardwareFile))}"` : ''} poster="${escape(repoUrl(item.poster))}" camera-controls auto-rotate shadow-intensity="1" alt="${escape(item.title)}">${renderModelHotspots(renderedItem)}</model-viewer>
    <button class="model-fullscreen" type="button" aria-label="Открыть модель на весь экран">На весь экран</button>
  </div>
  <div><span class="eyebrow">${escape(displayId(item.id))}</span><span class="media-status">${escape(badge)}</span><h3>${escape(item.title)}</h3>${renderAssetSizes([{ label: 'Постер', file: item.poster }, { label: 'GLB', file: item.file }, ...(item.hardwareFile ? [{ label: 'GLB с крепежом', file: item.hardwareFile }] : [])])}<p>${escape(descriptionSummary(item))}</p>
  <div class="model-actions"><button class="load-model" type="button">Загрузить интерактивную 3D-модель</button><a class="action" href="${escape(repoUrl(item.file))}" download>Скачать GLB</a><a class="description-link" href="${escape(descriptionUrl(item))}" target="_blank" rel="noopener">Подробное описание ${escape(displayId(item.id))}</a></div>
  <p class="model-status" aria-live="polite">Модель не загружена; изображение-постер сохранено.</p>${renderCalloutLegend(renderedItem)}</div>
</article>`;
}

const models = media.models.map(item => renderModelCard(item)).join('');

const printSessions = media.printSessions.map(item => `<article class="media-card print-session-card" data-kind="print-layout">
  <a href="${escape(repoUrl(item.file))}" target="_blank" rel="noopener"><img src="${escape(repoUrl(item.preview))}" alt="${escape(item.title)}" loading="lazy"></a>
  <div><span class="eyebrow">${escape(displayId(item.id))} · раздельная очередь</span><span class="media-status">актуально · v${escape(item.version)}</span><h3>${escape(item.title)}</h3>${renderAssetSizes([{ label: 'Изображение', file: item.preview }, { label: 'Исходник', file: item.file }])}<p>${escape(descriptionSummary(item))}</p><div class="media-actions"><a class="action" href="${escape(repoUrl(item.file))}" target="_blank" rel="noopener">Открыть раскладку</a><a class="description-link" href="${escape(descriptionUrl(item))}" target="_blank" rel="noopener">Подробное описание ${escape(displayId(item.id))}</a></div>${renderCalloutLegend(item)}</div>
</article>`).join('');

function renderCadDraftCard(draft, registryFile) {
  const dimensionRows = draft.finalPart.dimensions.map(item => `<tr><th>${escape(item.label)}</th><td><strong>${escape(item.value)} ${escape(item.unit)}</strong></td><td>${escape(item.status)}</td><td>${escape(item.reason)}</td></tr>`).join('');
  const couponSections = draft.couponSets.map(set => {
    const rows = set.variants.map(variant => {
      const bore = variant.boreDiameterMm ?? set.common.boreDiameterMm;
      const outer = variant.outerDiameterMm ?? set.common.outerDiameterMm;
      return `<tr><th>${escape(displayId(variant.id))}</th><td>Ø${escape(bore)} мм</td><td>Ø${escape(outer)} мм</td><td>${escape(set.common.heightMm)} мм</td></tr>`;
    }).join('');
    return `<section class="cad-coupon-set"><h4>${escape(set.label)}</h4><p>${escape(set.purpose)}</p><div class="cad-table-wrap"><table><thead><tr><th>ID</th><th>Отверстие</th><th>Наружный Ø</th><th>Высота</th></tr></thead><tbody>${rows}</tbody></table></div></section>`;
  }).join('');
  const dependencies = draft.physicalDependencies.map(item => `<li><a href="catalog.html#component-${escape(item.componentId)}" target="_blank" rel="noopener">${escape(displayId(item.componentId))}</a> — ${escape(item.role)}</li>`).join('');
  const rules = draft.finalPart.assemblyRules.map(rule => `<li>${escape(rule)}</li>`).join('');
  const acceptance = draft.acceptance.map(rule => `<li>${escape(rule)}</li>`).join('');
  const inner = draft.finalPart.dimensions.find(item => item.key === 'pole-bore-diameter')?.value;
  const outer = draft.finalPart.dimensions.find(item => item.key === 'bearing-seat-diameter')?.value;
  const schematic = draft.draftType === 'flexible-cable-strain-relief'
    ? `<div class="cad-draft-schematic cad-boot-schematic" role="img" aria-label="Схема гибкой закрытой втулки с шестью удерживающими рёбрами, коническим гофрированным хвостом и двумя каналами под жилы диаметром 2 мм"><div class="cad-pole-cut"><div class="cad-boot-seat"><i></i><i></i><i></i><i></i><i></i><i></i></div></div><div class="cad-boot-tail"><i></i><i></i><i></i><span class="cad-wire-hole one"></span><span class="cad-wire-hole two"></span></div><span class="cad-outer-label">6 рёбер · Ø24,7 мм</span><span class="cad-inner-label">2 × Ø2 мм</span></div>`
    : `<div class="cad-draft-schematic" role="img" aria-label="Схема кольцевой переходной втулки: наружный диаметр ${escape(outer)} мм, внутренний диаметр ${escape(inner)} мм"><div class="cad-ring"><div class="cad-bore"></div></div><span class="cad-outer-label">Ø${escape(outer)} мм</span><span class="cad-inner-label">Ø${escape(inner)} мм</span></div>`;
  return `<article id="cad-draft-${escape(draft.id)}" class="cad-draft-card">
    ${schematic}
    <div class="cad-draft-content"><span class="eyebrow">CAD-заготовка · ${escape(displayId(draft.id))}</span><span class="media-status draft-status">исходник без генерации</span><h3>${escape(draft.title)}</h3><p>${escape(draft.summary)}</p>
    <p><strong>Будущая деталь:</strong> ${escape(draft.finalPart.partId)} · ${escape(draft.finalPart.name)} · ${escape(draft.finalPart.quantity)} шт. · ${escape(draft.material)}</p>
    <div class="cad-table-wrap"><table><thead><tr><th>Размер финальной заготовки</th><th>Значение</th><th>Статус</th><th>Основание</th></tr></thead><tbody>${dimensionRows}</tbody></table></div>
    <h4>Физические зависимости</h4><ul>${dependencies}</ul><h4>Правила конструкции</h4><ul>${rules}</ul>${couponSections}<h4>Принятие</h4><ul>${acceptance}</ul>
    <div class="media-actions"><a class="action" href="${escape(repoUrl(registryFile))}" target="_blank" rel="noopener">Открыть единый файл размеров</a><a class="secondary-action" href="${escape(repoUrl(draft.sourceFile))}" target="_blank" rel="noopener">build123d-заготовка</a><a class="description-link" href="${escape(repoUrl(draft.documentation))}" target="_blank" rel="noopener">Техническое описание</a></div>
    <p class="callout-exemption"><strong>Файлы не созданы:</strong> карточка показывает параметры исходника; STL, STEP, GLB и изображение отсутствуют намеренно.</p></div>
  </article>`;
}

const cadDraftCards = cadDrafts.map((draft, index) => renderCadDraftCard(draft, media.catalogPolicy.cadDraftSources[index])).join('');

const categoryOptions = source.categories.map(category => `<option value="${escape(category.id)}">${escape(category.label)}</option>`).join('');
const calloutCount = media.drawings.filter(item => item.kind !== 'print-layout').length + media.models.filter(item => item.kind !== 'print-layout').length;

const html = `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(projectName)} — компоненты, актуальные чертежи и 3D</title>
<style>
:root{color-scheme:light dark;--bg:#edf1f3;--panel:#fff;--ink:#172126;--muted:#607078;--line:#d3dde1;--accent:#067a78;--warn:#9b4d00;--warn-bg:#fff0d9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}body.modal-open{overflow:hidden}header{padding:clamp(24px,5vw,56px);color:#fff;background:linear-gradient(125deg,#15373d,#087d78)}header h1{margin:0 0 8px;font-size:clamp(28px,5vw,48px);line-height:1.1}header p{max-width:970px;margin:0;color:#daf4f1}main{max-width:1500px;margin:auto;padding:24px}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:-48px;margin-bottom:20px}.metric{padding:16px 18px;border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:0 8px 30px #102d3320}.metric strong{display:block;font-size:28px;color:var(--accent)}.tabs{display:flex;gap:8px;margin:0 0 16px}.tab{padding:11px 18px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);font:inherit;font-weight:700;cursor:pointer}.tab[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.tab-panel[hidden]{display:none}.controls{display:flex;flex-wrap:wrap;align-items:end;gap:12px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.search{flex:1 1 330px}label span{display:block;margin-bottom:5px;font-weight:650}input[type="search"],select{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:9px;background:var(--panel);color:var(--ink);font:inherit}.category-filter{min-width:220px}.toggle{display:flex;align-items:center;gap:8px;padding:10px 4px}.toggle span{margin:0}.result-count{color:var(--muted);padding:10px 2px}.table-wrap{overflow:auto;margin-top:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}table{width:100%;min-width:1080px;border-collapse:collapse}th,td{padding:14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}thead th{position:sticky;top:0;z-index:2;background:#e4eeef;color:#27464c;font-size:13px;text-transform:uppercase;letter-spacing:.035em}.category-row th{background:#d8eeeb;color:#075b58;font-size:17px}.component-row:hover{background:#f3faf9}.id-cell code{display:block;font-weight:700;color:var(--accent)}.copy-id{margin-top:8px;padding:3px 7px;border:1px solid var(--line);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer}.thumb{width:180px;height:140px;object-fit:contain;display:block;border:1px solid var(--line);border-radius:9px;background:#fff}.badge{display:inline-block;margin-top:8px;padding:3px 8px;border-radius:999px;font-size:12px;font-weight:700}.warning{color:var(--warn);background:var(--warn-bg)}.ok{color:#126534;background:#dff4e7}.info{color:#075985;background:#e0f2fe}.aliases,.links{margin:8px 0 0;padding-left:18px}.specifications{display:grid;gap:6px;margin:12px 0 0}.specifications div{display:grid;grid-template-columns:minmax(95px,auto) 1fr;gap:8px;padding-top:6px;border-top:1px solid var(--line)}.specifications dt{font-weight:700;color:var(--muted)}.specifications dd{margin:0}.needed{margin-top:10px;padding:10px;border-left:4px solid #db7b16;background:var(--warn-bg);color:#633500}.empty,.model-status{color:var(--muted)}.no-results{display:none;padding:30px;text-align:center;color:var(--muted)}.section-intro{margin:0 0 18px}.policy-note{padding:14px 16px;border-left:4px solid var(--accent);border-radius:8px;background:var(--panel)}.media-grid,.model-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.media-card,.model-card{overflow:hidden;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.media-card img,model-viewer{display:block;width:100%;height:320px;object-fit:contain;background:#f8fafb}.media-card>div,.model-card>div:not(.viewer-shell){padding:16px}.media-card h3,.model-card h3{margin:4px 0}.eyebrow{color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase}.media-status{display:inline-block;margin-left:8px;padding:2px 7px;border-radius:999px;background:#dff4e7;color:#126534;font-size:11px;font-weight:800}.action,.secondary-action,.description-link{display:inline-block;color:var(--accent);font-weight:700}.secondary-action{font-weight:600}.description-link{font-weight:700;text-decoration-style:dotted}.media-actions,.model-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px}.models-heading{margin-top:32px}.load-model,.model-fullscreen{padding:9px 12px;border:0;border-radius:8px;background:var(--accent);color:#fff;font:inherit;font-weight:700;cursor:pointer}.load-model:disabled{opacity:.65;cursor:wait}.viewer-shell{position:relative}.model-fullscreen{position:absolute;right:12px;bottom:12px;z-index:4;box-shadow:0 2px 12px #0005}.model-card .viewer-shell>model-viewer .model-hotspot{display:none}.model-hotspot{position:relative;display:flex;align-items:center;gap:5px;padding:5px 8px;border:1px solid #172126;border-radius:999px;background:#fffffff2;color:#172126;font:700 12px/1.1 system-ui,sans-serif;box-shadow:0 2px 8px #0005;white-space:nowrap;cursor:default}.model-hotspot::before{content:"";position:absolute;width:9px;height:9px;border:2px solid #fff;border-radius:50%;background:#172126;transform:translate(-15px,0)}.hotspot-label{font-weight:500}.callout-legend{margin-top:14px;padding-top:10px;border-top:1px solid var(--line)}.callout-legend summary{cursor:pointer;font-weight:700;color:var(--accent)}.callout-legend ul{columns:2;column-gap:22px;padding-left:20px}.callout-legend li{break-inside:avoid;margin:4px 0}.callout-legend code{font-weight:800}.callout-exemption{margin:14px 0 0;padding:9px 11px;border-radius:8px;background:#eef2f4;color:#53626a}.fullscreen-overlay{position:fixed;inset:0;z-index:1000;display:grid;grid-template-rows:auto 1fr auto;background:#071013f5;color:#fff}.fullscreen-overlay[hidden]{display:none}.fullscreen-bar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 16px;background:#101d21}.fullscreen-bar h2{margin:0;font-size:18px}.fullscreen-controls{display:flex;align-items:center;gap:10px}.fullscreen-toggle-ids{height:46px;min-width:76px;padding:0 12px;border:1px solid #ffffff66;border-radius:23px;background:#203238;color:#fff;display:flex;align-items:center;justify-content:center;gap:7px;font:700 13px/1 system-ui,sans-serif;cursor:pointer}.fullscreen-toggle-ids[hidden]{display:none}.fullscreen-toggle-ids svg{width:23px;height:23px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}.fullscreen-toggle-ids .eye-slash{opacity:0}.fullscreen-toggle-ids[aria-pressed="false"]{background:#fff;color:#111}.fullscreen-toggle-ids[aria-pressed="false"] .eye-slash{opacity:1}.fullscreen-stage model-viewer.ids-hidden .model-hotspot{display:none}.fullscreen-close{width:46px;height:46px;border:0;border-radius:50%;background:#fff;color:#111;font-size:32px;line-height:1;cursor:pointer}.fullscreen-stage{min-height:0}.fullscreen-stage model-viewer{width:100%;height:100%;background:#0b1519}.fullscreen-hint{padding:8px 16px;margin:0;background:#101d21;color:#cfe2e5}footer{max-width:1500px;margin:auto;padding:0 24px 30px;color:var(--muted)}.gallery{display:grid;gap:8px}.gallery figure{margin:0}.gallery figcaption{margin-top:3px;max-width:180px;color:var(--muted);font-size:11px}@media(prefers-color-scheme:dark){:root{--bg:#0d171a;--panel:#152227;--ink:#edf6f5;--muted:#a5b5ba;--line:#34464c;--accent:#5ed5cd;--warn:#ffbd78;--warn-bg:#3b2b1b}thead th{background:#20343a;color:#c9e7e5}.category-row th{background:#193936;color:#aeece7}.component-row:hover{background:#193136}.needed{color:#ffd6a6}.thumb,.media-card img,model-viewer{background:#f8f8f8}a{color:#70c9ff}.callout-exemption{background:#263439;color:#c7d2d6}}@media(max-width:700px){main{padding:16px}.summary{margin-top:-32px}.copy-id{display:none}.media-card img,model-viewer{height:240px}.model-fullscreen{font-size:13px}.callout-legend ul{columns:1}.hotspot-label{display:none}}
.asset-size{display:block;font-weight:700}.asset-sizes{display:flex;flex-wrap:wrap;gap:4px;margin:6px 0 10px;color:var(--muted);font-size:13px}.asset-sizes strong{color:var(--ink)}
.cad-draft-card{display:grid;grid-template-columns:minmax(240px,340px) 1fr;overflow:hidden;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.cad-draft-card:target,.component-row:target{outline:4px solid color-mix(in srgb,var(--accent) 65%,transparent);outline-offset:3px}.cad-draft-content{padding:18px}.cad-draft-schematic{position:relative;display:grid;place-items:center;min-height:360px;padding:24px;background:linear-gradient(145deg,#e5ecef,#fafcfc);color:#172126}.cad-ring{display:grid;place-items:center;width:220px;height:220px;border:3px solid #9a551d;border-radius:50%;background:#ed914d;box-shadow:inset 0 0 0 2px #ffd7ba}.cad-bore{width:168px;height:168px;border:3px solid #77502f;border-radius:50%;background:#f8fafb}.cad-outer-label,.cad-inner-label{position:absolute;padding:4px 8px;border-radius:999px;background:#fffffff0;font-weight:800}.cad-outer-label{left:16px;bottom:38px}.cad-inner-label{right:16px;top:38px}.cad-table-wrap{overflow:auto}.cad-table-wrap table{min-width:680px;border:1px solid var(--line)}.cad-table-wrap th,.cad-table-wrap td{padding:8px 10px}.cad-coupon-set{margin-top:18px}.cad-coupon-set h4{margin-bottom:4px}.draft-status{background:#fff0d9;color:#8a4600}@media(max-width:850px){.cad-draft-card{grid-template-columns:1fr}.cad-draft-schematic{min-height:280px}}
.cad-boot-schematic{align-content:center}.cad-pole-cut{position:relative;width:150px;height:118px;border:8px solid #6f777b;border-bottom:0;background:#eef2f3}.cad-boot-seat{position:absolute;left:20px;right:20px;top:8px;height:110px;border-radius:12px 12px 4px 4px;background:#e9ecf0;border:3px solid #5d6770}.cad-boot-seat i{position:absolute;left:-6px;right:-6px;height:7px;border-radius:6px;background:#c9d0d6;border:2px solid #5d6770}.cad-boot-seat i:nth-child(1){top:8px}.cad-boot-seat i:nth-child(2){top:25px}.cad-boot-seat i:nth-child(3){top:42px}.cad-boot-seat i:nth-child(4){top:59px}.cad-boot-seat i:nth-child(5){top:76px}.cad-boot-seat i:nth-child(6){top:93px}.cad-boot-tail{position:relative;width:92px;height:148px;margin-top:-2px;border-radius:8px 8px 34px 34px;background:linear-gradient(90deg,#d7dce1,#f4f6f7 45%,#bfc7cd);border:3px solid #5d6770;clip-path:polygon(0 0,100% 0,72% 100%,28% 100%)}.cad-boot-tail>i{position:absolute;left:8px;right:8px;height:9px;border-radius:50%;background:#89949c}.cad-boot-tail>i:nth-child(1){top:32px}.cad-boot-tail>i:nth-child(2){top:70px}.cad-boot-tail>i:nth-child(3){top:106px}.cad-wire-hole{position:absolute;bottom:8px;width:10px;height:24px;border-radius:6px;background:#20282c}.cad-wire-hole.one{left:34px}.cad-wire-hole.two{right:34px}
.component-permalink{display:block;margin:5px 0;font-size:12px}.physical-data{margin:12px 0;padding:11px;border:1px solid var(--line);border-radius:9px;background:color-mix(in srgb,var(--panel) 88%,var(--accent) 12%)}.physical-data h4{margin:0 0 7px}.physical-measurements{display:grid;gap:6px;margin:0}.physical-measurements div{display:grid;grid-template-columns:minmax(150px,1fr) minmax(180px,1.2fr);gap:8px;padding-top:6px;border-top:1px solid var(--line)}.physical-measurements dt{font-weight:650}.physical-measurements dd{margin:0}.physical-measurements small{display:block;color:var(--muted)}.measurement-status{display:inline-block;margin-left:7px;padding:1px 6px;border-radius:999px;background:var(--panel);color:var(--muted);font-size:11px}.physical-needs{margin-top:9px;color:var(--muted)}.physical-needs ul{margin:4px 0;padding-left:18px}.physical-source{display:inline-block;margin-top:7px;font-weight:700}@media(max-width:700px){.physical-measurements div{grid-template-columns:1fr}}
.model-hotspot{position:relative;width:1px;height:1px;padding:0;border:0;border-radius:0;background:transparent;color:#172126;font:700 12px/1.1 system-ui,sans-serif;box-shadow:none;overflow:visible;cursor:default}.model-hotspot::before{display:none}.hotspot-anchor{position:absolute;left:0;top:0;width:10px;height:10px;border:2px solid #fff;border-radius:50%;background:#172126;box-shadow:0 1px 4px #0008;transform:translate(-50%,-50%)}.hotspot-leg{position:absolute;left:0;top:0;width:var(--hlen);border-top:2px solid #172126;filter:drop-shadow(0 0 1px #fff);transform:rotate(var(--ha));transform-origin:0 0}.hotspot-card{position:absolute;left:var(--hx);top:var(--hy);display:block;padding:5px 8px;border:1px solid #172126;border-radius:999px;background:#fffffff2;box-shadow:0 2px 8px #0005;white-space:nowrap;transform:translate(var(--hshift),-50%)}.hotspot-label{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
</style></head><body>
<header><h1>Проект ${escape(projectName)}</h1><p>Каталог компонентов и только актуальных чертежей/3D версии v${escape(currentVersion)}. Все непечатные виды имеют стабильные ID-выноски; раскладки печати оставлены чистыми намеренно.</p></header>
<main><section class="summary" aria-label="Сводка"><div class="metric"><strong>${components.length}</strong>компонентов</div><div class="metric"><strong>${source.categories.length}</strong>категорий</div><div class="metric"><strong>${media.drawings.length}</strong>актуальных чертежей</div><div class="metric"><strong>${media.models.length}</strong>актуальных 3D-моделей</div><div class="metric"><strong>${cadDrafts.length}</strong>CAD-заготовок</div><div class="metric"><strong>${calloutCount}</strong>видов с ID</div><div class="metric"><strong>${mediaDescriptions.size}</strong>подробных описаний</div><div class="metric"><strong>${incompleteCount}</strong>нужно уточнить</div></section>
<nav class="tabs" role="tablist" aria-label="Разделы проекта"><button class="tab" role="tab" id="components-tab" aria-controls="components-panel" aria-selected="true">Компоненты</button><button class="tab" role="tab" id="drawings-tab" aria-controls="drawings-panel" aria-selected="false">Чертежи и 3D</button></nav>
<section id="components-panel" class="tab-panel" role="tabpanel" aria-labelledby="components-tab"><section class="controls" aria-label="Фильтры"><label class="search"><span>Поиск по ID, названию и назначению</span><input id="search" type="search" placeholder="например: 009, 6804, датчик"></label><label class="category-filter"><span>Категория</span><select id="category"><option value="">Все категории</option>${categoryOptions}</select></label><label class="toggle"><input id="incompleteOnly" type="checkbox"><span>Только позиции, которые нужно уточнить</span></label><output id="resultCount" class="result-count"></output></section>
<div class="table-wrap"><table id="catalogTable"><thead><tr><th>ID</th><th>Картинка</th><th>Возможные названия компонента</th><th>Зачем он нужен</th><th>Описание или покупка</th></tr></thead><tbody>${rows}</tbody></table><p id="noResults" class="no-results">По заданному фильтру ничего не найдено.</p></div></section>
<section id="drawings-panel" class="tab-panel" role="tabpanel" aria-labelledby="drawings-tab" hidden><p class="section-intro policy-note"><strong>Правило публикации:</strong> здесь нет исторических карточек и смешения версий. Подписанные PNG-копии генерируются из чистых исходников; интерактивные GLB получают hotspots. Исходные CAD-заготовки показываются отдельно и явно не выдаются за сгенерированные модели.</p><div class="media-grid">${drawings}</div><h2 class="models-heading">CAD-заготовки без генерации</h2><p class="section-intro">Эти карточки показывают единые параметры будущих деталей и пробников. У них ещё нет STL, STEP, GLB или изображений.</p><div class="cad-draft-grid">${cadDraftCards}</div><h2 class="models-heading">Интерактивные 3D-модели</h2><p class="section-intro">GLB и модуль просмотра загружаются только после нажатия. В карточках ID скрыты; в полноэкранном режиме их можно показать или убрать кнопкой рядом с крестиком.</p><div class="model-grid">${models}</div><h2 class="models-heading">Раздельные очереди печати по материалам</h2><p class="section-intro">За один запуск печатается только один основной пластик. Эти раскладки печати намеренно не содержат выносок.</p><div class="media-grid">${printSessions}</div></section>
</main>
<footer>Источники: <code>catalog/components.json</code>, <code>catalog/physical-components.json</code>, <code>catalog/drawings.json</code>, перечисленные там <code>mechanical/cad_drafts/*.json</code>, <code>catalog/media-descriptions/&lt;ID&gt;.md</code>, <code>mechanical/part_id_registry_v06.json</code>, <code>VERSION.txt</code> и <code>project_identity.json</code>. Сгенерированный HTML вручную не редактировать.</footer>
<div id="fullscreenOverlay" class="fullscreen-overlay" hidden role="dialog" aria-modal="true" aria-labelledby="fullscreenTitle"><div class="fullscreen-bar"><h2 id="fullscreenTitle">3D-модель</h2><div class="fullscreen-controls"><button id="fullscreenToggleIds" class="fullscreen-toggle-ids" type="button" aria-pressed="true" aria-label="Скрыть ID-метки" title="Скрыть ID-метки" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2.5 12s3.7-6 9.5-6 9.5 6 9.5 6-3.7 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.8"/><path class="eye-slash" d="M4 4l16 16"/></svg><span>ID</span></button><button id="fullscreenToggleHardware" class="fullscreen-toggle-ids" type="button" aria-pressed="false" aria-label="Показать крепёж" title="Показать крепёж" hidden><span>Крепёж</span></button><button id="fullscreenClose" class="fullscreen-close" type="button" aria-label="Закрыть полноэкранный режим">×</button></div></div><div class="fullscreen-stage"><model-viewer id="fullscreenViewer" camera-controls auto-rotate shadow-intensity="1"></model-viewer></div><p class="fullscreen-hint">Вращайте мышью или пальцем. ID и упрощённый крепёж переключаются отдельными кнопками рядом с крестиком. Закрыть: × или Escape.</p></div>
<script>
const tabs=[...document.querySelectorAll('[role="tab"]')];function activateTab(tab){for(const button of tabs){const selected=button===tab;button.setAttribute('aria-selected',String(selected));document.getElementById(button.getAttribute('aria-controls')).hidden=!selected;}}for(const tab of tabs)tab.addEventListener('click',()=>activateTab(tab));function activateTabForHash(){if(location.hash.startsWith('#cad-draft-'))activateTab(document.getElementById('drawings-tab'));else if(location.hash.startsWith('#component-'))activateTab(document.getElementById('components-tab'));}window.addEventListener('hashchange',activateTabForHash);activateTabForHash();
const input=document.getElementById('search'),category=document.getElementById('category'),incompleteOnly=document.getElementById('incompleteOnly'),table=document.getElementById('catalogTable'),resultCount=document.getElementById('resultCount'),noResults=document.getElementById('noResults');
function applyFilters(){const query=input.value.trim().toLowerCase(),selectedCategory=category.value;let visible=0;for(const row of table.querySelectorAll('.component-row')){row.hidden=!(row.dataset.search.includes(query)&&(!selectedCategory||row.dataset.category===selectedCategory)&&(!incompleteOnly.checked||row.dataset.incomplete==='true'));if(!row.hidden)visible++;}for(const heading of table.querySelectorAll('.category-row'))heading.hidden=![...table.querySelectorAll('.component-row')].some(row=>!row.hidden&&row.dataset.category===heading.dataset.categoryHeading);resultCount.value='Показано: '+visible;noResults.style.display=visible?'none':'block';}
input.addEventListener('input',applyFilters);category.addEventListener('change',applyFilters);incompleteOnly.addEventListener('change',applyFilters);for(const button of document.querySelectorAll('.copy-id'))button.addEventListener('click',async()=>{await navigator.clipboard.writeText(button.dataset.id);const old=button.textContent;button.textContent='скопировано';setTimeout(()=>button.textContent=old,1200);});applyFilters();
let viewerRuntime;function loadViewerRuntime(){if(!viewerRuntime)viewerRuntime=new Promise((resolve,reject)=>{const script=document.createElement('script');script.type='module';script.src='https://ajax.googleapis.com/ajax/libs/model-viewer/4.2.0/model-viewer.min.js';script.onload=resolve;script.onerror=reject;document.head.append(script);});return viewerRuntime;}
async function ensureModel(card){const viewer=card.querySelector('[data-model]'),status=card.querySelector('.model-status'),button=card.querySelector('.load-model');if(viewer.src)return viewer;button.disabled=true;status.textContent='Загружается модуль просмотра…';await loadViewerRuntime();status.textContent='Загружается GLB…';viewer.src=viewer.dataset.src;await new Promise((resolve,reject)=>{viewer.addEventListener('load',resolve,{once:true});viewer.addEventListener('error',reject,{once:true});});status.textContent=card.dataset.kind==='print-layout'?'Готово: раскладка без выносок.':'Готово: модель можно вращать; ID-метки привязаны к деталям.';button.hidden=true;return viewer;}
for(const button of document.querySelectorAll('.load-model'))button.addEventListener('click',async()=>{const card=button.closest('.model-card');try{await ensureModel(card);}catch{card.querySelector('.model-status').textContent='Не удалось загрузить модель. Запустите локальный HTTP-сервер или скачайте GLB.';button.disabled=false;}});
const overlay=document.getElementById('fullscreenOverlay'),fullscreenViewer=document.getElementById('fullscreenViewer'),fullscreenTitle=document.getElementById('fullscreenTitle'),fullscreenToggleIds=document.getElementById('fullscreenToggleIds'),fullscreenToggleHardware=document.getElementById('fullscreenToggleHardware'),fullscreenClose=document.getElementById('fullscreenClose');
function setFullscreenIdsVisible(visible){fullscreenViewer.classList.toggle('ids-hidden',!visible);fullscreenToggleIds.setAttribute('aria-pressed',String(visible));const label=visible?'Скрыть ID-метки':'Показать ID-метки';fullscreenToggleIds.setAttribute('aria-label',label);fullscreenToggleIds.title=label;}
function setHardwareButtonVisible(visible){fullscreenToggleHardware.setAttribute('aria-pressed',String(visible));const label=visible?'Скрыть крепёж':'Показать крепёж';fullscreenToggleHardware.setAttribute('aria-label',label);fullscreenToggleHardware.title=label;}
async function setFullscreenHardwareVisible(visible){const target=visible?fullscreenViewer.dataset.hardwareSrc:fullscreenViewer.dataset.cleanSrc;if(!target)return;setHardwareButtonVisible(visible);fullscreenViewer.src=target;}
function copyHotspots(source,target){target.querySelectorAll('.model-hotspot').forEach(node=>node.remove());for(const hotspot of source.querySelectorAll('.model-hotspot'))target.append(hotspot.cloneNode(true));}
let hotspotLayoutFrame=0;
function layoutFullscreenHotspots(){hotspotLayoutFrame=0;if(overlay.hidden)return;const viewerRect=fullscreenViewer.getBoundingClientRect();const entries=[...fullscreenViewer.querySelectorAll('.model-hotspot')].map(hotspot=>{const anchor=hotspot.querySelector('.hotspot-anchor')?.getBoundingClientRect();return anchor?{hotspot,x:anchor.left+anchor.width/2-viewerRect.left,y:anchor.top+anchor.height/2-viewerRect.top}:null;}).filter(Boolean).sort((a,b)=>a.y-b.y);const left=[],right=[];entries.forEach((entry,index)=>(index%2?right:left).push(entry));const place=(group,isRight)=>{if(!group.length)return;const usable=Math.max(120,viewerRect.height-44);const gap=Math.min(28,usable/group.length);const start=(viewerRect.height-gap*(group.length-1))/2;const labelX=isRight?viewerRect.width-18:18;group.forEach((entry,index)=>{const labelY=start+index*gap;const dx=labelX-entry.x;const dy=labelY-entry.y;entry.hotspot.style.setProperty('--hx',dx+'px');entry.hotspot.style.setProperty('--hy',dy+'px');entry.hotspot.style.setProperty('--hlen',Math.hypot(dx,dy).toFixed(1)+'px');entry.hotspot.style.setProperty('--ha',(Math.atan2(dy,dx)*180/Math.PI).toFixed(1)+'deg');entry.hotspot.style.setProperty('--hshift',isRight?'-100%':'0%');});};place(left,false);place(right,true);}
function scheduleHotspotLayout(){if(!hotspotLayoutFrame)hotspotLayoutFrame=requestAnimationFrame(layoutFullscreenHotspots);}
async function openFullscreen(card){try{const viewer=await ensureModel(card);await loadViewerRuntime();fullscreenTitle.textContent=card.dataset.title;fullscreenViewer.poster=viewer.poster;copyHotspots(viewer,fullscreenViewer);const hasHotspots=Boolean(fullscreenViewer.querySelector('.model-hotspot'));fullscreenToggleIds.hidden=!hasHotspots;setFullscreenIdsVisible(true);fullscreenViewer.dataset.cleanSrc=viewer.src;fullscreenViewer.dataset.hardwareSrc=viewer.dataset.hardwareSrc||'';fullscreenToggleHardware.hidden=!viewer.dataset.hardwareSrc;setHardwareButtonVisible(false);fullscreenViewer.src=viewer.src;overlay.hidden=false;document.body.classList.add('modal-open');scheduleHotspotLayout();if(overlay.requestFullscreen){try{await overlay.requestFullscreen();}catch{}}fullscreenClose.focus();}catch{card.querySelector('.model-status').textContent='Полноэкранный режим недоступен: модель не загрузилась.';}}
async function closeFullscreen(){if(document.fullscreenElement){try{await document.exitFullscreen();}catch{}}overlay.hidden=true;document.body.classList.remove('modal-open');fullscreenViewer.removeAttribute('src');fullscreenViewer.querySelectorAll('.model-hotspot').forEach(node=>node.remove());fullscreenToggleIds.hidden=true;fullscreenToggleHardware.hidden=true;setFullscreenIdsVisible(true);setHardwareButtonVisible(false);}
fullscreenViewer.addEventListener('load',scheduleHotspotLayout);fullscreenViewer.addEventListener('camera-change',scheduleHotspotLayout);window.addEventListener('resize',scheduleHotspotLayout);for(const button of document.querySelectorAll('.model-fullscreen'))button.addEventListener('click',()=>openFullscreen(button.closest('.model-card')));fullscreenToggleIds.addEventListener('click',()=>setFullscreenIdsVisible(fullscreenToggleIds.getAttribute('aria-pressed')!=='true'));fullscreenToggleHardware.addEventListener('click',()=>setFullscreenHardwareVisible(fullscreenToggleHardware.getAttribute('aria-pressed')!=='true'));fullscreenClose.addEventListener('click',closeFullscreen);document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!overlay.hidden)closeFullscreen();});document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&!overlay.hidden){overlay.hidden=true;document.body.classList.remove('modal-open');fullscreenViewer.removeAttribute('src');fullscreenViewer.querySelectorAll('.model-hotspot').forEach(node=>node.remove());fullscreenToggleIds.hidden=true;fullscreenToggleHardware.hidden=true;setFullscreenIdsVisible(true);setHardwareButtonVisible(false);}else if(!overlay.hidden){scheduleHotspotLayout();}});
</script></body></html>`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf8') : '';
  if (current !== html) {
    console.error('catalog/catalog.html не соответствует JSON-источникам. Запустите npm run catalog:generate.');
    process.exit(1);
  }
  console.log(`Каталог v${currentVersion} синхронизирован: только актуальные материалы, обязательные ID-выноски и ${mediaDescriptions.size} синхронизированных подробных описаний.`);
} else {
  fs.writeFileSync(htmlPath, html, 'utf8');
  console.log(`Generated ${htmlPath}`);
}
