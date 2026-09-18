# repair_boundary_audit — S5-D 修復邊界唯讀審查

角色：子任務審查 AI（非主 AI）。範圍：唯讀審查，不修改主線、不啟動 GPU/模型。

## 基準與工作區狀態

- 基準 commit：`f4e5586c4a42e75aee146c5729f68718f4ba58ae`（HEAD，`git rev-parse HEAD`）。
- 工作區有大量既有未提交修改（`git status --porcelain`，本次開始前快照）：
  多個 `M`（含 `docs/STATE.md`、`docs/ROADMAP.md`、`profiles/open_box_v1.json` 等）
  與大量 `??` 新檔（`contracts/`、`docs/tasks/S5*`、`runs/*`、`docs/sessions/*` 等）。
  本次審查**未 reset/clean/stash，未新增/修改任何工作區檔案**，僅執行讀取與純函式呼叫。

## 任務範圍：讀取／執行的檔案

唯讀讀取：
- `src/parcel_forge/repair_guard.py`
- `src/parcel_forge/upstream_bridge.py`
- `src/parcel_forge/evidence.py`、`src/parcel_forge/schema.py`（追蹤依賴，僅讀）
- `contracts/repair_proposal_v1.schema.json`
- `contracts/repair_proposals/{remove_lid,restore_bottom,reject_probe_change}.json`
- `tests/test_repair_guard.py`
- `docs/REPAIR_CONTRACT.md`、`docs/tasks/S5.md`、`docs/tasks/S5D_bounded_upstream_repair.md`、
  `docs/UPSTREAM_ADOPTION_PLAN.md`、`docs/DECISIONS.md`（D012 一節）、`docs/STATE.md`、
  `docs/ROADMAP.md`、`docs/ENVIRONMENT.md`、最新 `docs/sessions/20260917T020054Z.md`
- `runs/20260917T015901Z_s5d_progress/repair_suite.json`（既有證據，唯讀）
- `config/upstream_requirements.freeze.txt`（確認上游隔離環境依賴清單）

執行（僅純函式呼叫與唯讀指令，未新增任何 `runs/` 目錄，未呼叫 CLI `main()`，未涉及 GPU/模型/影片）：
- `python3 -c "...apply_proposal(...)"`（記憶體內呼叫，無副作用）
- `PYTHONPATH=src python3 -m unittest tests.test_repair_guard -v`
- `grep`/`find` 靜態搜尋，確認 `repair_guard.py` 與 `upstream_bridge.py` 之間無互相 import，
  確認 `contracts/repair_proposal_v1.schema.json` 未被任何 `.py` 引用，
  確認 `jsonschema` 套件不在專案主環境而是在上游隔離環境凍結清單內。

未修改：`profiles/`、`tests/`、`src/parcel_forge/validation/`、任何驗收門檻、任何 `runs/` 原始證據。

## 結論（含來源檔案／函式／行號）

### 1（最高風險）：文件化的提案契約與實際強制邏輯是兩套不相容格式，且文件化契約允許修改 probe/geometry 保護欄位

- `contracts/repair_proposal_v1.schema.json:66-76` 的 `patch[].path` enum 允許
  `/probe/size_m`、`/probe/drop_xy_m`、`/probe/drop_offset_above_opening_m`、
  `/geometry/outer_size_m`、`/geometry/wall_thickness_m`、`/geometry/lid`，
  且每次最多 3 個 replace 操作（`patch` `minItems:1,maxItems:3`，行 51-53）。
- 但實際強制邏輯 `src/parcel_forge/repair_guard.py:apply_proposal()`（行 10-34）
  只接受完全不同的資料形狀（`{"schema","changes":[{"path","from","to"}]}`），
  且硬編碼只允許 **恰好一個** 變更、**只允許** `path=='/geometry/fault'`
  且 `to=='none'`（行 16、21、26）。兩者共用同一個 `schema` 常數字串
  `"parcel_forge.repair_proposal/1"`（schema.json 行 19 vs repair_guard.py 行 18），
  但欄位結構互斥——符合其中一套的文件絕不會符合另一套。
- `docs/REPAIR_CONTRACT.md:6` 明文指示「An actor submits
  contracts/repair_proposal_v1.schema.json」，這是唯一被文件指名的契約檔，
  但它從未被任何程式碼載入或驗證（`grep -rn "repair_proposal_v1\|jsonschema" src/` 無結果）。
- 風險已具備可利用的環境條件：`config/upstream_requirements.freeze.txt:53-54`
  顯示官方上游隔離環境（`.venvs/usd-content-agents`）已凍結安裝
  `jsonschema==4.26.0`。若日後接線官方 coding-agent 工作流時，
  依 `docs/REPAIR_CONTRACT.md` 的字面指示直接用 `jsonschema` 驗證
  `contracts/repair_proposal_v1.schema.json`（而非改路由到
  `repair_guard.apply_proposal`），會讓 actor 可以合法縮小 probe
  尺寸（`/probe/size_m`）——這正是 `docs/tasks/S5D_bounded_upstream_repair.md:11`
  明文禁止的「不能縮小 probe 或改 expected_outcome 作弊」。
- 具體重現失敗情境：一個符合 `repair_proposal_v1.schema.json` 的合法文件
  （`schema`, `source_run`, `source_spec_sha256`, `attempt`, `finding_ids`,
  `rationale`, `target:"candidate_spec"`, `patch:[{"op":"replace",
  "path":"/probe/size_m","value":0.01}]`）在 schema 驗證下會通過，
  但若之後直接把驗證通過的 patch 套用到候選 spec 上（略過
  `repair_guard.apply_proposal` 的硬編碼白名單），probe 就被實際縮小。

### 2：`contracts/repair_proposals/reject_probe_change.json` 是未被任何程式碼或測試消費的孤兒 fixture

- `grep -rln "reject_probe_change" tests/ src/ scripts/` 無結果（已執行，見上）。
- `tests/test_repair_guard.py:test_protected_fields_rejected`（行 18-21）改用另一種方式
  （複製 `remove_lid.json` 後動態替換 `path` 欄位）涵蓋等價語意，但從未讀取
  `reject_probe_change.json` 本體。
- 且該檔案本身用的是 `repair_guard.py` 的 `{"changes":[...]}` 形狀（不是
  `repair_proposal_v1.schema.json` 的 `{"patch":[...]}` 形狀），所以就算真的接上
  `jsonschema`，這個「應該被拒絕」的範例檔本身也不會通過 schema 驗證的必要欄位檢查
  （缺 `source_run`、`source_spec_sha256`、`attempt` 等），無法作為該 schema 的迴歸測試。
- 影響：這個 fixture 的存在製造「已有反例測試」的錯覺，但它既不在自動化測試路徑上，
  也不是任何一套實際契約的合法反例，未來允許清單一旦改動，不會有任何 CI 檔案偵測到迴歸。

### 3：`repair_guard.py` 完全沒有 `attempt` 次數／來源綁定的強制，只有內容層允許清單

- `src/parcel_forge/repair_guard.py` 全檔（37-58 行 `main()`）沒有任何欄位、
  變數或狀態記錄「這是第幾次嘗試」，也沒有讀取或比對
  `source_run`／`source_spec_sha256`（這兩個欄位只存在於未被使用的
  `contracts/repair_proposal_v1.schema.json` 中）。
- `docs/tasks/S5D_bounded_upstream_repair.md:9-10`：「max three attempts」、
  `docs/tasks/S5.md`（Binding design rules 第 6 點）：「At most three attempts,
  with the stopping reason recorded」——這些是專案明文的硬性上限，但目前程式碼層
  沒有任何機制可以偵測或拒絕第 4 次以上的提案；次數限制目前只存在於人工紀錄
  （`runs/20260917T015901Z_s5d_progress/repair_suite.json` 是人工彙整的
  before/after 對照，不是由程式強制產生或驗證的次數計數器）。
- `main()`（行 39-40）的 `--case`／`--proposal` 是任意檔案系統路徑，
  沒有任何白名單限制它們必須落在 `cases/` 或
  `contracts/repair_proposals/` 目錄下，也沒有 symlink／路徑穿越檢查。
  由於程式只讀取這兩個路徑並把 bytes 複製進**新建**的 run 目錄
  （`Path(make_run_dir(...))`，`evidence.make_run_dir` 用
  `os.makedirs(..., exist_ok=False)`，見 `evidence.py:67-71`），
  它不能覆寫既有檔案，但可以把任意可讀檔案（例如 `profiles/open_box_v1.json`
  或倉庫外的檔案）的內容複製進 run 目錄再嘗試解析——目前僅因為輸出面沒有
  「寫到任意路徑」的參數，才沒有造成寫入風險；這是**因缺少功能而安全**，
  不是**明確設計的邊界**，若未來有人加上 `--out` 這類參數，目前程式不會阻止它
  寫到 `profiles/`、`src/parcel_forge/validation/` 或 `tests/`。

### 4：原始證據與候選（修復後）證據之間的綁定，目前完全靠人工紀錄，程式碼沒有強制鏈路

- `upstream_bridge.py:evaluate()`（行 23-72）對**單一 run 目錄**做強綁定：
  六個檔案（`FILES`，行 17-18）逐一 sha256 比對 `manifest.json` 記錄的雜湊
  （行 26-28），再交叉核對 `manifest['inputs_sha256']`／`profile_sha256`／
  `asset_sha256`（行 33-37），最後重算物理結果與 `result['summary']
  ['observed_outcome']` 比對（行 66-67）。這一段對**單一 run 內部一致性**
  的把關是紮實的。
- 但 `repair_guard.py` 與 `upstream_bridge.py` 之間**沒有任何 import 或共用資料結構**
  （已用 `grep -n "^import\|^from"` 確認兩檔互不引用）。也就是說：
  - `repair_guard.py` 產生的 `candidate.json` 不含任何指向「這是從哪個原始 run
    修復而來」的雜湊或 run-id 欄位（`apply_proposal` 回傳值只是候選 spec 本身，
    `main()` 的 `result` 只記錄 `input_sha256`／`candidate_sha256`，
    行 49、53，沒有 `source_run` 欄位）。
  - 「修復前」與「修復後」兩個 run 之間的對應關係，目前只存在於
    `runs/20260917T015901Z_s5d_progress/repair_suite.json` 這份**人工彙整**檔的
    `"before"`／`"after"`／`"proposal"` 三個字串欄位——沒有任何雜湊把
    `before` run 的 asset/spec 雜湊、`proposal` run 的 `candidate_sha256`、
    和 `after` run 的 spec 雜湊串起來做交叉驗證。若有人（或未來自動化流程）
    手誤填錯 run-id 對照，目前沒有任何程式碼會偵測出來。
- 結論：「提案內容限制」與「證據綁定」是兩件事，本審查確認**內容限制**
  （單欄位、單一目標值、來源故障值比對，見發現 1 之外的其餘檢查）在
  `apply_proposal` 內是可信的；但**跨 run 的證據鏈**目前是人工敘事，不是程式保證。

### 5：實際強制的允許清單邏輯本身（不含上述文件不一致問題）已被正確測試並可重現通過

- `apply_proposal()` 的 7 道檢查（`repair_guard.py:12-33`）：
  來源 spec 需合法（12-13）、任務需為 `place_object_inside`（14-15）、
  提案只能有 `schema`/`changes` 兩鍵（16-17）、`schema` 常數需相符（18-19）、
  `changes` 必須恰好一筆（20-22）、變更只能有 `path`/`from`/`to` 三鍵（23-25）、
  目標必須是 `/geometry/fault`→`'none'`（26-27）、來源故障必須屬於
  `('sealed_lid','missing_bottom')`（28-29）、`from` 必須等於來源當前故障值
  （30-31，防 stale proposal）、候選 spec 修復後仍須通過 `validate_case`
  （32-33）。
- 已執行 `PYTHONPATH=src python3 -m unittest tests.test_repair_guard -v`：
  4 個測試全數 `ok`，總計 `Ran 4 tests in 0.001s`，exit 0
  （見下方「執行命令與 exit code」）。
- 額外以純函式呼叫方式（無副作用）驗證：對 `open_box_sealed.json` 套用
  `remove_lid.json` 可正確修復（`geometry.fault` 由 `sealed_lid` 變為
  `none`，其餘欄位含 `expected_outcome` 完全不變）；套用
  `reject_probe_change.json`（`/probe/size_m` 0.04→0.01）被正確拒絕，
  錯誤訊息 `"change outside repair allowlist"`。

## 提案內容限制 vs actor 檔案存取隔離：差異總結

- **內容限制**（欄位/數值層級）：強，且由 `apply_proposal` 的白名單邏輯獨力承擔，
  與 `contracts/` 下的 JSON Schema 檔案無關（該檔目前是死檔，見發現 1）。
- **檔案存取隔離**（路徑/程序層級）：弱。`main()` 對 `--case`／`--proposal`
  沒有目錄白名單、沒有路徑正規化後的前綴檢查、沒有唯讀掛載或子行程沙盒。
  目前之所以「安全」，純粹因為程式沒有任何寫入任意路徑的功能，
  而不是因為有主動阻擋。這與 `docs/tasks/S5D_bounded_upstream_repair.md:13`
  提到尚待解決的「actor filesystem boundary」是同一件事，本審查確認
  **目前完全不存在**，不是「部分存在待加強」。

## 防止 actor 直接修改 validator／profile 的現況

- 現有防護＝「沒有任何函式的輸出路徑指向 `profiles/`、
  `src/parcel_forge/validation/` 或 `tests/`」，屬於程式**未提供該能力**，
  而非**主動拒絕該能力**。沒有集中式的路徑允許清單函式可供未來新程式碼複用；
  若日後 S5-D 接上官方 coding-agent 工作流並新增檔案輸出參數，
  現有程式碼不會自動繼承這個保護。
- 建議最小修正（僅為建議，未實作）：在 `repair_guard.py` 新增一個顯式的
  `ALLOWED_WRITE_ROOTS = {REPO_ROOT/"runs"}` 之類的守門函式，
  未來任何新輸出路徑參數都必須先過這個函式，而不是依賴「目前沒有這個參數」
  這種隱性假設。

## 未測試項目與阻礙

- `main()`（CLI 入口，含檔案複製與路徑處理）完全沒有單元測試覆蓋，
  `tests/test_repair_guard.py` 只測 `apply_proposal` 這個純函式。
- `contracts/repair_proposal_v1.schema.json` 從未被任何程式碼路徑執行過
  （既非正例也非反例測試），其正確性/安全性未經任何自動化驗證。
- attempt 計數上限（三次）、`source_run`／`source_spec_sha256` 綁定：
  程式碼層完全不存在，因此無從測試「超過三次會被拒絕」——這不是
  「未測試」而是「未實作」。
- 跨 run 的候選↔原始證據雜湊鏈：不存在對應機制，因此無法測試其正確性。
- 本審查未執行、未測試：官方 checkpoint/resume、官方 coding-agent 呼叫、
  GPU、渲染、模型、WebRTC——依子任務授權範圍不得測試，狀態維持
  `not_tested`（與 `docs/STATE.md`／`docs/sessions/20260917T020054Z.md`
  既有記錄一致，未新增矛盾聲稱）。

## 執行命令、exit code、證據路徑

| 命令 | exit code | 說明 |
| --- | --- | --- |
| `git rev-parse HEAD` | 0 | 基準 commit 確認 |
| `git status --porcelain=v1` | 0 | 工作區未提交修改快照（唯讀） |
| `PYTHONPATH=src python3 -m unittest tests.test_repair_guard -v` | 0 | 4/4 測試通過，`Ran 4 tests in 0.001s` |
| `python3 -c "...apply_proposal(open_box_sealed, remove_lid)..."` | 0（Python 無例外） | 純函式呼叫，回傳修復後 candidate dict，記憶體內、無檔案寫入 |
| `python3 -c "...apply_proposal(open_box_sealed, reject_probe_change)..."` | 0（正確拋出並捕捉 `ValueError`） | 印出 `rejected: change outside repair allowlist` |
| `grep -rn "jsonschema" ...` / `grep -rln "repair_proposal_v1" .` | 0 | 確認 schema 檔案孤兒狀態與上游環境依賴 |

本次審查**沒有產生任何新的 `runs/` 目錄**（未呼叫 `repair_guard.main()`／
`upstream_bridge.main()`，兩者的 CLI 都會建立新 run 目錄，超出「唯讀審查」
授權，因此刻意避免執行）。所有引用的既有證據路徑（`runs/20260917T015901Z_s5d_progress/`
等）為既有檔案，本次僅讀取。

## 主 AI 下一步如何接入

1. **先解決發現 1（最高優先）**：明確選定唯一一套提案格式。若要延用官方
   coding-agent 產生 JSON Schema 相容輸出，需要重寫
   `repair_guard.apply_proposal` 使其真正解析 `contracts/repair_proposal_v1.schema.json`
   定義的 `patch`/`op`/`path`/`value` 形狀，**同時把允許清單收斂到只剩
   `/geometry/fault`（或明確追加其他每一個要開放的欄位都需要新的
   D-decision 記錄）**；或者反過來，直接刪除／改寫
   `contracts/repair_proposal_v1.schema.json`，讓它精確描述
   `repair_guard.py` 現有的 `{"schema","changes":[{"path","from","to"}]}`
   形狀與單一 `/geometry/fault` 允許清單，避免兩份文件同名不同義。
   兩者選一，不要保留現狀（兩套並存、只有一套被強制）。
2. **發現 3／4 需要新欄位＋新程式碼**：在 `candidate.json`／
   `proposal_result.json` 中新增 `source_run`、`source_spec_sha256`、
   `attempt` 欄位並在 `apply_proposal`／`main()` 內驗證（次數上限、
   雜湊比對來源 run 的 spec），讓 `runs/*_s5d_progress/repair_suite.json`
   這類 before/after 對照未來能由程式重新驗證，而不是永遠停留在人工敘事。
3. **發現 3 的檔案存取隔離**：在 `main()` 對 `--case`／`--proposal`
   加上路徑必須落在 `cases/` 或指定 run 目錄下的顯式檢查，
   再串接官方 actor 的檔案系統邊界（`docs/tasks/S5D_bounded_upstream_repair.md`
   點名的「actor filesystem boundary」）。
4. **發現 2**：決定 `reject_probe_change.json` 的去留——若選擇路線 1
   中「收斂到只剩 `/geometry/fault`」，應把它改寫成
   `{"changes":[...]}` 形狀並在 `tests/test_repair_guard.py` 中實際載入該檔，
   讓它成為會被 CI 執行的迴歸測試，而不是文件夾裡的裝飾品。
5. 以上任一項改動後，重新執行
   `PYTHONPATH=src python3 -m unittest discover`（沿用既有 115 項測試基準，
   `runs/20260917T015637Z_s5d_guard_checks` 為對照），並依 AGENTS.md
   規則把新結果寫入新的 `runs/<run-id>/`，不得覆蓋既有證據。

本報告本身未修改任何主線檔案、未變更 `docs/STATE.md`／`docs/ROADMAP.md`／
`docs/DECISIONS.md`，僅新增本檔案於 `reports/development/handoffs/`。
