# Codex 紙箱生成：四蓋 USD 與彈塑性原型

本次使用目前對話中的 Codex 直接建模／編程，保存使用者 prompt：
[carton_codex_prompt.md](../../contracts/carton_codex_prompt.md)。
不是另啟官方 Codex SDK child 或註冊外部 Geometry provider；不宣稱官方鍵盤流程已復現。
未新增 Isaac Lab 依賴，使用已安裝 Isaac Sim 6 standalone PhysX；Isaac Lab integration not_tested。

已新增 scripts/pf-carton、carton_runtime.py 與 crease_model.py。
四片獨立 rigid flap、四個 revolute joint、一個固定箱體 articulation、SI 質量／慣量讀回，
啟用所有 plate collision 與 articulation self collision，光源與紙板 displayColor。
RSC nominal flap length=W/2，實際端部減 0.5 mm 做有限厚度轉動間隙，兩主蓋中心閉合 gap=1 mm。
這是工程建模估計，不是量測紙箱尺寸。壁厚4mm、接觸偏移1mm／rest offset0。

## 可觀看的資產與執行方式

[初始 USD](../../runs/20260917T105836Z_ext1_carton/asset.usda) ·
[實測終態 USD](../../runs/20260917T105836Z_ext1_carton/scene_final.usda) ·
[原始 CSV](../../runs/20260917T105836Z_ext1_carton/trajectory.csv) ·
[測試結果](../../runs/20260917T105836Z_ext1_carton/carton_result.json)。

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-carton --physics-device cpu
```

本輪相同命令整體 exit 1，因完整 mechanics acceptance fail。Kit runtime exit 0
不代表物理驗收 pass；host 會看 carton_result.json，失敗保留 exit 1。
每次新 run，保存 config/prompt/source hashes/launch/CSV/result，不改舊 run。

3D 查看已生成的四片蓋（先停止播放）：

```bash
./scripts/pf view --run 20260917T105836Z_ext1_carton --scene scene_final.usda --ui --paused
```

若已有 viewer，保存既有場景後用其 Script Editor：

```python
import omni.usd
omni.usd.get_context().open_stage('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T105836Z_ext1_carton/scene_final.usda')
```

Stage 選 /World/Carton，滑鼠移到 viewport 按 F。此 viewer 只讀 USD；直接按 Play
不會執行 Python per-step plastic/fatigue 更新。完整 controller 測試需使用 pf-carton。
本次沒有 viewer launch、人類觀看、PNG 或影片，狀態各自 not_tested。

## prompt 的必要技術修正

- Angular USD limits/target 是 degrees，USD stiffness/damping 是 per-degree；配置與
controller 用 radian/SI，作者端乘 pi/180。tensor gain 讀回 k=.04、c=.003 正確。
- Isaac 6 使用 Articulation.set_dof_position_targets，不使用已移除的 4.x ArticulationView API。
- PhysxJointAPI.jointFriction 是無因次 coefficient；本原型 .01 未校準，不能寫成 .01 N·m。
若要常數抵抗力矩，必須另外配置 torque friction 模型／新版 friction effort API 後驗證。
- 含 dt 的塑性 flow 分母解讀為 viscosity eta（N·m·s/rad），非無時間單位 plastic modulus。
採用固定本步 angle 的 backward Euler：delta_p=sign(M)*max(|M|-Y,0)*dt/(eta+k*dt)。
Y 隨 accumulated absolute plastic rotation 軟化並設下限；不是每步無條件重複降值。
這是未校準 viscoplastic proxy，不是完整紙板微觀塑性。
- 最後施載採用 force-drive reference offset p+Mext/k，與線性 force drive 的附加力矩
方程等效，不直接設定瞬時關節姿態。CSV 保留 p 與 virtual loading torque。
不宣稱已用 sensor 量到實際外力；DOF effort/external link torque 的早期嘗試未通過。
- MD/CD orthotropy、B/C flute、單雙層層間力學目前未模擬。rigid panel 不能呈現板面
異向性彎曲；材料資訊與所有參數是 uncalibrated_assumption。

來源：[OpenUSD DriveAPI](https://openusd.org/dev/api/class_usd_physics_drive_a_p_i.html)、
[NVIDIA joint friction](https://docs.omniverse.nvidia.com/kit/docs/omni_usd_schema_physics/latest/physxschema/class_physx_schema_physx_joint_a_p_i.html)，
與本機 Articulation Python API。塑性／軟化及測試控制器為本專案 Codex 實作。

## 每一個可確認的小成果

| 項目 | 實測結果 |
| --- | --- |
| 生成四蓋 USD | implemented＋本機生成命令執行完成 |
| articulation 自由度／質量／慣量讀回 | 四 DOFs；tensor readback 保存 |
| 一般物理執行 | pass；2400 steps×4 joints=9600 CSV rows |
| 低力矩主蓋 | peak 14.5846°，終態 -0.1971°，plastic target=0° |
| 高力矩主蓋 | peak約100°，plastic target=30.2248°，終態角16.1549° |
| 高力矩主蓋穩定 | fail；終態速度 .2652 rad/s，不可稱 equilibrium |
| 兩片次蓋塑性／保留開口 | fail；另一主蓋未開，幾何阻擋尚待分離確認 |
| 整體驗收 | fail；未放寬 gate/停用 collision |
| 重複循環疲勞、dt收斂、實物校正 | not_tested（純函式 dt refinement 測試另列） |

原型已證明一片主蓋低負载回復、一片主蓋產生塑性內狀態；尚不能說所有蓋都符合 prompt。
終態角不能用來反推校正，因高力矩主蓋還沒穩定。殘餘平衡還應考慮 joint friction、接觸
與限位，不只是彈性與重力兩項。

132 項 offline tests，7 skipped，exit 0：20260917T084810Z_ext1_offline。
測試新增 subyield／high-load state、反向塑性、非負耗散 proxy、softening 下限與 dt refinement。
這些不等於真實紙板、PhysX fatigue／dt 收斂成功。smoke exit 0：084558Z_s1_smoke。

失敗歷史：084748（DOF torque），084927（gain/effort讀回），085207（external torque），
105512（contact offset），105603（CPU），105646（force-drive offset），105744（open-pose診斷），
105836（tip clearance）皆保留。105744 初始化後的角度未如預期保持，不能拿來證明開口姿態對照。
自動審查拒絕同時更換 low-control joint 的命令；改為只更新幾何間隙，原分類不變，無待批准動作。

下一個 bounded action：固定現有驗收與失敗證據，新增獨立的「主蓋先開、次蓋後開」診斷
與單折痕無其他蓋遮擋的測量資產，將材料回復與互撞分開；不能直接換控制關節把舊 gate 變 pass。
