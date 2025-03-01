document.addEventListener('DOMContentLoaded', function () {
  const eEstimation = getEl('#estimation');
  const ePoints = getEl('#points');
  const eQuestion = getEl('#question-text');
  const eForm = getEl('#question-form');
  const eInput = getEl('#form-input');
  const eSubmit = getEl('#form-btn-submit');
  const eNextQuestion = getEl('#form-btn-next-question');
  const eMsgResult = getEl('#msg-result');
  const eMsgEmpty = getEl('#msg-empty');
  const eStatElements = {}; // Хранилище для ссылок на элементы статистики
  const grades = ['N', 'F', 'D', 'C', 'B', 'A', 'S1', 'S2', 'S3'];
  grades.forEach(grade => {
    eStatElements[grade] = getEl(`.stat.${grade}`);
  });
  const eTotal = getEl('.total');
  const eSuspicious = getEl('.suspicious');
  // stats
  function updateStats(stat) {
    grades.forEach(grade => {
      if (eStatElements[grade]) {
        eStatElements[grade].textContent = `${grade}:${stat[grade] || 0}`;
      }
    });
    eTotal.textContent = `${stat.in_progress}/${stat.total}`;
    eSuspicious.textContent = `?:${stat.suspicious}`;
    // Обновление progress-bar
    const total = stat.total || 1;
    grades.forEach(grade => {
      const progressElement = getEl(`.sub-progress.${grade}`);
      if (progressElement) {
        progressElement.style.width = `${(stat[grade] / total * 100) || 0}%`;
      }
    });
  }

  let submitted = false;
  // Автофокус на поле ввода
  eInput.focus();
  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return;
    // Проверяем, введено ли хоть что-то
    if (!eInput.value.trim()) {
      show(eMsgEmpty);
      return;
    }
    hide(eMsgResult);
    submitted = true;

    const formData = new FormData(eForm);
    fetch(eForm.action, { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        // stats
        updateStats(data.stat);
        // estimation
        remCls(eEstimation, 'F', 'D', 'C', 'B', 'A');
        addCls(eEstimation, data.progress.estimation);
        eEstimation.textContent = data.progress.estimation + ':';
        ePoints.textContent = data.progress.points + '/' + data.progress.threshold;
        // question and spellcheck
        const eBlank = document.createElement('span');
        eBlank.innerHTML = highlightMistakes(data.answer, data.question.correct, data.is_correct);
        eQuestion.innerHTML = eQuestion.innerHTML.replace('___', eBlank.outerHTML);
        // input
        eInput.disabled = true;
        // buttons and messages
        addCls(eSubmit, data.is_correct ? 'btn-g' : 'btn-r');
        addCls(eNextQuestion, data.is_correct ? 'btn-g' : 'btn-r');
        addCls(eMsgResult, data.is_correct ? 'g' : 'r');
        eMsgResult.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
        hide(eSubmit);
        show(eNextQuestion, eMsgResult);
      }).catch(error => console.error('Error:', error));
  });

  // Обработчик кнопки "Next"
  eNextQuestion.addEventListener('click', () => {
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    window.location.href = '/topic/' + match[1];
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
