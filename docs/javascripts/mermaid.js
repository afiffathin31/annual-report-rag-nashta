document$.subscribe(() => {
  if (typeof mermaid === "undefined") return;

  const isDark = document.body.getAttribute("data-md-color-scheme") === "slate";
  mermaid.initialize({
    startOnLoad: false,
    theme: isDark ? "dark" : "default",
    securityLevel: "loose",
    fontFamily: "Inter, sans-serif"
  });

  // Material for MkDocs wraps mermaid in <pre class="mermaid"><code>...</code></pre>
  const mermaidNodes = document.querySelectorAll(".mermaid");
  if (mermaidNodes.length > 0) {
    mermaid.run({
      nodes: mermaidNodes
    });
  }
});
