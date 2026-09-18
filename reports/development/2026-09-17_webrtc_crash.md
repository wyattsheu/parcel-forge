# WebRTC GPU 崩潰診斷

保存日誌：runs/20260917T071258Z_viewer_crash_audit/viewer.before.log。
07:11:14Z omni.rtx 報 ERROR_DEVICE_LOST、vkWaitForFences failed，隨後主動退出；
crash metadata GPU crash=1，active shader=imgui.pixel。
可確認是 GPU/render 路徑退出；無法僅靠這份日誌證明 Play 按鈕、PhysX 或 OOM 為根因。
目前 GPU0 free 97231 MiB 是崩潰後數值，不代表崩潰當時用量。
完整 editor 還有 typing_extensions Sentinel 的擴充載入錯誤與 ROS2 啟動失敗；
尚未證明它們與 GPU crash 有因果關係，未修改共享環境。

新增可選 --paused；不自動 play、不切換 probe gravity、不做定時 release。
只通過 Python 語法檢查；尚未實測串流，不是已驗證修復。

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf view --run 20260917T064636Z_s2_open_box_sealed --scene scene_final.usda --ui --paused
```

先保持停止確認穩定，再按 Play。若只在 Play 後退出，仍需保存當次 viewer.log
作對照。下一個單一參數比較可去掉 --ui、保留 --paused，看 viewport 模式是否也退出；
這是定位 editor UI 路徑，不是已證明繞過 GPU 問題。不得停止其他 viewer 強占 ports。
本次沒有重啟 viewer、修改 driver、安裝套件或 reset GPU。
