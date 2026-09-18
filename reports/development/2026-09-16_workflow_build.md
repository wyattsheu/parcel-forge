# 工作流建置進度回報：S0 到 S4 物理覆蓋

日期：2026-09-17  
目前技術階段：S4 物理验收完成；S5 合約建置中

完整逐項操作（33 個確認點、指令與畫面預期）：
[從零到現在自行驗證](2026-09-17_self_verification_from_zero.md)。

## 來源標記

- **外部方法**：採用 NVIDIA、OpenUSD 官方文件或研究論文，後面直接列來源。
- **本專案設計**：parcel-forge 自行制定的案例、門檻、CLI 或判定方式。
- **本機 API 適配**：依已安裝的 Isaac Sim 6.0.1 原始碼與實測調整。
- 兩份本地 handbook 是整理與實作規格，不當成外部研究證據。

所有命令先從專案根目錄執行：

    cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge

WebRTC 共通用法：

    ./scripts/pf view --replace --run <run-id> --scene scene_final.usda --ui

看到終端 READY 後再連 WebRTC。看完在該終端按 Ctrl+C，或由你執行
./scripts/pf view --stop。WebRTC 只能做人工作畫面確認；數值與 pass/fail 仍以
JSON、CSV、exit code 為準。

## 階段 1：環境與可重現啟動（S0，完成）

### 建立內容與來源

- **外部方法**：workflow/tool 分離、每次執行保留獨立 evidence directory，參考
  [NVIDIA USD Content Agents](https://github.com/NVIDIA-Omniverse/usd-content-agents) 與
  [workflow 文件](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/agentic/README.md)。
- **外部方法**：可由沒有前文的新工作階段接手的任務卡，參考
  [OpenAI ExecPlan](https://developers.openai.com/cookbook/articles/codex_exec_plans)。
- **本專案設計**：pf doctor、STATE／ROADMAP／DECISIONS／sessions、append-only runs。
- **本機 API 適配**：盤點實際 Isaac Sim 6.0.1.0、PhysX 110.1.13 與安裝路徑。

### 自行確認

    ./scripts/pf doctor
    git status --short
    cat docs/ENVIRONMENT.md

成功條件：doctor exit code 0，新 run 有 environment.json。本階段沒有資產，
**WebRTC 不適用**。

## 階段 2：最小物理與讀回（S1，完成）

### 建立內容與來源

- **外部方法**：PhysX 作為 Isaac Sim 6.0 基準後端，依
  [官方 Physics 概覽](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/physics/index.html)。
- **本機 API 適配**：使用 6.0.1 的 SimulationManager 與
  isaacsim.core.experimental.prims.RigidPrim；API 取自本機同版本 site-packages。
- **本專案設計**：600 步、自由落體解析解比較、3 mm 工程門檻與 CSV 欄位。
  t=0.1 s 誤差 2.04 mm。

### 自行確認

    ./scripts/pf smoke
    ./scripts/pf runs --last 2
    xdg-open runs/20260916T152014Z_s1_smoke/renders/scene_final.png

成功條件：physics、readback、headless、render 分開確認。S1 現已增加最終 USD，
可看落地後方塊（不是動態重播）：

    ./scripts/pf smoke --physics-only
    ./scripts/pf view --run 20260917T004937Z_s1_smoke --scene scene_final.usda --ui

該 run physics 和非空白 PNG pass、exit 0；WebRTC 尚待人工確認。

## 階段 3：固定開口箱與故障辨識（S2，完成）

### 建立內容與來源

- **本專案規格**：30×20×15 cm、5 mm 壁厚五板件簡化幾何來自本地 handbook
  第 7 節；這是工程案例，不是論文量測值。
- **外部方法**：明寫 USD 單位與 composed transform 讀回依
  [OpenUSD length units](https://openusd.org/dev/api/group___usd_geom_linear_units__group.html)。
- **外部方法**：CCD 與 contact/rest offset 語意參考
  [PhysX Advanced Collision Detection](https://nvidia-omniverse.github.io/PhysX/physx/5.1.2/docs/AdvancedCollisionDetection.html)。
- **本專案設計**：正常、封口、漏底 outcome 使用箱體 local frame 判斷。

### 自行確認

    ./scripts/pf box --case open_box_normal
    ./scripts/pf box --dt-sweep

成功條件：正常箱 inside；1/60、1/120、1/240 都是 inside。

WebRTC 看正常、封口與漏底：

    ./scripts/pf view --replace --run 20260916T141357Z_s2_open_box_normal --scene scene_final.usda --ui
    ./scripts/pf view --replace --run 20260916T141411Z_s2_open_box_sealed --scene scene_final.usda --ui
    ./scripts/pf view --replace --run 20260916T141343Z_s2_open_box_no_bottom --scene scene_final.usda --ui

人工應分別看到 probe 在內底、箱口、箱體下方。人工觀察不能取代 s2_result.json。

## 階段 4：規格、USD 與靜態驗證（S3，完成）

### 建立內容與來源

- **外部方法**：generator、validator、workflow 分離，延續 NVIDIA USD Content Agents。
- **外部方法**：validator 與 profile 概念參考
  [Isaac Sim 6.0 Asset Validation](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/robot_setup/asset_validation.html)。
- **本機 API 適配**：整合已安裝的 omni.asset_validator 1.19.3，執行 41 條
  generic USD 規則，並用損壞 fixture 證明它會 fail。
- **本專案設計**：JSON schema、跨欄位構造檢查、7 個非法案例錯誤類別與用途專屬 G1。
  generic validator pass 不等於 SimReady 或箱內放置成功。

### 自行確認

    ./scripts/pf verify --case open_box_normal
    ./scripts/pf verify --all
    ./scripts/pf view --replace --run 20260916T151144Z_s3_verify_open_box_normal --scene asset.usda --ui

成功條件：合法案例 build＋G1 pass；非法案例在 simulator 前被指定 error class 拒絕。
WebRTC 可看幾何與 prim hierarchy；尺寸誤差和 41 條規則看 validation.json。

## 階段 5：USD reference 與 viewer 相容性（完成）

### 建立內容與來源

- **OpenUSD 機制**：reference 未指定 prim 時依賴 defaultPrim；PhysicsScene 必須位於
  reference 可達的 composed subtree。
- **本機實測修正**：先前 reference 後得到 0 meshes，據此補 defaultPrim 並移動場景。
- **本專案設計**：scene_final.usda 寫入 PhysX readback 的最終 pose，同時保留
  trajectory，避免用事後場景冒充動態證據。

### 自行確認

    /mnt/HDD4/wyattsheu/IsaacLab/.venv/bin/python3 -m unittest tests.test_export_defaultprim -v
    ./scripts/pf view --replace --run 20260916T141357Z_s2_open_box_normal --scene scene_final.usda --ui

成功條件：在 Isaac runtime 可用時 reference tests 通過；WebRTC stage tree 能看到
World/Box 與 World/Probe，不再是空場景。

## 階段 6：慣性可行性與動態質量屬性（S4，完成）

### 建立內容與來源

- **外部方法**：confidence tier、慣性不確定性與 pseudo-inertia constraint 採自
  [Scalable Real2Sim](https://arxiv.org/html/2503.00370v2)。
- **外部方法**：mass、local COM、diagonal inertia、principal axes 欄位依
  [OpenUSD MassAPI](https://openusd.org/release/api/class_usd_physics_mass_a_p_i.html)。
- **本專案修正**：以主慣性矩判定正定與三角不等式；對旋轉與尺度不變；
  用主軸重建 tensor，不直接比較 eigenvector 正負號。
- **限制**：0.20 kg 箱殼與均勻分布仍是 estimate。讀回吻合只證明參數傳遞。

### 自行確認

    python3 -m unittest tests.test_mass_properties -v
    ./scripts/pf verify --case open_box_dynamic
    ./scripts/pf mass-readback
    ./scripts/pf view --replace --run 20260916T155652Z_s4_mass_readback --scene asset.usda --ui

成功條件：rotated impossible tensor 被拒絕；小尺度合法 tensor 被接受；動態 USD
有 1 個 root rigid body、5 個 child colliders；PhysX mass/COM/inertia/axes pass。
WebRTC 只能看 hierarchy／物件，精確值看 s4_mass_readback.json。

## 階段 7：九點放置覆蓋（S4，完成）

### 建立內容與來源

- **本專案設計**：中心、四邊、四角共九點；每點保留完整 trajectory，用 box-local
  outcome 判斷。固定九點配置不是直接複製某篇論文。
- **外部方法影響**：motion evidence 優先於單張圖片，參考
  [Articulate-Anything](https://arxiv.org/html/2410.13882v2)。

### 自行確認

    ./scripts/pf placement-grid
    cat runs/20260916T160040Z_s4_placement_grid/summary.md
    ./scripts/pf view --replace --run 20260916T160040Z_s4_placement_grid --scene scene_final.usda --ui

成功條件：9/9 inside、render ok。離線圖：
runs/20260916T160040Z_s4_placement_grid/renders/s4_nine_point_grid.png，
1280×720、395169 bytes、distinct red levels 142、非空白；agent 未做人眼判讀。

## 階段 8：四面側撞（S4，physics 通過；render 待重跑）

### 建立內容與來源

- **本專案設計**：由箱內向 ±X／±Y 發射 probe，使用整段 trajectory 的最大
  signed position，避免最後位置掩蓋曾經穿牆。
- **外部方法**：薄壁離散碰撞與 CCD 風險依 PhysX collision 文件；四方向配置與
  2 mm 判定門檻是本專案工程設定。
- 完整資料為 240 steps × 4 shots；X 最大中心 0.124999983 m，Y 約
  0.075000010 m，physics 4/4 blocked。
- 原 run 在 render 階段 Kit exit -11；physics 與 render 分開報告。
  recovery：runs/20260916T161010Z_s4_sidewall_recovery/。

### 自行確認

    python3 -m unittest tests.test_sidewall -v
    cat runs/20260916T161010Z_s4_sidewall_recovery/summary.md
    ./scripts/pf sidewall
    ./scripts/pf view --replace --run 20260916T160621Z_s4_sidewall --scene scene_final.usda --ui

應人工看到四個 probe 分別接觸四面內牆。舊 run 的 offline render 仍是 fail；
WebRTC 查看不能把它升級為 render pass。

## 完成程度與命令

| 項目 | 狀態 | 自行確認 |
| --- | --- | --- |
| S0 環境 | verified | ./scripts/pf doctor |
| S1 最小模擬 | verified | ./scripts/pf smoke |
| S2 固定箱 | verified | ./scripts/pf box --dt-sweep |
| S3 USD／靜態驗證 | verified | ./scripts/pf verify --all |
| S4 慣性驗證器 | verified | python3 -m unittest tests.test_mass_properties -v |
| S4 PhysX mass readback | verified | ./scripts/pf mass-readback |
| S4 九點放置 | verified | ./scripts/pf placement-grid |
| S4 四面側撞 physics | verified | tests.test_sidewall ＋ recovery run |
| S4 四面側撞 render | fail，待重跑 | ./scripts/pf sidewall |
| S4 動態箱 drop／settling | verified | ./scripts/pf dynamic-drop |
| contact offset／rest offset／friction／restitution | USD 讀回＋接觸行為 verified | ./scripts/pf sidewall --physics-only |
| 真實紙箱材料校準 | 不在 rigid baseline 範圍 | 無 |

## 外部來源總表

| 來源 | 採用部分 | 專案落點 |
| --- | --- | --- |
| NVIDIA USD Content Agents | workflow/tool 分離、append-only evidence | host modules、runs、manifest |
| Isaac Sim 6.0 Physics | PhysX baseline | runtime adapter、S1–S4 |
| Isaac Sim Asset Validation | official validator/profile | validation/official_usd.py |
| OpenUSD units／MassAPI | SI、mass/COM/inertia/axes | usd_author.py、static_usd.py |
| PhysX Advanced Collision Detection | CCD／接觸參數語意 | dt sweep、wall tests |
| Scalable Real2Sim | confidence、pseudo-inertia、慣性不確定性 | mass_properties.py |
| Articulate-Anything | motion evidence、critic 不可單獨決定 pass | trajectory、D012 |
| LL3M | assets-as-code、版本相符文件 | geometry.py、usd_author.py、本機 6.0.1 source |
| OpenAI ExecPlan | 可獨立接手的任務卡 | AGENTS.md、docs/tasks |

完整的採用／未採用說明在 docs/METHODS.md。

## 下一個小階段

接觸參數與動態箱 settling 已完成，詳見 2026-09-17_contact_and_dynamic_settling.md。
CCD 的 USD attribute 為 true，但 runtime 明確警告停用，不能宣稱實際生效。
下一個階段是 S5 的 findings-to-patch 合約與受限修復。

## 階段 9：接觸設定與動態箱落地（S4，完成）

來源：本機 PhysxCollisionAPI／UsdPhysics.MaterialAPI；本專案 handbook 第 9、10 節。
估計參數與判定限制詳見 2026-09-17_contact_and_dynamic_settling.md。

    ./scripts/pf sidewall --physics-only
    ./scripts/pf placement-grid --physics-only
    ./scripts/pf dynamic-drop
    ./scripts/pf view --replace --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui

預期動態箱保持完整並停在地板。人工 WebRTC 結果仍為 not_tested。
