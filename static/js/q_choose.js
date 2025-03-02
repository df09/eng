document.addEventListener('DOMContentLoaded', function () {
  const eEstimation = getEl('#estimation');
  const ePoints = getEl('#points');
  const eQuestion = getEl('#question-text');
  const eForm = getEl('#question-form');
  const eCheckboxes = getEls('.option-input');
  const eLabels = getEls('.option-label');
  const eSubmit = getEl('#form-btn-submit');
  const eNextQuestion = getEl('#form-btn-next-question');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');

  let submitted = false; // Флаг для блокировки изменений

  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return; // Предотвращаем повторный сабмит
    // Проверяем, выбран ли хотя бы один чекбокс
    const isChecked = Array.from(eCheckboxes).some(cb => cb.checked);
    if (!isChecked) { show(eMsgEmpty); return; }
    hide(eMsgEmpty);

    submitted = true; // Флаг, что ответ уже отправлен
    const formData = new FormData(eForm);
    fetch(eForm.action, {
      method: 'POST',
      body: formData
    })
    .then(response => response.json())
    .then(data => {
      console.log(data)
      // estimation
      remCls(eEstimation, 'F','D','C','B','A');
      addCls(eEstimation, data.progress.estimation);
      eEstimation.textContent = data.progress.estimation + ':';
      ePoints.textContent = data.progress.points+'/'+data.progress.threshold;
      // checkboxes
      eLabels.forEach(eLabel => {
        const inputId = eLabel.getAttribute('for');
        const eInput = getEl('#' + inputId);
        const value = eInput.value.trim();
        const option = eLabel.querySelector('.option-text');

        // Блокировка кликов по чекбоксам
        eInput.addEventListener("click", function(event) {
          event.preventDefault();
        });
        // Блокировка изменения чекбоксов через клавиатуру
        eInput.disabled = true;
        // Убираем hover-эффект
        option.style.pointerEvents = 'none';
        remCls(option, 'hov');
        // options
        if (data.question.correct.includes(value) && eInput.checked) {  
          // Правильный и выбранный
          remCls(option, 'bg-w', 'brd-w');
          addCls(option, 'g', 'bg-g', 'brd-g');
        } 
        else if (data.question.correct.includes(value) && !eInput.checked) {  
          // Правильный, но НЕ выбранный
          remCls(option, 'bg-w', 'brd-w');
          addCls(option, 'y', 'bg-y', 'brd-y'); 
        } 
        else if (eInput.checked) { 
          // Неправильный и выбранный
          remCls(option, 'bg-w', 'brd-w');
          addCls(option, 'r', 'bg-r', 'brd-r'); 
        }
        eInput.checked = false; // Снимаем выбор
      });

      // submit/next
      hide(eSubmit)
      remCls(eNextQuestion, 'btn-g', 'btn-r');
      addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      show(eNextQuestion)
      // result-message
      addCls(eMsgResult, data.is_correct ? 'g' : 'r');
      eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      show(eMsgResult);
    })
    .catch(error => console.error('Error:', error));
  });

  // Обработчик кнопки "Next"
  eNextQuestion.addEventListener('click', () => {
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    window.location.href = '/topic/' + match[1];
  });

  // Горячие клавиши
  const numKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
  const vimKeys = ['s', 'd', 'f', 'g', 'x', 'c', 'v', 'b', 'j', 'k']; // vim-like keys
  const keyMap = {};

  eCheckboxes.forEach((cb, i) => {
    const numKey = i < numKeys.length ? numKeys[i] : null;
    const vimKey = i < vimKeys.length ? vimKeys[i] : null;
    if (numKey) keyMap[numKey] = cb;
    if (vimKey) keyMap[vimKey] = cb;
  });

  document.addEventListener('keydown', (event) => {
    if (submitted) {
      if (event.key === 'Enter' && !eNextQuestion.classList.contains('dnone')) {
        event.preventDefault();
        setTimeout(() => eNextQuestion.click(), 50);
      }
      return;
    }
    // ENTER -> Submit
    if (event.key === 'Enter') {
      event.preventDefault();
      eSubmit.click();
    // Горячие клавиши для выбора
    } else if (keyMap[event.key]) {
      keyMap[event.key].checked = !keyMap[event.key].checked;
    }
  });
});
