# 工作流建置回報：採用 NVIDIA 工作流的計畫調整

狀態：計畫完成；未安裝、未整合、未執行上游。
完整計畫：[上游採用計畫](../../docs/UPSTREAM_ADOPTION_PLAN.md)。

S0–S4 保留為 ITRI 案例與驗收基準。S5 改為先跑 NVIDIA 原廠範例，再接正常／缺底
案例、實際軌跡錄製、官方 agent 修復；數值調參需要時才接 BYOR。
自製 repair_loop 暫停擴寫；來源與版本會在 S5-A 固定完整 SHA。

本次確認指令（閱讀計畫，不是整合驗證）：

    cat docs/tasks/S5A_upstream_baseline.md
    cat docs/UPSTREAM_ADOPTION_PLAN.md

本階段沒有新模擬場景，WebRTC 不適用。既有成功場景仍見 33 點自行驗證清單。
執行回報將在第一個官方範例真正跑完後新增，不能預先寫 pass。
