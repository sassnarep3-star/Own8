"use strict";

document.querySelectorAll(".table-tools input[type='search']").forEach((input) => {
  const tools = input.closest(".table-tools");
  const table = tools?.nextElementSibling?.querySelector("table");
  const counter = tools?.querySelector(".row-count");
  if (!table) return;
  const rows = Array.from(table.querySelectorAll("tbody tr"));
  const update = () => {
    const query = input.value.trim().toLocaleLowerCase();
    let visible = 0;
    rows.forEach((row) => {
      const show = row.textContent.toLocaleLowerCase().includes(query);
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (counter) counter.textContent = `${visible} of ${rows.length} rows`;
  };
  input.addEventListener("input", update);
});
