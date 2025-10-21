// File: js/beban_usaha.js
document.addEventListener("DOMContentLoaded", function () {
  const addBebanBtn = document.getElementById("add-beban-btn");
  const addBebanModal = document.getElementById("add-beban-modal");
  const bebanForm = document.getElementById("beban-form");
  const successAlert = document.getElementById("success-alert");
  const errorAlert = document.getElementById("error-alert");

  if (!addBebanBtn || !addBebanModal || !bebanForm) return; // Make sure all elements exist

  const openModal = () => {
    if (addBebanModal) {
      addBebanModal.classList.remove("opacity-0", "pointer-events-none");
    }
  };
  const closeModal = () => {
    if (addBebanModal) {
      addBebanModal.classList.add("opacity-0", "pointer-events-none");
    }
    if (bebanForm) {
      bebanForm.reset();
    }
  };
  const showAlert = (alertElement) => {
    if (alertElement) {
      alertElement.classList.remove("opacity-0", "pointer-events-none");
      setTimeout(() => {
        alertElement.classList.add("opacity-0", "pointer-events-none");
      }, 2000);
    }
  };
  const formatRupiah = (number) =>
    new Intl.NumberFormat("id-ID").format(number);

  const trashIconSVG = `<svg class="w-5 h-5 pointer-events-none" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.134-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.067-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" /></svg>`;

  addBebanBtn.addEventListener("click", openModal);
  if (addBebanModal) {
    addBebanModal.addEventListener("click", (e) => {
      if (e.target === addBebanModal) closeModal();
    });
  }

  bebanForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const nomorInput = document.getElementById("modal-nomor");
    const jenisBebanSelect = document.getElementById("modal-jenis-beban");
    const keteranganInput = document.getElementById("modal-keterangan");
    const totalBiayaInput = document.getElementById("modal-total-biaya");
    const jenisDataSelect = document.getElementById("modal-jenis-data");

    const nomor = nomorInput ? nomorInput.value.trim() : "";
    const jenisBeban = jenisBebanSelect ? jenisBebanSelect.value : "";
    const keterangan = keteranganInput ? keteranganInput.value.trim() : "";
    const totalBiaya = totalBiayaInput ? totalBiayaInput.value : "";
    const jenisData = jenisDataSelect ? jenisDataSelect.value : "";

    if (!nomor || !jenisBeban || !keterangan || !totalBiaya) {
      showAlert(errorAlert);
      return;
    }
    const total = parseInt(totalBiaya) || 0;
    const newRowHTML = `<div class="data-row grid grid-cols-8 gap-4 items-center py-2 px-4" data-total="${total}"><div class="col-span-1 flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${nomor}</span></div><div class="col-span-3">${jenisBeban}</div><div class="col-span-2">${keterangan}</div><div class="col-span-2">${formatRupiah(
      total
    )}</div></div>`;

    const bebanUsahaRows = document.getElementById("beban-usaha-rows");
    const bebanLainRows = document.getElementById("beban-lain-rows");

    if (jenisData === "beban_usaha") {
      if (bebanUsahaRows)
        bebanUsahaRows.insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-beban-usaha", "#beban-usaha-rows");
    } else {
      if (bebanLainRows)
        bebanLainRows.insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-beban-lain", "#beban-lain-rows");
    }
    closeModal();
    showAlert(successAlert);
  });

  function updateGrandTotal(targetId, rowsSelector) {
    let grandTotal = 0;
    document.querySelectorAll(`${rowsSelector} .data-row`).forEach((row) => {
      grandTotal += parseFloat(row.dataset.total) || 0;
    });
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      targetElement.textContent = `Rp ${formatRupiah(grandTotal)}`;
    }
  }

  // Attach event listener to a static parent element
  const mainContent = document.getElementById("main-content");
  if (mainContent) {
    mainContent.addEventListener("click", function (event) {
      const removeBtn = event.target.closest(".remove-row-btn");
      if (removeBtn) {
        const row = removeBtn.closest(".data-row");
        if (row) {
          const parentElement = row.parentElement;
          if (!parentElement) return;
          const parentId = parentElement.id;
          row.remove();
          if (parentId === "beban-usaha-rows")
            updateGrandTotal("jumlah-beban-usaha", "#beban-usaha-rows");
          else if (parentId === "beban-lain-rows")
            updateGrandTotal("jumlah-beban-lain", "#beban-lain-rows");
        }
      }
    });
  }
});
