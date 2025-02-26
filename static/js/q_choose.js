document.addEventListener('DOMContentLoaded', function () {
  const eForm = document.getElementById('q-choose-form');
  const eSubmit = document.getElementById('q-choose-submit');
  const eMsg = document.getElementById('result-message');
  const eNext = document.getElementById('next-question');
  const eLabels = document.querySelectorAll('.option-label');
  const eCheckboxes = document.querySelectorAll('.option-input');

  let submitted = false; // Флаг для блокировки изменений

  // Обработчик отправки формы
  eForm.addEventListener('submit', function (event) {
    event.preventDefault();
    if (submitted) return; // Предотвращаем повторный сабмит

    // Проверяем, выбран ли хотя бы один чекбокс
    const isChecked = Array.from(eCheckboxes).some(cb => cb.checked);
    if (!isChecked) {
      // Показываем сообщение о необходимости выбора
      let msgSelect = document.getElementById('msg-select');
      if (!msgSelect) {
        msgSelect = document.createElement('p');
        msgSelect.id = 'msg-select';
        msgSelect.className = 'result-message r'; // Красный цвет ошибки
        msgSelect.textContent = 'Please select at least one option.';
        eMsg.parentNode.insertBefore(msgSelect, eMsg);
      }
      msgSelect.classList.remove('dnone');
      return;
    }

    // Если выбор сделан, скрываем сообщение об ошибке
    const msgSelect = document.getElementById('msg-select');
    if (msgSelect) msgSelect.classList.add('dnone');

    submitted = true; // Флаг, что ответ уже отправлен
    const formData = new FormData(eForm);
    fetch(eForm.action, { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          eLabels.forEach(e => {
            const inputId = e.getAttribute('for');
            const input = getEl('#' + inputId);
            const value = input.value.trim();
            const option = e.querySelector('.option-text');

            // Блокировка кликов по чекбоксам
            input.addEventListener("click", function(event) {
              event.preventDefault();
            });
            // Блокировка изменения чекбоксов через клавиатуру
            input.disabled = true;
            // Убираем hover-эффект
            option.style.pointerEvents = 'none';
            remCls(option, 'hov');

            // options
            if (data.correct.includes(value)) {
              option.classList.remove('bg-w', 'brd-w');
              option.classList.add('g', 'bg-g', 'brd-g'); // Правильный
            } else if (input.checked) {
              option.classList.remove('bg-w', 'brd-w');
              option.classList.add('r', 'bg-r', 'brd-r'); // Неправильный, но выбранный
            }
            input.checked = false; // Снимаем выбор
          });

          // Скрываем submit, показываем next
          eSubmit.classList.add('dnone');
          eNext.classList.remove('dnone', 'btn-g', 'btn-r');
          eNext.classList.add(data.is_correct ? 'btn-g' : 'btn-r');

          // Сообщение Correct / Incorrect
          eMsg.classList.remove('dnone', 'g', 'r');
          eMsg.classList.add(data.is_correct ? 'g' : 'r');
          eMsg.textContent = data.is_correct ? 'Correct!' : 'Incorrect.';
        }
      })
      .catch(error => console.error('Error:', error));
  });

  // Обработчик кнопки "Next"
  eNext.addEventListener('click', () => {
    const match = window.location.pathname.match(/\/topic\/(\d+)\//);
    if (match) {
      window.location.href = '/topic/' + match[1];
    }
  });

  // Горячие клавиши
  const numKeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9'];
  const vimKeys = ['f', 'd', 's', 'a', 'g', 'j', 'k', 'l', ';', 'h']; // vim-like keys
  const keyMap = {};

  eCheckboxes.forEach((cb, i) => {
    const numKey = i < numKeys.length ? numKeys[i] : null;
    const vimKey = i < vimKeys.length ? vimKeys[i] : null;
    if (numKey) keyMap[numKey] = cb;
    if (vimKey) keyMap[vimKey] = cb;
  });

  document.addEventListener('keydown', (event) => {
    if (submitted) {
      if (event.key === 'Enter' && !eNext.classList.contains('dnone')) {
        event.preventDefault(); // Блокируем стандартное поведение
        setTimeout(() => eNext.click(), 50); // Небольшая задержка для избежания конфликтов
      }
      return;
    }

    // ENTER -> Submit
    if (event.key === 'Enter') {
      eSubmit.click();
    // Горячие клавиши для выбора
    } else if (keyMap[event.key]) {
      keyMap[event.key].checked = !keyMap[event.key].checked;
    }
  });
});
