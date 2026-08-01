import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const componentPath = path.join(root, 'catalog', 'components.json');
const drawingsPath = path.join(root, 'catalog', 'drawings.json');
const imageDirectory = path.join(root, 'catalog', 'images');
const htmlPath = path.join(root, 'catalog', 'catalog.html');

const escape = value => String(value)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

function validateAsset(value, place, failures) {
  if (!value?.trim() || path.isAbsolute(value) || value.split(/[\\/]/).includes('..')) {
    failures.push(`${place} должен быть безопасным путём относительно корня проекта`);
  } else if (!fs.existsSync(path.join(root, value))) {
    failures.push(`${place} не найден: ${value}`);
  }
}

function validate(source, media) {
  const failures = [];
  const ids = new Set();
  const categoryIds = new Set();
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
    if (!/^cmp-\d{3}$/.test(item.id ?? '')) failures.push(`${place}.id должен иметь вид cmp-001`);
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
      try { if (new URL(link.url).protocol !== 'https:') throw new Error(); }
      catch { failures.push(`${place}.links[${linkIndex}].url должен быть корректным HTTPS URL`); }
    }
    for (const [specIndex, spec] of (item.specifications ?? []).entries()) {
      if (!spec.label?.trim() || !spec.value?.trim()) failures.push(`${place}.specifications[${specIndex}] требует label и value`);
    }
  }
  const sortedIds = [...ids].sort();
  sortedIds.forEach((id, index) => {
    const expected = `cmp-${String(index + 1).padStart(3, '0')}`;
    if (id !== expected) failures.push(`ID должны идти без пропусков: ожидался ${expected}, найден ${id}`);
  });
  if (media.schemaVersion !== 1) failures.push('schemaVersion drawings.json должен быть равен 1');
  for (const group of ['drawings', 'models']) {
    if (!Array.isArray(media[group])) failures.push(`${group} должен быть массивом`);
    for (const [index, item] of (media[group] ?? []).entries()) {
      if (!item.id?.trim() || !item.title?.trim() || !item.description?.trim()) failures.push(`${group}[${index}] требует id, title и description`);
      validateAsset(item.file, `${group}[${index}].file`, failures);
      validateAsset(group === 'drawings' ? item.preview : item.poster, `${group}[${index}].${group === 'drawings' ? 'preview' : 'poster'}`, failures);
    }
  }
  return failures;
}

const source = JSON.parse(fs.readFileSync(componentPath, 'utf8'));
const media = JSON.parse(fs.readFileSync(drawingsPath, 'utf8'));
const failures = validate(source, media);
if (failures.length) {
  console.error(`Ошибки каталога:\n- ${failures.join('\n- ')}`);
  process.exit(1);
}

const categoryOrder = new Map(source.categories.map((category, index) => [category.id, index]));
const categoryLabels = new Map(source.categories.map(category => [category.id, category.label]));
const components = [...source.components].sort((a, b) => categoryOrder.get(a.category) - categoryOrder.get(b.category) || a.id.localeCompare(b.id));
const incompleteCount = components.filter(item => item.imageStatus === 'placeholder' || item.missing).length;
const repoUrl = file => `../${file.split(path.sep).join('/')}`;
const fileSize = file => `${(fs.statSync(path.join(root, file)).size / 1024 / 1024).toFixed(1).replace('.', ',')} МБ`;

function renderLinks(links) {
  if (!links.length) return '<span class="empty">Ссылка пока не подтверждена</span>';
  return `<ul class="links">${links.map(link => `<li><a href="${escape(link.url)}" target="_blank" rel="noopener noreferrer">${escape(link.label)}</a></li>`).join('')}</ul>`;
}
function renderSpecifications(specifications = []) {
  return specifications.length ? `<dl class="specifications">${specifications.map(spec => `<div><dt>${escape(spec.label)}</dt><dd>${escape(spec.value)}</dd></div>`).join('')}</dl>` : '';
}
function renderBadge(status) {
  return status === 'confirmed' ? '<span class="badge ok">фото экземпляра</span>'
    : status === 'listing' ? '<span class="badge info">фото продавца</span>'
      : status === 'reference' ? '<span class="badge info">справочное изображение</span>'
        : '<span class="badge warning">нужно фото</span>';
}
function renderImages(item) {
  const images = [{ file: item.image, label: item.name }, ...(item.additionalImages ?? [])];
  return `<div class="gallery">${images.map(image => `<figure><img class="thumb" src="images/${escape(image.file)}" alt="${escape(image.label)}" loading="lazy"><figcaption>${escape(image.label)}</figcaption></figure>`).join('')}</div>${renderBadge(item.imageStatus)}`;
}

let currentCategory = '';
const rows = components.map(item => {
  const categoryRow = item.category !== currentCategory
    ? `<tr class="category-row" data-category-heading="${escape(item.category)}"><th colspan="5">${escape(categoryLabels.get(item.category))}</th></tr>` : '';
  currentCategory = item.category;
  const incomplete = item.imageStatus === 'placeholder' || Boolean(item.missing);
  const searchText = [item.id, item.name, ...item.aliases, item.purpose, ...(item.specifications ?? []).flatMap(spec => [spec.label, spec.value]), item.missing ?? ''].join(' ').toLowerCase();
  return `${categoryRow}<tr class="component-row" data-category="${escape(item.category)}" data-incomplete="${incomplete}" data-search="${escape(searchText)}">
    <td class="id-cell"><code>${escape(item.id)}</code><button class="copy-id" type="button" data-id="${escape(item.id)}">копировать</button></td>
    <td class="image-cell">${renderImages(item)}</td>
    <td><strong>${escape(item.name)}</strong><ul class="aliases">${item.aliases.map(alias => `<li>${escape(alias)}</li>`).join('')}</ul></td>
    <td><p>${escape(item.purpose)}</p>${renderSpecifications(item.specifications)}${item.missing ? `<aside class="needed"><strong>Нужно уточнить:</strong> ${escape(item.missing)}</aside>` : ''}</td>
    <td>${renderLinks(item.links)}</td>
  </tr>`;
}).join('');

const drawings = media.drawings.map(item => `<article class="media-card"><a href="${escape(repoUrl(item.file))}" target="_blank"><img src="${escape(repoUrl(item.preview))}" alt="${escape(item.title)}" loading="lazy"></a><div><span class="eyebrow">${escape(item.category)} · ${escape(item.id)}</span><h3>${escape(item.title)}</h3><p>${escape(item.description)}</p><a class="action" href="${escape(repoUrl(item.file))}" target="_blank">Открыть оригинал</a></div></article>`).join('');
const models = media.models.map(item => `<article class="model-card"><model-viewer data-model data-src="${escape(repoUrl(item.file))}" poster="${escape(repoUrl(item.poster))}" camera-controls auto-rotate shadow-intensity="1" alt="${escape(item.title)}"></model-viewer><div><span class="eyebrow">${escape(item.id)} · ${fileSize(item.file)}</span><h3>${escape(item.title)}</h3><p>${escape(item.description)}</p><div class="model-actions"><button class="load-model" type="button">Загрузить интерактивную 3D-модель</button><a class="action" href="${escape(repoUrl(item.file))}" download>Скачать GLB</a></div><p class="model-status" aria-live="polite">Модель не загружена.</p></div></article>`).join('');
const categoryOptions = source.categories.map(category => `<option value="${escape(category.id)}">${escape(category.label)}</option>`).join('');

const html = `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Crucian — компоненты, чертежи и 3D</title>
<style>
:root{color-scheme:light dark;--bg:#edf1f3;--panel:#fff;--ink:#172126;--muted:#607078;--line:#d3dde1;--accent:#067a78;--warn:#9b4d00;--warn-bg:#fff0d9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}header{padding:clamp(24px,5vw,56px);color:#fff;background:linear-gradient(125deg,#15373d,#087d78)}header h1{margin:0 0 8px;font-size:clamp(28px,5vw,48px);line-height:1.1}header p{max-width:900px;margin:0;color:#daf4f1}main{max-width:1500px;margin:auto;padding:24px}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:-48px;margin-bottom:20px}.metric{padding:16px 18px;border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:0 8px 30px #102d3320}.metric strong{display:block;font-size:28px;color:var(--accent)}.tabs{display:flex;gap:8px;margin:0 0 16px}.tab{padding:11px 18px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);font:inherit;font-weight:700;cursor:pointer}.tab[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.tab-panel[hidden]{display:none}.controls{display:flex;flex-wrap:wrap;align-items:end;gap:12px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.search{flex:1 1 330px}label span{display:block;margin-bottom:5px;font-weight:650}input[type="search"],select{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:9px;background:var(--panel);color:var(--ink);font:inherit}.category-filter{min-width:220px}.toggle{display:flex;align-items:center;gap:8px;padding:10px 4px}.toggle span{margin:0}.result-count{color:var(--muted);padding:10px 2px}.table-wrap{overflow:auto;margin-top:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}table{width:100%;min-width:1080px;border-collapse:collapse}th,td{padding:14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}thead th{position:sticky;top:0;z-index:2;background:#e4eeef;color:#27464c;font-size:13px;text-transform:uppercase;letter-spacing:.035em}.category-row th{background:#d8eeeb;color:#075b58;font-size:17px}.component-row:hover{background:#f3faf9}.id-cell code{display:block;font-weight:700;color:var(--accent)}.copy-id{margin-top:8px;padding:3px 7px;border:1px solid var(--line);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer}.gallery{display:grid;gap:8px}.gallery figure{margin:0}.gallery figcaption{margin-top:3px;max-width:180px;color:var(--muted);font-size:11px}.thumb{width:180px;height:140px;object-fit:contain;display:block;border:1px solid var(--line);border-radius:9px;background:#fff}.badge{display:inline-block;margin-top:8px;padding:3px 8px;border-radius:999px;font-size:12px;font-weight:700}.warning{color:var(--warn);background:var(--warn-bg)}.ok{color:#126534;background:#dff4e7}.info{color:#075985;background:#e0f2fe}.aliases,.links{margin:8px 0 0;padding-left:18px}.specifications{display:grid;gap:6px;margin:12px 0 0}.specifications div{display:grid;grid-template-columns:minmax(95px,auto) 1fr;gap:8px;padding-top:6px;border-top:1px solid var(--line)}.specifications dt{font-weight:700;color:var(--muted)}.specifications dd{margin:0}.needed{margin-top:10px;padding:10px;border-left:4px solid #db7b16;background:var(--warn-bg);color:#633500}.empty,.model-status{color:var(--muted)}.no-results{display:none;padding:30px;text-align:center;color:var(--muted)}.section-intro{margin:0 0 18px}.media-grid,.model-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.media-card,.model-card{overflow:hidden;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.media-card img,model-viewer{display:block;width:100%;height:320px;object-fit:contain;background:#f8fafb}.media-card>div,.model-card>div{padding:16px}.media-card h3,.model-card h3{margin:4px 0}.eyebrow{color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase}.action{display:inline-block;color:var(--accent);font-weight:700}.models-heading{margin-top:32px}.model-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px}.load-model{padding:9px 12px;border:0;border-radius:8px;background:var(--accent);color:#fff;font:inherit;font-weight:700;cursor:pointer}.load-model:disabled{opacity:.65;cursor:wait}footer{max-width:1500px;margin:auto;padding:0 24px 30px;color:var(--muted)}@media(prefers-color-scheme:dark){:root{--bg:#0d171a;--panel:#152227;--ink:#edf6f5;--muted:#a5b5ba;--line:#34464c;--accent:#5ed5cd;--warn:#ffbd78;--warn-bg:#3b2b1b}thead th{background:#20343a;color:#c9e7e5}.category-row th{background:#193936;color:#aeece7}.component-row:hover{background:#193136}.needed{color:#ffd6a6}.thumb,.media-card img,model-viewer{background:#f8f8f8}a{color:#70c9ff}}@media(max-width:700px){main{padding:16px}.summary{margin-top:-32px}.copy-id{display:none}.media-card img,model-viewer{height:240px}}
</style></head><body>
<header><h1>Проект Crucian</h1><p>Каталог компонентов, актуальные схемы и интерактивный просмотр текущих 3D-моделей. Карточки сгруппированы по назначению.</p></header>
<main><section class="summary" aria-label="Сводка"><div class="metric"><strong>${components.length}</strong>компонентов</div><div class="metric"><strong>${source.categories.length}</strong>категорий</div><div class="metric"><strong>${media.drawings.length}</strong>чертежей и видов</div><div class="metric"><strong>${media.models.length}</strong>3D-модели</div></section>
<nav class="tabs" role="tablist" aria-label="Разделы проекта"><button class="tab" role="tab" id="components-tab" aria-controls="components-panel" aria-selected="true">Компоненты</button><button class="tab" role="tab" id="drawings-tab" aria-controls="drawings-panel" aria-selected="false">Чертежи и 3D</button></nav>
<section id="components-panel" class="tab-panel" role="tabpanel" aria-labelledby="components-tab"><section class="controls" aria-label="Фильтры"><label class="search"><span>Поиск по ID, названию и назначению</span><input id="search" type="search" placeholder="например: cmp-008, 6804, датчик"></label><label class="category-filter"><span>Категория</span><select id="category"><option value="">Все категории</option>${categoryOptions}</select></label><label class="toggle"><input id="incompleteOnly" type="checkbox"><span>Только позиции, которые нужно уточнить</span></label><output id="resultCount" class="result-count"></output></section>
<div class="table-wrap"><table id="catalogTable"><thead><tr><th>ID</th><th>Картинка</th><th>Возможные названия компонента</th><th>Зачем он нужен</th><th>Описание или покупка</th></tr></thead><tbody>${rows}</tbody></table><p id="noResults" class="no-results">По заданному фильтру ничего не найдено.</p></div></section>
<section id="drawings-panel" class="tab-panel" role="tabpanel" aria-labelledby="drawings-tab" hidden><p class="section-intro">Превью загружаются локально. По ссылке открывается исходный SVG или PNG в полном размере.</p><div class="media-grid">${drawings}</div><h2 class="models-heading">Интерактивные 3D-модели</h2><p class="section-intro">GLB и модуль просмотра не загружаются, пока вы не нажмёте кнопку. Для вращения модели нужен локальный HTTP-сервер и доступ к интернету только для лёгкого компонента просмотра.</p><div class="model-grid">${models}</div></section></main>
<footer>Источники данных: <code>catalog/components.json</code> и <code>catalog/drawings.json</code>. Все изображения и GLB хранятся в проекте; внешний код просмотра 3D загружается только по явному нажатию.</footer>
<script>
const tabs=[...document.querySelectorAll('[role="tab"]')];for(const tab of tabs)tab.addEventListener('click',()=>{for(const button of tabs){const selected=button===tab;button.setAttribute('aria-selected',selected);document.getElementById(button.getAttribute('aria-controls')).hidden=!selected;}});
const input=document.getElementById('search'),category=document.getElementById('category'),incompleteOnly=document.getElementById('incompleteOnly'),table=document.getElementById('catalogTable'),resultCount=document.getElementById('resultCount'),noResults=document.getElementById('noResults');
function applyFilters(){const query=input.value.trim().toLowerCase(),selectedCategory=category.value;let visible=0;for(const row of table.querySelectorAll('.component-row')){row.hidden=!(row.dataset.search.includes(query)&&(!selectedCategory||row.dataset.category===selectedCategory)&&(!incompleteOnly.checked||row.dataset.incomplete==='true'));if(!row.hidden)visible++;}for(const heading of table.querySelectorAll('.category-row'))heading.hidden=![...table.querySelectorAll('.component-row')].some(row=>!row.hidden&&row.dataset.category===heading.dataset.categoryHeading);resultCount.value='Показано: '+visible;noResults.style.display=visible?'none':'block';}
input.addEventListener('input',applyFilters);category.addEventListener('change',applyFilters);incompleteOnly.addEventListener('change',applyFilters);for(const button of document.querySelectorAll('.copy-id'))button.addEventListener('click',async()=>{await navigator.clipboard.writeText(button.dataset.id);const old=button.textContent;button.textContent='скопировано';setTimeout(()=>button.textContent=old,1200);});applyFilters();
let viewerRuntime;function loadViewerRuntime(){if(!viewerRuntime)viewerRuntime=new Promise((resolve,reject)=>{const script=document.createElement('script');script.type='module';script.src='https://ajax.googleapis.com/ajax/libs/model-viewer/4.2.0/model-viewer.min.js';script.onload=resolve;script.onerror=reject;document.head.append(script);});return viewerRuntime;}
for(const button of document.querySelectorAll('.load-model'))button.addEventListener('click',async()=>{const card=button.closest('.model-card'),viewer=card.querySelector('[data-model]'),status=card.querySelector('.model-status');button.disabled=true;status.textContent='Загружается модуль просмотра…';try{await loadViewerRuntime();status.textContent='Загружается GLB '+card.querySelector('.eyebrow').textContent.split('·')[1].trim()+'…';viewer.src=viewer.dataset.src;viewer.addEventListener('load',()=>{status.textContent='Готово: модель можно вращать мышью или пальцем.';button.hidden=true;},{once:true});viewer.addEventListener('error',()=>{status.textContent='Не удалось загрузить GLB. Запустите локальный HTTP-сервер или скачайте файл по ссылке.';button.disabled=false;},{once:true});}catch{status.textContent='Не удалось загрузить модуль просмотра. Проверьте интернет или скачайте GLB.';button.disabled=false;}});
</script></body></html>`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf8') : '';
  if (current !== html) { console.error('catalog/catalog.html не соответствует JSON-источникам. Запустите npm run catalog:generate.'); process.exitCode = 1; }
  else console.log('Каталог компонентов, чертежей и 3D синхронизирован.');
} else {
  fs.writeFileSync(htmlPath, html, 'utf8');
  console.log(`Generated ${htmlPath}`);
}
