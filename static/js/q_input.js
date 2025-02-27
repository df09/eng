document.addEventListener('DOMContentLoaded', function () {
  const eEstimation = document.querySelector('.estimation');
  const ePoints = eEstimation.nextElementSibling;
  const eQuestion = document.querySelector('.b.bg-b + span');
  const eForm = document.getElementById('q-input-form');
  const eInput = document.getElementById('q-input');
  const eSubmit = document.getElementById('q-input-submit');
  const eNext = document.getElementById('next-question');
  const eMsg = document.getElementById('result-message');
  const eMsgSelect = document.getElementById('msg-select');

  let submitted = false;
  // Автофокус на поле ввода
  eInput.focus();
  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;
    // Проверяем, введено ли хоть что-то
    if (!eInput.value.trim()) {
      remCls(eMsgSelect, 'dnone');
      return;
    }
    addCls(eMsg, 'dnone');
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
          // submit/next
          addCls(eSubmit, 'dnone', data.is_correct ? 'btn-g' : 'btn-r');
          remCls(eNext, 'dnone');
          addCls(eNext, data.is_correct ? 'btn-g' : 'btn-r');
          // result-message
          remCls(eMsg, 'dnone', 'g', 'r');
          addCls(eMsg, data.is_correct ? 'g' : 'r');
          eMsg.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
        }
      }).catch(error => console.error('Error:', error));
  });

  // Обработчик кнопки "Next"
  eNext.addEventListener('click', () => {
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    if (match) {
      window.location.href = '/topic/' + match[1];
    }
  });

  // Горячие клавиши
  document.addEventListener('keydown', (event) => {
    if (submitted) {
      if (event.key === 'Enter' && !eNext.classList.contains('dnone')) {
        event.preventDefault();
        setTimeout(() => eNext.click(), 50);
      }
      return;
    }
    if (event.key === 'Enter') {
      eSubmit.click();
    }
  });
});
