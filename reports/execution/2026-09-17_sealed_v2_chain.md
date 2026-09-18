# 工作流執行紀錄：封口修復

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


[機器統整證據](../../runs/20260917T064758Z_s5d_sealed_completion/suite.json)。
影片未要求；WebRTC 人工觀看 not_tested；模型執行 not_tested。
