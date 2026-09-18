# 已接受提案的一鍵實際生成與驗證

本輪不是 dry-run。新增 pf repair-execute：對已接受 v2 提案重新產生箱子 USD、
跑完整 PhysX、核對 source→candidate→新實測鏈，再調用固定 NVIDIA focused
prepare/check/finalize。重用既有生成器與驗收，沒有新增服務或 scheduler。

| 小成功點 | 證據 |
| --- | --- |
| 提案快照、receipt／hash／允許修改核對 | 01_proposal_checked.json |
| 指定 GPU 資源檢查 | 02_gpu_inventory.json |
| 新 USD＋完整物理 | 03_physics_executed.json；runtime exit 0、pf exit 2 |
| 新實測修復鏈與 inside task | 04_link_checked.json，900 筆 CSV |
| NVIDIA＋ITRI 驗收 | 05_official_checked.json，官方與 task pass |
| 最終結果 | execution_result.json，pass、exit 0 |

上述檔案都在 runs/20260917T075134Z_s5d_repair_execution/。
新資產：[asset.usda](../../runs/20260917T075134Z_s2_open_box_sealed/asset.usda)。
新實測終態：[scene_final.usda](../../runs/20260917T075134Z_s2_open_box_sealed/scene_final.usda)。
官方 run：20260917T075202Z_s5d_focused_gate。

一條指令重新實際生成與驗證（需要 GPU；不再次消耗提案 receipt）：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf repair-execute --proposal-run 20260917T064621Z_s5d_repair_proposal
```

中斷後可重新跑此命令，但整個執行從 accepted candidate 開始，產生新的物理 run；
不是 checkpoint resume。程序不足資源寫 blocked.json，不停止別人的程序。
階段紀錄在每一步完成後寫入，可先查看 01～05 檔案得知進度；最終結果才是整鏈判定。
此命令不接受模型提供的 command，只接受本地 accepted proposal run id。
原 profile、probe、expected_outcome 不變：pf box exit 2 原因是原預期 at_mouth，
實測 inside；只在後續實測 task 與官方驗收皆成功時整鏈 exit 0。

WebRTC 檢查這次新終態：

```bash
./scripts/pf view --run 20260917T075134Z_s2_open_box_sealed --scene scene_final.usda --ui --paused
```

若原 viewer 已占用 ports，在既有 Script Editor 載入，不要強制停止：

```python
import omni.usd
omni.usd.get_context().open_stage('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T075134Z_s2_open_box_sealed/scene_final.usda')
```

先儲存既有場景，保持 timeline 停止，選 /World/Probe、按 F 看箱內位置。
本次 human view 未確認。例行 PNG 與物理分開记录；沒有新影片。

128 項測試、7 skipped，exit 0：runs/20260917T075203Z_repair_execute_tests。
新增負向測試：candidate 篡改拒絕、拒絕提案不啟動 GPU、指定 GPU 不足不執行、
不能用另一張 GPU 的空間冒充指定 GPU 資源足夠。smoke exit 0：20260917T075042Z_s1_smoke。

來源：串接控制器、指定 GPU 檢查與分階段檔案是本專案實作（D050）。
生成仍使用本地 box_s2.py，不是 NVIDIA 外部文字生成器；官方部分沿用固定
[usd-content-agents a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa)
的 focused validation。模型執行／外部幾何生成仍 not_tested。
下一步仍需提供可用模型或生成 provider 入口，才能實測真實生成提案；S5-D 未全部完成。
