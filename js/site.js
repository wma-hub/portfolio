/* WMA.NYC V3 - site.js */

/* Sticky nav scroll class */
(function () {
  var nav = document.querySelector('.site-nav');
  if (!nav) return;
  function onScroll() {
    nav.classList.toggle('scrolled', window.scrollY > 20);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* Fade-up on scroll, with stagger for row-like containers */
(function () {
  // fade-up sits on containers in these cases, so their children are
  // indexed and arrive in sequence rather than as one block
  var STAGGER = [
    '.card-row', '.wh-tiles', '.wh-surfaces', '.wh-stats',
    '.lockup-row', '.about-cols-inner', '.wh-zones', '.wh-pipeline'
  ].join(',');

  var els = [].slice.call(document.querySelectorAll('.fade-up'));

  els.forEach(function (el) {
    if (!el.matches(STAGGER)) return;
    var kids = [].slice.call(el.children);
    if (kids.length < 2) return;
    el.classList.add('stagger');
    kids.forEach(function (kid, i) { kid.style.setProperty('--i', i); });
  });

  if (!('IntersectionObserver' in window)) {
    els.forEach(function (el) { el.classList.add('visible'); });
    return;
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('visible');
      io.unobserve(e.target);
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(function (el) { io.observe(el); });
})();
