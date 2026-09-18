# 專案回報

這裡只有普通 Markdown 回報，不另外建立回報程式。

## 兩種回報

### `development/`：工作流建置進度

回答「parcel-forge 這套工作流本身建到哪裡」。每完成一個可說明的小階段，
新增一份日期檔，記錄做了什麼、如何驗證、圖片／影片證據、限制與下一步。

### `execution/`：工作流實際執行進度

回答「某一個資產任務目前跑到哪個步驟」。一個 case 或 batch 對應一份報告，
依序列出輸入解析、schema、USD 生成、靜態驗證、模擬、讀回、渲染與交付狀態。
開始一個 case 時先複製模板，尚未執行的列保留 `not_run`；每完成一步就更新
同一份 active report。結束後固定內容並連回最終 run。步驟可標 `pass`、`fail`、
`blocked`、`not_run` 或 `not_tested`，不能因後段通過而掩蓋前段失敗。

## 圖片與影片

- 圖片連回同一次 `runs/` 中的原始 PNG，並註明它是離線 render 或人工畫面。
- 動態結論需要觀看過程時，未來在模擬當下保存短影片、sim time、asset hash。
- 舊 run 只有最終影格，影片記 `not_available`，不事後重建成原始證據。
- agent 只報告圖片路徑與量測統計；WebRTC 畫面是否正確由人確認。

目前可直接參考：

- `development/2026-09-16_workflow_build.md`
- `execution/2026-09-16_open_box_baseline.md`
