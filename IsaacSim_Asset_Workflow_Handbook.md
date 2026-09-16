# Isaac Sim 資產生成工作流：跨週建構與驗證手冊

版本：1.0｜研究查核日期：2026-09-16｜對象：許懷仁／Task 1

本手冊是可交給 Codex／Claude Code 的建構規格與新手學習路線，不是已完成的模擬軟體。這次沒有連入 acm-803-1、沒有執行 Isaac Sim，也沒有確認伺服器上的既有程式。本手冊中的自訂 CLI 是「要實作的介面」，不是 NVIDIA 現成指令。所有數值門檻均標示用途；工程初值不等於真實材料量測。

## 1. 你接下來實際怎麼工作

**同一個專案資料夾、不同的小任務對話、每次留下可重跑的證據。**不用維持一段幾個月不關閉的 agent 對話，也不要讓模型的內建記憶成為唯一的進度來源。

建議先維持一位 coding agent 負責寫入專案。Codex 或 Claude Code 選你操作順手的一個；更換時讀取同一套交接檔案。第一版不需要多 agent 系統、向量資料庫、記憶 MCP 或資料庫伺服器。

同一小任務的 debug 可以延續原對話；換里程碑、換工具、對話混亂或隔週回來時，可以開新對話。新對話只要能讀到專案檔案和執行環境，就能重新建構工作狀態。一般網頁聊天若無伺服器存取，必須附上交接資料；它不會自動看到遠端硬碟。

這個安排符合官方的專案指引機制：Codex 會讀取適用的 AGENTS.md；Claude Code 支援 CLAUDE.md。**其餘 STATE、ROADMAP 等檔名是本專案自訂，必須在入口規則明確要求讀取，不能假設自動載入。**[Codex 官方文件](https://developers.openai.com/codex/agent-configuration/agents-md)；[Claude Code 官方文件](https://code.claude.com/docs/en/memory)。

每次開工的固定動作：

1. 進入正確 repo，檢查 branch、commit、未提交修改。
2. 讀入口指引、目前進度、當前任務卡與上一個證據摘要。
3. 先跑與當前任務相關的最小基準，確認環境仍然可用。
4. 只完成一張任務卡；卡太大就拆成下一張。
5. 實際執行驗證，保存成功和失敗結果。
6. 更新交接資料，明確寫下一個動作，再結束。

每週不一定要升一級。驗證失敗就延續同一張卡；週數只是排程參考，**里程碑通過才是進度**。

## 2. 目標、範圍與明確假設

第一版目標：用結構化需求生成開口紙箱 USD，在 Isaac Sim 中確認尺寸、內部空間、碰撞和基本動態可用；偵測故障後讓 coding agent 在固定預算內修正，完整保留證據。

使用者先前描述的環境為 Isaac Sim 6.0、Isaac Lab 3.0.0-beta2、雙 RTX PRO 6000；此處當作待確認的背景，不當作已驗證事實。第一張任務卡須記錄實際版本與 commit。

| 決策 | 第一版選擇 | 理由與例外 |
| --- | --- | --- |
| 物理後端 | PhysX | 先建立單一可重現基準；Newton 留作獨立相容性工作 |
| 資產類型 | 固定形狀開口箱＋測試立方體 | 最貼近箱內放置，又能設計明確的數值驗證 |
| 幾何生成 | OpenUSD Python，規則板件 | 暫不增加 Blender／CadQuery 安裝與轉檔依賴 |
| 測試世界 | 單環境、無 ROS | 資產驗證無需先連機械手臂通訊 |
| 物理驗收 | 程式與 simulator | VLM 不能覆寫數值失敗 |
| AI 角色 | 初期寫生成器；後期填規格及有限修正 | 批次相同家族不需要每個物件重寫程式 |
| 記錄 | JSON＋Markdown＋Git＋run 目錄 | 一人跨週可維護，可日後擴充 SQLite |

本版不承諾：真實紙板壓潰、膠帶撕裂、泡泡紙壓縮、袋子重塑、真機成功率或 1000 環境吞吐。這些是另外的驗證需求。

Isaac Sim 6.0 官方物理頁將 PhysX 列為預設、Newton 列為 experimental；這支持先固定 PhysX 的選擇，但不代表其他後端不可行。[官方物理概覽](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/physics/index.html)

## 3. 我已替你整理的研究結論

以下不是必讀清單，而是已轉成後續實作決策的來源。需要追溯時再點連結。

| 來源 | 經查核的方法／能力 | 本計畫採用什麼 | 不直接採用什麼 |
| --- | --- | --- | --- |
| [NVIDIA USD Content Agents](https://github.com/NVIDIA-Omniverse/usd-content-agents) | Coding agent 搭配 workflow、typed tools，產出 USD 與證據 | 工作流和工具分離、每次執行獨立資料夾 | 不假設它是穩定 SDK 或所有服務能直接在現有環境安裝 |
| [官方 workflow 實作文件](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/agentic/README.md) | 保留輸入、修改、驗證與恢復資訊；有驗證／SimReady 入口 | digest 綁定輸入，失敗 run 不覆蓋 | 不把 generic profile pass 當作箱內放置成功 |
| [LL3M 論文](https://arxiv.org/html/2508.08228v1) | 用程式生成 Blender 資產，以文件檢索協助 API 使用 | 查版本相符文件；保留可修改的生成程式 | 不把外觀品質視為機器人物理品質；MVP 不重建其整個 agent 系統 |
| [Articulate-Anything 論文](https://arxiv.org/html/2410.13882v2) | 以程式描述 articulation，actor–critic 看證據反覆修正 | 翻蓋階段借用「生成→運動→檢查」 | 論文亦討論 critic 誤判正確的情形，因此不能只靠 VLM |
| [Scalable Real2Sim 論文](https://arxiv.org/html/2503.00370v2) | 由外部影像及機器人互動辨識幾何與慣性參數 | 區分量測、估計與隨機化；保留物理參數來源 | 不假設名稱或照片能給出真實質量／摩擦 |
| [EmbodiedGen](https://github.com/HorizonRobotics/EmbodiedGen) | 生成資產與場景，提供模擬導向流程 | 日後當作外部資產輸入接同一驗證器 | 不讓生成來源自稱 sim-ready 就繞過驗收 |
| [Kit USD Agents](https://github.com/NVIDIA-Omniverse/kit-usd-agents) | USD／Kit／Isaac 開發輔助與 MCP | 版本查詢和工具入口的擴充選項 | 第一階段不把 MCP 安裝當成必要條件 |
| [OpenAI ExecPlan 範例](https://developers.openai.com/cookbook/articles/codex_exec_plans) | 可持續更新、能供無先前對話者接手的執行計畫 | 任務卡要自足，包含測試及目前發現 | 本專案不靠一個固定名稱自動觸發，入口明確要求遵守 |

具體工程結論：先做可以抓錯的工具，再接 AI 修復；已知紙箱家族用固定生成器；未知形狀再讓 agent 擴充生成器。開發生成器與量產資產是不同工作。

## 4. 專案放哪裡，以及怎麼防止下週失憶

先搜尋你現有 Task 1 程式、進度文件與測試，判斷哪些可重用。先前提及的 `scripts/task1/` 與 `docs/task1_progress.md` 只是待檢查線索，不代表目前檔案內容已被本手冊確認。

預設建議：用獨立 `parcel-forge` repo 管理新工作流，重用既有成果時保留來源；不要先改 Isaac Lab 核心。若現有 Task 1 已有完整 repo，就在那裡整理，不另建重複實作。記錄 `ISAACLAB_ROOT` 之類專案專用設定，指向已裝好的環境。

| 檔案／目錄 | 存什麼 | 更新時機 | 新對話是否必讀 |
| --- | --- | --- | --- |
| AGENTS.md | 工作契約、入口檔案、禁止偽造 pass 等 | 規則變更時 | 是 |
| CLAUDE.md | 要求讀取 AGENTS.md 的簡短入口 | 極少修改 | Claude 使用時 |
| docs/STATE.md | 目前關卡、最新證據、阻塞、下一步 | 每次工作結束及重要 checkpoint | 是 |
| docs/ROADMAP.md | M0–M9 狀態與依賴 | 關卡狀態變更 | 是，簡讀 |
| docs/tasks/Mx.md | 當前任务卡：目的、輸入、動作、驗收 | 任務進行中 | 只讀當前卡 |
| docs/DECISIONS.md | 決策及理由，取代哪個舊決策 | 有實質選擇時 | 讀相關條目 |
| docs/ENVIRONMENT.md | 實際版本、執行器、設備、工作命令 | 環境變更 | 是，簡讀 |
| docs/sessions/ | 每次工作的追加式紀錄 | 每次收工 | 只讀最新或相關紀錄 |
| docs/SOURCES.md | 文件網址、版本、採用結論與驗證狀態 | 增加來源／API 更動 | 按需 |
| cases/ | 正常、故障及保留測試規格 | 新增案例時 | 按需 |
| src/parcel_forge/ | schema、生成器、計算、檢查 | 開發時 | 按需 |
| scripts/ | 版本對應的 launcher 與 CLI 入口 | 開發時 | 按需 |
| tests/ | 有意義的數學、幾何與回歸測試 | 功能變更 | 按需 |
| runs/ | 資產、報告、圖片、軌跡、日誌 | 每次執行 | 讀摘要，不一次塞完整 log |

STATE 是目前真相的索引，不是完整日記，建議維持一至兩頁。sessions 記錄歷史；DECISIONS 記錄為什麼；run 保存證據。三者不可只用聊天摘要取代。

狀態定義：`todo`、`in_progress`、`blocked`、`verified`。只有驗收實際執行通過才寫 verified。程式已寫但沒 GPU 時，仍是 in_progress／blocked。

Git 保存程式、規格、文字報告、環境鎖定與小型基準。大型影片、快取與量產 USD 可放在持久磁碟，以 manifest 記錄位置和 SHA256。**Git commit 不等於備份**；每週結束把 repo 推到已授權遠端或備份位置，大型證據另備份。不要自動建立公開 repo。

當前進度對應的證據若來自舊 commit，應標 `stale`；不可把舊通過報告當成本次修改的通過。保存 dirty diff 或先提交相關修改後跑驗證，讓證據能對應精確程式版本。

## 5. 每週固定節奏

| 時段 | 你做什麼 | Agent 做什麼 | 留下什麼 |
| --- | --- | --- | --- |
| 開始 10–15 分鐘 | 看 STATE 的摘要 | 檢查 repo、讀交接、跑 smoke | 環境健康與上一關是否仍可重现 |
| 中段一 | 確認本次只做一張卡 | 實作卡片要求 | 小而清楚的差異 |
| 中段二 | 看一個正常、一個故障結果 | 執行驗證與排錯 | JSON、圖片、必要軌跡 |
| 學習 15–20 分鐘 | 改一個參數、先猜結果 | 解釋觀察到的差異 | 一段 LEARNING 記錄 |
| 結束前 15 分鐘 | 看「做完／沒做完／下一步」 | 寫 checkpoint 與交接 | STATE、session、下一張卡 |

這是工作安排，不是要求每天投入。只有一小時的那週，可以只重現上一關、修一個錯並交接。不要因為日曆換週而跳過未通過的關卡。

中斷處理：每完成一項驗證就寫入檔案，不能等額度快用完才保存。工具執行結果先寫磁碟，再請 AI 解讀。長程序使用已核准的 tmux／作業機制並記錄 PID、命令與輸出路徑；重新接手要先查程序是否還活著，不能盲目重開。

## 6. 軟體架構與工具契約

資料流：文字／尺寸 → schema → deterministic generator → USD → 靜態檢查 → Isaac 行為檢查 → 視覺複核 → 封存。任一必要關卡失敗，輸出結構化錯誤，agent 再選擇有限修正。

| 模組 | 輸入 | 輸出 | 應避免的責任 |
| --- | --- | --- | --- |
| schema.py | JSON/YAML | 驗證過的規格＋錯誤 | 不啟動 simulator |
| build_box.py | 規格＋seed | USD＋幾何 manifest | 不自己宣稱物理成功 |
| mass_properties.py | 板件與質量配置 | 總質量、COM、慣量 | 不由 VLM 隨意填 tensor |
| inspect_usd.py | 真正輸出 USD | 尺寸、階層、碰撞／質量讀回 | 不只讀輸入 schema 假裝驗證輸出 |
| validate_static.py | USD＋task profile | JSON findings | 不修改 asset 讓它自己過關 |
| simulate_checks.py | USD＋測試設定 | 軌跡、metrics、結果 | 不訓練 policy |
| render_evidence.py | USD／實際模擬狀態 | 圖片＋camera manifest | 不拿事後重建場景冒充真實模擬 |
| repair_loop.py | findings＋修正預算 | patch、新 run、停止原因 | 不改 acceptance profile |
| batch.py | cases＋seeds | 逐件 run＋總表 | 不讓 agent 決定每個 seed |

工程介面規格（M0 之後逐步實作，現在不能直接執行）：

```text
./scripts/pf doctor --out runs/<run-id>
./scripts/pf build --spec cases/<case>.yaml --out runs/<run-id>
./scripts/pf validate --asset <usd> --profile profiles/open_box_v1.yaml --out <dir>
./scripts/pf simulate --asset <usd> --suite cavity --out <dir>
./scripts/pf render --asset <usd> --views evidence_v1 --out <dir>
./scripts/pf verify --case <case-id> --out <dir>
./scripts/pf batch --suite <suite-name> --out <dir>
```

`scripts/pf` 的工作是轉到已確認的 Python／Isaac launcher，傳遞參數與 exit code；不得自行 pip 安裝／更新環境。純 schema 檢查可走一般 Python；simulation 和需要 Kit 的渲染走 Isaac 環境。第一版可讓全部使用同一已安裝 Isaac Python，減少不必要的雙環境衝突。

建議自訂 exit code：0＝必要檢查全通過，2＝資產／規格失敗，3＝環境／工具故障，4＝證據不足。外部工具原始 exit code 另存；不可混為本專案定義。

每次 run 至少包含：request.json、resolved_spec.json、environment.json、manifest.json、asset.usda、validation.json、summary.md、logs/；有動態測試就加 trajectory.csv，有渲染就加 renders/。manifest 保存程式 commit、dirty diff hash、輸入 hash、資產 hash、驗證器／profile 版本、seed、命令、UTC 時間、後端、dt。來源不是本次產生的證據需註記。

## 7. 開口紙箱的精確幾何規格

第一個示範箱：外長 L＝0.30 m、外寬 W＝0.20 m、外高 H＝0.15 m、壁厚 t＝0.005 m。這是工程測試樣本，並非聲稱某實體箱的量測值。箱底外表面中心是資產 local 原點，Z 朝上。

以下五個板件互不重複計算體積，接縫相接。尺寸皆為完整長寬高，不是 half-extents：

| 板件 | 尺寸 (x,y,z) | 中心 (x,y,z) |
| --- | --- | --- |
| bottom | (L,W,t) | (0,0,t/2) |
| wall_x_pos | (t,W,H-t) | ((L-t)/2,0,(H+t)/2) |
| wall_x_neg | (t,W,H-t) | (-(L-t)/2,0,(H+t)/2) |
| wall_y_pos | (L-2t,t,H-t) | (0,(W-t)/2,(H+t)/2) |
| wall_y_neg | (L-2t,t,H-t) | (0,-(W-t)/2,(H+t)/2) |

內長 Li＝L−2t＝0.29 m；內寬 Wi＝W−2t＝0.19 m；內部高度 Hi＝H−t＝0.145 m。內底 local z＝t。輸入不滿足 L>2t、W>2t、H>t 時直接拒絕。

第一版以 `UsdGeom.Cube` 表示板件，清楚處理 size 和 scale；世界尺寸檢查要計入所有祖先 transform。不要在祖先又縮放一次造成雙重比例。視覺與碰撞可使用同一板件，後續才拆更細視覺層。

固定箱測試：板件有 CollisionAPI，箱根不加動態 RigidBodyAPI。動態箱測試：只在箱根設定一個剛體，五塊 collider 是其子件，子件不各自變成剛體。場景地板與 PhysicsScene 放在測試世界，避免每個資產自帶重複的全局場景。

輸出 `defaultPrim` 指向資產根，stage 明確使用 metersPerUnit＝1、kilogramsPerUnit＝1、upAxis＝Z；所有物理數字依此解讀。OpenUSD 未明寫長度單位時預設可能是公分，因此不能靠模型猜。[長度單位](https://openusd.org/dev/api/group___usd_geom_linear_units__group.html)；[質量單位 API](https://openusd.org/dev/api/usd_physics_2metrics_8h_source.html)

最小 schema 範例（設計規格，非已實作 parser）：

```yaml
schema_version: 1
asset_id: open_box_demo
asset_type: open_box
intended_task: place_object_inside
units: {length: m, mass: kg, time: s}
frame: {origin: bottom_outer_center, up_axis: Z}
geometry:
  outer_size_m: [0.30, 0.20, 0.15]
  wall_thickness_m: 0.005
  lid: none
physics:
  body_mode: dynamic
  shell_mass_kg: 0.20
  mass_distribution: uniform_shell_volume
  collider: compound_boxes
  material_profile: engineering_baseline_v1
provenance:
  dimensions: engineering_example
  shell_mass: uncalibrated_assumption
  material: uncalibrated_assumption
seed: 0
```

schema 層另檢查所有數值 finite、質量>0、尺寸與厚度可構造、名稱唯一、enum 合法、未知欄位拒絕；不能只檢查型別。密度必須以板件體積計算，不能拿紙箱外包絡體積當成紙板體積。

## 8. 質量、質心與慣量怎麼做

固定示範箱質量 M＝0.20 kg 為未校正初值。先依每塊板件體積分配質量 mi＝M·Vi／ΣVi。每塊板件中心 ci；總質心 c＝Σ(mi·ci)／M。上方沒有蓋，COM 不應直接硬寫 H/2。

長方體在自身中心、沿自身主軸的慣量為：Ixx＝m(b²+c²)/12，Iyy＝m(a²+c²)/12，Izz＝m(a²+b²)/12。將各板件慣量旋轉到共同座標，再用平行軸定理加總：

```text
d_i = c_i - c
I_total = sum(R_i I_i R_i^T + m_i ((d_i dot d_i) Identity - d_i d_i^T))
```

由對稱正定 tensor 求主慣量及主軸；輸出主軸旋轉時檢查右手座標與 quaternion 排列。OpenUSD MassAPI 提供 mass、centerOfMass、diagonalInertia、principalAxes；centerOfMass 是對應 prim 的局部框架，不能把 world 值直接塞入。[MassAPI 文件](https://openusd.org/release/api/class_usd_physics_mass_a_p_i.html)

必要測試：M 加倍慣量加倍；幾何整體放大 s 且質量固定時慣量乘 s²；平移整體不改變繞自身 COM 的慣量；主慣量均為正並满足三角不等式（含合理浮點容差）。

後續要偏心內容物時，schema 增加質量、形狀、位置、是否固定；一起重算 COM 和慣量。只改 COM 而保留原 tensor 不作為量產策略。能移動的內容物要獨立剛體，不能用靜態偏心數字代替其移動。

## 9. Simulator 啟動與物理初值

使用現有 Isaac Lab checkout 中的 rigid-object tutorial 作為適配樣板。保持該版要求的初始化順序：先啟動 AppLauncher，再 import 依賴 Kit 的模組；每一步寫回／讀回狀態遵守該版範例。關閉時用 finally 確保 simulation_app.close，不把正常 GUI 無限 loop 搬成 headless 批次。[官方剛體教學](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/01_assets/run_rigid_object.html)

使用 AppLauncher 的 headless 相機流程時，官方文件說明 `--enable_cameras` 與 Isaac Lab SimulationContext 配合；不要混接另一個同名 SimulationContext。[AppLauncher 教學](https://isaac-sim.github.io/IsaacLab/main/source/tutorials/00_sim/launch_app.html)

以下是**待以基準案例校準的工程初值**，不是材料真值或官方通用設定：

| 設定 | 初值／策略 | 檢查 |
| --- | --- | --- |
| dt | 1/240 s | 以較粗 dt 對照，必要時細化；記錄效能 |
| gravity | (0,0,-9.81) m/s² | 無碰撞自由落體與解析值比較 |
| physics duration | 3 s | 最後 0.5 s 用於沉降指標 |
| rest offset | 0 | 與圖形表面一致的起點 |
| contact offset | 0.001 m | 對本示範箱；各形狀都記錄，且大於 rest offset |
| static/dynamic friction | 0.5 / 0.4 | 未校正初值；要記 material pair 與 combine mode |
| restitution | 0 | 沉降測試的初值，不代表所有包材 |
| solver | 記錄安裝環境實值並固定 | 有問題再依證據調整，不讓 agent 隨機掃所有參數 |
| device | 指定一張可用 GPU | 雙卡不會自動讓單個 physics scene 加倍快 |

contact offset 控制開始產生接觸的距離；rest offset 控制靜止間隔，二者不等於柔順度。要柔順接觸時，獨立驗證 stiffness／damping API 及效果，MVP 不啟用。[PhysX 說明](https://nvidia-omniverse.github.io/PhysX/physx/5.1.2/docs/AdvancedCollisionDetection.html)；[Isaac Lab 材質原始碼](https://isaac-sim.github.io/IsaacLab/main/_modules/isaaclab/sim/spawners/materials/physics_materials_cfg.html)

靜態工具成功不代表 PhysX cooking 成功；simulation 啟動日誌中的 unsupported collider、fallback、invalid inertia 必須抓出並分類。固定 timestep 與 seed 改善重現性，但不承諾跨 GPU／driver 位元完全相同。

## 10. 自動驗收：測什麼、怎麼算、怎麼避免假成功

下面的門檻是示範箱的 v1 工程驗收設定。首次用正確基準調校一次，記錄理由並封存 profile；之後不得為單件失敗偷偷放寬。擴充不同尺度時建立新 profile，不直接套 1 mm 到所有物件。

### G0：環境與基本積分

先做無物件碰撞的短自由落體，取高度足夠的立方體，初速零，測量 t＝0.1 s 時下降距離；理論值約 0.04905 m。以當前 dt 的離散誤差設定約 3 mm 初始容差；若失敗先看 timestep、重力及單位，不開始調箱子。固定記錄姿態、速度讀回 API 和座標慣例。

必要結果：無 NaN、可讀狀態、有限步數結束、正常關閉；需要渲染的 profile 額外確認 PNG 尺寸非零且確實看到物體。只有物理成功但 renderer 壞掉應分開記錄。

### G1：輸出 USD 靜態檢查

檢查真正寫出的 stage：可開啟、無缺引用、defaultPrim、單位、upAxis、世界尺寸、板件數、RigidBody/Collision 階層、材質綁定、finite 質量／慣量。動態箱只允許單一根剛體；固定箱依 profile 不要求動態剛體。

geometry tolerance 初值＝0.0001 m。尺寸從輸出幾何與 transform 讀回，不能用輸入值相互比較。對單純 Cube 板件可精確取得 corners；未知 mesh 的 cavity 檢查需另外實作，不宣稱目前已支援。

Isaac Sim 6.0 的 asset validation 可加入適用規則；不同資產用途採不同 profile，無關的機器人規則不應強制套紙箱。任何 skip 都列出 rule ID 和理由；自訂檢查與官方檢查的 coverage 分開報告。[6.0 驗證文件](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/robot_setup/asset_validation.html)

若已列為必要的官方驗證器無法執行，該 profile 結果是 blocked。可以另有較小的 internal profile，但不能把它的通過稱為官方 SimReady 認證。

### G2：空腔幾何與放入測試

固定箱的外底原點放在 world z＝0.20 m，世界地板在 z＝0。刻意留下落差，避免漏底時物件被地板接住而誤判成功。

測試立方體：邊長 a＝0.04 m，質量 0.05 kg，這是工程探針。箱不動、探針是動態剛體，無初速度。從箱口上方 0.05 m 的淨空開始，探針中心 local z＝H＋a/2＋0.05。

內部可用中心範圍：ux＝Li/2−a/2−margin，uy＝Wi/2−a/2−margin，margin 初值 0.005 m。若 ux 或 uy≤0，標 PROBE_DOES_NOT_FIT，不能算漏底或 collider 壞。

放入位置採 x∈{−ux/2,0,ux/2}、y∈{−uy/2,0,uy/2}，共 9 個案例，逐次獨立 reset。第一個里程碑先做中央一點，通過後擴充九點。

3 s 後檢查最後 0.5 s：

1. 探針八個角點轉回箱體 local frame，x/y 均落於 cavity 範圍內（含明定 1 mm 動態容差）。
2. 探針最底角點 local z 接近 t，初值容差 1 mm；全部角點不低於內底超出容差，也不高出箱口。
3. 質心在最後時間窗相對起点的最大位移≤1 mm，線速度最大值≤0.01 m/s，角速度最大值≤0.1 rad/s。這些不是物理定律，是本測試判定沉降的操作定義。
4. 碰撞日誌沒有明確失效；感測器可用時，確認 probe 對箱體有法向承托，而非地板承托。

接觸感測器資料須與 frame、body filter 和更新順序一起確認。`net_forces_w` 是法向合力，不可當成包括切向摩擦的完整力；篩選資料的語意與形狀需按安裝版本確認。[官方感測器 API](https://isaac-sim.github.io/IsaacLab/main/source/api/lab/isaaclab.sensors.html)

接觸資料非必要時可用明定的 pose-only profile，但報告必須寫清楚沒驗到接觸來源；不能把缺資料填零或假 pass。reset 後需更新 simulator 和 sensor，再讀當前時間戳；初期寧可每案新場景換取隔離，之後再最佳化。

### G3：底板與牆面是否真的阻擋物件

G2 只證明放得進去且底部承托，沒有證明四面牆都有效。因此加入：

- 缺底板故障：探針會落到地板，local 最底 z 明顯低於 t，必須 fail。
- 封口故障：在箱口加看不見的 collider 或改整箱凸包，probe 停在 H 附近，必須 fail OPENING_BLOCKED。
- 缺牆碰撞故障：對應板件仍可見但 CollisionAPI 被移除；靜態檢查必須報錯。
- 側向測試：把小 probe 初始置於箱內、接近選定牆面且不重疊，給沿法向向外的已知速度（初值 0.2 m/s），使用距離與時間足以碰到牆的配置。檢查沒有穿越牆外，且收到合理阻擋。每牆一個測試，重置初始狀態。

側向測試先以無牆對照確認 probe 的確會走過測試區域，避免摩擦先讓它停住造成假成功。必要時設計短距離、高於底面的碰撞測試，使底面摩擦不干擾。

穿透指標在這個 primitive MVP 以板件與 probe 幾何計算，並檢查每步轨迹；對任意 mesh 不宣稱具備精確 signed distance。AABB overlap 只能初篩，不可當通用穿透證明。

### G4：動態箱掉落與穩定性

另建動態箱版本，確認 root 的 rigid body、質量、COM、慣量真的讀回。箱外底離地 0.03 m、正放、初速度零，跑 3 s，檢查不穿地、不爆飛、不持續震盪，並量測最後 0.5 s 的位移／速度。這只验证正放落地，不保證任意姿態都穩定。

正放通過後，再加小角度傾斜與側放；不同預期姿態分案例，不強迫所有姿態最後都「站正」。COM 測試使用受控傾斜或推動與支撐區判定，不以 COM 偏移本身作為必定翻倒的條件。

### G5：已知控制器的抓取／放置（MVP 擴充）

先用尺寸小於夾爪開口的立方體，沿已知接近路徑做固定抓取：接近→閉合→抬高 0.05 m→維持 1 s→放入箱內。記錄夾爪開口、最大力、控制器、抓點、姿態、接觸與物件相對夾爪位移。

驗收分成 reach、close、lift、hold、place 各段。抓不到時先確認幾何可行性與控制設定，不能直接提高摩擦。第一版箱長 0.30 m，可能根本超過平行夾爪可夾寬度；不要把「抓整箱」設為必過項。

已知立方體通過後才換杯子；杯口與把手孔要依任務保留碰撞通道，不能用整杯 convex hull 然後宣稱把手抓取可用。

### G6：VLM 視覺複核

固定相機／燈光／背景，輸出前斜視、後斜視、正上方、側面、底部，以及獨立的 collider 疊圖。視覺與 collider 圖需可區別。動態證據採實際模擬 frame，加上 frame index、sim time，不要求初版直接支援長影片理解。

VLM 只回答：是否是開口箱、是否缺面、外觀是否符合需求、可疑相交位置、需哪個額外視角。輸出 finding、image_id、prim 或區域、severity、reason、requested_check。看不清要 `inconclusive`，不得估算毫米級穿透或摩擦值。

必要視覺項若不確定，最終不能 PASS。第一版沒有 VLM 時，用人工抽查加明確的「尚未自動語意驗收」範圍；不要假裝此層已完成。

### G7：驗證器本身的可靠性

建立至少 6 個錯誤案例：封口、漏底、缺一面牆碰撞、尺寸倍率錯、負質量或非 finite 值、錯誤根剛體階層。至少一個正常對照。

不是每個錯誤都要送 simulator；schema 可擋下的就早擋。測試應檢查預期錯誤碼和分類，不只看任何非零 exit code，避免 interpreter 壞掉卻算「抓到資產錯誤」。

新增兩個未給修復 agent 看的 holdout 故障，用於最後比較。固定生成器出現新 bug 時加案例，保留過去錯誤，不因修好就刪除。

## 11. 錯誤報告與 AI 修正規格

報告需要能驅動下一步，不只是 fail 字串。下例是格式示例，數值為示意，不是實驗結果：

```json
{
  "report_version": 1,
  "run_id": "EXAMPLE_ONLY",
  "asset_sha256": "<actual-hash>",
  "validator_version": "<actual-commit>",
  "profile": "open_box_v1",
  "verdict": "fail",
  "findings": [{
    "code": "OPENING_BLOCKED",
    "check_id": "cavity_center_drop",
    "prim_path": "/Asset/Collision",
    "observed": {"probe_bottom_z_local_m": 0.150},
    "expected": {"probe_bottom_z_local_m": 0.005},
    "tolerance_m": 0.001,
    "evidence": ["trajectory.csv", "renders/top_collision.png"],
    "suggested_inspection": "Check for a collider spanning the opening"
  }]
}
```

`suggested_inspection` 是調查方向，不是已證實根因。讀到 stop_at_rim 也可能是其他幾何或初始姿態問題，agent 要先看證據。

修正規則：最多 3 次修正；每次都產生新候選 asset 和新 run；修正前後保存差異。先允許修正 schema／局部生成器，不要一開始開放任意專案修改。修正器只能寫候選資產與指定生成器目錄，不能寫 tests／profiles／validator；簡單做法是為允許目錄套 patch，拒絕其他檔案變更。

開發者對 validator 的必要修正要另開任務，先說明 oracle 或量測為何錯，用正反案例驗證後更新版本；然後重跑既有資產。不可在修復同一個失敗 run 時順便放寬 validator。

停止條件：重複同一失敗且無新證據、超出次數、工具壞掉、缺必要量測、候選比前版破壞更多已通過項。狀態為 needs_human／blocked，保留最後有效版本，不自動覆蓋 published 資產。

在 M7 前，AI 是你互動式 coding agent，不需要付費 API orchestration。M8 再接非互動入口，並確認所用 CLI 版本、登入方式與費用；不要假設聊天訂閱含 API 額度。

## 12. 逐關任務卡與每週驗收

估計每關約 3–8 小時，M0 遇到環境問題或 M5 遇到物理讀回問題可更久；總體約 45–75 小時是規劃區間，不是保證。每週投入 4–8 小時，可安排約 8–16 週。若沿用先前程式，逐項重跑驗收後可縮短，不能只因已有檔案就跳過。

### M0｜建立交接與環境基準

**目的：**下週開新對話仍知道怎麼啟動、目前做到了哪裡。

Agent 動作：

1. 只讀盤點現有 Task 1、Git 狀態、Python、Isaac Lab commit、Isaac Sim build、driver、GPU 可用情況與啟動命令。
2. 確認已有改動與舊測試，不覆蓋使用者檔案；決定沿用 repo 或建立獨立 repo，記錄原因。
3. 建立第 4 節列出的最小文字檔：AGENTS、CLAUDE、STATE、ROADMAP、ENVIRONMENT、tasks/M0。
4. 從已安裝版 rigid tutorial 做有限步數 smoke，保存位姿與 exit code；再加一张圖片。
5. 建立可用的 `scripts/pf doctor`，將實際命令寫入 ENVIRONMENT。

產物：環境指紋、smoke run、交接檔案。驗收：G0；新對話只讀檔案能重跑。失敗時本週只處理環境，停止新增功能。

你學的概念：USD 是場景描述；simulator 是執行它的程式；headless 是不開互動視窗，仍可獨立配置渲染。

小實驗：把落下高度調整，說明哪個檔案控制它。不要改模型權重或安裝一堆服務。

### M1｜手工基準與故障樣本

**目的：**先知道什麼是對的箱子，再驗證生成器。

Agent 動作：按第 7 節固定公式建立正常箱；建立獨立的封口、漏底案例；把固定箱抬離地板；中央 probe 放入；輸出 trajectory。這個基準可以由小型人工審閱程式建立，不必 GUI 手刻；但驗證器要從 USD 讀回實際值。

產物：3 個案例、圖片與轨迹。驗收：正常中央放入通過；封口與漏底失敗原因不同。別把圖片有箱子當完成。

你學的概念：visual 與 collider 可以不同，畫面空的地方可能有 invisible collider。

小實驗：開／關碰撞疊圖，指出 probe 卡住的位置。

### M2｜把驗證器做成可重跑工具

**目的：**同一測試在下週或別台相容機器可重現。

Agent 動作：實作 G1–G3 的中央版、統一 JSON/exit code、純幾何和 simulation 工具分開、補錯尺寸與缺牆故障；建立 pytest 或等效的數學／幾何回歸。解析 exit code 不能掩蓋 simulator crash。

產物：`validate`／`simulate` 最小 CLI、版本化 acceptance profile。驗收：所有設計故障得到預期分類；一次乾淨重啟後仍通過。此關不是要求一般開發的過度測試，而是驗證器本身就是產品核心。

你學的概念：測試 oracle＝判定對錯的依據；正常樣本和故障樣本都必須有。

小實驗：把某一面牆的 collider 移除，先猜哪個錯誤碼會出現。

### M3｜schema 到參數化 USD

**目的：**調尺寸靠輸入資料，不靠每次改程式。

Agent 動作：實作嚴格 schema、五板件生成器、seed 記錄、unit metadata、輸出 hash；測試 10 組合理尺寸，其中至少含薄／厚壁、長／寬箱；所有 probe 適配條件先算清楚。

產物：`build`、10 組規格、幾何讀回報告。驗收：G1 並對可容納 probe 的案例跑中央 G2；非法厚度在生成前拒絕；相同輸入有相同幾何/參數結果。USD 檔案位元是否完全相同另外定義，不能拿時間戳差異當物理不重現。

你學的概念：schema 是可接受資料的規則；generator 是把規格變成資產的程式。

小實驗：改外寬 0.20→0.24 m，預測內寬從 0.19→0.23 m，再讀驗證報告。

### M4｜質量與動態箱

**目的：**從「可碰撞的容器」進一步到「會動且質量合理的容器」。

Agent 動作：實作第 8 節的板件質量、COM、慣量；新增動態模式；保持固定模式；寫 mass property 數學測試；讀回 simulator 中的有效參數；跑 G4。

產物：mass properties 報告、動態 drop run、官方規則適配結果。驗收：質量縮放、尺寸縮放、平移不變性通過；靜態箱放入功能無回歸；動態箱不散成五塊。

你學的概念：mass 決定平移慣性；inertia 描述轉動慣性；COM 不等於 bounding-box 中心。

小實驗：質量加倍但形狀不變，檢查 tensor 加倍；不要期待真空自由落體落得更快。

### M5｜擴充九點與動態驗證

**目的：**驗收不只對正中央湊巧成功。

Agent 動作：九點 cavity 測試、四面側向測試、reset 隔離、全部 corners containment、沉降時間窗；感測器若支援則加入箱體承托證據；測試 dt 與初始高度的有限擾動。

產物：逐案例結果表、最差位移／穿透代理值、失敗短影片或圖片。驗收：正常例通過適用測試，已知故障仍被抓出；持續有 NaN／stale sensor 則 blocked。

你學的概念：contact 是在模擬步進才發生；看最後一張圖不足以排除過程穿透。

小實驗：把 probe 增大到不可能放進箱內，應得到規格不適配，而不是叫 AI 修箱子。

### M6｜多視角證據與人的檢查頁

**目的：**你十分鐘內能判斷本週做了什麼。

Agent 動作：建立固定相機組、碰撞疊圖、圖說與軌跡摘要；生成本機 HTML 或 Markdown 報告（不必架網站）；保存實際動態幀；顯示 run、commit、asset hash。

產物：一頁案例報告。驗收：正常、封口、漏底能在同一格式看出差別；圖片確實對應相同 asset hash 和 run；不能偷用前次 render。

你學的概念：視覺驗收和物理驗收互補；相機看不到不代表沒有問題。

小實驗：只看側面是否能發現箱口封住？再加俯視和 collider 圖比較。

### M7｜互動式 AI 修正閉環

**目的：**先證明讀報告真的能修好，不急著做全自動服務。

Agent 動作：從 3 個可修故障開始；只讀規格、report、少量證據；提出根因假說及最小 patch；重跑失敗項與中央正常基準；最多三次。修正不得改 evaluator/profile。

產物：before/after、patch、重跑結果、修正次數。驗收：至少示範兩種不同故障的成功修復；至少有一個超預算／不可修問題能正確停下。這是工程功能验收，不宣称統計成功率。

你學的概念：修好要有新證據；「我認為修好了」不算。

小實驗：把路徑故意設成不存在，確認系統報工具／輸入問題，不亂改物理。

### M8｜自然語言與批次自動化

**目的：**一句話變規格，同一家族多件可重現。

Agent 動作：文字解析到 schema、記錄明示／假設／缺失欄位；對模糊單位要求澄清或拒絕，不默認 cm=m；包裝實際可用的 agent CLI/API；批次 driver 固定讀 cases 和 seeds，先序列執行，再量測是否平行。

另接第 10 節 G6 的 VLM adapter：輸入固定圖片與 checklist，輸出可解析 findings，保存模型識別、prompt 版本與原始回覆。先測正常／缺面／遮擋圖；若本週沒完成 VLM，M9 只比較前兩種流程，第三種標未實作，不能填估計結果。

產物：30 個案例的自動報表，文字→resolved spec→asset→report 全鏈。驗收：可中斷重啟、不覆寫已完成 run、不將資產失敗當環境失敗；成本未知就記 unknown，不用估計假裝實收費。

你學的概念：prompt 負責表達需求；schema 負責限制；工具負責執行。

小實驗：分別輸入「30 公分長的箱子」與「30 長的箱子」，看系統是否保留不確定性。

### M9｜交付、換對話與最小評估

**目的：**不用原對話也能完整接手，並知道自動化帶來什麼改善。

Agent 動作：固定評估 cases、模型與 profile 版本；比較一次生成、程式驗證修正、再加 VLM；至少測保留故障；重現一個成功與一個失敗 run；由全新對話依 README 和 STATE 接手；整理限制與下一階段。

產物：版本標記、最小重現資料、結果表、完整操作說明。驗收：新對話能在不讀所有歷史的情況下啟動與重現；所有完成狀態都有證據。

你學的概念：可重現交付＝輸入、程式、環境、證據都可追溯。

不將「30 案成功」解讀為任意包裹通用。記錄資產種類、尺寸範圍、試驗次數與失敗分布。

## 13. 可複製的專案記憶模板

這些是待放入你的 repo 的文字模板；本次只交付手冊，未直接修改遠端專案。模板中的未知值保留 unknown／null，不填猜測。

### AGENTS.md 最小內容

```markdown
# Project contract

Build a reproducible Isaac Sim asset generation and validation workflow.
Current scope: primitive open boxes and rigid probes, PhysX baseline.

Before changes:
- Read docs/STATE.md, docs/ROADMAP.md, docs/ENVIRONMENT.md, and the current task card.
- Check Git status. Preserve pre-existing changes.
- Summarize the current milestone, evidence, and next action in Traditional Chinese.
- Treat local version-matched examples as the API implementation reference.

Execution:
- Work on one bounded task card at a time.
- Reuse existing Task 1 work after reproducing its checks.
- Separate specification, asset generation, validation, and agent repair.
- A closed-looking image is not proof of collision or task readiness.
- Never modify acceptance criteria to make an asset pass.
- Report tool failures as blocked, never as successful validation.
- Keep estimated physical parameters marked as estimates.
- Do not upgrade simulator, driver, or dependencies as an incidental repair.

Evidence and handoff:
- Write tool outputs to a unique run directory before summarizing them.
- Record input/asset hashes, code version, validator/profile version, command and exit code.
- Save failed attempts. Never replace old evidence with new results under the same identity.
- At each checkpoint update docs/STATE.md and the current task card.
- At session end append docs/sessions/<timestamp>.md and give one exact next action.
- Call a milestone verified only after its required checks actually ran and passed.
- When teaching, explain the result and one small experiment for the user.
```

這個範本是專案指引，不是執行層安全限制；修復 agent 對驗證器的寫入限制仍要由工具／patch allowlist 實作。

### CLAUDE.md 最小內容

```markdown
This project uses AGENTS.md as its shared project contract.
Read AGENTS.md before editing, then read the handoff files it names.
Use docs/STATE.md and saved run evidence as the current progress source.
Do not infer completed work from previous conversations alone.
```

不用 symlink 也能運作，能減少不同 OS／打包方式帶來的問題。啟動一次新對話確認實際讀到了規則；若全局或父層已有規則，檢查並保留適用的指引。

### docs/STATE.md 範本

```markdown
# Current state
Updated: <actual timestamp and timezone>
Repository: <actual path>
Branch / commit: <actual values>
Working tree: <clean or describe uncommitted changes>
Milestone: M0
Status: todo

## Verified
- None yet. Do not infer runtime validation from this plan.

## Implemented but unverified
- <files/features, if any>

## Latest evidence
- Run: <path or none>
- Asset/code/profile hashes: <actual values or unknown>
- Command and exit code: <actual result>
- Coverage: <what this proves and what it does not>

## Blockers and failed attempts
- <symptom, evidence path, what has already been tried>

## Next exact action
- <one action; command only if it already exists>

## Related task and decisions
- docs/tasks/M0.md
- <relevant decision ids>
```

### docs/tasks/Mx.md 範本

```markdown
# Task Mx: <name>
Status: todo
Depends on: <verified prerequisite>

Goal: <observable behavior>
Inputs: <files, environment, test cases>
Scope: <allowed changes>
Steps: <ordered implementation and check actions>
Acceptance: <test ids, expected outcomes, tolerances>
Evidence: <required reports/images/trajectories>
Failure routing: <which layer to investigate>
Progress: <append exact findings and remaining steps>
User learning: <one concept, one experiment>
Next action: <one concrete action>
```

### docs/sessions/<timestamp>.md 範本

```markdown
# Session <timestamp>
Task: <id>
Start/end commit: <actual values>
Changed files: <list>
What changed and why: <short explanation>
Checks run: <exact command, exit code, run path>
Passed: <proven observations>
Failed/blocked: <evidence and attempted fixes>
Decisions: <decision ids>
Learning: <one concept the user can now explain>
Next session: <one exact starting action>
Background process: <none or actual process/job id and output path>
```

### docs/DECISIONS.md 範例

```markdown
# D001 — Open box uses five primitive colliders
Status: accepted for MVP
Reason: Task requires a usable cavity; a whole-object convex hull seals it.
Alternative: Convex decomposition, unnecessary for this regular shape.
Consequence: Visual detail can change independently, but collision fidelity needs revalidation.
Evidence: <local passing and fault-case run paths when available>
Revisit when: Irregular or damaged walls become task requirements.
```

決策若改變，新增 D002 並標明取代 D001；不刪除舊理由。

## 14. 你每次可以直接貼给 agent 的指令

### 第一次開始

```text
請讀取我附上的 IsaacSim_Asset_Workflow_Handbook.md，這是專案建構規格。
今天只做 M0，不要一次實作整套系統。

先只讀盤點目前 repo 與已有 Task 1 程式／測試／進度文件，確認哪些可以沿用。
保留既有未提交修改，不要重建或升級 Isaac Sim、Isaac Lab 或 driver。
以實際環境與本地版本範例為準，記錄版本、啟動方式及 GPU。
建立手冊第 13 節的入口與交接檔案，未知資訊不要猜。
完成有限步數的 rigid-body smoke，保存位姿、圖片、命令及退出碼。
若無法執行模擬，明確標 blocked 並保存根因，不宣稱驗證通過。

結束時更新 STATE、M0 任務卡、session 紀錄；列出唯一下一步。
最後用初學者能懂的繁體中文說明：改了什麼、如何證明、我能動手改哪一個參數。
```

### 隔週回來／新對話

```text
請從專案檔案恢復進度，不假設你記得之前對話。
讀 AGENTS.md、docs/STATE.md、docs/ROADMAP.md、docs/ENVIRONMENT.md、當前任務卡與最新 session。
先檢查 Git 狀態、證據是否對應目前版本、背景程序是否仍在執行。
用五點說明：目標、已驗證、未驗證、阻塞、下一步，然後直接執行這張卡可完成的下一項工作。
先跑相關最小基準，不重跑與本次風險無關的全部測試。
本次只完成一張小任務；結束時保存新證據並更新交接。
```

### 今天只剩十五分鐘／要收工

```text
請停止擴充功能，先完成安全的收尾與 checkpoint。
保存目前差異、已跑命令、退出碼、run 路徑、失敗原因與背景程序資訊。
更新 STATE、任務卡與本次 session。
清楚分開「已實作」「已驗證」「仍失敗」，並給下次唯一的起手動作。
不要把未執行的測試寫成 pass，也不要只把交接內容留在聊天裡。
```

### 讓 agent 教你一個概念

```text
請以今天修改的程式說明一個最重要的概念。
只選一個參數，先讓我預測改變後的結果，再給我可重跑的小實驗。
指出對應檔案、輸入值、要看哪個指標；不要要求我先讀整篇論文。
```

### 本週驗收

```text
請以當前任務卡的 acceptance 驗收，不以自己對程式的信心驗收。
列出每一項的命令、結果、證據路徑及版本。
至少展示一個正常案例與一個故障案例，說明故障為什麼確實被抓到。
若門檻設計有問題，另開 validator 任務並保留失敗，不在本次修復中偷偷放寬。
完成後更新 ROADMAP 和 STATE；未通過則保留同一關，不自動跳到下一關。
```

## 15. 常見卡關與指定排查順序

| 症狀 | 優先排查 | 不要先做 |
| --- | --- | --- |
| import 模組不存在 | 是否啟動正確 Python、Kit 初始化順序、該版範例名稱 | 隨機 pip 安裝另一版 Isaac |
| 畫面黑／相機回傳空 | enable_cameras、相機姿態、render 更新、光源與初始化幀 | 更換物理材質 |
| 物件卡在箱口 | collider 疊圖、整體 convex hull、隱藏上蓋、probe 是否太大 | 增加重力讓它硬擠進去 |
| 穿過箱底 | 底板 collider、初始位置、尺度、dt、速度、cooking 日誌 | 把地板抬高掩蓋漏底 |
| 箱體散架 | 根與子件 RigidBodyAPI 分布 | 先加五個 fixed joint 補救 |
| 物件懸空 | rest offset、碰撞／視覺尺寸不同、隱藏碰撞 | 讓渲染 mesh 跟著偏移掩蓋 |
| 接觸力一直零 | sensor 開啟、filter、更新順序、當前 frame、有無真實接觸 | 判定「物理引擎壞了」 |
| reset 後讀到前次資料 | simulator/sensor reset 與更新、時間戳 | 直接拿第一幀作判定 |
| 抓取失敗 | 可達性、夾爪寬度、抓點、力／控制器，再看材質 | 一律增加摩擦 |
| 同一案例每次不同 | commit、seed、dt、GPU、初始状態、reset 與外部依賴 | 假設只固定 seed 就完全確定 |
| agent 不斷反覆修 | 錯誤報告是否有數值、版本及新證據；是否同一失敗 | 增加到無限次重試 |
| 下週不知道做哪裡 | STATE 是否有唯一 next action；證據是否存在 | 把所有聊天一次貼回去 |

如果 agent 查到新版 API 與本機不同，讓它查看已安裝原始碼及同版範例，寫一個 adapter 隔離差異。API 文件只能證明有此介面，不能代替本機 runtime smoke。

## 16. 成本與批次策略

開發階段用較強 coding agent 寫工具、定位複雜錯誤。日常同一紙箱家族只執行 schema 及生成器，沒有理由每件重寫程式。VLM 放在數值驗證通過後或指定故障診斷，不對每個 simulation frame 呼叫。

每件記錄：schema parse 次數、repair 次數、LLM/VLM calls、可取得的 input/output tokens、工具運行時間、GPU 記憶體、最終 verdict。實際計價未知時記 unknown；不要把訂閱 usage 當 API 美元成本。

批次先跑 1，再跑 10 序列；確認無狀態殘留和記憶體成長，再決定 2 個 worker 或多環境。平行會增加環境共享／GPU 資源競爭，需要單獨驗證。大量訓練的環境數不是生成 pipeline 的先決條件。

M9 評估可先用 10 個正常、10 個開發故障、10 個保留案例，明確列出類型與比例。比較：

- 資產首次／最終通過率。
- 故障偵測率、正常誤報率與故障漏檢率。
- 可修故障修復率、平均修正次數、人工介入率。
- 中位數及高分位時間、token 與工具成本。
- 證據完整率、重新執行成功率。

三種流程使用相同案例與參數：A 一次生成；B 加程式驗證與修正；C 再加 VLM。保存所有失敗，不只挑漂亮 demo。少量案例結果附分子／分母，不虛報普遍有效性。

## 17. 何時才擴充翻蓋、杯子、包材

只有 M0–M9 的核心版本可重現後才開擴充卡。以下提供設計方向，不含在首版工時承諾內。

**翻蓋：**先做一片，再四片。箱體和每片蓋分別剛體；hinge 在折線，先固定箱體測 revolute joint，再測動態系統。joint 限位按實際翻折幾何與座標設定，不預設所有都是 0–180°。先做開／關目標角、無穿箱、速度穩定；封箱可用邏輯狀態和約束近似，但大 stiffness 不等於可靠鎖定，也不能當作膠帶撕裂物理。切換限位／約束是否需重建要在本機測試。

**杯子：**先從可信資產或規則杯體開始，明確需求是抓外壁、抓把手或放入物品。對需要內腔／孔洞的任務，採 compound／凸分解，必要時評估 SDF；實際 cooking 與吞吐測試後決定。網格水密與法線要按用途檢查，不能把所有 render mesh 一律要求水密。

**泡泡紙包杯子：**先固定外包絡形狀剛體，用文字標記「不能模擬壓縮與拆包」。不要以沿法線 offset 作為通用保證，複雜把手可能自交，外包絡可用較簡單參數模型。是否增加柔順接觸由校準需求決定。

**軟袋／布料：**如果任務真的依賴變形，另設 deformable compatibility spike：一個簡單軟物體、一個剛體／夾爪、接觸、reset、讀回、批次複製與效能。測試通過再擴充資產生成，不以 issue 標題或關閉狀態判斷你本機已支援。

**真實校準：**量尺寸、秤質量；固定接觸材質組合；以受控滑動／傾斜試驗建立摩擦估計，記錄不確定度；COM 與慣量用幾何分布或辨識。不要讓 simulator 調參補償一個錯誤的控制策略。

## 18. 官方模板如何接入，免去你重新研究

這些接入點已整理為 agent 工作，不需要你自行讀完 repo。

| 接入點 | 讓 agent 做的具體動作 | 成功證據 | 啟用時機 |
| --- | --- | --- | --- |
| 本機 Isaac rigid tutorial | 讀同版示例，抽出 launcher、step、state readback、close | 有限步 smoke 與軌跡 | M0 |
| Isaac asset validation | 枚舉安裝版本規則，選適用項，寫 adapter 成統一 findings | 規則列表、逐項狀態、故障例 | M2–M4 |
| NVIDIA workflow 參考 | 借用 run/checkpoint/evidence 結構，不強制引入服務 | 中斷後可恢復 | M0 起 |
| USD Content Agents 現成 CLI | 若要評估，使用獨立 checkout/env，固定 commit，先看 --help 再跑單一小資產 | 實際命令、輸出、成本、與本地 validator 差異 | M7 後可選 |
| Kit USD Agents MCP | 獨立安裝，確認 LFS 資料確實下載、查詢命中與版本 | 可回傳指定 USD API 文件 | 重複遇 API 幻覺才加 |
| LL3M／Blender | 加入額外 geometry backend，不改主 validation contract | 複雜 visual 能轉 USD 並通過任務測試 | 後續異形資產 |
| EmbodiedGen | 將輸出當外部輸入，記來源與授權，統一單位及物理處理 | 與參數化資產使用相同驗收 | 後續比較 |

Kit USD Agents 的官方 quickstart 目前有 Python、Poetry、NVIDIA API key 與 Git LFS 要求；LFS pointer 未下載可能導致「server 啟動但搜尋失敗」。因此不用把它當成第零天就要安裝的必要元件。[官方 quickstart](https://github.com/NVIDIA-Omniverse/kit-usd-agents/blob/main/QUICKSTART.md)

USD Content Agents 的工作流程文件有 `validate run` 和 `simready validate-profile` 等入口；先用該 checkout 的 `--help` 核對契約。它和這份手冊的 `scripts/pf` 是不同 CLI，不能混用參數。[官方 workflow 文件](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/agentic/README.md)

## 19. 數學基準值與本手冊的驗證範圍

本手冊撰寫時，用獨立 Python 計算檢查了第 7、8 節示範箱的五板件配置。計算結果（均質殼體假設）如下，供之後生成器的數學回歸對照：

| 項目 | 值 |
| --- | --- |
| 板件總體積 | 0.0010105 m³ |
| bottom 質量 | 0.0593765463 kg |
| 各 x 牆質量 | 0.0286986640 kg |
| 各 y 牆質量 | 0.0416130628 kg |
| COM（local） | (0,0,0.0552337952) m |
| Ixx（繞 COM） | 0.0016619320 kg·m² |
| Iyy（繞 COM） | 0.0027588147 kg·m² |
| Izz（繞 COM） | 0.0034580587 kg·m² |

這組對稱示範的慣量在 xyz 軸為對角矩陣；輸出主軸時允許等價的 eigenvector 符號表示，測試以重建 tensor 比較較穩健。上述是公式計算，不是 PhysX runtime 結果；也不是實際瓦楞紙箱材料辨識。

已完成的調查：官方專案記憶機制、公開 asset workflow、相關研究方法、OpenUSD 質量與單位、Isaac 6.0 驗證／接觸／啟動文件。尚待你的環境確認：已裝版本 API、GPU headless render、物理有效參數讀回、sensor filtering、實際吞吐、現有 Task 1 可重用範圍。

你的第一個動作：把本手冊放到 coding agent 可讀的專案位置，貼第 14 節「第一次開始」。這次只完成 M0。下次讀 STATE，再繼續 M1；無需把本手冊每一頁或所有論文先讀完。
