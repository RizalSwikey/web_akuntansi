// File: core/static/core/js/pendapatan.js
// This file now only handles the modal UI.
// All data logic (adding, deleting, totals) is handled by Django.

document.addEventListener("DOMContentLoaded", function () {
  const addIncomeBtn = document.getElementById("add-income-btn");
  const addIncomeModal = document.getElementById("add-income-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn"); // Get the 'Batal' button
  const incomeForm = document.getElementById("income-form");

  if (addIncomeBtn && addIncomeModal && incomeForm) {
    const modalDataType = document.getElementById("modal-data-type");
    const modalUsahaFields = document.getElementById("modal-usaha-fields");
    // Corrected the ID based on your HTML file
    const modalLainFields = document.getElementById("modal-lain-total-field"); 

    // Function to open the modal
    const openModal = () =>
      addIncomeModal.classList.remove("opacity-0", "pointer-events-none");

    // Function to close the modal
    const closeModal = () => {
      addIncomeModal.classList.add("opacity-0", "pointer-events-none");
      incomeForm.reset(); // Clear the form for next time
      
      // Reset fields to default state (usaha visible)
      modalUsahaFields.classList.remove("hidden");
      modalLainFields.classList.add("hidden");
    };

    // --- Event Listeners ---

    // 1. Open modal when "Tambah Data +" is clicked
    addIncomeBtn.addEventListener("click", openModal);

    // 2. Close modal when "Batal" button is clicked
    modalCloseBtn.addEventListener("click", closeModal);

    // 3. Close modal when clicking on the dark overlay
    addIncomeModal.addEventListener(
      "click",
      (e) => e.target === addIncomeModal && closeModal()
    );

    // 4. Toggle fields inside the modal when dropdown changes
    modalDataType.addEventListener("change", function () {
      const isUsaha = this.value === "usaha";
      modalUsahaFields.classList.toggle("hidden", !isUsaha);
      modalLainFields.classList.toggle("hidden", isUsaha);
    });

    // We have REMOVED the 'incomeForm.addEventListener("submit", ...)'
    // because the form now submits directly to Django.
  }
});