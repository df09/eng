// DOM-manipulations.classes
function hide(...els){els.forEach(e=>e.classList.add('dnone'))};
function show(...els){els.forEach(e=>e.classList.remove('dnone'))};
function addCls(e, ...cls){cls.forEach(c=>{if(!e.classList.contains(c)){e.classList.add(c)}})}
function remCls(e, ...cls){cls.forEach(c=>{if(e.classList.contains(c)){e.classList.remove(c)}})}
// DOM-manipulations.get-elements
function getEl(selector, pass=false) {
  // get by id
  if (/^#[a-zA-Z0-9\-_\.]+$/.test(selector)) {
    const e = document.getElementById(selector.slice(1));
    if (!e) {
      if (pass) {return false}
      alert('"'+selector+'" not found.')
    }
    return e;
  }
  // get by any selector
  const els = document.querySelectorAll(selector);
  if (els.length === 0) {
    if (pass) {return false}
    alert('"'+selector+'" not found.')
  }
  if (els.length > 1) {
    alert('"'+selector+'" multiple found.')
  }
  e = els[0];
  return e;
}
function getEls(selector, pass=false) {
  const els = document.querySelectorAll(selector);
  if (els.length === 0) {
    if (pass) { return false; }
    alert('"' + selector + '" not found.');
  }
  return els;
}
// hotkeys
function getKey(event, keys, n) {
  const k = keys.split('+')[n];
  if (!k) return false;
  if (k === 'Shift') return event.shiftKey;
  if (k === 'Ctrl') return event.ctrlKey;
  if (k === 'Alt') return event.altKey;
  if (k === 'Meta') return event.metaKey;
  return event.key === k;
}

// helpers
function highlightMistakes(userInput, correctInput, is_correct) {
  let resultHTML = '';
  let len = Math.max(userInput.length, correctInput.length);
  for (let i = 0; i < len; i++) {
    let userChar = userInput[i] || '';
    let correctChar = correctInput[i] || '';
    let styles = userChar === correctChar ? 'g bg-g' : 'r bg-r';
    resultHTML += '<span class="' + styles + '">' + correctChar + '</span>';
  }
  return resultHTML;
}
