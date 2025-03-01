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
  function highlightMistakes(userInput, correctInput) {
    let resultHTML = '';
    let len = Math.max(userInput.length, correctInput.length);
    for (let i = 0; i < len; i++) {
      let userChar = userInput[i] || ' ';
      let correctChar = correctInput[i] || ' ';
      let styles = userChar === correctChar ? 'g bg-g': 'r bg-r';
      resultHTML += styles ? '<span class="' + styles + '">' + correctChar + '</span>' : correctChar;
    }
    return resultHTML;
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
    
    fetch(eForm.action, {
      method: 'POST',
      body: new FormData(eForm)
    })
    .then(response => response.json())
    .then(data => {
      console.log('---------------');
      console.log('data:');
      console.log(data);
      // estimation
      remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
      addCls(eEstimation, data.progress.estimation);
      eEstimation.textContent = data.progress.estimation + ':';
      ePoints.textContent = data.progress.points + '/' + data.progress.threshhold;
      // spellcheck
      eBlanks.forEach((e, i) => {
          remCls(e, 'y', 'bg-y');
          let userAnswer = answers[i].trim();
          let correctAnswer = data.correct[i].replace(/^\[\d+\./, '').trim().slice(0, -1).trim();
          let maxLength = parseInt(e.dataset.maxlength, 10);
          let paddedCorrectAnswer = correctAnswer.padEnd(maxLength, ' ');
          console.log('------------------------');
          console.log('userAnswer:', userAnswer);
          console.log('correctAnswer:', correctAnswer);
          console.log('userAnswer === correctAnswer:', userAnswer === correctAnswer);
          if (userAnswer === correctAnswer) {
              addCls(e, 'g', 'bg-g');
              e.innerHTML = paddedCorrectAnswer;
          } else {
              e.innerHTML = highlightMistakes(userAnswer.padEnd(maxLength, ' '), paddedCorrectAnswer);
          }
      });
      // buttons and messages
      idx++;
      addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
      addCls(eMsgResult, data.is_correct ? 'g' : 'r');
      eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
      hide(eBack, eNext, eSubmit, eMsgEmpty);
      show(eNextQuestion, eMsgResult);
    })
    .catch(error => console.error('Error:', error));
  }
  function actionNextQuestion() {
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
