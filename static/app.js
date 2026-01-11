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
  // selection format:
  // {
  //   "/abs/path/file.py": {
  //     "functions": ["foo"],
  //     "classes": { "MyClass": ["method1","method2"], "Other": [] },
  //     "include_full_classes": ["WholeClassName"]   (optional, but we will use classes key with method lists)
  //   }
  // }

  const selection = {};

  // Functions
  qsa(".child-cb").forEach(cb => {
    if (!cb.checked) return;
    const file = cb.dataset.file;
    const name = cb.dataset.name;
    selection[file] ??= { functions: [], classes: {} };
    selection[file].functions.push(name);
  });

  // Classes (whole class)
  qsa(".class-cb").forEach(cb => {
    if (!cb.checked) return;
    const file = cb.dataset.file;
    const cls = cb.dataset.name;
    selection[file] ??= { functions: [], classes: {} };

    // Mark class selected; methods may further refine
    // We will include the class shell AND only selected methods,
    // but if class is checked and no methods are checked, include whole class.
    selection[file].classes[cls] ??= null;
  });

  // Methods
  qsa(".method-cb").forEach(cb => {
    if (!cb.checked) return;
    const file = cb.dataset.file;
    const cls = cb.dataset.class;
    const name = cb.dataset.name;
    selection[file] ??= { functions: [], classes: {} };

    if (selection[file].classes[cls] === null) {
      // class selected as whole; keep null (meaning whole class)
      return;
    }
    if (!Array.isArray(selection[file].classes[cls])) {
      selection[file].classes[cls] = [];
    }
    selection[file].classes[cls].push(name);
  });

  // If class is checked but some methods are checked, we want method list.
  // We handle it by: if class cb checked and method cbs checked -> list methods (not whole class)
  // Do second pass:
  const classBlocks = qsa(".class-block");
  classBlocks.forEach(block => {
    const file = qs(".class-cb", block).dataset.file;
    const cls = block.dataset.class;
    const classCb = qs(".class-cb", block);
    const methodCbs = qsa(".method-cb", block);
    const checkedMethods = methodCbs.filter(m => m.checked).map(m => m.dataset.name);

    if (!classCb.checked) return;
    selection[file] ??= { functions: [], classes: {} };

    if (checkedMethods.length > 0) {
      selection[file].classes[cls] = checkedMethods;
    } else {
      selection[file].classes[cls] = null; // whole class
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
