import * as h from './helpers.js';
import * as q from './q.js';

document.addEventListener('DOMContentLoaded', function () {
  const elements = {
    nextQuestion: h.getEl('#form-btn-next-question'),
    susCount: h.getEl('#suspicious'),
    btnSus: h.getEl('#btn-suspicious'),
    formSus: h.getEl('#suspicious-form'),
    inputNote: h.getEl('#suspicious-note'),
    btnSendSus: h.getEl('#btn-send-suspicious'),
    metadata: h.getEl('#question-metadata'),
    msgSus1: h.getEl('#msg-suspicious-1'),
    msgSus2: h.getEl('#msg-suspicious-2'),
    msgResult: h.getEl('#msg-result'),
    msgEmpty: h.getEl('#msg-empty'),
    total: h.getEl('#total'),
    suspicious: h.getEl('#suspicious'),
  };

  if (!elements.metadata) return; // Если нет метаданных, скрипт не должен выполняться

  const grades = ['N', 'F', 'D', 'C', 'B', 'A'];
  const eStatElements = {};
  grades.forEach(grade => {
    eStatElements[grade] = h.getEl(`#stat-${grade}`);
  });

  const tid = Number(elements.metadata?.dataset?.tid || 0);
  const qkind = String(elements.metadata?.dataset?.qkind || '');
  const qid = Number(elements.metadata?.dataset?.qid || 0);

  function updateSusCount() {
    if (!elements.susCount) return;

    let count = parseInt(elements.susCount.textContent.replace('?:', ''), 10) || 0;
    count += 1;
    elements.susCount.textContent = `?:${count}`;

    h.remCls(elements.susCount, 'zero', 'found');
    h.addCls(elements.susCount, count === 0 ? 'zero' : 'found');
  }

  function sendSuspiciousReport(event) {
    event.preventDefault();
    if (!elements.inputNote || !elements.formSus || !elements.msgSus1 || !elements.nextQuestion) return;

    const note = elements.inputNote.value.trim();
    if (!note) return; // Если заметка пуста, ничего не делаем

    fetch('/suspicious', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tid, qkind, qid, note })
    })
    .then(() => {
      // После успешной отправки обновляем DOM, но не обрабатываем JSON
      h.hide(elements.formSus);
      h.show(elements.msgSus1, elements.nextQuestion);
      updateSusCount();
    })
    .catch(error => console.error('Error sending suspicious report:', error));
  }

  // listeners
  elements.btnSus?.addEventListener('click', () => {
    h.hide(elements.btnSus, elements.nextQuestion, elements.msgEmpty, elements.msgResult);
    h.show(elements.formSus);
    elements.inputNote?.focus();
  });

  elements.btnSendSus?.addEventListener('click', sendSuspiciousReport);

  // hotkeys
  document.addEventListener('keydown', (event) => {
    h.hk(event, 'Enter', elements.btnSendSus, sendSuspiciousReport);
  });
});
