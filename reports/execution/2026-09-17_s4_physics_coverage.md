# 工作流執行回報：S4 物理覆蓋

日期：2026-09-17  
輸入：cases/s4/open_box_dynamic.json 與 cases/open_box_normal.json  
最終狀態：S4 必要物理驗收通過；render 與 WebRTC 分開保留限制

| 步驟 | 狀態 | 證據 | 自行重跑指令 |
| --- | --- | --- | --- |
| 動態 USD 生成 | pass | runs/20260916T155155Z_s3_verify_open_box_dynamic/ | ./scripts/pf verify --case open_box_dynamic |
| NVIDIA 41 generic rules | pass | 同 run validation.json | 同上 |
| PhysX mass／COM／inertia／axes | pass | runs/20260916T155652Z_s4_mass_readback/ | ./scripts/pf mass-readback |
| 九點放置 | pass，9/9 | runs/20260916T160040Z_s4_placement_grid/ | ./scripts/pf placement-grid |
| 九點 offline PNG | pass（統計非空白） | renders/s4_nine_point_grid.png | 同上 |
| 四面側撞 physics | pass，4/4 | runs/20260916T161010Z_s4_sidewall_recovery/ | ./scripts/pf sidewall |
| 四面側撞 offline render | fail | runs/20260916T160621Z_s4_sidewall/logs/isaac_runtime.log | ./scripts/pf sidewall |
| WebRTC 人工確認 | not_tested | 無人工作證 | 見下方 |
| 動態箱 drop／settling | pass | runs/20260916T163330Z_s4_dynamic_drop/ | ./scripts/pf dynamic-drop |
| contact composed USD＋行為 | pass | runs/20260916T163041Z_s4_sidewall/ | ./scripts/pf sidewall --physics-only |

## WebRTC 自行確認

九點：

    ./scripts/pf view --replace --run 20260916T160040Z_s4_placement_grid --scene scene_final.usda --ui

四面側撞：

    ./scripts/pf view --replace --run 20260916T160621Z_s4_sidewall --scene scene_final.usda --ui

請人工記錄是否看到九個 probe 位於九個箱內，以及四個 probe 是否分別停在四面內牆。
WebRTC 結果不會改寫 trajectory 的數值判定，也不會修復舊 run 的 offline render failure。

## 後續驗證更新

接觸參數、九點重跑及動態箱 settling 已驗證；舊限制以本節更新為準。
完整數值、來源與自行重跑／WebRTC 指令見
[接觸與落地回報](../development/2026-09-17_contact_and_dynamic_settling.md)。

最新明確接觸設定九點結果：runs/20260917T000241Z_s4_placement_grid/，9/9、exit 0；render not_tested。
六案例回歸：runs/20260917T000211Z_s2_open_box_thick_wall_suite.md，6/6、exit 0。
