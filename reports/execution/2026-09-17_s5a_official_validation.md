# 工作流執行回報：官方 Validation Agent 原廠範例

Run：20260917T010638Z_s5a_upstream_setup；模式：fixed-pipeline / validation-agent-cli。

| 步驟 | 結果 | 證據 |
| --- | --- | --- |
| clone／固定 SHA | exit 0、0.6.0／a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa | upstream.json、logs/clone.log |
| 獨立 venv／install | exit 0 | install_0.json、install_1.json |
| CLI help | exit 0 | logs/help.log |
| 依賴一致性 | exit 0 | logs/dependency_check.log |
| 原廠 behavior evidence | pass、exit 0 | official_example/validation_result.json |
| 缺資料負例 | fail、exit 1（預期拒絕） | missing_evidence_result/validation_result.json |
| 上游原碼未更動 | verified clean | logs/upstream_status.log |
| 本例重新執行 physics | not_tested | 未啟動模擬 |
| 本例 render／WebRTC／影片 | not_tested／not_produced | 無新畫面 |

輸入 fixture 與 config 原始 bytes 在 inputs/；manifest.json 記錄雜湊。
範例預先附帶的 judge 判定不是本次產生。缺資料負例使用缺失 summary，
不能以正常範例 pass 取代該 run 的 fail。

重跑指令：[建置報告](../development/2026-09-17_s5a_upstream_baseline.md)。
