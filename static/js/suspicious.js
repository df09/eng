document.addEventListener('DOMContentLoaded', function () {
  const eNextQuestion = getEl('#form-btn-next-question');
  const eSusCount = getEl('#suspicious');
  const eBtnSus = getEl('#btn-suspicious');
  const eFormSus = getEl('#suspicious-form');
  const eInputNote = getEl('#suspicious-note');
  const eBtnSendSus = getEl('#btn-send-suspicious');
  const eMetadata = getEl('#question-metadata');
  const eMsgSus1= getEl('#msg-suspicious-1');
  const eMsgSus2= getEl('#msg-suspicious-2');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');

  const tid = eMetadata.dataset.tid;
  const qkind = eMetadata.dataset.qkind;
  const qid = eMetadata.dataset.qid;

  function updateSusCount() {
    // Извлекаем текущее количество подозрительных вопросов
    let count = parseInt(eSusCount.textContent.replace('?:', ''), 10) || 0;
    count += 1; // Увеличиваем на 1
    eSusCount.textContent = '?:' + count;
    // Обновляем классы
    remCls(eSusCount, 'zero', 'found');
    addCls(eSusCount, count === 0 ? 'zero' : 'found');
  }

  // listeners
  eBtnSus.addEventListener('click', () => {
    hide(eBtnSus, eNextQuestion, eMsgEmpty, eMsgResult);
    show(eFormSus);
    eInputNote.focus();
  });
  eBtnSendSus.addEventListener('click', () => {
    event.preventDefault(); // Блокируем стандартное поведение кнопки
    const note = eInputNote.value.trim();
    fetch('/suspicious', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: string = JSON.stringify({
        tid: Number(tid),
        qkind: String(qkind),
        qid: Number(qid),
        note: String(note),
      })
    }).then(response => response.json()).then(data => {
      hide(eFormSus);
      show(eMsgSus1, eNextQuestion);
      // Обновляем статистику подозрительных вопросов
      updateSusCount();
    });
  });
});
