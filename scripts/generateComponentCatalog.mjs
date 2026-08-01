import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = process.cwd();
const componentPath = path.join(root, 'catalog', 'components.json');
const drawingsPath = path.join(root, 'catalog', 'drawings.json');
const identityPath = path.join(root, 'project_identity.json');
const imageDirectory = path.join(root, 'catalog', 'images');
const htmlPath = path.join(root, 'catalog', 'catalog.html');

const escape = value => String(value)
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;')
  .replaceAll("'", '&#39;');

function validateAsset(value, place, failures) {
  if (!value?.trim() || path.isAbsolute(value) || value.split(/[\\/]/).includes('..')) {
    failures.push(`${place} должен быть безопасным путём относительно корня проекта`);
  } else if (!fs.existsSync(path.join(root, value))) {
    failures.push(`${place} не найден: ${value}`);
  }
}

function validate(source, media, identity) {
  const failures = [];
  const ids = new Set();
  const categoryIds = new Set();

  if (identity.schemaVersion !== 1) failures.push('schemaVersion project_identity.json должен быть равен 1');
  for (const key of ['projectDisplayName', 'bluetoothDeviceName']) {
    if (typeof identity[key] !== 'string' || !identity[key].trim()) failures.push(`${key} должен быть непустой строкой`);
  }

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

  if (media.schemaVersion !== 1) failures.push('schemaVersion drawings.json должен быть равен 1');
  for (const group of ['drawings', 'models']) {
    if (!Array.isArray(media[group])) failures.push(`${group} должен быть массивом`);
    for (const [index, item] of (media[group] ?? []).entries()) {
      const place = `${group}[${index}]`;
      if (!/^\d{3}$/.test(item.id ?? '')) failures.push(`${place}.id должен состоять ровно из трёх цифр`);
      if (ids.has(item.id)) failures.push(`повтор ID: ${item.id}`);
      ids.add(item.id);
      if (!item.title?.trim() || !item.description?.trim()) failures.push(`${place} требует title и description`);
      validateAsset(item.file, `${place}.file`, failures);
      validateAsset(group === 'drawings' ? item.preview : item.poster, `${place}.${group === 'drawings' ? 'preview' : 'poster'}`, failures);
    }
  }
  return failures;
}

const source = JSON.parse(fs.readFileSync(componentPath, 'utf8'));
const media = JSON.parse(fs.readFileSync(drawingsPath, 'utf8'));
const identity = JSON.parse(fs.readFileSync(identityPath, 'utf8'));
const failures = validate(source, media, identity);
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
const projectName = identity.projectDisplayName;

function renderLinks(links) {
  if (!links.length) return '<span class="empty">Ссылка пока не подтверждена</span>';
  return `<ul class="links">${links.map(link => `<li><a href="${escape(link.url)}" target="_blank" rel="noopener noreferrer">${escape(link.label)}</a></li>`).join('')}</ul>`;
}

function renderSpecifications(specifications = []) {
  return specifications.length
    ? `<dl class="specifications">${specifications.map(spec => `<div><dt>${escape(spec.label)}</dt><dd>${escape(spec.value)}</dd></div>`).join('')}</dl>`
    : '';
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
    ? `<tr class="category-row" data-category-heading="${escape(item.category)}"><th colspan="5">${escape(categoryLabels.get(item.category))}</th></tr>`
    : '';
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

const drawings = media.drawings.map(item => `<article class="media-card">
  <a href="${escape(repoUrl(item.file))}" target="_blank" rel="noopener"><img src="${escape(repoUrl(item.preview))}" alt="${escape(item.title)}" loading="lazy"></a>
  <div><span class="eyebrow">${escape(item.category)} · ${escape(item.id)}</span><h3>${escape(item.title)}</h3><p>${escape(item.description)}</p><a class="action" href="${escape(repoUrl(item.file))}" target="_blank" rel="noopener">Открыть изображение</a></div>
</article>`).join('');

const models = media.models.map(item => `<article class="model-card" data-title="${escape(item.title)}">
  <div class="viewer-shell">
    <model-viewer data-model data-src="${escape(repoUrl(item.file))}" poster="${escape(repoUrl(item.poster))}" camera-controls auto-rotate shadow-intensity="1" alt="${escape(item.title)}"></model-viewer>
    <button class="model-fullscreen" type="button" aria-label="Открыть модель на весь экран">На весь экран</button>
  </div>
  <div><span class="eyebrow">${escape(item.id)} · ${fileSize(item.file)}</span><h3>${escape(item.title)}</h3><p>${escape(item.description)}</p>
  <div class="model-actions"><button class="load-model" type="button">Загрузить интерактивную 3D-модель</button><a class="action" href="${escape(repoUrl(item.file))}" download>Скачать GLB</a></div>
  <p class="model-status" aria-live="polite">Модель не загружена; изображение-постер сохранено.</p></div>
</article>`).join('');

const categoryOptions = source.categories.map(category => `<option value="${escape(category.id)}">${escape(category.label)}</option>`).join('');

const html = `<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${escape(projectName)} — компоненты, чертежи и 3D</title>
<style>
:root{color-scheme:light dark;--bg:#edf1f3;--panel:#fff;--ink:#172126;--muted:#607078;--line:#d3dde1;--accent:#067a78;--warn:#9b4d00;--warn-bg:#fff0d9}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}body.modal-open{overflow:hidden}header{padding:clamp(24px,5vw,56px);color:#fff;background:linear-gradient(125deg,#15373d,#087d78)}header h1{margin:0 0 8px;font-size:clamp(28px,5vw,48px);line-height:1.1}header p{max-width:900px;margin:0;color:#daf4f1}main{max-width:1500px;margin:auto;padding:24px}.summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-top:-48px;margin-bottom:20px}.metric{padding:16px 18px;border:1px solid var(--line);border-radius:14px;background:var(--panel);box-shadow:0 8px 30px #102d3320}.metric strong{display:block;font-size:28px;color:var(--accent)}.tabs{display:flex;gap:8px;margin:0 0 16px}.tab{padding:11px 18px;border:1px solid var(--line);border-radius:10px;background:var(--panel);color:var(--ink);font:inherit;font-weight:700;cursor:pointer}.tab[aria-selected="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.tab-panel[hidden]{display:none}.controls{display:flex;flex-wrap:wrap;align-items:end;gap:12px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.search{flex:1 1 330px}label span{display:block;margin-bottom:5px;font-weight:650}input[type="search"],select{width:100%;padding:11px 13px;border:1px solid var(--line);border-radius:9px;background:var(--panel);color:var(--ink);font:inherit}.category-filter{min-width:220px}.toggle{display:flex;align-items:center;gap:8px;padding:10px 4px}.toggle span{margin:0}.result-count{color:var(--muted);padding:10px 2px}.table-wrap{overflow:auto;margin-top:16px;border:1px solid var(--line);border-radius:14px;background:var(--panel)}table{width:100%;min-width:1080px;border-collapse:collapse}th,td{padding:14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}thead th{position:sticky;top:0;z-index:2;background:#e4eeef;color:#27464c;font-size:13px;text-transform:uppercase;letter-spacing:.035em}.category-row th{background:#d8eeeb;color:#075b58;font-size:17px}.component-row:hover{background:#f3faf9}.id-cell code{display:block;font-weight:700;color:var(--accent)}.copy-id{margin-top:8px;padding:3px 7px;border:1px solid var(--line);border-radius:6px;background:transparent;color:var(--muted);cursor:pointer}.thumb{width:180px;height:140px;object-fit:contain;display:block;border:1px solid var(--line);border-radius:9px;background:#fff}.badge{display:inline-block;margin-top:8px;padding:3px 8px;border-radius:999px;font-size:12px;font-weight:700}.warning{color:var(--warn);background:var(--warn-bg)}.ok{color:#126534;background:#dff4e7}.info{color:#075985;background:#e0f2fe}.aliases,.links{margin:8px 0 0;padding-left:18px}.specifications{display:grid;gap:6px;margin:12px 0 0}.specifications div{display:grid;grid-template-columns:minmax(95px,auto) 1fr;gap:8px;padding-top:6px;border-top:1px solid var(--line)}.specifications dt{font-weight:700;color:var(--muted)}.specifications dd{margin:0}.needed{margin-top:10px;padding:10px;border-left:4px solid #db7b16;background:var(--warn-bg);color:#633500}.empty,.model-status{color:var(--muted)}.no-results{display:none;padding:30px;text-align:center;color:var(--muted)}.section-intro{margin:0 0 18px}.media-grid,.model-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}.media-card,.model-card{overflow:hidden;border:1px solid var(--line);border-radius:14px;background:var(--panel)}.media-card img,model-viewer{display:block;width:100%;height:320px;object-fit:contain;background:#f8fafb}.media-card>div,.model-card>div:not(.viewer-shell){padding:16px}.media-card h3,.model-card h3{margin:4px 0}.eyebrow{color:var(--accent);font-size:12px;font-weight:800;text-transform:uppercase}.action{display:inline-block;color:var(--accent);font-weight:700}.models-heading{margin-top:32px}.model-actions{display:flex;flex-wrap:wrap;align-items:center;gap:12px}.load-model,.model-fullscreen{padding:9px 12px;border:0;border-radius:8px;background:var(--accent);color:#fff;font:inherit;font-weight:700;cursor:pointer}.load-model:disabled{opacity:.65;cursor:wait}.viewer-shell{position:relative}.model-fullscreen{position:absolute;right:12px;bottom:12px;box-shadow:0 2px 12px #0005}.fullscreen-overlay{position:fixed;inset:0;z-index:1000;display:grid;grid-template-rows:auto 1fr;background:#071013f5;color:#fff}.fullscreen-overlay[hidden]{display:none}.fullscreen-bar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 16px;background:#101d21}.fullscreen-bar h2{margin:0;font-size:18px}.fullscreen-close{width:46px;height:46px;border:0;border-radius:50%;background:#fff;color:#111;font-size:32px;line-height:1;cursor:pointer}.fullscreen-stage{min-height:0}.fullscreen-stage model-viewer{width:100%;height:100%;background:#0b1519}.fullscreen-hint{padding:8px 16px;margin:0;background:#101d21;color:#cfe2e5}footer{max-width:1500px;margin:auto;padding:0 24px 30px;color:var(--muted)}@media(prefers-color-scheme:dark){:root{--bg:#0d171a;--panel:#152227;--ink:#edf6f5;--muted:#a5b5ba;--line:#34464c;--accent:#5ed5cd;--warn:#ffbd78;--warn-bg:#3b2b1b}thead th{background:#20343a;color:#c9e7e5}.category-row th{background:#193936;color:#aeece7}.component-row:hover{background:#193136}.needed{color:#ffd6a6}.thumb,.media-card img,model-viewer{background:#f8f8f8}a{color:#70c9ff}}@media(max-width:700px){main{padding:16px}.summary{margin-top:-32px}.copy-id{display:none}.media-card img,model-viewer{height:240px}.model-fullscreen{font-size:13px}}
.gallery{display:grid;gap:8px}.gallery figure{margin:0}.gallery figcaption{margin-top:3px;max-width:180px;color:var(--muted);font-size:11px}
</style></head><body>
<header><h1>Проект ${escape(projectName)}</h1><p>Каталог компонентов, исходные изображения, чертежи и интерактивный просмотр 3D-моделей. Имя проекта задаётся один раз в <code>project_identity.json</code>.</p></header>
<main><section class="summary" aria-label="Сводка"><div class="metric"><strong>${components.length}</strong>компонентов</div><div class="metric"><strong>${source.categories.length}</strong>категорий</div><div class="metric"><strong>${media.drawings.length}</strong>изображений и чертежей</div><div class="metric"><strong>${media.models.length}</strong>3D-моделей</div><div class="metric"><strong>${incompleteCount}</strong>нужно уточнить</div></section>
<nav class="tabs" role="tablist" aria-label="Разделы проекта"><button class="tab" role="tab" id="components-tab" aria-controls="components-panel" aria-selected="true">Компоненты</button><button class="tab" role="tab" id="drawings-tab" aria-controls="drawings-panel" aria-selected="false">Чертежи и 3D</button></nav>
<section id="components-panel" class="tab-panel" role="tabpanel" aria-labelledby="components-tab"><section class="controls" aria-label="Фильтры"><label class="search"><span>Поиск по ID, названию и назначению</span><input id="search" type="search" placeholder="например: 009, 6804, датчик"></label><label class="category-filter"><span>Категория</span><select id="category"><option value="">Все категории</option>${categoryOptions}</select></label><label class="toggle"><input id="incompleteOnly" type="checkbox"><span>Только позиции, которые нужно уточнить</span></label><output id="resultCount" class="result-count"></output></section>
<div class="table-wrap"><table id="catalogTable"><thead><tr><th>ID</th><th>Картинка</th><th>Возможные названия компонента</th><th>Зачем он нужен</th><th>Описание или покупка</th></tr></thead><tbody>${rows}</tbody></table><p id="noResults" class="no-results">По заданному фильтру ничего не найдено.</p></div></section>
<section id="drawings-panel" class="tab-panel" role="tabpanel" aria-labelledby="drawings-tab" hidden><p class="section-intro">Оригинальные картинки остаются отдельными карточками. Ниже для выбранных видов добавлены интерактивные GLB.</p><div class="media-grid">${drawings}</div><h2 class="models-heading">Интерактивные 3D-модели</h2><p class="section-intro">GLB и модуль просмотра загружаются только после нажатия. Кнопка «На весь экран» открывает модель в отдельном полноэкранном слое; закрыть его можно крестиком или клавишей Escape.</p><div class="model-grid">${models}</div></section></main>
<footer>Источники данных: <code>catalog/components.json</code>, <code>catalog/drawings.json</code> и <code>project_identity.json</code>. Сгенерированный HTML вручную не редактировать.</footer>
<div id="fullscreenOverlay" class="fullscreen-overlay" hidden role="dialog" aria-modal="true" aria-labelledby="fullscreenTitle"><div class="fullscreen-bar"><h2 id="fullscreenTitle">3D-модель</h2><button id="fullscreenClose" class="fullscreen-close" type="button" aria-label="Закрыть полноэкранный режим">×</button></div><div class="fullscreen-stage"><model-viewer id="fullscreenViewer" camera-controls auto-rotate shadow-intensity="1"></model-viewer></div><p class="fullscreen-hint">Вращайте мышью или пальцем. Закрыть: × или Escape.</p></div>
<script>
const tabs=[...document.querySelectorAll('[role="tab"]')];for(const tab of tabs)tab.addEventListener('click',()=>{for(const button of tabs){const selected=button===tab;button.setAttribute('aria-selected',String(selected));document.getElementById(button.getAttribute('aria-controls')).hidden=!selected;}});
const input=document.getElementById('search'),category=document.getElementById('category'),incompleteOnly=document.getElementById('incompleteOnly'),table=document.getElementById('catalogTable'),resultCount=document.getElementById('resultCount'),noResults=document.getElementById('noResults');
function applyFilters(){const query=input.value.trim().toLowerCase(),selectedCategory=category.value;let visible=0;for(const row of table.querySelectorAll('.component-row')){row.hidden=!(row.dataset.search.includes(query)&&(!selectedCategory||row.dataset.category===selectedCategory)&&(!incompleteOnly.checked||row.dataset.incomplete==='true'));if(!row.hidden)visible++;}for(const heading of table.querySelectorAll('.category-row'))heading.hidden=![...table.querySelectorAll('.component-row')].some(row=>!row.hidden&&row.dataset.category===heading.dataset.categoryHeading);resultCount.value='Показано: '+visible;noResults.style.display=visible?'none':'block';}
input.addEventListener('input',applyFilters);category.addEventListener('change',applyFilters);incompleteOnly.addEventListener('change',applyFilters);for(const button of document.querySelectorAll('.copy-id'))button.addEventListener('click',async()=>{await navigator.clipboard.writeText(button.dataset.id);const old=button.textContent;button.textContent='скопировано';setTimeout(()=>button.textContent=old,1200);});applyFilters();
let viewerRuntime;function loadViewerRuntime(){if(!viewerRuntime)viewerRuntime=new Promise((resolve,reject)=>{const script=document.createElement('script');script.type='module';script.src='https://ajax.googleapis.com/ajax/libs/model-viewer/4.2.0/model-viewer.min.js';script.onload=resolve;script.onerror=reject;document.head.append(script);});return viewerRuntime;}
async function ensureModel(card){const viewer=card.querySelector('[data-model]'),status=card.querySelector('.model-status'),button=card.querySelector('.load-model');if(viewer.src)return viewer;button.disabled=true;status.textContent='Загружается модуль просмотра…';await loadViewerRuntime();status.textContent='Загружается GLB…';viewer.src=viewer.dataset.src;await new Promise((resolve,reject)=>{viewer.addEventListener('load',resolve,{once:true});viewer.addEventListener('error',reject,{once:true});});status.textContent='Готово: модель можно вращать мышью или пальцем.';button.hidden=true;return viewer;}
for(const button of document.querySelectorAll('.load-model'))button.addEventListener('click',async()=>{const card=button.closest('.model-card');try{await ensureModel(card);}catch{card.querySelector('.model-status').textContent='Не удалось загрузить модель. Запустите локальный HTTP-сервер или скачайте GLB.';button.disabled=false;}});
const overlay=document.getElementById('fullscreenOverlay'),fullscreenViewer=document.getElementById('fullscreenViewer'),fullscreenTitle=document.getElementById('fullscreenTitle'),fullscreenClose=document.getElementById('fullscreenClose');
async function openFullscreen(card){try{const viewer=await ensureModel(card);await loadViewerRuntime();fullscreenTitle.textContent=card.dataset.title;fullscreenViewer.poster=viewer.poster;fullscreenViewer.src=viewer.src;overlay.hidden=false;document.body.classList.add('modal-open');if(overlay.requestFullscreen){try{await overlay.requestFullscreen();}catch{}}fullscreenClose.focus();}catch{card.querySelector('.model-status').textContent='Полноэкранный режим недоступен: модель не загрузилась.';}}
async function closeFullscreen(){if(document.fullscreenElement){try{await document.exitFullscreen();}catch{}}overlay.hidden=true;document.body.classList.remove('modal-open');fullscreenViewer.removeAttribute('src');}
for(const button of document.querySelectorAll('.model-fullscreen'))button.addEventListener('click',()=>openFullscreen(button.closest('.model-card')));fullscreenClose.addEventListener('click',closeFullscreen);document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!overlay.hidden)closeFullscreen();});document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&!overlay.hidden){overlay.hidden=true;document.body.classList.remove('modal-open');fullscreenViewer.removeAttribute('src');}});
</script></body></html>`;

if (process.argv.includes('--check')) {
  const current = fs.existsSync(htmlPath) ? fs.readFileSync(htmlPath, 'utf8') : '';
  if (current !== html) {
    console.error('catalog/catalog.html не соответствует JSON-источникам. Запустите npm run catalog:generate.');
    process.exit(1);
  }
  console.log('Каталог компонентов, картинок и интерактивных 3D-моделей синхронизирован.');
} else {
  fs.writeFileSync(htmlPath, html, 'utf8');
  console.log(`Generated ${htmlPath}`);
}
