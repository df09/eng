document.addEventListener('DOMContentLoaded', function () {
  const topicRows = Array.from(document.querySelectorAll('.topic-row'));
  const topicLinks = {};
  
  // Собираем ссылки, привязывая их к ID топика
  topicRows.forEach(row => {
    const tid = row.dataset.topicId;
    const link = row.querySelector('.topic-link');
    if (tid < 10) topicLinks[tid] = link;
  });

  const vimKeys = ['s', 'd', 'f', 'g', 'x', 'c', 'v', 'b', 'j', 'k'];
  topicRows.forEach((row, i) => {
    const link = row.querySelector('.topic-link');
    if (i < vimKeys.length) topicLinks[vimKeys[i]] = link;
  });

  document.addEventListener('keydown', (event) => {
    if (topicLinks[event.key]) {
      event.preventDefault();
      topicLinks[event.key].click();
    }
  });
});
