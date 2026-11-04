'use strict';
document.querySelectorAll('.filter').forEach(input => {
  const tools = input.closest('.table-tools');
  const wrap = tools.nextElementSibling;
  const rows = [...wrap.querySelectorAll('tbody tr')];
  const count = tools.querySelector('.count');
  const empty = wrap.nextElementSibling;
  input.addEventListener('input', () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;
    rows.forEach(row => {
      const match = row.textContent.toLocaleLowerCase().includes(query);
      row.hidden = !match;
      if (match) visible++;
    });
    count.textContent = `${visible} / ${rows.length} rows`;
    empty.hidden = visible !== 0;
  });
});
