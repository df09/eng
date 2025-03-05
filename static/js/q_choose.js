document.addEventListener('DOMContentLoaded', function () {
  const ist0 = getEl('#ist0').dataset.ist0 === '1';
  const eMainMenuLink = getEl('#main-menu-link');
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
  const eStatElements = {}; // Хранилище для ссылок на элементы статистики
  const grades = ['N', 'F', 'D', 'C', 'B', 'A'];
  grades.forEach(grade => {
    eStatElements[grade] = getEl('#stat-'+grade);
  });
  const eTotal = getEl('#total');
  const eSuspicious = getEl('#suspicious');
  // progress-bar
  function updProgresBar(stat) {
    const total = stat.total || 1;
    grades.forEach(grade => {
      const progressElement = getEl(`.sub-progress.${grade}`);
      if (progressElement) {
        const width = (stat[grade] / total * 100) || 0;
        progressElement.style.width = width+'%';
        width === 0 ? hide(progressElement) : show(progressElement)
      }
    });
  }
  // stats
  function updateStats(stat, tdata) {
    grades.forEach(grade => {
      if (eStatElements[grade]) {
        // stats values
        eStatElements[grade].textContent = grade + ':' + (stat[grade] || 0);
        // stats classes
        remCls(eStatElements[grade], 'zero', 'N', 'F', 'D', 'C', 'B', 'A');
        addCls(eStatElements[grade], stat[grade] === 0 ? 'zero' : grade);
      }
    });
    // Обновление total
    eTotal.textContent = stat.in_progress+'/'+tdata.total;
    // Обновление suspicious
    eSuspicious.textContent = '?:'+tdata.suspicious;
    remCls(eSuspicious, 'zero', 'found');
    addCls(eSuspicious, tdata.suspicious === 0 ? 'zero' : 'found');
    // Обновление progress-bar
    updProgresBar(stat);
  }

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
      // stats
      updateStats(data.stat, data.tdata);
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
      // buttons
      hide(eSubmit)
      remCls(eNextQuestion, 'btn-g', 'btn-r');
      addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      show(eNextQuestion)
      // messages
      addCls(eMsgResult, data.is_correct ? 'g' : 'r');
      eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      show(eMsgResult);
    });
  });

  // listeners.next
  eNextQuestion.addEventListener('click', () => {
    if (ist0) {
      window.location.href = '/topic/0';
    } else {
      const match = window.location.pathname.match(/\/topic\/(\d+)\//);
      window.location.href = '/topic/' + match[1];
    }
  });
  // listeners.hotkeys
  const vimKeys = ['s', 'd', 'f', 'w', 'e', 'r', '2', '3', '4', 'c'];
  const keyMap = {};
  eCheckboxes.forEach((cb, i) => {
    const vimKey = i < vimKeys.length ? vimKeys[i] : null;
    if (vimKey) keyMap[vimKey] = cb;
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { eMainMenuLink.click(); }
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
