#!/usr/bin/env python3
from __future__ import annotations
import importlib, json, threading, time, uuid, io, csv
from collections import defaultdict
from typing import List, Dict
from flask import Flask, request, jsonify, Response, send_from_directory, send_file

app = Flask(__name__, static_folder=".")
JOBS : Dict[str, List[str]] = defaultdict(list)   # jid -> SSE queue
FILES: Dict[str, bytes]     = {}                  # jid -> file bytes
NAMES: Dict[str, str]       = {}                  # jid -> filename

AVAILABLE = { "logP": "engines.logp", "QED": "engines.qed" }

# ── launch server and gather data ──────────────────────────────────────────────
def start_engine(target:str, seed:str, jid:str):
    rows = []                      # 保存 TSV 行
    def push(obj): JOBS[jid].append(json.dumps(obj))
    def record(r): rows.append(r)          # r = [iteration, smi, metric]

    mod = importlib.import_module(AVAILABLE[target])
    mod.run(seed, push, record)            # blocking; 引擎內不推 status

    # 生成 TSV
    buf = io.StringIO()
    w = csv.writer(buf, delimiter='\t')
    w.writerow(["Iteration", "SMILES", target])
    w.writerows(rows)
    FILES[jid] = buf.getvalue().encode()
    NAMES[jid] = f"{jid}_{target}.tsv"

    # 強化學習停止後下載就緒
    push({
        "msg": "🎉 完成！可以下載結果。",
        "download": f"/download/{jid}"
    })

# ── Flask appoint for html ────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "rl_molecule_form.html")

@app.route("/api/run", methods=["POST"])
def api_run():
    data   = request.get_json(force=True)
    seed   = (data.get("smiles") or [""])[0]
    target = data.get("target", "logP")
    if target not in AVAILABLE:
        return jsonify({"error": "unsupported target"}), 400

    jid = uuid.uuid4().hex; JOBS[jid] = []
    threading.Thread(target=start_engine,
                     args=(target, seed, jid), daemon=True).start()
    return jsonify({"stream_url": f"/stream/{jid}"})

@app.route("/stream/<jid>")
def stream(jid):
    if jid not in JOBS: return "Not found", 404
    def sse():
        idx=0
        while True:
            q = JOBS[jid]
            while idx < len(q):
                yield f"data: {q[idx]}\n\n"; idx+=1
            # 下載訊息推出後就結束
            if q and json.loads(q[-1]).get("download"): break
            time.sleep(.5)
    return Response(sse(), mimetype="text/event-stream")

@app.route("/download/<jid>")
def download(jid):
    if jid not in FILES: return "Not ready", 404
    return send_file(io.BytesIO(FILES[jid]), as_attachment=True,
                     download_name=NAMES[jid],
                     mimetype="text/tab-separated-values")

if __name__ == "__main__":
    print("✅ app.py ready  (logP / QED)")
    app.run(host="0.0.0.0", port=5000, debug=True)

