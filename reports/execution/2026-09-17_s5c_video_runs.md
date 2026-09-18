# S5-C 執行回報：正常箱／缺底箱影片

已完成兩組 CSV → 錄製 USD → PNG → H.264 MP4。每組 900 筆位置與四元數逐筆重新讀取比對，最大誤差皆為 0；每支影片 960×540、30 FPS、450 張、15 秒，以 0.25 倍速播放。影格空白統計皆為 0，影格 RGB 有變化。這是程式量測結果，影像內容與 WebRTC 仍待你人工確認。

- [正常箱影片](../../runs/20260917T014950Z_s5c_recorded_video/test_recording.mp4) · [錄製 USD](../../runs/20260917T014950Z_s5c_recorded_video/recording.usda) · [執行證據](../../runs/20260917T014950Z_s5c_recorded_video/video_result.json)
- [缺底箱影片](../../runs/20260917T015128Z_s5c_recorded_video/test_recording.mp4) · [錄製 USD](../../runs/20260917T015128Z_s5c_recorded_video/recording.usda) · [執行證據](../../runs/20260917T015128Z_s5c_recorded_video/video_result.json)

正常箱原始任務驗收 pass；缺底箱 fell_through、任務驗收 fail、故障回歸 pass。兩支影片的生成 pass 不代表兩個箱子都合格。影片播放沒有重新模擬物理；USD 移除 PhysicsScene 並停用 rigidBodyEnabled。錄製僅涵蓋 CSV 的 0.029167–3.775 秒，沒有補造起始動作；影片定時取樣與 USD 插值並非逐一展示全部 900 筆，最後影格為約 3.770834 秒。只支援目前 S2 的單一動態 probe，不能宣稱已支援動態箱等多剛體錄製。

自行重跑：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf video --run 20260917T012407Z_s2_open_box_normal
./scripts/pf video --run 20260917T012420Z_s2_open_box_no_bottom
```

每次產生新 run，不覆寫舊證據；預期 exit 0，video_result.json 的 status=pass。此指令需要足夠 GPU VRAM，且不啟用 livestream。

直接開影片（在有桌面播放器的本機）：

```bash
xdg-open /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T014950Z_s5c_recorded_video/test_recording.mp4
xdg-open /mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T015128Z_s5c_recorded_video/test_recording.mp4
```

WebRTC：使用你目前已開啟的 Isaac Sim 編輯器，File → Open，開上述 recording.usda；選 /World/RecordingCamera 為視角，再用時間軸 Play 看原始速度錄製。不要另啟占用同一組串流連接埠的 viewer，也不要新增 PhysicsScene。這項人工操作未由程式驗證；請在人工確認表記錄是否看見 probe 正常留在箱內／缺底落下。檔案位置可由以下指令取得：

```bash
realpath runs/20260917T014950Z_s5c_recorded_video/recording.usda
realpath runs/20260917T015128Z_s5c_recorded_video/recording.usda
```

方法來源與本地新增：

- **參考 NVIDIA USD Content Agents**：exact rollout／time-sampled USD／PNG 的證據路徑；固定版本 [a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa)，本地來源 external/usd-content-agents/world_understanding/functions/graphics/render_time_sampled_usd.py。實際試跑官方 OVRTX 入口 exit 1：獨立 OVRTX runtime 尚未部署且禁止自動 provisioning；不能宣稱官方渲染已通過。
- **使用安裝版本 NVIDIA Replicator API**：orchestrator.step(delta_time=0.0, pause_timeline=True, wait_for_render=True)，來源是安裝版 omni.replicator.core 1.13.27 的 scripts/orchestrator.py:1745；它明確定義零時間增量與等待完成渲染。由現有 Isaac Sim 6.0.1 渲染，不安裝另一套 runtime。
- **本地新增**：CSV 轉錄、逐筆回讀、原始輸入與 USD hash 綁定、零時間偏移檢查、影格統計、ffmpeg 編碼與 ffprobe 張數核對。這些是 ITRI 證據保護，不宣稱為 NVIDIA 官方 certification。
- MP4 是提供人看的附加檔；官方 PNG-only judge 尚未執行，不能以 MP4 成功代表 VLM qualification。

歷程：014602、014716 兩次渲染空 RGB 均失敗並保留。修正為 Replicator 明確 capture 後，上述兩組命令 exit 0。離線 111 項測試、7 項跳過通過；session smoke physics-only exit 0，該 smoke 的離線渲染 not_tested。

下一步：S5-D 先沿用官方 checkpoint／request 入口，接入受限的候選 spec 修復；不改驗收門檻。
