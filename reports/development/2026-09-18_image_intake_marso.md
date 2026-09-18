# 圖片入口實作與 Marso 比較 — 2026-09-18

## 本次建置成果

圖片單例是手持電鑽。新增 scripts/pf-image-task（prepare / collect）、workflow/image_intake.py、drill_image 契約及 image_provider 固定版本設定。
prepare 強制使用既有 preflight，僅接受目前單剛體搬運 scope。保存來源授權陳述、照片 hash、RGB/RGBA PNG container/CRC/scanline 檢查、需求、registry、程式 hash 與待執行命令。尺寸/質量缺失拒絕，不自動補成已量測。
collect 在新 run 保存外部產物，禁止 symlink，驗來源照片及 bundle hash；首版驗 OBJ 顶點/面位置引用、有限座標、包圍盒與非共面表面。它不驗模型是否像照片、不驗完整拓撲/材質、不證明來源因果，不輸出 physics pass。GLB-only 尚未接入。

10 圖片防線測試與 13 既有 preflight 回歸 exit 0。測試使用合成小圖和解析器 fixture，不是真實圖片生成，更不是電鑽實測。第一輪 fixture 未確認初態造成失敗，保留失敗證據；修的是 fixture，不是 validator。
後端 checkout 已取得：EmbodiedGen v2.1.0，commit f0124197888c2b733e4eaa65acd81ad9cfda3b79；不是後端安裝完成。尚無獨立圖片環境或下載權重。

## Marso：可以用什麼

[使用者指定官方頁](https://marso.app/physical-ai) 成功 HTTP 200；原文保存在 runs/20260918T010038Z_image_backend_inventory/marso.html 與 marso.txt。
官方描述公尺尺度 USD、預測 albedo/metallic/roughness/IOR，以及推估 mass/density/static friction/dynamic friction/restitution；提供 SDF 與 CoACD 两種資產包。量測的是訓練資料，輸出明確仍是 predicted。
可接入為外部 USD 來源或圖片材質來源，借用 metric geometry、相對依賴、視覺/碰撞分離與 provenance 管理。需先讀回該 USD 實際 physics schemas、collision approximation、尺度、剛體与 inertia，再作受力實測；SDF/CoACD 標籤不直接證明本機版本可用。
PBR 是渲染表面參數，不等於紙箱塑性摺痕、MD/CD 板彎曲或包材可撕裂。推估物性應 assumed，不能升級 measured。本專案也不能僅由外觀材料斷定內部質量分布或接觸摩擦真值。
資產包需要提供公司/聯絡資料并同意聯絡；本次未提交。該頁沒公開完整圖片生成 API 契約或模型權重，所以尚不能當無人值守預設後端；不是判定它沒有 API。
[服務條款](https://marso.app/terms-of-service) 另外審查；免費取得資產不代表所有生成/商業條件都相同。

## 其他人的做法與採用順序

| 官方來源 | 做法 | 本專案決策 |
|---|---|---|
| [EmbodiedGen 固定版](https://github.com/HorizonRobotics/EmbodiedGen/tree/v2.1.0) | 圖片後端→mesh/URDF→推估物性與品質檢查 | 首個資格候選。已有 checkout；真實環境/權重/輸出仍未驗證。 |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2) | 單圖→PBR GLB；官方 A100/H100、至少24GB | 若想直接取得幾何可獨立接入；不是 EmbodiedGen 原 TRELLIS 的版本別名。Blackwell需另驗。 |
| [Meshy API](https://docs.meshy.ai/en/api/image-to-3d) | POST task→GET 狀態→下載 GLB/OBJ 等 | 商業服務備選，接我們同一檔案 adapter。需要帳號/key/費用，未呼叫。官方 auto_size 是估測尺度，不是實物量測。 |
| [Gen2Sim](https://github.com/pushkalkatara/Gen2Sim) | 圖片升成3D、LLM推物性，再導出任務 | 借方法與記錄模式；其 IsaacGym/舊環境不照裝到現有Isaac6。 |
| [PhysGen3D](https://github.com/by-luckk/PhysGen3D) | 單圖→互動小場景与物理渲染 | 研究參考；不是已驗證的 Isaac USD drop-in 後端。 |

以上推薦是本專案依可重現性/主線相容性所作工程判斷，並非有同圖基準證明哪個品質最佳。

## 自行確認命令

立即可執行，僅看真實程式介面：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-image-task --help
./scripts/pf-workflow-preflight contracts/workflow/examples/drill_image.json
```

第二條預期 exit 2 / needs_input，因電鑽全長與質量仍未知。這是正確阻擋，不是電鑽生成失敗。
準備自己的 PNG 與已填尺寸/質量/來源的 bundle 後：

```bash
./scripts/pf-image-task prepare \
  --bundle /absolute/path/drill_bundle.json \
  --image /absolute/path/drill.png \
  --reference '照片來源或拍攝紀錄' \
  --license-note '照片授權或自有拍攝聲明' \
  --backend TRELLIS
```

回傳新 run 路徑；prepared 只表示照片輸入準備成功。provider_command.json 不會自行執行。
後端真實產出帶 OBJ 的資料夾後：

```bash
./scripts/pf-image-task collect \
  --run /absolute/path/runs/IMAGE_INTAKE_RUN \
  --artifacts /absolute/path/provider_output
```

目前沒有圖片電鑽 USD，所以也沒有可以驗此電鑽的 WebRTC loader。下一張卡要先真生成，再轉 USD 與冷載入；不能用原參數化物件替代并宣稱圖片成功。

## 下一個有界任務

完成單後端隔離資格：Python3.10/torch2.8/cu128/CUDA extension 相容、權重與 agent 可用；取一張來源明確電鑽圖，以 n_retry=1 真實生成。固定原始版本 CLI 的 n_retry 是總次數，且影片為 inline，沒有公開 skip-video 參數；若要背景影片須單獨記錄修改，不能假設已加速。
conda/mamba/python3.10 不在本次 PATH；uv/nvcc 存在。不因 conda 未找到就說不可能，下一卡可盤點隔離工具。不得修改共享 Isaac venv/driver。

補充：阻擋來源資料夾包含輸出run造成遞迴複製；最後11圖片測試 exit0，證據 runs/20260918T010854Z_image_intake_overlap_checks。
