'use strict';
// Table filter. Each .table-tools block filters the table that follows it.
document.querySelectorAll('.table-tools').forEach(function (tools) {
  var wrap = tools.nextElementSibling;
  if (!wrap) return;
  var table = wrap.querySelector('table');
  if (!table || !table.tBodies.length) return;
  var input = tools.querySelector('input');
  var count = tools.querySelector('.row-count');
  var rows = Array.prototype.slice.call(table.tBodies[0].rows);
  if (count) count.textContent = rows.length + ' rows';
  if (!input) return;
  input.addEventListener('input', function () {
    var q = input.value.toLocaleLowerCase().trim();
    var visible = 0;
    rows.forEach(function (row) {
      row.hidden = q !== '' && row.textContent.toLocaleLowerCase().indexOf(q) === -1;
      if (!row.hidden) visible++;
    });
    if (count) count.textContent = visible + ' / ' + rows.length + ' rows';
  });
});
