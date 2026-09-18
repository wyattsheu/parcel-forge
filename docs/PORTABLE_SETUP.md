# 跨機部署與雙入口

支援交付目標：Linux、已安装 Isaac Sim 的機器。驗證來源是 Isaac 6.0.1.0，5090 或其他 Isaac 版本目前未實跑；版本相近不等於 API/PhysX/driver 相容。不得為此自動升級共享環境。

## Clone 與綁定現有環境

```bash
gh repo clone wyattsheu/parcel-forge
cd parcel-forge
./scripts/pf-machine --python /你的/Isaac環境/bin/python3 --cwd /你的/Isaac工作目錄 --write-local
./scripts/pf doctor
```

`config/isaac_env.local.json` 不進 Git；或設定 `PF_ISAAC_CONFIG=/絕對路徑/自訂.json`。工具保留 venv interpreter 的 symlink 路徑。probe 僅讀 package metadata 和 API 檔案，**不證明模擬可用**。不支援的 API exit 3，不能改成 pass；目前不是 4.x 相容層。獨立安裝型可嘗試其 Python interpreter，但 API probe 失敗時需要對應版本 adapter，不能保證只改路徑即可。

先做最小 API 檢查，再跑一個實際案例：

```bash
./scripts/pf-keyboard-package
```

這沿用紙箱＋鍵盤生成器及材質，不重新調參。共享 WebRTC 不能被停止；GPU0 需至少 8000 MiB 空閒，否則 blocked。API、物理、讀回、render、人工查看分開記錄。跨 GPU/版本不要求 bitwise 相同，但仍須通過原驗收條件。`config/quality_baseline.json` 保存交付前核心來源 hash；它是版本比較，不是物理成功證據。

## AI 使用

Codex 在專案中輸入 `$parcel-forge-assets`；Claude Code 輸入 `/parcel-forge-assets`。Codex 的 `.agents/skills/parcel-forge-assets/SKILL.md` 是主文件；Claude 的 `.claude/skills/parcel-forge-assets/SKILL.md` 以相對 symlink 共用它。Linux clone 可保留 symlink。只有配置與靜態驗證已測，尚未由兩個 CLI 分別作端到端 skill invocation。

新 AI 依 AGENTS.md 讀當前必要文件，正常執行只讀簡短 stage 結果；更改物理或處理失敗才讀相關程式/研究，不能省略任務必需的驗證。

## 文字入口

```bash
./scripts/pf-workflow text --prompt-file description.txt --bundle contracts/workflow/examples/carton_keyboard.json
```

詳細描述用途、初始狀態、尺寸/質量來源、自由移動、蓋子/接口及必需行為。AI 先形成 bundle；本命令只保存描述並跑 preflight，尚不自動把任意文字轉成模型，也未核對描述與 bundle 語意一致性。不能把紙箱範例的能力缺口當成功；原鍵盤紙箱生成器仍由上方命令獨立執行。文字 authoring 接 bundle 是後續工作。

## 圖片入口

```bash
./scripts/pf-workflow image --bundle contracts/workflow/examples/drill_image_proxy.json --image /路徑/object.png --reference '來源URL或自己的拍攝說明' --license-note '作者與授權'
# 確認規格後，一次真生成、物理、冷載入、匯出：
./scripts/pf-workflow image --bundle contracts/workflow/examples/drill_image_proxy.json --image /路徑/object.png --reference '來源' --license-note '授權' --execute --name my_asset_v1
```

RGB/RGBA 8-bit non-interlaced PNG。proxy 範例 0.25m/1.5kg 是上一輪的明示假設，不能當其他物體的校準值。修改 bundle 中參數與 provenance 後使用。現在只支援單個剛體 move；包裝、關節、材料變形未由此路徑支援。既有內部 Drill 命名不代表已泛化各物體的測試。執行時每個 stage 存 progress/log/child-run hash；失败即停止，不自動循環修復。不生成影片。

### 圖片後端重建（與 Isaac 隔離）

重建只寫專案 `.venvs/` 和 `external/`，不使用 Isaac 的 pip。以下是來源機的重現指令，**另機安裝尚未驗證**。先確認系統已有 Python 3.12 headers 與匹配的 CUDA compiler；缺少時停下，不自動安裝系統套件或 driver。

```bash
python3.12 -m venv .venvs/triposr
.venvs/triposr/bin/python -m pip install -r config/triposr_requirements.freeze.txt --extra-index-url https://download.pytorch.org/whl/cu128
git clone https://github.com/VAST-AI-Research/TripoSR external/TripoSR
git -C external/TripoSR checkout 107cefdc244c39106fa830359024f6a2f1c78871
git clone https://github.com/tatsy/torchmcubes external/torchmcubes
git -C external/torchmcubes checkout 879926d0ef58e6ce0ac2630fdecb5e53af7ed3ff
cp -a external/torchmcubes external/torchmcubes_torch28
git -C external/torchmcubes_torch28 apply ../../config/patches/torchmcubes_torch28_cpp17.patch
CUDA_HOME=/usr/local/cuda-12.8 .venvs/triposr/bin/python -m pip install --no-deps --no-build-isolation ./external/torchmcubes_torch28 --config-settings=cmake.define.CMAKE_CUDA_ARCHITECTURES=120
```

编译 Python.h 找不到時用该 venv 的 Python 3.12 include 路徑追加 `--config-settings=cmake.define.Python_INCLUDE_DIR=/你的/python3.12/include`；不要沿用來源機絕對路徑。120 是來源 Blackwell build 設定，其他 GPU 必須按當機架構處理，不重配共享 CUDA。

下載固定模型並核對 `config/triposr_provider.json` 的兩個 SHA256：

```bash
.venvs/triposr/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/TripoSR',revision='5b521936b01fbe1890f6f9baed0254ab6351c04a',local_dir='.venvs/models/triposr/5b521936b01fbe1890f6f9baed0254ab6351c04a',allow_patterns=['config.yaml','model.ckpt'])"
```

模型權重不推 Git。rembg 首次也可能下載 u2netp；無網路時先準備快取 `.venvs/u2net`。freeze 是來源機實測依賴版本，非跨 OS 保證或含 hashes 的 supply-chain lock。

## NVIDIA 官方沿用範圍

沿用 [官方 USD Content Agents](https://github.com/NVIDIA-Omniverse/usd-content-agents) 固定 SHA 的 validation/checkpoint integration；分工詳見 `docs/UPSTREAM_ADOPTION_PLAN.md`、`docs/REPAIR_CONTRACT.md`。這個入口只是薄 dispatch，不重寫官方 state/resume/repair，不改官方 validator。圖片 pipeline 仍未接官方整條 generation chain，結果明确 `nvidia_validation: not_tested`，不是 NVIDIA 認證。

```bash
git clone https://github.com/NVIDIA-Omniverse/usd-content-agents external/usd-content-agents
git -C external/usd-content-agents checkout a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa
# 在獨立 .venvs/usd-content-agents 依 docs/UPSTREAM_ADOPTION_PLAN.md 安裝，不能安裝到 Isaac。
```

兼容要求以當機版的 [NVIDIA requirements](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/requirements.html) 和本機 API 為準。Skill 發現路徑參考 [Codex](https://learn.chatgpt.com/docs/build-skills) 與 [Claude Code](https://code.claude.com/docs/en/skills)。

## WebRTC 查看

先儲存並 Stop，在既有 Script Editor：

```python
from pathlib import Path
PF_PROJECT_ROOT = '/你clone後的絕對路徑/parcel-forge'
p = Path(PF_PROJECT_ROOT) / 'scripts/keyboard_package_editor.py'
exec(compile(p.read_text(), str(p), 'exec'), globals())
```

在該機跑過 keyboard-package 後才有本機 runs 可載入。圖片則換成 `scripts/image_drill_editor.py`。選物體按 F，Stop 時旋轉；Play 後以 native force drag 操作。跨機 WebRTC launcher/連線仍由該機既有安裝提供，本專案不自動佔用 ports。

也可直接開 Git 中 `exports/image_drill_v1/scene.usda` 檢查既有交付；紙箱需隨附 crease controller，USD 本身不保存 Python per-step 塑性控制器，詳見 `exports/carton_v1/` 說明。不可只開 USD 就宣稱相同塑性行為。

### 家目錄快速啟動

來源機已建立 `~/start_webrtc.sh` → 專案 `scripts/pf-webrtc`。執行 `~/start_webrtc.sh` 在背景啟動完整編輯器，預設載入圖片電鑽，timeline Stop；`--check` 只做檢查。輸出run/runtime.log，等待 `[VIEW] READY` 再以WebRTC client連到140.113.203.85，signaling49100/stream47998。啟動PID不等於stream就緒或人工已確認。

另機可自行建立相同symlink，使用 `--public-ip 當機可達IP`；若已有同名script，保留不覆寫。這不修改共享環境，不接管已有WebRTC服務。

圖片碎塊修正：`pf-workflow image ... --component-policy largest --execute --name NEW_NAME` 顯式保留最大拓撲連通區塊，raw/removed_components另存。預設keep；合法分離零件不得自動刪。去背中仍可能有碎片，外觀需人工驗證；不把物理pass當外觀pass。新家目錄啟動器預設image_drill_appearance_v2，既有WebRTC不重啟，用Script Editor載入新版即可。
