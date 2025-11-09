document.addEventListener("DOMContentLoaded", function () {
  const addBebanBtn = document.getElementById("add-beban-btn");
  const addBebanModal = document.getElementById("add-beban-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const bebanForm = document.getElementById("beban-form");

  if (addBebanBtn && addBebanModal && bebanForm) {
    const openModal = () =>
      addBebanModal.classList.remove("opacity-0", "pointer-events-none");

    const closeModal = () => {
      addBebanModal.classList.add("opacity-0", "pointer-events-none");
      bebanForm.reset();
    };

    addBebanBtn.addEventListener("click", openModal);

    modalCloseBtn.addEventListener("click", closeModal);

    addBebanModal.addEventListener(
      "click",
      (e) => e.target === addBebanModal && closeModal()
    );

  }
});