生成一個供機器人拆包裹用的瓦楞紙箱模擬資產（Isaac Lab / USD / PhysX），情境為開箱動作模擬。

**箱體結構**

- 標準 RSC（regular slotted container）上蓋結構，四片上蓋：兩片長邊主蓋（major flap）、兩片短邊次蓋（minor flap），沿箱體上緣以摺痕連接，膠帶已拆除。
- 材質為單層或雙層瓦楞紙板（B flute 或 C flute），厚度約 3–5 mm，具正交異向性（順紋 MD 方向勁度遠高於橫紋 CD 方向）。

**摺痕力學特性**

- 每片上蓋與箱體連接處是壓痕造成的局部降伏區，用彈塑性鉸鏈（elasto-plastic hinge）描述，不是單純彈簧-阻尼關節。
- 力矩-轉角關係分兩段：
  - 轉角在降伏力矩以下時線性彈性回復，放手後彈回接近原始摺角。
  - 超過降伏力矩後產生不可逆塑性轉角，放手後停在「殘餘彈性回復力矩」與「重力力矩」打平的角度，不會完全彈回。
- 加載與卸載走不同曲線（力矩-轉角遲滯），重複開合會使降伏力矩逐漸下降（疲勞軟化）。

**USD 關節設定**

每片上蓋一個 `UsdPhysicsRevoluteJoint`，掛在箱體與蓋子之間：

- `physics:axis`：對齊摺痕方向
- `physics:lowerLimit` / `physics:upperLimit`：約 -5°～100°
- `UsdPhysicsDriveAPI:angular`
  - `physics:stiffness`：0.02–0.05 N·m/rad
  - `physics:damping`：0.001–0.005 N·m·s/rad
  - `physics:targetPosition`：動態塑性參考角（見下方）
- `PhysxSchemaPhysxJointAPI:jointFriction`：0.005–0.02 N·m，模擬摺痕纖維咬合與殘膠阻力

**降伏行為的 per-step 更新邏輯**

每個 physics step：

1. 讀取當前關節角度 θ，估算彈性回復力矩 M = stiffness × (θ - target)
2. 若 |M| > yield_torque（先給 0.03–0.08 N·m 量級）：
   - Δtarget = (|M| - yield_torque) / plastic_modulus × dt，往轉角方向更新 target
3. 若未超過降伏力矩，target 不變，走純彈性段
4. 用 `ArticulationView.set_joint_position_targets()` 寫回更新後的 target

**校準方式**

以上 stiffness / yield_torque / plastic_modulus 數值僅為初始量級，需以真實紙箱手動開合測試（推開至不同角度放手，量測最終停留角）反推校準，而非直接套用文獻數值。
