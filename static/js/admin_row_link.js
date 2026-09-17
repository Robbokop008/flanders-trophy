// Maakt tabelrijen met [data-href] klikbaar (opent de fiche), zonder de
// "markeer verwerkt"-knop/form binnenin de rij te kapen - zie
// templates/admin/offer_requests_list.html.
document.addEventListener("click", function (event) {
  const row = event.target.closest("tr[data-href]");
  if (!row) return;
  if (event.target.closest("a, button, form")) return;
  window.location.href = row.dataset.href;
});
