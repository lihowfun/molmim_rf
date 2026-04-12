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

### 2. 設定 MolMIM backend 位址

預設會連到本機的 `http://127.0.0.1:8000`。如果你的 MolMIM backend 跑在其他位址，請先設定：

```bash
export MOLMIM_API_BASE=http://127.0.0.1:8000
```

程式會自動使用：

- `${MOLMIM_API_BASE}/decode`
- `${MOLMIM_API_BASE}/hidden`

### 3. 啟動 Web 介面

```bash
cd molmim_rf
python app.py
```

預期輸出：

```text
app.py ready  (targets: logP / QED)
 * Running on http://127.0.0.1:5000
```

### 4. 開啟瀏覽器

```text
http://127.0.0.1:5000
```

## 備註

- 這個 repo 不包含 MolMIM backend 本體，需自行準備對應的 `/decode` 與 `/hidden` 服務。
- 目前前端 selector 僅提供 `logP` 與 `QED`。若要加入新目標，可比照 `engines/` 內模組擴充。
