document.addEventListener("DOMContentLoaded", function () {
  const addIncomeBtn = document.getElementById("add-income-btn");
  const addIncomeModal = document.getElementById("add-income-modal");
  const incomeForm = document.getElementById("income-form");
  const successAlert = document.getElementById("success-alert");
  const errorAlert = document.getElementById("error-alert");

  if (addIncomeBtn && addIncomeModal && incomeForm) {
    const modalDataType = document.getElementById("modal-data-type");
    const modalUsahaFields = document.getElementById("modal-usaha-fields");
    const modalLainTotalField = document.getElementById(
      "modal-lain-total-field"
    );

    const openModal = () =>
      addIncomeModal.classList.remove("opacity-0", "pointer-events-none");
    const closeModal = () => {
      addIncomeModal.classList.add("opacity-0", "pointer-events-none");
      incomeForm.reset();
      modalUsahaFields.classList.remove("hidden");
      modalLainTotalField.classList.add("hidden");
    };

    const showAlert = (alertElement) => {
      if (alertElement) {
        alertElement.classList.remove("opacity-0", "pointer-events-none");
        setTimeout(() => {
          alertElement.classList.add("opacity-0", "pointer-events-none");
        }, 2000);
      }
    };

    addIncomeBtn.addEventListener("click", openModal);
    addIncomeModal.addEventListener(
      "click",
      (e) => e.target === addIncomeModal && closeModal()
    );

    modalDataType.addEventListener("change", function () {
      const isUsaha = this.value === "usaha";
      modalUsahaFields.classList.toggle("hidden", !isUsaha);
      modalLainTotalField.classList.toggle("hidden", isUsaha);
    });

    incomeForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const productName = document
        .getElementById("modal-product-name")
        .value.trim();
      const dataType = modalDataType.value;
      const formatRupiah = (number) =>
        new Intl.NumberFormat("id-ID").format(number);
      const trashIconSVG = `<svg class="w-5 h-5 pointer-events-none" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.134-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.067-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" /></svg>`; // Define trash icon SVG

      if (dataType === "usaha") {
        const quantity = document.getElementById("modal-quantity").value;
        const price = document.getElementById("modal-price").value;

        if (!productName || !quantity || !price) {
          showAlert(errorAlert);
          return;
        }

        const total = (parseInt(quantity) || 0) * (parseInt(price) || 0);
        const newRowHTML = `<div class="data-row grid grid-cols-10 gap-4 items-center py-2 px-4" data-total="${total}"><button class="remove-row-btn text-slate-400 hover:text-red-500 -mr-2">${trashIconSVG}</button><div class="col-span-3 p-3">${productName}</div><div class="col-span-2 p-3">${quantity}</div><div class="col-span-2 p-3">${formatRupiah(
          price
        )}</div><div class="col-span-2 p-3 font-semibold">${formatRupiah(
          total
        )}</div></div>`;
        document
          .getElementById("pendapatan-usaha-rows")
          .insertAdjacentHTML("beforeend", newRowHTML);
        updateGrandTotal("usaha");
      } else {
        // Pendapatan Lain-lain
        const totalValue = document.getElementById("modal-total").value;
        if (!productName || !totalValue) {
          showAlert(errorAlert);
          return;
        }
        const total = parseInt(totalValue) || 0;
        const newRowHTML = `<div class="data-row grid grid-cols-10 gap-4 items-center py-2 px-4" data-total="${total}"><button class="remove-row-btn text-slate-400 hover:text-red-500 -mr-2">${trashIconSVG}</button><div class="col-span-7 p-3">${productName}</div><div class="col-span-2 p-3 font-semibold">${formatRupiah(
          total
        )}</div></div>`;
        document
          .getElementById("pendapatan-lain-rows")
          .insertAdjacentHTML("beforeend", newRowHTML);
        updateGrandTotal("lain");
      }
      closeModal();
      showAlert(successAlert);
    });

    function updateGrandTotal(type) {
      let grandTotal = 0;
      const selector =
        type === "usaha"
          ? "#pendapatan-usaha-rows .data-row"
          : "#pendapatan-lain-rows .data-row";
      document.querySelectorAll(selector).forEach((row) => {
        grandTotal += parseFloat(row.dataset.total) || 0;
      });
      const targetElementId =
        type === "usaha" ? "jumlah-penjualan-usaha" : "jumlah-penjualan-lain";
      document.getElementById(
        targetElementId
      ).textContent = `Rp ${new Intl.NumberFormat("id-ID").format(grandTotal)}`;
    }

    // Event listener for removing rows needs to be attached to a parent element
    // that exists when the page loads, like #main-content or the table body itself.
    document
      .querySelector("#main-content")
      .addEventListener("click", function (event) {
        const removeBtn = event.target.closest(".remove-row-btn");
        if (removeBtn) {
          const row = removeBtn.closest(".data-row");
          if (row) {
            // Check if the row exists before trying to access parentElement
            const parentId = row.parentElement.id; // Get parent ID before removing
            row.remove();
            // Check parentId to decide which total to update
            if (parentId === "pendapatan-usaha-rows") {
              updateGrandTotal("usaha");
            } else if (parentId === "pendapatan-lain-rows") {
              updateGrandTotal("lain");
            }
          }
        }
      });
  }
});
