from flask import Flask, request, jsonify, send_from_directory
import subprocess
import tempfile
import pathlib
import sys

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
# ROOT points to the folder that contains this api.py as well as
# index.html and sat_solver.py.  We run the solver *from* that
# directory so relative imports / paths still work.
ROOT = pathlib.Path(__file__).parent.resolve()

app = Flask(__name__, static_folder=str(ROOT))


# ------------------------------------------------------------
# Static front‑end (index.html + any JS/CSS)
# ------------------------------------------------------------
@app.route("/")
def home():
    """Serve the Tailwind GUI."""
    assert type(app.static_folder) == str
    return send_from_directory(app.static_folder, "index.html")


# ------------------------------------------------------------
# /solve API  – accepts a graph .txt upload, returns JSON
# ------------------------------------------------------------
@app.post("/solve")
def solve():
    """Run the SAT‑solver on the uploaded graph and return the result."""

    # 1) Validate upload ----------------------------------------------------
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    assert file is not None
    assert file.content_type == "text/plain"
    edges = []
    # 2) Save the file to a temp dir so the solver can read it --------------
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_path = pathlib.Path(tmpdir) / "graph.txt"
        file.save(graph_path)

        # 3) Build & run the solver command ---------------------------------
        #    We always invoke the same Python interpreter (sys.executable)
        #    so the venv is respected. sat_solver.py must sit in ROOT.
        cmd = [sys.executable, "k_clique_sat.py", str(graph_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        with open(graph_path, "r") as f:
            _, lines, _ = f.readline().split()
            for _ in range(int(lines)):
                a, b = f.readline().split()
                edges.append((int(a), int(b)))
        points = set()
        for a, b in edges:
            points.add(a)
            points.add(b)

    # 4) Merge stdout + stderr for easier pattern matching ------------------
    solver_out = (result.stdout or "") + (result.stderr or "")

    # 5) Hard failure?  Non‑zero exit code → surface error to client --------
    if result.returncode != 0:
        return (
            jsonify(
                {
                    "sat": False,
                    "clique": [],
                    "message": f"Solver error (exit {result.returncode}):\n"
                    + solver_out[:500],
                }
            ),
            500,
        )

    # 6) Check (un)sat case‑insensitively -----------------------------------
    up_out = solver_out.upper()
    if "UNSAT" in up_out:
        return jsonify(
            {"sat": False, "clique": [], "points": list(points), "edges": edges}
        )

    if "SAT" not in up_out:
        # Not obviously SAT or UNSAT – treat as unknown/error
        return (
            jsonify(
                {
                    "sat": False,
                    "clique": [],
                    "message": "Solver output unclear. Raw output:\n" + solver_out,
                }
            ),
            500,
        )

    # 7) Parse clique vertices (optional) -----------------------------------
    clique = []
    try:
        # Our solver prints exactly: "Clique: v1 v2 v3 ..."
        if "Clique:" in solver_out:
            after = solver_out.split("Clique:")[1]
            clique = list(map(int, after.strip().split()))
    except Exception:
        # Parsing failed – leave clique empty but still SAT
        clique = []

    return jsonify(
        {"sat": True, "clique": clique, "points": list(points), "edges": edges}
    )


# ------------------------------------------------------------
# Development entry point (don't use in production!)
# ------------------------------------------------------------
if __name__ == "__main__":
    # Run with:  python api.py
    # Then open http://127.0.0.1:5000 in your browser.
    app.run(host="127.0.0.1", port=5000, debug=True)
