# 工作流執行回報：<case/batch id>

日期：<YYYY-MM-DD>  
輸入：<spec path>  
run：<runs/path>  
最終狀態：<pass/fail/blocked/in_progress>

| 步驟 | 狀態 | 輸出／證據 | 自行重跑指令 | 說明 |
| --- | --- | --- | --- | --- |
| 1. 輸入解析 | not_run | | | |
| 2. Schema／構造檢查 | not_run | | | |
| 3. USD 生成 | not_run | | | |
| 4. 靜態／NVIDIA 規則 | not_run | | | |
| 5. PhysX 模擬 | not_run | | | |
| 6. 狀態讀回與任務判定 | not_run | | | |
| 7. 離線圖片／影片 | not_run | | | |
| 8. WebRTC 人工觀看 | not_tested | | | |

## WebRTC 自行確認

    ./scripts/pf view --replace --run <run-id> --scene <scene_final.usda|asset.usda> --ui

應人工看到：<具體現象>。WebRTC 結果不取代數值 verdict。

## 最終結論

<目前做到哪一步；如果中斷，下一步從哪裡開始。>
