document.addEventListener("DOMContentLoaded", function () {
  const businessStatusSelect = document.getElementById("business_status");
  const ptkpField = document.getElementById("ptkp-field-wrapper");

  if (businessStatusSelect && ptkpField) {
    function togglePTKPField() {
      if (businessStatusSelect.value === "orang_pribadi") {
        ptkpField.classList.remove("hidden");
      } else {
        ptkpField.classList.add("hidden");
      }
    }
    togglePTKPField();
    businessStatusSelect.addEventListener("change", togglePTKPField);
  }

});
