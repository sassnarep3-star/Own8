'use strict';
const search = document.getElementById('row-search');
if (search) search.addEventListener('input', () => {
  const query = search.value.trim().toLowerCase();
  document.querySelectorAll('table').forEach(table => {
    let shown = 0;
    table.querySelectorAll('tbody tr').forEach(row => {
      row.hidden = !row.textContent.toLowerCase().includes(query);
      if (!row.hidden) shown++;
    });
    const empty = table.parentElement.nextElementSibling;
    if (empty && empty.classList.contains('no-results')) empty.hidden = shown > 0;
  });
});
document.querySelectorAll('th .sort').forEach(button => button.addEventListener('click', () => {
  const th = button.closest('th');
  const table = button.closest('table');
  const index = Array.from(th.parentElement.children).indexOf(th);
  const direction = th.getAttribute('aria-sort') === 'ascending' ? -1 : 1;
  table.querySelectorAll('th').forEach(header => header.removeAttribute('aria-sort'));
  th.setAttribute('aria-sort', direction === 1 ? 'ascending' : 'descending');
  const body = table.tBodies[0];
  Array.from(body.rows).sort((a, b) => {
    const x = a.cells[index].textContent.trim(), y = b.cells[index].textContent.trim();
    if (!x || !y) return x === y ? 0 : x ? -1 : 1;
    const nx = Number(x), ny = Number(y);
    return direction * (Number.isFinite(nx) && Number.isFinite(ny) ? nx - ny : x.localeCompare(y));
  }).forEach(row => body.appendChild(row));
}));
