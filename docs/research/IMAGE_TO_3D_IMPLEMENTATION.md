# 圖片 → 物理資產：建置與單例驗收計畫

日期：2026-09-18。狀態：intake_implemented / provider_not_verified；入口與OBJ交接離線驗證，未安裝後端、未下載權重、未生成圖片來源 USD。

## 現況與入口邊界

已有 EMBODIEDGEN_QUALIFICATION.md 與主計畫 P3a。專案 external/、.venvs/ 目前只有 usd-content-agents；scripts/pf-upstream-geometry-plan 明確使用 --dry-run，輸入是既有 USD，不能當圖片生成入口。
現有 pf-keyboard-package 仍是參數化鍵盤。圖片 adapter、圖片產物轉換及此路徑 WebRTC 實測皆未完成。

## 後端調查與選擇

| 候選 | 官方依據 | 本專案取捨 |
|---|---|---|
| EmbodiedGen v2.1.0 | [README](https://github.com/HorizonRobotics/EmbodiedGen/blob/v2.1.0/README.md)：圖片 CLI、SAM3D/TRELLIS/HUNYUAN3D 後端、URDF/mesh、VLM 推估物性 | 優先資格測試其 adapter；固定 tag 並記錄實際 commit，只安裝一個後端。它不是 NVIDIA 專案。 |
| TRELLIS.2 | [官方 README](https://github.com/microsoft/TRELLIS.2)：GLB/PBR、Linux、至少 24GB VRAM，A100/H100 驗證；預設 torch2.6/CUDA12.4 | 可作獨立幾何後端備選；不可把 EmbodiedGen 的 TRELLIS 當成 TRELLIS.2。Blackwell 編譯相容須實測。 |
| SAM 3D Objects | [官方安裝說明](https://github.com/facebookresearch/sam-3d-objects/blob/main/doc/setup.md)：至少 32GB VRAM，權重需申請存取 | 若已有存取資格且隔離環境相容才選，不讓尚未取得的權重阻塞主線。 |

EmbodiedGen 的尺度、質量、摩擦是推估；我們必須保留 assumed/provenance。各候選的 code、權重與依賴授權分開登錄；未審查完成不標公司交付可用。
本機歷史環境是 Blackwell；VRAM 總量充足不代表當下可用或所有 CUDA extension 可編譯。
[EmbodiedGen install.sh](https://github.com/HorizonRobotics/EmbodiedGen/blob/v2.1.0/install.sh) 會修改啟用環境套件並呼叫其他安裝腳本，不能在 Isaac venv 直接執行。CUDA 子腳本本次抓取失敗，尚未完整審查；不得因此直接安裝 toolkit。

## 單一代表性實驗

使用者更正：圖片資格測試改成單一手持電鑽，不生成箱內鍵盤。紙箱裝鍵盤保留為既有包裹案例，這次不重跑。
使用一張完整露出電鑽的斜前方照片，可見機身、夾頭、握把與底部電池；避免手部遮擋與純側面照。保存來源/授權、SHA256、裁切與已知全長。照片與量測值尚未指定；未知尺度必須標 assumed。
此例只驗完整剛體：背面及遮擋區為生成推測，不以看似合理宣稱重建正確。另拍側面/背面照片可只作保留驗證資料，不提供給單圖生成器。扳機運動、旋轉、拆電池不在本次範圍。

## 建置順序與完成門檻

1. **輸入契約接通**：先讓生成器讀取 bundle 並強制 preflight。圖片入口收 image_path、hash、尺度及其來源、intended_task、物性來源；缺資料回 needs_input，能力缺失回 unsupported。圖片外觀成功不能解除 payload_extraction 缺口。
2. **隔離後端資格**：盤點已有模型快取、可用 GPU/磁碟及 CUDA 編譯器；固定 repo/model revision。僅在專案獨立環境安裝一個後端，保留安裝輸出、版本、時間與退出碼。資源不足寫 blocked.json，不碰現有 WebRTC。
3. **真實生成一次**：先保存不可變輸入；記完整非秘密命令、seed（若支援）、模型版本、時間、峰值 VRAM、退出碼、產物 SHA256。最多三次總嘗試，必須先確認上游 n_retry 是否含首次，避免內外重試相乘。影片可略過或獨立背景產生；不能以影片存在判成功。
4. **檔案 adapter**：外部環境輸出 mesh/材質/metadata；Isaac 6.0.1 環境負責 USD authoring。校正 units/up-axis/尺度，建立視覺 mesh 與獨立碰撞 proxy、質量/COM/可行慣量。先試本機可用轉換器，不假定 GLB 能直接 open_stage。驗貼圖相對路徑與外部依賴。
5. **電鑽單例驗收**：量測匯入後包圍盒及指定全長誤差，確認 mesh 不是平面、材質依賴完整；人工旋轉視角檢查握把、夾頭、電池與扳機間隙是否塌陷。厚度存在只是最低門檻，不代表形狀正確。保留驗證照片若缺少，隱藏面真實性標 unknown。物理檢查 dynamic／無世界錨定、質量慣量可行、落地有限且接觸穩定、受外力可移動。碰撞 proxy 必須保留任務需要的凹槽，不能用整體凸包堵住握把接近區。
6. **可攜交付與 WebRTC**：輸出 asset.usda、config、manifest、result、loader；新路徑冷載入同樣 dt/solver 設定。附真正可執行 Script Editor loader；先停 timeline 旋轉檢查三維外形，再播放、推動與提起放手。影片只錄最後一次，人工確認另記。尚未交付 loader 前不提供假想執行指令。

## 預定檔案介面（尚未實作）

輸入：request.json + input/drill.png。
中間：provider/raw/（原始產物不可覆蓋）、provider_result.json（版本/seed/退出/時間/hash）、conversion.json（尺度/座標/proxy/物性來源）。
出口：asset.usda + textures/ + config.json + runtime/ + load_in_isaacsim.py + result.json。
result 分開標 geometry、physics、readback、cold_load、render、human_webrtc、task_success；unsupported 不升級 pass。
幾何錯誤回生成後端，尺度/碰撞錯誤回轉換模組，力學缺失回物理模型，不能讓修復 agent 改驗收標準。

## 執行指令的成熟度

已有 pf-image-task prepare/collect（只準備與交接，不生成）。目前沒有可用的 pf-image-generate 指令。以下是上游 README 的入口形式，**僅在隔離安裝與 CLI --help 核對後**才能執行，不是本次已跑成功的指令：

```bash
img3d-cli --image_path /absolute/path/drill.png --output_root /absolute/path/new-run/provider
```

實際後端與重試參數須在鎖定版本確認後明確設定。不要現在執行安裝全部後端的命令。
第一輪比較只比較同一電鑽任務：生成/轉換/修復耗時分開、尺度誤差、碰撞代理誤差、物理測試、手動修改次數；官方 H100 時間不當本機性能承諾。

單一下一步：接通現有 bundle 與生成 gate，再以固定版本、單後端建立圖片 provider 資格環境；不要同時擴張到其他物件。

## 實作更新

WF-P3A-1已完成離線驗證；固定 upstream checkout 已取得、圖片環境尚未安裝。報告：reports/development/2026-09-18_image_intake_marso.md。Marso與其他官方做法比較見同報告。

## 真實生成與交付（取代前述未執行狀態）

已用固定TripoSR真實生成並通過剛體USD/cold-load；EmbodiedGen仍未安裝。詳見reports/development/2026-09-18_image_drill_delivery.md。不是通用變形/物性校準完成。
