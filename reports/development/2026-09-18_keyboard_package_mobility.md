# 修正：紙箱裝鍵盤可以整箱移动

原因：前次以固定箱底量測開蓋，產生 /World/Carton/FixedBase。此資產拿到 viewer 仍是固定的，使用者看到的黏地情況符合原設定。
本次改 base_mode=free，箱底為 dynamic，保留重力／地面／碰撞；没有通过關碰撞、零摩擦或 pose 指令讓它移動。

實測：`./scripts/pf-keyboard-package` → exit 0，runs/20260918T001602Z_keyboard_package。
USD 没有世界 joint 錨定；箱體 enabled dynamic。施加水平 12 N、0.2 s，箱體水平位移 0.213743 m，超過事先設定的 0.002 m 移動 gate；不是材料摩擦校準。
四蓋仍由外力打開；放手後大蓋約 175.25/186.38°，小蓋約 269.20/269.10°。受力固定邊界改變，不能沿用舊固定試驗的角度結果。
鍵盤 containment 改用箱體局部座標，避免移動後用世界原點誤判。內容物取出／逐步穿透／人工 viewer 仍 not_tested。

流程修正：free 物件必含 structure.mobility；move/open_and_extract/open_unwrap_and_extract 的 fixed 規格被拒絕。預檢只是選必要 check，實際可移動性仍以物理推力與讀回證據判定。
13 個預檢防線測試通過；包括漏 mobility check 和把取出包裹固定到世界的負向案例。證據：runs/20260918T001728Z_mobility_gate_checks.

## 在既有 WebRTC 更新資產

先儲存現有工作、停止 timeline，在 Script Editor 執行：
```python
from pathlib import Path
p = Path("/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/keyboard_package_editor.py")
exec(compile(p.read_text(), str(p), "exec"), globals())
```
載入器只選 mobility_verified=true 的最新通過 run，不再落回舊固定版本；啟動訊息應顯示 free movable base。
按 Play，使用原生 physics drag 在 /World/Carton/Base 的牆面施力，觀察整箱平移；抓蓋外緣則是開蓋。使用 Shift＋左鍵拖曳或已啟用的原生拖曳模式，避開 transform gizmo。
用相同位置只改施力大小，了解靜摩擦與移動；地面有摩擦，輕推不動不等于被固定。GUI 本次未由人確認，以上是待使用者確認的小操作。
重新實測只跑同一例：`./scripts/pf-keyboard-package`。

來源：現有 carton_author.py 的 free 分支，D066/D068 的固定／自由區別；本次針對可交付 robot prop 新增硬性 mobility gate。仍使用剛性 keyboard proxy，沒有按鍵功能或圖片生成。
