// slideshow.js

// Function to start the slideshow
function startSlideshow() {
  let currentIndex = 0;
  const images = [
    'img_mountains_wide.jpg',
    'img_nature_wide.jpg',
    'img_snow_wide.jpg',
    // Add more image URLs here
  ];

  const imageElement = document.getElementById('slideshow-image');

  function showNextImage() {
    imageElement.src = images[currentIndex];
    currentIndex = (currentIndex + 1) % images.length;
  }

  // Start the slideshow
  setInterval(showNextImage, 3000); // Change images every 3 seconds
}
