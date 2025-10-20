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

// Fungsi untuk membuka modal
function openModal(modal) {
  modal.classList.remove("opacity-0", "pointer-events-none");
}

// Fungsi untuk menutup modal
function closeModal(modal) {
  modal.classList.add("opacity-0", "pointer-events-none");
}

// === FUNGSI UNTUK MODAL LOGIN ===
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

// === FUNGSI UNTUK MODAL SIGN UP ===
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

// === FUNGSI UNTUK BERALIH ANTAR MODAL ===
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
