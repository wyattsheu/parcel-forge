# 兩個驗收失敗的真正原因與修正

使用者授權修兩項（D060）。兩項都不是放寬門檻，碰撞、材料參數、資產幾何皆未更動，舊 run 目錄一個字都沒改。

## 一、`settled` 失敗是量測方式錯，不是紙箱在動

[20260917T105836Z_ext1_carton](../../runs/20260917T105836Z_ext1_carton) 的高力矩主蓋 `HingeMajorYP`，
t≈2.8 s 之後角度連最後一個 bit 都沒變（固定在 0.2819564938545227 rad），持續 7.2 s；
同一時間 DOF 速度讀回卻停在 0.2651888430118561 rad/s。位置靜止而速度非零，是持續接觸下的關節速度讀回假象。

離線重放保留證據：[stale_velocity_replay.json](../../runs/20260917T130752Z_ext1_settle_spec_delivery/stale_velocity_replay.json)
量到該關節最後 1 秒的角度總變化量是 0.0 rad，舊 gate 卻判 fail。
新 run [20260917T130538Z_ext1_carton](../../runs/20260917T130538Z_ext1_carton) 獨立重現同一假象：
`HingeMinorXN` 速度讀回 0.339 rad/s，最後 1 秒角度變化 0.0021 rad。

修正：`settled` 改以最後 1 秒的角度峰對峰值除以視窗長度判定，容差仍是 0.02 rad/s，
平均速率判準與原本一致。速度讀回沒有被隱藏，仍完整記在 `settle_metrics.velocity_readback_rad_s`
與 `velocity_readback_settled`，讓假象本身留在證據裡。

## 二、legacy-mixed 的次蓋失敗是測試規格錯，不是資產壞

該情境用低力矩壓住一片主蓋，同時要求兩片次蓋塑性張開。RSC 的次蓋在下、主蓋在上，
被蓋住的次蓋轉不上去，任何力矩都無法滿足這個 gate。

量到的對照：同樣 0.08 N·m，在 legacy-mixed 只讓次蓋動 0.57°；在主蓋先開的 opening-order 則開到 100°。

修正：把 legacy-mixed 標為 `superseded_by_spec_error` 退役，不是放寬。情境仍可執行、
checks 仍照算照報、狀態是新的終端值 `superseded`（永遠不會變成 pass）、pf-carton 對它仍 exit 非 0。
它原本要測的高低載對照，由 crease-coupon 承接：比較兩片上方沒有遮擋的次蓋。
`pf-carton` 預設情境改為 opening-order。

## 本輪實測

| 命令 | run | 結果 |
| --- | --- | --- |
| `./scripts/pf-carton --scenario opening-order` | 20260917T130538Z_ext1_carton | pass, exit 0 |
| `./scripts/pf-carton --scenario crease-coupon` | 20260917T130614Z_ext1_carton | pass, exit 0 |
| `./scripts/pf-carton --scenario crease-cyclic` | 20260917T130641Z_ext1_carton | pass, exit 0 |
| `./scripts/pf-carton --scenario legacy-mixed` | 20260917T130717Z_ext1_carton | superseded, exit 1，次蓋阻擋 fail 仍在 checks 裡 |
| `./scripts/pf smoke` | 20260917T130254Z_s1_smoke | exit 0 |
| `python3 -m unittest discover -s tests` | — | 145 tests、7 skipped、exit 0（原 136＋新 9） |

## 沒有做到的事

真實紙板校正仍 not_tested，所有 stiffness / yield / viscosity 仍是 `uncalibrated_assumption`。
板面正交異向性只有一維條模型，箱壁與底仍是剛體。render、影片、WebRTC 人眼觀看本輪皆未執行。
`velocity_readback_settled` 為 false 的成因（PhysX 端為何保留舊值）尚未查明，只是不再用它當判準。
