document.addEventListener('DOMContentLoaded', function () {
  const topicRows = Array.from(document.querySelectorAll('.topic-row'));
  const topicLinks = {};
  
  const vimKeys = ['s', 'd', 'f', 'w', 'e', 'r', '2', '3', '4', 'c'];
  topicRows.forEach((row, i) => {
    if (i < vimKeys.length) {
      const link = row.querySelector('.topic-link');
      topicLinks[vimKeys[i]] = link;
    }
  });
  document.addEventListener('keydown', (event) => {
    if (topicLinks[event.key]) {
      event.preventDefault();
      topicLinks[event.key].click();
    }
  });
});
