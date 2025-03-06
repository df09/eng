import * as h from './helpers.js';
import * as q from './q.js';

document.addEventListener('DOMContentLoaded', function () {
  if (!q.elements.form || !q.elements.input) return;

  q.grades.forEach(grade => {
    q.eStatElements[grade] = h.getEl(`#stat-${grade}`);
  });

  let answers = [];
  let idx = 0;
  let eBlanks = [...h.getEls('.blank')].sort((a, b) => Number(a.dataset.num) - Number(b.dataset.num));

  // Обновление кнопок и сообщений
  function updateButtonsAndMessages() {
    h.hide(q.elements.back, q.elements.next, q.elements.submit, q.elements.nextQuestion, q.elements.msgResult, q.elements.msgEmpty);
    
    if (idx === 0) h.show(q.elements.next);
    else if (idx < eBlanks.length - 1) h.show(q.elements.back, q.elements.next);
    else h.show(q.elements.back, q.elements.submit);
  }

  function underline2blank() {
    const eBlank = eBlanks[idx];
    let maxLength = eBlank.dataset.maxlength || eBlank.textContent.trim().length;
    eBlank.dataset.maxlength = maxLength;
    
    Object.assign(q.elements.input, { maxlength: maxLength, size: maxLength, value: '' });
    
    eBlank.innerHTML = '';
    eBlank.appendChild(q.elements.input);
    q.elements.input.focus();
  }

  // Действия
  function actionBack() {
    if (idx <= 0) return;
    eBlanks[idx].innerHTML = '_'.repeat(parseInt(eBlanks[idx].dataset.maxlength, 10));
    h.remCls(eBlanks[idx], 'filled', 'y', 'bg-y');
    answers.pop();
    idx--;
    underline2blank();
    updateButtonsAndMessages();
  }

  function actionNext() {
    const userInput = q.elements.input.value.trim();
    if (!userInput) {
      h.show(q.elements.msgEmpty);
      q.elements.input.focus();
      return;
    }
    
    answers[idx] = userInput;
    eBlanks[idx].innerHTML = userInput.padEnd(parseInt(eBlanks[idx].dataset.maxlength, 10), ' ');
    h.addCls(eBlanks[idx], 'filled', 'y', 'bg-y');

    if (idx < eBlanks.length - 1) {
      idx++;
      underline2blank();
    }
    updateButtonsAndMessages();
  }

  function actionSubmit() {
    if (!q.elements.input.value.trim()) {
      h.show(q.elements.msgEmpty);
      q.elements.input.focus();
      return;
    }

    answers[idx] = q.elements.input.value.trim();
    eBlanks[idx].innerHTML = answers[idx].padEnd(parseInt(eBlanks[idx].dataset.maxlength, 10), ' ');
    h.addCls(eBlanks[idx], 'filled', 'y', 'bg-y');

    h.getEl('#hidden-answer')?.setAttribute('value', JSON.stringify(answers));

    fetch(q.elements.form.action, { method: 'POST', body: new FormData(q.elements.form) })
      .then(response => response.json())
      .then(data => {
        q.updateStats(data.stat, data.tdata);

        h.remCls(q.elements.estimation, ...q.grades);
        h.addCls(q.elements.estimation, data.progress.estimation);
        q.elements.estimation.textContent = `${data.progress.estimation}:`;
        q.elements.points.textContent = `${data.progress.points}/${data.progress.threshold}`;

        eBlanks.forEach((eBlank, i) => {
          h.remCls(eBlank, 'y', 'bg-y');
          let userAnswer = answers[i]?.trim() || '';
          let correctAnswer = data.question.correct[i]?.[1] || '';
          let maxLength = parseInt(eBlank.dataset.maxlength, 10);
          eBlank.innerHTML = q.highlightMistakes(userAnswer.padEnd(maxLength, ' '), correctAnswer.padEnd(maxLength, ' '));
        });

        idx++;
        h.addCls(q.elements.nextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
        h.addCls(q.elements.msgResult, data.is_correct ? 'g' : 'r');
        q.elements.msgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';

        h.hide(q.elements.back, q.elements.next, q.elements.submit, q.elements.msgEmpty);
        h.show(q.elements.nextQuestion, q.elements.msgResult);

        if (parseInt(data.question.suspicious_status, 10) === 0) {
          h.show(q.elements.susFormWrap);
        }
      });
  }

  // Слушатели событий
  q.elements.back?.addEventListener('click', actionBack);
  q.elements.next?.addEventListener('click', actionNext);
  q.elements.submit?.addEventListener('click', actionSubmit);
  q.elements.nextQuestion?.addEventListener('click', q.actionNextQuestion);
  q.elements.input?.addEventListener('input', () => h.hide(q.elements.msgEmpty));

  // Горячие клавиши
  document.addEventListener('keydown', function (event) {
    h.hk(event, 'Escape', q.elements.mainMenuLink, () => q.elements.mainMenuLink?.click());
    h.hk(event, [['ArrowLeft', 'ArrowUp'], ['Tab', event.shiftKey]], q.elements.back, actionBack);
    h.hk(event, ['ArrowRight', 'ArrowDown', 'Enter', 'Tab'], q.elements.next, actionNext);
    h.hk(event, 'Enter', q.elements.submit, actionSubmit);
    h.hk(event, 'Enter', q.elements.nextQuestion, q.actionNextQuestion);
  });

  // Инициализация
  underline2blank();
  updateButtonsAndMessages();
});
