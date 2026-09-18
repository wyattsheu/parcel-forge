# NVIDIA USD Content Agents 採用與後續實作計畫

日期：2026-09-17。狀態：S5-A 原廠基準已驗證；S5-B 箱體轉接尚未實作。
使用者同意改採官方工作流，本次要求是先整理更動後計畫。
這是既有 S5–S7 的修訂，不是另起一套 M0–M9 專案。

## 決策與分工

以固定版本的 NVIDIA USD Content Agents 作為通用工作流基礎。
保留 parcel-forge 作為 ITRI 規格、primitive 生成器、任務判定與 Isaac Sim 6.0.1 adapter。
S0–S4 既有結果保留為歷史基準；本次只整理計畫，未重跑，不能稱為新驗證。
停止擴寫獨立 repair_loop／workflow_state 框架。舊 repair proposal schema 保存作為
需求記錄，是否轉接以固定版本的官方介面為準，不要求官方配合我們的自訂格式。

| 部分 | 採用方式 |
| --- | --- |
| 上游 checkout、CLI、workflow state、決策／trace、resume | 優先直接使用官方原碼，固定完整 commit SHA |
| 通用 USD／physics sanity／behavior evidence validation | 使用官方 Validation Agent；41 generic rules 留作另一層覆蓋 |
| 五板件生成器、解析質量、COM、慣性、負例集 | 保留現有程式與測試 |
| inside／at_mouth／fell_through、九點、四牆、settling | 保留為 ITRI task checks，經薄 adapter 供官方流程使用 |
| 模擬執行 | 原 Isaac venv 子程序；官方工具放獨立環境 |
| 幾何／spec 修復 | 外部 actor JSON 提案＋本地限制；官方提供既有驗證與 checkpoint，無通用 spec-repair 插槽 |
| 數值參數調校 | 後續視需求接官方 BYOR；不把它當任意幾何 patch 引擎 |
| 公司回報 | reports/development 與 reports/execution Markdown，沿用現有資料夾 |

## 目標執行流程

使用者目標 → NVIDIA 工作流 → ITRI 規格／生成器 → 固定 Isaac runtime →
原始量測與錄製 USD → NVIDIA 通用驗證＋ITRI 任務判定 → 報告／受限修復。
官方結果、任務結果和人工作證各自保留，只有所有必需 gate 完成才能宣稱任務成功。
這是整合目標，並非目前已存在的可執行鏈。

## S5-A：固定官方版本，跑原廠最小範例（第一張任務卡）

1. 讀取上游 VERSION、release tag、pyproject、lock、CLI 與測試；選定完整 commit SHA。
   目前參考文件為 0.6 系列，但不得拿浮動 main 當可重現版本。
2. 建議 checkout 放 external/usd-content-agents，獨立 venv 放 .venvs/usd-content-agents。
   保存來源 URL、SHA、版本、授權／NOTICE、安裝命令與依賴鎖定資訊；上游修改另存 patch。
   先檢查 repo ignore 與容量，再建立環境；不得安裝到 IsaacLab/.venv 或更動 driver。
3. 只裝官方 Validation Agent 範例需要的依賴。先檢查固定版本 --help，再用官方
   steel_scaffold_behavior_refine_summary 範例，不啟動新 GPU runtime 或模型。
4. 保存官方原始 request／plan／result、stdout、stderr、exit code 到新 run。
5. 若依賴不合，記錄具體衝突；先隔離解決，不因為不相容又開始重寫官方 workflow。

通過條件：固定 SHA；獨立環境 CLI 可執行；官方範例結果與該版本預期吻合；缺失依賴
不被誤判成功。exit 0 不足以判成功，因為官方 planned／warn 也可能 exit 0。
公司小回報：「已能獨立執行 NVIDIA 原廠驗證範例」。WebRTC 不適用。

## S5-B：正常箱＋缺底故障，完成最小證據轉接

1. 第一輪重用兩個已保存 run，避免同時調整模擬與轉接：
   normal=20260917T000053Z_s2_open_box_normal；
   missing-bottom=20260917T000039Z_s2_open_box_no_bottom。
2. 檢查固定版本 ValidationRequest、physics_sane、physical_behavior 的實際 schema
   與支援的輸入種類。先跑官方工具讀我們的 USD，再接任務證據。
3. 編寫最小 adapter，引用原 run-id、case hash、profile hash、source code fingerprint、
   原始 JSON／CSV。官方若無可擴充 check hook，將 ITRI gate 作為外部必要 gate 並列，
   不偽造官方已支援的 artifact type 或改官方 validator 來放行。
4. 明確分開三種值：simulation_execution、task_acceptance、regression_expectation。
   normal：執行成功、inside 任務成功、回歸符合預期。
   missing-bottom：執行成功、inside 任務失敗、故障回歸符合預期。
   既有 s2_result.summary.verdict=pass 不能直接複製成 task_acceptance=pass。
5. 增加 missing evidence／改動 evidence hash 的負例。依據固定版本 gate 語意要求
   fail／blocked／insufficient，不接受資料不足的 pass。
6. 再跑一次新 normal 與 missing-bottom，確認轉接不依賴硬編碼舊 run。

通過條件：正常成功、缺底任務失敗、缺資料不成功；上游規則與 ITRI 規則各自可追溯。
若 USD physics_sane 對缺底給 pass 是合理的：有效 USD 不等於能裝東西。
公司小回報：「官方流程已能讀入本案，且沒有把故障測試 pass 誤當資產 pass」。
WebRTC：沿用既有正常／缺底最終場景與 33 點清單，人工填表。

## S5-C：錄下真正執行的軌跡，提供可重播畫面

1. 新 run 保存每個相關剛體的 position、orientation、simulation time、dt、seed。
   舊 CSV 若缺 orientation，不補猜測，重新執行取得完整量測。
2. 從該次量測建立 self-contained time-sampled USD；保留單位、物件識別、原始資產
   雜湊與記錄雜湊，核對開始／中間／結束樣本及整段時間軸。
3. 新增純錄製播放模式：以時間樣本播放，避免再啟動剛體計算覆寫動畫。
   現有 pf view 是即時模擬，不能直接宣稱具備此模式。
4. 先產生正常與缺底兩個錄製檔；各保存開始、接觸、結束畫面。
   優先使用固定版本官方 playback/render；WebRTC 視需要補薄播放 adapter。
5. Render 必須獨立成功才標記通過；物理成功但 render crash 的 run 仍保留分項結果。

通過條件：錄製姿態與原始量測在既定數值誤差內一致；觀看／後渲染不重新模擬。
公司小回報：「可看到該次實際成功與故障的完整運動」。WebRTC 人工確認另列。

## S5-D：官方 coding-agent 工作流調用本地驗收

1. 沿用官方 request／state／decision／resume 和工具入口；選最小需要的工作流。
   不另外建自己的 scheduler 或 runner。需要官方 child harness 時才加 Node／認證。
2. 工具只允許產生新候選 spec／asset 與新 run；門檻、profiles、tests、validator、
   原始證據禁止由修復 actor 修改。模型不能升級 deterministic fail。
3. 第一個修復使用可修正的 box spec 故障，例如非預期封口。
   固定 probe 尺寸／質量與實際任務要求，不能縮小 probe 或改 expected_outcome 作弊。
4. 每次保留實際 patch、套用結果、重跑結果；最多三次。不可修／缺量測／新退化要停止。
5. 驗收兩種不同根因的修復及一個正確拒絕案例；修改 allowlist 外欄位要被執行層拒絕。

通過條件：真實 before/after 與新驗證，拒絕例有效；重啟能從官方 checkpoint 恢復。
公司小回報：「官方 agent 調用了我們的工具並修好指定故障，沒有改驗收規則」。
WebRTC：看修復前後各自錄製，不拿重跑場景冒充同一次 evidence。

## S5-E：需要物理調參時才接 BYOR

BYOR 與 S5-D 不相等。它讓客戶 runtime 套用數值參數、回傳一個固定 scalar objective，
官方管理 qualification／optimization／refinement。先定義實際要匹配的目標和量測，
不能為了讓物件進箱便任意調質量／摩擦。沒有實測時，只能稱工程調參而非材料校準。

實作：依固定版本 request/result contract 封裝 Isaac 子程序；回傳 applied_params、
objective identity/unit/direction/value、diagnostics 與指定 artifacts；success 含義按
上游 contract，ITRI acceptance 保持獨立必需 gate，不能用高分抵消硬性失敗。
qualification 需要的 PNG 序列、動作、精確錄製及 digest 綁定先由 S5-C 提供。
官方流程若要求 exact qualification digest，先產生可檢查結果，再進入其核准步驟。
這是來源明定 gate，不另增加每個普通動作都要使用者核准的流程。

通過條件：單參數 nominal trial、參數實際讀回、固定 objective、artifact 完整性、
失敗候選不入選；之後才增加調參預算。此項尚未完成相容性測試。

## S6：擴大覆蓋與用途選擇

將最小流程擴至六個物理案例、七個非法 spec、九點與四牆；保留舊 oracle 不改門檻。
EXT2 的 intended_task 路由優先接官方 template/check 選擇，僅保留 ITRI task binding，
不要獨立再造通用 registry。未知任務必須明確拒絕或標示不支援。
再按實際需求加入第二資產族、批次、自然語言與視覺判斷。
通過條件：舊故障仍被抓到；每個被選／跳過 check 有理由；輸入與模型版本可追溯。

## S7：交接

提供固定上游 SHA＋本地 patch／adapter、環境建立記錄、一個正常及一個故障的單步操作、
實測命令、重播／WebRTC 指令、限制表與完整 reports。全新 shell 可重現；不能把
歷史證據路徑的檢查等同 cold-start 重現。

## 每個小階段都交付

- reports/development/<date>_<step>.md：增加了什麼、上游來源／本地改動、驗證命令與限制。
- reports/execution/<date>_<run>.md：該 run 執行到哪一步、原始 exit、分項結果、artifact。
- 有場景時附 WebRTC／錄製播放命令和預期畫面；無場景時直接說終端驗證。
- 指令須在該階段完成後實測再公布；目前不發明尚未存在的 pf upstream 子命令。

## 現在唯一下一步

S5-A 已通過。執行 S5-B：讀固定 SHA 的 behavior-evidence schema，
把正常箱與缺底案例轉接，保留 simulation、task acceptance、regression 三種判定。
後續 gate 為 S5-C–E；當前只啟用 S5-B 任務卡。

## 一手來源與界線

- [官方 README](https://github.com/NVIDIA-Omniverse/usd-content-agents)：reference implementation 與執行模式。
- [Validation Agent](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/apps/validation_agent/README.md)：template、request／plan／result、warn／planned exit 語意。
- [Agentic Workflow](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/agentic/README.md)：工作流入口與共用證據管理。
- [External Runtime](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/main/apps/physics_agent/docs/external_runtime_tuning.md)：BYOR、錄製與 qualification。

上述網址 main 是本次規劃參考，不是鎖定版本。S5-A 必須換成完整 SHA 的 permalink。
「正常／缺底雙案例」、修復欄位限制、ITRI task acceptance 與以上分階段安排為本專案設計。

## 執行更新與影片需求（2026-09-17）

S5-A 已完成，證據 runs/20260917T010638Z_s5a_upstream_setup/，詳見建置／執行報告。
當前下一張卡是 S5B_upstream_evidence.md；S5-A 初始計畫與執行證據均保留。

使用者新增：達到可展示階段後，測試過程應保存可直接點開的影片。
S5-C 在官方 exact-rollout USD＋PNG 序列之外，使用既有 ffmpeg 輸出 H.264 MP4。
保留原始 recording、frames、fps、sim-time 範圍、encoder 命令／版本、檔案 SHA256，
以 ffprobe 檢查 duration／frame count，並檢查非空白與動作統計；人眼判讀仍由使用者確認。
影片首頁／報告標明正常或故障、run-id、參數估計與播放速度。不得用生成影片或另一輪
模擬冒充量測。MP4 是公司檢視附件；官方 0.6 的相關調參接口仍使用其支援的 PNG
證據，不因為多了 MP4 就把未支援的 video 送進官方判斷接口。
若 render 失敗，保留 physics 結果並單列影片未產生；沒有影片不寫成已錄製。

## A/B/C 接線確認（D044/D045）

上游固定版本沒有任意 spec-repair 插槽或第五個 validation 模板；S5-D 的提案與 ITRI gate 維持外部，沿用官方 focused validation/checkpoint。原本「官方 coding-agent 直接修 spec」是待確認假設，不作為已提供的功能。完整 actor、真實提案、新 physics 執行與 interrupted resume 尚待完成。active 修復格式更新為 v2；參考 docs/REPAIR_CONTRACT.md 及 A/B/C 整合報告。
