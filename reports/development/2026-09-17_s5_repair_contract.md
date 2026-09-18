# 工作流建置回報：S5 修復合約

已建立 contracts/repair_proposal_v1.schema.json 與 docs/REPAIR_CONTRACT.md。
本階段是修復接口規格，尚未實作或驗證修復執行。

來源：本專案 handbook 第 11 節、S5 task；Articulate-Anything 與 LL3M 的
critic／minimal patch／套用和結果分離方法，來源連結見 docs/METHODS.md。
精確欄位 allowlist 和三個 patch 上限是專案設計，不是 NVIDIA 標準。

自行確認 JSON 語法：

    python3 -m json.tool contracts/repair_proposal_v1.schema.json

預期正常輸出 JSON、exit 0；這只證明語法，不證明 allowlist 已受執行層限制。
此階段沒有模擬場景或影片；前階段的 WebRTC 指令見接觸與落地回報。
下一步建立離線 gate，以禁止修改 expected_outcome 的實驗驗證限制。
