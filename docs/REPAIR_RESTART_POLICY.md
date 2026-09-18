# S5-D 中斷與重跑規則

這是目前可用指令的操作規則，不是已實作的自動續跑控制器。
來源：固定版本 NVIDIA usd-content-agents（a96faf9）的 validation/workflow.py
`_selected_templates`、本專案 repair_guard.py、repair_link.py 與已保存的
runs/20260917T062625Z_s5d_resume_check、20260917T062716Z_s5d_resume_check。

| 中斷階段 | 下一步 | 保留與驗收條件 |
| --- | --- | --- |
| 提案尚未預留 receipt | 修正輸入後重新提交 | 沒有 receipt 才沒有消耗 attempt；不可只看 exit code |
| 已預留 receipt，但沒有 accepted candidate | 查閱 proposal_result.json；若重提，使用控制器下一個 attempt | 該次已消耗；上限三次，不能刪 receipt 或換 source 逃避 |
| accepted candidate 已存在 | 使用原 candidate.json 與 inputs/profile.json 啟動新的 pf box | 不必重提提案；新 run id，舊證據保留 |
| 物理執行中斷或輸出不足 | 在資源足夠後重新跑完整物理 | 不接續部分 trajectory；不能稱為 checkpoint resume |
| link 檢查中斷 | 對同一 proposal 與完整 validation run 重跑 repair-link-check | 每次檢查寫新 run；profile/hash/實測 task 必須通過 |
| physics_sane focused 驗證中斷 | 對完整物理 run 重跑 upstream-focused-check | 重新 prepare/check/finalize；固定上游不支援此 template 的 Wave 2 resume |
| render_valid checkpoint 有 RUNNING claim | 先確認 claim 所屬程序已退出，再依官方 CLI 明確 recovery | 不能終止別人的程序；身份必須一致；恢復狀態不代表 render pass |
| 背景影片未完成 | pf-video-background --status JOB；仍 running 就等待 | stalled/failed 保留 job 與 log；重新提交產生新 job，不更改物理驗收 |

重跑前重新檢查 GPU0 可用 VRAM；不足寫 blocked.json。不得強制釋放資源。
若修復後的實測結果是 inside，但原 fault fixture 的 expected_outcome 是
at_mouth/fell_through，pf box exit 2 是保留下來的回歸標籤不一致。
它不能被單獨宣告為修復成功；仍需 link gate 與 focused official + ITRI gate。

人工檢查既有 candidate 後的重跑流程：

```bash
./scripts/pf box --case runs/PROPOSAL/candidate.json --profile runs/PROPOSAL/inputs/profile.json
./scripts/pf repair-link-check --proposal-run PROPOSAL --validation-run NEW_PHYSICS
./scripts/pf upstream-focused-check --run NEW_PHYSICS
```

render_valid 的受控失敗恢復診斷可用下列指令重新量測；它刻意沒有 OVRTX，
診斷 pass 與終端 render fail 分開記錄，不會生成可接受的影片：

```bash
./scripts/pf upstream-resume-check --run NEW_PHYSICS --template render_valid
```

目前沒有真實模型提案的中斷／重跑驗證。模型只輸出受約束 JSON 的接線仍待建置；
不能把人工提案或 Landlock 內容寫入測試稱為完整模型工作流。

D050 更新：pf repair-execute --proposal-run PROPOSAL 可自動執行 accepted candidate
之後的完整新生成／物理／link／focused 鏈。仍不是 checkpoint resume；失敗重跑
產生新 run，不重送 proposal，不重新保留 attempt。
