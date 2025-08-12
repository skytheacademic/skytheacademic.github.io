// slideshow_fieldwork.js
function startSlideshow() {
  let i = 0;
  const images = [
    '/images/fiji_1.jpg',
    '/images/fiji_2.jpg',
    '/images/fiji_3.jpg',
    '/images/fiji_4.jpg',
    '/images/fiji_5.jpg',
    '/images/fiji_6.jpg',
    '/images/fiji_7.jpg'
  ].map(p => new URL(p, window.location.origin).href);

  const el = document.getElementById('slideshow-image');
  function next() { el.src = images[i]; i = (i + 1) % images.length; }
  next();
  setInterval(next, 6000);
}