// begin profile section
document.addEventListener("DOMContentLoaded", function () {
  // --- Bagian untuk Sidebar ---
  const menuToggleBtn = document.getElementById("menu-toggle-btn");
  const sidebar = document.getElementById("sidebar");

  // Check if the elements exist before adding event listeners
  if (menuToggleBtn && sidebar) {
    menuToggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("collapsed");
    });
  }

  // --- Bagian BARU untuk Form Dinamis --
  const businessStatusSelect = document.getElementById("business-status");
  const ptkpField = document.getElementById("ptkp-field-wrapper");

  if (businessStatusSelect && ptkpField) {
    // Tambahkan event listener untuk \"mendengarkan\" perubahan
    businessStatusSelect.addEventListener("change", function () {
      // Cek apakah nilai yang dipilih adalah 'orang_pribadi'
      if (this.value === "orang_pribadi") {
        // Jika ya, hapus kelas 'hidden' untuk menampilkannya
        ptkpField.classList.remove("hidden");
      } else {
        // Jika tidak, tambahkan kelas 'hidden' untuk menyembunyikannya
        ptkpField.classList.add("hidden");
      }
    });
  }
});
// end profile section

// begin landing page section
// A function to handle closing modals to avoid repetition
const closeModal = (modal) => {
  modal.classList.add("hidden");
};

// A function to handle opening modals
const openModal = (modal) => {
  modal.classList.remove("hidden");
};

// --- ELEMEN UNTUK MODAL LOGIN ---
const loginBtn = document.getElementById("login-btn");
const loginModalOverlay = document.getElementById("login-modal-overlay");
const loginPasswordInput = document.getElementById("password");
const loginTogglePassword = document.querySelector(".toggle-password");

// --- ELEMEN UNTUK MODAL SIGN UP ---
const signupBtn = document.getElementById("signup-btn");
const createAccountBtn = document.getElementById("create-account-btn");
const signupModalOverlay = document.getElementById("signup-modal-overlay");
const signupPasswordInput = document.getElementById("signup-password");
const signupTogglePassword = document.querySelector(".toggle-password-signup");

// --- ELEMEN UNTUK BERALIH ANTAR MODAL ---
const showSignupLink = document.getElementById("show-signup-link");
const showLoginLink = document.getElementById("show-login-link");

// === FUNGSI UNTUK MODAL LOGIN ===
if (loginBtn) {
    loginBtn.addEventListener("click", () => openModal(loginModalOverlay));
    loginModalOverlay.addEventListener("click", (event) => {
      if (event.target === loginModalOverlay) closeModal(loginModalOverlay);
    });
    loginTogglePassword.addEventListener("click", function () {
      const type =
        loginPasswordInput.getAttribute("type") === "password"
          ? "text"
          : "password";
      loginPasswordInput.setAttribute("type", type);
      this.textContent = type === "password" ? "👁️" : "🙈";
    });
}

// === FUNGSI UNTUK MODAL SIGN UP ===
if(signupBtn && createAccountBtn) {
    signupBtn.addEventListener("click", () => openModal(signupModalOverlay));
    createAccountBtn.addEventListener("click", () => openModal(signupModalOverlay));
    signupModalOverlay.addEventListener("click", (event) => {
      if (event.target === signupModalOverlay) closeModal(signupModalOverlay);
    });
    signupTogglePassword.addEventListener("click", function () {
      const type =
        signupPasswordInput.getAttribute("type") === "password"
          ? "text"
          : "password";
      signupPasswordInput.setAttribute("type", type);
      this.textContent = type === "password" ? "👁️" : "🙈";
    });
}


// === FUNGSI UNTUK BERALIH ANTAR MODAL ===
if(showSignupLink && showLoginLink) {
    showSignupLink.addEventListener("click", (event) => {
      event.preventDefault();
      closeModal(loginModalOverlay);
      openModal(signupModalOverlay);
    });
    
    showLoginLink.addEventListener("click", (event) => {
      event.preventDefault();
      closeModal(signupModalOverlay);
      openModal(loginModalOverlay);
    });
}
