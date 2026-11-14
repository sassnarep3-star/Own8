// Lightweight table filter for the integration workspace (no dependencies).
document.addEventListener("input", function (ev) {
  if (ev.target.tagName !== "INPUT" || ev.target.type !== "search") return;
  const wrap = ev.target.closest(".table-tools");
  if (!wrap) return;
  const table = wrap.nextElementSibling;
  if (!table || table.tagName !== "DIV") return;
  const tbl = table.querySelector("table");
  if (!tbl) return;
  const q = ev.target.value.toLowerCase();
  let shown = 0;
  for (const tr of tbl.tBodies[0].rows) {
    const hit = tr.textContent.toLowerCase().includes(q);
    tr.style.display = hit ? "" : "none";
    if (hit) shown++;
  }
  const count = wrap.querySelector(".row-count");
  if (count) count.textContent = shown + " rows";
});
