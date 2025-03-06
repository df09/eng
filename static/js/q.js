import * as h from './helpers.js';

export const elements = {
  back: h.getEl('#form-btn-back'),
  checkboxes: h.getEls('.option-input'),
  estimation: h.getEl('#estimation'),
  extra: h.getEl('#extra-block'),
  form: h.getEl('#question-form'),
  hints: h.getEl('#hints'),
  input: h.getEl('#form-input'),
  labels: h.getEls('.option-label'),
  mainMenuLink: h.getEl('#main-menu-link'),
  msgEmpty: h.getEl('#msg-empty'),
  msgResult: h.getEl('#msg-result'),
  next: h.getEl('#form-btn-next'),
  nextQuestion: h.getEl('#form-btn-next-question'),
  points: h.getEl('#points'),
  question: h.getEl('#question-text'),
  submit: h.getEl('#form-btn-submit'),
  susFormWrap: h.getEl('#suspicious-form-wrap'),
  suspicious: h.getEl('#suspicious'),
  total: h.getEl('#total'),
};

export const grades = ['N', 'F', 'D', 'C', 'B', 'A'];
export const ist0 = elements.input?.dataset?.ist0 === '1';
export const eStatElements = {};

// Обновление статистики
export function updateStats(stat, tdata) {
  h.grades.forEach(grade => {
    if (eStatElements[grade]) {
      eStatElements[grade].textContent = `${grade}: ${stat[grade] || 0}`;
      h.remCls(eStatElements[grade], 'zero', ...h.grades);
      h.addCls(eStatElements[grade], stat[grade] === 0 ? 'zero' : grade);
    }
  });

  elements.total.textContent = `${stat.in_progress}/${tdata.total}`;
  elements.suspicious.textContent = `?:${tdata.suspicious}`;
  h.remCls(elements.suspicious, 'zero', 'found');
  h.addCls(elements.suspicious, tdata.suspicious === 0 ? 'zero' : 'found');

  updProgressBar(stat);
}

// Обновление прогресс-бара
export function updProgressBar(stat) {
  const total = stat.total || 1;
  h.grades.forEach(grade => {
    const progressElement = h.getEl(`.sub-progress.${grade}`);
    if (progressElement) {
      const width = ((stat[grade] || 0) / total * 100) || 0;
      progressElement.style.width = `${width}%`;
      width === 0 ? h.hide(progressElement) : h.show(progressElement);
    }
  });
}

// Переход к следующему вопросу
export function actionNextQuestion() {
  window.location.href = ist0 ? '/topic/0' : `/topic/${window.location.pathname.match(/\/topic\/(\d+)\//)[1]}`;
}

// Подсветка ошибок
export function highlightMistakes(userInput, correctInput) {
  return [...correctInput].map((char, i) => {
    const userChar = userInput[i] || '';
    const cls = userChar.toLowerCase() === char.toLowerCase() ? 'g bg-g' : 'r bg-r';
    return `<span class="${cls}">${char}</span>`;
  }).join('');
}
