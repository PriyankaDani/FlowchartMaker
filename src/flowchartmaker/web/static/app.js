mermaid.initialize({ startOnLoad: false });

const form = document.getElementById("parse-form");
const loading = document.getElementById("loading");
const errorBox = document.getElementById("error");
const diagram = document.getElementById("diagram");
const download = document.getElementById("download");
let renderCount = 0;

function show(el, on) { el.hidden = !on; }

function showError(message) {
  errorBox.textContent = message;
  show(errorBox, true);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  show(errorBox, false);
  show(diagram, false);
  show(download, false);
  show(loading, true);
  try {
    const response = await fetch("/parse", { method: "POST", body: new FormData(form) });
    const body = await response.json();
    if (!response.ok) { showError(body.error); return; }
    const { svg } = await mermaid.render(`diagram-${renderCount++}`, body.mermaid);
    diagram.innerHTML = svg;
    show(diagram, true);
    await fetch("/svg", { method: "POST", headers: { "Content-Type": "image/svg+xml" }, body: svg });
    show(download, true);
  } catch (err) {
    showError("Something went wrong. Please try again.");
  } finally {
    show(loading, false);
  }
});
