'use strict';

const COUNTRIES = {
  // ── 靜態：URL 帶藥名參數，直接開新分頁 ──
  UK: {
    type: 'static',
    url: 'https://services.nhsbsa.nhs.uk/dmd-browser/search?q={q}',
  },
  AU: {
    type: 'static',
    url: 'https://www.pbs.gov.au/search?q={q}',
  },
  BE: {
    type: 'static',
    url: 'https://www.cbip.be/fr/search?q={q}',
  },
  SE: {
    type: 'static',
    url: 'https://www.fass.se/LIF/result?query={q}&userType=2',
  },
  CH: {
    type: 'static',
    url: 'https://compendium.ch/search?q={q}',
  },

  // ── 動態：開啟首頁後注入腳本填入藥名並送出 ──
  JP: {
    type: 'dynamic',
    url: 'https://www.kegg.jp/medicus-bin/search_drug',
    inject: injectJP,
  },
  FR: {
    type: 'dynamic',
    url: 'http://www.codage.ext.cnamts.fr/codif/bdm_it/index.php?p_site=AMELI',
    inject: injectFR,
  },
  CA: {
    type: 'dynamic',
    url: 'https://formulary.drugplan.ehealthsask.ca/SearchFormulary',
    inject: injectCA,
  },

  // ── 需登入：僅開啟首頁 ──
  DE: {
    type: 'login',
    url: 'https://www.rote-liste.de/',
  },
  US: {
    type: 'login',
    url: 'https://www.micromedexsolutions.com/',
  },
};

// ────────────────────────────────────────────────────────────
// 動態網站的注入函式（會在目標分頁的頁面環境中執行）
// ────────────────────────────────────────────────────────────

function injectJP(drugName) {
  function attempt() {
    const input = document.querySelector(
      'input[name="keyword"], input[name="q"], input[type="text"]'
    );
    if (!input) return false;
    input.value = drugName;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    const form = input.closest('form');
    if (form) {
      form.submit();
    } else {
      const btn = document.querySelector(
        'input[type="submit"], button[type="submit"]'
      );
      if (btn) btn.click();
    }
    return true;
  }
  if (!attempt()) {
    const ob = new MutationObserver(() => { if (attempt()) ob.disconnect(); });
    ob.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => ob.disconnect(), 8000);
  }
}

function injectFR(drugName) {
  function attempt() {
    const input = document.querySelector(
      'input[name="motsCles"], input[name="q"], input[type="text"]'
    );
    if (!input) return false;
    input.value = drugName;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    const form = input.closest('form');
    if (form) {
      form.submit();
    } else {
      const btn = document.querySelector(
        'input[type="submit"], button[type="submit"]'
      );
      if (btn) btn.click();
    }
    return true;
  }
  if (!attempt()) {
    const ob = new MutationObserver(() => { if (attempt()) ob.disconnect(); });
    ob.observe(document.body, { childList: true, subtree: true });
    setTimeout(() => ob.disconnect(), 8000);
  }
}

function injectCA(drugName) {
  // Saskatchewan Formulary 是 Vue SPA，需要用原生 setter 觸發 Vue 響應
  function setNativeValue(el, value) {
    const setter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    ).set;
    setter.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function attempt() {
    const input = document.querySelector(
      'input[type="search"], input[type="text"], input.form-control, input[placeholder*="earch"]'
    );
    if (!input) return false;
    setNativeValue(input, drugName);
    setTimeout(() => {
      const btn = document.querySelector(
        'button[type="submit"], input[type="submit"], button.btn-primary, button.btn'
      );
      if (btn) {
        btn.click();
      } else {
        input.dispatchEvent(
          new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true })
        );
        input.dispatchEvent(
          new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true })
        );
      }
    }, 300);
    return true;
  }

  // SPA 可能延遲渲染，持續重試
  let retries = 0;
  const timer = setInterval(() => {
    if (attempt() || ++retries > 20) clearInterval(timer);
  }, 500);
}

// ────────────────────────────────────────────────────────────
// UI 邏輯
// ────────────────────────────────────────────────────────────

const drugInput = document.getElementById('drugInput');
const openAllBtn = document.getElementById('openAll');
const toast = document.getElementById('toast');

// 恢復上次輸入的藥名
try {
  const saved = localStorage.getItem('lastDrug');
  if (saved) drugInput.value = saved;
} catch (_) {}

function getDrugName() {
  const name = drugInput.value.trim();
  if (!name) {
    showToast('請先輸入英文藥名');
    drugInput.focus();
    return null;
  }
  try { localStorage.setItem('lastDrug', name); } catch (_) {}
  return name;
}

function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2000);
}

// ── 開啟靜態網站 ──
function openStatic(code, drugName) {
  const cfg = COUNTRIES[code];
  const url = cfg.url.replace('{q}', encodeURIComponent(drugName));
  chrome.tabs.create({ url, active: false });
}

// ── 開啟動態網站：先建分頁 → 載入完成後注入腳本 ──
function openDynamic(code, drugName) {
  const cfg = COUNTRIES[code];
  chrome.tabs.create({ url: cfg.url, active: false }, (tab) => {
    function listener(tabId, info) {
      if (tabId !== tab.id || info.status !== 'complete') return;
      chrome.tabs.onUpdated.removeListener(listener);
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: cfg.inject,
        args: [drugName],
      }).catch(() => {});
    }
    chrome.tabs.onUpdated.addListener(listener);
    // 逾時自動移除 listener
    setTimeout(() => chrome.tabs.onUpdated.removeListener(listener), 15000);
  });
}

// ── 開啟需登入的網站 ──
function openLogin(code) {
  const cfg = COUNTRIES[code];
  chrome.tabs.create({ url: cfg.url, active: false });
}

// ── 處理單國按鈕點擊 ──
function handleCountryClick(code) {
  const cfg = COUNTRIES[code];
  if (!cfg) return;

  if (cfg.type === 'login') {
    openLogin(code);
    showToast('已開啟首頁，請手動登入查詢');
    return;
  }

  const drugName = getDrugName();
  if (!drugName) return;

  if (cfg.type === 'static') {
    openStatic(code, drugName);
  } else {
    openDynamic(code, drugName);
  }
  showToast(`已開啟 ${code} 查詢`);
}

// ── 綁定所有按鈕事件 ──
document.querySelectorAll('[data-country]').forEach((btn) => {
  btn.addEventListener('click', () => {
    handleCountryClick(btn.dataset.country);
  });
});

// ── 一鍵全開 ──
openAllBtn.addEventListener('click', () => {
  const drugName = getDrugName();
  if (!drugName) return;

  const codes = Object.keys(COUNTRIES);
  let delay = 0;
  codes.forEach((code) => {
    setTimeout(() => {
      const cfg = COUNTRIES[code];
      if (cfg.type === 'static') openStatic(code, drugName);
      else if (cfg.type === 'dynamic') openDynamic(code, drugName);
      else openLogin(code);
    }, delay);
    delay += 200; // 間隔 200ms 避免瞬間開太多分頁
  });
  showToast('已開啟全部 10 國查詢');
});

// Enter 鍵 → 一鍵全開
drugInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') openAllBtn.click();
});
