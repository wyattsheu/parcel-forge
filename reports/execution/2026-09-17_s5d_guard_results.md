# S5-D 執行：修復工具測試與背景影片

已建立 `pf repair-proposal`：只接受移除非預期封口或補回箱底，其他欄位保持不變。兩個手寫提案均重新執行物理，數值任務驗收由 fail 變 pass；縮小 probe 提案 exit 1 被拒絕。115 項測試、7 項跳過通過。這是修復工具驗證；官方模型執行、checkpoint/resume 與模型檔案存取隔離尚未驗證。

[前後數值證據](../../runs/20260917T015901Z_s5d_progress/repair_suite.json)。兩組修復後的 pf box exit 2 是因為保留原本故障 expected_outcome，不修改它來換取 pass；後續 independent task_acceptance 與官方 physics_sane 均 pass，upstream-check exit 0。物理量測與回歸判定分开。

自行確認一個概念與實驗：保持箱子與 probe 不變，只改提案指向的欄位。

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf repair-proposal --case cases/open_box_sealed.json --proposal contracts/repair_proposals/remove_lid.json
./scripts/pf repair-proposal --case cases/open_box_sealed.json --proposal contracts/repair_proposals/reject_probe_change.json
```

第一個 exit 0、accepted_for_validation，表示可以產生候選，尚不等於物理合格；第二個 exit 1、rejected，不產生 candidate.json。可查看已量測修復結果：

```bash
./scripts/pf upstream-check --run 20260917T015648Z_s2_open_box_sealed
./scripts/pf upstream-check --run 20260917T015711Z_s2_open_box_no_bottom
```

兩者預期 task_acceptance=pass，regression_expectation=fail。這些命令不生成影片。

方法來源：沿用 NVIDIA 固定 SHA [a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa) 的工作流方向；已讀 entrypoint.py、validation_runner.py 與 FileValidationCheckpointStore。官方 checkpoint 具有 create/load/update/finalize 原子儲存邊界，這輪僅盤點，沒有拿自己的檔案冒充官方 checkpoint。allowlist 提案執行閘門為本地新增。前置量測指出獨立環境尚無 content_agent_workflows，PATH 中無 node/npm；認證 unknown，未印出任何 secrets。

影片改成需要時才做；前兩支渲染程序各約 78、83 秒，還不含編碼。新背景脚本不需安裝套件或服務：

```bash
./scripts/pf-video-background --run 20260917T015711Z_s2_open_box_no_bottom
```

命令會立即回傳 job 路徑與 PID，你可繼續其他工作。不要一次啟動多個 GPU 渲染工作；背景渲染仍會與物理測試競爭 GPU。job_request.json 保留指令，job_started.json 僅代表已啟動，video.log／worker.log 是日誌；job_result.json 才是完成結果。若 status=failed 請查日誌，不當成影片完成。

本次背景測試：

```bash
cat runs/20260917T015837Z_background_video/job_started.json
cat runs/20260917T015837Z_background_video/job_result.json
tail -n 20 runs/20260917T015837Z_background_video/video.log
```

job_result.json 在完成前不存在。成功時其中 video 欄位是可開啟 MP4 的絕對路徑。WebRTC 繼續使用既有編輯器 File → Open 開該 video_run 裡的 recording.usda，選 RecordingCamera 後播放；不另啟 viewer。人工確認仍 not_tested。

下一步：補齊最小官方 CLI／runner 前置與 actor 檔案隔離，再接官方 request/checkpoint。背景影片工具只處理媒體輸出，不另建工作流調度系統。

背景腳本實測已完成：job_result status=pass、exit 0，450 張 H.264 影格，影片 SHA256 重新核對一致。渲染同時進行修復證據與報告工作；這確認可以免等待，不代表 GPU 渲染加速。

[背景生成的修復後影片](../../runs/20260917T015837Z_s5c_recorded_video/test_recording.mp4) · [背景完成證據](../../runs/20260917T015837Z_background_video/job_result.json)。
