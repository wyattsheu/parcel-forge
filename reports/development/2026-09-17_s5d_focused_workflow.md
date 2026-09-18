# S5-D：官方 focused workflow 接線與寫入限制

本輪實作：新增 `pf upstream-focused-check`，凍結原始 run 的六個輸入，核對 upstream SHA 與乾淨工作區，呼叫官方 prepare → check → finalize，最後 AND 合併官方 physics_sane 與原本 ITRI 的 CSV 包含判定。沒有重新模擬物理、模型呼叫或影片生成。

| 案例 | 官方 physics_sane | ITRI task_acceptance | 合併結果／exit |
| --- | --- | --- | --- |
| 修復後缺底箱 | pass | pass | pass／0 |
| 原始缺底箱 | pass | fail（fell_through） | fail／1 |

[通過證據](../../runs/20260917T020921Z_s5d_focused_gate/focused_result.json) · [反例證據](../../runs/20260917T020945Z_s5d_focused_gate/focused_result.json) · [統整](../../runs/20260917T021113Z_s5d_focused_completion/suite.json)。官方 sanity 通過不能升級 deterministic task fail。

自行確認，不生成影片：

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf upstream-focused-check --run 20260917T015711Z_s2_open_box_no_bottom
./scripts/pf upstream-focused-check --run 20260917T012420Z_s2_open_box_no_bottom
./scripts/pf actor-boundary-check
```

前兩條預期 exit 0／1；第三條 exit 0、9 個探測檢查 pass。每次寫新 run。`official/` 保留 NVIDIA 的 request、plan、operation result、validation_result、evidence、checkpoint 與 final_summary。這是 outer-selected deterministic capability flow，不是模型自動修復。

官方依賴先 dry-run，再安裝到 `.venvs/usd-content-agents`：解析 132 個套件，本輪新增 29 個；安裝 exit 0，CLI／validate help／pip check 均 exit 0。共享 Isaac runtime 沒有改動，也沒有啟動任何服務。版本 freeze 與輸出保存在 runs/20260917T020546Z_s5d_cli_checks/。115 項離線測試、7 項跳過通過；實際新流程以兩個整合命令驗證。

官方 checkpoint 已由新程序使用 FileValidationCheckpointStore.load 讀回，physics_sane record=completed、attempts=1。證據：runs/20260917T020950Z_s5d_checkpoint_readback/。這證明持久化與讀回，不等於中断恢復測試通過；interrupted resume 仍 not_tested。

Linux bubblewrap 的網路 namespace 與 uid map 探測各 exit 1，保留 runs/20260917T020237Z_s5d_namespace_probe 與 020250Z_s5d_filesystem_probe。沒有改 kernel 或系統設定。

改用 Linux Landlock ABI 6 測試檔案內容寫入邊界：允許 outputs/ 候選寫入；拒絕保護檔寫入、建立、刪除、截斷、符號連結越界、rename 越界；exec 子程序繼承限制；原始 fixture 保持不變。來源：[Linux Kernel Landlock 文件](https://docs.kernel.org/userspace-api/landlock.html) 與本機 syscall headers。`actor_boundary.py` 提供先啟用限制、再 exec 的入口，啟用失敗就拒絕執行。

範圍必須清楚：目前不限制读取、網路、程序存取、chmod 等 metadata 操作；已開啟的 file descriptor 也不由這個寫入規則完整保護。這不是完整 actor sandbox，所以本輪沒有啟動不受信任的模型 shell。後續 actor 的權限邊界仍需設計與測試。

NVIDIA 來源固定為 [a96faf9](https://github.com/NVIDIA-Omniverse/usd-content-agents/tree/a96faf9cb2f5c1f655fe0d60c0ccf57e3477b1aa)：content_workflow_cli CLI 的 validate prepare/check/finalize；checkpoint 使用 upstream 原類別，沒有仿造 checkpoint 格式。CSV gate 與 Landlock adapter 為本地新增。第一輪 adapter 020828Z 因誤讀 template verdict 欄位 exit 4，已改讀官方 final verdict 並核對 template status；舊失敗保留。

物理 smoke：runs/20260917T020211Z_s1_smoke，exit 0、physics/readback pass，render not_tested。WebRTC 人工確認仍 not_tested；本輪無新影像。

協作：A/B/C 已由使用者交給其他 AI；C 的 scripts/pf-video-background 未在這輪修改。收到交接檔後，主線負責審查、整合與共同進度更新。

下一個動作：整合 A 的官方接線盤點與 B 的修復邊界審查，確定 actor 啟動權限與 checkpoint/resume 實驗後再呼叫模型。
