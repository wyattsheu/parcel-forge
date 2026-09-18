# 工作流實際執行回報：open_box baseline

日期：2026-09-16  
案例：正常箱、封口箱、漏底箱及尺寸變體  
最終狀態：目前可執行到固定箱動態驗證與離線 render；S4 動態箱覆蓋尚未開始。

## 執行步驟

| 步驟 | 狀態 | 輸出／證據 | 說明 |
| --- | --- | --- | --- |
| 1. 讀取 case | pass | 各 run 的 `request.json` | case、單位、預期結果與 provenance 已保存 |
| 2. Schema／構造檢查 | pass | `schema_findings.json` | 7 個非法案例在啟動 simulator 前正確拒絕 |
| 3. 產生 USD | pass | 各合法 run 的 `asset.usda` | defaultPrim、SI units、Z-up 已寫入 |
| 4. 內部 G1 靜態檢查 | pass | `validation.json` | 尺寸、collider、rigid-body hierarchy 等檢查通過 |
| 5. NVIDIA generic USD 規則 | pass | `validation.json` | 41 條已註冊規則執行；不是 SimReady 認證 |
| 6. PhysX 固定箱模擬 | pass | `trajectory.csv` | 正常、封口、漏底與 3 個尺寸變體符合預期 |
| 7. 狀態讀回與任務判定 | pass | `s2_result.json` | local-frame 結果為 inside／at_mouth／fell_through |
| 8. 最終 USD | pass | `scene_final.usda` | 寫入 PhysX 讀回的最終 pose |
| 9. 離線 PNG | pass | `renders/*.png` | 非空統計通過；圖片內容未由 agent 人眼判讀 |
| 10. WebRTC 人工觀看 | not_tested | 無本次人工作證 | 需由使用者實際觀看後另記 |
| 11. 動態箱 mass/COM/inertia readback | pass | `runs/20260916T155652Z_s4_mass_readback/` | `./scripts/pf mass-readback` |
| 12. 九點放置 | pass，9/9 | `runs/20260916T160040Z_s4_placement_grid/` | `./scripts/pf placement-grid` |
| 13. 四面側撞 physics | pass，4/4 | `runs/20260916T161010Z_s4_sidewall_recovery/` | 原 run render 失敗，physics trajectory 完整 |

## 案例結果

| 案例 | 預期 | 實際 | 證據 |
| --- | --- | --- | --- |
| normal | inside | inside | `runs/20260916T141357Z_s2_open_box_normal/` |
| sealed | at_mouth | at_mouth | `runs/20260916T141411Z_s2_open_box_sealed/` |
| missing bottom | fell_through | fell_through | `runs/20260916T141343Z_s2_open_box_no_bottom/` |
| small | inside | inside | `runs/20260916T141425Z_s2_open_box_small/` |
| tall | inside | inside | `runs/20260916T141438Z_s2_open_box_tall/` |
| thick wall | inside | inside | `runs/20260916T141450Z_s2_open_box_thick_wall/` |

## 圖片與動態證據

- 正常箱俯視：`runs/20260916T141357Z_s2_open_box_normal/renders/open_box_normal_interior_top.png`
- 正常箱側視：`runs/20260916T141357Z_s2_open_box_normal/renders/open_box_normal_side_low.png`
- 封口側視：`runs/20260916T141411Z_s2_open_box_sealed/renders/open_box_sealed_side_low.png`
- 漏底側視：`runs/20260916T141343Z_s2_open_box_no_bottom/renders/open_box_no_bottom_side_low.png`
- 動態資料：上述 run 的 `trajectory.csv`。
- 影片：not_available；這批歷史 run 沒有保存連續 render frames。

## 目前停止位置

固定箱 baseline 已完成到「生成 → 靜態檢查 → generic NVIDIA validator →
PhysX 模擬 → local-frame 判定 → 最終 USD → 離線圖片」。下一次執行工作流
已加入 S4 動態 readback、九點與側牆 physics。下一步是有效 contact 參數記錄與
動態箱 drop／settling；side-wall offline render 仍需新 run 重試。
