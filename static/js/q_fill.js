document.addEventListener('DOMContentLoaded', function () {
    const eQuestion = document.getElementById('question-text');
    const eInput = document.getElementById('q-fill-input');
    const eNext = document.getElementById('next-question');
    const eBack = document.getElementById('back-question');
    const eSubmit = document.getElementById('q-fill-submit');
    const eMsg = document.getElementById('result-message');
    const form = document.getElementById('q-fill-form');

    let blanksNodes = Array.from(eQuestion.querySelectorAll('.blank'));
    blanksNodes.sort((a, b) => Number(a.dataset.num) - Number(b.dataset.num));

    let currentIndex = 0;
    let answers = [];

    function updateButtons() {
        eBack.classList.toggle("dnone", currentIndex === 0);
        eNext.classList.toggle("dnone", currentIndex >= blanksNodes.length - 1);
        eSubmit.classList.toggle("dnone", currentIndex < blanksNodes.length);
    }

    function showError(message) {
        eMsg.textContent = message;
        eMsg.style.display = "block";
        setTimeout(() => { eMsg.style.display = "none"; }, 2000);
    }

    function formatFilledText(text, maxLength) {
        return text.padEnd(maxLength, " ");  // Дополняем пробелами
    }

    function insertInput() {
        if (currentIndex < blanksNodes.length) {
            const blankEl = blanksNodes[currentIndex];
            let maxLength = blankEl.dataset.maxlength || blankEl.textContent.trim().length;
            blankEl.dataset.maxlength = maxLength; // Устанавливаем явно

            eInput.setAttribute("maxlength", maxLength);
            eInput.setAttribute("size", maxLength);
            eInput.value = "";
            blankEl.innerHTML = "";
            blankEl.appendChild(eInput);
            eInput.focus();
        }
        updateButtons();
    }

    function moveToNextBlank() {
        const userInput = eInput.value.trim();
        if (!userInput) {
            showError("Please enter a valid answer.");
            return;
        }

        const blankEl = blanksNodes[currentIndex];
        const maxLength = parseInt(blankEl.dataset.maxlength, 10);

        answers[currentIndex] = userInput;
        blankEl.innerHTML = formatFilledText(userInput, maxLength);
        blankEl.classList.add("filled");
        blankEl.classList.add('y', 'bg-y');

        if (currentIndex < blanksNodes.length - 1) {
            currentIndex++;
            insertInput();
        } else {
            updateButtons();
        }
    }

    function moveToPrevBlank() {
        if (currentIndex > 0) {
            const blankEl = blanksNodes[currentIndex];
            const maxLength = parseInt(blankEl.dataset.maxlength, 10);

            blankEl.innerHTML = "_".repeat(maxLength);
            blankEl.classList.remove("filled");
            answers.pop();
            currentIndex--;
            insertInput();
        }
    }

    eNext.addEventListener('click', moveToNextBlank);
    eBack.addEventListener('click', moveToPrevBlank);

    eInput.addEventListener('keydown', function (event) {
        if (event.key === "Enter" || event.key === "Tab") {
            event.preventDefault();
            moveToNextBlank();
        } else if (event.key === "Tab" && event.shiftKey) {
            event.preventDefault();
            moveToPrevBlank();
        }
    });

    insertInput();
});
