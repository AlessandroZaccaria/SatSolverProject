const upPane = document.getElementById("uploadPane");
upPane.innerHTML = `<div id="box">
 <input type="file" id="file" name="graph" accept=".txt" required>
 <button id="go">upload</button>
</div>
<p id="hint">it takes a graph header &lt;n&gt; &lt;m&gt; &lt;k&gt; followed by m edge lines,<br>runs the SAT solver and shows a clique or UNSAT</p>`;

const form = new FormData(),
  file = document.getElementById("file"),
  go = document.getElementById("go");
go.onclick = (e) => {
  if (!file.files[0]) return;
  form.set("graph", file.files[0]);
  fetch("/upload", { method: "POST", body: form })
    .then((r) => r.json())
    .then(show);
};

const resPane = document.getElementById("resultPane"),
  ans = document.getElementById("answer"),
  svg = document.getElementById("viz");
document.getElementById("again").onclick = (_) => location.reload();

function show(j) {
  upPane.classList.add("hidden");
  draw(j.edges, j.clique);
  ans.textContent = j.sat ? `Clique: ${j.clique.join(" ")}` : "UNSAT";
  resPane.classList.remove("hidden");
}

function draw(edges, clique) {
  svg.innerHTML = "";
  if (!edges.length) return;
  const n = Math.max(...edges.flat()),
    R = 220,
    cx = 400,
    cy = 240;
  const pos = [, ...Array(n)].map((_, i) => [cx + R * Math.cos((2 * Math.PI * i) / n), cy + R * Math.sin((2 * Math.PI * i) / n)]);
  edges.forEach(([u, v]) => {
    const l = elem("line", { x1: pos[u][0], y1: pos[u][1], x2: pos[v][0], y2: pos[v][1] });
    svg.appendChild(l);
  });
  for (let i = 1; i <= n; i++) {
    const g = elem("g"),
      isC = clique.includes(i);
    const c = elem("circle", { cx: pos[i][0], cy: pos[i][1], r: 16, class: isC ? "clique" : "" });
    const t = elem("text", { x: pos[i][0], y: pos[i][1] }, i);
    g.appendChild(c);
    g.appendChild(t);
    svg.appendChild(g);
  }
}

function elem(tag, attrs = {}, txt) {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (txt) e.textContent = txt;
  return e;
}
