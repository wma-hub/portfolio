/* WMA.NYC V2 — site.js */

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

/* IntersectionObserver fade-up animations */
(function () {
  if (!('IntersectionObserver' in window)) {
    document.querySelectorAll('.fade-up').forEach(function (el) {
      el.classList.add('visible');
    });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12 });
  document.querySelectorAll('.fade-up').forEach(function (el) {
    io.observe(el);
  });
})();
