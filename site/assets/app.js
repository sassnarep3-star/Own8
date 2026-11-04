// Own8 dashboard: client-side table filtering + click-to-sort. No dependencies.
(function () {
  "use strict";
  document.querySelectorAll(".filter").forEach(function (input) {
    var table = document.getElementById(input.getAttribute("data-table"));
    if (!table) return;
    input.addEventListener("input", function () {
      var q = input.value.toLowerCase().trim();
      table.querySelectorAll("tbody tr").forEach(function (tr) {
        tr.style.display = tr.textContent.toLowerCase().indexOf(q) > -1 ? "" : "none";
      });
    });
  });

  document.querySelectorAll("table.sortable thead th").forEach(function (th, col) {
    th.style.cursor = "pointer";
    th.title = "Click to sort";
    th.addEventListener("click", function () {
      var table = th.closest("table");
      var tbody = table.querySelector("tbody");
      var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
      var asc = th.getAttribute("data-asc") !== "true";
      th.setAttribute("data-asc", asc ? "true" : "false");
      rows.sort(function (a, b) {
        var x = a.children[col].textContent.trim();
        var y = b.children[col].textContent.trim();
        var nx = parseFloat(x.replace(/[^0-9.\-]/g, ""));
        var ny = parseFloat(y.replace(/[^0-9.\-]/g, ""));
        var cmp;
        if (!isNaN(nx) && !isNaN(ny) && x.match(/[0-9]/) && y.match(/[0-9]/)) cmp = nx - ny;
        else cmp = x.localeCompare(y);
        return asc ? cmp : -cmp;
      });
      rows.forEach(function (r) { tbody.appendChild(r); });
    });
  });
})();
