# 執行：模板恢復資格與新缺底箱修復鏈

以目前 S0–S7 規劃粗估約 70%。只涵蓋 primitive open boxes／rigid probes／既有 Isaac PhysX 工作流，不包含實體紙板折痕、變形與材料校準。這是里程碑估算，不是剩餘工時、程式品質或物理準確率。

| 階段 | 現況 | 本次估算用的分數 |
| --- | --- | --- |
| S0–S4 基礎環境、物理、幾何、參數驗證與測試覆盖 | 歷史驗證完成；本輪 smoke 重跑 pass | 各 1 |
| S5 上游整合、錄製與修復 | A/B/C 完成；D 部分完成 | 暫估 0.6 |
| S6 批次／語意／VLM | 未完成 | 0 |
| S7 冷啟動交付與驗收 | 未完成 | 0 |

八個階段等權：(5 + 0.6) / 8 ≈ 70%。S5 的 0.6 是粗估，後续工時可能集中在 actor／模型／批次；不應拿此值推算日期。BYOR 是視需求的 S5-E，若納入必做範圍需重新估算。

本輪完成：

1. 新增 `pf upstream-resume-check`。固定版本 run_validation_workflow/resume 只接受 render_valid/look_right，physics_sane 被拒絕。官方 focused 流程會生成 physics_sane checkpoint，但 checkpoint 存在／可讀不代表這個 resume API 支援它。
2. 明確選 render_valid 做受控狀態恢復：在官方 claim 建立後，自己的 trusted Python 程序抛 KeyboardInterrupt，exit 130。改 request 以新程序恢復被 identity mismatch 拒絕；不回收 claim 的 CLI resume exit 2 被拒絕；確認原程序已退出後，只回收本次測試的 claim，再完成 attempt 2。
3. 此探測明確指定不存在的獨立 OVRTX 路徑、禁自動 provisioning，不產生新渲染。恢復後官方 final verdict 保持 fail（renderer_unavailable），CLI exit 1；檢查程序 exit 0 只表示恢復／失敗保留測試成功，不代表 asset/render pass。沒有 mock 視覺 pass。
4. 以已綁定的 v2 candidate 及原 source profile 重新跑物理：900 筆軌跡，inside；原 expected_outcome=fell_through 保持不變，因此 pf box exit 2（故障回歸 fail），新 task acceptance pass。repair-link-check exit 0、官方 focused gate exit 0。這次 controller 執行輸出是新的，不再只匹配舊資料。

[統整證據](../../runs/20260917T063120Z_s5d_resume_progress_completion/suite.json) · [視覺狀態恢復](../../runs/20260917T062716Z_s5d_resume_check/resume_result.json) · [物理 resume 拒絕](../../runs/20260917T062625Z_s5d_resume_check/resume_result.json) · [新修復鏈](../../runs/20260917T062915Z_s5d_repair_link/link_result.json)。

新物理 run：runs/20260917T062811Z_s2_open_box_no_bottom/。physics ran，readback/CSV gate pass；其例行兩張 PNG render status=ok（統計驗證），不宣稱人工觀看通過。官方 focused gate 不重跑物理或渲染，分開記錄 not_tested。WebRTC human confirmation 仍 not_tested。本輪沒有影片。

自行確認一個概念＋單一參數實驗：checkpoint 支援是依 template，不是依檔案存在。只改 --template：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf upstream-resume-check --run 20260917T015711Z_s2_open_box_no_bottom --template physics_sane
./scripts/pf upstream-resume-check --run 20260917T015711Z_s2_open_box_no_bottom --template render_valid
```

第一條 exit 4、not_supported；第二條診斷 exit 0、state 恢復 pass，但 final_verdict=fail、recovered_claim_exit=1。這是 deliberate unavailable-renderer 恢復測試，不會自動 provision 或當成新影像證據。

不重新執行物理的鏈接與驗收：

```bash
./scripts/pf repair-link-check --proposal-run 20260917T025702Z_s5d_repair_proposal --validation-run 20260917T062811Z_s2_open_box_no_bottom
./scripts/pf upstream-focused-check --run 20260917T062811Z_s2_open_box_no_bottom
```

兩條 exit 0。要看本次物理的實際圖片，可開新 run 的 renders/ 路徑，或用既有 WebRTC 編輯器載入 asset.usda 自行操作；後者是新的人類重跑，不等於觀看本次 trajectory，也未被本輪確認。不要另啟相同 ports 的 viewer。

來源：pinned NVIDIA [a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa) validation/workflow.py 的 _selected_templates、ValidationStepExecutor、run_validation_workflow；CLI 的 _handle_validate_resume 与 --recover-orphaned-claims。本地新增的是 trusted interruption probe，不改 upstream、不更換 validator、不放寬 threshold。A 審查的恢復功能在 template 層仍有這個限制，D046 記錄本次量測。

保留的失敗診斷：062342（發現 physics_sane 不支援）、062530／062619（診斷腳本把 fail verdict 的 CLI exit 1 誤當錯誤）；修正為核對官方退出碼與 terminal verdict/完整 checkpoint，062716 通過。不是修改物理或 asset 判定。

121 項離線測試、7 項跳過，exit 0：runs/20260917T062951Z_s5d_resume_final_checks。必要 smoke physics-only exit 0：runs/20260917T062202Z_s1_smoke。新物理執行前 GPU0 94284 MiB free，已保存 inventory；沒有停止共享程序、改環境、安裝套件、呼叫模型或 push。

仍待完成：封口修復的 v2 新執行鏈、受限模型產生提案與完整 actor 權限、對不支援物理 resume 的階段重啟政策，以及 S6/S7。

下一個動作：用 remove_lid v2 提案，建立來源封口 → 新 candidate → 新物理 → unchanged profile/task gate 的另一條執行鏈。
