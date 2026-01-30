function qs(sel, el = document) { return el.querySelector(sel); }
function qsa(sel, el = document) { return Array.from(el.querySelectorAll(sel)); }

function updateStats() {
  const fileCbs = qsa(".file-cb");
  const childCbs = qsa(".child-cb, .class-cb, .method-cb");
  const checkedFiles = fileCbs.filter(x => x.checked).length;
  const checkedItems = childCbs.filter(x => x.checked).length;
  qs("#stats").textContent = `Ausgewaehlt: ${checkedFiles} Dateien, ${checkedItems} Elemente`;
}

function setAll(checked) {
  qsa("input[type=checkbox]").forEach(cb => cb.checked = checked);
  updateStats();
}

function applyFilter(text) {
  const t = text.trim().toLowerCase();
  const fileNodes = qsa(".file-node");

  fileNodes.forEach(node => {
    const fileName = qs(".file-name", node).textContent.toLowerCase();

    // Match file itself?
    let matches = !t || fileName.includes(t);

    // Also check children labels
    if (!matches && t) {
      const childTexts = qsa(".children span", node).map(s => s.textContent.toLowerCase());
      matches = childTexts.some(s => s.includes(t));
    }

    node.style.display = matches ? "" : "none";
  });
}

function buildSelectionPayload(root) {
  const selection = {};

  // NUR angeklickte FILES sammeln
  document.querySelectorAll(".file-cb").forEach(cb => {
    if (cb.checked) {
      selection[cb.dataset.file] = true;
    }
  });

  return { root, selection };
}


function wireTree() {
  // File toggles children
  qsa(".file-cb").forEach(fileCb => {
    fileCb.addEventListener("change", (e) => {
      const file = e.target.dataset.file;
      const node = qs(`.file-node[data-file="${CSS.escape(file)}"]`);
      const all = qsa(`input[type=checkbox][data-file="${CSS.escape(file)}"]`, node)
        .filter(cb => cb !== e.target);
      all.forEach(cb => cb.checked = e.target.checked);
      updateStats();
    });
  });

  // Class toggles its methods
  qsa(".class-cb").forEach(classCb => {
    classCb.addEventListener("change", (e) => {
      const block = e.target.closest(".class-block");
      qsa(".method-cb", block).forEach(m => m.checked = e.target.checked);
      updateStats();
    });
  });

  // Child changes should update file checkbox state (indeterminate logic)
  function syncFileState(file) {
    const node = qs(`.file-node[data-file="${CSS.escape(file)}"]`);
    const fileCb = qs(".file-cb", node);
    const kids = qsa(`input[type=checkbox][data-file="${CSS.escape(file)}"]`, node)
      .filter(cb => cb !== fileCb);

    const checked = kids.filter(cb => cb.checked).length;
    if (checked === 0) {
      fileCb.indeterminate = false;
      fileCb.checked = false;
    } else if (checked === kids.length) {
      fileCb.indeterminate = false;
      fileCb.checked = true;
    } else {
      fileCb.indeterminate = true;
      fileCb.checked = false;
    }
  }

  qsa(".child-cb, .class-cb, .method-cb").forEach(cb => {
    cb.addEventListener("change", (e) => {
      const file = e.target.dataset.file;
      syncFileState(file);
      updateStats();
    });
  });

  // Collapse
  qsa(".toggle-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const node = btn.closest(".file-node");
      node.classList.toggle("collapsed");
    });
  });

  updateStats();
}

function wireTopBar() {
  qs("#reloadBtn").addEventListener("click", () => {
    const root = qs("#rootInput").value.trim() || ".";
    window.location.href = `/?root=${encodeURIComponent(root)}`;
  });

  qs("#filterInput").addEventListener("input", (e) => {
    applyFilter(e.target.value);
  });

  qs("#checkAllBtn").addEventListener("click", () => setAll(true));
  qs("#uncheckAllBtn").addEventListener("click", () => setAll(false));

  qs("#exportBtn").addEventListener("click", async () => {
    const root = qs("#rootInput").value.trim() || window.__INITIAL_ROOT__ || ".";
    const payload = buildSelectionPayload(root);

    const res = await fetch("/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (data.ok) {
      alert(`OK: gpt_bundle.txt erstellt\n${data.out_path}`);
    } else {
      alert("Fehler beim Export");
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  wireTopBar();
  wireTree();
});
