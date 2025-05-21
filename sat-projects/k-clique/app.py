from flask import Flask, request, jsonify, send_from_directory
import subprocess
import tempfile
import pathlib
import sys


ROOT = pathlib.Path(__file__).parent.resolve()

app = Flask(__name__, static_folder=str(ROOT))


@app.route("/")
def home():
    """Serve the Tailwind GUI."""
    assert type(app.static_folder) == str
    return send_from_directory(app.static_folder, "index.html")


@app.post("/solve")
def solve():
    """Run the SAT‑solver on the uploaded graph and return the result."""

    # Check for a file
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    assert file is not None
    assert file.content_type == "text/plain"
    edges = []
    # Read the graph file
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_path = pathlib.Path(tmpdir) / "graph.txt"
        file.save(graph_path)

        # Run the SAT solver
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

    # Check for empty file
    solver_out = (result.stdout or "") + (result.stderr or "")

    # Check for errors
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

    up_out = solver_out.upper()
    if "UNSAT" in up_out:
        return jsonify(
            {"sat": False, "clique": [], "points": list(points), "edges": edges}
        )

    if "SAT" not in up_out:
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

    # Check for a clique
    clique = []
    try:
        if "Clique:" in solver_out:
            after = solver_out.split("Clique:")[1]
            clique = list(map(int, after.strip().split()))
    except Exception:
        clique = []

    return jsonify(
        {"sat": True, "clique": clique, "points": list(points), "edges": edges}
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
