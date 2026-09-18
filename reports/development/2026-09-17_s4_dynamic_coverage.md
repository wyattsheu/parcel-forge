# 工作流建置回報：S4 動態質量與空間覆蓋

日期：2026-09-17  
技術階段：S4  
狀態：必要物理驗收完成；side-wall render failure 仍保留

## 完成內容

- 動態箱 USD 明寫 mass、local COM、principal inertia、principal axes。
- PhysX tensor view 直接讀回四項數值，全部在 transport tolerance 內。
- 九點放置 9/9 inside，保存 trajectory、scene_final 與非空白 PNG。
- 四方向側撞有完整 240×4 trajectory，4/4 被牆阻擋。
- side-wall runtime 改成先保存 physics checkpoint，再嘗試 optional render。

## 方法來源

| 類型 | 採用內容 | 來源 |
| --- | --- | --- |
| 外部方法 | MassAPI 欄位與 local COM | https://openusd.org/release/api/class_usd_physics_mass_a_p_i.html |
| 外部方法 | pseudo-inertia feasibility、參數 confidence | https://arxiv.org/html/2503.00370v2 |
| 外部方法 | 動態證據優先於單張影像 | https://arxiv.org/html/2410.13882v2 |
| 本專案設計 | 九點位置、四方向側撞、2 mm overshoot 門檻 | parcel-forge S4 task |
| 本機 API 適配 | RigidPrim get_masses/get_coms/get_inertias | Isaac Sim 6.0.1 local site-packages |

## 自行驗證

    ./scripts/pf mass-readback
    ./scripts/pf placement-grid
    python3 -m unittest tests.test_sidewall -v
    cat runs/20260916T161010Z_s4_sidewall_recovery/summary.md

WebRTC 看九點結果：

    ./scripts/pf view --replace --run 20260916T160040Z_s4_placement_grid --scene scene_final.usda --ui

WebRTC 看四面側撞最終場景：

    ./scripts/pf view --replace --run 20260916T160621Z_s4_sidewall --scene scene_final.usda --ui

## 證據

- Dynamic readback：runs/20260916T155652Z_s4_mass_readback/
- 九點：runs/20260916T160040Z_s4_placement_grid/
- 九點 PNG：runs/20260916T160040Z_s4_placement_grid/renders/s4_nine_point_grid.png
- 側撞原 run：runs/20260916T160621Z_s4_sidewall/
- 側撞 recovery：runs/20260916T161010Z_s4_sidewall_recovery/
- Offline regression：runs/20260916T161109Z_s4_offline_regression/，101 tests、7 skipped、exit 0

## 限制與下一步

側撞 physics pass，但舊 run 的 optional render 使 Kit exit -11；WebRTC 尚待人工確認。
動態 settling 與接觸讀回已完成，詳見下節。

## 後續驗證更新

接觸參數、九點重跑及動態箱 settling 已驗證；舊限制以本節更新為準。
完整數值、來源與自行重跑／WebRTC 指令見
[接觸與落地回報](../development/2026-09-17_contact_and_dynamic_settling.md)。
