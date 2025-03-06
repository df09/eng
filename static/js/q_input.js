import * as h from './helpers.js';
import * as q from './q.js';

document.addEventListener('DOMContentLoaded', function () {
  if (!q.elements.form || !q.elements.input) return;
  let submitted = false;

  q.grades.forEach(grade => {
    q.eStatElements[grade] = h.getEl(`#stat-${grade}`);
  });

  // Автофокус на поле ввода
  q.elements.input?.focus();

  // Слушатель ввода: скрывать сообщение об ошибке
  q.elements.input?.addEventListener('input', () => h.hide(q.elements.msgEmpty));

  // Обработка формы
  q.elements.form?.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;

    // Проверка ввода
    if (!q.elements.input.value.trim()) {
      h.show(q.elements.msgEmpty);
      q.elements.input.focus();
      return;
    }
    h.hide(q.elements.msgResult);
    submitted = true;

    // Отправка данных
    fetch(q.elements.form.action, {
      method: 'POST',
      body: new FormData(q.elements.form)
    })
    .then(response => response.json())
    .then(data => {
      // Обновление статистики
      q.updateStats(data.stat, data.tdata);

      // Оценка
      h.remCls(q.elements.estimation, ...q.grades);
      h.addCls(q.elements.estimation, data.progress.estimation);
      q.elements.estimation.textContent = `${data.progress.estimation}:`;
      q.elements.points.textContent = `${data.progress.points}/${data.progress.threshold}`;

      // Обработка текста и исправлений
      const eBlank = document.createElement('span');
      eBlank.innerHTML = q.highlightMistakes(data.answer, data.question.correct, data.is_correct);
      q.elements.question.innerHTML = q.elements.question.innerHTML.replace('___', eBlank.outerHTML);

      // Показ дополнительных блоков
      h.show(q.elements.extra);

      // Блокировка поля ввода
      q.elements.input.disabled = true;

      // Обновление кнопок и сообщений
      h.addCls(q.elements.submit, data.is_correct ? 'btn-g' : 'btn-r');
      h.addCls(q.elements.nextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      h.addCls(q.elements.msgResult, data.is_correct ? 'g' : 'r');
      q.elements.msgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';

      h.hide(q.elements.submit);
      h.show(q.elements.nextQuestion, q.elements.msgResult);

      // Показ формы для подозрительных вопросов
      if (parseInt(data.question.suspicious_status, 10) === 0) {
        h.show(q.elements.susFormWrap);
      }
    });
  });

  // Обработчик кнопки "Следующий вопрос"
  q.elements.nextQuestion?.addEventListener('click', q.actionNextQuestion);

  // Горячие клавиши
  document.addEventListener('keydown', (event) => {
    h.hk(event, 'Escape', q.elements.mainMenuLink, () => q.elements.mainMenuLink?.click());
    h.hk(event, 'Enter', q.elements.submit, () => q.elements.submit?.click());
    h.hk(event, 'Enter', q.elements.nextQuestion, q.actionNextQuestion);
  });
});
