document.addEventListener('DOMContentLoaded', function () {
  // vars
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
    // upd old input
    eBlank.innerHTML = '_'.repeat(parseInt(eBlank.dataset.maxlength, 10));
    remCls(eBlank, 'filled', 'y', 'bg-y');
    // upd new input
    answers.pop();
    idx--;
    underline2blank();
    // upd buttons and messages
    updateButtonsAndMessages();
  }
  function actionNext() {
    const userInput = eInput.value.trim();
    const eBlank = eBlanks[idx];
    // check empty input
    if (!userInput) { show(eMsgEmpty); eInput.focus(); return; }
    // upd old input
    answers[idx] = userInput;
    eBlank.innerHTML = userInput.padEnd(parseInt(eBlank.dataset.maxlength, 10), ' ');
    addCls(eBlank, 'filled', 'y', 'bg-y');
    // upd new input
    if (idx < eBlanks.length - 1) {
      idx++;
      underline2blank();
    }
    // upd buttons
    updateButtonsAndMessages();
  }
  function actionSubmit() {
    const userInput = eInput.value.trim();
    const eBlank = eBlanks[idx];
    // check empty input
    if (!userInput) { show(eMsgEmpty); eInput.focus(); return; }
    // upd old input
    answers[idx] = userInput;
    eBlank.innerHTML = userInput.padEnd(parseInt(eBlank.dataset.maxlength, 10), ' ');
    addCls(eBlank, 'filled', 'y', 'bg-y');
    // post data
    fetch(eForm.action, {
      method: 'POST',
      body: new FormData(eForm)
    })
    .then(response => response.json())
    .then(data => {
      // upd estimation
      remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
      console.log('data.progress:')
      console.log(data.progress)
      addCls(eEstimation, data.progress.estimation);
      eEstimation.textContent = data.progress.estimation + ':';
      ePoints.textContent = data.progress.points + '/' + data.progress.threshhold;
      // spellcheck blanks
      function highlightMistakes(userInput, correctInput) {
          let resultHTML = "";
          let len = Math.max(userInput.length, correctInput.length);
          for (let i = 0; i < len; i++) {
              let userChar = userInput[i] || "";
              let correctChar = correctInput[i] || "";
              if (userChar === correctChar) {
                  resultHTML += userChar;
              } else {
                  resultHTML += `<span class="error">${userChar || " "}</span>`;
              }
          }
          return resultHTML;
      }
      data.correct.forEach((correctAnswer, i) => {
          let eBlank = eBlanks[i];
          let userAnswer = answers[i] || "";
          if (userAnswer !== correctAnswer) {
              eBlank.innerHTML = highlightMistakes(userAnswer, correctAnswer);
              addCls(eBlank, 'bg-r');  // Красная подсветка ошибки
          } else {
              addCls(eBlank, 'bg-g');  // Зелёная подсветка верного ответа
          }
      });
      // upd buttons
      idx++;
      addCls(eNextQuestion, data.is_correct ? 'btn-g':'btn-r');
      addCls(eMsgResult, data.is_correct ? 'g':'r');
      eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      hide(eBack, eNext, eSubmit, eMsgEmpty);
      show(eNextQuestion, eMsgResult);
    })
    .catch(error => console.error('Error:', error));
  }
  function actionNextQuestion() {
    console.log('actionNextQuestion stat..')
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    window.location.href = '/topic/' + match[1];
  }

  // listeners
  eBack.addEventListener('click', actionBack);
  eNext.addEventListener('click', actionNext);
  eSubmit.addEventListener('click', actionSubmit);
  eNextQuestion.addEventListener('click', actionNextQuestion);
  eInput.addEventListener('input', () => hide(eMsgEmpty));

  // hotkeys
  document.addEventListener('keydown', function (event) {
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
