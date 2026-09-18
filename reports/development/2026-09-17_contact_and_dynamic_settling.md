# 工作流建置回報：接觸參數與動態箱落地

日期：2026-09-17；階段：S4。

本階段增加明確的接觸參數與前後 USD 讀回，並完成動態箱掉落與穩定判定。
回報檔案直接保存在 reports；沒有新增回報服務。

## 方法與來源

- 外部 API：本機 Isaac Sim 6.0.1 的 PhysxCollisionAPI、UsdPhysics.MaterialAPI、physics-purpose material binding；實作在 runtime/isaacsim_runtime.py。
- 外部參數語意：[NVIDIA PhysX 接觸說明](https://nvidia-omniverse.github.io/PhysX/physx/5.4.1/docs/AdvancedCollisionDetection.html)。版本適配以本機 API 為準。
- 專案方法：IsaacSim_Asset_Workflow_Handbook.md 第 9、10 節與 docs/tasks/S4.md；末段 0.5 秒的速度與整體結構判定。
- 專案工程假設：contact offset 0.002 m、rest offset 0 m、static friction 0.6、dynamic friction 0.5、restitution 0。這些是 estimated，並非紙板量測值或 NVIDIA 認證門檻。

## 已驗證

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| 四面側撞＋25 collider 接觸設定 | 4/4 blocked，exit 0 | runs/20260916T163041Z_s4_sidewall/ |
| 九點＋55 collider 接觸設定 | 9/9 inside，exit 0 | runs/20260917T000241Z_s4_placement_grid/ |
| 動態箱掉落 | 保持一個 root body、五面 collider；settled，exit 0 | runs/20260916T163330Z_s4_dynamic_drop/ |
| 離線測試 | 106 tests、7 skipped，exit 0 | runs/20260917T000047Z_s4_final_offline/ |

箱體從 0.35 m 落地，最終 root z 為 1.49e-8 m；最低 z 為 -0.00425 m，
在既定 -0.005 m 界限內。末段最大線速度 1.167e-5 m/s、角速度 6.456e-5 rad/s。
這只驗證剛體模型，不代表真實紙板材料已驗證。

## 自行確認指令

在專案根目錄執行：

    ./scripts/pf sidewall --physics-only
    ./scripts/pf placement-grid --physics-only
    ./scripts/pf dynamic-drop
    python3 -m unittest discover -s tests -v

每次會產生新的 runs 目錄。看該目錄 summary.md、manifest.json 與結果 JSON，
確認 exit、physics verdict 和 render 狀態分開記錄。

WebRTC 看箱體落地後的場景：

    ./scripts/pf view --replace --run 20260916T163330Z_s4_dynamic_drop --scene scene_final.usda --ui

WebRTC 看九點：

    ./scripts/pf view --replace --run 20260917T000241Z_s4_placement_grid --scene scene_final.usda --ui

預期分別看到完整開口箱停在地板，以及九個 probe 位於各自箱內。
這是最終場景檢視，不是掉落動畫；動態过程的數值在 trajectory.csv。
只有人工確認後才能記錄 WebRTC 成功。目前 WebRTC 是 not_tested。

## 限制

物理流程可用 physics-only 避開 optional renderer；這不修復曾發生的 render crash。
舊九點非空白圖片在 runs/20260916T160040Z_s4_placement_grid/renders/s4_nine_point_grid.png。
新接觸設定的 physics-only run 沒有產生圖片。
參數讀回是 composed USD，沒有宣稱取得 PhysX 內部係數 getter。
Runtime 明確警告 suppress readback 會停用 CCD，因此有效 CCD 狀態為 disabled_by_runtime_warning。

六案例完整回歸：runs/20260917T000211Z_s2_open_box_thick_wall_suite.md，6/6、exit 0。
