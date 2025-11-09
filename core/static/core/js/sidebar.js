document.addEventListener("DOMContentLoaded", function () {
  const menuToggleBtn = document.getElementById("menu-toggle-btn");
  const sidebar = document.getElementById("sidebar");
  if (menuToggleBtn && sidebar) {
    menuToggleBtn.addEventListener("click", () =>
      sidebar.classList.toggle("collapsed")
    );
  }
});
