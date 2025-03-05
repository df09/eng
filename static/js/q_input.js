document.addEventListener('DOMContentLoaded', function () {
  const ist0 = getEl('#ist0').dataset.ist0 === '1';
  const eMainMenuLink = getEl('#main-menu-link');
  const eEstimation = getEl('#estimation');
  const ePoints = getEl('#points');
  const eHints = getEl('#hints');
  const eQuestion = getEl('#question-text');
  const eExtra = getEl('#extra-block');
  const eForm = getEl('#question-form');
  const eInput = getEl('#form-input');
  const eSubmit = getEl('#form-btn-submit');
  const eNextQuestion = getEl('#form-btn-next-question');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');
  const eTotal = getEl('#total');
  const eSuspicious = getEl('#suspicious');
  const eSusFormWrap = getEl('#suspicious-form-wrap');

  const eStatElements = {}; // Хранилище для ссылок на элементы статистики
  const grades = ['N', 'F', 'D', 'C', 'B', 'A'];
  grades.forEach(grade => {
    eStatElements[grade] = getEl('#stat-'+grade);
  });
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

  let submitted = false;
  // Автофокус на поле ввода
  eInput.focus();
  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;
    // Проверяем, введено ли хоть что-то
    if (!eInput.value.trim()) { show(eMsgEmpty); eInput.focus(); return; }
    hide(eMsgResult);
    submitted = true;

    const formData = new FormData(eForm);
    fetch(eForm.action, { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        // stats
        updateStats(data.stat, data.tdata);
        // estimation
        remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
        addCls(eEstimation, data.progress.estimation);
        eEstimation.textContent = data.progress.estimation + ':';
        ePoints.textContent = data.progress.points + '/' + data.progress.threshold;
        // question and spellcheck
        const eBlank = document.createElement('span');
        eBlank.innerHTML = highlightMistakes(data.answer, data.question.correct, data.is_correct);
        eQuestion.innerHTML = eQuestion.innerHTML.replace('___', eBlank.outerHTML);
        // extra
        show(eExtra);
        // input
        eInput.disabled = true;
        // buttons and messages
        addCls(eSubmit, data.is_correct ? 'btn-g' : 'btn-r');
        addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
        addCls(eMsgResult, data.is_correct ? 'g' : 'r');
        eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
        hide(eSubmit);
        show(eNextQuestion, eMsgResult);
        // suspicious
        if (parseInt(data.tdata.suspicious, 10) !== 0) {
            show(eSusFormWrap);
        }
      });
  });

  // listeners
  eInput.addEventListener('input', () => hide(eMsgEmpty));
  eNextQuestion.addEventListener('click', () => {
    if (ist0) {
      window.location.href = '/topic/0';
    } else {
      const match = window.location.pathname.match(/\/topic\/(\d+)\//);
      window.location.href = '/topic/' + match[1];
    }
  });

  // hotkeys
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') { eMainMenuLink.click(); }
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
