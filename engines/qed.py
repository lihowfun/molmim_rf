# engines/qed.py — QED + Tanimoto (Median 統計版)

import base64, io, numpy as np, requests, cma
from rdkit import Chem, RDLogger
from rdkit.Chem import QED, Draw, AllChem, DataStructs
from engines.config import DECODE, HEADERS, HIDDEN

# 關閉 RDKit Warning（含 MorganGenerator deprecation）
RDLogger.DisableLog('rdApp.*')

# －－ 參數 －－
POPSIZE, SIGMA, N_STEPS, MIN_POP = 64, 1.0, 50, 0.5

# －－ 工具函式 －－
def tanimoto(a, b):
    fp_a = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(a), 2)
    fp_b = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(b), 2)
    return DataStructs.TanimotoSimilarity(fp_a, fp_b)

def score(qeds, sims):
    sim_t = np.clip(np.asarray(sims) / 0.4, 0, 1)
    return -1.0 * (np.asarray(qeds) + sim_t)

def mol_png_b64(mol):
    img = Draw.MolToImage(mol, size=(200, 200))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# －－ 主函式 －－
def run(seed_smiles: str, push, record):
    """
    seed_smiles : 起始 SMILES
    push(obj)   : 送即時資料到前端 (SSE)
    record(row) : 追加 row=[iteration, smi, QED] 寫 TSV
    """
    # 起始分子
    seed_mol = Chem.MolFromSmiles(seed_smiles)
    seed_qed = round(QED.qed(seed_mol), 3)
    seed_img = f"data:image/png;base64,{mol_png_b64(seed_mol)}"
    record([0, seed_smiles, seed_qed])           # Iteration 0 = seed

    # 起始 hidden 向量
    h0 = np.asarray(
        requests.post(HIDDEN, headers=HEADERS,
            json={"sequences": [seed_smiles]}).json()["hiddens"][0]
    ).ravel()

    es = cma.CMAEvolutionStrategy(h0, SIGMA,
                                  {'popsize': POPSIZE, 'maxiter': 1e4})

    med_qed, med_sim = [], []

    for step in range(N_STEPS):
        # 1) ask
        ask  = [v.ravel() for v in es.ask()]
        enc3 = np.expand_dims(np.asarray(ask), 1)

        # 2) hidden → SMILES
        dec = requests.post(
            DECODE, headers=HEADERS,
            json={"hiddens": enc3.tolist(), "mask": [[True]] * POPSIZE}
        ).json()["generated"]

        uniq   = list(dict.fromkeys(dec))
        valids = [s for s in uniq if Chem.MolFromSmiles(s)]
        if not valids or len(valids) / POPSIZE < MIN_POP:
            push({"msg": "⛔ valid_ratio too low, stop"}); break

        qeds, sims = [], []
        for smi in valids:
            mol = Chem.MolFromSmiles(smi)
            qeds.append(QED.qed(mol))
            sims.append(tanimoto(smi, seed_smiles))
            record([step + 1, smi, round(qeds[-1], 3)])

        scr = score(qeds, sims)

        # 3) SMILES → hidden 再 tell
        hid_vecs = [
            np.asarray(v).ravel() for v in
            requests.post(HIDDEN, headers=HEADERS,
                json={"sequences": valids}).json()["hiddens"]
        ]
        es.tell(hid_vecs, scr)

        # 4) 統計 median
        med_qed.append(float(np.median(qeds)))
        med_sim.append(float(np.median(sims)))

        # 5) 準備 Top-8 卡片（含 seed）
        top_idx  = np.argsort(scr)[:8]
        top_cards = (
            [{"img": seed_img, "qed": seed_qed, "sim": 1.0}] +
            [{"img": f"data:image/png;base64,{mol_png_b64(Chem.MolFromSmiles(valids[i]))}",
              "qed": round(qeds[i], 3), "sim": round(sims[i], 2)}
             for i in top_idx]
        )

        # 6) push 給前端 (使用 Median_qed / Median_sim)
        push({
            "iters":       list(range(1, len(med_qed) + 1)),
            "Median_qed":  med_qed,
            "Median_sim":  med_sim,
            "top_mols":    top_cards
        })
