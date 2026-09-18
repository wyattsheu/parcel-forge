# 封口修復：第二條 v2 新執行鏈

本階段完成來源封口 → 受限提案 → 新候選 → 新物理 → 雜湊鏈 → 官方與 ITRI 驗收。
這是人工準備提案的控制器驗證；尚未完成真實模型提案工作流。整體仍約 70% 的階段估計。

| 小成功點 | 證據／結果 |
| --- | --- |
| 基礎 smoke | 20260917T064430Z_s1_smoke，exit 0 |
| 來源與提案綁定 | 20260917T064621Z_s5d_repair_proposal，attempt 1，exit 0 |
| 唯一修改 fault | sealed_lid → none；probe、task、expected_outcome 皆保留 |
| 新物理執行 | 20260917T064636Z_s2_open_box_sealed，runtime exit 0，900 筆軌跡，inside |
| 雜湊／原 profile | 20260917T064719Z_s5d_repair_link，exit 0 |
| 官方＋任務驗收 | 20260917T064723Z_s5d_focused_gate，physics_sane pass、ITRI pass，exit 0 |

原始故障回歸 expected_outcome=at_mouth 沒改，因此 pf box exit 2、regression fail
如實保留。它與新 task acceptance pass 是兩個不同判定。缺底與封口兩種原因現在
都已有 v2 新物理鏈。不是僅靠 matching 舊資料，亦不是模型 actor 已成功。

自行核對（不消耗提案 attempt、不啟動 GPU）：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf repair-link-check --proposal-run 20260917T064621Z_s5d_repair_proposal --validation-run 20260917T064636Z_s2_open_box_sealed
./scripts/pf upstream-focused-check --run 20260917T064636Z_s2_open_box_sealed
```

兩條預期 exit 0。不要重送 remove_lid.json 的 attempt=1；本 source 的第一個 slot 已使用。
完整重跑與中斷規則見 [REPAIR_RESTART_POLICY](../../docs/REPAIR_RESTART_POLICY.md)。

在目前既有 WebRTC Isaac 編輯器的 Script Editor，可執行以下指令載入本次實測終態：

```python
import omni.usd
omni.usd.get_context().open_stage("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T064636Z_s2_open_box_sealed/scene_final.usda")
```

開啟前先儲存目前編輯器中的工作。載入後保持 timeline 停止，於 Stage 選取
/World/Probe、按 F 定位，確認探針在箱內。這是人工終態檢查，沒有播放已測 trajectory；
本輪沒有接管 viewer 或占用直播 ports。WebRTC human view 仍 not_tested，需你自行確認。

例行物理 run 另產生兩張 PNG；只記錄程式統計檢查，不宣稱人工看過：
[俯視](../../runs/20260917T064636Z_s2_open_box_sealed/renders/open_box_sealed_interior_top.png) ·
[側視](../../runs/20260917T064636Z_s2_open_box_sealed/renders/open_box_sealed_side_low.png)。

若這個里程碑需要影片，可由你按需提交背景工作；本輪沒有生成新影片：

```bash
./scripts/pf-video-background --run 20260917T064636Z_s2_open_box_sealed
# 用輸出中的 job id 查看狀態
./scripts/pf-video-background --status JOB_ID
```

來源標記：官方 prepare/check/finalize 與 physics_sane 來自固定 NVIDIA
[usd-content-agents a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa)。
受限 JSON fault 修復、三次 receipt、內容雜湊链、900 筆 ITRI task gate 是本專案實作，
不是官方通用修復 hook。新中斷規則參考該版本 workflow.py 的 _selected_templates 與
本專案既有診斷（D046）；不支援 physics_sane resume 時重新驗證，不改上游。

本輪沒有修改 Python 執行邏輯，未重跑全套離線測試；前一輪 121 項、7 skipped 的
結果保留在 20260917T062951Z_s5d_resume_final_checks，本輪新增實測鏈與七項統整斷言。
下一個動作：建立不提供 shell／檔案寫入工具的 JSON-only 模型提案輸入與輸出契約，
保存精確 prompt/output，再經既有 gate；先量測可用模型入口，沒有入口就如實標 blocked。
