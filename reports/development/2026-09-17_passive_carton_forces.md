# 被動紙箱：以拉力與接觸操作（2026-09-17）

## 使用者需求修正

紙箱是被動物件，不需告訴它「開／關」。四片蓋各有自己的物理關節，外力、重力、碰撞及摺痕／板面材料力決定角度。
已移除所有開／關按鈕；新資產 `interaction_mode=external_forces_only`，呼叫舊 drive-offset torque actuator 會明確拒絕。
保留舊 API 僅供既有基準回歸；新資產與新測試完全沒有用它，舊混合失敗未修改。

`carton_live.py` 只更新材料塑性参考角，對新資產不施加操作力。Drive 的目標是材料的無應力參考角，不是命令資產開到某角度。
`carton_force_probe.py` 是可選、獨立的外緣力測試工具，直接對最外側板段施加 N 單位力；不修改紙箱姿態／關節狀態。
`carton_contact_test.py` 的運動學球形手指只有自己的運動軌跡，紙箱透過碰撞被推動。機器人整合只需材料回呼，不需測試工具或介面。

## 為什麼之前不符合

1. 舊介面只有雙主蓋操作，錯誤地把展示操作當成主要使用方式；已移除。
2. 原板面純彈性、永久以零參考角恢復，故放手彈回是模型本身，不是永久損傷；新增估計彈塑性板條模型。
3. 原生滑鼠施力尚未被證明送到物件。讀回headless程序：三個相關UI擴充都false，pickingForce=1.0；此值是滑鼠施力係數，不是人拖曳「多用力」或已量測牛頓值。不能以headless結果斷言你的viewer也是同狀態。
4. 主蓋回彈遮擋次蓋仍是實際碰撞耦合：驗證次蓋時先用外力支撐主蓋，沒有把碰撞關掉或強制固定到開啟角。單片可操作，不代表與鄰片無接觸。

## 材料模型與來源

板面彈性MD/CD仍來自[Holmvall，130TL Table1](https://onlinelibrary.wiley.com/doi/full/10.1002/pts.2607)；沒有改軟來掩蓋拖曳失效。
新增 `estimated_elastoplastic_strip_v1`：降伏曲率假設2/m、塑性鬆弛時間假設0.05s，Y=k×段長×降伏曲率；不套用摺痕Y到板面。
這是未校準的現象學損傷代理。小變形仍應彈回，大變形可留下塑性角；不宣稱符合真實箱子的壓皺／撕裂或材料測試。
本輪大力案例放手後两個板面關節約30°，接近原±30°限位；塑性參考角更大，故這個殘留形狀也受人工限位影響，不可用作真實紙板損傷量測或可靠自由平衡角。
一維分段板材、固定底部／剛性箱壁等限制保留。

## 命令與逐項證據

```bash
cd /mnt/HDD4/wyattsheu/ITRI/parcel-forge
./scripts/pf-carton-interaction-test
./scripts/pf-carton-contact-test --run 20260917T123830Z_ext1_independent_interaction
./scripts/pf-panel-usd-check --run 20260917T123830Z_ext1_independent_interaction
```

| 項目 | 命令退出／run | 已量測結果 |
|---|---|---|
|單片閉合主蓋受外力|exit0，`20260917T123830Z_ext1_independent_interaction`|MajorYN外緣2N、2秒，約100°；對面約-0.37°|
|四片逐片受力|同run exit0|主蓋各自1N外力支撐，次蓋各自1N、3秒；MinorXP與MinorXN分次各約100°，第一片次蓋打開时對面仍關閉|
|板面估計塑性|同run exit0|MajorYN外緣35N、1秒，卸載後板面塑性與殘留彎曲；受±30°限位，非校準結果|
|沒有開關致動|同run exit0|無drive-offset命令且新資產拒絕舊 actuator|
|機器人式碰撞|exit0，`20260917T123950Z_ext1_passive_contact`|運動學球形手指碰撞；主蓋峰值94.77°、對面绝对最大0.435°，接觸力峰值0.778875N；無紙箱姿態／狀態命令|
|USD拓撲與官方規則|exit0，`20260917T123916Z_ext1_panel_usd_check`|16關節／21碰撞板件／剛度單位通過，NVIDIA41規則0 failures|
|舊四關節基準回歸|exit0，`20260917T123919Z_ext1_live_callback_test`|1208回呼、原結果重現；不是新資產的操作方式|
|離線測試|exit0，`20260917T123857Z_ext1_passive_offline`|136 tests，7 skipped；diff check0|
|smoke|exit0，`20260917T122729Z_s1_smoke`|原重力／自由落體基準重現|
|原生WebRTC拖曳|not_tested／使用者回報舊版失效|新版本尚未人眼與原生滑鼠驗證|
|完整機器人／夾爪|not_tested|接觸球測試不等於真正機器人工作流完成|
|render／影片|not_tested／未生成|[CSV接觸曲線](/mnt/HDD4/wyattsheu/ITRI/parcel-forge/runs/20260917T124149Z_ext1_passive_delivery/single_flap_contact.svg)不是相機影像|

失敗保存：123043混合版次蓋受主蓋回彈遮擋；123327缺少ContactReportAPI；123520用teleport而非kinematic target未產生接觸；123629未指定stage_id。上述沒有改驗收門檻，後續以正確API／外力邊界重跑。
接觸API以本機110.1.13 `omni.physics.tensors.RigidBodyView.set_kinematic_targets`（xyzw）為準，明確stage_id；PhysxContactReportAPI在Play前掛載。沒有重設共享模擬。

## WebRTC 載入被動物件

先保存編輯器工作、停止 timeline。Script Editor：

```python
exec(open('/mnt/HDD4/wyattsheu/ITRI/parcel-forge/scripts/carton_passive_editor.py').read())
```

等待載入後按Play，選 `/World/Carton/MajorYN_S3`、F定位。資產預設沒有操作視窗，也不自動開蓋；只有材料回呼。
loader印出唯讀mouse診斷；不啟用擴充套件，不安裝或重啟viewer。`carton_mdcd_editor.py` 已同步改為此被動入口。

如果只想隔離滑鼠問題，可在Play後打開**可選外力測試工具**：

```python
pf_live.show_controls()
```

單一實驗：只將 MajorYN edge force 從0改為2N，觀察單片動作，再改回0／Release。這是外力，不是開蓋命令；機器人工作流不需要此工具。
正負力沿當下板段法線，不是世界固定Z；保持施力直到設0或Release，Stop清除力／塑性歷史，Pause保留。
回呼證據由run內events.jsonl和force_probe.jsonl保存；Play按下后的數值紀錄不等於人眼WebRTC確認。

## 原生滑鼠UI阻擋與待批准動作

[AGENTS.md](/mnt/HDD4/wyattsheu/ITRI/parcel-forge/AGENTS.md) 明文："Never reinstall, upgrade or reconfigure Isaac Sim, the driver, or the shared venv."
自動批准審查拒絕 `set_extension_enabled_immediate` 啟用已安裝UI，判定違反上述規則；含該動作的整批命令未執行。未繞過拒絕。
具體待批准例外：只在目前viewer啟用本地110.1.13 `omni.physics.ui` 與 `omni.physics.physx.ui`（其依賴含omni.physx.ui）；不安裝／升級、不改設定檔、不重啟viewer或碰其他程序。擴充將改變目前應用程式的UI／互動狀態。
仍需先用loader的唯讀診斷確認viewer是否真的未啟用；若已啟用，應追查輸入與施力係數而非宣稱UI解決全部問題。
來源：[NVIDIA mouse settings](https://docs.omniverse.nvidia.com/kit/docs/omni_physics/107.0/dev_guide/settings.html) 為概念說明，本機110.1.13 extension.toml與API才是版本依據。

下一個單一动作：取得上述例外許可後，根據viewer唯讀診斷驗證原生拖曳／接觸；沒有許可就不啟用。
