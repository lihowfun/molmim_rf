# engines/logp.py — RF logP + Similarity
import base64, io, numpy as np, requests, cma
from rdkit import Chem
from rdkit.Chem import AllChem, Crippen, DataStructs, Draw
from engines.config import DECODE, HEADERS, HIDDEN

# －－ option －－
POPSIZE, SIGMA, N_STEPS, MIN_POP = 64, 1.0, 50, 0.5  # MolMIM option

# －－ tool function －－
def tanimoto(a, b):
    fp_a = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(a), 2)
    fp_b = AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(b), 2)
    return DataStructs.TanimotoSimilarity(fp_a, fp_b)

def score(logps, sims):
    lp_t = np.clip(np.asarray(logps) / 5.0, 0, 1)
    sm_t = np.clip(np.asarray(sims)  / 0.4, 0, 1)
    return -1.0 * (lp_t + sm_t)

def mol_png_b64(mol):
    img = Draw.MolToImage(mol, size=(200, 200))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

# －－ main －－
def run(seed_smiles: str, push, record):
    """seed_smiles: 起始 SMILES  
       push(obj):    送到前端 (SSE)  
       record(row):  儲存 TSV，每 row=[iteration, smi, metric]"""
    # 起始分子
    seed_mol  = Chem.MolFromSmiles(seed_smiles)
    seed_logp = round(Crippen.MolLogP(seed_mol), 2)
    seed_img  = f"data:image/png;base64,{mol_png_b64(seed_mol)}"
    record([0, seed_smiles, seed_logp])       # Iteration 0 表 seed

    # 起始 hidden 向量
    h0 = np.asarray(
        requests.post(HIDDEN, headers=HEADERS,
            json={"sequences":[seed_smiles]}).json()["hiddens"][0]
    ).ravel()

    es = cma.CMAEvolutionStrategy(h0, SIGMA,
                                  {'popsize': POPSIZE, 'maxiter': 1e4})

    med_sim, med_lp = [], []

    for step in range(N_STEPS):
        # 1) generate candidate hidden
        ask  = [v.ravel() for v in es.ask()]              # list[512]
        enc3 = np.expand_dims(np.asarray(ask), 1)         # (pop,1,512)

        # 2) hidden → SMILES
        dec = requests.post(DECODE, headers=HEADERS,
               json={"hiddens": enc3.tolist(),
                     "mask": [[True]] * POPSIZE}).json()["generated"]

        uniq   = list(dict.fromkeys(dec))
        valids = [s for s in uniq if Chem.MolFromSmiles(s)]
        if not valids or len(valids) / POPSIZE < MIN_POP:
            push({"msg": "⛔ valid_ratio too low, stop"}); break

        # 3) estimate logP & similarity
        sims, lps = [], []
        for smi in valids:
            mol = Chem.MolFromSmiles(smi)
            sims.append(tanimoto(smi, seed_smiles))
            lps .append(Crippen.MolLogP(mol))
            record([step + 1, smi, round(lps[-1], 2)])       # TSV

        scr = score(lps, sims)

        # 4) SMILES → hidden，再 tell
        hid_vecs = [
            np.asarray(v).ravel() for v in
            requests.post(HIDDEN, headers=HEADERS,
                json={"sequences": valids}).json()["hiddens"]
        ]
        es.tell(hid_vecs, scr)

        # 5) statistic & publish
        med_sim.append(float(np.median(sims)))
        med_lp .append(float(np.median(np.clip(np.asarray(lps)/5.0,0,1))))

        top_idx = np.argsort(scr)[:8]
        top_cards = ([{"img": seed_img, "logp": seed_logp, "sim": 1.0}] +
                     [{"img": f"data:image/png;base64,{mol_png_b64(Chem.MolFromSmiles(valids[i]))}",
                       "logp": round(lps[i],2), "sim": round(sims[i],2)}
                      for i in top_idx])

        push({
          "iters": list(range(1, len(med_sim) + 1)),
          "med_sim": med_sim,
          "med_logp": med_lp,
          "top_mols": top_cards
        })
