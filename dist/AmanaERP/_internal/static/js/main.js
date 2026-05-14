document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const html = document.documentElement;
      const mode = html.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
      html.setAttribute("data-bs-theme", mode);
      localStorage.setItem("ha-theme", mode);
    });
    const saved = localStorage.getItem("ha-theme");
    if (saved) document.documentElement.setAttribute("data-bs-theme", saved);
  }

  document.querySelectorAll(".js-data-table").forEach((table) => {
    const tbody = table.querySelector("tbody");
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll("tr"));
    let filtered = [...rows];
    let sortState = { idx: -1, asc: true };
    let page = 1;
    const pageSize = 10;

    const controls = document.createElement("div");
    controls.className = "d-flex justify-content-between align-items-center mb-2 gap-2";
    controls.innerHTML = `
      <input class="form-control form-control-sm" style="max-width:280px" placeholder="Search table...">
      <div class="btn-group btn-group-sm">
        <button type="button" class="btn btn-outline-secondary prev">Prev</button>
        <button type="button" class="btn btn-outline-secondary page">1</button>
        <button type="button" class="btn btn-outline-secondary next">Next</button>
      </div>
    `;
    table.parentElement.prepend(controls);
    const input = controls.querySelector("input");
    const prevBtn = controls.querySelector(".prev");
    const nextBtn = controls.querySelector(".next");
    const pageBtn = controls.querySelector(".page");

    function render() {
      const start = (page - 1) * pageSize;
      const end = start + pageSize;
      rows.forEach((r) => (r.style.display = "none"));
      filtered.slice(start, end).forEach((r) => (r.style.display = ""));
      const pages = Math.max(Math.ceil(filtered.length / pageSize), 1);
      page = Math.min(page, pages);
      pageBtn.textContent = `${page}/${pages}`;
    }

    table.querySelectorAll("th").forEach((th, idx) => {
      th.style.cursor = "pointer";
      th.addEventListener("click", () => {
        sortState.asc = sortState.idx === idx ? !sortState.asc : true;
        sortState.idx = idx;
        filtered.sort((a, b) => {
          const av = (a.children[idx]?.innerText || "").trim();
          const bv = (b.children[idx]?.innerText || "").trim();
          const an = Number(av.replace(/[^0-9.-]/g, ""));
          const bn = Number(bv.replace(/[^0-9.-]/g, ""));
          const bothNumeric = !Number.isNaN(an) && !Number.isNaN(bn) && av !== "" && bv !== "";
          if (bothNumeric) return sortState.asc ? an - bn : bn - an;
          return sortState.asc ? av.localeCompare(bv) : bv.localeCompare(av);
        });
        render();
      });
    });

    input.addEventListener("input", () => {
      const q = input.value.toLowerCase().trim();
      filtered = rows.filter((r) => r.innerText.toLowerCase().includes(q));
      page = 1;
      render();
    });
    prevBtn.addEventListener("click", () => {
      page = Math.max(1, page - 1);
      render();
    });
    nextBtn.addEventListener("click", () => {
      page += 1;
      render();
    });
    render();
  });

  const alerts = Array.from(document.querySelectorAll(".alert"));
  if (alerts.length) {
    const wrap = document.createElement("div");
    wrap.className = "toast-container position-fixed top-0 end-0 p-3";
    document.body.appendChild(wrap);
    alerts.forEach((alert) => {
      const toast = document.createElement("div");
      toast.className = "toast align-items-center text-bg-" + (alert.className.includes("danger") ? "danger" : alert.className.includes("warning") ? "warning" : "success") + " border-0";
      toast.setAttribute("role", "alert");
      toast.innerHTML = `<div class="d-flex"><div class="toast-body">${alert.textContent}</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
      wrap.appendChild(toast);
      bootstrap.Toast.getOrCreateInstance(toast, { delay: 3500 }).show();
      alert.remove();
    });
  }
});
