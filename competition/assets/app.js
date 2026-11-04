"use strict";
(() => {
  const toggle = document.querySelector(".menu-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && document.body.classList.contains("nav-open")) {
        document.body.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.focus();
      }
    });
    document.querySelectorAll(".sidebar a").forEach(a => a.addEventListener("click", () => {
      document.body.classList.remove("nav-open");
      toggle.setAttribute("aria-expanded", "false");
    }));
  }
  document.querySelectorAll(".table-card").forEach(card => {
    const table = card.querySelector("table");
    const body = table?.tBodies[0];
    if (!body) return;
    const input = card.querySelector("input[type=search]");
    const counter = card.querySelector(".row-count");
    const empty = card.querySelector(".table-empty");
    const rows = Array.from(body.rows);
    const update = () => {
      const terms = (input?.value || "").toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
      let visible = 0;
      rows.forEach(row => {
        const text = row.textContent.toLocaleLowerCase();
        row.hidden = !terms.every(term => text.includes(term));
        if (!row.hidden) visible++;
      });
      if (counter) counter.textContent = `${visible} of ${rows.length} rows`;
      if (empty) empty.classList.toggle("visible", visible === 0);
    };
    input?.addEventListener("input", update);
    card.querySelectorAll("thead button[data-column]").forEach(button => {
      button.addEventListener("click", () => {
        const column = Number(button.dataset.column);
        const th = button.closest("th");
        const asc = th.getAttribute("aria-sort") !== "ascending";
        card.querySelectorAll("th[aria-sort]").forEach(head => head.removeAttribute("aria-sort"));
        th.setAttribute("aria-sort", asc ? "ascending" : "descending");
        const normalized = cell => cell.textContent.trim().replace(/−/g, "-");
        const sorted = Array.from(body.rows).sort((left, right) => {
          const a = normalized(left.cells[column]);
          const b = normalized(right.cells[column]);
          if (!a && b) return 1;
          if (a && !b) return -1;
          if (!a && !b) return 0;
          const numeric = /^[-+]?\d+(\.\d+)?%?$/;
          const comparison = numeric.test(a) && numeric.test(b)
            ? parseFloat(a) - parseFloat(b)
            : a.localeCompare(b, undefined, {numeric: true, sensitivity: "base"});
          return asc ? comparison : -comparison;
        });
        sorted.forEach(row => body.append(row));
      });
    });
    update();
  });
  const dated = document.querySelector("[data-snapshot-date]");
  if (dated) {
    const snapshot = Date.parse(`${dated.dataset.snapshotDate}T00:00:00Z`);
    const days = Math.floor((Date.now() - snapshot) / 86400000);
    const warning = document.getElementById("snapshot-age");
    if (warning && Number.isFinite(days) && days > 1) {
      warning.textContent = `Historical snapshot: ${days} days since the checked date. Prices are not live; no current eligibility is implied.`;
      warning.setAttribute("role", "status");
    }
  }
})();
