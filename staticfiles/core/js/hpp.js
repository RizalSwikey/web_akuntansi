// File: js/hpp.js
document.addEventListener("DOMContentLoaded", function () {
  const addHppBtn = document.getElementById("add-hpp-btn");
  const addHppModal = document.getElementById("add-hpp-modal");
  const hppForm = document.getElementById("hpp-form");
  const successAlert = document.getElementById("success-alert");
  const errorAlert = document.getElementById("error-alert");

  if (!addHppBtn || !addHppModal || !hppForm) return; // Make sure all elements exist

  let productData = {};

  const hppDataType = document.getElementById("hpp-jenis-data");
  const awalFields = document.getElementById("hpp-awal-fields");
  const pembelianFields = document.getElementById("hpp-pembelian-fields");
  const akhirFields = document.getElementById("hpp-akhir-fields");

  const openHppModal = () => {
    if (addHppModal) {
      addHppModal.classList.remove("opacity-0", "pointer-events-none");
    }
  };
  const closeHppModal = () => {
    if (addHppModal) {
      addHppModal.classList.add("opacity-0", "pointer-events-none");
    }
    if (hppForm) {
      hppForm.reset();
    }
    // Reset field visibility
    if (awalFields) awalFields.classList.remove("hidden");
    if (pembelianFields) pembelianFields.classList.add("hidden");
    if (akhirFields) akhirFields.classList.add("hidden");
    if (hppDataType) hppDataType.value = "persediaan_awal"; // Reset dropdown
  };

  const showAlert = (alertElement) => {
    if (alertElement) {
      alertElement.classList.remove("opacity-0", "pointer-events-none");
      setTimeout(() => {
        alertElement.classList.add("opacity-0", "pointer-events-none");
      }, 2500);
    }
  };

  addHppBtn.addEventListener("click", openHppModal);
  if (addHppModal) {
    addHppModal.addEventListener(
      "click",
      (e) => e.target === addHppModal && closeHppModal()
    );
  }

  if (hppDataType) {
    hppDataType.addEventListener("change", function () {
      if (awalFields)
        awalFields.classList.toggle("hidden", this.value !== "persediaan_awal");
      if (pembelianFields)
        pembelianFields.classList.toggle("hidden", this.value !== "pembelian");
      if (akhirFields)
        akhirFields.classList.toggle(
          "hidden",
          this.value !== "persediaan_akhir"
        );
    });
  }

  hppForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const productNameInput = document.getElementById("hpp-product-name");
    const productName = productNameInput ? productNameInput.value.trim() : "";
    const dataType = hppDataType ? hppDataType.value : "";

    const formatRupiah = (number) =>
      new Intl.NumberFormat("id-ID").format(Math.round(number));

    if (!productName) {
      showAlert(errorAlert);
      return;
    }
    if (!productData[productName]) {
      productData[productName] = {
        qtyAwal: 0,
        totalValueAwal: 0,
        qtyBeli: 0,
        totalValueBeli: 0,
      };
    }

    const trashIconSVG = `<svg class="w-5 h-5 pointer-events-none" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.134-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.067-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" /></svg>`;

    if (dataType === "persediaan_awal") {
      const kuantitasInput = document.getElementById("hpp-awal-kuantitas");
      const keteranganInput = document.getElementById("hpp-awal-keterangan");
      const hargaInput = document.getElementById("hpp-awal-harga");

      const kuantitas = kuantitasInput ? kuantitasInput.value : "";
      const keterangan = keteranganInput ? keteranganInput.value.trim() : ""; // Add trim()
      const harga = hargaInput ? hargaInput.value : "";

      if (!kuantitas || !keterangan || !harga) {
        showAlert(errorAlert);
        return;
      }
      const qty = parseInt(kuantitas) || 0; // Parse quantity
      const hrg = parseInt(harga) || 0; // Parse price
      const total = qty * hrg; // Calculate total

      productData[productName].qtyAwal += qty; // Use parsed quantity
      productData[productName].totalValueAwal += total;

      const newRowHTML = `<div class="data-row grid grid-cols-5 gap-4 items-center py-2 px-4" data-total="${total}"><div class="flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${productName}</span></div><div>${qty}</div><div>${keterangan}</div><div>${formatRupiah(
        hrg
      )}</div><div>${formatRupiah(total)}</div></div>`;
      const persediaanAwalRows = document.getElementById(
        "persediaan-awal-rows"
      );
      if (persediaanAwalRows)
        persediaanAwalRows.insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-persediaan-awal", "#persediaan-awal-rows");
    } else if (dataType === "pembelian") {
      const kuantitasInput = document.getElementById("hpp-pembelian-kuantitas");
      const keteranganInput = document.getElementById(
        "hpp-pembelian-keterangan"
      );
      const hargaInput = document.getElementById("hpp-pembelian-harga");
      const diskonInput = document.getElementById("hpp-pembelian-diskon");
      const returInput = document.getElementById("hpp-pembelian-retur");
      const ongkirInput = document.getElementById("hpp-pembelian-ongkir");

      const kuantitas = kuantitasInput ? kuantitasInput.value : "";
      const keterangan = keteranganInput ? keteranganInput.value.trim() : ""; // Add trim()
      const harga = hargaInput ? hargaInput.value : "";
      const diskon = diskonInput ? diskonInput.value : "";
      const retur = returInput ? returInput.value : "";
      const ongkir = ongkirInput ? ongkirInput.value : "";

      // Check if ANY field is empty or just whitespace
      if (
        !kuantitas ||
        !keterangan ||
        !harga ||
        diskon.trim() === "" ||
        retur.trim() === "" ||
        ongkir.trim() === ""
      ) {
        showAlert(errorAlert);
        return;
      }

      const qty = parseInt(kuantitas) || 0;
      const hrg = parseInt(harga) || 0;
      const dsk = parseInt(diskon) || 0; // Allow 0
      const rtr = parseInt(retur) || 0; // Allow 0
      const ong = parseInt(ongkir) || 0; // Allow 0

      const jumlahRetur = rtr * hrg;
      const totalPembelian = qty * hrg - dsk - jumlahRetur + ong;

      productData[productName].qtyBeli += qty;
      productData[productName].totalValueBeli += totalPembelian;

      const uniqueId = Date.now(); // More reliable than just productName if multiple purchases of same item
      const row1HTML = `<div class="pembelian-row grid grid-cols-4 gap-4 items-center py-2 px-4" data-id="${uniqueId}"><div class="flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${productName}</span></div><div>${qty}</div><div>${keterangan}</div><div>${formatRupiah(
        hrg
      )}</div></div>`;
      const row2HTML = `<div class="data-row pembelian-row grid grid-cols-5 gap-4 items-center py-2 px-4" data-total="${totalPembelian}" data-id="${uniqueId}"><div>${formatRupiah(
        dsk
      )}</div><div>${rtr}</div><div>${formatRupiah(
        jumlahRetur
      )}</div><div>${formatRupiah(ong)}</div><div>${formatRupiah(
        totalPembelian
      )}</div></div>`;

      const pembelianRowsPart1 = document.getElementById(
        "pembelian-rows-part1"
      );
      const pembelianRowsPart2 = document.getElementById(
        "pembelian-rows-part2"
      );

      if (pembelianRowsPart1)
        pembelianRowsPart1.insertAdjacentHTML("beforeend", row1HTML);
      if (pembelianRowsPart2)
        pembelianRowsPart2.insertAdjacentHTML("beforeend", row2HTML);
      updateGrandTotal("jumlah-pembelian", "#pembelian-rows-part2");
    } else if (dataType === "persediaan_akhir") {
      const kuantitasInput = document.getElementById("hpp-akhir-kuantitas");
      const keteranganInput = document.getElementById("hpp-akhir-keterangan");

      const kuantitas = kuantitasInput ? kuantitasInput.value : "";
      const keterangan = keteranganInput ? keteranganInput.value.trim() : ""; // Add trim()

      if (!kuantitas || !keterangan) {
        showAlert(errorAlert);
        return;
      }
      const qtyInput = parseInt(kuantitas) || 0;
      const productInfo = productData[productName] || {
        qtyAwal: 0,
        totalValueAwal: 0,
        qtyBeli: 0,
        totalValueBeli: 0,
      };
      const { qtyAwal, totalValueAwal, qtyBeli, totalValueBeli } = productInfo;

      const totalQtyTersedia = qtyAwal + qtyBeli;
      const totalValueTersedia = totalValueAwal + totalValueBeli;

      let statusText = "Sesuai";
      let totalText;
      let totalValueAkhir = 0; // Renamed to avoid confusion

      // Calculate average price only if items were available
      const avgPrice =
        totalQtyTersedia > 0 ? totalValueTersedia / totalQtyTersedia : 0;
      totalValueAkhir = qtyInput * avgPrice;
      totalText = formatRupiah(totalValueAkhir); // Format the calculated value

      if (qtyInput > totalQtyTersedia) {
        totalText = `<span class='text-red-500 font-semibold'>Stok Tidak Cukup</span>`;
        statusText = `<span class='text-red-500 font-semibold'>Hitung Kembali</span>`;
        totalValueAkhir = 0; // Ensure data-total reflects the error state
      } else if (qtyInput === totalQtyTersedia && totalQtyTersedia > 0) {
        statusText = `<span class='text-yellow-500 font-semibold'>Periksa Penjualan</span>`;
        // Keep totalText as calculated value
      } else if (totalQtyTersedia === 0 && qtyInput > 0) {
        // Handle case where trying to set ending inventory for an item never held
        totalText = `<span class='text-red-500 font-semibold'>Stok Awal/Beli 0</span>`;
        statusText = `<span class='text-red-500 font-semibold'>Tidak Valid</span>`;
        totalValueAkhir = 0;
      }

      const newRowHTML = `<div class="data-row grid grid-cols-5 gap-4 items-center py-2 px-4" data-total="${totalValueAkhir}"><div class="flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${productName}</span></div><div>${qtyInput}</div><div>${keterangan}</div><div>${totalText}</div><div>${statusText}</div></div>`; // Use totalValueAkhir here
      const persediaanAkhirRows = document.getElementById(
        "persediaan-akhir-rows"
      );
      if (persediaanAkhirRows)
        persediaanAkhirRows.insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-persediaan-akhir", "#persediaan-akhir-rows");
    }

    closeHppModal();
    showAlert(successAlert);
  });

  function updateGrandTotal(targetId, rowsSelector) {
    let grandTotal = 0;
    const rows = document.querySelectorAll(`${rowsSelector} .data-row`);
    rows.forEach((row) => {
      // Only add if the value is a valid number (not NaN from error states)
      const total = parseFloat(row.dataset.total);
      if (!isNaN(total)) {
        grandTotal += total;
      }
    });
    const targetElement = document.getElementById(targetId);
    if (targetElement) {
      targetElement.textContent = `Rp ${new Intl.NumberFormat("id-ID").format(
        Math.round(grandTotal)
      )}`;
    }
  }

  // Attach event listener to a static parent element (#main-content exists on page load)
  const mainContent = document.querySelector("#main-content");
  if (mainContent) {
    mainContent.addEventListener("click", function (event) {
      const removeBtn = event.target.closest(".remove-row-btn");
      if (removeBtn) {
        const rowElement = removeBtn.closest(".data-row, .pembelian-row"); // Find the closest row (could be data-row or pembelian-row for part 1)
        if (!rowElement) return;

        const parentElement = rowElement.parentElement;
        if (!parentElement) return;

        const parentId = parentElement.id;

        // Special handling for 'pembelian' which has two rows per entry
        if (
          parentId === "pembelian-rows-part1" ||
          parentId === "pembelian-rows-part2"
        ) {
          const rowId = rowElement.dataset.id;
          if (rowId) {
            // Find both parts using the unique ID and remove them
            const rowPart1 = mainContent.querySelector(
              `.pembelian-row[data-id="${rowId}"]`
            );
            const rowPart2 = mainContent.querySelector(
              `.data-row.pembelian-row[data-id="${rowId}"]`
            );
            if (rowPart1) rowPart1.remove();
            if (rowPart2) rowPart2.remove();
            updateGrandTotal("jumlah-pembelian", "#pembelian-rows-part2");
          }
        } else {
          // Standard removal for 'persediaan_awal' and 'persediaan_akhir'
          rowElement.remove();
          if (parentId === "persediaan-awal-rows") {
            updateGrandTotal("jumlah-persediaan-awal", "#persediaan-awal-rows");
          } else if (parentId === "persediaan-akhir-rows") {
            updateGrandTotal(
              "jumlah-persediaan-akhir",
              "#persediaan-akhir-rows"
            );
          }
        }
      }
    });
  }
});
