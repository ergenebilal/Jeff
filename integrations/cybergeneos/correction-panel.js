'use strict';
/* Private, explicit selection. No chat interception, persistence or actions. */
(() => {
  const mount = document.querySelector('#jeff .tools');
  if (!mount || document.getElementById('correction-open')) return;
  const style = document.createElement('link'); style.rel = 'stylesheet';
  style.href = new URL('correction-panel.css', document.currentScript?.src || location.href).href;
  document.head.append(style);
  const button = document.createElement('button');
  button.id = 'correction-open'; button.type = 'button'; button.className = 'btn btn-text btn-sm';
  button.textContent = 'Düzeltme'; mount.append(button);
  const dialog = document.createElement('dialog');
  dialog.id = 'correction-dialog'; dialog.className = 'dlg'; dialog.setAttribute('aria-label', 'İşe bağlı düzeltme');
  dialog.innerHTML = `<form class="dlg-form" novalidate>
    <div class="dlg-head"><h2>İşe bağlı düzeltme</h2><button type="button" class="btn btn-text" data-close>Kapat</button></div>
    <p class="help">Bir özel taslak ve bir hafıza kaynağı seç. Düzeltmen yalnız bu seçim için incelenir.</p>
    <div class="field"><label for="correction-query">Hafızada ara</label><input id="correction-query" maxlength="2000" autocomplete="off" placeholder="Ne hakkında?"></div>
    <div class="actions"><button type="button" class="btn btn-sm" data-search>İşleri ve kaynakları getir</button><button type="button" class="btn btn-text btn-sm" data-more hidden>Diğer işler</button></div>
    <div class="field"><label for="correction-task">Özel taslak</label><select id="correction-task" disabled><option value="">Önce kayıtları getir</option></select></div>
    <div class="field"><label for="correction-source">Hafıza kaynağı</label><select id="correction-source" disabled><option value="">Önce kayıtları getir</option></select></div>
    <p class="help" data-source-note></p>
    <div class="actions"><button type="button" class="btn btn-sm" data-select disabled>Bu seçimle devam et</button></div>
    <div class="field"><label for="correction-text">Düzeltmen</label><input id="correction-text" maxlength="600" autocomplete="off" disabled></div>
    <div class="actions"><button type="submit" class="btn btn-primary" data-submit disabled>Öneriyi incele</button></div>
    <p class="help" data-state role="status" aria-live="polite"></p>
    <div data-result hidden><h3>Düzeltme önerisi</h3><p data-correction></p><p class="help" data-review></p><p class="help">Kalıcı hafızaya yazılmadı. İş yeniden çalıştırılmadı.</p></div>
  </form>`;
  document.body.append(dialog);
  const find = selector => dialog.querySelector(selector);
  const query = find('#correction-query'), task = find('#correction-task'), source = find('#correction-source');
  const text = find('#correction-text'), select = find('[data-select]'), submit = find('[data-submit]');
  const search = find('[data-search]'), more = find('[data-more]'), status = find('[data-state]');
  let sequence = 0, ticket = null, pending = null, expiry = null, nextOffset = null, activeQuery = '', sourceRows = [];
  const stamp = value => Number.isFinite(value) && value > 0
    ? new Date(value * 1000).toLocaleString('tr-TR', {day:'numeric', month:'long', hour:'2-digit', minute:'2-digit'}) : 'Tarihi bilinmiyor';
  const resetContext = () => {
    sequence++; pending?.abort(); pending = null; ticket = null; clearTimeout(expiry);
    search.disabled = false; more.disabled = false;
    text.disabled = true; submit.disabled = true; find('[data-result]').hidden = true;
  };
  const closeRemote = () => fetch('/api/correction/close', {method:'POST', credentials:'same-origin',
    headers:{'Content-Type':'application/json'}, body:'{}', keepalive:true}).catch(() => {});
  async function request(action, body, attempt) {
    const controller = new AbortController(); pending = controller;
    const timer = setTimeout(() => controller.abort(), 25000);
    try {
      const response = await fetch('/api/correction/' + action, {method:'POST', credentials:'same-origin',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify(body), signal:controller.signal});
      const data = await response.json();
      if (attempt !== sequence || !dialog.open) return null;
      if (!response.ok) throw new Error(response.status === 401 || response.status === 403 ? 'giris' : 'baglanti');
      return data;
    } finally { clearTimeout(timer); if (pending === controller) pending = null; }
  }
  const error = value => value.message === 'giris' ? 'Girişini doğrulayıp yeniden aç.'
    : value.name === 'AbortError' ? 'Yanıt zamanında gelmedi. Seçimi yeniden doğrula.' : 'Kayıtlar okunamadı. Öneri hazırlanmadı.';
  function options(field, rows, value, label, empty) {
    field.replaceChildren(new Option(empty, ''));
    rows.forEach(row => field.add(new Option(label(row), value(row))));
    field.disabled = rows.length === 0;
  }
  function updateSelection() {
    resetContext(); text.value = ''; closeRemote(); status.textContent = 'Seçim değişti; yeniden doğrula.';
    select.disabled = !(task.value && source.value);
    const row = sourceRows.find(row => row.source === source.value);
    find('[data-source-note]').textContent = !row ? '' : row.declared_date?.state === 'declared'
      ? `Kaynağın bildirdiği tarih: ${row.declared_date.value}. Güncel doğruluğu doğrulanmadı.`
      : 'Kaynağın tarihi bilinmiyor. Güncel bilgi sayılmayacak.';
  }
  async function choices(offset = 0) {
    if (!query.value.trim()) { status.textContent = 'Aramak istediğin konuyu yaz.'; return; }
    resetContext(); text.value = ''; find('[data-source-note]').textContent=''; closeRemote(); const attempt = sequence; search.disabled = true; more.disabled = true;
    select.disabled = true; task.disabled = true; source.disabled = true; status.textContent = 'Kayıtlar okunuyor…';
    try {
      const data = await request('choices', {query:query.value.trim(), offset}, attempt);
      if (!data) return;
      if (data.status !== 'choices_ready' || data.read_only !== true || !Array.isArray(data.tasks) || !Array.isArray(data.sources)) throw new Error('baglanti');
      activeQuery = query.value.trim(); nextOffset = Number.isInteger(data.next_offset) ? data.next_offset : null;
      sourceRows = data.sources;
      options(task, data.tasks, row => row.task_id, row => `Özel taslak · ${stamp(row.created_at)}`, 'Bir iş seç');
      options(source, data.sources, row => row.source, row => row.label, 'Bir kaynak seç');
      more.hidden = nextOffset === null;
      status.textContent = data.tasks.length === 0 ? 'Bu sayfada seçilebilen özel taslak yok.'
        : data.sources.length === 0 ? 'Bu aramada doğrulanmış kaynak bulunamadı.'
        : 'Listelenen taslaklar tamamlandı sayılmaz. İş ve kaynak ilişkisini sen seçiyorsun.';
      find('[data-source-note]').textContent = data.memory_list_partial ? 'Kaynak listesi kısmi; aramanı daraltabilirsin.' : '';
    } catch (value) { if (attempt === sequence && dialog.open) status.textContent = error(value); }
    finally { if (attempt === sequence) { search.disabled = false; more.disabled = false; } }
  }
  select.addEventListener('click', async () => {
    if (!task.value || !source.value) return;
    resetContext(); const attempt = sequence; select.disabled = true; search.disabled = true; more.disabled = true;
    task.disabled = true; source.disabled = true; status.textContent = 'Seçilen iş ve kaynak yeniden doğrulanıyor…';
    try {
      const data = await request('select', {task_id:task.value, source:source.value}, attempt);
      if (!data) return;
      if (data.status !== 'selection_ready' || typeof data.context_ticket !== 'string') {
        status.textContent = 'Seçilen iş veya kaynak doğrulanamadı. Öneri hazırlanmadı.'; return;
      }
      ticket = data.context_ticket; text.disabled = false; submit.disabled = false; text.focus();
      status.textContent = 'Düzeltmeni normal Türkçeyle yaz. Bu bağlantı beş dakika geçerli.';
      expiry = setTimeout(() => { resetContext(); closeRemote(); status.textContent = 'Seçimin süresi doldu. Yeniden doğrula.'; }, 300000);
    } catch (value) { if (attempt === sequence && dialog.open) status.textContent = error(value); }
    finally { if (attempt === sequence) { select.disabled = !(task.value && source.value); search.disabled = false; more.disabled = false; task.disabled = false; source.disabled = false; } }
  });
  find('form').addEventListener('submit', async event => {
    event.preventDefault(); if (!ticket || !text.value.trim() || text.disabled || submit.disabled) return;
    const attempt = sequence; submit.disabled = true; text.disabled = true; status.textContent = 'Düzeltmenin dayanağı yeniden okunuyor…';
    try {
      const data = await request('correct', {context_ticket:ticket, user_message:text.value}, attempt);
      if (!data) return;
      if (!['candidate_only','requires_source_review'].includes(data.status) || !data.candidate
          || data.rule_applied !== false || data.memory_write_authorized !== false
          || data.candidate.owner_correction !== text.value.trim() || data.candidate.source !== source.value
          || data.candidate.task_binding?.request_id !== task.value) {
        ticket = null; text.disabled = true; status.textContent = 'Bağlantı veya dayanak değişti. Seçimi yeniden doğrula.'; return;
      }
      find('[data-correction]').textContent = data.candidate.owner_correction;
      find('[data-review]').textContent = data.status === 'requires_source_review'
        ? 'Kaynak tarihi veya içeriği ayrıca incelenmeli. Bu öneri henüz uygulanmadı.' : 'Yalnız seçtiğin iş için öneri. Henüz uygulanmadı.';
      find('[data-result]').hidden = false; status.textContent = 'Öneri hazır; kalıcı bir değişiklik yapılmadı.';
    } catch (value) { if (attempt === sequence && dialog.open) { ticket = null; text.disabled = true; status.textContent = error(value); } }
    finally { if (attempt === sequence) { submit.disabled = !ticket; text.disabled = !ticket; } }
  });
  search.addEventListener('click', () => choices());
  more.addEventListener('click', () => { if (nextOffset !== null && query.value.trim() === activeQuery) choices(nextOffset); });
  task.addEventListener('change', updateSelection); source.addEventListener('change', updateSelection);
  query.addEventListener('input', () => { resetContext(); text.value=''; find('[data-source-note]').textContent=''; closeRemote(); options(task,[],()=>'',()=>'', 'Kayıtları yeniden getir'); options(source,[],()=>'',()=>'', 'Kayıtları yeniden getir'); sourceRows=[]; select.disabled = true; more.hidden = true; status.textContent = 'Arama değişti; kayıtları yeniden getir.'; });
  text.addEventListener('input', () => { find('[data-result]').hidden = true; });
  find('[data-close]').addEventListener('click', () => dialog.close());
  dialog.addEventListener('cancel', () => resetContext());
  dialog.addEventListener('close', () => { resetContext(); closeRemote(); text.value = ''; sourceRows = []; options(task,[],()=>'',()=>'', 'Kayıtları yeniden getir'); options(source,[],()=>'',()=>'', 'Kayıtları yeniden getir'); select.disabled=true; more.hidden=true; find('[data-source-note]').textContent=''; status.textContent = ''; button.focus(); });
  button.addEventListener('click', () => { resetContext(); dialog.showModal(); query.focus(); });
  const leave = () => { if (dialog.open) dialog.close(); else resetContext(); };
  document.getElementById('new-chat')?.addEventListener('click', leave);
  window.addEventListener('hashchange', leave);
  window.addEventListener('pagehide', leave);
})();
