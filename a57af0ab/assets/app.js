// Minimal client-side filter for tables. No network calls, no dependencies.
(function () {
  document.querySelectorAll('input[type="search"][data-target]').forEach(function (input) {
    var table = document.querySelector('table[data-filter="' + input.dataset.target + '"]');
    if (!table) return;
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      table.querySelectorAll('tbody tr').forEach(function (tr) {
        tr.style.display = !q || tr.textContent.toLowerCase().indexOf(q) !== -1 ? '' : 'none';
      });
    });
  });
})();
