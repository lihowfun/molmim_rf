## MolMIM RF Web Demo

`molmim_rf` 是一個 MolMIM 的快速上手 Web 介面，提供兩個示範目標：

- `logP`
- `QED`

前端預設起始分子採用 NVIDIA BioNeMo MolMIM IPython 範例中的 `imatinib`，也內建 `erlotinib` 與 `gefitinib` 快速切換。

## 快速安裝

### 1. 準備 MolMIM backend

建議直接依 NVIDIA 官方文件部署：

- Deploy: [NVIDIA MolMIM Deploy](https://build.nvidia.com/nvidia/molmim-generate/deploy)
- Quickstart: [NVIDIA NIM for MolMIM Quickstart Guide](https://docs.nvidia.com/nim/bionemo/molmim/1.0.0/quickstart-guide.html)

最短流程：

```bash
docker login nvcr.io
docker pull nvcr.io/nim/nvidia/molmim:1.0.0

docker run --rm -it --name molmim --runtime=nvidia \
  -e CUDA_VISIBLE_DEVICES=0 \
  -e NGC_CLI_API_KEY \
  -p 8000:8000 \
  nvcr.io/nim/nvidia/molmim:1.0.0
```

確認 backend ready：

```bash
curl -X GET http://localhost:8000/v1/health/ready -H 'accept: application/json'
```

### 2. 安裝本專案

```bash
git clone https://github.com/lihowfun/molmim_rf.git
cd molmim_rf

python3 -m venv .venv
source .venv/bin/activate
pip install flask requests numpy matplotlib cma rdkit
```

若 MolMIM backend 不在本機 `127.0.0.1:8000`，請改用你自己的位址：

```bash
export MOLMIM_API_BASE=http://127.0.0.1:8000
```

### 3. 啟動 Web

```bash
python app.py
```

打開瀏覽器：

```text
http://127.0.0.1:5000
```

## 示範怎麼用

1. 開啟首頁後，直接用預設的 `imatinib` 當 seed，或按按鈕切換成 `erlotinib` / `gefitinib`。
2. 在 `目標指標` 選 `logP` 或 `QED`。
3. 按 `提交任務`。
4. 觀察即時折線圖與 Top 分子卡片。
5. 完成後下載 TSV 結果。

目前這個介面會呼叫 MolMIM backend 的：

- `/hidden`
- `/decode`

## Citation

若使用本專案，建議至少引用：

- [NVIDIA MolMIM Deploy](https://build.nvidia.com/nvidia/molmim-generate/deploy)
- [NVIDIA MolMIM Model Card](https://build.nvidia.com/nvidia/molmim-generate/modelcard)
- [NVIDIA BioNeMo Framework MolMIM docs](https://docs.nvidia.com/bionemo-framework/1.10/models/molmim.html)

## License

- 本 repo 只提供前端與流程樣板，不包含 NVIDIA MolMIM model weights 或 NIM container。
- MolMIM API 與模型使用，請遵守 NVIDIA 官方條款與授權：
  - [NVIDIA API Trial Terms of Service](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf)
  - [NVIDIA AI Foundation Models Community License](https://docs.nvidia.com/ai-foundation-models-community-license.pdf)
