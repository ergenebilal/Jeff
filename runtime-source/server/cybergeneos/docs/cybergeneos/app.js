'use strict';
/* CybergeneOS panel. Lists come from /api/state; full lead reports load when opened. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const safeUrl = u => /^https?:\/\//i.test(u || '') ? u : '';

const LAYERS = {
  lead: {label: 'Leadler', color: '#C6A1F2'},
  opp:  {label: 'Fırsatlar', color: '#53C6D0'}
};
const SRC_ICON = {'GitHub': 'ph-github-logo', 'Hugging Face': 'ph-smiley', 'Hacker News': 'ph-code', 'Product Hunt': 'ph-rocket-launch', 'Google Haberler': 'ph-globe-hemisphere-east',
  'Telegram': 'ph-telegram-logo', 'Elle eklenen': 'ph-push-pin', 'Jeff ekledi': 'ph-sparkle', 'OpenStreetMap taraması': 'ph-map-trifold', 'Google Haritalar taraması': 'ph-map-trifold', 'OpenAI': 'ph-open-ai-logo'};
const CHANNELS = ['WhatsApp', 'E-posta', 'LinkedIn (elle)', 'Telefon (siz arayın)'];

let D = {opps: [], news: [], leads: [], approvals: [], sources: [], jobs: [], sections: [], districts: {}, digest: '', idea: '', topics: [], briefing: {text: ''}, radar: {}, stages: [], cities: {}, voice: false, voices: []};
let CITY = {};
const state = {layers: {lead: true, opp: true}, opp: null, oppStatus: 'acik', oppTag: 'all', oppSrc: 'all', focusJob: null, focusStub: null, newsTag: 'all', radarJob: null,
  leadSec: 'sira', leadSecSet: false, leadJob: null, city: 'all', q: '', loaded: false, error: false};

/* ---------- small helpers ---------- */
let toastT;
function toast(msg){ const t = $('#toast'); t.textContent = msg; t.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => t.hidden = true, 4200); }
function ago(ts){
  const s = Math.max(0, Math.round(Date.now() / 1000 - ts));
  if (s < 90) return 'az önce';
  if (s < 3600) return Math.round(s / 60) + ' dk önce';
  if (s < 86400) return Math.round(s / 3600) + ' saat önce';
  if (s < 172800) return 'dün';
  return Math.round(s / 86400) + ' gün önce';
}
const fmtDate = ts => new Date(ts * 1000).toLocaleString('tr-TR', {day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'});
const fmtDay = ts => new Date(ts * 1000).toLocaleDateString('tr-TR', {day: 'numeric', month: 'long'});
function strClass(s){ return s === 'Güçlü' ? 'strong' : s === 'Orta' ? 'mid' : 'weak'; }
const icon = s => SRC_ICON[s] || (/^Hacker News/.test(s) ? 'ph-code' : 'ph-rss');

async function api(path, body){
  const r = await fetch('/api/' + path, body === undefined ? {} : {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
  if (r.status === 401) { location.href = '/login'; throw new Error('giris'); }
  let d = null;
  try { d = await r.json(); } catch (e) {}
  if (!r.ok) { const err = new Error(d?.error || 'hata'); err.code = r.status; err.detail = d?.detail; throw err; }
  return d;
}
const ERRORS = {zaten_calisiyor: 'Bu tarama zaten sürüyor.', anahtar_yok: 'Jeff\'in anahtarı tanımlı değil.', cok_sik: 'Çok sık istek, biraz bekleyin.', jeff_ulasilamadi: 'Jeff\'e şu an ulaşılamadı.', kisa: 'Metin biraz daha uzun olmalı.', var: 'Bu kayıt zaten var.'};
async function act(path, body, okMsg){
  try { const d = await api(path, body || {}); if (okMsg) toast(okMsg); await refresh(); return d; }
  catch (e) { toast(ERRORS[e.message] || 'İşlem tamamlanamadı, tekrar deneyin.'); return null; }
}

/* ---------- data ---------- */
async function refresh(){
  try {
    const fresh = await api('state');
    // An open sheet owns its full detail; list refreshes must not erase it.
    fresh.leads = fresh.leads.map(row => {
      // Keep the open sheet's note until its user action finishes.
      return row;
    });
    D = fresh;
    leadSearchData = null;
    if (state.q) await loadLeadSearch();
    CITY = D.cities || {};
    if (!knownJobs) knownJobs = new Set(D.jobs.map(j => j.id));
    state.loaded = true; state.error = false;
  } catch (e) { if (e.message === 'giris') return; state.error = true; }
  renderAll();
}

/* ---------- router ---------- */
const VIEWS = ['komuta', 'radar', 'firsatlar', 'leadler', 'haberler'];
function go(v){
  if (!VIEWS.includes(v)) v = 'komuta';
  $$('.view').forEach(s => s.hidden = s.dataset.view !== v);
  $$('.tab').forEach(t => t.dataset.go === v ? t.setAttribute('aria-current', 'page') : t.removeAttribute('aria-current'));
  if (location.hash.slice(1) !== v) history.replaceState(null, '', '#' + v);
  if (v === 'komuta') requestAnimationFrame(drawMap);
  window.scrollTo({top: 0});
}
window.addEventListener('hashchange', () => go(location.hash.slice(1)));
document.addEventListener('click', e => {
  const t = e.target.closest('[data-toast]'); if (t) toast(t.dataset.toast);
  const g = e.target.closest('[data-go]'); if (g) go(g.dataset.go);
  const o = e.target.closest('[data-open="appr"]'); if (o) openApprovals();
  const s = e.target.closest('[data-say]'); if (s) { go('komuta'); ask(s.dataset.say); }
  const lb = e.target.closest('[data-lead]'); if (lb) openLead(lb.dataset.lead);
});
document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target.matches('tr[data-lead]')) openLead(e.target.dataset.lead); });

/* ---------- derived ---------- */
const oppOpen = o => o.status === 'Yeni' || o.status === 'Takipte';
const openOpps = () => D.opps.filter(oppOpen);
const newsItems = () => D.news;
function greeting(){ const h = new Date().getHours(); return h < 12 ? 'Günaydın' : h < 18 ? 'İyi günler' : 'İyi akşamlar'; }

function renderAll(){
  counts(); renderBanner(); renderLayers(); drawMap(); renderFocus(); renderRadar(); renderOpps(); renderLeadFilters(); renderLeads(); renderNews(); renderRadarLine();
  if (!jeffIntroShown && state.loaded) initJeff();
}

function counts(){
  $('#voice-pick').hidden = !D.voice;
  $('#sys').lastChild.textContent = state.error ? 'Sunucu yok' : D.jeff === undefined ? 'Jeff durumu yükleniyor' : D.jeff === 'hermes' ? 'Jeff bağlantısı ayarlı' : D.jeff === 'yedek' ? 'Yedek Jeff' : 'Jeff kapalı';
  $('#sys').classList.toggle('off', state.error || D.jeff !== 'hermes');
  $('#sys').title = D.jarvis?.work?.known && D.jarvis?.approvals?.known ? `${D.jarvis.work.open} açık iş; ${D.jarvis.approvals.pending} güncel onay` : 'Görev ve onay durumu okunamadı';
  $('#n-opp').textContent = openOpps().length;
  const mine = D.leads.filter(l => nextStep(l).list === 'sira').length;
  $('#n-lead').textContent = mine;
  $('#n-lead').hidden = !mine;
  $('#n-lead').title = 'Sizden bir adım bekleyen işletme';
  const open = D.approvals.filter(a => a.status === 'Bekliyor').length;
  $('#n-appr').textContent = open; $('#n-appr').hidden = !open;
  $('#today').textContent = new Date().toLocaleDateString('tr-TR', {day: 'numeric', month: 'long', year: 'numeric', weekday: 'long'});
  const fresh = openOpps().filter(o => o.status === 'Yeni').length;
  $('#h-komuta').innerHTML = !state.loaded ? `${greeting()} Bilal.`
    : mine ? `${greeting()} Bilal. <em class="grad">${mine} işletme</em> sizi bekliyor.`
    : fresh ? `${greeting()} Bilal. Bugün <em class="grad">${fresh} yeni fırsat</em> var.`
    : `${greeting()} Bilal. Bugün sizi bekleyen bir iş yok.`;
  const b = $('#data-badge');
  b.textContent = state.error ? 'Bağlantı yok' : !D.radar.last_run ? 'Henüz tarama yok' : 'Canlı veri, ' + ago(D.radar.last_run);
  b.classList.toggle('bad', state.error);
}
function renderBanner(){
  $('#banner').hidden = !state.error;
  $('#banner').innerHTML = state.error ? '<i class="ph ph-warning-circle" aria-hidden="true"></i> Sunucuya ulaşılamıyor. Gösterilen bilgiler eski olabilir. <button class="btn btn-text btn-sm" type="button" id="retry">Tekrar dene</button>' : '';
  if (state.error) $('#retry').onclick = refresh;
}

/* ---------- map ---------- */
let geo = null, geoFailed = false;
const NEIGH = ['300','100','268','051','364','368','760','196','031','642','804','643'];
function cityItems(){
  const by = {};
  const add = (city, layer, item) => { if (!city || !CITY[city]) return; (by[city] ||= {lead: [], opp: []})[layer].push(item); };
  D.leads.filter(l => l.section !== 'kapandi').forEach(l => add(l.city, 'lead', {t: l.name, s: l.section === 'yeni' ? 'Yeni bulundu' : l.stage, go: () => openLead(l.id), fresh: l.section === 'yeni' || l.due, located: !!(l.lat && l.lon)}));
  openOpps().forEach(o => add(o.city, 'opp', {t: o.title, s: o.src + ', ' + ago(o.ts), go: () => { state.opp = o.id; go('firsatlar'); renderOpps(); }, fresh: o.fresh}));
  return by;
}
function renderLayers(){
  const by = cityItems();
  const tot = {lead: 0, opp: 0};
  Object.values(by).forEach(c => { for (const k in tot) tot[k] += c[k].length; });
  $('#layers').innerHTML = Object.entries(LAYERS).map(([k, L]) =>
    `<button class="layer" type="button" style="--c:${L.color}" aria-pressed="${state.layers[k]}" data-layer="${k}"><i class="dot" aria-hidden="true"></i>${L.label} <span class="n">${tot[k]}</span></button>`).join('');
  $('#legend').innerHTML = Object.values(LAYERS).map(L => `<span style="--c:${L.color}"><i aria-hidden="true"></i>${L.label}</span>`).join('') + '<span><i style="--c:transparent;box-shadow:inset 0 0 0 1.5px #F2F2F5" aria-hidden="true"></i>Halka: yeni</span><span style="--c:#53C6D0"><i aria-hidden="true"></i>Dalga: tarama sürüyor</span>';
  const act = activeJobs();
  $('#unlocated').innerHTML = act.length ? `<i class="ph ph-crosshair" aria-hidden="true"></i>${esc(act[0].title)}, %${act[0].progress} <i class="ph ph-arrow-right" aria-hidden="true"></i>`
    : `<i class="ph ph-storefront" aria-hidden="true"></i>Bir şehirde işletme tara <i class="ph ph-arrow-right" aria-hidden="true"></i>`;
  $('#unlocated').onclick = () => act.length ? go('radar') : openScan();
  const none = !Object.keys(by).length;
  $('#map-empty').hidden = !none;
  $('#map-empty').hidden = !none || scanCities().length > 0;
  $('#map-empty').textContent = !state.loaded ? 'Yükleniyor' : 'Haritada henüz işletme yok. Bir şehirde işletme taraması başlatınca bulunanlar burada görünür.';
}
$('#layers').addEventListener('click', e => {
  const b = e.target.closest('[data-layer]'); if (!b) return;
  state.layers[b.dataset.layer] = !state.layers[b.dataset.layer];
  renderLayers(); drawMap();
});

async function loadGeo(){
  try {
    const topo = await fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-50m.json').then(r => { if (!r.ok) throw new Error(); return r.json(); });
    const all = topojson.feature(topo, topo.objects.countries).features;
    geo = {tr: all.find(f => f.id === '792'), nb: {type: 'FeatureCollection', features: all.filter(f => NEIGH.includes(f.id))}};
    drawMap();
  } catch (e) { geoFailed = true; mapFallback(); }
}
function mapFallback(){
  if (mapMode === 'google') return;
  const f = $('#map-fallback'); f.hidden = false;
  const by = cityItems();
  f.innerHTML = `<div><h3 style="font-size:18px;margin-bottom:8px">Harita şu an çizilemedi</h3><p style="margin:0 0 14px">Şehirlere göre sinyaller yine de burada:</p><div class="row" style="justify-content:center">${Object.keys(by).map(c => `<span class="tag">${esc(c)} ${by[c].lead.length + by[c].opp.length + by[c].news.length}</span>`).join('')}</div></div>`;
}

const CFG = window.CGOS_CONFIG || {};
let mapMode = 'dots', gmap = null, gOverlay = null, gMarkers = [], activeCity = null;
const GSTYLE = [
  {elementType:'geometry', stylers:[{color:'#0b0e16'}]},
  {elementType:'labels.text.fill', stylers:[{color:'#8d90a0'}]},
  {elementType:'labels.text.stroke', stylers:[{color:'#0a0d14'}]},
  {featureType:'administrative.country', elementType:'geometry.stroke', stylers:[{color:'#3a3f55'}]},
  {featureType:'administrative.province', elementType:'geometry.stroke', stylers:[{color:'#1c2130'}]},
  {featureType:'administrative.locality', elementType:'labels', stylers:[{visibility:'off'}]},
  {featureType:'administrative.province', elementType:'labels', stylers:[{visibility:'off'}]},
  {featureType:'landscape.natural', elementType:'geometry', stylers:[{color:'#0d111c'}]},
  {featureType:'poi', stylers:[{visibility:'off'}]},
  {featureType:'road', elementType:'geometry', stylers:[{color:'#151a27'}]},
  {featureType:'road', elementType:'labels', stylers:[{visibility:'off'}]},
  {featureType:'transit', stylers:[{visibility:'off'}]},
  {featureType:'water', elementType:'geometry', stylers:[{color:'#05070c'}]},
  {featureType:'water', elementType:'labels', stylers:[{visibility:'off'}]}
];
function loadGoogle(){
  if (!CFG.googleMapsKey) return;
  window.cgosGoogleReady = initGoogle;
  window.gm_authFailure = () => { toast('Google Haritalar anahtarı kabul edilmedi. Sade haritaya dönüldü.'); $('#map-mode').hidden = true; setMapMode('dots'); };
  const s = document.createElement('script');
  s.src = 'https://maps.googleapis.com/maps/api/js?key=' + encodeURIComponent(CFG.googleMapsKey) + '&callback=cgosGoogleReady&v=weekly&language=tr&region=TR&loading=async';
  s.async = true;
  s.onerror = () => toast('Google Haritalar yüklenemedi. Sade harita gösteriliyor.');
  document.head.append(s);
}
function initGoogle(){
  gmap = new google.maps.Map($('#gmap'), {center: {lat: 39.1, lng: 35.2}, zoom: 6, disableDefaultUI: true, zoomControl: true, gestureHandling: 'greedy', backgroundColor: '#0A0D14', clickableIcons: false, styles: GSTYLE});
  gOverlay = new google.maps.OverlayView();
  gOverlay.onAdd = gOverlay.draw = gOverlay.onRemove = () => {};
  gOverlay.setMap(gmap);
  gmap.addListener('dragstart', () => { closeCityCard(); if (state.focusJob) focusCam.moved = true; });
  gmap.addListener('zoom_changed', closeCityCard);
  let zoomBucket = gmap.getZoom() >= 10;
  gmap.addListener('idle', () => { const z = gmap.getZoom() >= 10; if (z !== zoomBucket) { zoomBucket = z; drawGoogle(); } });
  $('#map-mode').hidden = false;
  setMapMode('google');
}
function setMapMode(m){
  mapMode = m;
  $('#gmap').toggleAttribute('hidden', m !== 'google');
  $('#map-dots').toggleAttribute('hidden', m === 'google');
  $('#map-nodes').toggleAttribute('hidden', m === 'google');
  if (m === 'google') $('#map-fallback').hidden = true;
  $$('#map-mode button').forEach(b => b.setAttribute('aria-pressed', b.dataset.v === m));
  closeCityCard();
  if (m === 'google' && gmap) { google.maps.event.trigger(gmap, 'resize'); gmap.fitBounds({south: 35.9, west: 26.0, north: 42.1, east: 44.8}, 8); }
  drawMap();
}
$('#map-mode').addEventListener('click', e => { const b = e.target.closest('[data-v]'); if (b && (b.dataset.v === 'dots' || gmap)) setMapMode(b.dataset.v); });
function closeCityCard(){ $$('.city-card').forEach(n => n.remove()); activeCity = null; }
function cityPixel(city){
  const wrap = $('#map-wrap');
  if (mapMode === 'google' && gOverlay?.getProjection()) {
    const p = gOverlay.getProjection().fromLatLngToContainerPixel(new google.maps.LatLng(CITY[city][1], CITY[city][0]));
    return [p.x, p.y];
  }
  return d3.geoMercator().fitExtent([[wrap.clientWidth * .05, wrap.clientHeight * .1], [wrap.clientWidth * .95, wrap.clientHeight * .92]], geo.tr)(CITY[city]);
}
const scanCities = () => [...new Set(activeJobs().filter(j => j.kind === 'lead_scan' && CITY[j.params.city]).map(j => j.params.city))];
const PULSE = 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="-60 -60 120 120"><circle r="10" fill="none" stroke="#53C6D0" stroke-width="2"><animate attributeName="r" from="8" to="56" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" from=".9" to="0" dur="1.8s" repeatCount="indefinite"/></circle><circle r="10" fill="none" stroke="#53C6D0" stroke-width="2"><animate attributeName="r" from="8" to="56" dur="1.8s" begin=".9s" repeatCount="indefinite"/><animate attributeName="opacity" from=".9" to="0" dur="1.8s" begin=".9s" repeatCount="indefinite"/></circle></svg>');
const SEC_COLOR = {yeni: '#C6A1F2', bekleyen: '#A2BCE7', islemde: '#6EDCB6', kapandi: '#8D90A0'};
function partsFor(L){ return Object.keys(LAYERS).filter(k => state.layers[k] && L[k].length).map(k => ({k, n: L[k].length})); }
function markerIcon(parts, fresh){
  const total = d3.sum(parts, d => d.n), r = 7 + Math.sqrt(total) * 2.2, S = Math.ceil((r + 12) * 2), c = S / 2;
  const arc = d3.arc().innerRadius(r - 2.5).outerRadius(r + 1).padAngle(parts.length > 1 ? .08 : 0);
  const rings = d3.pie().sort(null).value(d => d.n)(parts).map(p => `<path d="${arc(p)}" fill="${LAYERS[p.data.k].color}"/>`).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S}" viewBox="${-c} ${-c} ${S} ${S}"><circle r="${r + 10}" fill="${LAYERS[parts[0].k].color}" fill-opacity=".16"/>${fresh ? `<circle r="${r + 5}" fill="none" stroke="#F2F2F5" stroke-opacity=".6"/>` : ''}${rings}<circle r="3.2" fill="#F2F2F5"/></svg>`;
  return {url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg), size: new google.maps.Size(S, S), scaledSize: new google.maps.Size(S, S), anchor: new google.maps.Point(c, c)};
}
function drawGoogle(){
  if (!gmap) return;
  gMarkers.forEach(m => m.setMap(null)); gMarkers = [];
  const wrap = $('#map-wrap'), small = wrap.clientWidth < 560;
  scanCities().forEach(city => gMarkers.push(new google.maps.Marker({map: gmap, position: {lat: CITY[city][1], lng: CITY[city][0]}, clickable: false, zIndex: 1,
    icon: {url: PULSE, size: new google.maps.Size(120, 120), scaledSize: new google.maps.Size(120, 120), anchor: new google.maps.Point(60, 60)}})));
  const focused = focusJob(), pinned = new Set((focused?.found || []).map(p => p.id));
  /* close in, every business with a location gets its own pin */
  const close = gmap.getZoom() >= 10 && state.layers.lead;
  if (close) D.leads.filter(l => l.lat && l.lon && l.section !== 'kapandi' && !pinned.has(l.id)).forEach(l => {
    const m = new google.maps.Marker({map: gmap, position: {lat: +l.lat, lng: +l.lon}, title: `${l.name} (${l.section === 'yeni' ? 'yeni bulundu' : l.stage})`, zIndex: 50,
      icon: {path: google.maps.SymbolPath.CIRCLE, scale: 6, fillColor: SEC_COLOR[l.section] || '#C6A1F2', fillOpacity: .95, strokeColor: '#0A0D14', strokeWeight: 2}});
    m.addListener('click', () => openLead(l.id)); gMarkers.push(m);
  });
  if (focused) return drawFocusPins();
  Object.entries(cityItems()).forEach(([city, L]) => {
    if (close) L = {...L, lead: L.lead.filter(i => !i.located)};
    const parts = partsFor(L), total = d3.sum(parts, d => d.n); if (!total) return;
    const fresh = Object.keys(LAYERS).some(k => state.layers[k] && L[k].some(i => i.fresh));
    /* Classic Marker on purpose: AdvancedMarkerElement needs a Map ID, which turns off the JSON styling above. */
    const m = new google.maps.Marker({map: gmap, position: {lat: CITY[city][1], lng: CITY[city][0]}, icon: markerIcon(parts, fresh), zIndex: total,
      title: `${city}: ${parts.map(p => p.n + ' ' + LAYERS[p.k].label.toLowerCase()).join(', ')}`,
      label: small ? null : {text: `${city} ${total}`, color: activeCity === city ? '#F2F2F5' : '#C3C5CF', fontSize: '13px', fontWeight: '500'}});
    m.addListener('click', () => { const [x, y] = cityPixel(city); openCity(city, x, y, wrap.clientWidth, wrap.clientHeight); });
    gMarkers.push(m);
  });
}

/* ---------- Komuta: a business scan, live on the map ----------
   The moment a scan starts (Bilal's command, Jeff, or the scan form) the map flies to the area, and every business
   found drops in as a numbered pin, in the order the scan found it. The list beside it carries the same numbers. */
let focusMarkers = [], focusSeen = new Set(), focusCam = {n: -1, moved: false}, pinPick = null;
const focusJob = () => state.focusJob ? ((D.jobs || []).find(j => j.id === state.focusJob) || state.focusStub) : null;
const focusPts = j => (j?.found || []).filter(p => p.lat && p.lon);
function startFocus(j){
  if (state.focusJob === j.id) return renderFocus();
  focusMarkers.forEach(m => m.setMap(null)); focusMarkers = [];
  state.focusJob = j.id; state.focusStub = j; focusSeen = new Set(); focusCam = {n: -1, moved: false}; pinPick = null;
  closeCityCard();
  const c = CITY[j.params?.city];
  if (c && gmap && mapMode === 'google') { gmap.panTo({lat: c[1], lng: c[0]}); gmap.setZoom(j.params.district ? 11 : 10); }
  renderFocus(); drawMap();
}
function endFocus(){
  focusMarkers.forEach(m => m.setMap(null)); focusMarkers = [];
  state.focusJob = null; state.focusStub = null;
  $('#scan-card').hidden = true;
  if (gmap && mapMode === 'google') gmap.fitBounds({south: 35.9, west: 26.0, north: 42.1, east: 44.8}, 8);
  drawMap();
}
function renderFocus(){
  const j = focusJob(), card = $('#scan-card');
  if (!j) { card.hidden = true; return; }
  const run = j.status === 'running' || j.status === 'queued', all = j.found || [];
  const list = card.querySelector('.sc-list'), y = list ? list.scrollTop : 0;
  card.hidden = false;
  card.innerHTML = `<div class="sc-head"><span class="sc-radar ${run ? 'on' : ''}" aria-hidden="true"></span>
      <div><p class="kicker">${esc(STARTED[j.by] || STARTED.bilal)}${j.created_at ? ', ' + clock(j.created_at) : ''}</p><h2>${esc(j.title || 'İşletme taraması')}</h2></div>
      <button class="icon-btn" type="button" data-focus-close aria-label="Taramayı haritadan kaldır"><i class="ph ph-x" aria-hidden="true"></i></button></div>
    <div class="bar" role="progressbar" aria-label="İlerleme" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${j.status === 'done' ? 100 : j.progress}"><i style="width:${j.status === 'done' ? 100 : j.progress}%"></i></div>
    <p class="sc-note" aria-live="polite">${esc(run ? (j.note || 'Başlıyor') : jobLine(j))}</p>
    ${all.length ? `<ol class="sc-list">${all.map((p, i) => `<li class="${focusSeen.has(p.id) ? '' : 'new'}"><button type="button" data-pin="${esc(p.id)}" aria-current="${pinPick === p.id}" title="Haritada göster; ikinci tıklamada aç">
        <b style="background:${GATE[p.gate]?.[2] || 'var(--lav)'}" title="${p.gate ? esc(GATE[p.gate][0]) : 'Kapı bekliyor'}">${i + 1}</b><span>${esc(p.name)}</span>${p.phone ? '<i class="ph ph-phone" aria-label="Telefon var"></i>' : '<i></i>'}${p.web ? '<i class="ph ph-globe" aria-label="Web sitesi var"></i>' : '<i></i>'}</button></li>`).join('')}</ol>`
      : `<p class="help" style="margin:0">${run ? 'İşletmeler bulundukça burada ve haritada numaralanır.' : 'Bu taramada işletme bulunmadı.'}</p>`}
    ${!run && all.length ? `<div class="row"><button class="btn btn-glass btn-sm" type="button" data-show-job="${j.id}">Leadlerde gör</button><span class="help" style="margin:0">Bir iğneye tıklayınca işletme açılır.</span></div>` : ''}`;
  const nl = card.querySelector('.sc-list'); if (nl) nl.scrollTop = y;
  drawFocusPins();
}
function drawFocusPins(){
  const j = focusJob();
  if (!j || !gmap || mapMode !== 'google') return;
  const pts = focusPts(j), order = new Map((j.found || []).map((p, i) => [p.id, i + 1]));
  pts.forEach(p => {
    const old = focusMarkers.find(m => m.leadId === p.id);
    if (old && old.gate !== p.gate) { old.gate = p.gate; old.setIcon({...old.getIcon(), fillColor: GATE[p.gate]?.[2] || '#C6A1F2'}); }
    if (focusSeen.has(p.id)) return;
    focusSeen.add(p.id);
    const n = order.get(p.id);
    const m = new google.maps.Marker({map: gmap, position: {lat: +p.lat, lng: +p.lon}, title: `${n}. ${p.name}`, zIndex: 1000 - n, animation: google.maps.Animation.DROP,
      label: {text: String(n), color: '#171020', fontSize: '11px', fontWeight: '700'},
      icon: {path: google.maps.SymbolPath.CIRCLE, scale: 11, fillColor: GATE[p.gate]?.[2] || '#C6A1F2', fillOpacity: 1, strokeColor: '#0A0D14', strokeWeight: 2}});
    m.leadId = p.id; m.gate = p.gate;
    m.addListener('click', () => openLead(p.id));
    focusMarkers.push(m);
  });
  if (!focusCam.moved && pts.length && pts.length !== focusCam.n) {
    focusCam.n = pts.length;
    if (pts.length === 1) { gmap.panTo({lat: +pts[0].lat, lng: +pts[0].lon}); gmap.setZoom(14); return; }
    const b = new google.maps.LatLngBounds(); pts.forEach(p => b.extend({lat: +p.lat, lng: +p.lon}));
    const wide = $('#map-wrap').clientWidth > 720;
    gmap.fitBounds(b, {top: 50, bottom: 40, right: 40, left: wide ? 370 : 30});
  }
}
function onScanEvent(ev){
  const where = (ev.district ? ev.district + ', ' : '') + ev.city;
  knownJobs?.add(ev.id);  // no "Jeff started a scan" toast: the map already shows it
  if (location.hash.slice(1) !== 'komuta') go('komuta');
  startFocus({id: ev.id, kind: 'lead_scan', by: 'jeff', status: 'queued', progress: 0, note: 'Tarama başladı, kaynağa soruluyor', title: `${ev.niche} taraması: ${where}`,
    params: {city: ev.city, district: ev.district}, found: [], log: [], created_at: Math.floor(Date.now() / 1000)});
  pollJobs();
}
$('#scan-card').addEventListener('click', e => {
  if (e.target.closest('[data-focus-close]')) return endFocus();
  const b = e.target.closest('[data-pin]'); if (!b) return;
  const id = b.dataset.pin;
  if (pinPick === id) return openLead(id);
  pinPick = id;
  $$('#scan-card [data-pin]').forEach(x => x.setAttribute('aria-current', x.dataset.pin === id));
  const m = focusMarkers.find(x => x.leadId === id);
  if (m && gmap) { focusCam.moved = true; gmap.panTo(m.getPosition()); if (gmap.getZoom() < 14) gmap.setZoom(14); m.setAnimation(google.maps.Animation.BOUNCE); setTimeout(() => m.setAnimation(null), 1400); }
  else if (mapMode !== 'google') drawMap();
});

function drawMap(){
  if (mapMode === 'google') return drawGoogle();
  const wrap = $('#map-wrap'); if (!geo || wrap.offsetParent === null) return;
  const w = wrap.clientWidth, h = wrap.clientHeight; if (w < 50 || h < 50) return;
  $('#map-fallback').hidden = true;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const fj = focusJob(), fpts = focusPts(fj), fc = fj && CITY[fj.params?.city];
  const area = fpts.length > 1 ? {type: 'MultiPoint', coordinates: fpts.map(p => [+p.lon, +p.lat])}
    : fc ? {type: 'MultiPoint', coordinates: [[fc[0] - .35, fc[1] - .25], [fc[0] + .35, fc[1] + .25]]} : null;
  const proj = d3.geoMercator().fitExtent([[w * (area && w > 720 ? .32 : .05), h * .1], [w * .95, h * .92]], area || geo.tr);
  const off = document.createElement('canvas'); off.width = w; off.height = h;
  const oc = off.getContext('2d', {willReadFrequently: true});
  const path = d3.geoPath(proj, oc);
  oc.fillStyle = '#00ff00'; oc.beginPath(); path(geo.nb); oc.fill();
  oc.fillStyle = '#ff0000'; oc.beginPath(); path(geo.tr); oc.fill();
  const px = oc.getImageData(0, 0, w, h).data;
  const cv = $('#map-dots'); cv.width = w * dpr; cv.height = h * dpr;
  const c = cv.getContext('2d'); c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, w, h);
  const step = w > 760 ? 7 : 6;
  const [[x0], [x1]] = d3.geoPath(proj).bounds(geo.tr);
  const tint = d3.interpolateRgbBasis(['#C6A1F2', '#A2BCE7', '#53C6D0', '#6EDCB6']);
  for (let y = step / 2; y < h; y += step) {
    for (let x = step / 2; x < w; x += step) {
      const i = ((y | 0) * w + (x | 0)) * 4;
      if (px[i] > 128) { c.fillStyle = tint(Math.max(0, Math.min(1, (x - x0) / (x1 - x0)))); c.globalAlpha = .8; c.beginPath(); c.arc(x, y, 1.5, 0, 7); c.fill(); }
      else if (px[i + 1] > 128) { c.fillStyle = '#ffffff'; c.globalAlpha = .06; c.beginPath(); c.arc(x, y, 1.1, 0, 7); c.fill(); }
    }
  }
  c.globalAlpha = 1;
  const svg = d3.select('#map-nodes').attr('viewBox', `0 0 ${w} ${h}`);
  svg.selectAll('*').remove();
  const pie = d3.pie().sort(null).value(d => d.n);
  scanCities().forEach(city => {
    const [x, y] = proj(CITY[city]);
    const g = svg.append('g').attr('class', 'scan-pulse').attr('transform', `translate(${x},${y})`).attr('aria-hidden', 'true');
    g.append('circle').attr('r', 30); g.append('circle').attr('r', 30).style('animation-delay', '.9s');
  });
  if (area) {
    const order = new Map((fj.found || []).map((p, i) => [p.id, i + 1]));
    fpts.forEach(p => {
      const [x, y] = proj([+p.lon, +p.lat]), n = order.get(p.id);
      const g = svg.append('g').attr('class', 'pin' + (pinPick === p.id ? ' is-active' : '')).attr('transform', `translate(${x},${y})`).attr('tabindex', 0).attr('role', 'button').attr('aria-label', `${n}. ${p.name}`);
      g.append('circle').attr('r', 10).attr('fill', '#C6A1F2').attr('stroke', '#0A0D14').attr('stroke-width', 2);
      g.append('text').attr('y', 3.8).attr('text-anchor', 'middle').text(n);
      g.on('click', () => openLead(p.id)).on('keydown', ev => { if (ev.key === 'Enter') openLead(p.id); });
    });
    return;
  }
  Object.entries(cityItems()).forEach(([city, L]) => {
    const parts = partsFor(L), total = d3.sum(parts, d => d.n); if (!total) return;
    const [x, y] = proj(CITY[city]);
    const r = 7 + Math.sqrt(total) * 2.2;
    const fresh = Object.keys(LAYERS).some(k => state.layers[k] && L[k].some(i => i.fresh));
    const g = svg.append('g').attr('class', 'node' + (fresh ? ' is-new' : '') + (activeCity === city ? ' is-active' : ''))
      .attr('transform', `translate(${x},${y})`).attr('tabindex', 0).attr('role', 'button')
      .attr('aria-label', `${city}: ${parts.map(p => p.n + ' ' + LAYERS[p.k].label.toLowerCase()).join(', ')}`);
    g.append('circle').attr('class', 'halo').attr('r', r + 6).attr('fill', 'none').attr('stroke', '#F2F2F5').attr('stroke-opacity', fresh ? .5 : 0);
    g.append('circle').attr('r', r + 10).attr('fill', LAYERS[parts[0].k].color).attr('fill-opacity', .08);
    const arc = d3.arc().innerRadius(r - 2.5).outerRadius(r + 1).padAngle(parts.length > 1 ? .08 : 0);
    g.selectAll('path').data(pie(parts)).join('path').attr('d', arc).attr('fill', d => LAYERS[d.data.k].color);
    g.append('circle').attr('class', 'core').attr('r', 3.2).attr('fill', '#F2F2F5');
    const open = () => openCity(city, x, y, w, h);
    g.on('click', open).on('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); } });
    if (w < 560) return;
    const left = x > w - 150;
    const t = g.append('text').attr('x', left ? -(r + 8) : r + 8).attr('y', 4.5).attr('text-anchor', left ? 'end' : 'start');
    t.append('tspan').text(city + ' ');
    t.append('tspan').attr('class', 'cnt').text(total);
  });
}
function openCity(city, x, y, w, h){
  activeCity = city;
  $$('.city-card').forEach(n => n.remove());
  const L = cityItems()[city]; if (!L) return;
  const card = document.createElement('div');
  card.className = 'city-card'; card.setAttribute('role', 'dialog'); card.setAttribute('aria-label', city);
  const items = Object.keys(LAYERS).filter(k => state.layers[k]).flatMap(k => L[k].map(i => ({...i, k})));
  card.innerHTML = `<h3>${esc(city)}<button class="icon-btn" style="width:34px;height:34px" type="button" aria-label="Kapat"><i class="ph ph-x" aria-hidden="true"></i></button></h3>
    <ul>${items.slice(0, 10).map((i, n) => `<li><button type="button" data-i="${n}" style="--c:${LAYERS[i.k].color}"><i aria-hidden="true"></i><span>${esc(i.t)}<small>${LAYERS[i.k].label}: ${esc(i.s)}</small></span></button></li>`).join('')}</ul>
    ${items.length > 10 ? `<button class="btn btn-text btn-sm" type="button" data-city-all>Tümünü Leadlerde gör (${items.length})</button>` : ''}`;
  const cw = Math.min(300, w - 24);
  card.style.left = Math.max(12, Math.min(x + 22, w - cw - 12)) + 'px';
  card.style.top = Math.max(12, Math.min(y - 30, h - 260)) + 'px';
  $('#map-wrap').append(card);
  card.querySelector('h3 button').onclick = () => { card.remove(); activeCity = null; drawMap(); };
  card.querySelectorAll('[data-i]').forEach(b => b.onclick = () => items[+b.dataset.i].go());
  card.querySelector('[data-city-all]')?.addEventListener('click', () => { state.city = city; state.leadSec = 'havuz'; state.leadSecSet = true; go('leadler'); renderLeadFilters(); renderLeads(); });
  drawMap();
  card.querySelector('[data-i]')?.focus();
}
new ResizeObserver(() => { closeCityCard(); if (mapMode === 'dots') drawMap(); }).observe($('#map-wrap'));

/* ---------- Jeff live ---------- */
const QUICK = ['En önemli fırsat hangisi?', 'Bursa\'da diş kliniklerini tara', 'Bugün yapay zekâda ne oldu?', 'Takip zamanı gelen leadler'];
let jeffIntroShown = false;
function msg(who, html, meta){
  const d = document.createElement('div'); d.className = 'msg ' + who;
  d.innerHTML = html + (meta ? `<span class="meta">${meta}</span>` : '');
  $('#thread').append(d); $('#thread').scrollTop = 1e6; return d;
}
function setJeff(s, label){ $('#jeff').dataset.state = s; $('#jeff-state').textContent = label; }
function initJeff(){
  jeffIntroShown = true;
  const b = D.briefing || {};
  const acts = [];
  if (D.leads.some(l => nextStep(l).list === 'sira')) acts.push('<button class="btn btn-primary btn-sm" type="button" data-go="leadler">Leadlere git</button>');
  if (b.focus?.opp) acts.push('<button class="btn btn-text btn-sm" type="button" id="j-opp">Fırsatı aç</button>');
  if (b.focus?.city && CITY[b.focus.city]) acts.push('<button class="btn btn-text btn-sm" type="button" id="j-map">Haritada göster</button>');
  if (D.approvals.some(a => a.status === 'Bekliyor')) acts.push('<button class="btn btn-text btn-sm" type="button" data-open="appr">Onayları aç</button>');
  const m = msg('j', esc(b.text || 'Merhaba.') + (acts.length ? `<div class="acts">${acts.join('')}</div>` : ''), 'Panel özeti');
  m.querySelector('#j-opp')?.addEventListener('click', () => { state.opp = b.focus.opp; go('firsatlar'); renderOpps(); });
  m.querySelector('#j-map')?.addEventListener('click', () => { if (!geo && mapMode !== 'google') return; const w = $('#map-wrap'); const [x, y] = cityPixel(b.focus.city); openCity(b.focus.city, x, y, w.clientWidth, w.clientHeight); });
  $('#quick').innerHTML = QUICK.map(q => `<button class="chip" type="button">${q}</button>`).join('');
}
const jeffMeta = () => D.jeff === 'hermes' ? 'Jeff' : 'Yedek Jeff, gerçek Jeff\'e bağlı değil';

/* Voice. Jeff's words arrive as a stream; every finished sentence is turned into speech right away, and its text
   appears at the moment its voice starts, so what you read is what you hear. */
const voiceOn = () => $('#voice-out').getAttribute('aria-pressed') === 'true';
const VOICE_LABELS = {Charon: 'Charon, sakin', Orus: 'Orus, kararlı', Algieba: 'Algieba, yumuşak', Sadaltager: 'Sadaltager, bilgili'};
let voiceName = 'Charon';
try { const v = localStorage.getItem('cgos-voice'); if (VOICE_LABELS[v]) voiceName = v; } catch (e) {}
let geminiBlockedUntil = 0, voiceWarned = false;
const geminiVoice = () => D.voice && Date.now() > geminiBlockedUntil;
const spk = {ctx: null, token: 0, next: 0, sources: [], aborts: [], timers: [], flush: null, streamAbort: null};
const SPOKEN_LIMIT = 450;
function audioCtx(){
  spk.ctx ||= new (window.AudioContext || window.webkitAudioContext)();
  if (spk.ctx.state === 'suspended') spk.ctx.resume();
  return spk.ctx;
}
function stopAudio(){
  if ('speechSynthesis' in window) speechSynthesis.cancel();
  spk.token++;
  spk.sources.forEach(s => { try { s.stop(); } catch (e) {} }); spk.sources = [];
  spk.aborts.forEach(a => a.abort()); spk.aborts = [];
  spk.timers.forEach(clearTimeout); spk.timers = [];
  spk.next = 0;
  spk.streamAbort?.abort(); spk.streamAbort = null;
  const f = spk.flush; spk.flush = null; if (f) f();
}
const cleanSpeech = t => t.replace(/[*_`#>~]/g, '').replace(/\p{Extended_Pictographic}/gu, '').replace(/\s+/g, ' ').trim();
function splitSentences(buf, final){
  const done = []; let start = 0, m;
  const re = /[.!?…]+["')\]]*\s+|\n+/g;
  while ((m = re.exec(buf))) { const end = m.index + m[0].length, s = buf.slice(start, end).trim(); if (s) done.push(s); start = end; }
  let rest = buf.slice(start);
  if (final && rest.trim()) { done.push(rest.trim()); rest = ''; }
  return {done, rest};
}
/* One sentence of raw 24 kHz PCM, fetched immediately (so later sentences are ready while earlier ones play). */
function pcmStream(text, token){
  const q = [], waiters = [], ac = new AbortController();
  let finished = false, error = null;
  spk.aborts.push(ac);
  const wake = () => waiters.splice(0).forEach(w => w());
  (async () => {
    try {
      const r = await fetch('/api/tts/stream', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text: cleanSpeech(text), voice: voiceName}), signal: ac.signal});
      if (!r.ok) throw new Error('tts');
      const reader = r.body.getReader(); let carry = new Uint8Array(0);
      for (;;) {
        const {done, value} = await reader.read(); if (done) break;
        const bytes = new Uint8Array(carry.length + value.length); bytes.set(carry); bytes.set(value, carry.length);
        const even = bytes.length - (bytes.length % 2); carry = bytes.slice(even);
        if (!even) continue;
        const i16 = new Int16Array(bytes.slice(0, even).buffer), f32 = new Float32Array(i16.length);
        for (let k = 0; k < i16.length; k++) f32[k] = i16[k] / 32768;
        q.push(f32); wake();
      }
    } catch (e) { if (e.name !== 'AbortError') error = e; }
    finished = true; wake();
  })();
  return {async *[Symbol.asyncIterator](){
    for (let i = 0;;) {
      if (i < q.length) { yield q[i++]; continue; }
      if (finished) { if (error) throw error; return; }
      await new Promise(r => waiters.push(r));
    }
  }};
}
/* Plays the sentences of one reply in order. reveal(text) is called when that sentence's voice starts.
   The first sentence is spoken on its own (fastest start); the rest are joined into as few requests as possible,
   because the free voice quota is counted per request. If Gemini's voice is unavailable (daily quota), the browser's
   own voice takes over for that sentence, and the text still appears exactly when the voice starts. */
const sleep = ms => new Promise(r => setTimeout(r, ms));
const trVoice = () => 'speechSynthesis' in window ? speechSynthesis.getVoices().find(v => v.lang?.toLowerCase().startsWith('tr')) : null;
async function browserSay(texts, token, reveal){
  const c = audioCtx();
  const wait = Math.max(0, (spk.next - c.currentTime) * 1000); if (wait) await sleep(wait);
  if (token !== spk.token) return;
  const v = trVoice();
  if (!v || !('speechSynthesis' in window)) { texts.forEach(reveal); return; }
  for (const t of texts) {
    if (token !== spk.token) return;
    await new Promise(done => {
      const u = new SpeechSynthesisUtterance(cleanSpeech(t)); u.lang = 'tr-TR'; u.voice = v;
      u.onstart = () => { if (token === spk.token) { reveal(t); setJeff('speaking', 'Konuşuyor'); } };
      u.onend = u.onerror = done;
      speechSynthesis.speak(u);
    });
  }
}
function voiceQueue(token, reveal, onFallback){
  const list = [], waiters = []; let closed = false, pending = null, spoken = 0;
  const wake = () => waiters.splice(0).forEach(w => w());
  const make = texts => ({texts, silent: false, pcm: geminiVoice() ? pcmStream(texts.join(' '), token) : null});
  const flush = () => { if (pending) { list.push(make(pending.texts)); pending = null; wake(); } };
  (async () => { try {
    const c = audioCtx();
    for (let i = 0;;) {
      if (token !== spk.token) return;
      if (i < list.length) {
        const item = list[i++];
        if (item.silent) { const wait = Math.max(0, (spk.next - c.currentTime) * 1000); spk.timers.push(setTimeout(() => token === spk.token && item.texts.forEach(reveal), wait)); continue; }
        if (item.pcm) {
          try {
            let started = false, startWhen = 0;
            for await (const f32 of item.pcm) {
              if (token !== spk.token) return;
              const buf = c.createBuffer(1, f32.length, 24000); buf.copyToChannel(f32, 0);
              const src = c.createBufferSource(); src.buffer = buf; src.connect(c.destination);
              const when = Math.max(c.currentTime + 0.04, spk.next);
              src.start(when); spk.next = when + buf.duration; spk.sources.push(src);
              if (!started) {
                started = true; startWhen = when;
                spk.timers.push(setTimeout(() => { if (token === spk.token) { reveal(item.texts[0]); setJeff('speaking', 'Konuşuyor'); } }, Math.max(0, (when - c.currentTime) * 1000)));
              }
            }
            if (!started) throw new Error('bos');
            /* later sentences of a joined request appear in proportion to their length across the spoken time */
            const total = spk.next - startWhen, chars = item.texts.reduce((n, t) => n + t.length, 0);
            let cum = item.texts[0].length;
            item.texts.slice(1).forEach(t => {
              const at = startWhen + total * cum / chars; cum += t.length;
              spk.timers.push(setTimeout(() => token === spk.token && reveal(t), Math.max(0, (at - c.currentTime) * 1000)));
            });
            continue;
          } catch (e) {
            if (token !== spk.token) return;
            geminiBlockedUntil = Date.now() + 10 * 60 * 1000; onFallback();
          }
        }
        await browserSay(item.texts, token, reveal);
        continue;
      }
      if (closed) break;
      await new Promise(r => waiters.push(r));
    }
    const rest = Math.max(0, (spk.next - c.currentTime) * 1000) + 200;
    spk.timers.push(setTimeout(() => { if (token === spk.token) setJeff('idle', 'Hazır'); }, rest));
  } catch (e) { if (token === spk.token && spk.flush) spk.flush(); } })();
  return {
    add(text){
      const silent = spoken > SPOKEN_LIMIT; spoken += text.length;
      if (silent) { flush(); list.push({texts: [text], silent: true}); wake(); return; }
      if (!list.length && !pending) { list.push(make([text])); wake(); return; }
      pending ||= {texts: [], chars: 0}; pending.texts.push(text); pending.chars += text.length;
      if (pending.chars >= 220) flush();
    },
    close(){ flush(); closed = true; wake(); }
  };
}
const voiceFallbackNotice = () => { if (!voiceWarned) { voiceWarned = true; toast('Jeff\'in ses kotası şu an dolu, tarayıcının sesiyle devam ediyorum. Yazı yine sesle aynı anda çıkar.'); } };
async function playOnce(text){
  stopAudio(); const token = spk.token;
  setJeff('thinking', 'Ses hazırlanıyor');
  const vq = voiceQueue(token, () => {}, voiceFallbackNotice);
  vq.add(text); vq.close();
}

let jeffOpportunityId = null;
let askSeq = 0;
async function ask(text, opts = {}){
  text = text.trim(); if (!text) return;
  if (opts.opportunityId !== undefined) jeffOpportunityId = opts.opportunityId;
  abortListening(); stopAudio();
  const seq = ++askSeq, token = spk.token;
  const speaking = voiceOn();
  if (speaking) audioCtx();
  if (!opts.fromVoice) msg('u', esc(opts.displayText || text));
  setJeff('thinking', 'Düşünüyor');
  const t0 = Date.now();
  const tick = setInterval(() => { if (seq === askSeq && $('#jeff').dataset.state === 'thinking') $('#jeff-state').textContent = 'Yanıt hazırlanıyor... ' + Math.round((Date.now() - t0) / 1000) + ' sn'; }, 1000);
  let bubble = null, shown = '', revealed = 0;
  const sentences = [];
  const show = s => {
    if (!bubble) { bubble = msg('j', '<span class="t"></span>', jeffMeta()); }
    shown += (shown ? ' ' : '') + s; bubble.querySelector('.t').textContent = shown; $('#thread').scrollTop = 1e6;
  };
  const reveal = s => { if (seq !== askSeq) return; revealed++; show(s); };
  const vq = speaking ? voiceQueue(token, reveal, voiceFallbackNotice) : null;
  spk.flush = () => { if (seq !== askSeq) return; sentences.slice(revealed).forEach(show); revealed = sentences.length; clearInterval(tick); setJeff('idle', 'Hazır'); };
  const voiceActive = () => vq && token === spk.token;
  let buf = '', carry = '';
  const emit = s => { sentences.push(s); if (voiceActive()) vq.add(s); else { revealed++; show(s); } };
  const onSentence = (s, final) => { s = carry ? (s ? carry + ' ' + s : carry) : s; carry = ''; if (!s) return; if (!final && s.length < 28) { carry = s; return; } emit(s); };
  const ac = new AbortController(); spk.streamAbort = ac;
  let failed = false;
  try {
    const r = await fetch('/api/jeff/stream', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({text, ...(jeffOpportunityId ? {opportunity_id: jeffOpportunityId} : {})}), signal: ac.signal});
    if (r.status === 401) { location.href = '/login'; return; }
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || 'hata');
    const reader = r.body.getReader(), dec = new TextDecoder(); let line = '';
    for (;;) {
      const {done, value} = await reader.read(); if (done) break;
      line += dec.decode(value, {stream: true});
      let i;
      while ((i = line.indexOf('\n')) >= 0) {
        const ev = JSON.parse(line.slice(0, i)); line = line.slice(i + 1);
        if (ev.t === 'd') { buf += ev.x; const p = splitSentences(buf.replace(/^\s+/, ''), false); buf = p.rest; p.done.forEach(s => onSentence(s, false)); }
        else if (ev.t === 'job') onScanEvent(ev);
        else if (ev.t === 'err') failed = true;
      }
    }
    const p = splitSentences(buf.replace(/^\s+/, ''), true); p.done.forEach(s => onSentence(s, true));
    onSentence('', true);
  } catch (e) {
    if (e.name === 'AbortError') return;
    failed = true;
  }
  clearInterval(tick);
  setTimeout(pollJobs, 400);  // Jeff may have started a scan; show it on the radar right away
  if (seq !== askSeq) return;
  lastReply = sentences.join(' ');
  vq?.close();
  if (failed && !sentences.length) {
    setJeff('idle', 'Hazır'); spk.flush = null;
    msg('j', D.jeff === 'kapali' ? 'Jeff\'in anahtarı tanımlı olmadığı için şu an konuşamıyorum.' : 'Şu an Jeff\'e ulaşamadım. Birkaç saniye sonra tekrar deneyin.', 'Bağlantı yok');
    return;
  }
  if (failed) toast('Jeff\'in cevabı yarıda kesildi.');
  if (!vq) setJeff('idle', 'Hazır');
}
$('#quick').addEventListener('click', e => { const b = e.target.closest('button'); if (b) ask(b.textContent); });
$('#composer').addEventListener('submit', e => { e.preventDefault(); const a = $('#ask'); ask(a.value); a.value = ''; });
$('#ask').addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); $('#composer').requestSubmit(); } });
$('#new-chat').addEventListener('click', async () => {
  abortListening(); stopAudio(); askSeq++; lastReply = ''; jeffOpportunityId = null;
  try { await api('jeff/reset', {}); } catch (e) {}
  $('#thread').innerHTML = ''; setJeff('idle', 'Hazır'); initJeff(); toast('Yeni sohbet başladı.');
});

/* Continuous live call. */
const mic = $('#mic');
let lastReply = '';
const muteButton=document.createElement('button');
muteButton.type='button';muteButton.className='mic';muteButton.hidden=true;
muteButton.style.display='none';
muteButton.id='mic-mute';muteButton.setAttribute('aria-label','Mikrofonu kapat');
muteButton.innerHTML='<i class="ph ph-microphone-slash" aria-hidden="true"></i>';
mic.after(muteButton);
let liveBubble={user:null,jeff:null};
const liveCall=new JeffLiveCall({
  opportunity:()=>jeffOpportunityId,
  voice:()=>voiceName,worklet:new URL('mic-capture.js',location.href).href,
  state:(state,label)=>{
    setJeff(state==='connecting'?'thinking':state,label);
    const on=liveCall.active;mic.setAttribute('aria-pressed',String(on));
    mic.setAttribute('aria-label',on?'Görüşmeyi bitir':'Canlı görüşmeyi başlat');
    mic.innerHTML=`<i class="ph ${on?'ph-phone-disconnect':'ph-phone-call'}" aria-hidden="true"></i>`;
    muteButton.hidden=!on;
    muteButton.style.display=on?'grid':'none';
    $('#composer').style.gridTemplateColumns=on?'minmax(0,1fr) auto auto auto':'';
    $('#voice-out').disabled=on;$('#voice-pick').disabled=on;
    muteButton.setAttribute('aria-pressed',String(liveCall.muted===true));
    muteButton.setAttribute('aria-label',liveCall.muted?'Mikrofonu aç':'Mikrofonu kapat');
  },notice:toast,
  transcript:(who,text,final)=>{
    if(!liveBubble[who])liveBubble[who]=msg(who==='user'?'u':'j','<span class="t"></span>',who==='jeff'?jeffMeta():'Sesli');
    liveBubble[who].querySelector('.t').textContent=text;$('#thread').scrollTop=1e6;
    if(final)liveBubble[who]=null;
  }
});
function abortListening(){if(liveCall.active)liveCall.stop();}
function micHint(){
  const h=$('#mic-hint');h.hidden=window.isSecureContext&&!!navigator.mediaDevices?.getUserMedia;
  h.textContent=h.hidden?'':'Canlı görüşme için panelin güvenli https adresini açın. Yazarak konuşabilirsiniz.';
  mic.setAttribute('aria-label','Canlı görüşmeyi başlat');
  mic.innerHTML='<i class="ph ph-phone-call" aria-hidden="true"></i>';
}
mic.addEventListener('click',async()=>{
  if(liveCall.active){liveCall.stop();return;}
  stopAudio();askSeq++;liveBubble={user:null,jeff:null};
  try{await liveCall.start();}catch(e){toast(e.name==='NotAllowedError'?'Görüşme için tarayıcıda mikrofon izni verin.':e.message);}
});
muteButton.addEventListener('click',()=>{
  const muted=liveCall.mute();muteButton.setAttribute('aria-pressed',String(muted));
  muteButton.setAttribute('aria-label',muted?'Mikrofonu aç':'Mikrofonu kapat');
});
window.addEventListener('pagehide',()=>liveCall.stop());
$('#voice-out').addEventListener('click', e => {
  const b = e.currentTarget, on = b.getAttribute('aria-pressed') !== 'true';
  b.setAttribute('aria-pressed', on); b.setAttribute('aria-label', on ? 'Sesli yanıtı kapat' : 'Sesli yanıtı aç');
  b.innerHTML = `<i class="ph ${on ? 'ph-speaker-high' : 'ph-speaker-slash'}" aria-hidden="true"></i>`;
  if (!on) { stopAudio(); setJeff('idle', 'Hazır'); }
});
const vsel = $('#voice-pick');
vsel.innerHTML = Object.entries(VOICE_LABELS).map(([k, l]) => `<option value="${k}" ${k === voiceName ? 'selected' : ''}>${l}</option>`).join('');
vsel.addEventListener('change', () => {
  voiceName = vsel.value; geminiBlockedUntil = 0;
  try { localStorage.setItem('cgos-voice', voiceName); } catch (e) {}
  audioCtx(); playOnce('Merhaba, ben Jeff. Sesim böyle.');
});
micHint();

/* ---------- Radar: every scan is a job you can follow step by step ---------- */
const WHO = {bilal: 'Siz', jeff: 'Jeff', zamanlayici: 'Zamanlayıcı'};
const STARTED = {bilal: 'Siz başlattınız', jeff: 'Jeff başlattı', zamanlayici: 'Zamanlayıcı başlattı'};
const JOB_STATE = {queued: ['Sırada', '#A2BCE7'], running: ['Çalışıyor', '#53C6D0'], done: ['Bitti', '#6EDCB6'], failed: ['Olmadı', '#F4A3A3'], cancelled: ['Durduruldu', '#8D90A0']};
const KIND = {radar: 'Haber ve fırsat taraması', lead_scan: 'İşletme taraması'};
const activeJobs = () => (D.jobs || []).filter(j => j.status === 'queued' || j.status === 'running');
const clock = ts => new Date(ts * 1000).toLocaleTimeString('tr-TR', {hour: '2-digit', minute: '2-digit'});
let knownJobs = null, jobsTimer = null, pulseKey = '';
const seenBlips = new Set();
function hash(s){ let h = 2166136261; for (const ch of String(s)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619); return h >>> 0; }
function blipColor(t){
  if (/^Yeni:/.test(t)) return '#C6A1F2';
  if (/^Fırsat/.test(t)) return '#6EDCB6';
  if (/okunamadı|yanıt vermedi|hız sınırı|^Hata/.test(t)) return '#F4A3A3';
  if (/: \d+ kayıt$/.test(t)) return '#53C6D0';
  return null;
}
function scopeJob(){
  const jobs = D.jobs || [];
  return jobs.find(j => j.id === state.radarJob) || activeJobs().find(j => j.status === 'running') || activeJobs()[0] || jobs[0] || null;
}
function jobLine(j){
  const r = j.result || {};
  if (j.status === 'done' && j.kind === 'lead_scan') return `${r.found ?? 0} işletme bulundu, ${r.new ?? 0} yeni lead`;
  if (j.status === 'done' && j.kind === 'radar') return `${r.opps ?? 0} fırsat, ${r.news ?? 0} haber`;
  return j.note || JOB_STATE[j.status]?.[0] || '';
}
function blipsFor(j){
  if (!j) return [];
  /* a lead scan shows every business it found; a news scan shows each source it read and each opportunity it picked */
  if (j.kind === 'lead_scan') return D.leads.filter(l => l.job === j.id).slice(0, 60).map(l => ({k: j.id + l.id, t: l.name, c: '#C6A1F2'}));
  return j.log.map(([, t]) => ({k: j.id + t, t, c: blipColor(t)})).filter(b => b.c);
}
function renderScope(){
  const j = scopeJob(), running = !!j && (j.status === 'running' || j.status === 'queued');
  $('#scope').dataset.state = running ? 'running' : 'idle';
  $('#scope-ring').setAttribute('stroke-dasharray', `${j ? (j.status === 'done' ? 100 : j.progress) : 0} 100`);
  $('#scope-pct').innerHTML = !j ? '' : running ? `%${j.progress}` : j.status === 'done' ? '<i class="ph ph-check" aria-hidden="true"></i>' : j.status === 'failed' ? '<i class="ph ph-warning" aria-hidden="true"></i>' : '';
  const bl = blipsFor(j);
  $('#blips').innerHTML = bl.map((b, i) => {
    const a = (hash(b.t) % 360) * Math.PI / 180, r = 0.16 + 0.3 * ((i * 0.618 + (hash(b.k) % 97) / 97) % 1) + 0.0;
    const x = 50 + Math.cos(a) * r * 100, y = 50 + Math.sin(a) * r * 100;
    const fresh = !seenBlips.has(b.k); seenBlips.add(b.k);
    return `<span class="blip ${fresh && running ? 'new' : ''}" style="left:${x.toFixed(2)}%;top:${y.toFixed(2)}%;--c:${b.c}" title="${esc(b.t)}"></span>`;
  }).join('');
  const r = j?.result || {};
  let acts = '';
  if (j && j.status === 'done' && j.kind === 'lead_scan' && r.new) acts = `<button class="btn btn-primary btn-sm" type="button" data-show-job="${j.id}">Bulunan ${r.new} işletmeyi gör</button>`;
  if (j && j.status === 'done' && j.kind === 'radar') acts = `${r.opps ? `<button class="btn btn-primary btn-sm" type="button" data-go="firsatlar">${r.opps} fırsata bak</button>` : ''}<button class="btn btn-glass btn-sm" type="button" data-go="haberler">Haberlere git</button>`;
  if (j && running) acts = `<button class="btn btn-text btn-sm" type="button" data-cancel="${j.id}">Durdur</button>`;
  $('#scope-kicker').textContent = j ? `${KIND[j.kind]}, ${STARTED[j.by] || STARTED.bilal}, ${clock(j.created_at)}` : 'Radar';
  $('#scope-title').textContent = j ? j.title : 'Henüz tarama yok';
  $('#scope-note').innerHTML = (j ? esc(running ? (j.note || 'Başlıyor') : jobLine(j)) : 'Haber ve fırsat taraması kendiliğinden düzenli çalışır. İşletme taramasını siz başlatırsınız ya da Jeff\'e söylersiniz.')
    + (acts ? `<span class="row" style="justify-content:center;margin-top:12px">${acts}</span>` : '');
}
function jobCard(j){
  const [label, color] = JOB_STATE[j.status] || ['', '#8D90A0'];
  return `<article class="job" data-job="${j.id}" aria-current="${scopeJob()?.id === j.id}">
    <span class="m"><span class="tag" style="color:${color};border-color:${color}55">${label}</span><span class="tag who-tag">${esc(STARTED[j.by] || STARTED.bilal)}</span><span>${clock(j.created_at)}</span></span>
    <h3>${esc(j.title)}</h3>
    <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${j.progress}" aria-label="İlerleme"><i style="width:${j.progress}%"></i></div>
    <p class="now">%${j.progress}, ${esc(j.note || 'Başlıyor')}</p>
    ${j.log.length ? `<ol>${j.log.slice(-6).map(([ts, t]) => `<li><time>${clock(ts)}</time><span>${esc(t)}</span></li>`).join('')}</ol>` : ''}
    <div class="acts"><button class="btn btn-text btn-sm" type="button" data-cancel="${j.id}">Durdur</button></div>
  </article>`;
}
function renderJobs(){
  const act = activeJobs();
  $('#jobs-active').innerHTML = act.length ? act.map(jobCard).join('')
    : `<div class="panel empty" style="padding:22px">Şu an çalışan tarama yok.<br>Yukarıdan başlatın ya da Jeff'e söyleyin: <b style="font-weight:500;color:var(--text)">"Bursa'da diş kliniklerini tara"</b>.</div>`;
  const done = (D.jobs || []).filter(j => !act.includes(j)).slice(0, 8);
  $('#jobs-done').innerHTML = done.length ? done.map(j => `<li><button type="button" data-job="${j.id}" aria-current="${scopeJob()?.id === j.id}"><span class="st" style="--c:${JOB_STATE[j.status]?.[1] || '#8D90A0'}" aria-hidden="true"></span>
      <span>${esc(j.title)}<small>${esc(jobLine(j))}</small></span><small>${esc(WHO[j.by] || 'Siz')}, ${ago(j.finished_at || j.created_at)}</small></button></li>`).join('')
    : '<li class="help" style="margin:0">Biten tarama yok.</li>';
  const n = act.length;
  $('#n-jobs').hidden = !n; $('#n-jobs').textContent = n;
  const pill = $('#job-pill'); pill.hidden = !n;
  if (n) pill.querySelector('span').textContent = n > 1 ? `${n} tarama sürüyor` : `${act[0].title.split(':')[0]}, %${act[0].progress}`;
  renderScope();
  const key = scanCities().join('|');
  if (key !== pulseKey) { pulseKey = key; drawMap(); }
}
function renderSources(){
  const SS = {ok: '#6EDCB6', slow: '#F4C27A', down: '#F4A3A3', bekliyor: '#8D90A0'};
  $('#srcs').innerHTML = (D.sources || []).map(g => `<li><details><summary><span><span class="dot-s" style="--c:${SS[g.state] || SS.bekliyor}" aria-hidden="true"></span>${esc(g.name)}</span>
      <span>${g.state === 'bekliyor' ? 'henüz okunmadı' : `${g.ok}/${g.items.length} açık${g.last_ok ? ', ' + ago(g.last_ok) : ''}`}</span></summary>
      <ul>${g.items.map(i => `<li class="${i.state === 'down' ? 'down' : ''}">${esc(i.name)}: ${i.state === 'ok' ? i.count + ' kayıt' : i.state === 'slow' ? 'hız sınırı' : i.state === 'down' ? 'okunamadı' : 'bekliyor'}</li>`).join('')}</ul></details></li>`).join('')
    || '<li><span>Kaynak yok</span></li>';
}
function renderRadar(){ renderJobs(); renderSources(); }
async function pollJobs(){
  clearTimeout(jobsTimer);
  try {
    const before = new Set(activeJobs().map(j => j.id));
    const d = await api('jobs');
    D.jobs = d.jobs;
    const fresh = knownJobs ? D.jobs.filter(j => !knownJobs.has(j.id)) : [];
    knownJobs = new Set(D.jobs.map(j => j.id));
    fresh.filter(j => j.by === 'jeff').forEach(j => toast(`Jeff bir tarama başlattı: ${j.title}. Komuta ekranındaki haritada izleyebilirsiniz.`));
    const scan = fresh.find(j => j.kind === 'lead_scan' && (j.status === 'running' || j.status === 'queued'));
    const cur = focusJob();
    if (scan && (!cur || !(cur.status === 'running' || cur.status === 'queued') || cur.id === scan.id)) startFocus(scan);
    else if (state.focusJob) renderFocus();
    const nowActive = new Set(activeJobs().map(j => j.id));
    const ended = [...before].filter(id => !nowActive.has(id)).map(id => D.jobs.find(j => j.id === id)).filter(Boolean);
    if (ended.length) {
      await refresh();
      if (sheetKind === 'lead' && openLeadId && ended.some(j => ['marketing', 'qualification'].includes(j.kind) && (j.params?.ids || []).includes(openLeadId))) openLead(openLeadId);
      const j = ended[0];
      if (j.by !== 'zamanlayici' || j.kind !== 'radar') toast(`${j.title}: ${j.status === 'done' ? jobLine(j) : j.note}`);
    } else renderJobs();
  } catch (e) {}
  jobsTimer = setTimeout(pollJobs, activeJobs().length ? 1500 : 12000);
}
function renderRadarLine(){
  const r = D.radar || {};
  $('#radar-line').textContent = r.running ? 'Radar şu an tarıyor: ' + (r.progress || '...') : !r.last_run ? 'Radar henüz çalışmadı.' : `Son tarama ${ago(r.last_run)}. ${r.summary || ''}`;
  $('#run-radar').disabled = !!r.running;
  $('#run-radar').firstElementChild.className = 'ph ' + (r.running ? 'ph-circle-notch spin' : 'ph-arrow-clockwise');
}
$('#run-radar').addEventListener('click', async () => {
  try {
    const d = await api('radar/run', {});
    if (d.job) { state.radarJob = d.job; toast('Tarama başladı. İlerlemeyi burada görebilirsiniz.'); }
    else toast('Bir haber taraması zaten sürüyor.');
    go('radar'); await pollJobs();
  } catch (e) { toast(ERRORS[e.message] || 'Tarama başlatılamadı.'); }
});
document.addEventListener('click', async e => {
  const c = e.target.closest('[data-cancel]');
  if (c) { e.stopPropagation(); c.disabled = true; try { await api(`jobs/${c.dataset.cancel}/cancel`, {}); toast('Durdurma isteği gönderildi.'); } catch (err) { toast('Bu tarama artık durdurulamıyor.'); } return pollJobs(); }
  const j = e.target.closest('[data-job]');
  if (j && !e.target.closest('button[data-cancel]')) { state.radarJob = j.dataset.job; renderJobs(); if (innerWidth < 1000) $('#scope').scrollIntoView({behavior: 'smooth'}); }
  const sj = e.target.closest('[data-show-job]');
  if (sj) { state.leadSec = 'havuz'; state.leadSecSet = true; state.leadJob = sj.dataset.showJob; go('leadler'); renderLeadFilters(); renderLeads(); }
  if (e.target.closest('[data-scan]')) openScan();
});

/* ---------- Fırsatlar: only what Bilal can act on this week, ranked by Jeff ---------- */
const STARS = n => `<span class="stars" role="img" aria-label="${n} yıldız">${'★'.repeat(n)}<s>${'★'.repeat(5 - n)}</s></span>`;
function oppList(){
  const st = state.oppStatus;
  return D.opps.filter(o => (st === 'acik' ? oppOpen(o) : o.status === st) && (state.oppTag === 'all' || o.tags.includes(state.oppTag)) && (state.oppSrc === 'all' || o.src === state.oppSrc))
    .sort((a, b) => b.stars - a.stars || b.ts - a.ts);
}
function renderOpps(){
  const base = D.opps.filter(o => state.oppStatus === 'acik' ? oppOpen(o) : o.status === state.oppStatus);
  const tags = [...new Set(base.flatMap(o => o.tags))].sort((a, b) => a.localeCompare(b, 'tr'));
  if (state.oppTag !== 'all' && !tags.includes(state.oppTag)) state.oppTag = 'all';
  state.oppTag = 'all'; $('#opp-tags').hidden = true;  // topic chips removed (02.10): the list is short since only build-on sources feed it
  $$('#opp-status button').forEach(b => b.setAttribute('aria-pressed', b.dataset.v === state.oppStatus));
  const srcs = [...new Set(base.map(o => o.src))].sort((a, b) => a.localeCompare(b, 'tr'));
  if (state.oppSrc !== 'all' && !srcs.includes(state.oppSrc)) state.oppSrc = 'all';
  $('#opp-srcs').innerHTML = srcs.length > 1 ? ['all', ...srcs].map(t => `<button class="chip" type="button" data-src="${esc(t)}" aria-pressed="${state.oppSrc === t}">${t === 'all' ? 'Tüm kaynaklar' : `<i class="ph ${icon(t)}" aria-hidden="true"></i>${esc(t)}`} <span class="n">${t === 'all' ? base.length : base.filter(o => o.src === t).length}</span></button>`).join('') : '';
  if (!state.loaded) { $('#opp-list').innerHTML = '<li class="sk"></li><li class="sk"></li><li class="sk"></li>'; $('#opp-detail').innerHTML = ''; return; }
  const list = oppList();
  $('#opp-list').innerHTML = list.length ? list.map(o => `<li><button class="opp" type="button" role="option" aria-selected="${o.id === state.opp}" data-opp="${o.id}">
      <span class="row1">${STARS(o.stars)}<span><i class="ph ${icon(o.src)}" aria-hidden="true"></i> ${esc(o.src)}</span><span class="sp">${ago(o.ts)}</span></span>
      <h3>${esc(o.title)}</h3>
      ${o.gain ? `<p>${esc(o.gain)}</p>` : ''}
      <span class="foot">${o.fresh ? '<span class="tag sample">Yeni</span>' : ''}${o.status === 'Takipte' ? '<span class="tag you">Takipte</span>' : ''}${o.effort ? `<span class="tag">Efor: ${esc(o.effort)}</span>` : ''}${o.tags.map(t => `<span class="tag">${esc(t)}</span>`).join('')}</span>
    </button></li>`).join('')
    : `<li class="empty"><h3>${state.oppStatus === 'acik' ? 'Açık fırsat yok' : 'Bu listede fırsat yok'}</h3>${state.oppStatus !== 'acik' ? '' : D.radar.last_run ? 'Jeff son taramalarda bu hafta hamle yapmaya değer bir şey bulmadı. Gördüğünüz bir paylaşımı "Gördüğüm bir şeyi ekle" ile ekleyebilirsiniz.' : 'Radar çalışınca Jeff\'in seçtikleri burada görünür.'}</li>`;
  const o = list.find(x => x.id === state.opp) || list[0];
  if (o) state.opp = o.id;
  if (!o) { $('#opp-detail').innerHTML = '<div class="empty"><h3>Bir fırsat seçin</h3>Ne kazandıracağı ve önerilen hamle burada açılır.</div>'; return; }
  const link = safeUrl(o.url);
  $('#opp-detail').innerHTML = `
    <div class="row">${STARS(o.stars)}<span class="tag"><i class="ph ${icon(o.src)}" aria-hidden="true"></i>${esc(o.src)}${o.sub ? ', ' + esc(o.sub) : ''}</span><span class="kicker">${ago(o.ts)}</span></div>
    <h2>${esc(o.title)}</h2>
    ${o.why ? `<p style="margin:10px 0 0;color:var(--soft)">${esc(o.why)}</p>` : ''}
    <dl class="gain">
      <div class="move"><dt><i class="ph ph-footprints" aria-hidden="true"></i>Önerilen hamle</dt><dd>${esc(o.move || 'Jeff\'le konuşup birlikte belirleyin.')}</dd></div>
      <div><dt><i class="ph ph-trend-up" aria-hidden="true"></i>Ne kazandırır</dt><dd>${esc(o.gain || 'Jeff belirtmedi')}</dd></div>
      <div><dt><i class="ph ph-timer" aria-hidden="true"></i>Efor</dt><dd>${esc(o.effort || 'Belirsiz')}</dd></div>
    </dl>
    <div class="quote">${esc(o.quote)}<cite>Kaynaktan</cite></div>
    <div class="actions">
      <button class="btn btn-primary" type="button" data-oa="talk"><i class="ph ph-chats-circle" aria-hidden="true"></i>Jeff'le konuş</button>
      ${link ? `<a class="btn btn-glass" href="${esc(link)}" target="_blank" rel="noopener noreferrer">Kaynağı aç <i class="ph ph-arrow-up-right" aria-hidden="true"></i></a>` : ''}
      ${o.status === 'Yeni' ? '<button class="btn btn-text" type="button" data-oa="track">Takibe al</button>' : ''}
      ${o.status !== 'Yapıldı' ? '<button class="btn btn-text" type="button" data-oa="done">Yaptım</button>' : ''}
      <button class="btn btn-text" type="button" data-oa="${o.status === 'Geçildi' || o.status === 'Yapıldı' ? 'restore' : 'skip'}">${o.status === 'Geçildi' || o.status === 'Yapıldı' ? 'Açığa geri al' : 'Geç'}</button>
    </div>
    <p class="final"><i class="ph ph-info" aria-hidden="true"></i>Jeff yapay zekâ kaynaklarından yalnızca bu hafta hamle yapmaya değer olanları seçer. Yıldız, önemini gösterir.</p>`;
}
$('#opp-srcs').addEventListener('click', e => { const b = e.target.closest('[data-src]'); if (b) { state.oppSrc = b.dataset.src; renderOpps(); } });
$('#opp-tags').addEventListener('click', e => { const b = e.target.closest('[data-tag]'); if (b) { state.oppTag = b.dataset.tag; renderOpps(); } });
$('#opp-status').addEventListener('click', e => { const b = e.target.closest('[data-v]'); if (b) { state.oppStatus = b.dataset.v; state.opp = null; renderOpps(); } });
$('#opp-list').addEventListener('click', e => { const b = e.target.closest('[data-opp]'); if (b) { state.opp = b.dataset.opp; renderOpps(); if (innerWidth < 1000) $('#opp-detail').scrollIntoView({behavior: 'smooth'}); } });
$('#opp-detail').addEventListener('click', async e => {
  const b = e.target.closest('[data-oa]'); if (!b) return;
  const o = D.opps.find(x => x.id === state.opp); if (!o) return;
  if (b.dataset.oa === 'talk') { go('komuta'); return ask('Seçtiğim fırsatı konuşalım. Kartında neden fırsat gördüğünü, beklenen faydayı ve ilk küçük adımı açıkla. Önceki değerlendirmeni değiştirdiysen nedenini de söyle.', {opportunityId: o.id, displayText: `"${o.title}" fırsatını konuşalım.`}); }
  await act(`opp/${o.id}/${b.dataset.oa}`, {}, {track: 'Takibe alındı.', done: 'Yapıldı olarak işaretlendi.', skip: 'Geçildi.', restore: 'Açık fırsatlara geri alındı.'}[b.dataset.oa]);
});

/* ---------- sheets and dialogs ---------- */
let lastFocus = null;
function openSheet(html, narrow){
  lastFocus = lastFocus || document.activeElement;
  $('#overlay').innerHTML = `<div class="scrim" data-close></div><div class="sheet ${narrow === true ? 'narrow' : narrow || ''}" role="dialog" aria-modal="true">${html}</div>`;
  $('#overlay').querySelector('.sheet [data-close]')?.focus();
}
function closeSheet(){ ++leadOpenSequence; $('#overlay').innerHTML = ''; sheetKind = null; lastFocus?.focus?.(); lastFocus = null; }
$('#overlay').addEventListener('click', async e => { if (e.target.closest('[data-close]')) closeSheet(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape' && $('#overlay').innerHTML) closeSheet(); });
let sheetKind = null;

function form(title, fields, submitLabel, onSubmit, extra = ''){
  const dlg = $('#dlg');
  dlg.innerHTML = `<form method="dialog" class="dlg-form" novalidate><div class="dlg-head"><h2>${esc(title)}</h2><button class="icon-btn" type="button" data-x aria-label="Kapat"><i class="ph ph-x" aria-hidden="true"></i></button></div>
    ${extra}${fields.map(f => `<div class="field"><label for="f-${f.name}">${esc(f.label)}</label>${f.type === 'textarea'
      ? `<textarea id="f-${f.name}" name="${f.name}" rows="${f.rows || 4}" ${f.required ? 'required' : ''} placeholder="${esc(f.ph || '')}">${esc(f.value || '')}</textarea>`
      : f.type === 'city' ? `<input id="f-${f.name}" name="${f.name}" list="cities" value="${esc(f.value || '')}" ${f.required ? 'required' : ''} placeholder="${esc(f.ph || 'Şehir (isteğe bağlı)')}" autocomplete="off">`
      : f.type === 'number' ? `<input id="f-${f.name}" name="${f.name}" type="number" min="${f.min}" max="${f.max}" value="${esc(f.value ?? '')}">`
      : `<input id="f-${f.name}" name="${f.name}" value="${esc(f.value || '')}" ${f.list ? `list="${f.list}"` : ''} ${f.required ? 'required' : ''} placeholder="${esc(f.ph || '')}" autocomplete="off">`}
      ${f.help ? `<p class="help">${esc(f.help)}</p>` : ''}<p class="err" id="e-${f.name}" hidden></p></div>`).join('')}
    <div class="actions" style="margin-top:6px;padding-top:14px"><button class="btn btn-primary" type="submit">${esc(submitLabel)}</button><button class="btn btn-text" type="button" data-x>Vazgeç</button></div></form>`;
  const f = dlg.querySelector('form');
  dlg.querySelectorAll('[data-x]').forEach(b => b.onclick = () => dlg.close());
  f.onsubmit = async ev => {
    ev.preventDefault();
    const data = Object.fromEntries(new FormData(f));
    let bad = false;
    fields.forEach(fl => {
      const el = $('#e-' + fl.name, dlg), v = String(data[fl.name] || '').trim();
      let msg = '';
      if (fl.required && !v) msg = 'Bu alan boş bırakılamaz.';
      else if (fl.type === 'number') { if (v === '' || +v < fl.min || +v > fl.max) msg = `${fl.min} ile ${fl.max} arasında bir sayı yazın.`; }
      else if (fl.min && v.length < fl.min) msg = `En az ${fl.min} karakter yazın.`;
      el.hidden = !msg; el.textContent = msg; if (msg) bad = true;
    });
    if (bad) { dlg.querySelector('.err:not([hidden])')?.previousElementSibling?.focus?.(); return; }
    const btn = f.querySelector('[type=submit]'); btn.disabled = true;
    const ok = await onSubmit(data);
    btn.disabled = false;
    if (ok !== false) dlg.close();
  };
  dlg.showModal();
  dlg.querySelector('input, textarea')?.focus();
}
function fillCities(){ $('#cities').innerHTML = Object.keys(CITY).sort((a, b) => a.localeCompare(b, 'tr')).map(c => `<option value="${esc(c)}">`).join(''); }

$('#add-opp').addEventListener('click', () => form('Gördüğüm bir şeyi ekle',
  [{name: 'text', label: 'Paylaşımın ya da haberin metni', type: 'textarea', rows: 6, required: true, min: 15, ph: 'X, LinkedIn ya da başka bir yerde gördüğünüz paylaşımı buraya yapıştırın', help: 'Bağlantıdan otomatik okuma yapılmaz; Jeff yalnızca yapıştırdığınız metne bakar ve yıldızını verir.'},
   {name: 'url', label: 'Bağlantı (isteğe bağlı)', ph: 'https://'}],
  'Jeff değerlendirsin', async d => {
    try { const r = await api('opp/manual', d); await refresh(); state.opp = r.opp; state.oppStatus = 'acik'; renderOpps(); toast('Eklendi. Jeff değerlendirdi.'); return true; }
    catch (e) { toast(ERRORS[e.message] || 'Eklenemedi.'); return false; }
  }));
$('#add-lead').addEventListener('click', () => form('Lead ekle',
  [{name: 'name', label: 'İşletme adı', required: true, ph: 'Örn. Kadıköy\'de bir diş kliniği'}, {name: 'city', label: 'Şehir', type: 'city'}, {name: 'sector', label: 'Sektör', ph: 'Örn. Sağlık'},
   {name: 'origin', label: 'Nereden buldunuz?', ph: 'Örn. komşum, LinkedIn, fuar'}, {name: 'note', label: 'Bildiğiniz bir şey', type: 'textarea', rows: 3, help: 'Jeff araştırma notunu yalnızca yazdıklarınıza dayanarak hazırlar.'}],
  'Lead ekle', async d => {
    try {
      const r = await api('lead', d); await refresh(); toast('Lead eklendi.');
      state.leadSec = 'havuz'; state.leadSecSet = true; go('leadler'); openLead(r.lead);
      api(`lead/${r.lead}/research`, {}).then(refresh).catch(() => {});
      return true;
    } catch (e) { toast(ERRORS[e.message] || 'Eklenemedi.'); return false; }
  }));
$('#radar-settings').addEventListener('click', async () => {
  let c;
  try { c = await api('config'); } catch (e) { return toast('Ayarlar okunamadı.'); }
  const L = a => (a || []).join('\n');
  form('Neyi arıyoruz',
    [{name: 'definition', label: 'Jeff neye fırsat, neye haber desin?', type: 'textarea', rows: 7, value: c.definition, help: 'Düz Türkçe yazın. Jeff her taramada bu tarifi okur.'},
     {name: 'feeds', label: 'Takip edilen yayınlar (her satıra bir tane: Ad | adres)', type: 'textarea', rows: 6, value: (c.feeds || []).map(f => `${f.name} | ${f.url}`).join('\n'), help: 'RSS ya da Atom adresi olmalı.'},
     {name: 'github_topics', label: 'GitHub konuları (son bir haftada açılan, yıldız alan depolar)', type: 'textarea', rows: 2, value: L(c.github_topics)},
     {name: 'hn_queries', label: 'Hacker News aramaları (yalnızca topluluğun öne çıkardıkları)', type: 'textarea', rows: 2, value: L(c.hn_queries)},
     {name: 'news_queries', label: 'Google Haberler aramaları', type: 'textarea', rows: 2, value: (c.news_queries || []).map(q => q.q).join('\n')},
     {name: 'telegram_channels', label: 'Açık Telegram kanalları (kanal adı)', type: 'textarea', rows: 2, value: L(c.telegram_channels), help: 'Yalnızca herkese açık kanallar okunur (t.me/s/ada).'},
     {name: 'interval_min', label: 'Kaç dakikada bir taransın?', type: 'number', min: 15, max: 720, value: c.interval_min}],
    'Kaydet', async d => {
      try { await api('config', d); toast('Kaydedildi. Sonraki taramada geçerli olur.'); return true; }
      catch (e) { toast('Kaydedilemedi.'); return false; }
    }, '<p class="help" style="margin:-4px 0 6px">X\'teki önemli gelişmeler AINews özeti üzerinden gelir. X ya da LinkedIn\'de kendiniz gördüğünüz bir şeyi Fırsatlar ekranından ekleyebilirsiniz.</p>');
});
function openScan(pre = {}){
  const u = D.places_usage || {};
  const src = D.places === 'google' ? `Kaynak: Google Haritalar, telefon ve web sitesi de gelir. Bu ay ${u.n} / ${u.cap} ücretsiz arama kullanıldı; sınıra gelince ücret çıkmaması için OpenStreetMap'e geçilir.`
    : u.key ? 'Kaynak: OpenStreetMap. Google Haritalar\'ın bu ayki ücretsiz arama sınırı doldu; ay başında kendiliğinden geri döner.'
    : 'Kaynak: OpenStreetMap (ücretsiz). Türkiye\'de kapsamı dar, telefon bilgisi az gelir.';
  form('İşletme taraması',
    [{name: 'niche', label: 'Hangi işletmeler?', required: true, list: 'niches', value: pre.niche, ph: 'Örn. diş kliniği, kuaför, oto servis'},
     {name: 'city', label: 'Şehir', type: 'city', required: true, value: pre.city, ph: 'Örn. Bursa'},
     {name: 'district', label: 'İlçe (isteğe bağlı)', list: 'districts', value: pre.district, ph: 'Boş bırakırsanız tüm şehir taranır'},
     {name: 'limit', label: 'En çok kaç işletme?', type: 'number', min: 5, max: 200, value: pre.limit || 60}],
    'Taramayı başlat', async d => {
      try {
        const r = await api('jobs', {kind: 'lead_scan', ...d});
        state.radarJob = r.job; knownJobs?.add(r.job); go('komuta');
        startFocus({id: r.job, kind: 'lead_scan', by: 'bilal', status: 'queued', progress: 0, note: 'Tarama başladı', title: `${d.niche} taraması: ${d.district ? d.district + ', ' : ''}${d.city}`,
          params: {city: (Object.keys(CITY).find(c => c.toLocaleLowerCase('tr') === d.city.trim().toLocaleLowerCase('tr')) || d.city), district: d.district}, found: [], log: [], created_at: Math.floor(Date.now() / 1000)});
        await pollJobs();
        return true;
      } catch (e) {
        toast({sehir_ve_sektor: 'Şehri listeden seçin ve işletme türünü yazın.', zaten_calisiyor: 'Aynı tarama zaten sürüyor.'}[e.message] || 'Tarama başlatılamadı.');
        return false;
      }
    }, `<p class="help" style="margin:-4px 0 6px">${src} Bulunan işletmeler Leadler'de "Yeni bulunanlar" listesine düşer; kimseye mesaj gitmez.</p>`);
  const fill = () => { const c = $('#f-city')?.value.trim(); $('#districts').innerHTML = Object.entries(D.districts || {}).filter(([, p]) => p.toLocaleLowerCase('tr') === (c || '').toLocaleLowerCase('tr')).map(([d]) => `<option value="${esc(d)}">`).join(''); };
  $('#f-city')?.addEventListener('input', fill); fill();
}

const stageIdx = s => D.stages.indexOf(s);
/* ---------- Leadler: one queue, one next step per business ---------- */
const GATE = {'geçti': ['Kapıdan geçti', 'strong', '#6EDCB6'], 'şüpheli': ['Şüpheli', 'you', '#F4C27A'], 'elendi': ['Elendi', 'weak', '#8D90A0']};
const leadKind = l => l.category || l.sector || '';
const passed = l => l.gate === 'geçti' || !!l.gate_override;
const analysing = l => (D.jobs || []).some(j => ['analysis', 'marketing'].includes(j.kind) && (j.status === 'running' || j.status === 'queued') && (j.params?.ids || []).includes(l.id));
const qualifying = l => (D.jobs || []).some(j => j.kind === 'qualification' && ['running', 'queued'].includes(j.status) && (j.params?.ids || []).includes(l.id) && !(l.qualification?.current && l.qualification.job_id === j.id));
const LISTS = [['gorusme', 'Görüşme adayları', 'Hedef: hizmetimize ihtiyaç duyabilecek, gerekçesi kaynaklarla desteklenen en fazla 10 firma.'],
  ['kapibekleyen', 'Kapı bekleyen', 'Kalite kapısı sonucu olmayan kayıtlar. Kapı puanlar; hiçbir kaydı silmez.'],
  ['sira', 'Sırada', 'Sizin bir adım atmanızı bekleyenler.'],
  ['havuz', 'Havuz', 'Kapıdan ve analizden geçmeyi bekleyenler. Bu işleri Jeff yapar, siz yalnızca başlatırsınız.'],
  ['bekle', 'Yanıt bekleniyor', 'Mesaj gitti. Takip günü gelince Sırada listesine döner.'],
  ['arsiv', 'Arşiv', 'Kapananlar, kapıda elenenler ve keskin bulgu çıkmadığı için yazılmayanlar.']];

/* The single next step for a lead: the server works it out (briefing.next_step, the same one Jeff and the morning
   message use); the screen only adds what changes between refreshes: a running analysis and the follow-up date. */
function nextStep(l){
  if (qualifying(l)) return {list: 'havuz', rank: 0, text: 'Jeff görüşme gerekçesini sınayıp karşı kanıt arıyor', busy: true};
  if (analysing(l) && !['Gönderildi', 'Yanıt geldi', 'Görüşme', 'Kazanıldı', 'Kapandı'].includes(l.stage) && !l.optout) return {list: 'havuz', rank: 0, text: 'Jeff araştırıyor ve taslak hazırlıyor', busy: true};
  const s = l.step;
  if (s) {
    if (s.list === 'havuz' && !s.busy && analysing(l)) return {list: 'havuz', rank: 0, text: 'Jeff araştırıyor', busy: true};
    if (s.list === 'bekle' && l.follow_at) return {...s, text: 'Takip ' + fmtDay(l.follow_at)};
    return s;
  }
  return localStep(l);
}
function localStep(l){
  const ap = D.approvals.find(a => a.lead_id === l.id && a.status === 'Bekliyor');
  const okAp = D.approvals.find(a => a.lead_id === l.id && a.status === 'Onaylandı');
  const nf = (l.analysis?.bulgular || []).length;
  if (l.stage === 'Kazanıldı') return {list: 'arsiv', text: 'Kazanıldı', tone: 'ok'};
  if (l.optout) return {list: 'arsiv', text: 'Ret listesinde, bir daha yazılmaz'};
  if (l.stage === 'Kapandı') return {list: 'arsiv', text: 'Kapandı'};
  if (l.stage === 'Yanıt geldi') return {list: 'sira', rank: 0, text: 'Yanıt geldi, okuyun', act: ['meeting', 'Görüşme ayarlandı']};
  if (l.stage === 'Görüşme') return {list: 'sira', rank: 1, text: 'Görüşme nasıl geçti?', act: ['won', 'Kazanıldı']};
  if (ap) return {list: 'sira', rank: 2, text: 'Eski taslak onayınızı bekliyor', act: ['appr', 'Taslağı aç']};
  if (okAp) return {list: 'sira', rank: 2, text: 'Onaylı metin gönderilmedi', act: ['sent', 'Gönderdim']};
  if (l.stage === 'Gönderildi') {
    if (l.you?.startsWith('Sinyal yok')) return {list: 'sira', rank: 3, text: 'İki mesaj, iki hafta, ses yok', act: ['lost', 'Kapat']};
    if (l.follow_at && l.follow_at <= Date.now() / 1000) return {list: 'sira', rank: 3, text: 'Takip zamanı geldi', act: ['open', 'Aç']};
    return {list: 'bekle', text: l.follow_at ? 'Takip ' + fmtDay(l.follow_at) : 'Yanıt bekleniyor', act: ['reply', 'Yanıt geldi']};
  }
  if (l.drafts && !(l.contacts || []).length) return {list: 'sira', rank: 4, text: 'Mesaj hazır, gönderin', act: ['open', 'Mesaja geç']};
  if (l.analysis?.karar === 'bulgu_var') return {list: 'sira', rank: 5, text: `${nf} bulgu var, mesajı Jeff yazsın`, act: ['drafts', 'Mesajı yazdır']};
  if (l.analysis?.karar === 'gerek_yok') return {list: 'arsiv', text: 'Keskin bulgu yok, yazılmıyor'};
  if (l.gate === 'elendi' && !l.gate_override) return {list: 'arsiv', text: 'Kapıda elendi'};
  if (analysing(l)) return {list: 'havuz', rank: 0, text: 'Jeff araştırıyor', busy: true};
  if (passed(l)) return {list: 'havuz', rank: 1, text: l.analysis?.karar === 'hata' ? 'Analiz yarım kaldı' : 'Analiz bekliyor', act: ['analyze', 'Analiz et']};
  if (l.gate === 'şüpheli') return {list: 'havuz', rank: 2, text: 'Kapı emin olamadı, karar sizin', act: ['open', 'İncele']};
  return {list: 'havuz', rank: 3, text: 'Kapı bekliyor', act: ['gate-rerun', 'Kapıdan geçir']};
}
const plainReason = t => (t || '').replace('Sitemizdeki bir argümana denk gelen görünür bir dert bulunamadı', 'Bizim çözdüğümüz türden görünür bir dert bulunamadı');
const whyLine = l => l.summary || (l.qualification?.current && l.qualification.hypothesis ? 'İhtiyaç hipotezi: ' + l.qualification.hypothesis : '') || (l.analysis?.bulgular?.length ? 'İş hipotezi: ' + l.analysis.bulgular[0].baslik : '') || l.gate_info?.first_gap || plainReason(l.gate_reasons?.[0]?.text) || leadKind(l) || '';
function candidateSummary(l){
  const full = l.qualification?.hypothesis || l.summary || whyLine(l);
  const text = String(full);
  const colon = text.indexOf(':');
  const start = colon >= 0 && colon < 40 ? text.slice(colon + 1).trim() : text;
  const sentence = start.split(/[.!?](?:\s|$)|[;:]/)[0].trim();
  return sentence.length > 180 ? sentence.slice(0, 180).replace(/\s+\S*$/, '') + '…' : sentence + (sentence ? '.' : '');
}
function renderLeadFilters(){ fillCities(); }  // city and last-scan filters are drawn as removable chips in renderLeads
let leadSearchData = null;
async function loadLeadSearch(){
  if (leadSearchData) return leadSearchData;
  const {leads} = await api('leads/search-data');
  leadSearchData = new Map(leads.map(l => [l.id, l]));
  return leadSearchData;
}
function leadPool(){
  const q = state.q.toLocaleLowerCase('tr');
  return D.leads.filter(l => (state.city === 'all' || l.city === state.city) && (!state.leadJob || l.job === state.leadJob)
    && (!q || [l.name, l.city, l.district, leadKind(l), leadSearchData?.get(l.id)?.note, leadSearchData?.get(l.id)?.address].join(' ').toLocaleLowerCase('tr').includes(q)));
}
function leadRow([l, s]){
  const where = l.district || l.city || '';
  const candidate = state.leadSec === 'gorusme' && l.qualification;
  return `<li class="lrow ${s.list}${s.busy ? ' busy' : ''}">
    ${candidate ? '<div class="lrow-summary">' : ''}
    <button class="lrow-main" type="button" data-lead="${l.id}" title="${esc(l.name)}">
      <span class="lrow-name"><span class="t">${esc(l.short || l.name)}</span>${l.section === 'yeni' ? '<span class="new">yeni</span>' : ''}</span>
      <span class="lrow-why">${esc([where, candidate ? candidateSummary(l) : whyLine(l)].filter(Boolean).join(' · '))}</span>
    </button>
    ${candidate ? `<details class="lrow-reason"><summary>(neden?)</summary><p>${esc(whyLine(l))}</p></details></div>` : ''}
    <span class="lrow-step ${s.tone || ''}">${s.busy ? '<i class="ph ph-circle-notch spin" aria-hidden="true"></i> ' : ''}${esc(s.text)}</span>
    ${s.act ? `<button class="btn ${s.list === 'sira' ? 'btn-primary' : 'btn-glass'} btn-sm" type="button" data-row="${s.act[0]}" data-id="${l.id}">${esc(s.act[1])}</button>` : '<span></span>'}
  </li>`;
}
function renderMetrics(){
  const m = D.metrics, box = $('#lead-metrics');
  if (!m || !box) return;
  const f = m.funnel || [], sc = m.scorecard || {arguments: [], channels: []};
  const pct = (a, b) => b ? Math.round(100 * a / b) + '%' : '';
  const row = r => `<tr><td>${esc(CH_LABEL[r.name] || r.name)}</td><td>${r.contacts}</td><td>${r.opened} <small>${pct(r.opened, r.contacts)}</small></td><td>${r.tried} <small>${pct(r.tried, r.contacts)}</small></td><td>${r.replied} <small>${pct(r.replied, r.contacts)}</small></td><td>${r.won}</td><td>${r.avg_reply_days != null ? r.avg_reply_days + ' gün' : '-'}</td></tr>`;
  const head = '<thead><tr><th></th><th>Temas</th><th>Açtı</th><th>Denedi</th><th>Yanıt</th><th>Kazanıldı</th><th>Ort. yanıt</th></tr></thead>';
  const short = f.filter(x => ['Havuzda', 'Kapıdan geçti', 'Bulgu çıktı', 'Temas edildi', 'Yanıt verdi', 'Kazanıldı'].includes(x.step));
  box.innerHTML = `<details class="fold" ${state.metricsOpen ? 'open' : ''}><summary>Sonuçlar<small>${short.map(x => `${x.n} ${esc(x.step.toLocaleLowerCase('tr'))}`).join(', ')}</small></summary><div class="in">
    <ol class="funnel">${f.map((x, i) => `<li><b>${x.n}</b><span>${esc(x.step)}</span>${i ? `<small>${pct(x.n, f[i - 1].n)}</small>` : ''}</li>`).join('')}</ol>
    ${sc.arguments.length ? `<div class="score"><table class="ltable">${head}<tbody>${sc.arguments.map(row).join('')}</tbody></table>
      <table class="ltable" style="margin-top:10px">${head.replace('<th></th>', '<th>Kanal</th>')}<tbody>${sc.channels.map(row).join('')}</tbody></table></div>
      <p class="help">Bir işletmenin sonucu, ona yapılan ilk mesajın argümanına ve kanalına yazılır. "Açtı" ve "Denedi" kişisel bağlantıdan gelir, çerez kullanılmaz.</p>`
      : '<p class="help">Henüz mesaj gitmedi. İlk mesajlar gittikçe hangi argümanın tıklama, deneme ve yanıt getirdiği burada görünür.</p>'}
    <p class="help">Bu ay Google: ${m.usage?.google_search ?? 0} arama, ${m.usage?.google_details ?? 0} işletme ayrıntısı. İstek sınırları uygulanır; gerçek ücret sağlayıcı hesabından kontrol edilir.</p></div></details>`;
  box.querySelector('details').addEventListener('toggle', e => { state.metricsOpen = e.target.open; });
}
function renderLeads(){
  renderMetrics();
  const all = D.leads.map(l => [l, nextStep(l)]);
  const pool = leadPool().map(l => [l, nextStep(l)]);
  const board = D.meeting_candidates || {ids: [], target: 10, reviewed: 0};
  const of = (rows, k) => k === 'kapibekleyen' ? rows.filter(([l]) => !l.gate) : k === 'gorusme' ? rows.filter(([l]) => board.ids.includes(l.id)).map(([l]) => [l, {list: 'sira', rank: 0, text: 'Görüşme gerekçesini değerlendirin', act: ['open', 'Gerekçeyi incele']}]) : rows.filter(([, s]) => s.list === k);
  const mine = of(all, 'sira').length;
  if (!state.leadSecSet) state.leadSec = 'gorusme';
  if (!LISTS.some(([k]) => k === state.leadSec)) state.leadSec = 'sira';
  $('#lead-sub').textContent = !D.leads.length ? 'Henüz işletme yok.' : mine ? `${mine} işletme sizden bir adım bekliyor.` : 'Şu an sizden bekleyen bir adım yok.';
  $('#lead-sections').innerHTML = LISTS.map(([k, label]) => `<button type="button" role="tab" data-sec="${k}" aria-selected="${state.leadSec === k}">${label}<span class="n">${of(pool, k).length}</span></button>`).join('');
  $('#lead-chips').innerHTML = (state.city !== 'all' ? `<button class="chip" type="button" data-clear="city">${esc(state.city)} <i class="ph ph-x" aria-label="Kaldır"></i></button>` : '')
    + (state.leadJob ? '<button class="chip" type="button" data-clear="job">Son tarama <i class="ph ph-x" aria-label="Kaldır"></i></button>' : '');
  if (!state.loaded) { $('#lead-view').innerHTML = '<div class="lempty">Yükleniyor</div>'; return; }
  if (!D.leads.length) { $('#lead-view').innerHTML = '<div class="lempty"><h3>Henüz işletme yok</h3>"Yeni tarama" ile bir şehirde bir sektörü taratın ya da bildiğiniz bir işletmeyi elle ekleyin.</div>'; return; }
  const rows = of(pool, state.leadSec).sort(([a, s], [b, t]) => (state.leadSec === 'gorusme' ? (b.qualification?.score || 0) - (a.qualification?.score || 0) : ((s.rank ?? 9) - (t.rank ?? 9))) || ((b.updated_at || b.created_at) - (a.updated_at || a.created_at)));
  let top = `<p class="lnote">${LISTS.find(([k]) => k === state.leadSec)[2]}</p>`;
  if (state.leadSec === 'gorusme') {
    const active = (D.jobs || []).find(j => j.kind === 'qualification' && ['queued', 'running'].includes(j.status));
    top += `<div class="lbanner"><p><b>${board.ids.length}/10 görüşme adayı</b> · ${board.reviewed} firma güncel ölçütlerle değerlendirildi. ${active ? esc(active.note || 'Jeff seçimi sürdürüyor.') : 'Eksik yerler zayıf adaylarla doldurulmaz.'}</p><button class="btn btn-primary btn-sm" type="button" data-batch="qualification" ${active ? 'disabled' : ''}>${active ? 'Jeff adayları seçiyor' : 'Jeff görüşme adaylarını seçsin'}</button></div><p class="help">Öneriler ihtiyaç hipotezidir. Puan, görüşme veya satın alma olasılığı değildir. Kimseye mesaj gönderilmez.</p>`;
  }
  if (state.leadSec === 'kapibekleyen') {
    const pending = all.filter(([l]) => !l.gate && l.stage !== 'Kapandı').map(([l]) => l.id);
    const active = (D.jobs || []).some(j => j.kind === 'gate' && ['queued', 'running'].includes(j.status));
    top += `<div class="lbanner"><p><b>${of(all, 'kapibekleyen').length} kayıt</b> kalite kapısının sonucunu bekliyor. Önceden değerlendirilmiş kayıtlar ve kapanan kayıtlar bu işlemde değişmez.</p><button class="btn btn-glass btn-sm" type="button" data-batch="gate" data-ids="${pending.join(',')}" ${active || !pending.length ? 'disabled' : ''}>${active ? 'Kapı değerlendiriyor' : 'Kapıdan geçmemişleri değerlendir'}</button></div>`;
  }
  if (state.leadSec === 'havuz') {
    const toAnalyze = all.filter(([, s]) => s.act?.[0] === 'analyze').map(([l]) => l.id);
    const toGate = all.filter(([, s]) => s.act?.[0] === 'gate-rerun').length;
    const busy = all.filter(([, s]) => s.busy).length;
    const parts = [];
    if (toAnalyze.length) parts.push(`<div class="lbanner"><p><b>${toAnalyze.length} işletme</b> analiz bekliyor. Jeff sırayla araştırır, her biri birkaç dakika sürer. Mesaj gitmez.</p><button class="btn btn-primary btn-sm" type="button" data-batch="analysis" data-ids="${toAnalyze.slice(0, 50).join(',')}">Hepsini analiz et</button></div>`);
    if (toGate) parts.push(`<div class="lbanner"><p><b>${toGate} işletme</b> kapıdan geçmedi.</p><button class="btn btn-glass btn-sm" type="button" data-batch="gate">Kapıdan geçir</button></div>`);
    if (busy) parts.push(`<p class="lnote"><i class="ph ph-circle-notch spin" aria-hidden="true"></i> Jeff şu an ${busy} işletmeyi araştırıyor. İlerleme Radar ekranında.</p>`);
    top += parts.join('');
  }
  if (!rows.length) {
    const EMPTY = {kapibekleyen: ['Kapı kuyruğu boş', 'Kalite kapısı sonucu olmayan kayıt yok.'], gorusme: ['Henüz güçlü görüşme adayı yok', 'Jeff güncel resmî kaynakları inceler, hizmet uyumunu ve somut iş yükünü sınar. Yetersiz kanıtlı firmalar bu listeye girmez.'], sira: ['Sizden bekleyen bir şey yok', 'Jeff analizleri bitirdikçe mesajı hazır işletmeler buraya düşer.'],
      havuz: ['Havuz boş', 'Yeni işletme bulmak için bir tarama başlatın.'], bekle: ['Yanıt bekleyen mesaj yok', 'Gönderdiğiniz mesajlar burada takip edilir.'],
      arsiv: ['Arşiv boş', 'Kapanan ve elenen işletmeler burada durur.']}[state.leadSec];
    $('#lead-view').innerHTML = top + `<div class="lempty"><h3>${EMPTY[0]}</h3>${state.q || state.city !== 'all' || state.leadJob ? 'Arama ya da süzgeç yüzünden boş olabilir.' : EMPTY[1]}</div>`;
    return;
  }
  state.leadOrder = rows.map(([l]) => l.id);
  $('#lead-view').innerHTML = top + `<ul class="lrows">${rows.map(leadRow).join('')}</ul>`;
}
$('#lead-sections').addEventListener('click', e => { const b = e.target.closest('[data-sec]'); if (b) { state.leadSec = b.dataset.sec; state.leadSecSet = true; renderLeads(); } });
$('#lead-chips').addEventListener('click', e => {
  const b = e.target.closest('[data-clear]'); if (!b) return;
  if (b.dataset.clear === 'city') state.city = 'all'; else state.leadJob = null;
  renderLeads();
});
$('#lead-q').addEventListener('input', async e => { state.q = e.target.value; renderLeads(); if (state.q) { try { await loadLeadSearch(); renderLeads(); } catch (_) { toast('Arama ayrıntıları yüklenemedi.'); } } });
$('#lead-view').addEventListener('click', async e => {
  const bt = e.target.closest('[data-batch]');
  if (bt) {
    bt.disabled = true;
    if (bt.dataset.batch === 'qualification') {
      const keyName = 'cgos-qualification-batch';
      let key = sessionStorage.getItem(keyName);
      if (!key) { key = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join(''); sessionStorage.setItem(keyName, key); }
      try { const r = await api('jobs', {kind: 'qualification', request_key: key}); sessionStorage.removeItem(keyName); state.radarJob = r.job; toast('Jeff görüşme gerekçelerini araştırıyor. Mesaj gönderilmeyecek.'); pollJobs(); await refresh(); }
      catch (err) { bt.disabled = false; toast('Seçim başlatılamadı: ' + err.message); }
      return;
    }
    if (bt.dataset.batch === 'analysis') {
      const ids = (bt.dataset.ids || '').split(',').filter(Boolean);
      try { const r = await api('jobs', {kind: 'analysis', ids}); state.radarJob = r.job; toast(`Jeff ${ids.length} işletmeyi sırayla analiz edecek. İlerleme Radar ekranında.`); pollJobs(); }
      catch (err) { bt.disabled = false; toast(err.message === 'zaten_calisiyor' ? 'Bu analiz zaten sürüyor.' : 'Analiz başlatılamadı.'); }
    } else {
      try { const r = await api('jobs', {kind: 'gate', ...(bt.dataset.ids ? {ids: bt.dataset.ids.split(',').filter(Boolean)} : {})}); state.radarJob = r.job; toast('Kapı çalışıyor. İlerleme Radar ekranında.'); pollJobs(); }
      catch (err) { bt.disabled = false; toast({zaten_calisiyor: 'Kapı zaten çalışıyor.', bekleyen_yok: 'Kapıdan geçmeyi bekleyen işletme yok.'}[err.message] || 'Kapı başlatılamadı.'); }
    }
    return;
  }
  const rb = e.target.closest('[data-row]'); if (!rb) return;
  const id = rb.dataset.id, a = rb.dataset.row;
  if (a === 'open') return openLead(id);
  if (a === 'appr') return openApprovals();
  if (a === 'drafts') { rb.disabled = true; rb.textContent = 'Jeff yazıyor'; }
  await leadAction(a, undefined, id);
  renderLeads();  // also puts a button back when the step failed
});

let openLeadId = null;
const leadDetails = new Map();
let leadOpenSequence = 0;
async function loadLeadDetail(id, force = false){
  const row = D.leads.find(x => x.id === id);
  if (!row) throw new Error('yok');
  if (!force && leadDetails.get(id)?.updated_at === row.updated_at) return {...row, ...leadDetails.get(id)};
  const {lead} = await api(`lead/${encodeURIComponent(id)}/detail`);
  if (!lead || lead.id !== id) throw new Error('yok');
  leadDetails.set(id, lead);
  return {...row, ...lead};
}
function fullLead(id){ return {...D.leads.find(x => x.id === id), ...leadDetails.get(id)}; }
const linkCache = {};  // kept for the old personal-link action
const VERDICT = {bulgu_var: ['Bulgu var', 'strong'], gerek_yok: ['Kayda değer bulgu yok', 'weak'], hata: ['Tamamlanamadı', 'you']};
const argTitle = id => (D.arguments || []).find(a => a.id === id)?.title || id;
const CH_LABEL = {whatsapp: 'WhatsApp', instagram: 'Instagram', email: 'E-posta', form: 'Site formu'};
let contactTab = {};
const useSel = {};  // findings Bilal ticked for the message, per lead
const LB = (la, t, cls = 'btn-text', extra = '') => `<button class="btn ${cls} btn-sm" type="button" data-la="${la}" ${extra}>${t}</button>`;
const LP = (la, t, extra) => LB(la, t, 'btn-primary', extra);

/* ---------- one lead, one screen: İşletme · Jeff'in raporu · Raporu özelleştir ---------- */
function leadSide(l, s){
  const web = safeUrl(l.website), where = [l.district, l.city].filter(Boolean).join(', ');
  let host = ''; try { host = web ? new URL(web).hostname.replace(/^www\./, '') : ''; } catch (e) {}
  const tel = l.phone ? l.phone.replace(/[^\d+]/g, '') : '';
  const ext = 'target="_blank" rel="noopener noreferrer"';
  const row = (icon, html) => `<li><i class="ph ${icon}" aria-hidden="true"></i><span>${html}</span></li>`;
  const facts = [
    tel && row('ph-phone', `<a href="tel:${esc(tel)}">${esc(l.phone)}</a>${l.wa ? ' <small>WhatsApp var</small>' : ' <small>sabit hat</small>'}`),
    l.email && row('ph-envelope-simple', `<a href="mailto:${esc(l.email)}">${esc(l.email)}</a>`),
    l.instagram && row('ph-instagram-logo', `<a href="https://instagram.com/${encodeURIComponent(l.instagram)}" ${ext}>@${esc(l.instagram)}</a>`),
    web && row('ph-globe', `<a href="${esc(web)}" ${ext}>${esc(host || 'Web sitesi')}</a>`),
    (l.address || where) && row('ph-map-pin', `${esc(l.address || where)}${l.lat && l.lon ? ` <a href="https://www.google.com/maps/search/?api=1&query=${+l.lat},${+l.lon}" ${ext}>Harita</a>` : ''}`)].filter(Boolean).join('');
  const planned = l.follow_at && l.follow_at > Date.now() / 1000 ? l.follow_at : null;
  let acts = '';
  if (l.stage === 'Yanıt geldi') acts = LP('meeting', 'Görüşme ayarlandı') + LB('lost', 'Olmadı, kapat');
  else if (l.stage === 'Görüşme') acts = LP('won', 'Kazanıldı') + LB('lost', 'Kaybedildi');
  else if (l.stage === 'Gönderildi') acts = LP('reply', 'Yanıt geldi') + LB('snooze', '3 gün ertele') + (l.you?.startsWith('Sinyal yok') ? LB('lost', 'Sinyal yok, kapat') : '');
  else if (!['Kapandı', 'Kazanıldı'].includes(l.stage)) acts = LB('close', 'İlgilenmiyorum');
  return `<section class="wcol side" aria-label="İşletme">
    <h3 class="wh">İşletme</h3>
    <ul class="lfacts">${facts || '<li><span>İletişim bilgisi yok.</span></li>'}</ul>
    <div class="lstate"><p class="kicker">Durum</p><p class="st ${s.list}">${s.busy ? '<i class="ph ph-circle-notch spin" aria-hidden="true"></i> ' : ''}${esc(s.text)}</p>${acts ? `<div class="row">${acts}</div>` : ''}</div>
    <label class="kicker" for="lnote">Notunuz</label>
    <textarea class="note" id="lnote" placeholder="Bu işletme hakkında bildiğiniz bir şey">${esc(l.note)}</textarea>
    <div class="row remind">${[[2, '2 gün sonra hatırlat'], [7, '1 hafta sonra']].map(([d, t]) => `<button class="chip" type="button" data-follow="${d}">${t}</button>`).join('')}${l.follow_at ? '<button class="chip" type="button" data-follow="0">Hatırlatmayı kaldır</button>' : ''}</div>
    ${planned ? `<p class="help">Hatırlatma: ${fmtDay(planned)}. Yalnızca size haber verir.</p>` : ''}
    <details class="mini"><summary>Geçmiş (${l.events.length})</summary><ol class="tl">${l.events.map(([ts, t, x]) => `<li class="real" style="--c:#A2BCE7"><b>${esc(t)}</b><span>${fmtDate(ts)}${x ? ', ' + esc(x) : ''}</span></li>`).join('')}</ol></details>
    <details class="mini"><summary>Diğer işlemler</summary><div class="row">
      ${LB('edit', '<i class="ph ph-pencil-simple" aria-hidden="true"></i>Bilgileri düzenle', 'btn-glass')}
      ${l.optout ? '' : LB('optout', 'Bir daha yazma (ret listesi)')}</div>
      <div class="field" style="margin-top:10px"><label for="lstage">Aşamayı elle değiştir</label>
        <select class="stage-select" id="lstage">${D.stages.concat(['Kapandı']).map(x => `<option ${x === l.stage ? 'selected' : ''}>${x}</option>`).join('')}</select></div>
    </details>
  </section>`;
}
function reportCol(l, s){
  const a = l.analysis, ext = 'target="_blank" rel="noopener noreferrer"';
  const reasons = (l.gate_reasons || []).map(r => plainReason(r.text)).join(' ');
  let body;
  if (l.marketing?.source === 'qualification' || l.drafts?.source === 'qualification' || (l.qualification?.current && l.qualification.decision === 'gorusme_adayi')) body = '<p class="help">İlk temas taslağı güncel aday raporundaki kanıtlara bağlanır. İşletmenin iç düzeni ve gerçek ihtiyaç görüşmede doğrulanmalı.</p>';
  else if (s.busy) body = '<p class="empty-note"><i class="ph ph-circle-notch spin" aria-hidden="true"></i> Jeff araştırıyor. Birkaç dakika sürer, bitince rapor burada çıkar.</p>';
  else if (!a) {
    if (l.gate === 'elendi' && !l.gate_override) body = `<p class="empty-note">Kapıda elendi: ${esc(reasons)}</p>${LP('gate-override', 'Yine de araştırılsın')}`;
    else if (l.gate === 'şüpheli' && !l.gate_override) body = `<p class="empty-note">Kapı emin olamadı: ${esc(reasons)}</p>${LP('gate-override', 'Yine de araştırılsın')}`;
    else if (!l.gate) body = `<p class="empty-note">İlk temas taslağı için ön kontrol bekleniyor.</p>${LP('gate-rerun', 'Ön kontrolden geçir')}`;
    else body = `<p class="empty-note">Jeff firmanın resmî kaynaklarını inceler. Kaynağı denetlenmiş bulgulardan kişiye özel ilk mesaj taslakları hazırlar; yeterli bulgu yoksa mesaj yazmaz.</p>${LP('prepare', 'Jeff incelesin ve taslak hazırlasın')}${LB('analyze', 'Yalnız araştır')}`;
  } else {
    const f = a.bulgular || [];
    const sel = useSel[l.id] || l.drafts?.use || f.slice(0, 2).map((_, i) => i);
    body = f.length ? `<ol class="finds2">${f.map((x, i) => `<li>
        <label class="use"><input type="checkbox" data-use="${i}" ${sel.includes(i) ? 'checked' : ''}> Mesajda kullan</label>
        <h4>İş hipotezi: ${esc(x.baslik)}</h4>
        <blockquote>"${esc(x.alinti)}"</blockquote>
        <p class="src">${esc(x.kaynak?.label || 'Kaynak')}${safeUrl(x.kaynak?.url) ? ` · <a href="${esc(x.kaynak.url)}" ${ext}>Kaynakta gör</a>` : ''}${x.kaynak?.observed_at ? ` · ${fmtDate(x.kaynak.observed_at)}` : ''}</p>
        ${(x.notlar || []).map(n => `<p class="warn"><i class="ph ph-warning" aria-hidden="true"></i>${esc(n)}</p>`).join('')}
        ${x.gordugumuz || x.olasi_maliyet ? `<details><summary>Ayrıntı</summary>${x.gordugumuz ? `<p>Jeff’in yorumu: ${esc(x.gordugumuz)}</p>` : ''}${x.olasi_maliyet ? `<p>İş varsayımı: ${esc(x.olasi_maliyet)}</p>` : ''}</details>` : ''}
      </li>`).join('')}</ol>
      <p class="help">Göndermeden önce bulguya bir kez kendiniz bakın: kliniğe yanlış bir şey söylemek ilk izlenimi bozar.</p>`
      : `<p class="empty-note">${esc(a.gerekce || (a.karar === 'gerek_yok' ? 'Jeff nokta atışı bir bulgu görmedi. Kural gereği bu işletmeye yazılmaz.' : 'Rapor tamamlanamadı.'))}</p>`;
    body += `<div class="row" style="margin-top:12px">${LP('prepare', 'Jeff yeniden incelesin ve yazsın')}${LB('analyze', 'Yalnız araştır')}<span class="help" style="margin:0">${fmtDate(a.at)}</span></div>`;
  }
  const m = l.marketing;
  if (m) {
    const seconds = Object.values(m.steps || {}).reduce((sum, x) => sum + (x.elapsed_seconds || 0), 0);
    body += `<p class="help" aria-live="polite">${esc(m.note || 'İnceleme ve taslak görevi')}${seconds ? ` · ${Math.round(seconds)} saniye` : ''}. Kaynakta bulunan alıntı denetlenir; firmanın ihtiyacı varsayımdır.</p>`;
  }
  return `<section class="wcol report" aria-label="Jeff'in raporu"><h3 class="wh">Jeff'in raporu ${a ? `<span class="tag ${VERDICT[a.karar][1]}">${VERDICT[a.karar][0]}</span>` : ''}</h3>${qualificationCol(l)}${body}</section>`;
}
function qualificationCol(l){
  const q = l.qualification;
  const action = qualifying(l) ? '<p class="help">Jeff görüşme gerekçesini inceliyor.</p>' : LP('qualify', 'Görüşme gerekçesini Jeff araştırsın') + (q?.current && q.decision === 'gorusme_adayi' && !analysing(l) ? LP('prepare-qualified', 'Güncel kanıttan taslak hazırlasın') : '');
  if (!q) return `<div class="reviewbox"><h4>Görüşmeye değer mi?</h4><p class="help">Somut iş yükü, hizmet uyumu ve güncel işletme kanalı birlikte değerlendirilir.</p>${action}</div>`;
  const labels = {service_fit: 'Hizmet uyumu', need_signal: 'İhtiyaç işareti', timing: 'Zamanlama', reachability: 'Ulaşılabilirlik'};
  return `<div class="reviewbox"><h4>${q.current ? q.decision === 'gorusme_adayi' ? 'Görüşme adayı' : 'Güçlü aday için kanıt yetersiz' : 'Değerlendirme güncelliğini kaybetti'}</h4>
    <p class="help">Öncelik puanı ${q.score}/90 · ${Object.entries(q.dimensions || {}).map(([k, v]) => esc(labels[k] || k) + ': ' + v).join(' · ')}. Bu bir başarı olasılığı değildir.</p>
    <p><b>İhtiyaç hipotezi:</b> ${esc(q.hypothesis || 'Yeterli gerekçe yok.')}</p><p>${esc(q.reason)}</p>
    <p><b>Neden şimdi?</b> ${esc(q.why_now)}</p><p><b>Görüşmede sor:</b> ${esc(q.discovery_question)}</p>
    ${q.adversarial ? `<div class="reviewbox"><h4>Karşıt karar kontrolü · ${q.adversarial.status === 'completed' ? 'Tamamlandı' : 'Eksik'}</h4><p><b>Alternatif açıklama:</b> ${esc(q.adversarial.alternative_explanation)}</p><p><b>Kanıtın sınırı:</b> ${esc(q.adversarial.evidence_limit)}</p><p><b>Tekliften ne zaman vazgeçeriz?</b> ${esc(q.adversarial.disconfirming_observation)}</p><p class="help">${esc(q.adversarial.scope)}</p></div>` : '<p class="help">Önceki ayrı eleştirel okuma mevcut; genişletilmiş karşıt karar kontrolü için yeniden inceleme gerekli.</p>'}
    <details class="mini"><summary>Instagram incelemesi</summary>${(q.instagram || []).length ? q.instagram.map(ig => `<p><a href="${esc(ig.profile)}" target="_blank" rel="noopener noreferrer">${esc(ig.profile)}</a> · ${ig.status === 'readable' ? 'Herkese açık profil metni okundu' : 'İçerik okunamadı; akış bilinmiyor'}</p><p class="help">Hesap işletmenin sitesinden bağlandı. ${esc(ig.limitation || 'Profil içeriği, iç mesaj trafiğini ve yanıt süresini kanıtlamaz.')}</p>${ig.meta_error_code === 190 ? '<p class="help">Meta erişim anahtarı reddedildi. Bağlantı yeniden yetkilendirilmeli; bu, firmanın Instagram’da olmadığı anlamına gelmez.</p>' : ''}`).join('') : '<p class="help">Okunan resmî sayfalarda doğrulanabilir Instagram profil bağlantısı bulunamadı. Bu, hesabın olmadığı anlamına gelmez.</p>'}</details>
    ${q.contact ? `<p><b>İşletmenin yayımladığı kanal:</b> ${esc(q.contact.value)}. Karar vericiye ulaşım ve kanalın çalışması teyit edilmedi.</p>` : '<p class="help">Güncel resmî işletme kanalı doğrulanamadı.</p>'}
    <details class="mini"><summary>Kaynaklar, karşı kanıt ve bilinmeyenler</summary><ol class="evidence">${(q.facts || []).map(f => `<li><p>${esc(f.quote)}</p>${safeUrl(f.url) ? `<a href="${esc(f.url)}" target="_blank" rel="noopener noreferrer">Resmî kaynağı aç</a>` : ''}<p class="help">${fmtDate(f.observed_at)} · ${q.supported_ids?.includes(f.id) ? 'Jeff ayrı okumada dayanak olarak değerlendirdi' : 'Öncelik kararına dayanak yapılmadı'}</p></li>`).join('')}</ol><ul>${(q.unknowns || []).map(x => `<li>${esc(x)}</li>`).join('')}</ul></details>${action}</div>`;
}
function messageCol(l){
  if (l.marketing?.source === 'qualification' || l.drafts?.source === 'qualification' || (l.qualification?.current && l.qualification.decision === 'gorusme_adayi' && !l.drafts)) return qualifiedMessageCol(l);
  const a = l.analysis, d = l.drafts, sent = l.contacts || [];
  const head = '<h3 class="wh">Raporu özelleştir</h3>';
  if (analysing(l)) return `<section class="wcol msg">${head}<p class="empty-note">Jeff çalışıyor. İnceleme ve taslak tamamlandığında burada değerlendirebilirsiniz.</p></section>`;
  if (l.optout) return `<section class="wcol msg">${head}<p class="empty-note">Bu işletme ret listesinde. Kendisine bir daha yazılmaz.</p></section>`;
  if (!a || a.karar !== 'bulgu_var') return `<section class="wcol msg">${head}<p class="empty-note">${a ? 'Keskin bulgu olmadığı için mesaj yazılmaz.' : 'Jeff raporu yazınca mesajı buradan hazırlarsınız.'}</p></section>`;
  const wish = `<label class="kicker" for="jnote">Jeff'e notunuz (isteğe bağlı)</label>
    <input class="field-input" id="jnote" maxlength="300" placeholder="Örn. daha samimi yaz, pazar gününe değin" value="${esc(d?.note || '')}">
    <div class="row" style="margin-top:10px">${d ? LB('drafts', 'Seçimlerle yeniden yaz', 'btn-glass') : LP('drafts', 'Mesajı Jeff yazsın')}</div>`;
  if (!d) return `<section class="wcol msg">${head}<p class="help" style="margin:0 0 12px">Rapordan mesajda kullanılacak bulguları seçin. Jeff her kanal için kısa bir ilk mesaj yazar, sonunda firmaya özel kısa bağlantı olur. Hiçbir mesaj kendiliğinden gitmez.</p>${wish}</section>`;
  const tabs = ['whatsapp', 'instagram', 'email'].concat(l.form ? ['form'] : []);
  const can = {whatsapp: !!l.wa, instagram: !!l.instagram, email: true, form: !!l.form};
  const tab = contactTab[l.id] || (l.wa ? 'whatsapp' : l.email ? 'email' : l.instagram ? 'instagram' : l.form ? 'form' : 'whatsapp');
  const done = ch => sent.some(c => c.channel === ch);
  const notes = (d.notes?.[tab === 'email' || tab === 'form' ? 'email_govde' : tab] || []).map(n => `<p class="warn"><i class="ph ph-warning" aria-hidden="true"></i>${esc(n)}</p>`).join('');
  const text = {whatsapp: d.whatsapp, instagram: d.instagram, email: d.email_govde, form: d.email_govde}[tab];
  const sentBtn = ch => LB(`sent-${{whatsapp: 'wa', instagram: 'ig', form: 'form'}[ch]}`, done(ch) ? 'Gönderildi ✓' : 'Gönderdim', 'btn-glass', done(ch) ? 'disabled' : '');
  const go = {
    whatsapp: l.wa ? LP('wa-open', '<i class="ph ph-whatsapp-logo" aria-hidden="true"></i>WhatsApp\'ta aç') + sentBtn('whatsapp') : '<p class="help" style="margin:0">Numara sabit hat, WhatsApp açılamaz. Başka bir kanal seçin.</p>',
    instagram: l.instagram ? LP('ig-open', '<i class="ph ph-instagram-logo" aria-hidden="true"></i>Kopyala, DM\'yi aç') + sentBtn('instagram') : '<p class="help" style="margin:0">Instagram hesabı bulunamadı.</p>',
    email: LP('mail-send', `<i class="ph ph-paper-plane-tilt" aria-hidden="true"></i>${done('email') ? 'E-posta gönderildi' : 'E-postayı gönder'}`, done('email') ? 'disabled' : ''),
    form: LP('form-open', '<i class="ph ph-browser" aria-hidden="true"></i>Kopyala, siteyi aç') + sentBtn('form')}[tab];
  return `<section class="wcol msg">${head}
    <details class="mini wishbox" ${d.note ? 'open' : ''}><summary>Jeff'e not ve yeniden yazdırma</summary>${wish}</details>
    <div class="chan" role="group" aria-label="Kanal">${tabs.map(c => `<button type="button" data-ctab="${c}" aria-pressed="${tab === c}" class="${can[c] ? '' : 'off'}">${CH_LABEL[c]}${done(c) ? ' ✓' : ''}</button>`).join('')}</div>
    ${tab === 'email' ? `<div class="mailhead"><input class="field-input" id="c-to" value="${esc(l.email || '')}" placeholder="Alıcı: ornek@isletme.com" aria-label="Alıcı"><input class="field-input" id="c-subject" value="${esc(d.email_konu)}" aria-label="Konu"></div>` : ''}
    <label class="sr-only" for="c-text">Mesaj</label><textarea class="draft" id="c-text">${esc(text)}</textarea>${notes}
    ${l.marketing?.current ? `<div class="reviewbox"><p class="help">${esc({'accepted': 'Bu metni uygun buldunuz.', 'rejected': 'Bu metni uygun bulmadınız.', 'edited': 'Düzenleme kaydedildi; metni yeniden değerlendirin.'}[l.marketing.review?.decision] || 'Taslağı ve dayandığı bulguları inceleyin. Değerlendirmeniz gönderim yapmaz.')}</p>
      <div class="row">${LP('review-accept', 'Uygun buldum')}${LB('review-reject', 'Uygun değil')}${LB('review-edit', 'Düzenlemeyi kaydet', 'btn-glass', tab !== 'whatsapp' ? 'disabled title="İlk pilotta WhatsApp taslağı düzenlenir"' : '')}</div></div>` : ''}
    <div class="row send2">${go}${LB('copy-text', '<i class="ph ph-copy" aria-hidden="true"></i>Kopyala')}</div>
    <p class="help">${{whatsapp: 'Kendi WhatsApp\'ınızda metin yazılı açılır; gönderen sizsiniz.', instagram: 'Metin panoya kopyalanır, DM penceresine yapıştırırsınız.',
      email: 'info@cybergene.co adresinden gider, kopyası info@ kutusuna düşer. Altına "bir daha yazmayın" satırı eklenir.', form: 'Metin kopyalanır, site açılır; iletişim formuna yapıştırıp gönderin.'}[tab]}</p>
    ${sent.length ? `<ul class="contact-log">${sent.map(c => `<li>${CH_LABEL[c.channel]}, ${fmtDate(c.at)}</li>`).join('')}</ul>` : ''}
  </section>`;
}
function qualifiedMessageCol(l){
  const m = l.marketing || {}, d = l.drafts || {};
  const ready = m.current && m.published_at && d.marketing_job === m.job_id;
  const candidate = l.qualification?.current && l.qualification.decision === 'gorusme_adayi';
  const historical = m.published_at && d.marketing_job === m.job_id;
  const status = analysing(l) ? 'Jeff kaynakları ve taslağın iddialarını denetliyor.' : m.current
    ? {'accepted': 'Taslağı uygun buldunuz. Gönderim yapılmadı.', 'rejected': 'Taslağı uygun bulmadınız. Jeff’e not verip yeniden hazırlatabilirsiniz.'}[m.review?.decision] || 'Taslak ve karşıt inceleme hazır; değerlendirmeniz bekleniyor.'
    : m.stale_reason || (m.status === 'failed' ? m.note || 'Taslak denetlenemedi; hazır olarak işaretlenmedi.' : 'Güncel aday raporundaki kaynaklardan tek ilk temas taslağı hazırlanır.');
  const audit = m.audit;
  return `<section class="wcol msg" aria-label="Kaynaklı ilk temas taslağı"><h3 class="wh">İlk temas taslağı</h3>
    <p class="help" aria-live="polite">${esc(status)}</p>
    ${analysing(l) ? '<p class="empty-note">Bittiğinde metin ve dayanakları burada görünecek.</p>' : ''}
    ${historical ? `<label class="kicker" for="c-text">${ready ? 'Jeff’in hazırladığı metin' : 'Önceki metin · yeniden inceleme gerekli'}</label><textarea class="draft" id="c-text" readonly>${esc(d.whatsapp || '')}</textarea>
      <p><b>Önerilen görev:</b> ${esc(d.scope)}</p><p><b>Mevcut çözüm:</b> ${esc(d.known_counter)}</p>` : ''}
    ${audit ? `<div class="reviewbox"><h4>Taslağın karşıt incelemesi · ${audit.approved === true ? 'Uygun bulundu' : 'Uygun bulunmadı'}</h4>
      <p>${esc(audit.reason)}</p><p><b>Alternatif açıklama:</b> ${esc(audit.alternative_explanation)}</p>
      <p><b>Kanıtın sınırı:</b> ${esc(audit.evidence_limit)}</p><p><b>Tekliften ne zaman vazgeçeriz?</b> ${esc(audit.disconfirming_condition)}</p>
      <p class="help">Jeff’in ayrı oturumdaki eleştirel okumasıdır; bağımsız saha doğrulaması ve kullanıcı kabulü değildir.</p>
      ${(audit.unsupported_claims || []).length ? `<ul>${audit.unsupported_claims.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}</div>` : ''}
    ${ready ? `<details class="mini" open><summary>Cümle ve kanıt eşleşmesi</summary><ol class="evidence">${(d.claim_audit || []).map(c => `<li><p>${esc(c.claim)}</p>${c.fact_ids.map(id => `<span class="tag">Kaynak ${id + 1}</span>`).join(' ')}</li>`).join('')}</ol>
      <ol class="evidence">${(m.evidence || []).map(f => `<li><b>Kaynak ${f.id + 1}</b><blockquote>${esc(f.quote)}</blockquote>${safeUrl(f.url) ? `<a href="${esc(f.url)}" target="_blank" rel="noopener noreferrer">Kaynağı aç</a>` : ''}<p class="help">${fmtDate(f.observed_at)} · Yayıncı beyanı; alıntının kaynakta bulunduğu denetlendi.</p></li>`).join('')}</ol></details>
      <div class="reviewbox"><p class="help">Değerlendirmeniz gönderim yapmaz. Metinde değişiklik için Jeff’e not verin; yeni taslak yeniden karşıt incelemeden geçer.</p>
        <div class="row">${LP('review-accept', 'Uygun buldum')}${LB('review-reject', 'Uygun değil')}${LB('copy-text', 'Metni kopyala', 'btn-glass')}</div></div>` : ''}
    ${m.source_check?.verified_at ? `<p class="help" data-source-check>Taslak öncesi kaynak denetimi: ${fmtDate(m.source_check.verified_at)}. Rapor yenilendiğinde, geçerliliğini kaybettiğinde veya hizmet kapsamı değiştiğinde eski taslak yeniden inceleme gerektirir.</p>` : ''}
    ${candidate && !analysing(l) && !l.optout ? `<label class="kicker" for="q-draft-note">Jeff’e üslup notunuz (isteğe bağlı)</label><input class="field-input" id="q-draft-note" maxlength="300" value="${esc(d.note || '')}" placeholder="Örn. daha kısa ve doğrudan yaz"><div class="row">${LP('prepare-qualified', historical ? 'Güncel kanıttan yeniden hazırlasın' : 'Güncel kanıttan taslak hazırlasın')}</div>` : ''}
  </section>`;
}
async function openLead(id){
  if (!D.leads.some(x => x.id === id)) return;
  const sequence = ++leadOpenSequence;
  openLeadId = id;
  openSheet('<div class="sheet-head"><h2>İşletme yükleniyor</h2><button class="icon-btn" type="button" data-close aria-label="Kapat">Kapat</button></div><p class="help" aria-live="polite">Rapor ve taslak okunuyor.</p>', 'lead');
  sheetKind = 'lead';
  let l;
  try { l = await loadLeadDetail(id, true); }
  catch (error) {
    if (sequence === leadOpenSequence && sheetKind === 'lead') {
      openSheet(`<div class="sheet-head"><h2>İşletme okunamadı</h2><button class="icon-btn" type="button" data-close aria-label="Kapat">Kapat</button></div><button class="btn btn-glass" type="button" data-lead="${esc(id)}">Yeniden dene</button>`, 'lead');
      sheetKind = 'lead';
    }
    return;
  }
  if (sequence !== leadOpenSequence || sheetKind !== 'lead' || openLeadId !== id) return;
  if (!l.reviewed) { l.reviewed = true; api(`lead/${id}/review`, {}).then(() => refresh()).catch(() => {}); }
  const s = nextStep(l);
  const order = state.leadOrder || [], i = order.indexOf(id);
  const nav = i >= 0 && order.length > 1 ? `<span class="pager">${i + 1} / ${order.length}</span>
    <button class="icon-btn" type="button" data-nav="-1" aria-label="Önceki işletme" ${i === 0 ? 'disabled' : ''}><i class="ph ph-caret-left" aria-hidden="true"></i></button>
    <button class="icon-btn" type="button" data-nav="1" aria-label="Sonraki işletme" ${i === order.length - 1 ? 'disabled' : ''}><i class="ph ph-caret-right" aria-hidden="true"></i></button>` : '';
  openSheet(`
    <div class="sheet-head">
      <div>
        <p class="kicker">${esc([leadKind(l), [l.district, l.city].filter(Boolean).join(', ')].filter(Boolean).join(' · ') || 'İşletme')}</p>
        <h2>${esc(l.name)}</h2>
      </div>
      <div class="row head-acts">${nav}<button class="icon-btn" type="button" data-close aria-label="Kapat"><i class="ph ph-x" aria-hidden="true"></i></button></div>
    </div>
    <div class="sheet-body work">${leadSide(l, s)}${reportCol(l, s)}${messageCol(l)}</div>`, decisionFirst(l) ? 'lead decision-first' : 'lead');
  if (decisionFirst(l)) organizeDecisionCard(l);
}
// Source-qualified drafts share the same decision view; keep every report and action.
function decisionFirst(l){
  return l.marketing?.source === 'qualification' || l.drafts?.source === 'qualification';
}
function organizeDecisionCard(l){
  const body = $('#overlay .sheet-body'), report = body.querySelector('.report'), msg = body.querySelector('.msg'), side = body.querySelector('.side');
  const fold = title => {
    const el = document.createElement('details'); el.className = 'fold decision-fold';
    const summary = document.createElement('summary'); summary.textContent = title;
    const content = document.createElement('div'); content.className = 'in';
    el.append(summary, content); return [el, content];
  };
  const top = document.createElement('section'); top.className = 'decision-top';
  top.innerHTML = `<p class="decision-reason">${esc(candidateSummary(l))}</p>`;
  const heading = msg.querySelector('h3'); top.append(heading);
  const text = msg.querySelector('#c-text');
  if (text) {
    const preview = document.createElement('p'); preview.className = 'decision-preview';
    // Quote the draft's closing question; never replace the complete copyable text.
    const sentences = text.value.trim().split(/(?<=[.!?])\s+/);
    preview.textContent = sentences[sentences.length - 1]; top.append(preview);
  }
  const actions = msg.querySelector('[data-la="review-accept"]')?.closest('.row');
  if (actions) { actions.classList.add('decision-actions'); top.append(actions); }
  const status = msg.querySelector('[aria-live]'); if (status) top.append(status);
  const [why, whyContent] = fold('Neden bu?');
  const [proof, proofContent] = fold('Kanıt?');
  // Every original evidence disclosure is retained, inside one closed outer disclosure.
  for (const section of [report, msg]) {
    for (const detail of section.querySelectorAll('details.mini')) {
      detail.open = true; proofContent.append(detail);
    }
  }
  const checked = msg.querySelector('[data-source-check]'); if (checked) proofContent.append(checked);
  const [full, fullContent] = fold('Taslağın tamamı');
  if (text) { fullContent.append(msg.querySelector('label[for="c-text"]'), text); }
  const [info, infoContent] = fold('İşletme bilgileri ve notlar'); infoContent.append(side);
  whyContent.append(report, msg);
  body.replaceChildren(top, ...(text ? [full] : []), why, proof, info);
}
async function showEvidence(id){
  const box = $('#evidence-list'); if (!box) return;
  box.innerHTML = '<p class="help">Yükleniyor</p>';
  try {
    const {evidence} = await api(`lead/${id}/evidence`);
    box.innerHTML = evidence.length ? `<ol class="evidence">${evidence.map(e => `<li${e.suspicious ? ' class="sus"' : ''}><details><summary><b>${esc(e.label)}</b><span>${fmtDate(e.fetched_at)}${e.expires_at ? ', ' + fmtDay(e.expires_at) + ' tarihinde silinir' : ''}</span>${e.suspicious ? '<span class="tag you">Talimata benzeyen ifade</span>' : ''}</summary>
        <p>${esc(e.text.slice(0, 1200))}${e.text.length > 1200 ? '…' : ''}</p>${safeUrl(e.url) ? `<a href="${esc(e.url)}" target="_blank" rel="noopener noreferrer">Kaynağı aç <i class="ph ph-arrow-up-right" aria-hidden="true"></i></a>` : ''}</details></li>`).join('')}</ol>
      <p class="help">Bu metinler işletmenin sitesinden ve Google'dan alınmış veridir; talimat olarak işlenmez. Google yorumları 30 gün sonra silinir.</p>`
      : '<p class="help">Saklanan kanıt yok. Google yorumlarının süresi dolmuş olabilir; "Kapıdan yeniden geçir" ile tazeleyebilirsiniz.</p>';
  } catch (e) { box.innerHTML = '<p class="help">Kanıtlar okunamadı.</p>'; }
}
function editLead(l){
  form('Bilgileri düzenle',
    [{name: 'name', label: 'İşletme adı', required: true, value: l.name}, {name: 'sector', label: 'Sektör', value: leadKind(l)},
     {name: 'city', label: 'Şehir', type: 'city', value: l.city}, {name: 'district', label: 'İlçe', value: l.district},
     {name: 'phone', label: 'Telefon', value: l.phone}, {name: 'website', label: 'Web sitesi', value: l.website, ph: 'https://'},
     {name: 'email', label: 'E-posta', value: l.email}, {name: 'address', label: 'Adres', value: l.address}],
    'Kaydet', async d => {
      try { await api(`lead/${l.id}/update`, d); await refresh(); if (openLeadId === l.id && $('#overlay .sheet')) openLead(l.id); toast('Kaydedildi.'); return true; }
      catch (e) { toast('Kaydedilemedi.'); return false; }
    });
}
async function leadAction(a, extra, id = openLeadId){
  const y = $('#overlay .sheet-body')?.scrollTop || 0;
  const done = async () => { await refresh(); if (openLeadId === id && $('#overlay .sheet')) { await openLead(id); const b = $('#overlay .sheet-body'); if (b && openLeadId === id) b.scrollTop = y; } };
  try {
    const draft = $('#ldraft')?.value;
    const actionSequence = leadOpenSequence;
    const L = await loadLeadDetail(id, true);
    if (actionSequence !== leadOpenSequence) return;
    if (a === 'edit') return editLead(L);
    if (a === 'evidence') return showEvidence(id);
    const txt = () => ($('#c-text')?.value || '').trim();
    if (a === 'qualify') {
      const keyName = `cgos-qualify-${id}`;
      let key = sessionStorage.getItem(keyName);
      if (!key) { key = Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join(''); sessionStorage.setItem(keyName, key); }
      const r = await api(`lead/${id}/qualify`, {request_key: key}); sessionStorage.removeItem(keyName); state.radarJob = r.job; pollJobs(); await done(); return;
    }
    if (a === 'prepare' || a === 'prepare-qualified') {
      const keyName = `cgos-${a}-${id}`;
      let requestKey = sessionStorage.getItem(keyName);
      if (!requestKey) {
        requestKey = typeof crypto.randomUUID === 'function' ? crypto.randomUUID()
          : Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, '0')).join('');
        sessionStorage.setItem(keyName, requestKey);
      }
      try {
        const r = await api(`lead/${id}/${a}`, {request_key: requestKey, ...(a === 'prepare-qualified' ? {note: ($('#q-draft-note')?.value || '').trim()} : {})});
        sessionStorage.removeItem(keyName);
        state.radarJob = r.job; knownJobs?.add(r.job);
        toast('Görevin durumunu ve sonucunu bu firma kartından görebilirsiniz.'); pollJobs();
      } catch (e) { toast(e.detail || 'İnceleme başlatılamadı.'); return; }
      return done();
    }
    if (['review-accept', 'review-reject', 'review-edit'].includes(a)) {
      // Only a saved version can be accepted. Edits first invalidate the old decision.
      const tab = L.drafts?.source === 'qualification' ? 'whatsapp' : contactTab[id] || (L.wa ? 'whatsapp' : L.email ? 'email' : L.instagram ? 'instagram' : L.form ? 'form' : 'whatsapp');
      const stored = {whatsapp: L.drafts?.whatsapp, instagram: L.drafts?.instagram, email: L.drafts?.email_govde, form: L.drafts?.email_govde}[tab];
      if (a === 'review-accept' && (txt() !== (stored || '').trim() || (tab === 'email' && $('#c-subject')?.value !== L.drafts.email_konu))) return toast('Önce düzenlemeyi kaydedin, sonra güncel taslağı değerlendirin.');
      try {
        await api(`lead/${id}/draft-review`, {digest: L.marketing?.digest, decision: {'review-accept': 'accepted', 'review-reject': 'rejected', 'review-edit': 'edited'}[a], text: txt()});
        toast(a === 'review-edit' ? 'Düzenleme kaydedildi. Önceki değerlendirme geçersiz; güncel metni inceleyin.' : 'Değerlendirmeniz kaydedildi.');
      } catch (e) { toast(e.detail || 'Değerlendirme kaydedilemedi.'); return; }
      return done();
    }
    if (a === 'drafts') {
      toast('Jeff taslakları yazıyor; yarım dakika kadar sürebilir.');
      const L0 = L;
      const use = useSel[id] || L0?.drafts?.use || (L0?.analysis?.bulgular || []).slice(0, 2).map((_, i) => i);
      if (openLeadId === id && $('#overlay .sheet') && !use.length) return toast('Mesaj için en az bir bulgu seçin.');
      try { await api(`lead/${id}/drafts`, {use, note: ($('#jnote')?.value || L0?.drafts?.note || '').trim()}); toast('Mesaj hazır. Okuyun, gerekirse düzeltin.'); }
      catch (e) { toast(e.detail || 'Taslaklar yazılamadı.'); return; }
      return done();
    }
    if (a === 'wa-open') { window.open(`https://wa.me/${L.wa}?text=${encodeURIComponent(txt())}`, '_blank', 'noopener'); return toast('WhatsApp açıldı. Gönderdikten sonra "Gönderdim" deyin.'); }
    if (a === 'ig-open') { try { await navigator.clipboard.writeText(txt()); } catch (e) {} window.open(`https://ig.me/m/${encodeURIComponent(L.instagram)}`, '_blank', 'noopener'); return toast('Metin kopyalandı, DM penceresi açıldı. Gönderdikten sonra "Gönderdim" deyin.'); }
    if (a === 'copy-text') { try { await navigator.clipboard.writeText(txt()); toast('Metin kopyalandı.'); } catch (e) { toast('Kopyalanamadı; metni seçip kopyalayın.'); } return; }
    if (a === 'form-open') { try { await navigator.clipboard.writeText(txt()); } catch (e) {} const w = safeUrl(L.website); if (w) window.open(w, '_blank', 'noopener'); return toast('Metin kopyalandı, site açıldı. Formdan gönderdikten sonra "Gönderdim" deyin.'); }
    if (a === 'sent-wa' || a === 'sent-ig' || a === 'sent-form') {
      try { await api(`lead/${id}/contacted`, {channel: {'sent-wa': 'whatsapp', 'sent-ig': 'instagram', 'sent-form': 'form'}[a], text: txt()}); toast('Kaydedildi. 3 gün sonra takip hatırlatması kuruldu.'); }
      catch (e) { toast(e.detail || 'Kaydedilemedi.'); return; }
      return done();
    }
    if (a === 'mail-send') {
      const to = ($('#c-to')?.value || '').trim(), subject = ($('#c-subject')?.value || '').trim();
      if (!confirm(`Bu e-posta şimdi info@cybergene.co adresinden ${to} adresine gidecek.\n\nKonu: ${subject}\n\nGönderilsin mi?`)) return;
      try { const r = await api(`lead/${id}/email`, {to, subject, body: txt()}); toast('E-posta gönderildi. Kaydı kartta duruyor; kopyası info@ kutusunda.'); }
      catch (e) { toast(e.detail || 'E-posta gönderilemedi.'); return; }
      return done();
    }
    if (a === 'optout') {
      const reason = prompt('Bu işletme ret listesine alınacak; bir daha yazılmayacak. Nedeni (isteğe bağlı):', 'Çıkar dedi');
      if (reason === null) return;
      await api(`lead/${id}/optout`, {reason}); toast('Ret listesine alındı.'); closeSheet(); return refresh();
    }
    if (a === 'analyze') {
      try { await api(`lead/${id}/analyze`, {}); toast('Jeff analize başladı. Birkaç dakika sürebilir; bitince burada görünür.'); pollJobs(); }
      catch (e) {
        if (e.message === 'analiz_hazir_degil') toast(e.detail || 'Analiz modu hazır değil.');
        else toast(e.message === 'kapi' ? 'Analiz yalnızca kapıdan geçen işletmeler için yapılır.' : 'Analiz başlatılamadı.');
        return;
      }
      return done();
    }
    if (a === 'observe') {
      const text = ($('#obs-text')?.value || '').trim();
      if (text.length < 15) return toast('Biraz daha uzun bir metin yapıştırın.');
      await api(`lead/${id}/observe`, {text, url: ($('#obs-url')?.value || '').trim()});
      toast('Gözlem eklendi. Kapı yeniden değerlendiriyor.'); setTimeout(done, 8000); pollJobs(); return;
    }
    if (a === 'gate-override') { await api(`lead/${id}/gate-override`, {}); toast('Havuza alındı. Gerekçe geçmişe yazıldı.'); }
    else if (a === 'gate-rerun') { await api(`lead/${id}/gate-rerun`, {}); toast('Kapıdan geçiriliyor. Birkaç saniye içinde sonuç burada görünür.'); setTimeout(done, 9000); pollJobs(); }
    else
    if (a === 'link') { const r = await api(`lead/${id}/link`, {argument: extra}); linkCache[id] = {url: r.url, arg: extra}; toast('Bağlantı hazır. Kopyalayıp mesajınıza ekleyebilirsiniz.'); }
    else if (a === 'copy-link') { await navigator.clipboard.writeText(linkCache[id]?.url || ''); return toast('Bağlantı kopyalandı.'); }
    else
    if (a === 'research') { toast('Jeff not hazırlıyor...'); await api(`lead/${id}/research`, {}); toast('Araştırma notu hazır.'); }
    else if (a === 'draft') { toast('Jeff yazıyor...'); await api(`lead/${id}/draft`, {channel: extra}); toast('Taslak hazır.'); }
    else if (a === 'save-draft') { await api(`lead/${id}/update`, {draft}); toast('Taslak kaydedildi.'); }
    else if (a === 'to-approval') {
      if (!(draft || '').trim()) return toast('Önce bir taslak yazın ya da Jeff\'e yazdırın.');
      await api(`lead/${id}/to-approval`, {text: draft}); toast('Onaylar listesine eklendi.');
    }
    else if (a === 'sent') {
      const okAp = D.approvals.find(x => x.lead_id === id && x.status === 'Onaylandı');
      if (okAp) await api(`approval/${okAp.id}/sent`, {}); else await api(`lead/${id}/sent`, {});
      toast('Gönderildi olarak kaydedildi, 3 gün sonra takip hatırlatması kuruldu.');
    }
    else if (a === 'reply') { await api(`lead/${id}/reply`, {}); toast('Yanıt geldi olarak işaretlendi.'); }
    else if (a === 'snooze') { await api(`lead/${id}/update`, {follow_days: 3}); toast('3 gün sonrasına ertelendi.'); }
    else if (a === 'close') { await api(`lead/${id}/update`, {stage: 'Kapandı', reason: 'İlgilenilmedi'}); toast('Kapananlar listesine taşındı.'); closeSheet(); return refresh(); }
    else if (a === 'meeting' || a === 'won' || a === 'lost') {
      const stage = {meeting: 'Görüşme', won: 'Kazanıldı', lost: 'Kapandı'}[a];
      const reason = prompt({meeting: 'Görüşme ne zaman, nasıl? (kısa not)', won: 'Ne kazanıldı? (ör. pilot başladı)', lost: 'Neden kapanıyor? (ör. sinyal yok, ilgilenmedi)'}[a], a === 'lost' && L?.you?.startsWith('Sinyal yok') ? 'Sinyal yok: iki temas, iki hafta' : '');
      if (reason === null) return;
      await api(`lead/${id}/update`, {stage, reason}); toast({meeting: 'Görüşme aşamasına alındı.', won: 'Kazanıldı olarak işaretlendi.', lost: 'Kapatıldı; gerekçe geçmişe yazıldı.'}[a]);
      if (a !== 'meeting') { closeSheet(); return refresh(); }
    }
    else if (a === 'channel') { await api(`lead/${id}/update`, {channel: extra}); }
    else if (a === 'follow') { await api(`lead/${id}/update`, {follow_days: +extra}); }
    else if (a === 'stage') {
      const reason = prompt('Aşama değişikliğinin gerekçesi (geçmişe yazılır):', '');
      if (reason === null) { const sel = $('#lstage'); if (sel) sel.value = L.stage; return; }
      await api(`lead/${id}/update`, {stage: extra, reason}); if (extra === 'Kapandı' || extra === 'Kazanıldı') { closeSheet(); return refresh(); }
    }
    else if (a === 'note') { await api(`lead/${id}/update`, {note: extra}); await refresh(); return; }
    await done();
  } catch (e) { toast(ERRORS[e.message] || 'İşlem tamamlanamadı, tekrar deneyin.'); }
}
$('#overlay').addEventListener('click', async e => {
  if (sheetKind !== 'lead') return;
  const nv = e.target.closest('[data-nav]'); if (nv) return stepLead(+nv.dataset.nav);
  const b = e.target.closest('[data-la]');
  if (b) { if (b.dataset.la === 'focus-contact') return $('#overlay .contact')?.scrollIntoView({behavior: 'smooth'}); return leadAction(b.dataset.la, b.dataset.la === 'draft' ? ($('.channel [data-channel][aria-pressed=true]')?.dataset.channel || 'WhatsApp') : b.dataset.la === 'link' ? b.dataset.arg : undefined); }
  const c = e.target.closest('[data-channel]'); if (c) return leadAction('channel', c.dataset.channel);
  const ct = e.target.closest('[data-ctab]'); if (ct) { contactTab[openLeadId] = ct.dataset.ctab; const y = $('#overlay .sheet-body')?.scrollTop || 0; await openLead(openLeadId); const sb = $('#overlay .sheet-body'); if (sb) sb.scrollTop = y; return; }
  const f = e.target.closest('[data-follow]'); if (f) return leadAction('follow', f.dataset.follow);
});
$('#overlay').addEventListener('change', e => {
  if (sheetKind !== 'lead') return;
  if (e.target.id === 'lstage') return leadAction('stage', e.target.value);
  if (e.target.matches('[data-use]')) useSel[openLeadId] = [...document.querySelectorAll('#overlay [data-use]:checked')].map(x => +x.dataset.use);
});
function stepLead(dir){
  const o = state.leadOrder || [], i = o.indexOf(openLeadId);
  if (i < 0 || !o[i + dir]) return;
  openLead(o[i + dir]);
}
document.addEventListener('keydown', e => {
  if (sheetKind !== 'lead' || e.target.closest?.('input, textarea, select') || e.altKey || e.ctrlKey || e.metaKey) return;
  if (e.key === 'ArrowRight') stepLead(1);
  if (e.key === 'ArrowLeft') stepLead(-1);
});
$('#overlay').addEventListener('focusout', e => { if (sheetKind === 'lead' && e.target.id === 'lnote') { const l = fullLead(openLeadId); if (l && l.note !== e.target.value) leadAction('note', e.target.value); } });

/* ---------- Haberler: the AI world, ranked by importance ---------- */
function renderNews(){
  const day = Date.now() / 1000 - 48 * 3600;
  const basis = D.news.filter(n => (n.ts || 0) >= day).sort((x, y) => (y.stars - x.stars) || (y.ts - x.ts)).slice(0, 25);
  $('#news-sub').textContent = D.radar.last_run ? `Yapay zekâ dünyasında son iki günde olanlar, Jeff'in dilinden. Son derleme ${ago(D.radar.last_run)}.` : 'Radar çalışınca Jeff burada günün özetini yazar.';
  $('#digest').innerHTML = D.digest ? esc(D.digest) : (state.loaded ? 'Henüz özet yok. Radar haber bulunca Jeff burada günün özetini yazar.' : 'Yükleniyor');
  $('#news-basis').hidden = !basis.length;
  $('#news-n').textContent = basis.length ? basis.length + ' başlık' : '';
  $('#news-list').innerHTML = basis.map(n => `<li>${safeUrl(n.url) ? `<a href="${esc(n.url)}" target="_blank" rel="noopener noreferrer">${esc(n.title)}</a>` : esc(n.title)}<small>${esc(n.src)}, ${ago(n.ts)}</small></li>`).join('');
  $('#idea-text').textContent = D.idea || 'Haberler gelince Jeff burada bir paylaşım fikri önerir.';
  $('#idea-actions').hidden = !D.idea;
}
$('#idea-approve').addEventListener('click', async () => { const d = await act('idea/approve', {}, 'Taslak Onaylar listesine eklendi.'); if (d) openApprovals(); });

/* ---------- Onaylar ---------- */
function openApprovals(){
  sheetKind = 'appr';
  const list = D.approvals;
  openSheet(`<div class="sheet-head"><div><p class="kicker">Sizin onayınızla gider</p><h2>Onaylar</h2></div><button class="icon-btn" type="button" data-close aria-label="Kapat"><i class="ph ph-x" aria-hidden="true"></i></button></div>
    <div style="overflow-y:auto"><div class="appr">${list.length ? list.map(a => `<div class="aitem ${a.status !== 'Bekliyor' && a.status !== 'Onaylandı' ? 'done' : ''}" data-a="${a.id}">
      <span class="m">${esc(a.channel)} <span class="tag ${a.status === 'Onaylandı' ? 'strong' : ''}">${esc(a.status)}</span></span>
      <h3>${esc(a.target)}</h3>
      ${a.status === 'Bekliyor' ? `<label class="sr-only" for="at-${a.id}">Taslak</label><textarea class="draft" id="at-${a.id}" style="min-height:110px">${esc(a.text)}</textarea>` : `<p>${esc(a.text)}</p>`}
      <div class="actions">${a.status === 'Bekliyor' ? `<button class="btn btn-primary btn-sm" type="button" data-act="approve">Onayla</button><button class="btn btn-text btn-sm" type="button" data-act="reject">Reddet</button>`
        : a.status === 'Onaylandı' ? `<button class="btn btn-glass btn-sm" type="button" data-act="copy">Metni kopyala</button><button class="btn btn-primary btn-sm" type="button" data-act="sent">Gönderdim</button>` : ''}</div>
      ${a.status === 'Onaylandı' ? '<p class="help">Panel mesaj göndermez. Metni kopyalayıp kendiniz gönderin, sonra "Gönderdim" deyin.</p>' : ''}
    </div>`).join('') : '<div class="empty"><h3>Onay bekleyen bir şey yok</h3>Bir fırsattan ya da lead\'den taslağı onaya gönderince burada görünür.</div>'}</div></div>`, true);
}
$('#overlay').addEventListener('click', async e => {
  if (sheetKind !== 'appr') return;
  const b = e.target.closest('[data-act]'); if (!b) return;
  const box = b.closest('[data-a]'), id = box.dataset.a, a = D.approvals.find(x => x.id === id);
  try {
    if (b.dataset.act === 'copy') { await navigator.clipboard.writeText(a.text); return toast('Metin kopyalandı.'); }
    if (b.dataset.act === 'approve') { const t = $('#at-' + id)?.value; if (t !== undefined && t !== a.text) await api(`approval/${id}/edit`, {text: t}); }
    await api(`approval/${id}/${b.dataset.act}`, {});
    toast({approve: 'Onaylandı. Şimdi metni kopyalayıp kendiniz gönderin.', reject: 'Reddedildi.', sent: 'Gönderildi olarak kaydedildi, 3 gün sonra takip hatırlatması kuruldu.'}[b.dataset.act]);
    await refresh(); openApprovals();
  } catch (err) { toast('İşlem tamamlanamadı, tekrar deneyin.'); }
});
$('#open-appr').addEventListener('click', openApprovals);

/* ---------- Komut paleti ---------- */
let palIdx = 0;
function cmds(){
  return [
    {t: 'Komuta ekranı', i: 'ph-compass', f: () => go('komuta')}, {t: 'Radar', i: 'ph-crosshair', f: () => go('radar')}, {t: 'Fırsatlar', i: 'ph-lightbulb', f: () => go('firsatlar')},
    {t: 'Leadler', i: 'ph-users-three', f: () => go('leadler')}, {t: 'Haberler (günün özeti)', i: 'ph-newspaper', f: () => go('haberler')},
    {t: 'Onaylar', i: 'ph-seal-check', f: openApprovals}, {t: 'İşletme taraması', i: 'ph-storefront', f: () => openScan()},
    {t: 'Haber ve fırsat taraması', i: 'ph-arrow-clockwise', f: () => $('#run-radar').click()},
    ...D.leads.map(l => ({t: 'Lead: ' + l.name, i: 'ph-user', f: () => { go('leadler'); openLead(l.id); }}))
  ];
}
function renderPal(){
  const q = $('#pal-q').value.trim().toLocaleLowerCase('tr');
  const list = cmds().filter(c => !q || c.t.toLocaleLowerCase('tr').includes(q));
  const askItem = q ? [{t: 'Jeff\'e sor: ' + $('#pal-q').value.trim(), i: 'ph-sparkle', f: () => { go('komuta'); ask($('#pal-q').value.trim()); }}] : [];
  const all = [...askItem, ...list].slice(0, 9);
  palIdx = Math.min(palIdx, all.length - 1);
  $('#pal-list').innerHTML = all.map((c, n) => `<li><button type="button" class="${n === palIdx ? 'is-active' : ''}" data-n="${n}"><i class="ph ${c.i}" aria-hidden="true"></i>${esc(c.t)}</button></li>`).join('');
  $('#pal-list').onclick = e => { const b = e.target.closest('[data-n]'); if (b) { $('#palette').close(); all[+b.dataset.n].f(); } };
  $('#pal-q').onkeydown = e => {
    if (e.key === 'ArrowDown') { palIdx = Math.min(palIdx + 1, all.length - 1); renderPal(); e.preventDefault(); }
    if (e.key === 'ArrowUp') { palIdx = Math.max(palIdx - 1, 0); renderPal(); e.preventDefault(); }
    if (e.key === 'Enter' && all[palIdx]) { e.preventDefault(); $('#palette').close(); all[palIdx].f(); }
  };
}
function openPal(){ $('#pal-q').value = ''; palIdx = 0; renderPal(); $('#palette').showModal(); $('#pal-q').focus(); }
$('#pal-q').addEventListener('input', () => { palIdx = 0; renderPal(); });
$('#open-cmd').addEventListener('click', openPal);
document.addEventListener('keydown', e => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openPal(); } });

/* ---------- start ---------- */
if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
go(location.hash.slice(1) || 'komuta');
renderAll();
refresh().then(() => { loadGeo(); loadGoogle(); pollJobs(); });
setInterval(() => { if (!document.hidden && !$('#dlg').open) refresh(); }, 45000);
