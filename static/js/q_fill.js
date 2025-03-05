document.addEventListener('DOMContentLoaded', function () {
  const ist0 = getEl('#ist0').dataset.ist0 === '1';
  const eMainMenuLink = getEl('#main-menu-link');
  const eEstimation = getEl('#estimation');
  const ePoints = getEl('#points');
  const eQuestion = getEl('#question-text');
  const eForm = getEl('#question-form');
  const eInput = getEl('#form-input');
  const eNext = getEl('#form-btn-next');
  const eBack = getEl('#form-btn-back');
  const eSubmit = getEl('#form-btn-submit');
  const eNextQuestion = getEl('#form-btn-next-question');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');
  const eStatElements = {}; // Хранилище для ссылок на элементы статистики
  const eSusFormWrap = getEl('#suspicious-form-wrap');

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

  let answers = [];
  let idx = 0;
  let eBlanks = Array.from(getEls('.blank')).sort((a, b) => Number(a.dataset.num) - Number(b.dataset.num));

  // helpers
  function updateButtonsAndMessages() {
    hide(eBack, eNext, eSubmit, eNextQuestion, eMsgResult, eMsgEmpty);
    if (idx === 0) show(eNext);
    if (idx >= 1 && idx < eBlanks.length - 1) show(eBack, eNext);
    if (idx === eBlanks.length - 1) show(eBack, eSubmit);
  }
  function underline2blank() {
    const eBlank = eBlanks[idx];
    let maxLength = eBlank.dataset.maxlength || eBlank.textContent.trim().length;
    eBlank.dataset.maxlength = maxLength;
    eInput.setAttribute('maxlength', maxLength);
    eInput.setAttribute('size', maxLength);
    eInput.value = '';
    eBlank.innerHTML = '';
    eBlank.appendChild(eInput);
    eInput.focus();
  }

  // actions
  function actionBack() {
    const eBlank = eBlanks[idx];
    eBlank.innerHTML = '_'.repeat(parseInt(eBlank.dataset.maxlength, 10));
    remCls(eBlank, 'filled', 'y', 'bg-y');
    answers.pop();
    idx--;
    underline2blank();
    updateButtonsAndMessages();
  }
  function actionNext() {
    const userInput = eInput.value.trim();
    const eBlank = eBlanks[idx];
    if (!userInput) { show(eMsgEmpty); eInput.focus(); return; }
    answers[idx] = userInput;
    eBlank.innerHTML = userInput.padEnd(parseInt(eBlank.dataset.maxlength, 10), ' ');
    addCls(eBlank, 'filled', 'y', 'bg-y');
    if (idx < eBlanks.length - 1) {
      idx++;
      underline2blank();
    }
    updateButtonsAndMessages();
  }

  function actionSubmit() {
    const userInput = eInput.value.trim();
    const eBlank = eBlanks[idx];
    if (!userInput) { show(eMsgEmpty); eInput.focus(); return; }
    answers[idx] = userInput;
    eBlank.innerHTML = userInput.padEnd(parseInt(eBlank.dataset.maxlength, 10), ' ');
    addCls(eBlank, 'filled', 'y', 'bg-y');

    getEl('#hidden-answer').value = JSON.stringify(answers);
    fetch(eForm.action, {
      method: 'POST',
      body: new FormData(eForm)
    })
    .then(response => response.json())
    .then(data => {
      // stats
      updateStats(data.stat, data.tdata);
      // estimation
      remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
      addCls(eEstimation, data.progress.estimation);
      eEstimation.textContent = data.progress.estimation + ':';
      ePoints.textContent = data.progress.points + '/' + data.progress.threshold;
      // spellcheck
      eBlanks.forEach((eBlank, i) => {
          remCls(eBlank, 'y', 'bg-y');
          let userAnswer = answers[i].trim();
          let correctAnswer = data.question.correct[i][1]
          let maxLength = parseInt(eBlank.dataset.maxlength, 10);
          let paddedCorrectAnswer = correctAnswer.padEnd(maxLength, ' ');
          eBlank.innerHTML = highlightMistakes(userAnswer.padEnd(maxLength, ' '), paddedCorrectAnswer, data.is_correct);
      });
      // buttons and messages
      idx++;
      addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      addCls(eMsgResult, data.is_correct ? 'g' : 'r');
      eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      hide(eBack, eNext, eSubmit, eMsgEmpty);
      show(eNextQuestion, eMsgResult);
      // suspicious
      if (parseInt(data.question.suspicious_status, 10) === 0) {
          show(eSusFormWrap);
      }
    });
  }
  function actionNextQuestion() {
    if (ist0) {
      window.location.href = '/topic/0';
    } else {
      const match = window.location.pathname.match(/\/topic\/(\d+)\//);
      window.location.href = '/topic/' + match[1];
    }
  };

  // listeners
  eBack.addEventListener('click', actionBack);
  eNext.addEventListener('click', actionNext);
  eSubmit.addEventListener('click', actionSubmit);
  eNextQuestion.addEventListener('click', actionNextQuestion);
  eInput.addEventListener('input', () => hide(eMsgEmpty));

  // hotkeys
  document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') { eMainMenuLink.click(); }
    if ((event.key === 'ArrowLeft' || event.key === 'ArrowUp' || (event.key === 'Tab' && event.shiftKey)) && idx > 0) {
      event.preventDefault(); actionBack();
    } else if ((event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === 'Enter' || event.key === 'Tab') && idx < eBlanks.length - 1) {
      event.preventDefault(); actionNext();
    } else if (event.key === 'Enter' && idx === eBlanks.length - 1) {
      event.preventDefault(); actionSubmit();
    } else if ((event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === 'Enter' || event.key === 'Tab') && idx === eBlanks.length) {
      event.preventDefault(); actionNextQuestion();
    }
  });

  // init
  underline2blank();
  updateButtonsAndMessages();
});
