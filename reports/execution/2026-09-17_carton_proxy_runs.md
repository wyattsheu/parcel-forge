# 紙箱工作流實際執行紀錄

此文件紀錄每次真實執行，不是軟體建置進度。各run不可覆寫。

| 案例 | run | steps×4 / rows | raw exit / host exit | 個別診斷 | 原mixed gate |
| --- | --- | --- | --- | --- | --- |
| opening (.005Nm friction) | `20260917T114330Z_ext1_carton` | 4800×4 / 19200 | 0 / 1 | pass | fail |
| coupon (.005Nm friction) | `20260917T114240Z_ext1_carton` | 4800×4 / 19200 | 0 / 1 | pass | fail |
| cyclic (.005Nm friction) | `20260917T114414Z_ext1_carton` | 7200×4 / 28800 | 0 / 1 | pass | fail |

## 執行內部步驟

最新開箱案 [progress.jsonl](../../runs/20260917T114330Z_ext1_carton/progress.jsonl)：runtime_requested → asset_generated → physics_readback_ready → physics_running每3秒 → finished。
progress中的finished只是執行結束；各驗收狀態必須分別讀取，不把fail改pass。

每案 asset.usda/config/prompt/request/source hashes/launch/runtime.log/trajectory.csv/link_poses.csv/scene_final.usda/recording.usda/results分開保留。

| 證據類型 | 狀態 |
| --- | --- |
| standalone headless PhysX、tensor readback | verified |
| CSV到USD measured replay export＋reopen | verified；component error0 |
| 相機render、MP4 | not_tested／not_requested |
| 人類WebRTC觀看 | not_tested |
| 真實紙板／IsaacLab integration | not_tested |

## 循環模型量測

高載荷次蓋每次開啟末端降伏力矩N·m：`[0.0265769250980553, 0.024364463198682167, 0.02147245798161202, 0.018382552066810193]`。只證明程式內部模型，並非真實纖維疲勞。

官方41規則與負例：`20260917T114413Z_ext1_usd_check`；測試程式與命令見 [建置報告](../development/2026-09-17_carton_proxy_milestone.md)。

所有發射前保存GPU0 free VRAM inventory；未停止他人程序，未變更Isaac/driver/venv，未啟用livestream。
