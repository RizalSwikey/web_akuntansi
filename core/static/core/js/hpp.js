// File: js/hpp.js
document.addEventListener("DOMContentLoaded", function () {
  const addHppBtn = document.getElementById("add-hpp-btn");
  const addHppModal = document.getElementById("add-hpp-modal");
  const hppForm = document.getElementById("hpp-form");
  const successAlert = document.getElementById("success-alert");
  const errorAlert = document.getElementById("error-alert");

  if (!addHppBtn) return;

  let productData = {};

  const hppDataType = document.getElementById("hpp-jenis-data");
  const awalFields = document.getElementById("hpp-awal-fields");
  const pembelianFields = document.getElementById("hpp-pembelian-fields");
  const akhirFields = document.getElementById("hpp-akhir-fields");

  const openHppModal = () =>
    addHppModal.classList.remove("opacity-0", "pointer-events-none");
  const closeHppModal = () => {
    addHppModal.classList.add("opacity-0", "pointer-events-none");
    hppForm.reset();
    awalFields.classList.remove("hidden");
    pembelianFields.classList.add("hidden");
    akhirFields.classList.add("hidden");
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
  addHppModal.addEventListener(
    "click",
    (e) => e.target === addHppModal && closeHppModal()
  );

  hppDataType.addEventListener("change", function () {
    awalFields.classList.toggle("hidden", this.value !== "persediaan_awal");
    pembelianFields.classList.toggle("hidden", this.value !== "pembelian");
    akhirFields.classList.toggle("hidden", this.value !== "persediaan_akhir");
  });

  hppForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const productName = document
      .getElementById("hpp-product-name")
      .value.trim();
    const dataType = hppDataType.value;
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
      const kuantitas = document.getElementById("hpp-awal-kuantitas").value;
      const keterangan = document.getElementById("hpp-awal-keterangan").value;
      const harga = document.getElementById("hpp-awal-harga").value;
      if (!kuantitas || !keterangan || !harga) {
        showAlert(errorAlert);
        return;
      }
      const total = (parseInt(kuantitas) || 0) * (parseInt(harga) || 0);
      productData[productName].qtyAwal += parseInt(kuantitas) || 0;
      productData[productName].totalValueAwal += total;
      const newRowHTML = `<div class="data-row grid grid-cols-5 gap-4 items-center py-2 px-4" data-total="${total}"><div class="flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${productName}</span></div><div>${kuantitas}</div><div>${keterangan}</div><div>${formatRupiah(
        harga
      )}</div><div>${formatRupiah(total)}</div></div>`;
      document
        .getElementById("persediaan-awal-rows")
        .insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-persediaan-awal", "#persediaan-awal-rows");
    } else if (dataType === "pembelian") {
      const kuantitas = document.getElementById(
        "hpp-pembelian-kuantitas"
      ).value;
      const keterangan = document.getElementById(
        "hpp-pembelian-keterangan"
      ).value;
      const harga = document.getElementById("hpp-pembelian-harga").value;
      const diskon = document.getElementById("hpp-pembelian-diskon").value;
      const retur = document.getElementById("hpp-pembelian-retur").value;
      const ongkir = document.getElementById("hpp-pembelian-ongkir").value;
      if (!kuantitas || !keterangan || !harga || !diskon || !retur || !ongkir) {
        showAlert(errorAlert);
        return;
      }
      const qty = parseInt(kuantitas) || 0,
        hrg = parseInt(harga) || 0,
        dsk = parseInt(diskon) || 0,
        rtr = parseInt(retur) || 0,
        ong = parseInt(ongkir) || 0;
      const jumlahRetur = rtr * hrg;
      const totalPembelian = qty * hrg - dsk - jumlahRetur + ong;
      productData[productName].qtyBeli += qty;
      productData[productName].totalValueBeli += totalPembelian;
      const uniqueId = Date.now();
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
      document
        .getElementById("pembelian-rows-part1")
        .insertAdjacentHTML("beforeend", row1HTML);
      document
        .getElementById("pembelian-rows-part2")
        .insertAdjacentHTML("beforeend", row2HTML);
      updateGrandTotal("jumlah-pembelian", "#pembelian-rows-part2");
    } else if (dataType === "persediaan_akhir") {
      const kuantitas = document.getElementById("hpp-akhir-kuantitas").value;
      const keterangan = document.getElementById("hpp-akhir-keterangan").value;
      if (!kuantitas || !keterangan) {
        showAlert(errorAlert);
        return;
      }
      const qtyInput = parseInt(kuantitas) || 0;
      const {
        qtyAwal = 0,
        totalValueAwal = 0,
        qtyBeli = 0,
        totalValueBeli = 0,
      } = productData[productName] || {};
      const totalQtyTersedia = qtyAwal + qtyBeli;
      const totalValueTersedia = totalValueAwal + totalValueBeli;

      let statusText = "Sesuai";
      let totalText;
      let totalValue = 0;

      const avgPrice =
        totalQtyTersedia > 0 ? totalValueTersedia / totalQtyTersedia : 0;
      totalValue = qtyInput * avgPrice;
      totalText = formatRupiah(totalValue); // Selalu hitung total dan format

      if (qtyInput > totalQtyTersedia) {
        totalText = `<span class='text-red-500 font-semibold'>Stok Tidak Cukup</span>`;
        statusText = `<span class='text-red-500 font-semibold'>Hitung Kembali</span>`;
        totalValue = 0;
      } else if (qtyInput === totalQtyTersedia && totalQtyTersedia > 0) {
        // Total sudah dihitung, hanya ubah status
        statusText = `<span class='text-yellow-500 font-semibold'>Periksa Penjualan</span>`;
      }

      const newRowHTML = `<div class="data-row grid grid-cols-5 gap-4 items-center py-2 px-4" data-total="${totalValue}"><div class="flex items-center gap-3"><button class="remove-row-btn text-slate-400 hover:text-red-500">${trashIconSVG}</button><span>${productName}</span></div><div>${qtyInput}</div><div>${keterangan}</div><div>${totalText}</div><div>${statusText}</div></div>`;
      document
        .getElementById("persediaan-akhir-rows")
        .insertAdjacentHTML("beforeend", newRowHTML);
      updateGrandTotal("jumlah-persediaan-akhir", "#persediaan-akhir-rows");
    }
    closeHppModal();
    showAlert(successAlert);
  });

  function updateGrandTotal(targetId, rowsSelector) {
    let grandTotal = 0;
    document.querySelectorAll(`${rowsSelector} .data-row`).forEach((row) => {
      grandTotal += parseFloat(row.dataset.total) || 0;
    });
    document.getElementById(targetId).textContent = `Rp ${new Intl.NumberFormat(
      "id-ID"
    ).format(Math.round(grandTotal))}`;
  }

  document
    .querySelector("#main-content")
    ?.addEventListener("click", function (event) {
      const removeBtn = event.target.closest(".remove-row-btn");
      if (removeBtn) {
        const row1 =
          removeBtn.closest(".data-row") || removeBtn.closest(".pembelian-row");
        if (!row1) return;
        const parentId1 = row1.parentElement.id;
        if (parentId1 === "pembelian-rows-part1") {
          const rowId = row1.dataset.id;
          const row2 = document.querySelector(
            `#pembelian-rows-part2 .pembelian-row[data-id="${rowId}"]`
          );
          if (row2) row2.remove();
          row1.remove();
          updateGrandTotal("jumlah-pembelian", "#pembelian-rows-part2");
        } else {
          row1.remove();
          if (parentId1.includes("persediaan-awal"))
            updateGrandTotal("jumlah-persediaan-awal", "#persediaan-awal-rows");
          else if (parentId1.includes("persediaan-akhir"))
            updateGrandTotal(
              "jumlah-persediaan-akhir",
              "#persediaan-akhir-rows"
            );
        }
      }
    });
});
