// slideshow.js

// Function to start the slideshow
function startSlideshow() {
  let currentIndex = 0;
  const images = [
    './images/car.svg',
    './images/fiji_2.jpg',
    './images/fiji_3.jpg',
    './images/fiji_4.jpg',
    './images/fiji_5.jpg',
    './images/fiji_6.jpg',
    './images/fiji_7.jpg'
  ];

  const imageElement = document.getElementById('slideshow-image');

  function showNextImage() {
    imageElement.src = images[currentIndex];
    currentIndex = (currentIndex + 1) % images.length;
  }

  // Show the first image immediately
  showNextImage();

  // Start the slideshow
  setInterval(showNextImage, 6000); // Change images every 6 seconds
}
