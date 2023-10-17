// slideshow.js

// Function to start the slideshow
function startSlideshow() {
  let currentIndex = 0;
  const images = [
    './images/car.svg',
    './images/drc_ug.svg',
    './images/car_1.svg',
    './images/men_map.svg',
    './images/women_map.svg'
    // Add more image URLs here
  ];

  const imageElement = document.getElementById('slideshow-image');

  function showNextImage() {
    imageElement.src = images[currentIndex];
    currentIndex = (currentIndex + 1) % images.length;
  }

  // Start the slideshow
  setInterval(showNextImage, 6000); // Change images every 6 seconds
}
