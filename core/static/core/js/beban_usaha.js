// File: core/static/core/js/beban_usaha.js
// This file now only handles the modal UI.
// All data logic (adding, deleting, totals) is handled by Django.

document.addEventListener("DOMContentLoaded", function () {
  const addBebanBtn = document.getElementById("add-beban-btn");
  const addBebanModal = document.getElementById("add-beban-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const bebanForm = document.getElementById("beban-form");

  if (addBebanBtn && addBebanModal && bebanForm) {
    // Function to open the modal
    const openModal = () =>
      addBebanModal.classList.remove("opacity-0", "pointer-events-none");

    // Function to close the modal
    const closeModal = () => {
      addBebanModal.classList.add("opacity-0", "pointer-events-none");
      bebanForm.reset(); // Clear the form for next time
    };

    // --- Event Listeners ---

    // 1. Open modal when "Tambah Data +" is clicked
    addBebanBtn.addEventListener("click", openModal);

    // 2. Close modal when "Batal" button is clicked
    modalCloseBtn.addEventListener("click", closeModal);

    // 3. Close modal when clicking on the dark overlay
    addBebanModal.addEventListener(
      "click",
      (e) => e.target === addBebanModal && closeModal()
    );

    // We have REMOVED the 'bebanForm.addEventListener("submit", ...)'
    // because the form now submits directly to Django.
  }
});