from flask import Flask, render_template, request, jsonify
import subprocess, os, uuid, tempfile, re

app = Flask(__name__, static_folder="static", template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    f = request.files["graph"]
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, f"{uuid.uuid4()}.txt")
    f.save(path)

    out = subprocess.check_output(["python3", "k_clique_sat.py", path]).decode()
    sat = re.search(r"^s SATISFIABLE", out, re.M) is not None
    clique = []
    if sat:
        m = re.search(r"Clique:\s*(.*)", out)
        if m:
            clique = list(map(int, m.group(1).split()))

    edges = []
    with open(path) as g:
        g.readline()
        for line in g:
            if line.strip():
                u, v = map(int, line.split())
                edges.append([u, v])

    return jsonify({"sat": sat, "clique": clique, "edges": edges})

if __name__ == "__main__":
    app.run(debug=True)
