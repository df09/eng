import * as h from './helpers.js';
import * as q from './q.js';

document.addEventListener('DOMContentLoaded', function () {
  if (!q.elements.form) return;
  let submitted = false;

  h.grades.forEach(grade => {
    q.eStatElements[grade] = h.getEl(`#stat-${grade}`);
  });

  q.elements.form.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;

    if (!Array.from(q.elements.checkboxes).some(cb => cb.checked)) {
      h.show(q.elements.msgEmpty);
      return;
    }
    h.hide(q.elements.msgEmpty);

    submitted = true;
    fetch(q.elements.form.action, {
      method: 'POST',
      body: new FormData(q.elements.form)
    })
    .then(response => response.json())
    .then(data => {
      q.updateStats(data.stat, data.tdata);

      h.remCls(q.elements.estimation, ...h.grades);
      h.addCls(q.elements.estimation, data.progress.estimation);
      q.elements.estimation.textContent = `${data.progress.estimation}:`;
      q.elements.points.textContent = `${data.progress.points}/${data.progress.threshold}`;

      q.elements.labels.forEach(label => {
        const input = h.getEl(`#${label.getAttribute('for')}`);
        if (!input) return;
        const option = label.querySelector('.option-text');

        input.disabled = true;
        option.style.pointerEvents = 'none';
        h.remCls(option, 'hov');

        if (data.question.correct.includes(input.value.trim())) {
          h.addCls(option, input.checked ? 'g bg-g brd-g' : 'y bg-y brd-y');
        } else if (input.checked) {
          h.addCls(option, 'r bg-r brd-r');
        }
      });

      h.hide(q.elements.submit);
      h.remCls(q.elements.nextQuestion, 'btn-g', 'btn-r');
      h.addCls(q.elements.nextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      h.show(q.elements.nextQuestion);

      h.addCls(q.elements.msgResult, data.is_correct ? 'g' : 'r');
      q.elements.msgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      h.show(q.elements.msgResult);

      if (parseInt(data.question.suspicious_status, 10) === 0) {
        h.show(q.elements.susFormWrap);
      }
    });
  });

  q.elements.nextQuestion?.addEventListener('click', q.actionNextQuestion);

  document.addEventListener('keydown', (event) => {
    h.hk(event, 'Escape', q.elements.mainMenuLink, () => q.elements.mainMenuLink?.click());
    h.hk(event, 'Enter', q.elements.submit, () => q.elements.submit?.click());
    h.hk(event, 'Enter', q.elements.nextQuestion, q.actionNextQuestion);
  });
});
