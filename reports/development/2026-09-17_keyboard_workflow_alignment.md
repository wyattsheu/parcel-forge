# README 鍵盤示例與本專案生成入口

使用者記得正確：固定版本 README 頂部展示 generated keyboard 用於 robot-learning polish training。
它是成果示意，沒有提供可重現鍵盤生成的完整 prompt、source、模型／provider 設定或 run 證據。
本地 connector 的 keyboard 單元測試是 contract 測試，不能拿來證明展示鍵盤就是由該 provider 生成。

來源：[NVIDIA README](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa/README.md)。

| 層級 | 官方實際入口／責任 | 我們目前狀態 |
| --- | --- | --- |
| 外層 coding agent | 理解自然語言並規劃工具操作 | 本次互動由現有 coding agent 協調；不另造 scheduler |
| 從文字建立新幾何 | 外部 geometry authoring provider 明確設定 | provider 未選定，未呼叫 |
| Geometry 交接 | geometry run 消費既有 source／typed manifest | 新增 pinned dry-run 腳本，實際 exit 0 |
| Asset 組合 | asset run 需要 source 或 usd；help 明示文字生成須先 geometry-agent | 不是單靠 prompt 生成鍵盤的命令 |
| 驗證與物理 | 官方工具與證據 gate | 箱子已有官方 focused＋獨立 ITRI PhysX task gate |
| 訓練 polish | README 示意的下游成果 | 目前專案不做訓練 |

本輪建置 scripts/pf-upstream-geometry-plan。它驗證 checkout pin/clean、快照六份
證據並校驗既有實測結果，再呼叫官方 geometry run --dry-run。
保留預設 render_evidence=true；沒有取消最終渲染要求。direct_preserve、repair off、
optimization skip 只用於這次既有 USD 交接規劃，不是新生成品質驗收。

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-upstream-geometry-plan --run 20260917T064636Z_s2_open_box_sealed
```

預期 plan_created、exit 0；新 run 中 official.log 是官方標準化 request，
plan_result.json 明確記 generation/physics/render/model=not_tested。
本輪最終實測 runs/20260917T073054Z_upstream_geometry_plan，前一版規劃 073010 也保留。
CLI help 證據：runs/20260917T073053Z_upstream_generation_reference。
這一步是規劃成功，不能宣告 NVIDIA geometry generation/render 成功，也不新增可看的場景。

生成需求已整理在 [box_generation_goal.txt](../../contracts/box_generation_goal.txt)。
我們應沿用外層 agent → configured authoring provider → typed source bundle →
官方 Geometry → 本地任務驗收的做法，用箱子替代鍵盤。
需要額外保留的 ITRI 條件是固定 probe/profile、實測 placement、來源雜湊與 fail 不可升 pass。
不應把目前 JSON fault 提案接線誤稱為完整文字生成幾何。

官方 connector 原始依據：
[geometry_authoring_connectors README](https://github.com/NVIDIA-Omniverse/usd-content-agents/blob/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa/agentic/packages/geometry_authoring_connectors/README.md)。
明確外部 worker 可以回傳 geometry.source.v1，render_geometry/collision_candidate
與 source/provider/units/hash。ForgeCadArtifactAdapter 只匯入已輸出的 artifact，不執行 ForgeCAD。
不能僅因 connector 有名字就當 provider 可用；本輪未建立服務、裝 CAD 套件或呼叫端點。

基礎 smoke：runs/20260917T072846Z_s1_smoke，exit 0。
未修改 Python 物理模組，未重跑已通過的 124 項離線測試；本輪實測的是官方 dry-run。
WebRTC 沿用你已回覆 OK 的 paused viewer；沒有新影片。
下一個動作：量測實際可用的 authoring provider，固定 provider 與輸出契約後，
把本需求送入生成流程；若仍無 endpoint，不能拿 deterministic box generator 冒充外部生成成功。
