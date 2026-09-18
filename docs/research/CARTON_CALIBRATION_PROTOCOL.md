# 紙箱摺痕實物校準（待實測）

目前密度、勁度、降伏力矩、黏塑性黏度、軟化率、摩擦力矩都是估計。
四蓋 PhysX 行為通過，不等於真實 B/C flute 材料已辨識。

## 一個概念、一個實驗

概念：低於降伏時回彈，高於降伏時留下塑性參考角。單次放手角不能唯一
辨識勁度、降伏、黏度、摩擦與疲勞；接觸、重力、限位也會影響停留角。

實驗：固定箱體，其他蓋保持打開；同一片蓋從相同初始角出發，只改最大推開角。
先推20°再放手，下一次推80°再放手。記錄施力、垂直力臂、角度、時間與放手後角度。
第一次已留下塑性變形時，後續不能假設未使用狀態；用新樣品或完整紀錄歷史。

使用 [CSV空白模板](../../reports/development/2026-09-17_carton_calibration_template.csv)，
phase 建議 loading/unloading/released，flap_name 用 MajorYN/MajorYP/MinorXP/MinorXN。
原始影片另存 reports/development/ 的實測附件資料夾，CSV記下影片名稱／時間碼。
保留原始影片，不能把重建曲線當成力計讀值。模板沒有虛構量測列。

## 下一階段辨識要求

- 分別量測四條摺痕，註記 MD/CD、flute類型、層數、濕度、尺寸及實際質量。
- 施力×垂直力臂得到外力矩（正負方向一致）；扣除／平衡重力及慣性後才能求摺痕力矩。
- 小角加／卸載斜率辨識勁度；不同推開角辨識降伏／殘餘角；不同速度辨識阻尼／黏度。
- 正反向曲線辨識摩擦／遲滯；重複循環辨識軟化率。不能從一次放手角猜所有參數。
- 分開校準與保留測試集，固定接受誤差後驗證。未提供保留資料不能稱實物驗證 pass。
- 板面正交異向性彎曲與局部折痕是不同模型；目前剛性板件不會產生 MD/CD 板面彎曲。

## 方法來源與適用範圍

使用者提供的 carton prompt 是此專案折痕代理模型的直接需求，數值不是文獻校準。
[OpenUSD DriveAPI](https://openusd.org/dev/api/class_usd_physics_drive_a_p_i.html) 定義 angular drive 的 degree 單位。
[NVIDIA PhysxJointAPI](https://docs.omniverse.nvidia.com/kit/docs/omni_usd_schema_physics/latest/physxschema/class_physx_schema_physx_joint_a_p_i.html) 的 legacy jointFriction 是係數。
本機 Isaac6 experimental Articulation 的 set/get_dof_friction_properties 與 PhysxJointAxisAPI
提供 friction efforts；轉動DOF以N·m表示。軟化／黏塑性更新為本專案代理模型，需實測。

紙板壓痕與遲滯方法可參考 [Beex & Peerlings 2009](https://publications.uni.lu/bitstream/10993/17431/1/BeexPeerlings2009.pdf)，
但該研究不能直接給此瓦楞紙箱的數值；其他來源與限制見 CARDBOARD_MECHANICS.md。
