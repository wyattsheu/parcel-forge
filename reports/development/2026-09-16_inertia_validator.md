# 工作流建置回報：慣性可行性驗證器修正

日期：2026-09-16  
技術階段：S4  
狀態：完成並驗證

## 目標

修正慣性 tensor 判定依賴座標方向與絕對數值尺度的問題。

## 完成內容

- 改用對稱 3×3 tensor 的主慣性矩，不再把 Ixx／Iyy／Izz 對角項直接當主值。
- 使用 `Sigma = 0.5 trace(I) Identity - I` 的特徵值表示三角不等式。
- 容差改為相對 tensor 尺度，避免小型物件被固定 determinant 門檻誤拒。
- `mass_manifest` 對一般 tensor 回報真正的主慣性矩。

## 驗證

| 檢查 | 結果 | 證據 |
| --- | --- | --- |
| 旋轉後主值 (1,1,4) | 正確拒絕 | `runs/20260916T154420Z_s4_inertia_validator/counterexamples_after.json` |
| 1e-5 合法 tensor | 正確接受 | 同上 |
| 旋轉合法 tensor | 主值還原為 (1,2,2.5) | 同上 |
| 尺度 1e-12、1、1e12 | 判定一致 | `tests/test_mass_properties.py` |
| 質量／慣性 focused tests | 29 通過 | run logs |
| 全部離線測試 | 93 個，7 skipped，exit 0 | run logs |

## 圖片／影片

這是純數學驗證，不需要場景圖片或影片。

## 限制

此結果證明 validator 的數學判定，不代表 0.20 kg 箱體或均質殼體假設符合
任何真實紙箱。

## 下一個小階段

將 mass、COM、principal inertia 與 principal axes 寫入動態箱 USD，並由
PhysX runtime 讀回比較。
