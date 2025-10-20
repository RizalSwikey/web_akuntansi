document.addEventListener("DOMContentLoaded", function () {
  // --- Bagian untuk Sidebar (Berfungsi di semua halaman) ---
  const menuToggleBtn = document.getElementById("menu-toggle-btn");
  const sidebar = document.getElementById("sidebar");
  if (menuToggleBtn && sidebar) {
    menuToggleBtn.addEventListener("click", () =>
      sidebar.classList.toggle("collapsed")
    );
  }

  // --- Elemen Alert (Bisa digunakan di banyak halaman) ---
  const successAlert = document.getElementById("success-alert");
  const errorAlert = document.getElementById("error-alert");
  const showAlert = (alertElement) => {
    if (alertElement) {
      alertElement.classList.remove("opacity-0", "pointer-events-none");
      setTimeout(() => {
        alertElement.classList.add("opacity-0", "pointer-events-none");
      }, 2000);
    }
  };

  // --- Logika HANYA untuk halaman Profile Perusahaan (dashboard.html) ---
  const profileNextBtn = document.getElementById("profile-next-btn");
  if (profileNextBtn) {
    // ... (kode validasi profile perusahaan)
  }

  // --- Logika HANYA untuk halaman Pendapatan (pendapatan.html) ---
  const addIncomeBtn = document.getElementById("add-income-btn");
  if (addIncomeBtn) {
    const addIncomeModal = document.getElementById("add-income-modal");
    const incomeForm = document.getElementById("income-form");
    // ... (semua logika untuk halaman pendapatan ada di sini)
    incomeForm.addEventListener("submit", function (event) {
      event.preventDefault();
      // ... (logika submit, validasi, dan kalkulasi pendapatan)
      showAlert(successAlert);
      // ...
    });
  }

  // =========================================================
  //      LOGIKA HANYA untuk halaman HPP (hpp.html)
  // =========================================================
  const addHppBtn = document.getElementById("add-hpp-btn");
  if (addHppBtn) {
    const addHppModal = document.getElementById("add-hpp-modal");
    const hppForm = document.getElementById("hpp-form");
    const hppDataType = document.getElementById("hpp-jenis-data");
    const awalFields = document.getElementById("hpp-awal-fields");
    const pembelianFields = document.getElementById("hpp-pembelian-fields");
    const akhirFields = document.getElementById("hpp-akhir-fields");
    let productData = {};

    const openHppModal = () =>
      addHppModal.classList.remove("opacity-0", "pointer-events-none");
    const closeHppModal = () => {
      /* ... logika close modal HPP ... */
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
      // ... (SEMUA LOGIKA VALIDASI, KALKULASI, DAN PENAMBAHAN BARIS HPP DI SINI)
      showAlert(successAlert);
      closeHppModal();
    });

    function updateGrandTotal(targetId, rowsSelector) {
      /* ... logika update total HPP ... */
    }
  }
});
