from flask import Flask, request, jsonify, send_from_directory
import subprocess
import tempfile
import pathlib
import sys


ROOT = pathlib.Path(__file__).parent.resolve()

app = Flask(__name__, static_folder=str(ROOT))


@app.route("/")
def home():
    return app.send_static_file("index.html")


@app.post("/solve")
def solve():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    if file.mimetype != "text/plain":
        return jsonify({"error": "Only .txt accepted"}), 400

    edges = []
    with tempfile.TemporaryDirectory() as tmpdir:
        gpath = pathlib.Path(tmpdir) / "graph.txt"
        file.save(gpath)

        # read graph
        with open(gpath) as f:
            n, m, _ = map(int, f.readline().split())
            for _ in range(m):
                a, b = map(int, f.readline().split())
                edges.append((a, b))
        points = list(range(1,n+1))

        # run solver
        proc = subprocess.run(
            [sys.executable, "k_clique_sat.py", str(gpath)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )

    out = proc.stdout + proc.stderr
    if proc.returncode:
        return (
            jsonify({"sat": False, "clique": [], "message": out[:500]}),
            500,
        )

    up = out.upper()
    if "UNSAT" in up:
        return jsonify({"sat": False, "clique": [], "points": points, "edges": edges})

    if "SAT" not in up:
        return jsonify({"sat": False, "clique": [], "message": out}), 500

    clique = []
    if "Clique:" in out:
        clique = list(map(int, out.split("Clique:", 1)[1].split()))

    return jsonify({"sat": True, "clique": clique, "points": points, "edges": edges})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
