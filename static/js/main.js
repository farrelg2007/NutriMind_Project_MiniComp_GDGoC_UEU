let selectedMood = '';
let streak = parseInt(localStorage.getItem('nm_streak') || '1');
let loadingTimer = null;

(function init() {
  const h = new Date().getHours();
  const greet = h < 11 ? 'Hei, selamat pagi! ☀️'
              : h < 15 ? 'Hei, selamat siang! 🌤️'
              : h < 19 ? 'Hei, selamat sore! 🌅'
              :           'Hei, selamat malam! 🌙';
  document.getElementById('greeting-text').textContent = greet;
  document.getElementById('streak-num').textContent = streak;
})();

function setStep(n) {
  [1,2,3].forEach(i => {
    const dot = document.getElementById('sdot-' + i);
    dot.className = 'step-dot' + (i < n ? ' done' : i === n ? ' active' : '');
  });
  [1,2].forEach(i => {
    document.getElementById('sline-' + i).style.width = i < n ? '100%' : '0%';
  });
  const labels = ['Pilih mood','Tulis jurnal','Lihat hasil'];
  document.getElementById('step-label').textContent = `Langkah ${Math.min(n,3)} dari 3`;

  document.getElementById('step-bar').style.display = n > 3 ? 'none' : 'flex';
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function selectMood(btn, mood) {
  document.querySelectorAll('.mood-card').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedMood = mood;
  setTimeout(() => {
    document.getElementById('btn-next-mood').disabled = false;
  }, 150);
}

function goToJournal() {
  setStep(2);
  showScreen('screen-journal');
}

function goBack() {
  setStep(1);
  showScreen('screen-mood');
}

function onJournalInput(el) {
  const len = el.value.length;
  const counter = document.getElementById('char-counter');
  counter.textContent = len + ' / 1000';
  counter.className = 'char-counter' + (len > 900 ? ' warn' : '');
  document.getElementById('btn-analyze').disabled = len < 10;
}

function fillChip(chip) {
  const ta = document.getElementById('journal-input');
  ta.value = chip.textContent.trim();
  onJournalInput(ta);
  ta.focus();
  chip.style.transform = 'scale(.95)';
  setTimeout(() => chip.style.transform = '', 150);
}

function animateLoadingSteps() {
  const steps = ['lstep-1','lstep-2','lstep-3','lstep-4'];
  let i = 0;

  function next() {
    if (i > 0) {
      document.getElementById(steps[i-1]).className = 'loading-step done';
    }
    if (i < steps.length) {
      document.getElementById(steps[i]).className = 'loading-step active';
      i++;
      loadingTimer = setTimeout(next, 700);
    }
  }
  next();
}

function resetLoadingSteps() {
  clearTimeout(loadingTimer);
  ['lstep-1','lstep-2','lstep-3','lstep-4'].forEach(id => {
    document.getElementById(id).className = 'loading-step';
  });
}

async function submitJournal() {
  let text = document.getElementById('journal-input').value.trim();
  if (text.length < 10) return;

  if (selectedMood) text += `. Suasana hati saya saat ini: ${selectedMood}.`;

  document.getElementById('btn-analyze').disabled = true;
  setStep(3);
  showScreen('screen-loading');
  resetLoadingSteps();
  animateLoadingSteps();

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ journal: text })
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || 'Terjadi kesalahan.');

    clearTimeout(loadingTimer);

    streak++;
    localStorage.setItem('nm_streak', streak);
    document.getElementById('streak-num').textContent = streak;

    displayResult(data);

  } catch (err) {
    clearTimeout(loadingTimer);
    displayError(err.message);
  } finally {
    document.getElementById('btn-analyze').disabled = false;
  }
}

function displayResult(data) {
  const {
    ringkasan        = 'Analisis selesai.',
    skor_nutrisi     = 50,
    kalori_estimasi  = '~? kkal',
    kekurangan       = [],
    insight          = '',
    saran_makanan    = [],
    pesan_motivasi   = 'Semangat terus ya!'
  } = data;

  document.getElementById('error-toast').classList.add('hidden');

  document.getElementById('res-skor').textContent = skor_nutrisi;
  document.getElementById('res-kalori').textContent = kalori_estimasi;

  let statusText, scoreBorderColor;
  if (skor_nutrisi >= 70) {
    statusText = '🟢 Nutrisi Baik!';
    scoreBorderColor = 'rgba(45,107,63,.6)';
  } else if (skor_nutrisi >= 40) {
    statusText = '🟡 Cukup — bisa lebih baik';
    scoreBorderColor = 'rgba(200,134,10,.6)';
  } else {
    statusText = '🔴 Perlu banyak perbaikan';
    scoreBorderColor = 'rgba(184,50,50,.6)';
  }
  document.getElementById('res-status').textContent = statusText;
  document.querySelector('.score-ring').style.borderColor = scoreBorderColor;

  document.getElementById('res-ringkasan').textContent = ringkasan;

  document.getElementById('res-insight').textContent = insight;

  const defEl = document.getElementById('res-deficiency');
  defEl.innerHTML = kekurangan.length ? kekurangan.map((item, i) => `
    <div class="deficiency-item" style="animation-delay:${i * 0.08}s">
      <div class="item-badge">${escHtml(item.icon || '⚠️')}</div>
      <div>
        <p class="item-name">${escHtml(item.nutrisi)}</p>
        <p class="item-desc">${escHtml(item.dampak)}</p>
      </div>
    </div>
  `).join('') : '<p style="font-size:14px;color:var(--ink-3);padding:0 4px">Tidak ada kekurangan signifikan hari ini — bagus! 🎉</p>';

  const foodEl = document.getElementById('res-foods');
  foodEl.innerHTML = saran_makanan.length ? saran_makanan.map((item, i) => `
    <div class="food-item" style="animation-delay:${i * 0.08}s">
      <div class="item-badge">🥗</div>
      <div style="flex:1">
        <p class="item-name">
          ${escHtml(item.nama)}
          ${item.mudah_didapat ? '<span class="easy-tag">Mudah didapat</span>' : ''}
        </p>
        <p class="item-desc">${escHtml(item.alasan)}</p>
      </div>
    </div>
  `).join('') : '';

  document.getElementById('res-motivasi').textContent = pesan_motivasi;

  setStep(4);
  showScreen('screen-result');
}

function displayError(msg) {
  document.getElementById('error-msg').textContent = msg;
  document.getElementById('error-toast').classList.remove('hidden');
  ['score-hero','ringkasan-strip','insight-card','motivasi-card'].forEach(id => {
    document.getElementById(id).classList.add('hidden');
  });
  document.querySelectorAll('.result-section-label, .items-wrap').forEach(el => el.classList.add('hidden'));
  setStep(4);
  showScreen('screen-result');
}

function resetAll() {
  selectedMood = '';
  document.getElementById('journal-input').value = '';
  document.getElementById('char-counter').textContent = '0 / 1000';
  document.getElementById('btn-next-mood').disabled = true;
  document.getElementById('btn-analyze').disabled = true;
  document.querySelectorAll('.mood-card').forEach(b => b.classList.remove('selected'));

  ['score-hero','ringkasan-strip','insight-card','motivasi-card'].forEach(id => {
    document.getElementById(id).classList.remove('hidden');
  });
  document.querySelectorAll('.result-section-label, .items-wrap').forEach(el => el.classList.remove('hidden'));
  document.getElementById('error-toast').classList.add('hidden');
  document.getElementById('streak-num').textContent = streak;

  setStep(1);
  showScreen('screen-mood');
}

function shareResult() {
  const skor = document.getElementById('res-skor').textContent;
  const text = `Skor nutrisi harianku: ${skor}/100 🥗\nDianalisis oleh NutriMind — AI Wellness Tracker\n#NutriMind #GDGoC #Kesehatan`;
  if (navigator.share) {
    navigator.share({ title: 'NutriMind — Hasil Analisis Nutrisi', text });
  } else {
    navigator.clipboard.writeText(text)
      .then(() => alert('Teks hasil disalin ke clipboard!'))
      .catch(() => alert(text));
  }
}

function escHtml(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(str)));
  return d.innerHTML;
}