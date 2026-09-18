# upstream_wiring_audit — pinned external/usd-content-agents 唯讀接線審查

角色：子任務審查 AI（session `parcel-forge-d7`，非主 AI）。範圍：唯讀分析
`external/usd-content-agents`（pinned checkout），不修改主線、不啟動 GPU/影片/模型、
不安裝套件、不登入。

## 基準與工作區狀態

- parcel-forge 基準 commit：`f4e5586c4a42e75aee146c5729f68718f4ba58ae`（`git rev-parse HEAD`）。
- parcel-forge 工作區：`git status --short` 回報 206 筆既有變更（大量 `M` 與 `??`，
  含 `docs/STATE.md`、`docs/ROADMAP.md`、`contracts/`、多個 `docs/sessions/*`、
  `docs/tasks/S4.md`／`S5.md` 等）。**本次審查未 reset/clean/stash，未新增或修改
  這 206 筆中的任何一筆**，只新增本檔案於 `reports/development/handoffs/`。
- pinned upstream checkout：`external/usd-content-agents`，`git rev-parse HEAD`
  回報 `a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa`，與 `config/upstream_content_agents.json`
  的 `"commit"` 欄位一致；`git status --short` 回報 0 筆變更（乾淨，未被本次或先前
  任何工作修改）。審查結束時再次確認：commit 與乾淨狀態不變。

## 任務範圍與讀取／修改的檔案

**唯讀讀取（parcel-forge 側，確認既有本地接線現況）：**
- `AGENTS.md`、`docs/STATE.md`、`docs/ROADMAP.md`、`docs/ENVIRONMENT.md`
- `docs/tasks/S5D_bounded_upstream_repair.md`、`docs/UPSTREAM_ADOPTION_PLAN.md`
- 最新 `docs/sessions/20260917T020054Z.md`
- `docs/REPAIR_CONTRACT.md`
- `config/upstream_content_agents.json`、`config/upstream_requirements.freeze.txt`
- `scripts/pf`（CLI 分派表）
- `src/parcel_forge/upstream_bridge.py`（全檔）
- `src/parcel_forge/focused_validation_host.py`（全檔）
- `src/parcel_forge/repair_guard.py`、`src/parcel_forge/actor_boundary_check.py`
  （僅確認是否引用 upstream，未逐行審查其修復邏輯——那是
  `repair_boundary_audit.md` 已完成的範圍，本次不重複）
- `src/parcel_forge/validation/official_usd.py`（比對 issue 欄位形狀，見下）

**唯讀讀取（`external/usd-content-agents` pinned 原始碼，本次審查主體）：**
- `agentic/.agents/skills/content-workflow-cli/SKILL.md`（全檔）
- `agentic/.agents/skills/content-workflow-geometry-repair/SKILL.md`（前半段，
  Capability Map／Limitations／Prerequisites／Workflow 步驟 1–11）
- `agentic/.agents/skills/content-workflow-physics/SKILL.md`（Runtime Preflight／
  Workflow 步驟 1–14）
- `agentic/packages/content_workflow_cli/content_workflow_cli/cli.py`
  （5781 行；只讀取 `add_parser(` 呼叫點與其上下文，未逐函式審查實作）
- `agentic/packages/content_workflow_cli/content_workflow_cli/entrypoint.py`（全檔，47 行）
- `agentic/packages/content_workflow_cli/content_workflow_cli/asset_runner.py`（360–399 行）
- `agentic/packages/content_workflow_cli/content_workflow_cli/geometry_runner.py`（105–118 行）
- `agentic/packages/content_workflow_cli/content_workflow_cli/child_launch.py`（結構掃描，
  45–686 行的 class/def 列表）
- `agentic/packages/content_workflow_cli/content_workflow_cli/runner.py`
  （9555–9935 行：`_find_claude_cli_binary`、`_build_claude_cli_sandbox_settings`；
  以及全檔 `shutil.which`／`RUNNER_CODEX`／`RUNNER_CLAUDE` 出現位置的 grep 掃描）
- `agentic/packages/content_agent_workflows/content_agent_workflows/common/run_record.py`（全檔）
- `agentic/packages/content_agent_workflows/content_agent_workflows/validation/workflow.py`
  （檔頭註解、85–135 行 import 與常數）
- `agentic/packages/content_agent_workflows/content_agent_workflows/validation/models.py`
  （59–260 行 class 列表）
- `agentic/packages/content_agent_workflows/content_agent_workflows/validation/checkpoint.py`
  （27–68 行 class 列表）
- `world_understanding/validation/models.py`（1–260 行，`ValidationRequest` 全定義）
- `world_understanding/validation/templates.py`（全檔，173 行）
- `world_understanding/functions/physics/physics_sane_adapter.py`（1–90 行）
- `world_understanding/functions/physics/physics_sanity.py`（605–655 行，
  `_add_asset_validator_findings`）
- `world_understanding/functions/physics/physical_behavior_evidence.py`（結構掃描，
  1–60 行的 class/def 列表）
- `apps/validation_agent/README.md`（前 150 行）
- `apps/validation_agent/pyproject.toml`（前 50 行）

**執行（僅唯讀指令，未呼叫任何 `main()`、未新增任何 `runs/` 目錄、
未執行 `content-workflow-cli`／`validation-agent`／`claude`／`codex` 本體）：**
見文末「執行命令、exit code、證據路徑」表。

**未讀取／未修改**：`profiles/`、`tests/`、其他子任務的審查範圍
（`repair_boundary_audit.md`、`background_video_hardening.md` 已涵蓋的邏輯不重複）、
`docs/DECISIONS.md`、`docs/STATE.md`、`docs/ROADMAP.md`（依協作限制第 4 點，
本次不寫入這些檔案）。

---

## 結論（含來源檔案／函式／行號）

### 1（最重要，直接回答「是否有任意自訂修復工具入口」）：**沒有。V1 驗證模板是硬編碼四項的允許清單，沒有任何註冊／外掛機制。**

- `world_understanding/validation/templates.py:12-17`：

  ```python
  V1_TEMPLATE_NAMES = (
      "look_right",
      "render_valid",
      "physics_sane",
      "physical_behavior",
  )
  ```

- `ValidationTemplateRegistry.register()`（同檔 126-137 行）：任何 `definition.name`
  不在 `V1_TEMPLATE_NAMES` 內，直接 `raise ValidationContractError`。
  `validate_template_names()`（159-169 行）對 `requested_templates` 做同樣的
  硬性拒絕。
- `ValidationRequest.requested_templates`（`world_understanding/validation/models.py:194`）
  在 pydantic 層級只是 `tuple[str, ...]`，沒有 `Literal` 限制字面值——但實際
  分派前一定會經過上述 registry 的 allowlist 檢查，所以在 pydantic 層看似
  「可以塞任何字串」不代表真的能執行。
- 全文檢索 `agentic/docs`、`content-workflow-validation` skill、
  `apps/validation_agent/README.md` 的 "custom check"／"extension point"／
  "register.*template"／"plugin.*template"／"third.?party.*check"：**零筆命中**
  （`grep -rniE` 已執行，見執行命令表）。
- 結論：ITRI 想要的「place_object_inside 九點／四牆容納測試」或「repair_proposal
  審核」都**不可能**被註冊成這個 pinned 0.6.0 版本裡的第五個驗證模板。這不是
  「尚未接線」，是「這個介面在這個版本裡本來就不存在」——本審查明確陳述，不假設。

### 2：「修復」在上游是兩個各自封閉、只作用在**既有 USD 資產**上的專用工作流，不是通用工具入口

- `content-workflow-geometry-repair`（`agentic/.agents/skills/content-workflow-geometry-repair/SKILL.md`）：
  範圍是「imported CAD, mesh, USD, URDF, or MJCF」的**拓樸**修復（collision
  separation、correspondence、typed workers）。Prerequisites 一節明文：
  > "Geometry Repair may select only a driver admitted by checked-in `sdf_tools`
  > policy and separately behaviorally qualified by checked-in Geometry Repair
  > policy; **agent input cannot install or register an implementation**."
  這句話直接排除了「把 parcel-forge 的 spec-patch 邏輯註冊成一個 worker」的可能性。
- `content-workflow-physics`（`agentic/.agents/skills/content-workflow-physics/SKILL.md`
  步驟 8-12）：物理修復的形式是 agent 產出
  `raw/physics_decision_patch.json`（只能用 `collider_target_ids`，
  "never retype USD prim paths"），由**受信任的 wrapper**解析成實際操作。
  這是對「密度／摩擦／碰撞近似」的修復，不是對「JSON spec 的
  `wall_thickness_m`／`fault`」的修復——upstream 從一開始就假設輸入是
  一個已存在的 USD／CAD 來源，不建模「由參數化 spec 產生 USD」這一層，
  而這正是 `parcel_forge.repair_guard` 運作的層級。兩者操作的物件不同，
  不是同一件事的兩種實作。
- 因此：`src/parcel_forge/repair_guard.py`（已由 `repair_boundary_audit.md` 詳細
  審查其內部邏輯，本次不重複）**架構上就沒有一個對應的上游插槽可以接**。
  這與 `docs/UPSTREAM_ADOPTION_PLAN.md` 的 S5-D 段落本身的陳述一致：
  「官方若無可擴充 check hook，將 ITRI gate 作為外部必要 gate 並列」——
  本審查現在把這句話從「保守假設」變成「已用原始碼確認的事實」。

### 3：`request/state/decision/checkpoint/resume` 的實際契約——存在且相當完整，但只在 **agentic validate prepare/check/finalize** 這條路徑上，且從未在本專案被真正中斷測試過

- 通用 run manifest：`agentic/packages/content_agent_workflows/content_agent_workflows/common/run_record.py`：
  - `WorkflowArtifactRecord`（31-38 行）、`WorkflowCheckpointRecord`（42-49 行，
    含 `phase`、`artifact_sha256`、`sealed: bool`）、`WorkflowRunManifest`
    （53-70 行，pydantic `ConfigDict(extra="forbid")`，
    `schema_version: Literal["content-agent-workflows.run-manifest.v1"]`，
    `status: Literal["running","pass","fail","blocked"]`，`request_sha256`，
    `source_sha256`，`checkpoints: list[WorkflowCheckpointRecord]`）。
  - `extra="forbid"` 表示**不能**把任意額外欄位（例如 parcel-forge 的
    `case_id`／`profile_sha256`）直接塞進這個 pydantic model；要傳遞 ITRI
    專屬中繼資料，只能走下面第 4 點提到的 `policy`／`metadata` 自由欄位。
- 驗證工作流專用的更細緻模型：
  `agentic/packages/content_agent_workflows/content_agent_workflows/validation/models.py`：
  `ValidationWorkItemState`（59 行）、`ValidationWorkflowStatus`（68 行）、
  `ValidationArtifactIdentity`（79 行）、`ValidationWorkflowIdentity`（105 行）、
  `ValidationAcceptedTemplateResult`（171 行）、`ValidationWorkItemRecord`
  （190 行）、`ValidationWorkflowCheckpoint`（223 行）、`ValidationWorkflowRun`
  （260 行）。
- Checkpoint store 抽象：`agentic/packages/content_agent_workflows/content_agent_workflows/validation/checkpoint.py`：
  `ValidationCheckpointError(RuntimeError)`（27 行）、
  `ValidationCheckpointStore(Protocol)`（40 行）、
  `FileValidationCheckpointStore`（68 行，實際檔案型實作）。
- `workflow.py` 檔頭註解（17-30 行）精確描述 resume 語意：
  > "a checkpoint holds... has since gone missing or stale is reopened on
  > resume, along with everything evidence, and summary while excluding
  > concurrent checkpoint mutation... implies a complete bundle at the
  > checkpoint revision it names."
  且有明確的鎖／claim 機制防止兩個 runner 同時跑同一個 check
  （`content-workflow-cli/SKILL.md`：「If the previous run was interrupted
  mid-check, its claim is still live and resume refuses to run beside it」，
  需要顯式 `--recover-orphaned-claims` 才能釋放）。
- **但**：本地 `focused_validation_host.py`（parcel-forge 側，第 47 行附近）
  已經自己記錄
  `'checkpoint_resume':'not_tested'`——這與本次審查的結論一致：上游
  checkpoint/resume 的**原始碼確實存在且結構完整**，但 parcel-forge
  端**從未真的中斷過一次 `check` 再呼叫 `content-workflow-cli validate
  resume` 去驗證它**。這是「存在但未操作驗證」，不是「不存在」。

### 4：`ValidationRequest` 的 `policy`／`metadata` 是唯一真正「自由」的欄位，可作為 ITRI 中繼資料的合法載體

- `world_understanding/validation/models.py:182-217`（`class ValidationRequest`）：
  `policy: dict[str, Any] = Field(default_factory=dict)`、
  `metadata: dict[str, Any] = Field(default_factory=dict)`，兩者都經過
  `_normalize_json_mapping`（214-217 行）正規化，接受任意 JSON 物件，
  沒有欄位白名單。
- 這與 `requested_templates` 的硬編碼 allowlist（發現 1）不同：`policy`／
  `metadata` 是設計上就開放的自由欄位，可以合法夾帶 parcel-forge 的
  `case_id`、`profile_sha256`、`run_id` 等，讓上游的 `validation_result.json`
  在事後可以被人工或程式追溯回哪一個 parcel-forge run，而不需要修改上游
  pydantic model。這是本次審查找到的**唯一乾淨、不需改動 upstream 原始碼**
  的中繼資料傳遞管道。

### 5：`physics_sane` 已經支援外部 USD-validator 報告注入，欄位形狀與 `official_usd.py` 幾乎一致——這是目前唯一可低成本銜接的檢查層

- `world_understanding/functions/physics/physics_sane_adapter.py:30-38`
  （`run_physics_sane_adapter` 簽名）：接受
  `asset_validator_report: Mapping[str, Any] | None = None`，文件字串
  （50-51 行）：「Optional USD validation report to pass through to the
  underlying inspector.」
- 實際消費邏輯在 `world_understanding/functions/physics/physics_sanity.py:613-646`
  （`_add_asset_validator_findings`）：讀取
  `asset_validator_report.get("issues", [])`，每個 issue 期望的欄位是
  `severity`、`at`、`message`、`rule`、`category`（optional）、`suggestion`
  （optional）（631-646 行）。
- 對照 parcel-forge 自己的 `src/parcel_forge/validation/official_usd.py`
  （`_issue_dict` 函式，本次僅讀取確認）：輸出的 issue dict 欄位正是
  `severity`、`rule`、`message`、`at`、`suggestion`——**與上游期望的形狀
  幾乎一對一吻合**（差別只在上游多接受一個 optional 的 `category`，
  parcel-forge 目前沒有這個欄位，但因為是 `.get("category")` 取用，
  沒有這個欄位時上游會安靜地留空，不會出錯）。
- **已發現但尚未接線的介面落差**：上游只在
  `asset_validator_report.get("status") == "error"`（`physics_sanity.py:620`）
  時才特別產生一筆 `physics.asset_validator_unavailable` 的 warn finding；
  parcel-forge 的 `official_usd.py` 頂層 `status` 用的是小寫的
  `"pass"`／`"fail"`／`"blocked"`（三態），沒有 `"error"` 這個字面值。
  也就是說：若 parcel-forge 官方驗證器本身載入失敗（我們自己定義的
  `"blocked"` 狀態），直接把整包 dict 傳給上游的 `asset_validator_report`，
  上游會因為字串不等於 `"error"` 而**安靜地跳過**這個警示分支，
  只剩下空的 `issues: []` 被逐一 iterate（結果是零筆 finding，而非
  預期的一筆 warn）。這是一個具體、可重現的欄位語意落差，需要一個
  1-2 行的本地轉換（把 `blocked` 映成 `error`）才能讓上游的既有邏輯
  正確反應「驗證器不可用」這件事，而不是新建一個上游沒有的機制。

### 6：`content-workflow-cli` 的子命令清單是完整枚舉出來的，沒有 `repair`／`tool`／`plugin` 這類通用動詞

- `agentic/packages/content_workflow_cli/content_workflow_cli/cli.py` 內
  `subparsers.add_parser(` 直接呼叫共 49 處，加上委派給
  `add_asset_subcommands`（`asset_runner.py:360`）與
  `add_geometry_subcommands`（`geometry_runner.py:105`）。完整頂層動詞：
  `convert-to-usd`、`preflight`（子動詞：`convert-to-usd`／`simready`／
  `physics-runtime`／`articulation-platform`／`claude-sandbox`）、
  `simready`（`validate`／`conform`／`runtime-validate`）、
  `auth`（`login`／`status`，Codex 專用）、`materials`（`assign`）、
  `articulation`（`run`／`review`／`revision`／`resume`／`agent-prepare`／
  `agent-apply`／`agent-finalize`）、`physics`（`apply`／`refine-external`）、
  `mesh-segmentation`（`run`）、`validate`（`run`／`resume`／`prepare`／
  `check`／`finalize`／`ingest-verified`／`produce-visual`／
  `collect-evidence`／`assess`／`review-assessment`）、`scene`
  （`run`／`resume`／`phase`(動態子名)／`collect`）、`artifact`
  （`write-json`）、`trace`（`build`）、`geometry`（`run`）、`asset`
  （`catalog`／`run`／`review`／`resume`）。
- **沒有**任何一個頂層或次層動詞叫做 `repair`、`tool`、`plugin`、`hook`、
  `extend`、`custom-check` 或語意相近的字串（已對 `cli.py` 全檔的
  `add_parser(` 呼叫點逐筆核對上述清單，見執行命令表的 grep 記錄）。
- 對本地 `upstream-check`（`upstream_bridge.py`）與 `repair-proposal`
  （`repair_guard.py`）而言，這代表：**沒有一個「幫我把 repair-proposal
  包成上游可以呼叫的東西」的現成入口**；唯一能接的是既有的
  `validate run`／`validate prepare|check|finalize`／`validate resume`
  這條驗證鏈（見發現 3、5），而不是任何修復鏈。

### 7：需要真正啟動子代理（child coding agent）的路徑，與 parcel-forge 目前實際使用的 `physics_sane` 路徑是分開的兩件事

- `agentic/.agents/skills/content-workflow-cli/SKILL.md`（"Wrapper
  Responsibilities" 一節）：
  > "launch Codex or Claude Code for standalone skill-routed Texture and
  > Articulation workflows, while embedded composed execution launches no
  > nested child."
- Claude Code 子行程實際落地在
  `agentic/packages/content_workflow_cli/content_workflow_cli/runner.py`：
  - `_find_claude_cli_binary()`（9572 行起）：
    `shutil.which("claude")`（or 環境變數覆寫），找不到就丟出
    「The 'claude' CLI was not found on PATH. Install Claude Code and run
    `claude auth login` once...」；找到後立刻執行
    `subprocess.run([resolved, "auth", "status", "--json"], ...)`
    （9579-9587 行）驗證登入狀態。
  - `_build_claude_cli_sandbox_settings()`（9911-9922 行）：
    `node_executable = shutil.which("node")`；找不到就
    `raise RuntimeError("Node.js is required for the child execution
    policy hook.")`（9921 行）。這個函式建置的是 Claude CLI 沙盒工具政策
    （執行 `codex_sdk_bridge.mjs` 作為 policy hook），只在真的要啟動一次
    Claude Code child turn 時才會被呼叫到。
  - Codex 對應的認證入口是 `cli.py` 的 `auth`（265 行）／`auth login`
    （267 行）／`auth status`（278 行）子命令，明文標註
    「Codex authentication utilities.」。
- **關鍵區分**：parcel-forge 現有的 `focused_validation_host.py` 呼叫的
  是 `content-workflow-cli validate prepare/check/finalize --template
  physics_sane`，且它自己在
  `operation['nested_agent_launched']` 上斷言必須為 `False`（否則
  `raise ValueError('unexpected nested agent')`）——也就是說，
  **`physics_sane` 這個模板目前的執行路徑本身就不需要、也被本地程式
  主動驗證過「沒有」啟動 Claude Code／Codex 子代理**。Node/npm 缺失
  因此**不會**阻擋現在 S5-B/S5-D 已經在用的 `physics_sane` 路徑；
  它只會阻擋 materials／texture／articulation／VLM 版
  `validate`（`look_right`）這些**目前 parcel-forge 完全沒有使用**的路徑。
  這一點過去的 session 紀錄（`docs/STATE.md`「node/npm absent from PATH」）
  沒有明確區分「這件事影響哪一條路徑」，本次審查把它精確化。

---

## 最小依賴清單：已量測 vs 未知（本次唯讀，未安裝、未登入、未呼叫模型）

| 項目 | 狀態 | 量測方式／來源 |
| --- | --- | --- |
| `node`／`npm`／`npx` 是否在 PATH | **已量測：不存在** | 本次互動式 Bash session 執行 `command -v node npm npx`，三者皆無輸出（NOT FOUND） |
| `claude` CLI 二進位是否存在 | **已量測：存在** | `command -v claude` → `/mnt/HDD4/wyattsheu/.local/bin/claude` |
| `codex` CLI 二進位是否存在 | **已量測：存在** | `command -v codex` → `/mnt/HDD4/wyattsheu/.local/bin/codex` |
| `claude`／`codex` 的 OAuth／登入 session 狀態 | **未知（刻意未測）** | 需要執行 `claude auth status`／`codex auth status`；本子任務授權範圍明文禁止登入相關操作，即使查詢狀態本身不算登入，仍選擇不執行以維持嚴格唯讀邊界 |
| 上述 PATH 量測是否等同 parcel-forge 子行程實際看到的 PATH | **未知** | `upstream_bridge.py`／`focused_validation_host.py` 用 `env=dict(os.environ, ...)` 幾乎原樣繼承呼叫者環境（只剔除 `*_API_KEY`／`*_TOKEN`／`*_SECRET` 字尾的變數，見 `upstream_bridge.py` 對應行），但本次量測是在目前這個互動式 session 的 PATH 下做的，未在「主 AI 實際啟動 `pf upstream-check` 的那個 process 環境」下重新量測，兩者可能不同，不可假設一致 |
| `physics_sane`／`physical_behavior` 是否需要 Node／child runner／OVRTX | **已量測：不需要** | `apps/validation_agent/README.md`（Runtime Dependencies 一節）明文：「`physics_sane` and `physical_behavior` can run from local evidence without a VLM」；且本地 `focused_validation_host.py` 已用 `nested_agent_launched` 斷言驗證過實際執行時沒有子代理被啟動（見發現 7） |
| `look_right`／`render_valid`／materials／texture／articulation 是否需要 Node／child runner／OVRTX | **已量測（讀原始碼）：需要，视路徑而定** | `render_valid`／`look_right` 需要 `--render-backend`（`remote`／`ovrtx`）與／或 VLM key；materials／texture／articulation 的 standalone skill-routed 路徑需要 Codex 或 Claude Code 子代理（見發現 7），Claude 路徑額外需要 `node`（`runner.py:9920`） |
| `.venvs/usd-content-agents` 目前已安裝套件是否等於 `physics_sane` 嚴格最小需求 | **已量測：不是，範圍更廣** | `config/upstream_requirements.freeze.txt` 內含 `langchain-anthropic`、`boto3`、`google-genai`、`anthropic` SDK 等一整套 agentic 套件；但 `apps/validation_agent/pyproject.toml`（12-15 行）本身宣告的直接依賴只有 `python-dotenv`、`rich`、`typer`、`world-understanding>=0.5.0`。目前環境是「已裝好、比嚴格最小需求大」，本審查只記錄此事實，**不建議重建環境**（超出本子任務授權，且會影響既有已驗證的 S5-A/B/C 證據） |
| `physics apply`（`content-workflow-cli preflight physics-runtime`）的隔離 OvPhysX runtime 需求 | **未量測（超出本次範圍）** | 該 preflight 指令文件明文「missing reviewed dependencies are installed from the architecture-specific lock **by default**」——本身帶有預設安裝行為，執行它有違反「不安裝套件」授權的風險，本次刻意不執行；且 parcel-forge 目前用的是 `physics_sane`（不需要這個 runtime），與 `physics apply`（agent 驅動的物理屬性授權）是不同路徑 |

---

## 提出最小整合方案（不另建 scheduler／runner）

1. **維持現狀分工，不嘗試把 repair 塞進上游**：`repair_guard.py`
   繼續在 parcel-forge 這一側對**修復前的 JSON spec** 做欄位級白名單修補
   （這是 `repair_boundary_audit.md` 已審查的既有邏輯）；`upstream_bridge.py`
   與 `focused_validation_host.py` 繼續在修復**後**對重新產生的 `asset.usda`
   做獨立、外部的驗證閘門。這正是發現 1、2、6 共同指向的結論——上游沒有
   給第三方修復邏輯任何註冊點，勉強接線只會製造一個上游不認得、
   將來升版就會斷掉的隱藏耦合。
2. **把 `official_usd.py` 的 41 條 NVIDIA 規則報告接進 `physics_sane`**
   （發現 5）：在呼叫 `validation-agent validate --template physics_sane`
   之前（或改用 `content-workflow-cli validate prepare` 搭配可傳入
   `asset_validator_report` 的呼叫方式，需先確認 CLI 層是否曝露這個參數—
   —本次只確認了 Python 函式層接受它，**CLI 參數層是否有對應旗標尚未
   核對，是明確的下一步，不可假設存在**），把 `official_usd.py` 的
   `status` 欄位在 `blocked` 時轉成上游期待的 `"error"` 字面值，
   讓既有的 `physics.asset_validator_unavailable` warn 邏輯正確觸發。
   這是一個小型轉接函式，不是新的 runner。
3. **用 `policy`／`metadata` 自由欄位（發現 4）夾帶 parcel-forge 的
   run 識別碼**：呼叫 `validate run`／`prepare` 時，在
   `ValidationRequest.metadata` 內放入 `{"parcel_forge_run_id": ...,
   "parcel_forge_profile_sha256": ...}`，讓上游產出的
   `validation_result.json` 事後可追溯回哪一個 parcel-forge run，
   不需要修改上游任何 pydantic model 或 registry。
4. **checkpoint/resume 需要的不是新程式碼，是一次真正的中斷測試**
   （發現 3）：用既有的 `focused_validation_host.py` 呼叫序列
   （`prepare`／`check`／`finalize`），在 `check` 執行到一半時中斷
   （例如逾時或 SIGTERM），再呼叫既有的
   `content-workflow-cli validate resume --output-dir <同一個目錄>`
   （必要時加 `--recover-orphaned-claims`），把
   `focused_validation_host.py` 裡目前寫死的
   `'checkpoint_resume':'not_tested'` 換成一次真正量測到的結果。
   這是執行既有命令，不是建立新工具。
5. **明確不做的事**：不新增任何自訂 scheduler、不新增任何「通用外掛」
   CLI 動詞去模擬上游沒有的 registry、不嘗試把 `repair_guard` 包裝成
   `geometry-repair` 或 `physics apply` 的 worker（發現 2 已證明這條路
   在這個 pinned 版本裡走不通）。

---

## 未測試項目與阻礙

- **CLI 層是否真的曝露 `asset_validator_report` 參數給 `validate run`／
  `prepare`**：本次只確認了 Python 函式
  `run_physics_sane_adapter(..., asset_validator_report=...)` 接受這個
  參數，**沒有**確認 `content-workflow-cli validate run/prepare` 的
  argparse 層是否有對應的 `--asset-validator-report <path>` 之類旗標，
  或是否只能透過更底層的 Python API 呼叫才能傳入。這是明確的下一步，
  不可假設 CLI 已曝露它。
- **`content-workflow-cli validate resume` 與其 claim/lock 機制從未在
  本專案被實際觸發過**：本次只讀了原始碼與 skill 文件裡描述的語意
  （發現 3），沒有執行一次真正的中斷＋resume。這是 S5-D 任務卡本身
  已列出的缺口，本審查沒有新增進展，只是把「原始碼裡的契約長怎樣」
  釐清到有檔案／行號可查。
- **`claude`／`codex` 的登入狀態**：本子任務授權明文禁止登入相關操作，
  維持 `unknown`，不得推論為「已登入」或「未登入」。
- **`physics apply` 所需的隔離 OvPhysX runtime**（`preflight
  physics-runtime`）完全未量測：該指令本身預設會安裝缺少的依賴，
  執行它有違反本子任務「不安裝套件」授權的風險，故刻意不執行。
  parcel-forge 目前使用的 `physics_sane` 路徑不需要這個 runtime，
  兩者不要混為一談。
- **`physical_behavior` 模板的 `trajectory_metrics`／`simulation_json`
  證據種類自動判別，是否真的認得 parcel-forge 的
  `trajectory.csv`／`s2_result.json` 檔案形狀**：本次只讀了
  `_infer_json_evidence_kind` 一類函式的簽名與行號列表
  （`physical_behavior_evidence.py`），**沒有**逐行核對其判別邏輯是否
  接受這兩個既有檔案的實際 schema。這是留給下一階段的具體、有邊界的
  待驗證項目，不是本審查的結論。
- **本次沒有執行、也不在授權範圍內**：GPU、渲染、影片、任何模型呼叫、
  任何登入流程、任何 `runs/` 新目錄的產生（本審查全程零寫入 `runs/`）。

---

## 執行命令、exit code、證據路徑

本次審查全程只執行唯讀指令（`cat`／`sed -n`／`grep`／`ls`／`find`／
`git rev-parse`／`git status`／`git log`／`command -v`），**沒有呼叫任何
`main()` 或建立任何新的 `runs/` 目錄**。以下列出本次審查中具代表性、
決定結論的指令；未逐一列出的 `cat`／`sed -n` 讀檔動作皆為 exit 0
的成功讀取，來源檔案已在「任務範圍與讀取／修改的檔案」一節列出。

| 命令 | exit code | 用途／證據 |
| --- | --- | --- |
| `git -C external/usd-content-agents rev-parse HEAD` | 0 | 確認 pinned commit = `a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa`，與 `config/upstream_content_agents.json` 一致 |
| `git -C external/usd-content-agents status --short`（審查前後各一次） | 0（兩次皆無輸出） | 確認 upstream checkout 全程乾淨，未被本次或先前任何工作修改 |
| `git rev-parse HEAD`（parcel-forge） | 0 | 記錄基準 commit `f4e5586c...` |
| `git status --short`（parcel-forge） | 0 | 206 筆既有變更快照，本次未新增/移除任何一筆 |
| `grep -n "add_parser(" .../cli.py \| wc -l` | 0 | 確認共 49 處直接 `add_parser` 呼叫 |
| `grep -n "def add_asset_subcommands\|add_parser(" .../asset_runner.py` | 0 | 確認 `asset` 動詞的 `catalog/run/review/resume` 四個子命令 |
| `grep -n "def add_geometry_subcommands\|add_parser(" .../geometry_runner.py` | 0 | 確認 `geometry run` 為唯一子命令 |
| `grep -rn "class ValidationRequest" --include="*.py" .` | 0 | 定位 `world_understanding/validation/models.py:182` |
| `grep -n "^def \|^class \|...|allowlist" .../templates.py` | 0 | 定位 `V1_TEMPLATE_NAMES`、`ValidationTemplateRegistry.register/validate_template_names` 行號 |
| `grep -n "asset_validator_report" .../physics_sanity.py` | 0 | 定位 613/615/617/620/626/631 行的實際消費邏輯 |
| `grep -n "\"codex\"\|'codex'\|\"claude\"\|'claude'\|which(\|npx\|npm\|node " .../runner.py` | 0 | 定位 `RUNNER_CODEX`/`RUNNER_CLAUDE` 常數與 `shutil.which("node")`（9920 行）等呼叫點 |
| `sed -n '9555,9600p' / '9905,9935p' .../runner.py` | 0 | 取得 `_find_claude_cli_binary`／`_build_claude_cli_sandbox_settings` 完整上下文與精確錯誤訊息文字 |
| `grep -rniE "custom.?check\|extension point\|register.*template\|plugin.*template\|third.?party.*check" agentic/docs ...` | 0（無命中） | 確認全文檢索找不到任何自訂檢查／外掛註冊機制的文件描述 |
| `grep -rln "usd-content-agents\|content_workflow_cli\|content-workflow-cli\|external/" src/parcel_forge/repair_guard.py src/parcel_forge/actor_boundary_check.py src/parcel_forge/focused_validation_host.py` | 0 | 確認 `repair_guard.py`／`actor_boundary_check.py` 對 upstream 零引用，只有 `focused_validation_host.py` 引用 |
| `command -v node npm npx claude codex uv python3` | 0（各別檢查） | node/npm/npx 無輸出（不存在）；claude/codex/uv/python3 各回報一個絕對路徑（存在） |
| `ls reports/development/handoffs` | 0 | 確認既有 `repair_boundary_audit.md`、`background_video_hardening.md`，作為本檔案格式參照 |

本審查產出的唯一新檔案：`reports/development/handoffs/upstream_wiring_audit.md`
（本檔）。未修改 `docs/STATE.md`／`docs/ROADMAP.md`／`docs/DECISIONS.md`／
任何 `profiles/`／`tests/`／既有 `runs/` 證據。

---

## 主 AI 下一步如何接入

1. **先確認 CLI 層是否曝露 `asset_validator_report`**（本審查未測項目
   第一條）：讀 `content_workflow_cli/validation_runner.py` 與
   `cli.py` 裡 `validate_prepare`／`validate_run` 對應的 argparse 選項，
   確認有沒有 `--asset-validator-report`／`--extra-evidence` 之類旗標，
   或是否只能繞過 CLI 直接呼叫 `run_physics_sane_adapter` Python API。
   這決定「發現 5／整合方案第 2 點」是走 CLI 旗標還是走 Python 呼叫。
2. **在 `official_usd.py` 或其呼叫端加一個 1-2 行的狀態轉接**：
   把 `status == "blocked"` 映射成上游期待的 `"error"` 字面值，
   再實際跑一次 `upstream_bridge.py`／`focused_validation_host.py`，
   確認上游確實吐出 `physics.asset_validator_unavailable` 這筆 warn
   finding（目前只是原始碼比對，尚未實測這條路徑）。
3. **執行一次真正的 checkpoint/resume 測試**（整合方案第 4 點）：
   對某個既有 `physics_sane` `official/` 輸出目錄的 `check` 階段
   人為中斷，重跑 `content-workflow-cli validate resume
   --output-dir <同目錄>`，把結果寫進新的 `runs/<run-id>/`，並把
   `focused_validation_host.py` 裡的 `'checkpoint_resume':'not_tested'`
   換成有 exit code／證據路徑佐證的真實值。
4. **不要嘗試**把 `repair_guard.py` 接進 `geometry run --repair-mode`
   或 `physics apply` 的決策補丁機制——本審查已用原始碼（發現 2）
   確認這兩條路徑分別要求「拓樸修復 worker 需被 checked-in policy
   允許」與「物理屬性補丁只認 collider_target_ids」，都不是 parcel-forge
   repair 運作的層級（參數化 spec 而非既有 USD 資產屬性）。若未來真的
   需要更深的整合，第一步應該是重新確認上游是否在未來版本開放了
   `register()`／plugin 機制，而不是在目前 pinned 的 0.6.0 上硬接。
5. **量測 `physical_behavior` 對既有 trajectory 檔案的相容性**
   （本審查未測項目最後一條）作為獨立、有界的下一個子任務——這需要
   讀 `physical_behavior_evidence.py` 的 `_infer_json_evidence_kind`
   完整實作（本次只讀了行號列表），不建議與本次的 `physics_sane`
   接線工作混在同一個 commit 或同一個 run 裡。

本報告本身未修改任何主線檔案、未變更 `docs/STATE.md`／`docs/ROADMAP.md`／
`docs/DECISIONS.md`，僅新增本檔案於 `reports/development/handoffs/`。
