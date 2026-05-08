// ===== SUBMIT TO SERVER =====
async function submitForm(data) {
  const p = new URLSearchParams(window.location.search);
  data.utm_source   = p.get('utm_source')   || '';
  data.utm_medium   = p.get('utm_medium')   || '';
  data.utm_campaign = p.get('utm_campaign') || '';
  data.utm_content  = p.get('utm_content')  || '';
  data.utm_term     = p.get('utm_term')     || '';
  try {
    await fetch('/send-form.php', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data)
    });
  } catch(e) { console.warn('Submit error', e); }
}

// ===== CONTACT MODAL =====
function scrollToForm() { openContactModal(); }

function openContactModal() {
  document.getElementById('contactModal').classList.add('active');
  document.body.style.overflow = 'hidden';
  setTimeout(() => { const el = document.getElementById('cName'); if (el) el.focus(); }, 100);
}
function closeContactModal(e) {
  if (e && e.target !== document.getElementById('contactModal') && !e.target.classList.contains('modal-close')) return;
  document.getElementById('contactModal').classList.remove('active');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closeContactModal({ target: document.getElementById('contactModal') });
    closeLetterModal({ target: document.getElementById('lbOverlay') });
  }
});

// ===== FAQ ACCORDION =====
function toggleFaq(btn) {
  const item = btn.closest('.faq-item');
  const isOpen = item.classList.contains('open');
  document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
  if (!isOpen) item.classList.add('open');
}

// ===== PHONE MASK (для полей org-формы: (000) 000-00-00) =====
function applyPhoneMask(input) {
  input.addEventListener('input', function () {
    let val = this.value.replace(/\D/g, '');
    if (val.length > 10) val = val.slice(0, 10);
    let result = '';
    if (val.length > 0) result = '(' + val.slice(0, 3);
    if (val.length >= 4) result += ') ' + val.slice(3, 6);
    if (val.length >= 7) result += '-' + val.slice(6, 8);
    if (val.length >= 9) result += '-' + val.slice(8, 10);
    this.value = result;
  });
}

applyPhoneMask(document.getElementById('phone1'));
applyPhoneMask(document.getElementById('phone2'));

// ===== MODAL PHONE MASK: +7 (___) ___-__-__ =====
(function() {
  const input = document.getElementById('cPhone');
  if (!input) return;
  function format(val) {
    let d = val.replace(/\D/g, '');
    if (d.startsWith('7') || d.startsWith('8')) d = d.slice(1);
    d = d.slice(0, 10);
    let r = '+7';
    if (d.length > 0) r += ' (' + d.slice(0, 3);
    if (d.length >= 3) r += ')';
    if (d.length > 3) r += ' ' + d.slice(3, 6);
    if (d.length > 6) r += '-' + d.slice(6, 8);
    if (d.length > 8) r += '-' + d.slice(8, 10);
    return r;
  }
  input.addEventListener('focus', function() { if (!this.value) this.value = '+7 '; });
  input.addEventListener('input', function() { this.value = format(this.value); });
  input.addEventListener('keydown', function(e) {
    if ((e.key === 'Backspace' || e.key === 'Delete') && this.value.replace(/\D/g,'').length <= 1) {
      e.preventDefault(); this.value = '+7 ';
    }
  });
})();

// ===== PHONE WRAP STATE =====
['phone1', 'phone2'].forEach(function(id, i) {
  const input = document.getElementById(id);
  const wrap  = document.getElementById('phoneWrap' + (i + 1));
  input.addEventListener('focus',  () => wrap.style.borderColor = 'var(--blue2)');
  input.addEventListener('blur',   () => wrap.style.borderColor = '');
});

// ===== FILE UPLOAD NAME =====
document.getElementById('orgCard').addEventListener('change', function () {
  const label = document.getElementById('uploadName');
  label.textContent = this.files.length ? this.files[0].name : 'Файл не выбран';
});

// ===== VALIDATION HELPERS =====
function showError(fieldId, msg) {
  const input = document.getElementById(fieldId);
  const err   = document.getElementById('err-' + fieldId);
  if (input)  { input.classList.add('error'); input.classList.remove('valid'); }
  if (err)    { err.textContent = msg; }
}
function showValid(fieldId) {
  const input = document.getElementById(fieldId);
  const err   = document.getElementById('err-' + fieldId);
  if (input)  { input.classList.remove('error'); input.classList.add('valid'); }
  if (err)    { err.textContent = ''; }
}
function clearState(fieldId) {
  const input = document.getElementById(fieldId);
  const err   = document.getElementById('err-' + fieldId);
  if (input)  { input.classList.remove('error', 'valid'); }
  if (err)    { err.textContent = ''; }
}
function showPhoneError(wrapId, inputId, msg) {
  const wrap  = document.getElementById(wrapId);
  const input = document.getElementById(inputId);
  const err   = document.getElementById('err-' + inputId);
  if (wrap)  { wrap.classList.add('error'); wrap.classList.remove('valid'); }
  if (input) { input.classList.add('error'); }
  if (err)   { err.textContent = msg; }
}
function showPhoneValid(wrapId, inputId) {
  const wrap  = document.getElementById(wrapId);
  const input = document.getElementById(inputId);
  const err   = document.getElementById('err-' + inputId);
  if (wrap)  { wrap.classList.remove('error'); wrap.classList.add('valid'); }
  if (input) { input.classList.remove('error'); input.classList.add('valid'); }
  if (err)   { err.textContent = ''; }
}

function getPhoneDigits(id) {
  return document.getElementById(id).value.replace(/\D/g, '');
}

// ===== VALIDATION RULES =====
function validateForm() {
  let valid = true;

  const orgName = document.getElementById('orgName').value.trim();
  if (!orgName) { showError('orgName', 'Укажите наименование организации'); valid = false; }
  else showValid('orgName');

  const orgAddress = document.getElementById('orgAddress').value.trim();
  if (!orgAddress) { showError('orgAddress', 'Укажите адрес организации'); valid = false; }
  else showValid('orgAddress');

  const p1 = getPhoneDigits('phone1');
  if (p1.length < 10) { showPhoneError('phoneWrap1', 'phone1', 'Введите полный номер телефона'); valid = false; }
  else showPhoneValid('phoneWrap1', 'phone1');

  const p2 = getPhoneDigits('phone2');
  if (p2.length < 10) { showPhoneError('phoneWrap2', 'phone2', 'Введите полный номер телефона'); valid = false; }
  else showPhoneValid('phoneWrap2', 'phone2');

  const email = document.getElementById('orgEmail').value.trim();
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showError('orgEmail', 'Введите корректный Email'); valid = false; }
  else showValid('orgEmail');

  const inn = document.getElementById('inn').value.replace(/\D/g, '');
  if (inn.length !== 10 && inn.length !== 12) { showError('inn', 'ИНН должен содержать 10 или 12 цифр'); valid = false; }
  else showValid('inn');

  const kpp = document.getElementById('kpp').value.replace(/\D/g, '');
  if (kpp.length !== 9) { showError('kpp', 'КПП должен содержать 9 цифр'); valid = false; }
  else showValid('kpp');

  const ogrn = document.getElementById('ogrn').value.replace(/\D/g, '');
  if (ogrn.length < 16) { showError('ogrn', 'Введите корректный ОГРН (16 или более цифр)'); valid = false; }
  else showValid('ogrn');

  const okpo = document.getElementById('okpo').value.replace(/\D/g, '');
  if (okpo.length < 13) { showError('okpo', 'Введите корректный ОКПО (13 или более цифр)'); valid = false; }
  else showValid('okpo');

  return valid;
}

// ===== FORM SUBMIT =====
document.getElementById('orgForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  ['orgName','orgAddress','orgEmail','inn','kpp','ogrn','okpo'].forEach(clearState);
  ['phoneWrap1','phoneWrap2'].forEach(id => {
    const w = document.getElementById(id);
    if (w) { w.classList.remove('error','valid'); }
  });

  if (!validateForm()) return;

  const submitBtn = this.querySelector('.btn--submit');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Отправка...';

  const orgName = document.getElementById('orgName').value.trim();
  await submitForm({
    name:       orgName,
    orgName:    orgName,
    orgAddress: document.getElementById('orgAddress').value.trim(),
    phone:      '+7' + getPhoneDigits('phone1'),
    phone2:     getPhoneDigits('phone2'),
    email:      document.getElementById('orgEmail').value.trim(),
    inn:        document.getElementById('inn').value.replace(/\D/g, ''),
    kpp:        document.getElementById('kpp').value.replace(/\D/g, ''),
    ogrn:       document.getElementById('ogrn').value.replace(/\D/g, ''),
    okpo:       document.getElementById('okpo').value.replace(/\D/g, ''),
  });

  window.location.href = '/thanks3';
});

// ===== CONTACT FORM (маленькая модалка) =====
document.getElementById('contactForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  let valid = true;

  const name = document.getElementById('cName').value.trim();
  if (!name || name.length < 2) {
    showError('cName', 'Введите ваше имя');
    valid = false;
  } else { showValid('cName'); }

  const phoneDigits = document.getElementById('cPhone').value.replace(/\D/g, '');
  if (phoneDigits.length < 11) {
    showError('cPhone', 'Введите полный номер телефона');
    valid = false;
  } else { showValid('cPhone'); }

  if (!valid) return;

  const btn = this.querySelector('.modal-submit');
  btn.disabled = true;
  btn.textContent = 'Отправка...';

  await submitForm({ name, phone: '+' + phoneDigits });
  window.location.href = '/spasibo';
});

// ===== LETTER LIGHTBOX =====
function openLetterModal(el) {
  const imgSrc = el.getAttribute('data-img');
  const overlay = document.getElementById('lbOverlay');
  const content = document.getElementById('lbContent');

  if (imgSrc) {
    const img = document.createElement('img');
    img.src = imgSrc;
    img.alt = 'Благодарственное письмо';
    img.style.cssText = 'width:100%;border-radius:4px;display:block;';
    img.onerror = function() {
      const clone = el.cloneNode(true);
      clone.classList.add('lb-clone');
      clone.style.cssText = 'cursor:default;transform:none;box-shadow:none;';
      content.innerHTML = '';
      content.appendChild(clone);
    };
    content.innerHTML = '';
    content.appendChild(img);
  } else {
    const clone = el.cloneNode(true);
    clone.classList.add('lb-clone');
    clone.style.cssText = 'cursor:default;transform:none;box-shadow:none;';
    content.innerHTML = '';
    content.appendChild(clone);
  }

  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeLetterModal(e) {
  if (e && e.target !== document.getElementById('lbOverlay') && !e.target.classList.contains('lb-close')) return;
  document.getElementById('lbOverlay').classList.remove('active');
  document.body.style.overflow = '';
}
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') closeLetterModal({ target: document.getElementById('lbOverlay') });
});

// ===== HEADER SCROLL SHADOW =====
window.addEventListener('scroll', function () {
  const header = document.querySelector('.header');
  if (window.scrollY > 10) header.style.boxShadow = '0 2px 20px rgba(0,0,0,0.15)';
  else header.style.boxShadow = '';
});
