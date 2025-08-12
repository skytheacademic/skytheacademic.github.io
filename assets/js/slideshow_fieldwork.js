// slideshow_fieldwork.js

// Function to start the slideshow
function startSlideshow() {
  let currentIndex = 0;
  const baseurl = "{{ www.skytheacademic.com }}";
  const images = [
    `${baseurl}/images/fiji_1.jpg`,
    `${baseurl}/images/fiji_2.jpg`,
    `${baseurl}/images/fiji_3.jpg`,
    `${baseurl}/images/fiji_4.jpg`,
    `${baseurl}/images/fiji_5.jpg`,
    `${baseurl}/images/fiji_6.jpg`,
    `${baseurl}/images/fiji_7.jpg`
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
