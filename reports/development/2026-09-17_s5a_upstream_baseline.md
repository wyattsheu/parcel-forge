# 工作流建置回報：S5-A 原廠驗證基準已跑通

日期：2026-09-17。狀態：done (verified)。

## 本階段完成

- 下載 NVIDIA USD Content Agents 0.6.0，固定完整 commit `a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa`，detached HEAD；原碼未修改。
- 工具裝在 `.venvs/usd-content-agents`，原 Isaac runtime 不變。
- 原廠 steel-scaffold behavior-evidence 範例：官方 verdict=pass、CLI exit=0。
- 缺少必要 behavior summary 的負例：官方 verdict=fail、exit=1，issue=`physics.behavior_evidence_missing`。
- `uv pip check` 通過，版本清單保存 `config/upstream_requirements.freeze.txt` 與本 run 的 freeze.log。
- 本 session 的 Isaac smoke --physics-only 通過：runs/20260917T010648Z_s1_smoke/，render=not_tested。

本階段驗證的是「官方驗證工具可以執行並正確拒絕缺資料」。官方範例讀上游附帶的
refine_summary.json，沒有在本機重新跑鷹架模擬，也沒有呼叫 VLM／GPU renderer。
這不是已完成 ITRI 箱體整合。上游範例的 judge score=0.91 是 fixture，並非本次模型或物理量測。

## 來源

[官方 fixed-pipeline skill](../../external/usd-content-agents/.agents/skills/fixed-pipeline/SKILL.md)
與 validation-agent-cli/reference.md 指導本次命令與輸出檢查。
[固定版本 Validation Agent](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa/apps/validation_agent/README.md)
是實際接口依據；上游程式、LICENSE、NOTICE 與 pyproject 摘存於 run/source。

獨立環境、正常／缺資料負例與公司分階段報告是本專案整合設計。
本階段使用的是完整 Validation Agent，不再把 omni.asset_validator 的 41 rules 稱為此 Agent。

## 自行重新執行

以下每次產生新目錄並保留 CLI 輸出：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
pf_upstream_run="$PWD/runs/$(date -u +%Y%m%dT%H%M%SZ)_s5a_user_check"
mkdir -p "$pf_upstream_run/logs"
.venvs/usd-content-agents/bin/validation-agent run \
  external/usd-content-agents/apps/validation_agent/examples/configs/steel_scaffold_behavior_refine_summary.yaml \
  --output-dir "$pf_upstream_run/official_example" --format json \
  > "$pf_upstream_run/logs/validation.log" 2>&1
pf_upstream_exit=$?
printf 'CLI exit: %s\n' "$pf_upstream_exit"
cat "$pf_upstream_run/official_example/validation_result.json"
```

成功條件：exit 0，result.verdict=pass、physical_behavior status=passed；不是 planned／warn。
若要看缺資料負例（會預期 exit 1）：

```bash
.venvs/usd-content-agents/bin/validation-agent run \
  runs/20260917T010638Z_s5a_upstream_setup/missing_evidence.yaml \
  --output-dir "$pf_upstream_run/missing_evidence" --fail-on-warn --format json \
  > "$pf_upstream_run/logs/missing_evidence.log" 2>&1
pf_upstream_exit=$?
printf 'CLI exit (expected 1): %s\n' "$pf_upstream_exit"
cat "$pf_upstream_run/missing_evidence/validation_result.json"
```

先執行上方初始化目錄的區塊，再跑負例。負例 fail 是正確拒絕，不是執行成功案例。

## 證據與下一步

本階段原始結果：`runs/20260917T010638Z_s5a_upstream_setup/official_example/validation_result.json`。
負例：`runs/20260917T010638Z_s5a_upstream_setup/missing_evidence_result/validation_result.json`。

WebRTC／影片：本階段沒有新模擬場景，均 not_tested／not_produced。
下一個小階段 S5-B 才接正常箱與缺底。接著 S5-C 保存實際軌跡、PNG 序列與 MP4，
讓你直接點影片看當次測試，不是另外重跑的動作。
