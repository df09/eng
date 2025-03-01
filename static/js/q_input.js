document.addEventListener('DOMContentLoaded', function () {
  const eEstimation = getEl('#estimation');
  const ePoints = getEl('#points');
  const eQuestion = getEl('#question-text');
  const eForm = getEl('#question-form');
  const eInput = getEl('#form-input');
  const eSubmit = getEl('#form-btn-submit');
  const eNextQuestion = getEl('#next-question');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');

  let submitted = false;
  // Автофокус на поле ввода
  eInput.focus();
  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;
    // Проверяем, введено ли хоть что-то
    if (!eInput.value.trim()) {
      remCls(eMsgEmpty, 'dnone');
      return;
    }
    addCls(eMsgResult, 'dnone');
    submitted = true;
    const formData = new FormData(eForm);
    fetch(eForm.action, { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // progress
          remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
          addCls(eEstimation, data.progress.estimation);
          eEstimation.textContent = data.progress.estimation + ':';
          ePoints.textContent = data.progress.points + '/' + data.progress.threshhold;
          // question
          const correctSpan = document.createElement('span');
          correctSpan.textContent = data.correct;
          addCls(correctSpan, data.is_correct ? 'g' : 'r');
          eQuestion.innerHTML = eQuestion.innerHTML.replace('___', correctSpan.outerHTML);
          // input
          eInput.disabled = true;
          // submit/eNextQuestion
          addCls(eSubmit, 'dnone', data.is_correct ? 'btn-g' : 'btn-r');
          remCls(eNextQuestion, 'dnone');
          addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
          // msg-result
          remCls(eMsgResult, 'dnone', 'g', 'r');
          addCls(eMsgResult, data.is_correct ? 'g' : 'r');
          eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
        }
      }).catch(error => console.error('Error:', error));
  });

  // Обработчик кнопки "eNextQuestion"
  eNextQuestion.addEventListener('click', () => {
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    if (match) {
      window.location.href = '/topic/' + match[1];
    }
  });

  // Горячие клавиши
  document.addEventListener('keydown', (event) => {
    if (submitted) {
      if (event.key === 'Enter' && !eNextQuestion.classList.contains('dnone')) {
        event.preventDefault();
        setTimeout(() => eNextQuestion.click(), 50);
      }
      return;
    }
    if (event.key === 'Enter') {
      eSubmit.click();
    }
  });
});
