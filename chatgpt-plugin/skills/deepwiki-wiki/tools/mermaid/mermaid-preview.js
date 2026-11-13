import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs";

mermaid.initialize({
  startOnLoad: false,
  securityLevel: "strict",
  theme: "default",
  flowchart: { htmlLabels: false, curve: "basis" }
});

const source = document.getElementById("source");
const output = document.getElementById("output");
const status = document.getElementById("status");
const renderButton = document.getElementById("render");
const clearButton = document.getElementById("clear");

function extractBlocks(text) {
  const fenced = [...text.matchAll(/```mermaid\s*\n([\s\S]*?)```/gi)].map(m => m[1].trim());
  return fenced.length ? fenced : [text.trim()].filter(Boolean);
}

function safeError(error) {
  return error instanceof Error ? error.message : String(error);
}

renderButton.addEventListener("click", async () => {
  output.replaceChildren();
  const blocks = extractBlocks(source.value);
  if (!blocks.length) {
    status.textContent = "No Mermaid source found.";
    return;
  }

  const results = [];
  for (let index = 0; index < blocks.length; index += 1) {
    const host = document.createElement("article");
    host.className = "diagram";
    const heading = document.createElement("h2");
    heading.textContent = `Diagram ${index + 1}`;
    host.append(heading);
    const target = document.createElement("div");
    host.append(target);
    output.append(host);

    try {
      const id = `deepwiki-mermaid-${Date.now()}-${index}`;
      await mermaid.parse(blocks[index]);
      const rendered = await mermaid.render(id, blocks[index]);
      target.innerHTML = rendered.svg;
      results.push({ diagram: index + 1, ok: true });

      const download = document.createElement("button");
      download.textContent = "Download SVG";
      download.addEventListener("click", () => {
        const blob = new Blob([rendered.svg], { type: "image/svg+xml;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement("a");
        anchor.href = url;
        anchor.download = `diagram-${index + 1}.svg`;
        anchor.click();
        URL.revokeObjectURL(url);
      });
      host.append(download);
    } catch (error) {
      const message = document.createElement("pre");
      message.className = "error";
      message.textContent = safeError(error);
      target.append(message);
      results.push({ diagram: index + 1, ok: false, error: safeError(error) });
    }
  }

  const passed = results.filter(x => x.ok).length;
  const failed = results.length - passed;
  status.textContent = `Mermaid.js parse/render completed: ${passed} passed, ${failed} failed. This is a real browser Mermaid.js check, not a CLI run.`;
});

clearButton.addEventListener("click", () => {
  output.replaceChildren();
  status.textContent = "Output cleared.";
});
