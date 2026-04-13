## MolMIM Reinforcement Learning Web Interface

`molmim_rf` 是一個基於 **Flask** + **Server-Sent Events (SSE)** + 原生 **HTML/CSS/JS** 的 MolMIM 快速上手介面，讓你可以從 seed SMILES 出發，快速試跑多目標分子優化流程。

目前公開版提供兩個範本目標：

- `logP`
- `QED`

這個 repo 的定位是輕量、可快速改造的研究樣板。後續可以沿著相同結構擴充更多目標函數，例如以親和力為目標，串接 DiffDock 類型流程做優化。

## 專案結構

```text
molmim_rf/
├── app.py                    # Flask 後端：任務管理、SSE、TSV 下載
├── rl_molecule_form.html     # 前端 UI：Tailwind + Chart.js + 分子圖
└── engines/
    ├── config.py             # MolMIM backend API 設定
    ├── logp.py               # logP + Tanimoto 強化邏輯
    └── qed.py                # QED + Tanimoto 強化邏輯
```

## 快速開始

### 1. 建立環境並安裝套件

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install flask requests numpy matplotlib cma rdkit
```

若尚未安裝 RDKit，請參考官方文件：[RDKit Install Guide](https://www.rdkit.org/docs/Install.html)

### 2. 快速架設 MolMIM backend

建議直接依 NVIDIA 官方 MolMIM NIM 文件準備 backend：

- Deploy: [NVIDIA MolMIM Deploy](https://build.nvidia.com/nvidia/molmim-generate/deploy)
- Quickstart: [NVIDIA NIM for MolMIM Quickstart Guide](https://docs.nvidia.com/nim/bionemo/molmim/1.0.0/quickstart-guide.html)
- Support Matrix: [NVIDIA NIM for MolMIM Support Matrix](https://docs.nvidia.com/nim/bionemo/molmim/1.0.0/support-matrix.html)
- Endpoints: [NVIDIA NIM for MolMIM Endpoints](https://docs.nvidia.com/nim/bionemo/molmim/1.0.0/endpoints.html)

依官方文件，至少先確認：

- Docker 已安裝
- NVIDIA Driver 與 NVIDIA Container Toolkit 已安裝
- 本機有可用的 NVIDIA GPU

官方文件列出的最低硬體需求包含：

- 4 CPU cores
- 16 GB RAM
- 50 GB NVMe SSD
- 1 張支援的 NVIDIA GPU

依 deploy 頁面，先準備 NVIDIA API key 並登入 registry：

```bash
docker login nvcr.io
```

登入時使用者名稱填 `$oauthtoken`，密碼填你的 NVIDIA API key。

接著可直接照官方 quickstart 啟動：

```bash
docker pull nvcr.io/nim/nvidia/molmim:1.0.0

docker run --rm -it --name molmim --runtime=nvidia \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e NGC_CLI_API_KEY \
  -p 8000:8000 \
  nvcr.io/nim/nvidia/molmim:1.0.0
```

等到 health check 回傳 `{"status":"ready"}` 之後，再讓本專案連過去：

```bash
curl -X GET http://localhost:8000/v1/health/ready -H 'accept: application/json'
```

這個專案目前會使用 MolMIM backend 的 `/hidden` 與 `/decode` 端點。

### 3. 設定 MolMIM backend 位址

預設會連到本機的 `http://127.0.0.1:8000`。如果你的 MolMIM backend 跑在其他位址，請先設定：

```bash
export MOLMIM_API_BASE=http://127.0.0.1:8000
```

程式會自動使用：

- `${MOLMIM_API_BASE}/decode`
- `${MOLMIM_API_BASE}/hidden`

### 4. 啟動 Web 介面

```bash
cd molmim_rf
python app.py
```

預期輸出：

```text
app.py ready  (targets: logP / QED)
 * Running on http://127.0.0.1:5000
```

### 5. 開啟瀏覽器

```text
http://127.0.0.1:5000
```

## 備註

- 這個 repo 不包含 MolMIM backend 本體，需自行準備對應的 MolMIM NIM 或相容服務。
- 目前前端 selector 僅提供 `logP` 與 `QED`。若要加入新目標，可比照 `engines/` 內模組擴充。
- 前端預設起始分子已改為 NVIDIA BioNeMo MolMIM IPython 範例中的 `imatinib`，並附上同一範例的 `erlotinib` 與 `gifitinib/gefitinib` 一鍵切換按鈕。這組例子來自 NVIDIA 的 CMA-ES notebook，其「Define starting molecules」段落列出三個起始 SMILES。[來源](https://docs.nvidia.com/bionemo-framework/1.10/notebooks/cma_es_guided_molecular_optimization_molmim.html)

## Citation

若你在研究、簡報或衍生專案中使用了這個流程，建議至少引用下列官方與模型相關資料：

- NVIDIA MolMIM Deploy: [https://build.nvidia.com/nvidia/molmim-generate/deploy](https://build.nvidia.com/nvidia/molmim-generate/deploy)
- NVIDIA MolMIM Model Card: [https://build.nvidia.com/nvidia/molmim-generate/modelcard](https://build.nvidia.com/nvidia/molmim-generate/modelcard)
- NVIDIA BioNeMo Framework MolMIM docs: [https://docs.nvidia.com/bionemo-framework/1.10/models/molmim.html](https://docs.nvidia.com/bionemo-framework/1.10/models/molmim.html)
- Improving Small Molecule Generation using Mutual Information Machine
- MIM: Mutual Information Machine
- The CMA Evolution Strategy: A Comparing Review

## License

- 本 repo 是一個與 MolMIM backend 整合的前端與流程樣板，不隨附 NVIDIA MolMIM model weights 或 NIM container。
- NVIDIA 的 MolMIM 頁面說明，API 使用需遵守 [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf)，模型使用需遵守 [NVIDIA AI Foundation Models Community License](https://docs.nvidia.com/ai-foundation-models-community-license.pdf)。
- NVIDIA BioNeMo Framework 的 MolMIM 文件另外註明 framework 版 MolMIM 「provided under the Apache License」。若你使用的是 framework 權重或相關發行內容，請以 NVIDIA 對應文件中的授權條款為準。
- 使用、下載或重新散布任何 NVIDIA MolMIM 相關資產前，請先閱讀並遵守 NVIDIA 官方文件與授權條款。
