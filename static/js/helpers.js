export const grades = ['N', 'F', 'D', 'C', 'B', 'A'];

// DOM-manipulations.classes
export function hide(...els) { els.forEach(e => e?.classList.add('dnone')); }
export function show(...els) { els.forEach(e => e?.classList.remove('dnone')); }
export function toggle(...els) { els.forEach(e => e?.classList.toggle('dnone')); }
export function isHidden(...els) { return els.every(e => e?.classList.contains('dnone')); }
export function isVisible(...els) { return els.every(e => !e?.classList.contains('dnone')); }
export function addCls(e, ...cls) { cls.forEach(c => e?.classList.add(c)); }
export function remCls(e, ...cls) { cls.forEach(c => e?.classList.remove(c)); }

// DOM-manipulations.get-elements
export function getEl(selector, pass = false) {
  if (!selector) return null;
  const e = document.querySelector(selector);
  if (!e && !pass) console.warn(`Element "${selector}" not found.`);
  return e;
}

export function getEls(selector, pass = false) {
  if (!selector) return [];
  const els = document.querySelectorAll(selector);
  if (els.length === 0 && !pass) console.warn(`Elements "${selector}" not found.`);
  return els;
}

// Hotkeys
export function hk(event, hotkeys, element, action) {
  if (!isVisible(element)) return;
  if (!Array.isArray(hotkeys)) hotkeys = [hotkeys];

  hotkeys.forEach(hk => {
    if (Array.isArray(hk)) {
      const [key, condition] = hk;
      if (event.key === key && condition) {
        event.preventDefault();
        setTimeout(() => action(event), 50);
      }
    } else if (event.key === hk) {
      event.preventDefault();
      setTimeout(() => action(event), 50);
    }
  });
}
