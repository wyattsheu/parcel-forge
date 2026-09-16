# Isaac Sim 資產工作流：從零開始的啟動指南

版本：1.0｜2026-09-16

## 1. 這次已確定的起點

- Isaac Sim 環境已建好且可啟動。
- 使用者可透過 WebRTC 觀看。
- 新的資產生成／驗證專案，從空白目錄開始。
- 不沿用舊 Task 1 實作，不刪除或覆蓋舊專案。
- 目前未確認 Isaac Lab、pxr 在一般 Python 中的可用性、headless 相機輸出、控制器、MCP 或新專案測試工具。

**從零開始指的是專案程式與流程，不是重新安裝 Isaac Sim。**WebRTC 能看畫面，證明既有觀看流程可用；它尚不能證明批次腳本、資料讀回與離線渲染都可用。這些是第一階段要實際確認的功能。

本文件是先前 `IsaacSim_Asset_Workflow_Handbook.md` 的啟動補充。兩份文件衝突時，以本文件對「從零開始、不依賴 Isaac Lab、保留現有環境」的要求為準。詳細手冊中的物理公式、驗證方法及證據規則仍沿用。

## 2. 你要準備與交給 agent 的東西

必要項目只有這些：

1. 本文件 `IsaacSim_From_Zero_Start_Here.md`。
2. 詳細規格 `IsaacSim_Asset_Workflow_Handbook.md`。
3. 能操作已安裝 Isaac Sim 機器的 coding agent，例如在該機器終端執行的 Codex／Claude Code。
4. 若你知道，補上目前「能正常啟動 Isaac Sim 和 WebRTC」的命令或啟動腳本路徑；不知道可直接寫「不知道，請先只讀查找」。

不需要先建立 AGENTS.md、寫 Python 或讀論文。第一輪 agent 負責建立專案骨架與交接檔案。你也不用貼全部舊對話、所有日誌、密碼、API key 或 SSH 私鑰。

兩份檔案放入新專案目錄，例如 `~/parcel-forge/`。如果這個目錄已有檔案，不覆蓋；改用另一個清楚命名的新目錄。路徑是建議，不是本次已在遠端建立的事實。

在 coding agent 裡附加兩份檔案，或告訴它們的實際路徑。只貼這段網頁聊天的下載連結，遠端 agent 不一定有權限取用；先下載再上傳到伺服器會較直接。

如果你的 agent 只有一般聊天能力、不能讀寫伺服器檔案與執行命令，它只能提供指令，無法替你驗收環境。這時應改用能在該機器工作的 coding agent。

## 3. 技術路線：先只依賴已裝好的 Isaac Sim

第一版採用：Python＋OpenUSD＋現有 Isaac Sim 的 PhysX 執行環境。先建立規則開口紙箱，之後才擴充複雜形狀。

| 元件 | 第一版用途 | 何時加入 |
| --- | --- | --- |
| 既有 Isaac Sim | 模擬、物理驗證與圖片輸出 | 現在 |
| OpenUSD／pxr | 編寫、讀回 USD 資產 | 由 agent 確認既有 runtime 中的可用方式 |
| JSON＋Python 標準庫 | 規格、結果、進度與命令包裝 | 現在 |
| Git | 追蹤程式與文字規格 | 現在；不自動公開或推送 |
| WebRTC | 人工觀看與抽查 | 沿用現有流程 |
| Isaac Lab | 後續機器人控制、批次環境或學習 | 有具體需求再評估，不是開始的必要条件 |
| Pydantic／YAML | 更完整的 schema 與易讀設定 | 基本流程穩定後，按需加入 |
| Blender／CadQuery | 複雜視覺或幾何 | 紙箱基準完成後 |
| MCP／資料庫 | 工具串接與大量結果管理 | 重複出現需求才加入 |
| LLM/VLM API | 批次自然語言輸入及視覺複核 | 驗證器完成後 |

不要把所有套件安裝進現有 Isaac Sim Python。先用既有 runtime 能提供的功能，缺少非必要套件時優先用標準庫實作。真正需要新依賴時，記錄原因並隔離安裝，保留現有環境。

先建立 `runtime adapter`，統一啟動、步進、讀回與關閉。這樣後續若導入 Isaac Lab，只需新增 adapter，不必重寫 schema、幾何計算和驗證報告。

## 4. 新專案要建立的內容

這些是要建立的規格，不代表現在已經存在或可執行。

| 路徑 | 責任 |
| --- | --- |
| README.md | 目前能做什麼、怎麼啟動、怎麼看結果 |
| AGENTS.md | Agent 每次開工、驗收與收尾規則 |
| CLAUDE.md | 指向同一份專案規則 |
| docs/STATE.md | 當前進度、已驗證證據與唯一下一步 |
| docs/ROADMAP.md | 以下 S0–S7 階段狀態 |
| docs/ENVIRONMENT.md | 實際版本、launcher、working command |
| docs/DECISIONS.md | 技術選擇與理由 |
| docs/tasks/ | 每階段的任務卡 |
| docs/sessions/ | 每次工作的完成、失敗與交接紀錄 |
| src/parcel_forge/schema.py | 輸入資料與跨欄位驗證 |
| src/parcel_forge/geometry.py | 紙箱板件位置與尺寸計算 |
| src/parcel_forge/mass_properties.py | 質量、COM 與慣量計算 |
| src/parcel_forge/usd_author.py | 把幾何與物理資訊寫成 USD |
| src/parcel_forge/runtime/ | 既有 Isaac Sim 的版本適配 |
| src/parcel_forge/validation/ | 靜態、幾何與動態驗證 |
| scripts/pf | 專案 CLI 入口，不假設預先存在 |
| cases/ | 正常案例與故意損壞的案例 |
| profiles/ | 版本化驗收門檻 |
| tests/ | 數學、資料及故障辨識回歸 |
| runs/ | 不覆寫的每次執行證據 |

不用第一天建立所有空檔案或空函式。S0 只建立文件與 doctor，S1 再加最小 runtime；其他模組到對應階段再實作。README 不得把未實作功能寫成已可用。

## 5. 八個建構階段

階段編號 S0–S7 是這次從零開始的主排程；詳細手冊的 M0–M9 用來查技術細節，不必再跑一套重複排程。

| 階段 | 具體工作 | 必須留下的證據 | 通過才前進 |
| --- | --- | --- | --- |
| S0 專案與環境 | 新 repo、入口規則、進度檔、只讀環境盤點、doctor | 實際版本／路徑、已知可用的啟動方式 | 不猜版本，現有環境未被改壞 |
| S1 最小模擬 | 地板＋立方體，有限步進，讀姿態，輸出 PNG | 命令、exit code、軌跡、PNG、run manifest | 立方體落地，資料能讀回；離線 render 功能單獨通過 |
| S2 固定開口箱 | 依手冊公式建立底板＋四牆，中央 probe 放入 | 正常箱、封口箱、漏底箱的結果 | 正常通過，兩種故障正確失敗 |
| S3 參數化與靜態驗證 | JSON schema、尺寸／厚度、USD 讀回、10 組案例 | 輸入到輸出的 hash、尺寸與錯誤分類 | 非法規格先拒絕，輸出尺寸正確 |
| S4 物理與覆蓋 | 動態箱、質量與慣量、九點放入、側牆測試 | 數學對照、動態軌跡、沉降與碰撞檢查 | 不散架、不漏底、故障仍被抓到 |
| S5 AI 修復 | Agent 依報告修規格／生成器，最多三次 | before/after、patch、新測試結果 | 能修至少兩種故障，也能正確停止 |
| S6 批次與語意 | 自然語言→規格、批次 driver、多視角 VLM | 逐案輸入、模型／prompt 版本、成本與 verdict | 中斷可恢復，證據不足不當 pass |
| S7 可交接交付 | 正常與故障測試集、保留案例、新對話接手 | 最小重現命令、結果表、版本與限制 | 不靠原聊天也能重跑 |

第一輪 agent 只做 S0＋S1；不是做到 S0 就停著等你再確認，也不是自行一路擴充到 S7。若有限時間內 S1 沒通過，保存 blocked 原因和最小下一步。

### S0 的細節

1. 確認目前使用者、工作目錄、Git 狀態、新資料夾是否為空。
2. 只读查看啟動腳本、程序與版本檔，不印出整包環境變數或含密鑰的命令內容。
3. 辨識現有安裝方式：standalone、pip/conda、container 或其他已設置 launcher；使用真正成功的路徑。
4. 建立最小 `doctor`，輸出環境健康 JSON。未測項標 unknown／not_tested，不猜 pass。
5. 建立 STATE、ROADMAP、ENVIRONMENT 與 S1 卡片。

只知道 WebRTC 可用，尚不表示有 headless 權限或可用第二個 GPU。啟動新程序前確認 GPU／VRAM 與現有 session；不要任意終止使用者或他人的程序。

### S1 的細節

目標：單一立方體在重力下掉到平面，模擬在有限步數內結束；每步記錄 position、orientation、linear/angular velocity 和 simulation time。

執行模式依實際環境選擇：优先使用同版官方 standalone 例子適配為有限步腳本；如果只能透過目前可用的互動 session 執行，就保留這個限制並另列批次能力待辦。不能用 GUI 執行成功宣稱 headless 通過。

圖像要來自實際場景，寫出 PNG 和 camera pose。WebRTC 可觀看是額外人工證據；agent 沒有取得影像時不能說「我看過畫面」。黑圖／空圖是 render 失敗，與物理成功分開記錄。

工具具體 API 以當前安裝版為準。詳細手冊提到的 Isaac Lab AppLauncher 只適用於採用 Isaac Lab 的情境；這份新方案若用 Isaac Sim standalone，就依其同版 SimulationApp 初始化順序，不混接兩套 launcher。

### S2 的細節

先固定形狀與大小，不先接 LLM 生成。採手冊第 7 節的 30×20×15 cm 外尺寸、5 mm 壁厚；箱子外底放在地面上方 20 cm；4 cm 測試立方體由上方落入。

正常箱要落到箱內底；封口故障停在箱口；漏底故障落到下面世界地板。以箱體 local 座標讀出差異，避免把地板承托誤判成箱底有效。這一關是第一個真正對研究任務有意義的 demo。

### S3–S7 的實作細節去哪裡找

不是讓你另找論文，直接交由 agent 依詳細手冊指定章節執行：

| 新階段 | 詳細手冊章節 |
| --- | --- |
| S3 | 第 6、7、10 節：工具契約、schema、USD 靜態檢查 |
| S4 | 第 8–10、19 節：慣量公式、接觸設定、動態驗證、數學答案 |
| S5 | 第 11 節：JSON findings、修正範圍與停止條件 |
| S6 | 第 10 節 G6、第 16 節：視覺複核、成本與批次 |
| S7 | 第 12 節 M9、第 13–15 節：交接、評估與排错 |

## 6. 驗收與跨週記錄不能省略

每次工作都分清楚：`已實作`、`已實際驗證`、`未驗證`、`blocked`。只建立程式檔不算完成，沒有命令與證據的 pass 不接受。

最小 run 內容：manifest.json、environment.json、command/exit code、trajectory.csv、validation.json、summary.md；涉及圖像時再加 renders/。manifest 綁定 code commit 或 dirty diff、asset hash、case、seed、profile 和 backend。

STATE 每次只維持最新摘要，寫入「下一個唯一動作」。歷史放 sessions，重大選擇放 DECISIONS。新對話先讀檔案，不一開始重新研究整個專案。

當週只有一點時間時，至少完成：重跑上一個相關基準、執行一個小改動、記錄結果、寫下一步。中斷要保留已完成部分，不強迫每週換階段。

## 7. 可以直接貼給 agent 的第一次完整指令

把兩份檔案放好，將下方整段貼給 coding agent。你知道的路徑可補上，不知道的保留「請只讀查找」。

```text
請開始建立我的 Isaac Sim 資產生成與自動驗證專案。

【目前狀態】
Isaac Sim 已經安裝、可以啟動，而且我可以透過 WebRTC 觀看。
除了這個已可用的環境，其餘專案請從零開始建立。
不要沿用舊 Task 1 程式，不要刪除或覆蓋舊專案，也不要重新安裝、
升級或隨意更改目前能正常運作的 Isaac Sim、driver 或相關環境。
不要假設 Isaac Lab、MCP、Blender、Pydantic 或其他依賴已經安裝。

【請先讀兩份規格】
1. IsaacSim_From_Zero_Start_Here.md
2. IsaacSim_Asset_Workflow_Handbook.md
本次以第一份的從零建構條件與 S0–S7 排程為準。
第二份提供幾何、物理、驗證、證據和交接的詳細規格。
文件中的自訂 CLI 是要實作的介面，不能假設已经存在。

【環境資訊】
專案目錄：目前工作目錄；如果不是空白專案，請選擇新目錄並說明。
Isaac Sim 安裝位置：請先只讀查找。
目前可用的啟動命令／WebRTC 啟動腳本：請先只讀查找；若有無法由環境
判定的關鍵資訊，先完成能做的盤點，再集中問我一次。

【第一輪範圍：完成 S0＋S1】
1. 確認工作目錄、Git 狀態、安裝方式、實際版本、GPU 和已在執行的程序。
   不印出密鑰或整包環境變數，不停止他人的程序。
2. 建立一個全新、獨立的資產工作流 repo；不要修改 Isaac Sim 核心。
3. 建立 README.md、AGENTS.md、CLAUDE.md、docs/STATE.md、docs/ROADMAP.md、
   docs/ENVIRONMENT.md、docs/DECISIONS.md、docs/tasks/ 和 docs/sessions/。
   將「每次開工讀交接、每次收工寫證據與下一步」寫進入口指引。
4. 建立最小 runtime adapter 和 doctor，使用目前已安裝版的官方範例／API。
   優先只依賴 Python 標準庫和既有 Isaac runtime。
5. 建立地板＋立方體的有限步數 smoke：模擬掉落，記錄每步位姿、速度與時間，
   輸出一張實際場景 PNG，保存命令、exit code、日誌與 run manifest。
6. 分開報告物理執行、資料讀回、headless、圖像輸出、WebRTC 人工觀看的狀態。
   沒有測到的項目不能填 pass；看不到圖片不能說你已看過。
7. 在不干擾現有 WebRTC session 的前提下驗證；若缺 GPU 資源，保存 blocked
   原因，不任意 kill 程序或重設共用環境。
8. 完成 S0＋S1 後停止擴充，更新所有交接檔案，建立 S2 的具體任務卡。

【驗收與工作規則】
- 自主完成已授權且可逆的專案工作，不要每建一個檔案就停下詢問。
- 不要加入本階段不需要的服務、資料庫、MCP、ROS 或訓練流程。
- 不要把修復驗證器、放寬門檻、關閉碰撞當作資產修復。
- 每個完成宣稱都要有實際執行命令、結果與證據路徑。
- 若無法跑模擬，先保存完整可交接狀態；清楚寫明缺什麼，不偽造結果。
- 不自動公開、推送 repo 或傳送訊息给別人。
- 初始盤點後給簡短實作計畫，接著直接執行 S0＋S1，不只停在提案。

【回報格式】
請以繁體中文說明：
1. 本次實際完成什麼。
2. 如何驗證，證據在哪裡。
3. 未完成或受阻的部分。
4. 下次開新對話的唯一下一步。
5. 用新手能懂的方式解釋一個概念，給我一個只改一個參數的小練習。
```

## 8. 第二次以後只貼這一段

```text
請依本專案 AGENTS.md 恢復工作。
讀 docs/STATE.md、docs/ROADMAP.md、docs/ENVIRONMENT.md、目前階段任務卡與最新 session。
這個專案從零建立，使用現有 Isaac Sim 環境；不要重裝，也不要回頭混入舊 Task 1。
先確認目前 code 與驗證證據是否一致，重跑相關最小基準。
用五點簡述目前狀態後，直接執行當前任務卡的下一個小步驟。
本次完成一張有明確驗收的小任務；結束時更新檔案並留下唯一下一步。
```

## 9. 你要親自確認的最少事情

第一輪收工只需問五件事：

1. 原來的 Isaac Sim／WebRTC 是否仍能正常使用？
2. 新專案目錄到底在哪？
3. 能否用已記錄的一條命令重現立方體掉落？
4. PNG、軌跡與結果報告是否真的存在，並屬於同一次 run？
5. STATE 裡是否清楚寫著下一步 S2，或 S1 的具體阻塞？

你不用第一天理解所有 USD API。先理解「資產檔案描述物件」「模擬程式讓它運動」「驗證報告用數值判斷結果」三件事。到了 S2 再學 collider 與 visual 的差別；S4 再學質心與慣量。

## 10. 參考依據與本文件限制

本文件主要是針對最新起點調整的工程計畫；研究與物理參考詳見配套手冊。相關官方入口：

- [Isaac Sim 6.0 安裝與執行環境概覽](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/installation/index.html)：實際操作仍須按已安裝版本適配。
- [Isaac Sim 物理基础](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/physics/simulation_fundamentals.html)：碰撞與物理設定概念。
- [Isaac Sim 資產驗證](https://docs.isaacsim.omniverse.nvidia.com/6.0.0/robot_setup/asset_validation.html)：適用規則的官方入口。
- [Codex AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md) 與 [Claude Code 記憶文件](https://code.claude.com/docs/en/memory)：專案指引機制。

本次沒有操作遠端伺服器，沒有新建 runtime 或執行 smoke。本文件與配套手冊是交给該機器 coding agent 的可執行工作規格；真正的驗證結果由 S0＋S1 開始產生。
