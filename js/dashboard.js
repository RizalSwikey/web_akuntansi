// File: js/dashboard.js

document.addEventListener("DOMContentLoaded", function () {
  // --- Bagian untuk mengurus Sidebar ---
  const menuToggleBtn = document.getElementById("menu-toggle-btn");
  const sidebar = document.getElementById("sidebar");

  // Tambahkan event listener ke tombol ikon menu ☰
  menuToggleBtn.addEventListener("click", function () {
    // Ini akan menambah atau menghapus kelas 'collapsed' pada sidebar
    sidebar.classList.toggle("collapsed");
  });

  // --- Bagian untuk mengurus Form Dinamis ---
  const businessStatusSelect = document.getElementById("business-status");
  const ptkpField = document.getElementById("ptkp-field-wrapper");

  // Tambahkan event listener untuk "mendengarkan" perubahan pada dropdown Status Usaha
  businessStatusSelect.addEventListener("change", function () {
    // Cek apakah nilai yang dipilih adalah 'orang_pribadi'
    if (this.value === "orang_pribadi") {
      // Jika ya, hapus kelas 'hidden' untuk menampilkannya
      ptkpField.classList.remove("hidden");
    } else {
      // Jika tidak (atau pilihannya kosong), tambahkan lagi kelas 'hidden' untuk menyembunyikannya
      ptkpField.classList.add("hidden");
    }
  });
});
